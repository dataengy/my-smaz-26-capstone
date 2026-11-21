---
name: git-github-workflow
description: Work with local Git branches, remotes, commits, GitHub repositories, and published commit hashes. Use when a task requires setting an origin, pushing project changes, or inspecting repository state.
---

# Git and GitHub workflow

1. Read `AGENTS.md`, inspect `git status`, current branch/upstream, remotes, ignore rules, and active object locks before changing files or Git state. Preserve uncommitted user changes and other sessions' work. Distinguish staged, unstaged, untracked and already-unpushed commits.
2. Use the repository's lock workflow for shared edits. In non-Git/partially initialized workspaces, do not infer that `git init` means the current branch has commits or that a remote exists.
3. Set `origin` to the URL the user named. Preserve an already-correct origin. If `.git/config` is not writable, honor that restriction and report the exact command the user can run; do not hide metadata elsewhere and claim it changed the current repo.
4. Before pushing, inspect the remote repository and branch history. Preserve existing commits and use fast-forward updates. Never force-push, delete branches, or replace unrelated content without explicit authorization.
5. Resolve the commit set from the invocation and the user's explicit scope. With a smart-commit skill that defaults to staged files, do not silently stage every unstaged path; if relevant changes are unstaged and no flag or explicit instruction covers them, ask whether to stage all safe changes or only named paths. Review the exact paths to be committed. Exclude secrets, environments, caches, downloaded data, generated outputs, private logs, and unrelated/concurrently owned files. Do not reveal credentials in output. Never include local `*.env` settings just because they are untracked.
6. Run the project's relevant full validation before committing. Summarize results and skips precisely; do not bypass a failing check unless the user explicitly overrides it.
7. Review all local-ahead commits before push. Prefer a message-only correction for a weak subject. If history rewriting is required, show the proposed rewrite and obtain the confirmation required by the active smart-commit workflow. Never rewrite already-published commits or force-push without explicit authorization.
8. An explicit `$smart-commit-and-push` invocation authorizes the requested push; do not repeat a generic push-confirmation prompt after its required scope/rewrite decisions are resolved. Preserve normal network and filesystem constraints. If push fails, report the exact stage and leave local commits intact.
9. After a push, verify the remote branch tip and report the HTTPS URL and full commit hash. A local commit or configured remote alone does not prove publication. Open the CI page for the repository's actual host and workflow; do not assume GitLab when origin and workflow are GitHub Actions, or vice versa.

For create/update publication and form-ready commit hashes, use [upsert-repo-and-get-hashid](../upsert-repo-and-get-hashid/SKILL.md).
