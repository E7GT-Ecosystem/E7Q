# SPDX-License-Identifier: Apache-2.0
"""Optional, evidence-bearing adapter for MQT QCEC.

The adapter is not part of default F2 conformance.  It records a caller-selected
criterion and the backend's raw verdict without upgrading probabilistic or
resource-limited results to universal equivalence.
"""
from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import resource
from typing import Any, Callable

from .canonical import digest
from .envelope import build_artifact

BACKEND_ID = "mqt.qcec"
SUPPORTED_BACKEND_VERSION = "3.9.0"
NUMERICAL_TOLERANCE = 2.2737367544323206e-13
FIDELITY_THRESHOLD = 1e-8
NUMERICAL_EXACT_CRITERION = {
    "id": "e7q.ir.qcec-numerical-unitary",
    "version": "1",
    "options": {
        "numerical_tolerance": NUMERICAL_TOLERANCE,
        "fidelity_threshold": FIDELITY_THRESHOLD,
        "global_phase": False,
    },
}
NUMERICAL_GLOBAL_PHASE_CRITERION = {
    "id": "e7q.ir.qcec-numerical-global-phase",
    "version": "1",
    "options": {
        "numerical_tolerance": NUMERICAL_TOLERANCE,
        "fidelity_threshold": FIDELITY_THRESHOLD,
        "global_phase": True,
    },
}
SUPPORTED_CRITERIA = {
    NUMERICAL_EXACT_CRITERION["id"]: NUMERICAL_EXACT_CRITERION,
    NUMERICAL_GLOBAL_PHASE_CRITERION["id"]: NUMERICAL_GLOBAL_PHASE_CRITERION,
}
LIMITATIONS = (
    "The optional backend is not default E7Q-IR conformance truth.",
    "MQT QCEC 3.9.0 uses recorded numerical tolerances; its criteria are separate from exact algebraic E7Q-IR criteria.",
    "A probabilistic passing result is inconclusive for universal circuit equivalence.",
    "Timeout, no-information, backend error and unsupported input are not non-equivalence.",
    "No provider authenticity, hardware execution or physical fidelity is established.",
)


def map_verdict(raw_verdict: str, criterion_id: str, *, timed_out: bool = False) -> tuple[str, str]:
    """Map one QCEC verdict without weakening the selected criterion."""
    if criterion_id not in SUPPORTED_CRITERIA:
        return "UNSUPPORTED", "INCONCLUSIVE"
    if raw_verdict == "equivalent":
        return "PASS", "ESTABLISHED"
    if raw_verdict == "equivalent_up_to_global_phase":
        return (
            ("PASS", "ESTABLISHED")
            if criterion_id == NUMERICAL_GLOBAL_PHASE_CRITERION["id"]
            else ("FAIL", "REFUTED")
        )
    if raw_verdict == "not_equivalent":
        return "FAIL", "REFUTED"
    if raw_verdict == "no_information" and timed_out:
        return "BLOCKED", "INCONCLUSIVE"
    if raw_verdict in {
        "no_information",
        "equivalent_up_to_phase",
        "probably_equivalent",
        "probably_not_equivalent",
    }:
        return "NOT_ASSESSED", "INCONCLUSIVE"
    return "NOT_ASSESSED", "INCONCLUSIVE"


def _package_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "unavailable"


def _peak_rss_bytes() -> int:
    # Linux reports KiB. The repository's supported CI/development platform is Linux.
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def _load_verify() -> Callable[..., Any]:
    try:
        from mqt.qcec import verify
    except (ImportError, OSError) as exc:
        raise RuntimeError("optional backend mqt.qcec is unavailable") from exc
    return verify


