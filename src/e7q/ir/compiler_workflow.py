# SPDX-License-Identifier: Apache-2.0
"""Typed E7Q-IR conversion of the reference topology compiler Proof-of-Path."""
from __future__ import annotations

import argparse
from base64 import b64decode, b64encode
from binascii import Error as BinasciiError
from dataclasses import asdict, dataclass
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import tempfile
from typing import Any, Callable, Iterable

from ..language import (
    Compilation,
    E7QError,
    Program,
    compilation_result,
    compile_topology,
    parse,
)
from .canonical import canonical_bytes, digest
from .circuit import MAX_SOURCE_BYTES
from .conformance import validate_graph
from .envelope import build_artifact
from .graph import build_graph, build_relation
from .native_qcec_workflow import (
    CRITERIA,
    MAX_GATES,
    MAX_QUBITS,
    PROJECTION_ASSUMPTIONS,
    PROJECTION_LOSSES,
    PROJECTION_PRESERVES,
    _admit_native,
    _criterion_record,
    _finite_positive,
    _json_program,
    _non_pass_assessment,
    _projection_qasm,
    _raw_digest,
)
from .qcec import NUMERICAL_EXACT_CRITERION, evaluate

WORKFLOW_FORMAT = "e7q.ir.topology-compiler-proof-workflow/v1"
SOURCE_ADAPTER = "e7q.ir.topology-compiler-source/v1"
TRACE_FORMAT = "e7q.ir.topology-compiler-trace/v1"
REPRESENTATION_FORMAT = "e7q.ir.topology-compiler-circuit/v1"
REQUEST_FORMAT = "e7q.ir.topology-compilation-request/v1"
TRACE_CRITERION = {
    "id": "e7q.ir.topology-compiler-trace-consistency",
    "version": "1",
}
COMPILER_IMPLEMENTATION = "e7q.language.compile_topology"
COMPILER_BACKEND = "topology-reference"
TWO_QUBIT_GATES = frozenset({"CX", "CZ", "SWAP"})
LIMITATIONS = (
    "The compiler is the existing deterministic topology-reference compiler; this workflow does not define another compiler.",
    "The compiler Proof-of-Path is a preservation declaration and never establishes semantic equivalence by itself.",
    "Independent QCEC evidence applies only to the admitted static noiseless unitary prefix under the explicitly requested numerical criterion.",
    "Terminal measurement is preserved in the complete representations and removed only from the QCEC evaluation projections.",
    "No hardware feasibility, coupling quality, physical fidelity, provider authentication, execution success, exact-algebraic equivalence, arbitrary scalability or Phase 2 completion is established.",
)
TRACE_PRESERVES = (
    "source-operation-order",
    "source-logical-gate-semantics-under-layout-restoration",
    "logical-qubit-count",
    "terminal-measurement-mapping",
    "compiler-proof-of-path",
)
TRACE_LOSSES = (
    "original-physical-operation-count",
    "direct-logical-to-physical-locality",
)
TRACE_ASSUMPTIONS = (
    "coupling-edges-are-undirected",
    "swap-is-the-declared-native-swap-operation",
    "compiler-shortest-path-selection-is-deterministic",
    "each-routing-step-restores-the-logical-layout",
    "compiler-trace-consistency-is-not-semantic-equivalence",
)


@dataclass(frozen=True)
class TypedSwap:
    order: int
    phase: str
    qubits: tuple[int, int]


@dataclass(frozen=True)
class TypedRouteStep:
    order: int
    source_operation_index: int
    zero_based_source_operation_index: int
    operator: str
    logical_qubits: tuple[int, int]
    selected_physical_path: tuple[int, ...]
    routed_physical_qubits: tuple[int, int]
    inserted_swaps: tuple[TypedSwap, ...]
    inserted_swap_count: int
    layout_assertion: dict[str, Any]


@dataclass(frozen=True)
class TypedCompileContext:
    order: int
    kind: str
    compiler_backend: str
    logical_qubit_count: int
    coupling_edges: tuple[tuple[int, int], ...]
    native_gate_set: tuple[str, ...]
    boundary: str


@dataclass(frozen=True)
class TypedCompileSummary:
    order: int
    kind: str
    source_operation_count: int
    compiled_operation_count: int
    inserted_swap_count: int
    routing_overhead_operations: int
    layout_assertion: dict[str, Any]


def _package_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "unavailable"


def _issue(code: str, message: str, status: str) -> dict[str, str]:
    return {
        "role": "compiler",
        "code": code,
        "status": status,
        "type": "CompilerEvidenceError",
        "message": message,
    }


