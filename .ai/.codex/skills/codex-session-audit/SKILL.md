---
name: codex-session-audit
description: Use when assessing project Codex sessions, token usage, and agent collaboration efficiency.
---

# Codex session audit

1. Inspect available metadata schemas and determine the authorized project scope using working-directory and parent relationships where supported. Record uncertain attribution and coverage.
2. Establish whether usage counters are per-message or cumulative before aggregation; deduplicate and avoid invented counts. Never estimate monetary cost without verified rates or billing.
3. Produce aggregate counts and concrete evidence of duplication or wasted context. Do not copy raw transcripts, credentials, or records from other projects into the repository or external services.
4. Keep session management and audit operations under `.ai/`, without copying raw session logs. Document missing records and counter semantics. Evaluate Langfuse or MLflow only against actual integration and privacy requirements; do not claim full capture without verification.
