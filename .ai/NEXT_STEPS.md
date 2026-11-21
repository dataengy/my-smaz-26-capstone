# Next steps and execution plan

Updated: 2026-11-21. Coordinator: root session. The [backlog](BACKLOG.md) is the canonical task list; this file sequences it. Recorded evidence is in [status](STATUS.md) and the [implementation plan](IMPLEMENTATION_PLAN.md). Planned work is not verified work.

## Objective

Complete a locally reproducible, point-in-time study of five-session GLD/SLV returns with COT and market features, chronological model selection, and cost-aware simulation. Do not publish performance conclusions until real data and an untouched holdout run exist.

## Current gates

- The configured `make download` produced 10 market CSVs and 9 CFTC archives with valid SHA-256 sidecars; all archives parse, and the latest cache-aware validation accepted target rows through 2026-11-20. The manifest now has nine report-specific evidenced publication dates, but the COT-gated table has only 31 distinct signal dates. See [COT publication evidence](../docs/COT_RELEASE_EVIDENCE.md).
- The intended `.run/venv` uses Python 3.12 with yfinance 0.2.66 and Peewee 3.19.0. The CFTC 403 was traced to default `urllib` headers and fixed with a provider-accepted User-Agent; the full configured `make download` completed. Three market series still have null latest close values. The notebook workflow and full research run remain unverified.
- Latest recorded `just verify` passed **42 tests, 2 skipped, 43 warnings**; those software checks do not establish financial results. The COT-inclusive `make run` stops at its 40-labeled-date minimum. A separate market-only diagnostic has a purged holdout and is documented in [EDA findings](../docs/EDA_FINDINGS.md); it cannot assess COT's incremental value.
- Git is on `main`, synchronized with local `origin/main` at inspection; the configured remote is `https://github.com/dataengy/my-smaz-26-capstone.git`. Do not treat local tracking state as a fresh network verification. Keep object locks and preserve other sessions' changes.

## Ordered plan

### 1. Recheck source and dependency access

**Owner:** Orchestrator / data engineer. **Backlog:** P0 “Restore and verify source access.”

- First synchronize the intended Python 3.12 `.run/venv` explicitly (for example `UV_PROJECT_ENVIRONMENT=.run/venv UV_CACHE_DIR=.run/uv-cache uv sync --locked --extra dev --python 3.12`), then check DNS and HTTPS access to CFTC, Yahoo Finance and PyPI with small metadata or bounded source requests. Do not confuse the successful `.venv` dependency install with a successful data download.
- Record date, commands, response/failure, provider terms and any rate-limit information that is actually published. Do not treat web-search access as proof that runtime downloads work.
- If access works, proceed to step 2 and retrieve only required inputs with source URL, retrieval/request-start times, schema checks and SHA-256 provenance. Keep snapshots under ignored `data/`.
- If access fails, record the concrete error and leave acquisition blocked. Continue steps 3 and 4 where local dependencies permit; do not fabricate or substitute market data.

**Gate:** Valid GLD/SLV and required market snapshots are locally available with provenance, or the access blocker is freshly documented.

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

**Gate:** Clean locked setup and documented command path pass, or the unavailable prerequisite and unverified stages are clearly recorded.

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

- Use `scripts/object_lock.py` for exact shared objects before edits. The current checkout is on an unborn `main` branch with no remote; use a worktree only if Git can create a genuinely isolated worktree, otherwise queue conflicting writers.
- Keep `PARALLEL_SESSION_PROMPTS.md` claim states and object-lock ownership aligned. Release only locks acquired by the current session after handoff.
- Never commit downloaded data, secrets, environments or generated research artifacts. Never claim a test, integration, data retrieval, metric or course outcome without recorded evidence.
- Reconsider optional dashboards, MLflow/Langfuse, Dagster, CI, Docker, cloud and RAG only after a verified core run or a specific demonstrated need.

## Latest follow-up evidence — 2026-11-21

- `make test-source-smoke` passed **2 checks** across configured market sources and CFTC archives/evidence page. All 19 existing market/CFTC snapshots passed SHA-256 sidecar checks.
- Offline feature generation created a 30-row table for 2023-02-27–2023-03-17; preliminary distributions and correlations are in [EDA findings](../docs/EDA_FINDINGS.md). The four-row release manifest remains the limiting gate. A subsequent online feature refresh failed DNS for `guce.yahoo.com`; do not treat the preflight pass as proof that full downloads or refreshed data succeeded.
- The next research prerequisite remains expanding report-specific COT publication evidence and validating sufficient historical coverage. Only after that, run broad EDA and chronological purged evaluation; the 30-row descriptive sample is not a model-selection or performance result.

The follow-up above supersedes older notes in this file that referred to four COT dates, null target closes, or a 30-row feature table. Current evidence: nine supported COT dates, 62 COT-gated feature rows / 31 signal dates, full-history market EDA, and a purged market-only holdout; the COT-inclusive model and cost-aware holdout strategy remain unrun.

## Follow-up — 2026-11-21

- The official CFTC special-announcements page supports three additional actual 2023 delayed releases when paired with the stated ordinary previous-Tuesday report relationship. `config/release_dates.csv` now contains nine dates. The offline COT-gated feature table contains 62 rows and 31 distinct signal dates; the standard run refuses modeling below its configured 40-date minimum.
- Local market snapshots span 2018–2026 with valid hashes and no duplicate dates/null closes or volumes in the ten configured files. Full market EDA is recorded in [`docs/EDA_FINDINGS.md`](../docs/EDA_FINDINGS.md).
- A purged market-only holdout was run to use that broad history while excluding unsupported COT joins. It is interim evidence only; next blocker is finding enough report-specific CFTC publication evidence to evaluate COT-inclusive features on train/validation/holdout. The CFTC states a complete historical release-date list is not available.
