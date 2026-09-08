# SPDX-License-Identifier: Apache-2.0
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
from e7q.ir.qcec_workflow import (
    build_external_qcec_graph,
    recover_external_qcec_source,
)

STAMP = "2026-09-08T00:00:00Z"
UNITARY = "e7q.ir.qcec-numerical-unitary"
GLOBAL_PHASE = "e7q.ir.qcec-numerical-global-phase"
LEFT_REF = "external:test:left"
RIGHT_REF = "external:test:right"


def qasm(gates: str = "", *, qubits: int = 2) -> bytes:
    return (
        f'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[{qubits}];\n'
        f'creg c[{qubits}];\n{gates}measure q -> c;\n'
    ).encode()


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
        assert Path(left).name == "left.qasm"
        assert Path(right).name == "right.qasm"
        assert kwargs["numerical_tolerance"] == NUMERICAL_TOLERANCE
        assert kwargs["fidelity_threshold"] == FIDELITY_THRESHOLD
        return Result(self.verdict)


def sleeping_backend(*args, **kwargs):
    time.sleep(10)
    return Result("equivalent")


def memory_backend(*args, **kwargs):
    raise MemoryError("bounded allocation rejected")


def crash_backend(*args, **kwargs):
    os._exit(19)


def _write_pair(tmp_path, left: bytes, right: bytes):
    left_path = tmp_path / "original-left.qasm"
    right_path = tmp_path / "original-right.qasm"
    left_path.write_bytes(left)
    right_path.write_bytes(right)
    return left_path, right_path


def _build(tmp_path, verdict="equivalent", criterion=UNITARY, *, left=None, right=None,
           timeout=5.0, memory=64 * 1024**3, backend=None):
    left_path, right_path = _write_pair(
        tmp_path,
        left if left is not None else qasm("h q[0];\n"),
        right if right is not None else qasm("h q[0];\n"),
    )
    return build_external_qcec_graph(
        left_path,
        right_path,
        criterion_id=criterion,
        numerical_tolerance=NUMERICAL_TOLERANCE,
        fidelity_threshold=FIDELITY_THRESHOLD,
        timeout_seconds=timeout,
        memory_limit_bytes=memory,
        created_at=STAMP,
        left_source_ref=LEFT_REF,
        right_source_ref=RIGHT_REF,
        nthreads=1,
        max_simulations=4,
        seed=7,
        verify_backend=backend or Backend(verdict),
    )


def _artifacts(graph):
    return {kind: [item for item in graph["artifacts"] if item["kind"] == kind]
            for kind in {item["kind"] for item in graph["artifacts"]}}


def _outcome(graph):
    return _artifacts(graph)["assessment"][0]["payload"]["outcome"]


def _claim(graph):
    return _artifacts(graph)["claim"][0]["payload"]


def test_numerically_identical_circuits_produce_supported_bounded_claim(tmp_path):
    graph = _build(tmp_path)
    outcome = _outcome(graph)
    assert outcome["status"] == "PASS"
    assert outcome["raw_verdict"] == "equivalent"
    assert _claim(graph)["support_status"] == "supported-within-declared-scope"
    assert validate_graph(graph, level="F1")["status"] == "PASS"
    assert [item["kind"] for item in graph["artifacts"]] == [
        "source", "source", "representation", "representation", "assessment", "claim"
    ]


def test_global_phase_only_equality_obeys_requested_criterion(tmp_path):
    phase_graph = _build(
        tmp_path, verdict="equivalent_up_to_global_phase", criterion=GLOBAL_PHASE,
        left=qasm("x q[0];\nz q[0];\n"), right=qasm("z q[0];\nx q[0];\n"),
    )
    assert _outcome(phase_graph)["status"] == "PASS"
    assert _claim(phase_graph)["support_status"] == "supported-within-declared-scope"

    unitary_dir = tmp_path / "unitary"
    unitary_dir.mkdir()
    unitary_graph = _build(
        unitary_dir, verdict="equivalent_up_to_global_phase", criterion=UNITARY,
        left=qasm("x q[0];\nz q[0];\n"), right=qasm("z q[0];\nx q[0];\n"),
    )
    assert _outcome(unitary_graph)["status"] == "FAIL"
    assert _claim(unitary_graph)["support_status"] == "unsupported"


def test_deliberately_altered_circuit_is_non_pass(tmp_path):
    graph = _build(
        tmp_path, verdict="not_equivalent",
        left=qasm("x q[0];\n"), right=qasm("z q[0];\n"),
    )
    assert _outcome(graph)["status"] == "FAIL"
    assert _claim(graph)["support_status"] == "unsupported"


def test_unsupported_syntax_is_preserved_without_starting_qcec(tmp_path):
    graph = _build(
        tmp_path,
        left=qasm("mystery q[0];\n"),
        right=qasm(),
        backend=crash_backend,
    )
    outcome = _outcome(graph)
    assessment = _artifacts(graph)["assessment"][0]["payload"]
    representations = _artifacts(graph)["representation"]
    assert outcome["status"] == "UNSUPPORTED"
    assert outcome["reason"] == "unsupported_input"
    assert assessment["worker"]["started"] is False
    assert any(item["payload"]["parse_status"] == "UNSUPPORTED" for item in representations)
    assert _claim(graph)["support_status"] == "unsupported"


