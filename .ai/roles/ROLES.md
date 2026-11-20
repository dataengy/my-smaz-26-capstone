# Agent role profiles

Roles are reusable responsibilities, not continuously running processes or separate permissions. The orchestrator provides the task, relevant spec, inputs, output format, ownership boundaries, and handoff deadline; a worker preserves changes outside its assignment. Combine compatible roles where useful. QA must independently assess integrated behavior.

## Orchestrator
- **Purpose:** Sequence work, resolve dependencies and integrate the standalone capstone.
- **Inputs:** User request, specifications, plan, worker findings and current working tree.
- **Outputs:** Scoped assignments, decisions, integrated review, current `.ai/IMPLEMENTATION_PLAN.md` and `.ai/STATUS.md`, and final evidence-based handoff.
- **Boundaries and handoff:** Avoid overlapping ownership; resolve shared contracts before parallel edits. Inspect active sessions and obtain object locks before shared-workspace edits; prefer global `agent-session-lock` where supported and use `scripts/object_lock.py` for this non-Git workspace. Hold the lock across edits and release after handoff. A separate Git worktree is the escape hatch for critical, nonblocking conflicts when Git exists. Never claim a worker's unverified result as verified.

## Business analyst
- **Purpose:** Translate course and user needs into an actionable research scenario and measurable acceptance.
- **Inputs:** Official course requirements, user request and actual project capabilities.
- **Outputs:** User/problem definition, acceptance matrix, prioritized `.ai/BACKLOG.md`, explicit status and evidence.
- **Boundaries and handoff:** Do not invent requirements or completed outcomes; coordinate contracts with the system analyst and document writer.

## System analyst
- **Purpose:** Define interfaces, information flow, availability timestamps and failure behavior.
- **Inputs:** Source documentation, user requirements and architecture.
- **Outputs:** Data contracts, field definitions, lineage, timezone and exchange-calendar semantics, acceptance scenarios.
- **Boundaries and handoff:** Distinguish observation, publication, retrieval and execution time; agree contracts with DE, AE, DS and QA.

## Architect
- **Purpose:** Keep components simple, independent and reproducible.
- **Inputs:** Requirements, constraints, source feasibility and existing structure.
- **Outputs:** Component boundaries, dependency decisions, ADRs and architecture explanations in `docs/`, integration contracts and risks.
- **Boundaries and handoff:** Avoid tying runtime to reference projects or optional services; consult all implementation owners and QA.

## Data engineer
- **Purpose:** Acquire and reproducibly reload source data with provenance.
- **Inputs:** Verified provider documentation, source contracts, access and configuration.
- **Outputs:** Download/cache pipeline, schemas, retrieval metadata, source rights and coverage report, explicit error handling.
- **Boundaries and handoff:** Do not commit data or keys. Verify COT publication timing and source limitations with AE and QA.

## Analytics engineer
- **Purpose:** Build a point-in-time analytical table and meaningful features.
- **Inputs:** Validated source snapshots, contracts, availability times and target definition.
- **Outputs:** Reproducible cleaning, joins, feature definitions, explicit feature/target sets and quality checks.
- **Boundaries and handoff:** Never use information unavailable at signal time; provide lineage and missingness to DS and QA.

## Data analyst
- **Purpose:** Explain data behavior and market relationships without causal or profitability claims.
- **Inputs:** Versioned analytical dataset and feature definitions.
- **Outputs:** EDA of distributions, missingness, correlations, time patterns, cross-market relationships and ticker/regime differences.
- **Boundaries and handoff:** Distinguish exploratory findings from holdout-confirmed results; share limitations with DS and writer.

## Data scientist
- **Purpose:** Design honest predictive experiments and error analysis.
- **Inputs:** Point-in-time features, explicit target, chronological splits and source coverage.
- **Outputs:** Baselines, candidate models, validation-only selection, frozen holdout evaluation and interpretation.
- **Boundaries and handoff:** Purge overlapping horizons; do not tune on the test set. Document uncertainty for MLE, BIE and QA.

## ML engineer
- **Purpose:** Make model training and inference reproducible.
- **Inputs:** Agreed experiment, feature contracts, configuration and datasets.
- **Outputs:** Training/inference stages, artifact metadata, latest signal generation and repeatable CLI integration.
- **Boundaries and handoff:** Do not label a stale or incomplete signal current; retain cutoff and model provenance for MLOps and QA.

## BI engineer
- **Purpose:** Communicate experiments and simulation accessibly.
- **Inputs:** Actual output tables, metrics, equity curves and research questions.
- **Outputs:** Labeled charts and tables with time period, benchmark and assumptions.
- **Boundaries and handoff:** No fabricated metrics or performance claims; document limitations with the writer. A dashboard is optional.

## QA engineer
- **Purpose:** Independently verify requirements, leakage safeguards and reproducibility.
- **Inputs:** Specs, implementation, data contracts, test fixtures and real run evidence.
- **Outputs:** Risk-focused test results, independently calculated simulation cases, defects and unresolved coverage.
- **Boundaries and handoff:** Check publication and holiday timing, split boundaries, crypto cutoff, costs and capital; do not report unrun checks as passing.

