# SPDX-License-Identifier: Apache-2.0
"""External circuit-pair validation as a complete E7Q-IR evidence graph."""
from __future__ import annotations

import argparse
from base64 import b64decode, b64encode
from binascii import Error as BinasciiError
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
import math
from pathlib import Path
import tempfile
from typing import Any, Callable

from ..language import E7QError
from ..openqasm2 import import_openqasm2
from .canonical import canonical_bytes, digest
from .circuit import MAX_SOURCE_BYTES
from .conformance import validate_graph
from .envelope import build_artifact
from .graph import build_graph, build_relation
from .qcec import (
    BACKEND_ID,
    NUMERICAL_EXACT_CRITERION,
    NUMERICAL_GLOBAL_PHASE_CRITERION,
    SUPPORTED_BACKEND_VERSION,
    evaluate,
)

WORKFLOW_FORMAT = "e7q.ir.external-qcec-workflow/v1"
SOURCE_ADAPTER = "e7q.ir.external-qcec-source/v1"
CRITERIA = {
    NUMERICAL_EXACT_CRITERION["id"]: NUMERICAL_EXACT_CRITERION,
    NUMERICAL_GLOBAL_PHASE_CRITERION["id"]: NUMERICAL_GLOBAL_PHASE_CRITERION,
}
LIMITATIONS = (
    "Only the captured OpenQASM 2 snapshots are parsed and evaluated.",
    "QCEC numerical criteria are not exact-algebraic E7Q-IR criteria.",
    "A PASS applies only to the explicitly requested numerical criterion and recorded tolerances.",
    "Structured fixtures above 25 qubits do not establish general tractability for arbitrary circuits.",
    "No provider authenticity, hardware execution, physical fidelity or production readiness is established.",
)


def _raw_digest(raw: bytes) -> str:
    return "sha256:" + sha256(raw).hexdigest()


def _package_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "unavailable"


def _finite_positive(value: Any, label: str) -> float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(float(value))
        or value <= 0
    ):
        raise E7QError(f"{label} must be a positive finite number")
    return float(value)


def _read_snapshot(path: str | Path, label: str) -> tuple[Path, bytes]:
    source = Path(path)
    try:
        with source.open("rb") as stream:
            raw = stream.read(MAX_SOURCE_BYTES + 1)
    except OSError as exc:
        raise E7QError(f"cannot read {label} circuit: {exc}") from exc
    if len(raw) > MAX_SOURCE_BYTES:
        raise E7QError(f"{label} circuit exceeds the {MAX_SOURCE_BYTES}-byte input budget")
    return source, raw


def _criterion_record(criterion_id: str, numerical_tolerance: float, fidelity_threshold: float) -> dict[str, Any]:
    criterion = CRITERIA.get(criterion_id)
    if criterion is None:
        raise E7QError("unsupported QCEC numerical criterion")
    return {
        "id": criterion_id,
        "version": criterion["version"],
        "options": {
            **criterion["options"],
            "numerical_tolerance": numerical_tolerance,
            "fidelity_threshold": fidelity_threshold,
        },
    }


def _source_artifact(
    raw: bytes,
    *,
    role: str,
    display_name: str,
    source_ref: str,
    created_at: str,
    actor: str,
) -> dict[str, Any]:
    return build_artifact(
        "source",
        {
            "format": "openqasm-2-source-bytes",
            "adapter": SOURCE_ADAPTER,
            "role": role,
            "display_name": display_name,
            "stable_source_ref": source_ref,
            "content_encoding": "base64",
            "content_base64": b64encode(raw).decode("ascii"),
            "content_digest": _raw_digest(raw),
            "byte_length": len(raw),
        },
        created_at=created_at,
        actor=actor,
        capabilities_required=("artifact.identity",),
        limitations=LIMITATIONS,
    )


def _parse_representation(
    source: dict[str, Any], raw: bytes, *, role: str, display_name: str,
    created_at: str, actor: str,
) -> tuple[dict[str, Any], dict[str, str] | None]:
    error: dict[str, str] | None = None
    parsed: dict[str, Any] | None = None
    try:
        text = raw.decode("utf-8")
        parsed = dict(import_openqasm2(text, name=display_name))
    except (UnicodeDecodeError, E7QError) as exc:
        error = {"type": type(exc).__name__, "message": str(exc)}
    payload: dict[str, Any] = {
        "format": "e7q.openqasm2-circuit/v1alpha1",
        "role": role,
        "source_ref": source["artifact_id"],
        "parse_status": "PASS" if error is None else "UNSUPPORTED",
        "parsed": parsed,
    }
    if error is not None:
        payload["error"] = error
    return build_artifact(
        "representation",
        payload,
        created_at=created_at,
        actor=actor,
        source_refs=(source["artifact_id"],),
        capabilities_required=("artifact.identity",),
        limitations=LIMITATIONS,
    ), error


