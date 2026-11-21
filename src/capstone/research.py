"""Frozen, offline full-COT experiment and deterministic replay.

Usage: python -m capstone.research --output artifacts/full-cot-YYYYMMDD
An existing output directory is never overwritten. No acquisition is performed.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
from datetime import datetime, timezone
import hashlib
from importlib.metadata import distributions, version
import io
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

import pandas as pd
import yaml

from .config import read_config
from .data import load_sources
from .features import build_features

REQUIRED_OUTPUTS = {
    'features.csv', 'predictions.csv', 'model_metrics.csv', 'model_comparison.csv', 'split_counts.csv',
    'holdout_comparison.csv', 'threshold_scores.json', 'vector_equity.csv',
    'vector_trades.csv', 'vector_metrics.json', 'eda_summary.csv',
    'target_correlations.csv', 'missingness.csv', 'test_errors.csv',
    'test_errors_by_ticker_year.csv', 'equity.csv', 'metrics.csv', 'trades.csv',
    'latest_signals.csv', 'summary.json',
}


def hashes(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(Path(root).rglob('*')) if p.is_file() and '__pycache__' not in p.parts}


def coverage(frame, config):
    """Check the agreed minimum before fitting or observing model metrics."""
    labeled = frame[frame.target.notna() & frame.exit_date.notna()].copy()
    labeled['date'] = pd.to_datetime(labeled.date)
    labeled['exit_date'] = pd.to_datetime(labeled.exit_date)
    dates = sorted(labeled.date.unique())
    if not dates:
        return {'failures': ['No labeled signals'], 'by_ticker': []}
    val = pd.Timestamp(dates[int(len(dates) * config['train_fraction'])])
    test = pd.Timestamp(dates[int(len(dates) * (config['train_fraction'] + config['validation_fraction']))])
    failures, rows = [], []
    for ticker in config['target_symbols']:
        part = labeled[labeled.ticker == ticker]
        count = part.date.nunique()
        span = (part.date.max() - part.date.min()).days if count else 0
        releases = part.report_date.nunique()
        partitions = {
            'train': part[(part.date < val) & (part.exit_date < val)],
            'validation': part[(part.date >= val) & (part.date < test) & (part.exit_date < test)],
            'test': part[part.date >= test],
        }
        sizes = {key: value.date.nunique() for key, value in partitions.items()}
        rows.append({'ticker': ticker, 'labeled_dates': count, 'confirmed_reports_used': releases,
                     'span_days': span, 'first_signal': str(part.date.min()),
                     'last_signal': str(part.date.max()), 'purged_partition_dates': sizes})
        if count < 500 or span < 1095 or releases < 150:
            failures.append(f'{ticker}: need >=500 labeled dates, >=1095 span days, >=150 confirmed reports')
        for key, minimum in [('train', 250), ('validation', 75), ('test', 75)]:
            if sizes[key] < minimum:
                failures.append(f'{ticker} {key}: {sizes[key]} dates after purge < {minimum}')
    return {'minimum': {'labeled_dates': 500, 'span_days': 1095, 'confirmed_reports': 150,
                        'purged_dates': {'train': 250, 'validation': 75, 'test': 75}},
            'validation_start': str(val), 'test_start': str(test), 'by_ticker': rows, 'failures': failures}


def compare_outputs(first, second):
    """Exact hashes for deterministic numeric/selection outputs only."""
    def selected(root):
        return {k: v for k, v in hashes(root).items() if Path(k).suffix in {'.csv', '.json'}}
    a, b = selected(first), selected(second)
    if not REQUIRED_OUTPUTS.issubset(a) or not REQUIRED_OUTPUTS.issubset(b) or a != b:
        raise ValueError('Replay numeric artifacts differ or are absent')
    return a


def execute_frozen(inputs, output):
    """Resolve portable paths inside an integrity-checked frozen bundle."""
    from .cli import execute
    inputs = Path(inputs).resolve()
    config = json.loads((inputs / 'effective-config.json').read_text())
    config['data_dir'] = str(inputs / 'data')
    config['release_manifest'] = str(inputs / 'release_dates.csv')
    config['output_dir'] = str(Path(output).resolve())
    execute(config, refresh=False)


def _run_pair(inputs, output, evidence):
    for name in ('run-1', 'run-2'):
        if hashes(inputs) != evidence['input_sha256']:
            raise ValueError('Frozen inputs changed before execution')
        command = [sys.executable, '-c',
                   'import sys; from capstone.research import execute_frozen; '
                   'execute_frozen(sys.argv[1],sys.argv[2])',
                   str(inputs), str(output / name)]
        env = {**os.environ, 'PYTHONPATH': str(inputs / 'code'), 'PYTHONDONTWRITEBYTECODE': '1',
               'MPLBACKEND': 'Agg', 'MPLCONFIGDIR': str(output / 'matplotlib-cache')}
        evidence.setdefault('execution_commands', []).append(command)
        with (output / f'{name}.log').open('w') as stream:
            completed = subprocess.run(command, cwd=output, env=env, stdout=stream, stderr=subprocess.STDOUT)
        if completed.returncode:
            raise RuntimeError(f'{name} failed with exit {completed.returncode}; see its log')
    if hashes(inputs) != evidence['input_sha256']:
        raise ValueError('Frozen inputs changed during execution')
    evidence['numeric_output_sha256'] = compare_outputs(output / 'run-1', output / 'run-2')
    evidence['status'] = 'reproduced'


def run(config_path, settings_path, output, replay=None):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    inputs = output / 'inputs'
    inputs.mkdir()
    evidence = {'status': 'started', 'started_at': datetime.now(timezone.utc).isoformat(),
                'command': [sys.executable, '-m', 'capstone.research', *sys.argv[1:]],
                'python': sys.version, 'platform': platform.platform(),
                'environment': {d.metadata['Name']: d.version for d in distributions()},
                'versions': {name: version(name) for name in
                             ['numpy', 'pandas', 'scikit-learn', 'exchange-calendars', 'PyYAML']}}
    try:
        if replay:
            previous = Path(replay).resolve()
            saved = json.loads((previous / 'evidence.json').read_text())
            if saved.get('status') != 'reproduced' or saved.get('coverage', {}).get('failures', [True]):
                raise ValueError('Replay requires a completed, adequate-history experiment')
            if saved['versions'] != evidence['versions']:
                raise ValueError('Replay dependency versions differ from the original experiment')
            original = hashes(previous / 'inputs')
            if original != saved['input_sha256']:
                raise ValueError('Saved input hashes do not match evidence')
            shutil.copytree(previous / 'inputs', inputs, dirs_exist_ok=True)
            if hashes(inputs) != original:
                raise ValueError('Saved inputs changed during replay freezing')
            evidence.update(input_sha256=original, coverage=saved['coverage'], replay_of=str(previous))
            _run_pair(inputs, output, evidence)
            if evidence['numeric_output_sha256'] != saved['numeric_output_sha256']:
                raise ValueError('Replay differs from original numerical results')
            return 0
        config = read_config(config_path, settings_path)
        # Copy first so a concurrent source refresh cannot change replay inputs.
        raw = Path(config['data_dir']) / 'raw'
        original = hashes(raw)
        shutil.copytree(raw, inputs / 'data' / 'raw')
        if original != hashes(raw) or original != hashes(inputs / 'data' / 'raw'):
            raise ValueError('Source snapshots changed during freezing; retry after owner handoff')
        shutil.copy2(config['release_manifest'], inputs / 'release_dates.csv')
        if config.get('release_evidence_dir'):
            shutil.copytree(config['release_evidence_dir'], inputs / 'release-evidence')
        shutil.copy2(config_path, inputs / 'source-config.yml')
        settings = settings_path or yaml.safe_load(Path(config_path).read_text()).get('settings_file', 'config/settings.yml')
        shutil.copy2(settings, inputs / 'source-settings.yml')
        root = Path(__file__).resolve().parents[2]
        shutil.copytree(root / 'src' / 'capstone', inputs / 'code' / 'capstone',
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for name in ('uv.lock', 'pyproject.toml'):
            shutil.copy2(root / name, inputs / name)
        config['data_dir'] = str(inputs / 'data')
        config['release_manifest'] = str(inputs / 'release_dates.csv')
        log = io.StringIO()
        with redirect_stdout(log):
            sources = load_sources(config, refresh=False)
        # Freeze an explicit common completed ETF endpoint, even for end: null.
        if not config.get('end'):
            last = min(pd.to_datetime(sources[t].date).max() for t in config['target_symbols'])
            config['end'] = str((last + pd.Timedelta(days=1)).date())
            with redirect_stdout(log):
                sources = load_sources(config, refresh=False)
        (output / 'source-load.log').write_text(log.getvalue())
        evidence['source_rows'] = {key: len(value) for key, value in sources.items()}
        evidence['source_ranges'] = {
            key: {'first': str(pd.to_datetime(value[column]).min()),
                  'last': str(pd.to_datetime(value[column]).max())}
            for key, value in sources.items() for column in ['report_date' if key == 'cot' else 'date']}
        frame = build_features(sources, config)
        frame.to_csv(output / 'preflight_features.csv', index=False)
        evidence['coverage'] = coverage(frame, config)
        frozen = {k: v for k, v in config.items() if k != 'output_dir'}
        frozen['data_dir'] = 'data'
        frozen['release_manifest'] = 'release_dates.csv'
        if 'release_evidence_dir' in frozen:
            frozen['release_evidence_dir'] = 'release-evidence'
        (inputs / 'effective-config.json').write_text(json.dumps(frozen, indent=2, default=str) + '\n')
        evidence['input_sha256'] = hashes(inputs)
        if evidence['coverage']['failures']:
            evidence['status'] = 'blocked_insufficient_confirmed_cot_history'
            return 2
        _run_pair(inputs, output, evidence)
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        evidence['status'] = 'failed'
        evidence['error'] = str(exc)
        return 1
    finally:
        evidence.setdefault('input_sha256', hashes(inputs))
        evidence['finished_at'] = datetime.now(timezone.utc).isoformat()
        (output / 'evidence.json').write_text(json.dumps(evidence, indent=2, default=str) + '\n')
        print(json.dumps(evidence, indent=2, default=str))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='config/config.yml')
    parser.add_argument('--settings')
    parser.add_argument('--output', required=True)
    parser.add_argument('--replay', help='Replay a completed frozen bundle without using current sources')
    args = parser.parse_args()
    raise SystemExit(run(args.config, args.settings, args.output, replay=args.replay))


if __name__ == '__main__':
    main()
