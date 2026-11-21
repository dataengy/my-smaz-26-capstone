"""Read-only Streamlit interactions on a tiny explicitly fictional bundle."""
from pathlib import Path

import pytest

pytest.importorskip('streamlit')
pytest.importorskip('plotly')
from streamlit.testing.v1 import AppTest

from tests.unit.test_reporting import saved_run  # shared fictional bundle fixture

APP = Path(__file__).resolve().parents[2] / 'src/capstone/dashboard.py'


def test_dashboard_filters_errors_without_changing_portfolio(saved_run, monkeypatch):
    monkeypatch.setenv('CAPSTONE_RESEARCH_RUN', str(saved_run))
    app = AppTest.from_file(APP).run(timeout=30)
    assert not app.exception
    assert len(app.tabs) == 4
    assert app.metric[0].value == 'mean'
    portfolio = next(item.value for item in app.dataframe if 'total_return' in item.value.columns)
    next(item for item in app.selectbox if item.label == 'Ticker diagnostics').select('GLD').run(timeout=30)
    assert not app.exception
    filtered = next(item.value for item in app.dataframe if {'ticker', 'mae', 'bias'}.issubset(item.value.columns))
    assert filtered.ticker.tolist() == ['GLD']
    current = next(item.value for item in app.dataframe if 'total_return' in item.value.columns)
    assert current.equals(portfolio)


def test_dashboard_rejects_tampered_run(saved_run, monkeypatch):
    monkeypatch.setenv('CAPSTONE_RESEARCH_RUN', str(saved_run))
    (saved_run / 'run-1/equity.csv').write_text('tampered\n')
    app = AppTest.from_file(APP).run(timeout=30)
    assert not app.exception
    assert any('Integrity check failed' in item.value for item in app.error)
    assert not app.metric
