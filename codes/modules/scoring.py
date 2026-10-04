"""Relevance scoring of search candidates.

Signals (each turned into a percentile before weighting):
  coupling  citation overlap with the seed references; NaN (no evidence) when
            the publisher does not deposit reference lists - never 0.
  tfidf     wording similarity between title+abstract and the main documents.
  specter   optional semantic similarity (see specter.py).
The composite is the weighted mean of the signals that are available,
re-normalised over those present. Percentiles are then taken separately for
articles with and without an abstract, because both text signals favour
articles that have one."""
from collections import Counter

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from .crossref import coupling_denominator

LEVELS = [(0.95, "Very High"), (0.80, "High"), (0.20, "Normal"), (0.05, "Low"), (0.0, "Very Low")]
MIN_STRATUM = 30


def pct_rank(series):
    """Percentile with average rank for ties, so a large block of identical
    values (e.g. coupling = 0) lands in the middle of its range, not the top."""
    return series.rank(pct=True, method="average")


def add_coupling(frame, references, seed_data, direct_weight):
    """coupling = (direct_weight x seeds cited + references shared with seeds) / sqrt(n_refs)."""
    seed_dois = set(seed_data)
    cited_by_seeds = Counter()
    for data in seed_data.values():
        cited_by_seeds.update(set(data.get("ref_dois", [])))
    n_cites, n_shared, coupling = [], [], []
    for doi, n_refs in zip(frame["doi"], frame["references_count"]):
        ref_dois = {r["doi"] for r in references.get(doi, []) if r.get("doi")}
        if not ref_dois:
            n_cites.append(np.nan), n_shared.append(np.nan), coupling.append(np.nan)
            continue
        own = set(seed_data[doi].get("ref_dois", [])) if doi in seed_data else set()
        cites = len((ref_dois & seed_dois) - {doi})
        # leave-one-out: a seed must not match its own reference list
        shared = sum(1 for d in ref_dois - seed_dois if cited_by_seeds[d] - (d in own) >= 1)
        n_cites.append(cites), n_shared.append(shared)
        coupling.append((direct_weight * cites + shared) / coupling_denominator(n_refs or len(ref_dois)))
    frame["n_cites_seed"], frame["n_shared_refs"], frame["coupling"] = n_cites, n_shared, coupling
    return frame


def candidate_text(frame):
    return (frame["title"].fillna("") + ". " + frame["abstract"].fillna("")).tolist()


def add_tfidf(frame, queries):
    """tfidf = best percentile across the query documents; `tfidf_raw` keeps the cosine.

    queries: list of (name, text). Percentiles are taken per query because raw
    cosines against a long manuscript and a short seed profile are not comparable."""
    texts = candidate_text(frame)
    queries = [(name, text) for name, text in queries if text and text.strip()]
    if not queries or not len(frame):
        frame["tfidf"], frame["tfidf_raw"], frame["best_match"] = np.nan, np.nan, ""
        return frame
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english",
                                 min_df=2 if len(texts) >= 50 else 1, max_features=300000)
    matrix = vectorizer.fit_transform(texts)
    query_matrix = vectorizer.transform([text for _, text in queries])
    sims = (matrix @ query_matrix.T).toarray()
    ranks = np.column_stack([pct_rank(pd.Series(sims[:, i])).to_numpy() for i in range(sims.shape[1])])
    best = ranks.argmax(axis=1)
    frame["tfidf"] = ranks.max(axis=1)
    frame["tfidf_raw"] = sims.max(axis=1).round(4)
    frame["best_match"] = [queries[i][0] for i in best]
    return frame


def add_composite(frame, weights):
    signals = [s for s in ("coupling", "tfidf", "specter") if s in frame and frame[s].notna().any()]
    total = np.zeros(len(frame))
    weight_sum = np.zeros(len(frame))
    for signal in signals:
        pct = pct_rank(frame[signal])
        frame[f"{signal}_pct"] = pct.round(4)
        present = pct.notna().to_numpy()
        total[present] += weights.get(signal, 0) * pct.to_numpy()[present]
        weight_sum[present] += weights.get(signal, 0)
    with np.errstate(invalid="ignore", divide="ignore"):
        frame["composite"] = np.where(weight_sum > 0, total / weight_sum, np.nan).round(4)
    frame["n_signals"] = sum(frame[s].notna().astype(int) for s in signals) if signals else 0
    # stratified percentile: with / without abstract, unless a stratum is tiny
    sizes = frame.groupby("has_abstract")["composite"].transform("size")
    stratified = frame.groupby("has_abstract")["composite"].transform(pct_rank)
    overall = pct_rank(frame["composite"])
    frame["composite_pct"] = np.where(sizes >= MIN_STRATUM, stratified, overall).round(4)
    frame["relevance_level"] = [level_of(p) for p in frame["composite_pct"]]
    return frame, signals


def level_of(pct):
    if pct != pct:
        return ""
    for cut, name in LEVELS:
        if pct >= cut:
            return name
    return "Very Low"


def scoring_report(frame, signals, pool_cut):
    """Numbers that tell the user how much each signal could be trusted."""
    report = {
        "scored": int(len(frame)),
        "signals_used": signals,
        "abstract_coverage": round(float(frame["has_abstract"].mean()), 3) if len(frame) else 0,
        "reference_coverage": round(float(frame["coupling"].notna().mean()), 3) if len(frame) else 0,
        "cites_a_seed": int((frame["n_cites_seed"] > 0).sum()),
        "level_counts": frame.loc[~frame["is_seed"], "relevance_level"].value_counts().to_dict(),
    }
    if len(signals) > 1:
        report["signal_correlation"] = frame[signals].corr(method="spearman").round(3).to_dict()
    seeds = frame[frame["is_seed"]]
    report["seeds_found_by_search"] = int(len(seeds))
    if len(seeds):
        report["seeds_median_composite_pct"] = round(float(seeds["composite_pct"].median()), 3)
        report["seeds_in_pool_share"] = round(float((seeds["composite_pct"] >= pool_cut).mean()), 3)
    return report
