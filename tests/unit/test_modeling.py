import json

import numpy as np
import pandas as pd
import pytest
from capstone.modeling import fit_predict


def test_chronological_selection_purges_labels_and_predicts_latest():
    dates = pd.bdate_range('2020-01-01', periods=150)
    rows = []
    for i, date in enumerate(dates):
        for ticker in ('GLD', 'SLV'):
            rows.append({'date': date, 'ticker': ticker, 'feature': np.sin(i / 8),
                         'empty_feature': np.nan, 'target': np.cos(i / 11) / 100 if i < 144 else np.nan,
                         'exit_date': dates[i + 6] if i < 144 else pd.NaT})
    frame = pd.DataFrame(rows)
    result = fit_predict(frame, ['feature', 'empty_feature'])
    assert pd.Timestamp(result['split_dates']['train_last_exit']) < pd.Timestamp(result['split_dates']['validation_start'])
    assert pd.Timestamp(result['split_dates']['validation_last_exit']) < pd.Timestamp(result['split_dates']['test_start'])
    assert len(result['model_metrics'].query("split == 'test'")) == 1
    assert len(result['predictions'].query("split == 'latest'")) == 2
    assert result['predictions'].query("split == 'latest'").date.nunique() == 1
    assert np.isfinite(result['predictions'].prediction).all()


def test_insufficient_history_fails_explicitly():
    frame = pd.DataFrame({'date': pd.date_range('2020-01-01', periods=3), 'ticker': 'GLD',
                          'target': 0.01, 'exit_date': pd.date_range('2020-01-02', periods=3), 'x': 1})
    with pytest.raises(ValueError, match='40 labeled'):
        fit_predict(frame, ['x'])


def test_split_boundaries_use_configured_signal_dates_and_purge_horizon():
    dates = pd.bdate_range('2022-01-03', periods=100)
    # Both assets have 10-session labels. The last labeled signals have longer
    # exits, so deriving boundaries from surviving/purged rows would shift them.
    frame = pd.DataFrame([
        {'date': date, 'ticker': ticker, 'x': float(i), 'target': i / 1000,
         'exit_date': dates[min(i + 10, len(dates) - 1)]}
        for i, date in enumerate(dates[:-10]) for ticker in ('GLD', 'SLV')
    ])
    result = fit_predict(frame, ['x'], {'train_fraction': .6, 'validation_fraction': .2})

    assert result['split_dates']['validation_start'] == str(dates[int(90 * .6)].date())
    assert result['split_dates']['test_start'] == str(dates[int(90 * .8)].date())
    assert pd.Timestamp(result['split_dates']['train_last_exit']) < pd.Timestamp(
        result['split_dates']['validation_start']
    )
    assert pd.Timestamp(result['split_dates']['validation_last_exit']) < pd.Timestamp(
        result['split_dates']['test_start']
    )


def test_heldout_labels_do_not_select_model_threshold_or_change_predictions():
    dates = pd.bdate_range('2020-01-01', periods=130)
    frame = pd.DataFrame([
        {'date': date, 'ticker': ticker, 'feature': np.sin(i / 7),
         'target': np.cos(i / 9) / 100 if i + 6 < len(dates) else np.nan,
         'exit_date': dates[i + 6] if i + 6 < len(dates) else pd.NaT}
        for i, date in enumerate(dates) for ticker in ('GLD', 'SLV')
    ])
    baseline = fit_predict(frame, ['feature'])
    changed = frame.copy()
    heldout = (changed.date >= pd.Timestamp(baseline['split_dates']['test_start'])) & changed.target.notna()
    changed.loc[heldout, 'target'] += 1.0
    repeated = fit_predict(changed, ['feature'])
    assert repeated['selected_model'] == baseline['selected_model']
    assert repeated['selected_threshold'] == baseline['selected_threshold']
    pd.testing.assert_frame_equal(repeated['model_comparison'], baseline['model_comparison'])
    np.testing.assert_allclose(repeated['predictions'].prediction, baseline['predictions'].prediction)
    assert repeated['model_metrics'].query("split == 'test'").mae.iloc[0] > .5