def evaluate(
    left: str | Path,
    right: str | Path,
    *,
    criterion: dict[str, Any],
    source_refs: tuple[str, str],
    created_at: str,
    timeout_seconds: float,
    nthreads: int = 1,
    max_simulations: int = 16,
    seed: int = 0,
    memory_limit_bytes: int | None = None,
    verify_backend: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Run the optional backend and return an E7Q-IR assessment artifact.

    ``memory_limit_bytes`` is recorded but not enforced by QCEC. Callers that
    require hard memory isolation must execute this adapter in a constrained
    subprocess or container.
    """
    if criterion not in SUPPORTED_CRITERIA.values():
        raise ValueError("an exact supported criterion object must be selected explicitly")
    if (
        not isinstance(timeout_seconds, (int, float))
        or isinstance(timeout_seconds, bool)
        or timeout_seconds <= 0
    ):
        raise ValueError("timeout_seconds must be positive")
    if type(nthreads) is not int or nthreads < 1:
        raise ValueError("nthreads must be a positive integer")
    if type(max_simulations) is not int or max_simulations < 0:
        raise ValueError("max_simulations must be a non-negative integer")
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    if memory_limit_bytes is not None and (
        type(memory_limit_bytes) is not int or memory_limit_bytes <= 0
    ):
        raise ValueError("memory_limit_bytes must be positive when supplied")
    if len(source_refs) != 2 or any(not isinstance(ref, str) for ref in source_refs):
        raise ValueError("source_refs must identify exactly two circuit artifacts")

    configuration = {
        "timeout_seconds": float(timeout_seconds),
        "nthreads": nthreads,
        "parallel": False,
        "max_simulations": max_simulations,
        "seed": seed,
        "memory_limit_bytes": memory_limit_bytes,
        "numerical_tolerance": NUMERICAL_TOLERANCE,
        "fidelity_threshold": FIDELITY_THRESHOLD,
    }
    backend = {
        "id": BACKEND_ID,
        "version": _package_version("mqt.qcec"),
        "dependency_versions": {"mqt.core": _package_version("mqt.core")},
        "license": "MIT",
    }
    raw_result: dict[str, Any] = {}
    error: dict[str, str] | None = None
    error_status: str | None = None
    before_rss = _peak_rss_bytes()
    try:
        runner = verify_backend or _load_verify()
        result = runner(
            left,
            right,
            timeout=float(timeout_seconds),
            nthreads=nthreads,
            parallel=False,
            max_sims=max_simulations,
            seed=seed,
            numerical_tolerance=NUMERICAL_TOLERANCE,
            fidelity_threshold=FIDELITY_THRESHOLD,
        )
        raw_result = dict(result.json())
        raw_verdict = str(raw_result.get("equivalence", "no_information"))
    except (ValueError, TypeError) as exc:
        raw_verdict = "unsupported_input"
        error_status = "UNSUPPORTED"
        error = {"type": type(exc).__name__, "message": str(exc)}
    except (RuntimeError, OSError) as exc:
        raw_verdict = "backend_error"
        error = {"type": type(exc).__name__, "message": str(exc)}
    peak_rss = max(before_rss, _peak_rss_bytes())
    check_time = raw_result.get("check_time")
    timed_out = (
        raw_verdict == "no_information"
        and isinstance(check_time, (int, float))
        and check_time >= timeout_seconds
    )
    status, conclusion = map_verdict(raw_verdict, criterion["id"], timed_out=timed_out)
    if error_status is not None or (error is not None and "unavailable" in error["message"]):
        status, conclusion = "UNSUPPORTED", "INCONCLUSIVE"
    if backend["version"] not in {SUPPORTED_BACKEND_VERSION, "unavailable"}:
        status, conclusion = "UNSUPPORTED", "INCONCLUSIVE"

    payload: dict[str, Any] = {
        "format": "e7q.ir.external-equivalence-assessment/v1",
        "criterion": dict(criterion),
        "backend": backend,
        "configuration": configuration,
        "method": {
            "kind": "tolerance-based-numerical",
            "exact_algebraic": False,
            "backend_checkers": [
                item.get("checker")
                for item in raw_result.get("checkers", [])
                if isinstance(item, dict) and isinstance(item.get("checker"), str)
            ],
        },
        "outcome": {
            "status": status,
            "conclusion": conclusion,
            "raw_verdict": raw_verdict,
            "timed_out": timed_out,
            "universal_equivalence_established": status == "PASS",
        },
        "resource_use": {
            "preprocessing_seconds": raw_result.get("preprocessing_time"),
            "checking_seconds": check_time,
            "process_peak_rss_bytes": peak_rss,
            "memory_measurement_scope": "whole-adapter-process-peak-not-per-check-delta",
            "memory_limit_enforced": False,
        },
        "raw_result": raw_result,
        "assumptions": [
            "input-and-output-permutations-follow-the-pinned-backend-configuration",
            "global-phase-meaning-follows-the-selected-e7q-ir-criterion",
            "numerical-tolerances-are-part-of-the-recorded-method",
        ],
    }
    if error is not None:
        payload["error"] = error
    payload["assessment_id"] = digest(payload)
    return build_artifact(
        "assessment",
        payload,
        profile_id="e7q.ir.external-equivalence-assessment",
        profile_version="1",
        capabilities_required=("mqt-qcec-optional-backend",),
        created_at=created_at,
        actor="e7q.ir.qcec-adapter",
        source_refs=source_refs,
        limitations=LIMITATIONS,
    )
