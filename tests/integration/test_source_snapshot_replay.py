"""Exercise the offline source boundary with source-shaped synthetic snapshots."""
from __future__ import annotations

import io
import zipfile

import pandas as pd
import pytest

from capstone.data import CFTC_URL, _write_snapshot, load_sources
from capstone.features import build_features
from tests.fixtures.synthetic_market import make_synthetic_market_bars


def _write_cot_snapshot(root):
    rows = pd.DataFrame({
        "CFTC_Contract_Market_Code": ["088691", "084691"],
        "Report_Date_as_YYYY-MM-DD": ["2024-01-02", "2024-01-02"],
        "Open_Interest_All": [100_000, 80_000],
        "M_Money_Positions_Long_All": [20_000, 15_000],
        "M_Money_Positions_Short_All": [10_000, 8_000],
        "Prod_Merc_Positions_Long_All": [30_000, 25_000],
        "Prod_Merc_Positions_Short_All": [40_000, 35_000],
    })
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr("annual.txt", rows.to_csv(index=False))
    _write_snapshot(root / "raw/cftc/2024.zip", payload.getvalue(), CFTC_URL.format(year=2024))


def _config(tmp_path, manifest_path):
    return {
        "data_dir": str(tmp_path / "data"),
        "release_manifest": str(manifest_path),
        "start": "2024-01-02",
        "end": "2024-01-05",
        "symbols": {name: name for name in ("GLD", "SLV", "BTC-USD", "NVDA")},
        "required_symbols": ["GLD", "SLV", "BTC-USD", "NVDA"],
        "target_symbols": ["GLD", "SLV"],
        "market_features": {},
        "market_sources": {"BTC-USD": {"provider": "binance", "ticker": "BTCUSDT"}},
    }


def test_offline_source_replay_validates_snapshots_and_respects_date_range(tmp_path, monkeypatch):
    """Cached market and COT inputs replay with provenance and no provider calls."""
    data_root = tmp_path / "data"
    market_root = data_root / "raw/market"
    observed_at = pd.Timestamp("2024-01-07T22:00:00Z").to_pydatetime()
    dates = pd.date_range("2024-01-02", "2024-01-05", freq="D")
    bars = make_synthetic_market_bars(dates)
    for name in ("GLD", "SLV", "BTC-USD", "NVDA"):
        source = (
            "Binance Spot: https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1d (USDT quote)"
            if name == "BTC-USD" else f"Yahoo Finance: {name}"
        )
        _write_snapshot(
            market_root / f"{name}.csv",
            bars.to_csv(index=False).encode(),
            source,
            observed_at=observed_at,
        )
    _write_cot_snapshot(data_root)
    manifest = tmp_path / "release.csv"
    manifest.write_text(
        "report_date,available_at,source_url\n"
        "2024-01-02,2024-01-05T06:00:00Z,https://example.invalid/cot-notice\n"
    )

    def unexpected_network(*args, **kwargs):
        pytest.fail("offline snapshot replay attempted a provider request")

    monkeypatch.setattr("capstone.data._download_market", unexpected_network)
    monkeypatch.setattr("capstone.data.urllib.request.urlopen", unexpected_network)

    config = _config(tmp_path, manifest)
    result = load_sources(config)
    snapshot_files = {
        str(path.relative_to(data_root)): path.read_bytes()
        for path in (data_root / "raw").rglob("*")
        if path.is_file()
    }
    replay = load_sources(config)

    assert set(result) == {"GLD", "SLV", "BTC-USD", "NVDA", "cot"}
    for name in ("GLD", "SLV", "BTC-USD", "NVDA"):
        # end is exclusive, and the following day is not accidentally included.
        assert result[name].date.tolist() == list(pd.date_range("2024-01-02", "2024-01-04"))
    cot = result["cot"].sort_values("ticker").reset_index(drop=True)
    assert cot.ticker.tolist() == ["GLD", "SLV"]
    assert cot.available_at.eq(pd.Timestamp("2024-01-05T06:00:00Z")).all()
    assert cot.source_url.eq("https://example.invalid/cot-notice").all()
    assert replay.keys() == result.keys()
    for name in result:
        pd.testing.assert_frame_equal(replay[name], result[name])

    # Feature processing is deterministic for the same replayed source frames.
    feature_sources = {name: frame.copy(deep=True) for name, frame in result.items()}
    feature_sources["cot"]["available_at"] = pd.Timestamp("2024-01-03T06:00:00Z")
    feature_config = {"target_symbols": ["GLD", "SLV"], "market_features": {}, "holding_sessions": 5}
    features_first = build_features(feature_sources, feature_config)
    features_replay = build_features(feature_sources, feature_config)
    pd.testing.assert_frame_equal(features_replay, features_first)
    assert features_replay.to_csv(index=False) == features_first.to_csv(index=False)

    assert snapshot_files == {
        str(path.relative_to(data_root)): path.read_bytes()
        for path in (data_root / "raw").rglob("*")
        if path.is_file()
    }

    # Reject repeated dates rather than silently multiplying source observations.
    gld_path = market_root / "GLD.csv"
    gld = pd.read_csv(gld_path)
    duplicate_payload = pd.concat([gld, gld.iloc[[0]]], ignore_index=True).to_csv(index=False).encode()
    _write_snapshot(
        gld_path,
        duplicate_payload,
        "Yahoo Finance: GLD",
        observed_at=observed_at,
    )
    with pytest.raises(RuntimeError, match="Duplicate market dates in snapshot: GLD"):
        load_sources(config)


def test_offline_source_replay_fails_clearly_for_missing_required_snapshot(tmp_path):
    manifest = tmp_path / "release.csv"
    manifest.write_text(
        "report_date,available_at,source_url\n"
        "2024-01-02,2024-01-05T06:00:00Z,https://example.invalid/cot-notice\n"
    )
    with pytest.raises(RuntimeError, match=r"Required market data GLD unavailable: Missing cached data or hash metadata"):
        load_sources(_config(tmp_path, manifest))
