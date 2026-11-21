"""Generate and run a clearly labeled synthetic demonstration of the workflow.

No provider is called. Every generated price and COT value is fictional and
exists only to exercise project code and produce a visual walkthrough.
"""
from __future__ import annotations

import argparse
import base64
from datetime import timedelta
import json
import os
from pathlib import Path
import webbrowser

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[2] / ".run" / "matplotlib"))
import exchange_calendars as xcals
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

from .backtest import run_backtest, run_vectorized_backtest
from .config import read_config
from .features import _market_frame, build_features, numeric_features
from .modeling import fit_predict


SYNTHETIC_SOURCE_URL = "https://example.invalid/synthetic-human-demo"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _price_frame(dates: pd.DatetimeIndex, ticker: str, start_price: float, seed: int) -> pd.DataFrame:
    """Create deterministic, source-shaped fictional OHLCV rows."""
    rng = np.random.default_rng(seed + sum((i + 1) * ord(char) for i, char in enumerate(ticker)))
    index = np.arange(len(dates), dtype=float)
    shared = 0.0012 * np.sin(index / 13.0) + 0.0007 * np.cos(index / 5.0)
    beta = 0.25 + (sum(map(ord, ticker)) % 90) / 100.0
    overnight = rng.normal(0.0, 0.0007, len(dates))
    intraday = beta * shared + rng.normal(0.0001, 0.002, len(dates))
    open_price = start_price * np.cumprod(1.0 + overnight)
    close_price = open_price * (1.0 + intraday)
    high = np.maximum(open_price, close_price) * (1.0 + rng.uniform(0.0002, 0.003, len(dates)))
    low = np.minimum(open_price, close_price) * (1.0 - rng.uniform(0.0002, 0.003, len(dates)))
    return pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "Open": open_price,
        "High": high,
        "Low": low,
        "Close": close_price,
        "Adj Close": close_price,
        "Volume": rng.integers(100_000, 2_000_000, len(dates)),
    })


def generate_synthetic_sources(config: dict) -> tuple[dict[str, pd.DataFrame], dict]:
    """Create synthetic target and cross-market histories plus fictional COT."""
    seed = int(config["seed"])
    count = int(config["sessions"])
    if count < 100:
        raise ValueError("Synthetic demo requires at least 100 NYSE sessions")
    calendar = xcals.get_calendar("XNYS")
    start = pd.Timestamp(config["start_date"])
    end = start + timedelta(days=count * 2)
    sessions = calendar.sessions_in_range(start, end).tz_localize(None)[:count]
    if len(sessions) != count:
        raise ValueError(f"Could not create {count} synthetic NYSE sessions from {start.date()}")

    market_sources: dict[str, pd.DataFrame] = {}
    market_features = config["market_features"]
    tickers = list(dict.fromkeys([*config["target_symbols"], *market_features.keys()]))
    start_price = float(config.get("market_start_price", 100.0))
    for ticker in tickers:
        labels = pd.date_range(sessions[0], sessions[-1], freq="D") if ticker.endswith("-USD") else sessions
        market_sources[ticker] = _price_frame(labels, ticker, start_price, seed)

    cot_rows: list[dict] = []
    # A made-up weekly Friday release, timestamped after the simulated NYSE close.
    session_closes = calendar.schedule["close"]
    for position, session in enumerate(sessions):
        if session.weekday() != 4:
            continue
        release = pd.Timestamp(session_closes.loc[session]) + timedelta(hours=2)
        report_index = max(0, position - 3)
        report_date = sessions[report_index]
        for ticker_index, ticker in enumerate(config["target_symbols"]):
            wave = 0.08 * np.sin(position / 11.0 + ticker_index)
            scale = 1 + ticker_index
            oi = 50_000 * scale
            managed_long = int(oi * (0.32 + wave))
            managed_short = int(oi * (0.24 - wave / 2))
            producer_long = int(oi * (0.28 - wave / 3))
            producer_short = int(oi * (0.30 + wave / 2))
            cot_rows.append({
                "ticker": ticker,
                "report_date": report_date.strftime("%Y-%m-%d"),
                "available_at": release.isoformat().replace("+00:00", "Z"),
                "source_url": f"{SYNTHETIC_SOURCE_URL}/cot",
                "open_interest": oi,
                "managed_long": managed_long,
                "managed_short": managed_short,
                "producer_long": producer_long,
                "producer_short": producer_short,
            })
    if not cot_rows:
        raise ValueError("Synthetic dates did not include any Friday COT fixture releases")
    sources = {**market_sources, "cot": pd.DataFrame(cot_rows)}
    metadata = {
        "synthetic_only": True,
        "warning": "FICTIONAL DATA. NOT HISTORICAL MARKET OBSERVATIONS OR INVESTMENT RESULTS.",
        "generator": "capstone.synthetic_demo.generate_synthetic_sources",
        "seed": seed,
        "session_count": count,
        "start_date": sessions[0].strftime("%Y-%m-%d"),
        "end_date": sessions[-1].strftime("%Y-%m-%d"),
        "source_url": SYNTHETIC_SOURCE_URL,
        "tickers": tickers,
        "cot_release_rule": "Invented Friday timestamp two hours after the simulated NYSE close; not a CFTC schedule.",
    }
    return sources, metadata


