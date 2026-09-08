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
from e7q.ir.semantic import SemanticRegistry, SemanticResult
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
F2_GOLDEN = (
    Path(__file__).parents[1]
    / "examples"
    / "e7q-ir"
    / "f2-framework-not-assessed.json"
)


def graph():
    manifest, base = load_external_circuit_manifest(EXAMPLE)
    return build_external_circuit_graph(manifest, base)


class PassValidator:
    profile_id = "e7q.ir.circuit-basic"
    profile_version = "0alpha1"
    validator_id = "e7q.ir.validator.circuit-basic/0alpha1"

    def validate_artifact(self, artifact, graph_value):
        del graph_value
        return [
            SemanticResult(
                check_id=f"test.artifact.{artifact['kind']}",
                status="PASS",
                subject_kind="artifact",
                subject_id=artifact["artifact_id"],
                profile_id=self.profile_id,
                profile_version=self.profile_version,
                evidence_refs=(artifact["artifact_id"],),
                message="Test validator passed the declared fixture rule.",
            )
        ]

    def validate_relation(self, relation, graph_value):
        del graph_value
        return [
            SemanticResult(
                check_id=f"test.relation.{relation['kind']}",
                status="PASS",
                subject_kind="relation",
                subject_id=relation["relation_id"],
                profile_id=self.profile_id,
                profile_version=self.profile_version,
                evidence_refs=(relation["source"], relation["target"]),
                message="Test validator passed the declared fixture rule.",
            )
        ]


class UnsupportedValidator(PassValidator):
    def validate_relation(self, relation, graph_value):
        results = list(super().validate_relation(relation, graph_value))
        if relation["kind"] == "transforms":
            result = results[0]
            return [
                SemanticResult(
                    check_id="test.transformation.unsupported",
                    status="UNSUPPORTED",
                    subject_kind=result.subject_kind,
                    subject_id=result.subject_id,
                    profile_id=result.profile_id,
                    profile_version=result.profile_version,
                    evidence_refs=result.evidence_refs,
                    message="The test criterion is outside this validator domain.",
                )
            ]
        return results


class MalformedValidator(PassValidator):
    def validate_artifact(self, artifact, graph_value):
        del artifact, graph_value
        return [{"status": "PASS"}]


class ExcessiveValidator(PassValidator):
    def validate_artifact(self, artifact, graph_value):
        del graph_value
        for index in range(129):
            yield SemanticResult(
                check_id=f"test.excessive.{index}",
                status="PASS",
                subject_kind="artifact",
                subject_id=artifact["artifact_id"],
                profile_id=self.profile_id,
                profile_version=self.profile_version,
                evidence_refs=(artifact["artifact_id"],),
                message="Synthetic result used to exercise the framework limit.",
            )


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


def test_unknown_profile_is_f2_blocked_after_f0_f1_inspection():
    artifact = build_artifact(
        "source",
        {"name": "opaque input"},
        profile_id="example.not-installed",
        profile_version="9",
        capabilities_required=["example.unknown-semantics"],
        created_at="2026-09-05T12:00:00Z",
        limitations=["No installed semantic profile."],
    )
    report = validate_graph(
        build_graph([artifact], [], name="unknown profile"), level="F2"
    )
    assert report["status"] == "BLOCKED"
    assert report["highest_level_passed"] == "F1"
    assert report["level_results"]["F2"] == "BLOCKED"
    assert report["semantic_results"][0]["status"] == "BLOCKED"


def test_unsupported_required_capability_blocks_f2_before_validator():
    artifact = build_artifact(
        "source",
        {"name": "future circuit input"},
        profile_id="e7q.ir.circuit-basic",
        profile_version="0alpha1",
        capabilities_required=["circuit.future-semantics"],
        created_at="2026-09-05T12:00:00Z",
        limitations=["Required capability is not installed."],
    )
    report = validate_graph(
        build_graph([artifact], [], name="unsupported capability"), level="F2"
    )
    assert report["status"] == "BLOCKED"
    assert report["level_results"]["F2"] == "BLOCKED"
    assert report["semantic_results"][0]["check_id"] == (
        "e7q.ir.framework.capability-negotiation-blocked"
    )


def test_phase_1a_keeps_current_circuit_semantics_not_assessed():
    report = validate_graph(graph(), level="F2")
    assert report["status"] == "BLOCKED"
    assert report["highest_level_passed"] == "F1"
    assert report["level_results"]["F2"] == "BLOCKED"
    assert len(report["semantic_results"]) == 12
    transformation = next(
        item
        for item in report["semantic_results"]
        if item["subject"]["kind"] == "relation" and "criterion" in item
    )
    assert transformation["status"] == "NOT_ASSESSED"
    assert transformation["criterion"]["id"] == "declared-computational-basis-behaviour"
    assert json.loads(F2_GOLDEN.read_text(encoding='utf-8'))['status'] == 'NOT_ASSESSED'  # historical Phase 1A fixture


