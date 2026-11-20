---
name: parallel-prompt-implementation
description: Select, claim, implement, verify, and hand off a scoped work package from the capstone parallel prompt catalog.
---

# Parallel prompt implementation

Use this workflow when taking an implementation or review package from `.ai/PARALLEL_SESSION_PROMPTS.md`.

1. Read `AGENTS.md`, `.ai/RULES.md`, `.ai/roles/ROLES.md`, `.ai/IMPLEMENTATION_PLAN.md`, `.ai/NEXT_STEPS.md`, `.ai/BACKLOG.md`, the relevant OpenSpec requirement, and `.ai/.codex/skills/parallel-session-coordination/SKILL.md`. Inspect the target prompt and current status table. Choose an unclaimed prompt that is actionable under current dependencies; do not infer that blocked work is actionable.
2. Check the exact lock slug named by the prompt and any additional shared objects you need. Acquire each lock with a stable session ID before editing. If any required lock is held or has invalid owner metadata, do not edit those objects; report the conflict and wait or choose independent unclaimed work.
3. Under the `parallel-prompts` lock, record the claim in `.ai/PARALLEL_SESSION_PROMPTS.md` as **In progress**, with prompt ID, owner/session, date, and expected handoff. Keep ownership to the prompt's exact files and agreed interfaces. Do not edit another owner's files or broaden scope without coordination.
4. Implement the prompt and its stated acceptance criteria. For behavior changes, follow the spec-driven workflow and update the relevant requirement/scenario before or alongside implementation. Add focused checks when the prompt requires them; distinguish fixture checks from real-data or external integration evidence.
5. Hand off exact changed paths, interface effects, commands and outcomes, skipped/unrun checks, assumptions, limitations, and remaining work. Update the prompt status to **Completed** only when its acceptance evidence passes; use **Blocked** when an external prerequisite prevents completion, and state the concrete blocker. Update `.ai/STATUS.md` and `.ai/BACKLOG.md` when their evidence or task status changes. Never represent code presence or a plan as verified behavior.
6. Release only locks acquired by this session after handoff, using `scripts/object_lock.py release`. Leave other sessions' locks and changes untouched.

## Status meanings

- **Available:** no active claim is recorded; still check dependencies and locks before taking it.
- **In progress:** a named owner/session has claimed it; do not start overlapping work.
- **Blocked:** the owner recorded an unavailable dependency or access requirement and the next action needed.
- **Completed:** the prompt's acceptance checks passed and the handoff links to evidence. A completed prompt may be reopened as a new claim when follow-up work is needed.
