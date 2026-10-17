# SPDX-License-Identifier: Apache-2.0
import json
from pathlib import Path
import re
import shutil
from zipfile import ZipFile

import pytest

from e7q.artifacts import validate_artifact
from e7q.cli import main
from e7q.external_bundles import SCHEMA, _DIRECTORY_FD_SUPPORTED, verify_external_bundle
from e7q.language import E7QError
from e7q.temporal import conformance_checks as temporal_checks


EXAMPLE = Path("examples/external-evidence-synthetic")
RECORD = EXAMPLE / "synthetic_bell"


def test_synthetic_directory_passes_with_bounded_judgments():
    result = verify_external_bundle(EXAMPLE)
    assert result["schema"] == SCHEMA
    assert result["status"] == "PASS"
    assert result["conformance"] == "INTERNALLY_CONSISTENT_WITH_LIMITATIONS"
    assert result["records"] == 1
    assert result["judgments"]["archive_safety"]["status"] == "PASS"
    assert result["judgments"]["artifact_integrity"]["status"] == "PASS"
    assert result["judgments"]["internal_consistency"]["status"] == "PASS"
    assert result["judgments"]["external_provenance"]["status"] == "PARTIAL"
    assert result["judgments"]["reproducibility"]["status"] == "PARTIAL"
    assert (
        result["judgments"]["algorithmic_claim_validation"]["status"]
        == "NOT_EVALUATED"
    )
    assert "values" not in result["circuits"][0]["counts"]
    assert all(check["passed"] for check in temporal_checks(result["temporal_evidence"]))


def test_counts_are_embedded_only_when_requested():
    result = verify_external_bundle(EXAMPLE, include_counts=True)
    assert result["circuits"][0]["counts"]["values"] == {"00": 510, "11": 490}


def test_zip_and_multi_record_shapes_are_discovered(tmp_path):
    package = tmp_path / "package"
    shutil.copytree(RECORD, package / "first")
    shutil.copytree(RECORD, package / "second")
    archive = tmp_path / "package.zip"
    with ZipFile(archive, "w") as output:
        for path in sorted(package.rglob("*")):
            if path.is_file():
                output.write(path, path.relative_to(package))
    result = verify_external_bundle(archive)
    assert result["status"] == "PASS"
    assert result["source"]["kind"] == "zip"
    assert result["records"] == 2
    assert len(result["jobs"]) == 1
    assert result["jobs"][0]["records"] == 2
    assert result["jobs"][0]["shared_mapping"] is True


def test_abbreviated_manifest_is_partial_not_failed(tmp_path):
    package = tmp_path / "fixture"
    shutil.copytree(EXAMPLE, package)
    manifest = package / "synthetic_bell" / "MANIFEST.md"
    content = manifest.read_text(encoding="utf-8")
    content = re.sub(r"`([0-9a-f]{16})[0-9a-f]{48}`", r"`\1…`", content)
    manifest.write_text(content, encoding="utf-8")
    result = verify_external_bundle(package)
    assert result["status"] == "PASS"
    assert result["judgments"]["artifact_integrity"]["status"] == "PARTIAL"
    assert "manifest-full-sha256" in result["circuits"][0]["warnings"]


def test_tampered_counts_fail_integrity_and_consistency(tmp_path):
    package = tmp_path / "fixture"
    shutil.copytree(EXAMPLE, package)
    counts_path = package / "synthetic_bell" / "raw_counts.json"
    counts = json.loads(counts_path.read_text(encoding="utf-8"))
    counts["counts"]["00"] = 509
    counts_path.write_text(json.dumps(counts), encoding="utf-8")
    result = verify_external_bundle(package)
    assert result["status"] == "FAIL"
    assert result["judgments"]["artifact_integrity"]["status"] == "FAIL"
    assert result["judgments"]["internal_consistency"]["status"] == "FAIL"


def test_archive_traversal_is_rejected_before_ingestion(tmp_path):
    archive = tmp_path / "unsafe.zip"
    with ZipFile(archive, "w") as output:
        output.writestr("../job_metadata.json", "{}")
    with pytest.raises(E7QError, match="unsafe member"):
        verify_external_bundle(archive)


