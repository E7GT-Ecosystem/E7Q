# SPDX-License-Identifier: Apache-2.0
"""Bounded, optional E7Q-CIRQ/0.1 return adapter; never executes SDK source.

Admission accepts only the AST dialect emitted by adapters.cirq_source. Cirq
is imported exclusively in a resource-limited subprocess. Evidence establishes
F0/F1 integrity, not F2 SDK truth, physical fidelity, or external attestation.
"""
from __future__ import annotations

import ast
from dataclasses import asdict
import json
import math
import os
import platform
import signal
import subprocess
import sys

from .adapters import adapt
from .language import (E7QError, E7QResourceLimitError, Operation, ParseLimits,
                       Program, circuit_unitary, compare, comparison_result, parse)
from .resources import ExecutionPolicy, preflight, validate_program

VERSION = "E7Q-CIRQ/0.1"
CIRQ_VERSION = "1.6.1"
MAX_SOURCE_BYTES = 16384
MAX_JSON_BYTES = 32768
MAX_QUBITS = 2
MAX_GATES = 64
MEMORY_BYTES = 3 * 1024**3
CPU_SECONDS = 10
CONSISTENCY_TOLERANCE = 1e-9
IDENTITY_SENTINEL = "1970-01-01T00:00:00Z"
POLICY = ExecutionPolicy(memory_budget_bytes=256 * 1024**2)
PARSE_LIMITS = ParseLimits(65, 128, 256, 16)
GATES = {"X": 1, "Y": 1, "Z": 1, "H": 1, "S": 1, "T": 1,
         "CX": 2, "CZ": 2, "SWAP": 2}
LIMITATIONS = [
    "F0/F1 identity and reference integrity only; no F2 SDK semantic validator or F3 claim.",
    "Cirq observations are local ideal simulation, not independently authenticated evidence.",
    "No hardware, noise, sampling, shots, credentials, or physical fidelity claim.",
    "created_at is a fixed identity sentinel, not an event timestamp.",
    "Export loses native context name, shots, seed, invariants, and reusable-path structure.",
]


class CirqInteropError(E7QError):
    """Typed refusal; never a quantum inequality result."""

    def __init__(self, status: str, reason: str):
        self.status, self.reason = status, reason
        super().__init__(reason)


def _refuse(reason: str, status: str = "UNSUPPORTED"):
    raise CirqInteropError(status, reason)


def _source_bytes(source: str) -> bytes:
    if not isinstance(source, str):
        _refuse("source must be UTF-8 text", "ERROR")
    if len(source) > MAX_SOURCE_BYTES:
        _refuse("source byte budget exceeded", "RESOURCE_REFUSED")
    try:
        raw = source.encode("utf-8")
    except UnicodeError:
        _refuse("source is not UTF-8", "ERROR")
    if len(raw) > MAX_SOURCE_BYTES:
        _refuse("source byte budget exceeded", "RESOURCE_REFUSED")
    return raw


def _shape(node: ast.AST, expected: str) -> bool:
    return ast.dump(node, include_attributes=False) == ast.dump(
        ast.parse(expected).body[0], include_attributes=False)


def _integer(node: ast.AST) -> int:
    if not isinstance(node, ast.Constant) or type(node.value) is not int:
        _refuse("literal integer required")
    return node.value


