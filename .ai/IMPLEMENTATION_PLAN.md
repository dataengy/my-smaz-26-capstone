# Implementation plan

This is the operational plan shared by the orchestrator and parallel workers. Requirements and acceptance scenarios live in [the capstone specification](../openspec/specs/capstone/spec.md). Update this file with dated evidence when work is verified. Status below is a starting record, not proof of completed execution.

## Objective

Build an independent, locally reproducible research project for predicting five-trading-session returns of GLD and SLV using point-in-time CFTC COT reports, prices and feasible cross-market features. Evaluate predictions and cost-aware trading against a meaningful benchmark, without claims of future profitability. The target audience is a course reviewer and a researcher comparing conditional signals to passive ETF ownership.

## Work packages and ownership

| Stage | Owner roles | Deliverables and exit criteria | Status |
|---|---|---|---|
| Governance and specifications | Orchestrator, BA, system analyst, architect | Rules, roles, shared plan, specs and evidence ledger exist; interfaces agreed | Drafted; CLI validation and independent skill tests outstanding |
| Source feasibility and ingestion | DE, system analyst | Confirm sources, rights, actual coverage, availability and errors; download or reload snapshots; no secrets or downloaded data in Git | Pending verification |
| Dataset and features | AE, DE | Point-in-time joins, calendar and availability rules, documented target and feature sets; at least five meaningful derived features | Pending verification |
| EDA | DA, BIE | Missingness, distributions, correlations, time and cross-market analysis supported by actual data | Pending verification |
| Models and evaluation | DS, MLE | Baselines and tree/forest, chronological train/validation/test, purging and validation-only selection, untouched holdout evaluation | Pending verification |
| Simulation and reporting | DS, BIE, QA | Capital-aware, cost-aware simulation and benchmark with actual metrics, error and subgroup analyses | Pending verification |
| Orchestration and reproducibility | DevOps, MLE | Pinned dependencies, stage scripts, notebook and one-command workflow, reproducible from cached data | Pending verification |
| Independent acceptance and documentation | QA, writer, BA | Tests and full real-data run recorded; English README, evidence-backed course checklist and defense demo | Pending verification |
| Agent operations | LLMOps, orchestrator | Project knowledge, scoped session-metadata audit, coverage and evidenced optimization recommendations | Pending verification |

The orchestrator assigns non-overlapping files and contracts and integrates results. Separate QA reviews final integrated behavior. Cloud, SRE, dashboard, RAG and external telemetry are optional follow-on work, not substitutes for local acceptance.

## Project layout, tooling and backlog

- Use `.run/` for the local virtual environment, caches and temporary runtime state, `data/` for downloaded and derived data, and keep both out of Git. Generated reports and model artifacts remain outside Git as well. Document paths and commands; do not require files from another project.
- Organize tests by purpose under `tests/smoke/`, `tests/unit/`, `tests/integration/` and `tests/e2e/`. Move the existing tests into the appropriate groups without changing their behavior; keep a single command that runs all applicable checks. Use deterministic fixtures for unit checks, real dependency boundaries for integration checks and a clearly identified real-data end-to-end check. Report unavailable prerequisites and skips honestly.
- Use Plotly for interactive exploration only if it improves understanding of real research outputs. Consider a local Streamlit dashboard after the core workflow works, for reviewing signals, model errors and strategy equity; the CLI and static reports remain sufficient to reproduce results. Do not add either dependency until its usefulness and a runnable implementation are established.
- Evaluate local MLflow for tracking model configuration, data snapshot identifiers, metrics and artifacts once real experiments can run. Keep its storage local and ignored by Git; do not claim it automatically measures Codex token consumption. Keep the existing local session metadata audit separate unless an integration is verified.
- Consider Dagster only if repeated scheduled runs, dependency visibility or operational recovery justify an orchestrator beyond the existing one-command CLI. A Dagster service, cloud deployment and scheduler are not prerequisites for the capstone. Record any tool rejected or deferred, the reason and the conditions for revisiting it.
- Use [the project backlog](BACKLOG.md) as the canonical record of priorities, acceptance criteria and evidence; use GitHub Issues and a GitHub Projects v2 board as the interactive work queue and progress visualization when this workspace has a configured GitHub repository and authenticated CLI. Keep `.ai/BACKLOG.md` and `.ai/BUGS.md` authoritative for project context and defect evidence; link tracker items to those records and update them alongside issue status. Do not duplicate the full backlog into tracker descriptions or claim a task complete without project evidence. GitHub is optional: until repository and auth are configured, continue using the local backlog. Prefer this existing GitHub integration over Linear, which has no project-specific setup here.

