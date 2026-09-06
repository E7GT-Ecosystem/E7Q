# SPDX-License-Identifier: Apache-2.0
"""External circuit workflow demonstrator for E7Q-IR v0alpha1."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from ..language import E7QError
from .envelope import build_artifact
from .graph import build_graph, build_relation


MANIFEST_SCHEMA = "e7q.ir.external-circuit-workflow/v0alpha1"


def _raw_digest(value: bytes) -> str:
    return "sha256:" + sha256(value).hexdigest()


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise E7QError(f"E7Q-IR {label} must be an object")
    return value


def load_external_circuit_manifest(path: str | Path) -> tuple[dict[str, Any], Path]:
    source = Path(path)
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise E7QError(f"invalid E7Q-IR workflow manifest: {exc}") from exc
    manifest = _object(value, "workflow manifest")
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise E7QError(f"E7Q-IR workflow manifest must use {MANIFEST_SCHEMA}")
    return manifest, source.parent


def _read_bytes(base: Path, relative: Any, label: str) -> tuple[Path, bytes]:
    if not isinstance(relative, str) or not relative:
        raise E7QError(f"E7Q-IR {label} path must be a non-empty string")
    base = base.resolve()
    candidate = Path(relative)
    if candidate.is_absolute():
        raise E7QError(f"E7Q-IR {label} path must be relative to the manifest")
    path = (base / candidate).resolve()
    if not path.is_relative_to(base):
        raise E7QError(f"E7Q-IR {label} path escapes the manifest directory")
    try:
        return path, path.read_bytes()
    except OSError as exc:
        raise E7QError(f"cannot read E7Q-IR {label}: {exc}") from exc


def _counts(base: Path, relative: Any) -> tuple[dict[str, int], int, str]:
    path, raw = _read_bytes(base, relative, "counts")
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise E7QError(f"invalid E7Q-IR counts JSON: {exc}") from exc
    declared_shots = value.get("shots") if isinstance(value, dict) else None
    counts_value = value.get("counts") if isinstance(value, dict) and "counts" in value else value
    counts = _object(counts_value, "counts")
    normalized: dict[str, int] = {}
    width: int | None = None
    for outcome, count in counts.items():
        if not isinstance(outcome, str) or not outcome or set(outcome) - {"0", "1"}:
            raise E7QError("E7Q-IR count outcomes must be binary strings")
        if width is None:
            width = len(outcome)
        if len(outcome) != width:
            raise E7QError("E7Q-IR count outcomes must have a common width")
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise E7QError("E7Q-IR counts must be non-negative integers")
        normalized[outcome] = count
    shots = sum(normalized.values())
    if not normalized or shots < 1:
        raise E7QError("E7Q-IR counts must contain at least one observed shot")
    if declared_shots is not None and declared_shots != shots:
        raise E7QError("E7Q-IR declared shots do not match the count total")
    return dict(sorted(normalized.items())), shots, _raw_digest(raw)


def _expected_distribution(value: Any) -> dict[str, float]:
    distribution = _object(value, "expected distribution")
    normalized: dict[str, float] = {}
    for outcome, probability in distribution.items():
        if not isinstance(outcome, str) or not outcome or set(outcome) - {"0", "1"}:
            raise E7QError("E7Q-IR expected outcomes must be binary strings")
        if not isinstance(probability, (int, float)) or isinstance(probability, bool):
            raise E7QError("E7Q-IR expected probabilities must be numbers")
        probability = float(probability)
        if probability < 0.0 or probability > 1.0:
            raise E7QError("E7Q-IR expected probabilities must be between zero and one")
        normalized[outcome] = probability
    if not normalized or abs(sum(normalized.values()) - 1.0) > 1e-9:
        raise E7QError("E7Q-IR expected probabilities must sum to one")
    return dict(sorted(normalized.items()))


def _strings(value: Any, label: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise E7QError(f"E7Q-IR {label} must be a list of non-empty strings")
    if nonempty and not value:
        raise E7QError(f"E7Q-IR {label} must not be empty")
    return list(value)


def build_external_circuit_graph(
    manifest: dict[str, Any],
    base: str | Path = ".",
) -> dict[str, Any]:
    """Build a bounded graph without importing or executing the supplied circuit."""
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise E7QError(f"E7Q-IR workflow manifest must use {MANIFEST_SCHEMA}")
    base_path = Path(base)
    name = manifest.get("name")
    created_at = manifest.get("created_at")
    actor = manifest.get("actor", "unspecified")
    if not isinstance(name, str) or not name:
        raise E7QError("E7Q-IR workflow name must be a non-empty string")
    if not isinstance(created_at, str) or not created_at:
        raise E7QError("E7Q-IR workflow created_at must be a non-empty string")
    if not isinstance(actor, str) or not actor:
        raise E7QError("E7Q-IR workflow actor must be a non-empty string")

    source_spec = _object(manifest.get("source"), "source declaration")
    executable_spec = _object(manifest.get("executable"), "executable declaration")
    transformation_spec = _object(manifest.get("transformation"), "transformation declaration")
    observation_spec = _object(manifest.get("observation"), "observation declaration")
    assessment_spec = _object(manifest.get("assessment"), "assessment declaration")
    claim_spec = _object(manifest.get("claim"), "claim declaration")

    source_path, source_bytes = _read_bytes(base_path, source_spec.get("path"), "source circuit")
    executable_path, executable_bytes = _read_bytes(
        base_path,
        executable_spec.get("path"),
        "executable circuit",
    )
    counts, shots, counts_digest = _counts(base_path, observation_spec.get("counts_path"))
    expected = _expected_distribution(assessment_spec.get("expected_distribution"))
    threshold = assessment_spec.get("max_total_variation")
    if (
        not isinstance(threshold, (int, float))
        or isinstance(threshold, bool)
        or not 0 <= float(threshold) <= 1
    ):
        raise E7QError("E7Q-IR max_total_variation must be between zero and one")
    threshold = float(threshold)
    observed = {outcome: count / shots for outcome, count in counts.items()}
    outcomes = set(observed) | set(expected)
    tvd = 0.5 * sum(abs(observed.get(item, 0.0) - expected.get(item, 0.0)) for item in outcomes)
    assessment_passed = tvd <= threshold

    common = {"created_at": created_at, "actor": actor, "profile_id": "e7q.ir.circuit-basic"}
    source = build_artifact(
        "source",
        {
            "name": source_path.name,
            "format": source_spec.get("format", "openqasm"),
            "media_type": "text/plain",
            "content_digest": _raw_digest(source_bytes),
            "byte_length": len(source_bytes),
            "role": "declared source circuit",
        },
        capabilities_required=["artifact.identity", "circuit.openqasm.source"],
        limitations=[
            "The source is identified as supplied bytes; E7Q-IR does not "
            "execute it during graph construction."
        ],
        **common,
    )
    representation = build_artifact(
        "representation",
        {
            "name": executable_path.name,
            "format": executable_spec.get("format", "openqasm"),
            "media_type": "text/plain",
            "content_digest": _raw_digest(executable_bytes),
            "byte_length": len(executable_bytes),
            "role": "declared executable representation",
        },
        capabilities_required=["artifact.identity", "circuit.openqasm.source"],
        source_refs=[source["artifact_id"]],
        limitations=[
            "Representation identity does not establish semantic equivalence "
            "to the source circuit."
        ],
        **common,
    )
    criterion = _object(transformation_spec.get("criterion"), "transformation criterion")
    preserves = _strings(transformation_spec.get("preserves"), "preserves")
    loses = _strings(transformation_spec.get("loses"), "loses")
    assumptions = _strings(transformation_spec.get("assumptions"), "assumptions")
    transformation = build_artifact(
        "transformation",
        {
            "tool": transformation_spec.get("tool", "unspecified"),
            "tool_version": transformation_spec.get("tool_version", "unspecified"),
            "input_refs": [source["artifact_id"]],
            "output_refs": [representation["artifact_id"]],
            "criterion": criterion,
            "preserves": preserves,
            "loses": loses,
            "assumptions": assumptions,
            "validation_status": "declared-not-verified",
        },
        capabilities_required=["transformation.accounting"],
        source_refs=[source["artifact_id"], representation["artifact_id"]],
        limitations=[
            "Preservation and loss entries are declarations until a semantic "
            "profile validates them."
        ],
        **common,
    )
    execution = build_artifact(
        "execution",
        {
            "provider": observation_spec.get("provider", "unspecified"),
            "job_id": observation_spec.get("job_id", "unspecified"),
            "target": observation_spec.get("target", "unspecified"),
            "completed_at": observation_spec.get("completed_at"),
            "authentication_status": "not-authenticated",
            "witness_status": "not-witnessed-by-e7q",
        },
        capabilities_required=["observation.record"],
        source_refs=[representation["artifact_id"]],
        limitations=[
            "Provider, job, target, and chronology are supplied and not "
            "authenticated by E7Q."
        ],
        **common,
    )
    observation = build_artifact(
        "observation",
        {
            "counts": counts,
            "shots": shots,
            "counts_digest": counts_digest,
            "label_order": observation_spec.get("label_order", "declared-unspecified"),
            "status": "supplied-not-authenticated",
        },
        capabilities_required=["observation.record", "circuit.counts.observation"],
        source_refs=[execution["artifact_id"]],
        limitations=[
            "Aggregate counts do not reconstruct shot order, device history, "
            "or intermediate quantum states."
        ],
        **common,
    )
    assessment = build_artifact(
        "assessment",
        {
            "method": "total-variation-distance",
            "observation_ref": observation["artifact_id"],
            "expected_distribution": expected,
            "observed_distribution": dict(sorted(observed.items())),
            "total_variation_distance": tvd,
            "maximum_total_variation": threshold,
            "status": "PASS" if assessment_passed else "FAIL",
            "scope": "descriptive distribution comparison",
        },
        capabilities_required=["circuit.distribution.tvd"],
        source_refs=[observation["artifact_id"]],
        limitations=[
            "This descriptive assessment does not authenticate execution or "
            "establish physical fidelity."
        ],
        **common,
    )
    statement = claim_spec.get("statement")
    if not isinstance(statement, str) or not statement:
        raise E7QError("E7Q-IR claim statement must be a non-empty string")
    boundaries = _strings(claim_spec.get("boundaries"), "claim boundaries", nonempty=True)
    prohibited = _strings(
        claim_spec.get("prohibited_inferences"),
        "prohibited inferences",
        nonempty=True,
    )
    claim = build_artifact(
        "claim",
        {
            "statement": statement,
            "claim_type": claim_spec.get("claim_type", "statistical"),
            "evidence_refs": [assessment["artifact_id"]],
            "support_status": (
                "supported-within-declared-scope"
                if assessment_passed
                else "unsupported"
            ),
            "boundaries": boundaries,
            "prohibited_inferences": prohibited,
        },
        capabilities_required=["claim.boundary", "circuit.distribution.tvd"],
        source_refs=[assessment["artifact_id"]],
        limitations=boundaries,
        **common,
    )

    relation_values = [
        build_relation(
            "transforms",
            source["artifact_id"],
            representation["artifact_id"],
            criterion=criterion,
            preserves=preserves,
            loses=loses,
            assumptions=assumptions,
            validation_status="declared-not-verified",
        ),
        build_relation("produces", representation["artifact_id"], execution["artifact_id"]),
        build_relation("observes", execution["artifact_id"], observation["artifact_id"]),
        build_relation(
            "assesses",
            observation["artifact_id"],
            assessment["artifact_id"],
            validation_status="validated",
        ),
        build_relation(
            "supports",
            assessment["artifact_id"],
            claim["artifact_id"],
            validation_status="supported" if assessment_passed else "failed",
        ),
    ]
    return build_graph(
        [source, representation, transformation, execution, observation, assessment, claim],
        relation_values,
        name=name,
        extensions={
            "workflow_schema": MANIFEST_SCHEMA,
            "construction_boundary": (
                "Files were hashed and counts were assessed; circuit semantics, provider identity, "
                "execution chronology, and physical fidelity were not authenticated or verified."
            ),
        },
    )
