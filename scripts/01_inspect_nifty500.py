import pandas as pd
from pathlib import Path

# -------------------------------
# Project Root
# -------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# -------------------------------
# File Path
# -------------------------------

file_path = PROJECT_ROOT / "data" / "external" / "ind_nifty500list.csv"

# -------------------------------
# Read CSV
# -------------------------------

df = pd.read_csv(file_path)

print("=" * 80)
print("FIRST 5 ROWS")
print("=" * 80)
print(df.head())

print("\n")

print("=" * 80)
print("COLUMN NAMES")
print("=" * 80)
print(df.columns.tolist())

print("\n")

print("=" * 80)
print("DATA TYPES")
print("=" * 80)
print(df.dtypes)

print("\n")

print("=" * 80)
print("SHAPE")
print("=" * 80)
print(df.shape)

print("\n")

print("=" * 80)
print("MISSING VALUES")
print("=" * 80)
print(df.isnull().sum())