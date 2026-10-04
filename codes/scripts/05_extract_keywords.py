"""Step 5 - propose search keywords from the main documents and the seeds.

Writes intermediate-data/keyword-candidates.csv (ranked n-grams with flags)
and, if it does not exist yet, intermediate-data/keywords.csv - the list that
is actually searched. The agent edits keywords.csv (columns: keyword, use,
source, note) and the user confirms it before step 6.
"""
import _bootstrap  # noqa: F401
from modules.config import project_from_args, read_json, write_csv_rows
from modules.keywords import default_selection, keyword_candidates


def main():
    project, args = project_from_args(__doc__, lambda p: p.add_argument(
        "--reset", action="store_true", help="overwrite an existing keywords.csv"))
    project.require(project.processed_docs / "manifest.csv", "run 02_prepare_main_docs.py first")
    main_texts = [p.read_text(encoding="utf-8") for p in sorted(project.processed_docs.glob("*.md"))]
    seeds = read_json(project.seed_data, {})
    seed_texts = [f"{s['title']}. {s.get('abstract', '')}" for s in seeds.values()]
    rows = keyword_candidates(main_texts, seed_texts)
    write_csv_rows(project.keyword_candidates, rows,
                   ["keyword", "ngram", "main_doc_count", "doc_frequency", "score", "flag"])
    print(f"{len(rows)} candidate keywords -> {project.keyword_candidates}")
    if project.keywords.exists() and not args.reset:
        print(f"kept existing {project.keywords} (use --reset to regenerate)")
    else:
        selection = default_selection(rows, project.config["max_keywords"])
        write_csv_rows(project.keywords, selection, ["keyword", "use", "source", "note"])
        print(f"starting list of {len(selection)} keywords -> {project.keywords}")
        for row in selection:
            print("  ", row["keyword"])
    print("\nAgent: curate keywords.csv now - drop terms that are too generic or off-topic, add\n"
          "concepts the documents rely on but the counts missed, keep it within max_keywords.")


if __name__ == "__main__":
    main()
