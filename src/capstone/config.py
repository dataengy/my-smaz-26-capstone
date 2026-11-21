"""Load the project's source configuration and research settings from YAML."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml


def _read_yaml(path: str | Path) -> dict:
    path = Path(path)
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Cannot read configuration {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Configuration must be a YAML mapping: {path}")
    return value


def read_config(config_path: str | Path = "config/config.yml",
                settings_path: str | Path | None = None) -> dict:
    """Merge source config and research settings; reject ambiguous duplicate keys."""
    config = _read_yaml(config_path)
    configured_settings = config.pop("settings_file", "config/settings.yml")
    configured_settings = settings_path or configured_settings
    settings = _read_yaml(configured_settings)
    overlap = config.keys() & settings.keys()
    if overlap:
        raise ValueError(f"Keys must be defined in only one config file: {sorted(overlap)}")
    result = {**config, **settings}
    required = {"data_dir", "release_manifest", "start", "symbols", "required_symbols",
                "target_symbols", "market_features", "train_fraction", "validation_fraction",
                "holding_sessions", "cot_max_age_days", "cross_market_max_age_days", "cost_bps",
                "market_download_timeout_seconds", "cftc_download_timeout_seconds",
                "download_cache_ttl_hours",
                "thresholds", "codex_sessions_root"}
    missing = required - result.keys()
    if missing:
        raise ValueError(f"Missing required configuration keys: {sorted(missing)}")
    if not isinstance(result["symbols"], dict) or not isinstance(result["market_features"], dict):
        raise ValueError("symbols and market_features must be YAML mappings")
    market_sources = result.get("market_sources", {})
    if not isinstance(market_sources, dict):
        raise ValueError("market_sources must be a YAML mapping")
    for key in ("required_symbols", "target_symbols", "thresholds"):
        if not isinstance(result[key], list):
            raise ValueError(f"{key} must be a YAML list")
    if not all(isinstance(value, str) and value for value in result["market_features"].values()):
        raise ValueError("market feature prefixes must be non-empty strings")
    symbol_names = set(result["symbols"])
    if not set(result["required_symbols"]).issubset(symbol_names):
        raise ValueError("required_symbols must be keys in symbols")
    if not set(result["target_symbols"]).issubset(symbol_names):
        raise ValueError("target_symbols must be keys in symbols")
    if not set(result["market_features"]).issubset(symbol_names):
        raise ValueError("market_features must be keys in symbols")
    if not set(market_sources).issubset(symbol_names):
        raise ValueError("market_sources must be keys in symbols")
    for name, source in market_sources.items():
        if not isinstance(source, dict):
            raise ValueError(f"market_sources.{name} must be a mapping")
        provider = source.get("provider")
        ticker = source.get("ticker")
        if not isinstance(provider, str) or provider not in {"yahoo", "binance"}:
            raise ValueError(f"Unsupported market_sources provider for {name}: {provider!r}")
        if not isinstance(ticker, str) or not ticker.strip():
            raise ValueError(f"market_sources.{name}.ticker must be a non-empty string")
        history_start = source.get("history_start")
        if history_start is not None:
            if not isinstance(history_start, str):
                raise ValueError(f"market_sources.{name}.history_start must be an ISO date string")
            try:
                parsed_history_start = date.fromisoformat(history_start)
            except ValueError as exc:
                raise ValueError(f"market_sources.{name}.history_start must be an ISO date string") from exc
            if parsed_history_start.isoformat() != history_start:
                raise ValueError(f"market_sources.{name}.history_start must use YYYY-MM-DD")
    if len(set(result["market_features"].values())) != len(result["market_features"]):
        raise ValueError("market feature prefixes must be unique")
    train = float(result["train_fraction"])
    validation = float(result["validation_fraction"])
    if not (0 < train < 1 and 0 < validation < 1 and train + validation < 1):
        raise ValueError("train_fraction and validation_fraction must be positive and sum to less than one")
    if int(result["holding_sessions"]) < 1 or int(result["cot_max_age_days"]) < 1 or int(result["cross_market_max_age_days"]) < 1:
        raise ValueError("holding and freshness settings must be positive")
    if int(result["market_download_timeout_seconds"]) < 1 or int(result["cftc_download_timeout_seconds"]) < 1:
        raise ValueError("download timeouts must be positive")
    if float(result["download_cache_ttl_hours"]) <= 0:
        raise ValueError("download_cache_ttl_hours must be positive")
    cost_bps = float(result["cost_bps"])
    if not 0 <= cost_bps < 10000:
        raise ValueError("cost_bps must be in [0, 10000)")
    if not result["thresholds"] or any(float(value) < 0 for value in result["thresholds"]):
        raise ValueError("thresholds must be a non-empty list of nonnegative returns")
    return result
