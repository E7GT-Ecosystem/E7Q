"""Run the repository-owned review campaign; never authenticate external claims."""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout, redirect_stderr
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def verdict(exit_code, cases, collection_errors):
    if exit_code or collection_errors or not cases or any(c['status'] == 'FAIL' for c in cases):
        return 'FAIL'
    if any(c['status'] != 'PASS' for c in cases):
        return 'NOT_ASSESSED'
    return 'PASS'


class Recorder:
    def __init__(self):
        self.cases = {}
        self.collection_errors = []

    def pytest_collectreport(self, report):
        if report.failed:
            self.collection_errors.append(str(report.longrepr))

    def pytest_runtest_logreport(self, report):
        case = self.cases.setdefault(report.nodeid, {'id': report.nodeid, 'status': 'NOT_ASSESSED', 'phases': []})
        case['phases'].append({'phase': report.when, 'outcome': report.outcome,
                               'detail': str(report.longrepr) if report.longrepr else None})
        if report.failed:
            case['status'] = 'FAIL'
        elif case['status'] != 'FAIL':
            if report.skipped or getattr(report, 'wasxfail', False):
                case['status'] = 'NOT_ASSESSED'
            elif report.when == 'call' and report.passed:
                case['status'] = 'PASS'


def fingerprint(root):
    """Capture local source/test/fixture inputs, including uncommitted files."""
    paths = [p for directory in ('src', 'tests', 'examples', 'profiles', 'schemas', 'scripts')
             for p in (root / directory).rglob('*') if p.is_file()
             and '__pycache__' not in p.parts and not p.name.endswith('.pyc')]
    paths += [root / 'pyproject.toml', root / 'docs/e7q-ir/REVIEW_CAMPAIGN.json']
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(set(paths)) if p.exists()}


def run(output):
    import pytest
    manifest_path = ROOT / 'docs/e7q-ir/REVIEW_CAMPAIGN.json'
    manifest = json.loads(manifest_path.read_text())
    paths = [entry['test_file'] for entry in manifest['capabilities']]
    if len(paths) != len(set(paths)) or any(
        not p.startswith('tests/test_') or not p.endswith('.py')
        or Path(p).name != p.removeprefix('tests/') or not (ROOT / p).is_file()
        for p in paths
    ):
        raise ValueError('Campaign requires unique existing tests/test_*.py files')
    git = lambda *args: subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()
    revision = git('rev-parse', 'HEAD')
    dirty = git('status', '--porcelain')
    before = fingerprint(ROOT)
    recorder = Recorder()
    capture = io.StringIO()
    old_cwd = Path.cwd()
    # Pin local package import and disable incidental third-party pytest plugins.
    old_plugins = os.environ.get('PYTEST_DISABLE_PLUGIN_AUTOLOAD')
    old_addopts = os.environ.pop('PYTEST_ADDOPTS', None)
    os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
    sys.path.insert(0, str(ROOT / 'src'))
    try:
        os.chdir(ROOT)
        with redirect_stdout(capture), redirect_stderr(capture):
            code = int(pytest.main(['-q', '-o', 'addopts=', *paths], plugins=[recorder]))
    finally:
        os.chdir(old_cwd)
        if old_addopts is not None:
            os.environ['PYTEST_ADDOPTS'] = old_addopts
        if old_plugins is None:
            os.environ.pop('PYTEST_DISABLE_PLUGIN_AUTOLOAD', None)
        else:
            os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = old_plugins
    cases = sorted(recorder.cases.values(), key=lambda c: c['id'])
    missing_files = sorted(set(paths) - {c['id'].split('::')[0] for c in cases})
    changed = before != fingerprint(ROOT) or revision != git('rev-parse', 'HEAD')
    report = {
        'format': 'e7q.local-review-campaign/v1', 'campaign_id': manifest['id'],
        'provenance': 'repository-owned internal test campaign',
        'external_campaign_reproduction': 'NOT_ESTABLISHED',
        'revision': revision, 'working_tree_status_before': dirty, 'inputs_changed_during_run': changed,
        'environment': {'python': sys.version, 'platform': platform.platform(),
                        'packages': {p: importlib.metadata.version(p) for p in ('numpy', 'pytest')},
                        'pytest_plugin_autoload': False},
        'input_sha256': before, 'pytest_exit_code': code,
        'missing_test_files': missing_files,
        'command': [sys.executable, 'scripts/review_campaign.py', '--output', str(output)],
        'status': 'FAIL' if changed or missing_files else verdict(code, cases, recorder.collection_errors),
        'cases': cases, 'collection_errors': recorder.collection_errors,
        'capabilities': [{**entry, 'case_ids': [c['id'] for c in cases if c['id'].split('::')[0] == entry['test_file']]}
                         for entry in manifest['capabilities']],
        'terminal_output': capture.getvalue(),
        'limits': ['Test-case outcomes, not a count of individual Python assertions.',
                   'Seeds, tolerances and generated fixture definitions are in the hashed tests.',
                   'PASS covers only selected tests; it is not F2, F3, F4 or production certification.',
                   'File digests identify local inputs; they do not authenticate this report.'],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(f"{report['status']}: {len(cases)} test cases; report: {output}")
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.is_relative_to(ROOT):
        parser.error('Write reports outside the repository to keep input identity stable')
    raise SystemExit(run(output))
