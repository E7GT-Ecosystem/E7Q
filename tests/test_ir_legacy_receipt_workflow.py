# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from base64 import b64encode
import copy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

import pytest

from e7q.bundles import build_execution_bundle
from e7q.ir.canonical import digest, identified_digest
from e7q.ir.conformance import validate_graph
from e7q.ir.legacy_receipt_workflow import (
    ASSESSMENT_FORMAT,
    CLAIM_TYPE,
    EXECUTION_FORMAT,
    INTENT_FORMAT,
    OBSERVATION_FORMAT,
    REPRESENTATION_FORMAT,
    SOURCE_ADAPTER,
    TRANSFORMATION_FORMAT,
    build_legacy_receipt_graph,
    recover_legacy_source,
    validate_legacy_receipt_evidence,
)
from e7q.language import parse
from e7q.results import build_execution_receipt

STAMP = "2026-09-08T00:00:00Z"
REFS = {
    "bundle": "fixture:legacy-receipt:bundle",
    "result": "fixture:legacy-receipt:result",
    "receipt": "fixture:legacy-receipt:receipt",
}
SOURCE = b"""context LegacyReceipt {\n  shots: 8\n  backend: statevector\n  seed: 7\n}\n\nqubits q[2]\nbits c[2]\n\ninvariant normalized\ninvariant outcomes in {00, 11}\n\npath Prepare {\n  H q[0]\n  CX q[0], q[1]\n  measure q -> c\n}\n\nverify Prepare\n"""


def _raw_digest(raw: bytes) -> str:
    return "sha256:" + sha256(raw).hexdigest()


def snapshot():
    return {
        "schema": "e7q.calibration/v1",
        "captured_at": "2026-09-08T00:00:00Z",
        "targets": [{
            "name": "synthetic-offline-target",
            "qubits": 2,
            "topology": "linear",
            "native_gates": ["H", "CX", "SWAP"],
            "available": True,
            "queue_depth": 0,
            "single_qubit_error": 0.001,
            "two_qubit_error": 0.01,
            "readout_error": 0.02,
        }],
    }


def _encode(value) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _fixture_bytes():
    bundle = build_execution_bundle(parse(SOURCE.decode()), SOURCE, snapshot(), shots=8)
    bundle["vendor_bundle_extension"] = {
        "retained": True,
        "limitation": "synthetic unknown field",
    }
    bundle_raw = _encode(bundle)
    result = {
        "schema": "e7q.execution-result/v1",
        "provider": "synthetic-provider-declaration",
        "job_id": "synthetic-job-declaration",
        "target": bundle["target"],
        "shots": 8,
        "counts": {"00": 4, "01": 0, "11": 4},
        "completed_at": "2026-09-08T00:01:00Z",
        "bundle_digest": _raw_digest(bundle_raw),
        "vendor_result_extension": {"retained": True},
    }
    result_raw = _encode(result)
    receipt = build_execution_receipt(
        bundle,
        bundle_raw,
        result,
        result_raw,
        include_observational_claim_pilot=True,
        include_temporal_orientation_pilot=True,
    )
    receipt["vendor_receipt_extension"] = {"retained": True}
    receipt_raw = _encode(receipt)
    return bundle, bundle_raw, result, result_raw, receipt, receipt_raw


def _write_inputs(
    tmp_path: Path,
    *,
    bundle_raw: bytes | None = None,
    result_raw: bytes | None = None,
    receipt_raw: bytes | None = None,
):
    _, default_bundle, _, default_result, _, default_receipt = _fixture_bytes()
    values = {
        "bundle": bundle_raw if bundle_raw is not None else default_bundle,
        "result": result_raw if result_raw is not None else default_result,
        "receipt": receipt_raw if receipt_raw is not None else default_receipt,
    }
    paths = {}
    for role, raw in values.items():
        path = tmp_path / f"{role}.json"
        path.write_bytes(raw)
        paths[role] = path
    return paths, values


