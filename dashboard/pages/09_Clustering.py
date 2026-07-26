"""Clustering Analysis — groups companies based on market behavior."""

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

from utils import apply_custom_theme, load_company_metrics
from ai_core import render_ai_chat

st.title("Clustering Analysis")
st.caption(
    "K-Means clustering of companies based on CAGR, volatility, Sharpe ratio, "
    "maximum drawdown, beta, and market correlation"
)
apply_custom_theme()

with st.expander("ℹ️ Understanding Clustering Analysis"):
    st.markdown("""
    - **Clustering (K-Means)**: An algorithm that groups companies based on similar financial characteristics (growth, volatility, risk, etc.) without knowing their industries beforehand.
    - **Why use it?** It helps find "hidden" groupings. For example, a tech stock and a pharma stock might behave exactly the same way, putting them in the same cluster.
    - **Silhouette Score**: Measures how similar an object is to its own cluster compared to other clusters. A score closer to 1 implies the clusters are distinct and well-separated.
    """)

CLUSTER_FEATURES = [
    "CAGR", "Annualized Volatility", "Sharpe Ratio (Rf=6.5%)",
    "Maximum Drawdown", "Beta to NIFTY 50", "Market Correlation",
]

metrics = load_company_metrics()
full = metrics.loc[metrics["Regime"] == "Full Sample"].copy()

# ── Cluster visualization ────────────────────────────────────────
st.subheader("Cluster Visualization")
x_axis = st.selectbox(
    "X-axis",
    ["Annualized Volatility", "Beta to NIFTY 50",
     "Maximum Drawdown", "Market Correlation"],
    index=0,
)
y_axis = st.selectbox(
    "Y-axis",
    ["CAGR", "Sharpe Ratio (Rf=6.5%)",
     "Annualized Alpha (Rf=6.5%)", "Sortino Ratio (Rf=6.5%)"],
    index=0,
)
size_col = "Market Correlation" if x_axis != "Market Correlation" else "Annualized Volatility"

fig_cluster = px.scatter(
    full, x=x_axis, y=y_axis, color="Quantitative Cluster",
    hover_data=["Symbol", "Company Name", "Industry"],
    title=f"Company Clusters: {y_axis} vs {x_axis}",
    size=size_col,
)
st.plotly_chart(fig_cluster, use_container_width=True)
st.info("""
**Quant Explainer: K-Means Clustering**
- **What you're seeing**: Companies grouped mathematically into distinct clusters based on their historical risk and return profiles.
- **How to read it**: The colors represent completely different mathematical 'DNA'. Notice how Cluster 0 might consist of high-growth tech stocks, while Cluster 1 captures slow-growing dividend stocks. Use the dropdowns to explore how these groupings separate across different metrics.
""")

# ── Cluster statistics ───────────────────────────────────────────
st.subheader("Cluster Statistics")
cluster_stats = full.groupby("Quantitative Cluster").agg(
    Companies=("Symbol", "count"),
    **{"Mean CAGR": ("CAGR", "mean")},
    **{"Mean Volatility": ("Annualized Volatility", "mean")},
    **{"Mean Sharpe": ("Sharpe Ratio (Rf=6.5%)", "mean")},
    **{"Mean Max Drawdown": ("Maximum Drawdown", "mean")},
    **{"Mean Beta": ("Beta to NIFTY 50", "mean")},
    **{"Mean Correlation": ("Market Correlation", "mean")},
).reset_index()

st.dataframe(
    cluster_stats.style.format({
        "Mean CAGR": "{:.2%}", "Mean Volatility": "{:.2%}",
        "Mean Sharpe": "{:.2f}", "Mean Max Drawdown": "{:.2%}",
        "Mean Beta": "{:.2f}", "Mean Correlation": "{:.2f}",
    }),
    hide_index=True, use_container_width=True,
)
st.info("""
**Quant Explainer: Cluster Statistics**
This table calculates the "Centroid" (average values) for each mathematical cluster. 
By looking at the Mean Beta and Mean Volatility, you can instantly categorize clusters into archetypes:
- e.g., A cluster with Beta < 0.8 and Low Volatility is the **Defensive/Value Cluster**.
- e.g., A cluster with Beta > 1.2 and High Volatility is the **High-Beta/Growth Cluster**.
""")

