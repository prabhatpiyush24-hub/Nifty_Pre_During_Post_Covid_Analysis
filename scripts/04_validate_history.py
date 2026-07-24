import pandas as pd
from pathlib import Path

# ==========================================================
# PATHS
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PRICE_FOLDER = PROJECT_ROOT / "data" / "raw" / "prices"

MASTER_FILE = PROJECT_ROOT / "data" / "external" / "ind_nifty500list.csv"

REFERENCE_FILE = PROJECT_ROOT / "data" / "metadata" / "reference_calendar.csv"

OUTPUT_FILE = PROJECT_ROOT / "data" / "metadata" / "history_validation.csv"

# ==========================================================
# LOAD FILES
# ==========================================================

master = pd.read_csv(MASTER_FILE)

reference = pd.read_csv(REFERENCE_FILE)

reference["Date"] = pd.to_datetime(reference["Date"])

expected_days = len(reference)

results = []

print("Validating historical coverage...\n")

# ==========================================================
# VALIDATION
# ==========================================================

for _, row in master.iterrows():

    symbol = row["Symbol"]

    file = PRICE_FOLDER / f"{symbol}.csv"

    if not file.exists():

        results.append({

            "Symbol": symbol,
            "Coverage (%)": 0,
            "Trading Days": 0,
            "First Date": None,
            "Last Date": None,
            "Eligible": False,
            "Reason": "Missing File"

        })

        continue

    df = pd.read_csv(file)

    df["Date"] = pd.to_datetime(df["Date"])

    study = df[
        (df["Date"] >= "2015-01-01") &
        (df["Date"] <= "2025-12-31")
    ]

    if study.empty:

        results.append({

            "Symbol": symbol,
            "Coverage (%)": 0,
            "Trading Days": 0,
            "First Date": None,
            "Last Date": None,
            "Eligible": False,
            "Reason": "No Data in Study Period"

        })

        continue

    trading_days = study["Date"].nunique()

    coverage = trading_days / expected_days * 100

    first_date = study["Date"].min().date()

    last_date = study["Date"].max().date()

    eligible = first_date <= pd.to_datetime("2015-01-02").date()

    reason = "PASS" if eligible else "Listed After Study Start"

    results.append({

        "Symbol": symbol,
        "Coverage (%)": round(coverage, 2),
        "Trading Days": trading_days,
        "First Date": first_date,
        "Last Date": last_date,
        "Eligible": eligible,
        "Reason": reason

    })

# ==========================================================
# SAVE
# ==========================================================

history = pd.DataFrame(results)

history.to_csv(OUTPUT_FILE, index=False)

print(history["Reason"].value_counts())

print()

print(f"Saved to:\n{OUTPUT_FILE}")