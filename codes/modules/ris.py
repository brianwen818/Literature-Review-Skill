"""RIS export (imports directly into Zotero and other reference managers)."""

RIS_TYPE = {
    "journal-article": "JOUR", "book": "BOOK", "monograph": "BOOK", "edited-book": "BOOK",
    "reference-book": "BOOK", "book-chapter": "CHAP", "book-section": "CHAP", "book-part": "CHAP",
    "posted-content": "UNPB", "dissertation": "THES", "report": "RPRT",
    "proceedings-article": "CPAPER", "dataset": "DATA", "unknown": "GEN",
}


def _name(person):
    if person.get("family"):
        return f"{person['family']}, {person.get('given', '')}".rstrip(", ")
    return person.get("name", "")


def to_ris(record, keywords=(), note=""):
    """One bibliographic record (see crossref.parse_item) -> RIS lines."""
    ris_type = RIS_TYPE.get(record.get("type", ""), "JOUR")
    lines = [("TY", ris_type)]
    for person in record.get("authors", []):
        lines.append(("AU", _name(person)))
    if not record.get("authors") and record.get("authors_str"):
        lines.append(("AU", record["authors_str"]))
    for person in record.get("editors", []):
        lines.append(("A2", _name(person)))
    lines.append(("TI", record.get("title", "")))
    container = record.get("journal", "")
    if container:
        lines.append(("T2" if ris_type != "JOUR" else "JO", container))
    pages = str(record.get("pages", "") or "")
    start, _, end = pages.partition("-")
    for tag, value in (("PY", record.get("year", "")), ("VL", record.get("volume", "")),
                       ("IS", record.get("issue", "")), ("SP", start.strip()), ("EP", end.strip("- ")),
                       ("PB", record.get("publisher", "") if ris_type != "JOUR" else ""),
                       ("DO", record.get("doi", "")), ("UR", record.get("url", "")),
                       ("AB", record.get("abstract", ""))):
        if value:
            lines.append((tag, str(value)))
    for keyword in keywords:
        lines.append(("KW", keyword))
    if note:
        lines.append(("N1", note))
    lines.append(("ER", ""))
    return "\r\n".join(f"{tag}  - {value}" for tag, value in lines if tag == "ER" or value)


def write_ris(path, entries):
    """entries: list of RIS strings."""
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write("\r\n\r\n".join(entries) + "\r\n")
