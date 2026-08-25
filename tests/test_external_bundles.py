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
