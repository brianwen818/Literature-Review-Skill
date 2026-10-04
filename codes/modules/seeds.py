"""Seed references: read whatever the user supplied, clean it, resolve to DOIs."""
import re
from concurrent.futures import ThreadPoolExecutor

from .config import read_csv_rows
from .crossref import MAX_WORKERS, match_result
from .textutil import clean_text, find_doi, normalize_doi, normalize_title

# Column aliases, lowercased. Covers the template and a Zotero CSV export.
_COLUMNS = {
    "reference": ("reference", "citation", "ref", "引用", "參考文獻"),
    "doi": ("doi",),
    "title": ("title", "標題"),
    "authors": ("authors", "author", "作者"),
    "year": ("year", "publication year", "年份"),
}


def _pick(row, field):
    for key, value in row.items():
        if key and key.strip().lower() in _COLUMNS[field] and value and str(value).strip():
            return clean_text(value).strip()
    return ""


def read_seed_rows(path):
    """Seed CSV -> list of {reference, doi, title} (empty list if nothing usable)."""
    seeds = []
    for row in read_csv_rows(path):
        title = _pick(row, "title")
        reference = _pick(row, "reference")
        doi = normalize_doi(_pick(row, "doi")) or find_doi(reference)
        if not reference and title:
            parts = [_pick(row, "authors"), f"({_pick(row, 'year')})" if _pick(row, "year") else "", title]
            reference = " ".join(p for p in parts if p)
        if reference or doi:
            seeds.append({"reference": reference, "doi": doi, "title": title, "origin": "seed-references.csv"})
    return seeds


def seeds_from_documents(documents):
    """Fallback when the seed CSV is empty: the main documents' reference lists."""
    seeds = []
    for document in documents:
        for entry in document.get("reference_entries", []):
            seeds.append({"reference": entry, "doi": find_doi(entry), "title": "",
                          "origin": f"main-docs/{document['source']}"})
    return seeds


def dedupe_seeds(seeds):
    seen, unique = set(), []
    for seed in seeds:
        key = seed["doi"] or re.sub(r"\s+", " ", normalize_title(seed["reference"]))[:120]
        if key and key not in seen:
            seen.add(key)
            unique.append(seed)
    return unique


def resolve_seeds(seeds, crossref, progress=None, cache=None):
    """Attach Crossref metadata. Returns (rows for the CSV, {doi: record}).

    cache: {reference text: lookup result} from earlier runs; free-text lookups
    are slow, so only references not seen before are sent to Crossref. Failed
    requests are not cached and are retried on the next run."""
    cache = {} if cache is None else cache
    given = crossref.works_by_dois([s["doi"] for s in seeds if s["doi"]])
    to_resolve = [i for i, s in enumerate(seeds)
                  if s["reference"] and not s["doi"] and s["reference"] not in cache]
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        for index, result in zip(to_resolve, pool.map(
                lambda i: crossref.resolve_citation(seeds[i]["reference"]), to_resolve)):
            if result["status"] != "error":
                cache[seeds[index]["reference"]] = result
    rows, records = [], {}
    for index, seed in enumerate(seeds):
        row = {"no": index + 1, "reference": seed["reference"], "origin": seed["origin"],
               "doi": "", "status": "", "match_score": "", "title_overlap": "",
               "matched_title": "", "matched_journal": "", "matched_year": ""}
        record = None
        if seed["doi"] and seed["doi"] in given:
            record, row["status"] = given[seed["doi"]], "doi_given"
        elif seed["doi"]:
            row["doi"], row["status"] = seed["doi"], "doi_not_in_crossref"
        if record is None and seed["reference"] and row["status"] != "doi_not_in_crossref":
            result = cache.get(seed["reference"]) or {"status": "error"}
            if result.get("record"):   # re-judge cached hits with the current rules
                result = match_result(seed["reference"], result["record"], result["score"])
            row["failed_checks"] = result.get("failed_checks", "")
            row["status"] = result["status"]
            row["match_score"] = result.get("score", "")
            row["title_overlap"] = result.get("title_overlap", "")
            candidate = result.get("record")
            if candidate:
                row["matched_title"] = candidate["title"]
                row["matched_journal"] = candidate["journal"]
                row["matched_year"] = candidate["year"]
                if result["status"] == "resolved":
                    record = candidate
                else:
                    row["doi"] = ""  # shown for review only; not used downstream
                    row["candidate_doi"] = candidate["doi"]
        if record is not None:
            row.update(doi=record["doi"], matched_title=record["title"],
                       matched_journal=record["journal"], matched_year=record["year"])
            records[record["doi"]] = record
        rows.append(row)
        if progress:
            progress(index + 1, len(seeds))
    return rows, records


def seed_data(records):
    """What scoring needs from each seed: text and the DOIs it cites."""
    data = {}
    for doi, record in records.items():
        data[doi] = {
            "title": record["title"], "abstract": record["abstract"], "journal": record["journal"],
            "year": record["year"],
            "ref_dois": sorted({r["doi"] for r in record["references"] if r.get("doi")}),
            "references": record["references"],
        }
    return data