def test_f2_pass_requires_every_registered_semantic_check_to_pass():
    registry = SemanticRegistry()
    registry.register(PassValidator())
    report = validate_graph(graph(), level="F2", semantic_registry=registry)
    assert report["status"] == "PASS"
    assert report["highest_level_passed"] == "F2"
    assert report["level_results"]["F2"] == "PASS"
    assert all(item["status"] == "PASS" for item in report["semantic_results"])
    assert all(item["result_id"].startswith("sha256:") for item in report["semantic_results"])


def test_unsupported_semantic_domain_is_not_reported_as_failure_or_pass():
    registry = SemanticRegistry()
    registry.register(UnsupportedValidator())
    report = validate_graph(graph(), level="F2", semantic_registry=registry)
    assert report["status"] == "UNSUPPORTED"
    assert report["level_results"]["F2"] == "UNSUPPORTED"
    assert any(item["status"] == "UNSUPPORTED" for item in report["semantic_results"])


def test_malformed_validator_result_fails_deterministically():
    registry = SemanticRegistry()
    registry.register(MalformedValidator())
    first = validate_graph(graph(), level="F2", semantic_registry=registry)
    second = validate_graph(graph(), level="F2", semantic_registry=registry)
    assert first == second
    assert first["status"] == "FAIL"
    assert any(
        item["check_id"] == "e7q.ir.framework.validator-result-contract"
        for item in first["semantic_results"]
    )


def test_validator_result_limit_blocks_semantic_promotion():
    registry = SemanticRegistry()
    registry.register(ExcessiveValidator())
    report = validate_graph(graph(), level="F2", semantic_registry=registry)
    assert report["status"] == "BLOCKED"
    assert any(
        item["check_id"] == "e7q.ir.framework.validator-result-limit"
        for item in report["semantic_results"]
    )


def test_malformed_profile_payload_prevents_f2_assessment():
    artifact = build_artifact(
        "source",
        {"name": "malformed profile"},
        created_at="2026-09-05T12:00:00Z",
        limitations=["Invalid fixture."],
    )
    artifact["profile"]["capabilities_required"] = "not-a-list"
    artifact["artifact_id"] = identified_digest(artifact, "artifact_id")
    report = validate_graph(
        build_graph([artifact], [], name="malformed profile"), level="F2"
    )
    assert report["status"] == "FAIL"
    assert report["level_results"]["F0"] == "FAIL"
    assert report["level_results"]["F2"] == "NOT_ASSESSED"
    assert report["semantic_results"] == []


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


@pytest.mark.parametrize("subject_kind", ["artifact", "relation"])
def test_contradictory_transformation_declarations_fail_f0(subject_kind):
    value = graph()
    if subject_kind == "artifact":
        subject = next(
            item for item in value["artifacts"] if item["kind"] == "transformation"
        )
        declarations = subject["payload"]
        id_field = "artifact_id"
    else:
        subject = next(item for item in value["relations"] if item["kind"] == "transforms")
        declarations = subject
        id_field = "relation_id"
    declarations["loses"] = list(declarations["preserves"])
    subject[id_field] = identified_digest(subject, id_field)
    value["graph_id"] = identified_digest(value, "graph_id")
    report = validate_graph(value, level="F0")
    assert report["status"] == "FAIL"
    assert any(
        item["name"].endswith(":transformation-contract") and not item["passed"]
        for item in report["checks"]
    )


def test_duplicate_transformation_declarations_fail_f0():
    value = graph()
    relation = next(item for item in value["relations"] if item["kind"] == "transforms")
    relation["assumptions"] = relation["assumptions"] * 2
    relation["relation_id"] = identified_digest(relation, "relation_id")
    value["graph_id"] = identified_digest(value, "graph_id")
    report = validate_graph(value, level="F0")
    assert report["status"] == "FAIL"


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


def test_e7q_ir_cli_f2_preserves_not_assessed_exit_and_report(tmp_path):
    graph_path = tmp_path / "graph.json"
    report_path = tmp_path / "f2.json"
    graph_path.write_text(json.dumps(graph()), encoding="utf-8")
    assert main([
        "ir", "validate", str(graph_path), "--level", "F2",
        "-o", str(report_path),
    ]) == 1
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "BLOCKED"
    assert report["level_results"]["F2"] == "BLOCKED"


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
