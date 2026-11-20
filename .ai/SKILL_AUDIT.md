# Skill audit

Initial file-presence audit, 2026-11-20. Presence is not proof that a skill fits this project, has been invoked, or that project skill discovery works. Read each relevant `SKILL.md` and check project-specific assumptions before use.

| Capability | Installed candidate | Project decision |
|---|---|---|
| Planning, delegation, debugging and verification | Superpowers 7.0.1: `writing-plans`, `dispatching-parallel-agents`, `systematic-debugging`, `verification-before-completion` | Use relevant skills when their workflows apply; follow higher-priority user and system instructions. |
| Shared-session exclusion and handoff | Global `agent-session-lock`, `sync-with-parallel-session`, and `sync-with-parallel-session-and-go-on` | Prefer object locks. The global lock helper requires a Git worktree; use the project `scripts/object_lock.py` fallback in this non-Git workspace. |
| Isolated concurrent work | Superpowers 7.0.1: `using-git-worktrees` | Use only for critical work that cannot wait on a shared object lock, when Git exists. Never run concurrent writers in the same worktree. |
| Minimal complete implementation and review | Ponytail 5.3.3: `ponytail`, `ponytail-review` | Use where applicable without omitting required research or safety checks. |
| Data quality and EDA | Global `data-validation`, `data-profiler`; data-analytics `visualize-data` | Check suitability and project-specific dependencies before use. |
| Session inspection | Global `codex-logs-maintainer` | Inspect scope and behavior before use; never assume its output covers every project session. |
| Review | Global `check-and-refine` | Use only if instructions fit this task and environment. |
| Human and agent command interface | Global `make-just-manager` | Read and applied for this change; its command catalog and linter references informed the Makefile/Justfile split. Project-specific follow-up is `.ai/.codex/skills/build-command-interface/SKILL.md`. |
| COT, finance backtesting, acceptance, session accounting, SDD, docs, parallel coordination | Project drafts under `.ai/.codex/skills/` | Read explicitly by path; discovery, behavioral tests and deployment are unverified. |

The global `just-setup-inspector` was inspected and not applied: its focus is setup shell scripts, while this change organizes project command recipes. No global skill installation or mutation was needed.

No global installation is necessary solely on the basis of this audit. If a proven capability gap remains after reviewing candidates, propose a specific skill and install it only using authorized repository tooling. Do not edit global installed skills directly. The OpenSpec CLI is a separate tool, not an installed skill, and was not found on PATH in the initial inspection.
