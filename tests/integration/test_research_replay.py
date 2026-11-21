"""Two complete numerical workflow passes on explicitly fictional data."""
from capstone import cli
from capstone.research import compare_outputs
from capstone.synthetic_demo import generate_synthetic_sources


def test_frozen_acceptance_runner_and_relocated_replay(tmp_path):
    """Exercise subprocesses and the real loader on fictional source-shaped files."""
    import io
    import json
    import shutil
    import zipfile
    from pathlib import Path
    import pandas as pd
    import yaml
    from capstone.config import read_config
    from capstone.data import CFTC_URL, _write_snapshot
    from capstone.research import run

    root = Path(__file__).resolve().parents[2]
    cfg = read_config(root / 'config/config.yml', root / 'config/settings.yml')
    cfg.update(seed=42, sessions=900, start_date='2018-01-02', market_features={},
               required_symbols=['GLD', 'SLV'], symbols={'GLD': 'GLD', 'SLV': 'SLV'},
               market_sources={}, forest_estimators=2, start='2018-01-02', end='2021-12-31')
    sources, metadata = generate_synthetic_sources(cfg)
    assert metadata['synthetic_only']
    raw = tmp_path / 'fictional-data'
    for ticker in cfg['target_symbols']:
        _write_snapshot(raw / 'raw/market' / f'{ticker}.csv',
                        sources[ticker].to_csv(index=False).encode(), f'Yahoo Finance: {ticker}',
                        observed_at=pd.Timestamp('2024-01-01T22:00:00Z').to_pydatetime())
    cot = sources['cot'].copy()
    manifest = tmp_path / 'fictional-release.csv'
    cot[['report_date', 'available_at', 'source_url']].drop_duplicates().to_csv(manifest, index=False)
    cot['CFTC_Contract_Market_Code'] = cot.ticker.map({'GLD': '088691', 'SLV': '084691'})
    cot = cot.rename(columns={'report_date': 'Report_Date_as_YYYY-MM-DD',
                              'open_interest': 'Open_Interest_All',
                              'managed_long': 'M_Money_Positions_Long_All',
                              'managed_short': 'M_Money_Positions_Short_All',
                              'producer_long': 'Prod_Merc_Positions_Long_All',
                              'producer_short': 'Prod_Merc_Positions_Short_All'})
    for year in range(2018, 2022):
        rows = cot[pd.to_datetime(cot['Report_Date_as_YYYY-MM-DD']).dt.year == year]
        payload = io.BytesIO()
        with zipfile.ZipFile(payload, 'w') as archive:
            archive.writestr('fictional.txt', rows.to_csv(index=False))
        _write_snapshot(raw / 'raw/cftc' / f'{year}.zip', payload.getvalue(), CFTC_URL.format(year=year))
    cfg.update(data_dir=str(raw), release_manifest=str(manifest))
    source, settings = tmp_path / 'source.yml', tmp_path / 'settings.yml'
    # All mandatory merged settings remain present; an empty settings map is valid.
    source.write_text(yaml.safe_dump(cfg))
    settings.write_text('{}\n')
    bundle = tmp_path / 'bundle'
    assert run(source, settings, bundle) == 0
    evidence = json.loads((bundle / 'evidence.json').read_text())
    assert evidence['status'] == 'reproduced'
    assert evidence['coverage']['failures'] == []
    moved = tmp_path / 'moved-bundle'
    shutil.move(bundle, moved)
    replay = tmp_path / 'replay'
    assert run(source, settings, replay, replay=moved) == 0
    assert json.loads((replay / 'evidence.json').read_text())['numeric_output_sha256'] == evidence['numeric_output_sha256']
    with (moved / 'inputs/release_dates.csv').open('a') as stream:
        stream.write('\n')
    rejected = tmp_path / 'rejected'
    assert run(source, settings, rejected, replay=moved) == 1
    assert 'hashes' in json.loads((rejected / 'evidence.json').read_text())['error']


def test_fictional_complete_workflow_replays(tmp_path, monkeypatch):
    import json
    import pandas as pd

    config = {'target_symbols': ['GLD', 'SLV'], 'market_features': {},
              'seed': 42, 'sessions': 180, 'start_date': '2020-01-02',
              'forest_estimators': 2}
    sources, metadata = generate_synthetic_sources(config)
    assert metadata['synthetic_only']
    monkeypatch.setattr(cli, 'load_sources', lambda *args, **kwargs: sources)
    for name in ('a', 'b'):
        cli.execute({**config, 'output_dir': str(tmp_path / name)}, refresh=False)
    compared = compare_outputs(tmp_path / 'a', tmp_path / 'b')
    assert {'features.csv', 'predictions.csv', 'model_comparison.csv', 'split_counts.csv', 'holdout_comparison.csv',
            'equity.csv', 'trades.csv', 'metrics.csv', 'threshold_scores.json',
            'vector_metrics.json', 'summary.json'}.issubset(compared)
    comparison = pd.read_csv(tmp_path / 'a' / 'model_comparison.csv')
    summary = json.loads((tmp_path / 'a' / 'summary.json').read_text())
    assert comparison.split.eq('validation').all()
    assert comparison.selected.sum() == 1
    assert comparison.loc[comparison.selected, 'model'].item() == summary['selected_model']
