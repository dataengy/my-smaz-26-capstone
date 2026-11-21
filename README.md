**EN** | [RU](docs/README.ru.md)

# Precious Metals ETF Forecasting with CFTC Positioning

## Project status

**Work in progress; no empirical results have been produced.** The development environment could not resolve CFTC, Yahoo Finance or PyPI. The release-evidence file contains only four independently evidenced historical reports, which are insufficient for the intended experiment. Consequently the end-to-end experiment, source formats in live downloads, full calendar test suite, clean installation, and notebook execution remain unverified. A focused exchange-calendar check passed in the project environment. This repository does not claim profitability or benchmark outperformance.

This educational research project investigates whether futures positioning, market history and cross-market signals can help a researcher estimate the next five-session return of GLD and SLV. The user is an analyst comparing hypothetical signals with passive ETF exposure, not someone receiving investment advice. Unlike the course's largest-stock weekly setup, the traded universe is two precious-metals ETFs and the study adds CFTC futures positioning and crypto/stock-market context.

## Setup and running

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/). The resolved dependency versions are in `uv.lock`. Core dependencies were installed locally, but a clean installation including test and notebook dependencies is not yet verified due to intermittent DNS failures.

```bash
export UV_PROJECT_ENVIRONMENT=.run/venv UV_CACHE_DIR=.run/uv-cache
uv sync --locked --extra dev
uv run capstone download --config config/config.yml --settings config/settings.yml
# Extend config/release_dates.csv with independently evidenced publication times.
uv run capstone run --config config/config.yml --settings config/settings.yml --offline
uv run --locked --extra test python -m pytest -q
```

Alternatively `uv run capstone run` downloads and then runs; `make download`, `make run`, `make run-notebook`, and `make test` are shortcuts. `make run-notebook` opens `notebooks/workflow.ipynb` in Jupyter from the project root. The notebook calls the same Python functions. Outputs are written under `artifacts/`; downloaded data and outputs are excluded from Git. Refreshing snapshots overwrites the local snapshot for that source; keep a separate copy to freeze a previous run. See the [command reference](docs/COMMANDS.md) for all Make and Just operations.

For an offline walkthrough that does not use real market observations, run `make demo-synthetic`; it creates generated source-shaped rows in `data/synthetic/human-demo/` and opens a prominently labeled visual report under `artifacts/synthetic-demo/`. Run `make test-demo-synthetic` to verify that the report and charts render. See the [synthetic demo guide](docs/SYNTHETIC_DEMO.md). Its generated metrics are software-demo output only, not research results.

