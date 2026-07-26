"""PCA — Principal Component Analysis of market structure."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

dashboard_directory = Path(__file__).resolve().parents[1]
if str(dashboard_directory) not in sys.path:
    sys.path.insert(0, str(dashboard_directory))

from utils import apply_custom_theme, load_company_metrics, load_daily_returns, run_pca
from ai_core import render_ai_chat

st.title("Principal Component Analysis")
st.caption(
    "Dimensionality reduction of the cross-sectional return matrix "
    "to understand market structure and common risk factors"
)
apply_custom_theme()

with st.expander("ℹ️ Understanding PCA (Principal Component Analysis)"):
    st.markdown("""
    - **What is PCA?** It's a technique to simplify complex data. Instead of looking at 311 stocks, PCA finds a few "Principal Components" (synthetic factors) that explain most of the market's movement.
    - **Explained Variance**: Tells you how much of the total market movement is captured by a specific component. If PC1 explains 40%, it means 40% of all stock movements can be attributed to this single hidden factor (often the general market trend).
    - **PC1 vs PC2**: These are the first two most important factors. Plotting them shows which stocks behave similarly.
    - **Loadings**: Indicates how strongly a stock is connected to a principal component. A high positive loading means the stock moves strongly with that component.
    """)

daily = load_daily_returns()
metrics = load_company_metrics()
full = metrics.loc[metrics["Regime"] == "Full Sample"].copy()

# Pivot returns to wide format (Date × Symbol)
returns_wide = daily.pivot_table(index="Date", columns="Symbol", values="Return")

n_components = st.slider(
    "Number of components", min_value=2,
    max_value=min(20, returns_wide.shape[1] - 1), value=10,
)
explained, transformed, loadings = run_pca(returns_wide, n_components)

# ── Explained variance ───────────────────────────────────────────
st.subheader("Explained Variance")
left, right = st.columns(2)
with left:
    fig_scree = px.bar(
        explained, x="Component", y="Explained Variance Ratio",
        title="Scree Plot: Variance Explained by Each Component",
    )
    fig_scree.update_layout(yaxis_tickformat=".1%")
    st.plotly_chart(fig_scree, use_container_width=True)
    st.caption("Shows how much market variance is explained by each individual principal component.")
with right:
    fig_cum = px.line(
        explained, x="Component", y="Cumulative Variance",
        title="Cumulative Variance Explained", markers=True,
    )
    fig_cum.update_layout(yaxis_tickformat=".1%")
    st.plotly_chart(fig_cum, use_container_width=True)
    st.caption("Shows the running total of variance explained as you add more components.")

st.info(
    f"The first **{n_components}** components explain "
    f"**{explained['Cumulative Variance'].iloc[-1]:.1%}** "
    f"of total return variance."
)

st.info("""
**Quant Explainer: Explained Variance**
In institutional quantitative finance, PCA is used to extract hidden "Risk Factors" from the market. 
- **PC1 (Principal Component 1)** usually represents the broader market movement (e.g., the NIFTY 50 itself). If PC1 explains 40% of variance, it means 40% of all stock volatility is just stocks moving with the market.
- **PC2, PC3, etc.** often map to sector-specific factors, size factors (large vs small cap), or momentum factors.
*By hedging out these major components, quants isolate pure idiosyncratic (stock-specific) returns, known as statistical arbitrage.*
""")

# ── PC1 vs PC2 scatter ───────────────────────────────────────────
st.subheader("PC1 vs PC2 — Market Structure")
symbols = loadings.index.tolist()
pc_df = pd.DataFrame({
    "Symbol": symbols,
    "PC1 Loading": loadings["PC1"].values,
    "PC2 Loading": loadings["PC2"].values,
})
pc_df = pc_df.merge(
    full[["Symbol", "Company Name", "Industry", "Quantitative Cluster"]],
    on="Symbol", how="left",
)

color_by = st.radio("Color by", ["Industry", "Quantitative Cluster"],
                    horizontal=True)
fig_pca = px.scatter(
    pc_df, x="PC1 Loading", y="PC2 Loading", color=color_by,
    hover_data=["Symbol", "Company Name", "Industry"],
    title="Company Loadings on PC1 vs PC2",
)
st.plotly_chart(fig_pca, use_container_width=True)
st.caption("Scatter plot of companies mapped by the two most dominant market factors. Companies close together behave similarly.")

# ── Loading analysis ─────────────────────────────────────────────
st.subheader("Loading Analysis")
selected_pc = st.selectbox(
    "Select component", [f"PC{i+1}" for i in range(n_components)]
)
pc_loadings = loadings[selected_pc].sort_values()

left, right = st.columns(2)
with left:
    st.markdown(f"**Top 15 positive loadings — {selected_pc}**")
    top_pos = (
        pc_loadings.nlargest(15)
        .reset_index()
        .rename(columns={"index": "Symbol", selected_pc: "Loading"})
    )
    fig_pos = px.bar(
        top_pos, x="Loading", y="Symbol", orientation="h",
        title=f"{selected_pc}: Largest Positive Loadings",
    )
    fig_pos.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_pos, use_container_width=True)
    st.caption("Companies that move most strongly in the same direction as this component.")
with right:
    st.markdown(f"**Top 15 negative loadings — {selected_pc}**")
    top_neg = (
        pc_loadings.nsmallest(15)
        .reset_index()
        .rename(columns={"index": "Symbol", selected_pc: "Loading"})
    )
    fig_neg = px.bar(
        top_neg, x="Loading", y="Symbol", orientation="h",
        title=f"{selected_pc}: Largest Negative Loadings",
        color_discrete_sequence=["crimson"],
    )
    fig_neg.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_neg, use_container_width=True)
    st.caption("Companies that move most strongly in the opposite direction of this component.")

# ── Interactive 3D PCA visualization ─────────────────────────────
st.subheader("Interactive PCA Visualization")
if n_components >= 3:
    pc_df["PC3 Loading"] = loadings["PC3"].values
    fig_3d = px.scatter_3d(
        pc_df, x="PC1 Loading", y="PC2 Loading", z="PC3 Loading",
        color=color_by, hover_data=["Symbol", "Company Name"],
        title="3D PCA: Company Loadings on PC1, PC2, PC3",
    )
    fig_3d.update_layout(height=600)
    st.plotly_chart(fig_3d, use_container_width=True)
    st.info("""
    **Terminal Explainer: 3D Principal Component Analysis**
    - **What you're seeing**: This 3D cloud maps how stocks behave relative to the broader market's hidden factors.
    - **How to read it**: Stocks plotted close to each other in this 3D space share highly similar return profiles and risk exposures, regardless of their official industry classification. Outliers (dots far away from the center cluster) are idiosyncratic stocks that move independently from the broader market.
    """)
else:
    st.info("Select at least 3 components to view the 3D visualization.")

render_ai_chat(
    context_data=f"The user is viewing PCA Analysis. Explained Variance Ratios for the selected components: {var.to_dict()}.",
    unique_key="pca_bottom"
)
