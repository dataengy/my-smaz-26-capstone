#!/usr/bin/env python3
"""Summarize local Codex metadata without exporting conversation text."""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import yaml

FIELDS = ('input_tokens', 'cached_input_tokens', 'output_tokens', 'reasoning_output_tokens', 'total_tokens')


def _usage(value):
    if not isinstance(value, dict):
        return None
    result = {k: value[k] for k in FIELDS if isinstance(value.get(k), int) and not isinstance(value[k], bool) and value[k] >= 0}
    return result or None


def summarize(root: Path, project: Path) -> dict:
    project = project.resolve()
    files = defaultdict(list)
    unreadable = malformed = without_id = 0
    root_available = root.is_dir()
    for path in root.rglob('*.jsonl') if root_available else ():
        meta = None
        legacy = newer = model = None
        try:
            with path.open(encoding='utf-8') as stream:
                for line in stream:
                    try:
                        record = json.loads(line)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        malformed += 1
                        continue
                    if not isinstance(record, dict) or not isinstance(record.get('payload'), dict):
                        malformed += 1
                        continue
                    payload = record['payload']
                    kind = record.get('type')
                    if kind == 'session_meta':
                        meta = payload
                    elif kind == 'turn_context':
                        candidate = payload.get('model')
                        if isinstance(candidate, str) and re.fullmatch(r'[A-Za-z0-9._-]{1,80}', candidate):
                            model = candidate
                    elif kind == 'event_msg' and payload.get('type') == 'token_count':
                        info = payload.get('info')
                        if isinstance(info, dict):
                            legacy = _usage(info.get('total_token_usage')) or legacy
                    elif kind == 'token_usage_record':
                        newer = _usage(payload.get('thread_token_usage')) or newer
        except (OSError, UnicodeError):
            unreadable += 1
            continue
        sid = (meta.get('id') or meta.get('session_id')) if isinstance(meta, dict) else None
        if not isinstance(sid, str) or not sid:
            without_id += 1
            continue
        cwd = meta.get('cwd')
        parent = meta.get('parent_thread_id')
        if isinstance(cwd, str) and cwd:
            try:
                Path(cwd).resolve().relative_to(project)
                scope = 'project'
            except (ValueError, OSError, RuntimeError):
                scope = 'other'
        else:
            scope = 'unknown'
        files[sid].append({'scope': scope, 'parent': parent if isinstance(parent, str) else None,
                           'usage': legacy or newer, 'model': model})

    # Explicit external paths never become project sessions through a parent link.
    sessions = {}
    conflicts = 0
    for sid, copies in files.items():
        scopes = {c['scope'] for c in copies} - {'unknown'}
        parents = {c['parent'] for c in copies if c['parent']}
        if len(scopes) > 1 or len(parents) > 1:
            conflicts += 1
            continue
        sessions[sid] = {'scope': next(iter(scopes), 'unknown'), 'parent': next(iter(parents), None), 'copies': copies}
    selected = {sid for sid, s in sessions.items() if s['scope'] == 'project'}
    direct = len(selected)
    while True:
        children = {sid for sid, s in sessions.items() if s['scope'] == 'unknown' and s['parent'] in selected} - selected
        if not children:
            break
        selected.update(children)

    totals = Counter()
    field_coverage = Counter()
    models = Counter()
    with_usage = usage_conflicts = 0
    for sid in selected:
        copies = sessions[sid]['copies']
        usage_options = {tuple(sorted(c['usage'].items())) for c in copies if c['usage'] is not None}
        if len(usage_options) > 1:
            usage_conflicts += 1
        elif usage_options:
            with_usage += 1
            for key, value in dict(next(iter(usage_options))).items():
                totals[key] += value
                field_coverage[key] += 1
        model_options = {c['model'] for c in copies if c['model']}
        models[next(iter(model_options)) if len(model_options) == 1 else 'unknown'] += 1
    return {
        'sessions_root_available': root_available,
        'sessions_matched_by_cwd': direct,
        'sessions_attributed_by_parent': len(selected) - direct,
        'sessions_with_usage': with_usage,
        'sessions_without_usage': len(selected) - with_usage - usage_conflicts,
        'sessions_with_conflicting_usage': usage_conflicts,
        'duplicate_session_files': sum(len(copies) - 1 for copies in files.values()),
        'sessions_with_conflicting_identity': conflicts,
        'files_without_session_id': without_id,
        'unreadable_files': unreadable,
        'malformed_lines': malformed,
        'last_reported_cumulative_usage_sum': {field: totals[field] if field_coverage[field] else None for field in FIELDS},
        'sessions_with_field': {field: field_coverage[field] for field in FIELDS},
        'model_counts': dict(sorted(models.items())),
        'limitations': ('Experimental metadata only. Parent attribution requires a missing CWD; explicit external CWDs are excluded. '
                        'Legacy total_token_usage is preferred over thread_token_usage when both exist. '
                        'Conflicting duplicate counters are excluded. Counter semantics and coverage are unverified; '
                        'totals are not verified billing and no cost is estimated.'),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path.cwd())
    parser.add_argument('--settings', type=Path, default=Path('config/settings.yml'))
    parser.add_argument('--sessions-root', type=Path, help='Override codex_sessions_root from settings')
    args = parser.parse_args()
    try:
        settings = yaml.safe_load(args.settings.read_text(encoding='utf-8'))
    except OSError as exc:
        parser.error(f'Cannot read settings {args.settings}: {exc}')
    if not isinstance(settings, dict):
        parser.error(f'Settings must be a YAML mapping: {args.settings}')
    configured_root = settings.get('codex_sessions_root')
    if not isinstance(configured_root, str) or not configured_root:
        parser.error(f'Settings must define a non-empty codex_sessions_root: {args.settings}')
    sessions_root = args.sessions_root or Path(configured_root).expanduser()
    print(json.dumps(summarize(sessions_root, args.project), indent=2))


if __name__ == '__main__':
    main()
