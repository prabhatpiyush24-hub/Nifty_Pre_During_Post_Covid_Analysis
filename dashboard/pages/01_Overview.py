"""Overview — high-level summary of the research dataset."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

dashboard_directory = Path(__file__).resolve().parents[1]
if str(dashboard_directory) not in sys.path:
    sys.path.insert(0, str(dashboard_directory))

from utils import (
    apply_custom_theme, cumulative_wealth, load_audit, load_company_metrics, load_daily_returns,
    load_market_metrics, to_number, to_percent,
)

st.title("Overview")
st.caption("High-level summary of the NIFTY 500 quantitative research dataset")
apply_custom_theme()

summary, _, _ = load_audit()
daily = load_daily_returns()
company_metrics = load_company_metrics()
market_metrics = load_market_metrics()
full_metrics = company_metrics.loc[company_metrics["Regime"] == "Full Sample"].copy()
market_full = market_metrics.loc[market_metrics["Regime"] == "Full Sample"].iloc[0]

# ── Research period and headline metrics ──────────────────────────
st.info(
    f"📅 **Research period**: {summary['study_period']['start']} to {summary['study_period']['end']} "
    f"&nbsp;|&nbsp; **Benchmark**: NIFTY 50"
)

st.markdown("""
This dashboard provides a comprehensive quantitative analysis of the **NIFTY 500 universe**—representing the top 500 companies listed on the National Stock Exchange of India. 

