"""Downloads & Reports — export research outputs."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

dashboard_directory = Path(__file__).resolve().parents[1]
if str(dashboard_directory) not in sys.path:
    sys.path.insert(0, str(dashboard_directory))

from utils import (
    apply_custom_theme, load_audit, load_clusters, load_company_comparison, load_company_metrics,
    load_correlation, load_correlation_pairs, load_daily_returns,
    load_market_metrics, load_sector_metrics,
)

st.title("Downloads & Reports")
st.caption(
    "Export research outputs as CSV files for further analysis or "
    "dissertation use"
)
apply_custom_theme()


def _csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


# ── Company metrics ──────────────────────────────────────────────
st.subheader("📊 Company Performance Metrics")
st.markdown(
    "Full performance metrics for all 311 companies across all regimes "
    "(CAGR, volatility, Sharpe, beta, alpha, etc.)"
)
company_metrics = load_company_metrics()
st.download_button(
    "Download Company Metrics (CSV)", _csv(company_metrics),
    "company_regime_metrics.csv", "text/csv",
)

# ── Industry metrics ─────────────────────────────────────────────
st.subheader("🏭 Industry Performance Metrics")
st.markdown("Equal-weight industry performance metrics across all regimes")
sector_metrics = load_sector_metrics()
st.download_button(
    "Download Industry Metrics (CSV)", _csv(sector_metrics),
    "sector_regime_metrics.csv", "text/csv",
)

# ── Benchmark metrics ────────────────────────────────────────────
st.subheader("📈 NIFTY 50 Benchmark Metrics")
market_metrics = load_market_metrics()
st.download_button(
    "Download Benchmark Metrics (CSV)", _csv(market_metrics),
    "market_regime_metrics.csv", "text/csv",
)

# ── COVID comparison ─────────────────────────────────────────────
st.subheader("🦠 Pre/Post COVID Comparison")
st.markdown("Company-level pre-COVID vs post-COVID performance changes")
comparison = load_company_comparison()
st.download_button(
    "Download COVID Comparison (CSV)", _csv(comparison),
    "company_covid_comparison.csv", "text/csv",
)

# ── Correlation ──────────────────────────────────────────────────
st.subheader("🔗 Correlation Analysis")
left, right = st.columns(2)
with left:
    pre_corr = load_correlation("Pre-COVID")
    st.download_button(
        "Download Pre-COVID Correlation (CSV)",
        pre_corr.to_csv().encode("utf-8"),
        "pre_covid_correlation.csv", "text/csv",
    )
with right:
    post_corr = load_correlation("Post-COVID")
    st.download_button(
        "Download Post-COVID Correlation (CSV)",
        post_corr.to_csv().encode("utf-8"),
        "post_covid_correlation.csv", "text/csv",
    )

pairs = load_correlation_pairs()
st.download_button(
    "Download Correlation Pair Changes (CSV)", _csv(pairs),
    "correlation_changes.csv", "text/csv",
)

# ── Clusters ─────────────────────────────────────────────────────
st.subheader("🎯 Cluster Assignments")
clusters = load_clusters()
st.download_button(
    "Download Cluster Assignments (CSV)", _csv(clusters),
    "quantitative_clusters.csv", "text/csv",
)

# ── Data quality ─────────────────────────────────────────────────
st.subheader("✅ Data Quality Audit")
summary, audit, issues = load_audit()
left, right = st.columns(2)
with left:
    st.download_button(
        "Download Audit Report (CSV)", _csv(audit),
        "return_audit.csv", "text/csv",
    )
with right:
    st.download_button(
        "Download Data Quality Issues (CSV)", _csv(issues),
        "data_quality_issues.csv", "text/csv",
    )

# ── Daily returns (large) ───────────────────────────────────────
st.subheader("📁 Daily Returns Dataset")
st.markdown(
    "⚠️ **Large file**: verified daily returns for all 311 companies. "
    "Download may take a moment."
)
daily_returns = load_daily_returns()
st.download_button(
    "Download Daily Returns (CSV)", _csv(daily_returns),
    "daily_returns.csv", "text/csv",
)

# ── Research summary ─────────────────────────────────────────────
st.markdown("---")
st.subheader("📝 Research Summary")
summary_text = f"""# NIFTY 500 Quantitative Research Summary

## Dataset
- **Study Period**: {summary['study_period']['start']} to {summary['study_period']['end']}
- **Eligible Companies**: {summary['eligible_companies']}
- **Benchmark**: NIFTY 50
- **Valid Daily Return Observations**: {summary['valid_daily_return_rows']:,}
- **Data Quality Status**: {summary['status']}

## COVID Regimes
- **Pre-COVID**: {summary['covid_regimes']['pre_covid']}
- **COVID Shock**: {summary['covid_regimes']['covid_shock']}
- **Post-COVID**: {summary['covid_regimes']['post_covid']}

## Methodology
{summary['method']}

## Quality Assurance
- Companies with complete coverage: {summary['companies_with_complete_daily_return_coverage']}
- Companies with flagged sessions: {summary['companies_with_flagged_missing_sessions']}
- Maximum formula error: {summary['max_formula_error']:.2e}
- Warnings retained: {summary['warnings']}
- Errors: {summary['errors']}
"""
st.download_button(
    "Download Research Summary (Markdown)",
    summary_text.encode("utf-8"),
    "research_summary.md", "text/markdown",
)
st.markdown(summary_text)
