#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Replay one frozen real-workflow task through Joint and both table baselines.

The machine artifact is not a human reviewer session. It accepts only the
bounded two-layout/two-target carrier implemented by this pilot.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from e7q.ir.canonical import canonical_bytes
from tools.run_e7c_joint_pilot import import_e7c, make_joint, run_case

SCHEMA = "e7q.joint-visible-effect-task/v1"
ORACLE_SCHEMA = "e7q.joint-visible-effect-oracle/v1"
LAYOUTS = {"L0", "L1"}
TARGETS = {"T0", "T1"}
FILTER_IDENTITIES = (
    {"stage": 1, "rule_id": "joint.first.exclude-layout-L1/v1", "dimension": "layout", "excluded": "L1"},
    {"stage": 2, "rule_id": "joint.second.exclude-target-T1/v1", "dimension": "target", "excluded": "T1"},
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class TaskFormatError(ValueError):
    """Task or oracle input is not frozen in the declared pilot format."""


def _nonempty_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TaskFormatError(f"{field} must be a non-empty string")
    return value


def validate_task(value: object) -> tuple[dict, list[tuple[str, str]], list[Fraction]]:
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        raise TaskFormatError(f"task schema must be {SCHEMA}")
    if value.get("task_kind") != "real_workflow":
        raise TaskFormatError("task_kind must be real_workflow; synthetic fixtures are not reviewer tasks")
    for field in ("task_id", "source_intent", "origin_ref"):
        _nonempty_text(value.get(field), field)

    dimensions = value.get("dimension_mapping")
    if not isinstance(dimensions, dict):
        raise TaskFormatError("dimension_mapping is required")
    for dimension, labels in (("layout", LAYOUTS), ("target", TARGETS)):
        mapping = dimensions.get(dimension)
        if not isinstance(mapping, dict) or set(mapping) != labels:
            raise TaskFormatError(f"dimension_mapping.{dimension} must define exactly {sorted(labels)}")
        meanings = [_nonempty_text(mapping[label], f"dimension_mapping.{dimension}.{label}") for label in sorted(labels)]
        if len(set(meanings)) != len(meanings):
            raise TaskFormatError(f"dimension_mapping.{dimension} meanings must be distinct")

    rules = value.get("filter_rules")
    if not isinstance(rules, list) or len(rules) != len(FILTER_IDENTITIES):
        raise TaskFormatError("filter_rules must identify both ordered pilot filters")
    for index, (rule, identity) in enumerate(zip(rules, FILTER_IDENTITIES)):
        if not isinstance(rule, dict):
            raise TaskFormatError(f"filter_rules[{index}] must be an object")
        for key, expected in identity.items():
            if rule.get(key) != expected:
                raise TaskFormatError(f"filter_rules[{index}].{key} must be {expected!r}")
        _nonempty_text(rule.get("description"), f"filter_rules[{index}].description")

    expected = value.get("expected_result")
    if not isinstance(expected, dict):
        raise TaskFormatError("expected_result reference and SHA-256 are required")
    _nonempty_text(expected.get("ref"), "expected_result.ref")
    if not isinstance(expected.get("sha256"), str) or not _SHA256.fullmatch(expected["sha256"]):
        raise TaskFormatError("expected_result.sha256 must be 64 lowercase hexadecimal characters")

    rows_value = value.get("rows")
    if not isinstance(rows_value, list) or not rows_value:
        raise TaskFormatError("rows must be a non-empty list")
    pairs: list[tuple[str, str]] = []
    coefficients: list[Fraction] = []
    for index, row in enumerate(rows_value):
        if not isinstance(row, dict):
            raise TaskFormatError(f"rows[{index}] must be an object")
        layout, target, coefficient_text = row.get("layout"), row.get("target"), row.get("coefficient")
        if (not isinstance(layout, str) or layout not in LAYOUTS
                or not isinstance(target, str) or target not in TARGETS):
            raise TaskFormatError(f"rows[{index}] must use L0/L1 and T0/T1")
        if not isinstance(coefficient_text, str):
            raise TaskFormatError(f"rows[{index}].coefficient must be an exact fraction string")
        try:
            coefficient = Fraction(coefficient_text)
        except (ValueError, ZeroDivisionError) as exc:
            raise TaskFormatError(f"rows[{index}].coefficient is not a rational") from exc
        if coefficient == 0:
            raise TaskFormatError(f"rows[{index}].coefficient must be nonzero")
        if str(coefficient) != coefficient_text:
            raise TaskFormatError(f"rows[{index}].coefficient must be reduced canonical form")
        pair = (layout, target)
        if pair in pairs:
            raise TaskFormatError(f"rows[{index}] duplicates pair {pair}")
        pairs.append(pair)
        coefficients.append(coefficient)

    for field in ("step_bound", "ledger_bound"):
        bound = value.get(field, 20)
        if type(bound) is not int or bound < 0:
            raise TaskFormatError(f"{field} must be a non-negative integer")
    return value, pairs, coefficients


def task_scope_limit(task: dict) -> str:
    return (f"Finite real-workflow task {task['task_id']!r} as declared in the frozen input; "
            "one-task machine replay only, with no human reviewer timing or decision.")


def comparison_disposition(status: str) -> str:
    if status == "success":
        return "compare_retained_and_excluded_sets"
    if status == "resource_limit":
        return "separate_resource_limit_outcome_no_decision_comparison"
    return f"not_comparable_terminal_outcome:{status}"


def _row_signature(row: dict) -> tuple[str, str, str]:
    if not isinstance(row, dict):
        raise TaskFormatError("oracle rows must be objects")
    try:
        layout, target = row["layout"], row["target"]
        coefficient_text = row["coefficient"]
    except (KeyError, TypeError) as exc:
        raise TaskFormatError("oracle row needs layout, target, and exact coefficient") from exc
    if not isinstance(coefficient_text, str):
        raise TaskFormatError("oracle coefficient must be an exact fraction string")
    try:
        coefficient = Fraction(coefficient_text)
    except (TypeError, ValueError, ZeroDivisionError) as exc:
        raise TaskFormatError("oracle coefficient must be a rational string") from exc
    if str(coefficient) != coefficient_text:
        raise TaskFormatError("oracle coefficient must be reduced canonical form")
    if (not isinstance(layout, str) or layout not in LAYOUTS
            or not isinstance(target, str) or target not in TARGETS or coefficient == 0):
        raise TaskFormatError("oracle row has unsupported labels or a zero coefficient")
    return layout, target, str(coefficient)


def load_oracle(task: dict, oracle_path: Path) -> tuple[dict, str]:
    raw = oracle_path.read_bytes()
    actual_sha = sha256(raw).hexdigest()
    if actual_sha != task["expected_result"]["sha256"]:
        raise TaskFormatError("oracle bytes do not match the frozen expected_result SHA-256")
    try:
        oracle = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TaskFormatError("oracle file is not valid JSON") from exc
    if not isinstance(oracle, dict) or oracle.get("schema") != ORACLE_SCHEMA:
        raise TaskFormatError(f"oracle schema must be {ORACLE_SCHEMA}")
    if oracle.get("task_id") != task["task_id"]:
        raise TaskFormatError("oracle task_id does not match the frozen task")
    if (not isinstance(oracle.get("terminal_status"), str)
            or oracle.get("terminal_status") not in {"success", "resource_limit"}):
        raise TaskFormatError("oracle terminal_status must be success or resource_limit")
    if oracle["terminal_status"] == "resource_limit":
        _nonempty_text(oracle.get("resource_limit_reason"), "oracle.resource_limit_reason")
        return oracle, actual_sha

    for name in ("retained", "first_excluded", "second_excluded"):
        rows = oracle.get(name)
        if not isinstance(rows, list):
            raise TaskFormatError(f"oracle.{name} must be a list for a success result")
        signatures = [_row_signature(row) for row in rows]
        if len(set(signatures)) != len(signatures):
            raise TaskFormatError(f"oracle.{name} contains duplicate rows")
    _validate_oracle_reasons(oracle)
    return oracle, actual_sha


def _validate_oracle_reasons(oracle: dict) -> None:
    excluded = {}
    for row in oracle["first_excluded"]:
        excluded[_row_signature(row)[:2]] = FILTER_IDENTITIES[0]["rule_id"]
    for row in oracle["second_excluded"]:
        key = _row_signature(row)[:2]
        if key in excluded:
            raise TaskFormatError("oracle row is excluded twice")
        excluded[key] = FILTER_IDENTITIES[1]["rule_id"]
    reasons = oracle.get("exclusion_reasons")
    if not isinstance(reasons, list):
        raise TaskFormatError("oracle.exclusion_reasons must list every excluded row and rule")
    seen = {}
    for reason in reasons:
        if not isinstance(reason, dict):
            raise TaskFormatError("oracle exclusion reasons must be objects")
        layout, target = reason.get("layout"), reason.get("target")
        if not isinstance(layout, str) or not isinstance(target, str):
            raise TaskFormatError("oracle exclusion reason needs string row labels")
        key = (layout, target)
        if key in seen:
            raise TaskFormatError("oracle has duplicate exclusion reasons")
        if key not in excluded or reason.get("rule_id") != excluded[key]:
            raise TaskFormatError("oracle exclusion reason does not match its frozen filter identity")
        _nonempty_text(reason.get("reason"), "oracle exclusion reason")
        seen[key] = reason
    if set(seen) != set(excluded):
        raise TaskFormatError("oracle must give a reason for every excluded row")


def _table_signature(rows: list[dict]) -> list[tuple[str, str, str]]:
    result = []
    for row in rows:
        bindings = row["bindings"]
        coefficient = row["coefficient"]
        result.append((bindings["layout"], bindings["target"],
                       str(Fraction(coefficient["numerator"], coefficient["denominator"]))))
    return result


def check_success_oracle(oracle: dict, replay: dict) -> dict:
    actual_status = replay["e7c_source_result"]["terminal_outcome"]["tag"]
    expected_status = oracle["terminal_status"]
    if actual_status != expected_status:
        raise TaskFormatError(f"source terminal status {actual_status!r} differs from frozen oracle {expected_status!r}")
    disposition = comparison_disposition(actual_status)
    if actual_status == "resource_limit":
        return {"status": disposition, "terminal_status": actual_status}
    if actual_status != "success":
        return {"status": disposition, "terminal_status": actual_status}

    actual_sets = {
        "retained": _table_signature(replay["full_correlated_table"]["final"]),
        "first_excluded": _table_signature(replay["full_correlated_table"]["first_excluded"]),
        "second_excluded": _table_signature(replay["full_correlated_table"]["second_excluded"]),
    }
    for key, rows in actual_sets.items():
        expected = [_row_signature(row) for row in oracle[key]]
        if rows != expected:
            raise TaskFormatError(f"full correlated table {key} differs from the frozen oracle")
    return {
        "status": disposition,
        "terminal_status": actual_status,
        "retained_and_exclusion_sets_match_oracle": True,
        "frozen_exclusion_reasons": oracle["exclusion_reasons"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--e7c-root", required=True, type=Path,
                        help="checkout pinned at 5b5cb5f10ddd913df66f5d9f65fbe059a2e33193")
    parser.add_argument("--task", required=True, type=Path,
                        help=f"frozen task JSON using schema {SCHEMA}")
    parser.add_argument("--oracle", required=True, type=Path,
                        help="separate expected-result JSON whose SHA-256 is pinned in the task")
    parser.add_argument("--output", required=True, type=Path,
                        help="path for canonical machine replay JSON")
    args = parser.parse_args()

    try:
        task_bytes = args.task.read_bytes()
        task, pairs, coefficients = validate_task(json.loads(task_bytes))
        oracle, oracle_sha = load_oracle(task, args.oracle)
        e7c = import_e7c(args.e7c_root)
        config, joint, _source, _ir, _nested = e7c
        source_joint = make_joint(config, joint, pairs, coefficients=coefficients)
        replay = run_case(
            e7c,
            task["task_id"],
            source_joint,
            step_bound=task.get("step_bound", 20),
            ledger_bound=task.get("ledger_bound", 20),
        )
        replay["limits"][0] = task_scope_limit(task)
        comparison = check_success_oracle(oracle, replay)
    except (OSError, json.JSONDecodeError, TaskFormatError, ValueError, KeyError) as exc:
        parser.error(str(exc))

    result = {
        "schema": "e7q.joint-visible-effect-replay/v1",
        "task_record_sha256": sha256(task_bytes).hexdigest(),
        "oracle_ref": task["expected_result"]["ref"],
        "oracle_sha256": oracle_sha,
        "task": task,
        "machine_replay": replay,
        "oracle_check": comparison,
        "limits": [
            "This artifact contains a source/IR replay and deterministic table baselines, not a human reviewer session.",
            "Only the pinned two-layout/two-target carrier is admitted; unsupported task topology must not be coerced.",
            "A resource_limit is preserved as a separate outcome and never scored as a retained/excluded decision.",
            "Reviewer decision, active effort, errors, reasons, and independent assessor result belong in the separate session record.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_bytes(result) + b"\n")
    print(json.dumps({"status": "PASS", "task_id": task["task_id"],
                      "oracle_check": comparison["status"], "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
