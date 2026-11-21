"""Dagster's adapter must preserve the existing runner's completion gate."""
import shutil

import pytest

dg = pytest.importorskip('dagster')
from capstone import orchestration
from tests.unit.test_reporting import saved_run


def test_one_atomic_research_call_materializes_all_reports(saved_run, tmp_path, monkeypatch):
    calls = []

    def completed(source, settings, output):
        calls.append((source, settings, output))
        shutil.copytree(saved_run, output)
        return 0

    monkeypatch.setattr(orchestration.research, 'run', completed)
    result = dg.materialize([orchestration.frozen_research_assets], run_config={'ops': {
        'frozen_research_assets': {'config': {'output_root': str(tmp_path / 'dagster')}}}})
    assert result.success and len(calls) == 1
    assert len(result.get_asset_materialization_events()) == 4
    assert (calls[0][2] / 'run-1/model_comparison.csv').is_file()


def test_blocked_research_never_materializes_success(tmp_path, monkeypatch):
    monkeypatch.setattr(orchestration.research, 'run', lambda *args: 2)
    result = dg.materialize([orchestration.frozen_research_assets], raise_on_error=False, run_config={'ops': {
        'frozen_research_assets': {'config': {'output_root': str(tmp_path / 'blocked')}}}})
    assert not result.success
    assert not result.get_asset_materialization_events()