## Contracts and safeguards

- Source scope, dates, paths and ticker maps are maintained in `config/config.yml`. Research/runtime settings (freshness limits, split, model grid, thresholds, cost, capital, outputs and local session metadata root) are maintained in `config/settings.yml`; the YAML loader rejects duplicate top-level keys and validates target/required/optional ticker mappings. Keep the default start of 2018 subject to verified coverage. Runtime contracts must match the implementation and documentation.
- COT dates are eligible only with externally confirmed public release dates/times, including exceptional delays; observation date alone is insufficient. Exclude unconfirmed records and report coverage. If no verified records are available, clearly fail or report the blocked research run; do not invent dates.
- Set and document the exact timezone and timestamps for signal, order execution and the five-session target. Use ETF sessions, exclude unfinished crypto daily bars, and prohibit backward-filling future values. Account explicitly for adjusted prices and corporate actions.
- Choose train, validation and holdout chronologically after verifying coverage. Purge observations whose forward labels cross split boundaries. Fit transformations on training data; select models and strategy thresholds using validation only; evaluate holdout after selection.
- State allocation, capital, overlap, transaction costs and slippage; benchmark over the same period with comparable costs. Metrics require real run evidence.
- Check ETH, ZEC, SOL and market indices as optional features/analysis; put inaccessible or sample-restricting series in backlog with reasons. Add FRED only with defensible historical vintage and release availability.
- Keep data, secrets, generated models and large artifacts out of Git. Record provider terms, source URLs, retrieval timestamps, file hashes and exact reproduction commands.

## Acceptance checks

1. Inspect official course requirements in full; cite and mark each checklist item against actual evidence, including external peer-review and defense obligations.
2. Test late COT release, holiday/exception, unconfirmed publication, ETF holidays, closed crypto candles, missing records, duplicates and invalid source responses.
3. Test chronological splits and purging of forward intervals; ensure test data do not select a model or threshold.
4. Independently verify small simulation cases for entries, exits, overlapping trades, insufficient capital, fees and slippage. Check benchmark alignment.
5. Run unit checks and the end-to-end workflow with real accessible data, then rerun from the stored snapshot; report blockers or unrun steps explicitly.
6. Confirm README commands, feature dictionary, source limits, actual metrics, risks and statuses against artifacts. Never label planned work as complete.

## SDD and agent operations

OpenSpec is the selected SDD framework. The checked-in spec is a human-readable baseline; OpenSpec CLI installation and validation are not yet verified. Use specs for requirements/scenarios and this document for scheduling/status; link rather than duplicate detailed text. Apply relevant Superpowers and Ponytail skills while respecting user and system instructions. Project skill drafts live under `.ai/.codex/skills/`; automatic discovery and independent behavioral validation are unverified.

For LLMOps, begin with Markdown knowledge and verify available project-scoped session metadata and counter semantics. Report attribution coverage and unavailable counts; do not export private logs or infer cost from unverified rates. Evaluate Langfuse or MLflow only when useful and technically available.

## Evidence log

- 2026-11-20: Initial inspection found no `openspec` executable on PATH. CLI setup and validation are not established.
- 2026-11-20: Data team reported shell DNS failures and no retrieved observations at the time of inspection. Confirm again in the execution environment and record actual results.
- 2026-11-20: Code for snapshots, evidence-gated features, purged model selection, two simulation methods, a CLI and a notebook has been drafted. This is implementation status, not proof of a successful real-data run.
- 2026-11-20: Network DNS failed for CFTC, Yahoo Finance and PyPI; `uv lock` could not resolve dependencies and the OpenSpec package was not present in the npm cache. No provider observations, lockfile, or empirical metrics were produced.
- 2026-11-20: Unit checks use synthetic fixtures only. The real exchange-calendar test is skipped when its dependency is unavailable; final test counts must be recorded from the latest test invocation.
- 2026-11-20: Initial local Codex metadata audit uses CWD attribution and last reported cumulative values. Descendants outside the CWD, counter semantics, full coverage and billed cost remain unverified. Raw conversation contents are not exported.
- 2026-11-20: Latest local verification: `python3 -m pytest -q` reported 14 passed and 1 skipped; `python3 -m compileall -q src scripts` succeeded. The skipped test requires the real `exchange_calendars` dependency. `PYTHONPATH=src python3 -m capstone.cli run --offline` failed as expected because no GLD snapshot exists. These checks do not establish end-to-end reproducibility.

