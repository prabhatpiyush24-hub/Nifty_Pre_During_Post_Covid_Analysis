# NIFTY 500 Quantitative Research Platform

An auditable Python and Streamlit research platform for 311 continuously eligible NIFTY 500 companies, benchmarked against the NIFTY 50 from 2015 to 2025.

## Run the project

```powershell
.\.venv\Scripts\python.exe scripts\build_research_data.py
.\.venv\Scripts\python.exe scripts\verify_research_data.py
.\.venv\Scripts\streamlit.exe run dashboard\app.py
```

Install dependencies into a new virtual environment when needed:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Data integrity guarantee

The build recalculates simple, log, benchmark, and excess returns from adjusted closing prices. Each company is first aligned to the NIFTY 50 trading calendar; no price or return is forward-filled, back-filled, or inferred. `scripts/verify_research_data.py` independently rebuilds and checks the persisted outputs before they are used.

The quality report explicitly retains two warnings: AEGISLOG and PVRINOX have no source observation on the special benchmark session of 2025-02-01. Their affected multi-session return is excluded rather than presented as a one-day return.

## Project layout

| Path | Purpose |
| --- | --- |
| `data/raw/` | Verified source prices for the research universe and NIFTY 50 benchmark |
| `data/metadata/company_master.csv` | Universe definition and industry classifications |
| `data/processed/` | Benchmark-aligned research dataset and valid daily-return table |
| `data/analysis/` | Company, sector, correlation, clustering, and COVID-comparison outputs |
| `data/quality/` | Return-formula audit, summary, and retained warnings |
| `src/research.py` | Single source of truth for validation, analytics, and export logic |
| `scripts/` | Rebuild and independent verification entry points |
| `dashboard/` | Fast Streamlit research dashboard |

See [methodology.md](docs/methodology.md) for metric definitions and COVID-regime rules.