def _build(tmp_path: Path, **overrides):
    paths, values = _write_inputs(tmp_path, **overrides)
    graph = build_legacy_receipt_graph(
        paths["bundle"],
        paths["result"],
        paths["receipt"],
        count_label_order="clbit-descending",
        created_at=STAMP,
        bundle_source_ref=REFS["bundle"],
        result_source_ref=REFS["result"],
        receipt_source_ref=REFS["receipt"],
    )
    return graph, paths, values


def _artifact(graph, *, kind=None, format=None, role=None, name=None):
    matches = []
    for artifact in graph["artifacts"]:
        payload = artifact["payload"]
        if kind is not None and artifact["kind"] != kind:
            continue
        if format is not None and payload.get("format") != format:
            continue
        if role is not None and payload.get("role") != role:
            continue
        if name is not None and payload.get("name") != name:
            continue
        matches.append(artifact)
    assert len(matches) == 1
    return matches[0]


def _assessment(graph):
    return _artifact(graph, format=ASSESSMENT_FORMAT)["payload"]


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


def test_valid_bundle_result_receipt_builds_strictly_bounded_mapping(tmp_path):
    graph, _, _ = _build(tmp_path)
    assert validate_legacy_receipt_evidence(graph)["status"] == "PASS"
    assert graph["extensions"]["assessment_status"] == "PASS"
    intent = _artifact(graph, format=INTENT_FORMAT)["payload"]
    execution = _artifact(graph, format=EXECUTION_FORMAT)["payload"]
    observation = _artifact(graph, format=OBSERVATION_FORMAT)["payload"]
    assessment = _assessment(graph)
    claim = _claim(graph)

    assert intent["selected_target"] == "synthetic-offline-target"
    assert intent["requested_shots"] == 8
    assert intent["declared_source_digest"].startswith("sha256:")
    assert intent["declared_openqasm_digest"].startswith("sha256:")
    assert intent["computed_compiled_content_digest"].startswith("sha256:")
    assert intent["submission_status"] == "not-submitted"
    assert execution["provider_declaration"] == "synthetic-provider-declaration"
    assert execution["job_id_declaration"] == "synthetic-job-declaration"
    assert execution["authentication_status"] == "not-authenticated"
    assert execution["chronology_status"] == "provider-reported-not-authenticated"
    assert observation["count_label_order"] == "clbit-descending"
    assert observation["outcome_sequence"] == ["00", "01", "11"]
    assert observation["outcome_width"] == 2
    assert observation["zero_count_outcomes"] == ["01"]
    assert observation["empirical_probabilities"] == {"00": 0.5, "01": 0.0, "11": 0.5}
    assert assessment["outcome"]["receipt_consistency_established"] is True
    assert assessment["outcome"]["execution_authenticity_established"] is False
    assert claim["claim_type"] == CLAIM_TYPE
    assert claim["support_status"] == "supported-within-declared-scope"
    assert "execution authenticity" in " ".join(claim["prohibited_inferences"]).lower()


def test_every_input_is_byte_perfectly_recoverable_and_complete_object_is_retained(tmp_path):
    graph, _, values = _build(tmp_path)
    for role in ("bundle", "result", "receipt"):
        assert recover_legacy_source(graph, REFS[role]) == values[role]
        representation = _artifact(graph, format=REPRESENTATION_FORMAT, role=role)["payload"]
        assert representation["complete_original_object"] == json.loads(values[role])
        assert representation["content_identity"].startswith("sha256:")
    assert "vendor_bundle_extension" in _artifact(graph, format=REPRESENTATION_FORMAT, role="bundle")["payload"]["unknown_fields"]
    assert "vendor_result_extension" in _artifact(graph, format=REPRESENTATION_FORMAT, role="result")["payload"]["unknown_fields"]
    receipt_rep = _artifact(graph, format=REPRESENTATION_FORMAT, role="receipt")["payload"]
    assert "vendor_receipt_extension" in receipt_rep["unknown_fields"]
    assert receipt_rep["legacy_proof"] == json.loads(values["receipt"])["proof"]


