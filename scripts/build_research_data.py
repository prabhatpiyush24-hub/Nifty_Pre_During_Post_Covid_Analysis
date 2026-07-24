"""Build validated NIFTY 500 research data and all dashboard artifacts."""

from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.research import run_pipeline


if __name__ == "__main__":
    summary = run_pipeline(PROJECT_ROOT)
    print(json.dumps(summary, indent=2))
    if summary["status"] != "PASS":
        raise SystemExit("Data-quality errors detected; research artifacts were not approved.")
