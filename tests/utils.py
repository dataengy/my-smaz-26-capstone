from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


def _run(command: list[str], *, cwd: Path, env: dict[str, str], timeout: int) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        pytest.fail(f"Command timed out after {timeout}s: {command!r}\n{exc.stdout or ''}\n{exc.stderr or ''}")
    assert result.returncode == 0, (
        f"Command failed ({result.returncode}): {command!r}\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    return result
