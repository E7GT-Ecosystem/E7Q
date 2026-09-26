#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Independent conventional NumPy calculation for the qubit view fixture.

This script intentionally imports no E7Q quantum-view adapter code. Its role is
an independently written finite numerical cross-check, not a proof or physics
claim. It regenerates the committed `independent_numpy_result.json` with
`python scripts/quantum_view_numpy_check.py`.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples/quantum-view/v0alpha1/qubit_xzy_fixture.json"
OUTPUT = ROOT / "examples/quantum-view/v0alpha1/independent_numpy_result.json"

def fraction(obj):
    from fractions import Fraction
    return Fraction(obj["numerator"], obj["denominator"])


def main() -> int:
    fixture = json.loads(FIXTURE.read_text())
    a = float(fraction(fixture["model"]["a"]))
    identity = np.eye(2, dtype=np.complex128)
    pauli = {
        "X": np.array([[0, 1], [1, 0]], dtype=np.complex128),
        "Y": np.array([[0, -1j], [1j, 0]], dtype=np.complex128),
        "Z": np.array([[1, 0], [0, -1]], dtype=np.complex128),
    }
    states = {
        "rho_plus": (identity + a * pauli["Y"]) / 2,
        "rho_minus": (identity - a * pauli["Y"]) / 2,
    }
    observed = {}
    max_probability_error = 0.0
    for state_name, rho in states.items():
        observed[state_name] = {}
        for axis in ("X", "Y", "Z"):
            probabilities = {}
            for outcome in (1, -1):
                effect = (identity + outcome * pauli[axis]) / 2
                probabilities[f"{outcome:+d}"] = float(np.trace(rho @ effect).real)
            observed[state_name][axis] = probabilities
            expected = fixture["expected_exact"][state_name][axis]
            for key, value in probabilities.items():
                from fractions import Fraction
                target = float(Fraction(expected[key]))
                max_probability_error = max(max_probability_error, abs(value - target))
                assert abs(value - target) <= 1e-12
            assert abs(sum(probabilities.values()) - 1.0) <= 1e-12

    eta = 0.5
    parent = {}
    parent_effects = {}
    for x in (1, -1):
        for z in (1, -1):
            effect = (identity + x * eta * pauli["X"] + z * eta * pauli["Z"]) / 4
            parent_effects[(x, z)] = effect
            parent[f"{x:+d},{z:+d}"] = {
                "minimum_eigenvalue": float(np.linalg.eigvalsh(effect).min()),
                "trace": float(np.trace(effect).real),
            }
    total = sum(parent_effects.values(), np.zeros((2, 2), dtype=np.complex128))
    assert np.allclose(total, identity, atol=1e-12)
    x_marginals_ok = True
    z_marginals_ok = True
    for x in (1, -1):
        marginal = sum((parent_effects[(x, z)] for z in (1, -1)), np.zeros((2, 2), dtype=np.complex128))
        expected = (identity + x * eta * pauli["X"]) / 2
        x_marginals_ok &= bool(np.allclose(marginal, expected, atol=1e-12))
    for z in (1, -1):
        marginal = sum((parent_effects[(x, z)] for x in (1, -1)), np.zeros((2, 2), dtype=np.complex128))
        expected = (identity + z * eta * pauli["Z"]) / 2
        z_marginals_ok &= bool(np.allclose(marginal, expected, atol=1e-12))
    assert x_marginals_ok and z_marginals_ok
    assert all(item["minimum_eigenvalue"] >= -1e-12 for item in parent.values())

    overlaps = {}
    for x in (1, -1):
        px = (identity + x * pauli["X"]) / 2
        for z in (1, -1):
            pz = (identity + z * pauli["Z"]) / 2
            overlaps[f"{x:+d},{z:+d}"] = float(np.trace(px @ pz).real)
            assert abs(overlaps[f"{x:+d},{z:+d}"] - 0.5) <= 1e-12

    result = {
        "format": "e7q.quantum-view.independent-numpy-check/v1",
        "method": "direct 2x2 NumPy matrices and trace/eigenspectrum calculations; no adapter imports",
        "fixture": FIXTURE.relative_to(ROOT).as_posix(),
        "probabilities": observed,
        "sharp_xz_rank_one_projector_overlap_squared": overlaps,
        "unsharp_eta": "1/2",
        "unsharp_parent_effects": parent,
        "unsharp_parent_normalizes": True,
        "unsharp_x_marginals_verified": x_marginals_ok,
        "unsharp_z_marginals_verified": z_marginals_ok,
        "max_probability_error_vs_exact_fixture": round(max_probability_error, 15),
        "scope_note": "independent finite numerical reproduction only; not a universal proof, physical run, product comparison, or new-physics claim",
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "PASS", "output": OUTPUT.relative_to(ROOT).as_posix(), "max_probability_error": result["max_probability_error_vs_exact_fixture"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
