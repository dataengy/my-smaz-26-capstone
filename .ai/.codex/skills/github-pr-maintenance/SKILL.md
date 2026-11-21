---
name: github-pr-maintenance
description: Inspect, update, validate, and merge pull requests for this repository when explicitly requested.
---

# GitHub pull request maintenance

Use this skill for existing PR review, metadata updates, branch publication, and requested merges. Follow the repository's `AGENTS.md`, `.ai/.codex/skills/git-github-workflow/SKILL.md`, and `.ai/agents/git-github-maintainer.md` for local state, locks, and publication safeguards.

1. Confirm the origin host and repository, target PR, head branch/SHA, base branch, worktree state, and whether the PR already exists. Inspect changed paths, reviews, mergeability, and available CI checks before changing anything.
2. Preserve concurrent work. Push only commits intentionally included in the PR; never stage unrelated dirty files, force-push, or delete branches unless explicitly requested. Do not include secrets or local environment files.
3. Update title/body only when requested or when needed to make the requested PR actionable. Describe actual scope and verified checks; label checks not run. Do not imply that a branch push updated PR metadata.
4. For a requested merge, verify the PR is open, mergeable, review requirements are satisfied, and required checks have completed successfully. Use the repository's documented merge convention; if none is discoverable, prefer squash for a short-lived feature branch unless the user specified another method. Pass the observed head SHA when the API supports it, so a moving PR cannot be merged accidentally.
5. Diagnose access failures by layer. A GitHub connector `403 Resource not accessible by integration` means that connector lacks the needed write permission; it does not prove the user's CLI token is invalid. Check `gh auth status` without printing credentials, then make at most one small `gh api` or `gh pr` retry. If the CLI cannot connect to `api.github.com`, treat that as API/network reachability, separate from Git push connectivity. Do not repeatedly retry, switch accounts, alter credential/configuration, or request broader permissions without user direction.
6. If authenticated CLI/API writes are unavailable, use the already-authenticated GitHub UI only if browser access is available. Otherwise leave the PR unchanged, report the exact failure, and give the direct PR link and smallest manual action. Never claim an update or merge succeeded without verifying PR state afterward.

Report the PR URL, branch and head SHA, changed paths at a high level, observed checks/reviews, operations that succeeded, and any remaining blocker. Do not expose token values, private logs, or local credential contents.
