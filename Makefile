# Human-facing shortcuts for common local work.
# More involved verification and agent/session helpers live in Justfile.
.DEFAULT_GOAL := help
.PHONY: help setup download data features run run-notebook test test-smoke test-unit test-integration e2e-origin e2e-real hooks install-hooks usage doctor verify verify-fast agents

export UV_PROJECT_ENVIRONMENT ?= .run/venv
export UV_CACHE_DIR ?= .run/uv-cache

help:
	@printf '%s\n' \
	  'Common project commands:' \
	  '  make setup          Install locked development dependencies' \
	  '  make download       Fetch configured market/COT snapshots' \
	  '  make features       Build the feature dataset from snapshots' \
	  '  make run            Run the offline research workflow' \
	  '  make run-notebook   Open the workflow notebook' \
	  '  make test           Run all applicable tests' \
	  '  make test-unit      Run unit tests only' \
	  '  make test-integration  Run integration tests only' \
	  '  make test-smoke     Run smoke tests only' \
	  '  make e2e-origin     Clone CAPSTONE_E2E_ORIGIN and verify the checkout' \
	  '  make e2e-real       Run against CAPSTONE_E2E_CONFIG snapshots' \
	  '  make hooks          Run repository pre-commit checks' \
	  '  make install-hooks  Install the local pre-commit hook' \
	  '  make usage          Summarize local project-attributed Codex metadata' \
	  '  make verify         Run the extended Justfile verification workflow' \
	  '  make agents         List supporting/agentic Justfile recipes'

setup:
	uv sync --locked --extra dev

download data:
	uv run --locked --no-sync capstone download

features:
	uv run --locked --no-sync capstone features

run:
	uv run --locked --no-sync capstone run --offline

run-notebook:
	uv run --locked --no-sync jupyter notebook notebooks/workflow.ipynb

test:
	uv run --locked --no-sync python -m pytest -q -ra

test-unit:
	uv run --locked --no-sync python -m pytest -q -ra tests/unit

test-integration:
	uv run --locked --no-sync python -m pytest -q -ra tests/integration

test-smoke:
	uv run --locked --no-sync python -m pytest -q -ra tests/smoke

e2e-origin:
	uv run --locked --no-sync python -m pytest -q -ra tests/e2e/test_origin_fresh_clone.py

e2e-real:
	uv run --locked --no-sync python -m pytest -q -ra tests/e2e/test_real_data.py

hooks:
	uv run --locked --no-sync prek run --all-files

install-hooks:
	uv run --locked --no-sync prek install

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
