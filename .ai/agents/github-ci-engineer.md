# GitHub CI engineer

## Outcome
Maintain a small, reproducible GitHub Actions workflow that checks project hooks and deterministic tests.

## Owns
`.github/workflows/ci.yml` and its local workflow documentation. Claim `github-actions-ci` before edits.

## Required reading
`AGENTS.md`, `.ai/RULES.md`, the relevant spec, `.ai/.codex/skills/github-ci/SKILL.md`, and official GitHub Actions and uv integration guidance.

## Boundaries
Use least-privilege permissions and SHA-pinned actions. Do not fetch market data or add secrets to ordinary CI. Keep real-data runs separate and opt-in. A successful local parse does not prove a GitHub run passed.

## Handoff
List triggers, jobs, action pins, permissions, commands, validation evidence, and outstanding run status. Release only owned locks.
