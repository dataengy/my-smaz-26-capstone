"""Offline synthetic human demo: proves the workflow runs, not finance quality."""
from __future__ import annotations

import json

import pandas as pd

from capstone.synthetic_demo import run_human_demo


def test_synthetic_human_demo_runs_and_renders_a_clearly_labeled_report(tmp_path):
    source_dir = tmp_path / "data" / "synthetic"
    output_dir = tmp_path / "artifacts" / "synthetic-demo"

    result = run_human_demo(source_dir=source_dir, output_dir=output_dir)

    report_path = output_dir / "index.html"
    summary_path = output_dir / "summary.json"
    assert report_path.is_file()
    assert summary_path.is_file()
    html = report_path.read_text(encoding="utf-8")
    assert "FICTIONAL SYNTHETIC DATA ONLY" in html
    assert "not evidence about strategy quality" in html
    assert html.count("data:image/png;base64,") == 3
    assert (output_dir / "input_prices.png").stat().st_size > 1_000
    assert (output_dir / "predictions.png").stat().st_size > 1_000
    assert (output_dir / "equity_curves.png").stat().st_size > 1_000

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["synthetic_only"] is True
    assert summary["html_report"] == str(report_path)
    assert summary["summary_json"] == str(summary_path)
    assert summary["seed"] == 2026
    assert summary["feature_rows"] == result["feature_rows"] > 100
    assert len(summary["numeric_features"]) >= 5
    assert summary["model"] in {"mean", "ridge_1", "ridge_10", "tree_3", "tree_5", "forest_3", "forest_5"}
    assert all("example.invalid" in row["source_url"] for row in pd.read_csv(source_dir / "cot.csv").to_dict("records"))
    assert (source_dir / "GLD.csv").is_file()
    assert (source_dir / "SLV.csv").is_file()
    assert (source_dir / "BTC_USD.csv").is_file()
