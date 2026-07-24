import pandas as pd
from pathlib import Path

file = Path("data/raw/prices/RELIANCE.csv")

# Read only the date column exactly as stored
raw = pd.read_csv(file, usecols=["Date"])

print("First 20 raw date strings:")
print(raw.head(20))

print("\nRandom sample:")
print(raw.sample(20, random_state=42))