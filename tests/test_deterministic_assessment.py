# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from e7q.artifacts import validate_artifact
from e7q.cli import main
from e7q.deterministic import assess_deterministic_reference
from e7q.language import E7QError


ROOT = Path(__file__).parents[1]
REFERENCE = ROOT / "pilots" / "qec_syndrome" / "hardware_reference.json"


def _fixture():
    reference = json.loads(REFERENCE.read_text())
    circuits = []
    for case in reference["cases"]:
        expected = case["expected_outcome"]
        alternative = str(1 - int(expected[0])) + expected[1:]
        circuits.append({
            "circuit_name": case["circuit_name"],
            "counts": {
                "shots": 100,
                "values": {expected[::-1]: 80, alternative[::-1]: 20},
            },
        })
    receipt = {
        "schema": "e7q.external-evidence-receipt/v1alpha1",
        "status": "PASS",
        "source": {"kind": "synthetic", "digest": "sha256:fixture"},
        "circuits": circuits,
    }
    return receipt, reference


def test_deterministic_assessment_normalizes_qiskit_order_and_checks_relations():
    receipt, reference = _fixture()
    assert validate_artifact(reference)["status"] == "PASS"
    report = assess_deterministic_reference(receipt, reference)
    assert report["status"] == "PASS"
    assert report["claim_mode"] == "exploratory"
    x0 = next(case for case in report["cases"] if case["circuit_name"] == "x0")
    assert x0["expected_outcome"] == "10100"
    assert x0["expected_primary"] == "10"
    assert x0["primary"]["observed_probability"] == 0.8
    assert x0["primary"]["wilson_interval"][0] > 0.5
    assert report["relations"][0]["observed"]["left_xor_right"] == "01"
    assert validate_artifact(report)["status"] == "PASS"


def test_deterministic_assessment_fails_when_confidence_bound_misses_threshold():
    receipt, reference = _fixture()
    expected = reference["cases"][0]["expected_outcome"]
    alternative = str(1 - int(expected[0])) + expected[1:]
    receipt["circuits"][0]["counts"]["values"] = {
        expected[::-1]: 50,
        alternative[::-1]: 50,
    }
    report = assess_deterministic_reference(receipt, reference)
    assert report["status"] == "FAIL"
    assert report["cases"][0]["primary"]["status"] == "FAIL"


def test_deterministic_assessment_requires_embedded_counts():
    receipt, reference = _fixture()
    del receipt["circuits"][0]["counts"]["values"]
    with pytest.raises(E7QError, match="--include-counts"):
        assess_deterministic_reference(receipt, reference)


def test_deterministic_assessment_rejects_implicit_bit_order():
    receipt, reference = _fixture()
    reference = copy.deepcopy(reference)
    reference["observed_label_order"] = "qiskit-default"
    with pytest.raises(E7QError, match="observed_label_order"):
        assess_deterministic_reference(receipt, reference)


def test_deterministic_assessment_cli(tmp_path):
    receipt, _ = _fixture()
    receipt_path = tmp_path / "receipt.json"
    output = tmp_path / "assessment.json"
    receipt_path.write_text(json.dumps(receipt))
    status = main([
        "assess-deterministic", str(receipt_path),
        "--reference", str(REFERENCE), "-o", str(output),
    ])
    report = json.loads(output.read_text())
    assert status == 0
    assert report["schema"] == "e7q.deterministic-assessment/v1alpha1"
