---
name: project-session-wrap-up
description: Summarize this project's current work, published Git state, active sessions, scheduled commit/push task, and concrete next steps before handoff or finalization.
---

# Project session status and wrap-up

Use when the user asks where the project stands, what remains, or whether a session can be finalized. Also use after a requested commit/push workflow when the result needs a clear handoff.

1. Read `AGENTS.md`, `.ai/IMPLEMENTATION_PLAN.md`, `.ai/RULES.md`, relevant roles, project memory, and the capstone spec. Load the Git/GitHub workflow and periodic commit/push guidance when publication or scheduling is involved.
2. Inspect `git status --short --branch`, current branch and upstream, origin URL, recent commits, and `git rev-list --left-right --count origin/main...HEAD`. Report local-ahead commits separately from the verified remote tip. Use `git ls-remote` when reachable; never present a local hash as a published hash.
3. Inspect `.ai/.locks/*/owner.json` before proposing commits or edits. Preserve files under active locks. Do not treat the existence of another session's lock as stale or release it. A scheduled commit task should wait while project locks are held.
4. If a periodic LaunchAgent is part of the task, inspect its plist and `launchctl print gui/$(id -u)/<label>`. Confirm its executable and script paths point into the current project checkout, check its interval, and distinguish `state = not running` before the first interval from failure. Do not manually invoke a scheduled cycle just to inspect it, since it may commit and push.
5. Give a concise handoff with: completed and verified work; uncommitted changes and their owners; local commits not yet pushed; installed automation state; the smallest concrete next actions; and any blockers. Say the session is ready to finalize only when no requested work or required handoff remains.

6. Distinguish project completion from session completion. State which work is actually verified, what is still in the backlog, what is pending in this session, and whether another session owns an active lock. A session can be finalized while the project has backlog, but not while this session has an outstanding requested action or unhanded-off changes.

7. If the user invoked `$smart-commit-and-push` or otherwise explicitly authorized publication, treat that as authorization to push the requested commit(s); do not ask a second generic “push?” question. Still resolve commit scope safely: inspect staged, unstaged and untracked paths; exclude secrets and unrelated concurrent work. If there are no staged paths but relevant unstaged changes exist and the command's flags do not authorize staging them, ask one concise scope question before changing the index. Do not imply a commit or push occurred while awaiting that choice. Report any local-ahead commit separately from the uncommitted work.

Preserve existing authorization boundaries. A request to summarize state does not authorize committing, pushing, force-pushing, installing or removing a LaunchAgent, or changing files owned by another session. If the user explicitly requested publication, use the Git/GitHub workflow, review exact staged paths, honor local filesystem/network restrictions, and verify the remote tip after push. Never claim the scheduler is installed merely because its installer exists, or claim it has run before its first interval.
