# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
import multiprocessing
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from e7q.ir.conformance import validate_graph
from e7q.ir.qcec import FIDELITY_THRESHOLD, NUMERICAL_TOLERANCE
from e7q.ir.native_qcec_workflow import (
    build_native_external_qcec_graph,
    recover_native_external_source,
)
from e7q.ir.unitary import CRITERION
from e7q.language import E7QError

STAMP = "2026-09-08T00:00:00Z"
UNITARY = "e7q.ir.qcec-numerical-unitary"
GLOBAL_PHASE = "e7q.ir.qcec-numerical-global-phase"
NATIVE_REF = "native:test:source"
EXTERNAL_REF = "external:test:source"


def native(
    gates: str = "  H q[0]\n  CX q[0], q[1]\n",
    *,
    qubits: int = 2,
    bits: int | None = None,
    backend: str = "statevector",
    seed: str = "  seed: 7\n",
) -> bytes:
    bits = qubits if bits is None else bits
    return (
        "context NativeComparison {\n"
        "  shots: 32\n"
        f"  backend: {backend}\n"
        f"{seed}"
        "}\n\n"
        f"qubits q[{qubits}]\n"
        f"bits c[{bits}]\n\n"
        "invariant normalized\n\n"
        "path Compare {\n"
        f"{gates}"
        "  measure q -> c\n"
        "}\n\n"
        "verify Compare\n"
    ).encode("utf-8")


def qasm(
    gates: str = "h q[0];\ncx q[0],q[1];\n",
    *,
    qubits: int = 2,
    classical: int | None = None,
    measurement: str = "measure q -> c;\n",
) -> bytes:
    classical = qubits if classical is None else classical
    return (
        "OPENQASM 2.0;\n"
        'include "qelib1.inc";\n'
        f"qreg q[{qubits}];\n"
        f"creg c[{classical}];\n"
        f"{gates}{measurement}"
    ).encode("utf-8")


class Result:
    def __init__(self, verdict: str):
        self.verdict = verdict

    def json(self):
        return {
            "equivalence": self.verdict,
            "preprocessing_time": 0.001,
            "check_time": 0.002,
            "checkers": [{
                "checker": "decision_diagram_alternating",
                "runtime": 0.002,
                "equivalence": self.verdict,
            }],
        }


class Backend:
    def __init__(self, verdict: str):
        self.verdict = verdict

    def __call__(self, left, right, **kwargs):
        assert Path(left).read_text().endswith("\n")
        assert Path(right).read_text().endswith("\n")
        assert "measure" not in Path(left).read_text().lower()
        assert "measure" not in Path(right).read_text().lower()
        assert kwargs["numerical_tolerance"] == NUMERICAL_TOLERANCE
        assert kwargs["fidelity_threshold"] == FIDELITY_THRESHOLD
        return Result(self.verdict)


def sleeping_backend(*args, **kwargs):
    time.sleep(10)
    return Result("equivalent")


def memory_backend(*args, **kwargs):
    raise MemoryError("bounded allocation rejected")


def crash_backend(*args, **kwargs):
    os._exit(31)


def _write_pair(tmp_path: Path, native_raw: bytes, external_raw: bytes):
    native_path = tmp_path / "input.e7q"
    external_path = tmp_path / "external.qasm"
    native_path.write_bytes(native_raw)
    external_path.write_bytes(external_raw)
    return native_path, external_path


def _build(
    tmp_path: Path,
    *,
    native_raw: bytes | None = None,
    external_raw: bytes | None = None,
    criterion: str = UNITARY,
    verdict: str = "equivalent",
    backend=None,
    timeout: float = 5.0,
):
    native_path, external_path = _write_pair(
        tmp_path,
        native_raw if native_raw is not None else native(),
        external_raw if external_raw is not None else qasm(),
    )
    return build_native_external_qcec_graph(
        native_path,
        external_path,
        criterion_id=criterion,
        numerical_tolerance=NUMERICAL_TOLERANCE,
        fidelity_threshold=FIDELITY_THRESHOLD,
        timeout_seconds=timeout,
        memory_limit_bytes=64 * 1024**3,
        created_at=STAMP,
        native_source_ref=NATIVE_REF,
        external_source_ref=EXTERNAL_REF,
        nthreads=1,
        max_simulations=4,
        seed=11,
        verify_backend=backend or Backend(verdict),
    )