def test_cli_and_registered_artifact_schema(tmp_path):
    output = tmp_path / "receipt.json"
    assert main([
        "external-bundle", "verify", str(EXAMPLE), "-o", str(output)
    ]) == 0
    receipt = json.loads(output.read_text(encoding="utf-8"))
    report = validate_artifact(receipt)
    assert report["status"] == "PASS"
    assert report["artifact_schema"] == SCHEMA


@pytest.mark.parametrize('payload', [
    b'{"counts":{"00":1,"00":2}}',
    b'{"value":NaN}', b'{"value":Infinity}', b'{"value":-Infinity}',
    b'{"value":1e999}', b'{"nested":{"key":1,"key":2}}',
])
def test_ambiguous_or_nonfinite_json_is_rejected(payload):
    from e7q.external_bundles import _json_object
    checks = []
    assert _json_object({'raw_counts.json': payload}, '', 'raw_counts.json', checks) is None
    assert checks[-1]['passed'] is False


def test_archive_input_budget_precedes_read(tmp_path, monkeypatch):
    import e7q.external_bundles as bundles
    archive = tmp_path / 'large.zip'
    with ZipFile(archive, 'w') as output:
        output.writestr('job_metadata.json', '{}')
    monkeypatch.setattr(bundles, '_MAX_ARCHIVE_BYTES', 10, raising=False)
    with pytest.raises(E7QError, match='archive.*size limit'):
        verify_external_bundle(archive)


@pytest.mark.parametrize('name', ['/absolute.json', 'a/../b.json', 'a/./b.json', 'a//b.json', 'C:/file.json', 'a\\b.json'])
def test_noncanonical_member_paths_rejected(tmp_path, name):
    archive = tmp_path / 'unsafe.zip'
    with ZipFile(archive, 'w') as output:
        output.writestr(name, '{}')
    with pytest.raises(E7QError, match='unsafe member'):
        verify_external_bundle(archive)


def test_duplicate_directory_entries_are_rejected(tmp_path):
    archive = tmp_path / 'duplicate.zip'
    with ZipFile(archive, 'w') as output:
        output.writestr('record/', '')
        with pytest.warns(UserWarning):
            output.writestr('record/', '')
    with pytest.raises(E7QError, match='duplicate member'):
        verify_external_bundle(archive)


def test_zip_symlink_is_rejected(tmp_path):
    from zipfile import ZipInfo
    import stat
    archive = tmp_path / 'symlink.zip'
    entry = ZipInfo('link')
    entry.create_system = 3
    entry.external_attr = (stat.S_IFLNK | 0o777) << 16
    with ZipFile(archive, 'w') as output:
        output.writestr(entry, '../outside')
    with pytest.raises(E7QError, match='symlink'):
        verify_external_bundle(archive)


@pytest.mark.parametrize('payload', [b'{"counts":{"00":510,"00":510,"11":490},"total_shots":1000,"num_unique_bitstrings":2}', b'{"value":NaN}'])
def test_rehashed_manifest_does_not_hide_invalid_json(tmp_path, payload):
    from hashlib import sha256
    package = tmp_path / 'fixture'
    shutil.copytree(EXAMPLE, package)
    target = package / 'synthetic_bell/raw_counts.json'
    original = sha256(target.read_bytes()).hexdigest()
    target.write_bytes(payload)
    manifest = package / 'synthetic_bell/MANIFEST.md'
    manifest.write_text(manifest.read_text().replace(original, sha256(payload).hexdigest()))
    result = verify_external_bundle(package)
    assert result['judgments']['artifact_integrity']['status'] == 'PASS'
    assert result['judgments']['internal_consistency']['status'] == 'FAIL'
    assert result['status'] == 'FAIL'


@pytest.mark.parametrize('limit,value,message', [('_MAX_FILES', 1, 'members'), ('_MAX_FILE_BYTES', 1, 'too large'), ('_MAX_TOTAL_BYTES', 3, 'expands')])
def test_zip_resource_limits(tmp_path, monkeypatch, limit, value, message):
    import e7q.external_bundles as bundles
    archive = tmp_path / 'budget.zip'
    with ZipFile(archive, 'w') as output:
        output.writestr('one', '{}')
        output.writestr('two', '{}')
    monkeypatch.setattr(bundles, limit, value)
    with pytest.raises(E7QError, match=message):
        verify_external_bundle(archive)


