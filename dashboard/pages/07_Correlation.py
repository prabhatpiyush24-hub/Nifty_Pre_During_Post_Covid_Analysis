"""Correlation Analysis — relationships between companies and industries."""

from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

dashboard_directory = Path(__file__).resolve().parents[1]
if str(dashboard_directory) not in sys.path:
    sys.path.insert(0, str(dashboard_directory))

from utils import (
    apply_custom_theme, load_company_metrics, load_correlation, load_correlation_pairs,
    load_correlation_summary, load_daily_returns, load_sector_daily,
)

st.title("Correlation Analysis")
st.caption(
    "Pairwise Pearson correlations of verified adjusted-close daily returns. "
    "March 2020 is excluded from the pre/post comparison."
)
apply_custom_theme()

with st.expander("ℹ️ Understanding Correlation"):
    st.markdown("""
    - **Pearson Correlation**: Measures the linear relationship between two variables, ranging from -1 to 1.
    - **1.0**: Perfect positive correlation (move exactly together).
    - **0.0**: No correlation (move independently).
    - **-1.0**: Perfect negative correlation (move in exact opposite directions).
    - *Note: High correlation implies less diversification benefit.*
    """)

metrics = load_company_metrics()
daily = load_daily_returns()
full = metrics.loc[metrics["Regime"] == "Full Sample"].sort_values("Symbol")
pairs = load_correlation_pairs()
summary = load_correlation_summary().merge(
    full[["Symbol", "Company Name", "Industry"]], on="Symbol", how="left"
)

# ── Correlation Matrix ───────────────────────────────────────────
st.subheader("Correlation Matrix")
regime = st.radio("Correlation regime", ["Pre-COVID", "Post-COVID"],
                  horizontal=True)
matrix = load_correlation(regime)
available_symbols = sorted(matrix.columns)
defaults = (
    summary.sort_values("Change in Average Stock Correlation", ascending=False)
    ["Symbol"].head(20).tolist()
)
selected_symbols = st.multiselect(
    "Companies in the heatmap (maximum 40)", available_symbols, default=defaults
)[:40]

if len(selected_symbols) >= 2:
    sel = matrix.loc[selected_symbols, selected_symbols]
    heatmap = go.Figure(go.Heatmap(
        z=sel.values, x=sel.columns, y=sel.index,
        colorscale="RdBu_r", zmin=-1, zmax=1,
        colorbar={"title": "Correlation"},
    ))
    heatmap.update_layout(
        title=f"{regime} return-correlation matrix",
        height=max(500, len(selected_symbols) * 24),
    )
    st.plotly_chart(heatmap, use_container_width=True)
    st.caption("A heatmap showing pairwise correlation between stocks. Red means they move together, blue means they move oppositely.")
else:
    st.info("Select at least two companies to display a correlation matrix.")

# ── Pairwise shifts and company-average ──────────────────────────
left, right = st.columns(2)
with left:
    st.subheader("Largest pairwise correlation shifts")
    st.dataframe(
        pairs.head(25).style.format({
            "Pre-COVID Correlation": "{:.2f}",
            "Post-COVID Correlation": "{:.2f}",
            "Correlation Change (Post - Pre)": "{:+.2f}",
            "Absolute Correlation Change": "{:.2f}",
        }),
        hide_index=True, use_container_width=True,
    )
with right:
    st.subheader("Company-average correlation shift")
    plot_data = summary.sort_values(
        "Change in Average Stock Correlation", ascending=False
    ).head(30)
    st.plotly_chart(
        px.bar(plot_data, x="Symbol",
               y="Change in Average Stock Correlation", color="Industry",
               title="Largest increases in average co-movement"),
        use_container_width=True,
    )
    st.caption("Highlights the industries whose average stock correlations increased the most.")

# ── Correlation and cluster map ──────────────────────────────────
st.subheader("Correlation and Cluster Map")
st.plotly_chart(
    px.scatter(
        summary,
        x="Pre-COVID Average Stock Correlation",
        y="Post-COVID Average Stock Correlation",
        color="Quantitative Cluster",
        hover_data=["Symbol", "Company Name", "Industry"],
        title="Average correlation before versus after COVID",
    ),
    use_container_width=True,
)
st.caption("Compares how a company's correlation changed from pre-COVID to post-COVID. Points above the diagonal mean correlation increased.")

# ── Industry-level correlation ───────────────────────────────────
st.markdown("---")
st.subheader("Industry-Level Correlation")
st.caption("Average pairwise correlation between equal-weight industry return series")
sector_daily = load_sector_daily()

for corr_regime in ["Pre-COVID", "Post-COVID"]:
    sector_pivot = sector_daily.loc[sector_daily["Regime"] == corr_regime].pivot_table(
        index="Date", columns="Industry", values="Return"
    )
    industry_corr = sector_pivot.corr()
    fig_ind = go.Figure(go.Heatmap(
        z=industry_corr.values, x=industry_corr.columns, y=industry_corr.index,
        colorscale="RdBu_r", zmin=-1, zmax=1,
        colorbar={"title": "Correlation"},
    ))
    fig_ind.update_layout(
        title=f"{corr_regime}: Industry Return Correlation", height=500,
    )
    st.plotly_chart(fig_ind, use_container_width=True)
    st.caption("A heatmap showing how different industries correlate with one another.")

# ── Company pairwise comparison ──────────────────────────────────
st.markdown("---")
st.subheader("Company Pairwise Comparison")
comp_symbols = sorted(full["Symbol"])
col1, col2 = st.columns(2)
with col1:
    sym_a = st.selectbox("Company A", comp_symbols, index=0)
with col2:
    sym_b = st.selectbox("Company B", comp_symbols,
                         index=min(1, len(comp_symbols) - 1))

if sym_a != sym_b:
    ret_a = daily.loc[daily["Symbol"] == sym_a, ["Date", "Return"]].rename(
        columns={"Return": sym_a}
    )
    ret_b = daily.loc[daily["Symbol"] == sym_b, ["Date", "Return"]].rename(
        columns={"Return": sym_b}
    )
    merged = ret_a.merge(ret_b, on="Date")
    corr_val = merged[sym_a].corr(merged[sym_b])
    st.metric("Pearson Correlation", f"{corr_val:.3f}", help="Linear relationship measure from -1 (opposite) to 1 (identical).")
    fig_pair = px.scatter(
        merged, x=sym_a, y=sym_b,
        title=f"{sym_a} vs {sym_b} Daily Returns (r = {corr_val:.3f})",
        opacity=0.4,
    )
    fig_pair.update_layout(xaxis_tickformat=".1%", yaxis_tickformat=".1%")
    st.plotly_chart(fig_pair, use_container_width=True)
    st.caption("A scatter plot comparing the daily returns of two specific companies to visually assess their correlation.")
else:
    st.info("Select two different companies to compare.")
