# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from e7q.ir.canonical import digest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "benchmark_qcec", ROOT / "scripts" / "benchmark_qcec.py",
)
assert SPEC is not None and SPEC.loader is not None
benchmark = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(benchmark)


def fake_evaluator(left, right, *, criterion, source_refs, created_at, **configuration):
    case_id = Path(left).stem.removesuffix("-left")
    if case_id.startswith("global-phase"):
        status = "PASS" if criterion["options"]["global_phase"] else "FAIL"
        reason = "backend_verdict"
    elif case_id.startswith("altered-gate"):
        status, reason = "FAIL", "backend_verdict"
    elif case_id.startswith("unsupported"):
        status, reason = "UNSUPPORTED", "unsupported_input"
    elif case_id.startswith("forced-timeout"):
        status, reason = "BLOCKED", "wall_clock_timeout"
    else:
        status, reason = "PASS", "backend_verdict"
    payload = {
        "criterion": criterion,
        "outcome": {
            "status": status,
            "conclusion": "ESTABLISHED" if status == "PASS" else "INCONCLUSIVE",
            "reason": reason,
        },
        "configuration": configuration,
        "source_refs": list(source_refs),
        "created_at": created_at,
    }
    return {"artifact_id": digest(payload), "payload": payload}


def test_manifest_is_stable_and_covers_every_required_rung_and_family():
    manifest = benchmark.manifest(
        rungs=benchmark.DEFAULT_RUNGS,
        repetitions=benchmark.DEFAULT_REPETITIONS,
    )
    assert manifest["rungs"] == [4, 8, 12, 16, 20, 26, 32]
    structured = [
        case for case in manifest["cases"]
        if case["expected"] not in {"unsupported", "blocked"}
    ]
    assert len(structured) == 4 * len(benchmark.DEFAULT_RUNGS)
    assert {case["family"] for case in structured} == {
        "disjoint-swap-decomposition",
        "pauli-anticommutation",
        "intentional-single-gate-error",
        "commuting-operation-order-permutation",
    }
    assert all("source_refs" in case and len(case["source_refs"]) == 2 for case in structured)
    assert digest(manifest) == digest(benchmark.manifest(
        rungs=benchmark.DEFAULT_RUNGS,
        repetitions=benchmark.DEFAULT_REPETITIONS,
    ))


def test_run_repeats_supported_cases_and_retains_every_control_outcome():
    report = benchmark.run(
        "2026-09-09T00:00:00Z",
        rungs=(4, 8),
        repetitions=3,
        evaluator=fake_evaluator,
    )
    assert report["schema"] == benchmark.SCHEMA
    assert report["summary"]["cases"] == 11
    assert report["summary"]["attempts"] == 54
    assert report["summary"]["expectation_match_rate"] == 1.0
    assert report["summary"]["statuses"] == {
        "BLOCKED": 2, "FAIL": 18, "PASS": 30, "UNSUPPORTED": 4,
    }
    assert report["summary"]["non_pass_reasons"] == {
        "backend_verdict": 18,
        "unsupported_input": 4,
        "wall_clock_timeout": 2,
    }
    supported = [
        case for case in report["results"]
        if case["expected"] not in {"unsupported", "blocked"}
    ]
    assert all(len(case["runs"]) == 6 for case in supported)
    assert all(run["evidence_id"] == run["assessment"]["artifact_id"]
               for case in report["results"] for run in case["runs"])
    assert digest({key: value for key, value in report.items() if key != "report_id"}) == report["report_id"]


def test_invalid_repetition_and_rung_requests_fail_closed():
    for repetitions in (0, -1, True):
        try:
            benchmark.run("2026-09-09T00:00:00Z", repetitions=repetitions)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid repetitions must be rejected")
    for rungs in ((), (1,), (4, "8"), (8, 4), (4, 4)):
        try:
            benchmark.run("2026-09-09T00:00:00Z", rungs=rungs)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid rungs must be rejected")


def test_published_repeated_ladder_is_internally_consistent():
    path = ROOT / "benchmarks" / "e7q-ir" / "qcec-e5-repeated-ladder-results.json"
    assert path.exists()
    report = json.loads(path.read_text())
    assert report["schema"] == benchmark.SCHEMA
    assert report["manifest"]["rungs"] == [4, 8, 12, 16, 20, 26, 32]
    assert report["manifest"]["repetitions"] == 3
    assert report["summary"] == benchmark.summarize(report["results"])
    assert report["summary"]["expectation_match_rate"] == 1.0
    assert digest(report["manifest"]) == report["corpus_id"]
    assert digest({key: value for key, value in report.items() if key != "report_id"}) == report["report_id"]
    for case in report["results"]:
        expected_runs = 2 if case["expected"] in {"unsupported", "blocked"} else 6
        assert len(case["runs"]) == expected_runs
        for run in case["runs"]:
            assert run["evidence_id"] == run["assessment"]["artifact_id"]
            outcome = run["assessment"]["payload"]["outcome"]
            assert outcome["status"] == run["expected_status"]
            assert outcome["conclusion"] == (
                "ESTABLISHED" if outcome["status"] == "PASS"
                else "REFUTED" if outcome["status"] == "FAIL"
                else "INCONCLUSIVE"
            )
            assert run["assessment"]["payload"]["worker"]["reaped"] is True
            if outcome["status"] in {"PASS", "FAIL"}:
                resource = run["assessment"]["payload"]["resource_use"]
                assert resource["memory_limit_enforced"] is True
                assert resource["memory_limit_effective_bytes"] == benchmark.DEFAULT_MEMORY_LIMIT_BYTES
                assert resource["worker_peak_rss_bytes"] > 0
