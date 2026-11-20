"""Point-in-time feature engineering for NYSE ETF close signals.

Signals occur at the actual NYSE session close, entry is next session's open,
and exit is the open six sessions after the signal (five held sessions).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .data import _local_bar_dates

BASE_NUMERIC = ["return_1", "return_5", "return_20", "volatility_5", "volatility_20",
                "price_to_ma_20", "volume_change_5", "cot_managed_net", "cot_producer_net",
                "cot_managed_change", "cot_age_days"]
DEFAULT_MARKET_FEATURES = {
    "BTC-USD": "btc", "SOL-USD": "sol", "ETH-USD": "eth", "ZEC-USD": "zec",
    "NVDA": "nvda", "^GSPC": "sp500", "^IXIC": "nasdaq", "^DJI": "dow",
}
# Full default feature catalog remains available for course-style explicit sets;
# the actual modeled columns are selected by ``numeric_features(config)``.
NUMERIC = BASE_NUMERIC + [f"{name}_return_5" for name in DEFAULT_MARKET_FEATURES.values()]
DUMMIES = ["ticker"]
TO_PREDICT = "target"


def _market_frame(raw: pd.DataFrame, label: str) -> pd.DataFrame:
    frame = raw.copy()
    frame.columns = [str(c).strip().lower().replace(" ", "_") for c in frame.columns]
    if not {"date", "open", "close", "adj_close", "volume"}.issubset(frame.columns):
        raise ValueError(f"{label} is missing OHLC/adjusted close/volume columns")
    # Provider dates are daily bar labels, not timestamps at which the bar was known.
    frame["date"] = _local_bar_dates(frame.date)
    if frame.date.duplicated().any():
        raise ValueError(f"Duplicate daily price rows for {label}")
    frame = frame.sort_values("date").reset_index(drop=True)
    for col in ("open", "close", "adj_close", "volume"):
        frame[col] = pd.to_numeric(frame[col], errors="raise")
    if frame[["open", "close", "adj_close"]].isna().any().any() or (frame[["open", "close", "adj_close"]] <= 0).any().any():
        raise ValueError(f"Invalid price in {label}")
    frame["adjusted_open"] = frame["open"] * frame["adj_close"] / frame["close"]
    return frame


def _session_closes(dates: pd.Series) -> pd.Series:
    try:
        import exchange_calendars as xcals
    except ImportError as exc:
        raise RuntimeError("exchange_calendars is required for accurate NYSE close timestamps") from exc
    cal = xcals.get_calendar("XNYS")
    result = []
    for dt in dates:
        try:
            close = cal.session_close(pd.Timestamp(dt))
        except (ValueError, KeyError) as exc:
            raise ValueError(f"Price date {dt} is not a NYSE session: {exc}") from exc
        result.append(pd.Timestamp(close).tz_convert("UTC"))
    return pd.Series(result, index=dates.index, dtype="datetime64[ns, UTC]")


def _other_returns(raw: pd.DataFrame, symbol: str, signals: pd.DataFrame, max_age_days: int = 4) -> pd.Series:
    frame = _market_frame(raw, symbol)
    frame["value"] = frame.adj_close.pct_change(5, fill_method=None)
    if symbol.endswith("-USD"):
        # Yahoo's crypto bars run 00:00 through 23:59:59 UTC; available next midnight.
        frame["known_at"] = (frame.date + pd.Timedelta(days=1)).dt.tz_localize("UTC")
    else:
        frame["known_at"] = _session_closes(frame.date)
    # The bounded tolerance accommodates long US holidays but avoids indefinite fill.
    values = pd.merge_asof(signals[["signal_at"]].sort_values("signal_at"),
                           frame[["known_at", "value"]].sort_values("known_at"),
                           left_on="signal_at", right_on="known_at", direction="backward",
                           tolerance=pd.Timedelta(days=max_age_days))
    return values.value.reset_index(drop=True)


def build_features(sources: dict[str, pd.DataFrame], config: dict) -> pd.DataFrame:
    """Build a row per confirmed-COT ETF signal; never use future prices as features.

    COT is joined by explicitly evidenced UTC release timestamp, with a configurable
    maximum age (default seven days). Missing or stale reports exclude signal rows.
    Labels and execution prices are retained for evaluation, never in NUMERIC.
    """
    if "cot" not in sources:
        raise ValueError("Confirmed COT records are required")
    cot = sources["cot"].copy()
    required_cot = {"ticker", "report_date", "available_at", "source_url", "open_interest", "managed_long", "managed_short", "producer_long", "producer_short"}
    if not required_cot.issubset(cot.columns):
        raise ValueError(f"Missing COT columns: {sorted(required_cot - set(cot.columns))}")
    cot["available_at"] = pd.to_datetime(cot.available_at, utc=True, errors="raise")
    cot["report_date"] = pd.to_datetime(cot.report_date, errors="raise")
    rows = []
    market_features = config.get("market_features", DEFAULT_MARKET_FEATURES)
    holding_sessions = int(config.get("holding_sessions", 5))
    if holding_sessions < 1:
        raise ValueError("holding_sessions must be positive")
    market_age = int(config.get("cross_market_max_age_days", 4))
    for ticker in config.get("target_symbols", ["GLD", "SLV"]):
        if ticker not in sources:
            raise ValueError(f"Missing target ETF {ticker}")
        frame = _market_frame(sources[ticker], ticker)
        frame["signal_at"] = _session_closes(frame.date)
        # Require a full exchange calendar: a missing bar must not silently shorten the horizon.
        import exchange_calendars as xcals
        calendar = xcals.get_calendar("XNYS")
        expected = calendar.sessions_in_range(frame.date.iloc[0], frame.date.iloc[-1]).tz_localize(None)
        if not pd.DatetimeIndex(frame.date).equals(expected):
            raise ValueError(f"{ticker} market snapshot contains missing/non-session dates")
        frame["ticker"] = ticker
        for n in (1, 5, 20):
            frame[f"return_{n}"] = frame.adj_close.pct_change(n, fill_method=None)
        for n in (5, 20):
            frame[f"volatility_{n}"] = frame["return_1"].rolling(n, min_periods=n).std()
        frame["price_to_ma_20"] = frame.adj_close / frame.adj_close.rolling(20, min_periods=20).mean() - 1
        frame["volume_change_5"] = frame.volume.pct_change(5, fill_method=None).replace([np.inf, -np.inf], np.nan)
        frame["entry_date"] = frame.date.shift(-1)
        frame["exit_date"] = frame.date.shift(-(holding_sessions + 1))
        frame["entry_open"] = frame.adjusted_open.shift(-1)
        frame["exit_open"] = frame.adjusted_open.shift(-(holding_sessions + 1))
        frame["target"] = frame.exit_open / frame.entry_open - 1
        for symbol, name in market_features.items():
            frame[f"{name}_return_5"] = _other_returns(sources[symbol], symbol, frame, market_age) if symbol in sources else np.nan
        positions = cot.loc[cot.ticker == ticker].sort_values("available_at").copy()
        if positions.empty:
            raise ValueError(f"No confirmed COT data for {ticker}")
        if positions.available_at.duplicated().any():
            raise ValueError(f"Duplicate COT availability timestamps for {ticker}")
        for c in ("open_interest", "managed_long", "managed_short", "producer_long", "producer_short"):
            positions[c] = pd.to_numeric(positions[c], errors="raise")
        if (positions.open_interest <= 0).any():
            raise ValueError("COT open interest must be positive")
        positions["cot_managed_net"] = (positions.managed_long - positions.managed_short) / positions.open_interest
        positions["cot_producer_net"] = (positions.producer_long - positions.producer_short) / positions.open_interest
        positions["cot_managed_change"] = positions.cot_managed_net.diff()
        # Drop duplicate ticker column before join to keep ETF label unambiguous.
        positions = positions.drop(columns="ticker")
        frame = pd.merge_asof(frame.sort_values("signal_at"), positions, left_on="signal_at", right_on="available_at", direction="backward", tolerance=pd.Timedelta(days=config.get("cot_max_age_days", 7)))
        frame["cot_age_days"] = (frame.signal_at - frame.available_at).dt.total_seconds() / 86400
        frame = frame.loc[frame.available_at.notna()].copy()
        rows.append(frame)
    result = pd.concat(rows, ignore_index=True).sort_values(["date", "ticker"]).reset_index(drop=True)
    if result.empty:
        raise ValueError("No ETF sessions have a timely, confirmed COT release")
    return result


def numeric_features(config: dict) -> list[str]:
    """Return base features plus only the cross-market series enabled in config."""
    return BASE_NUMERIC + [f"{name}_return_5" for name in config.get("market_features", DEFAULT_MARKET_FEATURES).values()]
