import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

log = pd.read_csv(PROJECT_ROOT / "data" / "processed" / "download_log.csv")

print("=" * 60)

print("DOWNLOAD SUMMARY")

print("=" * 60)

print()

print(log["Status"].value_counts())

print()

print("Failed Companies:\n")

print(log[log["Status"] == "FAILED"][

    ["Symbol",

     "Company Name",

     "Error"]

])