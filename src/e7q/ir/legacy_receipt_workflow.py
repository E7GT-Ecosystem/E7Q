# SPDX-License-Identifier: Apache-2.0
"""Typed E7Q-IR mapping for supplied legacy execution receipts."""
from __future__ import annotations

import argparse
from base64 import b64decode, b64encode
from binascii import Error as BinasciiError
import json
from pathlib import Path
from typing import Any, Iterable

from ..artifacts import validate_artifact
from ..language import E7QError
from ..openqasm2 import COUNT_ORDERS
from ..results import build_execution_receipt
from .canonical import canonical_bytes, digest
from .conformance import validate_graph
from .envelope import build_artifact
from .graph import build_graph, build_relation
from .legacy import LIMITS as LEGACY_LIMITS
from .legacy import MAX_BYTES, SCHEMAS, _parse

WORKFLOW_FORMAT = "e7q.ir.legacy-execution-receipt-workflow/v1"
SOURCE_ADAPTER = "e7q.ir.legacy-execution-receipt-source/v1"
REPRESENTATION_FORMAT = "e7q.ir.legacy-execution-object/v1"
INTENT_FORMAT = "e7q.ir.legacy-execution-intent/v1"
EXECUTION_FORMAT = "e7q.ir.supplied-execution-record/v1"
OBSERVATION_FORMAT = "e7q.ir.legacy-count-observation/v1"
ASSESSMENT_FORMAT = "e7q.ir.legacy-receipt-consistency-assessment/v1"
TRANSFORMATION_FORMAT = "e7q.ir.legacy-receipt-transformation/v1"
CLAIM_TYPE = "bounded-offline-legacy-receipt-consistency"
CRITERION = {
    "id": "e7q.ir.legacy-receipt-consistency",
    "version": "1",
    "legacy_criterion": {
        "id": "e7q.receipt-consistency",
        "edition": "1",
    },
}
ROLE_SCHEMAS = {
    "bundle": "e7q.execution-bundle/v1",
    "result": "e7q.execution-result/v1",
    "receipt": "e7q.execution-receipt/v1",
}
ROLE_KNOWN_FIELDS = {
    "bundle": frozenset({
        "schema", "status", "submitted", "target", "shots", "captured_at",
        "temporal_evidence", "source_digest", "snapshot_digest", "openqasm",
        "openqasm_digest", "planning", "selection", "proof", "limitations",
        "compiled_digest",
    }),
    "result": frozenset({
        "schema", "provider", "job_id", "target", "shots", "counts",
        "completed_at", "bundle_digest", "label_order", "limitations",
    }),
    "receipt": frozenset({
        "schema", "status", "bundle_digest", "result_digest", "provider",
        "job_id", "target", "shots", "completed_at", "temporal_evidence",
        "counts", "probabilities", "proof", "observational_claim_pilot",
        "temporal_orientation_pilot", "limitations",
    }),
}
RECEIPT_FIELDS = (
    "schema", "status", "bundle_digest", "result_digest", "provider", "job_id",
    "target", "shots", "completed_at", "temporal_evidence", "counts",
    "probabilities", "proof", "observational_claim_pilot",
    "temporal_orientation_pilot",
)
LIMITATIONS = tuple(LEGACY_LIMITS) + (
    "A typed mapping and independently recomputed legacy receipt establish only offline internal consistency under the declared criterion.",
    "Provider, job and completion-time fields are supplied unauthenticated declarations; no submission, execution witness or chronology is established.",
    "Reported counts and empirical probabilities do not prove hardware execution, physical fidelity, circuit correctness or computational advantage.",
    "No F3 authentication, default F2 semantic validation, arbitrary scalability, Phase 2 completion, H5 completion, provider integration or K12/CFS implementation is established.",
)
SOURCE_PRESERVES = (
    "exact-input-bytes",
    "byte-length",
    "sha256-content-digest",
    "declared-legacy-schema",
    "stable-source-reference",
)
SOURCE_LOSSES = (
    "filesystem-metadata",
    "external-origin-authentication",
)
SOURCE_ASSUMPTIONS = (
    "stable-source-reference-is-caller-declared",
    "content-digest-is-integrity-only-not-authenticity",
)
MAPPING_ASSUMPTIONS = (
    "legacy-fields-are-supplied-unauthenticated-data",
    "count-label-order-is-explicit-mapping-context",
    "unknown-fields-are-preserved-but-not-interpreted",
    "receipt-consistency-is-not-execution-authenticity",
)


def _raw_digest(raw: bytes) -> str:
    from hashlib import sha256

    return "sha256:" + sha256(raw).hexdigest()


def _issue(role: str, code: str, message: str, status: str) -> dict[str, str]:
    return {
        "role": role,
        "code": code,
        "status": status,
        "type": "LegacyReceiptMappingError",
        "message": message,
    }


def _status(issues: Iterable[dict[str, str]], default: str = "PASS") -> str:
    items = list(issues)
    for candidate in ("BLOCKED", "UNSUPPORTED", "FAIL", "NOT_ASSESSED"):
        if any(item["status"] == candidate for item in items):
            return candidate
    return default


def _validation_status(status: str) -> str:
    if status == "PASS":
        return "validated"
    if status == "NOT_ASSESSED":
        return "not-assessed"
    return "failed"


def _read(path: str | Path, role: str) -> tuple[Path, bytes]:
    source = Path(path)
    try:
        with source.open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
    except OSError as exc:
        raise E7QError(f"cannot read {role}: {exc}") from exc
    if len(raw) > MAX_BYTES:
        raise E7QError(f"{role} exceeds the {MAX_BYTES}-byte legacy input budget")
    return source, raw


