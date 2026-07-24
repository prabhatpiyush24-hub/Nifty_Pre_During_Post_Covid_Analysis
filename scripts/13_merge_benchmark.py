import pandas as pd
from pathlib import Path

# ==========================================================
# PATHS
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RETURNS_FILE = PROJECT_ROOT / "data" / "processed" / "all_returns.csv"

NIFTY_FILE = PROJECT_ROOT / "data" / "processed" / "NIFTY50_returns.csv"

OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "final_dataset.csv"

# ==========================================================
# LOAD DATA
# ==========================================================

returns = pd.read_csv(RETURNS_FILE)

nifty = pd.read_csv(NIFTY_FILE)

# ==========================================================
# DATE PARSING
# ==========================================================

returns["Date"] = pd.to_datetime(
    returns["Date"],
    format="mixed",
    dayfirst=True,
    errors="raise"
)

nifty["Date"] = pd.to_datetime(
    nifty["Date"],
    format="mixed",
    dayfirst=True,
    errors="raise"
)

# ==========================================================
# KEEP REQUIRED MARKET COLUMNS
# ==========================================================

nifty = nifty[
    [
        "Date",
        "Simple Return",
        "Log Return"
    ]
].rename(
    columns={
        "Simple Return": "Market Return",
        "Log Return": "Market Log Return"
    }
)

# ==========================================================
# MERGE
# ==========================================================

final = returns.merge(
    nifty,
    on="Date",
    how="left"
)

# ==========================================================
# SAVE
# ==========================================================

final.to_csv(OUTPUT_FILE, index=False)

print("=" * 60)
print("FINAL DATASET CREATED")
print("=" * 60)
print()

print(f"Rows      : {len(final):,}")
print(f"Companies : {final['Symbol'].nunique()}")
print(f"Columns   : {len(final.columns)}")

print()

print(f"Saved to:\n{OUTPUT_FILE}")