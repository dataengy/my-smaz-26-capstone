[EN](FULL_RUN.md) | [RU](FULL_RUN.ru.md)

# Reproduced full-COT experiment — 2026-11-21

**Canonical result: the validation-selected model is the mean baseline.** The current-code frozen experiment in `artifacts/full-cot-current-code-20261121/` ran twice; all 20 declared numerical outputs match their hashes. The separate `artifacts/full-cot-model-comparison-20261121/` bundle has the same frozen model code and result. Validation MAE is 0.036398 for mean and 0.036521 for `forest_3`; mean wins the predeclared MAE selection rule. Both holdout strategies lost money after modeled costs. See the independent [final QA report](FINAL_QA.md).

## Availability evidence and frozen data

The former nine-report bottleneck was resolved for this experiment through a separate audited manifest. The official [CFTC PRE launch announcement](https://www.cftc.gov/PressRoom/PressReleases/8612-22) dates public launch to 2022-10-20; the [2026 CFTC description](https://www.cftc.gov/media/13801/COTFinal043026/download) states simultaneous PRE publication since October 2022. [Socrata system-field documentation](https://dev.socrata.com/docs/system-fields.html) defines row creation and last-update timestamps. The audit uses those official per-row timestamps as evidence for a conservative public API availability cutoff. It does not assert the original static-report release instant.

The audit downloaded **426 API rows** for the two target contracts, yielding **213 paired report dates**. Every included record is after public launch, has equal creation/update timestamps, and exactly matches all five modeled position fields in hash-verified annual CFTC archives. Bulk pre-launch imports, changed/mismatching rows and incomplete pairs are excluded. Eligibility starts at **05:00 UTC on the day after the later creation timestamp of the pair**. This relies on the official public dataset's row metadata representing public ingestion; historical access logs are unavailable. The raw response, source query, retrieval timestamp, archive hashes and row audit are frozen with the experiment. Source evidence is retained under `inputs/release-evidence/`.

Market snapshots cover **2018-01-02–2026-11-20**, with **2235 rows per ETF**. The modeled table has **1916 rows**, including 1906 labeled rows (953 per ETF). Labeled signal dates cover **2022-10-31–2026-11-12**, a 1473-day span, using **211 report dates**; the final reports also support unlabeled/latest rows. Features include COT and all configured cross-market inputs. COT change has 0.5247% missingness among labeled rows and is imputed within the fitted pipeline; other modeled inputs have zero missingness in this run. Seven-day COT freshness was preserved.

## Chronology and model comparison

Counts below are per ETF; partitions use unique signal dates. A label must exit strictly before the next partition's first signal.

| Partition | Before purge | Purged | After purge | Retained signals | Last label exit |
|---|---:|---:|---:|---|---|
| Train | 571 | 6 | 565 | 2022-10-31–2025-03-05 | 2025-03-13 |
| Validation | 191 | 6 | 185 | 2025-03-14–2026-01-29 | 2026-02-06 |
| Holdout | 191 | 0 | 191 | 2026-02-09–2026-11-12 | 2026-11-20 |

The search and seed 42 were fixed before holdout inspection. Preprocessing is fitted inside each training pipeline; the final estimator refits the retained train and validation rows. Validation MAE chooses the model. Targets and errors below are decimal five-session returns.

| Model | Validation MAE | Validation RMSE |
|---|---:|---:|
| mean | 0.03639792 | 0.05862704 |
| ridge_1 | 0.04059626 | 0.06155964 |
| ridge_10 | 0.03980479 | 0.06096146 |
| tree_3 | 0.03643589 | 0.05863567 |
| tree_5 | 0.03677929 | 0.05890086 |
| forest_3 | 0.03652135 | 0.05866329 |
| forest_5 | 0.03674397 | 0.05888992 |

The mean baseline won. After the final refit, its holdout **MAE was 0.04425741 and RMSE 0.05882651**. The fixed-baseline holdout comparison equals the selected model because the winner itself is mean. All validation threshold objectives were **0.01710234113204263** for thresholds 0, 0.002 and 0.005; the predetermined tie handling selected 0. The proxy objective is not a portfolio return. No parameters were changed in response to holdout outcomes.

## Strategy results

Execution and benchmark period: **2026-02-10–2026-11-20**. Initial capital: **100000**, holding horizon: **five sessions**, combined commission/slippage: **10 bps per execution side**. Signals use the actual ETF session close, trades use next-session adjusted open, exit occurs five held sessions later. Overlapping lots are cash funded and capped at one tenth of marked equity; exits precede purchases. Buy-and-hold is equal weight GLD/SLV with both entry and liquidation costs.

| Strategy | Net return | CAGR | Sharpe | Max drawdown | Paid costs | Round trips |
|---|---:|---:|---:|---:|---:|---:|
| long_cash | -38.6062% | -46.7222% | -1.555794 | -43.5323% | 6398.53 | 382 |
| threshold | -38.6062% | -46.7222% | -1.555794 | -43.5323% | 6398.53 | 382 |
| buy_hold | -39.6260% | -47.8616% | -1.564580 | -43.6746% | 160.33 | 2 |

The two policies coincide because the selected threshold is zero. They are not independent empirical strategies in this run. Their gross traded notional was **6398529.27**, versus **160334.56** for buy-and-hold. The vectorized fixed-notional approximation returned **−43.3500%** over 382 selected trades; it uses different accounting and is not expected to equal the event simulation. Strategy Sharpe is based on daily marked-equity changes, using 252 sessions/year and zero risk-free rate.

## Commands, hashes and repeat

Actual acquisition, current-code freeze and replay commands:

```sh
.run/venv/bin/python -m capstone.cot_publication_audit --output artifacts/cot-publication-audit-20261121-retry
.run/venv/bin/python -m capstone.research --config .run/full-cot-verified-config.yml --output artifacts/full-cot-current-code-20261121
.run/venv/bin/python -m capstone.research --replay artifacts/full-cot-current-code-20261121 --output artifacts/full-cot-current-code-replay-NEW
```

The generated `.run/full-cot-verified-config.yml` freezes `end: 2026-11-21` (exclusive), points to the audited manifest, and otherwise uses the existing source universe and research settings. To reconstruct that local override after acquiring the audit:

```python
from pathlib import Path
import yaml
cfg = yaml.safe_load(Path("config/config.yml").read_text())
cfg.update(settings_file="config/settings.yml", end="2026-11-21",
           release_manifest="artifacts/cot-publication-audit-20261121-retry/release_dates.csv",
           release_evidence_dir="artifacts/cot-publication-audit-20261121-retry")
Path(".run/full-cot-verified-config.yml").write_text(yaml.safe_dump(cfg))
```

Existing output directories are never overwritten; choose fresh names for a new acquisition/experiment. For exact historical replay, use the saved bundle and `--replay`, which needs no current configuration or provider requests. Frozen source settings are also retained in `inputs/source-config.yml` and `inputs/source-settings.yml`.

The canonical current-code run is under `artifacts/full-cot-current-code-20261121/`; the prior `full-cot-model-comparison-20261121` run is retained as an independently repeated bundle with the same modeling/research code hashes and output metrics. The current-code bundle fingerprints **60 input files** and matches **20 numerical output hashes** across both calculations. Exact replay uses the frozen code and inputs in the bundle, validates them before execution, and requires equality with the recorded outputs. Relative bundle data paths support relocation. Plots, model binary bytes and timestamps are excluded from byte equality. Source code, snapshot sidecars, API provenance, config and dependency files are included in input fingerprints. The current evidence-file SHA-256 is `b840940466d32383eeb507ec58e0e690ce678e6a092a98c47107d08f86209635`.

| Input | SHA-256 |
|---|---|
| `release_dates.csv` | `694c02fb29237f0314815d6e1191ca8e136d3cc15b3e8a0409421d7cac293235` |
| `release-evidence/api-rows.json` | `886f76bc898fa1885dc73f25918a3ddbcbe674d4bf7e8f4eceb5f78525b057d1` |
| `effective-config.json` | `8a3440bff0f8bdf50a5908f1b58041eb026585e11b03940629ee63d745260758` |
| Verified `evidence.json` | `1e8b5f9e3b487e19915854b9de666e225619712989701b439646aac57f58c6e4` |

Recorded runtime: Python 3.12.14, NumPy 2.5.5, pandas 2.3.3, scikit-learn 1.9.1, exchange-calendars 4.13.3 and PyYAML 6.0.3. Replay checks these core versions; complete installed versions are recorded. It uses the existing environment rather than creating a fresh one.

## Verification and limits

The subprocess integration check covers an adequate-history fictional dataset, a relocated bundle replay, and rejection of a tampered manifest. Additional tests cover incomplete replay outputs, COT metadata validation, purging, holdout-label isolation, baseline arithmetic and transaction-cost reconciliation. Executed `CAPSTONE_E2E_CONFIG=.run/full-cot-verified-config.yml .run/venv/bin/python -m pytest -q -ra`: **73 passed, 3 skipped, 66 deprecation warnings**. The real offline E2E passed. Skips are the opt-in fresh-origin clone and two live-provider probes. They do not block the demonstrated snapshot experiment. The separate real saved-bundle replay also completed: all 58 input hashes and 19 numerical hashes match across four real calculations. Its `evidence.json` SHA-256 is `3c545b90665ed3bb074db5261c645fcb6ac8ff43c94046a4e4c46784bbd44851`.

The earlier `full-cot-20261121` and `full-cot-20261121-final` attempts remain as historical blocked evidence; they used nine confirmed release dates and did not train a model. The `full-cot-20261121-verified` run is also retained as an earlier implementation bundle. A separate, unprovenanced set of root outputs once reported `forest_3` and 1,964 feature rows beginning 2020-12-29. Those signals precede the 2022-10-20 public launch of CFTC PRE and were not accompanied by frozen code/config/input evidence; they are excluded from the defensible experiment. The current audited workflow begins signals on 2022-10-31, uses the 213-pair post-launch audit (211 report dates enter labeled rows), and selects mean on validation. Root-level generated CSV/JSON outputs were refreshed from the current-code frozen run. The bilingual report and EDA use this canonical result; see [independent QA](FINAL_QA.md) for the install and notebook runtime limits.

This experiment uses current vendor-adjusted price history and CFTC archives, not captured historical vintages. The conservative API metadata policy does not eliminate all vintage or execution uncertainty. Current data gaps, source revisions, the single holdout and correlated five-session labels limit generalization. Results do not establish future profitability or justify further tuning on this holdout.