def test_fixed_sources_metadata_graph_artifacts_transformations_and_relations_are_deterministic(tmp_path):
    first, _, _ = _build(tmp_path)
    other = tmp_path / "other"
    other.mkdir()
    second, _, _ = _build(other)
    assert first["graph_id"] == second["graph_id"]
    assert first["extensions"]["workflow_request_id"] == second["extensions"]["workflow_request_id"]
    assert [artifact["artifact_id"] for artifact in first["artifacts"]] == [artifact["artifact_id"] for artifact in second["artifacts"]]
    assert [relation["relation_id"] for relation in first["relations"]] == [relation["relation_id"] for relation in second["relations"]]
    transformations = [
        artifact["payload"] for artifact in first["artifacts"]
        if artifact["payload"].get("format") == TRANSFORMATION_FORMAT
    ]
    assert len(transformations) == 4
    assert all(item["transformation_id"].startswith("sha256:") for item in transformations)
    assert all(item["input_refs"] and item["output_refs"] for item in transformations)
    assert all(item["criterion"]["version"] == "1" for item in transformations)


def test_f0_f1_pass_while_default_f2_remains_non_pass(tmp_path):
    graph, _, _ = _build(tmp_path)
    report = validate_graph(graph, level="F2")
    assert report["level_results"]["F0"] == "PASS"
    assert report["level_results"]["F1"] == "PASS"
    assert report["level_results"]["F2"] != "PASS"
    assert report["highest_level_passed"] == "F1"


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("target", "different-target", "target_mismatch"),
        ("shots", 9, "shot_mismatch"),
        ("bundle_digest", "sha256:" + "0" * 64, "bundle_digest_mismatch"),
    ],
)
def test_target_shot_and_bundle_digest_mismatches_fail_closed(tmp_path, field, value, reason):
    _, bundle_raw, result, _, _, receipt_raw = _fixture_bytes()
    result[field] = value
    result_raw = _encode(result)
    graph, _, _ = _build(tmp_path, bundle_raw=bundle_raw, result_raw=result_raw, receipt_raw=receipt_raw)
    assert _assessment(graph)["outcome"]["status"] == "FAIL"
    assert _assessment(graph)["outcome"]["reason"] == reason
    assert reason in _assessment(graph)["failure_reasons"]
    assert _claim(graph)["support_status"] == "unsupported"


@pytest.mark.parametrize(
    "counts",
    [
        {"0": 4, "11": 4},
        {"00": 4, "2x": 4},
        {"00": 4, "11": -1, "01": 5},
        {"00": 4.0, "11": 4},
        {},
    ],
)
def test_malformed_outcomes_and_inconsistent_widths_are_unsupported(tmp_path, counts):
    _, bundle_raw, result, _, _, receipt_raw = _fixture_bytes()
    result["counts"] = counts
    graph, _, _ = _build(
        tmp_path,
        bundle_raw=bundle_raw,
        result_raw=_encode(result),
        receipt_raw=receipt_raw,
    )
    assert _assessment(graph)["outcome"]["status"] == "UNSUPPORTED"
    assert "malformed_counts" in _assessment(graph)["failure_reasons"]
    assert _claim(graph)["support_status"] == "unsupported"


def test_unsupported_or_conflicting_count_label_semantics_are_non_pass(tmp_path):
    paths, _ = _write_inputs(tmp_path)
    unsupported = build_legacy_receipt_graph(
        paths["bundle"], paths["result"], paths["receipt"],
        count_label_order="provider-native-magic-order",
        created_at=STAMP,
        bundle_source_ref=REFS["bundle"],
        result_source_ref=REFS["result"],
        receipt_source_ref=REFS["receipt"],
    )
    assert _assessment(unsupported)["outcome"]["status"] == "UNSUPPORTED"
    assert _claim(unsupported)["support_status"] == "unsupported"

    _, bundle_raw, result, _, _, receipt_raw = _fixture_bytes()
    result["label_order"] = "clbit-ascending"
    conflict_dir = tmp_path / "conflict"
    conflict_dir.mkdir()
    conflict, _, _ = _build(
        conflict_dir,
        bundle_raw=bundle_raw,
        result_raw=_encode(result),
        receipt_raw=receipt_raw,
    )
    assert _assessment(conflict)["outcome"]["status"] == "UNSUPPORTED"
    assert "unsupported_count_label_semantics" in _assessment(conflict)["failure_reasons"]


