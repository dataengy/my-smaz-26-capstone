[EN](SYNTHETIC_DEMO.md) | [RU](SYNTHETIC_DEMO.ru.md)

# Run the synthetic human demo

This offline demo generates source-shaped files under `data/synthetic/human-demo/`, sends them through the project's real feature, chronological model-selection and trading-simulation functions, then opens a visual report. All values are fictional. The COT release times are invented for the demo and are not CFTC publication evidence. Synthetic holdout metrics show that the code path ran; they say nothing about trading quality.

## Run it

From the project root, after installing Python 3.11+ and `uv`:

```sh
make setup
make demo-synthetic
```

The command uses the deterministic settings in [`config/synthetic_demo.yml`](../config/synthetic_demo.yml) and writes replayable synthetic CSVs plus a provenance manifest under `data/synthetic/human-demo/`. Open `artifacts/synthetic-demo/index.html` in a browser to see the report; on macOS, run `open artifacts/synthetic-demo/index.html`. The report embeds a prominent synthetic-only warning and shows generated price paths, synthetic test predictions, and simulated equity curves. It does not download data or change the real-data configuration.

If you only want to verify the demo without opening a browser:

```sh
make test-demo-synthetic
```

The test writes to a temporary directory and checks that the inputs, machine-readable summary, synthetic disclaimer and all three rendered charts are present. `make test` also runs this test as part of the complete suite. `just verify` runs the same tests plus lockfile and compile checks.

## Generated files

- `data/synthetic/human-demo/*.csv` and `manifest.json`: generated input snapshots and their seed/timing disclaimer. These files are ignored by Git and can be recreated with the command above.
- `artifacts/synthetic-demo/index.html`: visual walkthrough.
- `artifacts/synthetic-demo/summary.json`: machine-readable run metadata, feature list, split dates and synthetic-only metrics.
- `artifacts/synthetic-demo/*.png`: the report's rendered figures for reuse in a clearly labeled software walkthrough.

The generator uses seed `2026`, NYSE session labels for ETF and equity-index bars, full daily labels for the fictional crypto bars, and explicitly timestamped made-up weekly COT rows. It runs the same feature builder (including publication-time joins), chronological training/validation/test splitting, model selection, event-ordered simulation, fixed-notional vectorized simulation, and buy-and-hold benchmark used by the project. The demonstration config uses a smaller model grid to keep the run quick; it does not change the research config.

Do not use these files in a research result, defense performance claim, or investment decision. For the real experiment, follow the [research runbook](RUNBOOK.md); real provider snapshots and sufficient report-specific COT publication evidence are still required.
