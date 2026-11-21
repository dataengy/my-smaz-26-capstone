# Research explorer implementation

Owner: `codex-explorer-20261121`. The user authorized adding the recommended improvements in descending priority. This first complete increment covers the research notebook and Streamlit/Plotly explorer; do not install competing presentation frameworks or an ingestion stack without a concrete need.

Spec: [research explorer](../../openspec/changes/research-explorer/spec.md).

## Ownership

- `research-explorer`: new `src/capstone/reporting.py`, `dashboard.py`, `notebooks/research.ipynb`, focused reporting/dashboard tests.
- `dashboard-dependencies`: `pyproject.toml`, `uv.lock` dashboard/orchestration extras only; preserve unrelated changes.
- `explorer-docs`: this plan, the new spec and bilingual `docs/RESEARCH_EXPLORER.*`.
- Shared workflow, model, QA, status, backlog and Makefile are owned by other sessions at start. Do not edit their objects; integrate common commands only after `build-interface` is available.

- `build-interface`: Makefile/Justfile targets, preserving their hardlink and existing work.
- `plotly-report`: standalone `src/capstone/plotly_report.py` and its focused tests.

## Sequence and checks

- [x] Add a read-only bundle loader and diagnostic calculations. Test hash failures, missing outputs, blocked runs, train-only correlations, independent drawdown arithmetic and ticker error summaries.
- [x] Create one research notebook, using shared functions and portable Matplotlib figures. Execute from `notebooks/` using an explicit bundle; save the executed copy and HTML under ignored `artifacts/research-explorer/`. Inspect rendered figures.
- [x] Create Streamlit tabs for data, models, portfolio and errors. Add Plotly equity/drawdown charts and ticker diagnostics; portfolio results retain the full universe. Test with Streamlit AppTest and check the local rendered UI when available.
- [x] Lock/install the optional dashboard extra, document setup/run/missing-bundle behavior in EN/RU, and integrate Make commands when ownership permits.
- [ ] Run focused checks and the project suite; record commands, outputs and any installation/rendering limitations. Release only this session's locks.

## Subsequent priorities

1. Dagster adapter if recurring execution/run visibility is the next desired outcome; preserve existing CLI and frozen-replay semantics.
2. dlt only when a source, destination, cursor, deduplication key and historical-revision policy are specified and tested. Snapshot reuse alone is not incremental ingestion.

## Dagster follow-through

After the explorer's `just verify` passed (83 passed, 4 skipped), implemented the next priority as a separate optional adapter: `src/capstone/orchestration.py`, `dg.toml`, `config/dagster*`, `tests/integration/test_orchestration.py`, bilingual `docs/ORCHESTRATION.*` and `openspec/changes/local-orchestration/spec.md`. Locks: `dagster-adapter` and `dagster-project-config`, in addition to the already held dependency/build locks. Four related assets come from one atomic call to the existing runner, preserving frozen input/coverage/replay semantics. No scheduler, provider fetch, dlt ingestion or Prefect service is added.

## Verification evidence and handoff (2026-11-21)

- Core verification after the dashboard: `MPLCONFIGDIR=.run/matplotlib-cache just verify` — 83 passed, 4 skipped. After Dagster: 85 passed, 4 skipped. Optional skips cover origin clone, real-data E2E and live source checks.
- `just dagster-check` loaded definitions successfully. Actual `just dagster-run` succeeded with four materializations and 20 reproduced numerical outputs in `artifacts/dagster/37f447d6-64e6-4160-a46a-bfda761e8924`. One native runner invocation preserved its two-pass replay contract. The run recorded `forest_3`, validation MAE 0.032349 and RMSE 0.048348; this differs from the older mean-baseline bundle because the effective configuration/split changed. Explorers show the chosen bundle's recorded selection.
- Executed the research notebook top-to-bottom on that Dagster bundle. Local executed copy, HTML and four figures are under ignored `artifacts/research-explorer/`. Inspected all four PNGs. Checked-in notebook outputs remain cleared. AppTest loaded the actual bundle with four tabs and no exceptions; focused tests cover ticker filtering without portfolio changes and tamper rejection.
- `make plotly` exported `artifacts/research-explorer/plotly.html` from the same Dagster bundle. Both exporter tests passed: embedded JavaScript/no remote script dependency, verified read-only inputs, and rejection of output inside a frozen bundle.
- `just streamlit artifacts/dagster/37f447d6-64e6-4160-a46a-bfda761e8924 8502` started successfully on localhost. Stopped both this instance and the earlier port-8501 test instance after the user's port conflict; confirmed neither 8501 nor 8502 had a listener. Leave service launch to the user's terminal.
- `make help`, `just --list`, `just --fmt --check --justfile Justfile`, Make dry-runs and local Markdown links passed (87 files). Makefile delegates to parameterized Just recipes; `make dashboard` and `make streamlit` share the same recipe. Both preserve `CAPSTONE_RESEARCH_RUN` and `STREAMLIT_SERVER_PORT`. Justfile/justfile retain inode 78254528.
- Ruff passed all four new modules. `git diff --check` passed. Browser visual inspection was unavailable because the CUA browser host was unavailable; AppTest and notebook figure inspection are the verified UI/visual evidence.
- Main implementation plan/status/course reports and shared command documentation remain owned by other sessions; this file and the bilingual explorer/orchestration docs provide the integration handoff without overwriting those sessions' work.
