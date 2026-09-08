# SPDX-License-Identifier: Apache-2.0
"""Bounded pure two-qubit entanglement-assurance pilot.

The pilot classifies the ideal pre-measurement state produced by E7Q's
state-vector reference backend.  It does not infer entanglement from sampled
counts and does not establish that physical hardware prepared the same state.
"""
from __future__ import annotations

import math
import re

import numpy as np

from .language import E7QError, Program, run


PROFILE = "e7q.entanglement-assurance/pure-two-qubit-v1alpha1"
SCHEMA = "e7q.entanglement-assessment/v1alpha1"
_BOUNDARY = (
    "The verdict concerns the ideal pure two-qubit pre-measurement state "
    "computed by E7Q's state-vector reference backend under the declared "
    "numerical tolerance. It does not infer entanglement from sampled counts, "
    "authenticate a provider, establish physical state preparation, certify "
    "Bell nonlocality, or support a universal-connection claim."
)


def _unsupported(program: Program, tolerance: float, reason: str) -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "profile": PROFILE,
        "status": "UNSUPPORTED",
        "program": {"name": program.name, "qubits": program.qubits},
        "partition": {"left": [0], "right": [1]} if program.qubits == 2 else None,
        "criterion": {
            "name": "pure-state-reduced-density-purity",
            "tolerance": tolerance,
        },
        "reason": reason,
        "boundary": _BOUNDARY,
    }


def _amplitudes(state: np.ndarray) -> list[dict[str, object]]:
    return [
        {
            "basis": f"{index:02b}",
            "real": float(amplitude.real),
            "imag": float(amplitude.imag),
        }
        for index, amplitude in enumerate(state)
    ]


def assess_pure_two_qubit_entanglement(
    program: Program,
    *,
    tolerance: float = 1e-12,
    source_sha256: str | None = None,
) -> dict[str, object]:
    """Classify a supported ideal state as entangled or separable.

    For a pure bipartite state, either reduced density matrix is pure exactly
    when the joint state is separable.  This bounded profile fixes the
    bipartition to ``q[0] | q[1]`` and uses ``1 - Tr(rho_A**2)`` as the
    numerical entanglement gap.
    """
    if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)):
        raise E7QError("entanglement tolerance must be a finite positive number")
    tolerance = float(tolerance)
    if not math.isfinite(tolerance) or tolerance <= 0:
        raise E7QError("entanglement tolerance must be a finite positive number")
    if source_sha256 is not None and not re.fullmatch(r"[0-9a-f]{64}", source_sha256):
        raise E7QError("source SHA-256 must be 64 lowercase hexadecimal characters")
    if program.qubits != 2:
        return _unsupported(
            program, tolerance, "profile supports exactly two qubits"
        )
    if program.backend != "statevector":
        return _unsupported(
            program, tolerance, "profile requires the pure state-vector backend"
        )
    if any(operation.gate == "NOISE" for operation in program.operations):
        return _unsupported(program, tolerance, "profile does not support noise channels")
    if any(
        operation.condition is not None
        or (operation.gate == "MEASURE" and not operation.full_register)
        or operation.gate == "ASSERT"
        for operation in program.operations
    ):
        return _unsupported(
            program,
            tolerance,
            "profile requires a static unitary path with terminal full-register measurement",
        )

    execution = run(program)
    state = np.asarray(execution.state, dtype=complex)
    norm = float(np.vdot(state, state).real)
    if state.shape != (4,) or abs(norm - 1.0) > tolerance:
        return {
            "schema": SCHEMA,
            "profile": PROFILE,
            "status": "UNDETERMINED",
            "program": {"name": program.name, "qubits": program.qubits},
            "partition": {"left": [0], "right": [1]},
            "criterion": {
                "name": "pure-state-reduced-density-purity",
                "tolerance": tolerance,
            },
            "reason": "computed state is not established as a normalized four-amplitude vector",
            "evidence": {"state_norm": norm},
            "boundary": _BOUNDARY,
        }

    coefficient_matrix = state.reshape(2, 2)
    reduced = coefficient_matrix @ coefficient_matrix.conj().T
    purity = float(np.trace(reduced @ reduced).real)
    linear_entropy = max(0.0, 1.0 - purity)
    eigenvalues = np.linalg.eigvalsh(reduced)
    outcome = (
        "ENTANGLED_ESTABLISHED"
        if linear_entropy > tolerance
        else "SEPARABLE_ESTABLISHED"
    )
    source = {"sha256": source_sha256} if source_sha256 is not None else None
    return {
        "schema": SCHEMA,
        "profile": PROFILE,
        "status": outcome,
        "program": {
            "name": program.name,
            "qubits": program.qubits,
            "backend": program.backend,
            "source": source,
        },
        "partition": {"left": [0], "right": [1]},
        "criterion": {
            "name": "pure-state-reduced-density-purity",
            "rule": "entangled when 1 - Tr(rho_left^2) exceeds tolerance",
            "tolerance": tolerance,
        },
        "evidence": {
            "state_representation": "ideal pre-measurement statevector",
            "state_norm": norm,
            "amplitudes": _amplitudes(state),
            "reduced_density_eigenvalues": [float(value) for value in eigenvalues],
            "reduced_density_purity": purity,
            "linear_entropy": linear_entropy,
            "sampled_counts_used": False,
        },
        "projection": {
            "operation": "partial trace over q[1]",
            "preserved": "reduced state of q[0] under partition q[0] | q[1]",
            "hidden_or_lost": [
                "local state of q[1]",
                "full joint-state phase and correlation structure",
            ],
            "source_return": "inspect the recorded joint state amplitudes",
        },
        "claim": {
            "supported": (
                "the ideal E7Q reference state is non-separable under the declared criterion"
                if outcome == "ENTANGLED_ESTABLISHED"
                else "the ideal E7Q reference state is separable within the declared tolerance"
            ),
            "prohibited_inferences": [
                "sampled computational-basis correlation alone proves entanglement",
                "a physical device prepared the assessed ideal state",
                "Bell nonlocality was experimentally demonstrated",
                "all entities or systems are physically interconnected",
            ],
        },
        "proof": [
            {
                "step": 0,
                "kind": "source-state",
                "representation": "ideal pre-measurement statevector",
                "state_norm": norm,
            },
            {
                "step": 1,
                "kind": "project",
                "operator": "partial-trace",
                "traced_qubits": [1],
                "retained_qubits": [0],
            },
            {
                "step": 2,
                "kind": "assess",
                "criterion": "pure-state-reduced-density-purity",
                "reduced_density_purity": purity,
                "linear_entropy": linear_entropy,
                "tolerance": tolerance,
                "outcome": outcome,
            },
        ],
        "boundary": _BOUNDARY,
    }
