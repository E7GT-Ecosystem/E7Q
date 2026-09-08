# SPDX-License-Identifier: Apache-2.0
"""Criterion-bound native E7Q to external OpenQASM 2 comparison workflow."""
from __future__ import annotations

import argparse
from base64 import b64decode, b64encode
from binascii import Error as BinasciiError
from dataclasses import asdict
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
import json
import math
from pathlib import Path
import tempfile
from typing import Any, Callable

from ..language import E7QError, Program, parse, run, verify
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

WORKFLOW_FORMAT = "e7q.ir.native-external-qcec-workflow/v1"
SOURCE_ADAPTER = "e7q.ir.native-external-qcec-source/v1"
PROJECTION_CRITERION = {
    "id": "e7q.ir.unitary-prefix-evaluation-projection",
    "version": "1",
}
CRITERIA = {
    NUMERICAL_EXACT_CRITERION["id"]: NUMERICAL_EXACT_CRITERION,
    NUMERICAL_GLOBAL_PHASE_CRITERION["id"]: NUMERICAL_GLOBAL_PHASE_CRITERION,
}
SUPPORTED_GATES = frozenset({"X", "Y", "Z", "H", "S", "T", "CX", "CZ", "SWAP"})
MAX_QUBITS = 8
MAX_GATES = 256
LIMITATIONS = (
    "The admitted common subset is static and noiseless with one quantum register, one equally wide classical register, supported gates, and terminal identity measurement.",
    "Terminal measurement is retained in the source representations but removed from the QCEC evaluation projections.",
    "QCEC numerical criteria apply only to the unitary prefixes and are not exact-algebraic E7Q-IR criteria.",
    "A PASS applies only to the explicitly requested criterion and recorded tolerances.",
    "No compiler provenance, provider authenticity, hardware execution, physical fidelity, arbitrary-circuit scalability or Phase 2 completion is established.",
)
PROJECTION_PRESERVES = (
    "qubit-width",
    "ordered-supported-unitary-gates",
    "gate-operands",
    "unitary-prefix-semantics-under-the-declared-gate-table",
    "original-representation-reference",
)
PROJECTION_LOSSES = (
    "terminal-measurement-operation-from-evaluation-projection",
    "classical-register-from-evaluation-projection",
    "measurement-outcome-information",
    "source-formatting-and-comments-in-evaluation-projection",
)
PROJECTION_ASSUMPTIONS = (
    "terminal-measurement-map-was-validated-before-projection",
    "selected-qcec-criterion-applies-only-to-the-static-noiseless-unitary-prefix",
    "qelib1-supported-gate-meanings-match-the-pinned-qcec-backend",
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
        raise E7QError(f"cannot read {label} source: {exc}") from exc
    if len(raw) > MAX_SOURCE_BYTES:
        raise E7QError(f"{label} source exceeds the {MAX_SOURCE_BYTES}-byte input budget")
    return source, raw


def _criterion_record(
    criterion_id: str, numerical_tolerance: float, fidelity_threshold: float,
) -> dict[str, Any]:
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
    source_format: str,
    display_name: str,
    source_ref: str,
    created_at: str,
    actor: str,
) -> dict[str, Any]:
    return build_artifact(
        "source",
        {
            "format": source_format,
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


def _json_program(program: Program) -> dict[str, Any]:
    value = asdict(program)
    value["allowed_outcomes"] = (
        sorted(program.allowed_outcomes) if program.allowed_outcomes is not None else None
    )
    return json.loads(json.dumps(value))


def _parse_native_representation(
    source: dict[str, Any], raw: bytes, *, created_at: str, actor: str,
) -> tuple[dict[str, Any], Program | None, list[dict[str, str]]]:
    program: Program | None = None
    errors: list[dict[str, str]] = []
    try:
        program = parse(raw.decode("utf-8"))
    except (UnicodeDecodeError, E7QError) as exc:
        errors.append({
            "role": "native",
            "code": "native_parse_error",
            "status": "UNSUPPORTED",
            "type": type(exc).__name__,
            "message": str(exc),
        })
    payload: dict[str, Any] = {
        "format": "e7q.native-program/v1",
        "role": "native",
        "source_ref": source["artifact_id"],
        "parse_status": "PASS" if program is not None else "UNSUPPORTED",
        "program": _json_program(program) if program is not None else None,
    }
    if errors:
        payload["errors"] = errors
    return build_artifact(
        "representation",
        payload,
        created_at=created_at,
        actor=actor,
        source_refs=(source["artifact_id"],),
        capabilities_required=("artifact.identity",),
        limitations=LIMITATIONS,
    ), program, errors


def _parse_external_representation(
    source: dict[str, Any], raw: bytes, *, display_name: str,
    created_at: str, actor: str,
) -> tuple[dict[str, Any], dict[str, Any] | None, list[dict[str, str]]]:
    parsed: dict[str, Any] | None = None
    errors: list[dict[str, str]] = []
    try:
        parsed = dict(import_openqasm2(raw.decode("utf-8"), name=display_name))
    except (UnicodeDecodeError, E7QError) as exc:
        errors.append({
            "role": "external",
            "code": "external_parse_error",
            "status": "UNSUPPORTED",
            "type": type(exc).__name__,
            "message": str(exc),
        })
    payload: dict[str, Any] = {
        "format": "e7q.openqasm2-circuit/v1alpha1",
        "role": "external",
        "source_ref": source["artifact_id"],
        "parse_status": "PASS" if parsed is not None else "UNSUPPORTED",
        "parsed": parsed,
    }
    if errors:
        payload["errors"] = errors
    return build_artifact(
        "representation",
        payload,
        created_at=created_at,
        actor=actor,
        source_refs=(source["artifact_id"],),
        capabilities_required=("artifact.identity",),
        limitations=LIMITATIONS,
    ), parsed, errors


def _error(role: str, code: str, message: str, status: str = "UNSUPPORTED") -> dict[str, str]:
    return {"role": role, "code": code, "status": status, "type": "AdmissionError", "message": message}


def _admit_native(program: Program | None) -> tuple[list[tuple[str, tuple[int, ...]]], list[tuple[int, int]], list[dict[str, str]]]:
    if program is None:
        return [], [], []
    errors: list[dict[str, str]] = []
    if program.backend != "statevector":
        errors.append(_error("native", "noise_or_nonunitary_backend", "native comparison requires the noiseless statevector backend"))
    if program.qubits > MAX_QUBITS:
        errors.append(_error("native", "qubit_budget", f"native comparison exceeds the {MAX_QUBITS}-qubit budget", "BLOCKED"))
    if program.bits != program.qubits:
        errors.append(_error("native", "native_register_widths", "native quantum and classical register widths must match"))
    if not program.operations or program.operations[-1].gate != "MEASURE" or not program.operations[-1].full_register:
        errors.append(_error("native", "terminal_measurement", "native source requires one terminal full-register measurement"))
    prefix = list(program.operations[:-1]) if program.operations else []
    if len(prefix) > MAX_GATES:
        errors.append(_error("native", "gate_budget", f"native unitary prefix exceeds the {MAX_GATES}-gate budget", "BLOCKED"))
    gates: list[tuple[str, tuple[int, ...]]] = []
    for operation in prefix:
        if operation.gate == "NOISE":
            errors.append(_error("native", "noise", "noise is outside the static noiseless common subset"))
        elif operation.gate == "ASSERT":
            errors.append(_error("native", "assertion", "assertions are outside the unitary-prefix comparison subset"))
        elif operation.gate == "MEASURE":
            errors.append(_error("native", "dynamic_measurement", "nonterminal or partial measurement is unsupported"))
        elif operation.condition is not None:
            errors.append(_error("native", "dynamic_control", "classical control is unsupported"))
        elif operation.gate not in SUPPORTED_GATES:
            errors.append(_error("native", "unsupported_gate", f"native gate {operation.gate} is unsupported"))
        else:
            gates.append((operation.gate, operation.qubits))
    measurements = [(index, index) for index in range(program.qubits)]
    return gates, measurements, errors


def _admit_external(parsed: dict[str, Any] | None) -> tuple[list[tuple[str, tuple[int, ...]]], list[tuple[int, int]], int | None, int | None, list[dict[str, str]]]:
    if parsed is None:
        return [], [], None, None, []
    errors: list[dict[str, str]] = []
    registers = parsed["registers"]
    qregs = registers["quantum"]
    cregs = registers["classical"]
    if len(qregs) != 1 or len(cregs) != 1:
        errors.append(_error("external", "register_count", "external source requires exactly one quantum and one classical register"))
        return [], [], None, None, errors
    qreg, creg = qregs[0], cregs[0]
    qwidth, cwidth = int(qreg["width"]), int(creg["width"])
    if qwidth > MAX_QUBITS:
        errors.append(_error("external", "qubit_budget", f"external comparison exceeds the {MAX_QUBITS}-qubit budget", "BLOCKED"))
    if qwidth != cwidth:
        errors.append(_error("external", "external_register_widths", "external quantum and classical register widths must match"))
    if parsed["language"]["includes"] != ["qelib1.inc"]:
        errors.append(_error("external", "include_contract", "external source must declare only qelib1.inc"))
    gates: list[tuple[str, tuple[int, ...]]] = []
    measurements: list[tuple[int, int]] = []
    measurement_started = False
    for operation in parsed["operations"]:
        name = str(operation["name"])
        if name == "measure":
            measurement_started = True
            measurements.append((
                int(operation["qubits"][0]["index"]),
                int(operation["clbits"][0]["index"]),
            ))
            continue
        if measurement_started:
            errors.append(_error("external", "nonterminal_measurement", "all external measurements must be terminal"))
        upper = name.upper()
        if operation.get("condition") is not None:
            errors.append(_error("external", "dynamic_control", "external classical control is unsupported"))
        elif name == "barrier":
            errors.append(_error("external", "barrier", "barriers are not silently removed in this increment"))
        elif upper not in SUPPORTED_GATES or operation.get("parameters"):
            errors.append(_error("external", "unsupported_gate", f"external gate {name} is outside the common subset"))
        else:
            gates.append((upper, tuple(int(ref["index"]) for ref in operation["qubits"])))
    if len(gates) > MAX_GATES:
        errors.append(_error("external", "gate_budget", f"external unitary prefix exceeds the {MAX_GATES}-gate budget", "BLOCKED"))
    expected = [(index, index) for index in range(qwidth)]
    if measurements != expected:
        errors.append(_error("external", "terminal_measurement_mapping", "external terminal measurement must map q[i] to c[i] once in ascending order"))
    return gates, measurements, qwidth, cwidth, errors


def _projection_qasm(width: int, gates: list[tuple[str, tuple[int, ...]]]) -> bytes:
    lines = ["OPENQASM 2.0;", 'include "qelib1.inc";', f"qreg q[{width}];"]
    for gate, qubits in gates:
        operands = ",".join(f"q[{index}]" for index in qubits)
        lines.append(f"{gate.lower()} {operands};")
    return ("\n".join(lines) + "\n").encode("utf-8")


def _evaluation_representation(
    role: str,
    representation: dict[str, Any],
    projection: bytes | None,
    errors: list[dict[str, str]],
    *,
    width: int | None,
    gates: list[tuple[str, tuple[int, ...]]],
    measurement_mapping: list[tuple[int, int]],
    created_at: str,
    actor: str,
) -> dict[str, Any]:
    status = "PASS" if projection is not None and not errors else (
        "BLOCKED" if any(item["status"] == "BLOCKED" for item in errors) else "UNSUPPORTED"
    )
    return build_artifact(
        "representation",
        {
            "format": "e7q.openqasm2-unitary-prefix/v1",
            "role": role,
            "projection_status": status,
            "source_representation_ref": representation["artifact_id"],
            "qubit_width": width,
            "ordered_gates": [
                {"name": gate.lower(), "qubits": list(qubits)} for gate, qubits in gates
            ],
            "terminal_measurement_mapping": [
                {"qubit": qubit, "clbit": clbit} for qubit, clbit in measurement_mapping
            ],
            "content_encoding": "base64" if projection is not None else None,
            "content_base64": b64encode(projection).decode("ascii") if projection is not None else None,
            "content_digest": _raw_digest(projection) if projection is not None else None,
            "byte_length": len(projection) if projection is not None else None,
            "errors": errors,
        },
        created_at=created_at,
        actor=actor,
        source_refs=(representation["artifact_id"],),
        capabilities_required=("artifact.identity",),
        limitations=LIMITATIONS,
    )


def _transformation_artifact(
    role: str,
    representation: dict[str, Any],
    evaluation: dict[str, Any],
    *,
    created_at: str,
    actor: str,
) -> dict[str, Any]:
    return build_artifact(
        "transformation",
        {
            "format": "e7q.ir.unitary-prefix-projection/v1",
            "role": role,
            "input_refs": [representation["artifact_id"]],
            "output_refs": [evaluation["artifact_id"]],
            "criterion": PROJECTION_CRITERION,
            "validation_status": "not-assessed",
            "projection_status": evaluation["payload"]["projection_status"],
            "preserves": list(PROJECTION_PRESERVES),
            "loses": list(PROJECTION_LOSSES),
            "assumptions": list(PROJECTION_ASSUMPTIONS),
            "reason": "QCEC evaluates the static noiseless unitary prefix; terminal measurement compatibility is validated before removal.",
        },
        created_at=created_at,
        actor=actor,
        source_refs=(representation["artifact_id"], evaluation["artifact_id"]),
        capabilities_required=("artifact.identity",),
        limitations=LIMITATIONS,
    )


def _native_execution_artifact(
    representation: dict[str, Any], program: Program, *, created_at: str, actor: str,
) -> dict[str, Any] | None:
    if program.seed is None:
        return None
    result = verify(run(program))
    return build_artifact(
        "execution",
        {
            "format": "e7q.native-proof-of-path/v1",
            "backend": program.backend,
            "seed": program.seed,
            "shots": program.shots,
            "proof": result["proof"],
            "native_verifier_status": result["status"],
            "native_result": result,
            "assurance_boundary": "Native Proof-of-Path is preserved as local execution evidence; it is not the QCEC verdict or F2 conformance.",
        },
        created_at=created_at,
        actor=actor,
        source_refs=(representation["artifact_id"],),
        capabilities_required=("artifact.identity",),
        limitations=LIMITATIONS,
    )


def _non_pass_assessment(
    representation_refs: tuple[str, str],
    *,
    criterion: dict[str, Any],
    timeout_seconds: float,
    memory_limit_bytes: int,
    nthreads: int,
    max_simulations: int,
    seed: int,
    errors: list[dict[str, str]],
    created_at: str,
    actor: str,
) -> dict[str, Any]:
    status = "BLOCKED" if any(item["status"] == "BLOCKED" for item in errors) else "UNSUPPORTED"
    reason = "input_budget_blocked" if status == "BLOCKED" else "unsupported_input"
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
            "status": status,
            "conclusion": "INCONCLUSIVE",
            "raw_verdict": reason,
            "reason": reason,
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
        "assumptions": list(PROJECTION_ASSUMPTIONS),
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


def _recover_projection(evaluation: dict[str, Any]) -> bytes:
    payload = evaluation["payload"]
    raw = b64decode(payload["content_base64"], validate=True)
    if len(raw) != payload["byte_length"] or _raw_digest(raw) != payload["content_digest"]:
        raise E7QError("evaluation projection identity mismatch")
    return raw


def build_native_external_qcec_graph(
    native: str | Path,
    external: str | Path,
    *,
    criterion_id: str,
    numerical_tolerance: float,
    fidelity_threshold: float,
    timeout_seconds: float,
    memory_limit_bytes: int,
    created_at: str,
    native_source_ref: str,
    external_source_ref: str,
    name: str = "Native E7Q to external OpenQASM 2 QCEC comparison",
    actor: str = "e7q.ir.native-external-qcec-workflow",
    nthreads: int = 1,
    max_simulations: int = 16,
    seed: int = 0,
    verify_backend: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Build one bounded, criterion-selected native-to-external comparison graph."""
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
    for value, label in (
        (created_at, "created_at"), (native_source_ref, "native_source_ref"),
        (external_source_ref, "external_source_ref"), (name, "name"), (actor, "actor"),
    ):
        if not isinstance(value, str) or not value:
            raise E7QError(f"{label} must be a non-empty string")

    criterion = _criterion_record(criterion_id, numerical_tolerance, fidelity_threshold)
    native_path, native_raw = _read_snapshot(native, "native")
    external_path, external_raw = _read_snapshot(external, "external")
    native_source = _source_artifact(
        native_raw, role="native", source_format="e7q-native-source-bytes",
        display_name=native_path.name, source_ref=native_source_ref,
        created_at=created_at, actor=actor,
    )
    external_source = _source_artifact(
        external_raw, role="external", source_format="openqasm-2-source-bytes",
        display_name=external_path.name, source_ref=external_source_ref,
        created_at=created_at, actor=actor,
    )
    native_rep, program, native_errors = _parse_native_representation(
        native_source, native_raw, created_at=created_at, actor=actor,
    )
    external_rep, parsed_external, external_errors = _parse_external_representation(
        external_source, external_raw, display_name=external_path.name,
        created_at=created_at, actor=actor,
    )
    native_gates, native_measurements, admission_native = _admit_native(program)
    external_gates, external_measurements, external_qwidth, external_cwidth, admission_external = _admit_external(parsed_external)
    native_local_errors = native_errors + admission_native
    external_local_errors = external_errors + admission_external
    pair_errors: list[dict[str, str]] = []
    native_width = program.qubits if program is not None else None
    native_bits = program.bits if program is not None else None
    if program is not None and parsed_external is not None:
        if native_width != external_qwidth:
            pair_errors.append(_error("pair", "quantum_width_mismatch", "native and external quantum register widths differ"))
        if native_bits != external_cwidth:
            pair_errors.append(_error("pair", "classical_width_mismatch", "native and external classical register widths differ"))
        if native_measurements != external_measurements:
            pair_errors.append(_error("pair", "measurement_mapping_mismatch", "native and external terminal measurement mappings differ"))
    errors = native_local_errors + external_local_errors + pair_errors

    native_projection = (
        _projection_qasm(native_width, native_gates)
        if native_width is not None and not native_local_errors else None
    )
    external_projection = (
        _projection_qasm(external_qwidth, external_gates)
        if external_qwidth is not None and not external_local_errors else None
    )
    native_eval = _evaluation_representation(
        "native", native_rep, native_projection, native_local_errors + pair_errors,
        width=native_width, gates=native_gates, measurement_mapping=native_measurements,
        created_at=created_at, actor=actor,
    )
    external_eval = _evaluation_representation(
        "external", external_rep, external_projection, external_local_errors + pair_errors,
        width=external_qwidth, gates=external_gates, measurement_mapping=external_measurements,
        created_at=created_at, actor=actor,
    )
    native_transform = _transformation_artifact(
        "native", native_rep, native_eval, created_at=created_at, actor=actor,
    )
    external_transform = _transformation_artifact(
        "external", external_rep, external_eval, created_at=created_at, actor=actor,
    )
    native_execution = (
        _native_execution_artifact(native_rep, program, created_at=created_at, actor=actor)
        if program is not None and not errors else None
    )
    evaluation_refs = (native_eval["artifact_id"], external_eval["artifact_id"])
    if errors:
        assessment = _non_pass_assessment(
            evaluation_refs, criterion=criterion, timeout_seconds=timeout_seconds,
            memory_limit_bytes=memory_limit_bytes, nthreads=nthreads,
            max_simulations=max_simulations, seed=seed, errors=errors,
            created_at=created_at, actor=actor,
        )
    else:
        with tempfile.TemporaryDirectory(prefix="e7q-native-external-qcec-") as directory:
            root = Path(directory)
            left = root / "native-prefix.qasm"
            right = root / "external-prefix.qasm"
            left.write_bytes(_recover_projection(native_eval))
            right.write_bytes(_recover_projection(external_eval))
            assessment = evaluate(
                left, right, criterion=CRITERIA[criterion_id], source_refs=evaluation_refs,
                created_at=created_at, timeout_seconds=timeout_seconds,
                memory_limit_bytes=memory_limit_bytes,
                numerical_tolerance=numerical_tolerance,
                fidelity_threshold=fidelity_threshold,
                nthreads=nthreads, max_simulations=max_simulations, seed=seed,
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
            "statement": f"The native and external unitary prefixes pass {relation_name} under the recorded QCEC configuration.",
            "claim_type": "bounded-native-external-unitary-prefix-equivalence",
            "requested_criterion": criterion,
            "evidence_refs": [assessment["artifact_id"]],
            "support_status": "supported-within-declared-scope" if passed else "unsupported",
            "boundaries": list(LIMITATIONS),
            "prohibited_inferences": [
                "Do not infer exact-algebraic equivalence from this numerical assessment.",
                "Do not infer equivalence of unsupported measurement, noise, assertion, condition, permutation or ancilla semantics.",
                "Do not infer that the external circuit was produced by a compiler without separately supplied provenance evidence.",
            ],
        },
        created_at=created_at,
        actor=actor,
        source_refs=(assessment["artifact_id"],),
        capabilities_required=("claim.boundary",),
        limitations=LIMITATIONS,
    )

    projection_status = "not-assessed"
    assessment_status = "validated" if passed else "failed"
    artifacts = [
        native_source, external_source, native_rep, external_rep,
        native_transform, external_transform, native_eval, external_eval,
    ]
    if native_execution is not None:
        artifacts.append(native_execution)
    artifacts.extend([assessment, claim])
    relations = [
        build_relation("represents", native_source["artifact_id"], native_rep["artifact_id"], validation_status="validated" if not native_errors else "failed"),
        build_relation("represents", external_source["artifact_id"], external_rep["artifact_id"], validation_status="validated" if not external_errors else "failed"),
        build_relation(
            "transforms", native_rep["artifact_id"], native_eval["artifact_id"],
            criterion=PROJECTION_CRITERION, preserves=PROJECTION_PRESERVES,
            loses=PROJECTION_LOSSES, assumptions=PROJECTION_ASSUMPTIONS,
            validation_status=projection_status,
        ),
        build_relation(
            "transforms", external_rep["artifact_id"], external_eval["artifact_id"],
            criterion=PROJECTION_CRITERION, preserves=PROJECTION_PRESERVES,
            loses=PROJECTION_LOSSES, assumptions=PROJECTION_ASSUMPTIONS,
            validation_status=projection_status,
        ),
        build_relation("assesses", native_eval["artifact_id"], assessment["artifact_id"], criterion=criterion, validation_status=assessment_status),
        build_relation("assesses", external_eval["artifact_id"], assessment["artifact_id"], criterion=criterion, validation_status=assessment_status),
        build_relation("supports", assessment["artifact_id"], claim["artifact_id"], criterion=criterion, validation_status="supported" if passed else "failed"),
    ]
    if native_execution is not None:
        relations.append(build_relation("produces", native_rep["artifact_id"], native_execution["artifact_id"], validation_status="not-assessed"))
    request_identity = {
        "format": WORKFLOW_FORMAT,
        "source_digests": [_raw_digest(native_raw), _raw_digest(external_raw)],
        "source_refs": [native_source_ref, external_source_ref],
        "criterion": criterion,
        "limits": {"timeout_seconds": timeout_seconds, "memory_limit_bytes": memory_limit_bytes},
        "configuration": {"nthreads": nthreads, "max_simulations": max_simulations, "seed": seed},
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
            "assessment_status": outcome["status"],
            "assessment_reason": outcome["reason"],
            "common_subset": {
                "maximum_qubits": MAX_QUBITS,
                "maximum_unitary_gates": MAX_GATES,
                "supported_gates": sorted(gate.lower() for gate in SUPPORTED_GATES),
                "requires_static_noiseless": True,
                "requires_terminal_identity_measurement": True,
            },
            "f2_boundary": "All applicable installed F2 validators must be run by the consumer; relations without a semantic validator remain not-assessed.",
            "compiler_provenance": "not-supplied-not-claimed",
        },
    )
    if validate_graph(graph, level="F1")["status"] != "PASS":
        raise E7QError("constructed native/external QCEC graph failed F1 validation")
    return graph


def recover_native_external_source(graph: dict[str, Any], source_ref: str) -> bytes:
    """Recover one preserved input exactly after F1, encoding, size and digest checks."""
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
    parser.add_argument("native", type=Path)
    parser.add_argument("external", type=Path)
    parser.add_argument("--criterion", required=True, choices=sorted(CRITERIA))
    parser.add_argument("--numerical-tolerance", required=True, type=float)
    parser.add_argument("--fidelity-threshold", required=True, type=float)
    parser.add_argument("--timeout-seconds", required=True, type=float)
    parser.add_argument("--memory-limit-bytes", required=True, type=int)
    parser.add_argument("--created-at", required=True)
    parser.add_argument("--native-source-ref", required=True)
    parser.add_argument("--external-source-ref", required=True)
    parser.add_argument("--name", default="Native E7Q to external OpenQASM 2 QCEC comparison")
    parser.add_argument("--actor", default="e7q.ir.native-external-qcec-workflow")
    parser.add_argument("--nthreads", type=int, default=1)
    parser.add_argument("--max-simulations", type=int, default=16)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        output = args.output.resolve()
        for source in (args.native, args.external):
            if source.resolve() == output or (output.exists() and source.samefile(output)):
                raise E7QError("output must not overwrite an input source")
        graph = build_native_external_qcec_graph(
            args.native, args.external,
            criterion_id=args.criterion,
            numerical_tolerance=args.numerical_tolerance,
            fidelity_threshold=args.fidelity_threshold,
            timeout_seconds=args.timeout_seconds,
            memory_limit_bytes=args.memory_limit_bytes,
            created_at=args.created_at,
            native_source_ref=args.native_source_ref,
            external_source_ref=args.external_source_ref,
            name=args.name,
            actor=args.actor,
            nthreads=args.nthreads,
            max_simulations=args.max_simulations,
            seed=args.seed,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(canonical_bytes(graph) + b"\n")
    except (OSError, E7QError, ValueError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
