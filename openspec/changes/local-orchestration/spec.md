# Local frozen-research orchestration

The optional Dagster adapter SHALL call the existing `capstone.research.run` exactly once per materialization, preserving its atomic freeze/coverage/two-run equality protocol. It SHALL use cached inputs and SHALL NOT acquire sources, schedule downloads, change models or weaken research gates.

- Represent the frozen bundle, feature table, validation comparison and strategy report as assets from the same atomic computation. Report their recorded paths, row counts, chosen model, numerical-output count and metrics as materialization metadata.
- Use a new directory under configured local output storage for each Dagster run. Never overwrite a prior research bundle.
- Treat nonzero research status or failed output integrity as a failed Dagster run; emit no successful asset materializations for blocked research.
- Keep state under ignored `.run/` and research outputs under ignored `artifacts/`. Local UI binds to localhost. No schedule or daemon service is installed persistently.
- The standalone CLI/notebook and frozen replay SHALL remain usable without Dagster. Optional orchestration dependencies and human Make commands SHALL be documented independently from dashboard dependencies.
- Verify successful and blocked materializations with fictional fixtures, validate definitions through available Dagster CLI, and execute one real offline materialization without changing source snapshots.
