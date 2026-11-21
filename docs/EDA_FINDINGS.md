# Market EDA and interim holdout evidence

[Русская версия](EDA_FINDINGS.ru.md).

**Status: historical EDA and interim diagnostics, with a full-COT model comparison added below.** The [full experiment report](FULL_RUN.md) describes current results and availability limits. Nine-date restrictions below describe the earlier project stage. Checked on 2026-11-21 using local snapshots under ignored `data/`. The standard offline loader validated the configured cache while building features; no snapshot was refreshed in that run. The bounded live-provider smoke passed on this date, but a separate online feature refresh failed DNS for `guce.yahoo.com`.

## Market snapshot coverage

All ten configured market CSVs have unique dates, no missing `Close`/`Adj Close` or volume values, and matching SHA-256 sidecars. GLD, SLV, NVDA and the three indices each contain 2,235 daily rows from 2018-01-02 through 2026-11-20. BTC and ETH contain 3,247 UTC daily rows from 2018-01-01 through 2026-11-21; SOL contains 2,294 rows from 2020-08-11; ZEC contains 2,803 rows from 2019-03-21. Their last UTC-day candles are subject to the loader's completed-bar cutoff.

## Full-history price diagnostics

Adjusted-close one-session returns for GLD and SLV provide 2,234 common observations. Descriptive summaries are below; these are vendor-adjusted historical returns and may reflect retrospective revisions.

| Daily return statistic | GLD | SLV |
|---|---:|---:|
| Mean | 0.048% | 0.061% |
| Standard deviation | 1.089% | 2.158% |
| Median | 0.060% | 0.071% |
| Minimum | -10.274% | -28.540% |
| Maximum | 6.359% | 9.143% |

GLD/SLV daily returns have Pearson correlation 0.790 over the common dates. Pairwise correlations with daily returns are GLD–BTC 0.140, SLV–BTC 0.186, GLD–S&P 500 0.132 and SLV–S&P 500 0.258. These align daily labels for exploration; they do not by themselves prove point-in-time availability at ETF signal time or causal/forecast relationships.

## COT-gated combined feature table

The updated nine-row release manifest admitted 62 rows (31 per ETF) from 2020-12-29 through 2023-03-28, with nine distinct COT reports. Eight rows (12.9%) lack `cot_managed_change`, because there is no preceding evidenced report for the first row in each admitted COT segment. The pooled five-held-session open-to-open target has mean 1.57%, median 1.64%, standard deviation 3.65%, minimum -10.14% and maximum 10.64%.

Pooled target correlations are `cot_managed_net` −0.531, `return_5` −0.040, `volatility_20` 0.103, `price_to_ma_20` −0.103 and `cot_producer_net` 0.217. The small number of distinct reports and repeated weekly positions make these unstable, descriptive quantities only. The report releases occurred in three sparse segments separated by large gaps; 62 table rows are not 62 independent COT observations.

Reproduce the table offline with:

```sh
./.run/venv/bin/capstone features --config config/config.yml --settings config/settings.yml --offline
```

At the earlier nine-report stage, the standard COT-inclusive `capstone run --offline` stopped at `At least 40 labeled session dates are required`: that manifest yielded only 31 distinct labeled signal dates after freshness and target-window requirements. No COT-inclusive model or test-period score was generated in that attempt; the later full run below supersedes that blocker.

## Interim market-only purged holdout

To evaluate the available long price history without pretending the sparse COT manifest was complete, [`scripts/market_only_diagnostic.py`](../scripts/market_only_diagnostic.py) runs the same five-session target, candidate models, chronological splits, purge rule and validation-only model/threshold selection using the seven ETF price features plus eight enabled cross-market returns. **It excludes every COT predictor and is not the planned COT-inclusive experiment.**

The script used 4,470 ETF rows across signal dates 2018-01-02–2026-11-20. After purging label windows, the partitions contained 2,662 train, 880 validation and 892 holdout rows. Validation began 2023-04-26; the untouched test began 2025-02-05. Validation selected `forest_3` and threshold 0.0. Holdout metrics:

| Holdout diagnostic | `forest_3` | Mean-only baseline |
|---|---:|---:|
| MAE | 3.817% | 3.839% |
| RMSE | 5.613% | 5.556% |
| Directional accuracy | 55.6% | — |

