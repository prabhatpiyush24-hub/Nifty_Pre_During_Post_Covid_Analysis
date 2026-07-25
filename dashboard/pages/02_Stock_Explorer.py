"""Stock Explorer — interactive single-stock deep-dive for all 311 companies."""

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

from utils import apply_custom_theme, compute_stock_metrics, load_daily_returns, to_number, to_percent

st.title("Stock Explorer")
st.caption(
    "Search any of the 311 companies · Filter by industry · "
    "Custom date ranges · Benchmark comparison"
)
apply_custom_theme()

daily = load_daily_returns()

# ── Filters ───────────────────────────────────────────────────────
industries = ["All Industries"] + sorted(daily["Industry"].unique())
col_ind, col_comp = st.columns([1, 2])
with col_ind:
    selected_industry = st.selectbox("Filter by industry", industries)

available = daily[["Symbol", "Company Name", "Industry"]].drop_duplicates()
if selected_industry != "All Industries":
    available = available[available["Industry"] == selected_industry]
available = available.sort_values("Symbol")

with col_comp:
    labels = dict(zip(
        available["Symbol"] + " — " + available["Company Name"],
        available["Symbol"],
    ))
    selected_label = st.selectbox("Search company", list(labels.keys()))
    selected_symbol = labels[selected_label]

col_start, col_end, col_bench = st.columns([1, 1, 1])
min_date = daily["Date"].min().date()
max_date = daily["Date"].max().date()
with col_start:
    start_date = st.date_input("Start date", value=min_date,
                               min_value=min_date, max_value=max_date)
with col_end:
    end_date = st.date_input("End date", value=max_date,
                             min_value=min_date, max_value=max_date)
with col_bench:
    compare_benchmark = st.checkbox("Compare with NIFTY 50", value=True)

if start_date > end_date:
    st.error("Start date must be before end date.")
    st.stop()

# ── Filter data ──────────────────────────────────────────────────
stock = daily[daily["Symbol"] == selected_symbol].copy()
stock = stock[
    (stock["Date"].dt.date >= start_date) & (stock["Date"].dt.date <= end_date)
].copy().reset_index(drop=True)

if stock.empty:
    st.warning("No data for the selected company and date range.")
    st.stop()

# ── Performance metrics ──────────────────────────────────────────
m = compute_stock_metrics(stock["Return"], stock["NIFTY Return"], stock["Date"])
st.subheader("Performance & Risk Metrics")
row1 = st.columns(4)
row1[0].metric("Total Return", to_percent(m.get("Total Return")), help="Cumulative return over the selected period.")
row1[1].metric("CAGR", to_percent(m.get("CAGR")), help="Compound Annual Growth Rate.")
row1[2].metric("Ann. Volatility", to_percent(m.get("Annualized Volatility")), help="Annualized standard deviation of daily returns.")
row1[3].metric("Sharpe Ratio", to_number(m.get("Sharpe Ratio")), help="Risk-adjusted return (using 0% risk-free rate).")

row2 = st.columns(4)
row2[0].metric("Max Drawdown", to_percent(m.get("Maximum Drawdown")), help="Largest peak-to-trough drop in value.")
row2[1].metric("Beta", to_number(m.get("Beta")), help="Sensitivity to the NIFTY 50 benchmark.")
row2[2].metric("Alpha (Ann.)", to_percent(m.get("Alpha (Ann.)")), help="Annualized excess return relative to the benchmark.")
row2[3].metric("Observations", f"{m.get('Observations', 0):,}", help="Number of trading days in the selected period.")

st.markdown("---")

# ── 1. Adjusted Closing Price ────────────────────────────────────
st.subheader("Adjusted Closing Price")
fig_price = px.line(stock, x="Date", y="Adj Close",
                    title=f"{selected_symbol} — Adjusted Closing Price")
st.plotly_chart(fig_price, use_container_width=True)
st.caption("Displays the historical adjusted closing prices over the selected period. This helps visualize the raw price trend of the stock.")

# ── 2. Daily Returns ─────────────────────────────────────────────
st.subheader("Daily Returns")
fig_ret = go.Figure()
fig_ret.add_trace(go.Bar(
    x=stock["Date"], y=stock["Return"], name=selected_symbol,
    marker_color="#00FFFF", opacity=0.8,
))
if compare_benchmark:
    fig_ret.add_trace(go.Scatter(
        x=stock["Date"], y=stock["NIFTY Return"], name="NIFTY 50",
        line=dict(color="#FF9900", width=1), opacity=0.5,
    ))
