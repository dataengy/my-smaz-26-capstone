"""Run a separate price/cross-market-only diagnostic.

Reads and validates cached snapshots only; never refreshes providers. This
interim experiment deliberately excludes COT predictors and is not a substitute
for the intended COT-inclusive capstone evaluation.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

from capstone.config import read_config
from capstone.data import load_sources
from capstone.features import _market_frame, _other_returns, _session_closes
from capstone.modeling import fit_predict


def build_market_only_frame(sources: dict, config: dict) -> tuple[pd.DataFrame, list[str]]:
    rows = []
    market_features = config.get("market_features", {})
    for ticker in config.get("target_symbols", ["GLD", "SLV"]):
        frame = _market_frame(sources[ticker], ticker)
        frame["signal_at"] = _session_closes(frame.date)
        frame["ticker"] = ticker
        for n in (1, 5, 20):
            frame[f"return_{n}"] = frame.adj_close.pct_change(n, fill_method=None)
        for n in (5, 20):
            frame[f"volatility_{n}"] = frame.return_1.rolling(n, min_periods=n).std()
        frame["price_to_ma_20"] = frame.adj_close / frame.adj_close.rolling(20, min_periods=20).mean() - 1
        frame["volume_change_5"] = frame.volume.pct_change(5, fill_method=None).replace([float("inf"), -float("inf")], pd.NA)
        holding = int(config.get("holding_sessions", 5))
        frame["entry_date"] = frame.date.shift(-1)
        frame["exit_date"] = frame.date.shift(-(holding + 1))
        frame["entry_open"] = frame.adjusted_open.shift(-1)
        frame["exit_open"] = frame.adjusted_open.shift(-(holding + 1))
        frame["target"] = frame.exit_open / frame.entry_open - 1
        for symbol, name in market_features.items():
            if symbol in sources:
                frame[f"{name}_return_5"] = _other_returns(sources[symbol], symbol, frame)
        rows.append(frame)
    result = pd.concat(rows, ignore_index=True).sort_values(["date", "ticker"]).reset_index(drop=True)
    features = ["return_1", "return_5", "return_20", "volatility_5", "volatility_20",
                "price_to_ma_20", "volume_change_5"]
    features += [f"{name}_return_5" for name in market_features.values()]
    return result, features


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    config = read_config(root / "config/config.yml", root / "config/settings.yml")
    sources = load_sources(config, refresh=False)
    frame, features = build_market_only_frame(sources, config)
    result = fit_predict(frame, features, config)
    validation_start = pd.Timestamp(result["split_dates"]["validation_start"])
    test_start = pd.Timestamp(result["split_dates"]["test_start"])
    labeled = frame.loc[frame.target.notna()].copy()
    train = labeled.loc[(labeled.date < validation_start) & (labeled.exit_date < validation_start)]
    validation = labeled.loc[(labeled.date >= validation_start) & (labeled.date < test_start) & (labeled.exit_date < test_start)]
    test = labeled.loc[labeled.date >= test_start]
    test_predictions = result["predictions"].loc[result["predictions"].split.eq("test")].copy()
    baseline_mean = float(pd.concat([train.target, validation.target]).mean())
    test_predictions["baseline_prediction"] = baseline_mean
    model_holdout = {
        "mae": float(mean_absolute_error(test_predictions.target, test_predictions.prediction)),
        "rmse": float(mean_squared_error(test_predictions.target, test_predictions.prediction) ** 0.5),
        "directional_accuracy": float((test_predictions.target.gt(0) == test_predictions.prediction.gt(0)).mean()),
    }
    mean_baseline_holdout = {
        "training_validation_mean_prediction": baseline_mean,
        "mae": float(mean_absolute_error(test_predictions.target, test_predictions.baseline_prediction)),
        "rmse": float(mean_squared_error(test_predictions.target, test_predictions.baseline_prediction) ** 0.5),
    }
    output = root / config.get("output_dir", "artifacts") / "market-only-diagnostic"
    output.mkdir(parents=True, exist_ok=True)
    result["predictions"].to_csv(output / "predictions.csv", index=False)
    result["model_metrics"].to_csv(output / "model_metrics.csv", index=False)
    result["model_comparison"].to_csv(output / "model_comparison.csv", index=False)
    summary = {
        "status": "interim market-only diagnostic; COT predictors excluded",
        "source_rows": int(len(frame)),
        "signal_date_range": [str(frame.date.min().date()), str(frame.date.max().date())],
        "feature_count": len(features),
        "features": features,
        "selected_model_on_validation": result["selected_model"],
        "selected_threshold_on_validation": result["selected_threshold"],
        "split_dates": result["split_dates"],
        "rows_by_partition_after_purge": {"train": int(len(train)), "validation": int(len(validation)), "test": int(len(test))},
        "rows_by_split": result["predictions"].groupby("split").size().to_dict(),
        "threshold_scores_validation_only": result["threshold_scores"],
        "selected_model_holdout": model_holdout,
        "mean_baseline_holdout": mean_baseline_holdout,
        "limitations": [
            "COT predictors are excluded by design; this is separate from the full-COT experiment.",
            "Adjusted vendor history can contain retrospective revisions.",
            "This diagnostic does not evaluate COT's incremental value and is not the planned final experiment.",
        ],
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    print(json.dumps(summary, indent=2, default=str))
    print("Market-only model comparison: validation only; selected by minimum MAE (returns in decimal units).")
    print(result["model_comparison"].to_string(index=False))


if __name__ == "__main__":
    main()
