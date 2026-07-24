from pathlib import Path

# ==========================================================
# PROJECT ROOT
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ==========================================================
# DATA DIRECTORIES
# ==========================================================

DATA_DIR = PROJECT_ROOT / "data"

RAW_DIR = DATA_DIR / "raw"

RAW_PRICES = RAW_DIR / "prices"
RAW_INDICES = RAW_DIR / "indices"

PROCESSED_DIR = DATA_DIR / "processed"

DAILY_RETURNS = PROCESSED_DIR / "daily_returns"

METADATA_DIR = DATA_DIR / "metadata"

REPORTS_DIR = PROJECT_ROOT / "reports"

DOCS_DIR = PROJECT_ROOT / "docs"