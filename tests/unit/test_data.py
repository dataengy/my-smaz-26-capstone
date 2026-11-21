"""Risk-focused fixtures for availability and snapshot handling; no real results."""
import io
import zipfile

import pandas as pd
import pytest

from capstone.data import _read_snapshot, _write_snapshot, load_release_manifest, parse_cot_archive
from capstone.features import _market_frame, _other_returns, build_features
from tests.fixtures.synthetic_market import make_synthetic_market_bars


def test_snapshot_detects_modification(tmp_path):
    path = tmp_path / "prices.csv"
    _write_snapshot(path, b"original", "fixture")
    assert _read_snapshot(path) == b"original"
    path.write_bytes(b"altered")
    with pytest.raises(ValueError, match="SHA-256"):
        _read_snapshot(path)


def test_failed_optional_refresh_does_not_reuse_older_cache(tmp_path, monkeypatch, capsys):
    from capstone import data

    data_dir = tmp_path / "data"
    market_dir = data_dir / "raw" / "market"
    observed_at = pd.Timestamp("2024-01-05T22:00:00Z").to_pydatetime()
    bars = make_synthetic_market_bars(["2024-01-02", "2024-01-03"])
    for name in ("GLD", "SLV", "NVDA"):
        path = market_dir / f"{name}.csv"
        _write_snapshot(path, bars.to_csv(index=False).encode(), f"Yahoo Finance: {name}", observed_at=observed_at)

    raw = pd.DataFrame({
        "CFTC_Contract_Market_Code": ["088691"],
        "Report_Date_as_YYYY-MM-DD": ["2024-01-02"],
        "Open_Interest_All": [100],
        "M_Money_Positions_Long_All": [20],
        "M_Money_Positions_Short_All": [10],
        "Prod_Merc_Positions_Long_All": [30],
        "Prod_Merc_Positions_Short_All": [40],
    })
    archive_path = data_dir / "raw" / "cftc" / "2024.zip"
    archive_path.parent.mkdir(parents=True)
    archive_buffer = io.BytesIO()
    with zipfile.ZipFile(archive_buffer, "w") as archive:
        archive.writestr("annual.txt", raw.to_csv(index=False))
    _write_snapshot(archive_path, archive_buffer.getvalue(), data.CFTC_URL.format(year=2024))

    manifest_path = tmp_path / "release.csv"
    manifest_path.write_text(
        "report_date,available_at,source_url\n"
        "2024-01-02,2024-01-05T05:00:00Z,https://example.invalid/release-evidence\n"
    )
    monkeypatch.setattr(data, "_completed_market_bars", lambda frame, symbol, observed_at: frame)

    def fake_download(symbol, start, end, timeout):
        if symbol == "NVDA":
            raise ValueError("fixture refresh failure")
        source_bars = bars.set_index(pd.DatetimeIndex(pd.to_datetime(bars.date), name="date")).drop(columns="date")
        return source_bars.to_csv().encode()

    monkeypatch.setattr(data, "_download_market", fake_download)
    monkeypatch.setattr(data.urllib.request, "urlopen", lambda url, timeout: io.BytesIO(archive_buffer.getvalue()))
    config = {
        "data_dir": str(data_dir),
        "release_manifest": str(manifest_path),
        "start": "2024-01-01",
        "end": "2024-01-04",
        "symbols": {"GLD": "GLD", "SLV": "SLV", "NVDA": "NVDA"},
        "required_symbols": ["GLD", "SLV"],
        "target_symbols": ["GLD", "SLV"],
        "market_features": {"NVDA": "nvda"},
    }

    sources = data.load_sources(config, refresh=True)

    assert {"GLD", "SLV", "cot"}.issubset(sources)
    assert "NVDA" not in sources
    assert "Optional market data NVDA unavailable: fixture refresh failure" in capsys.readouterr().out
    # The failed refresh does not delete the older snapshot; offline replay remains possible.
    assert (market_dir / "NVDA.csv").is_file()


def test_manifest_requires_explicit_evidenced_utc(tmp_path):
    path = tmp_path / "release.csv"
    path.write_text("report_date,available_at,source_url\n2024-01-02,2024-01-05 20:30:00,https://example.org/report\n")
    with pytest.raises(ValueError, match="UTC"):
        load_release_manifest(path)
    path.write_text("report_date,available_at,source_url\n2024-01-02,2024-01-05T20:30:00Z,https://example.org/report\n")
    assert load_release_manifest(path).available_at.iloc[0] == pd.Timestamp("2024-01-05T20:30:00Z")


