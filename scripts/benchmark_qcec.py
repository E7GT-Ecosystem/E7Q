#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Run the pinned, repeated MQT QCEC structured scalability ladder."""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
from typing import Any, Callable, Iterable

from e7q.ir.canonical import canonical_bytes, digest
from e7q.ir.qcec import (
    NUMERICAL_EXACT_CRITERION,
    NUMERICAL_GLOBAL_PHASE_CRITERION,
    evaluate,
)

SCHEMA = "e7q.ir.qcec-benchmark/v2"
RUNNER_REVISION = "e5-repeated-ladder-v1"
DEFAULT_RUNGS = (4, 8, 12, 16, 20, 26, 32)
DEFAULT_REPETITIONS = 3
DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_MEMORY_LIMIT_BYTES = 2 * 1024**3
CRITERIA = (NUMERICAL_EXACT_CRITERION, NUMERICAL_GLOBAL_PHASE_CRITERION)


def qasm(n: int, gates: Iterable[str], *, classical: Iterable[str] = ()) -> str:
    statements = [
        "OPENQASM 2.0;",
        'include "qelib1.inc";',
        f"qreg q[{n}];",
        *classical,
        *gates,
    ]
    return "\n".join(statements) + "\n"


def source_ref(text: str) -> str:
    return "sha256:" + sha256(text.encode()).hexdigest()


def _case(
    *,
    case_id: str,
    family: str,
    qubits: int,
    expected: str,
    left: list[str],
    right: list[str],
    depth: tuple[int, int],
    gate_set: list[str],
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    memory_limit_bytes: int | None = DEFAULT_MEMORY_LIMIT_BYTES,
    classical: tuple[list[str], list[str]] | None = None,
) -> dict[str, Any]:
    classical = classical or ([], [])
    left_text = qasm(qubits, left, classical=classical[0])
    right_text = qasm(qubits, right, classical=classical[1])
    return {
        "id": case_id,
        "family": family,
        "qubits": qubits,
        "expected": expected,
        "left": left_text,
        "right": right_text,
        "source_refs": [source_ref(left_text), source_ref(right_text)],
        "depth": {"left": depth[0], "right": depth[1]},
        "gate_count": {"left": len(left), "right": len(right)},
        "gate_set": gate_set,
        "timeout_seconds": timeout_seconds,
        "memory_limit_bytes": memory_limit_bytes,
    }


def structured_cases(rungs: Iterable[int] = DEFAULT_RUNGS) -> Iterable[dict[str, Any]]:
    """Yield the supported four-family matrix at every requested rung."""
    for n in rungs:
        swap = [f"swap q[{i}],q[{i + 1}];" for i in range(0, n - 1, 2)]
        swap_rewrite = [
            gate
            for i in range(0, n - 1, 2)
            for gate in (
                f"cx q[{i}],q[{i + 1}];",
                f"cx q[{i + 1}],q[{i}];",
                f"cx q[{i}],q[{i + 1}];",
            )
        ]
        yield _case(
            case_id=f"swap-rewrite-{n}",
            family="disjoint-swap-decomposition",
            qubits=n,
            expected="exact-equivalent",
            left=swap,
            right=swap_rewrite,
            depth=(1, 3),
            gate_set=["swap", "cx"],
        )
        yield _case(
            case_id=f"global-phase-{n}",
            family="pauli-anticommutation",
            qubits=n,
            expected="global-phase-only",
            left=["x q[0];", "z q[0];"],
            right=["z q[0];", "x q[0];"],
            depth=(2, 2),
            gate_set=["x", "z"],
        )
        yield _case(
            case_id=f"altered-gate-{n}",
            family="intentional-single-gate-error",
            qubits=n,
            expected="not-equivalent",
            left=["x q[0];"],
            right=["z q[0];"],
            depth=(1, 1),
            gate_set=["x", "z"],
        )
        ordered = [f"x q[{i}];" for i in range(0, n, 2)]
        ordered += [f"z q[{i}];" for i in range(1, n, 2)]
        yield _case(
            case_id=f"commuting-permutation-{n}",
            family="commuting-operation-order-permutation",
            qubits=n,
            expected="exact-equivalent",
            left=ordered,
            right=list(reversed(ordered)),
            depth=(1, 1),
            gate_set=["x", "z"],
        )


def control_cases() -> Iterable[dict[str, Any]]:
    """Yield fail-closed unsupported and resource-bound controls."""
    dynamic = ["h q[0];", "measure q[0] -> c[0];", "if(c==1) x q[1];"]
    yield _case(
        case_id="unsupported-dynamic-4",
        family="unsupported-mid-circuit-classical-control",
        qubits=4,
        expected="unsupported",
        left=dynamic,
        right=dynamic,
        depth=(3, 3),
        gate_set=["h", "measure", "if"],
        classical=(["creg c[1];"], ["creg c[1];"]),
    )
    noisy = ["bit_flip(0.01) q[0];"]
    yield _case(
        case_id="unsupported-noise-4",
        family="unsupported-noise-instruction",
        qubits=4,
        expected="unsupported",
        left=noisy,
        right=noisy,
        depth=(1, 1),
        gate_set=["bit_flip"],
    )
    n = 26
    deep = [
        gate
        for i in range(300)
        for gate in (f"h q[{i % n}];", f"cx q[{i % n}],q[{(i + 1) % n}];")
    ]
    yield _case(
        case_id="forced-timeout-26",
        family="resource-deadline-control",
        qubits=n,
        expected="blocked",
        left=deep,
        right=deep,
        depth=(600, 600),
        gate_set=["h", "cx"],
        timeout_seconds=1e-9,
    )


