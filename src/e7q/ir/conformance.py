# SPDX-License-Identifier: Apache-2.0
"""F0 structural, F1 referential, and F2 semantic conformance orchestration."""
from __future__ import annotations

import re
from typing import Any

from .canonical import identified_digest
from .envelope import KINDS, SCHEMA as ARTIFACT_SCHEMA
from .graph import RELATION_KINDS, SCHEMA as GRAPH_SCHEMA
from .profiles import negotiate
from .semantic import DEFAULT_REGISTRY, SemanticRegistry, validate_semantics


_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_LEVELS = {"F0": 0, "F1": 1, "F2": 2}
_SUPPORT_STATUSES = {
    "supported-within-declared-scope",
    "unsupported",
    "conflicting",
    "insufficient-evidence",
}
_VALIDATION_STATUSES = {
    "declared-not-verified",
    "validated",
    "failed",
    "not-assessed",
    "supported",
}


def _check(checks: list[dict[str, Any]], name: str, passed: bool, **details: Any) -> None:
    checks.append({"name": name, "passed": bool(passed), **details})


def _string_list(value: Any, *, nonempty: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (bool(value) or not nonempty)
        and all(isinstance(item, str) and bool(item) for item in value)
    )


def _reference_list(value: Any, *, nonempty: bool = False) -> bool:
    return _string_list(value, nonempty=nonempty) and all(
        bool(_DIGEST.fullmatch(item)) for item in value
    )


def _transformation_declarations_are_consistent(value: dict[str, Any]) -> bool:
    fields = ("preserves", "loses", "assumptions")
    declarations = [value.get(field) for field in fields]
    return (
        all(_string_list(items) and len(items) == len(set(items)) for items in declarations)
        and not (set(declarations[0]) & set(declarations[1]))
    )


def _artifact_checks(value: Any, index: int) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    prefix = f"artifact[{index}]"
    if not isinstance(value, dict):
        _check(checks, f"{prefix}:object", False)
        return checks
    allowed = {
        "schema", "artifact_id", "kind", "profile", "provenance",
        "payload", "limitations", "extensions",
    }
    required = allowed - {"extensions"}
    _check(checks, f"{prefix}:fields", required <= value.keys())
    _check(checks, f"{prefix}:unknown-fields", not (value.keys() - allowed))
    _check(checks, f"{prefix}:schema", value.get("schema") == ARTIFACT_SCHEMA)
    _check(checks, f"{prefix}:kind", value.get("kind") in KINDS)
    artifact_id = value.get("artifact_id")
    _check(
        checks,
        f"{prefix}:artifact-id-format",
        isinstance(artifact_id, str) and bool(_DIGEST.fullmatch(artifact_id)),
    )
    try:
        expected = identified_digest(value, "artifact_id")
    except (TypeError, ValueError):
        expected = None
    _check(checks, f"{prefix}:artifact-id", artifact_id == expected)
    profile = value.get("profile")
    profile_ok = (
        isinstance(profile, dict)
        and set(profile) == {"id", "version", "capabilities_required"}
        and isinstance(profile.get("id"), str)
        and bool(profile.get("id"))
        and isinstance(profile.get("version"), str)
        and bool(profile.get("version"))
        and _string_list(profile.get("capabilities_required"))
        and len(profile.get("capabilities_required", []))
        == len(set(profile.get("capabilities_required", [])))
    )
    _check(checks, f"{prefix}:profile", profile_ok)
    provenance = value.get("provenance")
    provenance_ok = (
        isinstance(provenance, dict)
        and set(provenance) == {"created_at", "actor", "source_refs"}
        and isinstance(provenance.get("created_at"), str)
        and bool(provenance.get("created_at"))
        and isinstance(provenance.get("actor"), str)
        and bool(provenance.get("actor"))
        and _reference_list(provenance.get("source_refs"))
    )
    _check(checks, f"{prefix}:provenance", provenance_ok)
    _check(checks, f"{prefix}:payload", isinstance(value.get("payload"), dict))
    _check(checks, f"{prefix}:limitations", _string_list(value.get("limitations")))
    if "extensions" in value:
        _check(checks, f"{prefix}:extensions", isinstance(value["extensions"], dict))
    if value.get("kind") == "transformation" and isinstance(value.get("payload"), dict):
        payload = value["payload"]
        required_transformation = {
            "input_refs", "output_refs", "criterion",
            "preserves", "loses", "assumptions",
        }
        transformation_ok = (
            required_transformation <= payload.keys()
            and _reference_list(payload.get("input_refs"), nonempty=True)
            and _reference_list(payload.get("output_refs"), nonempty=True)
            and isinstance(payload.get("criterion"), dict)
            and bool(payload.get("criterion"))
            and _transformation_declarations_are_consistent(payload)
            and payload.get("validation_status") in _VALIDATION_STATUSES
        )
        _check(checks, f"{prefix}:transformation-contract", transformation_ok)
    if value.get("kind") == "claim" and isinstance(value.get("payload"), dict):
        payload = value["payload"]
        required_claim = {
            "statement", "claim_type", "evidence_refs", "support_status",
            "boundaries", "prohibited_inferences",
        }
        claim_ok = (
            required_claim <= payload.keys()
            and isinstance(payload.get("statement"), str)
            and bool(payload.get("statement"))
            and isinstance(payload.get("claim_type"), str)
            and bool(payload.get("claim_type"))
            and _reference_list(payload.get("evidence_refs"), nonempty=True)
            and payload.get("support_status") in _SUPPORT_STATUSES
            and _string_list(payload.get("boundaries"), nonempty=True)
            and _string_list(payload.get("prohibited_inferences"), nonempty=True)
        )
        _check(checks, f"{prefix}:claim-contract", claim_ok)
    return checks


