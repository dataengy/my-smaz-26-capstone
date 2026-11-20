---
name: bug-tracking
description: Record, prioritize, fix, and verify defects found in the capstone project.
---

# Bug tracking

Use this workflow whenever a user reports a defect or a reproducible project defect is discovered.

1. Read `AGENTS.md`, `.ai/RULES.md`, `.ai/roles/ROLES.md`, `.ai/BUG_TRACKING_RULES.md`, `.ai/BUGS.md`, and the relevant specification or implementation notes. Check active object locks before editing shared files.
2. Reproduce the symptom or inspect saved evidence. Identify the smallest root cause; distinguish follow-on errors from separate defects.
3. Add or update a stable `BUG-NNN` entry in `.ai/BUGS.md` with status, priority, area, symptom/evidence, and an acceptance check. Keep open implementation work prioritized in `.ai/BACKLOG.md` and link between the records.
4. Fix the cause, preserve unrelated user work, and make the narrowest meaningful validation. Do not claim a full workflow passed when only a focused check ran.
5. Update the bug entry to **fixed** when code changed and **verified** only after its stated acceptance check passes. Include the exact check and any limits.
6. Update relevant plans/status records when evidence or project state changes. Release only locks acquired by this session after handing off changed paths and verification results.
