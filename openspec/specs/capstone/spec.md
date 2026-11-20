# Capstone research requirements

This baseline is written in an OpenSpec-style requirement/scenario format. It has not been validated by an OpenSpec CLI; install and run the CLI only through a supported, verified workflow.

## Purpose

Support a reviewer in reproducing a cautious investigation of whether COT and cross-market data help predict five-session GLD and SLV returns and whether cost-aware signals compare favorably with a stated baseline on an untouched holdout.

## Requirements

### Requirement: Standalone reproducibility
The project SHALL provide local setup, documented external data retrieval, reload from local snapshots, stage scripts, a notebook orchestrator and a single end-to-end command. It SHALL NOT require code or data from a reference project at runtime.

#### Scenario: Cached input rerun
- **GIVEN** complete previously retrieved source snapshots and their metadata
- **WHEN** the user executes the documented offline workflow with the same configuration
- **THEN** it uses those snapshots and reports outputs and limitations without silently fetching replacement data.

### Requirement: Information availability
Every feature SHALL be available by its documented signal cutoff. COT observations SHALL have a confirmed public release time, and unavailable or unconfirmed releases SHALL be excluded. Completed crypto candles and the ETF exchange calendar SHALL be respected.

#### Scenario: Publication after signal
- **GIVEN** a COT observation published after a session's signal cutoff
- **WHEN** features are assembled for that signal
- **THEN** the observation is not available to that signal.

#### Scenario: Unconfirmed release
- **GIVEN** a COT observation without confirmed release availability
- **WHEN** a dataset is constructed
- **THEN** the observation is excluded and the gap is reported.

### Source and timing contract (reviewed 2026-11-21)

- Treat a COT report's observation date and public release as separate fields. An archive row or planned schedule date alone does not establish `available_at`; require report-specific contemporaneous evidence, use an explicitly conservative UTC cutoff when the exact hour is absent, and retain source and retrieval provenance.
- Apply the actual NYSE session calendar, including holidays and early closes, to ETF signal cutoffs. A daily ETF bar is available only after that session closes. Crypto daily bars are available only after the bar's UTC day has ended. Historical vendor prices may be revised or retrospectively adjusted and must be documented as a point-in-time limitation.
- Record independent source, request/retrieval timestamps, and failure state for every configured series. Optional-market failures must not silently alter required targets; unconfirmed required data must fail clearly or be reported as unavailable. Verify current provider terms and schedules before broad use or after announced schedule changes.
- This contract is grounded in the [COT publication evidence](../../../docs/COT_RELEASE_EVIDENCE.md); it does not add release dates to the manifest or claim a successful provider download.

### Requirement: Chronological model selection
The project SHALL document signal and execution times and a five-trading-session target. It SHALL compare a baseline and a DecisionTree or RandomForest with chronological training, validation and holdout. Overlapping labels SHALL be purged at boundaries; holdout SHALL not be used to select models or strategy parameters.

#### Scenario: Target crosses a split boundary
- **GIVEN** a training observation whose target ends in validation
- **WHEN** the split is constructed
- **THEN** the observation is purged from training.

#### Scenario: Latest signal uses a frozen model
- **GIVEN** the latest signal is produced by a model trained only through validation
- **WHEN** the signal report is generated
- **THEN** it includes the latest training-label exit date so the model's age is visible.

### Requirement: Cost-aware simulation
The project SHALL define capital, position sizing, execution, transaction costs, slippage and a meaningful benchmark on the same evaluation period. It SHALL report relevant performance metrics and limitations only from actual runs.

#### Scenario: Trade and transaction costs
- **GIVEN** a known entry and exit, available capital and configured costs
- **WHEN** the simulator processes the trade
- **THEN** cash and equity reflect executed quantities and both sides' costs.

### Requirement: Honest evidence and documentation
The project SHALL describe sources, features, methods, data and model limitations, setup, results, and course criteria in English. Results, tests, service integrations and deployments SHALL be distinguished from planned work.

#### Scenario: External data unavailable
- **GIVEN** an external source cannot be reached and no suitable local snapshot exists
- **WHEN** the workflow is run
- **THEN** it reports the missing dependency without manufacturing records, metrics or a successful run.

### Requirement: Explicit local configuration
The project SHALL keep source scope and paths separate from research/runtime settings in documented YAML files. Secret values SHALL be supplied through environment variables rather than checked-in configuration.

#### Scenario: Disable optional market feature
- **GIVEN** a cross-market source is removed from the configured optional feature map
- **WHEN** sources are loaded and the feature set is built
- **THEN** the optional source is not downloaded and its feature is not included in model inputs.

#### Scenario: Configuration key collision
- **GIVEN** the same top-level key is present in source config and settings
- **WHEN** the configuration is loaded
- **THEN** the workflow reports the conflict instead of silently choosing one value.

## Course acceptance evidence matrix