def admit_cirq_source(source: str) -> Program:
    """Non-executing strict AST admission; malformed syntax raises typed ERROR.

    Measurement uses explicit indexed references, as the current exporter does,
    not Python star expansion. Exact original bytes are retained by evaluate.
    """
    _source_bytes(source)
    try:
        tree = ast.parse(source)
    except SyntaxError:
        _refuse("invalid Cirq source syntax", "ERROR")
    except (MemoryError, RecursionError):
        _refuse("AST parser resource limit", "RESOURCE_REFUSED")
    stack, count = [(tree, 0)], 0
    while stack:
        node, depth = stack.pop()
        count += 1
        if count > 2048 or depth > 32:
            _refuse("AST node/depth budget exceeded", "RESOURCE_REFUSED")
        stack.extend((child, depth + 1) for child in ast.iter_child_nodes(node))
    body = tree.body
    if len(body) < 4 or not _shape(body[0], "import cirq"):
        _refuse("expected sole unaliased cirq import and exporter declarations")
    declaration = body[1]
    if not (isinstance(declaration, ast.Assign) and len(declaration.targets) == 1
            and isinstance(declaration.value, ast.Call)
            and len(declaration.value.args) == 1):
        _refuse("expected LineQubit.range declaration")
    n = _integer(declaration.value.args[0])
    if not 1 <= n <= MAX_QUBITS:
        _refuse("qubit width outside 1..2", "RESOURCE_REFUSED")
    if not _shape(declaration, f"qubits = cirq.LineQubit.range({n})"):
        _refuse("unexpected qubit declaration")
    if not _shape(body[2], "circuit = cirq.Circuit()"):
        _refuse("unexpected circuit declaration")
    if len(body) - 4 > MAX_GATES:
        _refuse("unitary gate budget exceeded", "RESOURCE_REFUSED")
    operations = []
    for index, statement in enumerate(body[3:]):
        if not (isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Call)
                and len(statement.value.args) == 1):
            _refuse("expected circuit.append call")
        inner = statement.value.args[0]
        if not (isinstance(inner, ast.Call) and isinstance(inner.func, ast.Attribute)
                and isinstance(inner.func.value, ast.Name)
                and inner.func.value.id == "cirq"):
            _refuse("expected canonical built-in Cirq gate")
        name = inner.func.attr
        if name == "measure":
            refs = ", ".join(f"qubits[{q}]" for q in range(n))
            if index != len(body) - 4 or not _shape(
                    statement, f'circuit.append(cirq.measure({refs}, key="c"))'):
                _refuse("only final full identity measurement with key c admitted")
            operations.append(Operation("MEASURE", full_register=True))
            continue
        gate = "CX" if name == "CNOT" else name
        if name == "CX" or gate not in GATES or len(inner.args) != GATES[gate]:
            _refuse("unsupported gate or arity")
        indices = []
        for arg in inner.args:
            if not isinstance(arg, ast.Subscript):
                _refuse("indexed declared qubit required")
            q = _integer(arg.slice)
            if not 0 <= q < n:
                _refuse("qubit index outside declared wires")
            indices.append(q)
        refs = ", ".join(f"qubits[{q}]" for q in indices)
        if len(set(indices)) != len(indices) or not _shape(
                statement, f"circuit.append(cirq.{name}({refs}))"):
            _refuse("noncanonical gate call")
        operations.append(Operation(gate, tuple(indices)))
    if not operations or operations[-1].gate != "MEASURE":
        _refuse("terminal measurement required")
    program = Program("cirq_admitted", 1, "statevector", None, n, n,
                      "cirq_admitted", tuple(operations), None, False)
    validate_program(program)
    return program


def _subset(program: Program) -> None:
    if not 1 <= program.qubits <= MAX_QUBITS or len(program.operations) > 65:
        _refuse("native width/operation budget exceeded", "RESOURCE_REFUSED")
    if program.backend != "statevector" or program.bits != program.qubits:
        _refuse("statevector and identity full-register classical map required")
    if not program.operations or program.operations[-1] != Operation("MEASURE", full_register=True):
        _refuse("terminal full-register measurement required")
    if any(op.gate not in GATES or op.condition is not None
           for op in program.operations[:-1]):
        _refuse("only unconditional supported unitary prefix admitted")
    validate_program(program)
    preflight(program, POLICY, representation="unitary")


def _json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _records(program: Program) -> dict:
    return {"qubits": program.qubits,
            "operations": [{"gate": op.gate, "qubits": list(op.qubits)}
                           for op in program.operations[:-1]]}


def _child_transport(records: dict, timeout_seconds: float) -> dict:
    env = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1",
               PYTHONDONTWRITEBYTECODE="1")
    try:
        completed = subprocess.run(
            [sys.executable, "-B", "-m", "e7q.cirq_interop", "--worker"],
            input=_json(records), capture_output=True, text=True, env=env,
            timeout=timeout_seconds, check=False)
    except subprocess.TimeoutExpired:
        _refuse("Cirq child wall deadline exceeded", "TIMEOUT")
    except OSError:
        _refuse("Cirq child could not start", "ERROR")
    if completed.returncode != 0:
        resource_signal = getattr(signal, "SIGXCPU", None)
        status = ("RESOURCE_REFUSED" if resource_signal is not None
                  and completed.returncode == -resource_signal else "ERROR")
        _refuse("Cirq child terminated without observation", status)
    if len(completed.stdout.encode("utf-8")) > MAX_JSON_BYTES:
        _refuse("child response byte budget exceeded", "RESOURCE_REFUSED")
    try:
        response = json.loads(completed.stdout)
    except (ValueError, RecursionError):
        _refuse("invalid child JSON", "ERROR")
    if not isinstance(response, dict):
        _refuse("invalid child response", "ERROR")
    if response.get("status") != "OK":
        status = response.get("status")
        if status not in {"UNSUPPORTED", "RESOURCE_REFUSED", "TIMEOUT", "ERROR"}:
            status = "ERROR"
        _refuse(str(response.get("reason", "child failure")), status)
    return response


