"""Tiny fictional saved results; these are not market-performance evidence."""
import hashlib
import json

import numpy as np
import pandas as pd
import pytest

from capstone.reporting import load_run, equity_series, error_summary, feature_correlations


@pytest.fixture
def saved_run(tmp_path):
    bundle = tmp_path / 'fictional-run'
    output = bundle / 'run-1'
    output.mkdir(parents=True)
    inputs = bundle / 'inputs'
    inputs.mkdir()
    config = inputs / 'effective-config.json'
    config.write_text(json.dumps({'initial_capital': 100, 'market_features': {}}))
    dates = pd.date_range('2024-01-01', periods=10)
    tables = {
        'features': pd.DataFrame({'date': dates, 'ticker': 'GLD', 'return_1': np.arange(10.),
                                 'target': [0., 1., 2., 3., -4., -5., -6., -7., -8., np.nan],
                                 'exit_date': dates + pd.Timedelta(days=1)}),
        'model_comparison': pd.DataFrame([{'model': 'mean', 'split': 'validation', 'mae': .02,
                                          'rmse': .03, 'estimator': 'DummyRegressor',
                                          'parameters': '{"strategy":"mean"}', 'selected': True}]),
        'metrics': pd.DataFrame([{'strategy': 'buy_hold', 'total_return': -.1, 'cagr': -.2,
                                 'sharpe': -1., 'max_drawdown': -.25, 'transaction_costs': .1}]),
        'equity': pd.DataFrame({'date': dates[:3], 'strategy': 'buy_hold',
                               'equity': [99., 120., 90.], 'cash': 0.}),
        'test_errors': pd.DataFrame({'date': dates[7:9], 'ticker': ['GLD', 'SLV'],
                                    'target': [.01, -.01], 'prediction': [.03, -.04]}),
        'split_counts': pd.DataFrame([{'split': 'train', 'ticker': 'GLD', 'rows_after': 3,
                                      'dates_after': 3, 'purged_rows': 1}]),
        'latest_signals': pd.DataFrame([{'date': dates[-1], 'ticker': 'GLD', 'prediction': .01,
                                        'signal': True, 'model_training_last_exit': '2024-01-07'}]),
        'holdout_comparison': pd.DataFrame([{'model': 'mean', 'mae': .02, 'rmse': .03}]),
    }
    for name, table in tables.items():
        table.to_csv(output / f'{name}.csv', index=False)
    (output / 'summary.json').write_text(json.dumps({
        'selected_model': 'mean', 'selected_threshold': 0.,
        'split_dates': {'validation_start': '2024-01-05', 'test_start': '2024-01-08',
                        'validation_last_exit': '2024-01-07'},
        'model_training_last_exit': '2024-01-07',
    }))
    (bundle / 'evidence.json').write_text(json.dumps({
        'status': 'reproduced', 'coverage': {'failures': []},
        'numeric_output_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in output.iterdir()},
        'input_sha256': {'effective-config.json': hashlib.sha256(config.read_bytes()).hexdigest()},
    }))
    return bundle


def test_saved_run_is_read_only_and_computations_reconcile(saved_run):
    before = {str(p): p.read_bytes() for p in saved_run.rglob('*') if p.is_file()}
    run = load_run(saved_run)
    curve = equity_series(run)
    np.testing.assert_allclose(curve.net_return, [-.01, .2, -.1])
    np.testing.assert_allclose(curve.drawdown, [-.01, 0., -.25])
    errors = error_summary(run).set_index('ticker')
    assert errors.loc['GLD', 'mae'] == pytest.approx(.02)
    assert errors.loc['SLV', 'rmse'] == pytest.approx(.03)
    assert errors.loc['SLV', 'bias'] == pytest.approx(-.03)
    assert feature_correlations(run).loc['return_1'] == pytest.approx(1.)
    assert before == {str(p): p.read_bytes() for p in saved_run.rglob('*') if p.is_file()}


@pytest.mark.parametrize('failure', ['tamper', 'missing', 'blocked', 'traversal', 'config'])
def test_invalid_evidence_fails_before_display(saved_run, failure):
    evidence_file = saved_run / 'evidence.json'
    evidence = json.loads(evidence_file.read_text())
    if failure == 'tamper':
        (saved_run / 'run-1/equity.csv').write_text('incorrect\n')
    elif failure == 'missing':
        (saved_run / 'run-1/equity.csv').unlink()
    elif failure == 'blocked':
        evidence['status'] = 'blocked_insufficient_confirmed_cot_history'
    elif failure == 'traversal':
        evidence['numeric_output_sha256']['../outside.csv'] = '0' * 64
    else:
        (saved_run / 'inputs/effective-config.json').write_text('{}')
    evidence_file.write_text(json.dumps(evidence))
    with pytest.raises(ValueError):
        load_run(saved_run)


def test_empty_ticker_group_remains_empty(saved_run):
    run = load_run(saved_run)
    assert error_summary(run, 'UNKNOWN').empty
    assert feature_correlations(run, 'UNKNOWN').empty
