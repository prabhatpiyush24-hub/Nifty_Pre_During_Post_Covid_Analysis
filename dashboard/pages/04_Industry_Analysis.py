"""Industry Analysis — composition, performance, and comparison across industries."""

from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

dashboard_directory = Path(__file__).resolve().parents[1]
if str(dashboard_directory) not in sys.path:
    sys.path.insert(0, str(dashboard_directory))

from utils import apply_custom_theme, cumulative_wealth, load_daily_returns, load_sector_daily, load_sector_metrics

st.title("Industry Analysis")
st.caption(
    "Industry returns are equal-weight averages of eligible company returns, "
    "not market-cap-weighted sector indices."
)
apply_custom_theme()

with st.expander("ℹ️ How to read this dashboard"):
    st.markdown("""
    - **Industry Composition**: Shows the number of companies in each industry.
    - **Industry Average Returns**: Shows the annualized growth rate (CAGR) averaged across companies in the industry.
    - **Risk-Return Map**: Plots each industry on a scatter plot. The ideal position is top-left (high return, low risk).
    """)

metrics = load_sector_metrics()
sector_daily = load_sector_daily()
daily = load_daily_returns()
regime = st.selectbox("Regime", ["Full Sample", "Pre-COVID",
                                  "COVID Shock (Mar 2020)", "Post-COVID"])
display = metrics.loc[metrics["Regime"] == regime].copy()

# ── Industry composition ─────────────────────────────────────────
st.subheader("Industry Composition")
composition = (
    daily.groupby("Industry", as_index=False)["Symbol"]
    .nunique()
    .rename(columns={"Symbol": "Companies"})
    .sort_values("Companies", ascending=False)
)
fig_comp = px.bar(
    composition, x="Industry", y="Companies",
    title="Number of Companies per Industry",
    color="Companies", color_continuous_scale="Viridis",
)
fig_comp.update_xaxes(tickangle=-40)
st.plotly_chart(fig_comp, use_container_width=True)
st.caption("Shows the number of valid companies representing each industry in the dataset.")

# ── Industry returns and volatility ──────────────────────────────
left, right = st.columns(2)
with left:
    st.subheader("Industry Average Returns")
    fig_ret = px.bar(
        display.sort_values("CAGR", ascending=False),
        x="Industry", y="CAGR", color="CAGR",
        title=f"{regime}: Industry CAGR",
        color_continuous_scale="RdYlGn",
    )
    fig_ret.update_xaxes(tickangle=-40)
    fig_ret.update_layout(yaxis_tickformat=".1%")
    st.plotly_chart(fig_ret, use_container_width=True)
    st.caption("The annualized growth rate (CAGR) averaged across all companies within each industry.")
with right:
    st.subheader("Industry Volatility")
    fig_vol = px.bar(
        display.sort_values("Annualized Volatility", ascending=False),
        x="Industry", y="Annualized Volatility",
        color="Annualized Volatility",
        title=f"{regime}: Industry Volatility",
        color_continuous_scale="Reds",
    )
    fig_vol.update_xaxes(tickangle=-40)
    fig_vol.update_layout(yaxis_tickformat=".1%")
    st.plotly_chart(fig_vol, use_container_width=True)
    st.caption("The average price volatility (risk) for companies within each industry.")

# ── Risk-return map ──────────────────────────────────────────────
st.subheader("Risk-Return Map")
st.plotly_chart(
    px.scatter(
        display, x="Annualized Volatility", y="CAGR",
        size="Companies", color="Industry",
        hover_data=["Sharpe Ratio (Rf=6.5%)", "Maximum Drawdown",
                     "Beta to NIFTY 50"],
        title=f"{regime}: Return vs Risk",
    ),
    use_container_width=True,
)
st.caption("Plots each industry's average return against its average risk. The ideal position is the top-left (high return, low risk).")

# ── Best and worst performing ────────────────────────────────────
st.subheader("Best and Worst Performing Industries")
left, right = st.columns(2)
with left:
    st.markdown("**Top 5 by CAGR**")
    top5 = display.nlargest(5, "CAGR")[
        ["Industry", "Companies", "CAGR", "Sharpe Ratio (Rf=6.5%)"]
    ]
    st.dataframe(
        top5.style.format({"CAGR": "{:.2%}", "Sharpe Ratio (Rf=6.5%)": "{:.2f}"}),
        hide_index=True, use_container_width=True,
    )
with right:
    st.markdown("**Bottom 5 by CAGR**")
    bot5 = display.nsmallest(5, "CAGR")[
        ["Industry", "Companies", "CAGR", "Sharpe Ratio (Rf=6.5%)"]
    ]
    st.dataframe(
        bot5.style.format({"CAGR": "{:.2%}", "Sharpe Ratio (Rf=6.5%)": "{:.2f}"}),
        hide_index=True, use_container_width=True,
    )

# ── Industry scorecard ──────────────────────────────────────────
st.subheader("Industry Scorecard")
scorecard = display.sort_values("Sharpe Ratio (Rf=6.5%)", ascending=False)[
    ["Industry", "Companies", "CAGR", "Annualized Volatility",
     "Sharpe Ratio (Rf=6.5%)", "Maximum Drawdown", "Beta to NIFTY 50",
     "Annualized Alpha (Rf=6.5%)"]
]
st.dataframe(
    scorecard.style.format({
        "CAGR": "{:.2%}", "Annualized Volatility": "{:.2%}",
        "Sharpe Ratio (Rf=6.5%)": "{:.2f}", "Maximum Drawdown": "{:.2%}",
        "Beta to NIFTY 50": "{:.2f}", "Annualized Alpha (Rf=6.5%)": "{:.2%}",
    }),
    hide_index=True, use_container_width=True,
)

# ── Industry wealth paths ───────────────────────────────────────
st.subheader("Industry Wealth Paths")
all_industries = sorted(sector_daily["Industry"].unique())
selected = st.multiselect(
    "Select industries", all_industries,
    default=all_industries[: min(5, len(all_industries))],
)
if selected:
    path = sector_daily.loc[sector_daily["Industry"].isin(selected)]
    if regime != "Full Sample":
        path = path.loc[path["Regime"] == regime]
    path = cumulative_wealth(path, "Return", "Industry")
    st.plotly_chart(
        px.line(path, x="Date", y="Wealth Index", color="Industry",
                title="Growth of ₹100"),
        use_container_width=True,
    )
    st.caption("Cumulative growth of a ₹100 investment in an equal-weight portfolio of the selected industries.")
