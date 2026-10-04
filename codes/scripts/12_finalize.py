"""Step 12 - read the user's marks and produce the final files.

Without --upload:  outputs/zotero-added.xlsx + outputs/zotero-import.ris
With    --upload:  the marked items are added to the Zotero library (records
                   only, no PDFs), then outputs/zotero-added.xlsx +
                   outputs/zotero-export.rdf (exported back from Zotero)

    --dry-run   with --upload: show what would be created, write nothing to Zotero
"""
from datetime import datetime

import _bootstrap  # noqa: F401
from modules import outputs
from modules.config import load_env, mask, project_from_args, write_csv_rows
from modules.crossref import Crossref, consistent_match
from modules.ris import to_ris, write_ris
from modules.textutil import normalize_title


def options(parser):
    parser.add_argument("--upload", action="store_true", help="add the marked items to Zotero")
    parser.add_argument("--dry-run", action="store_true", help="with --upload: do not write to Zotero")


def minimal_record(row):
    """Record built from the sheet alone, for works Crossref does not know."""
    return {"doi": str(row.get("doi-link", "")).replace("https://doi.org/", ""),
            "title": str(row.get("title", "")), "journal": str(row.get("journal") or row.get("container") or ""),
            "year": str(row.get("year", "")), "authors": [], "editors": [],
            "authors_str": str(row.get("authors", "")), "type": str(row.get("type") or "unknown"),
            "abstract": "", "volume": "", "issue": "", "pages": "", "publisher": "", "url": "", "issns": []}


def collect_records(selected, crossref):
    """Full bibliographic records for the marked rows."""
    dois = [str(r["item_id"]) for r in selected if not str(r["item_id"]).startswith("ref:")]
    found = crossref.works_by_dois(dois)
    result = []
    for row in selected:
        item_id = str(row["item_id"])
        record = found.get(item_id)
        if record is None and item_id.startswith("ref:"):
            query = str(row.get("raw_reference") or "") or " ".join(
                str(row.get(k, "")) for k in ("authors", "year", "title"))
            match = crossref.resolve_citation(query)
            if match["status"] == "resolved" and consistent_match(
                    match["record"], str(row.get("authors", "")), str(row.get("type", "")) == "book"):
                record = match["record"]
        result.append((row, record or minimal_record(row)))
    return result


def main():
    project, args = project_from_args(__doc__, options)
    config = project.config
    link_column = config["library_link_column"]
    shortlist_path = project.require(project.outputs / "shortlist.xlsx", "run 11_build_outputs.py first")
    lock = outputs.excel_lock_file(shortlist_path)
    if lock:
        raise SystemExit(f"{shortlist_path.name} seems to be open in Excel ({lock.name} exists).\n"
                         "  -> save and close it, then run this step again.")
    selected, counts, odd = outputs.read_marks(shortlist_path, ["shortlist", "snowball"])
    for name, count in counts.items():
        print(f"{name}: {count['marked_yes']} of {count['rows']} marked yes")
    if odd:
        print("Unrecognised marks (treated as no):", "; ".join(odd[:10]))
    if not selected:
        raise SystemExit(f"Nothing is marked yes in the '{outputs.MARK_COLUMN}' column. "
                         "Mark the articles to keep, save, close the file, and run again.")

    crossref = Crossref(config["crossref_mailto"])
    pairs = collect_records(selected, crossref)
    keys = {}
    if args.upload:
        keys = upload(project, config, pairs, args.dry_run)

    final_rows = []
    for row, record in pairs:
        final_rows.append({
            "title": record["title"], "authors": record.get("authors_str") or row.get("authors", ""),
            "year": record["year"], "journal": record["journal"], "type": record["type"],
            "doi": record["doi"], "doi-link": outputs.doi_link(record["doi"]),
            link_column: row.get(link_column, ""), "agent_relevance": row.get("agent_relevance", ""),
            "agent_reason": row.get("agent_reason", ""), "theme": row.get("theme", ""),
            "source_sheet": row["sheet"], "zotero_key": keys.get(str(row["item_id"]), ""),
        })
    columns = ["title", "authors", "year", "journal", "type", "doi", "doi-link", link_column,
               "agent_relevance", "agent_reason", "theme", "source_sheet"]
    if keys:
        columns.append("zotero_key")
    outputs.write_workbook(project.outputs / "zotero-added.xlsx", [
        {"name": "zotero-added", "columns": columns, "rows": final_rows, "links": ("doi-link", link_column)}])
    print(f"zotero-added.xlsx: {len(final_rows)} rows")

    if not args.upload:
        tag = config["zotero"]["tag"]
        entries = [to_ris(record, keywords=[tag] + ([str(row["theme"])] if row.get("theme") else []),
                          note=str(row.get("agent_reason", ""))) for row, record in pairs]
        write_ris(project.outputs / "zotero-import.ris", entries)
        print("zotero-import.ris: import it in Zotero with File > Import")
    project.update_stats(marked_yes=len(selected), uploaded_to_zotero=len(keys))
    print(f"-> {project.outputs}")


