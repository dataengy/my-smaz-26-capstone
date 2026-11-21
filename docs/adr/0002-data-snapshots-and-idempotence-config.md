[EN](0002-data-snapshots-and-idempotence-config.md) | [RU](0002-data-snapshots-and-idempotence-config.ru.md)

# ADR-0002: Preserve research snapshots and keep temporary configuration local

- **Status:** Accepted for the current local workflow; external backup storage is not implemented by this ADR.
- **Date:** 2026-11-21
- **Scope:** Data retention, Git LFS adoption and `.run/idempotence-settings.yml` placement.

## Context

Downloading data again is not a guarantee of restoring the original research inputs. Project acquisition has encountered DNS failures and HTTP 403 responses. Historical market prices can be revised or retrospectively adjusted. CFTC provides [annual historical archives](https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm), but availability of an archive does not guarantee byte-identical recovery of an earlier download or establish report publication timestamps.

At inspection on 2026-11-21, `data/` occupied approximately 21 MB. The [project rules](../../.ai/RULES.md) and [implementation plan](../../.ai/IMPLEMENTATION_PLAN.md) exclude downloaded data from Git. The local working-tree implementation in `src/capstone/research.py` already copies raw snapshots, release evidence, configuration, source code and dependency definitions into an experiment directory, records input hashes and supports deterministic output comparison. That implementation was uncommitted when this ADR was prepared and is outside this documentation commit. It is not evidence that a complete real-data experiment or external backup has succeeded.

The ignored `.run/idempotence-settings.yml` is largely a copy of [the shared settings](../../config/settings.yml), with `output_dir: .run/idempotence-output`. At inspection, no references to this temporary filename were found in project code or documentation, and it lacked the shared `download_cache_ttl_hours` setting. Promoting the copy would introduce another maintained configuration that can drift.

## Decision

1. Keep `data/` as an ignored local cache. Do not enable Git LFS for the entire directory now.
2. Preserve immutable input snapshots for significant experiments. Include raw inputs and provenance sidecars, SHA-256 hashes, source/retrieval details, effective configuration, the COT release manifest and the code/dependency version needed for replay. Preserve the original bytes when refreshing the working cache.
3. Retain those experiment bundles in separate backup storage; keep a small snapshot manifest and restoration instructions in Git. Hashes identify and verify data but cannot restore missing bytes. The backup destination, retention policy and restoration procedure remain to be implemented and verified.
4. Check provider redistribution rights before sharing snapshots. The [yfinance project](https://github.com/ranaroussi/yfinance) warns that Yahoo Finance API use is intended for personal use; public redistribution rights have not been established here. This ADR does not authorize publishing downloaded market data.
5. Leave `.run/idempotence-settings.yml` local and temporary. Keep shared research/runtime settings in `config/settings.yml` and generated verification outputs under `.run/`.
6. If idempotence verification becomes a maintained, documented scenario, introduce a named profile under `config/`. Prefer overriding only the differing parameters instead of duplicating all shared settings. Implement and verify any required profile/override support before documenting it as available.

## Alternatives considered

- **Always download again:** insufficient for exact replay because source access and historical values can change.
- **Track all of `data/` with Git LFS:** deferred. [Git LFS](https://git-lfs.com/) stores pointers in Git and file contents on a separate server. It can version snapshots alongside code, but adds storage and retrieval dependencies and does not resolve redistribution rights. Current project rules also exclude these files from Git.
- **Move the temporary settings copy directly into `config/`:** deferred because it would preserve duplicated settings without a maintained scenario or references.

## Consequences and revisit criteria

The local workflow remains simple, while exact reproducibility depends on preserving and backing up the actual experiment inputs. Local frozen bundles alone do not protect against loss of the machine or disk. Derived data and generated outputs remain reproducible artifacts outside Git unless a separate decision establishes a reason to retain them.

Revisit LFS when collaborators need specific licensed data versions restored with a checkout and its storage/access requirements are justified. Such adoption requires an explicit revision of the current data-in-Git policy and an explicit snapshot scope, rather than tracking every cache file. Revisit configuration placement when a stable idempotence command and a documented profile contract exist.

This ADR records policy only: no files in `data/` or `.run/` were moved, no LFS configuration was added and no external backup was created.
