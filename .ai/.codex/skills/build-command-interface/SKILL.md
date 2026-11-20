---
name: build-command-interface
description: Maintain the project's human-facing Makefile and supporting Justfile without duplicating workflows.
---

# Build command interface

Use this skill before changing `Makefile` or `Justfile`.

## Ownership and intent

- `Makefile` is the discoverable human interface: short, common project tasks and general local operations.
- `Justfile` holds additional, supporting, multi-step, parameterized, reusable and agentic operations.
- Prefer a simple Make target when a developer can understand it as one familiar command. Delegate complex shared workflows to Just rather than implementing them twice.
- Keep common Make targets usable without Just where practical. `make help` must explain prerequisites and point to advanced recipes.
- Do not add optional infrastructure or a command solely to increase checklist coverage.

## Before editing

1. Read `AGENTS.md`, `.ai/RULES.md`, `.ai/IMPLEMENTATION_PLAN.md`, the relevant role profile and this skill.
2. Check `.ai/PARALLEL_SESSION_PROMPTS.md` and `.ai/.locks/`; acquire the `build-interface` object lock via `scripts/object_lock.py` before editing these shared files.
3. Inspect existing target behavior, environment defaults, CI and hook commands. Preserve unrelated changes and both `Justfile`/`justfile` names, which may be filesystem aliases.
4. Keep data, secrets, artifacts and environments under ignored paths; never add downloaded data or credentials through a command target.

## Design rules

- Use clear, stable, lowercase target names, useful `help`, and `.PHONY` for non-file Make targets.
- Keep shell and repeated complex code out of Make recipes; put reusable logic in Just recipes or project scripts.
- Avoid surprising network activity. Name online acquisition explicitly and keep offline replay available.
- Pass configuration and environment explicitly. Avoid shell interpolation hazards and silent error masking.
- Agent/session operations must use the project object-lock contract; do not automatically expire or break locks.
- Document opt-in E2E variables and expensive/networked behavior.

## Verification and handoff

Run and report what is available:

```sh
make help
just --list
just --fmt --check --justfile Justfile
make -n verify
make test
```

For behavior changes, run the relevant command(s), not only dry-runs. Ensure `Justfile` and lowercase `justfile` remain equivalent (ideally the same inode where supported). Record limitations and actual outcomes in `docs/COMMANDS.md`, the changelog, `.ai/STATUS.md` and the implementation plan when applicable. Release only the lock owned by this session after handing off.
