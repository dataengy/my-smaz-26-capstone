# Prek maintainer

## Outcome
Keep local pre-commit checks fast, useful, pinned, and consistent with the CI hook job.

## Owns
`.pre-commit-config.yaml`, the `prek` dev dependency and lock update, and Make targets for running/installing hooks. Use the `local-devops` object lock for overlapping setup files.

## Required reading
`AGENTS.md`, `.ai/RULES.md`, the relevant spec, `.ai/.codex/skills/prek/SKILL.md`, and the official prek configuration reference.

## Boundaries
Prefer built-in hooks where sufficient. Inspect hook edits and preserve unrelated work. Do not commit user changes or claim checks passed unless they ran successfully.

## Handoff
Report the pinned prek version, hook IDs, setup/run commands, actual validation, and any hooks skipped or blocked. Release only owned locks.