def _artifacts(graph, kind):
    return [artifact for artifact in graph["artifacts"] if artifact["kind"] == kind]


def _assessment(graph):
    return _artifacts(graph, "assessment")[0]["payload"]


def _claim(graph):
    return _artifacts(graph, "claim")[0]["payload"]


def test_native_bell_and_external_bell_build_complete_criterion_bound_path(tmp_path):
    graph = _build(tmp_path)
    assessment = _assessment(graph)
    assert assessment["outcome"]["status"] == "PASS"
    assert assessment["criterion"]["id"] == UNITARY
    assert assessment["method"]["exact_algebraic"] is False
    assert _claim(graph)["support_status"] == "supported-within-declared-scope"
    assert len(_artifacts(graph, "source")) == 2
    assert len(_artifacts(graph, "representation")) == 4
    assert len(_artifacts(graph, "transformation")) == 2
    assert len(_artifacts(graph, "execution")) == 1
    assert _artifacts(graph, "execution")[0]["payload"]["proof"]
    transforms = [relation for relation in graph["relations"] if relation["kind"] == "transforms"]
    assert len(transforms) == 2
    assert all(relation["validation_status"] == "not-assessed" for relation in transforms)
    assert all("terminal-measurement-operation" in " ".join(relation["loses"]) for relation in transforms)

    report = validate_graph(graph, level="F2")
    assert report["level_results"]["F0"] == "PASS"
    assert report["level_results"]["F1"] == "PASS"
    assert report["highest_level_passed"] == "F1"
    assert report["level_results"]["F2"] != "PASS"


def test_global_phase_only_equality_is_bound_to_requested_criterion(tmp_path):
    native_raw = native("  X q[0]\n  Z q[0]\n")
    external_raw = qasm("z q[0];\nx q[0];\n")
    phase = _build(
        tmp_path, native_raw=native_raw, external_raw=external_raw,
        criterion=GLOBAL_PHASE, verdict="equivalent_up_to_global_phase",
    )
    assert _assessment(phase)["outcome"]["status"] == "PASS"
    assert _claim(phase)["support_status"] == "supported-within-declared-scope"

    exact_dir = tmp_path / "unitary"
    exact_dir.mkdir()
    unitary = _build(
        exact_dir, native_raw=native_raw, external_raw=external_raw,
        criterion=UNITARY, verdict="equivalent_up_to_global_phase",
    )
    assert _assessment(unitary)["outcome"]["status"] == "FAIL"
    assert _claim(unitary)["support_status"] == "unsupported"


def test_deliberately_altered_external_circuit_fails(tmp_path):
    graph = _build(
        tmp_path,
        external_raw=qasm("h q[0];\nx q[1];\n"),
        verdict="not_equivalent",
    )
    assert _assessment(graph)["outcome"]["status"] == "FAIL"
    assert _claim(graph)["support_status"] == "unsupported"


@pytest.mark.parametrize(
    ("external_raw", "code"),
    [
        (qasm(qubits=3), "quantum_width_mismatch"),
        (
            qasm(measurement="measure q[0] -> c[1];\nmeasure q[1] -> c[0];\n"),
            "terminal_measurement_mapping",
        ),
    ],
)
def test_incompatible_width_or_measurement_mapping_is_unsupported_without_qcec(
    tmp_path, external_raw, code,
):
    graph = _build(tmp_path, external_raw=external_raw, backend=crash_backend)
    assessment = _assessment(graph)
    assert assessment["outcome"]["status"] == "UNSUPPORTED"
    assert assessment["worker"]["started"] is False
    assert any(error["code"] == code for error in assessment["input_errors"])
    evaluations = {
        artifact["payload"]["role"]: artifact["payload"]
        for artifact in _artifacts(graph, "representation")
        if artifact["payload"].get("format") == "e7q.openqasm2-unitary-prefix/v1"
    }
    assert evaluations["native"]["content_base64"] is not None
    if code == "quantum_width_mismatch":
        assert evaluations["external"]["content_base64"] is not None
    else:
        assert evaluations["external"]["content_base64"] is None


