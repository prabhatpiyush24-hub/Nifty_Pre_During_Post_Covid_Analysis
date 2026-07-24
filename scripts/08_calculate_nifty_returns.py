import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT = PROJECT_ROOT / "data/raw/indices/NIFTY50.csv"

OUTPUT = PROJECT_ROOT / "data/processed/NIFTY50_returns.csv"

df = pd.read_csv(INPUT)

df["Date"] = pd.to_datetime(df["Date"])

df["Simple Return"] = df["Adj Close"].pct_change()

df["Log Return"] = np.log(
    df["Adj Close"] /
    df["Adj Close"].shift(1)
)

df.to_csv(OUTPUT, index=False)

print(df.head())

print()

print("Saved:", OUTPUT)