A local file run verifies SHA-256 sidecars. Market snapshots also record request-start time: bars are eligible only after the NYSE session close or crypto UTC midnight, as applicable. Legacy market snapshots without request-start metadata must be refreshed; replay never promotes a previously incomplete bar. `config/release_dates.csv` must contain `report_date,available_at,source_url`, with independently substantiated availability in explicit UTC and an HTTPS evidence link per report. The four included reports are insufficient for the planned experiment; see [publication evidence](docs/COT_RELEASE_EVIDENCE.md). The timestamps are conservative eligibility cutoffs, not actual release instants. A forecast must not use a report based only on its observation date or an unverified schedule. Availability evidence is a human-reviewed input, not something the parser independently authenticates. Consider holidays, the 2025 federal funding lapse and later schedule changes. The [CFTC historical FAQ](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm) says there is no full historical release-date list; the [2026 schedule](https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm) is tentative, not proof of publication. The [backlog announcement](https://www.cftc.gov/PressRoom/PressReleases/9147-25) illustrates exceptional delays. Newer schedules must be verified before use.

## Developer checks and GitHub CI

The `dev` extra includes the pinned [`prek`](https://prek.j178.dev/) hook runner. Run `uv sync --locked --extra dev`, then `make hooks` to check all files or `make install-hooks` to install the local pre-commit hook. The hook configuration is in `.pre-commit-config.yaml`. GitHub Actions is configured to run those hooks and the locked test suite on pushes to `main`, pull requests, and manual dispatch. CI uses fixtures and does not download market data or verify the real-data research workflow.

## Data and methodology

CFTC [disaggregated futures-only annual archives](https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm) supply COMEX gold and silver open interest and managed-money and producer long/short positions. They are public US government reports; consult the provider's terms and attribution notices. Archives are locally cached with download timestamps, source and checksum. Yahoo Finance prices are retrieved using yfinance, which is an unaffiliated tool for educational/research use; [Yahoo data is intended for personal use](https://ranaroussi.github.io/yfinance/). Provider availability, rate limits, revisions and terms can change. Optional SOL-USD, ETH-USD, ZEC-USD, S&P 500, Nasdaq Composite and Dow Jones data may be absent; required rows include GLD, SLV, BTC-USD and NVDA. FRED is deferred until vintage and publication timing can be verified.

The combined table has one row per ETF/session with a timely evidenced COT report. `TO_PREDICT` is adjusted-open return from the next session's open to the open five sessions later; `DUMMIES` contains ticker. `NUMERIC` includes ETF 1/5/20-session returns, 5/20-session volatility, distance to 20-session mean, five-session volume change, COT managed/producer net positioning divided by open interest, change in managed positioning, age of COT, and five-observation returns of the available cross-market series. Missing optional inputs remain missing and model imputation is fitted on training data only. The price adjustment factor also adjusts opens, approximating total return; it is not a separate dividend cash ledger, and provider revisions or corporate-action adjustments can introduce point-in-time limitations.

Source dates, storage locations, targets, required and optional tickers, and the ticker-to-feature map live in [`config/config.yml`](config/config.yml). Remove an optional ticker from `market_features` to disable its download and model input; required tickers remain active. Research timing, freshness windows, provider timeouts, chronological split fractions, model search grid, thresholds, costs, capital, report output and the local Codex session path live in [`config/settings.yml`](config/settings.yml). CLI `--config` and `--settings` options can point to alternate YAML files; settings keys may not duplicate source-config keys. Credentials do not belong in either file.

Signals are generated at the actual NYSE close, including early closes; entries occur at the next open. Crypto daily bars are usable only after the next UTC midnight. COT joins use evidenced publication timestamps and expire after seven days by default. Exchange-session validation rejects missing ETF bars. Current source files can differ from information available historically, which remains a research limitation.

Distinct session dates are divided chronologically into train/validation/test (default 60/20/20), with observations purged where their target exits on or beyond the next split. A mean baseline, Ridge, DecisionTree and RandomForest candidates are compared by validation MAE. A trading threshold is selected on validation only; the selected model is refit on eligible train and validation observations and tested on the held-out period. Overlapping long/cash trades use available cash and fixed per-lot allocation; a threshold rule and equal-weight buy-and-hold are compared over the same window. Combined commission and slippage default to 10 basis points per side; capital defaults to 100,000 units. Results include MAE, RMSE, total return, CAGR, Sharpe, drawdown and equity charts when execution succeeds. A vectorized fixed-notional simulation accumulates closed-trade returns without reinvestment or daily marking; it assumes budgets remain affordable and is only an approximation. The reinvesting simulation is event-ordered and cash-constrained.

## Course checklist

| Criterion | Status |
|---|---|
| Problem and intended user documented | Drafted; awaiting review |
| Lecture sources and features | Partially implemented; live access and full lecture mapping unverified |
| One table and explicit feature sets | Implemented; real data run unverified |
| DecisionTree/RandomForest | Implemented; real training unverified |
| Vector simulation | Fixed-notional approximation implemented; real-data execution and course acceptance unverified |
| Notebook and script workflow, latest signals | Drafted; complete execution unverified |
| Extra features, CFTC source, EDA | Implemented in code; real evidence and results outstanding |
| Multiple models, tuning, trading rules and benchmark | Implemented in code; results outstanding |
| Reproducibility and local snapshots | Designed and partially tested; clean environment and real rerun outstanding |
| Individual presentation and three peer reviews | Not completed |
| Cloud, broker integration, deployment | Not completed; optional backlog |

The [official criteria](https://github.com/DataTalksClub/stock-markets-analytics-zoomcamp/blob/main/projects/README.md) are the source of truth for scoring. There is no claim that code alone has earned points.

## Limitations and defense

Risk factors include leakage from publication timing or source revisions, overlapping horizons, hyperparameter selection, a small fixed asset universe and survivorship/selection bias, transaction cost and liquidity assumptions, and historical performance that may not generalize. No signal is a guarantee of future returns. No live orders, cloud deployment or fabricated experiments are included.

For a defense: explain the problem and user; show source provenance and a confirmed COT timestamp; trace one signal through its next-open entry and five-session exit; demonstrate the local reproduction command; compare validation-selected models and held-out net equity with the benchmark; discuss errors and limitations. Actual numerical results must be added only after a successful real-data run.

The [documentation index](docs/index.md) describes the project, while the [project backlog](.ai/BACKLOG.md) tracks prioritized work, blockers and acceptance evidence. Agent roles, development rules and the shared plan are linked from [AGENTS.md](AGENTS.md). Local Codex usage metadata can be summarized with `make usage`; that report is experimental, incomplete and is not billing information.

Latest signals use the frozen train-plus-validation model, not a model retrained on the holdout. The report includes `model_training_last_exit` so its training cutoff is visible; it may be old.
