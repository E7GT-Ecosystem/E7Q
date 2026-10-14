# SPDX-License-Identifier: Apache-2.0
import hashlib
import json
from pathlib import Path

import pytest

from e7q.cli import main
from e7q.entanglement import assess_pure_two_qubit_entanglement
from e7q.language import E7QError, load, parse


ROOT = Path(__file__).parents[1]
BELL = ROOT / "examples" / "bell.e7q"
PRODUCT = ROOT / "examples" / "product-two-qubit.e7q"


def test_bell_state_is_entangled_under_pure_state_criterion():
    source = BELL.read_bytes()
    report = assess_pure_two_qubit_entanglement(
        load(BELL), source_sha256=hashlib.sha256(source).hexdigest()
    )
    assert report["status"] == "ENTANGLED_ESTABLISHED"
    assert report["partition"] == {"left": [0], "right": [1]}
    assert report["evidence"]["reduced_density_purity"] == pytest.approx(0.5)
    assert report["evidence"]["linear_entropy"] == pytest.approx(0.5)
    assert report["evidence"]["sampled_counts_used"] is False
    assert report["program"]["source"]["sha256"] == hashlib.sha256(source).hexdigest()


def test_product_superposition_is_separable():
    report = assess_pure_two_qubit_entanglement(load(PRODUCT))
    assert report["status"] == "SEPARABLE_ESTABLISHED"
    assert report["evidence"]["reduced_density_purity"] == pytest.approx(1.0)
    assert report["evidence"]["linear_entropy"] == pytest.approx(0.0)


def test_assessment_does_not_sample_declared_shots(monkeypatch):
    source = BELL.read_text(encoding="utf-8").replace("shots: 1000", "shots: 1000000")

    def sampling_forbidden(*args, **kwargs):
        raise AssertionError("assessment must not enter the sampling executor")

    monkeypatch.setattr("e7q.language._run_unitary", sampling_forbidden)
    report = assess_pure_two_qubit_entanglement(parse(source))
    assert report["status"] == "ENTANGLED_ESTABLISHED"
    assert report["evidence"]["sampled_counts_used"] is False


@pytest.mark.parametrize(
    "source,reason",
    [
        (
            PRODUCT.read_text(encoding="utf-8").replace(
                "qubits q[2]", "qubits q[3]"
            ).replace("bits c[2]", "bits c[3]").replace(
                "{00, 10}", "{000, 100}"
            ),
            "exactly two qubits",
        ),
        (
            PRODUCT.read_text(encoding="utf-8").replace(
                "backend: statevector", "backend: densitymatrix"
            ),
            "pure state-vector backend",
        ),
        (
            PRODUCT.read_text(encoding="utf-8").replace(
                "H q[0]", "H q[0]\n  measure q[0] -> c[0]"
            ),
            "static unitary path",
        ),
    ],
)
def test_out_of_scope_programs_are_explicitly_unsupported(source, reason):
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    report = assess_pure_two_qubit_entanglement(parse(source), source_sha256=digest)
    assert report["status"] == "UNSUPPORTED"
    assert reason in report["reason"]
    assert report["program"]["source"]["sha256"] == digest


@pytest.mark.parametrize("tolerance", [0, -1, float("inf"), float("nan"), True])
def test_invalid_tolerance_is_rejected(tolerance):
    with pytest.raises(E7QError, match="finite positive"):
        assess_pure_two_qubit_entanglement(load(BELL), tolerance=tolerance)


def test_cli_writes_deterministic_entanglement_report(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    assert main(["assess-entanglement", str(BELL), "-o", str(first)]) == 0
    assert main(["assess-entanglement", str(BELL), "-o", str(second)]) == 0
    assert first.read_bytes() == second.read_bytes()
    assert json.loads(first.read_text(encoding="utf-8"))["status"] == (
        "ENTANGLED_ESTABLISHED"
    )


def test_cli_hashes_the_same_bytes_it_parses(tmp_path, monkeypatch):
    original_read = Path.read_bytes
    source = BELL.read_bytes()
    reads = 0

    def read_once(path):
        nonlocal reads
        if path == BELL:
            reads += 1
            if reads > 1:
                raise AssertionError("source must be read only once")
            return source
        return original_read(path)

    monkeypatch.setattr(Path, "read_bytes", read_once)
    report_path = tmp_path / "report.json"
    assert main(["assess-entanglement", str(BELL), "-o", str(report_path)]) == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert reads == 1
    assert report["program"]["source"]["sha256"] == hashlib.sha256(source).hexdigest()