def test_saved_estimator_predicts_from_raw_ticker_and_numeric_features(tmp_path):
    import joblib

    dates = pd.bdate_range('2021-01-01', periods=100)
    frame = pd.DataFrame([
        {'date': date, 'ticker': ticker, 'feature': np.nan if i % 7 == 0 else i / 100,
         'target': np.cos(i / 10) / 100 if i + 6 < len(dates) else np.nan,
         'exit_date': dates[i + 6] if i + 6 < len(dates) else pd.NaT}
        for i, date in enumerate(dates) for ticker in ('GLD', 'SLV')
    ])
    result = fit_predict(frame, ['feature'])
    latest = result['predictions'].query("split == 'latest'")
    path = tmp_path / 'model.joblib'
    joblib.dump(result['estimator'], path)
    restored = joblib.load(path)
    raw = latest[['ticker', 'feature']].copy()
    actual = restored.predict(raw)
    np.testing.assert_allclose(actual, latest.prediction)
    raw.loc[raw.index[0], 'feature'] = np.nan
    assert np.isfinite(restored.predict(raw)).all()


@pytest.mark.parametrize('constant_target', [False, True])
def test_validation_comparison_reports_parameters_and_train_only_baseline(constant_target):
    # Fictional returns; constant targets also exercise deterministic MAE ties.
    dates = pd.bdate_range('2020-01-01', periods=100)
    frame = pd.DataFrame([
        {'date': date, 'ticker': ticker, 'feature': float(i),
         'target': 0.0 if constant_target else np.sin(i / 7) / 100,
         'exit_date': date + pd.offsets.BDay(6)}
        for i, date in enumerate(dates) for ticker in ('GLD', 'SLV')
    ])
    cfg = {'ridge_alphas': [2.5], 'tree_depths': [4], 'tree_min_samples_leaf': 3,
           'forest_depths': [2], 'forest_estimators': 3, 'forest_min_samples_leaf': 2,
           'random_state': 17}
    result = fit_predict(frame, ['feature'], cfg)
    comparison = result['model_comparison']
    assert comparison.model.is_unique
    assert set(comparison.estimator) == {
        'DummyRegressor', 'Ridge', 'DecisionTreeRegressor', 'RandomForestRegressor'}
    assert comparison.split.eq('validation').all()
    assert comparison.mae.is_monotonic_increasing
    assert comparison.selected.sum() == 1
    assert comparison.loc[comparison.selected, 'model'].item() == result['selected_model']
    assert comparison.iloc[0].model == result['selected_model']
    rows = comparison.set_index('model')
    assert json.loads(rows.loc['mean', 'parameters'])['strategy'] == 'mean'
    assert json.loads(rows.loc['ridge_2.5', 'parameters'])['alpha'] == 2.5
    tree = json.loads(rows.loc['tree_4', 'parameters'])
    assert (tree['max_depth'], tree['min_samples_leaf'], tree['random_state']) == (4, 3, 17)
    forest = json.loads(rows.loc['forest_2', 'parameters'])
    assert (forest['max_depth'], forest['n_estimators'], forest['min_samples_leaf'],
            forest['random_state'], forest['n_jobs']) == (2, 3, 2, 17, 1)
    train = frame[(frame.date < dates[60]) & (frame.exit_date < dates[60])]
    val = frame[(frame.date >= dates[60]) & (frame.date < dates[80]) & (frame.exit_date < dates[80])]
    errors = val.target - train.target.mean()
    assert rows.loc['mean', 'mae'] == pytest.approx(errors.abs().mean())
    assert rows.loc['mean', 'rmse'] == pytest.approx(np.sqrt((errors ** 2).mean()))
    if constant_target:
        assert result['selected_model'] == 'mean'
