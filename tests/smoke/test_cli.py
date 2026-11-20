"""Check that the installed CLI entry module can display its help."""
import os
from pathlib import Path
import subprocess
import sys


def test_cli_help_starts():
    root = Path(__file__).resolve().parents[2]
    env = {**os.environ, 'PYTHONPATH': str(root / 'src')}
    result = subprocess.run([sys.executable, '-m', 'capstone.cli', '--help'], cwd=root, env=env,
                            capture_output=True, text=True, timeout=30, check=False)
    assert result.returncode == 0, result.stderr
    assert 'download' in result.stdout and 'features' in result.stdout and 'run' in result.stdout
