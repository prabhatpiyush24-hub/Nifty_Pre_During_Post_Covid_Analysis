import pandas as pd
import yfinance as yf
from pathlib import Path
from tqdm import tqdm
from datetime import datetime
import time

# ==========================================================
# PATHS
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MASTER_FILE = PROJECT_ROOT / "data" / "external" / "ind_nifty500list.csv"

PRICE_FOLDER = PROJECT_ROOT / "data" / "raw" / "prices"
PRICE_FOLDER.mkdir(parents=True, exist_ok=True)

METADATA_FOLDER = PROJECT_ROOT / "data" / "metadata"
METADATA_FOLDER.mkdir(parents=True, exist_ok=True)

LOG_FILE = METADATA_FOLDER / "download_log.csv"

# ==========================================================
# LOAD MASTER LIST
# ==========================================================

companies = pd.read_csv(MASTER_FILE)

download_log = []

print(f"\nDownloading data for {len(companies)} companies...\n")

# ==========================================================
# DOWNLOAD LOOP
# ==========================================================

for _, row in tqdm(companies.iterrows(), total=len(companies)):

    symbol = row["Symbol"]
    company = row["Company Name"]
    industry = row["Industry"]

    ticker = f"{symbol}.NS"

    file_path = PRICE_FOLDER / f"{symbol}.csv"

    status = "FAILED"
    attempts = 0
    rows = 0
    error = ""

    while attempts < 5:

        attempts += 1

        try:

            stock = yf.Ticker(ticker)

            df = stock.history(period="max", auto_adjust=False)

            if df.empty:
                raise Exception("Empty DataFrame")

            df.reset_index(inplace=True)

            if "Date" in df.columns:
                df["Date"] = df["Date"].dt.tz_localize(None)

            df.to_csv(file_path, index=False)

            rows = len(df)

            status = "SUCCESS"

            break

        except Exception as e:

            error = str(e)

            time.sleep(2)

    download_log.append({

        "Symbol": symbol,
        "Company Name": company,
        "Industry": industry,
        "Ticker": ticker,
        "Status": status,
        "Attempts": attempts,
        "Rows Downloaded": rows,
        "Error": error,
        "Timestamp": datetime.now()

    })

# ==========================================================
# SAVE LOG
# ==========================================================

log_df = pd.DataFrame(download_log)

log_df.to_csv(LOG_FILE, index=False)

print("\nDownload Complete\n")

print(log_df["Status"].value_counts())

print(f"\nDownload log saved to:\n{LOG_FILE}")