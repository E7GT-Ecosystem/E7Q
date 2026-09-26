#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Replay one frozen reviewer task through Joint and both table baselines.

Input is a bounded real-task carrier in the existing two-layout/two-target
pilot vocabulary. This creates evidence for the machine replay only; a human
reviewer session and its effort/decision/errors must be recorded separately.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
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
LAYOUTS = {"L0", "L1"}
TARGETS = {"T0", "T1"}


class TaskFormatError(ValueError):
    """Task input is not representable by the bounded pilot carrier."""


def validate_task(value: object) -> tuple[dict, list[tuple[str, str]], list[Fraction]]:
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        raise TaskFormatError(f"task schema must be {SCHEMA}")
    for field in ("task_id", "source_intent", "origin_ref"):
        if not isinstance(value.get(field), str) or not value[field].strip():
            raise TaskFormatError(f"{field} must be a non-empty string")
    if not isinstance(value.get("rows"), list) or not value["rows"]:
        raise TaskFormatError("rows must be a non-empty list")

    pairs: list[tuple[str, str]] = []
    coefficients: list[Fraction] = []
    for index, row in enumerate(value["rows"]):
        if not isinstance(row, dict):
            raise TaskFormatError(f"rows[{index}] must be an object")
        layout, target, coefficient_text = (
            row.get("layout"), row.get("target"), row.get("coefficient")
        )
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

    step_bound = value.get("step_bound", 20)
    ledger_bound = value.get("ledger_bound", 20)
    if type(step_bound) is not int or step_bound < 0:
        raise TaskFormatError("step_bound must be a non-negative integer")
    if type(ledger_bound) is not int or ledger_bound < 0:
        raise TaskFormatError("ledger_bound must be a non-negative integer")
    return value, pairs, coefficients


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--e7c-root", required=True, type=Path,
                        help="checkout pinned at 5b5cb5f10ddd913df66f5d9f65fbe059a2e33193")
    parser.add_argument("--task", required=True, type=Path,
                        help=f"frozen JSON task using schema {SCHEMA}")
    parser.add_argument("--output", required=True, type=Path,
                        help="path for canonical replay JSON")
    args = parser.parse_args()

    try:
        task, pairs, coefficients = validate_task(json.loads(args.task.read_text()))
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
    except (OSError, json.JSONDecodeError, TaskFormatError, ValueError, KeyError) as exc:
        parser.error(str(exc))

    result = {
        "schema": "e7q.joint-visible-effect-replay/v1",
        "task": task,
        "machine_replay": replay,
        "limits": [
            "This artifact contains a source/IR replay and both deterministic table baselines, not a human reviewer session.",
            "Only L0/L1 layout and T0/T1 target pairs supported by the pinned pilot mapping are admitted.",
            "Reviewer decision, active effort, errors, reasons, and independent assessor result belong in the separate session record.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_bytes(result) + b"\n")
    print(json.dumps({"status": "PASS", "task_id": task["task_id"], "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
