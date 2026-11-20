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
