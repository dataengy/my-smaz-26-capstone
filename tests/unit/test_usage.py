import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('codex_usage', Path(__file__).parents[2] / 'scripts' / 'codex_usage.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def write(root, name, *records):
    (root / name).write_text('\n'.join(map(json.dumps, records)))


def meta(sid, cwd=None, parent=None):
    return {'type': 'session_meta', 'payload': {'id': sid, 'cwd': str(cwd) if cwd else None, 'parent_thread_id': parent}}


def legacy(total):
    return {'type': 'event_msg', 'payload': {'type': 'token_count', 'info': {'total_token_usage': {'total_tokens': total}}}}


def test_project_scope_dedup_and_no_private_output(tmp_path):
    root = tmp_path / 'sessions'; root.mkdir()
    project = tmp_path / 'project'; project.mkdir()
    write(root, 'one.jsonl', meta('one', project), legacy(12), {'type': 'response_item', 'payload': {'text': 'secret not for export'}})
    write(root, 'duplicate.jsonl', meta('one', project), legacy(12))
    write(root, 'child.jsonl', meta('child', parent='one'), legacy(5))
    write(root, 'other.jsonl', meta('other', tmp_path, 'one'), legacy(1000))
    report = module.summarize(root, project)
    assert report['sessions_matched_by_cwd'] == 1
    assert report['sessions_attributed_by_parent'] == 1
    assert report['duplicate_session_files'] == 1
    assert report['last_reported_cumulative_usage_sum']['total_tokens'] == 17
    assert 'secret not for export' not in json.dumps(report)


def test_conflicting_duplicate_and_new_schema_are_not_silently_summed(tmp_path):
    root = tmp_path / 'sessions'; root.mkdir()
    project = tmp_path / 'project'; project.mkdir()
    write(root, 'one.jsonl', meta('one', project), legacy(12))
    write(root, 'copy.jsonl', meta('one', project), legacy(14))
    write(root, 'two.jsonl', meta('two', project), {'type': 'token_usage_record', 'payload': {'thread_token_usage': {'total_tokens': 8}}})
    report = module.summarize(root, project)
    assert report['sessions_with_conflicting_usage'] == 1
    assert report['sessions_with_usage'] == 1
    assert report['last_reported_cumulative_usage_sum']['total_tokens'] == 8
    assert report['model_counts']['unknown'] == 2


def test_missing_root_and_invalid_lines_are_reported(tmp_path):
    assert module.summarize(tmp_path / 'absent', tmp_path)['sessions_root_available'] is False
    root = tmp_path / 'sessions'; root.mkdir()
    (root / 'bad.jsonl').write_text('not json\n')
    report = module.summarize(root, tmp_path)
    assert report['malformed_lines'] == 1
    assert report['files_without_session_id'] == 1
