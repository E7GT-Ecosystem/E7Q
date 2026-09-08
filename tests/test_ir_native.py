# SPDX-License-Identifier: Apache-2.0
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json
import subprocess
import sys

import pytest

from e7q.language import E7QError, parse, run, verify
from e7q.ir.canonical import canonical_bytes, identified_digest
from e7q.ir.conformance import validate_graph
from e7q.ir.legacy import import_evidence, recover_source
from e7q.ir.native import execute_native
from e7q.ir.native_semantic import (
    MAXIMUM_CONCLUSION,
    PROFILE_ID,
    PROFILE_VERSION,
    VALIDATOR_ID,
    _CONTEXT_CACHE,
    _CONTEXT_CACHE_LIMIT,
)
from e7q.ir.semantic import SemanticRegistry

STAMP = "2026-09-07T00:00:00Z"
BELL = Path("examples/bell.e7q").read_bytes()
PUBLIC_GRAPH = Path("examples/e7q-ir/native-execution-bell-graph.json")
PUBLIC_REPORT = Path("examples/e7q-ir/native-execution-bell-f2.json")


def artifact(graph, kind):
    matches = [item for item in graph["artifacts"] if item["kind"] == kind]
    assert len(matches) == 1
    return matches[0]


def by_kind(graph, kind):
    return artifact(graph, kind)["payload"]


def rehash(graph):
    mapping = {}

    def rewrite(value):
        if isinstance(value, str):
            return mapping.get(value, value)
        if isinstance(value, list):
            return [rewrite(item) for item in value]
        if isinstance(value, dict):
            return {key: rewrite(item) for key, item in value.items()}
        return value

    for item in graph["artifacts"]:
        old = item["artifact_id"]
        item.update(rewrite(item))
        item["artifact_id"] = identified_digest(item, "artifact_id")
        mapping[old] = item["artifact_id"]
    for relation in graph["relations"]:
        relation.update(rewrite(relation))
        relation["relation_id"] = identified_digest(relation, "relation_id")
    graph["graph_id"] = identified_digest(graph, "graph_id")


def assert_f2_nonpass(graph, expected=None):
    assert validate_graph(graph, level="F1")["status"] == "PASS"
    report = validate_graph(graph, level="F2")
    assert report["highest_level_passed"] == "F1"
    assert report["level_results"]["F2"] != "PASS"
    if expected is not None:
        assert report["level_results"]["F2"] == expected
    assert report == validate_graph(graph, level="F2")


def test_native_bell_reaches_deterministic_f2_and_preserves_source():
    graph = execute_native(BELL, created_at=STAMP)
    assert [item["kind"] for item in graph["artifacts"]] == [
        "source", "intent", "representation", "execution", "observation", "assessment"
    ]
    assert recover_source(graph) == BELL
    result = verify(run(parse(BELL.decode())))
    assert by_kind(graph, "assessment")["native_result"] == result
    assert by_kind(graph, "execution")["proof"] == result["proof"]
    assert by_kind(graph, "observation")["counts"] == result["counts"]
    assert graph == execute_native(BELL, created_at=STAMP)

    report = validate_graph(graph, level="F2")
    assert report == validate_graph(graph, level="F2")
    assert report["status"] == "PASS"
    assert report["highest_level_passed"] == "F2"
    assert report["level_results"]["F2"] == "PASS"
    assert len(report["semantic_results"]) == 17
    assert all(item["status"] == "PASS" for item in report["semantic_results"])
    assert all(
        item["profile"] == {"id": PROFILE_ID, "version": PROFILE_VERSION}
        and MAXIMUM_CONCLUSION in item["boundaries"]
        for item in report["semantic_results"]
    )
    graph_ids = {
        item["artifact_id"] for item in graph["artifacts"]
    } | {item["relation_id"] for item in graph["relations"]}
    assert all(
        set(item["evidence_refs"]) <= graph_ids
        for item in report["semantic_results"]
    )
    assert all(relation["validation_status"] == "validated" for relation in graph["relations"])


