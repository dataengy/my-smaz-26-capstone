# Parallel session prompts

Copy a prompt below for a single session. These are scoped work packages, not a request to launch every role at once. `.ai/NEXT_STEPS.md` and `.ai/BACKLOG.md` determine which packages are currently actionable. The orchestrator owns integration and status updates. A prompt is unclaimed unless it appears in the claim table below. Update the table when work is claimed, completed or blocked; completed entries should link to verification evidence.

## Prompt claim status

| Prompt | Status | Owner/session | Started | Handoff/evidence |
|---|---|---|---|---|
| C — Data engineer: acquisition and COT snapshots | **In progress** | Session (`УНИКАЛЬНЫЙ_SESSION_ID-1`) | 2026-11-21 | Claim recorded by `just take-next-prompt`; handoff pending |
| A — System analyst: source and timing contract | **Completed** | Session (`codex-next-20261121`) | 2026-11-21 | Updated [COT source and timing evidence](../docs/COT_RELEASE_EVIDENCE.md) and its [Russian mirror](../docs/COT_RELEASE_EVIDENCE.ru.md), plus a named source/timing contract in the [spec](../openspec/specs/capstone/spec.md#source-and-timing-contract-reviewed-2026-11-21). Official CFTC, NYSE and yfinance docs reviewed; no market data downloaded and no release manifest rows added. `git diff --check` produced no whitespace errors; no tests were applicable to this documentation/spec review. |
| B — YAML configuration contract | **Completed** | Orchestrator (`codex-config-implementation-2026-11-21`) | 2026-11-21 | [Config acceptance evidence](STATUS.md#current-execution-wave); full real-data run remains separately blocked on snapshots |

## Shared coordination contract

All sessions first read `AGENTS.md`, `.ai/RULES.md`, `.ai/roles/ROLES.md`, the relevant OpenSpec requirements, and `.ai/.codex/skills/parallel-session-coordination/SKILL.md`. Check other sessions before edits. In this non-Git shared workspace, acquire the named object lock before writing:

```sh
python3 scripts/object_lock.py acquire <LOCK_SLUG> --session-id <UNIQUE_SESSION_ID> --reason "<short task>"
```

If held, do not edit the owned files; report the owner and wait or use an isolated Git worktree only for critical work that cannot wait, when Git is available. Never break a lock based on age alone. Hold the lock across edits and verification; release your own lock after the handoff:

```sh
python3 scripts/object_lock.py release <LOCK_SLUG> --session-id <UNIQUE_SESSION_ID>
```

The global `agent-session-lock` skill is preferred when its Git-backed helper applies. Global Superpowers `dispatching-parallel-agents` and `using-git-worktrees` guide independent task selection and worktree setup. A worktree is isolated: do not also edit the same objects in the shared checkout. Do not edit shared instructions, status, backlog, changelog, or config unless your prompt owns them. Report exact files, commands and actual outcomes, skipped/unrun checks, assumptions, interface changes and remaining risks. Never create fake market data, results, token counts, test evidence, or profitability claims.

## Recommended execution waves

| Wave | Parallel packages | Gate before next wave |
|---|---|---|
| 0. Contracts | A system/data contract; B configuration and architecture review | Orchestrator records accepted schemas, timing and settings keys |
| 1a. Independent core | C ingestion/COT; E model evaluation; F simulation | Interfaces in Wave 0 are stable; disjoint ownership confirmed |
| 1b. Integration | D feature engineering; G local workflow; one of H QA or I EDA | Ingestion/model/simulation contracts are handed off; keep to three workers maximum |
| 2. Evidence | H independent QA; I EDA and error analysis when real data exist; J session accounting | Data/snapshots are available where required |
| 3. Defense | K documentation and course checklist; orchestrator integration | Actual execution evidence exists; docs describe observed behavior |
| 4. Optional | L visualization; M Dagster/MLflow/cloud feasibility | Core local workflow passes and a concrete use case is established |

At most three workers run concurrently with the orchestrator, as recorded in the implementation plan. Combine compatible roles instead of opening more sessions. If a package depends on a not-yet-approved contract, do read-only analysis and hand off recommendations without editing the dependent files.

## A — System analyst: source and timing contract

> **Outcome:** Produce an evidence-based contract for source fields, COT publication availability, market bar timestamps, optional assets and failure behavior.
>
> **Own/lock:** Read-only research initially. If the orchestrator approves implementation, own only `docs/COT_RELEASE_EVIDENCE.md`, its Russian mirror, and a clearly named spec sub-section; lock `cot-evidence-docs`. Do not edit source code, YAML configs, other docs, backlog or status.
>
> **Work:** Read the official CFTC source pages and current provider docs; identify format/rights/rate limits, report identity and relevant known publication evidence. State exactly which timestamps are confirmed and which remain unknown. Use exchange/calendar evidence for signal and market availability. Distinguish report date, public release, retrieval and signal cutoff. Do not infer ordinary release timestamps from a weekday schedule. Report optional series coverage only if it can be verified without fabricating/downloaded examples.
>
> **Handoff:** Source links, field contract, explicit confidence/coverage gaps, proposed scenarios, changed files (if authorized), and checks actually performed. Do not report a data download unless one completed.

## B — Architect and DevOps: YAML configuration contract

> **Outcome:** Keep configuration discoverable and remove behavior settings from code only when doing so improves clarity and reproducibility.
>
> **Own/lock:** `config/config.yml`, `config/settings.yml`, `src/capstone/config.py`, `pyproject.toml`, `uv.lock`, `Makefile`; lock `project-configuration`. Coordinate before touching consumers or tests.
>
> **Work:** Preserve the division: source scope/paths/universe in `config/config.yml`; analysis, feature freshness, split, model/trading, output and local tooling options in `config/settings.yml`. Inspect every consumer and document precedence/types/defaults. Keep secrets out. Make optional-market removal coherent across download and feature selection. Update the dependency lock only if necessary and report whether it succeeded.
>
> **Off limits:** `src/capstone/data.py`, `features.py`, `modeling.py`, `backtest.py`, `cli.py`, `scripts/codex_usage.py`, tests and human docs without an explicit coordinated interface request.
>
> **Handoff:** Key inventory, validation/default rules, changed files, lockfile status, consumers that must migrate, and checks actually performed. Release `project-configuration` only after handoff.

## C — Data engineer: acquisition and COT snapshots

> **Outcome:** Make source ingestion, caching, manifests and replay honest and reproducible.
>
> **Own/lock:** `src/capstone/data.py`, `tests/unit/test_data.py`, `tests/e2e/test_real_data.py`; lock `data-ingestion`. If another owner has `config/config.yml`, use its approved config contract without editing it.
>
> **Work:** Verify public provider fields, supported archive formats, checksums, missing/duplicate behavior, freshness, request-start cutoff, historical coverage, rights/limits and offline replay. For COT, use only independently substantiated availability evidence and exclude unconfirmed reports. Ensure optional series failure cannot silently reduce or alter required target scope. Never commit downloaded snapshots or secrets.
>
> **Off limits:** Feature, modeling, simulation, CLI, lock files, README and shared governance artifacts.
>
> **Handoff:** Source URLs/terms, actual retrieval evidence or exact blocker, schemas and limitations, files changed, focused checks/results/skips, and unresolved availability questions. Do not invent normal-week COT timestamps.

## D — Analytics engineer: point-in-time features

> **Outcome:** Build the documented unified ETF-session table and meaningful leakage-safe features from accepted source contracts.
>
> **Own/lock:** `src/capstone/features.py`, `tests/integration/test_features_calendar.py`, `tests/unit/test_data.py` only when pre-agreed with the ingestion owner; otherwise do not touch the shared unit file. Lock `feature-engineering` (or use a single agreed joint owner for shared tests).
>
> **Work:** Keep GLD/SLV as targets, others as predictors. Verify NYSE close and early-close signal time, next-open entry and five-session label, completed crypto bars, COT `available_at`, stale cutoff, missing bars, duplicates and absent optional features. Make feature names derive from the agreed config map. Exclude label/execution fields from predictor lists. Add only meaningful features backed by available data and document lineage.
>
> **Off limits:** `data.py`, model/backtest code, YAML config and docs unless a contract owner approves a coordinated interface change.
>
> **Handoff:** Row grain, timing assumptions, feature list, missingness policy, edited paths and actual validation evidence. Clearly state that synthetic fixtures do not prove provider availability.

## E — Data scientist: models and chronological evaluation

> **Outcome:** Compare a simple baseline with Ridge/tree/forest candidates using chronological, horizon-purged splits and validation-only selection.
>
> **Own/lock:** `src/capstone/modeling.py`, `tests/unit/test_modeling.py`; lock `model-evaluation`.
>
> **Work:** Check partition boundaries against target exit intervals, learned preprocessing, minimum sample requirements, deterministic settings, model selection, threshold selection and frozen holdout scoring. Honor configured targets and dynamic feature lists. Test perturbing holdout labels does not alter selection. Do not tune on test results or present synthetic tests as empirical conclusions.
>
> **Off limits:** data/features, backtests, config files, docs, status and backlog.
>
> **Handoff:** Split formulas and dates from fixtures or real run, selected model logic, tests actually run and their evidence, limitations, and artifact interface.

## F — Financial validation: event and vector simulations

> **Outcome:** Verify capital, event order, overlapping trades, fees/slippage, reinvestment and benchmark comparability.
>
> **Own/lock:** `src/capstone/backtest.py`, `tests/unit/test_backtest.py`; lock `trading-simulation`.
>
> **Work:** Independently calculate small cases for entry/exit timing and both-side costs. Ensure predictions are holdout-only, target tickers align with config, cash never goes negative, unavailable prices fail, benchmark shares the same period and fee policy, and the vector approximation is labeled accurately. Keep CAGRs/Sharpes out of documentation until produced by an actual run.
>
> **Off limits:** data, features, modeling, CLI, config, docs and status.
>
> **Handoff:** Assumptions, equations, independent case calculations, edited paths, actual test results and unresolved risks.

## G — ML engineer: CLI and notebook workflow

> **Outcome:** One reproducible local command consumes approved YAML, verified snapshots, features, selected model, simulation and latest-signal report.
>
> **Own/lock:** `src/capstone/cli.py`, `notebooks/workflow.ipynb`; lock `workflow-orchestration`. Treat `config.py` and YAML as interfaces owned by package B. Use the existing Makefile/Justfile contract; do not edit either command catalog. Agree with package E on feature list and package F on output schema first.
>
> **Work:** Make CLI defaults and notebook use `config/config.yml` plus `config/settings.yml`. Ensure offline mode actually avoids network calls, output paths are configurable, failures are actionable, all generated artifacts stay ignored, and the final report shows signal/model training cutoffs. Preserve independent stages.
>
> **Off limits:** source/feature/model/backtest implementations, YAML files, docs/governance unless owners approve exact shared edits.
>
> **Handoff:** Commands, artifact schema, behavior changed, exact checks executed and blockers. Do not say full workflow succeeded without real data.

## H — QA engineer: independent acceptance review

> **Outcome:** Review integrated acceptance and identify the highest-risk defects without taking over implementation ownership.
>
> **Own/lock:** Initially read-only; if writing, own `tests/smoke/`, `tests/integration/` only after checking the existing test owners and lock `acceptance-tests`. Never edit production code or change pass/fail claims in README/status.
>
> **Work:** Map OpenSpec requirements to evidence. Review COT release eligibility, holiday and crypto cutoff, duplicated/missing rows, horizon purging, validation/test isolation, capital/cost accounting, offline reproducibility, ignored data/secrets and language links. Run only checks available and authorized by the task. Separate fixture tests, dependency checks and real-data runs.
>
> **Handoff:** Findings ordered by severity with exact paths, exact commands/outcomes, untested areas and acceptance status. No test result inferred from source inspection.

## I — Data analyst and BI engineer: EDA and error analysis

> **Outcome:** Produce reproducible, correctly labeled EDA and subgroup/error analysis from actual snapshots and run artifacts.
>
> **Own/lock:** A new `src/capstone/eda.py` and `tests/unit/test_eda.py` only after orchestrator approves that split; otherwise provide a read-only analysis proposal. Lock `eda-reporting`. Generated numeric results belong in ignored `artifacts/`, never hand-authored docs.
>
> **Work:** Show distributions, missingness, correlations, time patterns, cross-market relationships and model errors by ticker/period or regime. Label the date range, row count, target and data hashes. Avoid causal language and don't treat full-sample correlations as model selection. If no real snapshots exist, report the EDA as blocked and implement only reusable code without example claims.
>
> **Off limits:** provider acquisition, features/model/backtest changes, docs claims and status edits.
>
> **Handoff:** Code/artifact paths, dataset provenance, actual findings or explicit blocker, checks and caveats.

## J — LLMOps: local session accounting and project knowledge

> **Outcome:** Improve project-scoped session coverage and efficiency analysis while protecting private logs.
>
> **Own/lock:** `scripts/codex_usage.py`, `tests/unit/test_usage.py`, `.ai/SESSION_ACCOUNTING.md`, `.ai/memory/PROJECT_MEMORY.md`; lock `llmops-session-audit`.
>
> **Work:** Read global `agent-session-lock` and session-sync guidance as relevant, but do not edit global skills. Inspect actual metadata schema, project CWD attribution, parents, duplicate/conflicting counters and coverage. Never export raw messages, external projects, secrets, or estimate costs with unverified rates. Keep Markdown as the project knowledge base; assess MLflow/Langfuse/RAG only against a concrete capability need and actual local availability.
>
> **Off limits:** all market pipeline/model/docs and global Codex settings/skills.
>
> **Handoff:** Coverage boundaries, actual fields and semantics, conflicts, verified sums or `unknown`, privacy boundary, evidence-backed optimization ideas and updated `.ai/` artifacts.

## K — Documentation writer: implementation and defense docs

> **Outcome:** Explain only the behavior and results supported by code and run evidence, with synchronized English and Russian human docs.
>
> **Own/lock:** `README.md`, `docs/` and matching `.ru.` mirrors; lock `human-docs`. Consult implementers and QA before stating contracts or results.
>
> **Work:** Follow the existing light Diátaxis organization. Document configuration files and exact commands, field/feature definitions, timing, data conditions, model split, simulation costs, actual metrics (only from artifacts), course checklist, limitations and defense demonstration. Use reciprocal language-switch links. Agentic plans and prompts remain in `.ai/`; link them rather than duplicating them.
>
> **Off limits:** code, config values, backlog/status/plan, specs and tests. If behavior is unclear, mark it unresolved and ask the orchestrator/owner in the handoff; don't infer it.
>
> **Handoff:** Docs changed, source-of-truth paths consulted, local links/mirrors checked if run, and unsupported claims removed or flagged.

## L — DevOps: clean local setup and reproducibility

> **Outcome:** Make the documented local setup reproducible and failures understandable.
>
> **Own/lock:** `pyproject.toml`, `uv.lock`, `.gitignore`, `scripts/doctor/` only if that path is approved; lock `local-devops`. Do not edit `Makefile` or `Justfile`; request an interface change from the build-interface maintainer and coordinate with configuration/workflow owners before editing overlaps.
>
> **Work:** Verify lock/sync and CLI stages where dependencies/network permit, use `.run/`, confirm caches/data/artifacts are ignored, no secret is embedded, and source snapshots are reproducible offline. Keep Docker, Dagster, cloud, Streamlit, Plotly and hosted telemetry deferred unless the core path works and a specific need is proven.
>
> **Off limits:** statistical or financial logic, config semantics, docs, global skills and external deployment.
>
> **Handoff:** Environment versions, commands/results, network constraints, exact dependency changes and deferred infrastructure rationale.

## M — Optional visualization / orchestration feasibility

> **Outcome:** Recommend only whether Plotly/Streamlit, Dagster or MLflow improves an already-working local research workflow.
>
> **Own/lock:** Read-only analysis. Do not add dependencies or services; if the orchestrator approves a prototype, take a new exclusive scope and lock before edits.
>
> **Work:** Use actual project outputs to identify a specific user problem, compare the simplest local alternative, estimate operational burden from available evidence, and define acceptance for a small prototype. No dashboards, deployments, scheduled runs, external tracking or fabricated screenshots/results without explicit approved scope.
>
> **Handoff:** Recommendation, evidence, prerequisites, estimated complexity with assumptions and backlog-ready acceptance criteria.

## N — Business analyst: course acceptance and defense readiness

> **Outcome:** Turn official course criteria and the intended reviewer/user needs into a truthful, evidence-linked acceptance matrix.
>
> **Own/lock:** `.ai/BACKLOG.md` and a proposed acceptance section in `openspec/specs/capstone/spec.md`; lock `course-acceptance`. Do not update human-facing README or `.ai/STATUS.md` without coordinating with their owners.
>
> **Work:** Re-read the official course criteria and current spec. Map each mandatory/bonus point to an existing artifact, observed result and missing evidence. Separate code presence from completion, note peer-review/defense tasks, and prioritize blockers. Avoid duplicate backlogs or changing technical behavior requirements without architect/QA agreement.
>
> **Off limits:** source/model/financial code, config, human docs, test execution evidence.
>
> **Handoff:** Criterion-to-evidence table, prioritized backlog edits, exact sources consulted and unresolved interpretations. Do not mark criteria complete from plans or source files alone.

## O — MLOps: experiment and artifact tracking feasibility

> **Outcome:** Assess experiment lineage requirements and whether local MLflow adds value after real data runs exist.
>
> **Own/lock:** Read-only review of artifacts and dependencies; if approved, own a new tracking module and its isolated tests under an agreed interface, lock `experiment-tracking`. Do not edit existing modeling/CLI/docs in this feasibility task.
>
> **Work:** Define the minimum lineage fields (config, snapshot hashes, dates, split, model and actual metrics), persistence and privacy needs. Verify MLflow availability and local-only behavior before proposing adoption. Distinguish ML experiment tracking from Codex token tracking; do not fabricate runs or install services for a checklist.
>
> **Handoff:** Evidence-based recommendation, integration boundary, setup burden, security/local storage assumptions and backlog-ready acceptance criteria.

## P — Cloud engineer and SRE: deployment/readiness review

> **Outcome:** Decide whether the capstone needs deployment, scheduling, monitoring or recovery beyond a local reproducible run.
>
> **Own/lock:** Read-only. If the core system and an authorized use case later justify a prototype, take a newly approved non-overlapping scope and lock before changes. Do not access accounts, deploy or add credentials during this review.
>
> **Work:** Review actual workload, source update cadence, failure modes, secrets, data persistence and user need. Compare local execution with Docker/Dagster/cloud options and name concrete costs/risks only when evidence is available. Draft a runbook or backlog acceptance proposal, not an unperformed service.
>
> **Handoff:** Decision, prerequisites, operational risks and evidence, service boundaries, and explicit criteria for reopening the deferred item. Do not claim an SLO or deployment.

## Q — Build tooling maintainer: human and agent command interface

> **Outcome:** Keep common local operations easy for people to discover in Make, while reusable multi-step and agentic operations live in Just.
>
> **Own/lock:** `Makefile`, `Justfile`/`justfile`, `.ai/.codex/skills/build-command-interface/SKILL.md`, `.ai/agents/build-tooling-maintainer.md`; lock `build-interface`. The orchestrator must explicitly assign any shared docs, rules, roles, plan, status, backlog or prompt-catalog edits before touching them.
>
> **Work:** Read `AGENTS.md`, `.ai/RULES.md`, the build-command-interface skill and the existing CI/hook contract. Keep common Make targets simple and useful without Just where practical. Put parameterized, multi-step, reusable and agent/session recipes in Just; delegate shared complex behavior instead of duplicating it. Preserve `Justfile` and lowercase `justfile` equivalence. Document networked and opt-in operations, keep data/secrets out of Git, and validate both command catalogs.
>
> **Off limits:** Data/model/trading logic, unrelated scripts, config semantics, global skills, optional infrastructure, deployment and unassigned shared artifacts.
>
> **Handoff:** Exact edits, `make help`, `just --list`, formatting/dry-run results, tests or workflows actually run, skips/failures, prerequisites and lock release status.