def _worker() -> dict:
    # Fail closed before importing the optional SDK. This is a resource boundary,
    # not a general sandbox; the worker never receives executable source/objects.
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (MEMORY_BYTES, MEMORY_BYTES))
        resource.setrlimit(resource.RLIMIT_CPU, (CPU_SECONDS, CPU_SECONDS))
    except (ImportError, AttributeError, OSError, ValueError):
        return {"status": "RESOURCE_REFUSED", "reason": "POSIX resource limits unavailable"}
    try:
        raw = sys.stdin.buffer.read(MAX_JSON_BYTES + 1)
        if len(raw) > MAX_JSON_BYTES:
            _refuse("worker input budget exceeded", "RESOURCE_REFUSED")
        records = json.loads(raw)
        if not isinstance(records, dict) or set(records) != {"qubits", "operations"}:
            _refuse("invalid worker record", "ERROR")
        n, operations = records["qubits"], records["operations"]
        if type(n) is not int or not 1 <= n <= MAX_QUBITS:
            _refuse("worker width refused", "RESOURCE_REFUSED")
        if not isinstance(operations, list) or len(operations) > MAX_GATES:
            _refuse("worker operations refused", "RESOURCE_REFUSED")
        for op in operations:
            if (not isinstance(op, dict) or set(op) != {"gate", "qubits"}
                    or not isinstance(op["gate"], str) or op["gate"] not in GATES
                    or not isinstance(op["qubits"], list)
                    or len(op["qubits"]) != GATES[op["gate"]]
                    or any(type(q) is not int or not 0 <= q < n for q in op["qubits"])
                    or len(set(op["qubits"])) != len(op["qubits"])):
                _refuse("invalid worker operation", "ERROR")
        try:
            import cirq
        except ImportError:
            return {"status": "UNSUPPORTED", "reason": "missing optional Cirq dependency"}
        import numpy as np
        if cirq.__version__ != CIRQ_VERSION:
            return {"status": "UNSUPPORTED", "reason": "requires Cirq " + CIRQ_VERSION}
        qubits = cirq.LineQubit.range(n)
        gates = {"X": cirq.X, "Y": cirq.Y, "Z": cirq.Z, "H": cirq.H,
                 "S": cirq.S, "T": cirq.T, "CX": cirq.CNOT,
                 "CZ": cirq.CZ, "SWAP": cirq.SWAP}
        circuit = cirq.Circuit(gates[op["gate"]](*(qubits[q] for q in op["qubits"]))
                               for op in operations)
        simulator = cirq.Simulator(dtype=np.complex128, split_untangled_states=False)
        columns = [simulator.simulate(circuit, qubit_order=qubits, initial_state=basis)
                   .final_state_vector for basis in range(2**n)]
        matrix = np.column_stack(columns)
        if not np.isfinite(matrix).all():
            _refuse("nonfinite simulator output", "ERROR")
        return {"status": "OK", "real": matrix.real.tolist(), "imag": matrix.imag.tolist(),
                "environment": {"python": platform.python_version(),
                                "cirq": cirq.__version__, "numpy": np.__version__}}
    except CirqInteropError as exc:
        return {"status": exc.status, "reason": exc.reason}
    except MemoryError:
        return {"status": "RESOURCE_REFUSED", "reason": "child allocation failure"}
    except Exception:
        return {"status": "ERROR", "reason": "child evaluation error"}


def _matrix(response: dict, n: int):
    import numpy as np
    if set(response) != {"status", "real", "imag", "environment"}:
        _refuse("unexpected simulator response fields", "ERROR")
    env = response["environment"]
    if (not isinstance(env, dict) or set(env) != {"python", "cirq", "numpy"}
            or env["cirq"] != CIRQ_VERSION
            or any(not isinstance(v, str) or len(v) > 128 for v in env.values())):
        _refuse("invalid simulator environment", "ERROR")
    for key in ("real", "imag"):
        rows = response[key]
        if (not isinstance(rows, list) or len(rows) != 2**n
                or any(not isinstance(row, list) or len(row) != 2**n for row in rows)
                or any(type(v) not in (int, float) or not math.isfinite(v)
                       for row in rows for v in row)):
            _refuse("invalid simulator matrix", "ERROR")
    return np.array(response["real"]) + 1j * np.array(response["imag"])


