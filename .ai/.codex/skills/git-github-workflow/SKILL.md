---
name: git-github-workflow
description: Work with local Git branches, remotes, commits, GitHub repositories, and published commit hashes. Use when a task requires setting an origin, pushing project changes, or inspecting repository state.
---

# Git and GitHub workflow

1. Read `AGENTS.md`, inspect `git status`, current branch, remotes, ignore rules, and active object locks before changing files or Git state. Preserve uncommitted user changes and other sessions' work.
2. Use the repository's lock workflow for shared edits. In non-Git/partially initialized workspaces, do not infer that `git init` means the current branch has commits or that a remote exists.
3. Set `origin` to the URL the user named. Preserve an already-correct origin. If `.git/config` is not writable, honor that restriction and report the exact command the user can run; do not hide metadata elsewhere and claim it changed the current repo.
4. Before pushing, inspect the remote repository and branch history. Preserve existing commits and use fast-forward updates. Never force-push, delete branches, or replace unrelated content without explicit authorization.
5. Review the staged file list. Exclude secrets, environments, caches, downloaded data, generated outputs, private logs, and unrelated files. Do not reveal credentials in output.
6. After a push, verify the remote branch tip and report the HTTPS URL and full commit hash. A local commit or configured remote alone does not prove publication.

For create/update publication and form-ready commit hashes, use [upsert-repo-and-get-hashid](../upsert-repo-and-get-hashid/SKILL.md).
