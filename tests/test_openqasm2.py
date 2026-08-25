# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
from pathlib import Path

import pytest

from e7q.artifacts import validate_artifact
from e7q.cli import main
from e7q.language import E7QError
from e7q.openqasm2 import canonicalize_outcome, import_openqasm2


ROOT = Path(__file__).parents[1]
SYNTHETIC = (
    ROOT / "examples" / "external-evidence-synthetic" /
    "synthetic_bell" / "final_circuit.qasm"
)


def test_imports_synthetic_openqasm2_as_typed_non_executable_artifact():
    artifact = import_openqasm2(SYNTHETIC.read_text(), name="synthetic_bell")
    assert artifact["status"] == "PASS"
    assert artifact["operation_counts"] == {"cx": 1, "h": 1, "measure": 2}
    assert artifact["measurements"][0] == {
        "qubit": {"register": "q", "index": 0},
        "clbit": {"register": "c", "index": 0},
    }
    assert artifact["outcome_conventions"]["qiskit_counts"] == "clbit-descending"
    assert validate_artifact(artifact)["status"] == "PASS"


def test_imports_native_parameterized_isa_surface_without_allocating_statevector():
    source = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[156];
creg c[2];
rz(pi/2) q[42];
sx q[42];
cz q[42],q[43];
measure q[42] -> c[0];
measure q[43] -> c[1];
"""
    artifact = import_openqasm2(source)
    assert artifact["registers"]["quantum"] == [{"name": "q", "width": 156}]
    assert artifact["operation_counts"] == {
        "cz": 1, "measure": 2, "rz": 1, "sx": 1,
    }
    assert artifact["operations"][0]["parameters"] == ["pi/2"]
    assert artifact["active_qubits"] == [
        {"register": "q", "index": 42},
        {"register": "q", "index": 43},
    ]


def test_import_preserves_barrier_condition_and_whole_register_measurement():
    source = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
barrier q;
if(c==1) x q[0];
measure q -> c;
"""
    artifact = import_openqasm2(source)
    assert artifact["operations"][0]["name"] == "barrier"
    assert artifact["operations"][1]["condition"] == {
        "register": "c", "equals": 1,
    }
    assert len(artifact["measurements"]) == 2


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("OPENQASM 3.0; qreg q[1]; creg c[1]; measure q[0] -> c[0];", "2.0"),
        ("OPENQASM 2.0; qreg q[1]; creg c[1]; mystery q[0]; measure q[0] -> c[0];", "unsupported"),
        ("OPENQASM 2.0; qreg q[1]; creg c[1]; x q[1]; measure q[0] -> c[0];", "out of range"),
    ],
)
def test_import_fails_closed(source, message):
    with pytest.raises(E7QError, match=message):
        import_openqasm2(source)


def test_count_label_normalization_is_explicit():
    assert canonicalize_outcome("00101", order="clbit-descending") == "10100"
    assert canonicalize_outcome("10100", order="clbit-ascending") == "10100"
    with pytest.raises(E7QError, match="order"):
        canonicalize_outcome("00101", order="implicit")


def test_openqasm2_cli_writes_registered_artifact(tmp_path):
    output = tmp_path / "import.json"
    status = main(["import-openqasm2", str(SYNTHETIC), "-o", str(output)])
    artifact = json.loads(output.read_text())
    assert status == 0
    assert artifact["schema"] == "e7q.openqasm2-circuit/v1alpha1"
    assert validate_artifact(artifact)["status"] == "PASS"
