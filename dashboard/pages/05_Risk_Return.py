"""Risk & Return Analysis — quantitative measures of investment performance."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import plotly.express as px
import streamlit as st

dashboard_directory = Path(__file__).resolve().parents[1]
if str(dashboard_directory) not in sys.path:
    sys.path.insert(0, str(dashboard_directory))

from utils import (
    apply_custom_theme, cumulative_wealth, load_company_metrics, load_daily_returns,
    to_number, to_percent, TRADING_DAYS, format_symbol,
)

st.title("Risk & Return Analysis")
st.caption(
    "Annualized metrics with 252 trading days. "
    "Sharpe, Sortino, and Alpha assume a 0% risk-free rate."
)
apply_custom_theme()

with st.expander("ℹ️ Understanding Risk & Return Metrics"):
    st.markdown("""
    - **CAGR**: Compound Annual Growth Rate.
    - **Volatility**: A measure of price fluctuation risk.
    - **Sharpe Ratio**: Return divided by risk (volatility). Higher is better.
    - **Sortino Ratio**: Similar to Sharpe, but only penalizes negative volatility (downside risk).
    - **Maximum Drawdown**: The largest percentage drop from a peak.
    - **CVaR 95%**: Conditional Value at Risk. The expected loss in the worst 5% of cases.
    """)

metrics = load_company_metrics()
daily = load_daily_returns()
regime = st.selectbox("Regime", ["Full Sample", "Pre-COVID",
                                  "COVID Shock (Mar 2020)", "Post-COVID"])
display = metrics.loc[metrics["Regime"] == regime].copy()

# ── Risk-return scatter ──────────────────────────────────────────
st.subheader("Risk-Return Scatter")
st.plotly_chart(
    px.scatter(
        display, x="Annualized Volatility", y="CAGR",
        color="Quantitative Cluster", size="Market Correlation",
        hover_data=["Symbol", "Company Name", "Industry",
                     "Sharpe Ratio (Rf=6.5%)", "Maximum Drawdown",
                     "Beta to NIFTY 50"],
        title=f"{regime}: Return vs Risk by Cluster",
    ),
    use_container_width=True,
)
st.caption("Plots individual companies based on their return and risk. Bubble size indicates correlation with the market.")

# ── Sharpe and Sortino rankings ──────────────────────────────────
left, right = st.columns(2)
with left:
    st.subheader("Top 20 — Sharpe Ratio")
    top_sharpe = display.nlargest(20, "Sharpe Ratio (Rf=6.5%)")
    fig_sharpe = px.bar(
        top_sharpe, x="Symbol", y="Sharpe Ratio (Rf=6.5%)", color="Industry",
        title="Highest Sharpe Ratios",
    )
    st.plotly_chart(fig_sharpe, use_container_width=True)
    st.caption("Companies with the best risk-adjusted returns (return divided by total volatility).")
with right:
    st.subheader("Top 20 — Sortino Ratio")
    top_sortino = display.nlargest(20, "Sortino Ratio (Rf=6.5%)")
    fig_sortino = px.bar(
        top_sortino, x="Symbol", y="Sortino Ratio (Rf=6.5%)", color="Industry",
        title="Highest Sortino Ratios",
    )
    st.plotly_chart(fig_sortino, use_container_width=True)
    st.caption("Companies with the best return relative to downside risk (ignores upside volatility).")

# ── Maximum drawdown rankings ───────────────────────────────────
st.subheader("Maximum Drawdown Rankings")
worst_dd = display.nsmallest(20, "Maximum Drawdown")
fig_dd = px.bar(
    worst_dd, x="Symbol", y="Maximum Drawdown", color="Industry",
    title="Deepest Drawdowns (most negative)",
)
fig_dd.update_layout(yaxis_tickformat=".0%")
st.plotly_chart(fig_dd, use_container_width=True)
st.caption("The companies that suffered the largest peak-to-trough drops in value.")

# ── Risk-adjusted and tail-risk tables ───────────────────────────
st.info("""
**Quant Explainer: Risk & Return Rankings**
- **Risk-Adjusted Leaders** (left): Ranks stocks by Sharpe Ratio. High Sharpe indicates the stock generates high returns without wild price swings.
- **Tail-Risk Leaders** (right): Ranks stocks by CVaR (Conditional Value at Risk). CVaR measures the expected loss *in the worst 5% of trading days*. Stocks here are highly defensive—their worst-case scenarios are much milder than the rest of the market.
""")
left, right = st.columns(2)
with left:
    st.subheader("Best risk-adjusted companies")
    best = display.nlargest(20, "Sharpe Ratio (Rf=6.5%)")[
        ["Symbol", "Company Name", "Industry", "Sharpe Ratio (Rf=6.5%)",
         "CAGR", "Annualized Volatility", "Maximum Drawdown"]
    ]
    st.dataframe(
        best.style.format({
            "Sharpe Ratio (Rf=6.5%)": "{:.2f}", "CAGR": "{:.2%}",
            "Annualized Volatility": "{:.2%}", "Maximum Drawdown": "{:.2%}",
        }),
        hide_index=True, use_container_width=True,
    )
with right:
    st.subheader("Tail-risk leaders (least severe CVaR)")
    tail = display.nlargest(20, "Historical CVaR 95% (1D)")[
        ["Symbol", "Company Name", "Industry",
         "Historical VaR 95% (1D)", "Historical CVaR 95% (1D)",
         "Maximum Drawdown"]
    ]
    st.dataframe(
        tail.style.format({
            "Historical VaR 95% (1D)": "{:.2%}",
            "Historical CVaR 95% (1D)": "{:.2%}",
            "Maximum Drawdown": "{:.2%}",
        }),
        hide_index=True, use_container_width=True,
    )

# ── Rolling risk analysis ────────────────────────────────────────
st.subheader("Rolling Risk Analysis")
symbols = sorted(display["Symbol"].unique())
selected_symbols = st.multiselect(
    "Select companies for rolling volatility",
    symbols, default=symbols[:3], max_selections=8, format_func=format_symbol,
)
if selected_symbols:
    rolling_data = daily[daily["Symbol"].isin(selected_symbols)].copy()
    if regime != "Full Sample":
        rolling_data = rolling_data[rolling_data["Regime"] == regime]
    rolling_data["Rolling Vol"] = rolling_data.groupby("Symbol")["Return"].transform(
        lambda x: x.rolling(63, min_periods=21).std() * np.sqrt(TRADING_DAYS)
    )
    fig_rolling = px.line(
        rolling_data, x="Date", y="Rolling Vol", color="Symbol",
        title="63-Day Rolling Annualized Volatility",
    )
    fig_rolling.update_layout(yaxis_tickformat=".0%")
    st.plotly_chart(fig_rolling, use_container_width=True)
    st.caption("Tracks how a company's short-term risk fluctuates over time. Peaks indicate periods of high uncertainty.")

# ── Company versus benchmark ────────────────────────────────────
st.markdown("---")
st.subheader("Deep Dive: Single Company")
symbol = st.selectbox("Company", sorted(display["Symbol"]), index=0, format_func=format_symbol)

company = display[display["Symbol"] == symbol].iloc[0]
company_path = daily.loc[daily["Symbol"] == symbol]
if regime != "Full Sample":
    company_path = company_path.loc[company_path["Regime"] == regime]
company_path = cumulative_wealth(company_path, "Return").rename(
    columns={"Wealth Index": symbol}
)
benchmark_path = cumulative_wealth(
    company_path[["Date", "NIFTY Return"]], "NIFTY Return"
).rename(columns={"Wealth Index": "NIFTY 50"})
chart = (
    company_path[["Date", symbol]]
    .merge(benchmark_path[["Date", "NIFTY 50"]], on="Date")
    .melt("Date", var_name="Series", value_name="Wealth Index")
)
st.plotly_chart(
    px.line(chart, x="Date", y="Wealth Index", color="Series",
            title=f"{symbol} versus NIFTY 50"),
    use_container_width=True,
)
st.caption("Direct comparison of the selected company's wealth growth versus the NIFTY 50 index.")

row1 = st.columns(3)
row1[0].metric("CAGR", to_percent(company["CAGR"]), help="Compound Annual Growth Rate.")
row1[1].metric("Volatility", to_percent(company["Annualized Volatility"]), help="Annualized risk measure.")
row1[2].metric("Beta", to_number(company["Beta to NIFTY 50"]), help="Sensitivity to the NIFTY 50 benchmark.")

row2 = st.columns(3)
row2[0].metric("Alpha", to_percent(company["Annualized Alpha (Rf=6.5%)"]), help="Annualized excess return relative to the benchmark.")
row2[1].metric("Max Drawdown", to_percent(company["Maximum Drawdown"]), help="Largest peak-to-trough drop.")
