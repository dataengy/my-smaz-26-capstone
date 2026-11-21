"""Read-only diagnostics shared by the research notebook and dashboard."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from io import BytesIO
import json
from pathlib import Path

import pandas as pd

from .features import numeric_features


TABLE_COLUMNS = {
    'features': {'date', 'ticker', 'target', 'exit_date'},
    'model_comparison': {'model', 'split', 'mae', 'rmse', 'parameters', 'selected'},
    'metrics': {'strategy', 'total_return', 'cagr', 'sharpe', 'max_drawdown', 'transaction_costs'},
    'equity': {'date', 'strategy', 'equity'},
    'test_errors': {'date', 'ticker', 'target', 'prediction'},
    'split_counts': {'split', 'ticker', 'rows_after', 'dates_after', 'purged_rows'},
    'latest_signals': {'date', 'ticker', 'prediction', 'model_training_last_exit'},
    'holdout_comparison': {'model', 'mae', 'rmse'},
}


@dataclass
class ResearchRun:
    path: Path
    evidence: dict
    config: dict
    summary: dict
    tables: dict[str, pd.DataFrame]


def discover_runs(artifacts):
    """List completed bundle directories; load_run performs integrity checks."""
    completed = []
    for evidence in Path(artifacts).glob('*/evidence.json'):
        try:
            metadata = json.loads(evidence.read_text())
            if metadata.get('status') == 'reproduced':
                completed.append((metadata.get('finished_at', ''), evidence.parent))
        except (OSError, ValueError, AttributeError):
            continue
    return [path for _, path in sorted(completed, reverse=True)]


def _verified_bytes(path, expected):
    try:
        contents = path.read_bytes()
    except OSError as exc:
        raise ValueError(f'Missing saved artifact: {path.name}. Choose a complete research bundle.') from exc
    if hashlib.sha256(contents).hexdigest() != expected:
        raise ValueError(f'Integrity check failed: {path.name}. Restore the saved bundle or rerun research.')
    return contents


def load_run(path):
    """Load a completed bundle without executing code or deserializing models."""
    root = Path(path).expanduser().resolve()
    try:
        evidence = json.loads((root / 'evidence.json').read_text())
        if evidence.get('status') != 'reproduced' or evidence.get('coverage', {}).get('failures', [True]):
            raise ValueError('Choose a reproduced research bundle with adequate coverage, not a blocked run.')
        recorded = evidence.get('numeric_output_sha256', {})
        required = {f'{name}.csv' for name in TABLE_COLUMNS} | {'summary.json'}
        if not required.issubset(recorded):
            raise ValueError('Bundle lacks explorer outputs. Run the current research runner into a new directory.')
        output = root / 'run-1'
        saved = {}
        for name, digest in recorded.items():
            artifact = output / name
            if Path(name).name != name or artifact.resolve().parent != output.resolve():
                raise ValueError('Invalid artifact path in saved evidence.')
            saved[name] = _verified_bytes(artifact, digest)
        config_path = root / 'inputs/effective-config.json'
        if not config_path.resolve().is_relative_to(root):
            raise ValueError('Invalid frozen configuration path.')
        config = json.loads(_verified_bytes(config_path, evidence.get('input_sha256', {}).get('effective-config.json')))
        tables = {}
        for name, columns in TABLE_COLUMNS.items():
            table = pd.read_csv(BytesIO(saved[f'{name}.csv']))
            if not columns.issubset(table):
                raise ValueError(f'{name}.csv lacks required columns: {sorted(columns.difference(table))}')
            for column in ('date', 'exit_date', 'entry_date', 'report_date'):
                if column in table:
                    table[column] = pd.to_datetime(table[column])
            tables[name] = table
        comparison = tables['model_comparison']
        summary = json.loads(saved['summary.json'])
        selected = comparison.loc[comparison.selected.eq(True)]
        if (not comparison.split.eq('validation').all() or len(selected) != 1
                or selected.model.iloc[0] != summary['selected_model']):
            raise ValueError('Saved validation selection and summary disagree.')
        if float(config.get('initial_capital', 100000)) <= 0:
            raise ValueError('Saved initial capital must be positive.')
        return ResearchRun(root, evidence, config, summary, tables)
    except (OSError, KeyError, TypeError, AttributeError) as exc:
        raise ValueError(f'Cannot read completed research bundle at {root}: {exc}') from exc


def equity_series(run):
    """Full-portfolio returns/drawdown, including loss from initial costs."""
    curve = run.tables['equity'].sort_values(['strategy', 'date']).copy()
    capital = float(run.config.get('initial_capital', 100000))
    curve['net_return'] = curve.equity / capital - 1
    peaks = curve.groupby('strategy').equity.cummax().clip(lower=capital)
    curve['drawdown'] = curve.equity / peaks - 1
    return curve


def error_summary(run, ticker=None):
    """Descriptive holdout errors; never a model-selection objective."""
    data = run.tables['test_errors'].copy()
    if ticker:
        data = data[data.ticker == ticker]
    data['error'] = data.prediction - data.target
    data['absolute_error'] = data.error.abs()
    data['squared_error'] = data.error ** 2
    result = data.groupby('ticker').agg(count=('error', 'count'), mae=('absolute_error', 'mean'),
                                      mse=('squared_error', 'mean'), bias=('error', 'mean')).reset_index()
    result['rmse'] = result.pop('mse') ** .5
    return result


def training_rows(run, ticker=None):
    """Return only labeled training rows whose exits precede validation."""
    frame = run.tables['features']
    boundary = pd.Timestamp(run.summary['split_dates']['validation_start'])
    train = frame[(frame.date < boundary) & (frame.exit_date < boundary) & frame.target.notna()]
    if ticker:
        train = train[train.ticker == ticker]
    return train.copy()


def feature_correlations(run, ticker=None):
    """Correlations on purged training only; no holdout-guided feature selection."""
    train = training_rows(run, ticker)
    columns = [name for name in numeric_features(run.config) if name in train]
    if train.empty or not columns:
        return pd.Series(dtype=float, name='training_target_correlation')
    return train[columns + ['target']].corr()['target'].drop('target').rename('training_target_correlation')


def coverage_summary(run):
    frame = run.tables['features']
    return frame.groupby('ticker').agg(rows=('date', 'size'), labeled_rows=('target', 'count'),
                                      first_signal=('date', 'min'), last_signal=('date', 'max'))


def feature_missingness(run):
    frame = run.tables['features']
    columns = [name for name in numeric_features(run.config) if name in frame]
    return frame[columns].isna().mean().rename('fraction_missing').sort_values(ascending=False)
