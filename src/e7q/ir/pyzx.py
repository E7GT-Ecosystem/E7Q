# SPDX-License-Identifier: Apache-2.0
"""Optional, fail-closed PyZX rewrite-equality evidence adapter."""
from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from hashlib import sha256
import multiprocessing
from multiprocessing.connection import Connection
from pathlib import Path
import time
from typing import Any, Callable

from ..language import E7QError
from ..openqasm2 import import_openqasm2
from .canonical import digest
from .envelope import build_artifact
from .qcec import (
    _memory_enforcement,
    _peak_rss_bytes,
    _signal_metadata,
    _terminate_and_reap,
)

BACKEND_ID = "pyzx"
SUPPORTED_BACKEND_VERSION = "0.10.6"
EXACT_CRITERION = {
    "id": "e7q.ir.pyzx-rewrite-unitary",
    "version": "1",
    "options": {"up_to_swaps": False, "up_to_global_phase": False},
}
GLOBAL_PHASE_CRITERION = {
    "id": "e7q.ir.pyzx-rewrite-global-phase",
    "version": "1",
    "options": {"up_to_swaps": False, "up_to_global_phase": True},
}
SUPPORTED_CRITERIA = {
    EXACT_CRITERION["id"]: EXACT_CRITERION,
    GLOBAL_PHASE_CRITERION["id"]: GLOBAL_PHASE_CRITERION,
}
MAX_SOURCE_BYTES = 262_144
MAX_QUBITS = 64
MAX_GATES = 2048
LIMITATIONS = (
    "PyZX rewrite success is optional backend evidence, not default E7Q-IR conformance truth.",
    "A failed reduction is inconclusive and never establishes non-equivalence.",
    "The admitted domain is bounded static noiseless OpenQASM 2 with terminal identity measurement projected away.",
    "Input/output swaps are disabled; global phase follows the selected criterion.",
    "No provider authenticity, hardware execution, physical fidelity or arbitrary scalability is established.",
)
_POLL_SECONDS = 0.02


def _package_version() -> str:
    try:
        return version("pyzx")
    except PackageNotFoundError:
        return "unavailable"


def _read(path: str | Path, role: str) -> str:
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise E7QError(f"cannot read {role} circuit: {exc}") from exc
    if len(raw) > MAX_SOURCE_BYTES:
        raise E7QError(f"{role} circuit exceeds the {MAX_SOURCE_BYTES}-byte budget")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise E7QError(f"{role} circuit is not UTF-8") from exc


def _admit(
    source: str, role: str,
) -> tuple[str | None, int | None, dict[str, Any] | None]:
    try:
        parsed = import_openqasm2(source, name=f"PyZX {role}")
    except E7QError as exc:
        return None, None, {"role": role, "status": "UNSUPPORTED", "message": str(exc)}
    qregs = parsed["registers"]["quantum"]
    cregs = parsed["registers"]["classical"]
    if len(qregs) != 1 or len(cregs) != 1:
        return None, None, {"role": role, "status": "UNSUPPORTED", "message": "exactly one quantum and one classical register are required"}
    qwidth, cwidth = int(qregs[0]["width"]), int(cregs[0]["width"])
    if qwidth > MAX_QUBITS:
        return None, None, {"role": role, "status": "BLOCKED", "message": f"circuit exceeds the {MAX_QUBITS}-qubit adapter budget"}
    if qwidth != cwidth:
        return None, None, {"role": role, "status": "UNSUPPORTED", "message": "quantum and classical register widths differ"}
    if parsed["language"]["includes"] != ["qelib1.inc"]:
        return None, None, {"role": role, "status": "UNSUPPORTED", "message": "only qelib1.inc is admitted"}
    gates: list[str] = []
    measurements: list[tuple[int, int]] = []
    measurement_started = False
    for operation in parsed["operations"]:
        name = str(operation["name"])
        if name == "measure":
            measurement_started = True
            measurements.append((
                int(operation["qubits"][0]["index"]),
                int(operation["clbits"][0]["index"]),
            ))
            continue
        if measurement_started:
            return None, None, {"role": role, "status": "UNSUPPORTED", "message": "measurements must be terminal"}
        if name == "barrier" or operation.get("condition") is not None:
            return None, None, {"role": role, "status": "UNSUPPORTED", "message": "barriers and classical control are outside the adapter domain"}
        parameters = operation.get("parameters", [])
        parameter_text = f"({','.join(parameters)})" if parameters else ""
        operands = ",".join(
            f"q[{int(item['index'])}]" for item in operation["qubits"]
        )
        gates.append(f"{name}{parameter_text} {operands};")
    if len(gates) > MAX_GATES:
        return None, None, {"role": role, "status": "BLOCKED", "message": f"unitary prefix exceeds the {MAX_GATES}-gate adapter budget"}
    if measurements != [(index, index) for index in range(qwidth)]:
        return None, None, {"role": role, "status": "UNSUPPORTED", "message": "terminal measurement must map q[i] to c[i] exactly once in ascending order"}
    projection = "\n".join((
        "OPENQASM 2.0;",
        'include "qelib1.inc";',
        f"qreg q[{qwidth}];",
        *gates,
        "",
    ))
    return projection, qwidth, None


