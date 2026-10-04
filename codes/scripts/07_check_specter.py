"""Step 7 (optional) - check whether the SPECTER signal is worth turning on.

Reports whether torch is installed, whether a GPU is usable, whether the
model is already downloaded, and a rough time estimate. Changes nothing.
The project argument is optional; with it, the estimate uses the real
number of candidates.
"""
import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401
from modules import specter
from modules.config import PROJECTS_DIR, Project, read_csv_rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project")
    parser.add_argument("--project-dir")
    parser.add_argument("--json", action="store_true", help="print the raw result as JSON")
    args = parser.parse_args()
    n_texts = 0
    if args.project or args.project_dir:
        project = Project(Path(args.project_dir) if args.project_dir else PROJECTS_DIR / args.project)
        n_texts = sum(1 for r in read_csv_rows(project.candidates) if r["excluded"] in ("", "seed"))
    info = specter.check(n_texts)
    if args.json:
        print(json.dumps(info, indent=1))
        return
    print(f"torch installed:                  {info['torch_installed']}"
          + (f" ({info['torch_version']})" if info.get("torch_version") else ""))
    print(f"sentence-transformers installed:  {info['sentence_transformers_installed']}")
    print(f"NVIDIA GPU:                       {info['nvidia_gpu'] or 'none detected'}")
    print("device torch would use:           "
          + (info["device"] if info["torch_installed"] else "unknown (torch not installed)"))
    print(f"model already downloaded:         {info['model_cached']}"
          + (f"\n    {info['model_cache_path']} (will be reused)" if info["model_cached"] else ""))
    if n_texts:
        minutes = info["estimated_minutes"]
        print(f"candidates to encode:             {n_texts}  "
              f"({'under a minute' if minutes < 1 else f'about {minutes:.0f} min'})")
    print(f"\nRecommendation: use_specter = {info['recommendation']}  ({info['reason']})")
    if info["setup_steps"]:
        print("To turn it on:")
        for step in info["setup_steps"]:
            print(f"  - {step}")
    print("Set `use_specter` in the project's config.yaml (off | on | auto).")


if __name__ == "__main__":
    main()