@pytest.mark.parametrize('filename,field,value', [
    ('job_metadata.json', 'status', []),
    ('job_metadata.json', 'status', {}),
    ('job_metadata.json', 'circuit_name', []),
    ('job_metadata.json', 'circuit_depth', True),
    ('job_metadata.json', 'creation_date', {}),
    ('job_metadata.json', 'completion_time_utc', {}),
    ('job_metadata.json', 'completed_at', '2026-08-25T13:02:00+00:00'),
    ('job_metadata.json', 'num_qubits_device', 2.0),
    ('job_metadata.json', 'op_counts', {'h': True, 'cx': 1, 'measure': 2}),
    ('job_metadata.json', 'op_counts', {'h': 1.0, 'cx': 1, 'measure': 2}),
    ('job_metadata.json', 'op_counts', {'h': 99, 'H': 1, 'cx': 1, 'measure': 2}),
    ('raw_counts.json', 'total_shots', 1000.0),
    ('raw_counts.json', 'num_unique_bitstrings', 2.0),
    ('mapping.json', 'num_clbits', 2.0),
    ('mapping.json', 'num_active_qubits', 2.0),
    ('mapping.json', 'initial_index_layout', [0, 0]),
    ('mapping.json', 'final_index_layout', [0, -1]),
    ('hieroglyphs_ir.json', 'num_gates', float(len(json.loads((RECORD / 'hieroglyphs_ir.json').read_text())['gates']))),
])
def test_rehashed_malformed_fields_fail_consistency(tmp_path, filename, field, value):
    from hashlib import sha256
    package = tmp_path / 'fixture'
    shutil.copytree(EXAMPLE, package)
    target = package / 'synthetic_bell' / filename
    original = sha256(target.read_bytes()).hexdigest()
    payload = json.loads(target.read_bytes())
    payload[field] = value
    target.write_text(json.dumps(payload))
    manifest = package / 'synthetic_bell/MANIFEST.md'
    manifest.write_text(manifest.read_text().replace(original, sha256(target.read_bytes()).hexdigest()))
    result = verify_external_bundle(package)
    assert result['judgments']['artifact_integrity']['status'] == 'PASS'
    assert result['judgments']['internal_consistency']['status'] == 'FAIL'
    assert result['status'] == 'FAIL'
    assert result == verify_external_bundle(package)


def test_directory_entry_budget_counts_empty_directories(tmp_path, monkeypatch):
    import e7q.external_bundles as bundles
    for name in ('a', 'b', 'c'):
        (tmp_path / name).mkdir()
    monkeypatch.setattr(bundles, '_MAX_DIRECTORY_ENTRIES', 2, raising=False)
    with pytest.raises(E7QError, match='directory entry limit'):
        verify_external_bundle(tmp_path)


def test_directory_depth_is_bounded(tmp_path, monkeypatch):
    import e7q.external_bundles as bundles
    (tmp_path / 'a/b/c').mkdir(parents=True)
    monkeypatch.setattr(bundles, '_MAX_DIRECTORY_DEPTH', 2, raising=False)
    with pytest.raises(E7QError, match='directory depth limit'):
        verify_external_bundle(tmp_path)


def test_special_directory_member_rejected_without_opening(tmp_path):
    import os
    if not hasattr(os, 'mkfifo'):
        pytest.skip('FIFO creation unavailable')
    os.mkfifo(tmp_path / 'pipe')
    with pytest.raises(E7QError, match='non-regular'):
        verify_external_bundle(tmp_path)


@pytest.mark.parametrize('limit,value', [('_MAX_FILE_BYTES', 1), ('_MAX_TOTAL_BYTES', 3), ('_MAX_FILES', 1)])
def test_directory_member_budgets(tmp_path, monkeypatch, limit, value):
    import e7q.external_bundles as bundles
    (tmp_path / 'a').write_bytes(b'{}')
    (tmp_path / 'b').write_bytes(b'{}')
    monkeypatch.setattr(bundles, limit, value)
    with pytest.raises(E7QError, match='large|safety limits'):
        verify_external_bundle(tmp_path)


