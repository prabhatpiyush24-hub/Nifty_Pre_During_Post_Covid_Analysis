import pandas as pd
import yfinance as yf
from pathlib import Path

# ==========================================================
# PATHS
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

METADATA_FOLDER = PROJECT_ROOT / "data" / "metadata"
METADATA_FOLDER.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = METADATA_FOLDER / "reference_calendar.csv"

# ==========================================================
# DOWNLOAD NIFTY 50
# ==========================================================

print("Downloading NIFTY 50 reference calendar...")

nifty = yf.Ticker("^NSEI")

calendar = nifty.history(
    start="2015-01-01",
    end="2026-01-01",
    auto_adjust=False
)

calendar.reset_index(inplace=True)

calendar["Date"] = calendar["Date"].dt.tz_localize(None)

calendar = calendar[["Date"]]

calendar["Trading Day"] = True

calendar.to_csv(OUTPUT_FILE, index=False)

print()

print(f"Trading Days : {len(calendar)}")

print(f"Saved to:\n{OUTPUT_FILE}")