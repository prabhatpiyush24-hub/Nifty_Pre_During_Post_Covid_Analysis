import pandas as pd
from pathlib import Path

# ==========================================================
# SETTINGS
# ==========================================================

SYMBOL = "RELIANCE"

START_DATE = "2015-01-01"
END_DATE = "2025-12-31"

# ==========================================================
# LOAD STOCK
# ==========================================================

file = Path("data/raw/prices") / f"{SYMBOL}.csv"

prices = pd.read_csv(file)

prices["Date"] = pd.to_datetime(
    prices["Date"],
    format="mixed",
    dayfirst=True
)

prices = prices.sort_values("Date")

print("=" * 60)
print(f"{SYMBOL} BEFORE FILTER")
print("=" * 60)

print("Rows :", len(prices))
print("Start:", prices["Date"].min().date())
print("End  :", prices["Date"].max().date())

# ==========================================================
# FILTER TO RESEARCH PERIOD
# ==========================================================

prices = prices[
    (prices["Date"] >= START_DATE) &
    (prices["Date"] <= END_DATE)
].copy()

print("\n" + "=" * 60)
print(f"{SYMBOL} AFTER FILTER")
print("=" * 60)

print("Rows :", len(prices))
print("Start:", prices["Date"].min().date())
print("End  :", prices["Date"].max().date())

print("\nFirst 5 rows:")
print(prices[["Date", "Close", "Adj Close"]].head())

print("\nLast 5 rows:")
print(prices[["Date", "Close", "Adj Close"]].tail())