def _graph(source, exported, returned, original, admitted, result):
    from .ir import build_artifact, build_graph, build_relation, validate_graph
    artifacts, relations = [], []

    def add(kind, payload, refs=()):
        item = build_artifact(kind, payload, created_at=IDENTITY_SENTINEL,
                              actor=VERSION, limitations=LIMITATIONS,
                              source_refs=[r["artifact_id"] for r in refs])
        artifacts.append(item)
        return item

    def link(kind, left, right):
        relations.append(build_relation(kind, left["artifact_id"], right["artifact_id"],
                                        validation_status="declared-not-verified"))

    sources = [add("source", {"format": fmt, "encoding": "utf-8", "source": text})
               for fmt, text in (("e7q", source), ("cirq-export", exported),
                                 ("cirq-return", returned))]
    def program_payload(program):
        payload = asdict(program)
        payload["allowed_outcomes"] = (sorted(program.allowed_outcomes)
                                       if program.allowed_outcomes is not None else None)
        return json.loads(_json(payload))

    representation = add("representation", {"format": VERSION + "/programs",
        "native": program_payload(original), "admitted": program_payload(admitted)}, sources)
    for item in sources:
        link("represents", item, representation)
    execution = add("execution", {"format": VERSION + "/execution",
        "method": result["method"], "environment": result["environment"],
        "limits": result["limits"]}, [representation])
    observation = add("observation", {"format": VERSION + "/observation",
        "simulator": result["simulator"], "diagnostics": result["diagnostics"]}, [execution])
    assessment = add("assessment", {"format": VERSION + "/assessment",
        "native_assessment": result["native_assessment"], "status": result["status"],
        "criterion": result["criterion"], "tolerance": result["tolerance"]},
        [representation, observation])
    claim = add("claim", {"format": VERSION + "/claim", "scope": "F0/F1 only",
        "statement": "A bounded native return assessment and SDK mapping diagnostic were made; not an unqualified equivalence claim.",
        "native_criterion": result["criterion"], "native_outcome": result["status"],
        "claim_type": "bounded-local-reference-comparison",
        "evidence_refs": [assessment["artifact_id"]],
        "support_status": "supported-within-declared-scope",
        "boundaries": LIMITATIONS, "prohibited_inferences": ["F2 SDK truth", "F3", "hardware fidelity"]},
        [assessment])
    for kind, left, right in (("produces", representation, execution),
            ("produces", execution, observation), ("assesses", assessment, observation),
            ("supports", assessment, claim)):
        link(kind, left, right)
    graph = build_graph(artifacts, relations, name=VERSION, extensions={
        "e7q.cirq_interop": {"optional": True, "scope": "F0/F1", "sdk_truth": False}})
    if validate_graph(graph, level="F1")["status"] != "PASS":
        _refuse("internal evidence graph failed F1 integrity", "ERROR")
    return graph


