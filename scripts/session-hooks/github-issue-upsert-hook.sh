#!/usr/bin/env bash
# github-issue-upsert-hook.sh — Remind to reconcile actionable backlog changes with GitHub Issues using stable IDs and upsert semantics
#
# ── Provenance / metadata ────────────────────────────────────────────────────
# Created-at:   2026-11-21 · scaffolded by /add-session-hook
# Event:        SessionEnd (registered in .claude/settings.local.json)
# Contract:     print-only reminder; ALWAYS exit 0 — хук не имеет права блокировать сессию
# Settings:     settings.yml#session_hooks.github-issue-upsert (рядом с этим файлом)
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail
DIR="$(cd "$(dirname "$(python3 -c 'import os,sys;print(os.path.realpath(sys.argv[1]))' "${BASH_SOURCE[0]}")")" && pwd)"
SETTINGS="$DIR/settings.yml"

main() {
  local enabled repo path changed=false reminder
  enabled="$(yq -r '.session_hooks.github-issue-upsert.enabled' "$SETTINGS" 2>/dev/null)" || return 0
  [ "$enabled" = "true" ] || return 0
  repo="$(git -C "$DIR" rev-parse --show-toplevel 2>/dev/null)" || return 0
  while IFS= read -r path; do
    [ -n "$path" ] || continue
    if ! git -C "$repo" diff HEAD --quiet -- "$path" 2>/dev/null; then
      changed=true
      break
    fi
  done < <(yq -r '.session_hooks.github-issue-upsert.tracked_paths[]' "$SETTINGS" 2>/dev/null)
  [ "$changed" = true ] || return 0
  reminder="$(yq -r '.session_hooks.github-issue-upsert.reminder' "$SETTINGS" 2>/dev/null)" || return 0
  [ -n "$reminder" ] && printf '⚙ [github-issue-upsert] %s\n' "$reminder"
}

main || true
exit 0
