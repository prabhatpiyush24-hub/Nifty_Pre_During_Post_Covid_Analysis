"""Fail fast if persisted research artifacts no longer satisfy audit expectations."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.research import RETURN_TOLERANCE, build_research_dataset, project_paths


def main() -> None:
    paths = project_paths(PROJECT_ROOT)
    full_dataset, daily_returns, audit, issues = build_research_dataset(paths)
    persisted = pd.read_parquet(paths.processed / "research_dataset.parquet")
    persisted_returns = pd.read_parquet(paths.processed / "daily_returns.parquet")

    assert len(persisted) == len(full_dataset), "Persisted aligned dataset row count differs from rebuilt data"
    assert len(persisted_returns) == len(daily_returns), "Persisted daily-return row count differs from rebuilt data"
    assert persisted["Symbol"].nunique() == 311, "Expected 311 eligible companies"
    assert persisted.duplicated(["Date", "Symbol"]).sum() == 0, "Duplicate company-date rows found"
    assert persisted_returns[["Return", "Log Return", "NIFTY Return", "Excess Return"]].isna().sum().sum() == 0, "Invalid return rows reached analytics dataset"
    assert audit.filter(like="Formula Error").max().max() <= RETURN_TOLERANCE, "Return formula verification failed"
    assert not any(issue["Severity"] == "ERROR" for issue in issues), "Data-quality error found"

    summary = json.loads((paths.quality / "return_audit_summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "PASS", "Persisted audit summary is not PASS"
    print(
        "PASS | "
        f"companies={persisted['Symbol'].nunique()} | "
        f"aligned_rows={len(persisted):,} | "
        f"valid_return_rows={len(persisted_returns):,} | "
        f"warnings={summary['warnings']}"
    )


if __name__ == "__main__":
    main()