def validate_graph(
    graph: Any,
    *,
    level: str = "F1",
    semantic_registry: SemanticRegistry = DEFAULT_REGISTRY,
) -> dict[str, Any]:
    if level not in _LEVELS:
        raise ValueError(f"unsupported E7Q-IR conformance level: {level}")
    f0: list[dict[str, Any]] = []
    _check(f0, "graph:object", isinstance(graph, dict))
    if not isinstance(graph, dict):
        return _report(level, f0, [], [], "NOT_ASSESSED", [])
    allowed = {"schema", "graph_id", "name", "artifacts", "relations", "extensions"}
    required = allowed - {"extensions"}
    _check(f0, "graph:fields", required <= graph.keys())
    _check(f0, "graph:unknown-fields", not (graph.keys() - allowed))
    _check(f0, "graph:schema", graph.get("schema") == GRAPH_SCHEMA)
    _check(f0, "graph:name", isinstance(graph.get("name"), str) and bool(graph.get("name")))
    artifacts = graph.get("artifacts")
    relations = graph.get("relations")
    _check(f0, "graph:artifacts", isinstance(artifacts, list) and bool(artifacts))
    _check(f0, "graph:relations", isinstance(relations, list))
    if isinstance(artifacts, list):
        for index, artifact in enumerate(artifacts):
            f0.extend(_artifact_checks(artifact, index))
    if isinstance(relations, list):
        for index, relation in enumerate(relations):
            prefix = f"relation[{index}]"
            relation_ok = isinstance(relation, dict)
            _check(f0, f"{prefix}:object", relation_ok)
            if not relation_ok:
                continue
            _check(f0, f"{prefix}:kind", relation.get("kind") in RELATION_KINDS)
            endpoints_ok = (
                isinstance(relation.get("source"), str)
                and bool(_DIGEST.fullmatch(relation.get("source", "")))
                and isinstance(relation.get("target"), str)
                and bool(_DIGEST.fullmatch(relation.get("target", "")))
            )
            _check(f0, f"{prefix}:endpoints", endpoints_ok)
            _check(
                f0,
                f"{prefix}:validation-status",
                relation.get("validation_status") in _VALIDATION_STATUSES,
            )
            relation_id = relation.get("relation_id")
            _check(
                f0,
                f"{prefix}:relation-id",
                relation_id == identified_digest(relation, "relation_id"),
            )
            if relation.get("kind") == "transforms":
                contract = {"criterion", "preserves", "loses", "assumptions", "validation_status"}
                transformation_relation_ok = (
                    contract <= relation.keys()
                    and isinstance(relation.get("criterion"), dict)
                    and bool(relation.get("criterion"))
                    and _transformation_declarations_are_consistent(relation)
                )
                _check(f0, f"{prefix}:transformation-contract", transformation_relation_ok)

    f1: list[dict[str, Any]] = []
    negotiations: list[dict[str, Any]] = []
    if _LEVELS[level] >= 1 and all(item["passed"] for item in f0):
        graph_id = graph.get("graph_id")
        _check(f1, "graph:graph-id", graph_id == identified_digest(graph, "graph_id"))
        ids = [item["artifact_id"] for item in artifacts]
        id_set = set(ids)
        _check(f1, "graph:unique-artifact-ids", len(ids) == len(id_set))
        relation_ids = [item["relation_id"] for item in relations]
        _check(f1, "graph:unique-relation-ids", len(relation_ids) == len(set(relation_ids)))
        for index, artifact in enumerate(artifacts):
            refs = list(artifact["provenance"]["source_refs"])
            payload = artifact["payload"]
            if artifact["kind"] == "transformation":
                refs.extend(payload.get("input_refs", []))
                refs.extend(payload.get("output_refs", []))
            if artifact["kind"] == "claim":
                refs.extend(payload.get("evidence_refs", []))
            _check(
                f1,
                f"artifact[{index}]:references",
                all(ref in id_set for ref in refs),
                unresolved=sorted(ref for ref in refs if ref not in id_set),
            )
            negotiations.append({
                "artifact_id": artifact["artifact_id"],
                **negotiate(artifact["profile"]),
            })
        for index, relation in enumerate(relations):
            endpoints = (relation["source"], relation["target"])
            _check(
                f1,
                f"relation[{index}]:references",
                all(ref in id_set for ref in endpoints),
                unresolved=sorted(ref for ref in endpoints if ref not in id_set),
            )
    f0_pass = bool(f0) and all(item["passed"] for item in f0)
    f1_pass = f0_pass and bool(f1) and all(item["passed"] for item in f1)
    semantic_status = "NOT_IMPLEMENTED"
    semantic_results: list[dict[str, Any]] = []
    if level == "F2":
        semantic_status = "NOT_ASSESSED"
        if f1_pass:
            semantic_status, semantic_results = validate_semantics(
                graph, registry=semantic_registry
            )
    return _report(
        level,
        f0,
        f1,
        negotiations,
        semantic_status,
        semantic_results,
    )


