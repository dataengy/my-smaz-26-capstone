---
name: session-gate-handoff
description: Update or consume the shared cross-session handoff gate before starting, ending, or handing work to another session.
---

# Session gate handoff

Use `.ai/.locks/GATE.md` as the short entry point for parallel sessions. Keep it evidence-based and useful to the next owner; do not copy raw chat/session logs or replace canonical project records.

1. Read `AGENTS.md`, `.ai/RULES.md`, `.ai/STATUS.md`, `.ai/NEXT_STEPS.md`, `.ai/IMPLEMENTATION_PLAN.md`, the relevant run reports and every relevant `.ai/.locks/*/owner.json`. Treat each `owner.json` as current ownership evidence only at the time read.
2. Before editing the gate, acquire the `gate-handoff` object lock with `scripts/object_lock.py`. If another session owns it, hand off the proposed update; never edit around a held lock or infer that it is stale.
3. Summarize only claims with a dated source: status/report path, exact check result and environment, relevant artifact, and limits. Label user-pasted output as user-reported. Preserve historical attempts as history and state which later evidence supersedes them.
4. Distinguish project state from the status of each session. List active lock owners and scopes compactly, identify the immediate dependency, and give one to three ordered next actions. Never claim another session's work is integrated or complete until its owner hands it off and releases the relevant lock.
5. Keep competing evidence sets separate. For COT, a row count in the canonical manifest is not interchangeable with a frozen row audit that checked post-launch scope, paired contracts, creation/update equality, exact archive-field matches, raw response provenance and hashes. Refer to the governing acceptance requirement and report.
6. Do not edit owner-locked status, backlog, implementation plan, docs, specs, or code while updating the gate. Ask the owning session to reconcile its record or update only files explicitly assigned to this session. Do not commit, push, download data or run an experiment unless the active user request authorizes it.
7. Before handoff, recheck lock owners, verify links and claims in the gate, run `git diff --check` for owned changed files, and release only locks acquired by this session. State changed paths, checks, unresolved conflicts and next owner in the handoff.

SessionEnd hook reminder is registered through `scripts/session-hooks/cross-session-gate-hook.sh`; it prints a reminder only and never edits the gate or blocks session shutdown.
