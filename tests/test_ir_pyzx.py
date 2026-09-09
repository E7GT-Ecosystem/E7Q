# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
from pathlib import Path
import time

import pytest

from e7q.ir.canonical import digest
from e7q.ir.pyzx import EXACT_CRITERION, GLOBAL_PHASE_CRITERION, evaluate

STAMP = "2026-09-09T00:00:00Z"
REFS = ("sha256:" + "1" * 64, "sha256:" + "2" * 64)
ROOT = Path(__file__).resolve().parents[1]


def qasm(gates, *, width=4, measurement=True):
    lines = [
        "OPENQASM 2.0;",
        'include "qelib1.inc";',
        f"qreg q[{width}];",
        f"creg c[{width}];",
        *gates,
    ]
    if measurement:
        lines.append("measure q -> c;")
    return "\n".join(lines) + "\n"


def verified_backend(left, right, global_phase):
    assert "measure" not in left
    assert "measure" not in right
    return True


def inconclusive_backend(left, right, global_phase):
    return None


def false_backend(left, right, global_phase):
    return False


def phase_observer_backend(left, right, global_phase):
    return global_phase


def sleeping_backend(left, right, global_phase):
    time.sleep(10)
    return True


def exhausted_backend(left, right, global_phase):
    raise MemoryError("bounded allocation denied")


def write_pair(tmp_path, left_gates=("h q[0];",), right_gates=("h q[0];",), **kwargs):
    left = tmp_path / "left.qasm"
    right = tmp_path / "right.qasm"
    left.write_text(qasm(left_gates, **kwargs))
    right.write_text(qasm(right_gates, **kwargs))
    return left, right


def assess(tmp_path, backend, criterion=EXACT_CRITERION, **kwargs):
    left, right = write_pair(tmp_path)
    return evaluate(
        left,
        right,
        criterion=criterion,
        source_refs=REFS,
        created_at=STAMP,
        verify_backend=backend,
        **kwargs,
    )


def test_verified_rewrite_passes_only_the_selected_named_criterion(tmp_path):
    artifact = assess(tmp_path, verified_backend)
    payload = artifact["payload"]
    assert payload["criterion"] == EXACT_CRITERION
    assert payload["method"] == {
        "kind": "zx-calculus-rewrite-reduction",
        "exact_algebraic": False,
        "returns_counterexample": False,
    }
    assert payload["outcome"]["status"] == "PASS"
    assert payload["outcome"]["raw_verdict"] == "verified"
    assert payload["configuration"]["up_to_swaps"] is False
    assert payload["projection"]["terminal_identity_measurement_removed"] is True
    assert payload["worker"]["reaped"] is True
    assert any("one-sided" in item for item in payload["assumptions"])


def test_exact_and_global_phase_options_are_not_collapsed(tmp_path):
    exact = assess(tmp_path, phase_observer_backend, EXACT_CRITERION)
    phase = assess(tmp_path, phase_observer_backend, GLOBAL_PHASE_CRITERION)
    assert exact["payload"]["outcome"]["status"] == "NOT_ASSESSED"
    assert phase["payload"]["outcome"]["status"] == "PASS"


@pytest.mark.parametrize("backend", [inconclusive_backend, false_backend])
def test_failed_or_absent_reduction_is_always_inconclusive(tmp_path, backend):
    artifact = assess(tmp_path, backend)
    outcome = artifact["payload"]["outcome"]
    assert outcome["status"] == "NOT_ASSESSED"
    assert outcome["conclusion"] == "INCONCLUSIVE"
    assert outcome["universal_equivalence_established"] is False


def test_dynamic_nonterminal_and_missing_measurement_fail_before_worker(tmp_path):
    left, right = write_pair(
        tmp_path,
        left_gates=("measure q[0] -> c[0];", "x q[0];"),
    )
    artifact = evaluate(
        left, right, criterion=EXACT_CRITERION, source_refs=REFS,
        created_at=STAMP, verify_backend=verified_backend,
    )
    assert artifact["payload"]["outcome"]["status"] == "UNSUPPORTED"
    assert artifact["payload"]["worker"]["started"] is False


