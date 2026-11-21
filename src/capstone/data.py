"""Fetch and cache public market data and CFTC disaggregated futures archives.

A cache is a research input, not an assertion that the provider data is point in time.
Market snapshots are stored as CSV, CFTC archives as original ZIP bytes. Each has a
SHA-256 sidecar; offline reads verify it and never contact the network.
"""
from __future__ import annotations

import hashlib
import io
import json
import logging
import math
import os
import tempfile
import urllib.parse
import urllib.error
import urllib.request
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

SYMBOLS = {s: s for s in ("GLD", "SLV", "BTC-USD", "SOL-USD", "ETH-USD", "ZEC-USD", "NVDA", "^GSPC", "^IXIC", "^DJI")}
REQUIRED = {"GLD", "SLV", "BTC-USD", "NVDA"}
CFTC_URL = "https://www.cftc.gov/files/dea/history/fut_disagg_txt_{year}.zip"
CFTC_USER_AGENT = "Mozilla/5.0 (compatible; capstone-research/1.0)"
BINANCE_KLINES_URL = "https://data-api.binance.vision/api/v3/klines"
BINANCE_KLINES_LIMIT = 1000
LOGGER = logging.getLogger("capstone.download")


def _active_symbols(config: dict) -> tuple[dict[str, str], set[str]]:
    symbols = config.get("symbols", SYMBOLS)
    required = set(config.get("required_symbols", REQUIRED))
    targets = set(config.get("target_symbols", ("GLD", "SLV")))
    feature_symbols = set(config.get("market_features", symbols).keys())
    active = required | targets | feature_symbols
    missing = active - symbols.keys()
    if missing:
        raise ValueError(f"Configured active symbols have no provider ticker: {sorted(missing)}")
    return {name: ticker for name, ticker in symbols.items() if name in active}, required


def _local_bar_dates(values: pd.Series) -> pd.Series:
    """Preserve each provider daily label's local calendar date across DST offsets.

    Converting mixed-offset labels to UTC first can move a bar into a different
    calendar date. Strip each label's timezone while retaining its wall date.
    """
    def date_label(value):
        parsed = pd.Timestamp(value)
        if pd.isna(parsed):
            raise ValueError("Missing daily bar date")
        return pd.Timestamp(parsed.date())
    return pd.to_datetime(values.map(date_label), errors="raise")


def _safe_symbol(symbol: str) -> str:
    return symbol.replace("^", "index_").replace("/", "_")


def _market_source(name: str, default_ticker: str, config: dict) -> tuple[str, str, str]:
    """Resolve the provider ticker and provenance label for a configured series."""
    setting = config.get("market_sources", {}).get(name, {})
    provider = setting.get("provider", "yahoo")
    ticker = setting.get("ticker", default_ticker)
    if provider not in {"yahoo", "binance"}:
        raise ValueError(f"Unsupported market provider for {name}: {provider!r}")
    if not isinstance(ticker, str) or not ticker.strip():
        raise ValueError(f"Market provider ticker must be a non-empty string for {name}")
    label = (
        f"Yahoo Finance: {ticker}"
        if provider == "yahoo"
        else f"Binance Spot: {BINANCE_KLINES_URL}?symbol={ticker}&interval=1d (USDT quote)"
    )
    return provider, ticker, label


