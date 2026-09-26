#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Independent exact audit calculations for the bounded qubit proposal.

This script uses Bloch-vector trace identities and standalone Fraction matrix
arithmetic. It imports no E7Q adapter implementation.
"""
from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples/quantum-view/v0alpha1/qubit_xzy_fixture.json"
OUTPUT = ROOT / "examples/quantum-view/v0alpha1/math_audit_calculations.json"


def probabilities(sign: int, a: Fraction) -> dict[str, dict[str, Fraction]]:
    # For rho=(I+r.sigma)/2 and P_(n,o)=(I+o*n.sigma)/2,
    # Tr(rho P_(n,o))=(1+o*r.n)/2; here r=(0, sign*a, 0).
    return {
        axis: {
            "+1": (1 + sign * a if axis == "Y" else Fraction(1)) / 2,
            "-1": (1 - sign * a if axis == "Y" else Fraction(1)) / 2,
        }
        for axis in ("X", "Y", "Z")
    }


def g_effect(x: int, z: int, eta: Fraction) -> tuple[tuple[Fraction, Fraction], tuple[Fraction, Fraction]]:
    return (
        ((1 + z * eta) / 4, x * eta / 4),
        (x * eta / 4, (1 - z * eta) / 4),
    )


def madd(a, b):
    return tuple(tuple(a[i][j] + b[i][j] for j in range(2)) for i in range(2))


def msum(items):
    total = ((Fraction(0), Fraction(0)), (Fraction(0), Fraction(0)))
    for item in items:
        total = madd(total, item)
    return total


def determinant(a):
    return a[0][0] * a[1][1] - a[0][1] * a[1][0]


def sharp_x_projector(x: int):
    return ((Fraction(1, 2), Fraction(x, 2)), (Fraction(x, 2), Fraction(1, 2)))


def sharp_z_projector(z: int):
    return ((Fraction(1 + z, 2), Fraction(0)), (Fraction(0), Fraction(1 - z, 2)))


def trace_product(a, b):
    # Tr(AB)=sum_ij A_ij B_ji; exact for the standalone rational matrices.
    return sum((a[i][j] * b[j][i] for i in range(2) for j in range(2)), Fraction(0))


def main() -> None:
    fixture = json.loads(FIXTURE.read_text())
    a = Fraction(fixture["model"]["a"]["numerator"], fixture["model"]["a"]["denominator"])
    rho_plus, rho_minus = probabilities(1, a), probabilities(-1, a)
    exact_probs = {"rho_plus": rho_plus, "rho_minus": rho_minus}
    for state_id, distributions in exact_probs.items():
        for axis, values in distributions.items():
            assert values["+1"] == Fraction(fixture["expected_exact"][state_id][axis]["+1"])
            assert values["-1"] == Fraction(fixture["expected_exact"][state_id][axis]["-1"])
            assert values["+1"] + values["-1"] == 1

    eta = Fraction(1, 2)
    effects = {(x, z): g_effect(x, z, eta) for x in (1, -1) for z in (1, -1)}
    positivity = {
        f"{x:+d},{z:+d}": {
            "diagonal": [str(g[0][0]), str(g[1][1])],
            "determinant": str(determinant(g)),
        }
        for (x, z), g in effects.items()
    }
    assert all(g[0][0] >= 0 and g[1][1] >= 0 and determinant(g) >= 0 for g in effects.values())
    identity = ((Fraction(1), Fraction(0)), (Fraction(0), Fraction(1)))
    assert msum(effects.values()) == identity
    x_marginals = {
        f"{x:+d}": msum(effects[(x, z)] for z in (1, -1))
        for x in (1, -1)
    }
    z_marginals = {
        f"{z:+d}": msum(effects[(x, z)] for x in (1, -1))
        for z in (1, -1)
    }
    assert x_marginals["+1"] == ((Fraction(1, 2), Fraction(1, 4)), (Fraction(1, 4), Fraction(1, 2)))
    assert x_marginals["-1"] == ((Fraction(1, 2), Fraction(-1, 4)), (Fraction(-1, 4), Fraction(1, 2)))
    assert z_marginals["+1"] == ((Fraction(3, 4), Fraction(0)), (Fraction(0), Fraction(1, 4)))
    assert z_marginals["-1"] == ((Fraction(1, 4), Fraction(0)), (Fraction(0), Fraction(3, 4)))

    # Compute Tr(Px Pz)=|<x_X|z_Z>|^2 directly from independent exact matrices.
    overlaps = {
        f"{x:+d},{z:+d}": trace_product(sharp_x_projector(x), sharp_z_projector(z))
        for x in (1, -1) for z in (1, -1)
    }
    assert all(value == Fraction(1, 2) for value in overlaps.values())

    # Boundary and scope countercases, evaluated from the same analytic laws.
    edge_states = {}
    for edge_a in (Fraction(0), Fraction(1)):
        plus, minus = probabilities(1, edge_a), probabilities(-1, edge_a)
        eigenvalues = ((1 + edge_a) / 2, (1 - edge_a) / 2)
        edge_states[str(edge_a)] = {
            "eigenvalues": [str(v) for v in eigenvalues],
            "plus_equals_minus_state": edge_a == 0,
            "xz_views_equal": all(plus[axis] == minus[axis] for axis in ("X", "Z")),
            "y_views_differ": plus["Y"] != minus["Y"],
        }
    assert edge_states["0"]["plus_equals_minus_state"] and not edge_states["0"]["y_views_differ"]
    assert edge_states["1"]["xz_views_equal"] and edge_states["1"]["y_views_differ"]

    eta_scope = {}
    for q in (Fraction(0), Fraction(1, 2), Fraction(3, 5), Fraction(3, 4), Fraction(1)):
        det = (1 - 2 * q * q) / 16
        eta_scope[str(q)] = {
            "determinant_for_same_parent_formula": str(det),
            "formula_parent_psd": 0 <= q <= 1 and det >= 0,
            "adapter_has_general_witness_claim": q == Fraction(1, 2),
        }

    result = {
        "format": "e7q.quantum-view.math-audit-calculations/v1",
        "method": "exact Fraction Bloch trace identities and independent 2x2 real matrix calculations; no adapter imports",
        "input_fixture": FIXTURE.relative_to(ROOT).as_posix(),
        "density_family_a_1_2": {
            "rho_plus_eigenvalues": ["3/4", "1/4"],
            "rho_minus_eigenvalues": ["3/4", "1/4"],
            "born_probabilities": {
                state: {axis: {outcome: str(prob) for outcome, prob in values.items()} for axis, values in data.items()}
                for state, data in exact_probs.items()
            },
        },
        "sharp_projector_overlap_squared": {key: str(value) for key, value in overlaps.items()},
        "eta_half_parent": {
            "effects_diagonal_and_determinants": positivity,
            "normalization": str(msum(effects.values()) == identity),
            "x_marginals": {key: [[str(v) for v in row] for row in matrix] for key, matrix in x_marginals.items()},
            "z_marginals": {key: [[str(v) for v in row] for row in matrix] for key, matrix in z_marginals.items()},
        },
        "boundary_countercases": edge_states,
        "same_constructive_parent_formula_scope": eta_scope,
        "limits": [
            "the table of state fibres is only over the finite explicitly admitted tuple passed to the API",
            "the overlap arithmetic is checked but the support-intersection lemma is a written mathematical derivation, not a formal proof checked by this script",
            "a failed positive-semidefinite test for one proposed parent never proves that no other parent exists",
            "no physical experiment or product workflow is represented",
        ],
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "PASS", "output": OUTPUT.relative_to(ROOT).as_posix()}))


if __name__ == "__main__":
    main()
