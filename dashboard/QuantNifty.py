"""Entry point for the NIFTY 500 quantitative research dashboard."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

dashboard_directory = Path(__file__).resolve().parent
if str(dashboard_directory) not in sys.path:
    sys.path.insert(0, str(dashboard_directory))

from utils import apply_custom_theme, load_audit


st.set_page_config(page_title="QuantNifty", page_icon="📈", layout="wide")
apply_custom_theme()

summary, _, _ = load_audit()
st.title("QuantNifty")
st.caption("311 continuously eligible companies • NIFTY 50 benchmark • 2015–2025")

if summary["status"] != "PASS":
    st.error("The data-quality gate is not passing. Do not use dashboard results until the audit is resolved.")
else:
    st.success(
        f"Verified data: {summary['eligible_companies']} companies, "
        f"{summary['valid_daily_return_rows']:,} valid daily returns, and zero return-formula errors."
    )

st.markdown(
    """
Use the sidebar to explore the complete research workflow:

- **Overview** — research period, universe coverage, benchmark comparison, and cross-sectional leaders.
- **Stock Explorer** — search any of the 311 companies with custom date ranges, benchmark comparison, and six interactive charts.
- **Benchmark Analysis** — dedicated NIFTY 50 price, return, volatility, and drawdown analysis.
- **Industry Analysis** — composition, average returns, volatility, and comparative performance charts.
- **Risk & Return** — annualized returns, volatility, Sharpe/Sortino rankings, rolling risk, and VaR/CVaR.
- **CAPM Analysis** — beta estimation, alpha estimation, Security Market Line, and OLS regression.
- **Correlation** — pre/post co-movement matrices, industry correlations, and pairwise comparison.
- **PCA** — dimensionality reduction, explained variance, loadings, and interactive visualization.
- **Clustering** — K-Means grouping, cluster statistics, and industry–cluster distribution.
- **Portfolio Optimization** — equal-weight, minimum-variance, and maximum-Sharpe portfolios with efficient frontier.
- **Downloads & Reports** — CSV exports and dissertation-ready research summary.
- **COVID Regimes** — pre-COVID, March 2020 shock, and post-COVID regime comparison.
- **Data Quality** — transparent source-to-return validation and all flagged sessions.
"""
)
st.info("All performance statistics use adjusted-close returns. Sharpe and alpha assume a 6.5% risk-free rate (Indian 10Y Govt Bond equivalent).")

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<div style='text-align: center; color: #94A3B8; font-size: 0.85em; margin-top: 20px; font-weight: 500; letter-spacing: 0.05em;'>"
    "MADE BY PIYUSH PRABHAT"
    "</div>", 
    unsafe_allow_html=True
)
