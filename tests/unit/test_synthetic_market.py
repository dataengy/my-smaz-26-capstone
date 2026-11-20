"""Contracts for deterministic synthetic fixtures; never empirical market data."""
import pandas as pd
from pandas.testing import assert_frame_equal

from tests.fixtures.synthetic_market import (
    make_synthetic_cot_positions,
    make_synthetic_market_bars,
    make_synthetic_sources,
)


def test_synthetic_market_factory_is_deterministic_and_provider_shaped():
    dates = pd.date_range("2024-03-04", periods=4, freq="B")

    first = make_synthetic_market_bars(dates, start_price=100.0, daily_step=1.0)
    second = make_synthetic_market_bars(dates, start_price=100.0, daily_step=1.0)

    assert_frame_equal(first, second)
    assert list(first.columns) == ["date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
    assert first["date"].tolist() == dates.strftime("%Y-%m-%d").tolist()
    assert first["Close"].tolist() == [100.0, 101.0, 102.0, 103.0]


def test_synthetic_cot_requires_explicit_release_time_and_is_marked_as_fixture():
    cot = make_synthetic_cot_positions(
        report_date="2024-03-05",
        available_at="2024-03-08T22:00:00Z",
    )

    assert set(cot["ticker"]) == {"GLD", "SLV"}
    assert set(cot["available_at"]) == {"2024-03-08T22:00:00Z"}
    assert cot["source_url"].str.startswith("https://example.invalid/").all()


def test_synthetic_research_sources_are_repeatable_and_have_only_expected_keys():
    dates = pd.date_range("2024-03-04", periods=4, freq="B")
    options = {
        "cot_report_date": "2024-03-05",
        "cot_available_at": "2024-03-08T22:00:00Z",
    }

    first = make_synthetic_sources(dates, **options)
    second = make_synthetic_sources(dates, **options)

    assert set(first) == {"GLD", "SLV", "cot"}
    for key in first:
        assert_frame_equal(first[key], second[key])
