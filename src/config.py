"""Shared paths and defaults. Change things here, not inside other files."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT / "data"
RAW_CSV = DATA_DIR / "mtsamples.csv"
BASE_NOTES = DATA_DIR / "base_notes.jsonl"

RESULTS_DIR = ROOT / "results"
CACHE_DIR = RESULTS_DIR / "cache"
FIGURES_DIR = ROOT / "figures"

# Defaults are for convenience; pass provider and model explicitly for research runs.
DEFAULT_PROVIDER = "gemini"
DEFAULT_MODEL = "gemini-3.8-flash"

# Temperature 0 so reruns give (near) identical answers.
TEMPERATURE = 0.0

# Seed for every random choice (which notes, which target drug).
SEED = 7


def fname(model: str) -> str:
    """Model name made safe for file names ('qwen2.5:3b' -> 'qwen2.5-3b'; colons break Windows unzip)."""
    return model.replace(":", "-")
