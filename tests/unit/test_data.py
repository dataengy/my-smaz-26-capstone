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
