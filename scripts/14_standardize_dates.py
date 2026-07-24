import pandas as pd
from pathlib import Path
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PRICE_FOLDER = PROJECT_ROOT / "data" / "processed" / "daily_returns"

print("Standardizing date formats...")

for file in tqdm(list(PRICE_FOLDER.glob("*.csv"))):

    df = pd.read_csv(file)

    df["Date"] = pd.to_datetime(
        df["Date"],
        format="mixed",
        dayfirst=True,
        errors="coerce"
    )

    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

    df.to_csv(file, index=False)

print("\nDone.")