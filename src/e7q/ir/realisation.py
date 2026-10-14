# SPDX-License-Identifier: Apache-2.0
"""Bounded, planning-only integer realisation of a linked finite residual.

Evidence references and upstream failures are declarations, not authenticated
execution evidence. Sorted identities canonicalise inventories, not preference.
"""
from __future__ import annotations

import re
from typing import Any

from .canonical import canonical_bytes, identified_digest
from .candidate_family import (
    CandidateFamilyError,
    assess_candidate_restriction,
    validate_candidate_family,
)
from .transformation_history import (
    TransformationHistoryError,
    validate_transformation_history,
)

PROFILE = "e7q.ir.finite-integer-lexicographic/v0alpha1"
TIE_POLICY = "retain_all_best"
SCHEMA = "e7q.ir.realisation-request/v0alpha1"
RESULT_SCHEMA = "e7q.ir.realisation-result/v0alpha1"
TABLE_SCHEMA = "e7q.ir.objective-table/v0alpha1"
WITNESS_SCHEMA = "e7q.ir.realisation-witness/v0alpha1"
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,127}\Z")
_MIN_VALUE = -(2 ** 127)
_MAX_VALUE = 2 ** 127 - 1
_MESSAGES = {
    "invalid_input": "Invalid bounded realisation input.",
    "resource_limit": "Realisation exceeds a declared resource bound.",
    "unsupported": "Realisation profile or transformation is unsupported.",
    "domain_error": "Upstream history declares a domain error.",
    "empty": "The linked restriction retained no members.",
    "unique": "Exactly one member has the best declared value vector.",
    "ambiguous": "All equally best members remain unresolved.",
}


class RealisationError(ValueError):
    """A typed refusal with a fixed, input-independent message."""

    def __init__(self, outcome: str = "invalid_input") -> None:
        if outcome not in {"invalid_input", "resource_limit", "unsupported"}:
            outcome = "invalid_input"
        self.outcome = outcome
        super().__init__(_MESSAGES[outcome])


def _require(condition: bool, outcome: str = "invalid_input") -> None:
    if not condition:
        raise RealisationError(outcome)


def _text(value: Any, limit: int) -> str:
    _require(type(value) is str and bool(value))
    # Bound allocation before encoding, and reject surrogate code points.
    _require(len(value) <= limit, "resource_limit")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise RealisationError() from exc
    _require(size <= limit, "resource_limit")
    return value


