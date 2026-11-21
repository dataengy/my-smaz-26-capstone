#!/usr/bin/env python3
"""Check relative links and heading anchors in repository Markdown files."""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
LINK_RE = re.compile(r"!?\[[^\]]*\]\((<[^>]+>|[^)]+)\)|^\[[^\]]+\]:\s*(\S+)", re.MULTILINE)
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)
HTML_ANCHOR_RE = re.compile(r"<(?:a|[^ >]+)[^>]*\bid=[\"']([^\"']+)[\"']", re.IGNORECASE)
CODE_FENCE_RE = re.compile(r"^\s*(```+|~~~+).*?^\s*\1\s*$", re.MULTILINE | re.DOTALL)


def slugify(heading: str) -> str:
    heading = re.sub(r"`([^`]*)`", r"\1", heading)
    heading = re.sub(r"<[^>]+>", "", heading)
    heading = unicodedata.normalize("NFKC", heading).casefold()
    heading = "".join(ch for ch in heading if ch in " -_" or ch.isalnum())
    return heading.replace(" ", "-").strip("-")


def anchors_for(path: Path) -> set[str]:
    text = CODE_FENCE_RE.sub("", path.read_text(encoding="utf-8"))
    counts: dict[str, int] = {}
    anchors: set[str] = set()
    for heading in HEADING_RE.findall(text):
        base = slugify(heading)
        count = counts.get(base, 0)
        counts[base] = count + 1
        anchors.add(base if count == 0 else f"{base}-{count}")
    anchors.update(HTML_ANCHOR_RE.findall(text))
    return anchors


def markdown_files() -> list[Path]:
    excluded = {".git", ".run", ".venv", ".worktrees"}
    return sorted(
        p for p in ROOT.rglob("*.md")
        if not any(part in excluded for part in p.relative_to(ROOT).parts)
    )


def check() -> list[str]:
    errors: list[str] = []
    files = markdown_files()
    for source in files:
        text = CODE_FENCE_RE.sub("", source.read_text(encoding="utf-8"))
        for match in LINK_RE.finditer(text):
            raw = (match.group(1) or match.group(2) or "").strip()
            target = raw[1:-1] if raw.startswith("<") and raw.endswith(">") else raw
            target = target.split(maxsplit=1)[0] if target else target
            parts = urlsplit(target)
            if parts.scheme or target.startswith("//"):
                continue
            line = text.count("\n", 0, match.start()) + 1
            if not parts.path:
                linked = source
            elif parts.path.startswith("/"):
                # Site-root links are not filesystem-relative; validate them from repository root.
                linked = ROOT / unquote(parts.path.lstrip("/"))
            else:
                linked = (source.parent / unquote(parts.path)).resolve()
            if not linked.exists():
                errors.append(f"{source.relative_to(ROOT)}:{line}: missing target {target}")
                continue
            if parts.fragment:
                anchor = unquote(parts.fragment)
                if anchor not in anchors_for(linked):
                    errors.append(f"{source.relative_to(ROOT)}:{line}: missing heading #{anchor} in {linked.relative_to(ROOT)}")
    return errors


def main() -> int:
    errors = check()
    if errors:
        print("Markdown link check failed:", file=sys.stderr)
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Markdown local links passed ({len(markdown_files())} files checked).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
