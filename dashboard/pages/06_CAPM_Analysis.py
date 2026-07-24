"""CAPM Analysis — Capital Asset Pricing Model calculations."""

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
    apply_custom_theme, capm_regression, load_company_metrics, load_daily_returns,
    load_market_metrics, to_number, to_percent, TRADING_DAYS,
)

st.title("CAPM Analysis")
st.caption(
    "Capital Asset Pricing Model — Beta estimation, Alpha estimation, "
    "Security Market Line, and regression diagnostics"
)
apply_custom_theme()

with st.expander("ℹ️ Understanding CAPM & Regression Metrics"):
    st.markdown("""
    - **Beta**: A measure of a stock's volatility in relation to the overall market (NIFTY 50). Beta > 1 means more volatile than the market, Beta < 1 means less volatile.
    - **Alpha (Ann.)**: The annualized excess return of the stock relative to the return predicted by CAPM. Positive alpha means the stock outperformed expectations.
    - **SML (Security Market Line)**: Shows the expected return of an asset based on its beta.
    - **R² (R-squared)**: The percentage of a stock's movements that can be explained by movements in the benchmark index.
    - **P-value**: Indicates the statistical significance of the Beta estimate (lower is more significant).
    """)

metrics = load_company_metrics()
daily = load_daily_returns()
market_metrics = load_market_metrics()

regime = st.selectbox("Regime", ["Full Sample", "Pre-COVID", "Post-COVID",
                                  "COVID Shock (Mar 2020)"])
display = metrics.loc[metrics["Regime"] == regime].copy()
market_row = market_metrics.loc[market_metrics["Regime"] == regime].iloc[0]
market_cagr = market_row["CAGR"]

# ── Security Market Line ─────────────────────────────────────────
st.subheader("Security Market Line (SML)")
st.markdown(
    f"**SML**: E(Rᵢ) = Rf + βᵢ × (E(Rₘ) – Rf) &nbsp;with&nbsp; "
    f"Rf = 0%, E(Rₘ) = {market_cagr:.2%}"
)

beta_min = max(display["Beta to NIFTY 50"].min() - 0.3, -0.5)
beta_max = display["Beta to NIFTY 50"].max() + 0.3
beta_range = np.linspace(beta_min, beta_max, 100)
sml_returns = beta_range * market_cagr

fig_sml = go.Figure()
fig_sml.add_trace(go.Scatter(
    x=display["Beta to NIFTY 50"], y=display["CAGR"],
    mode="markers", name="Companies",
    text=display["Symbol"],
    hovertemplate="%{text}<br>Beta: %{x:.2f}<br>CAGR: %{y:.2%}",
    marker=dict(
        size=6,
        color=display["Annualized Alpha (Rf=6.5%)"],
        colorscale="RdYlGn", showscale=True,
        colorbar=dict(title="Alpha"),
    ),
))
fig_sml.add_trace(go.Scatter(
    x=beta_range, y=sml_returns, mode="lines", name="SML",
    line=dict(color="red", dash="dash", width=2),
))
fig_sml.update_layout(
    title=f"{regime}: Security Market Line",
    xaxis_title="Beta", yaxis_title="CAGR",
    yaxis_tickformat=".0%",
)
st.plotly_chart(fig_sml, use_container_width=True)
st.caption(
    "The SML visualizes expected return for a given level of risk (Beta). "
    "Companies above the line have positive alpha (outperformed expectations), "
    "while those below have negative alpha."
)

# ── Beta and Alpha distributions ─────────────────────────────────
left, right = st.columns(2)
with left:
    st.subheader("Beta Distribution")
    fig_beta = px.histogram(
        display, x="Beta to NIFTY 50", nbins=40,
        title=f"{regime}: Distribution of Company Betas",
        marginal="box",
    )
    st.plotly_chart(fig_beta, use_container_width=True)
    st.caption("Distribution of Beta values across the dataset.")
