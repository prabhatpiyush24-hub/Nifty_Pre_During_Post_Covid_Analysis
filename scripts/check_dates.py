import pandas as pd

df = pd.read_csv("data/raw/prices/RELIANCE.csv")

print("First Date:", df["Date"].min())
print("Last Date :", df["Date"].max())
print("\nFirst 5 rows:")
print(df.head())