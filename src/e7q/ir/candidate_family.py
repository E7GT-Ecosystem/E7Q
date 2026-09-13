# SPDX-License-Identifier: Apache-2.0
"""Finite, dependence-aware candidate families for E7Q-IR.

This module implements the bounded Q-A1 contract.  Alternatives within one
factor are correlated; factors are combined only where the caller explicitly
declares independence by placing them in separate factors.  The contract does
not infer quantum semantics, feasibility, optimality, or statistical meaning.
"""
from __future__ import annotations

from itertools import islice, product
import re
from typing import Any, Iterable

from .canonical import digest, identified_digest


SCHEMA = "e7q.ir.candidate-family/v0alpha1"
RESTRICTION_SCHEMA = "e7q.ir.candidate-restriction/v0alpha2"
VIEW_SCHEMA = "e7q.ir.candidate-family-view/v0alpha2"
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,127}$")
MAX_FACTORS = 32
MAX_DIMENSIONS_PER_FACTOR = 32
MAX_ALTERNATIVES_PER_FACTOR = 256
MAX_MEMBERS = 65_536
MAX_METADATA_ITEMS = 128
MAX_CRITERION_TEXT = 1_024


class CandidateFamilyError(ValueError):
    """The requested family is invalid or exceeds the bounded profile."""


def _bounded_tuple(values: Iterable[Any], limit: int, label: str) -> tuple[Any, ...]:
    if isinstance(values, (str, bytes)):
        raise CandidateFamilyError(f"{label} must be a collection")
    try:
        result = tuple(islice(values, limit + 1))
    except TypeError as exc:
        raise CandidateFamilyError(f"{label} must be a collection") from exc
    if len(result) > limit:
        raise CandidateFamilyError(f"{label} exceeds the supported bound")
    return result


def _names(values: Iterable[str], label: str) -> tuple[str, ...]:
    result = _bounded_tuple(values, MAX_DIMENSIONS_PER_FACTOR, label)
    if not result or any(not isinstance(item, str) or not _NAME.fullmatch(item) for item in result):
        raise CandidateFamilyError(f"{label} must contain valid non-empty names")
    if len(set(result)) != len(result):
        raise CandidateFamilyError(f"{label} must not contain duplicates")
    return result


def _strings(values: Iterable[str], label: str) -> tuple[str, ...]:
    result = _bounded_tuple(values, MAX_METADATA_ITEMS, label)
    if any(not isinstance(item, str) or not item for item in result):
        raise CandidateFamilyError(f"{label} must contain non-empty strings")
    if len(set(result)) != len(result):
        raise CandidateFamilyError(f"{label} must not contain duplicates")
    return result


def factor(name: str, dimensions: Iterable[str], alternatives: Iterable[dict[str, str]]) -> dict[str, Any]:
    """Build one correlated choice factor.

    Every alternative must bind every dimension exactly once.  Values are
    inert identifiers; no probability or amplitude interpretation is allowed.
    """
    if not isinstance(name, str) or not _NAME.fullmatch(name):
        raise CandidateFamilyError("factor name is invalid")
    dims = _names(dimensions, "factor dimensions")
    raw = _bounded_tuple(alternatives, MAX_ALTERNATIVES_PER_FACTOR, "factor alternatives")
    if not raw:
        raise CandidateFamilyError("factor alternative count is outside the supported bound")
    normalised: list[dict[str, Any]] = []
    seen: set[tuple[tuple[str, str], ...]] = set()
    for bindings in raw:
        if not isinstance(bindings, dict) or set(bindings) != set(dims):
            raise CandidateFamilyError("each alternative must bind exactly the factor dimensions")
        if any(not isinstance(value, str) or not value for value in bindings.values()):
            raise CandidateFamilyError("alternative values must be non-empty strings")
        ordered = {dimension: bindings[dimension] for dimension in sorted(dims)}
        key = tuple(ordered.items())
        if key in seen:
            raise CandidateFamilyError("factor alternatives must be distinct")
        seen.add(key)
        item: dict[str, Any] = {"bindings": ordered}
        item["alternative_id"] = digest(item)
        normalised.append(item)
    normalised.sort(key=lambda item: item["alternative_id"])
    value: dict[str, Any] = {
        "name": name,
        "dimensions": sorted(dims),
        "combination_rule": "correlated-alternatives",
        "alternatives": normalised,
    }
    value["factor_id"] = digest(value)
    return value