# ── Cluster composition and profile ──────────────────────────────
left, right = st.columns(2)
with left:
    st.subheader("Cluster Composition")
    comp = (
        full["Quantitative Cluster"]
        .value_counts()
        .reset_index()
    )
    comp.columns = ["Cluster", "Companies"]
    fig_comp = px.bar(
        comp, x="Cluster", y="Companies", color="Cluster",
        title="Number of Companies per Cluster",
    )
    st.plotly_chart(fig_comp, use_container_width=True)
    st.caption("The total count of companies assigned to each cluster.")
with right:
    st.subheader("Cluster Risk-Return Profile")
    fig_profile = px.bar(
        cluster_stats, x="Quantitative Cluster",
        y=["Mean CAGR", "Mean Volatility"],
        barmode="group",
        title="Mean Return vs Volatility by Cluster",
    )
    fig_profile.update_layout(yaxis_tickformat=".1%")
    st.plotly_chart(fig_profile, use_container_width=True)
    st.caption("Compares the average risk and return for each distinct cluster group.")

# ── Industry-cluster heatmap ─────────────────────────────────────
st.subheader("Industry-Cluster Distribution")
cross = pd.crosstab(full["Industry"], full["Quantitative Cluster"])
fig_heat = go.Figure(go.Heatmap(
    z=cross.values, x=cross.columns.tolist(), y=cross.index.tolist(),
    colorscale="YlOrRd", colorbar={"title": "Count"},
))
fig_heat.update_layout(
    title="How Industries Distribute Across Clusters",
    height=max(400, len(cross) * 22),
)
st.plotly_chart(fig_heat, use_container_width=True)
st.caption("Shows the overlap between a company's traditional industry classification and its algorithmic cluster assignment.")

# ── Silhouette score ─────────────────────────────────────────────
st.subheader("Cluster Quality")
try:
    from sklearn.metrics import silhouette_score
    from sklearn.preprocessing import StandardScaler

    X = full[CLUSTER_FEATURES].copy()
    X = X.replace([np.inf, -np.inf], np.nan).fillna(X.median())
    X_scaled = StandardScaler().fit_transform(X)
    labels = full["Quantitative Cluster"].values
    score = silhouette_score(X_scaled, labels)
    st.metric("Silhouette Score", f"{score:.3f}", help="Measures cluster separation (higher is better, max 1.0).")
    st.caption(
        "Silhouette score ranges from −1 to 1. "
        "Values above 0.2 indicate reasonable cluster separation."
    )
except Exception:
    st.info("Silhouette score could not be computed.")

# ── Cluster member explorer ──────────────────────────────────────
st.subheader("Cluster Members")
selected_cluster = st.selectbox(
    "Select cluster", sorted(full["Quantitative Cluster"].unique())
)
members = full[full["Quantitative Cluster"] == selected_cluster][
    ["Symbol", "Company Name", "Industry", "CAGR", "Annualized Volatility",
     "Sharpe Ratio (Rf=6.5%)", "Maximum Drawdown", "Beta to NIFTY 50"]
].sort_values("Sharpe Ratio (Rf=6.5%)", ascending=False)

st.dataframe(
    members.style.format({
        "CAGR": "{:.2%}", "Annualized Volatility": "{:.2%}",
        "Sharpe Ratio (Rf=6.5%)": "{:.2f}", "Maximum Drawdown": "{:.2%}",
        "Beta to NIFTY 50": "{:.2f}",
    }),
    hide_index=True, use_container_width=True,
)

render_ai_chat(
    context_data=f"The user is viewing Clustering Analysis. Currently exploring cluster: {selected_cluster}. Cluster averages: {summary.to_markdown()}",
    unique_key="clustering_bottom"
)