with right:
    st.subheader("Alpha Distribution")
    fig_alpha = px.histogram(
        display, x="Annualized Alpha (Rf=6.5%)", nbins=40,
        title=f"{regime}: Distribution of Annualized Alphas",
        marginal="box",
    )
    fig_alpha.update_layout(xaxis_tickformat=".1%")
    st.plotly_chart(fig_alpha, use_container_width=True)
    st.caption("Distribution of Alpha values across the dataset.")

# ── Single-stock regression ──────────────────────────────────────
st.markdown("---")
st.subheader("Single-Stock CAPM Regression")
symbol = st.selectbox("Select company", sorted(display["Symbol"]))

stock_daily = daily[daily["Symbol"] == symbol].copy()
if regime != "Full Sample":
    stock_daily = stock_daily[stock_daily["Regime"] == regime]

stock_ret = stock_daily["Return"].to_numpy()
market_ret = stock_daily["NIFTY Return"].to_numpy()
reg = capm_regression(stock_ret, market_ret)

# Regression metrics
cards = st.columns(6)
cards[0].metric("Beta", to_number(reg["Beta"]), help="Volatility relative to benchmark.")
cards[1].metric("Alpha (Ann.)", to_percent(reg["Alpha (Annualized)"]), help="Excess annualized return.")
cards[2].metric("R²", to_number(reg["R²"]), help="Proportion of variance explained by the market.")
cards[3].metric("P-value (Beta)", f"{reg['P-value (Beta)']:.2e}", help="Statistical significance of Beta.")
cards[4].metric("Std Error", to_number(reg["Std Error (Beta)"], 4), help="Standard error of the Beta estimate.")
cards[5].metric("Residual Std", to_number(reg["Residual Std"], 4), help="Standard deviation of residuals.")

# CAPM expected return
expected_return = reg["Beta"] * market_cagr
st.info(
    f"**CAPM Expected Return** = β × E(Rₘ) = "
    f"{reg['Beta']:.2f} × {market_cagr:.2%} = {expected_return:.2%}"
)

# Regression scatter
fig_reg = go.Figure()
fig_reg.add_trace(go.Scatter(
    x=market_ret, y=stock_ret, mode="markers", name="Daily Returns",
    marker=dict(size=4, color="steelblue", opacity=0.4),
))
x_line = np.linspace(market_ret.min(), market_ret.max(), 100)
y_line = reg["Alpha (Daily)"] + reg["Beta"] * x_line
fig_reg.add_trace(go.Scatter(
    x=x_line, y=y_line, mode="lines",
    name=f"OLS: α={reg['Alpha (Daily)']:.4f}, β={reg['Beta']:.2f}",
    line=dict(color="red", width=2),
))
fig_reg.update_layout(
    title=f"{symbol} vs NIFTY 50: CAPM Regression",
    xaxis_title="NIFTY 50 Return", yaxis_title=f"{symbol} Return",
    xaxis_tickformat=".1%", yaxis_tickformat=".1%",
)
st.plotly_chart(fig_reg, use_container_width=True)
st.caption("Scatter plot of daily returns showing the line of best fit (regression). A steeper slope means higher Beta.")

# ── Stock vs Benchmark ───────────────────────────────────────────
st.subheader("Stock vs Benchmark Cumulative Performance")
stock_cum = stock_daily.copy()
stock_cum[symbol] = (1 + stock_cum["Return"]).cumprod() * 100
stock_cum["NIFTY 50"] = (1 + stock_cum["NIFTY Return"]).cumprod() * 100
chart = stock_cum[["Date", symbol, "NIFTY 50"]].melt(
    "Date", var_name="Series", value_name="Wealth Index"
)
st.plotly_chart(
    px.line(chart, x="Date", y="Wealth Index", color="Series",
            title=f"{symbol} vs NIFTY 50: Growth of ₹100"),
    use_container_width=True,
)
st.caption("Cumulative wealth growth of the selected stock compared to the NIFTY 50 benchmark.")