def test_failed_native_invariant_remains_fail_but_f2_conformance_passes():
    graph = execute_native(BELL.replace(b"{00, 11}", b"{00}"), created_at=STAMP)
    native_result = by_kind(graph, "assessment")["native_result"]
    assert native_result["status"] == "FAIL"
    assert native_result["first_failure"] is None
    report = validate_graph(graph, level="F2")
    assert report["status"] == "PASS"
    assert report["highest_level_passed"] == "F2"
    assert by_kind(graph, "assessment")["native_result"]["status"] == "FAIL"


def test_asymmetric_count_order_and_extra_bits():
    raw = BELL.replace(b"H q[0]", b"X q[0]").replace(b"  CX q[0], q[1]\n", b"")
    raw = raw.replace(b"bits c[2]", b"bits c[3]").replace(b"{00, 11}", b"{100}")
    graph = execute_native(raw, created_at=STAMP)
    observation = by_kind(graph, "observation")
    assert observation["counts"] == {"100": 1000}
    assert observation["probabilities"] == {"100": 1.0}
    assert observation["label_order"] == "clbit-ascending"
    assert observation["bit_width"] == 3
    assert validate_graph(graph, level="F2")["status"] == "PASS"


@pytest.mark.parametrize("old,new", [
    (b"backend: statevector", b"backend: densitymatrix"),
    (b"  seed: 7\n", b""),
    (b"shots: 1000", b"shots: 100001"),
    (b"q[2]", b"q[9]"),
    (b"c[2]", b"c[9]"),
    (b"  H q[0]", b"  measure q[0] -> c[0]\n  H q[0]"),
    (b"  H q[0]", b"  noise depolarizing(0.1) q[0]"),
    (b"  H q[0]", b"  if c[0] == 1 X q[0]"),
    (b"  H q[0]", b"  assert P(00) >= 0.9"),
    (b"  H q[0]", b"  X q[0]\n" * 1024),
])
def test_unsupported_or_excessive_execution_rejected_before_run(monkeypatch, old, new):
    def forbidden(*args):
        pytest.fail("simulation must not run")

    monkeypatch.setattr("e7q.ir.native.run", forbidden)
    with pytest.raises(E7QError):
        execute_native(BELL.replace(old, new), created_at=STAMP)


def _tamper(graph, case):
    source = artifact(graph, "source")
    intent = artifact(graph, "intent")
    representation = artifact(graph, "representation")
    execution = artifact(graph, "execution")
    observation = artifact(graph, "observation")
    assessment = artifact(graph, "assessment")
    transforms = next(item for item in graph["relations"] if item["kind"] == "transforms")

    if case == "source-content":
        source["payload"]["content"] = source["payload"]["content"].replace("H q[0]", "X q[0]")
    elif case == "source-digest":
        source["payload"]["content_digest"] = "sha256:" + "0" * 64
    elif case == "source-length":
        source["payload"]["byte_length"] += 1
    elif case == "intent-path":
        intent["payload"]["path"] = "ForgedPath"
    elif case == "intent-normalized":
        intent["payload"]["require_normalized"] = False
    elif case == "intent-outcomes":
        intent["payload"]["allowed_outcomes"] = ["00"]
    elif case == "intent-backend":
        intent["payload"]["backend"] = "densitymatrix"
    elif case == "intent-shots":
        intent["payload"]["shots"] = 999
    elif case == "intent-seed":
        intent["payload"]["seed"] = 8
    elif case == "operation-name":
        representation["payload"]["program"]["operations"][0]["gate"] = "X"
    elif case == "operation-order":
        operations = representation["payload"]["program"]["operations"]
        operations[0], operations[1] = operations[1], operations[0]
    elif case == "operation-operands":
        representation["payload"]["program"]["operations"][1]["qubits"] = [1, 0]
    elif case == "measurement-mapping":
        representation["payload"]["program"]["operations"][-1]["full_register"] = False
    elif case == "backend-profile":
        execution["payload"]["backend_profile"]["requires"]["density_matrix"] = True
    elif case == "implementation-version":
        execution["payload"]["implementation"]["e7q"] = "forged"
    elif case == "execution-proof":
        execution["payload"]["proof"][1]["operator"] = "X"
    elif case == "counts":
        observation["payload"]["counts"]["00"] -= 1
    elif case == "probabilities":
        observation["payload"]["probabilities"]["00"] = 0.75
    elif case == "bit-width":
        observation["payload"]["bit_width"] = 3
    elif case == "label-order":
        observation["payload"]["label_order"] = "clbit-descending"
    elif case == "assessment-check":
        assessment["payload"]["native_result"]["checks"][0]["passed"] = False
    elif case == "assessment-status":
        assessment["payload"]["native_result"]["status"] = "FAIL"
    elif case == "assessment-first-failure":
        assessment["payload"]["native_result"]["first_failure"] = "normalized"
    elif case == "provenance-reference":
        assessment["provenance"]["source_refs"] = [source["artifact_id"]]
    elif case == "profile-capability":
        intent["profile"]["capabilities_required"] = []
    elif case == "transform-criterion":
        transforms["criterion"]["id"] = "forged"
    elif case == "transform-preservation":
        transforms["preserves"] = []
    elif case == "transform-loss":
        transforms["loses"] = []
    elif case == "transform-assumption":
        transforms["assumptions"] = []
    elif case == "validation-status":
        transforms["validation_status"] = "not-assessed"
    elif case == "relation-endpoint":
        transforms["source"] = intent["artifact_id"]
    else:
        raise AssertionError(case)


