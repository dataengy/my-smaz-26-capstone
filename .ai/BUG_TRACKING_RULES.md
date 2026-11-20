# Bug tracking rules

- `.ai/BUGS.md` is the canonical defect register. Keep resolved entries as history.
- Put open implementation work and priority in `.ai/BACKLOG.md`; avoid duplicating task plans in the bug register.
- Every entry needs a stable ID, observed symptom, status, evidence, and an acceptance check.
- Use **fixed** for an implementation that still needs acceptance verification and **verified** only when the check passed. Report partial coverage and blockers plainly.
- Agents must update the register when they discover or resolve a defect, and link meaningful changes to project status/evidence.
- Follow `.ai/.codex/skills/bug-tracking/SKILL.md` and `.ai/agents/bug-tracker.md`.
