"""Deterministic synthetic source-shaped data for tests only.

Every COT source URL uses ``example.invalid`` and all values are constructed.
These fixtures are not historical observations and must never enter research
results or the project's downloaded snapshot directory.
"""
from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd


def make_synthetic_market_bars(
    dates: Iterable[object],
    *,
    start_price: float = 100.0,
    daily_step: float = 1.0,
) -> pd.DataFrame:
    """Return a small deterministic OHLCV table in Yahoo-like column form."""
    input_dates = list(dates)
    if not input_dates:
        raise ValueError("Synthetic market bars require at least one date")
    parsed_dates = [pd.Timestamp(value) for value in input_dates]
    if len({value.date() for value in parsed_dates}) != len(parsed_dates):
        raise ValueError("Synthetic market bar dates must be unique")
    labels = [
        value if isinstance(value, str) else parsed.strftime("%Y-%m-%d")
        for value, parsed in zip(input_dates, parsed_dates)
    ]

    close = start_price + daily_step * np.arange(len(labels), dtype=float)
    open_price = close.copy()
    low = pd.Series(close) - 0.5
    if not (pd.Series(close).gt(0).all() and low.gt(0).all()):
        raise ValueError("Synthetic OHLC prices must remain positive")
    return pd.DataFrame({
        "date": labels,
        "Open": open_price,
        "High": pd.Series(close) + 0.5,
        "Low": low,
        "Close": close,
        "Adj Close": close,
        "Volume": 1_000 + 100 * pd.RangeIndex(len(labels)).to_numpy(),
    })


def make_synthetic_cot_positions(
    *,
    report_date: str,
    available_at: str,
    tickers: tuple[str, ...] = ("GLD", "SLV"),
) -> pd.DataFrame:
    """Return made-up COT positions with an explicitly supplied UTC cutoff."""
    available = pd.Timestamp(available_at)
    if available.tzinfo is None:
        raise ValueError("Synthetic COT available_at must include an explicit timezone")
    available_utc = available.tz_convert("UTC").isoformat().replace("+00:00", "Z")
    rows = []
    for index, ticker in enumerate(tickers):
        scale = index + 1
        rows.append({
            "ticker": ticker,
            "report_date": report_date,
            "available_at": available_utc,
            "source_url": "https://example.invalid/synthetic-cot-fixture",
            "open_interest": 10_000 * scale,
            "managed_long": 3_000 * scale,
            "managed_short": 1_000 * scale,
            "producer_long": 2_000 * scale,
            "producer_short": 4_000 * scale,
        })
    return pd.DataFrame(rows)


def make_synthetic_sources(
    dates: Iterable[object],
    *,
    cot_report_date: str,
    cot_available_at: str,
) -> dict[str, pd.DataFrame]:
    """Build repeatable GLD/SLV bars and COT rows for point-in-time tests."""
    date_index = pd.DatetimeIndex(dates)
    return {
        "GLD": make_synthetic_market_bars(date_index),
        "SLV": make_synthetic_market_bars(date_index),
        "cot": make_synthetic_cot_positions(
            report_date=cot_report_date,
            available_at=cot_available_at,
        ),
    }
