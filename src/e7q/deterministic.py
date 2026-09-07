# SPDX-License-Identifier: Apache-2.0
"""Assessment of noisy observations against deterministic bit expectations."""
from __future__ import annotations

import json
from pathlib import Path
from statistics import NormalDist
from typing import Any

from .language import E7QError
from .openqasm2 import COUNT_ORDERS, canonicalize_outcome


REFERENCE_SCHEMA = "e7q.deterministic-reference/v1alpha1"
ASSESSMENT_SCHEMA = "e7q.deterministic-assessment/v1alpha1"


def _load_object(path: str | Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise E7QError(f"invalid {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise E7QError(f"{label} must be a JSON object")
    return value


def load_external_receipt(path: str | Path) -> dict[str, Any]:
    value = _load_object(path, "external evidence receipt")
    if value.get("schema") != "e7q.external-evidence-receipt/v1alpha1":
        raise E7QError("external receipt must use e7q.external-evidence-receipt/v1alpha1")
    return value


def load_deterministic_reference(path: str | Path) -> dict[str, Any]:
    value = _load_object(path, "deterministic reference")
    if value.get("schema") != REFERENCE_SCHEMA:
        raise E7QError(f"deterministic reference must use {REFERENCE_SCHEMA}")
    return value


def _wilson(successes: int, shots: int, confidence: float) -> tuple[float, float]:
    z = NormalDist().inv_cdf(0.5 + confidence / 2)
    observed = successes / shots
    denominator = 1 + z * z / shots
    center = (observed + z * z / (2 * shots)) / denominator
    radius = z * (
        (observed * (1 - observed) / shots + z * z / (4 * shots * shots)) ** 0.5
    ) / denominator
    return max(0.0, center - radius), min(1.0, center + radius)


def _metric(
    counts: dict[str, int],
    predicate: Any,
    *,
    minimum: float,
    confidence: float,
) -> dict[str, object]:
    shots = sum(counts.values())
    successes = sum(count for outcome, count in counts.items() if predicate(outcome))
    low, high = _wilson(successes, shots, confidence)
    return {
        "successes": successes,
        "shots": shots,
        "observed_probability": successes / shots,
        "confidence_level": confidence,
        "wilson_interval": [low, high],
        "minimum_probability": minimum,
        "status": "PASS" if low >= minimum else "FAIL",
    }


def assess_deterministic_reference(
    receipt: dict[str, Any], reference: dict[str, Any]
) -> dict[str, object]:
    """Assess embedded external counts under an explicit bit-order convention."""
    if receipt.get("schema") != "e7q.external-evidence-receipt/v1alpha1":
        raise E7QError("invalid external evidence receipt schema")
    if receipt.get("status") != "PASS":
        raise E7QError("external evidence receipt must pass before assessment")
    if reference.get("schema") != REFERENCE_SCHEMA:
        raise E7QError("invalid deterministic reference schema")
    bit_names = reference.get("canonical_bit_order")
    if (
        not isinstance(bit_names, list)
        or not bit_names
        or not all(isinstance(item, str) and item for item in bit_names)
        or len(bit_names) != len(set(bit_names))
    ):
        raise E7QError("canonical_bit_order must contain unique bit names")
    width = len(bit_names)
    observed_order = reference.get("observed_label_order")
    if not isinstance(observed_order, str) or observed_order not in COUNT_ORDERS:
        raise E7QError("deterministic reference has invalid observed_label_order")
    primary_indices = reference.get("primary_bit_indices")
    if (
        not isinstance(primary_indices, list)
        or not primary_indices
        or not all(
            isinstance(item, int) and not isinstance(item, bool) and 0 <= item < width
            for item in primary_indices
        )
        or len(primary_indices) != len(set(primary_indices))
    ):
        raise E7QError("primary_bit_indices must be unique in-range integers")
    minimum = reference.get("minimum_success_probability")
    confidence = reference.get("confidence_level")
    if not isinstance(minimum, (int, float)) or isinstance(minimum, bool) or not 0 < minimum < 1:
        raise E7QError("minimum_success_probability must be between zero and one")
    if (
        not isinstance(confidence, (int, float))
        or isinstance(confidence, bool)
        or not 0 < confidence < 1
    ):
        raise E7QError("confidence_level must be between zero and one")
    minimum, confidence = float(minimum), float(confidence)
    threshold_provenance = reference.get("threshold_provenance")
    if not isinstance(threshold_provenance, str) or not threshold_provenance:
        raise E7QError("deterministic reference must declare threshold_provenance")

    supplied = receipt.get("circuits")
    if not isinstance(supplied, list):
        raise E7QError("external receipt must contain circuits")
    by_name: dict[str, dict[str, Any]] = {}
    for circuit in supplied:
        if not isinstance(circuit, dict) or not isinstance(circuit.get("circuit_name"), str):
            raise E7QError("external receipt contains an invalid circuit record")
        name = circuit["circuit_name"]
        if name in by_name:
            raise E7QError(f"external receipt has duplicate circuit name: {name}")
        by_name[name] = circuit

    cases_value = reference.get("cases")
    if not isinstance(cases_value, list) or not cases_value:
        raise E7QError("deterministic reference must contain cases")
    cases: list[dict[str, object]] = []
    modal_primary: dict[str, str] = {}
    seen: set[str] = set()
    for declared in cases_value:
        if not isinstance(declared, dict):
            raise E7QError("deterministic reference case must be an object")
        name = declared.get("circuit_name")
        expected = declared.get("expected_outcome")
        if not isinstance(name, str) or not name or name in seen:
            raise E7QError("deterministic reference circuit names must be unique")
        seen.add(name)
        if (
            not isinstance(expected, str)
            or len(expected) != width
            or set(expected) - {"0", "1"}
        ):
            raise E7QError(f"invalid expected outcome for {name}")
        if name not in by_name:
            raise E7QError(f"external receipt is missing circuit: {name}")
        count_summary = by_name[name].get("counts")
        values = count_summary.get("values") if isinstance(count_summary, dict) else None
        if not isinstance(values, dict) or not values:
            raise E7QError(
                "external receipt must embed counts; rerun verification with --include-counts"
            )
        receipt_order = count_summary.get("label_order")
        if receipt_order is not None:
            if not isinstance(receipt_order, str) or receipt_order not in COUNT_ORDERS:
                raise E7QError(f"invalid receipt label order for {name}")
            if receipt_order != observed_order:
                raise E7QError(f"receipt label order conflicts with reference for {name}")
        # Missing/unknown legacy ordering remains an explicit reference assumption.
        normalized: dict[str, int] = {}
        for raw_outcome, raw_count in values.items():
            if (
                not isinstance(raw_outcome, str)
                or len(raw_outcome) != width
                or set(raw_outcome) - {"0", "1"}
                or not isinstance(raw_count, int)
                or isinstance(raw_count, bool)
                or raw_count < 0
            ):
                raise E7QError(f"invalid embedded counts for {name}")
            outcome = canonicalize_outcome(raw_outcome, order=str(observed_order))
            normalized[outcome] = normalized.get(outcome, 0) + raw_count
        shots = sum(normalized.values())
        if shots < 1 or count_summary.get("shots") != shots:
            raise E7QError(f"embedded counts do not match declared shots for {name}")
        expected_primary = "".join(expected[index] for index in primary_indices)
        primary = _metric(
            normalized,
            lambda outcome, expected_primary=expected_primary: "".join(
                outcome[index] for index in primary_indices
            ) == expected_primary,
            minimum=minimum,
            confidence=confidence,
        )
        full = _metric(
            normalized,
            lambda outcome, expected=expected: outcome == expected,
            minimum=minimum,
            confidence=confidence,
        )
        primary["role"] = "primary"
        full["role"] = "descriptive"
        primary_counts: dict[str, int] = {}
        for outcome, count in normalized.items():
            projected = "".join(outcome[index] for index in primary_indices)
            primary_counts[projected] = primary_counts.get(projected, 0) + count
        mode = min(
            (key for key, value in primary_counts.items() if value == max(primary_counts.values()))
        )
        modal_primary[name] = mode
        cases.append(
            {
                "circuit_name": name,
                "expected_outcome": expected,
                "expected_primary": expected_primary,
                "observed_modal_primary": mode,
                "primary": primary,
                "full_outcome": full,
                "status": primary["status"],
            }
        )

    relations: list[dict[str, object]] = []
    for relation in reference.get("relations", []):
        if not isinstance(relation, dict):
            raise E7QError("deterministic relation must be an object")
        kind = relation.get("kind")
        if kind == "xor":
            left, right, product = (
                relation.get("left"), relation.get("right"), relation.get("product")
            )
            if not all(
                isinstance(item, str) and item in modal_primary
                for item in (left, right, product)
            ):
                raise E7QError("xor relation references an unknown case")
            observed_xor = "".join(
                str(int(a) ^ int(b))
                for a, b in zip(modal_primary[left], modal_primary[right])
            )
            passed = observed_xor == modal_primary[product]
            relations.append(
                {
                    "kind": "xor",
                    "left": left,
                    "right": right,
                    "product": product,
                    "observed": {
                        "left": modal_primary[left],
                        "right": modal_primary[right],
                        "left_xor_right": observed_xor,
                        "product": modal_primary[product],
                    },
                    "status": "PASS" if passed else "FAIL",
                }
            )
        elif kind == "equal":
            names = relation.get("cases")
            expected_value = relation.get("expected")
            if (
                not isinstance(names, list)
                or not names
                or not all(isinstance(item, str) and item in modal_primary for item in names)
                or not isinstance(expected_value, str)
            ):
                raise E7QError("equal relation is invalid")
            observed = {name: modal_primary[name] for name in names}
            passed = all(value == expected_value for value in observed.values())
            relations.append(
                {
                    "kind": "equal",
                    "cases": names,
                    "expected": expected_value,
                    "observed": observed,
                    "status": "PASS" if passed else "FAIL",
                }
            )
        else:
            raise E7QError(f"unsupported deterministic relation: {kind}")

    status = "PASS" if all(case["status"] == "PASS" for case in cases) and all(
        relation["status"] == "PASS" for relation in relations
    ) else "FAIL"
    claim_mode = reference.get("claim_mode")
    if claim_mode not in {"exploratory", "prospective"}:
        raise E7QError("deterministic reference claim_mode must be exploratory or prospective")
    return {
        "schema": ASSESSMENT_SCHEMA,
        "status": status,
        "claim_mode": claim_mode,
        "receipt_source": receipt.get("source"),
        "reference": {
            "profile": reference.get("name"),
            "canonical_bit_order": bit_names,
            "observed_label_order": observed_order,
            "primary_bit_indices": primary_indices,
            "minimum_success_probability": minimum,
            "confidence_level": confidence,
            "threshold_provenance": threshold_provenance,
        },
        "cases": cases,
        "relations": relations,
        "judgments": {
            "declared_deterministic_expectation": status,
            "provider_authentication": "NOT_EVALUATED",
            "physical_fidelity": "NOT_EVALUATED",
            "fault_tolerance": "NOT_EVALUATED",
        },
        "limitations": [
            "Counts are normalized only under the declared single-register bit order.",
            (
                "PASS means the Wilson lower confidence bound clears the declared "
                "primary-bit success threshold for every case."
            ),
            (
                "Relations compare aggregate modal outcomes from separate circuits, "
                "not paired shot-level error products."
            ),
            (
                "The assessment does not authenticate the provider or establish "
                "physical fidelity, fault tolerance, causation, or novelty."
            ),
        ],
        "proof": [
            {
                "step": 0,
                "kind": "bit-order-normalization",
                "from": observed_order,
                "to": "clbit-ascending",
            },
            {
                "step": 1,
                "kind": "deterministic-reference-assessment",
                "cases": len(cases),
                "status": status,
                "claim_mode": claim_mode,
            },
            {
                "step": 2,
                "kind": "evidence-boundary",
                "boundary": (
                    "Finite-sample alignment with a declared deterministic-bit reference "
                    "under an explicit count-label convention; not provider authentication, "
                    "hardware certification, physical fidelity, fault tolerance, or proof of "
                    "the underlying mathematical theorem."
                ),
            },
        ],
    }
