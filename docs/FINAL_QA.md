[EN](FINAL_QA.md) | [RU](FINAL_QA.ru.md)

# Independent final QA

**Review date:** 2026-11-21. This is a bounded independent audit of the current integrated checkout and recorded real-data bundles. It does not replace course review or legal advice.

## Result

The experiment-scale data gate is no longer blocked: the frozen CFTC audit supports 213 complete paired report dates from 2022-10-25 through 2026-11-17 under the documented conservative cutoff, with exact agreement to verified annual archives. Provenance is resolved: `artifacts/full-cot-current-code-20261121/` and `artifacts/full-cot-model-comparison-20261121/` use the same modeling/research code hashes and select mean (validation MAE 0.036398; `forest_3` MAE 0.036521). A fresh current-code freeze ran twice and matched all 20 numerical outputs; it fingerprints 60 inputs. Earlier root-only outputs selected `forest_3` but had no frozen code/config/input evidence and included 1,964 feature rows starting 2020-12-29, before PRE's 2022-10-20 public launch; they are excluded from the eligible experiment. Root generated outputs are now synchronized with the current bundle. The bilingual full-run report identifies mean as the canonical result.

The offline notebook workflow reports signals for 2026-11-20. The current frozen result retains 565/185/191 purged train/validation/test dates per ETF; validation selects mean. This is a reproducibility observation, not evidence of future performance.

An earlier clean-development install passed in `/private/tmp/capstone-qa-venv` using the project uv cache and installed 129 packages from the lock state at that time. A newer clean venv attempt with the current 216-package lock failed while building the local project: build isolation could not resolve `setuptools>=75` from PyPI because DNS failed. A completely cold uv cache also previously failed to fetch CPython from GitHub. Offline clean installation is therefore unverified; the prior cache-backed result applies to the older lock state.

Notebook setup and offline workflow cells were previously executed directly through IPython from `notebooks/`; `nbconvert --to script` also completed. A full `nbclient` attempt on a temporary copy that skipped the optional network-refresh cell was denied before any cell ran because the sandbox could not bind a localhost port. This is an environment restriction. The checked-in saved output must be refreshed from the canonical mean result before a defense; do not run the refresh cell during an offline demo.

## Provider terms and limits

- **Yahoo Finance / yfinance:** Current [yfinance documentation](https://ranaroussi.github.io/yfinance/) says the library is unaffiliated with Yahoo, intended for research/education, and points users to [Yahoo's terms](https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html); it also says Yahoo's API is intended for personal use. This does not establish project redistribution or commercial rights. Numeric request quotas, SLA and a stable public rate limit were not verified. Keep downloaded Yahoo snapshots local; obtain the provider's applicable permission before redistribution or broader use.
- **Binance Spot:** Official [REST docs](https://developers.binance.com/en/docs/products/spot/rest-api) describe per-route weights, IP-level request-weight limits, required backoff on HTTP 429 and possible 418 bans; current configured limits are exposed by `exchangeInfo`. They are dynamic/configured and should be read at runtime rather than treated as one universal cap. The review did not establish which Binance entity/terms govern this user's location or a data redistribution license; see [Spot API terms](https://developers.binance.com/en/docs/products/spot/PROD-TERMS-OF-USE). Current code uses unauthenticated public klines with bounded pagination but does not implement explicit 429/Retry-After backoff or quota-header accounting.
- **CFTC:** The [CFTC COT FAQ](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm) says tokens are not currently provided and API users generally succeed without one so long as they do not overuse the API; it gives no numeric quota. A separate [CFTC FTP submission agreement](https://accountcreation.cftc.gov/TermsOfUseAgreement.aspx) says government information on the CFTC website is public domain and may be copied with acknowledgement, but the agreement is scoped to the submission portal and should not be generalized to every PRE/API use without checking current terms. Preserve attribution and distinguish row timestamps from original static-report publication times.
- **FRED:** Not used; vintage/release-time eligibility was not established.

## Course gate and external actions

The official [course rubric](https://github.com/DataTalksClub/stock-markets-analytics-zoomcamp/blob/main/projects/README.md) lists six bold minimum-score items, an individual presentation and three peer evaluations for project points. The currently checked page states attempt-one deadline 2026-11-20 23:59:59 Dublin time; it has elapsed. This workspace has no evidence of submission, a later attempt, an actual presentation or three completed peer reviews. These cannot be closed by code changes. Obtain current attempt/submission instructions from course staff or the official course channel, upload only if an eligible route exists, then record the presentation and review identifiers privately without exposing personal information.

The bilingual criteria summary records six minimum gates as partial (course-level results verified: 0), and the overall matrix records 20 partial / 16 open / 0 verified. The README, EDA and course matrix are being reconciled in parallel against the canonical mean result; check their final state before presenting. The feature dictionary describes five representative derived features, while the rubric asks for 20+; don't count raw source fields as new features. Other rubric items—over one million records, calibrated high-probability rules, incremental transformation, novel strategy, bonus deployment and reviewer credit—remain open or partial.

## Checks performed

- Current integrated test suite: `make test` — **72 passed, 4 skipped** in Python 3.12; skips are fresh-origin, opt-in real-data, and two live-source checks.
- Isolated dev install from warm project cache: **129 packages installed** from the lockfile.
- Isolated no-cache dev install: failed before installation because DNS could not resolve GitHub's CPython standalone download.
- Notebook setup/offline workflow cells: both executed without errors from the notebook directory, used current local snapshots, emitted model-comparison rows and latest signals. The final cell reads `model_comparison.csv` from the configured output directory, which matches the CLI output contract.
- Current-code frozen experiment: **20/20 numerical output hashes matched** across two runs; 60 input files fingerprinted; validation selected `mean` (MAE 0.036398; `forest_3` MAE 0.036521). All 23 root outputs now hash-match its run-1 files.
- Full notebook-kernel execution: not verified because the sandbox denied local socket binding. `make run-notebook` GUI/browser startup was not launched.
- Provider legal/limit review: official documentation checked; rights for reuse/redistribution and blanket numeric quotas remain unconfirmed as detailed above.
- `git diff --check` passed at review time; no files were committed or pushed.

## Follow-up before presenting

1. Finish the in-progress README, EDA and course-matrix reconciliation, then regenerate the checked-in notebook outputs from the canonical bundle.
2. Refresh the criterion matrix, `docs/COURSE_CRITERIA_STATUS.*`, README mirrors, status and defense slides from that canonical result; explicitly list remaining rubric gaps.
3. Confirm course attempt/submission availability, schedule the presentation, and complete three peer reviews if still eligible.
4. Confirm current applicable Yahoo and Binance terms for your jurisdiction and purpose before sharing raw data; preserve the existing local-only snapshot policy until resolved.
5. Rerun the notebook with a local Jupyter kernel outside this restricted sandbox, clear stale outputs, and preserve a clean replay output only if it contains no secrets or personal data.
6. Repeat `uv sync --locked --extra dev --python 3.12` from a truly clean cache when package network access is available; record success or exact blocker.
