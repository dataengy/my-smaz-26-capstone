"""Risk-focused fixtures for availability and snapshot handling; no real results."""
import io
import json
import urllib.error
import urllib.parse
import urllib.request
import zipfile

import pandas as pd
import pytest

from capstone.data import _download_market, _read_snapshot, _write_snapshot, load_release_manifest, parse_cot_archive
from capstone.features import _market_frame, _other_returns, build_features
from tests.fixtures.synthetic_market import make_synthetic_market_bars


def test_yfinance_missing_transitive_dependency_is_reported_precisely(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def missing_peewee(name, *args, **kwargs):
        if name == "yfinance":
            raise ModuleNotFoundError("No module named 'tests'", name="tests")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", missing_peewee)
    with pytest.raises(RuntimeError, match="dependency 'tests' is unavailable"):
        _download_market("GLD", "2024-01-01", "2024-01-10")


def test_cftc_download_uses_accepted_user_agent(monkeypatch):
    from capstone import data

    observed = {}

    def fake_urlopen(request, timeout):
        observed["request"] = request
        observed["timeout"] = timeout
        return io.BytesIO(b"archive")

    monkeypatch.setattr(data.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(data, "parse_cot_archive", lambda payload: None)

    url, payload = data._download_cot_archive(2026, timeout=12)

    assert url == data.CFTC_URL.format(year=2026)
    assert payload == b"archive"
    assert observed["request"].get_header("User-agent") == data.CFTC_USER_AGENT
    assert observed["timeout"] == 12


def test_cftc_http_error_reports_source_url_and_status(monkeypatch):
    from capstone import data

    def forbidden(request, timeout):
        raise urllib.error.HTTPError(request.full_url, 403, "Forbidden", {}, io.BytesIO())

    monkeypatch.setattr(data.urllib.request, "urlopen", forbidden)
    with pytest.raises(RuntimeError, match=r"cftc\.gov.*HTTP 403 Forbidden"):
        data._download_cot_archive(2026)


def test_binance_market_download_paginates_utc_daily_klines(monkeypatch):
    from capstone import data

    monkeypatch.setattr(data, "BINANCE_KLINES_LIMIT", 2)
    day_ms = 86_400_000
    first_page = [
        [1_704_067_200_000 + index * day_ms, "10", "12", "9", str(11 + index), "100",
         1_704_153_599_999 + index * day_ms, "1000", 5, "50", "500", "0"]
        for index in range(2)
    ]
    second_page = [[
        1_704_067_200_000 + 2 * day_ms, "12", "14", "11", "13", "120",
        1_704_153_599_999 + 2 * day_ms, "1500", 7, "60", "700", "0",
    ]]
    pages = iter((first_page, second_page))
    requests = []

    def fake_urlopen(request, timeout):
        requests.append((request, timeout))
        return io.BytesIO(json.dumps(next(pages)).encode())

    monkeypatch.setattr(data.urllib.request, "urlopen", fake_urlopen)
    payload = data._download_binance_market("BTCUSDT", "2024-01-01", "2024-01-04", timeout=9)
    frame = pd.read_csv(io.BytesIO(payload), parse_dates=["date"])

    assert frame.date.tolist() == list(pd.date_range("2024-01-01", periods=3, freq="D"))
    assert frame["Adj Close"].tolist() == frame.Close.tolist()
    assert len(requests) == 2
    assert all(timeout == 9 for _, timeout in requests)
    first_query = urllib.parse.parse_qs(urllib.parse.urlparse(requests[0][0].full_url).query)
    second_query = urllib.parse.parse_qs(urllib.parse.urlparse(requests[1][0].full_url).query)
    assert first_query["symbol"] == ["BTCUSDT"]
    assert first_query["interval"] == ["1d"]
    assert int(first_query["endTime"][0]) == int(pd.Timestamp("2024-01-04", tz="UTC").timestamp() * 1000) - 1
    assert int(second_query["startTime"][0]) == first_page[-1][6] + 1


def test_binance_market_download_rejects_empty_or_error_responses(monkeypatch):
    from capstone import data

    monkeypatch.setattr(data.urllib.request, "urlopen", lambda request, timeout: io.BytesIO(b'{"code":-1121}'))
    with pytest.raises(ValueError, match="expected a JSON array"):
        data._download_binance_market("NOTAPAIR", "2024-01-01", "2024-01-02")

    monkeypatch.setattr(data.urllib.request, "urlopen", lambda request, timeout: io.BytesIO(b"[]"))
    with pytest.raises(ValueError, match="no klines"):
        data._download_binance_market("BTCUSDT", "2024-01-01", "2024-01-02")


def test_snapshot_detects_modification(tmp_path):
    path = tmp_path / "prices.csv"
    _write_snapshot(path, b"original", "fixture")
    assert _read_snapshot(path) == b"original"
    path.write_bytes(b"altered")
    with pytest.raises(ValueError, match="SHA-256"):
        _read_snapshot(path)


def test_writing_identical_snapshot_preserves_bytes_and_original_cutoff(tmp_path):
    path = tmp_path / "prices.csv"
    first_observation = pd.Timestamp("2024-01-05T20:00:00Z").to_pydatetime()
    later_observation = pd.Timestamp("2024-01-06T20:00:00Z").to_pydatetime()
    _write_snapshot(path, b"same provider response", "fixture", observed_at=first_observation)
    original = (path.read_bytes(), path.with_suffix(".csv.json").read_bytes())

    _write_snapshot(path, b"same provider response", "fixture", observed_at=later_observation)

    assert (path.read_bytes(), path.with_suffix(".csv.json").read_bytes()) == original
    assert json.loads(path.with_suffix(".csv.json").read_text())["observed_at"] == first_observation.isoformat()


def _download_cache_fixture(tmp_path, monkeypatch):
    from capstone import data

    data_dir = tmp_path / "data"
    raw = data_dir / "raw"
    bars = make_synthetic_market_bars(["2024-01-02", "2024-01-03"])
    observed_at = pd.Timestamp("2024-01-04T22:00:00Z").to_pydatetime()
    for name in ("GLD", "SLV"):
        _write_snapshot(
            raw / "market" / f"{name}.csv",
            bars.to_csv(index=False).encode(),
            f"Yahoo Finance: {name}",
            observed_at=observed_at,
        )

    cot = pd.DataFrame({
        "CFTC_Contract_Market_Code": ["088691", "084691"],
        "Report_Date_as_YYYY-MM-DD": ["2024-01-02", "2024-01-02"],
        "Open_Interest_All": [100, 200],
        "M_Money_Positions_Long_All": [20, 40],
        "M_Money_Positions_Short_All": [10, 30],
        "Prod_Merc_Positions_Long_All": [30, 60],
        "Prod_Merc_Positions_Short_All": [40, 80],
    })
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("annual.txt", cot.to_csv(index=False))
    archive_bytes = buffer.getvalue()
    _write_snapshot(
        raw / "cftc" / "2024.zip", archive_bytes,
        data.CFTC_URL.format(year=2024),
    )

    monkeypatch.setattr(
        data, "_latest_expected_bar_date",
        lambda symbol, end, now=None: pd.Timestamp("2024-01-03"),
    )
    config = {
        "data_dir": str(data_dir), "start": "2024-01-01", "end": "2024-01-04",
        "symbols": {"GLD": "GLD", "SLV": "SLV"},
        "required_symbols": ["GLD", "SLV"], "target_symbols": ["GLD", "SLV"],
        "market_features": {}, "download_cache_ttl_hours": 24,
    }
    return data, config, raw, bars, archive_bytes


def test_download_skips_valid_current_market_and_historical_cot_caches(tmp_path, monkeypatch, caplog):
    caplog.set_level("INFO", logger="capstone.download")
    from capstone import data

    data, config, _, _, _ = _download_cache_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(data, "_download_market", lambda *args, **kwargs: pytest.fail("market cache should be reused"))
    monkeypatch.setattr(data, "_download_cot_archive", lambda *args, **kwargs: pytest.fail("COT cache should be reused"))

    failures = data.refresh_sources(config)

    assert failures == {}
    assert "market GLD: cache valid" in caplog.text
    assert "CFTC archive 2024: cache valid" in caplog.text
    assert "Download summary: downloaded=0 skipped=3 failed=0" in caplog.text


def test_download_refreshes_bad_market_cache_and_keeps_other_valid_caches(tmp_path, monkeypatch, caplog):
    caplog.set_level("INFO", logger="capstone.download")
    from capstone import data

    data, config, raw, bars, _ = _download_cache_fixture(tmp_path, monkeypatch)
    bad = bars.copy()
    bad.loc[bad.index[-1], "Close"] = float("nan")
    path = raw / "market" / "GLD.csv"
    _write_snapshot(
        path, bad.to_csv(index=False).encode(), "Yahoo Finance: GLD",
        observed_at=pd.Timestamp("2024-01-04T22:00:00Z").to_pydatetime(),
    )
    downloads = []

    def fetch_market(symbol, start, end, timeout):
        downloads.append(symbol)
        return bars.to_csv(index=False).encode()

    monkeypatch.setattr(data, "_download_market", fetch_market)
    monkeypatch.setattr(data, "_download_cot_archive", lambda year, timeout: (
        data.CFTC_URL.format(year=year), data._read_snapshot(raw / "cftc" / f"{year}.zip")
    ))

    data.refresh_sources(config)

    assert downloads == ["GLD"]
    assert "market GLD: refreshing" in caplog.text
    assert "market SLV: cache valid" in caplog.text
    assert "Download summary: downloaded=1 skipped=2 failed=0" in caplog.text
    assert pd.read_csv(path).Close.notna().all()


def test_force_download_refreshes_all_sources(tmp_path, monkeypatch, caplog):
    caplog.set_level("INFO", logger="capstone.download")
    from capstone import data

    data, config, raw, bars, archive_bytes = _download_cache_fixture(tmp_path, monkeypatch)
    downloads = []

    def fetch_market(symbol, start, end, timeout):
        downloads.append(symbol)
        return bars.to_csv(index=False).encode()

    monkeypatch.setattr(data, "_download_market", fetch_market)
    monkeypatch.setattr(data, "_download_cot_archive", lambda year, timeout: (
        data.CFTC_URL.format(year=year), archive_bytes
    ))

    data.refresh_sources(config, force=True)

    assert downloads == ["GLD", "SLV"]
    assert "force refresh enabled" in caplog.text
    assert "Download summary: downloaded=3 skipped=0 failed=0" in caplog.text


def test_malformed_market_refresh_does_not_replace_previous_snapshot(tmp_path, monkeypatch):
    from capstone import data

    data, config, raw, _, _ = _download_cache_fixture(tmp_path, monkeypatch)
    path = raw / "market" / "GLD.csv"
    original = (path.read_bytes(), path.with_suffix(".csv.json").read_bytes())
    monkeypatch.setattr(data, "_download_market", lambda *args, **kwargs: b"not,a,market,snapshot\n")

    with pytest.raises(RuntimeError, match="Required market data GLD unavailable"):
        data.refresh_sources(config, force=True)

    assert (path.read_bytes(), path.with_suffix(".csv.json").read_bytes()) == original


def test_current_year_cot_cache_respects_freshness_ttl(tmp_path, monkeypatch):
    from capstone import data

    data, _, raw, _, archive_bytes = _download_cache_fixture(tmp_path, monkeypatch)
    year = pd.Timestamp.now(tz="UTC").year
    path = raw / "cftc" / f"{year}.zip"
    url = data.CFTC_URL.format(year=year)
    _write_snapshot(path, archive_bytes, url)
    metadata_path = path.with_suffix(".zip.json")
    metadata = json.loads(metadata_path.read_text())
    metadata["downloaded_at"] = (pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=25)).isoformat()
    metadata_path.write_text(json.dumps(metadata))

    valid, reason = data._cot_cache_status(path, year, url, ttl_hours=24)

    assert not valid
    assert "hours old" in reason


def test_cache_coverage_respects_provider_history_start(tmp_path, monkeypatch, caplog):
    from capstone import data

    data, config, raw, _, _ = _download_cache_fixture(tmp_path, monkeypatch)
    sol = make_synthetic_market_bars(["2020-08-11", "2024-01-03"])
    _write_snapshot(
        raw / "market" / "SOL-USD.csv", sol.to_csv(index=False).encode(),
        f"Binance Spot: {data.BINANCE_KLINES_URL}?symbol=SOLUSDT&interval=1d (USDT quote)",
        observed_at=pd.Timestamp("2024-01-04T22:00:00Z").to_pydatetime(),
    )
    source = f"Binance Spot: {data.BINANCE_KLINES_URL}?symbol=SOLUSDT&interval=1d (USDT quote)"
    valid, reason = data._market_cache_status(
        raw / "market" / "SOL-USD.csv", "SOL-USD", source,
        start="2018-01-01", end="2024-01-04", history_start="2020-08-11",
    )

    assert valid, reason


def test_market_cache_expected_bar_tracks_session_close():
    from capstone.data import _latest_expected_bar_date

    before_close = _latest_expected_bar_date("GLD", None, pd.Timestamp("2024-01-03T20:59:00Z"))
    after_close = _latest_expected_bar_date("GLD", None, pd.Timestamp("2024-01-03T21:01:00Z"))
    assert before_close == pd.Timestamp("2024-01-02")
    assert after_close == pd.Timestamp("2024-01-03")


def test_failed_optional_refresh_does_not_reuse_older_cache(tmp_path, monkeypatch, caplog):
    caplog.set_level("WARNING", logger="capstone.download")
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
    assert "market NVDA: optional source failed: fixture refresh failure" in caplog.text
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
