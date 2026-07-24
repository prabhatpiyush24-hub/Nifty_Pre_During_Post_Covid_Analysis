import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm

# ==========================================================
# PATHS
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MASTER_FILE = PROJECT_ROOT / "data/metadata/company_master.csv"

PRICE_FOLDER = PROJECT_ROOT / "data/raw/prices"

OUTPUT_FOLDER = PROJECT_ROOT / "data/processed/daily_returns"

OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

# ==========================================================
# LOAD MASTER
# ==========================================================

master = pd.read_csv(MASTER_FILE)

eligible = master[master["Eligible"] == True]

print()

print(f"Processing {len(eligible)} companies...\n")

# ==========================================================
# LOOP
# ==========================================================

for _, row in tqdm(eligible.iterrows(), total=len(eligible)):

    symbol = row["Symbol"]

    file = PRICE_FOLDER / f"{symbol}.csv"

    df = pd.read_csv(file)

    df["Date"] = pd.to_datetime(df["Date"])

    df = df[
        (df["Date"] >= "2015-01-01") &
        (df["Date"] <= "2025-12-31")
    ]

    df.sort_values("Date", inplace=True)

    df["Simple Return"] = df["Adj Close"].pct_change()

    df["Log Return"] = np.log(
        df["Adj Close"] /
        df["Adj Close"].shift(1)
    )

    df.to_csv(
        OUTPUT_FOLDER / f"{symbol}.csv",
        index=False
    )

print()

print("Daily Returns Created")