fig_ret.update_layout(title=f"{selected_symbol} — Daily Returns",
                      yaxis_tickformat=".1%", barmode="overlay")
st.plotly_chart(fig_ret, use_container_width=True)
st.caption("Shows the daily percentage change in price. Spikes indicate high volatility or major news events. The benchmark line helps compare daily swings.")

# ── 3. Cumulative Returns ────────────────────────────────────────
st.subheader("Cumulative Returns")
stock_cum = stock.copy()
stock_cum["Stock Cumulative"] = (1 + stock_cum["Return"]).cumprod() - 1
fig_cum = go.Figure()
fig_cum.add_trace(go.Scatter(
    x=stock_cum["Date"], y=stock_cum["Stock Cumulative"],
    name=selected_symbol, line=dict(color="#00FFFF"),
))
if compare_benchmark:
    stock_cum["NIFTY Cumulative"] = (1 + stock_cum["NIFTY Return"]).cumprod() - 1
    fig_cum.add_trace(go.Scatter(
        x=stock_cum["Date"], y=stock_cum["NIFTY Cumulative"],
        name="NIFTY 50", line=dict(color="#FF9900"),
    ))
fig_cum.update_layout(title=f"{selected_symbol} — Cumulative Returns",
                      yaxis_tickformat=".0%")
st.plotly_chart(fig_cum, use_container_width=True)
st.caption("Illustrates the total return if you had invested at the start of the selected period. Useful for long-term performance comparison against the benchmark.")

# ── 4. Rolling Volatility (21-day) ───────────────────────────────
st.subheader("Rolling Volatility (21-day)")
stock_vol = stock.copy()
stock_vol["Stock Vol"] = stock_vol["Return"].rolling(21).std() * np.sqrt(252)
fig_vol = go.Figure()
fig_vol.add_trace(go.Scatter(
    x=stock_vol["Date"], y=stock_vol["Stock Vol"],
    name=selected_symbol, line=dict(color="#00FFFF"),
))
if compare_benchmark:
    stock_vol["NIFTY Vol"] = stock_vol["NIFTY Return"].rolling(21).std() * np.sqrt(252)
    fig_vol.add_trace(go.Scatter(
        x=stock_vol["Date"], y=stock_vol["NIFTY Vol"],
        name="NIFTY 50", line=dict(color="#FF9900"),
    ))
fig_vol.update_layout(title=f"{selected_symbol} — Annualized Rolling Volatility",
                      yaxis_tickformat=".0%")
st.plotly_chart(fig_vol, use_container_width=True)
st.caption("Shows how risk (volatility) changes over time. Higher peaks mean the stock was experiencing wilder price swings during that period.")

# ── 5. Drawdowns ─────────────────────────────────────────────────
st.subheader("Drawdowns")
wealth = (1 + stock["Return"]).cumprod()
drawdown = wealth / wealth.cummax() - 1
fig_dd = go.Figure()
fig_dd.add_trace(go.Scatter(
    x=stock["Date"], y=drawdown, fill="tozeroy",
    name=selected_symbol, line=dict(color="#FF0055"),
))
if compare_benchmark:
    bm_wealth = (1 + stock["NIFTY Return"]).cumprod()
    bm_dd = bm_wealth / bm_wealth.cummax() - 1
    fig_dd.add_trace(go.Scatter(
        x=stock["Date"], y=bm_dd, name="NIFTY 50",
        line=dict(color="#FF9900"),
    ))
fig_dd.update_layout(title=f"{selected_symbol} — Drawdowns",
                     yaxis_tickformat=".0%")
st.plotly_chart(fig_dd, use_container_width=True)
st.caption("Visualizes the percentage drop from the stock's highest peak. Deeper, wider red areas indicate periods of significant loss and long recovery times.")

# ── 6. Return Distribution ──────────────────────────────────────
st.subheader("Return Distribution")
fig_dist = px.histogram(
    stock, x="Return", nbins=80,
    title=f"{selected_symbol} — Return Distribution",
    marginal="box", opacity=0.7,
)
fig_dist.update_layout(xaxis_tickformat=".1%")
st.plotly_chart(fig_dist, use_container_width=True)
st.caption("A histogram showing the frequency of different daily returns. A wider bell shape means higher risk, while a narrow peak means consistent, low-volatility returns.")
