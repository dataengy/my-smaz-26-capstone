---
name: project-github-tracker
description: Manage this capstone's implementation backlog and defects through GitHub Issues and a GitHub Projects v2 kanban board while keeping local evidence authoritative.
---

# Project GitHub tracker

Use GitHub Issues for actionable work and GitHub Projects v2 for kanban visualization. This project's `.ai/BACKLOG.md` and `.ai/BUGS.md` remain the canonical context and evidence records. Do not use Linear for this project unless the user explicitly changes the tracker choice.

## Preconditions

- The project has a GitHub repository configured in `.ai/settings/github.env` or discoverable from its `origin` remote.
- `gh auth status` succeeds for that repository. Projects v2 requires the `project` scope.
- The GitHub Projects integration is available at `~/.ai/integrations/github/Justfile`.
- If either precondition is missing, work locally and report the exact setup blocker. Do not guess a repository, owner, project number, credentials or remote.

## Mapping

- Each meaningful open backlog task maps to one issue, with a stable reference such as `BACKLOG: P0 — Restore and verify source access` in the issue body and a link to the local backlog path. Include the acceptance criteria and relevant spec/evidence links.
- Each bug maps to one issue titled with its stable `BUG-NNN` ID. Link the bug register entry and capture the verified reproduction and acceptance check.
- Add implementation issues to the project board. Use its existing Status field/options; do not create duplicate status fields.
- Keep labels minimal: `backlog`, `bug`, and priority labels only when useful. Avoid duplicating project taxonomy as labels.
- Do not mark an issue/board item Done until the local acceptance evidence is recorded. Reflect blocked work with a blocked status/label and a concise blocker.
- Keep `BACKLOG.md`/`BUGS.md` synchronized when priorities, status or acceptance evidence change. Store tracker URLs beside the relevant entries when available.

## Workflow

1. Read `.ai/BACKLOG.md`, `.ai/BUGS.md`, `.ai/STATUS.md`, and the referenced implementation/spec evidence. Inspect existing issues and board items before creating anything; update matching records instead of duplicating them.
2. Use the shared integration, for example:

   ```sh
   just -f ~/.ai/integrations/github/Justfile issue-list --state all
   just -f ~/.ai/integrations/github/Justfile project-list
   just -f ~/.ai/integrations/github/Justfile project-fields <number>
   just -f ~/.ai/integrations/github/Justfile issue-create --title "..." --body-file <file> --label backlog
   just -f ~/.ai/integrations/github/Justfile project-add <number> --issue <issue-number> --status Todo
   ```

3. Use Markdown links in issue bodies to local repo files and relevant specs. Never include credentials, market-data contents, raw private session logs or unrelated private project data.
4. For every changed record, update the local canonical entry with its issue URL and status/evidence as appropriate. Report IDs/URLs and any item left local-only.

## Initial setup

Before any write to GitHub, inspect `~/.ai/integrations/github/README.md` and the project's repo state. A repository without a remote and an unauthenticated `gh` cannot receive issues or a board. Ask the user to configure/authorize the repository only after preparing a concrete proposed task set and mappings. Never create a public repository or change visibility as part of tracker setup.
