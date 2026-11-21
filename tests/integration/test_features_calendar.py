"""Point-in-time integration against the actual exchange calendar."""
import pandas as pd
import pytest

from capstone.features import build_features
from tests.fixtures.synthetic_market import make_synthetic_sources


def test_cot_cannot_arrive_after_signal_and_target_holds_five_sessions():
    pytest.importorskip("exchange_calendars")
    dates = pd.bdate_range("2024-03-04", periods=12)
    sources = make_synthetic_sources(
        dates,
        cot_report_date="2024-03-05",
        cot_available_at="2024-03-08T22:00:00Z",
    )
    frame = build_features(sources, {})
    gld = frame[frame.ticker == "GLD"].reset_index(drop=True)
    assert gld.date.min() == pd.Timestamp("2024-03-11")
    assert gld.loc[0, "entry_date"] == pd.Timestamp("2024-03-12")
    assert gld.loc[0, "exit_date"] == pd.Timestamp("2024-03-19")
    assert gld.loc[0, "target"] == pytest.approx(111 / 106 - 1)
    assert pd.isna(gld.iloc[-1].target)
