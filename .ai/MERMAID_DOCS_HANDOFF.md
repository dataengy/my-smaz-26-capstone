# Bilingual Mermaid documentation — 2026-11-21

Owner: `codex-mermaid-docs-20261121`.

- Updated and directly applied the repository-local [project-documentation skill](.codex/skills/project-documentation/SKILL.md): Mermaid selection, source agreement, EN/RU topology, captions, financial timing, source-policy boundaries and honest validation reporting.
- Added **five diagram pairs / ten new Mermaid blocks** across `docs/ARCHITECTURE.md`, `docs/RUNBOOK.md`, `docs/COT_RELEASE_EVIDENCE.md` and their Russian mirrors. Topics: signal/execution ordering, cash-constrained simulation, strict COT audit, frozen experiment/replay and failure recovery.
- Corrected the existing chronological-evaluation diagram in both architecture documents: purge precedes candidate fitting/selection, and held-out rows feed final evaluation only. Replaced stale “real run unverified” introductions in architecture and runbook with links to the canonical full-run report; did not duplicate metrics.
- Final inventory: architecture four diagrams per language; runbook three; COT publication evidence one. New diagrams distinguish the canonical manifest from the stricter frozen audit and do not transfer one policy's checks to the other.
- The canonical `FULL_RUN` report pair was locked by `independent-qa-20261121`; no edits were made there. Runtime code, configuration, data and other sessions' edits were preserved.
- Validation: local skill `quick_validate.py` returned **Skill is valid!**; inspected code agreement, balanced Markdown fences, EN/RU diagram topology and reciprocal language links; local Markdown link targets resolve. `git diff --check` passed with an unrelated existing CRLF normalization notice on the release manifest. No Mermaid parser/rendering tool was installed or run; no financial workflow or runtime tests were needed for this documentation edit.
- The skill remains a repo-local source, used by direct reading in this session; global installation and automatic skill discovery are not claimed. Release only this session's object locks after handoff.
