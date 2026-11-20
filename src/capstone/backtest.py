"""Event-ordered daily-open simulation with overlapping, fully funded long lots.

``run_backtest(predictions, prices, config=None)`` returns equity and metrics.
Prices contain date, ticker and adjusted_open and must cover the entire test window.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def _metrics(curve, initial_capital):
    values = curve['equity']
    duration = (curve.date.iloc[-1] - curve.date.iloc[0]).days / 365.25
    daily = values.pct_change().dropna()
    volatility = daily.std(ddof=1)
    return {'total_return': float(values.iloc[-1] / initial_capital - 1),
            'cagr': float((values.iloc[-1] / initial_capital) ** (1 / duration) - 1) if duration > 0 else np.nan,
            'sharpe': float(np.sqrt(252) * daily.mean() / volatility) if len(daily) > 1 and volatility > 0 else np.nan,
            'max_drawdown': float((values / values.cummax().clip(lower=initial_capital) - 1).min())}


def run_backtest(predictions, prices, config=None):
    """Simulate two long/cash policies and equal-weight buy-and-hold on test only.

    Inputs are predictions with split, ticker, entry_date, exit_date, prediction,
    and daily prices with date, ticker, adjusted_open. Config: initial_capital
    (100000), cost_bps per side (10), threshold (0), holding_sessions (5).
    A lot spends at most 1/(assets*holding_sessions) of marked equity at entry;
    sales execute before purchases, available cash caps purchases. Positions are
    marked at daily adjusted opens, with costs assessed on both executions.
    Threshold is chosen externally using validation, never from test.
    Returns {'equity': DataFrame, 'metrics': DataFrame, 'trades': DataFrame}.
    """
    cfg = config or {}
    capital = float(cfg.get('initial_capital', 100000))
    cost = float(cfg.get('cost_bps', 10)) / 10000
    threshold = float(cfg.get('threshold', 0))
    holding = int(cfg.get('holding_sessions', 5))
    if capital <= 0 or not 0 <= cost < 1 or threshold < 0 or holding < 1:
        raise ValueError('Invalid capital, costs, threshold or holding sessions')
    signals = predictions[predictions['split'] == 'test'].copy()
    if signals.empty:
        raise ValueError('No test predictions to simulate')
    for col in ['entry_date', 'exit_date']:
        signals[col] = pd.to_datetime(signals[col])
    if signals[['entry_date', 'exit_date', 'prediction']].isna().any().any():
        raise ValueError('Test signals require entry, exit and prediction')
    if (signals.exit_date <= signals.entry_date).any() or signals.duplicated(['entry_date', 'ticker']).any():
        raise ValueError('Invalid or duplicate test orders')
    px = prices.copy()
    px['date'] = pd.to_datetime(px.date)
    if px.duplicated(['date', 'ticker']).any():
        raise ValueError('Duplicate prices')
    tickers = sorted(signals.ticker.unique())
    if tickers != sorted(cfg.get('target_symbols', ['GLD', 'SLV'])):
        raise ValueError('Test predictions must match configured target symbols')
    start, end = signals.entry_date.min(), signals.exit_date.max()
    panel = px[px.ticker.isin(tickers) & px.date.between(start, end)].pivot(index='date', columns='ticker', values='adjusted_open').sort_index()
    if panel.empty or panel.index.min() != start or panel.index.max() != end or not set(tickers).issubset(panel.columns) or not np.isfinite(panel[tickers].to_numpy(dtype=float)).all() or (panel[tickers] <= 0).any().any():
        raise ValueError('Missing or invalid adjusted open prices in test window')
    if not set(signals.entry_date).union(set(signals.exit_date)).issubset(set(panel.index)):
        raise ValueError('Execution date absent from prices')
    events = []
    results = []
    for name, limit in [('long_cash', 0.0), ('threshold', threshold), ('buy_hold', None)]:
        cash = capital
        lots = []
        values = []
        for date, day_prices in panel.iterrows():
            if name == 'buy_hold':
                if date == start:
                    for ticker in tickers:
                        budget = capital / len(tickers)
                        shares = budget / (float(day_prices[ticker]) * (1 + cost))
                        cash -= budget
                        lots.append({'ticker': ticker, 'shares': shares, 'exit_date': end})
                if date == end:
                    for lot in lots:
                        cash += lot['shares'] * float(day_prices[lot['ticker']]) * (1 - cost)
                    lots = []
            else:
                remaining = []
                for lot in lots:
                    if lot['exit_date'] == date:
                        proceeds = lot['shares'] * float(day_prices[lot['ticker']]) * (1 - cost)
                        cash += proceeds
                        events.append({'strategy': name, 'date': date, 'ticker': lot['ticker'], 'side': 'sell', 'cash_flow': proceeds})
                    else:
                        remaining.append(lot)
                lots = remaining
                orders = signals[(signals.entry_date == date) & (signals.prediction > limit)].sort_values('ticker')
                for order in orders.itertuples():
                    equity = cash + sum(lot['shares'] * float(day_prices[lot['ticker']]) for lot in lots)
                    budget = min(cash, equity / (len(tickers) * holding))
                    if budget <= 0:
                        continue
                    shares = budget / (float(day_prices[order.ticker]) * (1 + cost))
                    cash -= budget
                    lots.append({'ticker': order.ticker, 'shares': shares, 'exit_date': order.exit_date})
                    events.append({'strategy': name, 'date': date, 'ticker': order.ticker, 'side': 'buy', 'cash_flow': -budget})
            equity = cash + sum(lot['shares'] * float(day_prices[lot['ticker']]) for lot in lots)
            values.append({'date': date, 'strategy': name, 'equity': equity, 'cash': cash})
        curve = pd.DataFrame(values)
        # Include initial costs in return/drawdown; Sharpe uses actual daily intervals.
        results.append((curve, {'strategy': name, **_metrics(curve, capital)}))
    return {'equity': pd.concat([x[0] for x in results], ignore_index=True),
            'metrics': pd.DataFrame([x[1] for x in results]),
            'trades': pd.DataFrame(events, columns=['strategy', 'date', 'ticker', 'side', 'cash_flow'])}


def run_vectorized_backtest(predictions, config=None):
    """Approximate fixed-notional long/cash test via vectorized closed-trade P&L.

    Inputs are held-out predictions with split, ticker, entry_date, exit_date,
    prediction and target. Config defaults to initial_capital=100000,
    holding_sessions=5, cost_bps=10 per side, and threshold=0. Threshold must
    be set before looking at the test period. For each positive signal, reserve
    a fixed 1/(2*holding_sessions) share of initial capital; compute net P&L
    using the known entry-to-exit return and accumulate it at exit.

    This is an approximate, non-reinvesting comparison: equity is marked only
    when lots close, and it assumes the fixed budgets remain affordable. It does
    not claim daily mark-to-market, capital constraints or Sharpe. Use the
    event-ordered simulation above for those properties. Returns equity and
    trades DataFrames and a metrics dict, explicitly labeled as approximate.
    """
    cfg = config or {}
    capital = float(cfg.get('initial_capital', 100000))
    cost = float(cfg.get('cost_bps', 10)) / 10000
    threshold = float(cfg.get('threshold', 0))
    holding = int(cfg.get('holding_sessions', 5))
    if capital <= 0 or not 0 <= cost < 1 or threshold < 0 or holding < 1:
        raise ValueError('Invalid capital, costs, threshold or holding sessions')
    data = predictions[predictions['split'] == 'test'].copy()
    if data.empty or sorted(data.ticker.unique()) != sorted(cfg.get('target_symbols', ['GLD', 'SLV'])):
        raise ValueError('Test predictions must match configured target symbols')
    for col in ('entry_date', 'exit_date'):
        data[col] = pd.to_datetime(data[col])
    if data[['entry_date', 'exit_date', 'prediction', 'target']].isna().any().any():
        raise ValueError('Test rows must have execution dates, predictions and targets')
    if (data.exit_date <= data.entry_date).any() or (data.target <= -1).any() or data.duplicated(['entry_date', 'ticker']).any():
        raise ValueError('Invalid or duplicate test orders')
    selected = data.loc[data.prediction > threshold].copy()
    selected['net_return'] = (1 + selected.target) * (1 - cost) / (1 + cost) - 1
    selected['pnl'] = capital / (2 * holding) * selected.net_return
    realized = selected.groupby('exit_date')['pnl'].sum()
    dates = pd.DatetimeIndex(sorted(set(realized.index) | {data.entry_date.min(), data.exit_date.max()}))
    equity = pd.DataFrame({'date': dates, 'equity': capital + realized.reindex(dates, fill_value=0).cumsum().to_numpy()})
    equity['strategy'] = 'vectorized_long_cash_approximate'
    metrics = {'strategy': 'vectorized_long_cash_approximate',
               'total_return': float(equity.equity.iloc[-1] / capital - 1),
               'trade_count': int(len(selected))}
    return {'equity': equity, 'trades': selected, 'metrics': metrics}
