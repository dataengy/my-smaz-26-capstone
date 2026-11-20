# Bug register

This is the canonical record of defects observed in the capstone. Keep entries concise and evidence-backed. Prioritize implementation work in the [project backlog](BACKLOG.md); this register records the defect, owner/status and the evidence that resolves it. When configured, link a GitHub issue and Projects board item to the corresponding `BUG-*` entry; this register remains the source for reproduction and fix evidence.

## Lifecycle rules

- Record a bug when a reproducible defect is observed. Include the symptom, reproduction context, affected area, and an acceptance check.
- Use stable IDs (`BUG-001`, `BUG-002`, ...). Do not remove resolved entries; retain them as a searchable fix history.
- Statuses: **open**, **in progress**, **fixed** (a code change exists but acceptance is not yet verified), and **verified** (the acceptance check passed). Record blockers without presenting them as fixes.
- Link implementation and verification evidence. State when a full workflow could not be run, and do not infer success from a targeted check.
- Agents discovering or fixing a bug update this register and link consequential work from the backlog. Follow the [bug-tracking skill](.codex/skills/bug-tracking/SKILL.md) and [bug-tracker agent guide](agents/bug-tracker.md).

## Bugs

| ID | Status | Priority | Area | Defect and evidence | Acceptance |
|---|---|---|---|---|---|
| BUG-001 | verified | P1 | Notebook startup | Jupyter ran the notebook kernel from `notebooks/`, so `read_config("config/config.yml", ...)` raised `FileNotFoundError`. The next workflow cell then raised `NameError` because `config` was never set. The setup cell now locates the project root by `pyproject.toml` and `config/config.yml`, changes to that directory, and loads the config. The user's subsequent saved run reached data loading and reported missing `data/raw/market/GLD.csv` or hash metadata; that is a required-input blocker, not a recurrence of this bug. | Executed the setup cell with the working directory set to `notebooks/`; config loaded and the working directory resolved to the project root. The saved workflow run passed config loading and stopped at the expected missing-snapshot check. Full research execution remains blocked until valid snapshots are available. See [`workflow.ipynb`](../notebooks/workflow.ipynb). |
| BUG-002 | verified | P1 | Notebook launcher | `make run-notebook` failed because `uv.lock` did not match the declared `dev` extra when `--locked` was used. Regenerated the lockfile with `uv lock`. The locked resolver check now succeeds. Launching the notebook server was separately blocked in this environment because PyPI DNS was unavailable for a missing `nbformat` wheel. | `UV_CACHE_DIR=.run/uv-cache UV_PROJECT_ENVIRONMENT=.run/venv uv lock --check` resolved 135 packages successfully, and `make -n run-notebook` emitted the expected locked Jupyter command. The actual server launch remains unverified in this environment. |
