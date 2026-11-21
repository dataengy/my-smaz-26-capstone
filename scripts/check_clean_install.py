#!/usr/bin/env python3
"""Verify a locked dev install in a disposable environment and empty uv cache."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], *, env: dict[str, str]) -> int:
    print("$ " + " ".join(command), flush=True)
    return subprocess.run(command, cwd=PROJECT_ROOT, env=env, check=False).returncode


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    uv = shutil.which("uv")
    if uv is None:
        print("ERROR: uv is not installed or is not on PATH", file=sys.stderr)
        return 2
    if not (PROJECT_ROOT / "uv.lock").is_file():
        print("ERROR: uv.lock is missing; refusing an unlocked install", file=sys.stderr)
        return 2

    started = datetime.now(timezone.utc)
    print(f"started_utc={started.isoformat()}")
    with tempfile.TemporaryDirectory(prefix="capstone-clean-install-") as scratch:
        temp_root = Path(scratch)
        env = os.environ.copy()
        env["UV_PROJECT_ENVIRONMENT"] = str(temp_root / "venv")
        env["UV_CACHE_DIR"] = str(temp_root / "uv-cache")
        env["UV_NO_PROGRESS"] = "1"

        status = run([uv, "sync", "--locked", "--extra", "dev"], env=env)
        if status:
            print(f"RESULT=sync_failed exit_code={status}", flush=True)
            return status

        python = temp_root / "venv" / "bin" / "python"
        status = run(
            [
                str(python),
                "-c",
                "import capstone, exchange_calendars, jupyter, nbformat, numpy, pandas, pytest, sklearn, yfinance; "
                "calendar = exchange_calendars.get_calendar('XNYS'); "
                "assert calendar.is_session('2024-07-03'); print('imports=ok calendar=XNYS-2024-07-03-session notebook_format=ok')",
            ],
            env=env,
        )
        if status:
            print(f"RESULT=import_check_failed exit_code={status}", flush=True)
            return status

    print(f"finished_utc={datetime.now(timezone.utc).isoformat()}")
    print("RESULT=clean_locked_dev_install_passed disposable_environment_and_cache_removed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
