[EN](COMMANDS.md) | [RU](COMMANDS.ru.md)

# Command reference

The Makefile is the entry point for common local work. It uses `uv` and defaults the project environment and cache to `.run/venv` and `.run/uv-cache`. Install [uv](https://docs.astral.sh/uv/) and Python 3.11 or newer first, then run `make setup` once to install the locked development dependencies. Run commands from the project root. Setup requires access to the package index unless the dependencies are already cached.

```sh
make help
make setup
make download       # reuse verified snapshots; fetch missing/stale sources
make download-refresh # force-fetch every configured source
make features       # build the analytical table from local snapshots
make run            # offline research workflow; requires downloaded snapshots
make run-notebook   # starts Jupyter for notebooks/workflow.ipynb
make demo-synthetic # generate ignored synthetic inputs and a visual HTML walkthrough
make test-demo-synthetic # verify the offline human-demo workflow
make test
make test-unit
make test-integration
make test-smoke
make test-source-smoke # live network check for configured providers; does not save data
make e2e-origin     # opt-in; requires CAPSTONE_E2E_ORIGIN
make e2e-real       # opt-in; requires CAPSTONE_E2E_CONFIG
make hooks
make install-hooks
make periodic-install  # optional macOS schedule; see the dedicated guide
make usage          # experimental local Codex metadata summary
```

`make download` contacts external providers only for missing, invalid, incomplete, or stale cache entries. A source cache is reusable only when its checksum, provider provenance, schema, unique ordered dates, completed bars, finite closes, and configured coverage pass validation. Historical CFTC archives are reused after checksum and parse validation; the current-year archive is refreshed after `download_cache_ttl_hours` (24 hours by default, in `config/settings.yml`). `make download-refresh` or `uv run capstone download --force` bypasses all cache checks. Download logs report each source decision, provider/ticker, coverage, bytes, SHA-256, and final downloaded/skipped/failed counts. Failed or malformed responses are rejected before replacing the previous snapshot. Snapshot data and outputs stay under ignored `data/` and `artifacts/`. E2E tests are opt-in and their required environment variables are described in the [runbook](RUNBOOK.md). The `usage` summary is not a complete session ledger or billing report.

`make hooks` runs the repository's `prek` checks. They include Lychee checks for links in Markdown (including external URLs), Ruff lint on Python source and project scripts, an offline local file/heading-anchor check, and `make verify-fast` (compile plus unit, integration and smoke tests), alongside whitespace, conflict-marker, YAML/JSON/TOML and private-key checks. Ruff uses the project's explicit core error and undefined-name rules. Lychee needs network access to verify external URLs; its hook checks the Markdown files selected by `prek` (all Markdown files with `make hooks` and in CI's `--all-files` run). The local link check scans the repository's Markdown files and works offline. The fast test hook runs when Python files are selected, and on all-files CI runs. CI installs the locked development dependencies before running the same hooks.

For assets whose provider history starts after the configured project start, `history_start` in `config/config.yml` sets the earliest expected cache-coverage date; it is a returned-data bound, not a claim about the asset's listing date. After acquisition, inspect the emitted source summaries and sidecars; a successful command or `0 downloaded` cache hit does not by itself certify usable target data or COT publication availability. The current validated snapshot ranges and a reproducible full experiment are recorded in [the full-run report](FULL_RUN.md).

`make test-source-smoke` is the bounded, opt-in acquisition preflight: it checks recent responses for every active configured market provider (Yahoo Finance or Binance Spot), reads only the ZIP signature from every annual CFTC archive in the configured date range, and checks each release-evidence page referenced by the COT manifest. Each request has an eight-second timeout; Yahoo responses are capped at 64 KiB and CFTC archive reads at four bytes. It never writes snapshots. A passing probe establishes current endpoint reachability and basic response shape; it does not validate full archive contents, data completeness, licensing, COT publication timestamps, or research usability. If it fails, do not start the bulk downloader. Ordinary `make test` and `make test-smoke` skip these live checks.

Offline source loading is idempotent for unchanged, checksum-valid snapshots and configuration: repeated calls return the same rows without network requests or snapshot writes. Duplicate dates are rejected. The downloader is cache-aware by default; forced refresh is explicit.

## Network diagnostics and clean installation

Use these scripts when source access or package installation is uncertain:

```sh
python3 scripts/check_external_access.py
python3 scripts/check_external_access.py --only yahoo_gld_5d_chart
python3 scripts/check_external_access.py --only cftc_disaggregated_futures_only_gold_api
python3 scripts/check_clean_install.py
```

The source probe records DNS and bounded HTTPS outcomes for GitHub, PyPI, CFTC, Yahoo Finance, FRED, Stooq and Alpha Vantage; it reads at most 8 KiB per response, checks the CFTC/Yahoo/CSV response shapes, saves no market data and does not retry HTTP 429. If Python `urllib` times out on the FRED landing page, it runs a bounded `curl` request that discards the body and records HTTP status and remote IP separately. This distinguishes a client/CDN-edge discrepancy from host unavailability; it does not validate FRED API access or point-in-time suitability. Its Stooq request is limited to a short recent GLD daily sample. `--only` can be repeated to select endpoints; `--timeout` sets the per-request timeout. Run it in the same network boundary as the acquisition workflow. A sandbox socket denial is not evidence of a device-wide DNS outage. The clean-install check uses `uv.lock` and the `dev` extra in a temporary environment with a new temporary uv cache, verifies imports, notebook-format support and an XNYS session, then removes both temporary paths. It does not run tests or download project market snapshots.

The synthetic demo uses deterministic fictional market and COT-shaped inputs, then exercises the real feature, model-selection and simulation code. It does not call providers and its metrics are not research results. Open `artifacts/synthetic-demo/index.html` after `make demo-synthetic`; see [Synthetic human demo](SYNTHETIC_DEMO.md) for details.

Change the schedule with `make periodic-install PERIODIC_INTERVAL_MINUTES=60`. The `periodic-uninstall` and `periodic-run` targets remove or run the task. See the [periodic commit and push guide](PERIODIC_COMMIT_PUSH.md) for its safeguards and behavior.

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