def _write_snapshot(path: Path, payload: bytes, source: str, *, observed_at: datetime | None = None) -> None:
    """Persist a verified snapshot, leaving identical content and provenance untouched.

    In particular, preserve the original request-start cutoff when a provider
    returns the same bytes again. Re-stamping an identical partial daily bar at
    a later time could otherwise make it appear complete during offline replay.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(payload).hexdigest()
    meta_path = path.with_suffix(path.suffix + ".json")
    if path.is_file() and meta_path.is_file():
        try:
            existing = json.loads(meta_path.read_text())
            existing_observed = existing.get("observed_at")
            has_required_cutoff = observed_at is None or bool(existing_observed)
            same_snapshot = (
                has_required_cutoff
                and existing.get("source") == source
                and existing.get("sha256") == digest
                and hashlib.sha256(path.read_bytes()).hexdigest() == digest
            )
            if same_snapshot:
                return
        except (OSError, json.JSONDecodeError):
            # Repair an unreadable/missing sidecar by rewriting this snapshot.
            pass
    metadata = {
        "sha256": digest, "source": source,
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
    }
    if observed_at is not None:
        metadata["observed_at"] = observed_at.isoformat()
    raw_fd, raw_tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    meta_fd, meta_tmp_name = tempfile.mkstemp(prefix=f".{meta_path.name}.", suffix=".tmp", dir=path.parent)
    raw_tmp, meta_tmp = Path(raw_tmp_name), Path(meta_tmp_name)
    try:
        with os.fdopen(raw_fd, "wb") as handle:
            handle.write(payload)
        with os.fdopen(meta_fd, "w", encoding="utf-8") as handle:
            json.dump(metadata, handle, indent=2)
            handle.write("\n")
        os.replace(raw_tmp, path)
        # Metadata is the commit marker: a crash before this replace leaves a
        # checksum mismatch that offline readers reject instead of partial data.
        os.replace(meta_tmp, meta_path)
    finally:
        raw_tmp.unlink(missing_ok=True)
        meta_tmp.unlink(missing_ok=True)


def _read_snapshot(path: Path) -> bytes:
    meta_path = path.with_suffix(path.suffix + ".json")
    if not path.exists() or not meta_path.exists():
        raise FileNotFoundError(f"Missing cached data or hash metadata: {path}; run with refresh enabled")
    payload = path.read_bytes()
    meta = json.loads(meta_path.read_text())
    if hashlib.sha256(payload).hexdigest() != meta.get("sha256"):
        raise ValueError(f"SHA-256 mismatch for {path}")
    return payload


def _completed_market_bars(frame: pd.DataFrame, symbol: str, observed_at: str) -> pd.DataFrame:
    """Exclude bars unfinished when the provider request began, not at replay time.

    A later offline replay cannot turn a partial cached close into a complete bar.
    For equities and indices the XNYS calendar supplies actual session close,
    including early closes. UTC daily crypto bars complete at the next midnight.
    """
    cutoff = pd.Timestamp(observed_at)
    if pd.isna(cutoff) or cutoff.tzinfo is None:
        raise ValueError("Market snapshot observed_at must be timezone-aware")
    cutoff = cutoff.tz_convert("UTC")
    dates = _local_bar_dates(frame["date"])
    if symbol.endswith("-USD"):
        known_at = (dates + pd.Timedelta(days=1)).dt.tz_localize("UTC")
        return frame.loc[known_at <= cutoff].copy()
    try:
        import exchange_calendars as xcals
    except ImportError as exc:
        raise RuntimeError("exchange_calendars is required to validate market snapshot close times") from exc
    cal = xcals.get_calendar("XNYS")
    # NYSE closes the same UTC date; definitely older dates require no calendar lookup.
    cutoff_day = cutoff.tz_localize(None).normalize()
    complete = dates < cutoff_day
    for index in dates.index[dates == cutoff_day]:
        session = dates.loc[index]
        if not cal.is_session(session):
            raise ValueError(f"{symbol} has a price bar on non-session {session.date()}")
        complete.loc[index] = cal.session_close(session) <= cutoff
    return frame.loc[complete].copy()


def _download_market(symbol: str, start: str, end: str | None, timeout: int = 30) -> bytes:
    try:
        import yfinance as yf
    except ModuleNotFoundError as exc:
        if exc.name == "yfinance":
            raise RuntimeError(
                "Install project dependencies to download market data (yfinance missing)"
            ) from exc
        raise RuntimeError(
            f"yfinance could not be imported because dependency {exc.name!r} is unavailable"
        ) from exc
    except ImportError as exc:
        raise RuntimeError(f"yfinance could not be imported: {exc}") from exc
    frame = yf.download(symbol, start=start, end=end, auto_adjust=False, progress=False,
                        threads=False, multi_level_index=False, timeout=timeout)
    if frame.empty:
        raise ValueError(f"No market prices returned for {symbol}")
    # Preserve the provider's daily bar label as a date, independent of DST.
    frame.index = pd.DatetimeIndex(frame.index).strftime("%Y-%m-%d")
    frame.index.name = "date"
    return frame.to_csv().encode()


def _download_binance_market(symbol: str, start: str, end: str | None, timeout: int = 30) -> bytes:
    """Fetch paginated UTC daily Spot klines and return the shared market CSV shape."""
    start_ms = int(pd.Timestamp(start, tz="UTC").timestamp() * 1_000)
    end_ms = int(pd.Timestamp(end, tz="UTC").timestamp() * 1_000) - 1 if end else None
    next_start_ms = start_ms
    rows: list[list] = []
    while True:
        params = {
            "symbol": symbol,
            "interval": "1d",
            "limit": BINANCE_KLINES_LIMIT,
            "startTime": next_start_ms,
        }
        if end_ms is not None:
            params["endTime"] = end_ms
        url = f"{BINANCE_KLINES_URL}?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(url, headers={"User-Agent": CFTC_USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                page = json.loads(response.read())
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"Binance Spot klines request failed for {symbol}: HTTP {exc.code} {exc.reason} ({url})"
            ) from exc
        if not isinstance(page, list):
            raise ValueError(f"Binance returned an invalid kline response for {symbol}: expected a JSON array")
        if not page:
            break
        if any(not isinstance(row, list) or len(row) < 12 for row in page):
            raise ValueError(f"Binance returned a malformed kline row for {symbol}")
        rows.extend(page)
        if len(page) < BINANCE_KLINES_LIMIT:
            break
        next_start_ms = int(page[-1][6]) + 1
        if end_ms is not None and next_start_ms > end_ms:
            break

    if not rows:
        raise ValueError(f"Binance returned no klines for {symbol} in the requested range")
    frame = pd.DataFrame(rows, columns=[
        "open_time", "Open", "High", "Low", "Close", "Volume", "close_time",
        "quote_volume", "trades", "taker_base_volume", "taker_quote_volume", "ignore",
    ])
    frame["date"] = pd.to_datetime(pd.to_numeric(frame.open_time), unit="ms", utc=True).dt.strftime("%Y-%m-%d")
    for column in ("Open", "High", "Low", "Close", "Volume"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    frame["Adj Close"] = frame["Close"]
    frame = frame[["date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]]
    if frame.date.duplicated().any() or not frame.date.is_monotonic_increasing:
        raise ValueError(f"Binance returned duplicate or unordered daily klines for {symbol}")
    return frame.to_csv(index=False).encode()


def parse_cot_archive(payload: bytes) -> pd.DataFrame:
    """Extract COMEX gold and silver positions from an official annual ZIP."""
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith((".txt", ".csv"))]
        if len(names) != 1:
            raise ValueError(f"Expected one CFTC text file in archive, found {names}")
        with archive.open(names[0]) as handle:
            raw = pd.read_csv(handle, dtype={"CFTC_Contract_Market_Code": str}, low_memory=False)
    # CFTC documents As_of_Date_Form_YYYY-MM-DD; some exports use Report_Date_as_YYYY-MM-DD.
    if "Report_Date_as_YYYY-MM-DD" not in raw and "As_of_Date_Form_YYYY-MM-DD" in raw:
        raw = raw.rename(columns={"As_of_Date_Form_YYYY-MM-DD": "Report_Date_as_YYYY-MM-DD"})
    needed = {"CFTC_Contract_Market_Code", "Report_Date_as_YYYY-MM-DD", "Open_Interest_All",
              "M_Money_Positions_Long_All", "M_Money_Positions_Short_All",
              "Prod_Merc_Positions_Long_All", "Prod_Merc_Positions_Short_All"}
    missing = needed - set(raw.columns)
    if missing:
        raise ValueError(f"CFTC archive missing columns: {sorted(missing)}")
    codes = raw["CFTC_Contract_Market_Code"].astype(str).str.strip().str.zfill(6)
    out = raw.loc[codes.isin(["088691", "084691"])].copy()
    if out.empty:
        raise ValueError("CFTC archive contains no COMEX gold or silver records")
    out["ticker"] = codes.loc[out.index].map({"088691": "GLD", "084691": "SLV"})
    out = out.rename(columns={"Report_Date_as_YYYY-MM-DD": "report_date", "Open_Interest_All": "open_interest",
        "M_Money_Positions_Long_All": "managed_long", "M_Money_Positions_Short_All": "managed_short",
        "Prod_Merc_Positions_Long_All": "producer_long", "Prod_Merc_Positions_Short_All": "producer_short"})
    if out.duplicated(["ticker", "report_date"]).any():
        raise ValueError("Duplicate COT ticker/report dates in archive")
    cols = ["ticker", "report_date", "open_interest", "managed_long", "managed_short", "producer_long", "producer_short"]
    return out[cols]


def _download_cot_archive(year: int, timeout: int = 45) -> tuple[str, bytes]:
    """Download and validate one CFTC archive with headers accepted by the provider."""
    url = CFTC_URL.format(year=year)
    request = urllib.request.Request(url, headers={"User-Agent": CFTC_USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"CFTC archive request failed for {url}: HTTP {exc.code} {exc.reason}"
        ) from exc
    parse_cot_archive(payload)  # Refuse to cache an invalid response.
    return url, payload


def _latest_expected_bar_date(symbol: str, end: str | None, now: pd.Timestamp | None = None) -> pd.Timestamp:
    """Last bar date that should be complete at ``now`` for this source type."""
    current = pd.Timestamp(now or datetime.now(timezone.utc))
    if current.tzinfo is None:
        raise ValueError("Download cache clock must be timezone-aware")
    current = current.tz_convert("UTC")
    upper = current.normalize()
    if end:
        upper = min(upper, (pd.Timestamp(end).normalize() - pd.Timedelta(days=1)).tz_localize("UTC"))
    if symbol.endswith("-USD"):
        return min(upper, current.normalize() - pd.Timedelta(days=1)).tz_localize(None).normalize()

    import exchange_calendars as xcals

    calendar = xcals.get_calendar("XNYS")
    session = calendar.date_to_session(upper.tz_localize(None), direction="previous")
    if calendar.session_close(session) > current or pd.Timestamp(session).tz_localize(None) > upper.tz_localize(None):
        session = calendar.previous_session(session)
    return pd.Timestamp(session).tz_localize(None).normalize()


def _market_cache_status(
    path: Path, name: str, source_label: str, start: str, end: str | None,
    history_start: str | None = None,
) -> tuple[bool, str]:
    """Return whether a local market snapshot is valid and complete for this run."""
    try:
        payload = _read_snapshot(path)
        meta_path = path.with_suffix(path.suffix + ".json")
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        if metadata.get("source") != source_label:
            return False, "provider/ticker provenance differs from current configuration"
        observed_at = metadata.get("observed_at")
        if not observed_at:
            return False, "request-start timestamp is missing"
        frame = pd.read_csv(io.BytesIO(payload), parse_dates=["date"])
        required = {"Open", "High", "Low", "Close", "Adj Close", "Volume"}
        missing = required - set(frame.columns)
        if missing:
            return False, f"missing market fields {sorted(missing)}"
        dates = _local_bar_dates(frame.date)
        if dates.duplicated().any() or not dates.is_monotonic_increasing:
            return False, "market dates are duplicated or unordered"
        frame["date"] = dates
        completed = _completed_market_bars(frame, name, observed_at)
        selected = dates.loc[completed.index] >= pd.Timestamp(start).normalize()
        if end:
            selected &= dates.loc[completed.index] < pd.Timestamp(end).normalize()
        completed = completed.loc[selected]
        if completed.empty:
            return False, "no completed observations in the configured date range"
        for column in ("Close", "Adj Close"):
            values = pd.to_numeric(completed[column], errors="coerce")
            if values.isna().any() or not values.map(math.isfinite).all():
                return False, f"completed {column} values contain null or non-finite data"
        latest = _local_bar_dates(completed.date).max()
        expected = _latest_expected_bar_date(name, end)
        if latest < expected:
            return False, f"latest complete bar {latest.date()} is behind expected {expected.date()}"
        first = _local_bar_dates(completed.date).min()
        start_date = max(pd.Timestamp(start).normalize(), pd.Timestamp(history_start or start).normalize())
        if name.endswith("-USD"):
            first_expected = start_date
        else:
            import exchange_calendars as xcals
            first_expected = pd.Timestamp(xcals.get_calendar("XNYS").date_to_session(start_date, direction="next")).tz_localize(None)
        if first > first_expected:
            return False, f"first complete bar {first.date()} is after expected start {first_expected.date()}"
        return True, f"valid rows={len(completed)} range={first.date()}..{latest.date()}"
    except (FileNotFoundError, ValueError, RuntimeError, OSError, KeyError, pd.errors.ParserError) as exc:
        return False, f"snapshot validation failed: {type(exc).__name__}: {exc}"


def _cot_cache_status(path: Path, year: int, source_url: str, ttl_hours: float) -> tuple[bool, str]:
    """Reuse valid historical COT archives; refresh the current archive by TTL."""
    try:
        payload = _read_snapshot(path)
        metadata = json.loads(path.with_suffix(path.suffix + ".json").read_text(encoding="utf-8"))
        if metadata.get("source") != source_url:
            return False, "archive source provenance differs"
        positions = parse_cot_archive(payload)
        if year == date.today().year:
            downloaded_at = pd.Timestamp(metadata.get("downloaded_at"))
            if downloaded_at.tzinfo is None:
                return False, "current archive retrieval timestamp is missing timezone"
            age = (pd.Timestamp.now(tz="UTC") - downloaded_at.tz_convert("UTC")).total_seconds() / 3600
            if age > ttl_hours:
                return False, f"current archive is {age:.1f} hours old (limit {ttl_hours:g})"
        return True, f"valid rows={len(positions)}"
    except (FileNotFoundError, ValueError, RuntimeError, OSError, KeyError, zipfile.BadZipFile) as exc:
        return False, f"archive validation failed: {type(exc).__name__}: {exc}"


def _validate_market_payload(payload: bytes, name: str, observed_at: datetime) -> tuple[int, str, str]:
    """Reject malformed provider responses before replacing a usable snapshot."""
    frame = pd.read_csv(io.BytesIO(payload), parse_dates=["date"])
    required = {"Open", "High", "Low", "Close", "Adj Close", "Volume"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Downloaded {name} data missing fields {sorted(missing)}")
    dates = _local_bar_dates(frame.date)
    if dates.duplicated().any() or not dates.is_monotonic_increasing:
        raise ValueError(f"Downloaded {name} data has duplicated or unordered dates")
    frame["date"] = dates
    completed = _completed_market_bars(frame, name, observed_at.isoformat())
    if completed.empty:
        raise ValueError(f"Downloaded {name} data has no completed bars at request start")
    for column in ("Close", "Adj Close"):
        values = pd.to_numeric(completed[column], errors="coerce")
        if values.isna().any() or not values.map(math.isfinite).all():
            raise ValueError(f"Downloaded {name} data has null or non-finite completed {column} values")
    complete_dates = _local_bar_dates(completed.date)
    return len(completed), complete_dates.min().date().isoformat(), complete_dates.max().date().isoformat()


def load_release_manifest(path: str | Path) -> pd.DataFrame:
    """Load individually evidenced UTC release timestamps; never infer one from weekdays."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Missing COT publication evidence manifest: {path}")
    manifest = pd.read_csv(path, dtype=str)
    expected = {"report_date", "available_at", "source_url"}
    if not expected.issubset(manifest.columns):
        raise ValueError(f"Release manifest must contain {sorted(expected)}")
    if manifest.empty:
        raise ValueError("Release manifest has no confirmed publications; add evidenced dates before running")
    if manifest[list(expected)].isna().any().any() or not manifest.source_url.str.startswith("https://").all():
        raise ValueError("Every release needs report date, UTC time and an HTTPS evidence URL")
    if not manifest.available_at.str.contains(r"(?:Z|[+-]00:00)$", regex=True).all():
        raise ValueError("Release availability must have an explicit UTC offset or Z")
    manifest["report_date"] = pd.to_datetime(manifest.report_date, errors="raise").dt.normalize()
    manifest["available_at"] = pd.to_datetime(manifest.available_at, utc=True, errors="raise")
    if manifest.report_date.duplicated().any():
        raise ValueError("Duplicate report dates in release manifest")
    if (manifest.available_at <= manifest.report_date.dt.tz_localize("UTC")).any():
        raise ValueError("A release must occur after its report date")
    return manifest


