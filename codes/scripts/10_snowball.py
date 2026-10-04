"""Step 10 - citation snowballing.

Collects the works cited by the most relevant search results and by the
seeds, keeps those cited by several of them, and exports the best for the
agent to read (intermediate-data/judging/snowball/batch-NNN.json).
Run after step 9 so the sources are the articles the agent rated highest.
"""
import json

import numpy as np
import pandas as pd

import _bootstrap  # noqa: F401
from modules import snowball
from modules.config import project_from_args, read_csv_rows, read_json
from modules.crossref import Crossref
from modules.judging import export_batches
from modules.outputs import rank_frame
from modules.textutil import normalize_doi, normalize_title

JUDGE_FIELDS = ["item_id", "title", "authors", "year", "container", "type", "abstract",
                "n_citing_sources", "cited_by", "raw_reference"]


def label_of(authors, year):
    first = (authors or "").split(";")[0].split(",")[0].strip() or "Anon."
    return f"{first} ({year})" if year else first


def main():
    project, _ = project_from_args(__doc__)
    config = project.config
    settings = config["snowball"]
    if not settings.get("enabled", True):
        print("Snowballing is disabled in config.yaml; skipping.")
        return
    project.require(project.scored, "run 08_score_candidates.py first")
    frame = pd.read_csv(project.scored, encoding="utf-8-sig", dtype={"year": str}, keep_default_na=False,
                        na_values=[""])
    frame = frame[~frame["is_seed"].astype(str).str.lower().eq("true")]
    judgments = pd.DataFrame(read_csv_rows(project.judging / "search" / "judgments.csv"))
    if len(judgments):
        judgments["agent_relevance"] = judgments["agent_relevance"].astype(int)
        frame = frame.merge(judgments, on="item_id", how="left")
        sources = frame[frame["agent_relevance"] >= max(4, int(config["min_agent_relevance"]))]
        if len(sources) < 10:
            sources = frame[frame["agent_relevance"] >= int(config["min_agent_relevance"])]
    else:
        print("No agent judgments found; using the highest-scoring candidates as sources.")
        sources = frame
    sources = rank_frame(sources).head(int(settings["max_sources"]))

    references = {}
    with project.candidate_refs.open(encoding="utf-8") as handle:
        for line in handle:
            entry = json.loads(line)
            references[entry["doi"]] = entry["references"]
    seed_data = read_json(project.seed_data, {})
    source_list = [(row.doi, label_of(row.authors, row.year), references.get(row.doi, []))
                   for row in sources.fillna("").itertuples()]
    source_list += [(f"seed:{doi}", "seed: " + data["title"][:40], data.get("references", []))
                    for doi, data in seed_data.items()]
    by_doi, by_key, labels = snowball.collect(source_list)

    existing = read_csv_rows(project.zotero_existing)
    candidates = read_csv_rows(project.candidates)
    skip_dois = (set(seed_data) | {r["doi"] for r in candidates}
                 | {normalize_doi(r["value"]) for r in existing if r["kind"] == "doi"})
    skip_titles = ({normalize_title(d["title"]) for d in seed_data.values()}
                   | {r["value"] for r in existing if r["kind"] == "title"})
    min_citing = int(settings["min_citing_sources"])
    wanted = sorted((d for d, s in by_doi.items() if len(s) >= min_citing and d not in skip_dois),
                    key=lambda d: -len(by_doi[d]))[:int(settings["fetch_max"])]
    crossref = Crossref(config["crossref_mailto"])
    print(f"{len(source_list)} sources cite {len(by_doi)} DOIs and {len(by_key)} works without a DOI; "
          f"fetching metadata for {len(wanted)}...")
    records = crossref.works_by_dois(wanted)
    listed = set()
    for row in read_csv_rows(project.journals_validated):
        listed.update(i for i in (row.get("all_issns") or "").split(";") if i)

    rows = snowball.build_rows({d: by_doi[d] for d in wanted}, by_key, labels, records, min_citing,
                               skip_dois, skip_titles, listed)
    main_docs = [(p.stem, p.read_text(encoding="utf-8")) for p in sorted(project.processed_docs.glob("*.md"))]
    scored = snowball.score(rows, main_docs)
    if scored.empty:
        print("No reference is cited by enough sources; nothing to snowball.")
        project.update_stats(snowball_candidates=0)
        scored.to_csv(project.snowball, index=False, encoding="utf-8-sig")
        return
    scored.to_csv(project.snowball, index=False, encoding="utf-8-sig")
    to_judge = scored.head(int(settings["judge_max"])).replace({np.nan: ""}).to_dict("records")
    files = export_batches(to_judge, project.judging / "snowball", int(config["judge_batch_size"]), JUDGE_FIELDS)
    project.update_stats(snowball_sources=len(source_list), snowball_cited_dois=len(by_doi),
                         snowball_cited_no_doi=len(by_key), snowball_candidates=int(len(scored)),
                         snowball_without_doi=int((scored["doi"].fillna("") == "").sum()),
                         snowball_sent_to_agent=len(to_judge),
                         snowball_dois_unknown_to_crossref=len(wanted) - len(records))
    print(f"{len(scored)} snowball candidates (cited by >= {min_citing} sources) -> {project.snowball}")
    print(f"{len(to_judge)} in {len(files)} batch file(s) -> {project.judging / 'snowball'}")
    print("Agent: judge them as before, then run step 9 with --stage snowball.")


if __name__ == "__main__":
    main()
