from pathlib import Path
import sys

# ==========================================================
# PROJECT ROOT
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

import pandas as pd
from tqdm import tqdm

from src.config import (
    RAW_PRICES,
    DAILY_RETURNS,
    PROCESSED_DIR,
    METADATA_DIR
)

# ==========================================================
# FILES
# ==========================================================

ALL_RETURNS_FILE = PROCESSED_DIR / "all_returns.csv"
FINAL_DATASET_FILE = PROCESSED_DIR / "final_dataset.csv"

# ==========================================================
# LOAD CONSOLIDATED FILES
# ==========================================================

print("Loading consolidated datasets...")

all_returns_df = pd.read_csv(ALL_RETURNS_FILE)
final_dataset_df = pd.read_csv(FINAL_DATASET_FILE)

report = []

price_files = sorted(RAW_PRICES.glob("*.csv"))

print(f"\nChecking {len(price_files)} companies...\n")

# ==========================================================
# AUDIT
# ==========================================================

for raw_file in tqdm(price_files):

    symbol = raw_file.stem

    try:

        # -----------------------------
        # RAW
        # -----------------------------
        raw_df = pd.read_csv(raw_file)

        raw_median = raw_df["Volume"].median()
        raw_mean = raw_df["Volume"].mean()

        # -----------------------------
        # DAILY RETURNS
        # -----------------------------
        returns_file = DAILY_RETURNS / f"{symbol}.csv"

        if returns_file.exists():

            returns_df = pd.read_csv(returns_file)

            if "Volume" in returns_df.columns:

                returns_median = returns_df["Volume"].median()
                returns_mean = returns_df["Volume"].mean()

            else:

                returns_median = None
                returns_mean = None

        else:

            returns_median = None
            returns_mean = None

        # -----------------------------
        # ALL RETURNS
        # -----------------------------
        company_all = all_returns_df[
            all_returns_df["Symbol"] == symbol
        ]

        if "Volume" in company_all.columns:

            all_median = company_all["Volume"].median()
            all_mean = company_all["Volume"].mean()

        else:

            all_median = None
            all_mean = None

        # -----------------------------
        # FINAL DATASET
        # -----------------------------
        company_final = final_dataset_df[
            final_dataset_df["Symbol"] == symbol
        ]

        if "Volume" in company_final.columns:

            final_median = company_final["Volume"].median()
            final_mean = company_final["Volume"].mean()

        else:

            final_median = None
            final_mean = None

        # -----------------------------
        # Detect corruption
        # -----------------------------

        status = "PASS"

        if returns_median is not None:

            if abs(raw_median - returns_median) > 1:

                status = "CHECK"

        if all_median is not None:

            if abs(raw_median - all_median) > 1:

                status = "CHECK"

        if final_median is not None:

            if abs(raw_median - final_median) > 1:

                status = "CHECK"

        report.append({

            "Symbol": symbol,

            "Raw Median": raw_median,

            "Returns Median": returns_median,

            "All Returns Median": all_median,

            "Final Median": final_median,

            "Raw Mean": raw_mean,

            "Returns Mean": returns_mean,

            "All Returns Mean": all_mean,

            "Final Mean": final_mean,

            "Status": status

        })

    except Exception as e:

        report.append({

            "Symbol": symbol,

            "Status": "ERROR",

            "Reason": str(e)

        })

# ==========================================================
# SAVE
# ==========================================================

report_df = pd.DataFrame(report)

output = METADATA_DIR / "volume_audit.csv"

report_df.to_csv(output, index=False)

print("\n" + "=" * 60)

print("VOLUME AUDIT COMPLETE")

print("=" * 60)

print(report_df["Status"].value_counts())

print()

print(f"Saved to:\n{output}")