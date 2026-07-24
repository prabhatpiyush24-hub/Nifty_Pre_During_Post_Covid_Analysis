"""Cached data access and reusable calculations for the research dashboard."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import plotly.io as pio

# Configure default Plotly template for Bloomberg-style dark mode
pio.templates.default = "plotly_dark"


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
ANALYSIS_DIR = DATA_DIR / "analysis"
QUALITY_DIR = DATA_DIR / "quality"
METADATA_DIR = DATA_DIR / "metadata"
RAW_DIR = DATA_DIR / "raw"
TRADING_DAYS = 252
REGIME_ORDER = ["Pre-COVID", "COVID Shock (Mar 2020)", "Post-COVID", "Full Sample"]


def apply_custom_theme():
    """Apply custom CSS for Bloomberg Terminal style and fix UI issues."""
    st.markdown(
        """
        <style>
        /* Fix metric truncation and adjust size */
        [data-testid="stMetricValue"] {
            font-size: 1.3rem !important;
            white-space: normal !important;
            word-break: break-word !important;
            line-height: 1.2 !important;
        }
        [data-testid="stMetricDelta"] {
            font-size: 0.9rem !important;
        }
        
        /* Adjust padding for denser, professional layout */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
        }
        
        /* High contrast text */
        p, span, div {
            color: #E0E0E0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ── Data loaders ──────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def load_daily_returns() -> pd.DataFrame:
    """Load only verified daily returns used by all charts and portfolio work."""
    frame = pd.read_parquet(PROCESSED_DIR / "daily_returns.parquet")
    frame["Date"] = pd.to_datetime(frame["Date"])
    return frame


@st.cache_data(show_spinner=False)
def load_research_dataset() -> pd.DataFrame:
    """Load the full benchmark-aligned research dataset including prices."""
    frame = pd.read_parquet(PROCESSED_DIR / "research_dataset.parquet")
    frame["Date"] = pd.to_datetime(frame["Date"])
    return frame


@st.cache_data(show_spinner=False)
def load_benchmark_prices() -> pd.DataFrame:
    """Load raw NIFTY 50 price file for benchmark charts."""
    path = RAW_DIR / "indices" / "NIFTY50.csv"
    frame = pd.read_csv(path)
    frame["Date"] = pd.to_datetime(frame["Date"])
    frame = frame.sort_values("Date").reset_index(drop=True)
    return frame


@st.cache_data(show_spinner=False)
def load_company_master() -> pd.DataFrame:
    """Load the company master file with universe definition."""
    return pd.read_csv(METADATA_DIR / "company_master.csv")


@st.cache_data(show_spinner=False)
def load_company_metrics() -> pd.DataFrame:
    frame = pd.read_parquet(ANALYSIS_DIR / "company_regime_metrics.parquet")
    frame["Regime"] = pd.Categorical(frame["Regime"], REGIME_ORDER, ordered=True)
    return frame


@st.cache_data(show_spinner=False)
def load_sector_daily() -> pd.DataFrame:
    frame = pd.read_parquet(ANALYSIS_DIR / "sector_daily_returns.parquet")
    frame["Date"] = pd.to_datetime(frame["Date"])
    return frame


@st.cache_data(show_spinner=False)
def load_sector_metrics() -> pd.DataFrame:
    frame = pd.read_csv(ANALYSIS_DIR / "sector_regime_metrics.csv")
    frame["Regime"] = pd.Categorical(frame["Regime"], REGIME_ORDER, ordered=True)
    return frame


@st.cache_data(show_spinner=False)
def load_market_metrics() -> pd.DataFrame:
    frame = pd.read_csv(ANALYSIS_DIR / "market_regime_metrics.csv")
    frame["Regime"] = pd.Categorical(frame["Regime"], REGIME_ORDER, ordered=True)
    return frame


@st.cache_data(show_spinner=False)
def load_company_comparison() -> pd.DataFrame:
    return pd.read_parquet(ANALYSIS_DIR / "company_covid_comparison.parquet")


@st.cache_data(show_spinner=False)
def load_correlation(regime: str) -> pd.DataFrame:
    filename = "pre_covid_correlation.parquet" if regime == "Pre-COVID" else "post_covid_correlation.parquet"
    matrix = pd.read_parquet(ANALYSIS_DIR / filename)
    matrix.index = matrix.columns
    return matrix


@st.cache_data(show_spinner=False)
def load_correlation_pairs() -> pd.DataFrame:
    return pd.read_parquet(ANALYSIS_DIR / "correlation_changes.parquet")


@st.cache_data(show_spinner=False)
def load_correlation_summary() -> pd.DataFrame:
    return pd.read_parquet(ANALYSIS_DIR / "correlation_summary.parquet")


@st.cache_data(show_spinner=False)
def load_clusters() -> pd.DataFrame:
    """Load quantitative cluster assignments."""
    return pd.read_csv(ANALYSIS_DIR / "quantitative_clusters.csv")


@st.cache_data(show_spinner=False)
def load_audit() -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    summary = json.loads((QUALITY_DIR / "return_audit_summary.json").read_text(encoding="utf-8"))
    audit = pd.read_csv(QUALITY_DIR / "return_audit.csv")
    issues = pd.read_csv(QUALITY_DIR / "data_quality_issues.csv")
    return summary, audit, issues


# ── Formatters ────────────────────────────────────────────────────

def to_percent(value: float, digits: int = 1) -> str:
    return "—" if pd.isna(value) else f"{value:.{digits}%}"


def to_number(value: float, digits: int = 2) -> str:
    return "—" if pd.isna(value) else f"{value:.{digits}f}"


# ── Computation helpers ───────────────────────────────────────────

def cumulative_wealth(frame: pd.DataFrame, value_column: str, group_column: str | None = None) -> pd.DataFrame:
    """Return a 100-base cumulative wealth series without mutating its input."""
    result = frame.copy().sort_values([group_column, "Date"] if group_column else "Date")
    if group_column:
        result["Wealth Index"] = result.groupby(group_column, observed=True)[value_column].transform(
            lambda series: 100 * (1 + series).cumprod()
        )
    else:
        result["Wealth Index"] = 100 * (1 + result[value_column]).cumprod()
    return result


def selected_regime_returns(frame: pd.DataFrame, regime: str) -> pd.DataFrame:
    """Select return rows for the displayed regime, including all dates for full sample."""
    return frame if regime == "Full Sample" else frame.loc[frame["Regime"] == regime].copy()


def compute_stock_metrics(returns: pd.Series, market_returns: pd.Series, dates: pd.Series) -> dict[str, float]:
    """Compute performance metrics for a single stock over a custom date range."""
    n_obs = len(returns)
    if n_obs < 2:
        return {}
    total_return = float((1 + returns).prod() - 1)
    start, end = pd.Timestamp(dates.min()), pd.Timestamp(dates.max())
    calendar_years = max((end - start).days / 365.25, 1 / TRADING_DAYS)
    cagr = float((1 + total_return) ** (1.0 / calendar_years) - 1)
    ann_vol = float(returns.std(ddof=1) * np.sqrt(TRADING_DAYS))
    sharpe = cagr / ann_vol if ann_vol > 0 else np.nan
    wealth = (1 + returns).cumprod()
    max_dd = float((wealth / wealth.cummax() - 1).min())
    mkt_var = float(market_returns.var(ddof=1))
    beta = float(returns.cov(market_returns) / mkt_var) if mkt_var > 0 else np.nan
    alpha = float((returns - beta * market_returns).mean() * TRADING_DAYS) if np.isfinite(beta) else np.nan
    return {
        "Total Return": total_return,
        "CAGR": cagr,
        "Annualized Volatility": ann_vol,
        "Sharpe Ratio": sharpe,
        "Maximum Drawdown": max_dd,
        "Beta": beta,
        "Alpha (Ann.)": alpha,
        "Observations": n_obs,
    }


def capm_regression(stock_returns: np.ndarray, market_returns: np.ndarray) -> dict[str, float]:
    """Run OLS regression for CAPM: stock = alpha + beta * market."""
    from scipy.stats import linregress

    slope, intercept, r_value, p_value, std_err = linregress(market_returns, stock_returns)
    residuals = stock_returns - (intercept + slope * market_returns)
    return {
        "Beta": slope,
        "Alpha (Daily)": intercept,
        "Alpha (Annualized)": intercept * TRADING_DAYS,
        "R²": r_value ** 2,
        "P-value (Beta)": p_value,
        "Std Error (Beta)": std_err,
        "Residual Std": float(np.std(residuals, ddof=2)),
    }


@st.cache_data(show_spinner=False)
def run_pca(_returns_wide: pd.DataFrame, n_components: int = 10):
    """Run PCA on wide-format return matrix.

    Returns explained-variance table, transformed coordinates, and loading matrix.
    """
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler

    clean = _returns_wide.fillna(0)
    n_comp = min(n_components, min(clean.shape) - 1)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(clean)
    pca = PCA(n_components=n_comp, random_state=42)
    transformed = pca.fit_transform(scaled)
    loadings = pd.DataFrame(
        pca.components_.T,
        index=clean.columns,
        columns=[f"PC{i+1}" for i in range(n_comp)],
    )
    explained = pd.DataFrame({
        "Component": [f"PC{i+1}" for i in range(n_comp)],
        "Explained Variance Ratio": pca.explained_variance_ratio_,
        "Cumulative Variance": np.cumsum(pca.explained_variance_ratio_),
    })
    return explained, transformed, loadings


def portfolio_weights(returns: pd.DataFrame, method: str, annual_risk_free_rate: float, max_weight: float) -> pd.Series:
    """Calculate long-only equal, minimum-variance, or maximum-Sharpe portfolio weights."""
    from scipy.optimize import minimize

    asset_count = returns.shape[1]
    if asset_count < 2:
        raise ValueError("Select at least two companies to build a portfolio.")
    effective_cap = max(max_weight, 1 / asset_count)
    equal = np.repeat(1 / asset_count, asset_count)
    if method == "Equal Weight":
        return pd.Series(equal, index=returns.columns, name="Weight")

    annual_mean = returns.mean().to_numpy() * TRADING_DAYS
    annual_covariance = returns.cov().to_numpy() * TRADING_DAYS

    def volatility(weights: np.ndarray) -> float:
        return float(np.sqrt(weights @ annual_covariance @ weights))

    def negative_sharpe(weights: np.ndarray) -> float:
        risk = volatility(weights)
        return -float((weights @ annual_mean - annual_risk_free_rate) / risk) if risk > 0 else 1e6

    objective = volatility if method == "Minimum Variance" else negative_sharpe
    result = minimize(
        objective,
        equal,
        method="SLSQP",
        bounds=[(0, effective_cap)] * asset_count,
        constraints={"type": "eq", "fun": lambda weights: weights.sum() - 1},
        options={"maxiter": 300, "ftol": 1e-10},
    )
    if not result.success:
        raise ValueError(f"Portfolio optimization failed: {result.message}")
    return pd.Series(result.x, index=returns.columns, name="Weight")


def portfolio_summary(returns: pd.Series, benchmark: pd.Series, annual_risk_free_rate: float) -> dict[str, float]:
    """Compute headline portfolio metrics from daily portfolio and market returns."""
    annual_return = float((1 + returns).prod() ** (TRADING_DAYS / len(returns)) - 1)
    annual_volatility = float(returns.std(ddof=1) * np.sqrt(TRADING_DAYS))
    wealth = (1 + returns).cumprod()
    max_drawdown = float((wealth / wealth.cummax() - 1).min())
    beta = float(returns.cov(benchmark) / benchmark.var(ddof=1))
    sharpe = (annual_return - annual_risk_free_rate) / annual_volatility if annual_volatility else np.nan
    return {
        "Annualized Return": annual_return,
        "Annualized Volatility": annual_volatility,
        "Sharpe Ratio": sharpe,
        "Maximum Drawdown": max_drawdown,
        "Beta to NIFTY 50": beta,
    }


def efficient_frontier_points(returns: pd.DataFrame, n_portfolios: int = 2000, risk_free: float = 0.0) -> pd.DataFrame:
    """Generate random portfolio points for the efficient frontier visualization."""
    n_assets = returns.shape[1]
    annual_mean = returns.mean().to_numpy() * TRADING_DAYS
    annual_cov = returns.cov().to_numpy() * TRADING_DAYS

    results = np.zeros((n_portfolios, 3))
    rng = np.random.default_rng(42)
    for i in range(n_portfolios):
        w = rng.random(n_assets)
        w /= w.sum()
        port_return = float(w @ annual_mean)
        port_vol = float(np.sqrt(w @ annual_cov @ w))
        sharpe = (port_return - risk_free) / port_vol if port_vol > 0 else 0
        results[i] = [port_vol, port_return, sharpe]

    return pd.DataFrame(results, columns=["Volatility", "Return", "Sharpe Ratio"])