def test_duplicate_keys_non_finite_values_and_unknown_schemas_are_unsupported(tmp_path):
    _, bundle_raw, result, result_raw, _, receipt_raw = _fixture_bytes()
    duplicate = result_raw.replace(b'"shots": 8,', b'"shots": 8,\n  "shots": 8,', 1)
    graph, _, _ = _build(tmp_path, bundle_raw=bundle_raw, result_raw=duplicate, receipt_raw=receipt_raw)
    assert _assessment(graph)["outcome"]["status"] == "UNSUPPORTED"

    nonfinite_dir = tmp_path / "nonfinite"
    nonfinite_dir.mkdir()
    result["vendor_nonfinite"] = float("nan")
    nonfinite = json.dumps(result, sort_keys=True, allow_nan=True).encode()
    graph, _, _ = _build(nonfinite_dir, bundle_raw=bundle_raw, result_raw=nonfinite, receipt_raw=receipt_raw)
    assert _assessment(graph)["outcome"]["status"] == "UNSUPPORTED"

    unknown_dir = tmp_path / "unknown"
    unknown_dir.mkdir()
    result = json.loads(result_raw)
    result["schema"] = "vendor.execution-result/v99"
    graph, _, _ = _build(unknown_dir, bundle_raw=bundle_raw, result_raw=_encode(result), receipt_raw=receipt_raw)
    assert _assessment(graph)["outcome"]["status"] == "UNSUPPORTED"
    assert _claim(graph)["support_status"] == "unsupported"

    missing_dir = tmp_path / "missing"
    missing_dir.mkdir()
    result.pop("schema")
    graph, _, _ = _build(missing_dir, bundle_raw=bundle_raw, result_raw=_encode(result), receipt_raw=receipt_raw)
    assert _assessment(graph)["outcome"]["status"] == "UNSUPPORTED"
    assert "result_not_admitted" in _assessment(graph)["failure_reasons"]


def test_forged_legacy_pass_and_tampered_probabilities_or_proof_fail(tmp_path):
    _, bundle_raw, _, result_raw, receipt, _ = _fixture_bytes()
    variants = []
    forged = copy.deepcopy(receipt)
    forged["bundle_digest"] = "sha256:" + "f" * 64
    forged["status"] = "PASS"
    variants.append(forged)
    probabilities = copy.deepcopy(receipt)
    probabilities["probabilities"]["00"] = 0.75
    variants.append(probabilities)
    proof = copy.deepcopy(receipt)
    proof["proof"][2]["count_total"] = 7
    variants.append(proof)
    for index, variant in enumerate(variants):
        root = tmp_path / str(index)
        root.mkdir()
        graph, _, _ = _build(root, bundle_raw=bundle_raw, result_raw=result_raw, receipt_raw=_encode(variant))
        assert _assessment(graph)["outcome"]["status"] == "FAIL"
        assert _assessment(graph)["outcome"]["reason"] == "supplied_receipt_semantics_mismatch"
        assert _claim(graph)["support_status"] == "unsupported"


@pytest.mark.parametrize("legacy_status", ["FAIL", "BLOCKED", "UNSUPPORTED", "NOT_ASSESSED"])
def test_failed_or_inconclusive_legacy_status_is_retained(legacy_status, tmp_path):
    _, bundle_raw, _, result_raw, receipt, _ = _fixture_bytes()
    receipt["status"] = legacy_status
    graph, _, _ = _build(tmp_path, bundle_raw=bundle_raw, result_raw=result_raw, receipt_raw=_encode(receipt))
    assert _assessment(graph)["outcome"]["status"] == legacy_status
    assert _assessment(graph)["outcome"]["reason"] == "supplied_receipt_non_pass"
    assert _claim(graph)["support_status"] == "unsupported"
    assert validate_legacy_receipt_evidence(graph)["status"] == legacy_status


