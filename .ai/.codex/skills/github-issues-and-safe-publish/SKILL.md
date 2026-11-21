---
name: github-issues-and-safe-publish
description: Synchronize this capstone's backlog with GitHub Issues, safely commit/publish authorized changes, and hand off current status and remaining work.
---

# GitHub issue sync and safe publication

Use when asked to update this project's GitHub Issues, run `$smart-commit-and-push`, or summarize where that combined workflow stands. Load and follow the project `project-github-tracker` and `git-github-workflow` skills plus the invoked smart-commit skill; this skill connects their sequence and stop conditions. For a status/finalization request, also use `project-session-wrap-up`.

1. Read `AGENTS.md`, `.ai/RULES.md`, current status/backlog/bug evidence, and the required GitHub workflow guidance. Check exact object locks and current worktree ownership before changing tracker files or publishing.
2. Treat `.ai/BACKLOG.md` and `.ai/BUGS.md` as canonical. Read existing repository issues and match stable backlog/bug keys before editing or creating issues. Upsert by stable key: update the matching issue's title/body/labels as needed, retaining its issue number and URL; create only when no matching key exists. Exact-title matches without the stable key are candidates to inspect, not sufficient evidence for an update. Never close or mark work Done without local evidence. Keep tracker URLs and state aligned in the local canonical record.
3. If the backlog tracker or any requested files are locked by another session, do not perform overlapping issue or file writes. Continue with independent read-only checks, then hand off the exact lock owner and deferred operations.
4. For `$smart-commit-and-push`, obey its scope and check prompts/defaults. Without `-a`/`--commit-all`, do not stage arbitrary unstaged changes. Even with broad scope authorization, exclude files owned by another session, secrets, generated data and unrelated changes. Review the exact staged paths and branch before committing.
5. Do not commit directly to `main` or rewrite published history unless project instructions and the user's request clearly authorize it. Never force-push. If Git metadata is read-only, the branch is behind without a safe update path, or push cannot be verified, stop without changing permissions or inventing alternate Git state.
6. Resolve CI from `origin`: use GitHub Actions for a GitHub remote even if a generic commit skill mentions GitLab. Report actual observed checks; do not claim a push or pipeline succeeded without verification.
7. Diagnose GitHub failures by layer. A connector write `403` indicates missing integration permission; a `gh` API connection failure indicates API reachability. These do not by themselves prove invalid credentials. Do not switch accounts, refresh tokens, widen permissions, or repeatedly retry. Use authenticated UI only when available; otherwise hand off the precise blocked action.
8. For status or finalization, separate project backlog from actions still outstanding in this session. State the verified current branch/PR/issue state, active lock owner, changed files and publication state; list the smallest next steps in dependency order. Say the session is ready to finalize only after requested writes are complete or explicitly handed off and changed files have a clear owner.

## Session-end reminder hook

The repository's `.claude/settings.local.json` registers `scripts/session-hooks/github-issue-upsert-hook.sh` for `SessionEnd`. It prints a reminder when `.ai/BACKLOG.md` or `.ai/BUGS.md` changed compared with `HEAD`. The hook never calls GitHub or edits issues; perform the upsert explicitly through the shared integration and update the local tracker URLs.

Report changed issue IDs/URLs, local tracker edits, exact commit scope, validation, published branch/commit, CI status, and any operation deferred because of locks, permissions or network access. Answer directly whether to continue or finalize.