def build_candidate_family(
    source_id: str,
    factors: Iterable[dict[str, Any]],
    *,
    assumptions: Iterable[str] = (),
    limitations: Iterable[str] = (),
) -> dict[str, Any]:
    """Build an explicitly finite family from independent factors.

    Cartesian expansion occurs *only* between the supplied factors.  A caller
    represents dependent choices as alternatives in the same factor.
    """
    if not isinstance(source_id, str) or not _DIGEST.fullmatch(source_id):
        raise CandidateFamilyError("source_id must be a SHA-256 identity")
    items = _bounded_tuple(factors, MAX_FACTORS, "factors")
    if not items:
        raise CandidateFamilyError("factor count is outside the supported bound")
    names: set[str] = set()
    dimensions: set[str] = set()
    size = 1
    for item in items:
        _validate_factor(item)
        if item["name"] in names:
            raise CandidateFamilyError("factor names must be distinct")
        names.add(item["name"])
        overlap = dimensions.intersection(item["dimensions"])
        if overlap:
            raise CandidateFamilyError("dimensions may belong to only one factor")
        dimensions.update(item["dimensions"])
        size *= len(item["alternatives"])
        if size > MAX_MEMBERS:
            raise CandidateFamilyError("candidate family exceeds the supported member bound")

    ordered_factors = sorted(items, key=lambda item: item["factor_id"])
    members: list[dict[str, Any]] = []
    for choices in product(*(item["alternatives"] for item in ordered_factors)):
        bindings: dict[str, str] = {}
        alternative_refs: list[str] = []
        for choice in choices:
            bindings.update(choice["bindings"])
            alternative_refs.append(choice["alternative_id"])
        member: dict[str, Any] = {
            "source_id": source_id,
            "bindings": {key: bindings[key] for key in sorted(bindings)},
            "alternative_refs": sorted(alternative_refs),
        }
        member["member_id"] = digest(member)
        members.append(member)
    members.sort(key=lambda item: item["member_id"])
    value: dict[str, Any] = {
        "schema": SCHEMA,
        "source_id": source_id,
        "combination_rule": "explicit-independent-factors",
        "factors": ordered_factors,
        "members": members,
        "assumptions": sorted(_strings(assumptions, "assumptions")),
        "limitations": sorted(_strings(limitations, "limitations")),
    }
    value["family_id"] = digest(value)
    return value


def validate_candidate_family(value: dict[str, Any]) -> None:
    """Fail closed when a family is malformed or its identity is stale."""
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        raise CandidateFamilyError("unsupported candidate-family schema")
    expected = build_candidate_family(
        value.get("source_id"),
        value.get("factors", ()),
        assumptions=value.get("assumptions", ()),
        limitations=value.get("limitations", ()),
    )
    if value != expected:
        raise CandidateFamilyError("candidate family is non-canonical or has a stale identity")


def restrict_candidate_family(
    family: dict[str, Any], retained_member_ids: Iterable[str], *, criterion: str
) -> dict[str, Any]:
    """Record an explicit restriction without presenting it as a view."""
    validate_candidate_family(family)
    if not isinstance(criterion, str) or not criterion:
        raise CandidateFamilyError("restriction criterion must be non-empty")
    retained = set(retained_member_ids)
    known = {item["member_id"] for item in family["members"]}
    if not retained or not retained.issubset(known):
        raise CandidateFamilyError("restriction must retain known family members")
    result: dict[str, Any] = {
        "schema": "e7q.ir.candidate-restriction/v0alpha1",
        "operation": "restrict",
        "source_family_id": family["family_id"],
        "criterion": criterion,
        "retained_member_ids": sorted(retained),
        "excluded_member_ids": sorted(known - retained),
        "limitations": [
            "Restriction records exclusion; it is not a source-preserving view.",
            "No feasibility, optimality, or quantum-semantic conclusion is established.",
        ],
    }
    result["restriction_id"] = digest(result)
    return result


def candidate_family_view(family: dict[str, Any]) -> dict[str, Any]:
    """Return a source-linked inventory view with no pruning or identification."""
    validate_candidate_family(family)
    value: dict[str, Any] = {
        "schema": "e7q.ir.candidate-family-view/v0alpha1",
        "operation": "view",
        "source_family_id": family["family_id"],
        "factor_count": len(family["factors"]),
        "member_count": len(family["members"]),
        "dimensions": sorted(
            dimension for item in family["factors"] for dimension in item["dimensions"]
        ),
        "member_ids": [item["member_id"] for item in family["members"]],
        "limitations": ["This inventory view does not select, identify, or restrict candidates."],
    }
    value["view_id"] = digest(value)
    return value