def _figure_png(fig, path: Path) -> str:
    fig.savefig(path, format="png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(path.read_bytes()).decode("ascii")


def _chart_block(encoded: str, title: str, alt: str) -> str:
    return (f"<section><h2>{title}</h2><img alt=\"{alt}\" "
            f"src=\"data:image/png;base64,{encoded}\"></section>")


def run_human_demo(config_path: str | Path | None = None, *, source_dir: str | Path | None = None,
                   output_dir: str | Path | None = None, open_browser: bool | None = None) -> dict:
    """Generate snapshots, run the real feature/model/simulation code and render HTML."""
    root = _project_root()
    demo_path = Path(config_path or root / "config" / "synthetic_demo.yml")
    if not demo_path.is_absolute():
        demo_path = root / demo_path
    demo = yaml.safe_load(demo_path.read_text(encoding="utf-8"))
    config = read_config(root / "config" / "config.yml")
    config["market_features"] = dict(config["market_features"])
    sources, source_metadata = generate_synthetic_sources({**config, **demo})

    raw_dir = Path(source_dir or root / demo["source_dir"])
    report_dir = Path(output_dir or root / demo["output_dir"])
    if not raw_dir.is_absolute():
        raw_dir = root / raw_dir
    if not report_dir.is_absolute():
        report_dir = root / report_dir
    raw_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    # Exercise a replayable local-snapshot boundary: write then reload the inputs.
    loaded: dict[str, pd.DataFrame] = {}
    for ticker, bars in sources.items():
        file_name = "cot.csv" if ticker == "cot" else f"{ticker.replace('^', 'index-').replace('-', '_')}.csv"
        bars.to_csv(raw_dir / file_name, index=False)
        loaded[ticker] = pd.read_csv(raw_dir / file_name)
    (raw_dir / "manifest.json").write_text(json.dumps(source_metadata, indent=2) + "\n", encoding="utf-8")

    print("[1/5] Replaying deterministic synthetic source files")
    features = build_features(loaded, config)
    feature_columns = numeric_features(config)
    print(f"[2/5] Built point-in-time features: {len(features)} rows")
    modeling = fit_predict(features, feature_columns, config)
    predictions = modeling["predictions"]
    print(f"[3/5] Selected {modeling['selected_model']} using validation only")
    prices = []
    for ticker in config["target_symbols"]:
        frame = _market_frame(loaded[ticker], ticker)[["date", "adjusted_open"]].copy()
        frame["ticker"] = ticker
        prices.append(frame)
    simulation_config = {**config, "threshold": modeling["selected_threshold"]}
    simulation = run_backtest(predictions, pd.concat(prices, ignore_index=True), simulation_config)
    vectorized = run_vectorized_backtest(predictions, simulation_config)
    print("[4/5] Ran cost-aware simulations on the synthetic test split")

    price_fig, price_ax = plt.subplots(figsize=(11, 4.5))
    for ticker in [*config["target_symbols"], "BTC-USD", "NVDA", "^GSPC"]:
        if ticker in loaded:
            normalized = _market_frame(loaded[ticker], ticker)
            price_ax.plot(normalized.date, normalized.adj_close / normalized.adj_close.iloc[0] * 100,
                          linewidth=1.2, label=ticker)
    price_ax.set_title("Fictional input price paths, rebased to 100")
    price_ax.set_ylabel("Synthetic index level")
    price_ax.legend(ncol=5, fontsize=8)
    price_ax.grid(alpha=.2)
    price_png = _figure_png(price_fig, report_dir / "input_prices.png")

    test_predictions = predictions.loc[predictions.split == "test"]
    pred_fig, pred_ax = plt.subplots(figsize=(11, 4.5))
    for ticker, rows in test_predictions.groupby("ticker"):
        pred_ax.plot(rows.date, rows.target, label=f"{ticker} synthetic target", alpha=.8)
        pred_ax.plot(rows.date, rows.prediction, label=f"{ticker} prediction", alpha=.8, linestyle="--")
    pred_ax.axhline(0, color="black", linewidth=.7)
    pred_ax.set_title("Synthetic held-out targets and predictions")
    pred_ax.set_ylabel("Five-session return (synthetic)")
    pred_ax.legend(ncol=2, fontsize=8)
    pred_ax.grid(alpha=.2)
    pred_png = _figure_png(pred_fig, report_dir / "predictions.png")

    equity_fig, equity_ax = plt.subplots(figsize=(11, 4.5))
    for strategy, rows in simulation["equity"].groupby("strategy"):
        equity_ax.plot(rows.date, rows.equity, label=f"Event simulation: {strategy}")
    equity_ax.plot(vectorized["equity"].date, vectorized["equity"].equity,
                   label="Vectorized fixed-notional approximation", linestyle=":")
    equity_ax.set_title("Synthetic holdout simulation; not real portfolio performance")
    equity_ax.set_ylabel("Synthetic demo capital units")
    equity_ax.legend(ncol=2, fontsize=8)
    equity_ax.grid(alpha=.2)
    equity_png = _figure_png(equity_fig, report_dir / "equity_curves.png")

    model_test = modeling["model_metrics"].query("split == 'test'").iloc[0].to_dict()
    metrics = simulation["metrics"].to_dict(orient="records")
    report = {
        **source_metadata,
        "source_dir": str(raw_dir),
        "output_dir": str(report_dir),
        "source_rows": {ticker: len(frame) for ticker, frame in loaded.items()},
        "feature_rows": len(features),
        "numeric_features": feature_columns,
        "model": modeling["selected_model"],
        "validation_selected_threshold": modeling["selected_threshold"],
        "split_dates": modeling["split_dates"],
        "synthetic_holdout_model_metrics": model_test,
        "synthetic_holdout_simulation_metrics": metrics,
        "vectorized_approximation_metrics": vectorized["metrics"],
        "limitations": [
            "Every value is generated and fictional; no provider or historical market data is used.",
            "Synthetic metrics demonstrate software flow only and are not evidence about strategy quality.",
            "The held-out synthetic period is an engineering fixture, not an empirical research holdout.",
        ],
    }
    report_path = report_dir / "summary.json"
    html_path = report_dir / "index.html"
    report["html_report"] = str(html_path)
    report["summary_json"] = str(report_path)
    report_path.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Synthetic Workflow Demo</title>
<style>body{{font:16px/1.5 system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#182230}}h1{{margin-bottom:.2rem}}.warning{{background:#fff0f0;border:2px solid #b42318;color:#7a271a;padding:1rem;font-weight:700}}section{{margin:2rem 0}}img{{width:100%;height:auto;border:1px solid #ddd}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #d0d5dd;padding:.5rem;text-align:left}}code{{background:#f2f4f7;padding:.1rem .25rem}}</style></head>
<body><h1>Synthetic workflow demo</h1>
<p class="warning">FICTIONAL SYNTHETIC DATA ONLY — NOT HISTORICAL QUOTES, A REAL EXPERIMENT, OR INVESTMENT PERFORMANCE.</p>
<p>This local human demo executes the project's real feature, chronological model-selection, and simulation functions on deterministic generated inputs. No market-data provider is contacted.</p>
<h2>What ran</h2><table><tr><th>Stage</th><th>Observed output</th></tr>
<tr><td>Generated source fixtures</td><td>{len(loaded)} sources; {sum(len(x) for x in loaded.values()):,} source rows; seed {source_metadata['seed']}</td></tr>
<tr><td>Point-in-time feature table</td><td>{len(features):,} rows; {len(feature_columns)} numeric features; targets GLD and SLV</td></tr>
<tr><td>Chronological model stage</td><td>Selected {modeling['selected_model']} using validation; threshold {modeling['selected_threshold']}; test dates {modeling['split_dates']['test_start']} to {source_metadata['end_date']}</td></tr>
<tr><td>Simulation</td><td>Event-ordered cost-aware strategies, buy-and-hold baseline, and vectorized approximation</td></tr></table>
<p><strong>Important:</strong> All metric values below arise from fictional values and a synthetic time series. They demonstrate that code paths ran; they do not measure or support a trading strategy.</p>
<h2>Synthetic-only run details</h2><pre>{json.dumps(report, indent=2, default=str)}</pre>
{_chart_block(price_png, '1. Synthetic inputs', 'Fictional generated price paths for target ETFs and selected cross-market features')}
{_chart_block(pred_png, '2. Feature and model flow', 'Synthetic held-out target and prediction paths by target ETF')}
{_chart_block(equity_png, '3. Simulation outputs', 'Synthetic-only equity curves for strategies and vectorized approximation')}
<p>Replay inputs are under <code>{raw_dir}</code>; this report and PNG assets are under <code>{report_dir}</code>. Both directories are generated local outputs and ignored by Git.</p>
</body></html>"""
    html_path.write_text(html, encoding="utf-8")
    print("[5/5] Wrote visual report and machine-readable summary")
    if open_browser if open_browser is not None else bool(demo.get("open_browser", False)):
        webbrowser.open(html_path.resolve().as_uri())
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=None, help="Path to synthetic demo YAML")
    parser.add_argument("--open", action="store_true", help="Open the generated report in a browser")
    args = parser.parse_args()
    result = run_human_demo(args.config, open_browser=args.open)
    print("Synthetic demo finished. All input values are fictional; this is not a financial result.")
    print(f"Synthetic source snapshots: {result['source_dir']}")
    print(f"Features: {result['feature_rows']} rows; numeric features: {len(result['numeric_features'])}")
    print(f"Model: {result['model']}; validation-selected threshold: {result['validation_selected_threshold']}")
    print(f"HTML report: {result['html_report']}")
    print(f"Machine-readable summary: {result['summary_json']}")


if __name__ == "__main__":
    main()
