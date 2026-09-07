# SPDX-License-Identifier: Apache-2.0
"""Optional, evidence-bearing adapter for MQT QCEC.

The adapter is not part of default F2 conformance. It records a caller-selected
criterion and the backend's raw verdict without upgrading probabilistic or
resource-limited results to universal equivalence.
"""
from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
import multiprocessing
from multiprocessing.connection import Connection
from pathlib import Path
import signal
import sys
import time
from typing import Any, Callable

try:
    import resource
except ImportError:  # pragma: no cover - unavailable on Windows
    resource = None  # type: ignore[assignment]

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
    "Timeout, resource exhaustion, worker failure, no-information, backend error and unsupported input are not non-equivalence.",
    "No provider authenticity, hardware execution or physical fidelity is established.",
)
_WORKER_STOP_GRACE_SECONDS = 1.0
_WORKER_POLL_SECONDS = 0.02


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


def _peak_rss_bytes() -> int | None:
    if resource is None:
        return None
    peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    # Linux reports KiB; macOS and the BSDs report bytes.
    return peak * 1024 if sys.platform.startswith("linux") else peak


def _load_verify() -> Callable[..., Any]:
    try:
        from mqt.qcec import verify
    except (ImportError, OSError) as exc:
        raise RuntimeError("optional backend mqt.qcec is unavailable") from exc
    return verify


def _memory_enforcement(requested_bytes: int | None) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "requested_bytes": requested_bytes,
        "enforced": False,
        "mechanism": "not-requested" if requested_bytes is None else "unsupported",
        "effective_bytes": None,
    }
    if requested_bytes is None:
        return metadata
    if resource is None or not hasattr(resource, "RLIMIT_AS"):
        metadata["detail"] = "RLIMIT_AS is unavailable on this platform"
        return metadata
    try:
        old_soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        infinity = resource.RLIM_INFINITY
        candidates = [requested_bytes]
        if old_soft != infinity:
            candidates.append(int(old_soft))
        if hard != infinity:
            candidates.append(int(hard))
        effective = min(candidates)
        # The worker is disposable, so lower both bounds to prevent backend code
        # from raising its own soft limit before native allocation.
        resource.setrlimit(resource.RLIMIT_AS, (effective, effective))
        new_soft, new_hard = resource.getrlimit(resource.RLIMIT_AS)
    except (OSError, ValueError) as exc:
        metadata["detail"] = f"{type(exc).__name__}: {exc}"
        return metadata
    metadata.update({
        "enforced": True,
        "mechanism": "posix-rlimit-as",
        "effective_bytes": effective if new_soft == infinity else int(new_soft),
        "soft_limit_bytes": effective if new_soft == infinity else int(new_soft),
        "hard_limit_bytes": effective if new_hard == infinity else int(new_hard),
    })
    return metadata


def _worker_send(connection: Connection, message: dict[str, Any]) -> None:
    try:
        connection.send(message)
    except (BrokenPipeError, EOFError, OSError):
        pass


def _qcec_worker(connection: Connection, request: dict[str, Any]) -> None:
    """Apply worker-local limits and execute one backend call."""
    memory = _memory_enforcement(request["memory_limit_bytes"])
    _worker_send(connection, {
        "kind": "worker_started",
        "memory_limit": memory,
        "worker_peak_rss_bytes": _peak_rss_bytes(),
    })
    response: dict[str, Any]
    try:
        runner = request["verify_backend"] or _load_verify()
        result = runner(
            request["left"],
            request["right"],
            timeout=request["timeout_seconds"],
            nthreads=request["nthreads"],
            parallel=False,
            max_sims=request["max_simulations"],
            seed=request["seed"],
            numerical_tolerance=NUMERICAL_TOLERANCE,
            fidelity_threshold=FIDELITY_THRESHOLD,
        )
        serialized = result.json()
        protocol_message: str | None = None
        if not isinstance(serialized, dict):
            protocol_message = "backend result.json() must return a mapping"
        elif not isinstance(serialized.get("equivalence", "no_information"), str):
            protocol_message = "backend equivalence must be a string"
        elif not isinstance(serialized.get("checkers", []), list):
            protocol_message = "backend checkers must be a list"
        elif any(not isinstance(item, dict) for item in serialized.get("checkers", [])):
            protocol_message = "every backend checker result must be a mapping"
        elif any(
            item.get("checker") is not None and not isinstance(item.get("checker"), str)
            for item in serialized.get("checkers", [])
        ):
            protocol_message = "backend checker identifiers must be strings"
        if protocol_message is not None:
            response = {
                "kind": "worker_protocol_error",
                "error": {"type": "TypeError", "message": protocol_message},
            }
        else:
            response = {"kind": "result", "raw_result": dict(serialized)}
    except MemoryError as exc:
        response = {
            "kind": "resource_exhaustion",
            "error": {"type": type(exc).__name__, "message": str(exc)},
        }
    except (ValueError, TypeError) as exc:
        response = {
            "kind": "unsupported_input",
            "error": {"type": type(exc).__name__, "message": str(exc)},
        }
    except (RuntimeError, OSError) as exc:
        response = {
            "kind": "backend_error",
            "error": {"type": type(exc).__name__, "message": str(exc)},
        }
    except Exception as exc:  # fail closed without losing an unexpected backend exception
        response = {
            "kind": "backend_error",
            "error": {"type": type(exc).__name__, "message": str(exc)},
        }
    response["memory_limit"] = memory
    response["worker_peak_rss_bytes"] = _peak_rss_bytes()
    _worker_send(connection, response)
    connection.close()


