# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import copy
import multiprocessing
import os
from pathlib import Path
import time

import pytest

from e7q.ir.canonical import digest, identified_digest
from e7q.ir.compiler_workflow import (
    REPRESENTATION_FORMAT,
    REQUEST_FORMAT,
    TRACE_FORMAT,
    build_compiler_proof_graph,
    recover_compiler_source,
    validate_compiler_evidence,
)
from e7q.ir.conformance import validate_graph
from e7q.ir.qcec import FIDELITY_THRESHOLD, NUMERICAL_TOLERANCE
from e7q.ir.unitary import CRITERION
from e7q.language import E7QError

STAMP = "2026-09-08T00:00:00Z"
SOURCE_REF = "fixture:compiler-proof:native"
UNITARY = "e7q.ir.qcec-numerical-unitary"
GLOBAL_PHASE = "e7q.ir.qcec-numerical-global-phase"
NATIVE_GATES = frozenset({"H", "X", "Z", "CX", "CZ", "SWAP"})


def native(operations: str, *, qubits: int = 4, seed: int = 7) -> bytes:
    return (
        "context CompilerEvidence {\n"
        "  shots: 32\n"
        "  backend: statevector\n"
        f"  seed: {seed}\n"
        "}\n\n"
        f"qubits q[{qubits}]\n"
        f"bits c[{qubits}]\n\n"
        "invariant normalized\n\n"
        "path Route {\n"
        f"{operations}"
        "  measure q -> c\n"
        "}\n\n"
        "verify Route\n"
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
    os._exit(29)


def _build(
    tmp_path: Path,
    *,
    source: bytes | None = None,
    edges=((0, 1), (1, 2), (2, 3)),
    native_gates=NATIVE_GATES,
    criterion=UNITARY,
    verdict="equivalent",
    backend=None,
    timeout=5.0,
):
    path = tmp_path / "input.e7q"
    path.write_bytes(source or native("  H q[0]\n  CX q[0], q[3]\n"))
    return build_compiler_proof_graph(
        path,
        coupling_edges=edges,
        native_gates=native_gates,
        criterion_id=criterion,
        numerical_tolerance=NUMERICAL_TOLERANCE,
        fidelity_threshold=FIDELITY_THRESHOLD,
        timeout_seconds=timeout,
        memory_limit_bytes=64 * 1024**3,
        created_at=STAMP,
        source_ref=SOURCE_REF,
        nthreads=1,
        max_simulations=4,
        seed=11,
        verify_backend=backend or Backend(verdict),
    )


def _artifact(graph, *, kind=None, format=None, role=None):
    matches = []
    for artifact in graph["artifacts"]:
        payload = artifact["payload"]
        if kind is not None and artifact["kind"] != kind:
            continue
        if format is not None and payload.get("format") != format:
            continue
        if role is not None and payload.get("role") != role:
            continue
        matches.append(artifact)
    assert len(matches) == 1
    return matches[0]


def _trace(graph):
    return _artifact(graph, format=TRACE_FORMAT)["payload"]


def _assessment(graph):
    return _artifact(graph, kind="assessment")["payload"]


def _claim(graph):
    return _artifact(graph, kind="claim")["payload"]


def _rehash(graph):
    mapping = {}

    def rewrite(value):
        if isinstance(value, str):
            return mapping.get(value, value)
        if isinstance(value, list):
            return [rewrite(item) for item in value]
        if isinstance(value, dict):
            return {key: rewrite(item) for key, item in value.items()}
        return value

    for artifact in graph["artifacts"]:
        old = artifact["artifact_id"]
        artifact.update(rewrite(artifact))
        artifact["artifact_id"] = identified_digest(artifact, "artifact_id")
        mapping[old] = artifact["artifact_id"]
    for relation in graph["relations"]:
        relation.update(rewrite(relation))
        relation["relation_id"] = identified_digest(relation, "relation_id")
    graph["graph_id"] = identified_digest(graph, "graph_id")


def test_adjacent_cx_needs_no_routing_and_builds_bounded_f0_f1_path(tmp_path):
    graph = _build(
        tmp_path,
        source=native("  H q[0]\n  CX q[0], q[1]\n", qubits=2),
        edges=((0, 1),),
    )
    trace = _trace(graph)
    assert trace["compiler_status"] == "PASS"
    assert trace["original_compilation_result"]["inserted_swaps"] == 0
    route = trace["typed_steps"][1]
    assert route["selected_physical_path"] == [0, 1]
    assert route["inserted_swaps"] == []
    assert route["layout_assertion"]["passed"] is True
    assert _assessment(graph)["outcome"]["status"] == "PASS"
    assert _claim(graph)["support_status"] == "supported-within-declared-scope"
    assert validate_compiler_evidence(graph)["status"] == "PASS"

    report = validate_graph(graph, level="F2")
    assert report["level_results"]["F0"] == "PASS"
    assert report["level_results"]["F1"] == "PASS"
    assert report["level_results"]["F2"] != "PASS"
    assert report["highest_level_passed"] == "F1"


def test_nonadjacent_cx_has_forward_and_reverse_swaps_with_restored_layout(tmp_path):
    graph = _build(tmp_path)
    trace = _trace(graph)
    route = trace["typed_steps"][1]
    assert route["source_operation_index"] == 2
    assert route["logical_qubits"] == [0, 3]
    assert route["selected_physical_path"] == [0, 1, 2, 3]
    assert route["routed_physical_qubits"] == [2, 3]
    assert route["inserted_swaps"] == [
        {"order": 0, "phase": "forward", "qubits": [0, 1]},
        {"order": 1, "phase": "forward", "qubits": [1, 2]},
        {"order": 2, "phase": "reverse", "qubits": [1, 2]},
        {"order": 3, "phase": "reverse", "qubits": [0, 1]},
    ]
    summary = trace["typed_steps"][-1]
    assert summary["inserted_swap_count"] == 4
    assert summary["routing_overhead_operations"] == 4
    assert summary["layout_assertion"] == {
        "assertion": "final-logical-layout-restored",
        "passed": True,
    }
    compiled = _artifact(graph, format=REPRESENTATION_FORMAT, role="compiled")["payload"]
    assert [operation["gate"] for operation in compiled["program"]["operations"]] == [
        "H", "SWAP", "SWAP", "CX", "SWAP", "SWAP", "MEASURE",
    ]


def test_multiple_routing_steps_are_typed_in_deterministic_source_order(tmp_path):
    source = native("  CX q[0], q[3]\n  CZ q[1], q[3]\n")
    first = _build(tmp_path, source=source)
    other = tmp_path / "other"
    other.mkdir()
    second = _build(other, source=source)
    routes = _trace(first)["typed_steps"][1:-1]
    assert [route["order"] for route in routes] == [1, 2]
    assert [route["source_operation_index"] for route in routes] == [1, 2]
    assert [route["operator"] for route in routes] == ["CX", "CZ"]
    assert [route["selected_physical_path"] for route in routes] == [
        [0, 1, 2, 3], [1, 2, 3],
    ]
    assert _trace(first)["typed_steps"] == _trace(second)["typed_steps"]


def test_disconnected_coupling_graph_is_blocked_before_qcec(tmp_path):
    graph = _build(tmp_path, edges=((0, 1), (2, 3)), backend=crash_backend)
    assert _trace(graph)["compiler_status"] == "BLOCKED"
    assert _assessment(graph)["outcome"]["status"] == "BLOCKED"
    assert _assessment(graph)["outcome"]["reason"] == "disconnected_topology"
    assert _assessment(graph)["worker"]["started"] is False
    assert _claim(graph)["support_status"] == "unsupported"
    assert validate_compiler_evidence(graph)["status"] == "BLOCKED"


def test_missing_swap_support_is_unsupported_before_qcec(tmp_path):
    graph = _build(
        tmp_path,
        native_gates=frozenset({"H", "CX"}),
        backend=crash_backend,
    )
    assert _trace(graph)["compiler_status"] == "UNSUPPORTED"
    assert _assessment(graph)["outcome"]["status"] == "UNSUPPORTED"
    assert _assessment(graph)["outcome"]["reason"] == "missing_swap_support"
    assert _assessment(graph)["worker"]["started"] is False
    assert _claim(graph)["support_status"] == "unsupported"


def test_source_gate_missing_from_native_set_is_unsupported(tmp_path):
    graph = _build(
        tmp_path,
        source=native("  CZ q[0], q[3]\n"),
        native_gates=frozenset({"H", "CX", "SWAP"}),
        backend=crash_backend,
    )
    assert _trace(graph)["compiler_status"] == "UNSUPPORTED"
    assert _assessment(graph)["outcome"]["reason"] == "unsupported_native_gate"
    assert _assessment(graph)["worker"]["started"] is False
    assert _claim(graph)["support_status"] == "unsupported"


@pytest.mark.parametrize(
    "edges,code",
    [
        (((0, 0), (1, 2)), "malformed_topology"),
        (((0, 1), (1, 0), (1, 2), (2, 3)), "duplicate_topology_edge"),
        (((0, 4), (1, 2)), "malformed_topology"),
    ],
)
def test_invalid_and_duplicate_topology_edges_are_unsupported(
    tmp_path, edges, code,
):
    graph = _build(tmp_path, edges=edges, backend=crash_backend)
    assert _assessment(graph)["outcome"]["status"] == "UNSUPPORTED"
    assert _assessment(graph)["worker"]["started"] is False
    assert any(error["code"] == code for error in _trace(graph)["errors"])
    assert _claim(graph)["support_status"] == "unsupported"


def test_compiled_representation_tampering_fails_after_recomputed_identities(tmp_path):
    graph = copy.deepcopy(_build(tmp_path))
    compiled = _artifact(graph, format=REPRESENTATION_FORMAT, role="compiled")
    compiled["payload"]["program"]["operations"][3]["gate"] = "CZ"
    compiled["payload"]["content_identity"] = digest({
        "format": "e7q.native-program-content/v1",
        "program": compiled["payload"]["program"],
    })
    _rehash(graph)
    assert validate_graph(graph, level="F1")["status"] == "PASS"
    report = validate_compiler_evidence(graph)
    assert report["status"] == "FAIL"
    assert report["reason"] == "compiler_evidence_inconsistent"
    assert _claim(graph)["support_status"] == "supported-within-declared-scope"


def test_compiler_trace_tampering_fails_after_recomputed_identities(tmp_path):
    graph = copy.deepcopy(_build(tmp_path))
    trace = _artifact(graph, format=TRACE_FORMAT)
    trace["payload"]["typed_steps"][1]["selected_physical_path"] = [0, 2, 3]
    trace["payload"]["original_compiler_proof"][1]["physical_path"] = [0, 2, 3]
    trace["payload"]["original_compilation_result"]["proof"][1]["physical_path"] = [0, 2, 3]
    _rehash(graph)
    assert validate_graph(graph, level="F1")["status"] == "PASS"
    assert validate_compiler_evidence(graph)["status"] == "FAIL"


def test_qcec_inequality_overrides_compiler_preservation_declaration(tmp_path):
    graph = _build(tmp_path, verdict="not_equivalent")
    declaration = _trace(graph)["compiler_preservation_declaration"]
    assert declaration["status"] == "PASS"
    assert declaration["semantic_equivalence_established"] is False
    assert _assessment(graph)["outcome"]["status"] == "FAIL"
    assert _claim(graph)["support_status"] == "unsupported"
    assert validate_compiler_evidence(graph)["status"] == "FAIL"


def test_qcec_memory_exhaustion_remains_blocked_and_reaped(tmp_path):
    graph = _build(tmp_path, backend=memory_backend)
    assessment = _assessment(graph)
    assert assessment["outcome"]["status"] == "BLOCKED"
    assert assessment["outcome"]["reason"] == "resource_exhaustion"
    assert assessment["outcome"]["resource_exhausted"] is True
    assert assessment["worker"]["reaped"] is True
    assert _claim(graph)["support_status"] == "unsupported"


def test_qcec_timeout_and_worker_failure_remain_non_pass_and_reaped(tmp_path):
    timed_out = _build(tmp_path, backend=sleeping_backend, timeout=0.05)
    timeout_assessment = _assessment(timed_out)
    assert timeout_assessment["outcome"]["status"] == "BLOCKED"
    assert timeout_assessment["outcome"]["reason"] == "wall_clock_timeout"
    assert timeout_assessment["worker"]["reaped"] is True
    timeout_pid = timeout_assessment["worker"]["pid"]
    assert all(child.pid != timeout_pid for child in multiprocessing.active_children())
    assert _claim(timed_out)["support_status"] == "unsupported"

    crash_dir = tmp_path / "crash"
    crash_dir.mkdir()
    crashed = _build(crash_dir, backend=crash_backend)
    crash_assessment = _assessment(crashed)
    assert crash_assessment["outcome"]["status"] == "NOT_ASSESSED"
    assert crash_assessment["outcome"]["reason"] == "worker_crash"
    assert crash_assessment["worker"]["exit_code"] == 29
    assert crash_assessment["worker"]["reaped"] is True
    assert _claim(crashed)["support_status"] == "unsupported"


def test_fixed_inputs_metadata_artifacts_and_relations_are_deterministic(tmp_path):
    first = _build(tmp_path)
    other = tmp_path / "other"
    other.mkdir()
    second = _build(other)
    assert first["extensions"]["workflow_request_id"] == second["extensions"]["workflow_request_id"]
    stable_kinds = {"source", "representation", "intent", "transformation"}
    assert [
        artifact["artifact_id"] for artifact in first["artifacts"]
        if artifact["kind"] in stable_kinds
    ] == [
        artifact["artifact_id"] for artifact in second["artifacts"]
        if artifact["kind"] in stable_kinds
    ]
    first_relations = [relation["relation_id"] for relation in first["relations"][:5]]
    second_relations = [relation["relation_id"] for relation in second["relations"][:5]]
    assert first_relations == second_relations


def test_source_and_complete_original_compiler_proof_are_preserved(tmp_path):
    raw = native("  H q[0]\n  CX q[0], q[3]\n") + b"\n# retained source bytes\n"
    graph = _build(tmp_path, source=raw)
    assert recover_compiler_source(graph, SOURCE_REF) == raw
    trace = _trace(graph)
    result = trace["original_compilation_result"]
    assert trace["original_compiler_proof"] == result["proof"]
    assert result["proof"][0]["kind"] == "compile"
    assert result["proof"][-1]["kind"] == "compilation-result"
    assert len(result["proof"]) == len(trace["typed_steps"])


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
def test_no_trace_only_or_inconclusive_case_can_support_a_claim(tmp_path, verdict):
    graph = _build(tmp_path, verdict=verdict)
    assert _trace(graph)["compiler_preservation_declaration"]["status"] == "PASS"
    assert _assessment(graph)["outcome"]["status"] != "PASS"
    assert _claim(graph)["support_status"] == "unsupported"
    assert validate_compiler_evidence(graph)["status"] != "PASS"


def test_numerical_compiler_workflow_rejects_exact_algebraic_criterion(tmp_path):
    path = tmp_path / "input.e7q"
    path.write_bytes(native("  CX q[0], q[1]\n", qubits=2))
    with pytest.raises(E7QError, match="unsupported QCEC numerical criterion"):
        build_compiler_proof_graph(
            path,
            coupling_edges=((0, 1),),
            native_gates=frozenset({"CX", "SWAP"}),
            criterion_id=CRITERION["id"],
            numerical_tolerance=NUMERICAL_TOLERANCE,
            fidelity_threshold=FIDELITY_THRESHOLD,
            timeout_seconds=5.0,
            memory_limit_bytes=64 * 1024**3,
            created_at=STAMP,
            source_ref=SOURCE_REF,
            verify_backend=Backend("equivalent"),
        )


def test_global_phase_criterion_is_recorded_without_becoming_exact_algebraic(tmp_path):
    graph = _build(tmp_path, criterion=GLOBAL_PHASE)
    request = _artifact(graph, format=REQUEST_FORMAT)["payload"]
    assert request["requested_equivalence_criterion"]["id"] == GLOBAL_PHASE
    assert _assessment(graph)["method"]["exact_algebraic"] is False
    assert _claim(graph)["requested_criterion"]["id"] == GLOBAL_PHASE