def _read_source(path: str | Path) -> tuple[Path, bytes]:
    source = Path(path)
    try:
        with source.open("rb") as stream:
            raw = stream.read(MAX_SOURCE_BYTES + 1)
    except OSError as exc:
        raise E7QError(f"cannot read native source: {exc}") from exc
    if len(raw) > MAX_SOURCE_BYTES:
        raise E7QError(f"native source exceeds the {MAX_SOURCE_BYTES}-byte input budget")
    return source, raw


def _source_artifact(
    raw: bytes,
    *,
    display_name: str,
    source_ref: str,
    created_at: str,
    actor: str,
) -> dict[str, Any]:
    return build_artifact(
        "source",
        {
            "format": "e7q-native-source-bytes",
            "adapter": SOURCE_ADAPTER,
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


def _normalize_edges(
    edges: Iterable[Iterable[int]], qubits: int,
) -> tuple[tuple[tuple[int, int], ...], list[list[Any]], list[dict[str, str]]]:
    normalized: list[tuple[int, int]] = []
    submitted: list[list[Any]] = []
    errors: list[dict[str, str]] = []
    seen: set[tuple[int, int]] = set()
    try:
        raw_edges = list(edges)
    except TypeError:
        return (), [], [_issue("malformed_topology", "coupling edges must be iterable", "UNSUPPORTED")]
    for index, edge in enumerate(raw_edges):
        try:
            pair = list(edge)
        except TypeError:
            submitted.append([edge])
            errors.append(_issue("malformed_topology", f"coupling edge {index} is not a pair", "UNSUPPORTED"))
            continue
        submitted.append(pair)
        if len(pair) != 2 or any(type(value) is not int for value in pair):
            errors.append(_issue("malformed_topology", f"coupling edge {index} must contain two integers", "UNSUPPORTED"))
            continue
        first, second = pair
        if first == second or not (0 <= first < qubits and 0 <= second < qubits):
            errors.append(_issue("malformed_topology", f"coupling edge {index} must join distinct in-range qubits", "UNSUPPORTED"))
            continue
        canonical = (min(first, second), max(first, second))
        if canonical in seen:
            errors.append(_issue("duplicate_topology_edge", f"coupling edge {index} duplicates an undirected edge", "UNSUPPORTED"))
            continue
        seen.add(canonical)
        normalized.append((first, second))
    return tuple(normalized), submitted, errors


def _parse_program(raw: bytes) -> tuple[Program | None, list[dict[str, str]]]:
    try:
        return parse(raw.decode("utf-8")), []
    except (UnicodeDecodeError, E7QError) as exc:
        return None, [_issue("native_parse_error", str(exc), "UNSUPPORTED")]


def _projection(program: Program | None) -> tuple[bytes | None, list[tuple[str, tuple[int, ...]]], list[tuple[int, int]], list[dict[str, str]]]:
    gates, measurements, errors = _admit_native(program)
    if program is None or errors:
        return None, gates, measurements, errors
    return _projection_qasm(program.qubits, gates), gates, measurements, []


def _representation_artifact(
    role: str,
    program: Program | None,
    projection: bytes | None,
    gates: list[tuple[str, tuple[int, ...]]],
    measurements: list[tuple[int, int]],
    errors: list[dict[str, str]],
    *,
    refs: tuple[str, ...],
    created_at: str,
    actor: str,
) -> dict[str, Any]:
    program_value = _json_program(program) if program is not None else None
    content_carrier = {
        "format": "e7q.native-program-content/v1",
        "program": program_value,
    }
    status = (
        "PASS" if program is not None and projection is not None and not errors
        else "BLOCKED" if any(item["status"] == "BLOCKED" for item in errors)
        else "UNSUPPORTED" if errors else "NOT_ASSESSED"
    )
    return build_artifact(
        "representation",
        {
            "format": REPRESENTATION_FORMAT,
            "role": role,
            "status": status,
            "program": program_value,
            "content_identity": digest(content_carrier) if program_value is not None else None,
            "qcec_evaluation_projection": {
                "format": "e7q.openqasm2-unitary-prefix/v1",
                "status": status,
                "content_encoding": "base64" if projection is not None else None,
                "content_base64": b64encode(projection).decode("ascii") if projection is not None else None,
                "content_digest": _raw_digest(projection) if projection is not None else None,
                "byte_length": len(projection) if projection is not None else None,
                "ordered_gates": [
                    {"name": gate.lower(), "qubits": list(qubits)} for gate, qubits in gates
                ],
                "terminal_measurement_mapping": [
                    {"qubit": qubit, "clbit": clbit} for qubit, clbit in measurements
                ],
                "preserves": list(PROJECTION_PRESERVES),
                "loses": list(PROJECTION_LOSSES),
                "assumptions": list(PROJECTION_ASSUMPTIONS),
                "criterion_boundary": "QCEC applies only to the static noiseless unitary prefix; terminal measurement compatibility is checked before removal.",
            },
            "errors": errors,
        },
        created_at=created_at,
        actor=actor,
        source_refs=refs,
        capabilities_required=("artifact.identity",),
        limitations=LIMITATIONS,
    )


def _typed_trace(source: Program, compilation: Compilation) -> list[dict[str, Any]]:
    proof = list(compilation.proof)
    if len(proof) < 2 or proof[0].get("kind") != "compile" or proof[-1].get("kind") != "compilation-result":
        raise E7QError("compiler Proof-of-Path has an invalid step sequence")
    if [step.get("step") for step in proof] != list(range(len(proof))):
        raise E7QError("compiler Proof-of-Path step numbers are inconsistent")
    header = proof[0]
    if (
        header.get("backend") != COMPILER_BACKEND
        or header.get("logical_qubits") != source.qubits
        or header.get("coupling_edges") != [list(edge) for edge in compilation.topology]
        or header.get("native_gates") != sorted(compilation.native_gates)
    ):
        raise E7QError("compiler initial context contradicts the compilation request")
    typed: list[dict[str, Any]] = [json.loads(json.dumps(asdict(TypedCompileContext(
        order=0,
        kind="initial-compile-context",
        compiler_backend=COMPILER_BACKEND,
        logical_qubit_count=source.qubits,
        coupling_edges=compilation.topology,
        native_gate_set=tuple(sorted(compilation.native_gates)),
        boundary=str(header["boundary"]),
    ))))]
    expected_routes = [
        (index, operation)
        for index, operation in enumerate(source.operations, start=1)
        if operation.gate in TWO_QUBIT_GATES
    ]
    route_proof = proof[1:-1]
    if len(route_proof) != len(expected_routes):
        raise E7QError("compiler route-step count does not match source operations")
    for order, (record, (source_index, operation)) in enumerate(
        zip(route_proof, expected_routes), start=1
    ):
        path = tuple(record.get("physical_path", ()))
        if (
            record.get("kind") != "route"
            or record.get("source_step") != source_index
            or record.get("operator") != operation.gate
            or tuple(record.get("logical_qubits", ())) != operation.qubits
            or len(path) < 2
            or path[0] != operation.qubits[0]
            or path[-1] != operation.qubits[1]
            or record.get("layout_restored") is not True
        ):
            raise E7QError("compiler route record contradicts its source operation")
        topology = {frozenset(edge) for edge in compilation.topology}
        if any(frozenset(pair) not in topology for pair in zip(path[:-1], path[1:])):
            raise E7QError("compiler route path uses an undeclared coupling edge")
        forward = tuple(zip(path[:-2], path[1:-1]))
        reverse = tuple(reversed(forward))
        swaps = tuple(
            TypedSwap(index, "forward", pair)
            for index, pair in enumerate(forward)
        ) + tuple(
            TypedSwap(len(forward) + index, "reverse", pair)
            for index, pair in enumerate(reverse)
        )
        if record.get("inserted_swaps") != len(swaps):
            raise E7QError("compiler route record has an inconsistent SWAP count")
        typed.append(json.loads(json.dumps(asdict(TypedRouteStep(
            order=order,
            source_operation_index=source_index,
            zero_based_source_operation_index=source_index - 1,
            operator=operation.gate,
            logical_qubits=operation.qubits,
            selected_physical_path=path,
            routed_physical_qubits=(path[-2], path[-1]),
            inserted_swaps=swaps,
            inserted_swap_count=len(swaps),
            layout_assertion={
                "assertion": "logical-layout-restored-after-route",
                "passed": True,
            },
        )))))
    summary = proof[-1]
    source_count = len(source.operations)
    compiled_count = len(compilation.program.operations)
    if (
        summary.get("source_operations") != source_count
        or summary.get("compiled_operations") != compiled_count
        or summary.get("inserted_swaps") != compilation.inserted_swaps
        or summary.get("layout_restored") is not True
        or compiled_count - source_count != compilation.inserted_swaps
    ):
        raise E7QError("compiler summary contradicts the compiled program")
    typed.append(json.loads(json.dumps(asdict(TypedCompileSummary(
        order=len(typed),
        kind="compilation-summary",
        source_operation_count=source_count,
        compiled_operation_count=compiled_count,
        inserted_swap_count=compilation.inserted_swaps,
        routing_overhead_operations=compiled_count - source_count,
        layout_assertion={
            "assertion": "final-logical-layout-restored",
            "passed": True,
        },
    )))))
    return typed


def _request_artifact(
    program: Program | None,
    submitted_edges: list[list[Any]],
    native_gates: frozenset[str],
    criterion: dict[str, Any],
    *,
    timeout_seconds: float,
    memory_limit_bytes: int,
    nthreads: int,
    max_simulations: int,
    seed: int,
    original_ref: str,
    created_at: str,
    actor: str,
) -> dict[str, Any]:
    return build_artifact(
        "intent",
        {
            "format": REQUEST_FORMAT,
            "coupling_edges": submitted_edges,
            "logical_qubit_count": program.qubits if program is not None else None,
            "native_gate_set": sorted(native_gates),
            "compiler": {
                "implementation": COMPILER_IMPLEMENTATION,
                "backend": COMPILER_BACKEND,
                "package": "e7q",
                "version": _package_version("e7q"),
            },
            "selected_program": program.name if program is not None else None,
            "selected_path": program.path if program is not None else None,
            "requested_equivalence_criterion": criterion,
            "numerical_tolerance": criterion["options"]["numerical_tolerance"],
            "fidelity_threshold": criterion["options"]["fidelity_threshold"],
            "wall_clock_limit_seconds": timeout_seconds,
            "memory_limit_bytes": memory_limit_bytes,
            "qcec_configuration": {
                "nthreads": nthreads,
                "max_simulations": max_simulations,
                "seed": seed,
            },
        },
        created_at=created_at,
        actor=actor,
        source_refs=(original_ref,),
        capabilities_required=("artifact.identity",),
        limitations=LIMITATIONS,
    )


def _recover_projection(representation: dict[str, Any]) -> bytes:
    projection = representation["payload"]["qcec_evaluation_projection"]
    try:
        raw = b64decode(projection["content_base64"], validate=True)
    except (BinasciiError, KeyError, TypeError, ValueError) as exc:
        raise E7QError("invalid QCEC projection encoding") from exc
    if len(raw) != projection["byte_length"] or _raw_digest(raw) != projection["content_digest"]:
        raise E7QError("QCEC projection identity mismatch")
    return raw


def _compile_error(exc: E7QError) -> dict[str, str]:
    message = str(exc)
    if "no coupling path" in message:
        return _issue("disconnected_topology", message, "BLOCKED")
    if "requires native SWAP" in message:
        return _issue("missing_swap_support", message, "UNSUPPORTED")
    if "backend does not support native gate" in message or "unknown native gates" in message:
        return _issue("unsupported_native_gate", message, "UNSUPPORTED")
    return _issue("compiler_failure", message, "NOT_ASSESSED")


def _compiler_non_pass_assessment(
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
    base = _non_pass_assessment(
        representation_refs,
        criterion=criterion,
        timeout_seconds=timeout_seconds,
        memory_limit_bytes=memory_limit_bytes,
        nthreads=nthreads,
        max_simulations=max_simulations,
        seed=seed,
        errors=errors,
        created_at=created_at,
        actor=actor,
    )
    priority = ("BLOCKED", "UNSUPPORTED", "FAIL", "NOT_ASSESSED")
    status = next(
        (candidate for candidate in priority if any(item["status"] == candidate for item in errors)),
        "NOT_ASSESSED",
    )
    selected = next((item for item in errors if item["status"] == status), errors[0])
    payload = json.loads(json.dumps(base["payload"]))
    payload["outcome"].update({
        "status": status,
        "conclusion": "INCONCLUSIVE",
        "raw_verdict": selected["code"],
        "reason": selected["code"],
        "universal_equivalence_established": False,
    })
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


def build_compiler_proof_graph(
    native: str | Path,
    *,
    coupling_edges: Iterable[Iterable[int]],
    native_gates: frozenset[str],
    criterion_id: str,
    numerical_tolerance: float,
    fidelity_threshold: float,
    timeout_seconds: float,
    memory_limit_bytes: int,
    created_at: str,
    source_ref: str,
    name: str = "Typed topology compiler Proof-of-Path",
    actor: str = "e7q.ir.topology-compiler-proof-workflow",
    nthreads: int = 1,
    max_simulations: int = 16,
    seed: int = 0,
    verify_backend: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Compile one native program and build bounded criterion-bound compiler evidence."""
    numerical_tolerance = _finite_positive(numerical_tolerance, "numerical_tolerance")
    fidelity_threshold = _finite_positive(fidelity_threshold, "fidelity_threshold")
    if fidelity_threshold > 1:
        raise E7QError("fidelity_threshold must not exceed one")
    timeout_seconds = _finite_positive(timeout_seconds, "timeout_seconds")
    if type(memory_limit_bytes) is not int or memory_limit_bytes <= 0:
        raise E7QError("memory_limit_bytes must be a positive integer")
    if not isinstance(native_gates, frozenset) or not native_gates:
        raise E7QError("native_gates must be a non-empty frozenset")
    if type(nthreads) is not int or nthreads < 1:
        raise E7QError("nthreads must be a positive integer")
    if type(max_simulations) is not int or max_simulations < 0:
        raise E7QError("max_simulations must be a non-negative integer")
    if type(seed) is not int or seed < 0:
        raise E7QError("seed must be a non-negative integer")
    for value, label in ((created_at, "created_at"), (source_ref, "source_ref"), (name, "name"), (actor, "actor")):
        if not isinstance(value, str) or not value:
            raise E7QError(f"{label} must be a non-empty string")

    criterion = _criterion_record(criterion_id, numerical_tolerance, fidelity_threshold)
    native_path, raw = _read_source(native)
    source = _source_artifact(
        raw,
        display_name=native_path.name,
        source_ref=source_ref,
        created_at=created_at,
        actor=actor,
    )
    program, parse_errors = _parse_program(raw)
    source_projection, source_gates, source_measurements, admission_errors = _projection(program)
    source_errors = parse_errors + admission_errors
    normalized_edges, submitted_edges, topology_errors = _normalize_edges(
        coupling_edges, program.qubits if program is not None else 0
    )
    original = _representation_artifact(
        "original",
        program,
        source_projection,
        source_gates,
        source_measurements,
        source_errors,
        refs=(source["artifact_id"],),
        created_at=created_at,
        actor=actor,
    )
    request = _request_artifact(
        program,
        submitted_edges,
        native_gates,
        criterion,
        timeout_seconds=timeout_seconds,
        memory_limit_bytes=memory_limit_bytes,
        nthreads=nthreads,
        max_simulations=max_simulations,
        seed=seed,
        original_ref=original["artifact_id"],
        created_at=created_at,
        actor=actor,
    )

    errors = source_errors + topology_errors
    compilation: Compilation | None = None
    compiler_result: dict[str, Any] | None = None
    typed_steps: list[dict[str, Any]] = []
    if program is not None and not errors:
        try:
            compilation = compile_topology(program, normalized_edges, native_gates)
            compiler_result = compilation_result(compilation)
            typed_steps = _typed_trace(program, compilation)
        except E7QError as exc:
            errors.append(_compile_error(exc))
    compiled_program = compilation.program if compilation is not None and not errors else None
    compiled_projection, compiled_gates, compiled_measurements, compiled_errors = _projection(compiled_program)
    errors.extend(compiled_errors)
    compiled = _representation_artifact(
        "compiled",
        compiled_program,
        compiled_projection,
        compiled_gates,
        compiled_measurements,
        errors,
        refs=(original["artifact_id"], request["artifact_id"]),
        created_at=created_at,
        actor=actor,
    )

    trace_status = (
        "PASS" if compilation is not None and compiler_result is not None and typed_steps and not errors
        else "BLOCKED" if any(item["status"] == "BLOCKED" for item in errors)
        else "UNSUPPORTED" if any(item["status"] == "UNSUPPORTED" for item in errors)
        else "NOT_ASSESSED"
    )
    transformation = build_artifact(
        "transformation",
        {
            "format": TRACE_FORMAT,
            "input_refs": [original["artifact_id"], request["artifact_id"]],
            "output_refs": [compiled["artifact_id"]],
            "criterion": TRACE_CRITERION,
            "validation_status": "validated" if trace_status == "PASS" else "failed",
            "compiler_status": trace_status,
            "compiler_preservation_declaration": {
                "status": compiler_result["status"] if compiler_result is not None else trace_status,
                "statement": "The topology-reference compiler declares logical operation preservation through deterministic routing and restored layout.",
                "semantic_equivalence_established": False,
            },
            "original_compilation_result": compiler_result,
            "original_compiler_proof": compiler_result["proof"] if compiler_result is not None else None,
            "typed_steps": typed_steps,
            "preserves": list(TRACE_PRESERVES),
            "loses": list(TRACE_LOSSES),
            "assumptions": list(TRACE_ASSUMPTIONS),
            "errors": errors,
        },
        created_at=created_at,
        actor=actor,
        source_refs=(original["artifact_id"], request["artifact_id"], compiled["artifact_id"]),
        capabilities_required=("artifact.identity", "transformation.accounting"),
        limitations=LIMITATIONS,
    )

    representation_refs = (original["artifact_id"], compiled["artifact_id"])
    if errors or source_projection is None or compiled_projection is None:
        assessment = _compiler_non_pass_assessment(
            representation_refs,
            criterion=criterion,
            timeout_seconds=timeout_seconds,
            memory_limit_bytes=memory_limit_bytes,
            nthreads=nthreads,
            max_simulations=max_simulations,
            seed=seed,
            errors=errors or [_issue("projection_unavailable", "QCEC projections are unavailable", "NOT_ASSESSED")],
            created_at=created_at,
            actor=actor,
        )
    else:
        with tempfile.TemporaryDirectory(prefix="e7q-compiler-qcec-") as directory:
            root = Path(directory)
            source_qasm = root / "source-prefix.qasm"
            compiled_qasm = root / "compiled-prefix.qasm"
            source_qasm.write_bytes(_recover_projection(original))
            compiled_qasm.write_bytes(_recover_projection(compiled))
            assessment = evaluate(
                source_qasm,
                compiled_qasm,
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
    trace_matches = trace_status == "PASS"
    qcec_passed = outcome["status"] == "PASS"
    supported = trace_matches and qcec_passed
    claim = build_artifact(
        "claim",
        {
            "statement": "The compiled unitary prefix preserves the selected native program under the explicitly requested numerical QCEC criterion and recorded compiler trace.",
            "claim_type": "bounded-topology-compiler-preservation",
            "requested_criterion": criterion,
            "evidence_refs": [transformation["artifact_id"], assessment["artifact_id"]],
            "support_status": "supported-within-declared-scope" if supported else "unsupported",
            "support_conditions": {
                "compilation_succeeded": compilation is not None and not errors,
                "compiled_representation_matches_trace": trace_matches,
                "layout_restoration_and_register_compatibility": trace_matches,
                "requested_qcec_criterion_passed": qcec_passed,
            },
            "boundaries": list(LIMITATIONS),
            "prohibited_inferences": [
                "Do not treat the compiler declaration or trace alone as semantic equivalence.",
                "Do not infer exact-algebraic equivalence from numerical QCEC evidence.",
                "Do not infer hardware feasibility, topology quality, physical fidelity, provider authentication or execution success.",
            ],
        },
        created_at=created_at,
        actor=actor,
        source_refs=(transformation["artifact_id"], assessment["artifact_id"]),
        capabilities_required=("claim.boundary",),
        limitations=LIMITATIONS,
    )

    relation_status = "validated" if trace_matches else "failed"
    assessment_status = "validated" if qcec_passed else "failed"
    relations = [
        build_relation("represents", source["artifact_id"], original["artifact_id"], validation_status="validated" if not parse_errors else "failed"),
        build_relation("constrains", original["artifact_id"], request["artifact_id"], validation_status="validated" if program is not None else "failed"),
        build_relation("produces", request["artifact_id"], transformation["artifact_id"], validation_status=relation_status),
        build_relation("produces", transformation["artifact_id"], compiled["artifact_id"], validation_status=relation_status),
        build_relation(
            "transforms",
            original["artifact_id"],
            compiled["artifact_id"],
            criterion=TRACE_CRITERION,
            preserves=TRACE_PRESERVES,
            loses=TRACE_LOSSES,
            assumptions=TRACE_ASSUMPTIONS,
            validation_status=relation_status,
        ),
        build_relation("assesses", original["artifact_id"], assessment["artifact_id"], criterion=criterion, validation_status=assessment_status),
        build_relation("assesses", compiled["artifact_id"], assessment["artifact_id"], criterion=criterion, validation_status=assessment_status),
        build_relation("constrains", transformation["artifact_id"], claim["artifact_id"], criterion=TRACE_CRITERION, validation_status=relation_status),
        build_relation("supports", assessment["artifact_id"], claim["artifact_id"], criterion=criterion, validation_status="supported" if supported else "failed"),
    ]
    request_identity = {
        "format": WORKFLOW_FORMAT,
        "source_digest": _raw_digest(raw),
        "source_ref": source_ref,
        "coupling_edges": submitted_edges,
        "native_gate_set": sorted(native_gates),
        "criterion": criterion,
        "limits": {"timeout_seconds": timeout_seconds, "memory_limit_bytes": memory_limit_bytes},
        "configuration": {"nthreads": nthreads, "max_simulations": max_simulations, "seed": seed},
        "created_at": created_at,
        "actor": actor,
        "name": name,
    }
    graph = build_graph(
        [source, original, request, compiled, transformation, assessment, claim],
        relations,
        name=name,
        extensions={
            "workflow_format": WORKFLOW_FORMAT,
            "workflow_request_id": digest(request_identity),
            "compiler_status": trace_status,
            "assessment_status": outcome["status"],
            "assessment_reason": outcome["reason"],
            "common_subset": {
                "maximum_qubits": MAX_QUBITS,
                "maximum_unitary_gates": MAX_GATES,
                "requires_static_noiseless": True,
                "requires_terminal_identity_measurement": True,
            },
            "f2_boundary": "No compiler-proof semantic validator is installed; F2 must remain NOT_ASSESSED or BLOCKED rather than infer trace truth.",
        },
    )
    if validate_graph(graph, level="F1")["status"] != "PASS":
        raise E7QError("constructed compiler Proof-of-Path graph failed F1 validation")
    consistency = validate_compiler_evidence(graph)
    if supported and consistency["status"] != "PASS":
        detail = consistency.get("message", consistency.get("reason", "unknown inconsistency"))
        raise E7QError(f"compiler evidence failed internal consistency validation: {detail}")
    return graph


def recover_compiler_source(graph: dict[str, Any], source_ref: str) -> bytes:
    """Recover the preserved native source after F1, encoding, size and digest checks."""
    if validate_graph(graph, level="F1")["status"] != "PASS":
        raise E7QError("cannot recover source from an invalid graph")
    matches = [
        artifact for artifact in graph["artifacts"]
        if artifact["kind"] == "source"
        and artifact["payload"].get("adapter") == SOURCE_ADAPTER
        and artifact["payload"].get("stable_source_ref") == source_ref
    ]
    if len(matches) != 1:
        raise E7QError("source_ref must identify exactly one compiler source")
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


def validate_compiler_evidence(graph: dict[str, Any]) -> dict[str, Any]:
    """Recompute source, compiler trace and claim eligibility after F1 validation."""
    f1 = validate_graph(graph, level="F1")
    if f1["status"] != "PASS":
        return {"status": "FAIL", "reason": "f1_invalid", "checks": []}
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, message: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "message": message})
        if not passed:
            raise E7QError(message)

    try:
        by_format: dict[str, list[dict[str, Any]]] = {}
        for artifact in graph["artifacts"]:
            value = artifact["payload"].get("format")
            if isinstance(value, str):
                by_format.setdefault(value, []).append(artifact)
        sources = [
            artifact for artifact in graph["artifacts"]
            if artifact["kind"] == "source" and artifact["payload"].get("adapter") == SOURCE_ADAPTER
        ]
        check("single-source", len(sources) == 1, "compiler graph requires one preserved source")
        source = sources[0]
        raw = recover_compiler_source(graph, source["payload"]["stable_source_ref"])
        program = parse(raw.decode("utf-8"))
        representations = by_format.get(REPRESENTATION_FORMAT, [])
        original_matches = [item for item in representations if item["payload"].get("role") == "original"]
        compiled_matches = [item for item in representations if item["payload"].get("role") == "compiled"]
        check("representation-count", len(original_matches) == 1 and len(compiled_matches) == 1, "compiler graph requires original and compiled representations")
        original, compiled = original_matches[0], compiled_matches[0]
        expected_original = _json_program(program)
        check("original-program", original["payload"].get("program") == expected_original, "original representation contradicts preserved source")
        check(
            "original-content-identity",
            original["payload"].get("content_identity") == digest({"format": "e7q.native-program-content/v1", "program": expected_original}),
            "original representation content identity is inconsistent",
        )
        requests = by_format.get(REQUEST_FORMAT, [])
        traces = by_format.get(TRACE_FORMAT, [])
        check("request-count", len(requests) == 1, "compiler graph requires one compilation request")
        check("trace-count", len(traces) == 1, "compiler graph requires one compiler trace")
        request, trace = requests[0], traces[0]
        rp = request["payload"]
        tp = trace["payload"]
        assessment = next(item for item in graph["artifacts"] if item["kind"] == "assessment")
        claim = next(item for item in graph["artifacts"] if item["kind"] == "claim")
        outcome = assessment["payload"]["outcome"]
        check("request-program", rp.get("logical_qubit_count") == program.qubits and rp.get("selected_program") == program.name and rp.get("selected_path") == program.path, "compilation request selects a different program")
        normalized, _, topology_errors = _normalize_edges(rp.get("coupling_edges", []), program.qubits)
        if topology_errors or tp.get("compiler_status") != "PASS":
            check("unsupported-claim", claim["payload"].get("support_status") == "unsupported", "non-PASS compilation cannot support a claim")
            return {"status": outcome["status"], "reason": outcome["reason"], "checks": checks}
        gates = frozenset(rp.get("native_gate_set", []))
        compilation = compile_topology(program, normalized, gates)
        expected_result = compilation_result(compilation)
        expected_typed = _typed_trace(program, compilation)
        check("compiler-result", tp.get("original_compilation_result") == expected_result, "preserved compiler result contradicts deterministic recompilation")
        check("compiler-proof", tp.get("original_compiler_proof") == expected_result["proof"], "preserved compiler Proof-of-Path is incomplete or inconsistent")
        check("typed-trace", tp.get("typed_steps") == expected_typed, "typed compiler trace contradicts deterministic recompilation")
        check("trace-refs", tp.get("input_refs") == [original["artifact_id"], request["artifact_id"]] and tp.get("output_refs") == [compiled["artifact_id"]], "compiler trace references are inconsistent")
        expected_compiled = _json_program(compilation.program)
        check("compiled-program", compiled["payload"].get("program") == expected_compiled, "compiled representation contradicts deterministic recompilation")
        check(
            "compiled-content-identity",
            compiled["payload"].get("content_identity") == digest({"format": "e7q.native-program-content/v1", "program": expected_compiled}),
            "compiled representation content identity is inconsistent",
        )
        expected_projection, _, _, projection_errors = _projection(compilation.program)
        check("compiled-projection-admitted", expected_projection is not None and not projection_errors, "compiled representation is outside the admitted QCEC subset")
        check("compiled-projection", _recover_projection(compiled) == expected_projection, "compiled QCEC projection contradicts deterministic recompilation")
        requested = rp["requested_equivalence_criterion"]
        check("assessment-criterion", assessment["payload"].get("criterion") == requested, "QCEC assessment criterion contradicts the compilation request")
        assessment_refs = assessment["provenance"]["source_refs"]
        check(
            "assessment-inputs",
            len(assessment_refs) == 2
            and set(assessment_refs) == {original["artifact_id"], compiled["artifact_id"]},
            "QCEC assessment does not identify both circuit representations",
        )
        eligible = outcome["status"] == "PASS"
        expected_support = "supported-within-declared-scope" if eligible else "unsupported"
        check("claim-evidence", claim["payload"].get("evidence_refs") == [trace["artifact_id"], assessment["artifact_id"]], "claim evidence references are inconsistent")
        check("claim-support", claim["payload"].get("support_status") == expected_support, "compiler claim support contradicts recomputed trace and QCEC evidence")
        check("trace-alone-boundary", tp.get("compiler_preservation_declaration", {}).get("semantic_equivalence_established") is False, "compiler declaration must not establish semantic equivalence")
        return {"status": outcome["status"], "reason": outcome["reason"], "checks": checks}
    except (E7QError, KeyError, StopIteration, TypeError, ValueError) as exc:
        return {"status": "FAIL", "reason": "compiler_evidence_inconsistent", "message": str(exc), "checks": checks}


def _parse_edge(value: str) -> tuple[int, int]:
    try:
        left, right = value.split(":", 1)
        return int(left), int(right)
    except (ValueError, TypeError) as exc:
        raise argparse.ArgumentTypeError("edge must be FIRST:SECOND") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("native", type=Path)
    parser.add_argument("--edge", action="append", required=True, type=_parse_edge, dest="edges")
    parser.add_argument("--native-gate", action="append", required=True, dest="native_gates")
    parser.add_argument("--criterion", required=True, choices=sorted(CRITERIA))
    parser.add_argument("--numerical-tolerance", required=True, type=float)
    parser.add_argument("--fidelity-threshold", required=True, type=float)
    parser.add_argument("--timeout-seconds", required=True, type=float)
    parser.add_argument("--memory-limit-bytes", required=True, type=int)
    parser.add_argument("--created-at", required=True)
    parser.add_argument("--source-ref", required=True)
    parser.add_argument("--name", default="Typed topology compiler Proof-of-Path")
    parser.add_argument("--actor", default="e7q.ir.topology-compiler-proof-workflow")
    parser.add_argument("--nthreads", type=int, default=1)
    parser.add_argument("--max-simulations", type=int, default=16)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.native.resolve() == args.output.resolve() or (
            args.output.exists() and args.native.samefile(args.output)
        ):
            raise E7QError("output must not overwrite source")
        graph = build_compiler_proof_graph(
            args.native,
            coupling_edges=args.edges,
            native_gates=frozenset(args.native_gates),
            criterion_id=args.criterion,
            numerical_tolerance=args.numerical_tolerance,
            fidelity_threshold=args.fidelity_threshold,
            timeout_seconds=args.timeout_seconds,
            memory_limit_bytes=args.memory_limit_bytes,
            created_at=args.created_at,
            source_ref=args.source_ref,
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