@pytest.mark.parametrize("case", [
    "source-content", "source-digest", "source-length",
    "intent-path", "intent-normalized", "intent-outcomes", "intent-backend", "intent-shots", "intent-seed",
    "operation-name", "operation-order", "operation-operands", "measurement-mapping",
    "backend-profile", "implementation-version", "execution-proof",
    "counts", "probabilities", "bit-width", "label-order",
    "assessment-check", "assessment-status", "assessment-first-failure",
    "provenance-reference", "profile-capability",
    "transform-criterion", "transform-preservation", "transform-loss", "transform-assumption",
    "validation-status", "relation-endpoint",
])
def test_rehashed_semantic_tampering_never_passes_f2(case):
    graph = deepcopy(execute_native(BELL, created_at=STAMP))
    _tamper(graph, case)
    rehash(graph)
    assert_f2_nonpass(graph)


@pytest.mark.parametrize("old,new,expected", [
    (b"backend: statevector", b"backend: densitymatrix", "UNSUPPORTED"),
    (b"  seed: 7\n", b"", "UNSUPPORTED"),
    (b"shots: 1000", b"shots: 100001", "BLOCKED"),
    (b"  H q[0]", b"  noise depolarizing(0.1) q[0]", "UNSUPPORTED"),
    (b"  H q[0]", b"  if c[0] == 1 X q[0]", "UNSUPPORTED"),
])
def test_rehashed_unsupported_source_never_passes_f2(old, new, expected):
    graph = deepcopy(execute_native(BELL, created_at=STAMP))
    payload = artifact(graph, "source")["payload"]
    raw = payload["content"].encode().replace(old, new)
    payload["content"] = raw.decode()
    payload["byte_length"] = len(raw)
    payload["content_digest"] = "sha256:" + sha256(raw).hexdigest()
    rehash(graph)
    assert_f2_nonpass(graph, expected)


def test_missing_required_relation_never_passes_f2():
    graph = deepcopy(execute_native(BELL, created_at=STAMP))
    graph["relations"].pop()
    rehash(graph)
    assert_f2_nonpass(graph, "FAIL")


def test_unknown_native_source_format_is_unsupported():
    graph = deepcopy(execute_native(BELL, created_at=STAMP))
    artifact(graph, "source")["payload"]["format"] = "unknown-native-format"
    rehash(graph)
    assert_f2_nonpass(graph, "UNSUPPORTED")


def test_historical_core_profile_native_graph_stays_f1_only():
    graph = deepcopy(execute_native(BELL, created_at=STAMP))
    by_kind(graph, "intent").pop("source_trust")
    for item in graph["artifacts"]:
        item["profile"] = {
            "id": "e7q.ir.core", "version": "0alpha1", "capabilities_required": []
        }
    for relation in graph["relations"]:
        relation["validation_status"] = "not-assessed"
    rehash(graph)
    assert validate_graph(graph, level="F0")["status"] == "PASS"
    assert validate_graph(graph, level="F1")["status"] == "PASS"
    assert_f2_nonpass(graph, "BLOCKED")