def _load_verify() -> Callable[[str, str, bool], bool | None]:
    from pyzx import Circuit

    def verify(left: str, right: str, global_phase: bool) -> bool | None:
        first = Circuit.from_qasm(left)
        second = Circuit.from_qasm(right)
        return first.verify_equality(
            second, up_to_swaps=False, up_to_global_phase=global_phase,
        )

    return verify


def _worker(connection: Connection, request: dict[str, Any]) -> None:
    memory = _memory_enforcement(request["memory_limit_bytes"])
    try:
        connection.send({"kind": "started", "memory": memory, "peak_rss": _peak_rss_bytes()})
        runner = request["verify_backend"] or _load_verify()
        started = time.monotonic()
        result = runner(
            request["left"], request["right"], request["up_to_global_phase"],
        )
        if result not in {True, False, None}:
            response = {"kind": "protocol_error", "error": {"type": "TypeError", "message": "PyZX verifier must return True, False or None"}}
        else:
            response = {
                "kind": "result",
                "raw_result": "verified" if result is True else "not_reduced",
                "verified": result is True,
                "elapsed_seconds": time.monotonic() - started,
            }
    except MemoryError as exc:
        response = {"kind": "resource_exhaustion", "error": {"type": type(exc).__name__, "message": str(exc)}}
    except (ValueError, TypeError, KeyError) as exc:
        response = {"kind": "unsupported_input", "error": {"type": type(exc).__name__, "message": str(exc)}}
    except (ImportError, RuntimeError, OSError) as exc:
        response = {"kind": "backend_error", "error": {"type": type(exc).__name__, "message": str(exc)}}
    except Exception as exc:
        response = {"kind": "backend_error", "error": {"type": type(exc).__name__, "message": str(exc)}}
    response["memory"] = memory
    response["peak_rss"] = _peak_rss_bytes()
    try:
        connection.send(response)
    except (BrokenPipeError, EOFError, OSError):
        pass
    connection.close()


