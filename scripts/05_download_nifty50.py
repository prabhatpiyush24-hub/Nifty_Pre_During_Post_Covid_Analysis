import yfinance as yf
from pathlib import Path

# ==========================================================
# PATHS
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INDEX_FOLDER = PROJECT_ROOT / "data" / "raw" / "indices"
INDEX_FOLDER.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = INDEX_FOLDER / "NIFTY50.csv"

# ==========================================================
# DOWNLOAD NIFTY 50
# ==========================================================

print("Downloading NIFTY 50 OHLCV data...")

ticker = yf.Ticker("^NSEI")

df = ticker.history(
    start="2015-01-01",
    end="2026-01-01",
    auto_adjust=False
)

if df.empty:
    raise ValueError("Failed to download NIFTY 50 data.")

df.reset_index(inplace=True)

# Remove timezone
df["Date"] = df["Date"].dt.tz_localize(None)

# Keep only required columns
df = df[
    [
        "Date",
        "Open",
        "High",
        "Low",
        "Close",
        "Adj Close",
        "Volume"
    ]
]

df.to_csv(OUTPUT_FILE, index=False)

print("\nDownload Successful!\n")

print(f"Rows Downloaded : {len(df)}")
print(f"Date Range      : {df['Date'].min().date()} to {df['Date'].max().date()}")

print(f"\nSaved to:\n{OUTPUT_FILE}")