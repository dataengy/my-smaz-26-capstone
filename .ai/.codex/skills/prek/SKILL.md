---
name: prek
description: Configure or run the project's pinned prek hooks for local Git checks and CI.
---

# Project prek workflow

- The project pins `prek==0.5.10` in the `dev` extra and defines hooks in `.pre-commit-config.yaml`.
- Install the development environment with `uv sync --locked --extra dev`.
- Run the configured hooks with `make hooks` or `uv run --locked --extra dev prek run --all-files`.
- Install the Git pre-commit shim for this clone with `make install-hooks` or `uv run --locked --extra dev prek install`. This writes to Git metadata; respect the workspace's filesystem permissions.
- Hooks may edit files. Inspect `git diff` afterward and keep unrelated or concurrently owned edits intact.
- Update hook versions and the uv lock together. Do not disable a failing check just to get a commit through; diagnose the finding and scope exceptions narrowly.

The project uses prek's built-in hooks, so this config does not need to clone hook repositories. CI runs the same configuration through the pinned `j178/prek-action`.
