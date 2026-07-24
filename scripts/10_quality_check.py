import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MASTER = pd.read_csv(
    PROJECT_ROOT /
    "data/metadata/company_master.csv"
)

print("="*60)

print("PROJECT SUMMARY")

print("="*60)

print()

print("Companies")

print(len(MASTER))

print()

print("Eligible")

print(MASTER["Eligible"].sum())

print()

print("Industries")

print(MASTER["Industry"].nunique())

print()

print(MASTER.groupby("Industry")["Eligible"].sum())