#!/usr/bin/env python3
"""Cooperative object locks for parallel sessions in a shared project directory.

The lock directory is created atomically. Locks have no automatic expiry: a live
agent session can outlast a fixed TTL. Release only your own lock; resolve stale
locks with the owner/session first.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path


def lock_path(root: Path, object_name: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", object_name):
        raise ValueError("Object name must be a 1-80 character slug")
    return root.resolve() / ".ai" / ".locks" / f"{object_name}.lock"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("acquire", "check", "release"))
    parser.add_argument("object", help="Exact file, component, or integration contract being claimed")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--session-id", required=True, help="Stable ID for this agent session")
    parser.add_argument("--reason", default="")
    args = parser.parse_args()
    try:
        path = lock_path(args.root, args.object)
    except ValueError as exc:
        parser.error(str(exc))
    owner_file = path / "owner.json"

    if args.action == "acquire":
        try:
            path.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            try:
                owner = json.loads(owner_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                owner = {"session_id": "unknown", "reason": "Lock exists but owner metadata is missing or invalid"}
            print(json.dumps({"status": "HELD", "object": args.object, "owner": owner}, indent=2))
            return 1
        owner = {
            "object": args.object,
            "session_id": args.session_id,
            "reason": args.reason,
            "acquired_at": datetime.now(timezone.utc).isoformat(),
            "host": socket.gethostname(),
            "pid": os.getpid(),
        }
        owner_file.write_text(json.dumps(owner, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "ACQUIRED", **owner}, indent=2))
        return 0

    if not path.exists():
        print(json.dumps({"status": "FREE", "object": args.object}))
        return 0
    try:
        owner = json.loads(owner_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        owner = {"session_id": "unknown", "reason": "Lock exists but owner metadata is missing or invalid"}
    if args.action == "check":
        print(json.dumps({"status": "HELD", "object": args.object, "owner": owner}, indent=2))
        return 1
    if owner.get("session_id") != args.session_id:
        print(json.dumps({"status": "NOT_OWNER", "object": args.object, "owner": owner}, indent=2))
        return 1
    owner_file.unlink(missing_ok=True)
    path.rmdir()
    print(json.dumps({"status": "RELEASED", "object": args.object, "session_id": args.session_id}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
