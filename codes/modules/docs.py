"""Main documents: convert PDF / Markdown to clean Markdown and pull out the
reference list."""
import re
from pathlib import Path

from .textutil import clean_text

REFERENCE_HEADINGS = (
    r"references?(\s+cited)?|reference\s+list|bibliography|works\s+cited|literature\s+cited|"
    r"參考文獻|参考文献|參考書目|引用文獻"
)
_HEADING_LINE = re.compile(rf"^\s*(#+\s*)?[*_]*\s*(\d+\.?\s*)?({REFERENCE_HEADINGS})\s*[*_]*\s*:?\s*$", re.I)
_AFTER_REFS = re.compile(r"^\s*(#+\s*)?[*_]*\s*(appendix|appendices|supplementary|online\s+appendix|tables?\s+and\s+figures|附錄)\b", re.I)
_YEAR = re.compile(r"\b(1[5-9]\d\d|20\d\d)[a-z]?\b")
_ENTRY_START = re.compile(r"^(\[?\d{1,3}[\].)]\s+)?[A-ZÀ-Ý一-鿿][^\n]{0,110}?\(?\b(1[5-9]\d\d|20\d\d)[a-z]?\)?")
# "Surname, Given (2001)" / "Surname AB (2001)": certainly a new entry, even when the
# previous one does not end with a full stop.
_STRONG_START = re.compile(r"^[A-ZÀ-Ý][\w'’\-]+(,\s+[A-ZÀ-Ý]|\s+[A-Z]{1,3}\b)[^\n]{0,100}?\((1[5-9]\d\d|20\d\d)[a-z]?\)")
_NUMBERED = re.compile(r"^\s*\[?\d{1,3}[\].)]\s+")
_MD_LINK = re.compile(r"\[([^\]]+)\]\((?:[^)]*)\)")

MIN_CHARS_PER_PAGE = 400
MIN_BODY_CHARS = 1000


def pdf_to_text(path):
    """Text of each page via pypdf. Returns (pages, text)."""
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        try:
            pages.append(clean_text(page.extract_text() or ""))
        except Exception:
            pages.append("")
    return len(pages), "\n\n".join(pages)


def strip_markdown(text):
    """Markdown source -> plain prose (keeps the words of links and emphasis)."""
    text = re.sub(r"~~.*?~~", " ", text, flags=re.S)           # struck-through drafts
    text = _MD_LINK.sub(r"\1", text)
    text = re.sub(r"^\s*\[\*{0,2}[^\]]*\t\d+\*{0,2}\]\s*$", " ", text, flags=re.M)  # TOC lines
    text = re.sub(r"[*_`]{1,3}", "", text)
    text = re.sub(r"^\s*#+\s*", "", text, flags=re.M)
    return text


def split_references(text):
    """Split a document into (body, references_text).

    The reference list starts at the last standalone heading such as
    'References' in the second half of the document and ends at an appendix
    heading, if any."""
    lines = text.splitlines()
    start = None
    for index in range(len(lines) - 1, -1, -1):
        if _HEADING_LINE.match(lines[index]):
            if index >= len(lines) * 0.3:
                start = index
            break
    if start is None:
        return text, ""
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if _AFTER_REFS.match(lines[index]):
            end = index
            break
    body = "\n".join(lines[:start] + lines[end:])
    return body, "\n".join(lines[start + 1:end])


def _looks_complete(entry):
    entry = entry.rstrip()
    return not entry or entry[-1] in ".)]" or bool(re.search(r"(doi\.org/\S+|https?://\S+)$", entry))


def split_reference_entries(references_text):
    """Reference section -> list of single-citation strings."""
    text = _MD_LINK.sub(r"\1", references_text)
    text = re.sub(r"[*_`]{1,3}", "", text)
    paragraphs = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", text)]
    paragraphs = [p for p in paragraphs if p]
    with_year = [p for p in paragraphs if _YEAR.search(p)]
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(paragraphs) >= 5 and len(with_year) >= 0.6 * len(paragraphs) and len(paragraphs) >= 0.3 * len(lines):
        entries = paragraphs  # one citation per paragraph (typical Markdown export)
    else:
        numbered = sum(bool(_NUMBERED.match(line)) for line in lines)
        use_numbers = numbered >= max(3, 0.15 * len(lines))
        entries, current = [], ""
        for line in lines:
            starts = bool(_NUMBERED.match(line)) if use_numbers else (
                bool(_STRONG_START.match(line))
                or (bool(_ENTRY_START.match(line)) and _looks_complete(current)))
            if starts and current:
                entries.append(current)
                current = line
            else:
                joiner = "" if current.endswith("-") and line[:1].islower() else " "
                current = (current.rstrip("-") if joiner == "" else current) + joiner + line if current else line
        if current:
            entries.append(current)
    cleaned = []
    for entry in entries:
        entry = _NUMBERED.sub("", re.sub(r"\s+", " ", entry)).strip()
        if is_citation(entry):
            cleaned.append(entry)
    return cleaned


def is_citation(entry):
    """Filter out page headers, footnotes and other debris."""
    if not 30 <= len(entry) <= 700:
        return False
    if not _YEAR.search(entry):
        return False
    letters = sum(ch.isalpha() for ch in entry)
    return letters / len(entry) >= 0.5


def process_document(path):
    """One input file -> dict with body text, reference entries and quality notes."""
    path = Path(path)
    suffix = path.suffix.lower()
    notes = []
    if suffix == ".pdf":
        pages, raw = pdf_to_text(path)
        if pages and len(raw) / pages < MIN_CHARS_PER_PAGE:
            notes.append("low_text_per_page (scanned PDF? consider OCR)")
    elif suffix in (".md", ".markdown", ".txt"):
        raw = clean_text(path.read_text(encoding="utf-8-sig", errors="replace"))
        pages = 0
    else:
        return None
    body, references_text = split_references(raw)
    if suffix != ".pdf":
        body = strip_markdown(body)
    body = re.sub(r"[ \t]+", " ", body)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    if len(body) < MIN_BODY_CHARS:
        notes.append("very_short_body")
    entries = split_reference_entries(references_text) if references_text else []
    if not references_text:
        notes.append("no_reference_section_found")
    return {"name": path.stem, "source": path.name, "pages": pages, "body": body,
            "reference_entries": entries, "notes": notes}
