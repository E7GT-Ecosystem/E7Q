# SPDX-License-Identifier: Apache-2.0
import json
from pathlib import Path
import re
import shutil
from zipfile import ZipFile

import pytest

from e7q.artifacts import validate_artifact
from e7q.cli import main
from e7q.external_bundles import SCHEMA, verify_external_bundle
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
    ('job_metadata.json', 'num_qubits_device', 2.0),
    ('job_metadata.json', 'op_counts', {'h': True, 'cx': 1, 'measure': 2}),
    ('job_metadata.json', 'op_counts', {'h': 1.0, 'cx': 1, 'measure': 2}),
    ('job_metadata.json', 'op_counts', {'h': 99, 'H': 1, 'cx': 1, 'measure': 2}),
    ('raw_counts.json', 'total_shots', 1000.0),
    ('raw_counts.json', 'num_unique_bitstrings', 2.0),
    ('mapping.json', 'num_clbits', 2.0),
    ('mapping.json', 'num_active_qubits', 2.0),
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
