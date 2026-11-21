"""Fetch and cache public market data and CFTC disaggregated futures archives.

A cache is a research input, not an assertion that the provider data is point in time.
Market snapshots are stored as CSV, CFTC archives as original ZIP bytes. Each has a
SHA-256 sidecar; offline reads verify it and never contact the network.
"""
from __future__ import annotations

import hashlib
import io
import json
import urllib.request
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

SYMBOLS = {s: s for s in ("GLD", "SLV", "BTC-USD", "SOL-USD", "ETH-USD", "ZEC-USD", "NVDA", "^GSPC", "^IXIC", "^DJI")}
REQUIRED = {"GLD", "SLV", "BTC-USD", "NVDA"}
CFTC_URL = "https://www.cftc.gov/files/dea/history/fut_disagg_txt_{year}.zip"


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


def _write_snapshot(path: Path, payload: bytes, source: str, *, observed_at: datetime | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    metadata = {
        "sha256": hashlib.sha256(payload).hexdigest(), "source": source,
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
    }
    if observed_at is not None:
        metadata["observed_at"] = observed_at.isoformat()
    path.with_suffix(path.suffix + ".json").write_text(json.dumps(metadata, indent=2) + "\n")


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
    except ImportError as exc:
        raise RuntimeError("Install project dependencies to download market data (yfinance missing)") from exc
    frame = yf.download(symbol, start=start, end=end, auto_adjust=False, progress=False,
                        threads=False, multi_level_index=False, timeout=timeout)
    if frame.empty:
        raise ValueError(f"No market prices returned for {symbol}")
    # Preserve the provider's daily bar label as a date, independent of DST.
    frame.index = pd.DatetimeIndex(frame.index).strftime("%Y-%m-%d")
    frame.index.name = "date"
    return frame.to_csv().encode()


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


def refresh_sources(config: dict) -> dict[str, str]:
    """Download snapshots and report optional market sources that failed.

    Existing optional snapshots are left on disk for intentional offline replay,
    but callers can avoid mistaking one for a successful refresh in this run.
    """
    start = config.get("start", "2018-01-01")
    end = config.get("end")
    root = Path(config.get("data_dir", "data")) / "raw"
    symbols, required = _active_symbols(config)
    market_timeout = int(config.get("market_download_timeout_seconds", 30))
    cftc_timeout = int(config.get("cftc_download_timeout_seconds", 45))
    if market_timeout < 1 or cftc_timeout < 1:
        raise ValueError("Download timeouts must be positive")
    failures: dict[str, str] = {}
    for name, symbol in symbols.items():
        path = root / "market" / f"{_safe_symbol(name)}.csv"
        try:
            # Capture before the request: an in-flight response can straddle the close.
            observed_at = datetime.now(timezone.utc)
            _write_snapshot(path, _download_market(symbol, start, end, timeout=market_timeout), f"Yahoo Finance: {symbol}",
                            observed_at=observed_at)
        except (ValueError, RuntimeError, OSError) as exc:
            if name in required:
                raise RuntimeError(f"Required market data {name} unavailable: {exc}") from exc
            failures[name] = f"{type(exc).__name__}: {exc}"
            print(f"Optional market data {name} unavailable: {exc}")
    first = pd.Timestamp(start).year
    last = (pd.Timestamp(end) - pd.Timedelta(days=1)).year if end else date.today().year
    for year in range(first, last + 1):
        url = CFTC_URL.format(year=year)
        with urllib.request.urlopen(url, timeout=cftc_timeout) as response:
            payload = response.read()
        parse_cot_archive(payload)  # Refuse to cache an invalid response.
        _write_snapshot(root / "cftc" / f"{year}.zip", payload, url)
    return failures


def load_sources(config: dict, refresh: bool = False) -> dict[str, pd.DataFrame]:
    """Read verified local snapshots by default; refresh downloads fresh snapshots.

    start is inclusive and end is exclusive. Optional markets can be unavailable;
    their absence is reported, while missing required series or COT data fails.
    """
    refresh_failures = {}
    if refresh:
        refresh_failures = refresh_sources(config) or {}
    start = config.get("start", "2018-01-01")
    end = config.get("end")
    root = Path(config.get("data_dir", "data")) / "raw"
    symbols, required = _active_symbols(config)
    result = {}
    for name, symbol in symbols.items():
        if name in refresh_failures:
            # Do not silently replace this run's failed refresh with an older cache.
            continue
        path = root / "market" / f"{_safe_symbol(name)}.csv"
        try:
            frame = pd.read_csv(io.BytesIO(_read_snapshot(path)), parse_dates=["date"])
            metadata = json.loads(path.with_suffix(path.suffix + ".json").read_text())
            if metadata.get("source") != f"Yahoo Finance: {symbol}":
                raise ValueError(f"Market snapshot {name} has different provider ticker; refresh it")
            observed_at = metadata.get("observed_at")
            if not observed_at:
                raise ValueError(f"Market snapshot {name} lacks request-start observed_at; refresh it")
            frame = _completed_market_bars(frame, symbol, observed_at)
            if frame.empty:
                raise ValueError(f"Empty market snapshot: {name}")
            # The snapshot may have been fetched over a wider period than this run.
            # Bar dates are date labels (not availability timestamps).
            dates = _local_bar_dates(frame["date"])
            selected = dates >= pd.Timestamp(start).normalize()
            if end:
                selected &= dates < pd.Timestamp(end).normalize()
            frame = frame.loc[selected].copy()
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
    return result