def test_directory_growth_cannot_bypass_read_budget(tmp_path, monkeypatch):
    import e7q.external_bundles as bundles
    target = tmp_path / 'growing'
    target.write_bytes(b'x')
    real_fdopen = bundles.os.fdopen
    reads = []

    class GrowingStream:
        def __init__(self, stream):
            self.stream = stream
        def __enter__(self):
            return self
        def __exit__(self, *args):
            self.stream.close()
        def fileno(self):
            return self.stream.fileno()
        def read(self, size):
            reads.append(size)
            target.write_bytes(b'x' * 20)
            return self.stream.read(size)

    monkeypatch.setattr(bundles, '_MAX_FILE_BYTES', 4)
    monkeypatch.setattr(bundles.os, 'fdopen', lambda *args, **kwargs: GrowingStream(real_fdopen(*args, **kwargs)))
    with pytest.raises(E7QError, match='too large'):
        bundles._load_directory(tmp_path)
    assert reads == [5]


@pytest.mark.parametrize('order', ['clbit-ascending', 'clbit-descending', 'unknown', [], None])
def test_bundle_preserves_or_rejects_declared_count_order(tmp_path, order):
    from hashlib import sha256
    package = tmp_path / 'fixture'
    shutil.copytree(EXAMPLE, package)
    target = package / 'synthetic_bell/raw_counts.json'
    original = sha256(target.read_bytes()).hexdigest()
    payload = json.loads(target.read_bytes())
    payload['label_order'] = order
    target.write_text(json.dumps(payload))
    manifest = package / 'synthetic_bell/MANIFEST.md'
    manifest.write_text(manifest.read_text().replace(original, sha256(target.read_bytes()).hexdigest()))
    receipt = verify_external_bundle(package, include_counts=True)
    valid = isinstance(order, str) and order in {'clbit-ascending', 'clbit-descending'}
    assert receipt['status'] == ('PASS' if valid else 'FAIL')
    if valid:
        assert receipt['circuits'][0]['counts']['label_order'] == order
        assert receipt['circuits'][0]['counts']['values'] == payload['counts']


def test_missing_count_order_is_explicitly_unknown():
    receipt = verify_external_bundle(EXAMPLE)
    assert receipt['status'] == 'PASS'
    assert receipt['circuits'][0]['counts']['label_order'] is None
    assert 'counts:label-order-declared' in receipt['circuits'][0]['warnings']


@pytest.mark.parametrize('kind', ['directory', 'zip'])
@pytest.mark.parametrize('qasm_register,declaration,expected', [
    pytest.param('c', {'classical_register': 'other'}, 'FAIL', id='contradictory-name'),
    pytest.param('c', {'classical_register': 'C'}, 'FAIL', id='case-mismatch'),
    pytest.param('c', {'classical_register': ''}, 'FAIL', id='empty-name'),
    pytest.param('c', {'classical_register': None}, 'FAIL', id='null-name'),
    pytest.param('c', {'classical_register': 0}, 'FAIL', id='integer-name'),
    pytest.param('c', {'classical_register': False}, 'FAIL', id='boolean-name'),
    pytest.param('c', {'classical_register': ['c']}, 'FAIL', id='list-name'),
    pytest.param('c', {'classical_register': {'name': 'c'}}, 'FAIL', id='object-name'),
    pytest.param('c', {'classical_register': 'c'}, 'PASS', id='matching-name'),
    pytest.param('c', {}, 'PASS', id='undeclared-name'),
    pytest.param('readout', {'classical_register': 'readout'}, 'PASS', id='renamed-register'),
])
def test_rehashed_counts_register_matches_qasm(tmp_path, kind, qasm_register, declaration, expected):
    from hashlib import sha256
    package = tmp_path / 'fixture'
    shutil.copytree(EXAMPLE, package)
    record = package / 'synthetic_bell'
    counts = json.loads((record / 'raw_counts.json').read_bytes())
    counts.pop('classical_register')
    counts.update(declaration)
    qasm = (record / 'final_circuit.qasm').read_text().replace('c[', f'{qasm_register}[')
    for filename, content in [('raw_counts.json', json.dumps(counts)), ('final_circuit.qasm', qasm)]:
        (record / filename).write_text(content)
    manifest = record / 'MANIFEST.md'
    manifest.write_text('| File | Purpose | SHA256 |\n| --- | --- | --- |\n' + ''.join(
        f'| `{path.name}` | Synthetic test member | `{sha256(path.read_bytes()).hexdigest()}` |\n'
        for path in sorted(record.iterdir()) if path.is_file() and path != manifest
    ))
    source = package
    if kind == 'zip':
        source = tmp_path / 'fixture.zip'
        with ZipFile(source, 'w') as archive:
            for path in sorted(package.rglob('*')):
                if path.is_file():
                    archive.write(path, path.relative_to(package))
    receipt = verify_external_bundle(source, include_counts=True)
    assert receipt['judgments']['artifact_integrity']['status'] == 'PASS'
    assert receipt['judgments']['internal_consistency']['status'] == expected
    assert receipt['status'] == expected
    assert receipt['judgments']['external_provenance']['status'] == 'PARTIAL'
    assert receipt['judgments']['algorithmic_claim_validation']['status'] == 'NOT_EVALUATED'
    if expected == 'FAIL':
        checks = {check['name']: check for check in receipt['circuits'][0]['checks']}
        assert checks['qasm:declared-registers']['passed'] is False
        assert checks['counts:sum-to-shots']['passed'] is True
        assert checks['mapping:qasm-measurements']['passed'] is True
    assert receipt == verify_external_bundle(source, include_counts=True)


