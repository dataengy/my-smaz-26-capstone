"""Optional local Dagster adapter for the atomic frozen-research protocol."""
from contextlib import redirect_stdout
import json
from pathlib import Path

import dagster as dg

from capstone import research
from capstone.reporting import load_run

ROOT = Path(__file__).resolve().parents[2]


class ResearchConfig(dg.Config):
    source_config: str = 'config/config.yml'
    settings: str = ''
    output_root: str = 'artifacts/dagster'


@dg.multi_asset(specs=[
    dg.AssetSpec('frozen_experiment', group_name='research'),
    dg.AssetSpec('feature_table', deps=['frozen_experiment'], group_name='research'),
    dg.AssetSpec('validation_comparison', deps=['feature_table'], group_name='research'),
    dg.AssetSpec('strategy_report', deps=['validation_comparison'], group_name='research'),
])
def frozen_research_assets(context: dg.AssetExecutionContext, config: ResearchConfig):
    """One atomic freeze/coverage/double-calculation run produces four related assets."""
    output_root = ROOT / config.output_root
    output_root.mkdir(parents=True, exist_ok=True)
    output = output_root / context.run.run_id
    log = output_root / f'{context.run.run_id}.log'
    if output.exists():
        raise dg.Failure('Research output already exists. Launch a new run; saved bundles are never overwritten.')
    source = ROOT / config.source_config
    settings = ROOT / config.settings if config.settings else None
    with log.open('w') as stream, redirect_stdout(stream):
        status = research.run(source, settings, output)
    if status != 0:
        raise dg.Failure(f'Research did not complete (exit {status}). See {output / "evidence.json"}',
                         metadata={'research_exit_status': status, 'log': dg.MetadataValue.path(str(log))})
    run = load_run(output)
    yield dg.MaterializeResult(asset_key='frozen_experiment', metadata={
        'bundle': dg.MetadataValue.path(str(output)),
        'numeric_outputs': len(run.evidence['numeric_output_sha256']),
        'execution_log': dg.MetadataValue.path(str(log)),
    })
    yield dg.MaterializeResult(asset_key='feature_table', metadata={
        'rows': len(run.tables['features']),
        'csv': dg.MetadataValue.path(str(output / 'run-1/features.csv')),
        'coverage': dg.MetadataValue.json(run.evidence['coverage']),
    })
    yield dg.MaterializeResult(asset_key='validation_comparison', metadata={
        'selected_model': run.summary['selected_model'],
        'candidates': len(run.tables['model_comparison']),
        'validation_start': run.summary['split_dates']['validation_start'],
        'holdout_start': run.summary['split_dates']['test_start'],
        'csv': dg.MetadataValue.path(str(output / 'run-1/model_comparison.csv')),
    })
    yield dg.MaterializeResult(asset_key='strategy_report', metadata={
        'metrics': dg.MetadataValue.json(json.loads(run.tables['metrics'].to_json(orient='records'))),
        'csv': dg.MetadataValue.path(str(output / 'run-1/metrics.csv')),
    })


frozen_research_job = dg.define_asset_job('frozen_research_job', selection=dg.AssetSelection.groups('research'))
defs = dg.Definitions(assets=[frozen_research_assets], jobs=[frozen_research_job])
