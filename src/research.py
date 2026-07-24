"""Auditable research-data and quantitative-analysis pipeline for NIFTY 500.

The study universe is defined by ``company_master.csv``.  Prices are never
forward-filled or otherwise imputed: when a company misses a benchmark session,
the affected interval is marked invalid rather than presented as a one-day
return.  This is important for both risk statistics and COVID regime analysis.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


START_DATE = pd.Timestamp("2015-01-01")
END_DATE = pd.Timestamp("2025-12-31")
COVID_START = pd.Timestamp("2020-03-01")
COVID_END = pd.Timestamp("2020-03-31")
POST_COVID_START = pd.Timestamp("2020-04-01")
TRADING_DAYS_PER_YEAR = 252
RISK_FREE_RATE_ANNUAL = 0.065
RETURN_TOLERANCE = 1e-12

REQUIRED_PRICE_COLUMNS = ("Date", "Open", "High", "Low", "Close", "Adj Close", "Volume")
PRICE_COLUMNS = ("Open", "High", "Low", "Close", "Adj Close")


@dataclass(frozen=True)
class ProjectPaths:
    """Canonical project paths, resolved relative to the repository root."""

    root: Path

    @property
    def raw_prices(self) -> Path:
        return self.root / "data" / "raw" / "prices"

    @property
    def benchmark_file(self) -> Path:
        return self.root / "data" / "raw" / "indices" / "NIFTY50.csv"

    @property
    def company_master(self) -> Path:
        return self.root / "data" / "metadata" / "company_master.csv"

    @property
    def processed(self) -> Path:
        return self.root / "data" / "processed"

    @property
    def analysis(self) -> Path:
        return self.root / "data" / "analysis"

    @property
    def quality(self) -> Path:
        return self.root / "data" / "quality"


def project_paths(root: Path | None = None) -> ProjectPaths:
    """Return project paths, defaulting to the parent of this source folder."""

    return ProjectPaths((root or Path(__file__).resolve().parents[1]).resolve())


def classify_regime(date: pd.Timestamp) -> str:
    """Classify a date into the pre-COVID, March shock, or post-COVID regime."""

    if date < COVID_START:
        return "Pre-COVID"
    if date <= COVID_END:
        return "COVID Shock (Mar 2020)"
    return "Post-COVID"


def _read_price_file(path: Path, label: str) -> pd.DataFrame:
    """Load and validate one raw price file without changing any price values."""

    if not path.exists():
        raise FileNotFoundError(f"Missing raw price file for {label}: {path}")

    frame = pd.read_csv(path)
    missing_columns = set(REQUIRED_PRICE_COLUMNS).difference(frame.columns)
    if missing_columns:
        raise ValueError(f"{label}: missing required columns: {sorted(missing_columns)}")

    frame["Date"] = pd.to_datetime(frame["Date"], errors="raise")
    frame = frame.loc[(frame["Date"] >= START_DATE) & (frame["Date"] <= END_DATE)].copy()
    if frame.empty:
        raise ValueError(f"{label}: no observations in the research period")

    if frame["Date"].duplicated().any():
        duplicates = int(frame["Date"].duplicated().sum())
        raise ValueError(f"{label}: {duplicates} duplicate date(s) in the research period")

    for column in (*PRICE_COLUMNS, "Volume"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")

    missing = int(frame[list(REQUIRED_PRICE_COLUMNS)].isna().sum().sum())
    if missing:
        raise ValueError(f"{label}: {missing} missing required value(s) in the research period")

    non_positive = int((frame[list(PRICE_COLUMNS)] <= 0).sum().sum())
    if non_positive:
        raise ValueError(f"{label}: {non_positive} non-positive price value(s) in the research period")

    negative_volume = int((frame["Volume"] < 0).sum())
    if negative_volume:
        raise ValueError(f"{label}: {negative_volume} negative volume value(s) in the research period")

    ohlc_error = (
        (frame["Low"] > frame[["Open", "High", "Close"]].min(axis=1))
        | (frame["High"] < frame[["Open", "Low", "Close"]].max(axis=1))
    )
    if ohlc_error.any():
        raise ValueError(f"{label}: {int(ohlc_error.sum())} invalid OHLC row(s) in the research period")

    return frame.sort_values("Date").reset_index(drop=True)


def load_benchmark(paths: ProjectPaths) -> pd.DataFrame:
    """Load the NIFTY 50 benchmark and calculate its daily return series."""

    benchmark = _read_price_file(paths.benchmark_file, "NIFTY 50")
    benchmark["NIFTY Return"] = benchmark["Adj Close"].pct_change(fill_method=None)
    benchmark["NIFTY Log Return"] = np.log(benchmark["Adj Close"] / benchmark["Adj Close"].shift(1))
    benchmark["Benchmark Session"] = np.arange(len(benchmark), dtype=int)
    return benchmark


def _return_error(frame: pd.DataFrame, value: str, expected: pd.Series) -> float:
    """Maximum absolute error between a calculated field and its defining formula."""

    valid = frame[value].notna() & expected.notna()
    if not valid.any():
        return 0.0
    return float((frame.loc[valid, value] - expected.loc[valid]).abs().max())


def build_research_dataset(paths: ProjectPaths) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[dict[str, Any]]]:
    """Build a validated, benchmark-aligned company dataset from raw prices.

    ``full_dataset`` retains rows with an unavailable return so the reason is
    inspectable. ``daily_returns`` is the strictly valid return universe used by
    every analysis metric and dashboard chart.
    """

    master = pd.read_csv(paths.company_master)
    required_master = {"Symbol", "Company Name", "Industry", "Eligible"}
    absent = required_master.difference(master.columns)
    if absent:
        raise ValueError(f"Company master is missing columns: {sorted(absent)}")

    universe = master.loc[master["Eligible"].astype(bool), ["Symbol", "Company Name", "Industry"]].copy()
    universe = universe.sort_values("Symbol").reset_index(drop=True)
    if universe.empty:
        raise ValueError("The eligible research universe is empty")
    if universe["Symbol"].duplicated().any():
        raise ValueError("The eligible research universe contains duplicate symbols")

    benchmark = load_benchmark(paths)
    benchmark_dates = pd.Index(benchmark["Date"])
    benchmark_lookup = pd.Series(benchmark["Benchmark Session"].to_numpy(), index=benchmark_dates)
    benchmark_columns = benchmark[["Date", "NIFTY Return", "NIFTY Log Return", "Benchmark Session"]]

    full_frames: list[pd.DataFrame] = []
    audit_rows: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []

    for symbol, company_name, industry in universe.itertuples(index=False, name=None):
        stock = _read_price_file(paths.raw_prices / f"{symbol}.csv", symbol)
        stock_dates = pd.Index(stock["Date"])
        unbenchmarked_dates = stock_dates.difference(benchmark_dates)
        missing_benchmark_sessions = benchmark_dates.difference(stock_dates)

        aligned = stock.merge(benchmark_columns, on="Date", how="inner", validate="one_to_one")
        aligned = aligned.sort_values("Date").reset_index(drop=True)
        aligned["Previous Date"] = aligned["Date"].shift(1)
        aligned["Previous Adj Close"] = aligned["Adj Close"].shift(1)
        aligned["Trading Sessions Since Prior"] = aligned["Benchmark Session"].diff()
        aligned["Is Valid Daily Return"] = (
            aligned["NIFTY Return"].notna()
            & aligned["Trading Sessions Since Prior"].eq(1)
            & aligned["Previous Adj Close"].notna()
        )
        raw_return = aligned["Adj Close"] / aligned["Previous Adj Close"] - 1
        raw_log_return = np.log(aligned["Adj Close"] / aligned["Previous Adj Close"])
        aligned["Return"] = raw_return.where(aligned["Is Valid Daily Return"])
        aligned["Log Return"] = raw_log_return.where(aligned["Is Valid Daily Return"])
        aligned["Excess Return"] = (aligned["Return"] - aligned["NIFTY Return"]).where(
            aligned["Is Valid Daily Return"]
        )
        aligned["Symbol"] = symbol
        aligned["Company Name"] = company_name
        aligned["Industry"] = industry
        aligned["Regime"] = aligned["Date"].map(classify_regime)

        valid = aligned.loc[aligned["Is Valid Daily Return"]].copy()
        nonconsecutive = int((aligned["Trading Sessions Since Prior"] > 1).sum())
        return_error = _return_error(valid, "Return", raw_return)
        log_return_error = _return_error(valid, "Log Return", raw_log_return)
        excess_error = _return_error(valid, "Excess Return", valid["Return"] - valid["NIFTY Return"])

        audit_rows.append(
            {
                "Symbol": symbol,
                "Company Name": company_name,
                "Industry": industry,
                "Raw Observations": len(stock),
                "Benchmark-Aligned Observations": len(aligned),
                "Valid Daily Returns": len(valid),
                "Expected Daily Returns": int(benchmark["NIFTY Return"].notna().sum()),
                "Missing Benchmark Sessions": len(missing_benchmark_sessions),
                "Unbenchmarked Stock Dates": len(unbenchmarked_dates),
                "Nonconsecutive Return Intervals": nonconsecutive,
                "Maximum Return Formula Error": return_error,
                "Maximum Log Return Formula Error": log_return_error,
                "Maximum Excess Return Formula Error": excess_error,
                "Status": "PASS" if return_error <= RETURN_TOLERANCE and nonconsecutive == 0 else "PASS WITH FLAG",
            }
        )

        if len(missing_benchmark_sessions):
            issues.append(
                {
                    "Severity": "WARNING",
                    "Symbol": symbol,
                    "Issue": "Missing company observation on benchmark session",
                    "Count": len(missing_benchmark_sessions),
                    "Dates": ", ".join(pd.Series(missing_benchmark_sessions).dt.strftime("%Y-%m-%d").tolist()),
                    "Resolution": "No price was imputed; the affected return interval is excluded from analytics.",
                }
            )
        if return_error > RETURN_TOLERANCE or log_return_error > RETURN_TOLERANCE or excess_error > RETURN_TOLERANCE:
            issues.append(
                {
                    "Severity": "ERROR",
                    "Symbol": symbol,
                    "Issue": "Return formula verification failed",
                    "Count": 1,
                    "Dates": "",
                    "Resolution": "Investigate source price history before using analytics.",
                }
            )

        full_frames.append(aligned)

    full_dataset = pd.concat(full_frames, ignore_index=True).sort_values(["Date", "Symbol"]).reset_index(drop=True)
    daily_returns = full_dataset.loc[full_dataset["Is Valid Daily Return"]].copy()
    daily_returns = daily_returns.sort_values(["Date", "Symbol"]).reset_index(drop=True)
    audit = pd.DataFrame(audit_rows).sort_values("Symbol").reset_index(drop=True)

    expected_symbols = set(universe["Symbol"])
    actual_symbols = set(full_dataset["Symbol"])
    if actual_symbols != expected_symbols:
        missing = sorted(expected_symbols.difference(actual_symbols))
        unexpected = sorted(actual_symbols.difference(expected_symbols))
        raise ValueError(f"Research universe mismatch. Missing={missing}; unexpected={unexpected}")

    return full_dataset, daily_returns, audit, issues


def _max_drawdown(returns: pd.Series) -> float:
    wealth = (1.0 + returns).cumprod()
    return float((wealth / wealth.cummax() - 1.0).min())


def _performance_record(frame: pd.DataFrame) -> dict[str, Any]:
    """Calculate auditable performance and risk statistics with a realistic risk-free rate."""

    returns = frame["Return"].dropna()
    market = frame.loc[returns.index, "NIFTY Return"]
    daily_rf = (1.0 + RISK_FREE_RATE_ANNUAL) ** (1.0 / TRADING_DAYS_PER_YEAR) - 1.0
    excess_return = returns - daily_rf
    excess_market = market - daily_rf
    excess = returns - market
    n_obs = len(returns)
    start = pd.Timestamp(frame.loc[returns.index, "Date"].min())
    end = pd.Timestamp(frame.loc[returns.index, "Date"].max())
    calendar_years = max((end - start).days / 365.25, 1 / TRADING_DAYS_PER_YEAR)
    total_return = float((1.0 + returns).prod() - 1.0)
    annualized_return = float((1.0 + total_return) ** (1.0 / calendar_years) - 1.0)
    annualized_volatility = float(returns.std(ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR))
    downside_deviation = float(np.sqrt(np.mean(np.minimum(excess_return.to_numpy(), 0.0) ** 2)) * np.sqrt(TRADING_DAYS_PER_YEAR))
    
    annualized_excess_return = annualized_return - RISK_FREE_RATE_ANNUAL
    sharpe = annualized_excess_return / annualized_volatility if annualized_volatility > 0 else np.nan
    sortino = annualized_excess_return / downside_deviation if downside_deviation > 0 else np.nan
    
    var_95 = float(returns.quantile(0.05))
    cvar_95 = float(returns.loc[returns <= var_95].mean())
    market_variance = float(excess_market.var(ddof=1))
    beta = float(excess_return.cov(excess_market) / market_variance) if market_variance > 0 else np.nan
    market_correlation = float(returns.corr(market))
    alpha_annualized = float((excess_return - beta * excess_market).mean() * TRADING_DAYS_PER_YEAR) if np.isfinite(beta) else np.nan
    tracking_error = float(excess.std(ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR))
    information_ratio = float(excess.mean() * TRADING_DAYS_PER_YEAR / tracking_error) if tracking_error > 0 else np.nan

    return {
        "Observations": n_obs,
        "Start Date": start,
        "End Date": end,
        "Total Return": total_return,
        "CAGR": annualized_return,
        "Annualized Volatility": annualized_volatility,
        "Downside Deviation": downside_deviation,
        "Sharpe Ratio (Rf=6.5%)": sharpe,
        "Sortino Ratio (Rf=6.5%)": sortino,
        "Maximum Drawdown": _max_drawdown(returns),
        "Historical VaR 95% (1D)": var_95,
        "Historical CVaR 95% (1D)": cvar_95,
        "Beta to NIFTY 50": beta,
        "Annualized Alpha (Rf=6.5%)": alpha_annualized,
        "Market Correlation": market_correlation,
        "Tracking Error": tracking_error,
        "Information Ratio": information_ratio,
        "Active Win Rate": float((excess > 0).mean()),
    }


def grouped_metrics(frame: pd.DataFrame, group_columns: Iterable[str]) -> pd.DataFrame:
    """Calculate performance records for every requested grouping."""

    records: list[dict[str, Any]] = []
    group_columns = list(group_columns)
    for keys, group in frame.groupby(group_columns, sort=True, observed=True):
        if not isinstance(keys, tuple):
            keys = (keys,)
        record = dict(zip(group_columns, keys))
        record.update(_performance_record(group))
        records.append(record)
    return pd.DataFrame(records)


def _comparison_table(metrics: pd.DataFrame, entity_columns: list[str]) -> pd.DataFrame:
    """Create a clear post-COVID versus pre-COVID comparison table."""

    metrics_to_compare = [
        "CAGR",
        "Annualized Volatility",
        "Sharpe Ratio (Rf=6.5%)",
        "Maximum Drawdown",
        "Beta to NIFTY 50",
        "Annualized Alpha (Rf=6.5%)",
        "Market Correlation",
        "Information Ratio",
    ]
    pre = metrics.loc[metrics["Regime"] == "Pre-COVID", entity_columns + metrics_to_compare].copy()
    post = metrics.loc[metrics["Regime"] == "Post-COVID", entity_columns + metrics_to_compare].copy()
    pre = pre.rename(columns={column: f"Pre-COVID {column}" for column in metrics_to_compare})
    post = post.rename(columns={column: f"Post-COVID {column}" for column in metrics_to_compare})
    comparison = pre.merge(post, on=entity_columns, how="outer", validate="one_to_one")
    for column in metrics_to_compare:
        comparison[f"Change in {column}"] = comparison[f"Post-COVID {column}"] - comparison[f"Pre-COVID {column}"]
    return comparison.sort_values(entity_columns).reset_index(drop=True)


def _correlation_outputs(daily_returns: pd.DataFrame) -> tuple[dict[str, pd.DataFrame], pd.DataFrame, pd.DataFrame]:
    """Calculate pre/post stock correlations and pair-level correlation changes."""

    matrices: dict[str, pd.DataFrame] = {}
    pairs: pd.DataFrame | None = None
    for regime in ("Pre-COVID", "Post-COVID"):
        pivot = daily_returns.loc[daily_returns["Regime"] == regime].pivot(
            index="Date", columns="Symbol", values="Return"
        )
        matrix = pivot.corr(min_periods=max(30, int(len(pivot) * 0.75)))
        matrix.index.name = "Symbol"
        matrices[regime] = matrix
        mask = np.triu(np.ones(matrix.shape, dtype=bool), k=1)
        pair_frame = (
            matrix.rename_axis(index="Symbol A", columns="Symbol B")
            .where(mask)
            .stack()
            .rename(f"{regime} Correlation")
            .reset_index()
        )
        pair_frame = pair_frame.dropna(subset=[f"{regime} Correlation"])
        pairs = pair_frame if pairs is None else pairs.merge(pair_frame, on=["Symbol A", "Symbol B"], how="outer")

    assert pairs is not None
    pairs["Correlation Change (Post - Pre)"] = pairs["Post-COVID Correlation"] - pairs["Pre-COVID Correlation"]
    pairs["Absolute Correlation Change"] = pairs["Correlation Change (Post - Pre)"].abs()
    pairs = pairs.sort_values("Absolute Correlation Change", ascending=False).reset_index(drop=True)

    summary = pd.DataFrame({"Symbol": matrices["Pre-COVID"].columns})
    for regime, matrix in matrices.items():
        values = matrix.to_numpy(dtype=float, copy=True)
        np.fill_diagonal(values, np.nan)
        summary[f"{regime} Average Stock Correlation"] = np.nanmean(values, axis=1)
    summary["Change in Average Stock Correlation"] = (
        summary["Post-COVID Average Stock Correlation"] - summary["Pre-COVID Average Stock Correlation"]
    )
    return matrices, pairs, summary


def _assign_clusters(full_sample_metrics: pd.DataFrame) -> pd.DataFrame:
    """Add reproducible K-means groups from return, risk, and market-exposure factors."""

    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    features = [
        "CAGR",
        "Annualized Volatility",
        "Sharpe Ratio (Rf=6.5%)",
        "Maximum Drawdown",
        "Beta to NIFTY 50",
        "Market Correlation",
    ]
    cluster_data = full_sample_metrics[["Symbol", *features]].copy()
    numeric = cluster_data[features].replace([np.inf, -np.inf], np.nan)
    numeric = numeric.fillna(numeric.median())
    n_clusters = min(6, len(cluster_data))
    labels = KMeans(n_clusters=n_clusters, n_init=25, random_state=42).fit_predict(StandardScaler().fit_transform(numeric))
    cluster_data["Quantitative Cluster"] = [f"Cluster {label + 1}" for label in labels]
    return cluster_data[["Symbol", "Quantitative Cluster"]]


def build_analysis_outputs(daily_returns: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Build company, sector, market, correlation, and clustering research outputs."""

    with_full_sample = pd.concat(
        [daily_returns, daily_returns.assign(Regime="Full Sample")], ignore_index=True
    )
    company_metrics = grouped_metrics(with_full_sample, ["Symbol", "Company Name", "Industry", "Regime"])

    sector_daily = (
        daily_returns.groupby(["Date", "Industry", "Regime"], observed=True)
        .agg(
            Return=("Return", "mean"),
            **{"NIFTY Return": ("NIFTY Return", "first")},
            Companies=("Symbol", "nunique"),
        )
        .reset_index()
    )
    sector_daily["Log Return"] = np.log1p(sector_daily["Return"])
    sector_daily["Excess Return"] = sector_daily["Return"] - sector_daily["NIFTY Return"]
    sector_metrics = grouped_metrics(
        pd.concat([sector_daily, sector_daily.assign(Regime="Full Sample")], ignore_index=True),
        ["Industry", "Regime"],
    )
    sector_company_counts = daily_returns.groupby("Industry", as_index=False)["Symbol"].nunique().rename(
        columns={"Symbol": "Companies"}
    )
    sector_metrics = sector_metrics.merge(sector_company_counts, on="Industry", how="left", validate="many_to_one")

    market_daily = daily_returns[["Date", "Regime", "NIFTY Return"]].drop_duplicates("Date").rename(
        columns={"NIFTY Return": "Return"}
    )
    market_daily["NIFTY Return"] = market_daily["Return"]
    market_metrics = grouped_metrics(
        pd.concat([market_daily, market_daily.assign(Regime="Full Sample")], ignore_index=True), ["Regime"]
    )
    market_metrics.insert(0, "Portfolio", "NIFTY 50")

    matrices, correlation_pairs, correlation_summary = _correlation_outputs(daily_returns)
    full_sample = company_metrics.loc[company_metrics["Regime"] == "Full Sample"].copy()
    clusters = _assign_clusters(full_sample)
    company_metrics = company_metrics.merge(clusters, on="Symbol", how="left", validate="many_to_one")
    correlation_summary = correlation_summary.merge(clusters, on="Symbol", how="left", validate="one_to_one")

    return {
        "company_metrics": company_metrics,
        "sector_daily": sector_daily,
        "sector_metrics": sector_metrics,
        "market_metrics": market_metrics,
        "company_covid_comparison": _comparison_table(company_metrics, ["Symbol", "Company Name", "Industry", "Quantitative Cluster"]),
        "sector_covid_comparison": _comparison_table(sector_metrics, ["Industry"]),
        "pre_correlation": matrices["Pre-COVID"],
        "post_correlation": matrices["Post-COVID"],
        "correlation_pairs": correlation_pairs,
        "correlation_summary": correlation_summary,
        "clusters": clusters,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def save_outputs(
    paths: ProjectPaths,
    full_dataset: pd.DataFrame,
    daily_returns: pd.DataFrame,
    audit: pd.DataFrame,
    issues: list[dict[str, Any]],
    outputs: dict[str, pd.DataFrame],
) -> dict[str, Any]:
    """Persist compact, dashboard-ready Parquet and human-readable audit artifacts."""

    for directory in (paths.processed, paths.analysis, paths.quality):
        directory.mkdir(parents=True, exist_ok=True)

    full_dataset.to_parquet(paths.processed / "research_dataset.parquet", index=False)
    daily_returns.to_parquet(paths.processed / "daily_returns.parquet", index=False)
    audit.to_csv(paths.quality / "return_audit.csv", index=False)
    pd.DataFrame(issues, columns=["Severity", "Symbol", "Issue", "Count", "Dates", "Resolution"]).to_csv(
        paths.quality / "data_quality_issues.csv", index=False
    )

    parquet_outputs = {
        "company_metrics": "company_regime_metrics.parquet",
        "sector_daily": "sector_daily_returns.parquet",
        "company_covid_comparison": "company_covid_comparison.parquet",
        "pre_correlation": "pre_covid_correlation.parquet",
        "post_correlation": "post_covid_correlation.parquet",
        "correlation_pairs": "correlation_changes.parquet",
        "correlation_summary": "correlation_summary.parquet",
    }
    csv_outputs = {
        "sector_metrics": "sector_regime_metrics.csv",
        "market_metrics": "market_regime_metrics.csv",
        "sector_covid_comparison": "sector_covid_comparison.csv",
        "clusters": "quantitative_clusters.csv",
    }
    for key, filename in parquet_outputs.items():
        outputs[key].to_parquet(paths.analysis / filename, index=True if "correlation" in key and key.startswith(("pre_", "post_")) else False)
    for key, filename in csv_outputs.items():
        outputs[key].to_csv(paths.analysis / filename, index=False)

    formula_error_columns = [column for column in audit.columns if "Formula Error" in column]
    summary: dict[str, Any] = {
        "status": "PASS" if not any(issue["Severity"] == "ERROR" for issue in issues) else "FAIL",
        "study_period": {"start": START_DATE.date().isoformat(), "end": END_DATE.date().isoformat()},
        "covid_regimes": {
            "pre_covid": f"{START_DATE.date().isoformat()} to 2020-02-28",
            "covid_shock": "2020-03-01 to 2020-03-31",
            "post_covid": f"{POST_COVID_START.date().isoformat()} to {END_DATE.date().isoformat()}",
        },
        "eligible_companies": int(audit["Symbol"].nunique()),
        "benchmark_sessions": int(full_dataset["Date"].nunique()),
        "benchmark_aligned_company_rows": int(len(full_dataset)),
        "valid_daily_return_rows": int(len(daily_returns)),
        "companies_with_complete_daily_return_coverage": int((audit["Missing Benchmark Sessions"] == 0).sum()),
        "companies_with_flagged_missing_sessions": int((audit["Missing Benchmark Sessions"] > 0).sum()),
        "max_formula_error": float(audit[formula_error_columns].max().max()),
        "warnings": int(sum(issue["Severity"] == "WARNING" for issue in issues)),
        "errors": int(sum(issue["Severity"] == "ERROR" for issue in issues)),
        "method": "Returns are recomputed from adjusted closes only after alignment to the NIFTY 50 calendar. No missing price or return is imputed.",
    }
    _write_json(paths.quality / "return_audit_summary.json", summary)
    return summary


def run_pipeline(root: Path | None = None) -> dict[str, Any]:
    """Run the complete validation and quantitative research pipeline."""

    paths = project_paths(root)
    full_dataset, daily_returns, audit, issues = build_research_dataset(paths)
    outputs = build_analysis_outputs(daily_returns)
    return save_outputs(paths, full_dataset, daily_returns, audit, issues, outputs)
