# Next steps and execution plan

Updated: 2026-11-21. Coordinator: root session. The [backlog](BACKLOG.md) is the canonical task list; this file sequences it. Recorded evidence is in [status](STATUS.md) and the [implementation plan](IMPLEMENTATION_PLAN.md). Planned work is not verified work.

## Objective

Complete a locally reproducible, point-in-time study of five-session GLD/SLV returns with COT and market features, chronological model selection, and cost-aware simulation. Do not publish performance conclusions until real data and an untouched holdout run exist.

## Current gates

- No real market snapshots or empirical experiment are recorded. Four COT report dates from the 2023 ION disruption have conservative eligibility cutoffs; this is not enough for the intended train/validation/holdout study. See [COT publication evidence](../docs/COT_RELEASE_EVIDENCE.md).
- Earlier in-sandbox commands could not open DNS sockets (`Operation not permitted`) and `curl` reported name-resolution failure; this did not establish a device-wide DNS outage. The reusable source probe resolved all configured hosts and received HTTP 200 from GitHub, PyPI, CFTC's COT reports page, CFTC PRE's filtered Disaggregated Futures Only GOLD query (one row, report date 2026-11-17), and Yahoo's GLD five-day chart query. The targeted Stooq GLD endpoint returned an HTML JavaScript challenge rather than CSV. Alpha Vantage's landing page returned HTTP 200, but its data API was not queried without a user key. FRED returned a Python `urllib` read timeout, while `curl` returned HTTP 200 from another resolved CDN edge IP; verify the actual configured FRED client before depending on it. No market snapshot was saved. Course materials identify Yahoo Finance for daily ETF prices, FRED for macro series, and Stooq as an index reference; the rubric asks for a source beyond Yahoo/FRED for the extra source point.
- Fresh `uv sync --locked --extra dev` runs passed twice in CPython 3.13.9 using disposable environments and previously empty temporary uv caches; project, dev, Jupyter, `nbformat` imports and the XNYS session check for 2024-07-03 passed, then the temporary paths were removed. A run from inside the sandbox failed to resolve `files.pythonhosted.org`, confirming that clean setup depends on the execution boundary. This does not run tests or start the notebook server.
- The latest local suite was recorded as 34 passed and 2 opt-in E2E skipped. This is fixture/code evidence, not a financial-result claim.
- `.git` exists, `origin` is configured as `https://github.com/dataengy/my-smaz-26-capstone.git`, and this isolated worktree is on `codex/time-simulation-acceptance-2026-11-21` at `bd2454d`. User supplied `43e768f` as the previous last commit; the branch's local base includes the subsequently created `.worktrees/` ignore commit. Keep object locks and don't publish changes without a working connection.

## Ordered plan

### 1. Recheck source and dependency access

**Owner:** Orchestrator / data engineer. **Backlog:** P0 “Restore and verify source access.”

