"""Step 6 - search every confirmed keyword in every validated journal (Crossref).

Safe to interrupt and re-run: finished queries are skipped.
    --plan     only print how many queries would run
    --zotero   also flag articles already in the Zotero library (needs zotero-info/.env)
Writes intermediate-data/candidates.csv and candidate-references.jsonl.
"""
import json

import _bootstrap  # noqa: F401
from modules.config import (load_env, project_from_args, read_csv_rows, read_json, write_csv_rows)
from modules.crossref import RATE_LIMIT_PER_SEC, Crossref
from modules.search import consolidate, run_search
from modules.textutil import normalize_doi, normalize_title


def options(parser):
    parser.add_argument("--plan", action="store_true", help="show the size of the search and stop")
    parser.add_argument("--zotero", action="store_true", help="exclude items already in the Zotero library")


def load_keywords(project):
    rows = read_csv_rows(project.require(project.keywords, "run 05_extract_keywords.py first"))
    keywords = [r["keyword"].strip() for r in rows
                if r.get("keyword", "").strip() and (r.get("use") or "yes").strip().lower() not in ("no", "n", "0")]
    return list(dict.fromkeys(keywords))


def load_journals(project):
    rows = read_csv_rows(project.require(project.journals_validated, "run 04_prepare_journals.py first"))
    return [r for r in rows if r.get("issn") and (r.get("use") or "yes").strip().lower() == "yes"]


def zotero_existing(project):
    from modules.zotero import Zotero, settings_from_env

    client = Zotero(**settings_from_env(load_env(project.env_path)))
    dois, titles, _ = client.existing()
    write_csv_rows(project.zotero_existing,
                   [{"kind": "doi", "value": d} for d in sorted(dois)] +
                   [{"kind": "title", "value": t} for t in sorted(titles)], ["kind", "value"])
    print(f"Zotero library holds {len(dois)} DOIs / {len(titles)} titles")


def main():
    project, args = project_from_args(__doc__, options)
    config = project.config
    keywords, journals = load_keywords(project), load_journals(project)
    limit = int(config["max_keywords"])
    if len(keywords) > limit:
        raise SystemExit(f"keywords.csv has {len(keywords)} active keywords; max_keywords is {limit}.\n"
                         "  -> trim the list or raise max_keywords in config.yaml")
    n_queries = len(keywords) * len(journals)
    minutes = n_queries / RATE_LIMIT_PER_SEC / 60 * 3   # responses carry reference lists, so allow slack
    estimate = "under a minute" if minutes < 1 else f"roughly {minutes:.0f} min"
    print(f"{len(keywords)} keywords x {len(journals)} journals = {n_queries} queries "
          f"(up to {config['rows_per_query']} results each), {estimate}")
    if args.plan:
        return
    if not keywords or not journals:
        raise SystemExit("Nothing to search: need at least one keyword and one journal.")
    crossref = Crossref(config["crossref_mailto"])
    project.search_dir.mkdir(parents=True, exist_ok=True)

    def progress(done, count):
        if done % 50 == 0 or done == count:
            print(f"  {done}/{count} queries")

    stats = run_search(journals, keywords, crossref, project.search_dir, int(config["rows_per_query"]),
                       config["year_from"], config["year_to"], progress)
    print(f"Crossref HTTP status counts: {dict(crossref.status_counts)}")
    if stats["queries_failed"]:
        print(f"WARNING: {stats['queries_failed']} queries failed; run this step again to retry them.")
    if args.zotero:
        zotero_existing(project)
    existing = read_csv_rows(project.zotero_existing)
    zotero_dois = {normalize_doi(r["value"]) for r in existing if r["kind"] == "doi"}
    zotero_titles = {r["value"] for r in existing if r["kind"] == "title"}
    seed_dois = set(read_json(project.seed_data, {}))
    rows, references, counters = consolidate(project.search_dir, seed_dois, zotero_dois, zotero_titles)
    write_csv_rows(project.candidates, rows)
    with project.candidate_refs.open("w", encoding="utf-8") as handle:
        for doi, refs in references.items():
            handle.write(json.dumps({"doi": doi, "references": refs}, ensure_ascii=False) + "\n")
    project.update_stats(keywords=keywords, n_keywords=len(keywords), n_journals=len(journals),
                         **stats, **counters)
    print("\nFunnel so far:")
    for key, value in counters.items():
        print(f"  {key:28} {value}")
    print(f"-> {project.candidates}")


if __name__ == "__main__":
    main()
