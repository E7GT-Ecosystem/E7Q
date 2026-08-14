#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Dependency-free oracle for the committed QEC syndrome pilot fixture."""
from __future__ import annotations

import json
from pathlib import Path


ANTICOMMUTING = {
    frozenset(("X", "Y")),
    frozenset(("X", "Z")),
    frozenset(("Y", "Z")),
}


def commutation_bit(left: str, right: str) -> int:
    return sum(
        frozenset((a, b)) in ANTICOMMUTING
        for a, b in zip(left, right)
        if a != "I" and b != "I"
    ) % 2


def main() -> int:
    fixture = Path(__file__).with_name("expected_results.json")
    data = json.loads(fixture.read_text())
    generators = data["code"]["generators"]
    failures = []
    for case in data["cases"]:
        observed = [commutation_bit(item, case["error"]) for item in generators]
        if observed != case["syndrome"]:
            failures.append(
                f"{case['error']}: expected {case['syndrome']}, observed {observed}"
            )
    claim = data["homomorphism_case"]
    expected_xor = [
        left ^ right
        for left, right in zip(claim["left_syndrome"], claim["right_syndrome"])
    ]
    if expected_xor != claim["product_syndrome"]:
        failures.append("homomorphism fixture does not add modulo 2")
    if failures:
        print("FAIL")
        print("\n".join(failures))
        return 1
    print("PASS: 6 syndromes and 1 homomorphism case independently checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
