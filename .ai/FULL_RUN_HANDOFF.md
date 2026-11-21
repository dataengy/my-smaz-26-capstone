# Full-COT experiment handoff — 2026-11-21

Owner: `codex-full-run-fixes-20261121`. **Full real-data execution and saved-snapshot replay completed.** This supersedes this session's earlier blocked-attempt evidence; other project acceptance obligations remain separate.

## Scope and integration

- Owned `src/capstone/research.py`, new `cot_publication_audit.py`, their dedicated tests and `docs/FULL_RUN.md` / `.ru.md`. Fixed BUG-005/006 and updated only the full-experiment acceptance subsection in the spec.
- Kept shared market snapshots, `config/release_dates.csv`, data/model/strategy parameters and other sessions' source/architecture/docs work intact. The source team independently extended the canonical manifest during this work; this experiment uses its own frozen audit to avoid concurrent writers.
- Shared status and implementation-plan objects were owned by `verify-snapshots-cot-20261121` during final handoff. Integrate this result into those records when that ownership is handed off; do not clear their locks. The canonical human evidence is [FULL_RUN.md](../docs/FULL_RUN.md), with a synchronized Russian mirror.

## Source evidence and actual execution

Official public CFTC API row creation/update metadata was checked against five modeled position fields in verified annual archives. Only post-public-launch, unchanged, exact-matching complete contract pairs entered the separate 213-report manifest. Availability uses next-day 05:00 UTC after the later pair timestamp; it is conservative public-API availability, not original static-report release timing. Raw response/query, retrieval time, archive hashes and field audit are frozen. See the report for CFTC launch/simultaneous-publication and Socrata system-field sources.

Actual commands:

```sh
.run/venv/bin/python -m capstone.cot_publication_audit --output artifacts/cot-publication-audit-20261121-retry
.run/venv/bin/python -m capstone.research --config .run/full-cot-verified-config.yml --output artifacts/full-cot-20261121-verified
.run/venv/bin/python -m capstone.research --replay artifacts/full-cot-20261121-verified --output artifacts/full-cot-20261121-replay
CAPSTONE_E2E_CONFIG=.run/full-cot-verified-config.yml .run/venv/bin/python -m pytest -q -ra
```

The first audit attempt hit sandbox DNS failure and retained an empty failed directory; the approved network retry succeeded. Both complete experiment commands exited 0. The dedicated runtime config uses the existing universe/settings, audited manifest and exclusive end 2026-11-21. A reconstruction recipe and all hashes are in the report.

## Verified results

- Real feature table: 1916 rows, 1906 labeled. Per ETF: 953 labeled signal dates spanning 2022-10-31–2026-11-12 and using 211 distinct reports. Retained train/validation/holdout: 565/185/191; purge removes 6/6/0 rows per ETF.
- Validation selected **mean**, threshold 0. Holdout MAE **0.04425741**, RMSE **0.05882651**. Trees and forests did not beat mean on validation. No tuning followed holdout inspection.
- Event simulation / benchmark execution dates: 2026-02-10–2026-11-20. Both policies coincide at the selected threshold; net return **-38.6062%**, buy-hold **-39.6260%**. No profitability is established.
- Original experiment plus standalone saved-bundle replay: **58 unchanged input hashes**, **19 identical required numerical output hashes across four real calculations**. A separate assertion compared both stored evidence files against actual input bytes and confirmed agreement.
- Adequate-history fictional subprocess integration also verifies relocation and rejection of tampered inputs. Equality now rejects identically incomplete result sets.
- Full suite with real-data E2E enabled: **73 passed, 3 skipped, 66 warnings**, 101.04 seconds. Skips: fresh-origin clone and two live-provider probes, all opt-in. `git diff --check` passed (separate existing CRLF normalization notice on another session's manifest).

## Remaining limitations

Current adjusted vendor series and archive values are not captured historical vintages. Public-row metadata supports conservative availability but does not provide historical HTTP access logs. Dependency deprecation warnings remain; fresh-origin and live-probe opt-in tests were not run here. No new model selection should use this holdout. Do not present the two coincident policies as independent empirical strategies or the negative returns as a profitable result.

Only this session's advisory locks are released at handoff. Downloaded evidence, snapshots and numerical artifacts remain ignored and local; no publication or commit was requested.