def _strict_object(raw: bytes, role: str) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    try:
        value = _parse(raw.decode("utf-8"))
    except (UnicodeError, ValueError, RecursionError) as exc:
        return None, [_issue(role, "invalid_json", str(exc), "UNSUPPORTED")]
    if not isinstance(value, dict):
        return None, [_issue(role, "non_object_json", f"{role} must be a JSON object", "UNSUPPORTED")]
    schema = value.get("schema")
    expected = ROLE_SCHEMAS[role]
    if not isinstance(schema, str):
        return value, [_issue(role, "missing_schema", f"{role} has no schema", "UNSUPPORTED")]
    if schema not in SCHEMAS or schema != expected:
        return value, [_issue(role, "unknown_schema", f"{role} must use {expected}", "UNSUPPORTED")]
    return value, []


def _source_payload(
    role: str,
    raw: bytes,
    parsed: dict[str, Any] | None,
    *,
    display_name: str,
    stable_source_ref: str,
) -> dict[str, Any]:
    return {
        "format": "e7q.legacy-source-bytes/v1",
        "adapter": SOURCE_ADAPTER,
        "role": role,
        "display_name": display_name,
        "stable_source_ref": stable_source_ref,
        "legacy_schema": parsed.get("schema") if isinstance(parsed, dict) else None,
        "content_encoding": "base64",
        "content_base64": b64encode(raw).decode("ascii"),
        "content_digest": _raw_digest(raw),
        "byte_length": len(raw),
    }


def _source_artifact(
    role: str,
    raw: bytes,
    parsed: dict[str, Any] | None,
    *,
    display_name: str,
    stable_source_ref: str,
    created_at: str,
    actor: str,
) -> dict[str, Any]:
    return build_artifact(
        "source",
        _source_payload(
            role,
            raw,
            parsed,
            display_name=display_name,
            stable_source_ref=stable_source_ref,
        ),
        created_at=created_at,
        actor=actor,
        capabilities_required=("artifact.identity",),
        limitations=LIMITATIONS,
    )


def _representation_payload(
    role: str,
    value: dict[str, Any] | None,
    issues: list[dict[str, str]],
) -> dict[str, Any]:
    structural = validate_artifact(value) if value is not None else None
    local_issues = list(issues)
    if structural is not None and structural["status"] != "PASS":
        local_issues.append(_issue(
            role,
            "structural_nonconformance",
            f"{role} fails registered legacy structural conformance",
            "UNSUPPORTED",
        ))
    return {
        "format": REPRESENTATION_FORMAT,
        "role": role,
        "mapping_status": _status(local_issues),
        "legacy_schema": value.get("schema") if value is not None else None,
        "legacy_status": value.get("status") if value is not None else None,
        "legacy_proof": value.get("proof") if value is not None else None,
        "legacy_limitations": value.get("limitations") if value is not None else None,
        "unknown_fields": sorted(set(value) - ROLE_KNOWN_FIELDS[role]) if value is not None else [],
        "complete_original_object": value,
        "content_identity": digest({
            "format": "e7q.legacy-json-object-content/v1",
            "role": role,
            "object": value,
        }) if value is not None else None,
        "structural_conformance": structural,
        "issues": local_issues,
    }


def _representation_artifact(
    role: str,
    value: dict[str, Any] | None,
    issues: list[dict[str, str]],
    *,
    source_id: str,
    created_at: str,
    actor: str,
) -> dict[str, Any]:
    return build_artifact(
        "representation",
        _representation_payload(role, value, issues),
        created_at=created_at,
        actor=actor,
        source_refs=(source_id,),
        capabilities_required=("artifact.identity",),
        limitations=LIMITATIONS,
    )


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:") or len(value) != 71:
        return False
    try:
        int(value[7:], 16)
    except ValueError:
        return False
    return True


def _add_check(
    checks: list[dict[str, Any]],
    name: str,
    passed: bool,
    *,
    failure_status: str,
    failure_reason: str,
    detail: Any = None,
) -> None:
    checks.append({
        "name": name,
        "passed": bool(passed),
        "failure_status": failure_status,
        "failure_reason": None if passed else failure_reason,
        "detail": detail,
    })


def _count_summary(
    result: dict[str, Any] | None,
    label_order: str,
    checks: list[dict[str, Any]],
) -> dict[str, Any]:
    valid_order = label_order in COUNT_ORDERS
    _add_check(
        checks,
        "mapping:count-label-order-supported",
        valid_order,
        failure_status="UNSUPPORTED",
        failure_reason="unsupported_count_label_order",
        detail=label_order,
    )
    declared_order = result.get("label_order") if result is not None else None
    order_agrees = declared_order is None or declared_order == label_order
    _add_check(
        checks,
        "result:declared-count-label-order-agrees",
        order_agrees,
        failure_status="UNSUPPORTED",
        failure_reason="unsupported_count_label_semantics",
        detail={"declared": declared_order, "mapping_context": label_order},
    )
    counts = result.get("counts") if result is not None else None
    valid_counts = isinstance(counts, dict) and bool(counts)
    width: int | None = None
    normalized: dict[str, int] = {}
    if valid_counts:
        widths: set[int] = set()
        for outcome, count in counts.items():
            if (
                not isinstance(outcome, str)
                or not outcome
                or set(outcome) - {"0", "1"}
                or not isinstance(count, int)
                or isinstance(count, bool)
                or count < 0
            ):
                valid_counts = False
                break
            widths.add(len(outcome))
            normalized[outcome] = count
        valid_counts = valid_counts and len(widths) == 1
        if valid_counts:
            width = next(iter(widths))
    _add_check(
        checks,
        "result:binary-nonnegative-equal-width-counts",
        valid_counts,
        failure_status="UNSUPPORTED",
        failure_reason="malformed_counts",
        detail=counts,
    )
    total = sum(normalized.values()) if valid_counts else None
    shots = result.get("shots") if result is not None else None
    total_matches = valid_counts and isinstance(shots, int) and not isinstance(shots, bool) and total == shots
    _add_check(
        checks,
        "result:counts-sum-to-shots",
        total_matches,
        failure_status="FAIL",
        failure_reason="count_total_mismatch",
        detail={"count_total": total, "shots": shots},
    )
    probabilities = {
        outcome: count / shots for outcome, count in sorted(normalized.items())
    } if total_matches else {}
    return {
        "format": OBSERVATION_FORMAT,
        "status": "PASS" if valid_order and total_matches else _status([
            {
                "status": check["failure_status"]
            }
            for check in checks
            if not check["passed"] and check["name"].startswith(("mapping:", "result:"))
        ]),
        "count_label_order": label_order if valid_order else None,
        "outcome_sequence": sorted(normalized) if valid_counts else [],
        "outcome_width": width,
        "counts": dict(sorted(normalized.items())) if valid_counts else None,
        "count_total": total,
        "empirical_probabilities": probabilities if total_matches else None,
        "zero_count_outcomes": sorted(
            outcome for outcome, count in normalized.items() if count == 0
        ) if valid_counts else [],
        "interpretation_boundary": "Aggregate supplied counts only; no shot ordering, execution witness, hardware fidelity or circuit-correctness inference.",
    }