def evaluate_roundtrip(source: str, *, returned_source: str | None = None,
                       criterion="tolerance", tolerance=1e-9,
                       timeout_seconds=15.0) -> dict:
    """Compare native/admitted semantics and independently check SDK mapping.

    PASS/FAIL are domain assessments only. Refusals and execution failures have
    distinct status codes and no assessment. Native measurement means all-basis
    probabilities; zero-input diagnostics do not redefine that core criterion.
    """
    try:
        _source_bytes(source)
        for value, label in ((tolerance, "tolerance"), (timeout_seconds, "timeout")):
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                _refuse(label + " must be finite positive nonboolean", "ERROR")
        if timeout_seconds > 30:
            _refuse("wall deadline exceeds 30 seconds", "RESOURCE_REFUSED")
        if criterion not in {"exact", "global-phase", "tolerance", "measurement"}:
            _refuse("unsupported comparison criterion")
        original = parse(source, limits=PARSE_LIMITS)
        _subset(original)
        exported = adapt(original, "cirq").source
        returned = exported if returned_source is None else returned_source
        admitted = admit_cirq_source(returned)
        _subset(admitted)
        if original.qubits != admitted.qubits:
            _refuse("returned declared width differs from native input")
        native = comparison_result(compare(original, admitted, criterion, tolerance, policy=POLICY))
        response = _child_transport(_records(admitted), float(timeout_seconds))
        sdk = _matrix(response, admitted.qubits)
        import numpy as np
        left = circuit_unitary(original, policy=POLICY)
        right = circuit_unitary(admitted, policy=POLICY)
        vector_error = float(np.max(np.abs(right[:, 0] - sdk[:, 0])))
        matrix_error = float(np.max(np.abs(right - sdk)))
        consistent = max(vector_error, matrix_error) <= CONSISTENCY_TOLERANCE
        # SDK inconsistencies are execution errors, never quantum inequality.
        if not consistent:
            _refuse("Cirq/native basis mapping consistency check failed", "ERROR")
        result = {"schema": VERSION, "status": native["status"],
            "criterion": criterion, "tolerance": float(tolerance),
            "native_assessment": native, "environment": response["environment"],
            "method": {"simulator": "cirq.Simulator", "dtype": "complex128",
                "split_untangled_states": False, "qubit_order": "LineQubit ascending; q0 tensor MSB",
                "basis_inputs": list(range(2**admitted.qubits)),
                "terminal_measurement": "excluded from simulation; identity q->c map",
                "observations": "ideal probabilities only; no sampling",
                "sampling_status": "NOT_ASSESSED",
                "native_criterion_scope": "all-basis unitary or all-basis measurement probabilities"},
            "limits": {"source_bytes": MAX_SOURCE_BYTES, "ast_nodes": 2048, "ast_depth": 32,
                "qubits": MAX_QUBITS, "unitary_gates": MAX_GATES, "json_bytes": MAX_JSON_BYTES,
                "memory_bytes": MEMORY_BYTES, "cpu_seconds": CPU_SECONDS,
                "timeout_seconds": float(timeout_seconds),
                "native_memory_budget_bytes": POLICY.memory_budget_bytes},
            "simulator": response,
            "diagnostics": {"mapping_zero_input_max_vector_error": vector_error,
                "mapping_all_basis_max_matrix_error": matrix_error,
                "mapping_tolerance": CONSISTENCY_TOLERANCE, "mapping_consistent": consistent,
                "state_relative_zero_input_max_error": float(np.max(np.abs(left[:, 0] - sdk[:, 0]))),
                "measurement_relative_zero_input_max_error": float(np.max(
                    np.abs(np.abs(left[:, 0])**2 - np.abs(sdk[:, 0])**2))),
                "zero_input_ideal_probabilities": (np.abs(sdk[:, 0])**2).tolist()},
            "limitations": LIMITATIONS.copy()}
        result["graph"] = _graph(source, exported, returned, original, admitted, result)
        # Convert dataclass tuples/frozensets to bounded JSON primitives.
        return json.loads(_json(result))
    except CirqInteropError as exc:
        return {"schema": VERSION, "status": exc.status, "reason": exc.reason,
                "native_assessment": None}
    except E7QResourceLimitError:
        return {"schema": VERSION, "status": "RESOURCE_REFUSED",
                "reason": "native parser or preflight resource refusal", "native_assessment": None}
    except (E7QError, ValueError, TypeError, OverflowError):
        return {"schema": VERSION, "status": "ERROR", "reason": "invalid input or result",
                "native_assessment": None}
    except MemoryError:
        return {"schema": VERSION, "status": "RESOURCE_REFUSED",
                "reason": "parent allocation failure", "native_assessment": None}


def replay(result: dict, source: str, *, returned_source: str | None = None,
           criterion="tolerance", tolerance=1e-9, timeout_seconds=15.0) -> bool:
    """Recompute admission, full native assessment, SDK observations and F1 graph.

    Caller supplies the independent inputs/options, not values trusted from the
    result. Exact canonical comparison rejects even consistently rehashed edits.
    Only successfully evaluated domain results are replayable attestations.
    """
    try:
        if not isinstance(result, dict) or result.get("status") not in {"PASS", "FAIL"}:
            return False
        expected = evaluate_roundtrip(source, returned_source=returned_source,
            criterion=criterion, tolerance=tolerance, timeout_seconds=timeout_seconds)
        return expected.get("status") in {"PASS", "FAIL"} and _json(result) == _json(expected)
    except (ValueError, TypeError, RecursionError):
        return False


if __name__ == "__main__":
    if sys.argv[1:] != ["--worker"]:
        raise SystemExit("private worker entry point only")
    output = _json(_worker())
    if len(output.encode("utf-8")) > MAX_JSON_BYTES:
        output = _json({"status": "RESOURCE_REFUSED", "reason": "worker output budget exceeded"})
    print(output)
