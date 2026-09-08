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
    report = assess_pure_two_qubit_entanglement(parse(source))
    assert report["status"] == "UNSUPPORTED"
    assert reason in report["reason"]


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