def _typed_payloads(
    bundle: dict[str, Any] | None,
    bundle_raw: bytes,
    result: dict[str, Any] | None,
    result_raw: bytes,
    receipt: dict[str, Any] | None,
    receipt_raw: bytes,
    *,
    label_order: str,
    representation_refs: dict[str, str],
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for role, value in (("bundle", bundle), ("result", result), ("receipt", receipt)):
        _add_check(
            checks,
            f"{role}:parsed-and-schema-admitted",
            value is not None and value.get("schema") == ROLE_SCHEMAS[role],
            failure_status="UNSUPPORTED",
            failure_reason=f"{role}_not_admitted",
            detail=value.get("schema") if value is not None else None,
        )
        structural = validate_artifact(value) if value is not None else None
        _add_check(
            checks,
            f"{role}:registered-structural-conformance",
            structural is not None and structural["status"] == "PASS",
            failure_status="UNSUPPORTED",
            failure_reason=f"{role}_structural_nonconformance",
            detail=structural,
        )

    bundle_ready = bundle is not None and bundle.get("status") == "READY" and bundle.get("submitted") is False
    _add_check(
        checks,
        "bundle:ready-offline-handoff",
        bundle_ready,
        failure_status="UNSUPPORTED",
        failure_reason="bundle_not_ready_or_already_submitted",
        detail={
            "status": bundle.get("status") if bundle is not None else None,
            "submitted": bundle.get("submitted") if bundle is not None else None,
        },
    )
    bundle_digest = _raw_digest(bundle_raw)
    planning = bundle.get("planning") if isinstance(bundle, dict) else None
    compiled = planning.get("compiled") if isinstance(planning, dict) else None
    compiled_digest = digest({
        "format": "e7q.legacy-compiled-content/v1",
        "compiled": compiled,
    }) if compiled is not None else None
    for field in ("source_digest", "openqasm_digest"):
        _add_check(
            checks,
            f"bundle:{field}-shape",
            bundle is not None and _is_sha256(bundle.get(field)),
            failure_status="UNSUPPORTED",
            failure_reason=f"invalid_{field}",
            detail=bundle.get(field) if bundle is not None else None,
        )
    _add_check(
        checks,
        "bundle:compiled-content-present",
        compiled is not None,
        failure_status="UNSUPPORTED",
        failure_reason="compiled_content_missing",
        detail=None,
    )
    intent = {
        "format": INTENT_FORMAT,
        "status": "PASS" if bundle_ready else "UNSUPPORTED",
        "input_refs": [representation_refs["bundle"]],
        "bundle_identity": bundle_digest,
        "declared_schema": bundle.get("schema") if bundle is not None else None,
        "declared_source_digest": bundle.get("source_digest") if bundle is not None else None,
        "declared_openqasm_digest": bundle.get("openqasm_digest") if bundle is not None else None,
        "declared_compiled_digest": bundle.get("compiled_digest") if bundle is not None else None,
        "computed_compiled_content_digest": compiled_digest,
        "selected_target": bundle.get("target") if bundle is not None else None,
        "requested_shots": bundle.get("shots") if bundle is not None else None,
        "captured_at": bundle.get("captured_at") if bundle is not None else None,
        "submission_status": "not-submitted" if bundle_ready else "supplied-unknown",
        "compiler_proof": compiled.get("proof") if isinstance(compiled, dict) else None,
        "bundle_proof": bundle.get("proof") if bundle is not None else None,
        "limitations": bundle.get("limitations") if bundle is not None else None,
    }

    result_required = (
        "provider", "job_id", "target", "shots", "counts", "completed_at",
    )
    result_complete = result is not None and all(field in result for field in result_required)
    _add_check(
        checks,
        "result:required-fields",
        result_complete,
        failure_status="UNSUPPORTED",
        failure_reason="result_missing_required_fields",
        detail=[field for field in result_required if result is None or field not in result],
    )
    identifiers_typed = (
        result is not None
        and isinstance(result.get("provider"), str) and bool(result["provider"])
        and isinstance(result.get("job_id"), str) and bool(result["job_id"])
        and isinstance(result.get("completed_at"), str) and bool(result["completed_at"])
    )
    _add_check(
        checks,
        "result:supplied-identifiers-and-completion-typed",
        identifiers_typed,
        failure_status="UNSUPPORTED",
        failure_reason="result_identifiers_not_typed",
        detail={
            "provider": result.get("provider") if result is not None else None,
            "job_id": result.get("job_id") if result is not None else None,
            "completed_at": result.get("completed_at") if result is not None else None,
        },
    )
    declared_bundle_digest = result.get("bundle_digest") if result is not None else None
    bundle_linked = declared_bundle_digest is None or declared_bundle_digest == bundle_digest
    _add_check(
        checks,
        "result:bundle-digest-linkage",
        bundle_linked,
        failure_status="FAIL",
        failure_reason="bundle_digest_mismatch",
        detail={"declared": declared_bundle_digest, "actual": bundle_digest},
    )
    target_matches = result is not None and bundle is not None and result.get("target") == bundle.get("target")
    shots_match = (
        result is not None and bundle is not None
        and isinstance(result.get("shots"), int) and not isinstance(result.get("shots"), bool)
        and result.get("shots") == bundle.get("shots") and result.get("shots", 0) > 0
    )
    _add_check(
        checks,
        "result:target-matches-bundle",
        target_matches,
        failure_status="FAIL",
        failure_reason="target_mismatch",
        detail={
            "result": result.get("target") if result is not None else None,
            "bundle": bundle.get("target") if bundle is not None else None,
        },
    )
    _add_check(
        checks,
        "result:shots-match-bundle",
        shots_match,
        failure_status="FAIL",
        failure_reason="shot_mismatch",
        detail={
            "result": result.get("shots") if result is not None else None,
            "bundle": bundle.get("shots") if bundle is not None else None,
        },
    )
    execution = {
        "format": EXECUTION_FORMAT,
        "status": "PASS" if result_complete and identifiers_typed else "UNSUPPORTED",
        "input_refs": [representation_refs["result"]],
        "intent_ref": None,
        "result_identity": _raw_digest(result_raw),
        "declared_bundle_digest": declared_bundle_digest,
        "provider_declaration": result.get("provider") if result is not None else None,
        "job_id_declaration": result.get("job_id") if result is not None else None,
        "authentication_status": "not-authenticated",
        "selected_target": result.get("target") if result is not None else None,
        "reported_shots": result.get("shots") if result is not None else None,
        "reported_completion_time": result.get("completed_at") if result is not None else None,
        "chronology_status": "provider-reported-not-authenticated",
        "chronology_limitation": "The supplied completion value is retained but neither its syntax, clock, chronology nor provider origin is authenticated.",
        "limitations": result.get("limitations") if result is not None else None,
    }
    observation = _count_summary(result, label_order, checks)
    observation["input_refs"] = []
    observation["provider_report_ref"] = None
    observation["optional_supplied_records"] = {
        "temporal_evidence": receipt.get("temporal_evidence") if receipt is not None else None,
        "observational_claim_pilot": receipt.get("observational_claim_pilot") if receipt is not None else None,
        "temporal_orientation_pilot": receipt.get("temporal_orientation_pilot") if receipt is not None else None,
        "claim_effect": "none",
    }

    recomputed: dict[str, Any] | None = None
    recompute_issue: dict[str, str] | None = None
    can_recompute = (
        bundle is not None and result is not None
        and bundle.get("schema") == ROLE_SCHEMAS["bundle"]
        and result.get("schema") == ROLE_SCHEMAS["result"]
        and bundle_ready and result_complete
    )
    if can_recompute:
        try:
            recomputed = build_execution_receipt(
                bundle,
                bundle_raw,
                result,
                result_raw,
                include_observational_claim_pilot=(
                    receipt is not None and "observational_claim_pilot" in receipt
                ),
                include_temporal_orientation_pilot=(
                    receipt is not None and "temporal_orientation_pilot" in receipt
                ),
            )
        except (E7QError, KeyError, TypeError, ValueError) as exc:
            message = str(exc)
            if "target does not match" in message:
                recompute_issue = _issue("assessment", "target_mismatch", message, "FAIL")
            elif "shots do not match" in message:
                recompute_issue = _issue("assessment", "shot_mismatch", message, "FAIL")
            elif "sum to shots" in message:
                recompute_issue = _issue("assessment", "count_total_mismatch", message, "FAIL")
            elif "bundle_digest" in message:
                recompute_issue = _issue("assessment", "bundle_digest_mismatch", message, "FAIL")
            elif "outcomes" in message or "counts" in message:
                recompute_issue = _issue("assessment", "malformed_counts", message, "UNSUPPORTED")
            else:
                recompute_issue = _issue("assessment", "legacy_recompute_failure", message, "NOT_ASSESSED")
    else:
        recompute_issue = _issue(
            "assessment",
            "legacy_recompute_blocked",
            "bundle or result is not admitted for legacy receipt recomputation",
            "UNSUPPORTED",
        )
    _add_check(
        checks,
        "assessment:legacy-receipt-recomputed",
        recomputed is not None,
        failure_status=recompute_issue["status"] if recompute_issue is not None else "NOT_ASSESSED",
        failure_reason=recompute_issue["code"] if recompute_issue is not None else "legacy_recompute_failure",
        detail=recompute_issue,
    )

    receipt_status = receipt.get("status") if receipt is not None else None
    supported_status = receipt_status in {"PASS", "FAIL", "BLOCKED", "UNSUPPORTED", "NOT_ASSESSED"}
    _add_check(
        checks,
        "receipt:known-status",
        supported_status,
        failure_status="NOT_ASSESSED",
        failure_reason="unknown_receipt_status",
        detail=receipt_status,
    )
    comparisons: list[dict[str, Any]] = []
    if recomputed is not None and receipt is not None:
        for field in RECEIPT_FIELDS:
            if field not in recomputed and field not in receipt:
                continue
            passed = receipt.get(field) == recomputed.get(field)
            comparisons.append({
                "field": field,
                "passed": passed,
                "supplied": receipt.get(field),
                "recomputed": recomputed.get(field),
            })
            _add_check(
                checks,
                f"receipt:matches-recomputed:{field}",
                passed,
                failure_status="FAIL",
                failure_reason="supplied_receipt_semantics_mismatch",
                detail={"field": field},
            )

    failed_checks = [check for check in checks if not check["passed"]]
    if receipt_status in {"FAIL", "BLOCKED", "UNSUPPORTED", "NOT_ASSESSED"}:
        outcome_status = receipt_status
        outcome_reason = "supplied_receipt_non_pass"
    elif not supported_status:
        outcome_status = "NOT_ASSESSED"
        outcome_reason = "unknown_receipt_status"
    elif failed_checks:
        outcome_status = _status(
            {"status": check["failure_status"]} for check in failed_checks
        )
        first = next(
            check for check in failed_checks
            if check["failure_status"] == outcome_status
        )
        outcome_reason = first["failure_reason"]
    else:
        outcome_status = "PASS"
        outcome_reason = "legacy_receipt_semantics_recomputed_and_matched"

    assessment = {
        "format": ASSESSMENT_FORMAT,
        "criterion": CRITERION,
        "input_refs": [
            representation_refs["bundle"],
            representation_refs["result"],
            representation_refs["receipt"],
        ],
        "outcome": {
            "status": outcome_status,
            "reason": outcome_reason,
            "conclusion": "SUPPORTED" if outcome_status == "PASS" else "INCONCLUSIVE" if outcome_status in {"BLOCKED", "UNSUPPORTED", "NOT_ASSESSED"} else "DISPROVED",
            "receipt_consistency_established": outcome_status == "PASS",
            "execution_authenticity_established": False,
            "provider_identity_authenticated": False,
            "chronology_authenticated": False,
            "physical_fidelity_established": False,
        },
        "checks": checks,
        "failure_reasons": [
            check["failure_reason"] for check in failed_checks
            if check["failure_reason"] is not None
        ],
        "supplied_receipt_status": receipt_status,
        "supplied_receipt_digest": _raw_digest(receipt_raw),
        "recomputed_receipt": recomputed,
        "receipt_field_comparisons": comparisons,
        "unknown_receipt_fields": sorted(set(receipt) - ROLE_KNOWN_FIELDS["receipt"]) if receipt is not None else [],
        "validation_boundary": "The existing build_execution_receipt logic was rerun over strictly parsed preserved bundle/result bytes. Agreement is offline internal consistency only.",
    }
    assessment["assessment_id"] = digest(assessment)
    return {
        "intent": intent,
        "execution": execution,
        "observation": observation,
        "assessment": assessment,
        "status": outcome_status,
        "reason": outcome_reason,
    }


def _transformation_payload(
    name: str,
    input_refs: Iterable[str],
    output_refs: Iterable[str],
    *,
    criterion: dict[str, Any],
    preserves: Iterable[str],
    loses: Iterable[str],
    assumptions: Iterable[str],
    validation_status: str,
) -> dict[str, Any]:
    payload = {
        "format": TRANSFORMATION_FORMAT,
        "name": name,
        "input_refs": list(input_refs),
        "output_refs": list(output_refs),
        "criterion": criterion,
        "preserves": list(preserves),
        "loses": list(loses),
        "assumptions": list(assumptions),
        "validation_status": validation_status,
    }
    payload["transformation_id"] = digest(payload)
    return payload


def _build_transformation(
    name: str,
    input_refs: Iterable[str],
    output_refs: Iterable[str],
    *,
    criterion: dict[str, Any],
    preserves: Iterable[str],
    loses: Iterable[str],
    assumptions: Iterable[str],
    validation_status: str,
    created_at: str,
    actor: str,
) -> dict[str, Any]:
    inputs = tuple(input_refs)
    outputs = tuple(output_refs)
    return build_artifact(
        "transformation",
        _transformation_payload(
            name,
            inputs,
            outputs,
            criterion=criterion,
            preserves=preserves,
            loses=loses,
            assumptions=assumptions,
            validation_status=validation_status,
        ),
        created_at=created_at,
        actor=actor,
        source_refs=inputs + outputs,
        capabilities_required=("artifact.identity", "transformation.accounting"),
        limitations=LIMITATIONS,
    )


def build_legacy_receipt_graph(
    bundle_path: str | Path,
    result_path: str | Path,
    receipt_path: str | Path,
    *,
    count_label_order: str,
    created_at: str,
    bundle_source_ref: str,
    result_source_ref: str,
    receipt_source_ref: str,
    name: str = "Typed legacy execution receipt mapping",
    actor: str = "e7q.ir.legacy-execution-receipt-workflow",
) -> dict[str, Any]:
    """Map supplied legacy execution files into bounded typed E7Q-IR evidence."""
    for value, label in (
        (count_label_order, "count_label_order"),
        (created_at, "created_at"),
        (bundle_source_ref, "bundle_source_ref"),
        (result_source_ref, "result_source_ref"),
        (receipt_source_ref, "receipt_source_ref"),
        (name, "name"),
        (actor, "actor"),
    ):
        if not isinstance(value, str) or not value:
            raise E7QError(f"{label} must be a non-empty string")
    if len({bundle_source_ref, result_source_ref, receipt_source_ref}) != 3:
        raise E7QError("stable source references must be distinct")

    inputs = {
        "bundle": _read(bundle_path, "execution bundle"),
        "result": _read(result_path, "execution result"),
        "receipt": _read(receipt_path, "execution receipt"),
    }
    parsed: dict[str, dict[str, Any] | None] = {}
    parse_issues: dict[str, list[dict[str, str]]] = {}
    for role, (_, raw) in inputs.items():
        parsed[role], parse_issues[role] = _strict_object(raw, role)

    refs = {
        "bundle": bundle_source_ref,
        "result": result_source_ref,
        "receipt": receipt_source_ref,
    }
    sources: dict[str, dict[str, Any]] = {}
    representations: dict[str, dict[str, Any]] = {}
    for role, (path, raw) in inputs.items():
        source = _source_artifact(
            role,
            raw,
            parsed[role],
            display_name=path.name,
            stable_source_ref=refs[role],
            created_at=created_at,
            actor=actor,
        )
        sources[role] = source
        representations[role] = _representation_artifact(
            role,
            parsed[role],
            parse_issues[role],
            source_id=source["artifact_id"],
            created_at=created_at,
            actor=actor,
        )

    representation_refs = {
        role: artifact["artifact_id"] for role, artifact in representations.items()
    }
    typed = _typed_payloads(
        parsed["bundle"],
        inputs["bundle"][1],
        parsed["result"],
        inputs["result"][1],
        parsed["receipt"],
        inputs["receipt"][1],
        label_order=count_label_order,
        representation_refs=representation_refs,
    )
    intent = build_artifact(
        "intent",
        typed["intent"],
        created_at=created_at,
        actor=actor,
        source_refs=(representation_refs["bundle"],),
        capabilities_required=("artifact.identity",),
        limitations=LIMITATIONS,
    )
    execution_payload = dict(typed["execution"])
    execution_payload["intent_ref"] = intent["artifact_id"]
    execution = build_artifact(
        "execution",
        execution_payload,
        created_at=created_at,
        actor=actor,
        source_refs=(representation_refs["result"], intent["artifact_id"]),
        capabilities_required=("artifact.identity",),
        limitations=LIMITATIONS,
    )
    observation_payload = dict(typed["observation"])
    observation_payload["input_refs"] = [execution["artifact_id"]]
    observation_payload["provider_report_ref"] = execution["artifact_id"]
    observation = build_artifact(
        "observation",
        observation_payload,
        created_at=created_at,
        actor=actor,
        source_refs=(execution["artifact_id"],),
        capabilities_required=("artifact.identity",),
        limitations=LIMITATIONS,
    )
    assessment_payload = json.loads(json.dumps(typed["assessment"]))
    assessment_payload["execution_intent_ref"] = intent["artifact_id"]
    assessment_payload["execution_record_ref"] = execution["artifact_id"]
    assessment_payload["observation_ref"] = observation["artifact_id"]
    assessment_payload["assessment_id"] = digest(assessment_payload)
    assessment = build_artifact(
        "assessment",
        assessment_payload,
        created_at=created_at,
        actor=actor,
        source_refs=(
            representation_refs["bundle"],
            representation_refs["result"],
            representation_refs["receipt"],
            intent["artifact_id"],
            execution["artifact_id"],
            observation["artifact_id"],
        ),
        capabilities_required=("artifact.identity",),
        limitations=LIMITATIONS,
    )

    map_criterion = {"id": "e7q.ir.legacy-execution-typed-mapping", "version": "1"}
    mapping_status = _validation_status(typed["status"])
    bundle_mapping = _build_transformation(
        "bundle-to-execution-intent",
        (representation_refs["bundle"],),
        (intent["artifact_id"],),
        criterion=map_criterion,
        preserves=("bundle-identity", "target", "shots", "declared-digests", "complete-bundle-proof", "unknown-fields-in-source-representation"),
        loses=("provider-authentication", "submission-evidence", "filesystem-metadata"),
        assumptions=MAPPING_ASSUMPTIONS,
        validation_status=_validation_status(typed["intent"]["status"]),
        created_at=created_at,
        actor=actor,
    )
    result_mapping = _build_transformation(
        "result-to-supplied-execution-record",
        (representation_refs["result"], intent["artifact_id"]),
        (execution["artifact_id"],),
        criterion=map_criterion,
        preserves=("result-identity", "bundle-linkage-declaration", "provider-job-declarations", "target", "shots", "reported-completion-time"),
        loses=("provider-authentication", "execution-witness", "authenticated-chronology"),
        assumptions=MAPPING_ASSUMPTIONS,
        validation_status=_validation_status(typed["execution"]["status"]),
        created_at=created_at,
        actor=actor,
    )
    observation_mapping = _build_transformation(
        "supplied-execution-record-to-observation",
        (execution["artifact_id"], representation_refs["result"]),
        (observation["artifact_id"],),
        criterion={"id": "e7q.ir.legacy-count-observation-mapping", "version": "1"},
        preserves=("complete-count-map", "zero-count-outcomes", "outcome-width", "explicit-label-order", "empirical-probabilities"),
        loses=("shot-order", "shot-timing", "intermediate-states", "hardware-fidelity"),
        assumptions=MAPPING_ASSUMPTIONS,
        validation_status=_validation_status(typed["observation"]["status"]),
        created_at=created_at,
        actor=actor,
    )
    receipt_mapping = _build_transformation(
        "receipt-to-independent-consistency-assessment",
        (
            representation_refs["receipt"],
            intent["artifact_id"],
            execution["artifact_id"],
            observation["artifact_id"],
        ),
        (assessment["artifact_id"],),
        criterion=CRITERION,
        preserves=("complete-supplied-receipt-proof", "supplied-status", "unknown-fields-in-source-representation", "all-consistency-checks", "all-failure-reasons"),
        loses=("provider-authentication", "execution-authenticity", "physical-fidelity", "circuit-correctness"),
        assumptions=MAPPING_ASSUMPTIONS,
        validation_status=mapping_status,
        created_at=created_at,
        actor=actor,
    )

    supported = typed["status"] == "PASS"
    claim_payload = {
        "statement": "The supplied bundle and result are internally consistent and the typed mapping agrees with independently recomputed legacy receipt semantics under the declared offline criterion.",
        "claim_type": CLAIM_TYPE,
        "criterion": CRITERION,
        "evidence_refs": [
            bundle_mapping["artifact_id"],
            result_mapping["artifact_id"],
            observation_mapping["artifact_id"],
            receipt_mapping["artifact_id"],
            assessment["artifact_id"],
        ],
        "support_status": "supported-within-declared-scope" if supported else "unsupported",
        "support_conditions": {
            "all_sources_strictly_parsed_and_schema_admitted": all(
                not parse_issues[role] for role in ROLE_SCHEMAS
            ),
            "typed_mappings_validated": all(
                artifact["payload"]["validation_status"] == "validated"
                for artifact in (bundle_mapping, result_mapping, observation_mapping)
            ),
            "legacy_receipt_recomputed": typed["assessment"]["recomputed_receipt"] is not None,
            "supplied_receipt_matches_recomputed_semantics": typed["status"] == "PASS",
            "supplied_receipt_status_pass": parsed["receipt"] is not None and parsed["receipt"].get("status") == "PASS",
        },
        "prohibited_inferences": [
            "Do not infer job submission or execution authenticity.",
            "Do not authenticate provider or job identity.",
            "Do not authenticate reported chronology.",
            "Do not infer hardware execution, physical fidelity or correctness of the executed circuit.",
            "Do not infer computational advantage, F3 authentication or arbitrary scalability.",
        ],
        "boundaries": list(LIMITATIONS),
    }
    claim = build_artifact(
        "claim",
        claim_payload,
        created_at=created_at,
        actor=actor,
        source_refs=tuple(claim_payload["evidence_refs"]),
        capabilities_required=("claim.boundary",),
        limitations=LIMITATIONS,
    )

    artifacts = [
        sources["bundle"],
        sources["result"],
        sources["receipt"],
        representations["bundle"],
        representations["result"],
        representations["receipt"],
        intent,
        execution,
        observation,
        assessment,
        bundle_mapping,
        result_mapping,
        observation_mapping,
        receipt_mapping,
        claim,
    ]
    relations = [
        build_relation("transforms", sources[role]["artifact_id"], representations[role]["artifact_id"], criterion={"id": "e7q.ir.legacy-json-projection", "version": "1"}, preserves=SOURCE_PRESERVES, loses=SOURCE_LOSSES, assumptions=SOURCE_ASSUMPTIONS, validation_status=_validation_status(representations[role]["payload"]["mapping_status"]))
        for role in ("bundle", "result", "receipt")
    ] + [
        build_relation("transforms", representations["bundle"]["artifact_id"], intent["artifact_id"], criterion=map_criterion, preserves=bundle_mapping["payload"]["preserves"], loses=bundle_mapping["payload"]["loses"], assumptions=bundle_mapping["payload"]["assumptions"], validation_status=bundle_mapping["payload"]["validation_status"]),
        build_relation("transforms", representations["result"]["artifact_id"], execution["artifact_id"], criterion=map_criterion, preserves=result_mapping["payload"]["preserves"], loses=result_mapping["payload"]["loses"], assumptions=result_mapping["payload"]["assumptions"], validation_status=result_mapping["payload"]["validation_status"]),
        build_relation("constrains", intent["artifact_id"], execution["artifact_id"], validation_status=_validation_status(typed["status"])),
        build_relation("transforms", execution["artifact_id"], observation["artifact_id"], criterion=observation_mapping["payload"]["criterion"], preserves=observation_mapping["payload"]["preserves"], loses=observation_mapping["payload"]["loses"], assumptions=observation_mapping["payload"]["assumptions"], validation_status=observation_mapping["payload"]["validation_status"]),
        build_relation("assesses", observation["artifact_id"], assessment["artifact_id"], criterion=CRITERION, validation_status=mapping_status),
        build_relation("assesses", representations["receipt"]["artifact_id"], assessment["artifact_id"], criterion=CRITERION, validation_status=mapping_status),
        build_relation("supports", assessment["artifact_id"], claim["artifact_id"], criterion=CRITERION, validation_status="supported" if supported else "failed"),
    ]
    request_identity = {
        "format": WORKFLOW_FORMAT,
        "sources": {
            role: {
                "content_digest": sources[role]["payload"]["content_digest"],
                "stable_source_ref": refs[role],
            }
            for role in ("bundle", "result", "receipt")
        },
        "count_label_order": count_label_order,
        "criterion": CRITERION,
        "created_at": created_at,
        "actor": actor,
        "name": name,
    }
    graph = build_graph(
        artifacts,
        relations,
        name=name,
        extensions={
            "workflow_format": WORKFLOW_FORMAT,
            "workflow_request_id": digest(request_identity),
            "source_refs": refs,
            "count_label_order": count_label_order,
            "assessment_status": typed["status"],
            "assessment_reason": typed["reason"],
            "f2_boundary": "No legacy receipt semantic validator is registered; F2 must remain NOT_ASSESSED or BLOCKED rather than trust an imported verdict.",
        },
    )
    if validate_graph(graph, level="F1")["status"] != "PASS":
        raise E7QError("constructed legacy receipt graph failed F1 validation")
    validation = validate_legacy_receipt_evidence(graph)
    if supported and validation["status"] != "PASS":
        raise E7QError(
            "legacy receipt evidence failed internal consistency validation: "
            + validation.get("message", validation.get("reason", "unknown inconsistency"))
        )
    return graph


def recover_legacy_source(graph: dict[str, Any], stable_source_ref: str) -> bytes:
    """Recover one exact supplied input after F1, size and digest checks."""
    if validate_graph(graph, level="F1")["status"] != "PASS":
        raise E7QError("cannot recover source from an invalid graph")
    matches = [
        artifact for artifact in graph["artifacts"]
        if artifact["kind"] == "source"
        and artifact["payload"].get("adapter") == SOURCE_ADAPTER
        and artifact["payload"].get("stable_source_ref") == stable_source_ref
    ]
    if len(matches) != 1:
        raise E7QError("stable_source_ref must identify exactly one legacy source")
    payload = matches[0]["payload"]
    try:
        raw = b64decode(payload["content_base64"], validate=True)
    except (BinasciiError, KeyError, TypeError, ValueError) as exc:
        raise E7QError("invalid preserved legacy source encoding") from exc
    if len(raw) > MAX_BYTES or type(payload.get("byte_length")) is not int or len(raw) != payload["byte_length"]:
        raise E7QError("preserved legacy source size mismatch")
    if payload.get("content_digest") != _raw_digest(raw):
        raise E7QError("preserved legacy source digest mismatch")
    return raw


def validate_legacy_receipt_evidence(graph: dict[str, Any]) -> dict[str, Any]:
    """Reparse all preserved inputs and rerun legacy receipt semantics."""
    if validate_graph(graph, level="F1")["status"] != "PASS":
        return {"status": "FAIL", "reason": "f1_invalid", "checks": []}
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, message: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "message": message})
        if not passed:
            raise E7QError(message)

    try:
        refs = graph.get("extensions", {}).get("source_refs")
        check("source-reference-map", isinstance(refs, dict) and set(refs) == set(ROLE_SCHEMAS), "legacy source reference map is missing or inconsistent")
        raw = {role: recover_legacy_source(graph, refs[role]) for role in ROLE_SCHEMAS}
        parsed: dict[str, dict[str, Any] | None] = {}
        issues: dict[str, list[dict[str, str]]] = {}
        for role in ROLE_SCHEMAS:
            parsed[role], issues[role] = _strict_object(raw[role], role)
        representations = {
            role: next(
                artifact for artifact in graph["artifacts"]
                if artifact["payload"].get("format") == REPRESENTATION_FORMAT
                and artifact["payload"].get("role") == role
            )
            for role in ROLE_SCHEMAS
        }
        for role in ROLE_SCHEMAS:
            expected = _representation_payload(role, parsed[role], issues[role])
            check(f"representation:{role}", representations[role]["payload"] == expected, f"typed {role} representation contradicts preserved bytes")
        typed = _typed_payloads(
            parsed["bundle"], raw["bundle"],
            parsed["result"], raw["result"],
            parsed["receipt"], raw["receipt"],
            label_order=graph["extensions"]["count_label_order"],
            representation_refs={role: representations[role]["artifact_id"] for role in ROLE_SCHEMAS},
        )
        intent = next(artifact for artifact in graph["artifacts"] if artifact["payload"].get("format") == INTENT_FORMAT)
        execution = next(artifact for artifact in graph["artifacts"] if artifact["payload"].get("format") == EXECUTION_FORMAT)
        observation = next(artifact for artifact in graph["artifacts"] if artifact["payload"].get("format") == OBSERVATION_FORMAT)
        assessment = next(artifact for artifact in graph["artifacts"] if artifact["payload"].get("format") == ASSESSMENT_FORMAT)
        expected_execution = dict(typed["execution"])
        expected_execution["intent_ref"] = intent["artifact_id"]
        expected_observation = dict(typed["observation"])
        expected_observation["input_refs"] = [execution["artifact_id"]]
        expected_observation["provider_report_ref"] = execution["artifact_id"]
        expected_assessment = json.loads(json.dumps(typed["assessment"]))
        expected_assessment["execution_intent_ref"] = intent["artifact_id"]
        expected_assessment["execution_record_ref"] = execution["artifact_id"]
        expected_assessment["observation_ref"] = observation["artifact_id"]
        expected_assessment["assessment_id"] = digest(expected_assessment)
        check("typed-intent", intent["payload"] == typed["intent"], "typed execution intent contradicts the supplied bundle")
        check("typed-execution", execution["payload"] == expected_execution, "typed execution record contradicts the supplied result")
        check("typed-observation", observation["payload"] == expected_observation, "typed observation contradicts supplied counts")
        check("receipt-assessment", assessment["payload"] == expected_assessment, "receipt assessment contradicts independent recomputation")
        transformations = [
            artifact for artifact in graph["artifacts"]
            if artifact["payload"].get("format") == TRANSFORMATION_FORMAT
        ]
        check("transformation-count", len(transformations) == 4, "legacy workflow requires four typed transformation records")
        for transformation in transformations:
            payload = transformation["payload"]
            carrier = dict(payload)
            identity = carrier.pop("transformation_id", None)
            check(
                f"transformation:{payload.get('name')}",
                identity == digest(carrier),
                "typed transformation identity is inconsistent",
            )
        claim = next(artifact for artifact in graph["artifacts"] if artifact["kind"] == "claim")
        expected_support = "supported-within-declared-scope" if typed["status"] == "PASS" else "unsupported"
        check("claim-support", claim["payload"].get("support_status") == expected_support, "claim support contradicts recomputed receipt status")
        check("claim-boundary", claim["payload"].get("claim_type") == CLAIM_TYPE and claim["payload"].get("statement") == "The supplied bundle and result are internally consistent and the typed mapping agrees with independently recomputed legacy receipt semantics under the declared offline criterion.", "claim boundary is inconsistent")
        return {"status": typed["status"], "reason": typed["reason"], "checks": checks}
    except (E7QError, KeyError, StopIteration, TypeError, ValueError) as exc:
        return {
            "status": "FAIL",
            "reason": "legacy_receipt_evidence_inconsistent",
            "message": str(exc),
            "checks": checks,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--count-label-order", required=True)
    parser.add_argument("--created-at", required=True)
    parser.add_argument("--bundle-source-ref", required=True)
    parser.add_argument("--result-source-ref", required=True)
    parser.add_argument("--receipt-source-ref", required=True)
    parser.add_argument("--name", default="Typed legacy execution receipt mapping")
    parser.add_argument("--actor", default="e7q.ir.legacy-execution-receipt-workflow")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    inputs = (args.bundle, args.result, args.receipt)
    try:
        output = args.output.resolve()
        if any(path.resolve() == output or (args.output.exists() and path.samefile(args.output)) for path in inputs):
            raise E7QError("output must not overwrite any input file")
        graph = build_legacy_receipt_graph(
            args.bundle,
            args.result,
            args.receipt,
            count_label_order=args.count_label_order,
            created_at=args.created_at,
            bundle_source_ref=args.bundle_source_ref,
            result_source_ref=args.result_source_ref,
            receipt_source_ref=args.receipt_source_ref,
            name=args.name,
            actor=args.actor,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(canonical_bytes(graph) + b"\n")
    except (OSError, E7QError, ValueError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
