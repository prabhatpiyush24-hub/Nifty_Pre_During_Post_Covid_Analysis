"""Entry point for the NIFTY 500 quantitative research dashboard."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

dashboard_directory = Path(__file__).resolve().parent
if str(dashboard_directory) not in sys.path:
    sys.path.insert(0, str(dashboard_directory))

from utils import apply_custom_theme, load_audit


st.set_page_config(page_title="QuantNifty", page_icon="📈", layout="wide")
apply_custom_theme()

summary, _, _ = load_audit()
st.title("QuantNifty")
st.caption("311 continuously eligible companies • NIFTY 50 benchmark • 2015–2025")

# Animated Quant Cover Image (CSS/SVG)
st.markdown("""
<div style="width: 100%; height: 220px; border-radius: 12px; overflow: hidden; position: relative; background: linear-gradient(135deg, #0B1120 0%, #0F172A 100%); border: 1px solid #1E293B; margin-bottom: 2rem; margin-top: 1rem; box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5);">
    <!-- Animated Grid -->
    <div style="position: absolute; inset: 0; background-image: linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px); background-size: 30px 30px; animation: panGrid 30s linear infinite;"></div>
    
    <!-- SVG Chart -->
    <svg width="100%" height="100%" viewBox="0 0 1000 200" preserveAspectRatio="none" style="position: absolute; bottom: 0;">
        <defs>
            <linearGradient id="glow" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#10B981" stop-opacity="0.3" />
                <stop offset="100%" stop-color="#10B981" stop-opacity="0.0" />
            </linearGradient>
            <filter id="blur">
                <feGaussianBlur stdDeviation="4" />
            </filter>
        </defs>
        
        <!-- Fill under the line -->
        <path class="animated-fill" d="M0,200 L0,170 L100,150 L200,165 L300,130 L400,140 L500,90 L600,110 L700,60 L800,75 L900,30 L1000,40 L1000,200 Z" fill="url(#glow)" />
        
        <!-- The glowing animated line -->
        <path class="animated-line" d="M0,170 L100,150 L200,165 L300,130 L400,140 L500,90 L600,110 L700,60 L800,75 L900,30 L1000,40" fill="none" stroke="#10B981" stroke-width="4" filter="url(#blur)" />
        <path class="animated-line" d="M0,170 L100,150 L200,165 L300,130 L400,140 L500,90 L600,110 L700,60 L800,75 L900,30 L1000,40" fill="none" stroke="#34D399" stroke-width="2" />
        
        <!-- Trendline overlay -->
        <path d="M0,180 L1000,20" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="1" stroke-dasharray="10,10" />
    </svg>
    
    <!-- Floating Data Nodes -->
    <div style="position: absolute; top: 20%; left: 15%; width: 6px; height: 6px; background: #38bdf8; border-radius: 50%; box-shadow: 0 0 15px #38bdf8; animation: pulseNode 3s ease-in-out infinite;"></div>
    <div style="position: absolute; top: 65%; left: 45%; width: 8px; height: 8px; background: #818cf8; border-radius: 50%; box-shadow: 0 0 20px #818cf8; animation: pulseNode 4s ease-in-out infinite 1s;"></div>
    <div style="position: absolute; top: 35%; left: 85%; width: 5px; height: 5px; background: #10b981; border-radius: 50%; box-shadow: 0 0 15px #10b981; animation: pulseNode 5s ease-in-out infinite 2s;"></div>

    <!-- Title Overlay -->
    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; pointer-events: none;">
        <h1 style="color: white; font-size: 3rem; margin: 0; font-weight: 800; letter-spacing: 0.1em; text-shadow: 0 4px 20px rgba(0,0,0,0.8); font-family: 'Inter', sans-serif;">QUANT<span style="color: #10B981;">NIFTY</span></h1>
        <p style="color: #94A3B8; font-size: 1rem; margin: 0; letter-spacing: 0.2em; text-transform: uppercase;">Algorithmic Research Platform</p>
    </div>

    <style>
        @keyframes panGrid {
            0% { background-position: 0 0; }
            100% { background-position: -60px 60px; }
        }
        .animated-line {
            stroke-dasharray: 2000;
            stroke-dashoffset: 2000;
            animation: drawLine 3s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }
        .animated-fill {
            opacity: 0;
            animation: fadeIn 2s ease-out forwards 1.5s;
        }
        @keyframes drawLine {
            to { stroke-dashoffset: 0; }
        }
        @keyframes fadeIn {
            to { opacity: 1; }
        }
        @keyframes pulseNode {
            0%, 100% { transform: scale(1); opacity: 0.5; }
            50% { transform: scale(1.5); opacity: 1; }
        }
    </style>
</div>
""", unsafe_allow_html=True)
if summary["status"] != "PASS":
    st.error("The data-quality gate is not passing. Do not use dashboard results until the audit is resolved.")
else:
    st.success(
        f"Verified data: {summary['eligible_companies']} companies, "
        f"{summary['valid_daily_return_rows']:,} valid daily returns, and zero return-formula errors."
    )

st.markdown(
    """
Use the sidebar to explore the complete research workflow:

- **Overview** — research period, universe coverage, benchmark comparison, and cross-sectional leaders.
- **Stock Explorer** — search any of the 311 companies with custom date ranges, benchmark comparison, and six interactive charts.
- **Benchmark Analysis** — dedicated NIFTY 50 price, return, volatility, and drawdown analysis.
- **Industry Analysis** — composition, average returns, volatility, and comparative performance charts.
- **Risk & Return** — annualized returns, volatility, Sharpe/Sortino rankings, rolling risk, and VaR/CVaR.
- **CAPM Analysis** — beta estimation, alpha estimation, Security Market Line, and OLS regression.
- **Correlation** — pre/post co-movement matrices, industry correlations, and pairwise comparison.
- **PCA** — dimensionality reduction, explained variance, loadings, and interactive visualization.
- **Clustering** — K-Means grouping, cluster statistics, and industry–cluster distribution.
- **Portfolio Optimization** — equal-weight, minimum-variance, and maximum-Sharpe portfolios with efficient frontier.
- **Downloads & Reports** — CSV exports and dissertation-ready research summary.
- **COVID Regimes** — pre-COVID, March 2020 shock, and post-COVID regime comparison.
- **Data Quality** — transparent source-to-return validation and all flagged sessions.
"""
)
st.info("All performance statistics use adjusted-close returns. Sharpe and alpha assume a 6.5% risk-free rate (Indian 10Y Govt Bond equivalent).")

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<div style='text-align: center; color: #94A3B8; font-size: 0.85em; margin-top: 20px; font-weight: 500; letter-spacing: 0.05em;'>"
    "MADE BY PIYUSH PRABHAT"
    "</div>", 
    unsafe_allow_html=True
)
