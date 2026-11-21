#!/usr/bin/env bash
# cross-session-gate-hook.sh — Remind to update the shared session gate before ending
#
# ── Provenance / metadata ────────────────────────────────────────────────────
# Created-at:   2026-11-21 · scaffolded by /add-session-hook
# Event:        SessionEnd (registered in .claude/settings.local.json)
# Contract:     print-only reminder; ALWAYS exit 0 — хук не имеет права блокировать сессию
# Settings:     settings.yml#session_hooks.cross-session-gate (рядом с этим файлом)
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail
DIR="$(cd "$(dirname "$(python3 -c 'import os,sys;print(os.path.realpath(sys.argv[1]))' "${BASH_SOURCE[0]}")")" && pwd)"
SETTINGS="$DIR/settings.yml"

main() {
  local enabled gate_path reminder
  if ! enabled="$(yq -r '.session_hooks.cross-session-gate.enabled' "$SETTINGS" 2>/dev/null)"; then
    printf '⚙ [cross-session-gate] unable to read hook settings: %s\n' "$SETTINGS"
    return 0
  fi
  [ "$enabled" = "true" ] || return 0
  if ! gate_path="$(yq -r '.session_hooks.cross-session-gate.gate_path' "$SETTINGS" 2>/dev/null)"; then
    printf '⚙ [cross-session-gate] unable to read gate_path: %s\n' "$SETTINGS"
    return 0
  fi
  if ! reminder="$(yq -r '.session_hooks.cross-session-gate.reminder' "$SETTINGS" 2>/dev/null)"; then
    printf '⚙ [cross-session-gate] unable to read reminder: %s\n' "$SETTINGS"
    return 0
  fi
  [ -n "$reminder" ] && printf '⚙ [cross-session-gate] %s (%s)\n' "$reminder" "$gate_path"
}

main || true
exit 0
