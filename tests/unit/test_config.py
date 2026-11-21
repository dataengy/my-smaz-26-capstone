from pathlib import Path

import pytest
import yaml

from capstone.config import read_config


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _write_config_pair(tmp_path, *, source_changes=None, settings_changes=None):
    source = yaml.safe_load((PROJECT_ROOT / "config/config.yml").read_text())
    settings = yaml.safe_load((PROJECT_ROOT / "config/settings.yml").read_text())
    source.update(source_changes or {})
    settings.update(settings_changes or {})
    settings_path = tmp_path / "settings.yml"
    config_path = tmp_path / "config.yml"
    settings_path.write_text(yaml.safe_dump(settings, sort_keys=False))
    source["settings_file"] = str(settings_path)
    config_path.write_text(yaml.safe_dump(source, sort_keys=False))
    return config_path, settings_path


def test_default_paths_load_project_yaml_config(monkeypatch):
    monkeypatch.chdir(PROJECT_ROOT)

    cfg = read_config()

    assert cfg["cost_bps"] >= 0
    assert cfg["holding_sessions"] == 5
    assert cfg["release_manifest"]
    assert cfg["target_symbols"] == ["GLD", "SLV"]
    assert set(cfg["required_symbols"]).issubset(cfg["symbols"])
    assert cfg["codex_sessions_root"] == "~/.codex/sessions"
    assert cfg["market_sources"]["BTC-USD"] == {"provider": "binance", "ticker": "BTCUSDT"}
    assert cfg["market_sources"]["SOL-USD"]["history_start"] == "2020-08-11"


def test_explicit_config_and_settings_paths_load(tmp_path):
    config_path, settings_path = _write_config_pair(tmp_path)

    cfg = read_config(config_path, settings_path)

    assert cfg["target_symbols"] == ["GLD", "SLV"]
    assert cfg["holding_sessions"] == 5


def test_configured_settings_path_is_used_when_no_override_is_given(tmp_path):
    config_path, _ = _write_config_pair(tmp_path)

    cfg = read_config(config_path)

    assert cfg["holding_sessions"] == 5
    assert cfg["target_symbols"] == ["GLD", "SLV"]


def test_rejects_key_collision_between_source_and_settings(tmp_path):
    config_path, settings_path = _write_config_pair(
        tmp_path, source_changes={"cost_bps": 1}
    )

    with pytest.raises(ValueError, match="defined in only one config file"):
        read_config(config_path, settings_path)


def test_rejects_missing_required_configuration_key(tmp_path):
    config_path, settings_path = _write_config_pair(tmp_path)
    source = yaml.safe_load(config_path.read_text())
    source.pop("target_symbols")
    config_path.write_text(yaml.safe_dump(source, sort_keys=False))

    with pytest.raises(ValueError, match="target_symbols"):
        read_config(config_path, settings_path)


def test_rejects_invalid_partition_fractions(tmp_path):
    config_path, settings_path = _write_config_pair(
        tmp_path,
        settings_changes={"train_fraction": 0.8, "validation_fraction": 0.3},
    )

    with pytest.raises(ValueError, match="sum to less than one"):
        read_config(config_path, settings_path)


def test_rejects_unsupported_market_source_provider(tmp_path):
    config_path, settings_path = _write_config_pair(
        tmp_path,
        source_changes={"market_sources": {"BTC-USD": {"provider": "unknown", "ticker": "BTCUSDT"}}},
    )

    with pytest.raises(ValueError, match="Unsupported market_sources provider"):
        read_config(config_path, settings_path)


def test_rejects_malformed_provider_history_start(tmp_path):
    config_path, settings_path = _write_config_pair(tmp_path)
    source = yaml.safe_load(config_path.read_text())
    source["market_sources"]["SOL-USD"]["history_start"] = "2020-02-31"
    config_path.write_text(yaml.safe_dump(source, sort_keys=False))

    with pytest.raises(ValueError, match="history_start must be an ISO date string"):
        read_config(config_path, settings_path)