# Synthetic races run synchronously at the admission/open boundary, not by timing.
def _replace_after_entry_stat(monkeypatch, victim, replace):
    import e7q.external_bundles as bundles
    real_scandir = bundles.os.scandir
    fired = []

    class Entry:
        def __init__(self, entry):
            self.entry = entry
        def __getattr__(self, name):
            return getattr(self.entry, name)
        def stat(self, **kwargs):
            info = self.entry.stat(**kwargs)
            if self.entry.name == victim.name and not fired:
                fired.append(True)
                replace()
            return info

    class Scan:
        def __init__(self, directory):
            self.scan = real_scandir(directory)
        def __enter__(self):
            self.scan.__enter__()
            return (Entry(entry) for entry in self.scan)
        def __exit__(self, *args):
            return self.scan.__exit__(*args)

    monkeypatch.setattr(bundles.os, 'scandir', Scan)
    return fired


@pytest.mark.skipif(not _DIRECTORY_FD_SUPPORTED, reason='POSIX directory descriptors unavailable')
@pytest.mark.parametrize('replacement', ['symlink', 'directory'])
def test_directory_replacement_after_admission_is_rejected(tmp_path, monkeypatch, replacement):
    import e7q.external_bundles as bundles
    root = tmp_path / 'bundle'
    victim = root / 'record'
    victim.mkdir(parents=True)
    (victim / 'data').write_bytes(b'admitted')
    outside = tmp_path / 'outside'
    outside.mkdir()
    (outside / 'data').write_bytes(b'replacement')

    def replace():
        victim.rename(tmp_path / 'moved')
        if replacement == 'symlink':
            victim.symlink_to(outside, target_is_directory=True)
        else:
            outside.rename(victim)

    fired = _replace_after_entry_stat(monkeypatch, victim, replace)
    with pytest.raises(E7QError, match='changed|cannot inspect|symlink'):
        bundles._load_directory(root)
    assert fired == [True]


@pytest.mark.skipif(not _DIRECTORY_FD_SUPPORTED, reason='POSIX directory descriptors unavailable')
@pytest.mark.parametrize('ancestor', ['root', 'child'])
def test_anchored_ancestor_move_cannot_redirect_file_open(tmp_path, monkeypatch, ancestor):
    import os
    import e7q.external_bundles as bundles
    root = tmp_path / 'bundle'
    child = root / 'record'
    child.mkdir(parents=True)
    (child / 'data').write_bytes(b'admitted')
    target = root if ancestor == 'root' else child
    identity = target.stat().st_ino
    real_scandir = bundles.os.scandir
    fired = []

    def scan(directory):
        info = os.fstat(directory) if isinstance(directory, int) else Path(directory).stat()
        if info.st_ino == identity and not fired:
            fired.append(True)
            target.rename(tmp_path / 'moved')
            child.mkdir(parents=True)
            (child / 'data').write_bytes(b'replacement')
        return real_scandir(directory)

    monkeypatch.setattr(bundles.os, 'scandir', scan)
    source = bundles._load_directory(root)
    assert fired == [True]
    assert source.members == {'record/data': b'admitted'}


