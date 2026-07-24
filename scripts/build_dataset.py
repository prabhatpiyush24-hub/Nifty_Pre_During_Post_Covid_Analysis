from pathlib import Path

import numpy as np
import pandas as pd

# ==========================================================
# SETTINGS
# ==========================================================

START_DATE = "2015-01-01"
END_DATE = "2025-12-31"

RAW_PRICES = Path("data/raw/prices")
NIFTY_FILE = Path("data/raw/indices/NIFTY50.csv")
MASTER_FILE = Path("data/metadata/company_master.csv")

OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "final_dataset.csv"

# ==========================================================
# LOAD RESEARCH UNIVERSE
# ==========================================================

master = pd.read_csv(MASTER_FILE)

eligible = master[master["Eligible"] == True].copy()

print(f"Eligible companies : {len(eligible)}")

# ==========================================================
# LOAD & PROCESS STOCKS
# ==========================================================

all_data = []

for _, company in eligible.iterrows():

    symbol = company["Symbol"]
    company_name = company["Company Name"]
    industry = company["Industry"]

    file = RAW_PRICES / f"{symbol}.csv"

    if not file.exists():
        print(f"Missing file: {symbol}")
        continue

    try:
        df = pd.read_csv(file)

        df["Date"] = pd.to_datetime(df["Date"])

        df = df.sort_values("Date")

        df = df[
            (df["Date"] >= START_DATE)
            & (df["Date"] <= END_DATE)
        ].copy()

        if df.empty:
            print(f"No data in period: {symbol}")
            continue

        df["Return"] = df["Adj Close"].pct_change()

        df["Log Return"] = np.log(
            df["Adj Close"] / df["Adj Close"].shift(1)
        )

        df["Symbol"] = symbol
        df["Company Name"] = company_name
        df["Industry"] = industry

        df = df[
            [
                "Date",
                "Symbol",
                "Company Name",
                "Industry",
                "Close",
                "Adj Close",
                "Volume",
                "Return",
                "Log Return",
            ]
        ]

        all_data.append(df)

    except Exception as e:
        print(f"Error processing {symbol}: {e}")

# ==========================================================
# COMBINE STOCKS
# ==========================================================

stocks = pd.concat(all_data, ignore_index=True)

print(f"\nRows after combining stocks : {len(stocks):,}")

# ==========================================================
# LOAD NIFTY 50
# ==========================================================

nifty = pd.read_csv(NIFTY_FILE)

nifty["Date"] = pd.to_datetime(nifty["Date"])

nifty = nifty.sort_values("Date")

nifty = nifty[
    (nifty["Date"] >= START_DATE)
    & (nifty["Date"] <= END_DATE)
].copy()

nifty["NIFTY Return"] = nifty["Adj Close"].pct_change()

nifty = nifty[
    [
        "Date",
        "NIFTY Return",
    ]
]

# ==========================================================
# MERGE BENCHMARK
# ==========================================================

final = stocks.merge(
    nifty,
    on="Date",
    how="left",
)

# Keep only dates where benchmark return exists
final = final.dropna(subset=["NIFTY Return"]).copy()

# Calculate excess return
final["Excess Return"] = (
    final["Return"] - final["NIFTY Return"]
)
# ==========================================================
# SORT
# ==========================================================

final = final.sort_values(
    [
        "Date",
        "Symbol",
    ]
).reset_index(drop=True)

# ==========================================================
# SAVE
# ==========================================================

final.to_csv(
    OUTPUT_FILE,
    index=False,
)

# ==========================================================
# VALIDATION
# ==========================================================

print("\n" + "=" * 60)
print("FINAL DATASET SUMMARY")
print("=" * 60)

print(f"Rows               : {len(final):,}")
print(f"Companies          : {final['Symbol'].nunique()}")
print(f"Start Date         : {final['Date'].min().date()}")
print(f"End Date           : {final['Date'].max().date()}")

print(f"\nMissing Returns    : {final['Return'].isna().sum()}")
print(f"Missing Benchmark  : {final['NIFTY Return'].isna().sum()}")

print(f"\nSaved to:")
print(OUTPUT_FILE)