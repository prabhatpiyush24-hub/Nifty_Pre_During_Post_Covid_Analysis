import pandas as pd
from pathlib import Path

# ==========================================================
# PATHS
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MASTER_FILE = PROJECT_ROOT / "data/metadata/company_master.csv"
REFERENCE_FILE = PROJECT_ROOT / "data/metadata/reference_calendar.csv"

OUTPUT_FILE = PROJECT_ROOT / "data/metadata/research_universe.csv"

# ==========================================================
# LOAD
# ==========================================================

master = pd.read_csv(MASTER_FILE)

reference = pd.read_csv(REFERENCE_FILE)

expected_days = len(reference)

# ==========================================================
# CALCULATIONS
# ==========================================================

master["Coverage (%)"] = (
    master["Trading Days"] / expected_days * 100
).round(2)

def classify(row):

    if row["Reason"] == "Missing File":
        return "Excluded"

    if row["Coverage (%)"] >= 95:
        return "Included"

    return "Excluded"

master["Research Universe"] = master.apply(classify, axis=1)

master.to_csv(OUTPUT_FILE, index=False)

print("=" * 60)
print("Research Universe Created")
print("=" * 60)
print()

print(master["Research Universe"].value_counts())

print()

print(master.groupby("Industry")["Research Universe"].value_counts())

print()

print(f"Saved to:\n{OUTPUT_FILE}")