@pytest.mark.skipif(not _DIRECTORY_FD_SUPPORTED, reason='POSIX directory descriptors unavailable')
@pytest.mark.parametrize('replacement', ['symlink', 'directory'])
def test_root_replacement_between_stat_and_open_is_rejected(tmp_path, monkeypatch, replacement):
    import e7q.external_bundles as bundles
    root = tmp_path / 'bundle'
    root.mkdir()
    (root / 'data').write_bytes(b'admitted')
    outside = tmp_path / 'outside'
    outside.mkdir()
    (outside / 'data').write_bytes(b'replacement')
    real_lstat = Path.lstat
    fired = []

    def lstat(path, *args, **kwargs):
        info = real_lstat(path, *args, **kwargs)
        if path == root and not fired:
            fired.append(True)
            root.rename(tmp_path / 'moved')
            if replacement == 'symlink':
                root.symlink_to(outside, target_is_directory=True)
            else:
                outside.rename(root)
        return info

    monkeypatch.setattr(Path, 'lstat', lstat)
    with pytest.raises(E7QError, match='changed|cannot inspect|symlink'):
        bundles._load_directory(root)
    assert fired == [True]


@pytest.mark.skipif(not _DIRECTORY_FD_SUPPORTED, reason='POSIX directory descriptors unavailable')
@pytest.mark.parametrize('replacement', ['file', 'symlink', 'directory'])
def test_file_replacement_after_admission_is_rejected(tmp_path, monkeypatch, replacement):
    import e7q.external_bundles as bundles
    target = tmp_path / 'data'
    target.write_bytes(b'admitted')

    def replace():
        target.rename(tmp_path / 'saved')
        if replacement == 'file':
            target.write_bytes(b'replacement')
        elif replacement == 'directory':
            target.mkdir()
        else:
            target.symlink_to(tmp_path / 'saved')

    fired = _replace_after_entry_stat(monkeypatch, target, replace)
    with pytest.raises(E7QError, match='changed|cannot inspect'):
        bundles._load_directory(tmp_path)
    assert fired == [True]


@pytest.mark.parametrize('anchored', [False, True])
def test_directory_canonical_and_receipt_identity_retained(monkeypatch, anchored):
    from hashlib import sha256
    import e7q.external_bundles as bundles
    if anchored and not _DIRECTORY_FD_SUPPORTED:
        pytest.skip('POSIX directory descriptors unavailable')
    monkeypatch.setattr(bundles, '_DIRECTORY_FD_SUPPORTED', anchored)
    receipt = verify_external_bundle(EXAMPLE)
    # Frozen from unmodified e3b6687, including the entire deterministic receipt.
    assert receipt['source']['digest'] == 'sha256:69811dece0bcc4c247d3c6044b5217fbf651af3b1b08a7162ae7da48b9916208'
    canonical = json.dumps(receipt, sort_keys=True, separators=(',', ':')).encode()
    assert sha256(canonical).hexdigest() == 'ac6228cc052e98c2b65eff493ef5be7296f174ea85b67347fe387593715b79e6'


def test_directory_compatibility_fallback_uses_paths(tmp_path, monkeypatch):
    import e7q.external_bundles as bundles
    root = tmp_path / 'bundle'
    (root / 'record').mkdir(parents=True)
    (root / 'record/data').write_bytes(b'admitted')
    real_open, real_scandir = bundles.os.open, bundles.os.scandir
    opens, scans = [], []

    def open_path(path, flags, *args, **kwargs):
        assert not isinstance(path, int)
        assert 'dir_fd' not in kwargs
        opens.append(path)
        return real_open(path, flags, *args, **kwargs)

    def scan_path(path):
        assert isinstance(path, Path)
        scans.append(path)
        return real_scandir(path)

    monkeypatch.setattr(bundles, '_DIRECTORY_FD_SUPPORTED', False)
    monkeypatch.setattr(bundles.os, 'open', open_path)
    monkeypatch.setattr(bundles.os, 'scandir', scan_path)
    assert bundles._load_directory(root).members == {'record/data': b'admitted'}
    assert len(opens) == 1 and len(scans) == 2
    monkeypatch.setattr(bundles, '_MAX_DIRECTORY_ENTRIES', 1)
    with pytest.raises(E7QError, match='entry limit'):
        bundles._load_directory(root)


