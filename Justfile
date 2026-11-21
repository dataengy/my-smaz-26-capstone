# Supporting and agentic workflows. Keep common human entrypoints in Makefile.
set positional-arguments

export UV_PROJECT_ENVIRONMENT := env_var_or_default("UV_PROJECT_ENVIRONMENT", ".run/venv")
export UV_CACHE_DIR := env_var_or_default("UV_CACHE_DIR", ".run/uv-cache")

default:
    @just --list

# Check that the local tools expected by the project are available.
doctor:
    @python3 --version
    @uv --version
    @make --version | head -n 1
    @just --version

# Validate the resolved dependency graph without contacting package indexes.
lock-check:
    uv lock --check --offline

# Compile project, scripts and test helpers without creating research outputs.
compile:
    uv run --locked --no-sync python -m compileall -q src scripts tests

# Run the checks useful for a complete local handoff.
verify:
    just doctor
    just lock-check
    just compile
    make test

# Run a smaller, deterministic check set while changing tests or fixtures.
verify-fast:
    just compile
    make test-unit
    make test-integration
    make test-smoke

# Check an advisory lock for a shared project object.
prompt-check lock_slug session_id:
    python3 scripts/object_lock.py check {{ lock_slug }} --session-id {{ session_id }}

# Atomically acquire an advisory lock before editing its owned object.
prompt-take lock_slug session_id reason:
    python3 scripts/object_lock.py acquire {{ lock_slug }} --session-id {{ session_id }} --reason {{ reason }}

# Release only the lock owned by the current session after handoff.
prompt-release lock_slug session_id:
    python3 scripts/object_lock.py release {{ lock_slug }} --session-id {{ session_id }}

# Claim the first unclaimed parallel prompt with an available object lock.
take-next-prompt session_id:
    python3 scripts/take_next_prompt.py --session-id {{ session_id }}

# Initialize ignored local Dagster state without overwriting user configuration.
dagster-init:
    mkdir -p .run/dagster
    test -f .run/dagster/dagster.yaml || cp config/dagster.yaml .run/dagster/dagster.yaml

# Load and validate the optional research asset definitions.
dagster-check: dagster-init
    DAGSTER_HOME="{{ justfile_directory() }}/.run/dagster" uv run --locked --no-sync dg check defs --use-active-venv

# Start local orchestration UI; no schedules are configured or enabled.
dagster-dev: dagster-init
    DAGSTER_HOME="{{ justfile_directory() }}/.run/dagster" uv run --locked --no-sync dg dev --host 127.0.0.1 --port 3000 --use-active-venv

# Execute one offline frozen experiment with a configurable launch configuration.
dagster-run config="config/dagster-run.yml": dagster-init
    DAGSTER_HOME="{{ justfile_directory() }}/.run/dagster" uv run --locked --no-sync dg launch --job frozen_research_job --config "{{ config }}"

# Run the local Streamlit explorer; optional explicit bundle and port.
streamlit run=env_var_or_default("CAPSTONE_RESEARCH_RUN", "") port=env_var_or_default("STREAMLIT_SERVER_PORT", "8501"):
    CAPSTONE_RESEARCH_RUN="{{ run }}" uv run --locked --no-sync streamlit run src/capstone/dashboard.py --server.address 127.0.0.1 --server.port "{{ port }}" --server.headless true --browser.gatherUsageStats false

# Export standalone offline Plotly charts and result tables from a saved bundle.
plotly run=env_var_or_default("CAPSTONE_RESEARCH_RUN", "") output="artifacts/research-explorer/plotly.html":
    uv run --locked --no-sync python -m capstone.plotly_report --run "{{ run }}" --output "{{ output }}"
