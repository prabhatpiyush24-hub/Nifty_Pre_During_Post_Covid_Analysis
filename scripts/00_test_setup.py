import pandas as pd

stocks = pd.read_csv("data/processed/final_dataset.csv")
nifty = pd.read_csv("data/raw/indices/NIFTY50.csv")

stocks["Date"] = pd.to_datetime(stocks["Date"])
nifty["Date"] = pd.to_datetime(nifty["Date"])

nifty = nifty[
    (nifty["Date"] >= "2015-01-01") &
    (nifty["Date"] <= "2025-12-31")
]

stock_dates = set(stocks["Date"].unique())
nifty_dates = set(nifty["Date"].unique())

print("Stock dates :", len(stock_dates))
print("NIFTY dates :", len(nifty_dates))

print("\nDates in stocks but not in NIFTY:")
print(sorted(stock_dates - nifty_dates)[:20])

print("\nCount:", len(stock_dates - nifty_dates))