def _run(request: dict[str, Any], *, worker_target: Callable[..., None] = _worker) -> dict[str, Any]:
    context = multiprocessing.get_context("spawn")
    receiving, sending = context.Pipe(duplex=False)
    process = context.Process(target=worker_target, args=(sending, request), name="e7q-pyzx-worker")
    started = time.monotonic()
    try:
        process.start()
    except Exception as exc:
        receiving.close()
        sending.close()
        return {"reason": "worker_start_error", "error": {"type": type(exc).__name__, "message": str(exc)}, "wall_clock_seconds": time.monotonic() - started, "worker": {"started": False, "pid": None, "exit_code": None, "signal": None, "signal_name": None, "termination_mechanism": None, "reaped": True, "start_method": "spawn"}, "memory": {"requested_bytes": request["memory_limit_bytes"], "enforced": False, "mechanism": "worker-not-started", "effective_bytes": None}, "peak_rss": None}
    sending.close()
    deadline = started + request["timeout_seconds"]
    startup = None
    response = None
    timed_out = False
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = process.is_alive()
                break
            if receiving.poll(min(_POLL_SECONDS, remaining)):
                try:
                    message = receiving.recv()
                except EOFError:
                    break
                if isinstance(message, dict) and message.get("kind") == "started":
                    startup = message
                elif isinstance(message, dict):
                    response = message
                else:
                    response = {"kind": "protocol_error", "error": {"type": "TypeError", "message": "worker response must be a mapping"}}
            if not process.is_alive():
                break
        if not timed_out:
            process.join(max(0.0, deadline - time.monotonic()))
            timed_out = process.is_alive()
            # A short-lived worker can exit between the liveness check and the
            # pipe becoming readable. Drain any final queued response before
            # closing the parent endpoint.
            while not timed_out and receiving.poll():
                try:
                    message = receiving.recv()
                except EOFError:
                    break
                if isinstance(message, dict) and message.get("kind") == "started":
                    startup = message
                elif isinstance(message, dict):
                    response = message
                else:
                    response = {"kind": "protocol_error", "error": {"type": "TypeError", "message": "worker response must be a mapping"}}
    finally:
        receiving.close()
    mechanism = None
    if timed_out:
        mechanism, reaped = _terminate_and_reap(process)
    else:
        process.join()
        reaped = not process.is_alive()
    exit_code = process.exitcode
    signal_number, signal_name = _signal_metadata(exit_code)
    worker = {"started": True, "pid": process.pid, "exit_code": exit_code, "signal": signal_number, "signal_name": signal_name, "termination_mechanism": mechanism, "reaped": reaped, "start_method": "spawn"}
    if reaped:
        process.close()
    base = {
        "wall_clock_seconds": time.monotonic() - started,
        "worker": worker,
        "memory": (response or {}).get("memory") or (startup or {}).get("memory") or {"requested_bytes": request["memory_limit_bytes"], "enforced": False, "mechanism": "worker-did-not-report", "effective_bytes": None},
        "peak_rss": (response or {}).get("peak_rss") or (startup or {}).get("peak_rss"),
    }
    if timed_out:
        return {**base, "reason": "wall_clock_timeout", "error": {"type": "TimeoutError", "message": "PyZX worker exceeded the parent deadline"}}
    if not reaped:
        return {**base, "reason": "worker_reap_failure", "error": {"type": "RuntimeError", "message": "PyZX worker could not be reaped"}}
    if exit_code is not None and exit_code < 0:
        return {**base, "reason": "worker_signal", "error": {"type": "WorkerSignalError", "message": f"PyZX worker terminated by signal {signal_number}"}}
    if exit_code not in {0, None}:
        return {**base, "reason": "worker_crash", "error": {"type": "WorkerProcessError", "message": f"PyZX worker exited with code {exit_code}"}}
    if response is None:
        return {**base, "reason": "worker_protocol_error", "error": {"type": "EOFError", "message": "PyZX worker exited without a result"}}
    return {**base, **response, "reason": response["kind"]}


