"""Step 2 - convert the main documents (PDF / Markdown / text) to Markdown.

Writes, per document, <name>.md (body) and <name>.references.txt (one
citation per line) to intermediate-data/processed-main-docs/.
"""
import _bootstrap  # noqa: F401
from modules.config import project_from_args, write_csv_rows
from modules.docs import process_document
from modules.textutil import han_ratio


def main():
    project, _ = project_from_args(__doc__)
    files = sorted(p for p in project.main_docs.iterdir() if p.is_file() and not p.name.startswith("."))
    if not files:
        raise SystemExit(f"No files in {project.main_docs}. Add at least one PDF or .md main document.")
    project.processed_docs.mkdir(parents=True, exist_ok=True)
    for old in project.processed_docs.glob("*"):
        old.unlink()
    manifest = []
    for path in files:
        document = process_document(path)
        if document is None:
            print(f"skipped  {path.name} (unsupported type; use .pdf, .md or .txt)")
            continue
        (project.processed_docs / f"{document['name']}.md").write_text(
            f"# {document['name']}\n\n{document['body']}\n", encoding="utf-8")
        (project.processed_docs / f"{document['name']}.references.txt").write_text(
            "\n".join(document["reference_entries"]) + "\n", encoding="utf-8")
        if han_ratio(document["body"][:20000]) >= 0.5:
            document["notes"].append("mostly_chinese (Crossref search is English-centred; add English keywords)")
        manifest.append({"source": document["source"], "pages": document["pages"],
                         "body_chars": len(document["body"]),
                         "reference_entries": len(document["reference_entries"]),
                         "notes": "; ".join(document["notes"])})
        print(f"ok       {path.name}: {len(document['body']):,} chars, "
              f"{len(document['reference_entries'])} references"
              + (f"  [{'; '.join(document['notes'])}]" if document["notes"] else ""))
    write_csv_rows(project.processed_docs / "manifest.csv", manifest)
    project.update_stats(main_docs=len(manifest),
                         main_doc_reference_entries=sum(m["reference_entries"] for m in manifest))
    print(f"\n{len(manifest)} document(s) -> {project.processed_docs}")


if __name__ == "__main__":
    main()
