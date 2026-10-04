"""Journal validation and the keyword x journal search with resume support."""
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import append_jsonl, read_jsonl
from .crossref import MAX_WORKERS, normalize_journal_name
from .textutil import noise_reason, normalize_title

_ISSN = re.compile(r"^\d{4}-?\d{3}[\dxX]$")
SUSPICIOUS_TOTAL_DOIS = 300


def format_issn(value):
    value = (value or "").strip().upper()
    if not _ISSN.match(value):
        return ""
    return value if "-" in value else value[:4] + "-" + value[4:]


def validate_journal(row, crossref):
    """One journal-list row -> validated row with a working ISSN and a status."""
    name = (row.get("journal") or row.get("Journal") or "").strip()
    issns = [format_issn(row.get(col)) for col in ("issn_print", "issn_online", "issn",
                                                    "ISSN (Print)", "ISSN (Online)", "ISSN", "EISSN")]
    issns = [i for i in dict.fromkeys(issns) if i]
    result = {"journal": name, "issn": "", "all_issns": "", "crossref_title": "",
              "publisher": "", "total_dois": "", "status": "not_found", "note": ""}
    info = None
    for issn in issns:
        info = crossref.journal(issn)
        if info:
            result["issn"] = issn
            break
    if info is None and name:
        info = crossref.find_journal_by_name(name)
        if info:
            result["issn"] = info["issns"][0]
            result["note"] = "ISSN found by exact title match"
    if info is None:
        result["note"] = "not in Crossref under the given ISSN or title"
        return result
    result.update(all_issns=";".join(info["issns"]), crossref_title=info["title"],
                  publisher=info["publisher"], total_dois=info["total_dois"], status="ok")
    if name and normalize_journal_name(info["title"]) != normalize_journal_name(name):
        result["status"] = "needs_review"
        result["note"] = "Crossref title differs from the listed name"
    elif info["total_dois"] < SUSPICIOUS_TOTAL_DOIS:
        result["status"] = "needs_review"
        result["note"] = f"only {info['total_dois']} DOIs registered"
    if not name:
        result["journal"] = info["title"]
    return result


def run_search(journals, keywords, crossref, search_dir, rows, year_from, year_to, progress=None):
    """Run every (journal, keyword) query that has not succeeded yet.

    Two append-only files make the run resumable:
    queries.jsonl  one line per finished query, with the DOIs it returned
    items.jsonl    one line per article, written the first time it is seen
    """
    queries_path = search_dir / "queries.jsonl"
    items_path = search_dir / "items.jsonl"
    done = {(q["issn"], q["keyword"]) for q in read_jsonl(queries_path) if q.get("status") == "ok"}
    seen = {item["doi"] for item in read_jsonl(items_path)}
    tasks = [(j, k) for j in journals for k in keywords if (j["issn"], k) not in done]
    lock = threading.Lock()
    failed = 0

    def work(journal, keyword):
        result = crossref.search_journal(journal["issn"], keyword, rows, year_from, year_to)
        return journal, keyword, result

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(work, j, k) for j, k in tasks]
        for count, future in enumerate(as_completed(futures), 1):
            journal, keyword, result = future.result()
            with lock:
                if result is None:
                    failed += 1
                    append_jsonl(queries_path, {"issn": journal["issn"], "keyword": keyword, "status": "failed"})
                else:
                    total, items = result
                    dois = []
                    for rank, item in enumerate(items, 1):
                        if not item["doi"]:
                            continue
                        dois.append(item["doi"])
                        if item["doi"] not in seen:
                            seen.add(item["doi"])
                            item["listed_journal"] = journal["journal"]
                            item["listed_issn"] = journal["issn"]
                            append_jsonl(items_path, item)
                    append_jsonl(queries_path, {"issn": journal["issn"], "keyword": keyword,
                                                "status": "ok", "total": total, "dois": dois})
            if progress:
                progress(count, len(tasks))
    return {"queries_total": len(journals) * len(keywords), "queries_run": len(tasks),
            "queries_failed": failed, "queries_skipped_done": len(done)}


def consolidate(search_dir, seed_dois, zotero_dois, zotero_titles):
    """Search files -> (candidate rows, {doi: references}, counters).

    Nothing is deleted: non-articles, duplicates, seeds and items already in
    Zotero are flagged in `excluded` so the funnel can be reported."""
    hits = {}
    raw_hits = 0
    for query in read_jsonl(search_dir / "queries.jsonl"):
        if query.get("status") != "ok":
            continue
        for doi in query.get("dois", []):
            raw_hits += 1
            hits.setdefault(doi, []).append(query["keyword"])
    items = {}
    for item in read_jsonl(search_dir / "items.jsonl"):
        if item["doi"] in hits:
            items[item["doi"]] = item

    def richness(item):
        return (bool(item["abstract"]), len(item["references"]), item["cited_by_count"])

    by_title = {}
    for doi, item in items.items():
        key = normalize_title(item["title"])
        if key and (key not in by_title or richness(item) > richness(items[by_title[key]])):
            by_title[key] = doi
    rows, references = [], {}
    for doi, item in items.items():
        key = normalize_title(item["title"])
        excluded = noise_reason(item["title"])
        if not excluded and key and by_title.get(key) != doi:
            excluded = "duplicate_title"
        if not excluded and doi in seed_dois:
            excluded = "seed"
        if not excluded and (doi in zotero_dois or (key and key in zotero_titles)):
            excluded = "in_zotero"
        keywords_hit = list(dict.fromkeys(hits[doi]))
        rows.append({
            "item_id": doi, "doi": doi, "title": item["title"], "authors": item["authors_str"],
            "year": item["year"], "journal": item.get("listed_journal") or item["journal"],
            "issn": item.get("listed_issn", ""), "type": item["type"],
            "abstract": item["abstract"], "has_abstract": bool(item["abstract"]),
            "references_count": item["references_count"],
            "has_references": bool(item["references"]),
            "cited_by_count": item["cited_by_count"],
            "n_keyword_hits": len(keywords_hit), "keywords_hit": "; ".join(keywords_hit),
            "excluded": excluded,
        })
        references[doi] = item["references"]
    counters = {"raw_hits": raw_hits, "unique_articles": len(rows)}
    for row in rows:
        if row["excluded"]:
            counters[f"excluded_{row['excluded']}"] = counters.get(f"excluded_{row['excluded']}", 0) + 1
    counters["candidates_for_scoring"] = sum(1 for r in rows if r["excluded"] in ("", "seed"))
    return rows, references, counters
