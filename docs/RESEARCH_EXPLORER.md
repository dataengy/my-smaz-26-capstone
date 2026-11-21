[EN](RESEARCH_EXPLORER.md) | [RU](RESEARCH_EXPLORER.ru.md)

# Research notebook and dashboard

Inspect a completed frozen GLD/SLV experiment through [the research notebook](../notebooks/research.ipynb) or a local Streamlit dashboard. Both use the same read-only diagnostic functions. They display the recorded model and results for the selected bundle; neither trains models, downloads data nor changes strategy parameters.

## Open the research notebook

After `make setup`, run:

```sh
make run-research-notebook
```

The notebook covers feature coverage/missingness, purged-training distributions and correlations, validation candidate parameters and scores, holdout equity/drawdown and errors by ticker. It calculates its conclusions from the chosen bundle. It retains one separate role from `workflow.ipynb`, which runs the pipeline.

By default the explorer chooses the most recently completed bundle under `artifacts/`. Choose an exact historical experiment explicitly for a defense or comparison:

```sh
CAPSTONE_RESEARCH_RUN=artifacts/full-cot-model-comparison-20261121 make run-research-notebook
```

The environment variable must be set before starting the notebook kernel. Alternatively change the bundle selection in the setup cell. A missing bundle is an error with instructions; synthetic results are never substituted.

To execute and export an HTML report without changing the checked-in notebook:

```sh
CAPSTONE_RESEARCH_RUN=artifacts/full-cot-model-comparison-20261121 \
uv run --locked --no-sync jupyter nbconvert --execute --to html \
  --output-dir artifacts/research-explorer notebooks/research.ipynb
```

Local notebook execution needs permission to bind localhost kernel ports. Keep executed notebook copies, HTML and images under ignored `artifacts/`. The checked-in notebook contains source cells with cleared outputs.

## Run the dashboard

Install the optional locked dependencies once; the core CLI does not require them:

```sh
make setup-dashboard
CAPSTONE_RESEARCH_RUN=artifacts/full-cot-model-comparison-20261121 make streamlit
```

Open `http://127.0.0.1:8501` locally. Stop with Ctrl+C. To choose another port set `STREAMLIT_SERVER_PORT`, for example `STREAMLIT_SERVER_PORT=8502 make dashboard`. Browser usage telemetry is disabled by the Make command. No cloud deployment, authentication service or public listener is configured.

`make dashboard` remains an alias. Both command catalogs expose Streamlit and Plotly; Just accepts an explicit bundle, port or output path:

```sh
make plotly
just streamlit artifacts/full-cot-model-comparison-20261121 8502
just plotly artifacts/full-cot-model-comparison-20261121 artifacts/research-explorer/comparison.html
```

`make plotly` exports `artifacts/research-explorer/plotly.html`. Open that file in a browser: it embeds Plotly JavaScript and works offline without a server. It follows the same `CAPSTONE_RESEARCH_RUN` selection and integrity checks. Export into a separate directory, outside the frozen bundle.

| Tab | Contents |
|---|---|
| Data | Signal coverage, feature missingness and saved signals with the model's label cutoff |
| Models | Validation-only candidate comparison, chronological split counts and purged-training correlations |
| Portfolio | Interactive Plotly return/drawdown charts, benchmark, paid costs and full-portfolio metrics |
| Errors | Holdout errors by ticker, predicted versus actual return and the ten largest absolute errors |

Ticker selection affects only error diagnostics. Portfolio curves and metrics retain the original full universe. There are no threshold/hyperparameter controls: the dashboard shows a completed selection. Reload rechecks saved output hashes; it does not refresh market sources. Saved signals are historical and are not live trading recommendations.

## Integrity and interpretation

The explorer accepts a completed `status=reproduced` bundle with an adequate coverage record, `run-1/` numerical outputs, and `inputs/effective-config.json`. It verifies every declared numerical output hash plus the effective-config hash, checks required table columns, and checks that the validation-selected row agrees with the run summary. Missing/tampered files, blocked research and old bundles lacking the candidate comparison fail explicitly. The reader does not independently revalidate provider history or all original input files; use the research runner's frozen replay for that broader check.

MAE/RMSE are five-session return errors; tables format decimal returns as percentages. Net returns include configured costs. Drawdown includes initial trading costs and uses the running equity peak with the original initial capital as its lower bound. Correlations use only labeled training rows whose exit is strictly before validation. Holdout error analysis is descriptive and must not be used to tune further against this same holdout.

Availability assumptions, retrospective price adjustments, overlapping labels and the fixed ETF universe remain limitations. See [the full-run report](FULL_RUN.md) for that experiment's provenance and assumptions. A local saved-result dashboard is not evidence of live operational monitoring or reviewer credit.

## Verification

With dashboard dependencies installed:

```sh
uv run --locked --no-sync python -m pytest -q tests/unit/test_reporting.py tests/unit/test_plotly_report.py tests/integration/test_dashboard.py
```

Tests use explicitly fictional saved results. They check read-only loading, integrity failures, train-only correlations, independently calculated drawdown/error values and ticker filtering without portfolio changes. The integration tests skip if optional dashboard packages are absent.

## Following priorities

An optional [Dagster adapter](ORCHESTRATION.md) now provides manual execution and asset/run visibility around the existing frozen runner. Scheduling remains separate. Evidence.dev remains an alternative publishing platform. dlt remains deferred until there is a specific incremental source/destination, cursor, deduplication key and historical-revision policy. These platforms are not installed by the dashboard extra.