def test_generic_core_evidence_remains_blocked_at_f2():
    graph = import_evidence(BELL, format="e7q", created_at=STAMP)
    assert validate_graph(graph, level="F0")["status"] == "PASS"
    assert validate_graph(graph, level="F1")["status"] == "PASS"
    assert_f2_nonpass(graph, "BLOCKED")


class BrokenValidator:
    profile_id = PROFILE_ID
    profile_version = PROFILE_VERSION
    validator_id = VALIDATOR_ID

    def __init__(self, mode):
        self.mode = mode

    def _results(self):
        if self.mode == "exception":
            raise RuntimeError("isolated")
        if self.mode == "empty":
            return []
        return [{}]

    def validate_artifact(self, artifact, graph):
        return self._results()

    def validate_relation(self, relation, graph):
        return self._results()


@pytest.mark.parametrize("mode,expected_check,expected_status", [
    ("exception", "e7q.ir.framework.validator-exception", "FAIL"),
    ("malformed", "e7q.ir.framework.validator-result-contract", "FAIL"),
    ("empty", "e7q.ir.framework.no-validator-results", "NOT_ASSESSED"),
])
def test_validator_failure_modes_fail_closed(mode, expected_check, expected_status):
    graph = execute_native(BELL, created_at=STAMP)
    registry = SemanticRegistry()
    registry.register(BrokenValidator(mode))
    report = validate_graph(graph, level="F2", semantic_registry=registry)
    assert report["level_results"]["F2"] == expected_status
    assert report["highest_level_passed"] == "F1"
    assert {item["check_id"] for item in report["semantic_results"]} == {expected_check}


def test_native_context_cache_is_bounded_and_does_not_retain_supplied_graphs():
    _CONTEXT_CACHE.clear()
    for seed in range(_CONTEXT_CACHE_LIMIT + 2):
        raw = BELL.replace(b"seed: 7", f"seed: {seed + 1}".encode())
        execute_native(raw, created_at=STAMP)
    assert len(_CONTEXT_CACHE) == _CONTEXT_CACHE_LIMIT
    assert all("artifacts" not in context for context in _CONTEXT_CACHE.values())
    assert all(set(context) <= {
        "status", "message", "artifact_ids", "expected_payloads", "expected_relations",
        "expected_source_refs", "created_at",
    } for context in _CONTEXT_CACHE.values())
    _CONTEXT_CACHE.clear()


def test_public_native_bell_f2_evidence_is_stable_and_fresh_graph_passes():
    graph = execute_native(BELL, created_at=STAMP)
    report = validate_graph(graph, level="F2")
    assert report["status"] == "PASS"
    assert report["highest_level_passed"] == "F2"

    public_graph = json.loads(PUBLIC_GRAPH.read_text())
    public_report = json.loads(PUBLIC_REPORT.read_text())
    assert PUBLIC_GRAPH.read_bytes() == canonical_bytes(public_graph) + b"\n"
    assert PUBLIC_REPORT.read_bytes() == (
        json.dumps(public_report, indent=2, sort_keys=True).encode() + b"\n"
    )
    assert public_graph["graph_id"] == (
        "sha256:c9fe173151778dcae3df500674a53c063c32119c6b600bfe40c0b82f00e59598"
    )
    assert validate_graph(public_graph, level="F1")["status"] == "PASS"
    subject_ids = {
        item["artifact_id"] for item in public_graph["artifacts"]
    } | {item["relation_id"] for item in public_graph["relations"]}
    artifact_ids = {item["artifact_id"] for item in public_graph["artifacts"]}
    assert public_report["status"] == "PASS"
    assert public_report["highest_level_passed"] == "F2"
    assert len(public_report["semantic_results"]) == 17
    assert all(
        item["status"] == "PASS"
        and item["subject"]["id"] in subject_ids
        and set(item["evidence_refs"]) <= artifact_ids
        for item in public_report["semantic_results"]
    )


def test_cli_native_execution(tmp_path):
    output = tmp_path / "graph.json"
    subprocess.run([
        sys.executable, "-m", "e7q.ir.native", "examples/bell.e7q",
        "--created-at", STAMP, "--output", str(output),
    ], check=True)
    graph = json.loads(output.read_text())
    assert recover_source(graph) == BELL
    assert by_kind(graph, "assessment")["native_result"]["status"] == "PASS"
    assert validate_graph(graph, level="F2")["status"] == "PASS"
