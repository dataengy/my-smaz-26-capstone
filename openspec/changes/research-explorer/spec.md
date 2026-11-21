# Research explorer

## Requirement: Inspect saved experiments

The research notebook and optional Streamlit dashboard SHALL read completed frozen research bundles without downloading, training, selecting parameters or mutating the bundle. Their calculations SHALL share `capstone.reporting`.

- Accept only `status=reproduced`, adequate-coverage bundles. Verify each declared numerical output against its recorded SHA-256, reject missing/tampered files, and reject paths outside the result directory.
- Identify the selected bundle, its signal/holdout periods, recorded model and label cutoff. Do not equate a historical latest signal with a live recommendation.
- Display validation candidate scores separately from holdout error analysis. Compute exploratory feature correlations from purged training observations only.
- Include missingness/coverage, model comparison, equity/drawdown against benchmark, paid costs, per-ticker errors and worst predictions. Preserve the original portfolio universe when filtering ticker diagnostics.
- Handle no bundles, blocked runs, empty diagnostic groups and invalid bundles with an actionable message. Never replace absent research with synthetic results.
- The notebook SHALL execute top-to-bottom on a configured local bundle. Save executed notebook/HTML exports under ignored artifacts; keep downloaded data and notebook result outputs out of Git.

## Requirement: Optional presentation dependencies

The existing core CLI SHALL remain usable without Streamlit or Plotly. Provide a separately locked `dashboard` extra and documented local commands. The dashboard SHALL bind to localhost by default, load saved results only, and expose no training controls.

The command catalogs SHALL expose `streamlit` for local exploration and `plotly` for standalone interactive HTML export. The export SHALL embed Plotly JavaScript, verify the saved bundle and refuse output paths inside that frozen bundle. Just recipes SHALL accept explicit bundle and port/output arguments.

## Priority boundary

This first increment delivers the research notebook and Streamlit/Plotly explorer. Evidence.dev is an alternative presentation platform, not an additional required service. Dagster is a subsequent adapter around the established workflow; dlt requires a separately specified incremental source/destination contract before adoption.
