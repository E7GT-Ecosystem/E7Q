# SPDX-License-Identifier: Apache-2.0
"""Bounded, auditable OpenQASM 2.0 import without circuit execution."""
from __future__ import annotations

from hashlib import sha256
import re
from typing import Any

from .language import E7QError


SCHEMA = "e7q.openqasm2-circuit/v1alpha1"
COUNT_ORDERS = frozenset({"clbit-ascending", "clbit-descending"})

_GATE_ARITIES = {
    "id": 1,
    "x": 1,
    "y": 1,
    "z": 1,
    "h": 1,
    "s": 1,
    "sdg": 1,
    "t": 1,
    "tdg": 1,
    "sx": 1,
    "sxdg": 1,
    "rx": 1,
    "ry": 1,
    "rz": 1,
    "p": 1,
    "u1": 1,
    "u2": 1,
    "u3": 1,
    "u": 1,
    "cx": 2,
    "cy": 2,
    "cz": 2,
    "ch": 2,
    "swap": 2,
    "crx": 2,
    "cry": 2,
    "crz": 2,
    "cu1": 2,
    "cu3": 2,
    "rxx": 2,
    "ryy": 2,
    "rzz": 2,
    "ecr": 2,
    "ccx": 3,
    "cswap": 3,
}
_PARAMETER_COUNTS = {
    "rx": 1,
    "ry": 1,
    "rz": 1,
    "p": 1,
    "u1": 1,
    "crx": 1,
    "cry": 1,
    "crz": 1,
    "cu1": 1,
    "rxx": 1,
    "ryy": 1,
    "rzz": 1,
    "u2": 2,
    "u3": 3,
    "u": 3,
    "cu3": 3,
}
_REGISTER = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\[(\d+)\]")


