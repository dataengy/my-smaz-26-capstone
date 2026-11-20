---
name: parallel-session-coordination
description: Coordinate Codex sessions editing this shared capstone workspace with advisory object locks, handoffs, and isolated worktrees when available.
---

# Parallel session coordination

## Default: lock the object

1. Read `AGENTS.md`, `.ai/RULES.md`, the relevant role and spec, and this project's parallel prompt catalog.
2. Inspect active sessions and check the exact files or interface contract you intend to change. Keep one owner per writable object; divide unrelated objects among sessions.
3. Use the global `agent-session-lock` skill when its repository-backed helper applies. It supports per-object locks and provides owner metadata. This workspace currently has no Git repository, so use `python3 scripts/object_lock.py`:

   ```sh
   python3 scripts/object_lock.py acquire <object-slug> --session-id <stable-session-id> --reason "<scope>"
   python3 scripts/object_lock.py check <object-slug> --session-id <stable-session-id>
   python3 scripts/object_lock.py release <object-slug> --session-id <stable-session-id>
   ```

4. If acquisition reports `HELD`, read the owner and coordinate the handoff; do not write those files. Locks are advisory and never expire automatically. Do not remove another session's lock based on age. A missing or malformed owner record also blocks edits until the owner is identified and the lock is deliberately recovered.
5. Keep the lock while editing and verifying the claimed object. Release only your lock after handing off changed paths, checks, evidence, risks and unresolved interface changes.

## Critical work that cannot wait

Use a separate Git worktree only when a critical change cannot wait on the object lock and a Git repository is available. Follow the global Superpowers `using-git-worktrees` skill: detect existing isolation, prefer native worktree support, otherwise use an ignored project worktree path. Keep the same object ownership boundaries, do not run concurrent writers in one worktree, and ask the orchestrator to integrate/review the isolated result. If Git or worktree support is unavailable, queue the conflicting edit; do not bypass the lock in the shared checkout.

The global Superpowers `dispatching-parallel-agents` skill applies only to independent tasks with separate writable scopes. Do not parallelize related work that changes a shared contract before the contract owner has agreed it.

## Prompt requirements

Every session prompt must include: role and outcome; exact owned files/objects and lock slug; dependencies and agreed interfaces; files explicitly off-limits; required reads; deliverables and evidence; checks to run or reason they cannot run; and the handoff/release steps. Treat the shared workspace as shared: another session's uncommitted edits belong to that session.
