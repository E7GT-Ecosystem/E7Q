# SPDX-License-Identifier: Apache-2.0
import copy
import json
from pathlib import Path

import pytest

from e7q.cli import main
from e7q.language import E7QError
from e7q.ir.canonical import identified_digest
from e7q.ir.conformance import validate_graph
from e7q.ir.envelope import build_artifact
from e7q.ir.graph import build_graph, graph_summary
from e7q.ir.workflow import (
    build_external_circuit_graph,
    load_external_circuit_manifest,
)


EXAMPLE = (
    Path(__file__).parents[1]
    / "examples"
    / "e7q-ir"
    / "external-circuit-workflow.json"
)


def graph():
    manifest, base = load_external_circuit_manifest(EXAMPLE)
    return build_external_circuit_graph(manifest, base)


def test_external_workflow_builds_language_independent_evidence_graph():
    value = graph()
    assert value["schema"] == "e7q.ir.graph/v0alpha1"
    assert [item["kind"] for item in value["artifacts"]] == [
        "source",
        "representation",
        "transformation",
        "execution",
        "observation",
        "assessment",
        "claim",
    ]
    assessment = next(item for item in value["artifacts"] if item["kind"] == "assessment")
    claim = next(item for item in value["artifacts"] if item["kind"] == "claim")
    assert assessment["payload"]["total_variation_distance"] == pytest.approx(0.005)
    assert assessment["payload"]["status"] == "PASS"
    assert claim["payload"]["support_status"] == "supported-within-declared-scope"
    assert validate_graph(value)["status"] == "PASS"


def test_graph_build_is_deterministic_for_pinned_manifest():
    assert graph() == graph()


def test_tampered_artifact_content_fails_f0_identity():
    value = graph()
    value["artifacts"][0]["payload"]["byte_length"] += 1
    report = validate_graph(value, level="F0")
    assert report["status"] == "FAIL"
    assert any(
        item["name"] == "artifact[0]:artifact-id" and not item["passed"]
        for item in report["checks"]
    )


def test_dangling_relation_fails_f1_after_valid_rehash():
    value = graph()
    value["relations"][0]["target"] = "sha256:" + "0" * 64
    value["relations"][0]["relation_id"] = identified_digest(
        value["relations"][0], "relation_id"
    )
    value["graph_id"] = identified_digest(value, "graph_id")
    report = validate_graph(value)
    assert report["level_results"]["F0"] == "PASS"
    assert report["level_results"]["F1"] == "FAIL"
    assert any(
        item["name"] == "relation[0]:references" and not item["passed"]
        for item in report["checks"]
    )


def test_unknown_profile_is_inspectable_but_semantically_blocked():
    artifact = build_artifact(
        "source",
        {"name": "opaque input"},
        profile_id="example.not-installed",
        profile_version="9",
        capabilities_required=["example.unknown-semantics"],
        created_at="2026-09-05T12:00:00Z",
        limitations=["No installed semantic profile."],
    )
    value = build_graph([artifact], [], name="unknown profile")
    report = validate_graph(value)
    assert report["status"] == "PASS"
    assert report["semantic_readiness"] == "BLOCKED"
    assert report["capability_negotiation"][0]["status"] == "BLOCKED"


def test_missing_transformation_contract_fails_closed():
    value = graph()
    transformation = next(
        item for item in value["artifacts"] if item["kind"] == "transformation"
    )
    del transformation["payload"]["loses"]
    transformation["artifact_id"] = identified_digest(transformation, "artifact_id")
    value["graph_id"] = identified_digest(value, "graph_id")
    report = validate_graph(value, level="F0")
    assert report["status"] == "FAIL"
    assert any(
        item["name"].endswith(":transformation-contract") and not item["passed"]
        for item in report["checks"]
    )


def test_malformed_claim_contract_fails_f0():
    value = graph()
    claim = next(item for item in value["artifacts"] if item["kind"] == "claim")
    claim["payload"]["evidence_refs"] = "not-a-reference-list"
    claim["artifact_id"] = identified_digest(claim, "artifact_id")
    value["graph_id"] = identified_digest(value, "graph_id")
    report = validate_graph(value, level="F0")
    assert report["status"] == "FAIL"
    assert any(
        item["name"].endswith(":claim-contract") and not item["passed"]
        for item in report["checks"]
    )


def test_failed_assessment_does_not_support_claim(tmp_path):
    manifest, base = load_external_circuit_manifest(EXAMPLE)
    manifest = copy.deepcopy(manifest)
    manifest["assessment"]["expected_distribution"] = {"01": 1.0}
    value = build_external_circuit_graph(manifest, base)
    assessment = next(item for item in value["artifacts"] if item["kind"] == "assessment")
    claim = next(item for item in value["artifacts"] if item["kind"] == "claim")
    assert assessment["payload"]["status"] == "FAIL"
    assert claim["payload"]["support_status"] == "unsupported"
    assert validate_graph(value)["status"] == "PASS"


def test_summary_is_inventory_not_assurance_verdict():
    summary = graph_summary(graph())
    assert summary["artifact_count"] == 7
    assert summary["relation_count"] == 5
    assert "status" not in summary


def test_e7q_ir_cli_build_validate_and_inspect(tmp_path):
    graph_path = tmp_path / "graph.json"
    report_path = tmp_path / "conformance.json"
    summary_path = tmp_path / "summary.json"
    assert main(["ir", "build", str(EXAMPLE), "-o", str(graph_path)]) == 0
    assert main([
        "ir", "validate", str(graph_path), "--level", "F1",
        "-o", str(report_path),
    ]) == 0
    assert main(["ir", "inspect", str(graph_path), "-o", str(summary_path)]) == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert report["highest_level_passed"] == "F1"
    assert report["level_results"]["F2"] == "NOT_IMPLEMENTED"
    assert summary["artifact_kinds"]["claim"] == 1


def test_manifest_file_paths_cannot_escape_manifest_directory(tmp_path):
    manifest, _ = load_external_circuit_manifest(EXAMPLE)
    manifest = copy.deepcopy(manifest)
    manifest["source"]["path"] = "../outside.qasm"
    with pytest.raises(E7QError, match="escapes the manifest directory"):
        build_external_circuit_graph(manifest, tmp_path / "manifest")


def test_declared_shots_must_match_count_total(tmp_path):
    qasm = "OPENQASM 2.0;\nqreg q[1];\ncreg c[1];\nmeasure q -> c;\n"
    (tmp_path / "source.qasm").write_text(qasm, encoding="utf-8")
    (tmp_path / "transpiled.qasm").write_text(qasm, encoding="utf-8")
    (tmp_path / "counts.json").write_text(
        json.dumps({"shots": 2, "counts": {"0": 1}}), encoding="utf-8"
    )
    manifest, _ = load_external_circuit_manifest(EXAMPLE)
    with pytest.raises(E7QError, match="declared shots"):
        build_external_circuit_graph(manifest, tmp_path)
