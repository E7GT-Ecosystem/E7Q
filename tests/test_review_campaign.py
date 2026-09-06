"""Failure and coverage checks for the local campaign evidence runner."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('review_campaign', ROOT / 'scripts/review_campaign.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def report(when, outcome, **extra):
    return SimpleNamespace(nodeid='test_case', when=when, outcome=outcome,
                           failed=outcome == 'failed', skipped=outcome == 'skipped',
                           passed=outcome == 'passed', longrepr=None, **extra)


def test_teardown_failure_overrides_success():
    recorder = runner.Recorder()
    recorder.pytest_runtest_logreport(report('call', 'passed'))
    recorder.pytest_runtest_logreport(report('teardown', 'failed'))
    assert runner.verdict(0, list(recorder.cases.values()), []) == 'FAIL'


def test_skip_xfail_empty_and_collection_failure_cannot_pass():
    for phase, extra in [('setup', {}), ('call', {'wasxfail': 'expected'})]:
        recorder = runner.Recorder()
        recorder.pytest_runtest_logreport(report(phase, 'skipped', **extra))
        assert runner.verdict(0, list(recorder.cases.values()), []) == 'NOT_ASSESSED'
    assert runner.verdict(0, [], []) == 'FAIL'
    assert runner.verdict(0, [{'status': 'PASS'}], ['collection error']) == 'FAIL'
    assert runner.verdict(2, [{'status': 'PASS'}], []) == 'FAIL'


def test_manifest_covers_each_repository_test_file_and_scope():
    manifest = json.loads((ROOT / 'docs/e7q-ir/REVIEW_CAMPAIGN.json').read_text())
    entries = manifest['capabilities']
    assert len({e['id'] for e in entries}) == len(entries)
    assert sorted(e['test_file'] for e in entries) == sorted(str(p.relative_to(ROOT)) for p in (ROOT / 'tests').glob('test_*.py'))
    for entry in entries:
        assert entry['scope'] and entry['limits'] and entry['next_gate']
        assert all((ROOT / path).exists() for path in entry['implementation'])
    assert len(manifest['external_report_groups']) == 25
    assert all(g['status'] == 'UNRESOLVED_ORIGINAL_HARNESS' for g in manifest['external_report_groups'])


def test_fingerprint_detects_changed_fixture(tmp_path):
    (tmp_path / 'examples').mkdir()
    fixture = tmp_path / 'examples/input.json'
    fixture.write_text('{}')
    before = runner.fingerprint(tmp_path)
    fixture.write_text('{"changed":true}')
    assert before != runner.fingerprint(tmp_path)