**Core Concepts:**
- **Performance Evaluation:** We compare each stock's performance against the **NIFTY 50** index (the top 50 blue-chip companies, used as our baseline benchmark).
- **Risk & Return:** We analyze how much return a stock generates relative to the risk (price volatility) it takes.
- **Advanced Analytics:** We use statistical techniques (PCA, Clustering) to uncover hidden patterns and relationships among these stocks.
""")

row1 = st.columns(3)
row1[0].metric("Eligible Companies", f"{summary['eligible_companies']}", help="Total number of companies analyzed that met data quality requirements.")
row1[1].metric("Industries", f"{daily['Industry'].nunique()}", help="Number of distinct industry classifications represented in the dataset.")
row1[2].metric("Benchmark Sessions", f"{summary['benchmark_sessions']:,}", help="Total number of trading days in the analysis period.")

row2 = st.columns(3)
row2[0].metric("Valid Daily Returns", f"{summary['valid_daily_return_rows']:,}", help="Total number of clean, usable daily return data points across all companies.")
row2[1].metric("Data-Quality Status", summary["status"], help="PASS indicates all data successfully passed the stringent audit for errors and missing values.")

# ── Dataset summary table ────────────────────────────────────────
st.subheader("Dataset Summary")
dataset_summary = pd.DataFrame({
    "Metric": [
        "Study Period",
        "Eligible Companies",
        "Industries Represented",
        "Benchmark Index",
        "Benchmark Sessions",
        "Benchmark-Aligned Company Rows",
        "Valid Daily Return Rows",
        "Companies with Complete Coverage",
        "Companies with Flagged Sessions",
        "Data-Quality Status",
    ],
    "Value": [
        f"{summary['study_period']['start']} to {summary['study_period']['end']}",
        str(summary["eligible_companies"]),
        str(daily["Industry"].nunique()),
        "NIFTY 50",
        f"{summary['benchmark_sessions']:,}",
        f"{summary['benchmark_aligned_company_rows']:,}",
        f"{summary['valid_daily_return_rows']:,}",
        str(summary["companies_with_complete_daily_return_coverage"]),
        str(summary["companies_with_flagged_missing_sessions"]),
        summary["status"],
    ],
})
st.dataframe(dataset_summary, hide_index=True, use_container_width=True)
st.info("""
**Quant Explainer: Dataset Summary**
This table confirms the integrity of the data pipeline. We strictly analyze companies that have full, unbroken trading histories over the 10-year study period to prevent survivorship bias and missing data anomalies.
""")

# ── Benchmark information ────────────────────────────────────────
st.subheader("Benchmark Information — NIFTY 50")
bench_cols1 = st.columns(2)
bench_cols1[0].metric("CAGR", to_percent(market_full["CAGR"]), help="Compound Annual Growth Rate: The annualized average rate of return.")
bench_cols1[1].metric("Volatility", to_percent(market_full["Annualized Volatility"]), help="Annualized Volatility: A measure of risk. Higher volatility means the price fluctuates more wildly.")

bench_cols2 = st.columns(2)
bench_cols2[0].metric("Maximum Drawdown", to_percent(market_full["Maximum Drawdown"]), help="The largest single drop from peak to trough in the portfolio's value.")
bench_cols2[1].metric("Sharpe Ratio", to_number(market_full["Sharpe Ratio (Rf=6.5%)"]), help="Risk-adjusted return. A higher number indicates better returns for the amount of risk taken.")

# ── Equal-weight universe versus NIFTY 50 ────────────────────────
st.subheader("Equal-weight Universe versus NIFTY 50")
universe = daily.groupby("Date", as_index=False).agg(
    Return=("Return", "mean"), **{"NIFTY Return": ("NIFTY Return", "first")}
)
universe = cumulative_wealth(universe, "Return").rename(
    columns={"Wealth Index": "Equal-weight NIFTY 500 universe"}
)
benchmark = cumulative_wealth(universe[["Date", "NIFTY Return"]], "NIFTY Return").rename(
    columns={"Wealth Index": "NIFTY 50"}
)
wealth = universe[["Date", "Equal-weight NIFTY 500 universe"]].merge(
    benchmark[["Date", "NIFTY 50"]], on="Date"
)
wealth_long = wealth.melt("Date", var_name="Portfolio", value_name="Wealth Index")
st.plotly_chart(
    px.line(wealth_long, x="Date", y="Wealth Index", color="Portfolio",
            title="Growth of ₹100 (adjusted-close returns)"),
    use_container_width=True,
)

# ── Cross-sectional reference ────────────────────────────────────
st.info("""
**Quant Explainer: Market Reference & Cross-Sectional Spread**
The **Market Reference** (left) shows the baseline performance of the NIFTY 50 index. The **Cross-Sectional Spread** (right) aggregates the median metrics of all 300+ individual companies. If the median company underperforms the NIFTY 50, it indicates that market gains were driven by a small handful of mega-cap stocks rather than broad participation.
""")
left, right = st.columns(2)
with left:
    st.subheader("Full-sample market reference")
    reference = pd.DataFrame({
        "Metric": ["NIFTY 50 CAGR", "NIFTY 50 Volatility",
                    "NIFTY 50 Maximum Drawdown", "NIFTY 50 Sharpe"],
        "Value": [
            to_percent(market_full["CAGR"]),
            to_percent(market_full["Annualized Volatility"]),
            to_percent(market_full["Maximum Drawdown"]),
            to_number(market_full["Sharpe Ratio (Rf=6.5%)"]),
        ],
    })
    st.dataframe(reference, hide_index=True, use_container_width=True)
with right:
    st.subheader("Cross-sectional spread")
    spread = pd.DataFrame({
        "Measure": ["Median company CAGR", "Median annualized volatility",
                     "Median beta", "Median maximum drawdown"],
        "Value": [
            to_percent(full_metrics["CAGR"].median()),
            to_percent(full_metrics["Annualized Volatility"].median()),
            to_number(full_metrics["Beta to NIFTY 50"].median()),
            to_percent(full_metrics["Maximum Drawdown"].median()),
        ],
    })
    st.dataframe(spread, hide_index=True, use_container_width=True)

# ── COVID-19 Sector Surprises ────────────────────────────────────
from utils import load_sector_metrics
st.subheader("COVID-19 Sector Surprises & Key Findings")
try:
    sector_metrics = load_sector_metrics()
    post_covid = sector_metrics[sector_metrics["Regime"] == "Post-COVID"]
    shock = sector_metrics[sector_metrics["Regime"] == "COVID Shock (Mar 2020)"]
    
    if not post_covid.empty and not shock.empty:
        best_post_covid = post_covid.loc[post_covid["CAGR"].idxmax()]
        worst_shock = shock.loc[shock["Total Return"].idxmin()]
        
        st.info(f"""
        **The March 2020 Devastation**: During the initial COVID-19 crash, **{worst_shock['Industry']}** was the hardest hit sector, suffering a staggering **{to_percent(worst_shock['Total Return'])}** total loss in just a few weeks. 
        
        **The Post-COVID Resurgence**: Surprisingly, the strongest rebound came from **{best_post_covid['Industry']}**, which completely inverted its trajectory to compound at an explosive **{to_percent(best_post_covid['CAGR'])}** annually in the Post-COVID era.
        
        *This highlights how macro-economic shocks can completely reorder market leadership and risk profiles.*
        """)
except Exception:
    st.info("COVID-19 Sector data is currently unavailable.")

# ── Company leaders ──────────────────────────────────────────────
st.subheader("Company leaders: full sample")
rank_by = st.selectbox(
    "Rank companies by",
    ["CAGR", "Sharpe Ratio (Rf=6.5%)", "Annualized Alpha (Rf=6.5%)", "Information Ratio"],
)
leaders = full_metrics.nlargest(15, rank_by)[
    ["Symbol", "Company Name", "Industry", "Quantitative Cluster",
     rank_by, "Annualized Volatility", "Maximum Drawdown", "Beta to NIFTY 50"]
]
fmt = {
    rank_by: "{:.2%}" if rank_by in {"CAGR", "Annualized Alpha (Rf=6.5%)"} else "{:.2f}",
    "Annualized Volatility": "{:.2%}",
    "Maximum Drawdown": "{:.2%}",
    "Beta to NIFTY 50": "{:.2f}",
}
st.dataframe(leaders.style.format(fmt), hide_index=True, use_container_width=True)
st.info("""
**Quant Explainer: Company Leaders**
This table isolates the absolute best-performing assets in the NIFTY 500 universe based on the selected metric. 
- **CAGR**: Pure growth rate (ignores risk).
- **Sharpe/Alpha**: Risk-adjusted returns (how much excess return was generated per unit of volatility). 
*Use this to identify outlier stocks that consistently beat the market on a risk-adjusted basis.*
""")
