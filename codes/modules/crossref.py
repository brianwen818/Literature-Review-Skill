"""Crossref REST client: polite rate limiting, journal search, citation lookup.

Rules carried over from the prototypes (each was learned the hard way):
- Stay at 8 requests/s with 3 workers; above ~10/s Crossref throttles
  silently and returns empty results instead of an error.
- respect_retry_after_header must stay False: the server has returned
  Retry-After values of many hours, which urllib3 would obey literally.
- /works/{doi} does not accept `select`; list endpoints do.
- '&' and other punctuation in a query string returns nothing.
- Unknown DOIs are skipped silently in batch lookups, so compare sent vs returned.
"""
import html
import math
import re
import threading
import time
from collections import Counter

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .textutil import clean_text, noise_reason, normalize_doi, strip_tags, title_tokens

BOOK_TYPES = {"book", "monograph", "edited-book", "reference-book"}

API = "https://api.crossref.org"
RATE_LIMIT_PER_SEC = 8
MAX_WORKERS = 3
MATCH_MIN_SCORE = 70.0
MATCH_MIN_TITLE_OVERLAP = 0.45
MATCH_MIN_TITLE_TOKENS = 3
DOI_BATCH = 40

SELECT_FIELDS = (
    "DOI,title,subtitle,container-title,ISSN,type,issued,author,editor,abstract,"
    "volume,issue,page,publisher,reference,references-count,is-referenced-by-count,URL,score"
)


class Crossref:
    def __init__(self, mailto=""):
        self.mailto = mailto or ""
        self.status_counts = Counter()
        self._lock = threading.Lock()
        self._next_slot = 0.0
        self.session = requests.Session()
        retry = Retry(
            total=5, backoff_factor=1.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",), respect_retry_after_header=False,
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry, pool_maxsize=MAX_WORKERS * 2))
        agent = "lit-review-automation/1.0"
        if self.mailto:
            agent += f" (mailto:{self.mailto})"
        self.session.headers["User-Agent"] = agent

    def _wait(self):
        with self._lock:
            now = time.monotonic()
            slot = max(now, self._next_slot)
            self._next_slot = slot + 1.0 / RATE_LIMIT_PER_SEC
        if slot > now:
            time.sleep(slot - now)

    def get(self, path, params=None):
        """GET and return the `message` object, or None on 404 / failure."""
        params = dict(params or {})
        if self.mailto:
            params["mailto"] = self.mailto
        self._wait()
        try:
            response = self.session.get(API + path, params=params, timeout=60)
        except requests.RequestException:
            self.status_counts["error"] += 1
            return None
        self.status_counts[response.status_code] += 1
        if response.status_code != 200:
            return None
        try:
            return response.json().get("message")
        except ValueError:
            self.status_counts["bad_json"] += 1
            return None

    # ----- journals -----

    def journal(self, issn):
        message = self.get(f"/journals/{issn}")
        if not message:
            return None
        return {
            "title": message.get("title", ""),
            "publisher": message.get("publisher", ""),
            "issns": message.get("ISSN", []),
            "total_dois": (message.get("counts") or {}).get("total-dois", 0),
        }

    def find_journal_by_name(self, name):
        """Exact (normalised) title match; the journal with most DOIs wins."""
        message = self.get("/journals", {"query": clean_query(name), "rows": 20})
        target = normalize_journal_name(name)
        best = None
        for item in (message or {}).get("items", []):
            if normalize_journal_name(item.get("title", "")) != target or not item.get("ISSN"):
                continue
            total = (item.get("counts") or {}).get("total-dois", 0)
            if best is None or total > best["total_dois"]:
                best = {"title": item["title"], "publisher": item.get("publisher", ""),
                        "issns": item["ISSN"], "total_dois": total}
        return best

    def search_journal(self, issn, keyword, rows=20, year_from=None, year_to=None):
        """Keyword search inside one journal. Returns (total_results, items) or None."""
        filters = ["type:journal-article"]
        if year_from:
            filters.append(f"from-pub-date:{int(year_from)}-01-01")
        if year_to:
            filters.append(f"until-pub-date:{int(year_to)}-12-31")
        message = self.get(f"/journals/{issn}/works", {
            "query.bibliographic": clean_query(keyword),
            "filter": ",".join(filters),
            "sort": "relevance", "rows": rows, "select": SELECT_FIELDS,
        })
        if message is None:
            return None
        return message.get("total-results", 0), [parse_item(it) for it in message.get("items", [])]

    # ----- works -----

    def works_by_dois(self, dois):
        """Metadata (with reference lists) for many DOIs. Returns {doi: record}."""
        wanted = [d for d in dict.fromkeys(normalize_doi(d) for d in dois) if d]
        found = {}
        for start in range(0, len(wanted), DOI_BATCH):
            batch = wanted[start:start + DOI_BATCH]
            message = self.get("/works", {
                "filter": ",".join(f"doi:{d}" for d in batch),
                "rows": len(batch), "select": SELECT_FIELDS,
            })
            for item in (message or {}).get("items", []):
                record = parse_item(item)
                found[record["doi"]] = record
        return found

    def resolve_citation(self, text):
        """Free-text citation -> best Crossref match, accepted only when both the
        Crossref score and the title overlap clear their thresholds."""
        text = clean_text(text).strip()
        if len(text) < 15:
            return {"status": "too_short"}
        message = self.get("/works", {
            "query.bibliographic": clean_query(text)[:500], "rows": 1, "select": SELECT_FIELDS,
        })
        if message is None:
            return {"status": "error"}       # request failed; worth retrying
        items = message.get("items", [])
        if not items:
            return {"status": "no_match"}
        record = parse_item(items[0])
        return match_result(text, record, float(items[0].get("score") or 0))


