# Capstone research requirements

This baseline is written in an OpenSpec-style requirement/scenario format. It has not been validated by an OpenSpec CLI; install and run the CLI only through a supported, verified workflow.

## Purpose

Support a reviewer in reproducing a cautious investigation of whether COT and cross-market data help predict five-session GLD and SLV returns and whether cost-aware signals compare favorably with a stated baseline on an untouched holdout.

## Requirements

### Requirement: Full-COT experiment evidence
The acceptance experiment SHALL use frozen real snapshots, confirmed COT releases and at least 500 labeled dates, 150 distinct confirmed reports used, and 1095 days of signal coverage per ETF. After chronological purging, each ETF SHALL retain at least 250 train, 75 validation and 75 holdout dates. These operational minima do not establish statistical power. The existing exploratory CLI remains available; `python -m capstone.research` enforces this acceptance gate.

For post-launch CFTC Public Reporting Environment records, a conservative API availability cutoff MAY be established from official per-row creation timestamps after 2022-10-20. Both target contracts SHALL be present, creation SHALL equal last-update time, and all five modeled position fields SHALL exactly match the verified annual archive. Wait until 05:00 UTC on the day after the later creation timestamp. Retain the raw API response, query, retrieval time, archive hashes and field comparison audit. This establishes conservative API availability, not an assertion of the original static-report publication instant; pre-launch bulk imports and modified/mismatching records SHALL be excluded. See [executed experiment](../../../docs/FULL_RUN.md) for source evidence and limitations.

#### Scenario: Insufficient confirmed history
- **WHEN** any minimum fails
- **THEN** persist input hashes and coverage, exit with status 2 before model fitting, and leave full-run acceptance open.

#### Scenario: Frozen experiment and repeat
- **GIVEN** adequate real confirmed history
- **WHEN** the acceptance runner executes
- **THEN** save code/config/snapshot SHA-256, environment versions, commands, per-ETF split/purge counts, validation candidate and threshold scores, fixed mean baseline versus selected model holdout metrics, and capital-aware strategy/benchmark costs and turnover.
- **AND** execute twice offline using the same frozen inputs and code; accept reproduction only if inputs remain unchanged and all numerical CSV/JSON outputs match exactly. Plots, binary estimators and run timestamps are excluded from byte equality.

#### Scenario: Incomplete or relocated replay
- **WHEN** both calculations omit the same required output
- **THEN** reproduction fails even if the remaining files match.
- **WHEN** a completed bundle is relocated and replayed with `--replay`
- **THEN** resolve data paths inside the bundle, verify saved input hashes and dependency versions, and require agreement with both the new repeat and original numerical results; refuse tampered inputs before execution.

### Requirement: Standalone reproducibility
The project SHALL provide local setup, documented external data retrieval, reload from local snapshots, stage scripts, a notebook orchestrator and a single end-to-end command. It SHALL NOT require code or data from a reference project at runtime.

#### Scenario: Cached input rerun
- **GIVEN** complete previously retrieved source snapshots and their metadata
- **WHEN** the user executes the documented offline workflow with the same configuration
- **THEN** it uses those snapshots and reports outputs and limitations without silently fetching replacement data.

#### Scenario: Repeated source replay
- **GIVEN** unchanged, checksum-valid source snapshots and the same date range
- **WHEN** the source loader is called repeatedly
- **THEN** each call returns the same date-ordered market rows and report-ordered COT rows without changing the snapshots or contacting providers.
- **AND** duplicate market dates or COT ticker/report dates fail clearly instead of multiplying observations.

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

#### Scenario: Validation candidate comparison
- **WHEN** model selection completes on sufficient chronological, purged history
- **THEN** export `model_comparison.csv` with each candidate's identifier, estimator class, actual estimator parameters, validation MAE/RMSE and an explicit selected flag; show the comparison in the CLI and workflow notebook.
- **AND** select exactly one candidate by minimum validation MAE, preserving candidate order for ties. Holdout labels SHALL NOT affect the comparison or selection; holdout scores remain separate.
- **AND** an insufficient-history run SHALL NOT generate candidate scores. A market-only diagnostic SHALL remain explicitly separate from COT-inclusive evidence.

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
| Problem: clear steps, findings and reproduction | Draft: README provides a reviewer route; findings and frozen-bundle replay are documented in the canonical full-run report. Two current-code calculations match 20 numerical outputs. |
| **Data: lecture sources and features** | Draft: [feature dictionary](../../../docs/FEATURE_DICTIONARY.md) maps project sources and transformations to official Modules 1–5; a full COT-inclusive run and replay are recorded in [the experiment report](../../../docs/FULL_RUN.md). The 20+ described-feature course criterion remains open; five derived examples are currently documented. |
| Data: 20+ described new features | Open: [settings](../../../config/settings.yml) enumerate numeric inputs; do not count source inputs or assume all are new, available and meaningful. |
| Data: new source beyond YFinance/FRED | Draft: CFTC ingestion and [release evidence](../../../docs/COT_RELEASE_EVIDENCE.md) exist; usable real source coverage and experiment remain unverified. |
| Data: over one million records | Open: no real dataset or verified row count. |
| **Transform: combined table and feature sets** | Draft: [feature implementation](../../../src/capstone/features.py) and frozen experiment bundle provide a 1,916-row modeled table, 1,906 labeled rows and 211 COT report dates after point-in-time filtering. |
| Transform: at least five relevant new features | Draft: five derived features are defined and available in the limited table; relevance and stability on adequate real history remain unverified. |
| Transform: EDA | Draft: [market EDA](../../../docs/EDA_FINDINGS.md) covers full local price history and validation candidate results; independent review and broader sensitivity remain open. |
| **Model: DecisionTree or RandomForest** | Draft: the canonical COT-inclusive comparison evaluates DecisionTree and RandomForest candidates against the mean baseline and selects mean by validation MAE. The current-code frozen experiment matches 20 numerical output hashes across two calculations; see [the full-run report](../../../docs/FULL_RUN.md). Reviewer acceptance remains unverified. |
| Model: more than one lecture model | Draft: DecisionTree and RandomForest candidates were fitted on train and compared on full-COT validation; [candidate parameters, metrics and selected flag](../../../docs/EDA_FINDINGS.md#full-cot-validation-candidate-comparison) are exported. Reviewer acceptance remains unverified. |
| Model: custom rules for higher-probability events | Open: demonstrate that actual rules and their validation satisfy the rubric; return-regression thresholds alone do not establish calibrated probabilities. |
| Model: hyperparameter tuning | Draft: configured tree/forest depths and Ridge alphas were compared on full-COT validation; the canonical run selected `mean` by validation MAE. No settings were changed in response to holdout. Reviewer acceptance remains unverified. |
| Model: new model | Draft: Ridge alpha 1 and 10 were compared on full-COT validation; neither won. Reviewer acceptance remains unverified. |
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
