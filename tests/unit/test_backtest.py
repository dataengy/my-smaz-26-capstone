import pandas as pd
import pytest
from capstone.backtest import run_backtest


def test_costs_and_cash_accounting_on_flat_prices():
    dates = pd.bdate_range('2024-01-02', periods=6)
    prices = pd.DataFrame([{'date': d, 'ticker': t, 'adjusted_open': 100.} for d in dates for t in ('GLD', 'SLV')])
    predictions = pd.DataFrame([{'split': 'test', 'ticker': t, 'entry_date': dates[0], 'exit_date': dates[-1], 'prediction': .1} for t in ('GLD', 'SLV')])
    result = run_backtest(predictions, prices, {'initial_capital': 100., 'cost_bps': 100})
    metrics = result['metrics'].set_index('strategy')
    assert metrics.loc['buy_hold', 'total_return'] == pytest.approx(.99 / 1.01 - 1)
    equity = result['equity']
    assert equity.cash.min() >= -1e-10
    assert len(result['trades'].query("strategy == 'long_cash' and side == 'buy'")) == 2
    assert len(result['trades'].query("strategy == 'long_cash' and side == 'sell'")) == 2
    assert metrics.loc['long_cash', 'total_return'] < 0


def test_missing_price_rejected():
    predictions = pd.DataFrame([{'split': 'test', 'ticker': t, 'entry_date': '2024-01-01', 'exit_date': '2024-01-03', 'prediction': .1} for t in ('GLD', 'SLV')])
    prices = pd.DataFrame([{'date': '2024-01-01', 'ticker': 'GLD', 'adjusted_open': 100.}])
    with pytest.raises(ValueError, match='Missing or invalid'):
        run_backtest(predictions, prices)


def test_missing_intermediate_price_for_one_ticker_is_rejected():
    dates = pd.bdate_range('2024-01-02', periods=6)
    predictions = pd.DataFrame([{'split': 'test', 'ticker': t, 'entry_date': dates[0], 'exit_date': dates[-1], 'prediction': .1} for t in ('GLD', 'SLV')])
    prices = pd.DataFrame([{'date': d, 'ticker': t, 'adjusted_open': 100.} for d in dates for t in ('GLD', 'SLV') if not (d == dates[2] and t == 'SLV')])
    with pytest.raises(ValueError, match='Missing or invalid'):
        run_backtest(predictions, prices)


def test_vectorized_fixed_notional_and_two_sided_costs():
    from capstone.backtest import run_vectorized_backtest
    signals = pd.DataFrame([
        {'split': 'test', 'ticker': ticker, 'entry_date': '2024-01-02', 'exit_date': '2024-01-09',
         'prediction': prediction, 'target': target}
        for ticker, prediction, target in [('GLD', .1, .1), ('SLV', -.1, .5)]
    ])
    result = run_vectorized_backtest(signals, {'initial_capital': 100., 'cost_bps': 100})
    expected_net_return = 1.1 * .99 / 1.01 - 1
    assert result['metrics']['trade_count'] == 1
    assert result['equity'].equity.iloc[0] == 100
    assert result['equity'].equity.iloc[-1] == pytest.approx(100 + 10 * expected_net_return)
    assert result['metrics']['total_return'] == pytest.approx(expected_net_return / 10)


def test_overlapping_positions_cannot_spend_more_cash_than_available():
    dates = pd.bdate_range('2024-01-02', periods=7)
    predictions = pd.DataFrame([
        {'split': 'test', 'ticker': t, 'entry_date': dates[i], 'exit_date': dates[i + 5],
         'prediction': .1 if t == 'GLD' else -.1}
        for i in range(2) for t in ('GLD', 'SLV')
    ])
    prices = pd.DataFrame([
        {'date': d, 'ticker': t, 'adjusted_open': 10000. if t == 'GLD' and i >= 1 else 100.}
        for i, d in enumerate(dates) for t in ('GLD', 'SLV')
    ])
    result = run_backtest(predictions, prices, {'initial_capital': 100., 'cost_bps': 0})
    buys = result['trades'].query("strategy == 'long_cash' and side == 'buy'")
    assert buys.cash_flow.tolist() == pytest.approx([-10., -90.])
    curve = result['equity'].query("strategy == 'long_cash'")
    assert curve.cash.min() == pytest.approx(0.)
    assert curve.equity.iloc[-1] == pytest.approx(1090.)


def test_rejects_infinite_prices_before_simulation():
    dates = pd.bdate_range('2024-01-02', periods=6)
    predictions = pd.DataFrame([{'split': 'test', 'ticker': t, 'entry_date': dates[0],
                                 'exit_date': dates[-1], 'prediction': .1} for t in ('GLD', 'SLV')])
    prices = pd.DataFrame([{'date': d, 'ticker': t, 'adjusted_open': float('inf') if d == dates[2] and t == 'GLD' else 100.}
                           for d in dates for t in ('GLD', 'SLV')])
    with pytest.raises(ValueError, match='Missing or invalid'):
        run_backtest(predictions, prices)