def test_unsupported_dynamic_control_is_not_silently_ignored(tmp_path):
    dynamic = native(
        "  H q[0]\n"
        "  measure q[0] -> c[0]\n"
        "  if c[0] == 1 X q[1]\n"
    )
    graph = _build(tmp_path, native_raw=dynamic, backend=crash_backend)
    assessment = _assessment(graph)
    assert assessment["outcome"]["status"] == "UNSUPPORTED"
    assert assessment["worker"]["started"] is False
    codes = {error["code"] for error in assessment["input_errors"]}
    assert {"dynamic_measurement", "dynamic_control"} <= codes


@pytest.mark.parametrize(
    "native_raw,expected_code",
    [
        (native("  noise bit_flip(0.1) q[0]\n", backend="densitymatrix"), "noise"),
        (native("  X q[0]\n  assert c[0] == 0\n"), "assertion"),
    ],
)
def test_noise_and_assertions_are_explicitly_unsupported(
    tmp_path, native_raw, expected_code,
):
    graph = _build(tmp_path, native_raw=native_raw, backend=crash_backend)
    assessment = _assessment(graph)
    assert assessment["outcome"]["status"] == "UNSUPPORTED"
    assert assessment["worker"]["started"] is False
    assert any(error["code"] == expected_code for error in assessment["input_errors"])


@pytest.mark.parametrize(
    ("external_raw", "expected_code"),
    [
        (qasm("u3(0,0,0) q[0];\n"), "unsupported_gate"),
        (qasm("h q[0];\nbarrier q;\n"), "barrier"),
        (
            b'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\n'
            b'qreg ancilla[1];\ncreg c[2];\nh q[0];\ncx q[0],q[1];\n'
            b'measure q -> c;\n',
            "register_count",
        ),
    ],
)
def test_unsupported_gates_barriers_and_ancillas_are_rejected_before_qcec(
    tmp_path, external_raw, expected_code,
):
    graph = _build(tmp_path, external_raw=external_raw, backend=crash_backend)
    assessment = _assessment(graph)
    assert assessment["outcome"]["status"] == "UNSUPPORTED"
    assert assessment["worker"]["started"] is False
    assert any(error["code"] == expected_code for error in assessment["input_errors"])


def test_memory_exhaustion_propagates_without_pass(tmp_path):
    graph = _build(tmp_path, backend=memory_backend)
    assessment = _assessment(graph)
    assert assessment["outcome"]["status"] == "BLOCKED"
    assert assessment["outcome"]["reason"] == "resource_exhaustion"
    assert assessment["outcome"]["resource_exhausted"] is True
    assert assessment["resource_use"]["memory_limit_requested_bytes"] == 64 * 1024**3
    assert assessment["worker"]["reaped"] is True
    assert _claim(graph)["support_status"] == "unsupported"


def test_timeout_and_worker_failure_propagate_without_pass(tmp_path):
    timed_out = _build(tmp_path, backend=sleeping_backend, timeout=0.05)
    timeout_assessment = _assessment(timed_out)
    assert timeout_assessment["outcome"]["status"] == "BLOCKED"
    assert timeout_assessment["outcome"]["reason"] == "wall_clock_timeout"
    assert timeout_assessment["worker"]["reaped"] is True
    worker_pid = timeout_assessment["worker"]["pid"]
    assert all(child.pid != worker_pid for child in multiprocessing.active_children())

    crash_dir = tmp_path / "crash"
    crash_dir.mkdir()
    crashed = _build(crash_dir, backend=crash_backend)
    crash_assessment = _assessment(crashed)
    assert crash_assessment["outcome"]["status"] == "NOT_ASSESSED"
    assert crash_assessment["outcome"]["reason"] == "worker_crash"
    assert crash_assessment["worker"]["exit_code"] == 31
    assert crash_assessment["worker"]["reaped"] is True
    assert _claim(crashed)["support_status"] == "unsupported"


