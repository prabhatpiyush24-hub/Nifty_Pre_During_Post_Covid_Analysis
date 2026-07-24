import numpy as np
import pandas as pd
from pathlib import Path

# ==========================================================
# SETTINGS
# ==========================================================

SYMBOL = "RELIANCE"
START_DATE = "2015-01-01"
END_DATE = "2025-12-31"

# ==========================================================
# LOAD DATA
# ==========================================================

file = Path("data/raw/prices") / f"{SYMBOL}.csv"

prices = pd.read_csv(file)

prices["Date"] = pd.to_datetime(prices["Date"])

prices = prices.sort_values("Date")

# Keep only research period
prices = prices[
    (prices["Date"] >= START_DATE) &
    (prices["Date"] <= END_DATE)
].copy()

# ==========================================================
# RETURNS
# ==========================================================

prices["Return"] = prices["Adj Close"].pct_change()

prices["Log Return"] = np.log(
    prices["Adj Close"] /
    prices["Adj Close"].shift(1)
)

# ==========================================================
# DISPLAY
# ==========================================================

print("=" * 60)
print(f"{SYMBOL} RETURNS")
print("=" * 60)

print(prices[
    [
        "Date",
        "Adj Close",
        "Return",
        "Log Return"
    ]
].head(10))

print("\n")

print("=" * 60)
print("SUMMARY")
print("=" * 60)

print(f"Observations : {len(prices)}")

print(f"Missing Returns : {prices['Return'].isna().sum()}")

print(f"Mean Return : {prices['Return'].mean():.6f}")

print(f"Std Dev : {prices['Return'].std():.6f}")

print(f"Minimum : {prices['Return'].min():.6f}")

print(f"Maximum : {prices['Return'].max():.6f}")