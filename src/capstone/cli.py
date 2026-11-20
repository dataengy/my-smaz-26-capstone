"""Project workflow: acquire, derive, train, simulate and report."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from .data import load_sources
from .features import build_features, _market_frame, numeric_features
from .config import read_config


def latest_signal_report(predictions, threshold, training_last_exit):
    """Expose the data cutoff of the frozen model alongside each latest signal."""
    latest = predictions.loc[predictions['split'] == 'latest', ['date', 'ticker', 'prediction']].copy()
    latest['signal'] = latest.prediction > threshold
    latest['model_training_last_exit'] = training_last_exit
    return latest


def save_eda(frame, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    data = frame[frame.target.notna()]
    features = [c for c in data.columns if c.endswith(("_return_5", "_net", "_change", "_days")) or c in {
        "return_1", "return_5", "return_20", "volatility_5", "volatility_20", "price_to_ma_20", "volume_change_5"}]
    data[['ticker', 'target'] + features].groupby('ticker').describe().to_csv(output / 'eda_summary.csv')
    data[['target'] + features].corr(numeric_only=True)['target'].sort_values().to_csv(output / 'target_correlations.csv')
    data[['target'] + features].isna().mean().to_csv(output / 'missingness.csv', header=['fraction_missing'])
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ticker, rows in data.groupby('ticker'):
        axes[0].hist(rows.target.dropna(), bins=40, alpha=.5, label=ticker)
        axes[1].plot(rows.date, rows.target, label=ticker, linewidth=.7)
    axes[0].set_title('Five-session target distribution')
    axes[1].set_title('Forward returns over time')
    for ax in axes:
        ax.legend()
    fig.tight_layout()
    fig.savefig(output / 'eda.png', dpi=120)
    plt.close(fig)


def execute(config, refresh=False, stage='run'):
    sources = load_sources(config, refresh=refresh)
    frame = build_features(sources, config)
    output = Path(config.get('output_dir', 'artifacts'))
    output.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output / 'features.csv', index=False)
    if stage == 'features':
        print(f'Features saved: {len(frame)} rows in {output}')
        return
    from .modeling import fit_predict
    from .backtest import run_backtest, run_vectorized_backtest
    import joblib
    result = fit_predict(frame, numeric_features(config), config)
    predictions = result['predictions']
    prices = []
    for ticker in config['target_symbols']:
        part = _market_frame(sources[ticker], ticker)[['date', 'adjusted_open']].copy()
        part['ticker'] = ticker
        prices.append(part)
    simulation = run_backtest(predictions, pd.concat(prices), {**config, 'threshold': result['selected_threshold']})
    vector = run_vectorized_backtest(predictions, {**config, 'threshold': result['selected_threshold']})
    vector['equity'].to_csv(output / 'vector_equity.csv', index=False)
    vector['trades'].to_csv(output / 'vector_trades.csv', index=False)
    (output / 'vector_metrics.json').write_text(json.dumps(vector['metrics'], indent=2, default=str) + '\n')
    save_eda(frame, output)
    predictions.to_csv(output / 'predictions.csv', index=False)
    result['model_metrics'].to_csv(output / 'model_metrics.csv', index=False)
    test_errors = predictions.loc[predictions['split'] == 'test', ['date', 'ticker', 'target', 'prediction']].copy()
    test_errors['error'] = test_errors['prediction'] - test_errors['target']
    test_errors['absolute_error'] = test_errors['error'].abs()
    test_errors['squared_error'] = test_errors['error'] ** 2
    test_errors['year'] = pd.to_datetime(test_errors['date']).dt.year
    test_errors.to_csv(output / 'test_errors.csv', index=False)
    test_errors.groupby(['ticker', 'year']).agg(
        count=('error', 'size'), mae=('absolute_error', 'mean'), mse=('squared_error', 'mean'),
        bias=('error', 'mean')).to_csv(output / 'test_errors_by_ticker_year.csv')
    for name in ('equity', 'metrics', 'trades'):
        simulation[name].to_csv(output / f'{name}.csv', index=False)
    joblib.dump(result['estimator'], output / 'model.joblib')
    # The holdout model is frozen after validation; expose its label cutoff so
    # users do not mistake recent signal dates for a recently retrained model.
    latest = latest_signal_report(predictions, result['selected_threshold'], result['split_dates']['validation_last_exit'])
    latest.to_csv(output / 'latest_signals.csv', index=False)
    summary = {'selected_model': result['selected_model'], 'selected_threshold': result['selected_threshold'],
               'split_dates': result['split_dates'], 'rows': len(frame), 'latest_signal_date': str(latest.date.max()),
               'model_training_last_exit': result['split_dates']['validation_last_exit'],
               'limitations': 'Research only. Adjusted opens approximate total return; simulations do not guarantee execution.'}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2, default=str) + '\n')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 4))
    for strategy, rows in simulation['equity'].groupby('strategy'):
        ax.plot(rows.date, rows.equity, label=strategy)
    ax.set_title('Held-out equity after costs')
    ax.legend()
    fig.tight_layout()
    fig.savefig(output / 'equity.png', dpi=120)
    plt.close(fig)
    print(json.dumps(summary, indent=2))
    print(latest.to_string(index=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['download', 'features', 'run'])
    parser.add_argument('--config', default='config/config.yml', help='YAML source and universe configuration')
    parser.add_argument('--settings', help='YAML research settings (defaults to config/settings.yml)')
    parser.add_argument('--offline', action='store_true', help='Read and verify cached snapshots')
    args = parser.parse_args()
    cfg = read_config(args.config, args.settings)
    try:
        if args.stage == 'download':
            from .data import refresh_sources
            refresh_sources(cfg)
        else:
            execute(cfg, refresh=not args.offline, stage=args.stage)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(1, f'Workflow failed: {exc}\n')


if __name__ == '__main__':
    main()