def refresh_sources(config: dict, *, force: bool = False) -> dict[str, str]:
    """Reuse valid snapshots, refresh invalid/stale ones, and report outcomes.

    Historical CFTC archives are immutable cache entries after checksum and
    schema validation. The current-year archive is refreshed after its configured
    TTL. Set ``force`` to fetch every configured source regardless of cache state.
    """
    start = config.get("start", "2018-01-01")
    end = config.get("end")
    root = Path(config.get("data_dir", "data")) / "raw"
    symbols, required = _active_symbols(config)
    market_timeout = int(config.get("market_download_timeout_seconds", 30))
    cftc_timeout = int(config.get("cftc_download_timeout_seconds", 45))
    cache_ttl = float(config.get("download_cache_ttl_hours", 24))
    if market_timeout < 1 or cftc_timeout < 1:
        raise ValueError("Download timeouts must be positive")
    if cache_ttl <= 0:
        raise ValueError("download_cache_ttl_hours must be positive")
    failures: dict[str, str] = {}
    downloaded = skipped = 0
    LOGGER.info("Starting source download: symbols=%d start=%s end=%s force=%s", len(symbols), start, end or "latest", force)
    for name, default_ticker in symbols.items():
        path = root / "market" / f"{_safe_symbol(name)}.csv"
        try:
            provider, ticker, source_label = _market_source(name, default_ticker, config)
            LOGGER.info("market %s: checking cache (%s ticker=%s)", name, provider, ticker)
            if not force:
                history_start = config.get("market_sources", {}).get(name, {}).get("history_start")
                valid, detail = _market_cache_status(path, name, source_label, start, end, history_start)
                if valid:
                    skipped += 1
                    LOGGER.info("market %s: cache valid; skipping (%s)", name, detail)
                    continue
                LOGGER.info("market %s: refreshing; %s", name, detail)
            else:
                LOGGER.info("market %s: force refresh enabled; downloading from %s (%s)", name, provider, ticker)
            # Capture before the request: an in-flight response can straddle the close.
            observed_at = datetime.now(timezone.utc)
            if provider == "binance":
                payload = _download_binance_market(ticker, start, end, timeout=market_timeout)
            else:
                payload = _download_market(ticker, start, end, timeout=market_timeout)
            rows, first_date, last_date = _validate_market_payload(payload, name, observed_at)
            _write_snapshot(path, payload, source_label, observed_at=observed_at)
            downloaded += 1
            digest = hashlib.sha256(payload).hexdigest()
            LOGGER.info("market %s: saved rows=%d range=%s..%s bytes=%d sha256=%s path=%s",
                        name, rows, first_date, last_date, len(payload), digest, path)
        except (ValueError, RuntimeError, OSError) as exc:
            if name in required:
                LOGGER.error("market %s: required source failed: %s", name, exc)
                LOGGER.info("Download summary: downloaded=%d skipped=%d failed=%d", downloaded, skipped, len(failures) + 1)
                raise RuntimeError(f"Required market data {name} unavailable: {exc}") from exc
            failures[name] = f"{type(exc).__name__}: {exc}"
            LOGGER.warning("market %s: optional source failed: %s", name, exc)
    first = pd.Timestamp(start).year
    last = (pd.Timestamp(end) - pd.Timedelta(days=1)).year if end else date.today().year
    for year in range(first, last + 1):
        path = root / "cftc" / f"{year}.zip"
        url = CFTC_URL.format(year=year)
        LOGGER.info("CFTC archive %d: checking cache (%s)", year, url)
        if not force:
            valid, detail = _cot_cache_status(path, year, url, cache_ttl)
            if valid:
                skipped += 1
                LOGGER.info("CFTC archive %d: cache valid; skipping (%s)", year, detail)
                continue
            LOGGER.info("CFTC archive %d: refreshing; %s", year, detail)
        else:
            LOGGER.info("CFTC archive %d: force refresh enabled", year)
        try:
            url, payload = _download_cot_archive(year, timeout=cftc_timeout)
            positions = parse_cot_archive(payload)
            _write_snapshot(path, payload, url)
            downloaded += 1
            LOGGER.info("CFTC archive %d: saved rows=%d bytes=%d sha256=%s path=%s",
                        year, len(positions), len(payload), hashlib.sha256(payload).hexdigest(), path)
        except (ValueError, RuntimeError, OSError, zipfile.BadZipFile) as exc:
            LOGGER.error("CFTC archive %d: failed: %s", year, exc)
            LOGGER.info("Download summary: downloaded=%d skipped=%d failed=%d", downloaded, skipped, len(failures) + 1)
            raise RuntimeError(f"CFTC archive {year} unavailable: {exc}") from exc
    LOGGER.info("Download summary: downloaded=%d skipped=%d failed=%d", downloaded, skipped, len(failures))
    return failures


