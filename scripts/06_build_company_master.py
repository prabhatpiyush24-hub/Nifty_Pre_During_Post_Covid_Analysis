import pandas as pd
from pathlib import Path

# ==========================================================
# PATHS
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MASTER = PROJECT_ROOT / "data/external/ind_nifty500list.csv"
HISTORY = PROJECT_ROOT / "data/metadata/history_validation.csv"

OUTPUT = PROJECT_ROOT / "data/metadata/company_master.csv"

# ==========================================================
# LOAD
# ==========================================================

master = pd.read_csv(MASTER)

history = pd.read_csv(HISTORY)

company_master = master.merge(
    history,
    on="Symbol",
    how="left"
)

company_master.to_csv(OUTPUT, index=False)

print()

print("="*60)

print("Company Master Created")

print("="*60)

print()

print(company_master.head())

print()

print(f"Rows : {len(company_master)}")

print(f"Saved : {OUTPUT}")