- 2026-11-21: Created the local prioritized backlog and linked it from the README. This records outstanding work and does not establish that blocked research or external checks have run.

- 2026-11-21: Four report/publication pairs from the 2023 disruption were added with conservative eligibility cutoffs and documented source evidence in [COT_RELEASE_EVIDENCE.md](../docs/COT_RELEASE_EVIDENCE.md). This limited sample is inadequate for the experiment.
- 2026-11-21: Local `.run/venv`, `.run/uv-cache` and `data/` directories were created; Makefile commands target the local environment. Shell DNS for PyPI and CFTC still failed, so dependencies and a lockfile are unavailable. Tests were grouped by purpose; `python3 -m pytest -q` reported 15 passed, 2 skipped. The skipped checks require a real exchange calendar and a configured real-data snapshot respectively.

- 2026-11-21: A later core dependency installation and lock resolution succeeded; `uv.lock` exists and `exchange_calendars` 4.13.3 and `yfinance` 0.2.66 import in `.run/venv`. A focused real-calendar check, including the 2024-07-03 early close, and the feature time-alignment integration fixture passed in that environment. Installing test/notebook extras subsequently failed on DNS, so the full clean installation and pytest execution in the project environment remain unverified.

- 2026-11-21: First parallel review wave fixed incomplete snapshot bars, nonfinite simulation prices and saved-estimator ticker encoding. The local session audit now excludes conflicting usage rather than fabricating a total. Independent integration verification reported `21 passed, 3 skipped` in the host environment; an early-close cutoff was separately verified in the project environment. Actual source data and real-data E2E remain blocked. See [status](STATUS.md) and [next steps](NEXT_STEPS.md).
- 2026-11-21: Fixed notebook startup from Jupyter's `notebooks/` working directory by locating the project root before loading YAML configuration. A focused check executed the setup cell from `notebooks/` and loaded config successfully; the saved full workflow then stopped at the expected missing-GLD-snapshot check. Regenerated stale `uv.lock`; `uv lock --check` resolved 135 packages, but notebook-server execution could not be verified because PyPI DNS blocked the missing `nbformat` wheel. Created the canonical [bug register](BUGS.md), its lifecycle rules, skill and agent guide; the bug-tracking skill passed `quick_validate.py`. See BUG-001 and BUG-002.
- 2026-11-21: Source and research/runtime config are centralized in the paired YAML files. `uv lock --check --offline`, source compilation and offline config smoke checks passed (GLD/SLV, 10 active sources, 19 numeric features, five-session horizon; disabling ZEC removes its download and feature); pytest and real-data behavior remain unverified for this change. Parallel sessions use object locks by default; this non-Git workspace uses `scripts/object_lock.py`, with isolated Git worktrees reserved for urgent conflicts when available.
- 2026-11-21: Added opt-in fresh-origin checkout E2E in `tests/e2e/test_origin_fresh_clone.py`, plus `make e2e-origin`, settings for workspace/timeouts and bilingual runbook instructions. A temporary local Git origin was cloned; a new environment installed the locked `test` extra with `UV_OFFLINE=1` using the shared local uv cache; smoke/unit/integration tests from the clone passed (**1 passed**). The full source checkout suite then reported **29 passed, 2 skipped** (origin and real-data E2E both require explicit configuration), with 13 existing deprecation warnings. This does not verify a published remote, clean install without a warm cache, dev/notebook extras, or the real financial workflow. The existing real-data E2E's missing `json` import was also fixed.
- 2026-11-21: Implemented the deterministic synthetic fixture backlog item: shared source-shaped OHLCV and COT generators live under `tests/fixtures/`, and unit/integration tests now reuse them. The fixtures mark their synthetic origin and require explicit COT availability timestamps. Targeted tests passed (**11 passed**); full suite passed (**32 passed, 2 skipped**, 13 deprecation warnings). No financial snapshot or empirical result was generated.

- 2026-11-21: Separated everyday human operations (`Makefile`) from supporting, multi-step and agentic recipes (`Justfile`). Added bilingual command reference, maintainership skill/agent/role, and prompt Q; removed Makefile overlap from prompts G/L. `just verify` passed tool discovery, offline lock check, compile and tests (**32 passed, 2 skipped**). No networked or real-data stage was run; details in `.ai/STATUS.md` and `docs/COMMANDS.md`.
