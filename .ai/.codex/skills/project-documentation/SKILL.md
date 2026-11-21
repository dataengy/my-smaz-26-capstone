---
name: project-documentation
description: Use when creating, translating, or updating capstone documentation, Mermaid diagrams, and documentation navigation.
---

# Project documentation

1. Read the applicable instructions, `.ai/RULES.md`, current implementation and evidence before describing behavior. Distinguish verified results, assumptions and unfinished work.
2. Place documentation of implemented project behavior in `docs/` for people and agents. Use Diátaxis as a guide: tutorials for learning, how-to guides for tasks, reference for facts, and explanations for concepts. Keep ADRs, architecture, runbooks and the changelog discoverable alongside these; choose the simplest structure that fits the content.
3. Keep agentic work artifacts, including backlog, implementation plans, next steps, rules, session prompts and session management, under `.ai/`. Link to canonical project facts and evidence instead of copying them. Requirements remain under `openspec/`.
4. English is primary. Maintain Russian mirrors for the main human-facing documents using `.ru.md` before the extension (for example `README.md` and `README.ru.md`). Add reciprocal language-switch links and preserve working relative links. Translate the actual content and keep its status and factual meaning aligned; explicitly mark any stale mirror until updated. Agent-only artifacts do not require translations by default.
5. Verify changed links, mirror pairing and commands as appropriate. Coordinate substantive facts with their owners and record checks and limitations without inventing outcomes.

## Mermaid diagrams in paired documentation

Use this workflow when diagrams help explain implemented data flow, availability, evaluation boundaries, simulation or reproduction.

1. Inventory existing diagrams and read the current code and canonical evidence. Choose a distinct reader question for each addition; extend or correct an existing diagram when that is clearer than repeating it. Respect active file ownership before editing.
2. Place each fenced `mermaid` block next to the section it explains, with a short introduction or caption. Prefer a flowchart for decisions and dependencies, and a sequence diagram for ordering across components. Use quoted labels and simple syntax; avoid decorative styling and remote assets.
3. Update the English document and Russian mirror together. Preserve diagram type, node/participant IDs, branches, edges and decision meaning across the pair; translate visible labels and surrounding explanation. Keep reciprocal language links.
4. Show only verified behavior. Keep report observation, API availability and trading cutoff distinct; show purge before fitting, validation-only model/threshold selection and frozen holdout evaluation. Separate the canonical COT manifest from a stricter frozen experiment audit. Link to run evidence rather than copying mutable metrics into every diagram.
5. Distinguish cash-constrained event simulation from vector approximation and benchmark. In reproduction diagrams, show the coverage gate, frozen inputs/code, hash checks, required numerical files and failure outcomes; matching incomplete directories are not successful reproduction.
6. Inspect every changed diagram for code agreement, paired topology, balanced fences and readable labels. Use an available local Mermaid parser/rendering tool when practical; report whether syntax/rendering was actually checked. Do not install a renderer, run the financial workflow, or change runtime settings merely for a documentation edit.
