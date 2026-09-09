#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Run the pinned PyZX one-sided equivalence evaluation corpus."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import tempfile

from e7q.ir.canonical import canonical_bytes, digest
from e7q.ir.pyzx import EXACT_CRITERION, GLOBAL_PHASE_CRITERION, evaluate


def qasm(width: int, gates: list[str]) -> str:
    return "\n".join((
        "OPENQASM 2.0;",
        'include "qelib1.inc";',
        f"qreg q[{width}];",
        f"creg c[{width}];",
        *gates,
        "measure q -> c;",
        "",
    ))


def ref(text: str) -> str:
    return "sha256:" + sha256(text.encode()).hexdigest()


def cases():
    width = 26
    swaps = [f"swap q[{i}],q[{i + 1}];" for i in range(0, width, 2)]
    rewrite = [
        gate for i in range(0, width, 2)
        for gate in (
            f"cx q[{i}],q[{i + 1}];",
            f"cx q[{i + 1}],q[{i}];",
            f"cx q[{i}],q[{i + 1}];",
        )
    ]
    yield "swap-rewrite-26", "exact-equivalent", qasm(width, swaps), qasm(width, rewrite), 10.0
    yield "global-phase-26", "global-phase-only", qasm(width, ["x q[0];", "z q[0];"]), qasm(width, ["z q[0];", "x q[0];"]), 10.0
    yield "altered-gate-26", "inconclusive-non-equivalent", qasm(width, ["x q[0];"]), qasm(width, ["z q[0];"]), 10.0
    deep = [gate for i in range(300) for gate in (
        f"h q[{i % width}];", f"cx q[{i % width}],q[{(i + 1) % width}];",
    )]
    yield "forced-timeout-26", "blocked", qasm(width, deep), qasm(width, deep), 1e-9


def expected(case: str, criterion: dict) -> str:
    if case == "exact-equivalent":
        return "PASS"
    if case == "global-phase-only":
        return "PASS" if criterion["options"]["up_to_global_phase"] else "NOT_ASSESSED"
    if case == "inconclusive-non-equivalent":
        return "NOT_ASSESSED"
    return "BLOCKED"


def run(created_at: str) -> dict:
    results = []
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for case_id, expectation, left_text, right_text, timeout in cases():
            left = root / f"{case_id}-left.qasm"
            right = root / f"{case_id}-right.qasm"
            left.write_text(left_text)
            right.write_text(right_text)
            runs = []
            for criterion in (EXACT_CRITERION, GLOBAL_PHASE_CRITERION):
                artifact = evaluate(
                    left,
                    right,
                    criterion=criterion,
                    source_refs=(ref(left_text), ref(right_text)),
                    created_at=created_at,
                    timeout_seconds=timeout,
                )
                actual = artifact["payload"]["outcome"]["status"]
                runs.append({
                    "criterion_id": criterion["id"],
                    "expected_status": expected(expectation, criterion),
                    "expectation_match": actual == expected(expectation, criterion),
                    "evidence_id": artifact["artifact_id"],
                    "assessment": artifact,
                })
            results.append({
                "id": case_id,
                "qubits": 26,
                "expected": expectation,
                "source_refs": [ref(left_text), ref(right_text)],
                "runs": runs,
            })
    statuses = {}
    for case in results:
        for item in case["runs"]:
            status = item["assessment"]["payload"]["outcome"]["status"]
            statuses[status] = statuses.get(status, 0) + 1
    report = {
        "schema": "e7q.ir.pyzx-benchmark/v1",
        "created_at": created_at,
        "backend_requirement": "pyzx==0.10.6",
        "scope": "one-sided structured rewrite evidence; failed reduction is inconclusive",
        "results": results,
        "summary": {
            "cases": len(results),
            "attempts": sum(len(case["runs"]) for case in results),
            "statuses": dict(sorted(statuses.items())),
            "expectation_matches": sum(
                item["expectation_match"] for case in results for item in case["runs"]
            ),
        },
    }
    report["report_id"] = digest(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--created-at", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.created_at)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_bytes(report) + b"\n")
    print(json.dumps({"report_id": report["report_id"], **report["summary"]}, sort_keys=True))
    return 0 if report["summary"]["expectation_matches"] == report["summary"]["attempts"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