def test_pair_width_mismatch_fails_before_worker(tmp_path):
    left, right = write_pair(tmp_path)
    right.write_text(qasm(("h q[0];",), width=5))
    artifact = evaluate(
        left, right, criterion=EXACT_CRITERION, source_refs=REFS,
        created_at=STAMP, verify_backend=verified_backend,
    )
    assert artifact["payload"]["outcome"]["status"] == "UNSUPPORTED"
    assert artifact["payload"]["worker"]["started"] is False
    assert artifact["payload"]["input_errors"] == [{
        "role": "pair",
        "status": "UNSUPPORTED",
        "message": "left and right quantum register widths differ",
    }]

    left.write_text(qasm(("h q[0];",), measurement=False))
    artifact = evaluate(
        left, right, criterion=EXACT_CRITERION, source_refs=REFS,
        created_at=STAMP, verify_backend=verified_backend,
    )
    assert artifact["payload"]["outcome"]["status"] == "UNSUPPORTED"
    assert artifact["payload"]["worker"]["started"] is False


def test_timeout_and_memory_exhaustion_are_blocked_and_reaped(tmp_path):
    timeout = assess(tmp_path, sleeping_backend, timeout_seconds=0.05)
    assert timeout["payload"]["outcome"]["status"] == "BLOCKED"
    assert timeout["payload"]["outcome"]["reason"] == "wall_clock_timeout"
    assert timeout["payload"]["worker"]["reaped"] is True

    exhausted = assess(tmp_path, exhausted_backend)
    assert exhausted["payload"]["outcome"]["status"] == "BLOCKED"
    assert exhausted["payload"]["outcome"]["reason"] == "resource_exhaustion"
    assert exhausted["payload"]["worker"]["reaped"] is True


def test_invalid_criterion_limits_and_refs_are_rejected(tmp_path):
    left, right = write_pair(tmp_path)
    with pytest.raises(ValueError, match="criterion"):
        evaluate(left, right, criterion={"id": "wrong"}, source_refs=REFS, created_at=STAMP)
    with pytest.raises(ValueError, match="timeout"):
        evaluate(left, right, criterion=EXACT_CRITERION, source_refs=REFS, created_at=STAMP, timeout_seconds=0)
    with pytest.raises(ValueError, match="memory"):
        evaluate(left, right, criterion=EXACT_CRITERION, source_refs=REFS, created_at=STAMP, memory_limit_bytes=True)
    with pytest.raises(ValueError, match="source_refs"):
        evaluate(left, right, criterion=EXACT_CRITERION, source_refs=("one",), created_at=STAMP)


def test_published_pyzx_evaluation_retains_one_sided_outcomes():
    report = json.loads(
        (ROOT / "benchmarks/e7q-ir/pyzx-0.10.6-results.json").read_text()
    )
    assert report["schema"] == "e7q.ir.pyzx-benchmark/v1"
    assert report["backend_requirement"] == "pyzx==0.10.6"
    assert report["summary"] == {
        "attempts": 8,
        "cases": 4,
        "expectation_matches": 8,
        "statuses": {"BLOCKED": 2, "NOT_ASSESSED": 3, "PASS": 3},
    }
    assert digest({key: value for key, value in report.items() if key != "report_id"}) == report["report_id"]
    assert all(
        run["evidence_id"] == run["assessment"]["artifact_id"]
        and run["assessment"]["payload"]["worker"]["reaped"] is True
        for case in report["results"] for run in case["runs"]
    )
    altered = next(case for case in report["results"] if case["id"] == "altered-gate-26")
    assert {run["assessment"]["payload"]["outcome"]["status"] for run in altered["runs"]} == {
        "NOT_ASSESSED"
    }
