"""Step 8 - score every candidate and export the best ones for the agent to read.

Writes intermediate-data/scored-candidates.csv, scoring-report.json and the
reading batches in intermediate-data/judging/search/batch-NNN.json.
"""
import json

import numpy as np
import pandas as pd

import _bootstrap  # noqa: F401
from modules import scoring, specter
from modules.config import project_from_args, read_json, write_json
from modules.judging import export_batches, select_for_judging

JUDGE_FIELDS = ["item_id", "title", "authors", "year", "journal", "abstract",
                "relevance_level", "n_cites_seed", "n_shared_refs", "keywords_hit"]


def load_references(path):
    references = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            entry = json.loads(line)
            references[entry["doi"]] = entry["references"]
    return references


def main():
    project, _ = project_from_args(__doc__)
    config = project.config
    project.require(project.candidates, "run 06_search_journals.py first")
    frame = pd.read_csv(project.candidates, encoding="utf-8-sig", dtype={"year": str}, keep_default_na=False)
    frame["has_abstract"] = frame["has_abstract"].astype(str).str.lower() == "true"
    frame = frame[frame["excluded"].isin(["", "seed"])].reset_index(drop=True)
    frame["is_seed"] = frame["excluded"] == "seed"
    if frame.empty:
        raise SystemExit("No candidates to score.")
    references = load_references(project.candidate_refs)
    seed_data = read_json(project.seed_data, {})
    main_docs = [(p.stem, p.read_text(encoding="utf-8")) for p in sorted(project.processed_docs.glob("*.md"))]
    seed_profile = " ".join(f"{s['title']}. {s.get('abstract', '')}" for s in seed_data.values())

    frame = scoring.add_coupling(frame, references, seed_data, float(config["direct_citation_weight"]))
    frame = scoring.add_tfidf(frame, main_docs + [("seed references", seed_profile)])
    use_specter, info = specter.resolve_setting(config["use_specter"], len(frame))
    if use_specter:
        print(f"SPECTER on (device: {info['device']}, model cached: {info['model_cached']})")
        values, device = specter.specter_scores(frame, main_docs, seed_data, project.inter / "specter-cache.npz")
        frame["specter"] = np.round(values, 4)
    elif str(config["use_specter"]).lower() == "auto":
        print(f"SPECTER auto -> off ({info.get('reason', '')})")
    frame, signals = scoring.add_composite(frame, config["weights"])

    pool_cut = 1 - float(config["pool_top_share"])
    frame["in_pool"] = (frame["composite_pct"] >= pool_cut) & ~frame["is_seed"]
    frame.to_csv(project.scored, index=False, encoding="utf-8-sig")
    report = scoring.scoring_report(frame, signals, pool_cut)
    report["specter_used"] = bool(use_specter)
    write_json(project.scoring_report, report)

    eligible = frame[~frame["is_seed"]]
    journals = list(dict.fromkeys(eligible["journal"]))
    to_judge = select_for_judging(eligible, int(config["n_articles"]), int(config["judge_multiplier"]),
                                  config["shortlist_mode"], journals)
    rows = to_judge.replace({np.nan: ""}).to_dict("records")
    files = export_batches(rows, project.judging / "search", int(config["judge_batch_size"]), JUDGE_FIELDS)
    project.update_stats(scored=int(len(eligible)), pool=int(frame["in_pool"].sum()),
                         sent_to_agent=len(rows), scoring=report)

    print(f"Scored {len(eligible)} candidates with signals {signals}")
    print(f"  abstract coverage {report['abstract_coverage']:.0%}, reference lists {report['reference_coverage']:.0%}, "
          f"{report['cites_a_seed']} cite at least one seed")
    if report["seeds_found_by_search"]:
        print(f"  check: {report['seeds_found_by_search']} seeds were found by the search; "
              f"{report.get('seeds_in_pool_share', 0):.0%} of them rank inside the pool")
    print(f"  pool (top {config['pool_top_share']:.0%} per stratum): {int(frame['in_pool'].sum())}")
    print(f"\n{len(rows)} articles in {len(files)} batch file(s) -> {project.judging / 'search'}")
    print("Agent: read each batch-NNN.json and write judged-NNN.json next to it, then run step 9.")


if __name__ == "__main__":
    main()