def test_timeout_is_blocked_and_worker_is_reaped(tmp_path):
    graph = _build(tmp_path, timeout=0.05, backend=sleeping_backend)
    assessment = _artifacts(graph)["assessment"][0]["payload"]
    assert assessment["outcome"]["status"] == "BLOCKED"
    assert assessment["outcome"]["reason"] == "wall_clock_timeout"
    assert assessment["worker"]["reaped"] is True
    pid = assessment["worker"]["pid"]
    assert all(child.pid != pid for child in multiprocessing.active_children())
    assert _claim(graph)["support_status"] == "unsupported"


def test_memory_exhaustion_is_non_pass_and_enforcement_is_recorded(tmp_path):
    requested = 64 * 1024**3
    graph = _build(tmp_path, memory=requested, backend=memory_backend)
    assessment = _artifacts(graph)["assessment"][0]["payload"]
    resources = assessment["resource_use"]
    assert assessment["outcome"]["status"] == "BLOCKED"
    assert assessment["outcome"]["reason"] == "resource_exhaustion"
    assert resources["memory_limit_requested_bytes"] == requested
    if sys.platform.startswith("linux"):
        assert resources["memory_limit_enforced"] is True
        assert resources["memory_limit_mechanism"] == "posix-rlimit-as"
    else:
        assert isinstance(resources["memory_limit_enforced"], bool)


def test_worker_failure_remains_distinct_non_pass(tmp_path):
    graph = _build(tmp_path, backend=crash_backend)
    assessment = _artifacts(graph)["assessment"][0]["payload"]
    assert assessment["outcome"]["status"] == "NOT_ASSESSED"
    assert assessment["outcome"]["reason"] == "worker_crash"
    assert assessment["worker"]["exit_code"] == 19
    assert assessment["worker"]["reaped"] is True
    assert _claim(graph)["support_status"] == "unsupported"


def test_fixed_metadata_produces_deterministic_request_source_and_representation_ids(tmp_path):
    first = _build(tmp_path)
    other = tmp_path / "other"
    other.mkdir()
    second = _build(other)
    assert first["extensions"]["workflow_request_id"] == second["extensions"]["workflow_request_id"]
    first_ids = [item["artifact_id"] for item in first["artifacts"][:4]]
    second_ids = [item["artifact_id"] for item in second["artifacts"][:4]]
    assert first_ids == second_ids


def test_byte_for_byte_input_recovery(tmp_path):
    left = qasm("h q[0];\n") + b"// retained trailing bytes\n\n"
    right = qasm("x q[1];\n") + b"  \n"
    graph = _build(tmp_path, left=left, right=right)
    assert recover_external_qcec_source(graph, LEFT_REF) == left
    assert recover_external_qcec_source(graph, RIGHT_REF) == right
    sources = _artifacts(graph)["source"]
    assert {item["payload"]["stable_source_ref"] for item in sources} == {LEFT_REF, RIGHT_REF}


@pytest.mark.parametrize("verdict", [
    "probably_equivalent",
    "probably_not_equivalent",
    "no_information",
    "equivalent_up_to_phase",
    "unknown_future_verdict",
])
def test_assurance_isolation_never_promotes_inconclusive_verdicts(tmp_path, verdict):
    graph = _build(tmp_path, verdict=verdict)
    outcome = _outcome(graph)
    assert outcome["status"] != "PASS"
    assert outcome["conclusion"] == "INCONCLUSIVE"
    assert _claim(graph)["support_status"] == "unsupported"


def test_cli_accepts_two_files_and_writes_non_pass_evidence(tmp_path):
    left_path, right_path = _write_pair(tmp_path, qasm("mystery q[0];\n"), qasm())
    output = tmp_path / "graph.json"
    subprocess.run([
        sys.executable, "-m", "e7q.ir.qcec_workflow", str(left_path), str(right_path),
        "--criterion", UNITARY,
        "--numerical-tolerance", str(NUMERICAL_TOLERANCE),
        "--fidelity-threshold", str(FIDELITY_THRESHOLD),
        "--timeout-seconds", "5",
        "--memory-limit-bytes", str(64 * 1024**3),
        "--created-at", STAMP,
        "--left-source-ref", LEFT_REF,
        "--right-source-ref", RIGHT_REF,
        "--output", str(output),
    ], check=True)
    graph = json.loads(output.read_text())
    assert _outcome(graph)["status"] == "UNSUPPORTED"
    assert recover_external_qcec_source(graph, LEFT_REF) == left_path.read_bytes()


def test_structured_32_qubit_fixture_builds_complete_graph(tmp_path):
    root = Path(__file__).parents[1] / "examples" / "e7q-ir" / "qcec-pair-32"
    graph = build_external_qcec_graph(
        root / "left.qasm",
        root / "right.qasm",
        criterion_id=UNITARY,
        numerical_tolerance=NUMERICAL_TOLERANCE,
        fidelity_threshold=FIDELITY_THRESHOLD,
        timeout_seconds=10.0,
        memory_limit_bytes=64 * 1024**3,
        created_at=STAMP,
        left_source_ref="fixture:qcec-pair-32:left",
        right_source_ref="fixture:qcec-pair-32:right",
        nthreads=1,
        max_simulations=4,
        seed=7,
        verify_backend=Backend("equivalent"),
    )
    representations = _artifacts(graph)["representation"]
    assert all(item["payload"]["parse_status"] == "PASS" for item in representations)
    assert all(
        item["payload"]["parsed"]["registers"]["quantum"][0]["width"] == 32
        for item in representations
    )
    assert _outcome(graph)["status"] == "PASS"
    assert any("do not establish general tractability" in item.lower() for item in _claim(graph)["boundaries"])