def assess_candidate_restriction(
    family: dict[str, Any],
    retained_member_ids: Iterable[str],
    *,
    criterion_id: str,
    criterion_edition: str,
    criterion_text: str,
) -> dict[str, Any]:
    """Assess a bounded restriction and retain non-success as typed evidence.

    This additive v0alpha2 operation does not change the v0alpha1 family or
    restriction identities.  In particular, an empty result is not invalid
    input and a resource refusal is not collapsed into either state.
    """
    source_family_id = family.get("family_id") if isinstance(family, dict) else None
    criterion: dict[str, str] | None = None
    outcome = "success"
    message = "Restriction retained a non-empty subset of the source family."
    retained: list[str] = []
    excluded: list[str] = []
    result_family: dict[str, Any] | None = None
    try:
        validate_candidate_family(family)
        if not isinstance(criterion_id, str) or not _NAME.fullmatch(criterion_id):
            raise CandidateFamilyError("restriction criterion id is invalid")
        if (
            not isinstance(criterion_edition, str)
            or not criterion_edition
            or len(criterion_edition.encode("utf-8")) > MAX_CRITERION_TEXT
        ):
            raise CandidateFamilyError("restriction criterion edition is invalid or too large")
        if (
            not isinstance(criterion_text, str)
            or not criterion_text
            or len(criterion_text.encode("utf-8")) > MAX_CRITERION_TEXT
        ):
            raise CandidateFamilyError("restriction criterion text is invalid or too large")
        criterion = {
            "id": criterion_id,
            "edition": criterion_edition,
            "text": criterion_text,
        }
        raw = _bounded_tuple(retained_member_ids, MAX_MEMBERS, "retained_member_ids")
        if any(not isinstance(item, str) or not _DIGEST.fullmatch(item) for item in raw):
            raise CandidateFamilyError("retained_member_ids must contain SHA-256 identities")
        if len(set(raw)) != len(raw):
            raise CandidateFamilyError("retained_member_ids must not contain duplicates")
        known = {item["member_id"] for item in family["members"]}
        if not set(raw).issubset(known):
            raise CandidateFamilyError("retained_member_ids contain unknown members")
        retained = sorted(raw)
        excluded = sorted(known - set(retained))
        if not retained:
            outcome = "empty"
            message = "The valid bounded criterion retained no source-family members."
        else:
            result_family = {
                "schema": "e7q.ir.candidate-family-subset/v0alpha1",
                "source_family_id": family["family_id"],
                "member_ids": retained,
            }
            result_family["family_id"] = digest(result_family)
    except CandidateFamilyError as exc:
        if "exceeds the supported bound" in str(exc):
            outcome = "resource_limit"
        else:
            outcome = "invalid_input"
        message = str(exc)

    value: dict[str, Any] = {
        "schema": RESTRICTION_SCHEMA,
        "operation": "restrict",
        "source_family_id": source_family_id if isinstance(source_family_id, str) else None,
        "criterion": criterion,
        "outcome": outcome,
        "retained_member_ids": retained,
        "excluded_member_ids": excluded,
        "result_family": result_family,
        "source_return": {
            "required": True,
            "source_family_id": source_family_id if isinstance(source_family_id, str) else None,
        },
        "message": message,
        "limitations": [
            "Restriction records exclusion; it is not a source-preserving view.",
            "No feasibility, optimality, or quantum-semantic conclusion is established.",
        ],
    }
    value["restriction_id"] = digest(value)
    return value


def candidate_family_view_v2(family: dict[str, Any]) -> dict[str, Any]:
    """Return a source-linked inventory with explicit preservation and loss."""
    validate_candidate_family(family)
    value: dict[str, Any] = {
        "schema": VIEW_SCHEMA,
        "operation": "view",
        "source_family_id": family["family_id"],
        "factor_count": len(family["factors"]),
        "member_count": len(family["members"]),
        "dimensions": sorted(
            dimension for item in family["factors"] for dimension in item["dimensions"]
        ),
        "member_ids": [item["member_id"] for item in family["members"]],
        "preserves": [
            "factor and member inventory",
            "member identities",
            "source-family linkage",
        ],
        "loses": [
            "alternative bindings",
            "assumption and limitation text",
            "factor correlation structure beyond the listed inventory",
        ],
        "source_return": {
            "required": True,
            "source_family_id": family["family_id"],
        },
        "limitations": ["This inventory view does not select, identify, or restrict candidates."],
    }
    value["view_id"] = digest(value)
    return value


def _validate_factor(value: dict[str, Any]) -> None:
    if not isinstance(value, dict):
        raise CandidateFamilyError("factor must be an object")
    expected = factor(value.get("name"), value.get("dimensions", ()), [
        item.get("bindings", {}) if isinstance(item, dict) else {}
        for item in value.get("alternatives", ())
    ])
    if value != expected:
        raise CandidateFamilyError("factor is non-canonical or has a stale identity")