def _unsupported_assessment(
    representation_refs: tuple[str, str], *, criterion: dict[str, Any],
    timeout_seconds: float, memory_limit_bytes: int, nthreads: int,
    max_simulations: int, seed: int, errors: list[dict[str, str]],
    created_at: str, actor: str,
) -> dict[str, Any]:
    payload = {
        "format": "e7q.ir.external-equivalence-assessment/v1",
        "criterion": criterion,
        "backend": {
            "id": BACKEND_ID,
            "version": _package_version("mqt.qcec"),
            "supported_version": SUPPORTED_BACKEND_VERSION,
            "dependency_versions": {"mqt.core": _package_version("mqt.core")},
            "license": "MIT",
        },
        "configuration": {
            "timeout_seconds": timeout_seconds,
            "nthreads": nthreads,
            "parallel": False,
            "max_simulations": max_simulations,
            "seed": seed,
            "memory_limit_bytes": memory_limit_bytes,
            "numerical_tolerance": criterion["options"]["numerical_tolerance"],
            "fidelity_threshold": criterion["options"]["fidelity_threshold"],
        },
        "method": {"kind": "tolerance-based-numerical", "exact_algebraic": False, "backend_checkers": []},
        "outcome": {
            "status": "UNSUPPORTED",
            "conclusion": "INCONCLUSIVE",
            "raw_verdict": "unsupported_input",
            "reason": "unsupported_input",
            "timed_out": False,
            "resource_exhausted": False,
            "universal_equivalence_established": False,
        },
        "resource_use": {
            "wall_clock_seconds": 0.0,
            "wall_clock_limit_enforced": False,
            "wall_clock_limit_mechanism": "not-started-input-rejected",
            "worker_peak_rss_bytes": None,
            "memory_measurement_scope": "worker-not-started",
            "memory_limit_requested_bytes": memory_limit_bytes,
            "memory_limit_enforced": False,
            "memory_limit_mechanism": "not-started-input-rejected",
            "memory_limit_effective_bytes": None,
        },
        "worker": {
            "start_method": "spawn",
            "started": False,
            "pid": None,
            "exit_code": None,
            "signal": None,
            "signal_name": None,
            "termination_mechanism": None,
            "reaped": True,
        },
        "raw_result": {},
        "input_errors": errors,
        "assumptions": [
            "input-syntax-must-pass-the-bounded-openqasm2-importer-before-qcec-execution",
            "global-phase-acceptance-follows-only-the-requested-criterion",
            "numerical-tolerances-are-part-of-the-recorded-method",
        ],
    }
    payload["assessment_id"] = digest(payload)
    return build_artifact(
        "assessment",
        payload,
        profile_id="e7q.ir.core",
        profile_version="0alpha1",
        capabilities_required=("artifact.identity",),
        created_at=created_at,
        actor=actor,
        source_refs=representation_refs,
        limitations=LIMITATIONS,
    )


