"""Step 9 - validate and merge the agent's judgments.

    --stage search     (default) judgments on the journal-search candidates
    --stage snowball   judgments on the snowballed references

Each judged-NNN.json is a JSON list of
    {"item_id": "...", "relevance": 1-5, "reason": "...", "theme": "..."}
covering every item of the matching batch-NNN.json.
"""
import json

import _bootstrap  # noqa: F401
from modules.config import project_from_args, write_csv_rows, write_json
from modules.judging import merge_judgments


def main():
    project, args = project_from_args(__doc__, lambda p: p.add_argument(
        "--stage", choices=("search", "snowball"), default="search"))
    stage_dir = project.judging / args.stage
    batches = sorted(stage_dir.glob("batch-*.json"))
    if not batches:
        raise SystemExit(f"No batch files in {stage_dir}. Run the step that exports them first.")
    items = [item for path in batches for item in json.loads(path.read_text(encoding="utf-8"))]
    expected = [item["item_id"] for item in items]
    judgments, problems = merge_judgments(stage_dir, expected)
    todo_path = stage_dir / "todo.json"
    if problems:
        print("Judgments are incomplete or invalid:")
        for problem in problems[:30]:
            print("  -", problem)
        todo = [item for item in items if item["item_id"] not in judgments]
        write_json(todo_path, todo)
        print(f"\n{len(todo)} item(s) still to judge are listed in {todo_path}.\n"
              "Write their judgments to a judged-NNN.json file (any unused number) and run this step again.")
        raise SystemExit(1)
    if todo_path.exists():
        todo_path.unlink()
    rows = [{"item_id": item_id, **judgments[item_id]} for item_id in expected]
    write_csv_rows(stage_dir / "judgments.csv", rows, ["item_id", "agent_relevance", "agent_reason", "theme"])
    counts = {}
    for row in rows:
        counts[row["agent_relevance"]] = counts.get(row["agent_relevance"], 0) + 1
    project.update_stats(**{f"judged_{args.stage}": len(rows),
                            f"judged_{args.stage}_by_relevance": {str(k): v for k, v in sorted(counts.items())}})
    print(f"{len(rows)} judgments merged -> {stage_dir / 'judgments.csv'}")
    print("relevance counts:", {k: counts[k] for k in sorted(counts, reverse=True)})


if __name__ == "__main__":
    main()
