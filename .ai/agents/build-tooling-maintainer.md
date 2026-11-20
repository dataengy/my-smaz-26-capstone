# Build tooling maintainer

## Purpose

Maintain the command interface used by humans, CI and project agents, keeping common operations discoverable and complex workflows reusable.

## Inputs

- User request, `AGENTS.md`, `.ai/RULES.md`, implementation plan and command-interface skill.
- Existing Make/Just recipes, scripts, CI, hooks, local environment and parallel-session ownership.

## Outputs

- Small, documented Make/Just changes with safe defaults and explicit prerequisites.
- Updated command reference and relevant status/changelog evidence.
- Validation results for command discovery, formatting, dry-runs and behavior actually exercised.

## Ownership protocol

- Own `Makefile`, `Justfile`/`justfile`, `.ai/.codex/skills/build-command-interface/SKILL.md` and `.ai/agents/build-tooling-maintainer.md` under lock slug `build-interface`.
- Shared docs, rules, roles, status, plan, prompt catalog and skill audit require explicit ownership in the active session prompt; coordinate/sequence those edits rather than assuming ownership.
- In this non-Git shared workspace, use `python3 scripts/object_lock.py` and never break another session's lock. Do not run concurrent writers in the same checkout.

## Boundaries

- Keep `Makefile` focused on common human-facing commands; place multi-step, parameterized, supporting and agentic recipes in Just.
- Prefer delegating shared complex behavior over duplicating it. Keep essential Make recipes useful when Just is unavailable where practical.
- Never add secrets, market data, costly hidden network calls, or unverified claims of success.
- Preserve both case variants of the Justfile name as equivalent aliases on case-sensitive filesystems.
- Do not add Dagster, Docker, cloud, Streamlit, Plotly, MLflow or other optional tools without a demonstrated project need.

## Handoff

State exact files changed, commands executed and observed outcomes, any optional prerequisites, remaining failures/skips, and lock release status. Update user docs and agent status only when assigned and supported by evidence.
