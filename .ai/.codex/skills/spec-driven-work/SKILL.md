---
name: spec-driven-work
description: Use when changing capstone behavior or acceptance requirements under the project SDD workflow.
---

# Spec-driven work

1. Read the affected requirement and scenario under `openspec/specs/`, plus `.ai/IMPLEMENTATION_PLAN.md` for ownership and status.
2. Before editing shared files, check parallel-session ownership and acquire relevant object locks using the project coordination skill. For a behavior change, update requirements and observable acceptance scenarios, agree affected interfaces, then implement and verify. Keep implementation status and evidence in the plan rather than duplicating the spec.
3. If the OpenSpec CLI is actually available, follow the verified installed version's commands and record validation output. Otherwise treat files as a human-readable baseline and report that CLI validation is unverified. If a critical edit is blocked by another lock, use an isolated Git worktree when available; do not bypass the lock by writing in the shared checkout.
