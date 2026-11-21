---
name: capstone-verification
description: Verify capstone reproducibility, course acceptance, or source/network access; leave evidence-based project and session status.
---

# Capstone verification

1. Read the current official course criteria and the project specification; map each item to a concrete artifact and observed result. Read `.ai/BUGS.md`; add reproducible defects found during QA and link open implementation work from `.ai/BACKLOG.md`. Check session ownership and acquire object locks before changing shared artifacts.
2. Run applicable tests and the documented end-to-end and local-snapshot workflows where inputs exist. Record exact commands, status and relevant output; report missing external prerequisites as blockers.
3. Check timing and leakage, simulation calculations, source rights, documented commands, secrets and excluded data. Cross-check README and `docs/` results against run artifacts and verify reciprocal links and consistency of main `.ru.md` mirrors.
4. Separate verified, partial and outstanding criteria; include defense and peer-review obligations when applicable. Do not treat a test file, a design, or a mock as evidence of a successful real-data experiment. Mark bugs verified only after their recorded acceptance check passes.

## Network and source-access diagnostics

Use this workflow when DNS, package installation, GitHub, or market-data acquisition appears unavailable.

Reusable project checks live in `scripts/check_external_access.py` and `scripts/check_clean_install.py`. Run the first from the same network boundary as acquisition; it performs bounded requests (including only a short recent Stooq GLD sample) and deliberately does not retry HTTP 429. Run the second when package access is available; it installs `uv.lock` with the `dev` extra into a temporary environment with a fresh temporary uv cache, imports core/dev packages, checks notebook-format support and an XNYS session, and removes both temporary paths when complete.

For FRED, the reachability probe also tries a bounded `curl` request if Python `urllib` fails. It discards the response body and reports the curl HTTP status and remote IP separately, preserving both outcomes so a client/CDN-edge discrepancy is not mislabeled as total host unavailability. This checks only the landing page, not FRED series API access or vintage suitability.

1. **Identify the execution boundary first.** Run a resolver lookup and a bounded HTTPS request in the same environment that failed. If sandboxed probes report socket permission errors, do not label that a host or machine DNS outage. Repeat the minimal probes through an explicitly approved non-sandboxed diagnostic path; record which boundary each result came from.
2. **Separate failure layers.** Check name resolution, TCP/TLS reachability, and HTTP status independently. `NXDOMAIN`/`SERVFAIL`, timeout, connection refusal, certificate failure, HTTP 429, HTTP 403, and HTTP 5xx mean different things. A successful DNS lookup does not prove HTTPS or data access; an HTTP response proves host reachability but a 429/403 does not prove endpoint usability.
3. **Probe independent control and data endpoints.** Include a neutral control such as GitHub and the package index (PyPI), then the primary data provider(s), then plausible alternatives. For this project those may include CFTC website/archive and PRE API, Yahoo Finance, FRED, Stooq, and Alpha Vantage. Keep requests bounded; never bulk-download during a connectivity check.
4. **Inspect local network context read-only.** Where permitted, record active interface/default route, resolver configuration, VPN/proxy state and relevant environment proxy settings. If the sandbox prevents system tools or socket access, report that limitation instead of inferring a device configuration. Do not change DNS, VPN, proxy, firewall, or system network settings without explicit authorization.
5. **Evaluate a data fallback before adopting it.** Verify the required instruments and date coverage, OHLCV fields, raw/adjusted price semantics, corporate actions, timezone/calendar, rate limits and terms. For COT, prefer CFTC's primary records and preserve report-specific publication availability. A reachable service is not automatically a fit-for-purpose or point-in-time-safe source.
6. **Record reproducible evidence.** Log timestamp and timezone, environment/boundary, exact host/path (omit secrets and API keys), command, resolver/remote IP when available, DNS result, TLS result, HTTP status, and interpretation. Do not place tokens or full sensitive URLs in skill notes or project logs. Repeat only when state may have changed or when a targeted next step depends on the result.
7. **Choose the next action from evidence.** If all name lookups fail only inside the sandbox but succeed outside, classify as sandbox egress/resolver restriction and request the necessary approved operation. If lookups fail in both contexts, inspect resolver/network state with the device owner or network administrator. If DNS succeeds but HTTPS fails, investigate routing, proxy, TLS or provider filtering. If package index responds, retry the clean locked installation as a separate step; if a provider returns 429, honor its limits and do not disguise it as DNS failure.

Keep acquisition and clean-install gates independent. Continue offline deterministic QA while either external gate is unavailable; never replace real observations with synthetic fixtures or call cached dependencies a clean install.

## Session closeout and handoff

When the requested investigation or implementation is complete, close the work with a short evidence-based handoff; do not imply the whole capstone is finished when a project gate remains open.

1. Check the exact branch, worktree, commit base and working tree. Preserve edits that predate the current task; identify uncommitted work and do not commit, merge or push unless requested.
2. Record only commands actually run and their outcomes. Separate resolved diagnostics from remaining acquisition, data-quality, modeling, notebook and course-acceptance gates. Do not repeat broad or networked checks without a concrete reason.
3. Update the canonical backlog/next step and project status with the finding and the next actionable owner/action. Keep user-facing documentation bilingual when changing a main human-facing document; do not copy agent plans into `docs/`.
4. Release only object locks acquired by this session. Handoff the branch/worktree, changed paths, checks, known limitations, uncommitted state and one clear next action. State when the focused task is complete even if the overall project is not.
