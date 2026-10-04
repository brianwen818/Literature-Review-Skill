"""Small text helpers shared by every stage."""
import hashlib
import html
import re
import unicodedata

_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_TAG_RE = re.compile(r"<[^>]+>")
_DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"<>]+", re.I)
_HAN_RE = re.compile(r"[一-鿿]")

# Titles of items that Crossref labels as journal articles but that are not
# research articles. Checked against the lowercased title.
_NOISE_PATTERNS = [
    ("book_review", re.compile(r"^\s*(book\s+reviews?|review\s+essay|reviews?\s*:|review\s+of\b|books?\s+received|book\s+notes?)")),
    ("book_review", re.compile(r"\bbook\s+review\b|,\s*reviewed\s+by\b")),
    # "<Book title>. By <Author>. <City>: <Publisher>, <year>" - how journals title their reviews
    ("book_review", re.compile(r"\.\s*(by|edited by)\s+.{3,100}?\.\s*\(?[^.]{0,60}(press|publishers?|books|routledge|palgrave|springer|macmillan|ashgate|blackwell|elgar)")),
    ("book_review", re.compile(r"\.\s*(by|edited by)\s+.{3,100}?\.\s*[^.:]{2,40}:\s*[^,]{2,60},\s*(1[5-9]|20)\d{2}\b")),
    ("book_review", re.compile(r"\b\d{2,4}\s*pp\.?(\s|,|$)")),
    ("front_matter", re.compile(r"^\s*(front\s+matter|back\s+matter|issue\s+information|table\s+of\s+contents|contents|index|masthead|cover|editorial\s+board|list\s+of\s+reviewers|notes?\s+on\s+contributors?|contributors|acknowledg(e)?ments?(\s+to\s+reviewers)?)\b")),
    ("correction", re.compile(r"^\s*(erratum|corrigendum|correction|retraction|retracted|addendum|expression\s+of\s+concern)\b")),
    ("editorial", re.compile(r"^\s*(editorial|editor'?s?\s+(note|introduction|comment)|from\s+the\s+editors?|in\s+memoriam|obituary|announcements?|call\s+for\s+papers)\b")),
]


def clean_text(text):
    """Drop control characters (NUL truncates CSV fields on read) and tidy spaces."""
    if text is None:
        return ""
    text = _CONTROL_RE.sub(" ", str(text))
    return text.replace("­", "").replace("﻿", "")


def strip_tags(text):
    """Remove JATS/HTML tags from a Crossref abstract."""
    if not text:
        return ""
    text = html.unescape(_TAG_RE.sub(" ", text))
    text = re.sub(r"^\s*abstract\s*[:.]?\s*", "", text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip()


def normalize_doi(doi):
    if not doi or (isinstance(doi, float) and doi != doi):
        return ""
    doi = str(doi).strip().lower()
    doi = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", doi)
    doi = re.sub(r"^doi:\s*", "", doi)
    return doi.rstrip(".,; ")


def find_doi(text):
    """First DOI embedded in a free-text string, normalised, or ''."""
    m = _DOI_RE.search(text or "")
    return normalize_doi(m.group(0)) if m else ""


def normalize_title(title):
    """ASCII-folded, lowercased, punctuation-free title for matching."""
    if not title:
        return ""
    text = unicodedata.normalize("NFKD", str(title))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9一-鿿]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def title_tokens(title):
    return [t for t in normalize_title(title).split() if len(t) > 1]


def han_ratio(text):
    """Share of CJK characters among letters; used to warn about non-English input."""
    letters = [ch for ch in (text or "") if ch.isalpha()]
    if not letters:
        return 0.0
    return len(_HAN_RE.findall("".join(letters))) / len(letters)


def noise_reason(title):
    """Why a title is not a research article ('' when it looks like one)."""
    low = (title or "").strip().lower()
    if not low:
        return "no_title"
    for reason, pattern in _NOISE_PATTERNS:
        if pattern.search(low):
            return reason
    return ""


def short_hash(text, length=12):
    return hashlib.sha1(str(text).encode("utf-8")).hexdigest()[:length]