The forest has slightly lower holdout MAE but higher RMSE than the mean baseline. This single market-only comparison is not evidence that COT adds value, does not include a cost-aware strategy/backtest, and should not be read as robust performance. Adjusted-price vintage revisions and the fixed feature/model search remain limitations.

Reproduce from unchanged local snapshots with:

```sh
./.run/venv/bin/python scripts/market_only_diagnostic.py
```

It writes predictions, summary metadata and `model_comparison.csv` under ignored `artifacts/market-only-diagnostic/`.

## Full-COT validation candidate comparison

This table describes the canonical current-code frozen experiment, repeated in `artifacts/full-cot-current-code-20261121/` and independently reproduced in `artifacts/full-cot-model-comparison-20261121/`. It is a separate full run with COT on real frozen inputs, not the market-only diagnostic above. It used 1,130 purged training rows and 370 validation rows; retained validation signals span 2025-03-14–2026-01-29. All seven candidates were fitted on training only. No model settings, features or split boundaries were changed after viewing holdout. Two current-code calculations match all 20 declared numerical output hashes. Earlier unprovenanced root outputs selected `forest_3` on a sample beginning before public CFTC PRE coverage; they are excluded from this point-in-time experiment and the root outputs have since been refreshed. See the [full-run report](FULL_RUN.md) for the reconciliation and replay details.

The evaluation order keeps model selection and the holdout separate:

```mermaid
flowchart LR
    rows["Eligible COT-gated rows"] --> train["Train: 571 before purge"]
    train --> trainPurge["Purge 6 crossing labels"]
    trainPurge --> trainKept["Train: 565 retained"]
    trainKept --> candidates["Fit candidate models"]
    candidates --> validation["Validation: 191 before purge"]
    validation --> valPurge["Purge 6 crossing labels"]
    valPurge --> valKept["Validation: 185 retained"]
    valKept --> select["Select by validation MAE"]
    select --> refit["Refit on retained train + validation"]
    refit --> holdout["Holdout: 191 untouched signals"]
    holdout --> score["Report final metrics once"]
```

The counts are unique signal dates per ETF. Candidate selection uses validation only; holdout labels do not select a model or threshold.

| Candidate | Key parameters | Validation MAE | Validation RMSE | Selected |
|---|---|---:|---:|---|
| `mean` | training-target mean | 3.6398% | 5.8627% | Yes |
| `tree_3` | depth 3, leaf minimum 20 | 3.6436% | 5.8636% | No |
| `forest_3` | depth 3, leaf minimum 10, 80 trees | 3.6521% | 5.8663% | No |
| `forest_5` | depth 5, leaf minimum 10, 80 trees | 3.6744% | 5.8890% | No |
| `tree_5` | depth 5, leaf minimum 20 | 3.6779% | 5.8901% | No |
| `ridge_10` | alpha 10 | 3.9805% | 6.0961% | No |
| `ridge_1` | alpha 1 | 4.0596% | 6.1560% | No |

Tree/forest seeds are 42; forests use one worker. All candidates share training-fitted median imputation, fixed ticker encoding and scaling. The winner has minimum validation MAE; exact ties retain candidate order. **The mean baseline won.** Trees, forests and Ridge did not improve this criterion on this validation period.

The CSV `artifacts/full-cot-model-comparison-20261121/run-1/model_comparison.csv` records all estimator parameters as JSON, estimator class, `split=validation`, MAE/RMSE in decimal-return units (`0.01 = 1%`) and a single `selected=True`. It is sorted by MAE and excludes holdout scores. The CLI exports and prints it; the workflow notebook displays it after successful execution. Insufficient-history runs do not create a new comparison. Numerical replay requires exact CSV equality.

Repeat offline with the same audited publication bundle, choosing a fresh output name:

```sh
.run/venv/bin/python -m capstone.research --config .run/full-cot-verified-config.yml --output artifacts/full-cot-model-comparison-NEW
```

## Availability limits

The earlier nine-date manifest was insufficient. A later separate PRE audit supported 213 paired report dates under a conservative cutoff, enabling the full-COT experiment. Complete pre-launch release history remains unavailable; system-timestamp and retrospective-vintage limitations are described in the [full-run report](FULL_RUN.md). The market-only diagnostic above remains a separate historical result and does not itself measure COT's incremental value.