def test_optional_temporal_and_observational_records_do_not_inflate_claim(tmp_path):
    graph, _, _ = _build(tmp_path)
    observation = _artifact(graph, format=OBSERVATION_FORMAT)["payload"]
    optional = observation["optional_supplied_records"]
    assert optional["temporal_evidence"] is not None
    assert optional["observational_claim_pilot"] is not None
    assert optional["temporal_orientation_pilot"] is not None
    assert optional["claim_effect"] == "none"
    outcome = _assessment(graph)["outcome"]
    assert outcome["provider_identity_authenticated"] is False
    assert outcome["chronology_authenticated"] is False
    assert outcome["physical_fidelity_established"] is False


def test_rehashed_receipt_source_tampering_is_detected_after_f1(tmp_path):
    graph, _, _ = _build(tmp_path)
    graph = copy.deepcopy(graph)
    source = _artifact(graph, kind="source", role="receipt")
    _, _, _, _, receipt, _ = _fixture_bytes()
    receipt["probabilities"]["00"] = 0.75
    altered = _encode(receipt)
    source["payload"]["content_base64"] = b64encode(altered).decode("ascii")
    source["payload"]["content_digest"] = _raw_digest(altered)
    source["payload"]["byte_length"] = len(altered)
    _rehash(graph)
    assert validate_graph(graph, level="F1")["status"] == "PASS"
    assert validate_legacy_receipt_evidence(graph)["status"] == "FAIL"


def test_rehashed_typed_receipt_representation_tampering_is_detected(tmp_path):
    graph, _, _ = _build(tmp_path)
    graph = copy.deepcopy(graph)
    representation = _artifact(graph, format=REPRESENTATION_FORMAT, role="receipt")
    representation["payload"]["complete_original_object"]["proof"][2]["count_total"] = 7
    representation["payload"]["legacy_proof"][2]["count_total"] = 7
    representation["payload"]["content_identity"] = digest({
        "format": "e7q.legacy-json-object-content/v1",
        "role": "receipt",
        "object": representation["payload"]["complete_original_object"],
    })
    _rehash(graph)
    assert validate_graph(graph, level="F1")["status"] == "PASS"
    assert validate_legacy_receipt_evidence(graph)["status"] == "FAIL"


def test_no_imported_or_inconclusive_verdict_alone_can_produce_f2_pass(tmp_path):
    _, bundle_raw, _, result_raw, receipt, _ = _fixture_bytes()
    receipt["status"] = "NOT_ASSESSED"
    graph, _, _ = _build(tmp_path, bundle_raw=bundle_raw, result_raw=result_raw, receipt_raw=_encode(receipt))
    assert _artifact(graph, format=REPRESENTATION_FORMAT, role="receipt")["payload"]["legacy_status"] == "NOT_ASSESSED"
    assert _assessment(graph)["outcome"]["status"] == "NOT_ASSESSED"
    assert _claim(graph)["support_status"] == "unsupported"
    assert validate_graph(graph, level="F2")["level_results"]["F2"] != "PASS"


def test_cli_never_overwrites_an_input_file(tmp_path):
    _, paths, values = _build(tmp_path)
    before = values["bundle"]
    completed = subprocess.run(
        [
            sys.executable, "-m", "e7q.ir.legacy_receipt_workflow",
            str(paths["bundle"]),
            "--result", str(paths["result"]),
            "--receipt", str(paths["receipt"]),
            "--count-label-order", "clbit-descending",
            "--created-at", STAMP,
            "--bundle-source-ref", REFS["bundle"],
            "--result-source-ref", REFS["result"],
            "--receipt-source-ref", REFS["receipt"],
            "--output", str(paths["bundle"]),
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 2
    assert "must not overwrite" in completed.stderr
    assert paths["bundle"].read_bytes() == before
