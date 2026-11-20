#!/usr/bin/env python3
"""Claim the first unclaimed session prompt with an available object lock."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / ".ai" / "PARALLEL_SESSION_PROMPTS.md"
LOCK_TOOL = ROOT / "scripts" / "object_lock.py"
SESSION_LOCK = "parallel-prompts"
PROMPT_RE = re.compile(r"^## ([A-P]) — (.+)$", re.MULTILINE)
LOCK_RE = re.compile(r"\block `([A-Za-z0-9_.-]+)`")
CLAIM_RE = re.compile(r"^\|\s*([A-P])\s+—[^|]*\|\s*\*\*(.*?)\*\*", re.MULTILINE)


def run_lock(action: str, slug: str, session_id: str, reason: str = "") -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(LOCK_TOOL), action, slug, "--session-id", session_id]
    if reason:
        command.extend(["--reason", reason])
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True)


def parse_prompts(markdown: str) -> list[tuple[str, str, str]]:
    headings = list(PROMPT_RE.finditer(markdown))
    prompts: list[tuple[str, str, str]] = []
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(markdown)
        body = markdown[heading.end():end]
        lock_match = LOCK_RE.search(body)
        if lock_match:
            prompts.append((heading.group(1), heading.group(2).strip(), lock_match.group(1)))
    return prompts


def insert_claim(markdown: str, letter: str, title: str, session_id: str) -> str:
    separator = "|---|---|---|---|---|\n"
    if separator not in markdown:
        raise ValueError("Prompt claim table header was not found")
    row = (
        f"| {letter} — {title} | **In progress** | Session (`{session_id}`) | "
        f"{date.today().isoformat()} | Claim recorded by `just take-next-prompt`; handoff pending |\n"
    )
    existing = re.compile(rf"^\|\s*{letter}\s+—[^|]*\|[^\n]*\n?", re.MULTILINE)
    if existing.search(markdown):
        return existing.sub(row, markdown, count=1)
    return markdown.replace(separator, separator + row, 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session-id", required=True, help="Stable ID for this session")
    parser.add_argument("--dry-run", action="store_true", help="Show the next eligible prompt without claiming it")
    args = parser.parse_args()

    catalog_lock_acquired = False
    prompt_lock_acquired = False
    prompt_slug = ""
    try:
        if not args.dry_run:
            result = run_lock("acquire", SESSION_LOCK, args.session_id, "Select and record next unclaimed prompt")
            if result.returncode:
                print(result.stdout or result.stderr, end="", file=sys.stderr)
                return result.returncode
            catalog_lock_acquired = True

        markdown = PROMPTS.read_text(encoding="utf-8")
        claimed = {letter: status.casefold() for letter, status in CLAIM_RE.findall(markdown)}
        candidates = [
            prompt for prompt in parse_prompts(markdown)
            if prompt[0] not in claimed
            or claimed[prompt[0]] in {"available", "unclaimed", "open"}
        ]

        for letter, title, lock_slug in candidates:
            lock_path = ROOT / ".ai" / ".locks" / f"{lock_slug}.lock"
            if lock_path.exists():
                continue
            if args.dry_run:
                print(f"Next prompt: {letter} — {title}\nLock: {lock_slug}\nSession: {args.session_id}")
                return 0

            reason = f"Prompt {letter}: {title}"
            result = run_lock("acquire", lock_slug, args.session_id, reason)
            if result.returncode:
                # The lock may have been taken outside the catalog protocol; try the next candidate.
                continue
            prompt_lock_acquired = True
            prompt_slug = lock_slug
            updated = insert_claim(markdown, letter, title, args.session_id)
            PROMPTS.write_text(updated, encoding="utf-8")
            print(f"Claimed prompt {letter} — {title}\nLock: {lock_slug}\nSession: {args.session_id}")
            print("Prompt catalog status: In progress")
            return 0

        print("No unclaimed prompt with a free object lock is available.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        if prompt_lock_acquired:
            run_lock("release", prompt_slug, args.session_id)
        print(f"Cannot claim next prompt: {exc}", file=sys.stderr)
        return 1
    finally:
        if catalog_lock_acquired:
            run_lock("release", SESSION_LOCK, args.session_id)


if __name__ == "__main__":
    raise SystemExit(main())
