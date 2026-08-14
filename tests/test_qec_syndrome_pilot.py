# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from e7q.cli import main
from e7q.language import load, run, verify
from e7q.qec import (
    QECError,
    StabilizerCode,
    analyze_error,
    multiply_paulis,
    qec_proof_json,
    syndrome,
    syndrome_homomorphism_report,
)


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "pilots" / "qec_syndrome" / "expected_results.json"
EXAMPLES = ROOT / "examples" / "qec-syndrome"
CODE = StabilizerCode("three-qubit repetition code", ("ZZI", "IZZ"))


def test_committed_syndromes_and_classifications_match_pilot_fixture():
    data = json.loads(FIXTURE.read_text())
    for case in data["cases"]:
        assert list(syndrome(CODE, case["error"])) == case["syndrome"]
        analysis = analyze_error(CODE, case["error"])
        assert analysis["classification"] == case["classification"]


def test_syndrome_map_adds_modulo_two():
    report = syndrome_homomorphism_report(CODE, "XII", "IXI")
    assert multiply_paulis("XII", "IXI") == "XXI"
    assert report["status"] == "PASS"
    assert report["syndromes"]["left_xor_right"] == [0, 1]
    assert report["syndromes"]["product"] == [0, 1]
    repeated = syndrome_homomorphism_report(CODE, "XII", "IXI")
    assert qec_proof_json(report) == qec_proof_json(repeated)


@pytest.mark.parametrize(
    ("generators", "message"),
    [
        (("ZZ", "XI"), "commute"),
        (("ZZ", "ZZ"), "independent"),
        (("II",), "identity"),
        (("ZA",), "only I, X, Y, and Z"),
    ],
)
def test_generator_validation_fails_closed(generators, message):
    with pytest.raises(QECError, match=message):
        StabilizerCode("invalid", generators)


@pytest.mark.parametrize(
    "filename",
    [
        "no-error.e7q",
        "xii.e7q",
        "ixi.e7q",
        "xxi.e7q",
        "zzi-stabilizer.e7q",
        "xxx-logical.e7q",
    ],
)
def test_reference_syndrome_circuits_pass(filename):
    result = verify(run(load(EXAMPLES / filename)))
    assert result["status"] == "PASS"
    assert sum(result["counts"].values()) == 64
    assert sum(step["kind"] == "project" for step in result["proof"]) == 5
    assert all(
        step["passed"]
        for step in result["proof"]
        if step["kind"] == "assert"
    )


def test_dependency_free_reference_checker_agrees():
    checker = ROOT / "pilots" / "qec_syndrome" / "reference_checker.py"
    completed = subprocess.run(
        [sys.executable, str(checker)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert completed.stdout.startswith("PASS")


def test_qec_homomorphism_cli_writes_auditable_report(tmp_path):
    output = tmp_path / "homomorphism.json"
    status = main([
        "qec-homomorphism", "XII", "IXI",
        "--generator", "ZZI", "--generator", "IZZ",
        "--name", "three-qubit repetition code", "-o", str(output),
    ])
    report = json.loads(output.read_text())
    assert status == 0
    assert report["status"] == "PASS"
    assert report["operators"]["product"] == "XXI"
