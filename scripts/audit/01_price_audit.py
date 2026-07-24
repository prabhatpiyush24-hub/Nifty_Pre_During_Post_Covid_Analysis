from pathlib import Path
import sys

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

import pandas as pd
from tqdm import tqdm

from src.config import RAW_PRICES, METADATA_DIR
from src.loader import load_price_file
from src.validator import (
    missing_values,
    duplicate_dates,
    negative_prices,
    negative_volume,
    date_sorted,
    ohlc_errors,
    volume_statistics
)

report = []

files = sorted(RAW_PRICES.glob("*.csv"))

print("=" * 60)
print("PRICE AUDIT")
print("=" * 60)

for file in tqdm(files):

    symbol = file.stem

    try:

        df = load_price_file(file)

        vol = volume_statistics(df)

        report.append({
            "Symbol": symbol,
            "Rows": len(df),
            "Start": df["Date"].min().date(),
            "End": df["Date"].max().date(),
            "Missing Values": missing_values(df),
            "Duplicate Dates": duplicate_dates(df),
            "Negative Prices": negative_prices(df),
            "Negative Volume": negative_volume(df),
            "OHLC Errors": ohlc_errors(df),
            "Sorted Dates": date_sorted(df),
            "Min Volume": vol["Minimum"],
            "Median Volume": vol["Median"],
            "Average Volume": vol["Average"],
            "Max Volume": vol["Maximum"],
            "Status": "PASS"
        })

    except Exception as e:

        report.append({
            "Symbol": symbol,
            "Status": "FAIL",
            "Reason": str(e)
        })

report = pd.DataFrame(report)

output = METADATA_DIR / "price_audit.csv"

report.to_csv(output, index=False)

print()
print("=" * 60)
print("AUDIT COMPLETE")
print("=" * 60)

print(report["Status"].value_counts())

print()

print("Saved to")

print(output)