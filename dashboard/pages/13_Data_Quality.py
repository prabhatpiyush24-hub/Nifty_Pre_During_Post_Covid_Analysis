"""Data Quality and Return Verification."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

dashboard_directory = Path(__file__).resolve().parents[1]
if str(dashboard_directory) not in sys.path:
    sys.path.insert(0, str(dashboard_directory))

from utils import apply_custom_theme, load_audit


st.title("Data Quality and Return Verification")
apply_custom_theme()
summary, audit, issues = load_audit()
if summary["status"] == "PASS":
    st.success("PASS — all persisted analysis returns have passed formula verification.")
else:
    st.error("FAIL — do not rely on research outputs until the underlying audit is resolved.")

cards = st.columns(4)
cards[0].metric("Eligible companies", summary["eligible_companies"], help="Total number of companies included in the dataset.")
cards[1].metric("Aligned rows", f"{summary['benchmark_aligned_company_rows']:,}", help="Rows successfully aligned with benchmark trading days.")
cards[2].metric("Valid return rows", f"{summary['valid_daily_return_rows']:,}", help="Usable return data points without errors.")
cards[3].metric("Maximum formula error", f"{summary['max_formula_error']:.2e}", help="Largest discrepancy found during calculation audits (ideally 0).")

st.subheader("Methodology")
st.markdown("""
1. Load only the 311 companies marked eligible in the master universe.
2. Validate required fields, duplicate dates, price positivity, volume, and OHLC consistency.
3. Align each stock to the NIFTY 50 benchmark calendar before calculating returns.
4. Calculate simple, log, and excess returns from adjusted closing prices.
5. Accept a return into analytics only when it spans exactly one benchmark trading session.
6. Recalculate and compare every persisted return formula; no missing price is filled or inferred.
""")

st.subheader("Flagged sessions")
if issues.empty:
    st.info("No data-quality issues were identified.")
else:
    st.warning("Warnings are deliberately retained rather than hidden. They are excluded from return analytics without price imputation.")
    st.dataframe(issues, hide_index=True, use_container_width=True)

st.subheader("Company-level audit")
status_filter = st.multiselect("Status", sorted(audit["Status"].unique()), default=sorted(audit["Status"].unique()))
filtered = audit.loc[audit["Status"].isin(status_filter)]
st.dataframe(filtered.style.format({"Maximum Return Formula Error": "{:.2e}", "Maximum Log Return Formula Error": "{:.2e}", "Maximum Excess Return Formula Error": "{:.2e}"}), hide_index=True, use_container_width=True)
with st.expander("Audit metadata"):
    st.json(summary)