def upload(project, config, pairs, dry_run):
    from modules.zotero import Zotero, ZoteroError, settings_from_env

    try:
        settings = settings_from_env(load_env(project.env_path))
    except ZoteroError as error:
        raise SystemExit(f"{error}\n  -> see {project.env_path.parent / 'README.md'}")
    client = Zotero(**settings)
    print(f"Zotero {settings['library_type']} library {settings['library_id']}, key {mask(settings['api_key'])}")
    try:
        can_read, can_write = client.can_write()
        if not can_read or not can_write:
            raise SystemExit("The API key lacks read/write access to this library. "
                             "Create a key with write permission (see zotero-info/README.md).")
        dois, titles, ids = client.existing()
        run_tag = f"{config['zotero']['tag']}:{datetime.now():%Y%m%d-%H%M}"
        tags = [config["zotero"]["tag"], run_tag]
        keys, new_items, new_ids, log = {}, [], [], []
        collection = None
        for row, record in pairs:
            item_id = str(row["item_id"])
            existing_key = (ids.get(item_id) or dois.get(record["doi"]) or
                            titles.get(normalize_title(record["title"])))
            if existing_key:
                keys[item_id] = existing_key
                log.append({"item_id": item_id, "title": record["title"], "result": "already_in_library",
                            "zotero_key": existing_key})
                continue
            if collection is None and not dry_run:
                collection = client.ensure_collection(config["zotero"]["collection"])
            extra = [f"relevance: {row.get('agent_relevance', '')}"] if row.get("agent_relevance") else []
            new_items.append(client.build_item(record, item_id, collection or "", tags, extra))
            new_ids.append((item_id, record["title"]))
        print(f"{len(keys)} already in the library, {len(new_items)} to add")
        if dry_run:
            for item_id, title in new_ids:
                print(f"  would add: {title[:90]}")
            return {}
        created, failed = client.create_items(new_items)
        for index, (item_id, title) in enumerate(new_ids):
            if index in created:
                keys[item_id] = created[index]
            log.append({"item_id": item_id, "title": title,
                        "result": "created" if index in created else f"failed: {failed.get(index, 'unknown')}",
                        "zotero_key": created.get(index, "")})
        write_csv_rows(project.outputs / "zotero-upload-log.csv", log,
                       ["item_id", "title", "result", "zotero_key"])
        print(f"created {len(created)}, failed {len(failed)}  (log: zotero-upload-log.csv)")
        if created:
            print(f"To undo this batch, select the tag '{run_tag}' in Zotero and delete its items.")
        if keys:
            rdf = client.export_rdf(list(dict.fromkeys(keys.values())))
            (project.outputs / "zotero-export.rdf").write_text(rdf, encoding="utf-8")
            print(f"zotero-export.rdf: {len(set(keys.values()))} items exported from Zotero")
        return keys
    except ZoteroError as error:
        raise SystemExit(f"Zotero: {error}")


if __name__ == "__main__":
    main()