- Repeat bounded source diagnostics with `python3 scripts/check_external_access.py`; use `--only <name>` for one endpoint and never auto-retry HTTP 429. The FRED check now falls back to bounded `curl` after an `urllib` timeout and reports client-specific discrepancy separately. The sandbox may block DNS sockets even when the approved host network works. Yahoo and one-row GOLD COT HTTP requests have now succeeded; this is endpoint smoke evidence, not a saved or validated acquisition snapshot.
- The 2026 course rubric names yfinance and FRED as lecture sources and awards an extra source point for a source beyond them; its data-source README links to the notebook rather than prescribing one provider. The notebook uses yfinance for ETF daily history, FRED via `pandas_datareader` for macro series, points to Stooq for index references, and mentions Alpha Vantage in its paid-data section. See [course rubric](https://github.com/DataTalksClub/stock-markets-analytics-zoomcamp/blob/main/projects/README.md), [module README](https://github.com/DataTalksClub/stock-markets-analytics-zoomcamp/blob/main/01-intro-and-data-sources/README.md), and [2026 data-source notebook](https://github.com/DataTalksClub/stock-markets-analytics-zoomcamp/blob/main/01-intro-and-data-sources/%5B2026%5D_Module_01_Colab_Introduction_and_Data_Sources.ipynb).
- Keep CFTC as the preferred COT authority: PRE API and downloadable COT archives draw from the same source data. One filtered GOLD API record was read, but a complete archive/snapshot and report-specific publication availability still need validation. Yahoo returned a small GLD chart response. Stooq's short GLD request returned a browser challenge, so its data are not currently usable through the checked endpoint. Alpha Vantage's API requires a key not configured here. FRED's landing page is reachable via `curl` (HTTP 200) while Python `urllib` times out; this does not verify series API access or vintage suitability, and FRED remains deferred until release availability and vintages are established. Before adopting a fallback, verify GLD/SLV coverage, OHLCV schema, adjustment/dividend semantics, history, rate limits, terms and point-in-time suitability. A provider with a reachable homepage but unusable data endpoint is not an acceptable fallback.
- Record date, exact commands, per-host response/failure, provider terms and only published rate-limit details. Web access or a notebook run in another environment does not prove runtime access here. If a connected machine is used to export snapshots, preserve original provider files, retrieval times, URLs, checksums and terms; do not commit market data.
- If a specific endpoint remains unusable, document the concrete layer/status and assess an alternative for source fit, rights and point-in-time behavior. Continue local deterministic QA and code work. Repeat the complete clean dev installation with `python3 scripts/check_clean_install.py` when needed; the verified run used a fresh empty cache. Do not fabricate or silently substitute data.

**Gate:** Valid GLD/SLV and required market snapshots are locally available with provenance, or each provider's current access blocker and evaluated fallback are documented.

### 2. Establish enough report-specific COT availability evidence

**Owner:** System analyst / data engineer. **Backlog:** P0 “Build a verified COT release manifest.”

- Continue from the reviewed [source and timing contract](../docs/COT_RELEASE_EVIDENCE.md) and CFTC notices. Link each proposed COT row to an identified gold or silver report and a contemporaneous notice that supports its actual publication date.
- A planned schedule, weekday convention, archive observation date or later-revised archive value does not establish publication time. Use a conservative next-day UTC eligibility cutoff only when the report-specific release day is independently supported and the hour is absent.
- Do not add a manifest row unless the report/date/contract scope and evidence URL are documented. Measure the eligible date range and count only after validating the actual archived data.
- Account for CFTC schedule changes, including the announced twice-weekly transition, before applying a weekly rule to later dates.

**Gate:** Enough evidenced, correctly mapped COT history exists to support chronological splits, or the intended experiment remains explicitly blocked with the exact coverage gap.

### 3. Close local time, modeling and simulation acceptance gaps

**Owner:** QA / financial validation. **Backlog:** P1 “Complete time and simulation acceptance.”

- Independently verify early closes and holidays, late/unconfirmed COT, completed crypto bars, missing and duplicate records, purging across split boundaries, validation-only selection, overlapping trades, cash constraints, both-side costs and benchmark alignment.
- Use deterministic fixtures and independently calculated small cases. Record which tests ran in `.run/venv`; distinguish those checks from provider and real-data acceptance.
- Do not change production contracts without updating the spec and coordinating the owning module. Run the documented verification command only when dependencies are available; report skips and warnings accurately.

**Gate:** Each listed case has an independent test or calculation, and remaining untested cases are named. This work may proceed while source access is blocked.

### 4. Verify clean setup and notebook workflow

**Owner:** DevOps / ML engineer. **Backlog:** P0 “Lock and install a clean environment” and P1 “Organize runtime and tests.”

- When package access is available, install the locked development and notebook extras in a fresh local environment and verify the actual exchange calendar and notebook startup.
- Run `make verify`, inspect opt-in skips, then run the origin-clone E2E only with an explicitly configured disposable local origin. Keep generated environments, caches, data and artifacts ignored.
- If registry access remains unavailable, record exact commands and failures; do not describe a warm-cache install as a clean install.

**Gate:** Clean locked dev installation passed in a disposable environment. Remaining: run the full verification suite from that clean environment and verify notebook startup; keep origin and real-data E2E opt-in gates explicit.

### 5. Run and replay the real experiment

**Owner:** Data, analytics, modeling, QA and orchestrator. **Backlog:** P0 “Run and reproduce the full experiment.”

- Start only after steps 1 and 2 provide complete market snapshots and sufficient evidenced COT coverage. Validate timestamps, required ticker coverage, duplicates, missingness, checksums and snapshot metadata first.
- Execute acquisition/cache validation, point-in-time features, chronological purged training/validation/holdout, validation-only model and threshold selection, holdout scoring, both simulations, EDA/error analysis and the notebook/CLI workflow.
- Replay from the same unchanged local snapshots and configuration. Record snapshot hashes, date ranges, row counts, commands, actual metrics and any differences.
- If the sample is insufficient or any gate fails, stop before model/strategy claims and document the blocker.

**Gate:** Reproduction succeeds from the same snapshots, or actual failures and limitations are recorded. Only then update results and course-evidence documentation.

### 6. Complete course/defense evidence

**Owner:** Business analyst / documentation writer. **Backlog:** P1 course, reviewer and rubric-evidence items.

- Update the criterion matrix from produced artifacts and observed outcomes. Verify current submission availability with the course before planning submission; the first-attempt deadline has passed.
- Record an individual presentation or three peer reviews only after they actually occur. Keep bonus infrastructure deferred unless the working core workflow demonstrates a concrete need.

## Coordination and stop conditions

- Use `scripts/object_lock.py` for exact shared objects before edits. Preserve isolation in the current feature worktree; do not move the shared checkout or merge other sessions' uncommitted changes into this branch.
- Keep `PARALLEL_SESSION_PROMPTS.md` claim states and object-lock ownership aligned. Release only locks acquired by the current session after handoff.
- Never commit downloaded data, secrets, environments or generated research artifacts. Never claim a test, integration, data retrieval, metric or course outcome without recorded evidence.
- Reconsider optional dashboards, MLflow/Langfuse, Dagster, CI, Docker, cloud and RAG only after a verified core run or a specific demonstrated need.