def test_cot_zip_filters_contract_codes():
    raw = pd.DataFrame({"CFTC_Contract_Market_Code": ["088691", "084691", "123456"],
        "Report_Date_as_YYYY-MM-DD": ["2024-01-02"] * 3, "Open_Interest_All": [100] * 3,
        "M_Money_Positions_Long_All": [20] * 3, "M_Money_Positions_Short_All": [10] * 3,
        "Prod_Merc_Positions_Long_All": [30] * 3, "Prod_Merc_Positions_Short_All": [40] * 3})
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("annual.txt", raw.to_csv(index=False))
    assert set(parse_cot_archive(buf.getvalue()).ticker) == {"GLD", "SLV"}
    documented = raw.rename(columns={"Report_Date_as_YYYY-MM-DD": "As_of_Date_Form_YYYY-MM-DD"})
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("annual.txt", documented.to_csv(index=False))
    assert len(parse_cot_archive(buf.getvalue())) == 2


def test_cot_zip_rejects_invalid_or_missing_target_records():
    with pytest.raises(zipfile.BadZipFile):
        parse_cot_archive(b"not a zip archive")

    raw = pd.DataFrame({"CFTC_Contract_Market_Code": ["123456"],
        "Report_Date_as_YYYY-MM-DD": ["2024-01-02"], "Open_Interest_All": [100],
        "M_Money_Positions_Long_All": [20], "M_Money_Positions_Short_All": [10],
        "Prod_Merc_Positions_Long_All": [30], "Prod_Merc_Positions_Short_All": [40]})
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("annual.txt", raw.to_csv(index=False))
    with pytest.raises(ValueError, match="no COMEX gold or silver"):
        parse_cot_archive(buf.getvalue())


def test_cot_zip_rejects_duplicate_contract_report_dates():
    raw = pd.DataFrame({"CFTC_Contract_Market_Code": ["088691", "088691"],
        "Report_Date_as_YYYY-MM-DD": ["2024-01-02", "2024-01-02"], "Open_Interest_All": [100, 101],
        "M_Money_Positions_Long_All": [20, 21], "M_Money_Positions_Short_All": [10, 11],
        "Prod_Merc_Positions_Long_All": [30, 31], "Prod_Merc_Positions_Short_All": [40, 41]})
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("annual.txt", raw.to_csv(index=False))
    with pytest.raises(ValueError, match="Duplicate COT ticker/report dates"):
        parse_cot_archive(buf.getvalue())


def test_crypto_bar_is_not_used_until_next_utc_midnight():
    prices = make_synthetic_market_bars(pd.date_range("2024-01-01", periods=8, freq="D"))
    signals = pd.DataFrame({"signal_at": pd.to_datetime(["2024-01-07T20:00Z", "2024-01-08T20:00Z"], utc=True)})
    result = _other_returns(prices, "BTC-USD", signals)
    assert result.iloc[0] == pytest.approx(105 / 100 - 1)
    assert result.iloc[1] == pytest.approx(106 / 101 - 1)


def test_mixed_dst_offsets_preserve_provider_local_bar_dates():
    # Include an eastern offset and a positive offset to detect accidental UTC conversion.
    labels = ["2024-03-08 00:00:00-05:00", "2024-03-11 00:00:00-04:00",
              "2024-03-12 00:00:00+09:00"]
    frame = _market_frame(make_synthetic_market_bars(labels), "fixture")
    assert frame.date.tolist() == list(pd.to_datetime(["2024-03-08", "2024-03-11", "2024-03-12"]))


def test_snapshot_crypto_cutoff_uses_observation_time_not_replay_time():
    from capstone.data import _completed_market_bars
    prices = make_synthetic_market_bars(pd.to_datetime(["2024-03-07", "2024-03-08", "2024-03-09"]))
    # Even if this is reloaded later, the incomplete March 8 candle stays excluded.
    early = _completed_market_bars(prices, "BTC-USD", "2024-03-08T23:59:59Z")
    assert early.date.tolist() == ["2024-03-07"]
    closed = _completed_market_bars(prices, "BTC-USD", "2024-03-09T00:00:00Z")
    assert closed.date.tolist() == ["2024-03-07", "2024-03-08"]
    with pytest.raises(ValueError, match="timezone-aware"):
        _completed_market_bars(prices, "BTC-USD", "2024-03-09T00:00:00")


def test_snapshot_etf_cutoff_respects_real_early_close():
    pytest.importorskip("exchange_calendars")
    from capstone.data import _completed_market_bars
    prices = make_synthetic_market_bars(pd.to_datetime(["2024-11-27", "2024-11-29"]))
    # Day after Thanksgiving closes at 13:00 ET = 18:00 UTC.
    before = _completed_market_bars(prices, "GLD", "2024-11-29T17:59:59Z")
    after = _completed_market_bars(prices, "GLD", "2024-11-29T18:00:00Z")
    assert before.date.tolist() == ["2024-11-27"]
    assert after.date.tolist() == ["2024-11-27", "2024-11-29"]
