# SPDX-License-Identifier: Apache-2.0
"""Optional compact Clifford execution; never a dense fallback or IR criterion."""
from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import version
from typing import Any

import numpy as np
from .language import E7QError, Program

BACKEND_ID = "stim.TableauSimulator"
SUPPORTED_VERSION = "1.16.0"
GATES = frozenset({"X", "Y", "Z", "H", "S", "CX", "CZ", "SWAP"})


class BackendUnsupported(E7QError):
    def __init__(self, reason: str):
        self.assessment = {"reason": reason, "backend": BACKEND_ID}
        super().__init__(reason)


def _dependency():
    try:
        import stim
    except (ImportError, OSError) as exc:
        raise BackendUnsupported("optional stabilizer dependency unavailable; install e7q[stabilizer]") from exc
    if version("stim") != SUPPORTED_VERSION:
        raise BackendUnsupported("unsupported Stim version; expected " + SUPPORTED_VERSION)
    return stim


def capabilities() -> dict[str, object]:
    return {
        "schema": "e7q.stabilizer-capabilities/1", "backend": BACKEND_ID,
        "dependency": "stim", "supported_version": SUPPORTED_VERSION,
        "gates": sorted(GATES), "initialization": "computational zero; X gates prepare other basis states",
        "measurement": "computational basis; individual/full-register",
        "classical_control": "one-bit equality controls on admitted Clifford gates; mid-circuit supported",
        "checks": ["normalized", "exact premeasurement Pauli expectation for unconditional terminal circuits", "finite-shot assertions"],
        "unsupported": ["T/non-Clifford", "noise/mixed states", "exhaustive probabilities", "exact output support", "unitary/channel comparison", "ensemble expectations after mid-circuit measurement"],
        "fallback": "none", "bit_order": "native q0/c0 first (leftmost)",
        "seed_scope": "same calls/Stim version/machine; not portable across SIMD or dense backend",
        "boundary": "Simulator/model evidence only; no hardware fidelity, advantage or universal equivalence.",
    }


@dataclass(frozen=True)
class StabilizerExecution:
    program: Program
    state: Any
    premeasurement: Any | None
    counts: dict[str, int]
    proof: tuple[dict[str, object], ...]
    resources: dict[str, object]

    @property
    def probabilities(self) -> dict[str, float]:
        # Absence of exhaustive probabilities must not look like an exact distribution.
        return {}


def _apply(sim, operation) -> None:
    method = {"CX": "cnot", "CZ": "cz", "SWAP": "swap"}.get(operation.gate, operation.gate.lower())
    getattr(sim, method)(*operation.qubits)


def run_stabilizer(program: Program, resources: dict[str, object]) -> StabilizerExecution:
    # Admission happens before dependency/tableau allocation; all operations checked,
    # including conditional branches that might not be visited by sampled shots.
    for op in program.operations:
        if op.gate not in GATES | {"MEASURE", "ASSERT"}:
            raise BackendUnsupported("stabilizer does not support " + op.gate)
    if program.seed is not None and not 0 <= program.seed < 2**64:
        raise BackendUnsupported("stabilizer seed must be in 0..2**64-1")
    stim = _dependency()
    rng = np.random.default_rng(program.seed)
    first = next(i for i, op in enumerate(program.operations) if op.gate == "MEASURE")
    terminal = (all(op.gate in GATES and op.condition is None for op in program.operations[:first]) and
                all(op.gate == "MEASURE" for op in program.operations[first:]))
    prepared = None
    if terminal:
        prepared = stim.TableauSimulator(seed=program.seed)
        prepared.set_num_qubits(program.qubits)
        for op in program.operations[:first]:
            _apply(prepared, op)
    counts: dict[str, int] = {}
    stats = [{"executed": 0, "skipped": 0, "failed": 0, "outcomes": {"0": 0, "1": 0}} for op in program.operations]
    for shot in range(program.shots):
        child_seed = int(rng.integers(0, 2**64, dtype=np.uint64))
        sim = prepared.copy(seed=child_seed) if prepared is not None else stim.TableauSimulator(seed=child_seed)
        if prepared is None:
            sim.set_num_qubits(program.qubits)
        classical = [0] * program.bits
        for i, op in enumerate(program.operations):
            stat = stats[i]
            if op.gate == "ASSERT":
                stat["executed"] += 1
                bit, value = op.condition
                stat["failed"] += int(classical[bit] != value)
                continue
            if op.condition is not None and classical[op.condition[0]] != op.condition[1]:
                stat["skipped"] += 1
                continue
            stat["executed"] += 1
            if terminal and i < first:
                continue
            if op.gate == "MEASURE":
                if op.full_register:
                    for q in range(program.qubits):
                        classical[q] = int(sim.measure(q))
                else:
                    outcome = int(sim.measure(op.qubits[0]))
                    classical[op.bits[0]] = outcome
                    stat["outcomes"][str(outcome)] += 1
            else:
                _apply(sim, op)
        label = "".join(map(str, classical))
        counts[label] = counts.get(label, 0) + 1
    proof: list[dict[str, object]] = [{"step": 0, "kind": "initialize", "backend": BACKEND_ID, "shots": program.shots}]
    for op, stat in zip(program.operations, stats):
        item = {"step": len(proof), "kind": "project" if op.gate == "MEASURE" else "transform",
                "operator": op.gate, "qubits": list(op.qubits), "bits": list(op.bits),
                "full_register": op.full_register, **stat}
        if op.condition is not None:
            item["condition"] = {"bit": op.condition[0], "equals": op.condition[1]}
        if op.gate == "ASSERT":
            item.update(kind="assert", assertion=op.label or "classical assertion", passed=stat["failed"] == 0)
        proof.append(item)
    proof.append({"step": len(proof), "kind": "result", "outcomes": counts, "shots": program.shots})
    return StabilizerExecution(program, sim, prepared, counts, tuple(proof), resources)


