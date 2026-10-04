"""Hand-off between the scripts and the agent's reading of titles and abstracts.

export: writes batch-NNN.json files for the agent to read.
merge:  reads the judged-NNN.json files the agent wrote and validates them."""
import json
import math

from .config import write_json

REQUIRED = ("item_id", "relevance", "reason", "theme")


def select_for_judging(frame, n_articles, multiplier, mode, journals):
    """Rows the agent should read: the global top (multiplier x n), plus each
    journal's own top slice when the shortlist is built per journal."""
    ranked = frame.sort_values(["composite_pct", "composite"], ascending=False)
    chosen = list(ranked.head(multiplier * n_articles).index)
    if mode == "per-journal" and journals:
        per_journal = math.ceil(n_articles / len(journals)) * multiplier
        for _, group in ranked.groupby("journal", sort=False):
            chosen.extend(group.head(per_journal).index)
    return ranked.loc[list(dict.fromkeys(chosen))]


def export_batches(rows, stage_dir, batch_size, fields):
    """rows: list of dicts. Existing batch files are replaced; judged files are kept."""
    stage_dir.mkdir(parents=True, exist_ok=True)
    for old in stage_dir.glob("batch-*.json"):
        old.unlink()
    files = []
    for number, start in enumerate(range(0, len(rows), batch_size), 1):
        batch = [{field: row.get(field, "") for field in fields} for row in rows[start:start + batch_size]]
        path = stage_dir / f"batch-{number:03d}.json"
        write_json(path, batch)
        files.append(path)
    return files


def merge_judgments(stage_dir, expected_ids):
    """Returns (judgments by item_id, problems). Problems must be empty to proceed."""
    judgments, problems = {}, []
    for path in sorted(stage_dir.glob("judged-*.json")):
        try:
            entries = json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as error:
            problems.append(f"{path.name}: not valid JSON ({error})")
            continue
        if not isinstance(entries, list):
            problems.append(f"{path.name}: expected a JSON list")
            continue
        for entry in entries:
            missing = [key for key in REQUIRED if key not in entry]
            if missing:
                problems.append(f"{path.name}: entry missing {missing}: {str(entry)[:80]}")
                continue
            try:
                relevance = int(entry["relevance"])
            except (TypeError, ValueError):
                relevance = 0
            if not 1 <= relevance <= 5:
                problems.append(f"{path.name}: relevance must be 1-5 for {entry['item_id']}")
                continue
            if not str(entry["reason"]).strip():
                problems.append(f"{path.name}: empty reason for {entry['item_id']}")
                continue
            judgments[str(entry["item_id"])] = {
                "agent_relevance": relevance,
                "agent_reason": " ".join(str(entry["reason"]).split()),
                "theme": " ".join(str(entry["theme"]).split()),
            }
    # Judgments for items no longer in the batches (left over from an earlier
    # scoring run) are simply ignored, so a re-run only needs the new items judged.
    expected = set(expected_ids)
    missing_ids = sorted(expected - set(judgments))
    if missing_ids:
        problems.append(f"{len(missing_ids)} item(s) not judged yet, e.g. {missing_ids[:3]}")
    return {k: v for k, v in judgments.items() if k in expected}, problems
