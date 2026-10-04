"""Step 1 - create a project folder from the templates.

    python codes/scripts/01_init_project.py --project my-paper
"""
import argparse
import shutil
import sys
from pathlib import Path

import _bootstrap  # noqa: F401
from modules.config import PROJECTS_DIR, TEMPLATES_DIR, Project


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--project", help="project name under projects/")
    group.add_argument("--project-dir", help="path of the project folder to create")
    args = parser.parse_args()
    root = Path(args.project_dir) if args.project_dir else PROJECTS_DIR / args.project
    project = Project(root)
    project.ensure_dirs()
    (project.inputs / "zotero-info").mkdir(exist_ok=True)
    copies = [
        (TEMPLATES_DIR / "seed-references.csv", project.seed_csv),
        (TEMPLATES_DIR / "journal-lists.csv", project.journal_csv),
        (TEMPLATES_DIR / "config.yaml", project.config_path),
        (TEMPLATES_DIR / "zotero-info" / "README.md", project.inputs / "zotero-info" / "README.md"),
        (TEMPLATES_DIR / "zotero-info" / ".env.example", project.inputs / "zotero-info" / ".env.example"),
    ]
    for source, target in copies:
        if target.exists():
            print(f"kept     {target.relative_to(project.root)} (already exists)")
        else:
            shutil.copyfile(source, target)
            print(f"created  {target.relative_to(project.root)}")
    print(f"\nProject ready: {project.root}")
    print("Next: put the main documents (PDF / .md) in inputs/main-docs/, then fill in\n"
          "      seed-references.csv, journal-lists.csv and config.yaml (all optional to start).")


if __name__ == "__main__":
    sys.exit(main())