def test_both_original_sources_recover_byte_for_byte(tmp_path):
    native_raw = native() + b"\n# retained native comment\n"
    external_raw = qasm() + b"// retained external comment\n\n"
    graph = _build(tmp_path, native_raw=native_raw, external_raw=external_raw)
    assert recover_native_external_source(graph, NATIVE_REF) == native_raw
    assert recover_native_external_source(graph, EXTERNAL_REF) == external_raw
    digests = {artifact["payload"]["content_digest"] for artifact in _artifacts(graph, "source")}
    assert len(digests) == 2


def test_fixed_inputs_and_metadata_produce_deterministic_nonruntime_identities(tmp_path):
    first = _build(tmp_path)
    other = tmp_path / "other"
    other.mkdir()
    second = _build(other)
    assert first["extensions"]["workflow_request_id"] == second["extensions"]["workflow_request_id"]
    stable_kinds = {"source", "representation", "transformation"}
    first_ids = [artifact["artifact_id"] for artifact in first["artifacts"] if artifact["kind"] in stable_kinds]
    second_ids = [artifact["artifact_id"] for artifact in second["artifacts"] if artifact["kind"] in stable_kinds]
    assert first_ids == second_ids


@pytest.mark.parametrize(
    "verdict",
    [
        "probably_equivalent",
        "probably_not_equivalent",
        "no_information",
        "equivalent_up_to_phase",
        "unknown_future_verdict",
    ],
)
def test_no_inconclusive_qcec_outcome_becomes_pass(tmp_path, verdict):
    graph = _build(tmp_path, verdict=verdict)
    outcome = _assessment(graph)["outcome"]
    assert outcome["status"] != "PASS"
    assert outcome["conclusion"] == "INCONCLUSIVE"
    assert _claim(graph)["support_status"] == "unsupported"


def test_cli_accepts_native_and_external_sources_and_preserves_non_pass_evidence(tmp_path):
    native_path, external_path = _write_pair(
        tmp_path, native(), qasm("u3(0,0,0) q[0];\n")
    )
    output = tmp_path / "graph.json"
    subprocess.run([
        sys.executable,
        "-m",
        "e7q.ir.native_qcec_workflow",
        str(native_path),
        str(external_path),
        "--criterion",
        UNITARY,
        "--numerical-tolerance",
        str(NUMERICAL_TOLERANCE),
        "--fidelity-threshold",
        str(FIDELITY_THRESHOLD),
        "--timeout-seconds",
        "5",
        "--memory-limit-bytes",
        str(64 * 1024**3),
        "--created-at",
        STAMP,
        "--native-source-ref",
        NATIVE_REF,
        "--external-source-ref",
        EXTERNAL_REF,
        "--output",
        str(output),
    ], check=True)
    graph = json.loads(output.read_text())
    assert _assessment(graph)["outcome"]["status"] == "UNSUPPORTED"
    assert recover_native_external_source(graph, NATIVE_REF) == native_path.read_bytes()
    assert recover_native_external_source(graph, EXTERNAL_REF) == external_path.read_bytes()


def test_numerical_workflow_rejects_exact_algebraic_criterion(tmp_path):
    native_path, external_path = _write_pair(tmp_path, native(), qasm())
    with pytest.raises(E7QError, match="unsupported QCEC numerical criterion"):
        build_native_external_qcec_graph(
            native_path,
            external_path,
            criterion_id=CRITERION["id"],
            numerical_tolerance=NUMERICAL_TOLERANCE,
            fidelity_threshold=FIDELITY_THRESHOLD,
            timeout_seconds=5.0,
            memory_limit_bytes=64 * 1024**3,
            created_at=STAMP,
            native_source_ref=NATIVE_REF,
            external_source_ref=EXTERNAL_REF,
            verify_backend=Backend("equivalent"),
        )
