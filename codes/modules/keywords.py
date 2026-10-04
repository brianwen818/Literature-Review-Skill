"""Candidate search keywords from the main documents and seed references.

The script only proposes; the agent curates the list before any search runs."""
import math
import re
from collections import Counter

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

# Words that are frequent in any academic text and useless as search terms.
GENERIC_WORDS = {
    "study", "studies", "paper", "article", "research", "analysis", "analyses", "result", "results",
    "finding", "findings", "data", "model", "models", "effect", "effects", "table", "figure",
    "section", "approach", "literature", "evidence", "theory", "hypothesis", "hypotheses",
    "variable", "variables", "sample", "author", "authors", "journal", "press", "university",
    "vol", "pp", "et", "al", "eds", "ed", "doi", "http", "https", "www", "org", "online",
    "use", "used", "using", "based", "new", "also", "however", "thus", "therefore", "may",
    "one", "two", "three", "first", "second", "third", "case", "cases", "example", "level",
    "levels", "number", "percent", "year", "years", "time", "significant", "significantly",
    "likely", "important", "different", "general", "specific", "large", "small", "high", "low",
    "show", "shows", "shown", "suggest", "suggests", "argue", "argues", "find", "finds",
    "note", "see", "among", "across", "within", "whether", "rather", "often", "many", "much",
}
# scikit-learn's stop list contains ordinary content words; several of them are
# core vocabulary in the social sciences ("party system", "interest group").
NOT_STOPWORDS = {"system", "interest", "bill", "fire", "mill", "computer", "cry", "side", "part",
                 "front", "back", "top", "bottom", "name", "amount", "detail", "move", "call",
                 "fill", "full", "empty", "thick", "thin", "serious", "sincere"}
STOPWORDS = (set(ENGLISH_STOP_WORDS) - NOT_STOPWORDS) | GENERIC_WORDS
_SEGMENT_SPLIT = re.compile(r"[^A-Za-z\-'\s]+")
_WORD = re.compile(r"[a-z][a-z\-']{1,}")
MAX_NGRAM = 3


def _singular(word):
    """Very light plural folding so 'party'/'parties' count together."""
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and word.endswith("ses"):
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]
    return word


def ngrams_of(text):
    """All 1-3 grams of a text; never crossing punctuation, never edged by a stopword."""
    grams = []
    for segment in _SEGMENT_SPLIT.split(text or ""):
        words = [w.strip("-'") for w in _WORD.findall(segment.lower())]
        words = [w for w in words if len(w) >= 3]
        for size in range(1, MAX_NGRAM + 1):
            for start in range(len(words) - size + 1):
                gram = words[start:start + size]
                if gram[0] in STOPWORDS or gram[-1] in STOPWORDS:
                    continue
                if size == 3 and gram[1] in GENERIC_WORDS:
                    continue
                grams.append(" ".join(_singular(w) if i == size - 1 else w for i, w in enumerate(gram)))
    return grams


def keyword_candidates(main_texts, seed_texts, per_size=40):
    """Rank n-grams. Returns rows sorted by n-gram size, then score.

    score = frequency in the main documents (dampened) weighted by how many
    separate documents (main documents and seeds) use the term."""
    main_counts = Counter()
    doc_freq = Counter()
    for text in main_texts:
        grams = ngrams_of(text)
        main_counts.update(grams)
        doc_freq.update(set(grams))
    for text in seed_texts:
        doc_freq.update(set(ngrams_of(text)))
    seed_only = Counter()
    if not main_counts:  # no main-document text: fall back to the seeds alone
        for text in seed_texts:
            seed_only.update(ngrams_of(text))
        main_counts = seed_only
    rows = []
    for gram, count in main_counts.items():
        size = gram.count(" ") + 1
        if count < 2 and doc_freq[gram] < 2:
            continue
        score = math.log1p(count) * (1 + math.log1p(doc_freq[gram]))
        rows.append({"keyword": gram, "ngram": size, "main_doc_count": count,
                     "doc_frequency": doc_freq[gram], "score": round(score, 3), "flag": ""})
    best = []
    for size in range(1, MAX_NGRAM + 1):
        ranked = sorted((r for r in rows if r["ngram"] == size), key=lambda r: -r["score"])
        best.extend(ranked[:per_size])
    _flag(best)
    return sorted(best, key=lambda r: (r["ngram"], -r["score"]))


def _flag(rows):
    """Mark terms that are probably poor search keywords, with the reason."""
    counts = {r["keyword"]: r["main_doc_count"] for r in rows}
    longer = [r["keyword"] for r in rows if r["ngram"] >= 2]
    for row in rows:
        keyword = row["keyword"]
        if row["ngram"] == 1:
            row["flag"] = "generic_unigram"   # single words match far too broadly
            continue
        for other in longer:
            if other != keyword and f" {keyword} " in f" {other} " and counts[other] >= 0.8 * counts[keyword]:
                row["flag"] = f"fragment_of:{other}"
                break


def default_selection(rows, max_keywords):
    """Starting keyword list: best unflagged bigrams and trigrams."""
    usable = sorted((r for r in rows if not r["flag"]), key=lambda r: -r["score"])
    return [{"keyword": r["keyword"], "use": "yes", "source": "auto", "note": ""}
            for r in usable[:max_keywords]]
