import pandas as pd

nifty = pd.read_csv("data/raw/indices/NIFTY50.csv")

print(nifty.columns.tolist())

print("\nFirst 5 rows:\n")
print(nifty.head())