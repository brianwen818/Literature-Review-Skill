"""Make `modules` importable when a script is run directly."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.config import setup_console  # noqa: E402

setup_console()
