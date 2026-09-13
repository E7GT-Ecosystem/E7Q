# SPDX-License-Identifier: Apache-2.0
"""Ordered, domain-explicit transformation histories for E7Q-IR candidate families."""
from __future__ import annotations

from itertools import islice
import re
from typing import Any, Iterable

from .canonical import digest


SCHEMA = "e7q.ir.transformation-history/v0alpha1"
STEP_SCHEMA = "e7q.ir.transformation-step/v0alpha1"
OUTCOMES = frozenset({"success", "empty", "invalid_input", "domain_error", "unsupported", "resource_limit"})
KINDS = frozenset({"transform", "identify", "restrict"})
MAX_STEPS = 256
MAX_MEMBERS = 65_536
MAX_DECLARATIONS = 128
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_.:/-]{0,255}$")


class TransformationHistoryError(ValueError):
    """The requested history is invalid or outside the bounded contract."""


def _items(values: Iterable[Any], limit: int, label: str) -> tuple[Any, ...]:
    if isinstance(values, (str, bytes)):
        raise TransformationHistoryError(f"{label} must be a collection")
    try:
        result = tuple(islice(values, limit + 1))
    except TypeError as exc:
        raise TransformationHistoryError(f"{label} must be a collection") from exc
    if len(result) > limit:
        raise TransformationHistoryError(f"{label} exceeds the supported bound")
    return result


def _digests(values: Iterable[str], label: str, *, allow_empty: bool = False) -> list[str]:
    result = _items(values, MAX_MEMBERS, label)
    if not allow_empty and not result:
        raise TransformationHistoryError(f"{label} must not be empty")
    if any(not isinstance(value, str) or not _DIGEST.fullmatch(value) for value in result):
        raise TransformationHistoryError(f"{label} must contain SHA-256 identities")
    if len(set(result)) != len(result):
        raise TransformationHistoryError(f"{label} must not contain duplicates")
    return sorted(result)


def _strings(values: Iterable[str], label: str) -> list[str]:
    result = _items(values, MAX_DECLARATIONS, label)
    if any(not isinstance(value, str) or not value for value in result):
        raise TransformationHistoryError(f"{label} must contain non-empty strings")
    if len(set(result)) != len(result):
        raise TransformationHistoryError(f"{label} must not contain duplicates")
    return sorted(result)


def transformation_step(
    *,
    index: int,
    kind: str,
    rule_id: str,
    rule_edition: str,
    input_family_id: str,
    admitted_member_ids: Iterable[str],
    outcome: str,
    output_family_id: str | None = None,
    excluded_member_ids: Iterable[str] = (),
    preserves: Iterable[str] = (),
    loses: Iterable[str] = (),
    limitations: Iterable[str] = (),
    message: str,
) -> dict[str, Any]:
    """Build one canonical step; failed steps have no output family."""
    if type(index) is not int or index < 0 or index >= MAX_STEPS:
        raise TransformationHistoryError("step index is outside the supported bound")
    if kind not in KINDS:
        raise TransformationHistoryError("unsupported transformation kind")
    if not isinstance(rule_id, str) or not _NAME.fullmatch(rule_id):
        raise TransformationHistoryError("rule_id is invalid")
    if not isinstance(rule_edition, str) or not rule_edition:
        raise TransformationHistoryError("rule_edition must be non-empty")
    if not isinstance(input_family_id, str) or not _DIGEST.fullmatch(input_family_id):
        raise TransformationHistoryError("input_family_id must be a SHA-256 identity")
    if outcome not in OUTCOMES:
        raise TransformationHistoryError("unsupported transformation outcome")
    admitted = _digests(admitted_member_ids, "admitted_member_ids", allow_empty=True)
    excluded = _digests(excluded_member_ids, "excluded_member_ids", allow_empty=True)
    if set(admitted).intersection(excluded):
        raise TransformationHistoryError("admitted and excluded domains must be disjoint")
    if outcome == "success":
        if not isinstance(output_family_id, str) or not _DIGEST.fullmatch(output_family_id):
            raise TransformationHistoryError("successful step requires output_family_id")
    elif output_family_id is not None:
        raise TransformationHistoryError("non-success step must not publish an output family")
    if kind == "transform" and excluded:
        raise TransformationHistoryError("strict transform cannot silently exclude members")
    if kind == "restrict" and outcome == "success" and not admitted:
        raise TransformationHistoryError("successful restriction must retain members")
    if outcome == "empty" and (kind != "restrict" or admitted or not excluded):
        raise TransformationHistoryError(
            "empty outcome requires a restriction that excludes its admitted domain"
        )
    if not isinstance(message, str) or not message:
        raise TransformationHistoryError("message must be non-empty")
    value: dict[str, Any] = {
        "schema": STEP_SCHEMA,
        "index": index,
        "kind": kind,
        "rule": {"id": rule_id, "edition": rule_edition},
        "domain": {"admitted_member_ids": admitted, "excluded_member_ids": excluded},
        "input_family_id": input_family_id,
        "outcome": outcome,
        "output_family_id": output_family_id,
        "preserves": _strings(preserves, "preserves"),
        "loses": _strings(loses, "loses"),
        "limitations": _strings(limitations, "limitations"),
        "message": message,
    }
    value["step_id"] = digest(value)
    return value


