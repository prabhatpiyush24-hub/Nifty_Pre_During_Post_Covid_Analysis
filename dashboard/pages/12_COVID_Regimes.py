"""COVID Regime Analysis — pre-COVID, March 2020 shock, and post-COVID changes."""

from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

dashboard_directory = Path(__file__).resolve().parents[1]
if str(dashboard_directory) not in sys.path:
    sys.path.insert(0, str(dashboard_directory))

from utils import apply_custom_theme, cumulative_wealth, load_company_comparison, load_daily_returns, load_sector_daily, load_sector_metrics


st.title("COVID Regime Analysis")
st.caption("Pre-COVID: 2015-01-01 to 2020-02-28 • COVID shock: March 2020 • Post-COVID: 2020-04-01 to 2025-12-31")
apply_custom_theme()

sector_metrics = load_sector_metrics()
sector_daily = load_sector_daily()
company_comparison = load_company_comparison()
daily = load_daily_returns()

st.subheader("Sector return and risk changed materially after COVID")
measure = st.radio("Compare", ["CAGR", "Annualized Volatility", "Sharpe Ratio (Rf=6.5%)", "Maximum Drawdown"], horizontal=True)
display = sector_metrics.loc[sector_metrics["Regime"].isin(["Pre-COVID", "Post-COVID"])]
fig = px.bar(display, x="Industry", y=measure, color="Regime", barmode="group", title=f"Equal-weight industry {measure}: pre- versus post-COVID")
fig.update_xaxes(tickangle=-40)
st.plotly_chart(fig, use_container_width=True)
st.caption("Compares industry-level performance metrics before and after the March 2020 COVID shock.")

st.subheader("Industry wealth paths")
available_industries = sorted(sector_daily["Industry"].unique())
selected_industries = st.multiselect("Select industries", available_industries, default=available_industries[: min(6, len(available_industries))])
if selected_industries:
    sector_path = cumulative_wealth(sector_daily.loc[sector_daily["Industry"].isin(selected_industries)], "Return", "Industry")
    st.plotly_chart(px.line(sector_path, x="Date", y="Wealth Index", color="Industry", title="Growth of ₹100 by equal-weight industry"), use_container_width=True)
    st.caption("Cumulative wealth growth of selected industries across all regimes, clearly showing the March 2020 dip.")

st.subheader("Company-level post-COVID change")
industry = st.selectbox("Filter industry", ["All industries", *available_industries])
sort_column = st.selectbox("Rank by change in", ["Change in CAGR", "Change in Annualized Volatility", "Change in Sharpe Ratio (Rf=6.5%)", "Change in Maximum Drawdown"])
comparison = company_comparison if industry == "All industries" else company_comparison.loc[company_comparison["Industry"] == industry]
comparison = comparison.sort_values(sort_column, ascending=False).head(30)
st.dataframe(
    comparison[["Symbol", "Company Name", "Industry", "Pre-COVID CAGR", "Post-COVID CAGR", "Change in CAGR", "Pre-COVID Annualized Volatility", "Post-COVID Annualized Volatility", "Change in Annualized Volatility"]].style.format(
        {"Pre-COVID CAGR": "{:.2%}", "Post-COVID CAGR": "{:.2%}", "Change in CAGR": "{:+.2%}", "Pre-COVID Annualized Volatility": "{:.2%}", "Post-COVID Annualized Volatility": "{:.2%}", "Change in Annualized Volatility": "{:+.2%}"}
    ),
    hide_index=True,
    use_container_width=True,
)

st.subheader("March 2020 shock")
shock = daily.loc[daily["Regime"] == "COVID Shock (Mar 2020)"].groupby("Date", as_index=False).agg(Return=("Return", "mean"), **{"NIFTY Return": ("NIFTY Return", "first")})
shock = cumulative_wealth(shock, "Return").rename(columns={"Wealth Index": "Equal-weight universe"})
benchmark = cumulative_wealth(shock[["Date", "NIFTY Return"]], "NIFTY Return").rename(columns={"Wealth Index": "NIFTY 50"})
shock_chart = shock[["Date", "Equal-weight universe"]].merge(benchmark[["Date", "NIFTY 50"]], on="Date").melt("Date", var_name="Series", value_name="Wealth Index")
st.plotly_chart(px.line(shock_chart, x="Date", y="Wealth Index", color="Series", title="March 2020: growth of ₹100"), use_container_width=True)
st.caption("Focuses strictly on the severe market drop during March 2020, comparing the universe average against the NIFTY 50.")
