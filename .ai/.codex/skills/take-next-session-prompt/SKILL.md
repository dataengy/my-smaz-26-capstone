---
name: take-next-session-prompt
description: Select, claim, implement, and hand off the next available prompt from the capstone parallel-session catalog.
---

# Take the next session prompt

Use this workflow when asked to take an unclaimed implementation or review prompt from `.ai/PARALLEL_SESSION_PROMPTS.md`.

1. Read `AGENTS.md`, `.ai/RULES.md`, `.ai/roles/ROLES.md`, `.ai/NEXT_STEPS.md`, `.ai/BACKLOG.md`, the relevant OpenSpec requirements, and the prompt catalog. Confirm the prompt is actionable and its dependencies are met.
2. Use a stable, unique session ID and run `just take-next-prompt <SESSION_ID>`. This serializes catalog claims, selects the earliest unclaimed prompt in catalog order with an available object lock, acquires that lock, and records **In progress** in the claim table. A prompt absent from the table is treated as unclaimed; **In progress**, **Completed**, and **Blocked** prompts are skipped.
3. Read the selected prompt in full. Follow its exact ownership, dependencies, off-limits paths, evidence requirements, checks, and handoff instructions. Do not edit files outside the prompt's scope without coordinating with their owner.
4. If no eligible prompt is available, stop and report that result. Do not remove another session's lock, infer that a lock is stale from its age, or skip a dependency gate to force a claim.
5. During handoff, update the claim row to **Completed** only when the prompt's acceptance checks have evidence. Otherwise record **Blocked** or keep it **In progress**, with the blocker and evidence. Update `.ai/STATUS.md` or `.ai/BACKLOG.md` only when the prompt or orchestrator owns those records.
6. Release only locks acquired by this session after handoff:

   ```sh
   just prompt-release <LOCK_SLUG> <SESSION_ID>
   ```

## Manual lock operations

For a deliberately selected prompt, use its declared lock slug:

```sh
just prompt-check <LOCK_SLUG> <SESSION_ID>
just prompt-take <LOCK_SLUG> <SESSION_ID> "<short reason>"
```

Manual lock operations do not change the prompt claim table. Record the claim under the `parallel-prompts` lock, or use `just take-next-prompt` for the automatic selection and claim flow.

## Dry run

Preview the next eligible prompt without acquiring locks or changing the catalog:

```sh
python3 scripts/take_next_prompt.py --session-id <SESSION_ID> --dry-run
```
