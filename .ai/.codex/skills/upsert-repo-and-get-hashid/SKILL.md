---
name: upsert-repo-and-get-hashid
description: Create or update a GitHub repository from the current project and return its canonical URL and latest commit hash. Use when asked to share/publish a project repo or provide a commit ID for a form.
---

# Upsert repository and return commit hash

Publish the requested project to the explicitly named GitHub owner/repository, then report its full URL and the full hash of the commit at the published branch tip.

1. Read the project instructions and inspect the workspace, Git status, remotes, ignore rules, and GitHub authentication. Preserve existing user changes. Never overwrite a remote branch or replace unrelated repository contents without first understanding the divergence. When asked to set `origin`, preserve an already-correct remote; replace a different URL only when the user explicitly names the desired target.
2. If the workspace is not a Git repository, initialize it only when the user has asked to publish this project. Review the complete candidate file list and exclude secrets, credentials, local environments, caches, downloaded data, generated artifacts, private logs, and unrelated files. Keep project source, documentation, and required lockfiles.
3. If Git metadata is read-only, do not route around filesystem restrictions; report that the local remote could not be saved and give the user the exact `git remote add origin <url>` command. If GitHub auth or network access is unavailable, stop before any remote mutation and explain the exact blocker. Do not claim that a repo was created or pushed.
4. For an existing remote, inspect its visibility and default branch before updating. Preserve history and use normal fast-forward pushes; never force-push unless the user explicitly authorizes replacement. For a missing remote, create it with the requested visibility; when the user says “shared” without further detail, use public visibility, unless organization policy or repo state indicates otherwise.
5. Create a clear commit only for the project changes intended for publication. Prefer the authenticated GitHub user's noreply commit email over exposing a personal email. Set and verify `origin` when requested, push the intended branch, then obtain the full HEAD commit hash from the remote; the local hash alone does not prove publication.
6. Return the full HTTPS repository URL and full published commit hash. State the branch and whether publication was verified. If blocked, give the URL only if it is verified and do not invent a commit ID.

Do not create issues, releases, tags, pages, or other GitHub resources unless separately requested.
