[EN](0001-orchestration-and-experiment-management.md) | [RU](0001-orchestration-and-experiment-management.ru.md)

# ADR-0001: Workflow orchestration and experiment management

- **Status:** Proposed
- **Date:** 2026-11-21
- **Decision owners:** Project orchestrator and maintainers
- **Scope:** Local research workflow and its experiment metadata; excludes the separate Codex lock-watcher/controller.
- **Evidence:** [Workflow and MLOps stack assessment](../research/workflow-and-ml-stack.md)

## Context

The project already has a local Python CLI/notebook workflow, Make/Just entry points and deterministic test coverage. The full research run on real data is not yet verified. There is no established operational requirement for frequent scheduled runs, service-level monitoring, low-latency inference or an online feature store. The project rules explicitly defer infrastructure until the local core works.

## Proposed decision

1. Keep the CLI and Make/Just commands as the canonical local workflow.
2. Do not adopt Prefect, Dagster, or dlt yet. If repeated execution, asset lineage, freshness, retries/recovery or run visibility become demonstrated needs after a real-data workflow works, prototype **Dagster first** as a thin adapter around the existing Python stages. dlt focuses on extracting, normalizing and loading data into a destination; the current contract instead keeps provider snapshots as local files with SHA-256 metadata and has no warehouse or incremental destination requirement. Consider dlt later only if multi-source extraction, schema evolution or a persistent destination becomes a concrete need. Do not add dlt under Dagster by default or orchestrate the same stages twice.
3. Evaluate **local MLflow Tracking** when repeated real experiments need comparable parameters, data snapshot identifiers, metrics and artifacts. Defer model registry until model lifecycle/deployment needs exist.
4. Keep the Codex lock watcher as a separate local controller; it must not be a research asset or run the data pipeline.
5. Defer dbt/MetricFlow, DVC, Feast, Evidently, Prometheus/Grafana and Telegram alerts until their specific conditions in the assessment are met.

This is a proposal, not an accepted implementation decision. No software installation, service, schedule, or integration is authorized or implied by this document.

## Alternatives considered

### Keep the current local CLI

Lowest operational burden and already matches project shape. It remains the selected current state; reconsider only when the stated orchestration needs appear.

### Adopt Dagster immediately

Its asset-oriented UI is a strong match for source snapshots, validated inputs, feature data, models and reports. Immediate adoption would add a service/daemon before a complete real-data workflow and operational need have been established.

### Adopt Prefect immediately

Prefect offers flow/task execution, schedules and a run UI, and is a sensible flow-centric alternative. The current assessment prefers Dagster only if future needs center on data assets and lineage.

### Add dlt under Dagster now

dlt can load Python data structures and custom sources into destinations, and its documented Dagster integration can expose dlt sources as assets. The project currently needs reproducible local snapshots, source-specific validation, point-in-time availability rules and offline replay; it does not need a destination warehouse or dlt's normalization/state layer. Adding both tools now would overlap the existing downloader and add setup without replacing the project's research-specific checks.

### Adopt the entire proposed tool list

Rejected. Several tools overlap in orchestration, pipeline execution, data modeling, tracking or monitoring. Adding them before their corresponding requirements exist increases setup and maintenance without demonstrated value.

## Consequences and revisit criteria

- The local CLI remains usable without an orchestration server.
- If an orchestrator is evaluated, implement it as a thin adapter around existing stage functions and preserve an offline/manual path.
- Keep source snapshots, point-in-time availability, time-based splits, holdout protection and cost-aware evaluation explicit in every orchestration layer.
- Revisit after the real-data workflow is reproducible and at least one concrete need appears: recurring schedules, operational recovery, asset lineage/freshness, or several users needing run visibility.
- Revisit MLflow after the first set of repeatable real experiments; record whether local storage is sufficient.
- Revisit other tools only when their specific triggers documented in the assessment are met.