def verify_stabilizer(execution: StabilizerExecution, *, pauli_checks=()) -> dict[str, object]:
    """Exact expectations refer to the unconditional state BEFORE Z measurement.

    A final sampled branch is never substituted for an ensemble property.
    Unsupported requested checks remain unassessed, not an empty PASS.
    """
    if len(pauli_checks) > 64:
        raise E7QError("at most 64 Pauli checks are admitted")
    checks: list[dict[str, object]] = []
    if execution.program.require_normalized:
        checks.append({"name": "normalized", "status": "PASS", "passed": True,
                       "method": "normalized pure Clifford tableau by construction"})
    if execution.program.allowed_outcomes is not None:
        checks.append({"name": "outcomes", "status": "UNSUPPORTED", "passed": None,
                       "reason": "exact classical support check is not implemented; counts are not a substitute"})
    for request in pauli_checks:
        pauli = request.get("pauli") if isinstance(request, dict) else None
        expected = request.get("expected") if isinstance(request, dict) else None
        valid = (isinstance(request, dict) and set(request) == {"pauli", "expected"} and
                 isinstance(pauli, str) and len(pauli) == execution.program.qubits and
                 not set(pauli) - set("IXYZ") and type(expected) is int and expected in (-1, 0, 1))
        if not valid or execution.premeasurement is None:
            checks.append({"name": "pauli-expectation", "status": "UNSUPPORTED", "passed": None,
                           "reason": "requires an admitted Pauli request and unconditional terminal-measurement preparation"})
            continue
        value = execution.premeasurement.peek_observable_expectation(_dependency().PauliString(pauli))
        passed = value == expected
        checks.append({"name": "pauli-expectation", "pauli": pauli, "expected": expected,
                       "value": value, "status": "PASS" if passed else "FAIL", "passed": passed,
                       "method": "exact stabilizer expectation", "scope": "premeasurement state", "shots": None})
    for item in execution.proof:
        if item["kind"] == "assert":
            checks.append({"name": item["assertion"], "status": "PASS" if item["passed"] else "FAIL",
                           "passed": item["passed"], "failed_shots": item["failed"], "method": "finite-shot assertion"})
    if any(c["status"] == "FAIL" for c in checks):
        status = "FAIL"
    elif not checks or any(c["status"] == "UNSUPPORTED" for c in checks):
        status = "NOT_ASSESSED"
    else:
        status = "PASS"
    tableau = execution.state.current_inverse_tableau().inverse()
    return {
        "schema": "e7q.stabilizer-result/1", "status": status,
        "execution_status": "COMPLETED", "verification_status": status,
        "checks": checks, "counts": execution.counts,
        "sample_frequencies": {label: count / execution.program.shots for label, count in execution.counts.items()},
        "probabilities": None, "probability_semantics": "exhaustive exact distribution not materialized",
        "state": {"representation": "stabilizer-generators", "scope": "final-shot collapsed state",
                  "qubits": execution.program.qubits,
                  "generators": [str(tableau.z_output(i)) for i in range(execution.program.qubits)]},
        "proof": list(execution.proof), "resources": execution.resources,
        "evidence": {**capabilities(), "dependency_version": version("stim"), "seed": execution.program.seed,
                     "shots": execution.program.shots},
        "first_failure": next((c for c in checks if c["status"] == "FAIL"), None),
    }
