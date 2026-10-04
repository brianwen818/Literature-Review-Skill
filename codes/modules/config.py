"""Project layout, configuration and small IO helpers."""
import argparse
import csv
import json
import os
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = REPO_ROOT / "templates"
PROJECTS_DIR = REPO_ROOT / "projects"

DEFAULTS = {
    "n_articles": 50,
    "shortlist_mode": "global",          # global | per-journal
    "per_journal_redistribute": True,
    "min_agent_relevance": 3,
    "crossref_mailto": "",
    "year_from": None,
    "year_to": None,
    "max_keywords": 30,
    "rows_per_query": 20,
    "weights": {"coupling": 0.40, "specter": 0.40, "tfidf": 0.20},
    "direct_citation_weight": 3.0,
    "use_specter": "off",                # off | on | auto
    "pool_top_share": 0.20,
    "judge_multiplier": 3,
    "judge_batch_size": 25,
    "snowball": {
        "enabled": True,
        "max_sources": 100,
        "min_citing_sources": 2,
        "fetch_max": 300,
        "judge_max": 60,
        "n_items": 30,
    },
    "library_link_template": (
        "https://nccu.primo.exlibrisgroup.com/discovery/search"
        "?query=any,contains,{title}&vid=886NCCU_INST:886NCCU_INST"
    ),
    "library_link_column": "nccu-lib-link",
    "summary_language": "zh-TW",         # zh-TW | en
    "zotero": {"collection": "", "tag": "lit-review-automation"},
}


class Project:
    """Paths of one project folder (inputs / intermediate-data / outputs)."""

    def __init__(self, root):
        self.root = Path(root).resolve()
        self.inputs = self.root / "inputs"
        self.inter = self.root / "intermediate-data"
        self.outputs = self.root / "outputs"
        self.main_docs = self.inputs / "main-docs"
        self.seed_csv = self.inputs / "seed-references.csv"
        self.journal_csv = self.inputs / "journal-lists.csv"
        self.config_path = self.inputs / "config.yaml"
        self.env_path = self.inputs / "zotero-info" / ".env"
        self.processed_docs = self.inter / "processed-main-docs"
        self.processed_seeds = self.inter / "processed-seed-references.csv"
        self.seed_data = self.inter / "seed-data.json"
        self.journals_validated = self.inter / "journals-validated.csv"
        self.keyword_candidates = self.inter / "keyword-candidates.csv"
        self.keywords = self.inter / "keywords.csv"
        self.search_dir = self.inter / "search"
        self.candidates = self.inter / "candidates.csv"
        self.candidate_refs = self.inter / "candidate-references.jsonl"
        self.zotero_existing = self.inter / "zotero-existing.csv"
        self.scored = self.inter / "scored-candidates.csv"
        self.scoring_report = self.inter / "scoring-report.json"
        self.judging = self.inter / "judging"
        self.snowball = self.inter / "snowball-candidates.csv"
        self.run_stats = self.inter / "run-stats.json"
        self._config = None

    def ensure_dirs(self):
        for path in (self.inputs, self.main_docs, self.inter, self.outputs):
            path.mkdir(parents=True, exist_ok=True)

    @property
    def config(self):
        if self._config is None:
            user = {}
            if self.config_path.exists():
                user = yaml.safe_load(self.config_path.read_text(encoding="utf-8")) or {}
            self._config = merge_config(DEFAULTS, user)
        return self._config

    def require(self, path, hint):
        if not Path(path).exists():
            sys.exit(f"Missing {path}\n  -> {hint}")
        return path

    def update_stats(self, **values):
        """Merge counters into run-stats.json; the summary reads them back."""
        stats = read_json(self.run_stats, {})
        stats.update(values)
        write_json(self.run_stats, stats)
        return stats


def merge_config(defaults, user):
    merged = dict(defaults)
    for key, value in (user or {}).items():
        if isinstance(value, dict) and isinstance(defaults.get(key), dict):
            merged[key] = merge_config(defaults[key], value)
        elif value is not None or key in ("year_from", "year_to"):
            merged[key] = value
    return merged


def project_from_args(description, extra=None):
    """Standard CLI: --project NAME (under projects/) or --project-dir PATH."""
    parser = argparse.ArgumentParser(description=description)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--project", help="project name under projects/")
    group.add_argument("--project-dir", help="path to a project folder")
    if extra:
        extra(parser)
    args = parser.parse_args()
    root = Path(args.project_dir) if args.project_dir else PROJECTS_DIR / args.project
    project = Project(root)
    if not project.root.exists():
        sys.exit(f"Project folder not found: {project.root}\n  -> run 01_init_project.py first")
    project.ensure_dirs()
    return project, args


def setup_console():
    """Windows consoles default to a legacy code page; force UTF-8 output."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def read_jsonl(path):
    path = Path(path)
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue  # a line cut off by an interrupted run
    return rows


def append_jsonl(path, row):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_csv_rows(path):
    """CSV -> list of dicts, tolerant of a BOM and of missing files."""
    path = Path(path)
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv_rows(path, rows, columns=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if columns is None:
        columns = []
        for row in rows:
            for key in row:
                if key not in columns:
                    columns.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_env(path):
    """Read KEY=VALUE lines without exporting them to the process environment."""
    values = {}
    path = Path(path)
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def mask(secret):
    secret = secret or ""
    return secret[:3] + "*" * max(len(secret) - 3, 0) if secret else "(empty)"