Reviewed against the [official course project rubric](https://github.com/DataTalksClub/stock-markets-analytics-zoomcamp/blob/main/projects/README.md), including the 2026 submission section, on 2026-11-21. This is an evidence inventory, not a score or reviewer decision. **Draft** means an artifact exists but course acceptance is unverified; **open** means the requested evidence or outcome has not been established. See the [backlog](../../../.ai/BACKLOG.md) for action ownership and [status](../../../.ai/STATUS.md) for recorded checks. Actual results must come from real runs.

| Rubric item | Status and evidence or gap |
|---|---|
| **Problem: brief README description** | Draft: [README](../../../README.md) describes GLD/SLV forecasting; reviewer acceptance unverified. |
| Problem: context, goal and usage | Draft: README identifies an analyst and benchmark comparison; validate against actual workflow. |
| Problem: new definition | Draft: two precious-metals ETFs and COT differ from the course's largest-stock setup. |
| Problem: clear steps, findings and reproduction | Open: commands and methods are described, but actual findings and complete reproducibility are absent. |
| **Data: lecture sources and features** | Open: Yahoo-based ingestion and feature code exist; full lecture-by-lecture mapping and real source execution are unverified. |
| Data: 20+ described new features | Open: [settings](../../../config/settings.yml) enumerate numeric inputs; do not count source inputs or assume all are new, available and meaningful. |
| Data: new source beyond YFinance/FRED | Draft: CFTC ingestion and [release evidence](../../../docs/COT_RELEASE_EVIDENCE.md) exist; usable real source coverage and experiment remain unverified. |
| Data: over one million records | Open: no real dataset or verified row count. |
| **Transform: combined table and feature sets** | Draft: [feature implementation](../../../src/capstone/features.py) and config define the approach; real combined table has not been produced. |
| Transform: at least five relevant new features | Draft: feature transformations exist; establish and describe at least five meaningful, available derived features on real data. |
| Transform: EDA | Open: actual target distributions, correlations and findings require a real dataset. |
| **Model: DecisionTree or RandomForest** | Draft: [modeling code](../../../src/capstone/modeling.py) contains candidates; real training and predictions are unverified. |
| Model: more than one lecture model | Draft: candidate definitions exist; actual comparisons require execution. |
| Model: custom rules for higher-probability events | Open: demonstrate that actual rules and their validation satisfy the rubric; return-regression thresholds alone do not establish calibrated probabilities. |
| Model: hyperparameter tuning | Draft: search code exists; no real tuning outcome verified. |
| Model: new model | Draft: Ridge candidate exists; no real comparison verified. |
| **Simulation: vector strategy and approximate capital return** | Draft: [simulation code](../../../src/capstone/backtest.py) contains a fixed-notional approximation; real execution and course acceptance remain unverified. |
| Simulation: at least two strategies | Draft: rules exist; demonstrate per-prediction outputs and comparisons on actual data. |
| Simulation: exact reinvestment and efficient capital use | Draft: cash-constrained event simulation exists; full real run and rubric acceptance of capital efficiency are unverified. |
| Simulation: benchmark and performance discussion | Open: no actual net returns, CAGR, Sharpe, drawdown or rolling returns have been produced. |
| Simulation: advanced strategy features | Open: define and test a justified risk-management or comparable feature; do not infer credit from existing accounting. |
| Simulation: new empirical strategy | Open: establish a genuinely distinct rule and evaluation on actual data; the reviewer decides credit. |
| Simulation: benchmark outperformance | Open: an empirical outcome, not a promised deliverable; test on the untouched period after costs. |
| Simulation: deep analysis and wrong predictions | Open: no real subgroup, error or improvement analysis. |
| **Automation: exported scripts and one end-to-end notebook** | Draft: [notebook](../../../notebooks/workflow.ipynb) and modules exist; complete download-to-latest-trades execution is unverified. |
| Automation: managed dependencies | Draft: [project dependencies](../../../pyproject.toml), lockfile and README exist; clean installation remains unverified. |
| Automation: cron-compatible latest predictions | Open: one-command workflow exists in code; scheduled, complete latest-data execution has not been demonstrated. |
| Automation: file and download modes | Draft: code has local and online paths; full real-snapshot replay and the rubric's no-transform file mode are unverified. |
| Automation: incremental loading/transformations | Open: snapshot caching is not demonstrated incremental loading or transformation. |
| Bonus: modular, well-designed and commented code | Draft: modules exist; independent qualitative review and reviewer credit remain open. |
| Bonus: broker API | Open; no broker integration claimed. |
| Bonus: live monitoring/dashboard or bot | Open; no live monitoring claimed. |
| Bonus: containerization | Open; no container verification claimed. |
| Bonus: cloud deployment | Open; no deployment claimed. |
| Bonus: subjective reviewer points | Open; determined by peer reviewers. |

The rubric requires the six bold points, individual presentation and evaluation of three peer projects to obtain points. The official 2026 attempt 1 page lists a deadline of 2026-11-20 23:59:59 Dublin time; submission status and any later attempt require current confirmation. No submission, defense or peer review is evidenced here. Do not interpret the rubric's 36-point maximum or additional peer-review points as earned by this project.
