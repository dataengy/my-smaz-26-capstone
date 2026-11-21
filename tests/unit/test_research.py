"""Research protocol checks. All generated observations here are fictional."""
import numpy as np
import pandas as pd
import pytest

from capstone.backtest import run_backtest
from capstone.modeling import fit_predict
from capstone.research import REQUIRED_OUTPUTS, compare_outputs, coverage, hashes


def fictional_frame(count=900):
    dates = pd.bdate_range('2018-01-01', periods=count + 6)
    return pd.DataFrame([
        {'date': d, 'exit_date': dates[i + 6], 'ticker': ticker,
         'report_date': dates[(i // 5) * 5], 'target': np.sin(i) / 100, 'x': float(i % 9)}
        for i, d in enumerate(dates[:count]) for ticker in ('GLD', 'SLV')
    ])


CFG = {'target_symbols': ['GLD', 'SLV'], 'train_fraction': .6, 'validation_fraction': .2}


def test_minimum_coverage_and_purging():
    frame = fictional_frame()
    result = coverage(frame, CFG)
    assert result['failures'] == []
    assert result['by_ticker'][0]['purged_partition_dates'] == {
        'train': 534, 'validation': 174, 'test': 180}
    assert coverage(frame.iloc[:62], CFG)['failures']
    frame['report_date'] = pd.Timestamp('2018-01-01')
    assert coverage(frame, CFG)['failures']  # Long price history alone is insufficient.


def test_numeric_replay_rejects_changed_or_missing_output(tmp_path):
    a, b = tmp_path / 'a', tmp_path / 'b'
    a.mkdir()
    b.mkdir()
    for p in (a, b):
        for name in REQUIRED_OUTPUTS:
            (p / name).write_text('return\n0.1\n')
    assert compare_outputs(a, b) == hashes(a)
    (b / 'metrics.csv').write_text('return\n0.2\n')
    with pytest.raises(ValueError, match='differ'):
        compare_outputs(a, b)
    (b / 'metrics.csv').unlink()
    with pytest.raises(ValueError):
        compare_outputs(a, b)


def test_identically_incomplete_replays_are_rejected(tmp_path):
    for name in ('a', 'b'):
        (tmp_path / name).mkdir()
        (tmp_path / name / 'metrics.csv').write_text('return\n0.1\n')
    with pytest.raises(ValueError, match='absent'):
        compare_outputs(tmp_path / 'a', tmp_path / 'b')


def test_snapshot_fingerprint_detects_tampering(tmp_path):
    path = tmp_path / 'snapshot.csv'
    path.write_text('price\n100\n')
    before = hashes(tmp_path)
    path.write_text('price\n101\n')
    assert hashes(tmp_path) != before


def test_baseline_and_split_evidence_do_not_change_selection():
    frame = fictional_frame(150)
    cfg = {**CFG, 'forest_estimators': 2}
    result = fit_predict(frame, ['x'], cfg)
    changed = frame.copy()
    changed.loc[changed.date >= result['split_dates']['test_start'], 'target'] += 2
    repeated = fit_predict(changed, ['x'], cfg)
    assert result['selected_model'] == repeated['selected_model']
    assert result['selected_threshold'] == repeated['selected_threshold']
    assert len(result['split_counts']) == 6
    baseline = result['holdout_comparison'].iloc[0]
    counts = result['split_counts'].set_index(['split', 'ticker'])
    assert counts.loc[('train', 'GLD'), 'purged_rows'] == 6
    assert counts.loc[('validation', 'GLD'), 'purged_rows'] == 6
    val = pd.Timestamp(result['split_dates']['validation_start'])
    test = pd.Timestamp(result['split_dates']['test_start'])
    refit = frame[((frame.date < val) & (frame.exit_date < val)) |
                  ((frame.date >= val) & (frame.date < test) & (frame.exit_date < test))]
    expected = abs(frame.loc[frame.date >= test, 'target'] - refit.target.mean()).mean()
    assert baseline['mae'] == pytest.approx(expected)


def test_recorded_costs_reconcile_flat_price_capital_loss():
    dates = pd.bdate_range('2024-01-02', periods=6)
    signals = pd.DataFrame([{'split': 'test', 'ticker': t, 'entry_date': dates[0],
                            'exit_date': dates[-1], 'prediction': .1} for t in ('GLD', 'SLV')])
    prices = pd.DataFrame([{'date': d, 'ticker': t, 'adjusted_open': 100.}
                           for d in dates for t in ('GLD', 'SLV')])
    result = run_backtest(signals, prices, {'initial_capital': 100., 'cost_bps': 100})
    for row in result['metrics'].itertuples():
        assert row.transaction_costs == pytest.approx(-100 * row.total_return)
        assert row.transaction_costs == pytest.approx(row.gross_traded_notional * .01)
        assert row.executions == 4
        assert row.round_trips == 2
