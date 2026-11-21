"""Chronological model selection and genuinely held-out predictions.

``fit_predict(frame, numeric_features, config=None)`` returns predictions, metrics,
selection metadata and the fitted estimator. Fractions split distinct session dates;
any label ending on or after the next partition's first signal is purged.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor


def _pipeline(estimator, numeric_features, tickers=('GLD', 'SLV')):
    # A fixed, known universe avoids learning ticker categories from future rows.
    # All learned transformations are fitted only through the enclosing pipeline.
    columns = ColumnTransformer([
        ('numeric', SimpleImputer(strategy="median", keep_empty_features=True), list(numeric_features)),
        ('ticker', OneHotEncoder(categories=[list(tickers)], drop='first', sparse_output=False), ['ticker']),
    ])
    return make_pipeline(columns, StandardScaler(), estimator)


def fit_predict(frame, numeric_features, config=None):
    """Fit models with purged time splits; return validation, test, latest predictions.

    Config: train_fraction=.6, validation_fraction=.2, random_state=42,
    thresholds=[0, .002, .005], cost_bps=10 (commission+slippage per side).
    ``frame`` must include date, ticker, target, exit_date and numeric features.
    Selection uses validation MAE, and validation net signal return for threshold.
    Test data are scored once after model selection and train+validation refit.
    """
    cfg = config or {}
    required = {'date', 'ticker', 'target', 'exit_date'} | set(numeric_features)
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if not numeric_features:
        raise ValueError("At least one numeric feature is required")
    data = frame.copy().sort_values(['date', 'ticker']).reset_index(drop=True)
    target_symbols = list(cfg.get('target_symbols', ['GLD', 'SLV']))
    if not set(data.ticker.dropna().unique()).issubset(target_symbols):
        raise ValueError(f'Only configured target symbols are supported: {target_symbols}')
    feature_cols = list(numeric_features) + ['ticker']
    data['date'] = pd.to_datetime(data['date'])
    data['exit_date'] = pd.to_datetime(data['exit_date'])
    labeled = data[data['target'].notna() & data['exit_date'].notna()].copy()
    # Partition by signal dates, independent of whether a label survives purging.
    # This ensures the boundaries describe the configured chronology rather than
    # shifting when label horizons or missing targets vary near the end.
    dates = np.sort(data.loc[data['target'].notna(), 'date'].unique())
    train_fraction = float(cfg.get('train_fraction', .6))
    val_fraction = float(cfg.get('validation_fraction', .2))
    if not (0 < train_fraction < 1 and 0 < val_fraction < 1 and train_fraction + val_fraction < 1):
        raise ValueError('Split fractions must be positive and sum to less than one')
    if len(dates) < 40:
        raise ValueError('At least 40 labeled session dates are required')
    val_start = pd.Timestamp(dates[int(len(dates) * train_fraction)])
    test_start = pd.Timestamp(dates[int(len(dates) * (train_fraction + val_fraction))])
    # A target is the return over (entry_date, exit_date]. It is safe in a
    # partition only when its exit is strictly before the next partition's
    # first signal, so no future partition outcome leaks across the boundary.
    train = labeled[(labeled.date < val_start) & (labeled.exit_date < val_start)]
    val = labeled[(labeled.date >= val_start) & (labeled.date < test_start) & (labeled.exit_date < test_start)]
    test = labeled[labeled.date >= test_start]
    if min(len(train), len(val), len(test)) < 5:
        raise ValueError('Insufficient observations after purging overlapping labels')
    seed = int(cfg.get('random_state', 42))
    tree_leaf = int(cfg.get('tree_min_samples_leaf', 20))
    forest_estimators = int(cfg.get('forest_estimators', 80))
    forest_leaf = int(cfg.get('forest_min_samples_leaf', 10))
    candidates = {
        'mean': DummyRegressor(strategy='mean'),
    }
    candidates.update({f'ridge_{alpha:g}': Ridge(alpha=float(alpha)) for alpha in cfg.get('ridge_alphas', [1.0, 10.0])})
    candidates.update({f'tree_{depth}': DecisionTreeRegressor(max_depth=int(depth), min_samples_leaf=tree_leaf, random_state=seed)
                       for depth in cfg.get('tree_depths', [3, 5])})
    candidates.update({f'forest_{depth}': RandomForestRegressor(n_estimators=forest_estimators, max_depth=int(depth),
                       min_samples_leaf=forest_leaf, random_state=seed, n_jobs=1)
                       for depth in cfg.get('forest_depths', [3, 5])})
    score_rows = []
    fitted = {}
    for name, estimator in candidates.items():
        model = _pipeline(estimator, numeric_features, target_symbols)
        model.fit(train[feature_cols], train.target)
        p = model.predict(val[feature_cols])
        score_rows.append({'model': name, 'split': 'validation', 'mae': float(mean_absolute_error(val.target, p)), 'rmse': float(np.sqrt(mean_squared_error(val.target, p)))})
        fitted[name] = model
    winner = min(score_rows, key=lambda r: r['mae'])['model']
    val_pred = val.copy()
    val_pred['prediction'] = fitted[winner].predict(val[feature_cols])
    val_pred['split'] = 'validation'
    cost = float(cfg.get('cost_bps', 10)) / 10000
    thresholds = [float(x) for x in cfg.get('thresholds', [0, .002, .005])]
    if not thresholds or any(x < 0 for x in thresholds) or cost < 0:
        raise ValueError('Thresholds and costs must be nonnegative')
    # Proxy averaged over all opportunities; avoids rewarding sparse activity by
    # dividing only by trades. This is a tuning objective, not a backtest result.
    threshold_scores = {t: float(np.where(val_pred.prediction > t, (1 + val_pred.target) * (1 - cost) / (1 + cost) - 1, 0).mean()) for t in thresholds}
    threshold = max(thresholds, key=lambda t: threshold_scores[t])
    final = _pipeline(candidates[winner], numeric_features, target_symbols)
    final.fit(pd.concat([train, val])[feature_cols], pd.concat([train, val]).target)
    test_pred = test.copy()
    test_pred['prediction'] = final.predict(test[feature_cols])
    test_pred['split'] = 'test'
    score_rows.append({'model': winner, 'split': 'test', 'mae': float(mean_absolute_error(test.target, test_pred.prediction)), 'rmse': float(np.sqrt(mean_squared_error(test.target, test_pred.prediction)))})
    latest = data[data.date == data.date.max()].copy()
    latest['prediction'] = final.predict(latest[feature_cols])
    latest['split'] = 'latest'
    return {'predictions': pd.concat([val_pred, test_pred, latest], ignore_index=True),
            'model_metrics': pd.DataFrame(score_rows), 'selected_model': winner,
            'selected_threshold': threshold, 'threshold_scores': threshold_scores,
            'split_dates': {'validation_start': str(val_start.date()), 'test_start': str(test_start.date()),
                            'train_last_exit': str(train.exit_date.max().date()), 'validation_last_exit': str(val.exit_date.max().date())},
            'estimator': final}
