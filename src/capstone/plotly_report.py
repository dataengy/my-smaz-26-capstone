"""Export an offline interactive Plotly report from verified saved results."""
import argparse
from html import escape
import os
from pathlib import Path

import plotly.express as px

from capstone.reporting import discover_runs, load_run, equity_series, error_summary


def export_report(bundle, output):
    run = load_run(bundle)
    destination = Path(output).expanduser().resolve()
    if destination.is_relative_to(run.path):
        raise ValueError('Export outside the frozen research bundle to preserve its integrity.')
    curve = equity_series(run)
    figures = []
    for column, title in [('net_return', 'Full-portfolio holdout return after costs'),
                          ('drawdown', 'Full-portfolio holdout drawdown')]:
        fig = px.line(curve, x='date', y=column, color='strategy', line_dash='strategy',
                      title=title, template='plotly_white',
                      labels={'date': 'Execution session', column: 'Return'})
        fig.update_yaxes(tickformat='.0%')
        figures.append(fig)
    sections = [f'<h1>Precious metals research</h1><p>Bundle: {escape(run.path.name)}</p>',
                f'<p>Validation-selected model: <strong>{escape(run.summary["selected_model"])}</strong>. '
                f'Holdout first signal: {escape(run.summary["split_dates"]["test_start"])}</p>',
                '<p>Saved historical results; the portfolio retains all target ETFs. '
                'No source refresh, model training or parameter selection occurs during export.</p>']
    for index, figure in enumerate(figures):
        sections.append(figure.to_html(full_html=False, include_plotlyjs=index == 0))
    for title, table in [('Validation comparison', run.tables['model_comparison']),
                         ('Full-portfolio metrics after costs', run.tables['metrics']),
                         ('Descriptive holdout errors by ticker', error_summary(run))]:
        sections.append(f'<h2>{title}</h2><div class="table">{table.to_html(index=False, float_format=lambda x: f"{x:.6f}")}</div>')
    sections.append('<p>Tables retain decimal return units (0.01 = 1%). '
                    'Source vintages, COT availability assumptions and overlapping labels limit interpretation. '
                    'Historical results do not establish future profitability.</p>')
    document = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,initial-scale=1">'
                '<title>Precious metals research</title><style>'
                'body{font:16px system-ui;margin:32px auto;padding:0 20px;max-width:1150px;color:#172b3a;background:white}'
                '.table{overflow:auto}table{border-collapse:collapse}td,th{padding:8px;border-bottom:1px solid #ddd;text-align:left}'
                '</style></head><body>' + '\n'.join(sections) + '</body></html>')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(document)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', help='Completed frozen research bundle')
    parser.add_argument('--output', default='artifacts/research-explorer/plotly.html')
    args = parser.parse_args()
    requested = args.run or os.environ.get('CAPSTONE_RESEARCH_RUN')
    if not requested:
        choices = discover_runs(Path(__file__).resolve().parents[2] / 'artifacts')
        if not choices:
            parser.error('No completed bundle. Pass --run or set CAPSTONE_RESEARCH_RUN.')
        requested = choices[0]
    try:
        print(f'Interactive Plotly report: {export_report(requested, args.output)}')
    except (OSError, ValueError) as exc:
        parser.exit(1, f'Plotly export failed: {exc}\n')


if __name__ == '__main__':
    main()