@pytest.mark.skipif(not _DIRECTORY_FD_SUPPORTED, reason='POSIX directory descriptors unavailable')
@pytest.mark.parametrize('failure', [None, 'entry-limit', 'open', 'fstat', 'fdopen', 'read', 'mutation'])
def test_directory_descriptors_are_bounded_and_closed(tmp_path, monkeypatch, failure):
    import os
    import e7q.external_bundles as bundles
    root = tmp_path / 'bundle'
    leaf = root.joinpath(*['nested'] * 6)
    leaf.mkdir(parents=True)
    target = leaf / 'data'
    target.write_bytes(b'admitted')
    real_open, real_close = bundles.os.open, bundles.os.close
    real_fdopen, real_fstat = bundles.os.fdopen, bundles.os.fstat
    live, opened = set(), []
    peak = 0
    before = len(os.listdir('/proc/self/fd')) if Path('/proc/self/fd').is_dir() else None

    def open_tracked(path, flags, *args, **kwargs):
        nonlocal peak
        if failure == 'open' and path == 'data':
            raise OSError('injected open failure')
        descriptor = real_open(path, flags, *args, **kwargs)
        live.add(descriptor)
        opened.append(descriptor)
        peak = max(peak, len(live))
        return descriptor

    def close_tracked(descriptor):
        live.remove(descriptor)
        return real_close(descriptor)

    def fstat_injected(descriptor):
        if failure == 'fstat':
            raise OSError('injected fstat failure')
        return real_fstat(descriptor)

    class Stream:
        def __init__(self, stream):
            self.stream = stream
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return self.stream.__exit__(*args)
        def read(self, size):
            if failure == 'read':
                raise OSError('injected read failure')
            content = self.stream.read(size)
            if failure == 'mutation':
                target.write_bytes(b'changed-size')
            return content

    def fdopen_injected(*args, **kwargs):
        if failure == 'fdopen':
            raise OSError('injected fdopen failure')
        return Stream(real_fdopen(*args, **kwargs))

    monkeypatch.setattr(bundles.os, 'open', open_tracked)
    monkeypatch.setattr(bundles.os, 'close', close_tracked)
    monkeypatch.setattr(bundles.os, 'fstat', fstat_injected)
    monkeypatch.setattr(bundles.os, 'fdopen', fdopen_injected)
    if failure == 'entry-limit':
        monkeypatch.setattr(bundles, '_MAX_DIRECTORY_ENTRIES', 3)
    if failure is None:
        assert bundles._load_directory(root).members == {'nested/' * 6 + 'data': b'admitted'}
    else:
        with pytest.raises(E7QError, match='cannot inspect|entry limit|changed'):
            bundles._load_directory(root)
    assert opened and not live
    assert peak <= 8  # seven directory anchors plus one file, independent of width
    for descriptor in set(opened):
        with pytest.raises(OSError):
            real_fstat(descriptor)
    if before is not None:
        assert len(os.listdir('/proc/self/fd')) == before  # includes scandir handles


@pytest.mark.skipif(not _DIRECTORY_FD_SUPPORTED, reason='POSIX directory descriptors unavailable')
@pytest.mark.parametrize('ancestor', ['root', 'child'])
def test_admitted_file_opens_from_anchor_after_ancestor_move(tmp_path, monkeypatch, ancestor):
    import e7q.external_bundles as bundles
    root = tmp_path / 'bundle'
    child = root / 'record'
    child.mkdir(parents=True)
    target = child / 'data'
    target.write_bytes(b'admitted')
    moved = root if ancestor == 'root' else child

    def replace():
        moved.rename(tmp_path / 'moved')
        child.mkdir(parents=True)
        target.write_bytes(b'replacement')

    fired = _replace_after_entry_stat(monkeypatch, target, replace)
    assert bundles._load_directory(root).members == {'record/data': b'admitted'}
    assert fired == [True]
