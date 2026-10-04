"""Citation snowballing: works cited by the most relevant articles and by the
seeds. This is how books and articles outside the journal list are found."""
import re
from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from .scoring import pct_rank
from .textutil import noise_reason, normalize_title, short_hash

_YEAR = re.compile(r"\b(1[5-9]\d\d|20\d\d)\b")


def reference_key(ref):
    """Grouping key and display fields for a reference without a DOI."""
    title = ref.get("volume_title") or ref.get("article_title") or ref.get("series_title") or ""
    author = re.split(r"[,\s]", (ref.get("author") or "").strip())[0].lower()
    year = ref.get("year", "")
    if title:
        key = f"{author}|{' '.join(normalize_title(title).split()[:6])}"
    else:
        text = ref.get("unstructured", "")
        if len(text) < 25:
            return None
        year = year or (_YEAR.search(text).group(0) if _YEAR.search(text) else "")
        key = "u|" + " ".join(normalize_title(text).split()[:10])
    return key, {"title": title, "author": ref.get("author", ""), "year": year,
                 "container": ref.get("journal_title", ""), "raw": ref.get("unstructured", ""),
                 "is_book": bool(ref.get("volume_title")) and not ref.get("article_title")}


def collect(sources):
    """sources: list of (source_id, source_label, references).
    Returns {doi: set(source ids)}, {key: {'sources': set, 'info': dict}}, {source_id: label}."""
    by_doi = defaultdict(set)
    by_key = {}
    labels = {}
    for source_id, label, references in sources:
        labels[source_id] = label
        for ref in references:
            if ref.get("doi"):
                by_doi[ref["doi"]].add(source_id)
                continue
            keyed = reference_key(ref)
            if keyed is None:
                continue
            key, info = keyed
            entry = by_key.setdefault(key, {"sources": set(), "info": info})
            entry["sources"].add(source_id)
            if len(info.get("raw", "")) > len(entry["info"].get("raw", "")) or (info["title"] and not entry["info"]["title"]):
                entry["info"] = {**entry["info"], **{k: v for k, v in info.items() if v}}
    return by_doi, by_key, labels


def build_rows(by_doi, by_key, labels, records, min_citing, skip_dois, skip_titles, listed_issns):
    """Turn grouped references into candidate rows (unscored)."""
    rows = []
    for doi, sources in by_doi.items():
        if len(sources) < min_citing or doi in skip_dois:
            continue
        record = records.get(doi)
        if record is None:
            continue  # DOI unknown to Crossref (other registrars); cannot describe it
        if noise_reason(record["title"]) or normalize_title(record["title"]) in skip_titles:
            continue
        rows.append({
            "item_id": doi, "doi": doi, "title": record["title"], "authors": record["authors_str"],
            "year": record["year"], "container": record["journal"] or record["publisher"],
            "type": record["type"], "abstract": record["abstract"],
            "in_journal_list": bool(set(record["issns"]) & listed_issns),
            "n_citing_sources": len(sources),
            "cited_by": "; ".join(sorted(labels[s] for s in sources)[:6]),
            "raw_reference": "",
        })
    for key, entry in by_key.items():
        if len(entry["sources"]) < min_citing:
            continue
        info = entry["info"]
        title = info["title"] or info["raw"]
        if normalize_title(info["title"]) in skip_titles and info["title"]:
            continue
        rows.append({
            "item_id": "ref:" + short_hash(key), "doi": "", "title": title, "authors": info["author"],
            "year": info["year"], "container": info["container"],
            "type": "book" if info["is_book"] else "unknown", "abstract": "",
            "in_journal_list": False, "n_citing_sources": len(entry["sources"]),
            "cited_by": "; ".join(sorted(labels[s] for s in entry["sources"])[:6]),
            "raw_reference": info["raw"],
        })
    return rows


def score(rows, queries):
    """snowball_score = 0.6 x percentile(citing sources) + 0.4 x percentile(tf-idf);
    items without usable text are ranked on citing sources alone."""
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    texts = (frame["title"].fillna("") + ". " + frame["abstract"].fillna("")).tolist()
    queries = [text for _, text in queries if text and text.strip()]
    frame["tfidf"] = np.nan
    if queries and len(frame) >= 5:
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english")
        matrix = vectorizer.fit_transform(texts)
        sims = (matrix @ vectorizer.transform(queries).T).toarray().max(axis=1)
        frame["tfidf"] = np.where(frame["doi"] != "", sims, np.nan)
    citing = pct_rank(frame["n_citing_sources"])
    text = pct_rank(frame["tfidf"])
    frame["snowball_score"] = np.where(text.notna(), 0.6 * citing + 0.4 * text, citing).round(4)
    frame["tfidf"] = frame["tfidf"].round(4)
    return frame.sort_values(["snowball_score", "n_citing_sources"], ascending=False).reset_index(drop=True)