def match_result(text, record, score):
    """Decide whether a Crossref hit really is the cited work.

    Score and title overlap (the prototypes' two checks) are not enough: a
    review of a book repeats the book's title and passes both. The author and
    year checks reject those. Kept separate from the request so cached hits
    can be re-judged without asking Crossref again."""
    tokens = title_tokens(record["title"])
    source = set(title_tokens(text))
    overlap = sum(t in source for t in tokens) / len(tokens) if tokens else 0.0
    failed = []
    if score < MATCH_MIN_SCORE:
        failed.append("score")
    if overlap < MATCH_MIN_TITLE_OVERLAP or len(tokens) < MATCH_MIN_TITLE_TOKENS:
        failed.append("title")
    if noise_reason(record["title"]):
        failed.append("is_review")
    if not author_in_citation(record, text):
        failed.append("author")
    if not year_in_citation(record, text):
        failed.append("year")
    return {"status": "low_confidence" if failed else "resolved", "failed_checks": ";".join(failed),
            "score": round(score, 1), "title_overlap": round(overlap, 2), "record": record}


def author_in_citation(record, text):
    """The matched work's first author (or editor) must be named in the citation."""
    people = record["authors"] or record["editors"]
    if not people:
        return False
    name = people[0].get("family") or people[0].get("name") or ""
    wanted = title_tokens(name)
    source = set(title_tokens(text))
    return bool(wanted) and all(token in source for token in wanted)


def year_in_citation(record, text):
    """The matched work's year must fit a year in the citation: up to three
    years earlier (Crossref dates an article by its online-first release, while
    citations give the print year) or one year later. Book reviews, which come
    out after the book, fall outside this window or fail the author check."""
    if not record["year"]:
        return True
    cited = [int(y) for y in re.findall(r"\b(1[5-9]\d\d|20\d\d)[a-z]?\b", text)]
    return not cited or any(-3 <= int(record["year"]) - year <= 1 for year in cited)


def consistent_match(record, authors, is_book):
    """Extra guard when a bare reference (author, year, title) was resolved:
    the first author's surname must be among the record's authors, and a book
    must resolve to a book - not to an article that merely shares its title."""
    surname = re.split(r"[,\s]", (authors or "").strip())[0].lower()
    families = {(p.get("family") or p.get("name") or "").lower() for p in record["authors"] + record["editors"]}
    if surname and families and not any(surname in family for family in families):
        return False
    return not is_book or record["type"] in BOOK_TYPES


def clean_query(text):
    """Crossref returns nothing for queries containing '&' and similar marks."""
    text = re.sub(r"[^\w\s\-']", " ", clean_text(text), flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def normalize_journal_name(name):
    name = re.sub(r"&", " and ", (name or "").lower())
    name = re.sub(r"^the\s+", "", name.strip())
    return re.sub(r"[^a-z0-9]+", " ", name).strip()


def _first(value):
    if isinstance(value, list):
        return value[0] if value else ""
    return value or ""


def _people(entries):
    people = []
    for person in entries or []:
        if person.get("family"):
            people.append({"family": clean_text(person["family"]).strip(),
                           "given": clean_text(person.get("given", "")).strip()})
        elif person.get("name"):
            people.append({"name": clean_text(person["name"]).strip()})
    return people


def people_to_string(people, limit=6):
    names = []
    for person in people[:limit]:
        if person.get("family"):
            names.append(f"{person['family']}, {person['given']}".rstrip(", "))
        else:
            names.append(person.get("name", ""))
    if len(people) > limit:
        names.append("et al.")
    return "; ".join(n for n in names if n)


def parse_reference(ref):
    """Compact form of one Crossref reference entry."""
    doi = normalize_doi(ref.get("DOI"))
    if doi:
        return {"doi": doi}
    compact = {}
    for source, target in (("author", "author"), ("year", "year"), ("article-title", "article_title"),
                           ("volume-title", "volume_title"), ("journal-title", "journal_title"),
                           ("series-title", "series_title"), ("unstructured", "unstructured")):
        value = clean_text(ref.get(source, "")).strip()
        if value:
            compact[target] = value[:400]
    return compact


def parse_item(item):
    """Crossref work -> flat record used throughout the pipeline."""
    title = clean_text(_first(item.get("title"))).strip()
    subtitle = clean_text(_first(item.get("subtitle"))).strip()
    if subtitle and subtitle.lower() not in title.lower():
        title = f"{title}: {subtitle}"
    year = ""
    parts = (item.get("issued") or {}).get("date-parts") or [[]]
    if parts and parts[0] and parts[0][0]:
        year = str(parts[0][0])
    authors = _people(item.get("author"))
    references = [parse_reference(r) for r in item.get("reference", [])]
    return {
        "doi": normalize_doi(item.get("DOI")),
        "title": re.sub(r"\s+", " ", strip_title_markup(title)),
        "journal": clean_text(_first(item.get("container-title"))).strip(),
        "issns": item.get("ISSN", []),
        "type": item.get("type", ""),
        "year": year,
        "authors": authors,
        "editors": _people(item.get("editor")),
        "authors_str": people_to_string(authors),
        "abstract": strip_tags(clean_text(item.get("abstract", ""))),
        "volume": item.get("volume", ""),
        "issue": item.get("issue", ""),
        "pages": item.get("page", ""),
        "publisher": clean_text(item.get("publisher", "")).strip(),
        "references": [r for r in references if r],
        "references_count": item.get("references-count", 0) or 0,
        "cited_by_count": item.get("is-referenced-by-count", 0) or 0,
        "url": item.get("URL", ""),
    }


def strip_title_markup(title):
    return html.unescape(re.sub(r"<[^>]+>", "", title or "")).strip()


def coupling_denominator(n_refs):
    return math.sqrt(max(int(n_refs or 0), 1))
