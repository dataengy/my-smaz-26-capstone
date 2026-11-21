#!/usr/bin/env python3
"""Install or run a guarded macOS LaunchAgent for periodic commit and push."""

from __future__ import annotations

import argparse
import os
import plistlib
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LABEL = "club.datatalks.my-smaz-26-capstone.periodic-commit-push"
EXPECTED_ORIGIN = "https://github.com/dataengy/my-smaz-26-capstone.git"
MAX_FILE_BYTES = 1024 * 1024
BLOCKED_PARTS = {
    ".aws", ".ssh", ".run", ".venv", "venv", "data", "artifacts",
    "credentials", "secrets", "__pycache__", ".pytest_cache", "node_modules",
}
BLOCKED_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=check, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def message(text: str) -> None:
    print(f"periodic-commit-push: {text}", flush=True)


def changed_paths() -> list[tuple[str, str]]:
    raw = git("status", "--porcelain=v1", "-z", "--untracked-files=all").stdout
    entries = raw.split(b"\0")
    result: list[tuple[str, str]] = []
    index = 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if not entry:
            continue
        if len(entry) < 4 or entry[2:3] != b" ":
            raise RuntimeError("Could not parse `git status`; refusing to stage changes")
        state = os.fsdecode(entry[:2])
        path = os.fsdecode(entry[3:])
        if "R" in state or "C" in state:
            # The next NUL record contains the other side of the rename.
            index += 1
            raise RuntimeError(f"Rename detected at {path!r}; commit it manually")
        result.append((state, path))
    return result


def check_path(path_text: str) -> str | None:
    path = Path(path_text)
    lowered = path.as_posix().lower()
    parts = {part.lower() for part in path.parts}
    if any(part in BLOCKED_PARTS for part in parts):
        return f"protected path {path_text!r}"
    if any(part.startswith(".env") for part in parts):
        return f"environment file {path_text!r}"
    if any("secret" in part or "credential" in part for part in parts):
        return f"sensitive-looking path {path_text!r}"
    if path.suffix.lower() in BLOCKED_SUFFIXES:
        return f"key or certificate file {path_text!r}"
    if lowered.endswith((".sqlite", ".sqlite3", ".db")):
        return f"database file {path_text!r}"
    full_path = ROOT / path
    if full_path.exists() and full_path.is_file() and full_path.stat().st_size > MAX_FILE_BYTES:
        return f"file over 1 MiB: {path_text!r}"
    return None


def locked_objects() -> list[Path]:
    lock_root = ROOT / ".ai" / ".locks"
    if not lock_root.is_dir():
        return []
    return sorted(path for path in lock_root.glob("*.lock") if path.is_dir())


def verify_repo() -> None:
    branch = git("branch", "--show-current").stdout.decode().strip()
    upstream = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}").stdout.decode().strip()
    origin = git("remote", "get-url", "origin").stdout.decode().strip()
    if branch != "main" or upstream != "origin/main":
        raise RuntimeError("expected branch main tracking origin/main")
    if origin.rstrip("/") != EXPECTED_ORIGIN:
        raise RuntimeError(f"origin is {origin!r}, expected {EXPECTED_ORIGIN!r}")
    if git("diff", "--cached", "--quiet", check=False).returncode != 0:
        raise RuntimeError("staged changes exist; leaving the index untouched")


def wait_until_quiet(paths: list[tuple[str, str]], quiet_minutes: int) -> None:
    threshold = time.time() - quiet_minutes * 60
    recent = []
    for _, name in paths:
        file_path = ROOT / name
        if file_path.is_file() and file_path.stat().st_mtime > threshold:
            recent.append(name)
    if recent:
        raise RuntimeError(
            f"working files changed within the last {quiet_minutes} minutes; waiting"
        )