def _digest(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _strip_comments(source: str) -> str:
    return "\n".join(line.split("//", 1)[0] for line in source.splitlines())


def _split_parameters(value: str | None) -> list[str]:
    if value is None or not value.strip():
        return []
    parameters = [item.strip() for item in value.split(",")]
    if any(not item for item in parameters):
        raise E7QError("OpenQASM 2 contains an empty gate parameter")
    allowed = re.compile(r"[0-9A-Za-z_+\-*/().\s]+")
    if any(not allowed.fullmatch(item) for item in parameters):
        raise E7QError("OpenQASM 2 contains an unsupported parameter expression")
    return parameters


def _reference(
    token: str,
    registers: dict[str, int],
    *,
    kind: str,
) -> dict[str, object]:
    match = _REGISTER.fullmatch(token.strip())
    if not match:
        raise E7QError(f"invalid OpenQASM 2 {kind} reference: {token.strip()}")
    register, raw_index = match.groups()
    if register not in registers:
        raise E7QError(f"unknown OpenQASM 2 {kind} register: {register}")
    index = int(raw_index)
    if index >= registers[register]:
        raise E7QError(f"OpenQASM 2 {kind} index out of range: {token.strip()}")
    return {"register": register, "index": index}


def _gate_statement(
    statement: str,
    qregs: dict[str, int],
    cregs: dict[str, int],
) -> dict[str, object]:
    condition: dict[str, object] | None = None
    conditional = re.fullmatch(
        r"if\s*\(\s*([A-Za-z_]\w*)\s*==\s*(\d+)\s*\)\s*(.+)",
        statement,
    )
    if conditional:
        register, raw_value, statement = conditional.groups()
        if register not in cregs:
            raise E7QError(f"unknown OpenQASM 2 classical register: {register}")
        value = int(raw_value)
        if value >= 2 ** cregs[register]:
            raise E7QError("OpenQASM 2 conditional value exceeds register width")
        condition = {"register": register, "equals": value}
    match = re.fullmatch(
        r"([A-Za-z_][A-Za-z0-9_]*)(?:\s*\((.*)\))?\s+(.+)", statement
    )
    if not match:
        raise E7QError(f"unsupported OpenQASM 2 statement: {statement[:160]}")
    name, raw_parameters, raw_operands = match.groups()
    name = name.lower()
    if name not in _GATE_ARITIES:
        raise E7QError(f"unsupported OpenQASM 2 gate: {name}")
    qubits = [
        _reference(item, qregs, kind="quantum")
        for item in raw_operands.split(",")
    ]
    if len(qubits) != _GATE_ARITIES[name]:
        raise E7QError(f"OpenQASM 2 gate {name} has invalid arity")
    parameters = _split_parameters(raw_parameters)
    expected_parameters = _PARAMETER_COUNTS.get(name, 0)
    if len(parameters) != expected_parameters:
        raise E7QError(f"OpenQASM 2 gate {name} has invalid parameter count")
    result: dict[str, object] = {
        "name": name,
        "parameters": parameters,
        "qubits": qubits,
    }
    if condition is not None:
        result["condition"] = condition
    return result


def import_openqasm2(source: str, *, name: str = "ImportedCircuit") -> dict[str, object]:
    """Import a supported OpenQASM 2.0 circuit into a non-executable E7Q artifact.

    The importer preserves physical indices, measurement destinations, parameters,
    and optional register-wide classical conditions. It deliberately does not
    execute included files, expand custom gates, or allocate a state vector.
    """
    if not isinstance(source, str) or not source.strip():
        raise E7QError("OpenQASM 2 source must be non-empty UTF-8 text")
    cleaned = _strip_comments(source)
    if not cleaned.rstrip().endswith(";"):
        raise E7QError("OpenQASM 2 statements must end with semicolons")
    statements = [item.strip() for item in cleaned.split(";") if item.strip()]
    if not statements or statements[0] != "OPENQASM 2.0":
        raise E7QError("source must declare OPENQASM 2.0")

    qregs: dict[str, int] = {}
    cregs: dict[str, int] = {}
    includes: list[str] = []
    operations: list[dict[str, object]] = []
    measurements: list[dict[str, object]] = []
    operation_counts: dict[str, int] = {}
    declarations_open = True

    for statement in statements[1:]:
        include = re.fullmatch(r'include\s+"([^"\n]+)"', statement)
        if include:
            if not declarations_open:
                raise E7QError("OpenQASM 2 include must precede operations")
            includes.append(include.group(1))
            continue
        declaration = re.fullmatch(
            r"(qreg|creg)\s+([A-Za-z_][A-Za-z0-9_]*)\[(\d+)\]", statement
        )
        if declaration:
            if not declarations_open:
                raise E7QError("OpenQASM 2 register declaration must precede operations")
            kind, register, raw_width = declaration.groups()
            target = qregs if kind == "qreg" else cregs
            if register in qregs or register in cregs:
                raise E7QError(f"duplicate OpenQASM 2 register: {register}")
            width = int(raw_width)
            if width < 1:
                raise E7QError("OpenQASM 2 register widths must be positive")
            target[register] = width
            continue

        declarations_open = False
        whole_measure = re.fullmatch(
            r"measure\s+([A-Za-z_]\w*)\s*->\s*([A-Za-z_]\w*)", statement
        )
        partial_measure = re.fullmatch(
            r"measure\s+([^\s]+)\s*->\s*([^\s]+)", statement
        )
        if whole_measure:
            qreg, creg = whole_measure.groups()
            if qreg not in qregs or creg not in cregs:
                raise E7QError("OpenQASM 2 whole-register measurement uses unknown register")
            if qregs[qreg] != cregs[creg]:
                raise E7QError("OpenQASM 2 whole-register measurement widths differ")
            pairs = [
                (
                    {"register": qreg, "index": index},
                    {"register": creg, "index": index},
                )
                for index in range(qregs[qreg])
            ]
        elif partial_measure:
            pairs = [
                (
                    _reference(partial_measure.group(1), qregs, kind="quantum"),
                    _reference(partial_measure.group(2), cregs, kind="classical"),
                )
            ]
        else:
            pairs = []
        if pairs:
            for qubit, clbit in pairs:
                operation = {
                    "name": "measure",
                    "parameters": [],
                    "qubits": [qubit],
                    "clbits": [clbit],
                }
                operation["index"] = len(operations)
                operations.append(operation)
                measurements.append({"qubit": qubit, "clbit": clbit})
                operation_counts["measure"] = operation_counts.get("measure", 0) + 1
            continue

        barrier = re.fullmatch(r"barrier\s+(.+)", statement)
        if barrier:
            references: list[dict[str, object]] = []
            for item in barrier.group(1).split(","):
                token = item.strip()
                if token in qregs:
                    references.extend(
                        {"register": token, "index": index}
                        for index in range(qregs[token])
                    )
                else:
                    references.append(_reference(token, qregs, kind="quantum"))
            operation = {
                "index": len(operations),
                "name": "barrier",
                "parameters": [],
                "qubits": references,
            }
        else:
            operation = _gate_statement(statement, qregs, cregs)
            operation["index"] = len(operations)
        operations.append(operation)
        opname = str(operation["name"])
        operation_counts[opname] = operation_counts.get(opname, 0) + 1

    if not qregs or not cregs:
        raise E7QError("OpenQASM 2 source must declare quantum and classical registers")
    if not measurements:
        raise E7QError("OpenQASM 2 source must contain measurement")
    measured_destinations = [
        (str(item["clbit"]["register"]), int(item["clbit"]["index"]))
        for item in measurements
    ]
    if len(measured_destinations) != len(set(measured_destinations)):
        raise E7QError("OpenQASM 2 measures more than once into a classical bit")

    active = sorted(
        {
            (str(ref["register"]), int(ref["index"]))
            for operation in operations
            for ref in operation.get("qubits", [])
        }
    )
    source_digest = _digest(source)
    return {
        "schema": SCHEMA,
        "status": "PASS",
        "name": name,
        "language": {"name": "OpenQASM", "version": "2.0", "includes": includes},
        "source": {"digest": source_digest, "characters": len(source)},
        "registers": {
            "quantum": [{"name": key, "width": value} for key, value in qregs.items()],
            "classical": [{"name": key, "width": value} for key, value in cregs.items()],
        },
        "operations": operations,
        "operation_counts": dict(sorted(operation_counts.items())),
        "measurements": measurements,
        "active_qubits": [
            {"register": register, "index": index} for register, index in active
        ],
        "outcome_conventions": {
            "canonical": "clbit-ascending",
            "canonical_description": (
                "Within one classical register, c[0] is the leftmost character."
            ),
            "qiskit_counts": "clbit-descending",
            "qiskit_description": (
                "Within one classical register, the highest clbit is leftmost."
            ),
        },
        "proof": [
            {"step": 0, "kind": "source-identity", "source_digest": source_digest},
            {
                "step": 1,
                "kind": "parse",
                "operations": len(operations),
                "measurements": len(measurements),
            },
            {
                "step": 2,
                "kind": "evidence-boundary",
                "boundary": (
                    "Syntactic and structural OpenQASM 2.0 import only; included files "
                    "and custom gates are not executed, hardware submission is not "
                    "authenticated, and the circuit is not simulated."
                ),
            },
        ],
    }


def canonicalize_outcome(label: str, *, order: str) -> str:
    """Return a single-register count label in ascending classical-bit order."""
    if order not in COUNT_ORDERS:
        raise E7QError(f"unsupported count-label order: {order}")
    if not isinstance(label, str) or not label or set(label) - {"0", "1"}:
        raise E7QError("count labels must be non-empty binary strings")
    return label if order == "clbit-ascending" else label[::-1]