def build_transformation_history(
    source_family_id: str,
    steps: Iterable[dict[str, Any]],
    *,
    context: str,
    inquiry: str,
) -> dict[str, Any]:
    """Build a canonical order-sensitive history and verify its successful chain."""
    if not isinstance(source_family_id, str) or not _DIGEST.fullmatch(source_family_id):
        raise TransformationHistoryError("source_family_id must be a SHA-256 identity")
    if not isinstance(context, str) or not context or not isinstance(inquiry, str) or not inquiry:
        raise TransformationHistoryError("context and inquiry must be non-empty")
    ordered = _items(steps, MAX_STEPS, "steps")
    if not ordered:
        raise TransformationHistoryError("history must contain at least one step")
    current = source_family_id
    blocked = False
    for index, step in enumerate(ordered):
        validate_transformation_step(step)
        if step["index"] != index:
            raise TransformationHistoryError("step indices must be contiguous and ordered")
        if blocked:
            raise TransformationHistoryError("history must stop after a non-success outcome")
        if step["input_family_id"] != current:
            raise TransformationHistoryError("step input does not continue the family chain")
        if step["outcome"] == "success":
            current = step["output_family_id"]
        else:
            blocked = True
    value: dict[str, Any] = {
        "schema": SCHEMA,
        "source_family_id": source_family_id,
        "context": context,
        "inquiry": inquiry,
        "steps": list(ordered),
        "terminal_outcome": ordered[-1]["outcome"],
        "residual_family_id": current if ordered[-1]["outcome"] == "success" else None,
        "limitations": [
            "This record preserves declared order and domains; it does not prove rule correctness.",
            "No feasibility, optimality, hardware, fidelity, or quantum-advantage conclusion is established.",
        ],
    }
    value["history_id"] = digest(value)
    return value


def validate_transformation_step(value: dict[str, Any]) -> None:
    if not isinstance(value, dict) or value.get("schema") != STEP_SCHEMA:
        raise TransformationHistoryError("unsupported transformation-step schema")
    expected = transformation_step(
        index=value.get("index"), kind=value.get("kind"),
        rule_id=(value.get("rule") or {}).get("id"),
        rule_edition=(value.get("rule") or {}).get("edition"),
        input_family_id=value.get("input_family_id"),
        admitted_member_ids=(value.get("domain") or {}).get("admitted_member_ids", ()),
        excluded_member_ids=(value.get("domain") or {}).get("excluded_member_ids", ()),
        outcome=value.get("outcome"), output_family_id=value.get("output_family_id"),
        preserves=value.get("preserves", ()), loses=value.get("loses", ()),
        limitations=value.get("limitations", ()), message=value.get("message"),
    )
    if value != expected:
        raise TransformationHistoryError("transformation step is non-canonical or has a stale identity")


def validate_transformation_history(value: dict[str, Any]) -> None:
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        raise TransformationHistoryError("unsupported transformation-history schema")
    expected = build_transformation_history(
        value.get("source_family_id"), value.get("steps", ()),
        context=value.get("context"), inquiry=value.get("inquiry"),
    )
    if value != expected:
        raise TransformationHistoryError("transformation history is non-canonical or has a stale identity")