def evaluate(
    left: str | Path,
    right: str | Path,
    *,
    criterion: dict[str, Any],
    source_refs: tuple[str, str],
    created_at: str,
    timeout_seconds: float = 10.0,
    memory_limit_bytes: int = 2 * 1024**3,
    verify_backend: Callable[[str, str, bool], bool | None] | None = None,
) -> dict[str, Any]:
    if criterion not in SUPPORTED_CRITERIA.values():
        raise ValueError("an exact supported PyZX criterion object must be selected")
    if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    if type(memory_limit_bytes) is not int or memory_limit_bytes <= 0:
        raise ValueError("memory_limit_bytes must be positive")
    if len(source_refs) != 2 or any(not isinstance(item, str) for item in source_refs):
        raise ValueError("source_refs must contain exactly two strings")
    errors = []
    projections = []
    widths = []
    for path, role in ((left, "left"), (right, "right")):
        try:
            projection, width, error = _admit(_read(path, role), role)
        except E7QError as exc:
            projection, width, error = None, None, {"role": role, "status": "UNSUPPORTED", "message": str(exc)}
        projections.append(projection)
        widths.append(width)
        if error:
            errors.append(error)
    if not errors and widths[0] != widths[1]:
        errors.append({
            "role": "pair",
            "status": "UNSUPPORTED",
            "message": "left and right quantum register widths differ",
        })
    if not errors and projections[0] is not None and projections[1] is not None:
        execution = _run({
            "left": projections[0],
            "right": projections[1],
            "up_to_global_phase": criterion["options"]["up_to_global_phase"],
            "timeout_seconds": float(timeout_seconds),
            "memory_limit_bytes": memory_limit_bytes,
            "verify_backend": verify_backend,
        })
        reason = execution["reason"]
    else:
        status = "BLOCKED" if any(item["status"] == "BLOCKED" for item in errors) else "UNSUPPORTED"
        execution = {
            "reason": "input_admission",
            "error": {"type": "AdmissionError", "message": "; ".join(item["message"] for item in errors)},
            "wall_clock_seconds": 0.0,
            "worker": {"started": False, "pid": None, "exit_code": None, "signal": None, "signal_name": None, "termination_mechanism": None, "reaped": True, "start_method": "spawn"},
            "memory": {"requested_bytes": memory_limit_bytes, "enforced": False, "mechanism": "not-started-input-rejected", "effective_bytes": None},
            "peak_rss": None,
            "admission_status": status,
        }
        reason = "input_admission"
    if reason == "result" and execution.get("verified") is True:
        status, conclusion, raw = "PASS", "ESTABLISHED", "verified"
    elif reason == "result":
        status, conclusion, raw = "NOT_ASSESSED", "INCONCLUSIVE", "not_reduced"
    elif reason == "input_admission":
        status, conclusion, raw = execution["admission_status"], "INCONCLUSIVE", "input_admission"
    elif reason in {"wall_clock_timeout", "resource_exhaustion"}:
        status, conclusion, raw = "BLOCKED", "INCONCLUSIVE", reason
    elif reason == "unsupported_input":
        status, conclusion, raw = "UNSUPPORTED", "INCONCLUSIVE", reason
    else:
        status, conclusion, raw = "NOT_ASSESSED", "INCONCLUSIVE", reason
    backend_version = _package_version()
    if reason == "backend_error" and backend_version == "unavailable":
        status, conclusion, raw = "UNSUPPORTED", "INCONCLUSIVE", "backend_unavailable"
    if reason == "result" and backend_version not in {SUPPORTED_BACKEND_VERSION, "unavailable"}:
        status, conclusion, raw = "UNSUPPORTED", "INCONCLUSIVE", "unsupported_backend_version"
    memory = execution["memory"]
    payload: dict[str, Any] = {
        "format": "e7q.ir.pyzx-equivalence-assessment/v1",
        "criterion": criterion,
        "backend": {"id": BACKEND_ID, "version": backend_version, "supported_version": SUPPORTED_BACKEND_VERSION, "license": "Apache-2.0"},
        "configuration": {"timeout_seconds": float(timeout_seconds), "memory_limit_bytes": memory_limit_bytes, **criterion["options"]},
        "method": {"kind": "zx-calculus-rewrite-reduction", "exact_algebraic": False, "returns_counterexample": False},
        "outcome": {"status": status, "conclusion": conclusion, "raw_verdict": raw, "reason": reason, "timed_out": reason == "wall_clock_timeout", "resource_exhausted": reason == "resource_exhaustion", "universal_equivalence_established": status == "PASS"},
        "resource_use": {"wall_clock_seconds": execution["wall_clock_seconds"], "worker_peak_rss_bytes": execution["peak_rss"], "memory_limit_requested_bytes": memory["requested_bytes"], "memory_limit_enforced": memory["enforced"], "memory_limit_mechanism": memory["mechanism"], "memory_limit_effective_bytes": memory["effective_bytes"]},
        "worker": execution["worker"],
        "projection": {
            "terminal_identity_measurement_removed": not errors,
            "left_sha256": "sha256:" + sha256(projections[0].encode()).hexdigest() if projections[0] else None,
            "right_sha256": "sha256:" + sha256(projections[1].encode()).hexdigest() if projections[1] else None,
        },
        "input_errors": errors,
        "assumptions": ["pyzx-full-reduce-success-is-one-sided-equivalence-evidence", "input-output-swaps-are-disabled", "global-phase-is-controlled-by-the-selected-criterion"],
    }
    if execution.get("elapsed_seconds") is not None:
        payload["resource_use"]["backend_seconds"] = execution["elapsed_seconds"]
    if execution.get("error") is not None:
        payload["error"] = execution["error"]
    payload["assessment_id"] = digest(payload)
    return build_artifact(
        "assessment",
        payload,
        profile_id="e7q.ir.external-equivalence-assessment",
        profile_version="1",
        capabilities_required=("pyzx-optional-backend",),
        created_at=created_at,
        actor="e7q.ir.pyzx-adapter",
        source_refs=source_refs,
        limitations=LIMITATIONS,
    )
