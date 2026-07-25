"""Benchmark Analysis — dedicated NIFTY 50 index analysis."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

dashboard_directory = Path(__file__).resolve().parents[1]
if str(dashboard_directory) not in sys.path:
    sys.path.insert(0, str(dashboard_directory))

from utils import (
    apply_custom_theme, load_benchmark_prices, load_daily_returns, load_market_metrics,
    to_number, to_percent,
)

st.title("Benchmark Analysis — NIFTY 50")
st.caption(
    "Dedicated analysis of the NIFTY 50 index used as the market benchmark "
    "throughout this research"
)
apply_custom_theme()

# ── Load data ────────────────────────────────────────────────────
benchmark_prices = load_benchmark_prices()
daily = load_daily_returns()
market_metrics = load_market_metrics()
market_full = market_metrics.loc[market_metrics["Regime"] == "Full Sample"].iloc[0]

# Unique benchmark returns (one row per date)
nifty = (
    daily[["Date", "NIFTY Return"]]
    .drop_duplicates("Date")
    .sort_values("Date")
    .reset_index(drop=True)
)

# Filter raw prices to research period
nifty_prices = benchmark_prices[["Date", "Adj Close"]].copy()
nifty_prices = nifty_prices[
    (nifty_prices["Date"] >= "2015-01-01") & (nifty_prices["Date"] <= "2025-12-31")
]

# ── Performance summary ──────────────────────────────────────────
st.subheader("Benchmark Risk & Return Metrics")
row1 = st.columns(3)
row1[0].metric("Total Return", to_percent(market_full["Total Return"]), help="Cumulative return of the index.")
row1[1].metric("CAGR", to_percent(market_full["CAGR"]), help="Compound Annual Growth Rate.")
row1[2].metric("Volatility", to_percent(market_full["Annualized Volatility"]), help="Annualized standard deviation of daily returns.")

row2 = st.columns(3)
row2[0].metric("Sharpe Ratio", to_number(market_full["Sharpe Ratio (Rf=6.5%)"]), help="Risk-adjusted return.")
row2[1].metric("Max Drawdown", to_percent(market_full["Maximum Drawdown"]), help="Largest peak-to-trough drop.")
row2[2].metric("Observations", f"{int(market_full['Observations']):,}", help="Number of trading days.")

st.markdown("---")

# ── 1. Benchmark price movement ─────────────────────────────────
st.subheader("NIFTY 50 Price Movement")
fig_price = px.line(nifty_prices, x="Date", y="Adj Close",
                    title="NIFTY 50 — Adjusted Closing Price")
st.plotly_chart(fig_price, use_container_width=True)
st.caption("The raw price trend of the NIFTY 50 benchmark index.")

# ── 2. Daily benchmark returns ───────────────────────────────────
st.subheader("Daily Benchmark Returns")
fig_ret = go.Figure()
fig_ret.add_trace(go.Bar(
    x=nifty["Date"], y=nifty["NIFTY Return"], name="NIFTY 50",
    marker_color="#00FFFF", opacity=0.8,
))
fig_ret.update_layout(title="NIFTY 50 — Daily Returns",
                      yaxis_tickformat=".1%")
st.plotly_chart(fig_ret, use_container_width=True)
st.caption("Daily percentage change of the index, highlighting the overall market's daily volatility.")

# ── 3. Cumulative benchmark performance ──────────────────────────
st.subheader("Cumulative Benchmark Performance")
nifty_cum = nifty.copy()
nifty_cum["Cumulative Return"] = (1 + nifty_cum["NIFTY Return"]).cumprod() - 1
fig_cum = px.line(nifty_cum, x="Date", y="Cumulative Return",
                  title="NIFTY 50 — Cumulative Return")
fig_cum.update_layout(yaxis_tickformat=".0%")
st.plotly_chart(fig_cum, use_container_width=True)
st.caption("The total accumulated return of the market index from the start of the period.")

# ── 4. Rolling volatility ───────────────────────────────────────
st.subheader("Rolling Volatility")
nifty_vol = nifty.copy()
nifty_vol["21-Day"] = nifty_vol["NIFTY Return"].rolling(21).std() * np.sqrt(252)
nifty_vol["63-Day"] = nifty_vol["NIFTY Return"].rolling(63).std() * np.sqrt(252)
fig_vol = go.Figure()
fig_vol.add_trace(go.Scatter(x=nifty_vol["Date"], y=nifty_vol["21-Day"],
                             name="21-day", line=dict(color="#00FFFF")))
fig_vol.add_trace(go.Scatter(x=nifty_vol["Date"], y=nifty_vol["63-Day"],
                             name="63-day", line=dict(color="#FF9900")))
fig_vol.update_layout(title="NIFTY 50 — Annualized Rolling Volatility",
                      yaxis_tickformat=".0%")
st.plotly_chart(fig_vol, use_container_width=True)
st.caption("Tracks short-term (21-day) and medium-term (63-day) risk. Spikes correspond to periods of market panic or uncertainty.")

# ── 5. Drawdown analysis ────────────────────────────────────────
st.subheader("Drawdown Analysis")
nifty_dd = nifty.copy()
wealth = (1 + nifty_dd["NIFTY Return"]).cumprod()
nifty_dd["Drawdown"] = wealth / wealth.cummax() - 1
fig_dd = go.Figure()
fig_dd.add_trace(go.Scatter(
    x=nifty_dd["Date"], y=nifty_dd["Drawdown"], fill="tozeroy",
    name="Drawdown", line=dict(color="#FF0055"),
))
fig_dd.update_layout(title="NIFTY 50 — Drawdowns", yaxis_tickformat=".0%")
st.plotly_chart(fig_dd, use_container_width=True)
st.caption("Highlights the severity of market crashes (e.g., the March 2020 COVID shock) and the time taken for the market to recover to previous highs.")

# ── 6. Return distribution ──────────────────────────────────────
st.subheader("Return Distribution")
fig_dist = px.histogram(
    nifty, x="NIFTY Return", nbins=80,
    title="NIFTY 50 — Return Distribution",
    marginal="box", opacity=0.7,
)
fig_dist.update_layout(xaxis_tickformat=".1%")
st.plotly_chart(fig_dist, use_container_width=True)
st.caption("Shows the frequency of daily returns. Notice the 'fat tails'—extreme positive or negative returns happen more often than a normal bell curve predicts.")

# ── Regime comparison ────────────────────────────────────────────
st.markdown("---")
st.subheader("Performance by Regime")
regime_display = market_metrics[[
    "Regime", "Total Return", "CAGR", "Annualized Volatility",
    "Sharpe Ratio (Rf=6.5%)", "Maximum Drawdown", "Observations",
]].copy()
st.dataframe(
    regime_display.style.format({
        "Total Return": "{:.2%}",
        "CAGR": "{:.2%}",
        "Annualized Volatility": "{:.2%}",
        "Sharpe Ratio (Rf=6.5%)": "{:.2f}",
        "Maximum Drawdown": "{:.2%}",
        "Observations": "{:,.0f}",
    }),
    hide_index=True,
    use_container_width=True,
)
