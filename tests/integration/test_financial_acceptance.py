"""Hand-calculated checks for holdout-only simulation and benchmark alignment."""

import pandas as pd
import pytest

from capstone.backtest import run_backtest


def test_simulation_uses_only_test_orders_and_matches_benchmark_window():
    dates = pd.bdate_range("2024-01-02", periods=2)
    prices = pd.DataFrame(
        [
            {"date": date, "ticker": ticker, "adjusted_open": price}
            for date, prices_by_ticker in zip(
                dates,
                ({"GLD": 100.0, "SLV": 100.0}, {"GLD": 110.0, "SLV": 100.0}),
            )
            for ticker, price in prices_by_ticker.items()
        ]
    )
    predictions = pd.DataFrame(
        [
            {
                "split": "validation",
                "ticker": "GLD",
                "entry_date": pd.Timestamp("2023-12-01"),
                "exit_date": pd.Timestamp("2023-12-04"),
                "prediction": 1.0,
            },
            {
                "split": "test",
                "ticker": "GLD",
                "entry_date": dates[0],
                "exit_date": dates[1],
                "prediction": 0.1,
            },
            {
                "split": "test",
                "ticker": "SLV",
                "entry_date": dates[0],
                "exit_date": dates[1],
                "prediction": -0.1,
            },
        ]
    )

    result = run_backtest(
        predictions,
        prices,
        {"initial_capital": 100.0, "cost_bps": 100, "holding_sessions": 1},
    )

    metrics = result["metrics"].set_index("strategy")
    one_side_cost_net_return = (1 + 0.1) * 0.99 / 1.01 - 1
    expected_strategy_return = 0.5 * one_side_cost_net_return
    expected_benchmark_return = (
        0.5 * ((1 + 0.1) * 0.99 / 1.01 - 1)
        + 0.5 * (0.99 / 1.01 - 1)
    )

    assert metrics.loc["long_cash", "total_return"] == pytest.approx(
        expected_strategy_return
    )
    assert metrics.loc["buy_hold", "total_return"] == pytest.approx(
        expected_benchmark_return
    )
    strategy_windows = result["equity"].groupby("strategy").date.agg(["min", "max"])
    assert set(strategy_windows.index) == {"buy_hold", "long_cash", "threshold"}
    assert (strategy_windows["min"] == dates[0]).all()
    assert (strategy_windows["max"] == dates[1]).all()

    trades = result["trades"]
    assert set(trades.ticker) == {"GLD"}
    assert set(trades.side) == {"buy", "sell"}
    assert set(trades.date) == set(dates)
    assert trades.query("strategy == 'long_cash'").cash_flow.tolist() == pytest.approx(
        [-50.0, 50.0 * 110.0 * 0.99 / (100.0 * 1.01)]
    )


def test_duplicate_execution_price_is_rejected():
    dates = pd.bdate_range("2024-01-02", periods=2)
    prices = pd.DataFrame(
        [
            {"date": date, "ticker": ticker, "adjusted_open": 100.0}
            for date in dates
            for ticker in ("GLD", "SLV")
        ]
    )
    prices = pd.concat([prices, prices.iloc[[0]]], ignore_index=True)
    predictions = pd.DataFrame(
        [
            {
                "split": "test",
                "ticker": ticker,
                "entry_date": dates[0],
                "exit_date": dates[1],
                "prediction": 0.1,
            }
            for ticker in ("GLD", "SLV")
        ]
    )

    with pytest.raises(ValueError, match="Duplicate prices"):
        run_backtest(predictions, prices)