def _signal_metadata(exit_code: int | None) -> tuple[int | None, str | None]:
    if exit_code is None or exit_code >= 0:
        return None, None
    number = -exit_code
    try:
        name = signal.Signals(number).name
    except ValueError:
        name = None
    return number, name


def _terminate_and_reap(process: multiprocessing.Process) -> tuple[str | None, bool]:
    mechanism: str | None = None
    if process.is_alive():
        mechanism = "terminate"
        process.terminate()
        process.join(_WORKER_STOP_GRACE_SECONDS)
    if process.is_alive():
        mechanism = "kill"
        process.kill()
        process.join(_WORKER_STOP_GRACE_SECONDS)
    if process.is_alive():  # defensive final wait; kill should make this bounded in practice
        process.join(_WORKER_STOP_GRACE_SECONDS)
    return mechanism, not process.is_alive()


def _run_isolated(request: dict[str, Any]) -> dict[str, Any]:
    context = multiprocessing.get_context("spawn")
    receiving, sending = context.Pipe(duplex=False)
    process = context.Process(
        target=_qcec_worker,
        args=(sending, request),
        name="e7q-qcec-worker",
    )
    started = time.monotonic()
    try:
        process.start()
    except Exception as exc:
        receiving.close()
        sending.close()
        return {
            "reason": "worker_start_error",
            "error": {"type": type(exc).__name__, "message": str(exc)},
            "wall_clock_seconds": time.monotonic() - started,
            "worker": {
                "start_method": "spawn",
                "started": False,
                "pid": None,
                "exit_code": None,
                "signal": None,
                "signal_name": None,
                "termination_mechanism": None,
                "reaped": True,
            },
            "memory_limit": {
                "requested_bytes": request["memory_limit_bytes"],
                "enforced": False,
                "mechanism": "worker-not-started",
                "effective_bytes": None,
            },
            "worker_peak_rss_bytes": None,
        }
    sending.close()
    deadline = started + request["timeout_seconds"]
    startup: dict[str, Any] | None = None
    response: dict[str, Any] | None = None
    timed_out = False
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = process.is_alive()
                break
            if receiving.poll(min(_WORKER_POLL_SECONDS, remaining)):
                try:
                    message = receiving.recv()
                except EOFError:
                    break
                if isinstance(message, dict) and message.get("kind") == "worker_started":
                    startup = message
                elif isinstance(message, dict):
                    response = message
                else:
                    response = {"kind": "worker_protocol_error", "error": {
                        "type": "TypeError", "message": "worker response must be a mapping",
                    }}
            if not process.is_alive():
                break
        if not timed_out:
            remaining = max(0.0, deadline - time.monotonic())
            process.join(remaining)
            timed_out = process.is_alive()
    finally:
        receiving.close()
    termination_mechanism = None
    if timed_out:
        termination_mechanism, reaped = _terminate_and_reap(process)
    else:
        process.join()
        reaped = not process.is_alive()
    exit_code = process.exitcode
    signal_number, signal_name = _signal_metadata(exit_code)
    worker = {
        "start_method": "spawn",
        "started": True,
        "pid": process.pid,
        "exit_code": exit_code,
        "signal": signal_number,
        "signal_name": signal_name,
        "termination_mechanism": termination_mechanism,
        "reaped": reaped,
    }
    if reaped:
        process.close()
    memory = (
        (response or {}).get("memory_limit")
        or (startup or {}).get("memory_limit")
        or {
            "requested_bytes": request["memory_limit_bytes"],
            "enforced": False,
            "mechanism": "worker-did-not-report",
            "effective_bytes": None,
        }
    )
    peak_rss = (
        (response or {}).get("worker_peak_rss_bytes")
        or (startup or {}).get("worker_peak_rss_bytes")
    )
    base = {
        "wall_clock_seconds": time.monotonic() - started,
        "worker": worker,
        "memory_limit": memory,
        "worker_peak_rss_bytes": peak_rss,
    }
    if timed_out:
        return {**base, "reason": "wall_clock_timeout", "error": {
            "type": "TimeoutError",
            "message": "isolated QCEC worker exceeded the parent-owned wall-clock deadline",
        }}
    if not reaped:
        return {**base, "reason": "worker_reap_failure", "error": {
            "type": "RuntimeError", "message": "isolated QCEC worker could not be reaped",
        }}
    if exit_code is not None and exit_code < 0:
        return {**base, "reason": "worker_signal", "error": {
            "type": "WorkerSignalError",
            "message": f"isolated QCEC worker terminated by signal {signal_number}",
        }}
    if exit_code not in {0, None}:
        return {**base, "reason": "worker_crash", "error": {
            "type": "WorkerProcessError",
            "message": f"isolated QCEC worker exited with code {exit_code}",
        }}
    if response is None:
        return {**base, "reason": "worker_protocol_error", "error": {
            "type": "EOFError", "message": "isolated QCEC worker exited without a result",
        }}
    return {**base, **response, "reason": response["kind"]}


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
    """Run one optional-backend check in an isolated, bounded worker process.

    Test or integration backends supplied through ``verify_backend`` must be
    importable and pickleable by Python's ``spawn`` multiprocessing context.
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
    execution = _run_isolated({
        "left": left,
        "right": right,
        "timeout_seconds": float(timeout_seconds),
        "nthreads": nthreads,
        "max_simulations": max_simulations,
        "seed": seed,
        "memory_limit_bytes": memory_limit_bytes,
        "verify_backend": verify_backend,
    })
    reason = execution["reason"]
    raw_result: dict[str, Any] = execution.get("raw_result", {})
    error: dict[str, str] | None = execution.get("error")
    check_time = raw_result.get("check_time")
    backend_timed_out = (
        reason == "result"
        and str(raw_result.get("equivalence", "no_information")) == "no_information"
        and isinstance(check_time, (int, float))
        and check_time >= timeout_seconds
    )
    if reason == "result":
        raw_verdict = str(raw_result.get("equivalence", "no_information"))
        status, conclusion = map_verdict(
            raw_verdict, criterion["id"], timed_out=backend_timed_out,
        )
        outcome_reason = "backend_timeout" if backend_timed_out else "backend_verdict"
    elif reason == "unsupported_input":
        raw_verdict = "unsupported_input"
        status, conclusion = "UNSUPPORTED", "INCONCLUSIVE"
        outcome_reason = reason
    elif reason in {"wall_clock_timeout", "resource_exhaustion"}:
        raw_verdict = reason
        status, conclusion = "BLOCKED", "INCONCLUSIVE"
        outcome_reason = reason
    else:
        raw_verdict = reason
        status, conclusion = "NOT_ASSESSED", "INCONCLUSIVE"
        outcome_reason = reason
    if reason == "backend_error" and error is not None and "unavailable" in error["message"]:
        status, conclusion = "UNSUPPORTED", "INCONCLUSIVE"
        outcome_reason = "backend_unavailable"
    if (
        reason == "result"
        and backend["version"] not in {SUPPORTED_BACKEND_VERSION, "unavailable"}
    ):
        status, conclusion = "UNSUPPORTED", "INCONCLUSIVE"
        outcome_reason = "unsupported_backend_version"

    memory = execution["memory_limit"]
    worker = execution["worker"]
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
            "reason": outcome_reason,
            "timed_out": reason == "wall_clock_timeout" or backend_timed_out,
            "resource_exhausted": reason == "resource_exhaustion",
            "universal_equivalence_established": status == "PASS",
        },
        "resource_use": {
            "preprocessing_seconds": raw_result.get("preprocessing_time"),
            "checking_seconds": check_time,
            "wall_clock_seconds": execution["wall_clock_seconds"],
            "wall_clock_limit_enforced": worker["started"],
            "wall_clock_limit_mechanism": "parent-process-monotonic-deadline",
            "worker_peak_rss_bytes": execution["worker_peak_rss_bytes"],
            "memory_measurement_scope": "isolated-worker-process-peak",
            "memory_limit_requested_bytes": memory["requested_bytes"],
            "memory_limit_enforced": memory["enforced"],
            "memory_limit_mechanism": memory["mechanism"],
            "memory_limit_effective_bytes": memory["effective_bytes"],
            "memory_limit_soft_bytes": memory.get("soft_limit_bytes"),
            "memory_limit_hard_bytes": memory.get("hard_limit_bytes"),
        },
        "worker": worker,
        "raw_result": raw_result,
        "assumptions": [
            "input-and-output-permutations-follow-the-pinned-backend-configuration",
            "global-phase-meaning-follows-the-selected-e7q-ir-criterion",
            "numerical-tolerances-are-part-of-the-recorded-method",
        ],
    }
    if memory.get("detail") is not None:
        payload["resource_use"]["memory_limit_detail"] = memory["detail"]
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
