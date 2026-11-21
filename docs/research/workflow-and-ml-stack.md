[EN](workflow-and-ml-stack.md) | [RU](workflow-and-ml-stack.ru.md)

# Workflow orchestration and MLOps stack assessment

**Assessment date:** 2026-11-21
**Status:** Research and recommendation; no platform has been adopted or deployed.

## Context

The capstone currently has a local Python research workflow, CLI/notebook entry points, Make/Just commands, cached source snapshots, feature construction, model evaluation, simulation and report generation. A full real-data run has not been established. The project rules say to keep the local core workflow working before adding orchestration or monitoring infrastructure. This assessment therefore describes decision gates and a possible direction; it is not evidence of an integration.

There are two distinct automation needs:

1. **Research pipeline:** ingest and validate market/COT snapshots, build point-in-time features, train/evaluate models, simulate strategies, and publish reports.
2. **Development-session controller:** periodically check a named object lock and, after it is free, launch one new Codex session with a saved task.

Keep the second function separate from the research pipeline. Launching an agent is a workspace/session-management action with different credentials, authorization and duplicate-run risks from producing analytical assets.

## macOS scheduling visibility

For a small local lock watcher, a per-user `launchd` LaunchAgent is the proportionate scheduler. Apple documents LaunchAgents as processes managed for the logged-in user and recommends `launchd` over cron for timed jobs. macOS Console can search system logs and activities; it is a log viewer rather than a workflow dashboard. The watcher should also write an application log and a small state record so the user can see `waiting`, `launched`, `completed` or `failed` without interpreting launchd internals. [Apple Service Management](https://developer.apple.com/documentation/ServiceManagement), [Apple scheduled jobs](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html), [Console User Guide](https://support.apple.com/guide/console/find-log-messages-and-activities-cnslbf30b61a/mac).

If a web UI is needed for the watcher, Prefect can represent polling and launch as a flow and expose scheduled flow runs in its UI. That introduces a Prefect server/worker and an agent-launch integration for a task that otherwise needs only one local process. Use it only if the watcher is part of a wider, already-operated Prefect deployment. [Prefect schedules](https://github.com/PrefectHQ/prefect/blob/main/docs/v3/concepts/schedules.mdx).

**Required watcher safeguards if implemented:** monitor only the configured lock; never remove another session's lock; start at most one Codex process; persist the task and attempt state; stop or disable itself after one launch; log stdout/stderr; require an explicit, bounded task prompt; and keep credentials outside the repository. A periodic checker cannot guarantee that a Codex process will finish or that a lock will stay free after the check; the launched session must acquire/check its own lock before editing. No such watcher is implemented by this document.

## Orchestration choices

| Option | What it offers | Fit here | Decision gate |
|---|---|---|---|
| Existing CLI + Make/Just | Direct local execution with few services and clear manual control | Best current baseline; already present | Keep while a single reproducible local run meets project needs |
| Dagster | Local web UI for runs, jobs, assets, schedules and sensors; asset catalog supports inspection of data products | Strongest first candidate if asset lineage and data-pipeline state become the main need | Prototype after repeated runs, freshness/recovery needs, or asset visibility become real requirements. The local UI/daemon can be started with `dg dev`; schedules and sensors require the daemon. [Dagster UI](https://dagster.io/docs/guides/operate/webserver) |
| Prefect | Python flow/task orchestration, scheduled deployments, run status and UI | A good alternative when the workflow is primarily a sequence of Python functions and execution visibility is the main need | Prefer it if flow-centric task management is more valuable than an asset catalog. A scheduler creates scheduled runs; a worker/work pool is still responsible for executing them. [Prefect schedules](https://github.com/PrefectHQ/prefect/blob/main/docs/v3/concepts/schedules.mdx) |
| launchd alone | Native macOS timed process launcher and Console-visible OS logs | Appropriate for the one-shot local lock watcher; no data-asset or pipeline UI | Use while it remains a single local utility |

**Recommendation:** keep the current CLI as the canonical user entry point. If automation is later justified, prototype Dagster first around the research assets, while keeping the existing Python functions and CLI usable. Choose Prefect instead if the desired abstraction is explicitly Python flows/tasks and Dagster's asset model adds no value. Do not run both orchestrators over the same stages.

dlt has a documented Dagster integration, but the project has no destination or incremental-load need for it today. If Dagster is later justified, first wrap the existing Python ingestion as an asset and preserve the source snapshots and validators; add dlt only if its source/normalization/destination behavior removes a demonstrated maintenance burden. [dlt and Dagster integration](https://dlthub.com/docs/walkthroughs/deploy-a-pipeline/deploy-with-dagster)

Potential Dagster assets could be `source_snapshot`, `validated_prices`, `validated_cot`, `feature_table`, `selected_model`, `holdout_evaluation`, `backtest`, and `research_report`. This is a design sketch, not an implemented asset graph. Ingestion should remain a callable Python boundary: the orchestrator invokes the existing ingest module and records its outputs/provenance rather than duplicating source logic.

## Adjacent tool assessment

| Tool | Appropriate role | Recommendation and trigger |
|---|---|---|
| **MLflow** | Track experiment parameters, metrics, code/data references and artifacts; its tracking UI works with local storage. [MLflow Tracking](https://mlflow.org/docs/latest/tracking/) | First optional addition once real repeated experiments can run. Record snapshot hashes, time split boundaries, model/search parameters, validation selection and untouched holdout results. Start local; model registry is unnecessary until there is a model lifecycle or deployment need. |
| **dlt** | Extract, normalize and load Python/API/database sources into a configured destination; custom Python sources and data structures are supported. [dlt pipeline](https://dlthub.com/docs/general-usage/pipeline), [dlt sources](https://dlthub.com/docs/general-usage/source) | Defer. Current ingestion preserves provider snapshots as local CSV/ZIP files with SHA-256 sidecars and has no persistent warehouse or incremental destination requirement. dlt would not replace source-specific validation, COT release evidence or point-in-time rules. Reconsider if multi-source extraction or a persistent destination is needed. |
| **dlt** | Extract, normalize and load Python/API/database sources into a configured destination; custom Python sources and data structures are supported. [dlt pipeline](https://dlthub.com/docs/general-usage/pipeline), [dlt sources](https://dlthub.com/docs/general-usage/source) | Defer. Current ingestion preserves provider snapshots as local CSV/ZIP files with SHA-256 sidecars and has no persistent warehouse or incremental destination requirement. dlt would not replace source-specific validation, COT release evidence or point-in-time rules. Reconsider if multi-source extraction or a persistent destination is needed. |
| **dbt Core** | SQL transformations and tests over relational/warehouse tables | Consider if the project grows a persistent SQL analytics layer with reusable transformations. Keep Python for source retrieval and point-in-time-sensitive logic unless an explicit SQL contract is useful. |
| **MetricFlow** | Define/query reusable metrics and dimensions on dbt semantic models. [dbt MetricFlow](https://docs.getdbt.com/docs/build/about-metricflow) | Add only if multiple consumers need consistent analytical/business metrics through a semantic layer. It does not replace the Python model-evaluation metrics or simulation logic. |
| **DVC** | Version large data/model artifacts and define file-based reproducible pipelines. It builds on Git for its important versioning workflows and does not provide full execution monitoring/recovery. [DVC User Guide](https://doc.dvc.org/user-guide) | Defer: this workspace currently has no Git repository, and market-data redistribution/rights must be resolved before storing snapshots in any remote. Consider later for snapshot/version reproducibility. Avoid making DVC and an orchestrator competing owners of the same stage DAG. |
| **Feast** | Historical/offline feature retrieval plus low-latency online feature serving; point-in-time training retrieval. [Feast overview](https://docs.feast.dev/) | Defer until there is an online inference service and a train/serve feature-consistency problem. The present workflow is batch research. |
| **Evidently** | Data quality and drift reports/monitoring across successive datasets or prediction batches | Defer until repeated production-like data/prediction streams exist. For a fixed research sample, ordinary dataset validation and evaluation reports are more direct. |
| **Prometheus + Grafana** | Operational time-series collection/alerting and dashboards. [Prometheus overview](https://prometheus.io/docs/introduction/overview/), [Grafana dashboards](https://grafana.com/docs/grafana/latest/visualizations/dashboards/build-dashboards/create-dashboard/) | Defer until a long-running service or scheduled workers expose operational metrics. These tools do not replace experiment tracking or pipeline run history. |
| **Telegram alerts** | Delivery channel for concise job failures or completion signals | Add only after a scheduler exists and alerts are useful. Keep bot tokens in the environment/secret store; report run IDs and log locations, not private session contents. |

## Staged path

1. Preserve the CLI and current deterministic checks; verify the core workflow with real, legally usable snapshots before claiming an end-to-end research pipeline.
2. Add MLflow locally when repeated real model runs need comparable, durable metadata.
3. Prototype one orchestrator only when repeated scheduling, lineage, retries/recovery or run visibility are demonstrated needs. Start with Dagster for data assets; choose Prefect for flow-first execution.
4. Add dbt/MetricFlow, DVC, Feast, Evidently and monitoring/alerts only when their stated triggers arise. Keep the lock-waiting Codex controller as a separate local utility.

## Limitations

This is a tool-fit assessment based on official product documentation and the current project plan, not a benchmark, cost estimate, security review or integration test. No tool was installed, configured, scheduled or tested as part of this research. Product capabilities and plans can change; recheck official docs before implementation.