def build_external_qcec_graph(
    left: str | Path,
    right: str | Path,
    *,
    criterion_id: str,
    numerical_tolerance: float,
    fidelity_threshold: float,
    timeout_seconds: float,
    memory_limit_bytes: int,
    created_at: str,
    left_source_ref: str,
    right_source_ref: str,
    name: str = "External QCEC circuit-pair validation",
    actor: str = "e7q.ir.external-qcec-workflow",
    nthreads: int = 1,
    max_simulations: int = 16,
    seed: int = 0,
    verify_backend: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Capture, parse and assess two external circuit files without weakening claims."""
    numerical_tolerance = _finite_positive(numerical_tolerance, "numerical_tolerance")
    fidelity_threshold = _finite_positive(fidelity_threshold, "fidelity_threshold")
    if fidelity_threshold > 1:
        raise E7QError("fidelity_threshold must not exceed one")
    timeout_seconds = _finite_positive(timeout_seconds, "timeout_seconds")
    if type(memory_limit_bytes) is not int or memory_limit_bytes <= 0:
        raise E7QError("memory_limit_bytes must be a positive integer")
    if type(nthreads) is not int or nthreads < 1:
        raise E7QError("nthreads must be a positive integer")
    if type(max_simulations) is not int or max_simulations < 0:
        raise E7QError("max_simulations must be a non-negative integer")
    if type(seed) is not int or seed < 0:
        raise E7QError("seed must be a non-negative integer")
    for value, label in ((created_at, "created_at"), (left_source_ref, "left_source_ref"),
                         (right_source_ref, "right_source_ref"), (name, "name"), (actor, "actor")):
        if not isinstance(value, str) or not value:
            raise E7QError(f"{label} must be a non-empty string")

    criterion = _criterion_record(criterion_id, numerical_tolerance, fidelity_threshold)
    left_path, left_raw = _read_snapshot(left, "left")
    right_path, right_raw = _read_snapshot(right, "right")
    left_source = _source_artifact(
        left_raw, role="left", display_name=left_path.name, source_ref=left_source_ref,
        created_at=created_at, actor=actor,
    )
    right_source = _source_artifact(
        right_raw, role="right", display_name=right_path.name, source_ref=right_source_ref,
        created_at=created_at, actor=actor,
    )
    left_representation, left_error = _parse_representation(
        left_source, left_raw, role="left", display_name=left_path.name,
        created_at=created_at, actor=actor,
    )
    right_representation, right_error = _parse_representation(
        right_source, right_raw, role="right", display_name=right_path.name,
        created_at=created_at, actor=actor,
    )
    representation_refs = (left_representation["artifact_id"], right_representation["artifact_id"])
    errors = [error for error in (left_error, right_error) if error is not None]
    if errors:
        assessment = _unsupported_assessment(
            representation_refs, criterion=criterion, timeout_seconds=timeout_seconds,
            memory_limit_bytes=memory_limit_bytes, nthreads=nthreads,
            max_simulations=max_simulations, seed=seed, errors=errors,
            created_at=created_at, actor=actor,
        )
    else:
        with tempfile.TemporaryDirectory(prefix="e7q-qcec-snapshot-") as directory:
            snapshot_root = Path(directory)
            left_snapshot = snapshot_root / "left.qasm"
            right_snapshot = snapshot_root / "right.qasm"
            left_snapshot.write_bytes(left_raw)
            right_snapshot.write_bytes(right_raw)
            assessment = evaluate(
                left_snapshot,
                right_snapshot,
                criterion=CRITERIA[criterion_id],
                source_refs=representation_refs,
                created_at=created_at,
                timeout_seconds=timeout_seconds,
                memory_limit_bytes=memory_limit_bytes,
                numerical_tolerance=numerical_tolerance,
                fidelity_threshold=fidelity_threshold,
                nthreads=nthreads,
                max_simulations=max_simulations,
                seed=seed,
                verify_backend=verify_backend,
            )

    outcome = assessment["payload"]["outcome"]
    passed = outcome["status"] == "PASS"
    relation_name = (
        "numerical unitary equivalence"
        if criterion_id == NUMERICAL_EXACT_CRITERION["id"]
        else "numerical equivalence up to global phase"
    )
    claim = build_artifact(
        "claim",
        {
            "statement": f"The captured circuit pair passes {relation_name} under the recorded QCEC configuration.",
            "claim_type": "bounded-numerical-circuit-equivalence",
            "requested_criterion": criterion,
            "evidence_refs": [assessment["artifact_id"]],
            "support_status": "supported-within-declared-scope" if passed else "unsupported",
            "boundaries": list(LIMITATIONS),
            "prohibited_inferences": [
                "Do not infer exact-algebraic equivalence from this numerical assessment.",
                "Do not infer global-phase acceptance when numerical-unitary was requested.",
                "Do not infer arbitrary-circuit scalability, provider authenticity or physical fidelity.",
            ],
        },
        created_at=created_at,
        actor=actor,
        source_refs=(assessment["artifact_id"],),
        capabilities_required=("claim.boundary",),
        limitations=LIMITATIONS,
    )
    relation_status = "validated" if passed else "failed"
    relations = [
        build_relation("represents", left_source["artifact_id"], left_representation["artifact_id"],
                       validation_status="validated" if left_error is None else "failed"),
        build_relation("represents", right_source["artifact_id"], right_representation["artifact_id"],
                       validation_status="validated" if right_error is None else "failed"),
        build_relation("assesses", left_representation["artifact_id"], assessment["artifact_id"],
                       criterion=criterion, validation_status=relation_status),
        build_relation("assesses", right_representation["artifact_id"], assessment["artifact_id"],
                       criterion=criterion, validation_status=relation_status),
        build_relation("supports", assessment["artifact_id"], claim["artifact_id"],
                       criterion=criterion, validation_status="supported" if passed else "failed"),
    ]
    request_identity = {
        "format": WORKFLOW_FORMAT,
        "source_digests": [_raw_digest(left_raw), _raw_digest(right_raw)],
        "source_refs": [left_source_ref, right_source_ref],
        "criterion": criterion,
        "limits": {"timeout_seconds": timeout_seconds, "memory_limit_bytes": memory_limit_bytes},
        "configuration": {"nthreads": nthreads, "max_simulations": max_simulations, "seed": seed},
        "created_at": created_at,
        "actor": actor,
        "name": name,
    }
    graph = build_graph(
        [left_source, right_source, left_representation, right_representation, assessment, claim],
        relations,
        name=name,
        extensions={
            "workflow_format": WORKFLOW_FORMAT,
            "workflow_request_id": digest(request_identity),
            "assessment_status": outcome["status"],
            "assessment_reason": outcome["reason"],
            "construction_boundary": "Original bytes and parsed projections are distinct; only captured snapshots reach the isolated QCEC worker.",
        },
    )
    if validate_graph(graph, level="F1")["status"] != "PASS":
        raise E7QError("constructed QCEC evidence graph failed F1 validation")
    return graph


def recover_external_qcec_source(graph: dict[str, Any], source_ref: str) -> bytes:
    """Recover one captured input exactly; digest agreement is not authenticity."""
    if validate_graph(graph, level="F1")["status"] != "PASS":
        raise E7QError("cannot recover source from an invalid graph")
    matches = [
        artifact for artifact in graph["artifacts"]
        if artifact["kind"] == "source"
        and artifact["payload"].get("adapter") == SOURCE_ADAPTER
        and artifact["payload"].get("stable_source_ref") == source_ref
    ]
    if len(matches) != 1:
        raise E7QError("source_ref must identify exactly one preserved input")
    payload = matches[0]["payload"]
    try:
        raw = b64decode(payload["content_base64"], validate=True)
    except (BinasciiError, KeyError, TypeError, ValueError) as exc:
        raise E7QError("invalid preserved source encoding") from exc
    if type(payload.get("byte_length")) is not int or len(raw) != payload["byte_length"]:
        raise E7QError("preserved source size mismatch")
    if payload.get("content_digest") != _raw_digest(raw):
        raise E7QError("preserved source digest mismatch")
    return raw


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("--criterion", required=True, choices=sorted(CRITERIA))
    parser.add_argument("--numerical-tolerance", required=True, type=float)
    parser.add_argument("--fidelity-threshold", required=True, type=float)
    parser.add_argument("--timeout-seconds", required=True, type=float)
    parser.add_argument("--memory-limit-bytes", required=True, type=int)
    parser.add_argument("--created-at", required=True)
    parser.add_argument("--left-source-ref", required=True)
    parser.add_argument("--right-source-ref", required=True)
    parser.add_argument("--name", default="External QCEC circuit-pair validation")
    parser.add_argument("--actor", default="e7q.ir.external-qcec-workflow")
    parser.add_argument("--nthreads", type=int, default=1)
    parser.add_argument("--max-simulations", type=int, default=16)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        output = args.output.resolve()
        for source in (args.left, args.right):
            if source.resolve() == output or (output.exists() and source.samefile(output)):
                raise E7QError("output must not overwrite an input circuit")
        graph = build_external_qcec_graph(
            args.left, args.right, criterion_id=args.criterion,
            numerical_tolerance=args.numerical_tolerance,
            fidelity_threshold=args.fidelity_threshold,
            timeout_seconds=args.timeout_seconds,
            memory_limit_bytes=args.memory_limit_bytes,
            created_at=args.created_at,
            left_source_ref=args.left_source_ref,
            right_source_ref=args.right_source_ref,
            name=args.name, actor=args.actor, nthreads=args.nthreads,
            max_simulations=args.max_simulations, seed=args.seed,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(canonical_bytes(graph) + b"\n")
    except (OSError, E7QError, ValueError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
