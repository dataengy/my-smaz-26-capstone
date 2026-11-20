"""Opt-in clean-origin checkout test for the standalone project.

Set ``CAPSTONE_E2E_ORIGIN`` to a Git URL or local Git repository. The test
clones it into an ignored temporary directory, installs the locked test extra,
then runs the deterministic smoke/unit/integration suite from that checkout.
It deliberately does not download market data or claim a real-data run.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys
import tempfile

import pytest
import yaml

from tests.utils import _run


@pytest.mark.e2e
def test_origin_fresh_clone_installs_and_runs_core_checks() -> None:
    origin = os.environ.get("CAPSTONE_E2E_ORIGIN", "").strip()
    if not origin:
        pytest.skip("Set CAPSTONE_E2E_ORIGIN to a Git URL or local repository to run the fresh-clone E2E")
    for executable in ("git", "uv"):
        if not shutil.which(executable):
            pytest.fail(f"{executable} is required when CAPSTONE_E2E_ORIGIN is configured")

    root = Path(__file__).resolve().parents[2]
    settings_path = root / "config" / "settings.yml"
    settings = yaml.safe_load(settings_path.read_text(encoding="utf-8"))
    workspace = root / settings["e2e_workspace"]
    workspace.mkdir(parents=True, exist_ok=True)

    origin_path = Path(origin).expanduser()
    if origin_path.exists():
        origin = str(origin_path.resolve())

    # Preserve only variables needed for Git authentication and package access.
    git_env = {
        key: os.environ[key]
        for key in (
            "PATH", "HOME", "USERPROFILE", "SSH_AUTH_SOCK", "GIT_SSH_COMMAND",
            "GIT_TERMINAL_PROMPT", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY",
        )
        if key in os.environ
    }
    uv_env = {
        key: value
        for key, value in os.environ.items()
        if key in {
            "PATH", "HOME", "USERPROFILE", "TMPDIR", "TEMP", "TMP",
            "SSL_CERT_FILE", "HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY", "NO_PROXY",
            "UV_INDEX_URL", "UV_EXTRA_INDEX_URL", "UV_DEFAULT_INDEX", "UV_NATIVE_TLS",
            "UV_OFFLINE", "UV_HTTP_TIMEOUT",
        }
    }

    with tempfile.TemporaryDirectory(prefix="origin-clone-", dir=workspace) as temp_dir:
        checkout = Path(temp_dir) / "checkout"
        clone = ["git", "clone", "--depth", "1"]
        git_ref = os.environ.get("CAPSTONE_E2E_GIT_REF", "").strip()
        if git_ref:
            clone.extend(["--branch", git_ref])
        clone.extend([origin, str(checkout)])
        _run(clone, cwd=root, env=git_env, timeout=int(settings["e2e_clone_timeout_seconds"]))

        env_dir = checkout / ".run" / "venv"
        cache_dir = root / ".run" / "uv-cache"
        uv_env.update({
            "UV_PROJECT_ENVIRONMENT": str(env_dir),
            "UV_CACHE_DIR": str(cache_dir),
            "UV_PYTHON": sys.executable,
        })
        timeout = int(settings["e2e_command_timeout_seconds"])
        _run(["uv", "sync", "--locked", "--extra", "test"], cwd=checkout, env=uv_env, timeout=timeout)

        python = env_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        assert python.is_file(), f"Locked project environment was not created: {python}"
        checks_env = {key: os.environ[key] for key in ("PATH", "HOME", "USERPROFILE") if key in os.environ}
        _run(
            [str(python), "-m", "pytest", "-q", "tests/smoke", "tests/unit", "tests/integration"],
            cwd=checkout,
            env=checks_env,
            timeout=timeout,
        )