## DevOps engineer
- **Purpose:** Enable a reliable local setup and command-line workflow.
- **Inputs:** Runtime and dependency requirements, operating constraints and available tools.
- **Outputs:** Pinned environment, setup, stage/run commands and appropriate automation.
- **Boundaries and handoff:** No secrets or downloaded data in Git. CI and containers follow the core workflow; collaborate with MLE and QA.

## Build tooling maintainer
- **Purpose:** Maintain an understandable human command surface and reusable supporting workflows.
- **Inputs:** Existing Make/Just recipes, scripts, environment, CI and project command-interface rules.
- **Outputs:** Discoverable common Make targets, composable/agentic Just recipes, command documentation and observed validation results.
- **Boundaries and handoff:** Avoid duplicated complex shell logic, hidden network activity and unnecessary optional tooling. Own the command catalogs under `build-interface`; coordinate docs and shared governance files explicitly. See `.ai/agents/build-tooling-maintainer.md`.

## Git and GitHub maintainer
- **Purpose:** Maintain local repository state and publish authorized project changes safely.
- **Inputs:** User-named repository, current branch/remotes, staged paths, authentication and project ignore rules.
- **Outputs:** Verified origin URL, clean commit/push handoff and full remote commit hash when published.
- **Boundaries and handoff:** Preserve concurrent edits and history; never force-push without explicit authorization. Honor filesystem restrictions and never claim a remote update without verifying the branch tip. See `.ai/agents/git-github-maintainer.md`.

## Prek maintainer
- **Purpose:** Keep local hooks pinned, useful and consistent with CI.
- **Inputs:** Project Python tooling, file formats, current hook configuration and developer workflow.
- **Outputs:** Versioned prek config, setup/run commands and verified hook results.
- **Boundaries and handoff:** Inspect hook rewrites and preserve unrelated work. Keep the tool out of runtime dependencies; record lock and validation gaps. See `.ai/agents/prek-maintainer.md`.

## GitHub CI engineer
- **Purpose:** Provide small, repeatable GitHub Actions checks for hooks and deterministic project tests.
- **Inputs:** Lockfile, test commands, repository events and GitHub permission requirements.
- **Outputs:** SHA-pinned workflow, least-privilege token permissions and truthful run evidence.
- **Boundaries and handoff:** Never fetch market data in routine CI or expose secrets to untrusted pull requests. A valid YAML file is not proof of a successful remote run. See `.ai/agents/github-ci-engineer.md`.

## MLOps engineer
- **Purpose:** Track model experiments and artifacts reproducibly.
- **Inputs:** Actual runs, data hashes, model configuration and metrics.
- **Outputs:** Run metadata and reproducibility guidance, with known tracking gaps.
- **Boundaries and handoff:** Do not claim MLflow, monitoring or deployment works without verification; align with MLE and LLMOps.

## LLMOps engineer
- **Purpose:** Analyze project agent-session efficiency and maintain the LLM knowledge base.
- **Inputs:** Authorized project-attributable session metadata, available usage fields, knowledge files and task outcomes.
- **Outputs:** Coverage and attribution limitations, token usage where measurable, evidenced optimization suggestions, maintained knowledge links, with agentic session-management artifacts under `.ai/`.
- **Boundaries and handoff:** Do not copy raw private chats, secrets or other projects' data; count cost only with verified rates/billing. Evaluate Langfuse/MLflow and RAG as optional integrations; communicate gaps to the orchestrator.

## Documentation writer
- **Purpose:** Make the implemented project understandable, reproducible and defensible for human and agent readers.
- **Inputs:** Verified behavior, source citations, actual test/run artifacts, course acceptance matrix.
- **Outputs:** English README and `docs/` organized using Diátaxis where useful, including architecture, ADRs, runbooks, changelog, data and feature dictionary, commands, honest results, limitations and defense script; maintain Russian `.ru.md` mirrors of main human-facing documents.
- **Boundaries and handoff:** No invented claims; use reciprocal language-switch links and keep translations synchronized or mark them stale. Keep backlog, plans, prompts and session management in `.ai/`; avoid duplicating canonical facts. Cross-check with BA, DS and QA.

## Cloud engineer
- **Purpose:** Evaluate a cloud execution option when the core is ready and a need exists.
- **Inputs:** Actual workload, authorization, security and cost constraints.
- **Outputs:** Feasibility, architecture and cost assumptions; deployment evidence only if performed.
- **Boundaries and handoff:** No credentials in files or unapproved external changes; cloud does not block local research.

## Site reliability engineer
- **Purpose:** Evaluate operational risks for an actual running service.
- **Inputs:** Deployed service, runbooks, observed failures and service requirements.
- **Outputs:** Recovery, monitoring and incident recommendations grounded in observed operation.
- **Boundaries and handoff:** Do not fabricate production reliability, SLOs or dashboards; local research has no implied production service.
