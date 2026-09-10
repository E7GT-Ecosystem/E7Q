# SPDX-License-Identifier: Apache-2.0
"""Bounded dihedral hidden-subgroup phase-state research primitives.

This module is a counterexample-oriented laboratory, not an E7Q-IR semantic
validator and not evidence of a new quantum algorithm or complexity result.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import islice
import math
from typing import Any, Iterable, Mapping

import numpy as np

from ..ir.canonical import digest

MAX_REFERENCE_MODULUS = 64
MAX_MODULI_PER_EVALUATION = 32
MAX_CANDIDATE_ID_LENGTH = 128
MAX_AFFINE_COEFFICIENT = 64
AFFINE_COMBINATION_CRITERION = {
    "id": "e7q.research.dhsp.affine-phase-combination",
    "version": "1",
    "conclusion": "bounded-exhaustive-label-agreement",
}
REFERENCE_RULE = {
    "outcome_0": {"k": 1, "l": 1},
    "outcome_1": {"k": 1, "l": -1},
}


def _integer(name: str, value: Any) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer")
    return value


def _modulus(value: Any) -> int:
    modulus = _integer("modulus", value)
    if not 2 <= modulus <= MAX_REFERENCE_MODULUS:
        raise ValueError(
            f"modulus must be between 2 and {MAX_REFERENCE_MODULUS} inclusive"
        )
    return modulus


def _residue(name: str, value: Any, modulus: int) -> int:
    residue = _integer(name, value)
    if not 0 <= residue < modulus:
        raise ValueError(f"{name} must be in [0, modulus)")
    return residue


def phase_state(modulus: int, label: int, hidden_shift: int) -> np.ndarray:
    """Return (|0> + omega**(label*hidden_shift)|1>)/sqrt(2)."""
    modulus = _modulus(modulus)
    label = _residue("label", label, modulus)
    hidden_shift = _residue("hidden_shift", hidden_shift, modulus)
    phase = np.exp(2j * np.pi * label * hidden_shift / modulus)
    return np.array([1.0, phase], dtype=np.complex128) / math.sqrt(2.0)


@dataclass(frozen=True)
class CombinationResult:
    """One postselected CNOT-combination branch and its declared losses."""

    modulus: int
    hidden_shift: int
    left_label: int
    right_label: int
    measurement_outcome: int
    resulting_label: int
    probability: float
    discarded_global_phase_exponent: int
    state: np.ndarray

    def evidence(self) -> dict[str, Any]:
        record: dict[str, Any] = {
            "format": "e7q.research.dhsp-phase-combination/v1",
            "source": {
                "modulus": self.modulus,
                "hidden_shift": self.hidden_shift,
                "left_label": self.left_label,
                "right_label": self.right_label,
            },
            "transformation": {
                "operation": "cnot-left-control-right-target-then-measure-right",
                "measurement_outcome": self.measurement_outcome,
                "resulting_label": self.resulting_label,
                "branch_probability": {"numerator": 1, "denominator": 2},
                "discarded_global_phase_exponent_mod_n": (
                    self.discarded_global_phase_exponent
                ),
            },
            "preserved": [
                "modulus",
                "hidden-shift-dependent-relative-phase",
            ],
            "lost": [
                "measured-source-qubit",
                "absolute-global-phase",
            ],
            "assumptions": [
                "ideal-phase-states",
                "ideal-cnot-and-computational-basis-measurement",
                "postselection-on-recorded-outcome",
            ],
            "maximum_conclusion": (
                "the recorded branch matches the declared phase-state identity"
            ),
            "nonclaims": [
                "polynomial-time-dhsp-algorithm",
                "physical-implementation-fidelity",
                "quantum-advantage",
            ],
        }
        record["evidence_id"] = digest(record)
        return record


def combine_phase_states(
    modulus: int,
    left_label: int,
    right_label: int,
    hidden_shift: int,
    measurement_outcome: int,
) -> CombinationResult:
    """Combine two phase states using the standard CNOT/measurement identity."""
    modulus = _modulus(modulus)
    left_label = _residue("left_label", left_label, modulus)
    right_label = _residue("right_label", right_label, modulus)
    hidden_shift = _residue("hidden_shift", hidden_shift, modulus)
    outcome = _integer("measurement_outcome", measurement_outcome)
    if outcome not in {0, 1}:
        raise ValueError("measurement_outcome must be 0 or 1")

    joint = np.kron(
        phase_state(modulus, left_label, hidden_shift),
        phase_state(modulus, right_label, hidden_shift),
    )
    cnot = np.array(
        [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]],
        dtype=np.complex128,
    )
    transformed = cnot @ joint
    branch = transformed[[outcome, outcome + 2]]
    probability = float(np.vdot(branch, branch).real)
    if probability <= 0:
        raise ArithmeticError("postselected branch has zero probability")
    state = branch / math.sqrt(probability)
    resulting_label = (
        left_label + right_label if outcome == 0 else left_label - right_label
    ) % modulus
    discarded = 0 if outcome == 0 else (right_label * hidden_shift) % modulus
    return CombinationResult(
        modulus=modulus,
        hidden_shift=hidden_shift,
        left_label=left_label,
        right_label=right_label,
        measurement_outcome=outcome,
        resulting_label=resulting_label,
        probability=probability,
        discarded_global_phase_exponent=discarded,
        state=state,
    )


def _candidate(candidate: Mapping[str, Any]) -> tuple[str, dict[str, dict[str, int]]]:
    if not isinstance(candidate, Mapping):
        raise TypeError("candidate must be a mapping")
    if set(candidate) != {"id", "outcome_0", "outcome_1"}:
        raise ValueError("candidate must contain only id, outcome_0 and outcome_1")
    candidate_id = candidate["id"]
    if (
        not isinstance(candidate_id, str)
        or not candidate_id.strip()
        or len(candidate_id) > MAX_CANDIDATE_ID_LENGTH
    ):
        raise ValueError(
            f"candidate id must be a non-empty string of at most "
            f"{MAX_CANDIDATE_ID_LENGTH} characters"
        )
    rules: dict[str, dict[str, int]] = {}
    for branch in ("outcome_0", "outcome_1"):
        rule = candidate[branch]
        if not isinstance(rule, Mapping) or set(rule) != {"k", "l"}:
            raise ValueError(f"{branch} must contain exactly k and l coefficients")
        coefficients = {
            "k": _integer(f"{branch}.k", rule["k"]),
            "l": _integer(f"{branch}.l", rule["l"]),
        }
        if any(
            abs(value) > MAX_AFFINE_COEFFICIENT
            for value in coefficients.values()
        ):
            raise ValueError(
                f"{branch} coefficients must have absolute value at most "
                f"{MAX_AFFINE_COEFFICIENT}"
            )
        rules[branch] = coefficients
    return candidate_id, rules


def _moduli(values: Iterable[int]) -> tuple[int, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("moduli must be an iterable of integers")
    try:
        result = tuple(islice(iter(values), MAX_MODULI_PER_EVALUATION + 1))
    except TypeError as exc:
        raise TypeError("moduli must be an iterable of integers") from exc
    if not result:
        raise ValueError("at least one modulus is required")
    if len(result) > MAX_MODULI_PER_EVALUATION:
        raise ValueError(
            f"at most {MAX_MODULI_PER_EVALUATION} moduli may be evaluated"
        )
    checked = tuple(_modulus(value) for value in result)
    if len(set(checked)) != len(checked):
        raise ValueError("moduli must not contain duplicates")
    return checked


def evaluate_affine_candidate(
    candidate: Mapping[str, Any], *, moduli: Iterable[int]
) -> dict[str, Any]:
    """Exhaustively compare a restricted affine label rule on bounded moduli.

    PASS means no disagreement in the enumerated label domain only. It is not an
    asymptotic result, a proof of DHSP correctness, or evidence of efficiency.
    """
    candidate_id, rules = _candidate(candidate)
    checked_moduli = _moduli(moduli)
    comparisons = 0
    counterexample = None
    for modulus in checked_moduli:
        for left_label in range(modulus):
            for right_label in range(modulus):
                for outcome in (0, 1):
                    branch = f"outcome_{outcome}"
                    rule = rules[branch]
                    observed = (
                        rule["k"] * left_label + rule["l"] * right_label
                    ) % modulus
                    expected = (
                        left_label + right_label
                        if outcome == 0
                        else left_label - right_label
                    ) % modulus
                    comparisons += 1
                    if observed != expected:
                        counterexample = {
                            "modulus": modulus,
                            "hidden_shift_witness": 1,
                            "left_label": left_label,
                            "right_label": right_label,
                            "measurement_outcome": outcome,
                            "expected_label": expected,
                            "candidate_label": observed,
                        }
                        break
                if counterexample:
                    break
            if counterexample:
                break
        if counterexample:
            break
    status = "PASS" if counterexample is None else "FAIL"
    conclusion = (
        "NO_COUNTEREXAMPLE_IN_ENUMERATED_DOMAIN"
        if counterexample is None
        else "COUNTEREXAMPLE_FOUND"
    )
    result: dict[str, Any] = {
        "format": "e7q.research.dhsp-affine-candidate-assessment/v1",
        "criterion": AFFINE_COMBINATION_CRITERION,
        "candidate": {
            "id": candidate_id,
            "rules": rules,
        },
        "domain": {
            "moduli": list(checked_moduli),
            "label_domain_requested": "all-pairs",
            "measurement_outcomes": [0, 1],
            "comparisons_performed": comparisons,
            "enumeration_complete": counterexample is None,
        },
        "outcome": {
            "status": status,
            "conclusion": conclusion,
            "counterexample": counterexample,
            "universal_correctness_established": False,
            "polynomial_time_established": False,
        },
        "preserved": [
            "candidate-rules",
            "tested-domain",
            "first-counterexample-when-found",
        ],
        "lost": ["claims-outside-enumerated-moduli", "implementation-cost-model"],
        "assumptions": [
            "ideal-dihedral-phase-state-label-semantics",
            "affine-rule-restriction",
        ],
        "maximum_conclusion": (
            "bounded affine-rule agreement or a concrete bounded counterexample"
        ),
    }
    result["assessment_id"] = digest(result)
    return result
