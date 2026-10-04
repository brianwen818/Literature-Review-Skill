"""Step 3 - clean the seed references and resolve them to DOIs via Crossref.

Uses inputs/seed-references.csv; when it has no usable rows, falls back to the
reference lists extracted from the main documents in step 2.
Writes intermediate-data/processed-seed-references.csv and seed-data.json.

Rows with status 'low_confidence' carry a candidate match that was not trusted.
After checking them, accept the right ones by their `no`:

    python codes/scripts/03_prepare_seeds.py --project NAME --accept 4,17
"""
import _bootstrap  # noqa: F401
from modules.config import project_from_args, read_csv_rows, read_json, write_csv_rows, write_json
from modules.crossref import Crossref
from modules.seeds import dedupe_seeds, read_seed_rows, resolve_seeds, seed_data, seeds_from_documents

COLUMNS = ["no", "reference", "doi", "status", "failed_checks", "match_score", "title_overlap", "matched_title",
           "matched_journal", "matched_year", "candidate_doi", "origin"]


def main():
    project, args = project_from_args(__doc__, lambda p: p.add_argument(
        "--accept", default="", help="comma-separated `no` values of low_confidence rows to accept"))
    accepted_path = project.inter / "seed-accepted.json"
    accepted = read_json(accepted_path, {})
    if args.accept:
        wanted = {n.strip() for n in args.accept.split(",") if n.strip()}
        for row in read_csv_rows(project.processed_seeds):
            if row["no"] in wanted and row.get("candidate_doi"):
                accepted[row["reference"]] = row["candidate_doi"]
        write_json(accepted_path, accepted)
    seeds = read_seed_rows(project.seed_csv)
    source = "seed-references.csv"
    if not seeds:
        project.require(project.processed_docs / "manifest.csv", "run 02_prepare_main_docs.py first")
        documents = []
        for path in sorted(project.processed_docs.glob("*.references.txt")):
            entries = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
            documents.append({"source": path.name.replace(".references.txt", ""), "reference_entries": entries})
        seeds = seeds_from_documents(documents)
        source = "reference lists of the main documents"
    total = len(seeds)
    for seed in seeds:
        if not seed["doi"] and seed["reference"] in accepted:
            seed["doi"] = accepted[seed["reference"]]
    seeds = dedupe_seeds(seeds)
    if not seeds:
        raise SystemExit("No seed references: seed-references.csv is empty and no reference list "
                         "was found in the main documents.")
    print(f"{total} seed reference(s) from {source}; {len(seeds)} after de-duplication. Resolving...")
    crossref = Crossref(project.config["crossref_mailto"])

    def progress(done, count):
        if done % 20 == 0 or done == count:
            print(f"  {done}/{count}")

    cache_path = project.inter / "seed-lookup-cache.json"
    cache = read_json(cache_path, {})
    rows, records = resolve_seeds(seeds, crossref, progress, cache)
    write_json(cache_path, cache)
    write_csv_rows(project.processed_seeds, rows, COLUMNS)
    write_json(project.seed_data, seed_data(records))
    statuses = {}
    for row in rows:
        statuses[row["status"]] = statuses.get(row["status"], 0) + 1
    with_refs = sum(1 for r in records.values() if any(ref.get("doi") for ref in r["references"]))
    project.update_stats(seeds_input=total, seeds_unique=len(seeds), seeds_resolved=len(records),
                         seeds_with_reference_list=with_refs, seed_status=statuses, seed_source=source)
    print(f"\nResolved to a DOI: {len(records)}/{len(seeds)}   status: {statuses}")
    print(f"Seeds whose own reference list is available: {with_refs}")
    if statuses.get("error"):
        print(f"{statuses['error']} lookup(s) failed (network or rate limit); run this step again to retry them.")
    if statuses.get("low_confidence"):
        print(f"Review the 'low_confidence' rows in {project.processed_seeds};\n"
              "  accept correct candidates with --accept NO,NO (see --help).")
    print(f"Crossref HTTP status counts: {dict(crossref.status_counts)}")


if __name__ == "__main__":
    main()
