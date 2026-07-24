"""Portfolio Optimization — construction and investment analysis."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

dashboard_directory = Path(__file__).resolve().parents[1]
if str(dashboard_directory) not in sys.path:
    sys.path.insert(0, str(dashboard_directory))

from utils import (
    apply_custom_theme, cumulative_wealth, efficient_frontier_points, load_company_metrics,
    load_daily_returns, portfolio_summary, portfolio_weights,
    selected_regime_returns, to_number, to_percent, TRADING_DAYS,
)

st.title("Portfolio Optimization")
st.caption(
    "Long-only historical optimization. "
    "This is research tooling, not an investment recommendation."
)
apply_custom_theme()

daily = load_daily_returns()
metrics = load_company_metrics()
full = metrics.loc[metrics["Regime"] == "Full Sample"].sort_values(
    "Sharpe Ratio (Rf=6.5%)", ascending=False
)
symbols = sorted(full["Symbol"])
default_symbols = full["Symbol"].head(8).tolist()

# ── Controls ─────────────────────────────────────────────────────
left, right, third = st.columns(3)
with left:
    regime = st.selectbox(
        "Return history",
        ["Full Sample", "Pre-COVID", "Post-COVID", "COVID Shock (Mar 2020)"],
    )
with right:
    method = st.selectbox(
        "Portfolio method",
        ["Equal Weight", "Minimum Variance", "Maximum Sharpe"],
    )
with third:
    risk_free = st.number_input(
        "Annual risk-free rate",
        min_value=0.0, max_value=0.20, value=0.0, step=0.005, format="%.3f",
    )

selected = st.multiselect(
    "Companies (2–30)", symbols, default=default_symbols, max_selections=30
)
max_weight = st.slider(
    "Maximum individual weight",
    min_value=0.10, max_value=1.00, value=0.35, step=0.05,
)
if len(selected) < 2:
    st.info("Select at least two companies to calculate a portfolio.")
    st.stop()

returns_frame = selected_regime_returns(
    daily.loc[daily["Symbol"].isin(selected)], regime
)
returns = returns_frame.pivot(
    index="Date", columns="Symbol", values="Return"
).dropna()
benchmark = (
    returns_frame.drop_duplicates("Date")
    .set_index("Date")["NIFTY Return"]
    .reindex(returns.index)
)
try:
    weights = portfolio_weights(returns, method, risk_free, max_weight)
except ValueError as error:
    st.error(str(error))
    st.stop()

# ── Portfolio metrics ────────────────────────────────────────────
portfolio_returns = returns.mul(weights, axis=1).sum(axis=1)
summary = portfolio_summary(portfolio_returns, benchmark, risk_free)

cards = st.columns(5)
cards[0].metric("Portfolio Return", to_percent(summary["Annualized Return"]), help="Annualized return of the selected portfolio.")
cards[1].metric("Portfolio Risk", to_percent(summary["Annualized Volatility"]), help="Annualized volatility (risk) of the portfolio.")
cards[2].metric("Sharpe Ratio", to_number(summary["Sharpe Ratio"]), help="Risk-adjusted return (Return / Risk).")
cards[3].metric("Max Drawdown", to_percent(summary["Maximum Drawdown"]), help="Largest peak-to-trough decline.")
cards[4].metric("Beta to NIFTY 50", to_number(summary["Beta to NIFTY 50"]), help="Portfolio sensitivity to the NIFTY 50 index.")

# ── Weights and Wealth chart ─────────────────────────────────────
left, right = st.columns([1, 2])
with left:
    st.subheader("Portfolio Weights")
    st.dataframe(
        weights.sort_values(ascending=False)
        .rename_axis("Symbol").reset_index()
        .style.format({"Weight": "{:.2%}"}),
        hide_index=True, use_container_width=True,
    )
with right:
    pf = pd.DataFrame({
        "Date": returns.index,
        "Portfolio": portfolio_returns.to_numpy(),
        "NIFTY 50": benchmark.to_numpy(),
    })
    p_path = cumulative_wealth(pf[["Date", "Portfolio"]], "Portfolio").rename(
        columns={"Wealth Index": "Portfolio"}
    )
    b_path = cumulative_wealth(pf[["Date", "NIFTY 50"]], "NIFTY 50").rename(
        columns={"Wealth Index": "NIFTY 50"}
    )
    chart = p_path.merge(b_path, on="Date").melt(
        "Date", var_name="Series", value_name="Wealth Index"
    )
    st.plotly_chart(
        px.line(chart, x="Date", y="Wealth Index", color="Series",
                title="Growth of ₹100"),
        use_container_width=True,
    )
    st.caption("Shows the hypothetical growth of a ₹100 investment in this portfolio versus the NIFTY 50.")

# ── Asset Allocation Pie ─────────────────────────────────────────
st.subheader("Asset Allocation")
nonzero = weights[weights > 0.001].sort_values(ascending=False)
fig_pie = px.pie(
    values=nonzero.values, names=nonzero.index,
    title=f"{method} — Asset Allocation",
)
st.plotly_chart(fig_pie, use_container_width=True)
st.caption("Visual breakdown of how capital is distributed among the selected companies.")

# ── Efficient Frontier ───────────────────────────────────────────
st.subheader("Efficient Frontier")
st.caption("2,000 random long-only portfolios with marked optimal portfolios")
frontier = efficient_frontier_points(returns, n_portfolios=2000, risk_free=risk_free)

fig_ef = px.scatter(
    frontier, x="Volatility", y="Return", color="Sharpe Ratio",
    color_continuous_scale="Viridis",
    title="Efficient Frontier — Random Portfolios", opacity=0.5,
)
fig_ef.update_layout(
    xaxis_tickformat=".1%", yaxis_tickformat=".1%",
    xaxis_title="Annualized Volatility", yaxis_title="Annualized Return",
)

# Mark current portfolio
fig_ef.add_trace(go.Scatter(
    x=[summary["Annualized Volatility"]], y=[summary["Annualized Return"]],
    mode="markers+text", name=method,
    marker=dict(size=15, color="red", symbol="star"),
    text=[method], textposition="top center",
))

# Mark other optimal portfolios
for alt_method in ["Equal Weight", "Minimum Variance", "Maximum Sharpe"]:
    if alt_method == method:
        continue
    try:
        alt_w = portfolio_weights(returns, alt_method, risk_free, max_weight)
        alt_ret = returns.mul(alt_w, axis=1).sum(axis=1)
        alt_s = portfolio_summary(alt_ret, benchmark, risk_free)
        fig_ef.add_trace(go.Scatter(
            x=[alt_s["Annualized Volatility"]], y=[alt_s["Annualized Return"]],
            mode="markers+text", name=alt_method,
            marker=dict(size=12, symbol="diamond"),
            text=[alt_method], textposition="top center",
        ))
    except ValueError:
        pass

st.plotly_chart(fig_ef, use_container_width=True)
st.caption("Plots 2,000 random portfolios to form the Efficient Frontier. The stars/diamonds highlight the theoretically optimal portfolios.")

# ── Portfolio Comparison Table ───────────────────────────────────
st.subheader("Portfolio Comparison")
comparison_rows = []
for comp_method in ["Equal Weight", "Minimum Variance", "Maximum Sharpe"]:
    try:
        comp_w = portfolio_weights(returns, comp_method, risk_free, max_weight)
        comp_ret = returns.mul(comp_w, axis=1).sum(axis=1)
        comp_s = portfolio_summary(comp_ret, benchmark, risk_free)
        comp_s["Method"] = comp_method
        comparison_rows.append(comp_s)
    except ValueError:
        pass

if comparison_rows:
    comparison = pd.DataFrame(comparison_rows)[
        ["Method", "Annualized Return", "Annualized Volatility",
         "Sharpe Ratio", "Maximum Drawdown", "Beta to NIFTY 50"]
    ]
    st.dataframe(
        comparison.style.format({
            "Annualized Return": "{:.2%}",
            "Annualized Volatility": "{:.2%}",
            "Sharpe Ratio": "{:.2f}",
            "Maximum Drawdown": "{:.2%}",
            "Beta to NIFTY 50": "{:.2f}",
        }),
        hide_index=True, use_container_width=True,
    )

st.caption(
    f"Optimization used {len(returns):,} synchronized daily observations. "
    f"The effective maximum weight is at least 1/N to keep the optimization feasible."
)
