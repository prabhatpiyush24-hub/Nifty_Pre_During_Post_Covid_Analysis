import pandas as pd
from pathlib import Path
from tqdm import tqdm

# ==========================================================
# PATHS
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MASTER = pd.read_csv(
    PROJECT_ROOT / "data/metadata/research_universe.csv"
)

RETURN_FOLDER = PROJECT_ROOT / "data/processed/daily_returns"

OUTPUT = PROJECT_ROOT / "data/processed/all_returns.csv"

# ==========================================================
# LOAD INCLUDED COMPANIES
# ==========================================================

included = MASTER[
    MASTER["Research Universe"] == "Included"
]

frames = []

print(f"Building dataset for {len(included)} companies...")

for symbol in tqdm(included["Symbol"]):

    file = RETURN_FOLDER / f"{symbol}.csv"

    if not file.exists():
        continue

    df = pd.read_csv(file)

    df["Symbol"] = symbol

    frames.append(df)

# ==========================================================
# SAVE
# ==========================================================

all_returns = pd.concat(frames, ignore_index=True)

all_returns.to_csv(OUTPUT, index=False)

print()

print("=" * 60)
print("MASTER RETURNS DATASET CREATED")
print("=" * 60)

print(f"Rows : {len(all_returns):,}")

print(f"Companies : {all_returns['Symbol'].nunique()}")

print(f"Saved : {OUTPUT}")