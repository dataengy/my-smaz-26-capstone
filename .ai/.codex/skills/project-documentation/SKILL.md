---
name: project-documentation
description: Use when creating, translating, or updating capstone documentation and documentation navigation.
---

# Project documentation

1. Read the applicable instructions, `.ai/RULES.md`, current implementation and evidence before describing behavior. Distinguish verified results, assumptions and unfinished work.
2. Place documentation of implemented project behavior in `docs/` for people and agents. Use Diátaxis as a guide: tutorials for learning, how-to guides for tasks, reference for facts, and explanations for concepts. Keep ADRs, architecture, runbooks and the changelog discoverable alongside these; choose the simplest structure that fits the content.
3. Keep agentic work artifacts, including backlog, implementation plans, next steps, rules, session prompts and session management, under `.ai/`. Link to canonical project facts and evidence instead of copying them. Requirements remain under `openspec/`.
4. English is primary. Maintain Russian mirrors for the main human-facing documents using `.ru.md` before the extension (for example `README.md` and `README.ru.md`). Add reciprocal language-switch links and preserve working relative links. Translate the actual content and keep its status and factual meaning aligned; explicitly mark any stale mirror until updated. Agent-only artifacts do not require translations by default.
5. Verify changed links, mirror pairing and commands as appropriate. Coordinate substantive facts with their owners and record checks and limitations without inventing outcomes.
