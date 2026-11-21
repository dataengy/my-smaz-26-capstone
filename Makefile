# Human-facing shortcuts for common local work.
# More involved verification and agent/session helpers live in Justfile.
.DEFAULT_GOAL := help
.PHONY: help setup download download-refresh data features run run-notebook demo-synthetic test-demo-synthetic test test-smoke test-source-smoke test-unit test-integration e2e-origin e2e-real hooks install-hooks periodic-install periodic-uninstall periodic-run usage doctor verify verify-fast agents
.PHONY: setup-dashboard dashboard run-research-notebook
.PHONY: setup-orchestration dagster
.PHONY: streamlit plotly

export UV_PROJECT_ENVIRONMENT ?= .run/venv
export UV_CACHE_DIR ?= .run/uv-cache
PERIODIC_INTERVAL_MINUTES ?= 30
PERIODIC_QUIET_MINUTES ?= 10

help:
	@printf '%s\n' \
	  'Common project commands:' \
	  '  make setup          Install locked development dependencies' \
	  '  make download       Reuse valid snapshots; fetch missing/stale sources' \
	  '  make download-refresh  Force-refresh every configured source' \
	  '  make features       Build the feature dataset from snapshots' \
	  '  make run            Run the offline research workflow' \
	  '  make run-notebook   Open the workflow notebook' \
	  '  make run-research-notebook  Open the saved-result research notebook' \
	  '  make setup-dashboard  Install locked development + dashboard extras' \
	  '  make dashboard      Explore saved runs at localhost:8501' \
	  '  make streamlit      Alias for the Streamlit dashboard' \
	  '  make plotly         Export a standalone interactive HTML report' \
	  '  make setup-orchestration  Install dev, dashboard and Dagster extras' \
	  '  make dagster        Open optional local research orchestration' \
	  '  make demo-synthetic Generate synthetic data and a visual human demo' \
	  '  make test-demo-synthetic  Run only the offline synthetic human-demo test' \
	  '  make test           Run all applicable tests' \
	  '  make test-unit      Run unit tests only' \
	  '  make test-integration  Run integration tests only' \
	  '  make test-smoke     Run smoke tests only' \
	  '  make test-source-smoke  Check live access to configured data sources' \
	  '  make e2e-origin     Clone CAPSTONE_E2E_ORIGIN and verify the checkout' \
	  '  make e2e-real       Run against CAPSTONE_E2E_CONFIG snapshots' \
	  '  make hooks          Run Ruff, Markdown-link, and fast-test checks' \
	  '  make install-hooks  Install the local pre-commit hook' \
	  '  make periodic-install  Install the opt-in macOS commit/push schedule' \
	  '  make periodic-uninstall  Remove the scheduled commit/push task' \
	  '  make periodic-run   Run one guarded periodic commit/push cycle' \
	  '  make usage          Summarize local project-attributed Codex metadata' \
	  '  make verify         Run the extended Justfile verification workflow' \
	  '  make agents         List supporting/agentic Justfile recipes'

setup:
	uv sync --locked --extra dev

setup-dashboard:
	uv sync --locked --extra dev --extra dashboard

setup-orchestration:
	uv sync --locked --extra dev --extra dashboard --extra orchestration

dagster:
	just dagster-dev

dashboard:
	just streamlit

streamlit: dashboard

plotly:
	just plotly

run-research-notebook:
	uv run --locked --no-sync jupyter notebook notebooks/research.ipynb

download data:
	uv run --locked --no-sync capstone download

download-refresh:
	uv run --locked --no-sync capstone download --force

features:
	uv run --locked --no-sync capstone features

run:
	uv run --locked --no-sync capstone run --offline

run-notebook:
	uv run --locked --no-sync jupyter notebook notebooks/workflow.ipynb

demo-synthetic:
	uv run --locked --no-sync python -m capstone.synthetic_demo

test-demo-synthetic:
	uv run --locked --no-sync python -m pytest -q -ra tests/e2e/test_human_demo.py

test:
	uv run --locked --no-sync python -m pytest -q -ra

test-unit:
	uv run --locked --no-sync python -m pytest -q -ra tests/unit

test-integration:
	uv run --locked --no-sync python -m pytest -q -ra tests/integration

test-smoke:
	uv run --locked --no-sync python -m pytest -q -ra tests/smoke

test-source-smoke:
	CAPSTONE_SOURCE_SMOKE=1 uv run --locked --no-sync python -m pytest -q -ra -s tests/smoke/test_source_availability.py

e2e-origin:
	uv run --locked --no-sync python -m pytest -q -ra tests/e2e/test_origin_fresh_clone.py

e2e-real:
	uv run --locked --no-sync python -m pytest -q -ra tests/e2e/test_real_data.py

hooks:
	uv run --locked --no-sync prek run --all-files

install-hooks:
	uv run --locked --no-sync prek install

periodic-install:
	python3 scripts/periodic_commit_push.py install --interval-minutes $(PERIODIC_INTERVAL_MINUTES) --quiet-minutes $(PERIODIC_QUIET_MINUTES)

periodic-uninstall:
	python3 scripts/periodic_commit_push.py uninstall

periodic-run:
	python3 scripts/periodic_commit_push.py run --quiet-minutes $(PERIODIC_QUIET_MINUTES)

usage:
	uv run --locked --no-sync python scripts/codex_usage.py --project .

doctor:
	just doctor

verify:
	just verify

verify-fast:
	just verify-fast

agents:
	just --list
