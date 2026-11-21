# Feature dictionary

[Русская версия](FEATURE_DICTIONARY.ru.md).

This is a code and configuration inventory, not evidence that the listed observations were retrieved or that a real combined dataset was produced. Model inputs are the eleven base columns plus enabled `*_return_5` columns in `config/config.yml`; the default set has 19 numeric inputs. Only rows with a confirmed, timely COT release are retained. Signal time is the actual NYSE close; cross-market bars are joined only after their close (or the completed UTC day for crypto), with a four-day maximum age. Historical vendor adjustments are retrospective and are a point-in-time limitation.

## Source → availability → transformed feature → model role

| Source / raw fields | Available when | Transformed feature | Role in model |
|---|---|---|---|
| GLD or SLV adjusted close | At that ETF session's NYSE close | `return_1`, `return_5`, `return_20`; rolling sample standard deviation of `return_1` over 5/20 sessions (`volatility_5`, `volatility_20`); adjusted close relative to 20-session mean minus one (`price_to_ma_20`) | Numeric predictors; ticker is a separate categorical predictor. Computed from each target's own price history. |
| GLD or SLV raw volume | At that ETF session's close | `volume_change_5`: five-session percentage change | Numeric predictor. |
| CFTC COT positions: managed long/short, producer long/short, open interest | At manifest `available_at`, only when release evidence is confirmed; backward as-of join, max age 7 days | `cot_managed_net` and `cot_producer_net`: net positions divided by open interest; `cot_managed_change`: difference from the preceding evidenced report; `cot_age_days`: age of joined report at signal | Four numeric predictors. Gaps between evidenced reports vary widely, so `cot_managed_change` is not necessarily a weekly change. COT rows without confirmed/timely publication availability are excluded. |
| BTC/USDT, SOL/USDT, ETH/USDT, ZEC/USDT Binance daily bars | After the UTC daily bar ends (next UTC midnight); as-of join max age 4 days | `{btc,sol,eth,zec}_return_5`: five-bar adjusted-close percentage change | Optional numeric cross-market predictors. USDT is treated as USD-equivalent. |
| NVDA, S&P 500 (`^GSPC`), Nasdaq (`^IXIC`), Dow (`^DJI`) Yahoo daily bars | At the source market's session close; as-of join max age 4 days | `{nvda,sp500,nasdaq,dow}_return_5`: five-bar adjusted-close percentage change | Optional numeric cross-market predictors. |
| Target ETF adjusted opens, future sessions | Entry: next ETF session open. Exit: open after five held sessions (six sessions after signal) | `target`: exit adjusted open / entry adjusted open − 1 | Label only; excluded from model inputs and used for training/evaluation. |
| Target ETF ticker | Known from configured target universe | `ticker` (`GLD` or `SLV`) | Categorical predictor, one-hot encoded by the model pipeline. |

The default numeric feature list is defined by `numeric_features()` in `src/capstone/features.py` and has 19 columns: 11 base inputs and eight enabled cross-market returns. Disabling a market map entry removes its download and its model input. Missing optional series produce missing values rather than fabricated observations.

## Five genuinely derived features

These are calculations from source observations, not raw source columns. They are implemented in `src/capstone/features.py`; their empirical usefulness and complete real-data coverage have not been established.

| Derived feature | Formula / transformation | Timing and caveat |
|---|---|---|
| `return_5` | `adj_close[t] / adj_close[t-5] - 1` | Available at ETF close `t`; retrospective vendor adjustment caveat applies. |
| `volatility_20` | Rolling 20-session sample standard deviation of one-session adjusted-close returns | Uses current and prior completed ETF sessions only. |
| `price_to_ma_20` | `adj_close[t] / mean(adj_close[t-19:t]) - 1` | Uses current and prior completed ETF closes. |
| `cot_managed_net` | `(managed_long - managed_short) / open_interest` | Only after confirmed public release; not at COT observation date by default. |
| `btc_return_5` | `BTC adjusted close[t] / BTC adjusted close[t-5] - 1` | Only after the final UTC daily candle in the change is complete; optional source. |

These five are representative and not an exclusive count: other return horizons, rolling volatility, volume change, producer net, managed-net change between confirmed rows, COT age, and the other configured-market returns are also derived or time-alignment features. Since confirmed COT rows are sparse, managed-net change may span months and is not consistently a one-week delta. `ticker` is an identifier/categorical input rather than a market transformation.

## Lecture feature/source mapping

Mapping checked against the [official course syllabus](https://github.com/DataTalksClub/stock-markets-analytics-zoomcamp) and its module outlines on 2026-11-21. This maps project components to course topics; it does not claim that GLD/SLV or COT were course-provided datasets.

| Course-style component | Project mapping | Evidence / status |
|---|---|---|
| Module 1: Introduction and Data Sources | Yahoo Finance prices for ETFs/equities/indices; CFTC COT; Binance Spot crypto bars | Course topic covers Finance APIs and source selection. Snapshot files exist and passed hash checks, but complete point-in-time usable coverage is not established. |
| Module 2: Working with the Data (in Pandas) | OHLCV cleanup, date alignment, categorical `ticker`, returns, volatility, price-to-average, volume change, COT net/changes, cross-market returns, target and merged table | The syllabus covers Pandas, dummy variables, feature generation, predictive targets, cleaning, joins, descriptive statistics and correlations. `build_features` produced a limited real-snapshot table (see [EDA evidence](EDA_FINDINGS.md)); the sample is insufficient for research conclusions. |
| Module 3: Analytical Modeling | Ridge, DecisionTree and RandomForest candidates; continuous five-session return target; validation selection | Course topics include heuristics, time-series prediction, regression and binary classification. This project's current target is regression, not calibrated probability classes. Real model results remain unverified. |
| Module 4: Trading Strategy and Simulation | Threshold-based signals, costs, capital-aware and fixed-notional simulations | Course topic covers fees, risk management, entry timing and strategy simulation. Implemented code paths exist; real-data strategy results remain unverified. |
| Module 5: Deployment and Automation | CLI, notebook, Make commands and offline snapshot replay | Course topic covers automation/deployment. Full real-data notebook-to-report run remains unverified. |

FRED features are not included: a defensible historical vintage and release-time join have not been established. The preliminary [EDA](EDA_FINDINGS.md) includes full local market history and a separate 62-row table admitted by nine confirmed COT dates. The COT table remains too sparse for claims about feature usefulness or predictive value.

## Reproduction pointers

- Sources and ticker/provider mapping: [`config/config.yml`](../config/config.yml)
- Freshness, horizon and model settings: [`config/settings.yml`](../config/settings.yml)
- Formulas, availability joins and input list: [`features.py`](../src/capstone/features.py)
- COT publication evidence and limitations: [`COT_RELEASE_EVIDENCE.md`](COT_RELEASE_EVIDENCE.md)
- Course criteria status: [`COURSE_CRITERIA_STATUS.md`](COURSE_CRITERIA_STATUS.md)
