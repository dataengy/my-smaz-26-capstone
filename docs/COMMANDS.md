[EN](COMMANDS.md) | [RU](COMMANDS.ru.md)

# Command reference

The Makefile is the entry point for common local work. It uses `uv` and defaults the project environment and cache to `.run/venv` and `.run/uv-cache`. Install [uv](https://docs.astral.sh/uv/) and Python 3.11 or newer first, then run `make setup` once to install the locked development dependencies. Run commands from the project root. Setup requires access to the package index unless the dependencies are already cached.

```sh
make help
make setup
make download       # network access; fetch configured sources
make features       # build the analytical table from local snapshots
make run            # offline research workflow; requires downloaded snapshots
make run-notebook   # starts Jupyter for notebooks/workflow.ipynb
make test
make test-unit
make test-integration
make test-smoke
make e2e-origin     # opt-in; requires CAPSTONE_E2E_ORIGIN
make e2e-real       # opt-in; requires CAPSTONE_E2E_CONFIG
make hooks
make install-hooks
make usage          # experimental local Codex metadata summary
```

`make download` accesses external providers and can overwrite local source snapshots. Snapshot data and outputs stay under ignored `data/` and `artifacts/`. E2E tests are opt-in and their required environment variables are described in the [runbook](RUNBOOK.md). The `usage` summary is not a complete session ledger or billing report.

The Justfile provides supporting, multi-step or agentic operations. Install [just](https://just.systems/) for these targets:

```sh
just --list
just doctor
just lock-check
just compile
just verify-fast
just verify
just prompt-check <lock-slug> <session-id>
just prompt-take <lock-slug> <session-id> "<reason>"
just prompt-release <lock-slug> <session-id>
just take-next-prompt <session-id>
```

`just verify` runs tool checks, offline lock validation, compilation and the full test suite. `just verify-fast` runs compilation and unit, integration and smoke tests. Prompt operations use advisory project object locks; they do not expire automatically. Check ownership and release only a lock held by your session. `make doctor`, `make verify`, `make verify-fast` and `make agents` are convenience delegates to Just, so these targets require Just.

Environment overrides are supported, for example:

```sh
UV_PROJECT_ENVIRONMENT=.run/venv UV_CACHE_DIR=.run/uv-cache make test
UV_PROJECT_ENVIRONMENT=.run/venv UV_CACHE_DIR=.run/uv-cache just verify
```

See the [runbook](RUNBOOK.md) for source setup and offline replay, and the [architecture](ARCHITECTURE.md) for workflow boundaries.