def run_once(quiet_minutes: int) -> int:
    try:
        verify_repo()
        locks = locked_objects()
        if locks:
            message("active object lock(s); waiting: " + ", ".join(p.name for p in locks))
            return 0
        ahead = int(git("rev-list", "--count", "origin/main..HEAD").stdout.decode().strip())
        if ahead:
            pushed = git("push", "origin", "main", check=False)
            if pushed.returncode:
                message("local commit(s) are ahead; push retry failed and commits are preserved")
                sys.stderr.buffer.write(pushed.stderr)
                return pushed.returncode
            message(f"pushed {ahead} previously unpushed commit(s)")
        paths = changed_paths()
        if not paths:
            message("working tree is clean")
            return 0
        for _, path in paths:
            reason = check_path(path)
            if reason:
                raise RuntimeError(f"protected change detected ({reason}); commit manually")
        wait_until_quiet(paths, quiet_minutes)
        git("diff", "--check")

        prek = ROOT / ".run" / "venv" / "bin" / "prek"
        if not prek.is_file():
            raise RuntimeError("project prek is not installed; run `make setup` first")
        checks = subprocess.run([str(prek), "run", "--all-files"], cwd=ROOT)
        if checks.returncode:
            raise RuntimeError(f"prek checks failed with exit code {checks.returncode}")

        # Hooks can edit files, so recheck locks, stability and path safety before staging.
        if locked_objects():
            message("an object lock appeared during checks; leaving changes unstaged")
            return 0
        paths = changed_paths()
        for _, path in paths:
            reason = check_path(path)
            if reason:
                raise RuntimeError(f"protected change detected ({reason}); commit manually")
        wait_until_quiet(paths, quiet_minutes)

        staged = False
        try:
            git("add", "-A")
            staged = True
            staged_paths = [os.fsdecode(item) for item in git("diff", "--cached", "--name-only", "-z").stdout.split(b"\0") if item]
            for path in staged_paths:
                reason = check_path(path)
                if reason:
                    raise RuntimeError(f"protected staged change ({reason})")
            git("diff", "--cached", "--check")
            if not staged_paths:
                message("no stageable changes")
                git("reset", "--mixed", "HEAD")
                return 0
            stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            git("commit", "-m", f"chore: periodic project sync {stamp}")
        except Exception:
            if staged:
                git("reset", "--mixed", "HEAD", check=False)
            raise

        pushed = git("push", "origin", "main", check=False)
        if pushed.returncode:
            message("commit created, but push failed; the local commit is preserved")
            sys.stderr.buffer.write(pushed.stderr)
            return pushed.returncode
        message("committed and pushed main")
        return 0
    except (OSError, subprocess.CalledProcessError, RuntimeError) as exc:
        message(f"skipped: {exc}")
        if isinstance(exc, subprocess.CalledProcessError) and exc.stderr:
            sys.stderr.buffer.write(exc.stderr)
        return 0


def launch_agent_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"


def project_python() -> Path:
    interpreter = ROOT / ".run" / "venv" / "bin" / "python"
    if not interpreter.is_file() or not os.access(interpreter, os.X_OK):
        raise RuntimeError("project Python is missing; run `make setup` before installing")
    return interpreter


def install(interval_minutes: int, quiet_minutes: int) -> int:
    if sys.platform != "darwin":
        raise RuntimeError("the included scheduler installer supports macOS launchd only")
    verify_repo()
    if interval_minutes < 15:
        raise RuntimeError("interval must be at least 15 minutes")
    if quiet_minutes < 1 or quiet_minutes >= interval_minutes:
        raise RuntimeError("quiet period must be positive and shorter than the interval")
    path = launch_agent_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    (ROOT / ".run").mkdir(exist_ok=True)
    plist = {
        "Label": LABEL,
        "ProgramArguments": [
            str(project_python()), str(Path(__file__).resolve()), "run",
            "--quiet-minutes", str(quiet_minutes),
        ],
        "WorkingDirectory": str(ROOT),
        "StartInterval": interval_minutes * 60,
        "RunAtLoad": False,
        "StandardOutPath": str(ROOT / ".run" / "periodic-commit-push.log"),
        "StandardErrorPath": str(ROOT / ".run" / "periodic-commit-push.log"),
    }
    path.write_bytes(plistlib.dumps(plist))
    domain = f"gui/{os.getuid()}"
    subprocess.run(["launchctl", "bootout", f"{domain}/{LABEL}"], check=False, capture_output=True)
    result = subprocess.run(["launchctl", "bootstrap", domain, str(path)], check=False)
    if result.returncode:
        raise RuntimeError(f"launchctl bootstrap failed with exit code {result.returncode}")
    message(f"installed every {interval_minutes} minutes (quiet period {quiet_minutes} minutes)")
    return 0


def uninstall() -> int:
    if sys.platform != "darwin":
        raise RuntimeError("the included scheduler installer supports macOS launchd only")
    path = launch_agent_path()
    domain = f"gui/{os.getuid()}"
    subprocess.run(["launchctl", "bootout", f"{domain}/{LABEL}"], check=False, capture_output=True)
    path.unlink(missing_ok=True)
    message("removed launch agent")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    run_parser = subparsers.add_parser("run", help="run one guarded commit/push cycle")
    run_parser.add_argument("--quiet-minutes", type=int, default=10)
    install_parser = subparsers.add_parser("install", help="install the macOS schedule")
    install_parser.add_argument("--interval-minutes", type=int, default=30)
    install_parser.add_argument("--quiet-minutes", type=int, default=10)
    subparsers.add_parser("uninstall", help="remove the macOS schedule")
    args = parser.parse_args()
    try:
        if args.action == "run":
            return run_once(args.quiet_minutes)
        if args.action == "install":
            return install(args.interval_minutes, args.quiet_minutes)
        return uninstall()
    except (OSError, RuntimeError) as exc:
        message(f"error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