def _identity(value: Any, *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    _require(type(value) is str and len(value) == 71 and bool(_DIGEST.fullmatch(value)))


def _keys(value: Any, keys: set[str]) -> None:
    _require(type(value) is dict and len(value) == len(keys))
    _require(all(type(key) is str for key in value) and set(value) == keys)


def _list(value: Any, ceiling: int) -> None:
    _require(type(value) is list)
    _require(len(value) <= ceiling, "resource_limit")


def _copy_plain(value: Any, *, backing: bool = False) -> Any:
    """Check a finite built-in JSON graph before copying or serialization.

    Request ceilings are not a hard time/RSS containment certificate. Backing
    records retain Q-A1/Q-A2's own bounds, including their inert string values.
    Active-path tracking rejects cycles but permits ordinary shared subobjects.
    """
    active: set[int] = set()
    nodes = 0
    text_bytes = 0

    def visit(item: Any, depth: int) -> Any:
        nonlocal nodes, text_bytes
        nodes += 1
        _require(depth <= 32, "resource_limit")
        if not backing:
            _require(nodes <= 1_000_000, "resource_limit")
        kind = type(item)
        if item is None or kind is bool:
            return item
        if kind is int:
            _require(_MIN_VALUE <= item <= _MAX_VALUE, "resource_limit")
            return item
        if kind is str:
            if not backing:
                _require(len(item) <= 1_024, "resource_limit")
            try:
                text_bytes += len(item.encode("utf-8"))
            except UnicodeEncodeError as exc:
                raise RealisationError() from exc
            if not backing:
                _require(text_bytes <= 32 * 1024 * 1024, "resource_limit")
            return item
        _require(kind is dict or kind is list)
        _require(id(item) not in active)
        _require(len(item) <= (65_536 if kind is list else 1_024), "resource_limit")
        active.add(id(item))
        try:
            if kind is list:
                return [visit(child, depth + 1) for child in item]
            result = {}
            for key, child in item.items():
                _require(type(key) is str)
                _text(key, 128)
                text_bytes += len(key.encode("utf-8"))
                if not backing:
                    _require(text_bytes <= 32 * 1024 * 1024, "resource_limit")
                result[key] = visit(child, depth + 1)
            return result
        finally:
            active.remove(id(item))

    return visit(value, 0)


def _same(actual: Any, expected: Any) -> None:
    _require(actual == expected and canonical_bytes(actual) == canonical_bytes(expected))


def _limit(value: Any, ceiling: int) -> None:
    _require(type(value) is int and 1 <= value <= ceiling)


def build_realisation_request(
    *, source_family_id: str, history_id: str, restriction_id: str | None,
    input_residual_family_id: str | None, objectives: list[dict[str, Any]],
    objective_rows: list[dict[str, Any]], context: str, inquiry: str,
    profile: str = PROFILE, tie_policy: str = TIE_POLICY,
    max_candidates: int = 4096, max_objectives: int = 16,
) -> dict[str, Any]:
    """Build a canonical request from exact built-in dictionaries and lists."""
    _limit(max_candidates, 4096)
    _limit(max_objectives, 16)
    _list(objectives, max_objectives)
    _require(bool(objectives))
    _list(objective_rows, max_candidates)
    for value in (source_family_id, history_id):
        _identity(value)
    for value in (restriction_id, input_residual_family_id):
        _identity(value, nullable=True)
    _text(context, 1024)
    _text(inquiry, 1024)
    _text(profile, 128)
    _text(tie_policy, 128)
    objectives = _copy_plain(objectives)
    objective_rows = _copy_plain(objective_rows)
    names = []
    for objective in objectives:
        _keys(objective, {"id", "edition", "direction", "unit"})
        name = _text(objective["id"], 128)
        _require(bool(_NAME.fullmatch(name)))
        _text(objective["edition"], 128)
        _text(objective["unit"], 128)
        _require(type(objective["direction"]) is str and objective["direction"] in {"min", "max"})
        names.append(name)
    _require(len(set(names)) == len(names))
    members: set[str] = set()
    rows = []
    for row in objective_rows:
        _keys(row, {"member_id", "values"})
        _identity(row["member_id"])
        _require(row["member_id"] not in members)
        members.add(row["member_id"])
        _list(row["values"], max_objectives)
        _require(len(row["values"]) == len(names))
        by_objective = {}
        for entry in row["values"]:
            _keys(entry, {"objective_id", "value", "evidence_ref"})
            name = _text(entry["objective_id"], 128)
            _require(name in names and name not in by_objective)
            _require(type(entry["value"]) is int)
            _require(_MIN_VALUE <= entry["value"] <= _MAX_VALUE, "resource_limit")
            _identity(entry["evidence_ref"])
            by_objective[name] = entry
        rows.append({"member_id": row["member_id"], "values": [by_objective[name] for name in names]})
    table = {"schema": TABLE_SCHEMA, "rows": sorted(rows, key=lambda row: row["member_id"])}
    table["table_id"] = identified_digest(table, "table_id")
    request = {
        "schema": SCHEMA, "profile": profile, "tie_policy": tie_policy,
        "context": context, "inquiry": inquiry, "source_family_id": source_family_id,
        "history_id": history_id, "restriction_id": restriction_id,
        "input_residual_family_id": input_residual_family_id,
        "objectives": objectives, "objective_table": table,
        "limits": {"max_candidates": max_candidates, "max_objectives": max_objectives},
    }
    request["request_id"] = identified_digest(request, "request_id")
    return request


def validate_realisation_request(request: dict[str, Any]) -> None:
    """Rebuild every request identity and require whole canonical equality."""
    _keys(request, {
        "schema", "request_id", "profile", "tie_policy", "context", "inquiry",
        "source_family_id", "history_id", "restriction_id", "input_residual_family_id",
        "objectives", "objective_table", "limits",
    })
    _keys(request["limits"], {"max_candidates", "max_objectives"})
    _limit(request["limits"]["max_candidates"], 4096)
    _limit(request["limits"]["max_objectives"], 16)
    request = _copy_plain(request)
    _require(request["schema"] == SCHEMA)
    _identity(request["request_id"])
    _keys(request["objective_table"], {"schema", "rows", "table_id"})
    _require(request["objective_table"]["schema"] == TABLE_SCHEMA)
    _identity(request["objective_table"]["table_id"])
    expected = build_realisation_request(
        source_family_id=request["source_family_id"], history_id=request["history_id"],
        restriction_id=request["restriction_id"], input_residual_family_id=request["input_residual_family_id"],
        objectives=request["objectives"], objective_rows=request["objective_table"]["rows"],
        context=request["context"], inquiry=request["inquiry"], profile=request["profile"],
        tie_policy=request["tie_policy"], **request["limits"],
    )
    _same(request, expected)


def _guard_family(family: Any) -> None:
    _require(type(family) is dict)
    _list(family.get("factors"), 32)
    _list(family.get("members"), 65_536)
    for key in ("assumptions", "limitations"):
        _list(family.get(key), 128)
    for factor in family["factors"]:
        _require(type(factor) is dict)
        _list(factor.get("dimensions"), 32)
        _list(factor.get("alternatives"), 256)
        for alternative in factor["alternatives"]:
            _require(type(alternative) is dict and type(alternative.get("bindings")) is dict)


def _guard_history(history: Any) -> None:
    _require(type(history) is dict)
    _list(history.get("steps"), 256)
    for step in history["steps"]:
        _require(type(step) is dict)
        _require(type(step.get("rule")) is dict and type(step.get("domain")) is dict)
        _require(type(step.get("kind")) is str and type(step.get("outcome")) is str)
        for key in ("admitted_member_ids", "excluded_member_ids"):
            _list(step["domain"].get(key), 65_536)
        for key in ("preserves", "loses", "limitations"):
            _list(step.get(key), 128)


def _result(outcome: str, bindings: dict[str, Any], *, best: list[str] | None = None,
            selected: str | None = None, witness: dict[str, Any] | None = None,
            upstream: str | None = None) -> dict[str, Any]:
    result = {
        "schema": RESULT_SCHEMA, "outcome": outcome,
        "request_id": None, "source_family_id": None, "history_id": None,
        "restriction_id": None, "input_residual_family_id": None,
        "best_member_ids": best if best is not None else [],
        "selected_member_id": selected, "witness": witness,
        "upstream_outcome": upstream, "message": _MESSAGES[outcome],
    }
    result.update(bindings)
    result["result_id"] = identified_digest(result, "result_id")
    return result


def assess_realisation(request: dict[str, Any], family: dict[str, Any],
                       history: dict[str, Any], restriction: dict[str, Any] | None = None) -> dict[str, Any]:
    """Reconstruct the linked restriction before ranking supplied integer rows."""
    bindings: dict[str, Any] = {}
    upstream = None
    try:
        validate_realisation_request(request)
        request = _copy_plain(request)
        bindings["request_id"] = request["request_id"]
        _require(request["profile"] == PROFILE and request["tie_policy"] == TIE_POLICY, "unsupported")
        family = _copy_plain(family, backing=True)
        history = _copy_plain(history, backing=True)
        _guard_family(family)
        _guard_history(history)
        validate_candidate_family(family)
        validate_transformation_history(history)
        # Public validators reconstruct records; byte identities add type-sensitive checking.
        _require(family["family_id"] == identified_digest(family, "family_id"))
        _require(history["history_id"] == identified_digest(history, "history_id"))
        for step in history["steps"]:
            _require(step["step_id"] == identified_digest(step, "step_id"))
        _require(request["source_family_id"] == family["family_id"] == history["source_family_id"])
        _require(request["history_id"] == history["history_id"])
        _require(request["context"] == history["context"] and request["inquiry"] == history["inquiry"])
        bindings.update(source_family_id=family["family_id"], history_id=history["history_id"])
        _require(len(history["steps"]) == 1 and history["steps"][0]["kind"] == "restrict", "unsupported")
        step = history["steps"][0]
        rows = request["objective_table"]["rows"]
        terminal = history["terminal_outcome"]
        if terminal not in {"success", "empty"}:
            _require(restriction is None and request["restriction_id"] is None
                     and request["input_residual_family_id"] is None and not rows)
            return _result(terminal, bindings, upstream=terminal)
        restriction = _copy_plain(restriction, backing=True)
        _require(type(restriction) is dict and restriction.get("outcome") in ("success", "empty"))
        criterion = restriction.get("criterion")
        _keys(criterion, {"id", "edition", "text"})
        _list(restriction.get("retained_member_ids"), 65_536)
        replay = assess_candidate_restriction(
            family, restriction["retained_member_ids"], criterion_id=criterion["id"],
            criterion_edition=criterion["edition"], criterion_text=criterion["text"],
        )
        _same(restriction, replay)
        _require(restriction["outcome"] == terminal)
        _require(request["restriction_id"] == restriction["restriction_id"])
        _require(step["input_family_id"] == restriction["source_family_id"] == family["family_id"])
        _require(step["rule"] == {"id": criterion["id"], "edition": criterion["edition"]})
        _require(step["domain"] == {
            "admitted_member_ids": restriction["retained_member_ids"],
            "excluded_member_ids": restriction["excluded_member_ids"],
        })
        residual = restriction["result_family"]["family_id"] if terminal == "success" else None
        _require(step["output_family_id"] == history["residual_family_id"] == residual)
        _require(request["input_residual_family_id"] == residual)
        bindings.update(restriction_id=restriction["restriction_id"], input_residual_family_id=residual)
        upstream = terminal
        if terminal == "empty":
            _require(not rows)
            return _result("empty", bindings, upstream=upstream)
        retained = restriction["retained_member_ids"]
        _require(len(retained) <= request["limits"]["max_candidates"], "resource_limit")
        _require([row["member_id"] for row in rows] == retained)
        best_key = None
        best_vector = None
        best = []
        for row in rows:
            vector = [entry["value"] for entry in row["values"]]
            key = tuple(value if objective["direction"] == "min" else -value
                        for value, objective in zip(vector, request["objectives"]))
            if best_key is None or key < best_key:
                best_key, best_vector, best = key, vector, [row["member_id"]]
            elif key == best_key:
                best.append(row["member_id"])
        _require(bool(best))
        witness = {
            "schema": WITNESS_SCHEMA, "input_residual_family_id": residual,
            "objective_table_id": request["objective_table"]["table_id"],
            "best_value_vector": best_vector, "best_member_ids": list(best),
        }
        witness["witness_id"] = identified_digest(witness, "witness_id")
        unique = len(best) == 1
        return _result("unique" if unique else "ambiguous", bindings, best=best,
                       selected=best[0] if unique else None, witness=witness, upstream=upstream)
    except RealisationError as exc:
        return _result(exc.outcome, bindings, upstream=upstream)
    except (CandidateFamilyError, TransformationHistoryError):
        return _result("invalid_input", bindings, upstream=upstream)


def validate_realisation_result(result: dict[str, Any], request: dict[str, Any],
                                family: dict[str, Any], history: dict[str, Any],
                                restriction: dict[str, Any] | None = None) -> None:
    """Reject even freshly rehashed forgery by recomputing the whole assessment."""
    result = _copy_plain(result)
    expected = assess_realisation(request, family, history, restriction)
    _same(result, expected)