def _report(
    level: str,
    f0: list[dict[str, Any]],
    f1: list[dict[str, Any]],
    negotiations: list[dict[str, Any]],
    semantic_status: str,
    semantic_results: list[dict[str, Any]],
) -> dict[str, Any]:
    f0_pass = bool(f0) and all(item["passed"] for item in f0)
    f1_assessed = _LEVELS[level] >= 1 and f0_pass
    f1_pass = f1_assessed and bool(f1) and all(item["passed"] for item in f1)
    passed = (
        f0_pass
        if level == "F0"
        else f1_pass
        if level == "F1"
        else f1_pass and semantic_status == "PASS"
    )
    capabilities_supported = bool(negotiations) and all(
        item["status"] == "SUPPORTED" for item in negotiations
    )
    highest = (
        "F2"
        if f1_pass and semantic_status == "PASS"
        else "F1"
        if f1_pass
        else "F0"
        if f0_pass
        else None
    )
    level_results = {
        "F0": "PASS" if f0_pass else "FAIL",
        "F1": "PASS" if f1_pass else ("NOT_ASSESSED" if not f1_assessed else "FAIL"),
        "F2": semantic_status if level == "F2" else "NOT_IMPLEMENTED",
        "F3": "NOT_IMPLEMENTED",
        "F4": "NOT_IMPLEMENTED",
    }
    overall_status = (
        "PASS" if passed else "FAIL"
        if level != "F2" or not f1_pass
        else semantic_status
    )
    proof = [
        {"step": 0, "kind": "structural-conformance", "status": "PASS" if f0_pass else "FAIL"},
        {
            "step": 1,
            "kind": "referential-conformance",
            "status": "PASS" if f1_pass else "NOT-PASSED",
        },
    ]
    if level == "F2":
        proof.append(
            {
                "step": 2,
                "kind": "profile-semantic-conformance",
                "status": semantic_status,
                "semantic_results": len(semantic_results),
            }
        )
    proof.append(
        {
            "step": len(proof),
            "kind": "evidence-boundary",
            "boundary": (
                (
                    "F0/F1 validation establishes structure, content identity, and graph "
                    "reference integrity only. It does not establish semantic correctness, "
                    "provider authenticity, physical fidelity, causation, or truth."
                )
                if level != "F2"
                else (
                    "F0/F1 validation establishes structure, content identity, and graph "
                    "reference integrity. F2 establishes only named installed profile "
                    "checks that report PASS. It does not establish provider authenticity, "
                    "physical fidelity, causation, or truth."
                )
            ),
        }
    )
    report = {
        "schema": "e7q.ir.conformance-report/v0alpha1",
        "status": overall_status,
        "requested_level": level,
        "highest_level_passed": highest,
        "level_results": level_results,
        "semantic_readiness": (
            semantic_status
            if level == "F2" and f1_pass
            else "READY_FOR_F2" if capabilities_supported else "BLOCKED"
        ),
        "capability_negotiation": negotiations,
        "checks": f0 + f1,
        "proof": proof,
    }
    if level == "F2":
        report["semantic_results"] = semantic_results
    return report
