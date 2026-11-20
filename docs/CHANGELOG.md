[EN](CHANGELOG.md) | [RU](CHANGELOG.ru.md)

# Changelog

This log records implemented project changes. It does not claim that planned work, financial results or external deployments are complete. The directory is not yet a Git repository, so the entries below are based on recorded project evidence rather than commit history.

## 2026-11-21

- Organized agent plans, backlog, status, session management, roles and skills under `.ai/`; added project documentation and Russian mirrors under `docs/`.
- Added research workflow scaffolding, local snapshot provenance, point-in-time feature checks, model selection, simulations and reporting; no real-data experiment has completed.
- Added evidence for four historical COT report publications and documented conservative eligibility cutoffs. Coverage remains insufficient for the intended study.
- Created the lockfile and local environment, organized tests, and documented installation and provider access limitations.
- Improved safeguards for incomplete market candles, invalid simulation prices, saved-model inference and reporting of the frozen model's training cutoff.
- Added a privacy-conscious, experimental Codex session metadata audit; token coverage and billing remain unverified.
- Moved runtime/source settings into `config/config.yml` and `config/settings.yml`; the CLI, feature builder, model universe, notebook and Codex metadata audit now read the configured values.
- Added project-local object locking for this non-Git shared directory, expanded ready-to-copy parallel-session prompts, and documented Git worktrees as the isolated path for critical work that cannot wait when Git is available.
- Split common human commands into `Makefile` and supporting multi-step/agent workflows into `Justfile`; added a bilingual command reference and build-tooling agent/skill guidance. The actual verification evidence is recorded in `.ai/STATUS.md`.
