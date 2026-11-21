# Project memory

This is a repository-maintained record, not automatic persistent model memory. Update dated entries with source links and evidence; never put credentials or raw private conversations here.

## Decisions

- 2026-11-21: Project-facing documentation belongs in `docs/`; agentic plans, backlog, status and session-management artifacts belong in `.ai/`. English remains primary, with linked `.ru.` translations for main human-facing documents.
- 2026-11-21: Source scope is configured in `config/config.yml`; research/runtime settings are in `config/settings.yml`. Project-level top-key collisions fail instead of silently overriding. In shared parallel workspaces, object locks are the default; this non-Git checkout uses `scripts/object_lock.py`; Git worktrees are reserved for urgent isolated changes when available.
- 2026-11-20: The traded assets are GLD and SLV; the target is a five-trading-session forward return. Other market series are features or analysis only.
- 2026-11-20: The working project is standalone. The course checkout is reference material, not an executable dependency or submodule.
- 2026-11-20: English is the primary documentation language; supplementary Russian translations use `.ru.` filenames.
- 2026-11-20: An orchestrator coordinates explicitly scoped workers; independent QA checks integrated behavior. Roles can be combined when appropriate.
- 2026-11-20: OpenSpec is the chosen spec-driven framework; the CLI was not found on PATH during initial inspection. Specification files are a baseline, not proof of CLI validation.
- 2026-11-20: Start the knowledge base as Markdown and evaluate Langfuse, MLflow and RAG only when their actual availability and value are established.

## Evidence and open questions

- Source coverage, rights, data retrieval and historical COT publication timestamps require documented verification before any research claim.
- Project skill drafts have not been shown to be automatically discoverable or pressure-tested by independent agents. Read them by path and treat them as drafts.
- Codex session metadata may include token counts and parent links; completeness, attribution and count semantics require independent verification. Cost cannot be assumed without verified prices or billing.
- Tests, full workflow, model metrics, signals and deployment status must be recorded from actual runs, not anticipated here. See the implementation plan and README for current evidence.

## Backlog

- Assess ETH, ZEC, SOL, market indices and FRED after checking availability, timing and impact on the core sample.
- Assess optional OpenSpec CLI installation and validation, session-cost integration, Langfuse/MLflow, retrieval, CI, Docker, dashboard and cloud deployment only when justified and permitted.

- 2026-11-21: Added `make demo-synthetic` and `make test-demo-synthetic` as an offline human demonstration. It generates ignored, deterministic, fictional OHLCV/COT snapshots and exercises project feature/model/simulation code, then creates a standalone HTML report with three embedded PNG charts. `make test-demo-synthetic` passed; latest `just verify` passed **37**, skipped **2** opt-in E2E tests. Demo numbers are not empirical results. Copy-ready bilingual PPTX authoring instructions live in `docs/PRESENTATION_PROMPT.md` and `.ru.md`.

## 2026-11-20 execution evidence

- Shell DNS failed for CFTC, Yahoo Finance and PyPI. No actual data or financial experiment was obtained.
- OpenSpec CLI was absent and no cached npm package was found. The checked-in spec is unvalidated by the CLI.
- At this date `config/release_dates.csv` was empty; see the later 2026-11-21 entry for newly documented evidence.
- Source, features, models, both simulation forms, workflow and a metadata audit have code and synthetic unit tests; real provider and calendar integration remain unverified. The initial dependency lock could not be generated offline.

## 2026-11-21 execution evidence

- CFTC same-day announcements substantiate four reports in the 2023 disruption; manifest times are conservative next-day eligibility cutoffs, not measured publication timestamps. See `docs/COT_RELEASE_EVIDENCE.md`. Coverage is insufficient for the intended experiment.
- Shell DNS remains unavailable for PyPI and CFTC. An empty local `.run/venv` was created, but dependency installation and a lockfile remain blocked.
- Tests are organized under unit, integration, smoke and e2e; two checks require a real exchange calendar or actual cached data and remain skipped when unavailable.

- Later on 2026-11-21, core dependencies and `uv.lock` were obtained. A real-calendar fixture passed in `.run/venv`; test and notebook extras remain unavailable after DNS errors.
- 2026-11-21: Added deterministic source-shaped synthetic OHLCV and COT fixture factories under `tests/fixtures/`, with explicit COT availability and `.invalid` source URLs. The full test suite reported 32 passed, 2 opt-in E2E skipped; no provider data or research result was generated.
- 2026-11-21: Command interface: use `Makefile` for common human-facing operations and `Justfile` for supporting multi-step/agentic operations. Make delegates only advanced verification/listing targets to Just. Keep `Justfile`/`justfile` equivalent. Read `.ai/.codex/skills/build-command-interface/SKILL.md` before edits and claim `build-interface`. `just verify` passed with 32 passed/2 opt-in E2E skipped; setup/network-dependent paths were not executed.
- 2026-11-21: Follow-up acceptance added a hand-computed event-order regression for exits funding same-session rebuys. Focused backtest tests passed (7); full local suite passed (36 passed, 2 opt-in skipped). Fresh-clone E2E against `.` passed offline from the shared uv cache (1 passed, 63.25s); online clone setup hit PyPI DNS resolving isolated `setuptools>=75`. This does not verify an uncached installation, published remote or real-data workflow. See `.ai/STATUS.md`.
- 2026-11-21: The flat-price event simulation test also checks exact two-sided costs and accounts for the second lot's lower budget after entry costs reduce marked equity; the full suite passed after this assertion.

- 2026-11-21: Source diagnostics distinguish sandbox socket restrictions from host DNS and transport failures. A bounded FRED fallback observed `urllib` timeout alongside `curl` HTTP 200 on a CDN edge; the checked Stooq sample endpoint returned a JavaScript challenge. These checks save no market data and do not establish API history, rights, vintage, or point-in-time suitability. See `.ai/STATUS.md` and `.ai/IMPLEMENTATION_PLAN.md`.
