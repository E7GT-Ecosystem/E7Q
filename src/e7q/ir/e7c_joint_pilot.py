# SPDX-License-Identifier: Apache-2.0
"""Opt-in, finite E7C Joint -> Q-A1 planning mapping, edition 0alpha1.

Exact coefficients live only in this source-bound mapping, never in Q-A1.
Neither coefficient nor planning label has a quantum interpretation.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any, Callable

from .canonical import digest
from .candidate_family import build_candidate_family, factor, validate_candidate_family


SCHEMA = "e7q.ir.e7c-joint-q-a1-mapping/v0alpha1"
SOURCE_EDITION = "E7C-EECQ-JOINT-TWO-STAGE/0.1-provisional"
FIRST_EDITION = "E7C-EECQ-JOINT-RESTRICT/0.1-provisional"
FIRST_PREDICATE = "FG3-JOINT-COORD0-ABSENT-AB/0.1-provisional"
SECOND_PREDICATE = "FG3-JOINT-COORD1-ABSENT-BC/0.1-provisional"
INTENT = "bounded-layout-target-planning-fixture/v0alpha1"
LAYOUT_TAG = "pilot.layout"
TARGET_TAG = "pilot.target"
PREDICATES = {"layout.L1": {"coordinate": 0, "edge": "AB", "meaning": "exclude"},
              "target.T1": {"coordinate": 1, "edge": "BC", "meaning": "exclude"}}


class MappingAdmission(ValueError):
    pass


def _rows(source: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        if (type(source) is not dict or source["edition"] != SOURCE_EDITION
                or source["second_predicate_edition"] != SECOND_PREDICATE
                or type(source["first"]) is not dict
                or source["first"]["edition"] != FIRST_EDITION
                or source["first"]["predicate_edition"] != FIRST_PREDICATE):
            raise MappingAdmission("unrecognised source or predicate edition")
        rows = source["first"]["rows"]
        if type(rows) is not list or not rows or len(rows) > 4:
            raise MappingAdmission("pilot requires one to four correlated rows")
        keys: list[tuple[tuple[Any, ...], ...]] = []
        members: set[tuple[str, str]] = set()
        for row in rows:
            if type(row) is not dict or set(row) != {"atoms", "coefficient"}:
                raise MappingAdmission("malformed source row")
            atoms, c = row["atoms"], row["coefficient"]
            if type(atoms) is not list or len(atoms) != 2:
                raise MappingAdmission("binary Joint required")
            pair = []
            for index, (allowed, tag) in enumerate((("AB", LAYOUT_TAG), ("BC", TARGET_TAG))):
                graph = atoms[index]
                if (type(graph) is not dict or set(graph) != {"edges", "tag"}
                        or graph["tag"] != tag or type(graph["edges"]) is not list
                        or graph["edges"] not in ([], [allowed])):
                    raise MappingAdmission("unsupported graph or tag encoding")
                pair.append(("graph", tuple(graph["edges"]), True, tag))
            if (type(c) is not dict or set(c) != {"numerator", "denominator"}
                    or type(c["numerator"]) is not int
                    or type(c["denominator"]) is not int
                    or c["denominator"] <= 0 or c["numerator"] == 0):
                raise MappingAdmission("nonzero signed rational required")
            q = Fraction(c["numerator"], c["denominator"])
            if (q.numerator, q.denominator) != (c["numerator"], c["denominator"]):
                raise MappingAdmission("coefficient must be reduced")
            key = tuple(pair)
            keys.append(key)
            member = ("L1" if atoms[0]["edges"] else "L0",
                      "T1" if atoms[1]["edges"] else "T0")
            if member in members:
                raise MappingAdmission("duplicate member mapping")
            members.add(member)
        if keys != sorted(set(keys)):
            raise MappingAdmission("noncanonical or duplicate source support")
        return rows
    except (KeyError, TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise MappingAdmission("invalid admitted Joint mapping source") from exc


def map_joint(source: dict[str, Any], *, admit_source: Callable[[dict[str, Any]], Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate this narrower pilot domain; preserve source row and Q-A1 orders."""
    # The pinned E7C admission is required; our narrow mapping is not a
    # replacement for canonical Joint, edition, or resource admission.
    if admit_source is None:
        raise MappingAdmission("pinned E7C admission is required")
    admit_source(source)
    rows = _rows(source)
    source_id = digest({"source_intent": INTENT})
    bindings = [{"layout": "L1" if row["atoms"][0]["edges"] else "L0",
                 "target": "T1" if row["atoms"][1]["edges"] else "T0"} for row in rows]
    family = build_candidate_family(source_id, [factor("layout_target", ["layout", "target"], bindings)],
                                    assumptions=["Planning identifiers only; graph edges use the explicit fixture convention."],
                                    limitations=["No quantum semantics or candidate feasibility is inferred."])
    members = {(m["bindings"]["layout"], m["bindings"]["target"]): m["member_id"]
               for m in family["members"]}
    mapping_rows = []
    for index, (row, binding) in enumerate(zip(rows, bindings)):
        c = row["coefficient"]
        mapping_rows.append({"source_row_index": index, "source_row_identity": digest(row),
                             "member_id": members[binding["layout"], binding["target"]],
                             "bindings": binding, "coefficient": dict(c)})
    record = {"schema": SCHEMA, "source_edition": SOURCE_EDITION,
              "source_joint_digest": digest(source), "source_intent": INTENT,
              "family_id": family["family_id"], "predicate_interpretation": PREDICATES,
              "rows_in_source_order": mapping_rows,
              "preserves": ["joint row correlation", "original source row order", "exact signed rational coefficients"],
              "limitations": ["Q-A1 sorts members by identity and omits coefficients; return to the bound Joint source.",
                              "No quantum amplitude, probability, feasibility or physical claim."]}
    record["mapping_id"] = digest(record)
    return record, family


