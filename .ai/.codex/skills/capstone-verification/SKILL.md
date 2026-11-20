---
name: capstone-verification
description: Use when checking whether the capstone is reproducible and meets course acceptance requirements.
---

# Capstone verification

1. Read the current official course criteria and the project specification; map each item to a concrete artifact and observed result. Read `.ai/BUGS.md`; add reproducible defects found during QA and link open implementation work from `.ai/BACKLOG.md`. Check session ownership and acquire object locks before changing shared artifacts.
2. Run applicable tests and the documented end-to-end and local-snapshot workflows where inputs exist. Record exact commands, status and relevant output; report missing external prerequisites as blockers.
3. Check timing and leakage, simulation calculations, source rights, documented commands, secrets and excluded data. Cross-check README and `docs/` results against run artifacts and verify reciprocal links and consistency of main `.ru.md` mirrors.
4. Separate verified, partial and outstanding criteria; include defense and peer-review obligations when applicable. Do not treat a test file, a design, or a mock as evidence of a successful real-data experiment. Mark bugs verified only after their recorded acceptance check passes.
