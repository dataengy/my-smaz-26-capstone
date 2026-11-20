"""Opt-in offline workflow test against the user's real, previously acquired data.

Set CAPSTONE_E2E_CONFIG to an existing configuration with valid snapshots and an
independently evidenced COT release manifest. Artifacts go to pytest's temp dir.
"""
import os
import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml


def test_real_data_offline_workflow(tmp_path):
    config_path = os.environ.get('CAPSTONE_E2E_CONFIG')
    if not config_path:
        pytest.skip('Set CAPSTONE_E2E_CONFIG to run against real local snapshots')
    root = Path(__file__).resolve().parents[2]
    path = Path(config_path).expanduser().resolve()
    if not path.is_file():
        pytest.fail(f'Configured E2E configuration is missing: {path}')
    source_config = yaml.safe_load(path.read_text())
    if not isinstance(source_config, dict):
        pytest.fail(f'E2E source configuration must be a YAML mapping: {path}')
    settings_path = Path(source_config.get('settings_file', 'config/settings.yml'))
    if not settings_path.is_absolute():
        settings_path = root / settings_path
    settings = yaml.safe_load(settings_path.read_text())
    if not isinstance(settings, dict):
        pytest.fail(f'E2E settings must be a YAML mapping: {settings_path}')
    for key in ('data_dir', 'release_manifest'):
        if key in source_config:
            source_config[key] = str((root / source_config[key]).resolve())
    settings['output_dir'] = str(tmp_path / 'artifacts')
    isolated_config = tmp_path / 'config.yml'
    isolated_settings = tmp_path / 'settings.yml'
    isolated_config.write_text(yaml.safe_dump(source_config, sort_keys=False))
    isolated_settings.write_text(yaml.safe_dump(settings, sort_keys=False))
    env = {**os.environ, 'PYTHONPATH': str(root / 'src')}
    result = subprocess.run([sys.executable, '-m', 'capstone.cli', 'run', '--offline', '--config', str(isolated_config), '--settings', str(isolated_settings)],
                            cwd=root, env=env, capture_output=True, text=True, timeout=600, check=False)
    assert result.returncode == 0, result.stdout + '\n' + result.stderr
    output = tmp_path / 'artifacts'
    assert {'summary.json', 'latest_signals.csv', 'equity.csv', 'metrics.csv', 'model_metrics.csv'}.issubset(
        {p.name for p in output.iterdir()})
    assert json.loads((output / 'summary.json').read_text())['rows'] > 0
