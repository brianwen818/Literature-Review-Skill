"""Step 4 - validate the journal list against Crossref.

Reads inputs/journal-lists.csv (columns: journal, issn_print, issn_online; a
name alone is enough) and writes intermediate-data/journals-validated.csv.
Only rows with status 'ok' or 'needs_review' are searched; set `use` to `no`
in the validated file to drop a journal.
"""
import _bootstrap  # noqa: F401
from modules.config import project_from_args, read_csv_rows, write_csv_rows
from modules.crossref import Crossref
from modules.search import validate_journal

COLUMNS = ["journal", "issn", "use", "status", "note", "crossref_title", "publisher", "total_dois", "all_issns"]


def main():
    project, _ = project_from_args(__doc__)
    rows = [r for r in read_csv_rows(project.journal_csv)
            if any((v or "").strip() for v in r.values())]
    if not rows:
        raise SystemExit(f"{project.journal_csv} has no journals.\n"
                         "  -> list the journals to search (see references/journal-lists/ for field lists).")
    crossref = Crossref(project.config["crossref_mailto"])
    validated, seen = [], set()
    for row in rows:
        result = validate_journal(row, crossref)
        if result["issn"] and result["issn"] in seen:
            continue
        seen.add(result["issn"])
        result["use"] = "yes" if result["status"] != "not_found" else "no"
        validated.append(result)
        print(f"{result['status']:13} {result['journal']}  {result['issn']}  {result['note']}")
    write_csv_rows(project.journals_validated, validated, COLUMNS)
    usable = sum(1 for r in validated if r["use"] == "yes")
    project.update_stats(journals_listed=len(rows), journals_usable=usable)
    print(f"\n{usable}/{len(rows)} journal(s) usable -> {project.journals_validated}")


if __name__ == "__main__":
    main()
