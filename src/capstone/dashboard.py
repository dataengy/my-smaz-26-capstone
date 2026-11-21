"""Local saved-result explorer. Start with: streamlit run src/capstone/dashboard.py"""
from pathlib import Path
import os

import plotly.express as px
import streamlit as st

from capstone.reporting import (
    discover_runs, load_run, coverage_summary, feature_missingness,
    feature_correlations, equity_series, error_summary,
)


def main():
    st.set_page_config(page_title='Precious metals research', layout='wide')
    st.title('Precious metals research')
    st.caption('Saved historical GLD/SLV experiments · validation selection · holdout evaluation')
    explicit = os.environ.get('CAPSTONE_RESEARCH_RUN')
    artifacts = Path(__file__).resolve().parents[2] / 'artifacts'
    runs = [Path(explicit).expanduser().resolve()] if explicit else discover_runs(artifacts)
    if not runs:
        st.info('No completed research bundles found. Run capstone.research first, or set CAPSTONE_RESEARCH_RUN to a completed bundle directory.')
        st.stop()
    selected = st.sidebar.selectbox('Saved experiment', runs, format_func=lambda path: path.name)
    try:
        run = load_run(selected)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()
    st.sidebar.caption(f'Bundle: {run.path}')
    st.sidebar.caption(f"Recorded completion: {run.evidence.get('finished_at', 'not recorded')}")
    st.sidebar.caption('Numerical output hashes checked on every reload.')
    st.sidebar.button('Reload saved results')
    dates = run.summary['split_dates']
    a, b, c = st.columns(3)
    a.metric('Validation-selected model', run.summary['selected_model'])
    b.metric('Holdout first signal', dates['test_start'])
    c.metric('Training-label cutoff', run.summary['model_training_last_exit'])

    data_tab, model_tab, portfolio_tab, errors_tab = st.tabs(['Data', 'Models', 'Portfolio', 'Errors'])
    with data_tab:
        st.subheader('Signal coverage')
        st.dataframe(coverage_summary(run), width='stretch')
        coverage = run.evidence.get('coverage', {}).get('by_ticker', [])
        if coverage:
            st.dataframe(coverage, width='stretch')
        st.subheader('Feature missingness')
        missing = feature_missingness(run).mul(100).reset_index()
        st.plotly_chart(px.bar(missing, x='index', y='fraction_missing',
                               labels={'index': 'Feature', 'fraction_missing': 'Missing (%)'}), width='stretch')
        st.subheader('Saved signals')
        st.caption('Historical signals as of the saved data cutoff. They do not update while this app is open.')
        st.dataframe(run.tables['latest_signals'], width='stretch', hide_index=True)
        st.caption('COT eligibility follows the frozen availability manifest; adjusted vendor history can contain retrospective revisions.')

    with model_tab:
        st.subheader('Validation candidate comparison')
        st.caption('Minimum validation MAE selects the model. MAE/RMSE below are five-session return errors; holdout is excluded from this table.')
        comparison = run.tables['model_comparison']
        st.dataframe(comparison.style.format({'mae': '{:.4%}', 'rmse': '{:.4%}'}), width='stretch', hide_index=True)
        st.subheader('Chronological partitions after purge')
        st.dataframe(run.tables['split_counts'], width='stretch', hide_index=True)
        correlations = feature_correlations(run).dropna().sort_values().reset_index()
        st.subheader('Exploratory correlations on training only')
        if not correlations.empty:
            st.plotly_chart(px.bar(correlations, x='training_target_correlation', y='index',
                                   orientation='h', labels={'index': 'Feature',
                                   'training_target_correlation': 'Training correlation with target'}), width='stretch')
        st.caption('Correlations are descriptive; overlapping targets and weekly COT reuse reduce independent information.')

    with portfolio_tab:
        st.subheader('Full-portfolio holdout performance')
        st.caption('All target ETFs remain included. Ticker diagnostics on the Errors tab do not recalculate this portfolio.')
        curve = equity_series(run)
        for column, title in [('net_return', 'Cumulative return after costs'), ('drawdown', 'Drawdown from running peak')]:
            fig = px.line(curve, x='date', y=column, color='strategy', line_dash='strategy',
                          title=title, labels={'date': 'Execution session', column: title})
            fig.update_yaxes(tickformat='.0%')
            fig.update_traces(hovertemplate='%{x|%Y-%m-%d}<br>%{y:.2%}')
            st.plotly_chart(fig, width='stretch')
        st.dataframe(run.tables['metrics'].style.format({
            'total_return': '{:.2%}', 'cagr': '{:.2%}', 'max_drawdown': '{:.2%}',
            'sharpe': '{:.3f}', 'transaction_costs': '{:,.2f}'}), width='stretch', hide_index=True)
        st.caption(f"Initial capital: {run.config.get('initial_capital', 100000):,.0f}; commission/slippage per side: {run.config.get('cost_bps', 10):g} bps. Historical simulation does not establish future profitability.")

    with errors_tab:
        st.subheader('Descriptive holdout errors')
        tickers = sorted(run.tables['test_errors'].ticker.unique())
        ticker = st.selectbox('Ticker diagnostics', ['All'] + tickers)
        errors = run.tables['test_errors'].copy()
        if ticker != 'All':
            errors = errors[errors.ticker == ticker]
        st.dataframe(error_summary(run, None if ticker == 'All' else ticker).style.format({
            'mae': '{:.3%}', 'rmse': '{:.3%}', 'bias': '{:.3%}'}), width='stretch', hide_index=True)
        if errors.empty:
            st.info('No holdout predictions in this group.')
        else:
            fig = px.scatter(errors, x='target', y='prediction', color='ticker', symbol='ticker',
                             hover_data=['date'], labels={'target': 'Actual five-session return',
                             'prediction': 'Predicted five-session return'})
            lower = min(errors.target.min(), errors.prediction.min())
            upper = max(errors.target.max(), errors.prediction.max())
            padding = max((upper - lower) * .05, .001)
            bounds = [lower - padding, upper + padding]
            fig.add_shape(type='line', x0=bounds[0], y0=bounds[0], x1=bounds[1], y1=bounds[1],
                          line={'color': 'gray', 'dash': 'dot'})
            fig.update_xaxes(tickformat='.0%', range=bounds)
            fig.update_yaxes(tickformat='.0%', range=bounds)
            st.plotly_chart(fig, width='stretch')
            errors['absolute_error'] = (errors.prediction - errors.target).abs()
            st.subheader('Largest absolute errors')
            st.dataframe(errors.nlargest(10, 'absolute_error')[
                ['date', 'ticker', 'target', 'prediction', 'absolute_error']].style.format({
                'target': '{:.3%}', 'prediction': '{:.3%}', 'absolute_error': '{:.3%}'}),
                width='stretch', hide_index=True)
        st.caption('Inspecting holdout errors does not authorize tuning on this period. New selections require a fresh evaluation design.')


if __name__ == '__main__':
    main()