def validate_mapping(source: dict[str, Any], mapping: dict[str, Any], family: dict[str, Any],
                     *, admit_source: Callable[[dict[str, Any]], Any]) -> None:
    validate_candidate_family(family)
    expected, expected_family = map_joint(source, admit_source=admit_source)
    if mapping != expected or family != expected_family:
        raise MappingAdmission("stale, altered, ambiguous or incomplete source mapping")


def full_table_baseline(mapping: dict[str, Any]) -> dict[str, Any]:
    """Conventional full correlated table retaining explicit coefficients."""
    rows = mapping["rows_in_source_order"]
    final = [r for r in rows if r["bindings"]["layout"] != "L1" and r["bindings"]["target"] != "T1"]
    first = [r for r in rows if r["bindings"]["layout"] == "L1"]
    second = [r for r in rows if r["bindings"]["layout"] != "L1" and r["bindings"]["target"] == "T1"]
    trace = [{"stage": "first", "event": "restriction_attempt"}]
    trace.extend({"stage": "first", "event": "row_checked", "source_row_index": r["source_row_index"],
                  "decision": "excluded" if r in first else "retained"} for r in rows)
    trace.append({"stage": "second", "event": "restriction_attempt"})
    trace.extend({"stage": "second", "event": "row_checked", "source_row_index": r["source_row_index"],
                  "decision": "second_excluded" if r in second else "retained"}
                 for r in rows if r not in first)
    return {"final": final, "first_excluded": first, "second_excluded": second,
            "audit_trace": trace,
            "method": "two ordered filters over full correlated two-column table with exact rational cell",
            "limitation": "No budget-sensitive evaluator; this complete-table result does not model E7C resource failure."}


def marginal_cartesian_baseline(mapping: dict[str, Any]) -> dict[str, Any]:
    """Intentionally lossy counterexample, unsuitable as competent baseline."""
    left = {"L0": Fraction(0), "L1": Fraction(0)}
    right = {"T0": Fraction(0), "T1": Fraction(0)}
    for row in mapping["rows_in_source_order"]:
        q = Fraction(**row["coefficient"])
        left[row["bindings"]["layout"]] += q
        right[row["bindings"]["target"]] += q
    return {"layout_marginals": {k: str(v) for k, v in left.items()},
            "target_marginals": {k: str(v) for k, v in right.items()},
            "invented_cartesian_pairs": [
                {"layout": a, "target": b, "coefficient": str(left[a] * right[b])}
                for a in left for b in right],
            "limitation": "This multiplication invents independence and loses the original correlated Joint."}