def manifest(*, rungs: Iterable[int], repetitions: int) -> dict[str, Any]:
    rungs = tuple(rungs)
    cases = [*structured_cases(rungs), *control_cases()]
    return {
        "schema": "e7q.ir.qcec-benchmark-manifest/v1",
        "runner_revision": RUNNER_REVISION,
        "backend_requirement": "mqt.qcec==3.9.0",
        "rungs": list(rungs),
        "repetitions": repetitions,
        "criteria": [deepcopy(item) for item in CRITERIA],
        "configuration": {
            "nthreads": 1,
            "parallel": False,
            "max_simulations": 4,
            "seed": 7,
            "default_timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
            "default_memory_limit_bytes": DEFAULT_MEMORY_LIMIT_BYTES,
        },
        "cases": [
            {key: value for key, value in case.items() if key not in {"left", "right"}}
            for case in cases
        ],
    }


def expected_status(expected: str, criterion_id: str) -> str:
    if expected == "exact-equivalent":
        return "PASS"
    if expected == "global-phase-only":
        return "PASS" if criterion_id == NUMERICAL_GLOBAL_PHASE_CRITERION["id"] else "FAIL"
    if expected == "not-equivalent":
        return "FAIL"
    if expected == "unsupported":
        return "UNSUPPORTED"
    if expected == "blocked":
        return "BLOCKED"
    raise ValueError(f"unknown benchmark expectation: {expected}")


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    statuses: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    attempts = 0
    matched = 0
    completed = 0
    per_rung: dict[str, dict[str, Any]] = {}
    for case in results:
        rung = per_rung.setdefault(str(case["qubits"]), {
            "cases": 0, "attempts": 0, "expectation_matches": 0,
        })
        rung["cases"] += 1
        for run in case["runs"]:
            attempts += 1
            rung["attempts"] += 1
            outcome = run["assessment"]["payload"]["outcome"]
            statuses[outcome["status"]] += 1
            if outcome["status"] != "PASS":
                reasons[outcome["reason"]] += 1
            if outcome["status"] in {"PASS", "FAIL"}:
                completed += 1
            if run["expectation_match"]:
                matched += 1
                rung["expectation_matches"] += 1
    return {
        "cases": len(results),
        "attempts": attempts,
        "statuses": dict(sorted(statuses.items())),
        "non_pass_reasons": dict(sorted(reasons.items())),
        "completed_decisive_attempts": completed,
        "decisive_completion_rate": completed / attempts if attempts else 0.0,
        "expectation_matches": matched,
        "expectation_match_rate": matched / attempts if attempts else 0.0,
        "per_rung": per_rung,
    }


Evaluator = Callable[..., dict[str, Any]]


def run(
    created_at: str,
    *,
    rungs: Iterable[int] = DEFAULT_RUNGS,
    repetitions: int = DEFAULT_REPETITIONS,
    evaluator: Evaluator = evaluate,
) -> dict[str, Any]:
    if type(repetitions) is not int or repetitions < 1:
        raise ValueError("repetitions must be a positive integer")
    rungs = tuple(rungs)
    if (
        not rungs
        or any(type(rung) is not int or rung < 2 for rung in rungs)
        or tuple(sorted(set(rungs))) != rungs
    ):
        raise ValueError("rungs must be unique increasing integers of at least two qubits")
    corpus_manifest = manifest(rungs=rungs, repetitions=repetitions)
    corpus_id = digest(corpus_manifest)
    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for case in [*structured_cases(rungs), *control_cases()]:
            left_text = case.pop("left")
            right_text = case.pop("right")
            left = root / f"{case['id']}-left.qasm"
            right = root / f"{case['id']}-right.qasm"
            left.write_text(left_text)
            right.write_text(right_text)
            runs = []
            case_repetitions = repetitions if case["expected"] not in {"unsupported", "blocked"} else 1
            for repetition in range(case_repetitions):
                for criterion in CRITERIA:
                    assessment = evaluator(
                        left,
                        right,
                        criterion=criterion,
                        source_refs=tuple(case["source_refs"]),
                        created_at=created_at,
                        timeout_seconds=case["timeout_seconds"],
                        nthreads=1,
                        max_simulations=4,
                        seed=7,
                        memory_limit_bytes=case["memory_limit_bytes"],
                    )
                    actual = assessment["payload"]["outcome"]["status"]
                    expected = expected_status(case["expected"], criterion["id"])
                    runs.append({
                        "repetition": repetition + 1,
                        "criterion_id": criterion["id"],
                        "expected_status": expected,
                        "expectation_match": actual == expected,
                        "evidence_id": assessment["artifact_id"],
                        "assessment": assessment,
                    })
            case["runs"] = runs
            results.append(case)
    report = {
        "schema": SCHEMA,
        "created_at": created_at,
        "corpus_id": corpus_id,
        "manifest": corpus_manifest,
        "scope": "structured evaluation corpus; not arbitrary-circuit scalability",
        "results": results,
    }
    report["summary"] = summarize(results)
    report["report_id"] = digest(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--created-at", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repetitions", type=int, default=DEFAULT_REPETITIONS)
    args = parser.parse_args()
    report = run(args.created_at, repetitions=args.repetitions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_bytes(report) + b"\n")
    print(json.dumps({
        "report_id": report["report_id"],
        "corpus_id": report["corpus_id"],
        **report["summary"],
    }, sort_keys=True))
    return 0 if report["summary"]["expectation_match_rate"] == 1.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