def load_sources(config: dict, refresh: bool = False) -> dict[str, pd.DataFrame]:
    """Read verified local snapshots by default; refresh downloads fresh snapshots.

    start is inclusive and end is exclusive. Optional markets can be unavailable;
    their absence is reported, while missing required series or COT data fails.
    """
    refresh_failures = {}
    if refresh:
        # ``refresh=True`` has historically meant fetch now. Keep that contract;
        # the standalone download command is cache-aware unless --force is set.
        refresh_failures = refresh_sources(config, force=True) or {}
    start = config.get("start", "2018-01-01")
    end = config.get("end")
    root = Path(config.get("data_dir", "data")) / "raw"
    symbols, required = _active_symbols(config)
    result = {}
    for name, default_ticker in symbols.items():
        _, _, source_label = _market_source(name, default_ticker, config)
        if name in refresh_failures:
            # Do not silently replace this run's failed refresh with an older cache.
            continue
        path = root / "market" / f"{_safe_symbol(name)}.csv"
        try:
            frame = pd.read_csv(io.BytesIO(_read_snapshot(path)), parse_dates=["date"])
            metadata = json.loads(path.with_suffix(path.suffix + ".json").read_text())
            if metadata.get("source") != source_label:
                raise ValueError(f"Market snapshot {name} has different provider or ticker; refresh it")
            observed_at = metadata.get("observed_at")
            if not observed_at:
                raise ValueError(f"Market snapshot {name} lacks request-start observed_at; refresh it")
            # Use the configured series name, not the provider ticker: provider
            # aliases such as Binance's BTCUSDT must retain the UTC crypto cutoff.
            frame = _completed_market_bars(frame, name, observed_at)
            if frame.empty:
                raise ValueError(f"Empty market snapshot: {name}")
            if frame["date"].duplicated().any():
                raise ValueError(f"Duplicate market dates in snapshot: {name}")
            # The snapshot may have been fetched over a wider period than this run.
            # Bar dates are date labels (not availability timestamps).
            dates = _local_bar_dates(frame["date"])
            selected = dates >= pd.Timestamp(start).normalize()
            if end:
                selected &= dates < pd.Timestamp(end).normalize()
            frame = frame.loc[selected].sort_values("date", kind="stable").reset_index(drop=True)
            if frame.empty:
                raise ValueError(f"Snapshot {name} has no observations in requested period")
            result[name] = frame
        except (FileNotFoundError, ValueError, RuntimeError, OSError) as exc:
            if name in required:
                raise RuntimeError(f"Required market data {name} unavailable: {exc}") from exc
            print(f"Optional market data {name} unavailable: {exc}")
    missing = required - result.keys()
    if missing:
        raise ValueError(f"Missing required configured symbols: {sorted(missing)}")
    manifest = load_release_manifest(config.get("release_manifest", "config/release_dates.csv"))
    first = pd.Timestamp(start).year
    last = (pd.Timestamp(end) - pd.Timedelta(days=1)).year if end else date.today().year
    cot = []
    for year in range(first, last + 1):
        path = root / "cftc" / f"{year}.zip"
        cot.append(parse_cot_archive(_read_snapshot(path)))
    combined = pd.concat(cot, ignore_index=True)
    combined["report_date"] = pd.to_datetime(combined.report_date, errors="raise").dt.normalize()
    if combined.duplicated(["ticker", "report_date"]).any():
        raise ValueError("Duplicate COT ticker/report dates")
    result["cot"] = combined.merge(manifest, on="report_date", how="inner", validate="many_to_one")
    if result["cot"].empty:
        raise ValueError("No COT records match confirmed release evidence")
    result["cot"] = result["cot"].sort_values(["report_date", "ticker"], kind="stable").reset_index(drop=True)
    return result
