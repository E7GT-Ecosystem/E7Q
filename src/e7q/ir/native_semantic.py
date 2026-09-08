# SPDX-License-Identifier: Apache-2.0
"""Installed semantic profile for bounded native E7Q reference execution."""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import asdict
from hashlib import sha256
from importlib.metadata import version
import json
import multiprocessing
from multiprocessing.connection import Connection
import signal
import sys
import time
from typing import Any, Iterable

try:
    import resource
except ImportError:  # pragma: no cover - unavailable on Windows
    resource = None  # type: ignore[assignment]

from ..language import (
    E7QError,
    E7QResourceLimitError,
    ParseLimits,
    backend_profile,
    parse,
    run,
    verify,
)
from .graph import build_relation
from .semantic import SemanticResult

PROFILE_ID = "e7q.ir.native-execution"
PROFILE_VERSION = "0alpha1"
VALIDATOR_ID = "e7q.ir.validator.native-execution/0alpha1"
ACTOR = "e7q.ir.native-execution/v1"

MAXIMUM_CONCLUSION = (
    "Under the installed bounded native-execution profile, this graph faithfully "
    "records the deterministic parsing, admitted reference execution, observation "
    "and native-verifier result recomputed from the preserved source."
)
BOUNDARIES = (
    MAXIMUM_CONCLUSION,
    "F2 does not establish hardware execution or fidelity, provider authentication, "
    "authenticated chronology, compiler correctness, equivalence to an external "
    "circuit, exact-algebraic equivalence, scalability, computational advantage, "
    "F3 authentication or F4 reproduction.",
    "Semantic conformance is separate from native program success; a faithfully "
    "recomputed native FAIL remains a FAIL program verdict.",
)
LIMITS = [
    "Statevector-only trusted local source with an explicit seed; no noise, dynamic "
    "measurement/control or assertions; exactly one terminal full-register measurement.",
    "At most 8 qubits, 8 classical bits, 100000 shots and 1024 expanded operations.",
    MAXIMUM_CONCLUSION,
    BOUNDARIES[1],
    "The supplied timestamp identifies this record, not authenticated execution time.",
    "State amplitudes and per-shot trajectories are not exported; counts lose phase information.",
]

CAPABILITIES_BY_KIND = {
    "source": ("artifact.identity", "native.source.utf8-bytes"),
    "intent": ("native.intent",),
    "representation": ("native.parser.projection", "transformation.accounting"),
    "execution": ("native.reference-execution",),
    "observation": ("native.observation", "observation.record"),
    "assessment": ("native.verification",),
}
EXPECTED_KINDS = tuple(CAPABILITIES_BY_KIND)

PARSER_CRITERION = {"id": "e7q.ir.native-parser-projection", "version": "1"}
PARSER_PRESERVES = [
    "parsed-program-fields",
    "expanded-operation-order",
    "original-source-reference",
]
PARSER_LOSES = [
    "comments-and-formatting-in-projection",
    "subpath-call-boundaries-in-expanded-operations",
]
PARSER_ASSUMPTIONS = ["native-parser-implementation"]

NATIVE_PARSE_LIMITS = ParseLimits(
    max_operations=1024,
    max_path_invocations=1024,
    max_statement_visits=2048,
    max_nesting_depth=64,
)
NATIVE_REPLAY_TIMEOUT_SECONDS = 5.0
NATIVE_REPLAY_MEMORY_LIMIT_BYTES = 8 * 1024**3
NATIVE_REPLAY_IMPLEMENTATION_REVISION = "native-f2-resource-safe-v1"
_WORKER_STOP_GRACE_SECONDS = 1.0
_WORKER_POLL_SECONDS = 0.02


def native_resource_policy() -> dict[str, Any]:
    """Return the installed, graph-independent native replay policy."""
    return {
        "parser": asdict(NATIVE_PARSE_LIMITS),
        "wall_clock_limit_seconds": NATIVE_REPLAY_TIMEOUT_SECONDS,
        "memory_limit_requested_bytes": NATIVE_REPLAY_MEMORY_LIMIT_BYTES,
        "memory_limit_mechanism": "posix-rlimit-as",
        "worker_start_method": "spawn",
        "implementation_revision": NATIVE_REPLAY_IMPLEMENTATION_REVISION,
    }


def program_payload(program: Any) -> dict[str, Any]:
    """Return the existing parser result in deterministic JSON data types."""
    value = asdict(program)
    value["allowed_outcomes"] = (
        sorted(program.allowed_outcomes)
        if program.allowed_outcomes is not None
        else None
    )
    return json.loads(json.dumps(value, allow_nan=False))


def implementation_versions() -> dict[str, str]:
    return {"e7q": version("e7q"), "numpy": version("numpy")}


def native_admission_status(program: Any) -> tuple[str, str | None]:
    """Apply the documented native admission boundary before simulator allocation."""
    if program.backend != "statevector":
        return "UNSUPPORTED", "native execution requires the statevector backend"
    if program.qubits > 8 or program.bits > 8 or program.shots > 100000:
        return "BLOCKED", "native execution exceeds the 8-qubit/bit or 100000-shot budget"
    if len(program.operations) > 1024:
        return "BLOCKED", "native execution exceeds the 1024-expanded-operation budget"
    if program.seed is None:
        return "UNSUPPORTED", "native execution requires an explicit seed"
    if (
        not program.operations
        or program.operations[-1].gate != "MEASURE"
        or not program.operations[-1].full_register
        or any(
            operation.gate in {"MEASURE", "ASSERT", "NOISE"}
            or operation.condition is not None
            for operation in program.operations[:-1]
        )
    ):
        return (
            "UNSUPPORTED",
            "native execution requires static gates and one terminal full-register measurement",
        )
    return "PASS", None


def admit_native_program(program: Any) -> None:
    status, message = native_admission_status(program)
    if status != "PASS":
        raise E7QError(message or "native execution was not admitted")


def _expected_source_payload(raw: bytes) -> dict[str, Any]:
    return {
        "format": "e7q",
        "content": raw.decode("utf-8"),
        "byte_length": len(raw),
        "content_digest": "sha256:" + sha256(raw).hexdigest(),
        "adapter": "e7q.ir.legacy-preservation/v1",
    }


def _peak_rss_bytes() -> int | None:
    if resource is None:
        return None
    peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return peak * 1024 if sys.platform.startswith("linux") else peak


def _memory_enforcement(requested_bytes: int) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "requested_bytes": requested_bytes,
        "enforced": False,
        "mechanism": "unsupported",
        "effective_bytes": None,
    }
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


def _native_replay_worker(connection: Connection, content: str) -> None:
    memory = _memory_enforcement(NATIVE_REPLAY_MEMORY_LIMIT_BYTES)
    _worker_send(connection, {
        "kind": "worker_started",
        "memory_limit": memory,
        "worker_peak_rss_bytes": _peak_rss_bytes(),
    })
    if not memory["enforced"]:
        response: dict[str, Any] = {
            "kind": "unsupported_platform",
            "status": "UNSUPPORTED",
            "message": "native replay requires enforceable POSIX RLIMIT_AS memory isolation",
        }
    else:
        try:
            program = parse(content, limits=NATIVE_PARSE_LIMITS)
            admission_status, admission_message = native_admission_status(program)
            if admission_status != "PASS":
                response = {
                    "kind": "admission",
                    "status": admission_status,
                    "message": admission_message or "native source was not admitted",
                }
            else:
                native_result = verify(run(program))
                response = {
                    "kind": "result",
                    "status": "PASS",
                    "program": program_payload(program),
                    "backend_profile": backend_profile(program),
                    "native_result": native_result,
                }
        except E7QResourceLimitError as exc:
            response = {
                "kind": "expansion_limit",
                "status": "BLOCKED",
                "message": str(exc),
            }
        except MemoryError as exc:
            response = {
                "kind": "memory_exhaustion",
                "status": "BLOCKED",
                "message": str(exc) or "native replay exhausted its memory budget",
            }
        except E7QError as exc:
            status = (
                "UNSUPPORTED"
                if str(exc) == "noise channels require the densitymatrix backend"
                else "FAIL"
            )
            response = {
                "kind": "parse_or_admission_error",
                "status": status,
                "message": f"native source could not be admitted by the parser: {exc}",
            }
        except (UnicodeError, ValueError, TypeError) as exc:
            response = {
                "kind": "parse_error",
                "status": "FAIL",
                "message": f"native source could not be parsed: {exc}",
            }
        except Exception as exc:
            response = {
                "kind": "worker_error",
                "status": "FAIL",
                "message": f"native reference execution failed: {type(exc).__name__}",
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
    return mechanism, not process.is_alive()


def _runtime_evidence(result: dict[str, Any]) -> dict[str, Any]:
    worker = result["worker"]
    return {
        "policy": native_resource_policy(),
        "outcome_reason": result["reason"],
        "memory": result["memory_limit"],
        "worker": {
            "start_method": worker["start_method"],
            "started": worker["started"],
            "exit_code": worker["exit_code"],
            "signal": worker["signal"],
            "signal_name": worker["signal_name"],
            "termination_mechanism": worker["termination_mechanism"],
            "reaped": worker["reaped"],
        },
    }


def _run_native_replay_isolated(
    content: str,
    *,
    worker_target: Any = _native_replay_worker,
) -> dict[str, Any]:
    context = multiprocessing.get_context("spawn")
    receiving, sending = context.Pipe(duplex=False)
    process = context.Process(
        target=worker_target,
        args=(sending, content),
        name="e7q-native-f2-worker",
    )
    started = time.monotonic()
    try:
        process.start()
    except Exception as exc:
        receiving.close()
        sending.close()
        return {
            "reason": "worker_start_error",
            "status": "NOT_ASSESSED",
            "message": f"native replay worker could not start: {type(exc).__name__}",
            "memory_limit": {
                "requested_bytes": NATIVE_REPLAY_MEMORY_LIMIT_BYTES,
                "enforced": False,
                "mechanism": "worker-not-started",
                "effective_bytes": None,
            },
            "worker": {
                "start_method": "spawn", "started": False, "pid": None,
                "exit_code": None, "signal": None, "signal_name": None,
                "termination_mechanism": None, "reaped": True,
            },
        }
    sending.close()
    deadline = started + NATIVE_REPLAY_TIMEOUT_SECONDS
    startup: dict[str, Any] | None = None
    response: dict[str, Any] | None = None
    timed_out = False

    def record_message(message: Any) -> None:
        nonlocal startup, response
        if isinstance(message, dict) and message.get("kind") == "worker_started":
            startup = message
        elif isinstance(message, dict):
            response = message
        else:
            response = {
                "kind": "worker_protocol_error",
                "status": "NOT_ASSESSED",
                "message": "native replay worker response is not an object",
            }

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
                record_message(message)
            if not process.is_alive():
                while receiving.poll():
                    try:
                        record_message(receiving.recv())
                    except EOFError:
                        break
                break
        if not timed_out:
            process.join(max(0.0, deadline - time.monotonic()))
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
        "start_method": "spawn", "started": True, "pid": process.pid,
        "exit_code": exit_code, "signal": signal_number, "signal_name": signal_name,
        "termination_mechanism": termination_mechanism, "reaped": reaped,
    }
    if reaped:
        process.close()
    memory = (
        (response or {}).get("memory_limit")
        or (startup or {}).get("memory_limit")
        or {
            "requested_bytes": NATIVE_REPLAY_MEMORY_LIMIT_BYTES,
            "enforced": False,
            "mechanism": "worker-did-not-report",
            "effective_bytes": None,
        }
    )
    base = {"worker": worker, "memory_limit": memory}
    if timed_out:
        return {
            **base, "reason": "wall_clock_timeout", "status": "BLOCKED",
            "message": "native replay exceeded the parent-owned wall-clock deadline",
        }
    if not reaped:
        return {
            **base, "reason": "worker_reap_failure", "status": "NOT_ASSESSED",
            "message": "native replay worker could not be reaped",
        }
    if exit_code is not None and exit_code < 0:
        return {
            **base, "reason": "worker_signal", "status": "NOT_ASSESSED",
            "message": f"native replay worker terminated by signal {signal_number}",
        }
    if exit_code not in {0, None}:
        return {
            **base, "reason": "worker_crash", "status": "NOT_ASSESSED",
            "message": f"native replay worker exited with code {exit_code}",
        }
    if response is None:
        return {
            **base, "reason": "worker_protocol_error", "status": "NOT_ASSESSED",
            "message": "native replay worker exited without a result",
        }
    if not all(key in response for key in ("kind", "status", "message")) and response.get("kind") != "result":
        return {
            **base, "reason": "worker_protocol_error", "status": "NOT_ASSESSED",
            "message": "native replay worker returned an incomplete response",
        }
    if response.get("kind") == "result" and not all(
        key in response for key in ("program", "backend_profile", "native_result")
    ):
        return {
            **base, "reason": "worker_protocol_error", "status": "NOT_ASSESSED",
            "message": "native replay worker omitted required result fields",
        }
    return {**base, **response, "reason": response["kind"]}


def _failure(
    status: str,
    message: str,
    runtime_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "message": message,
        "artifact_ids": {},
        "expected_payloads": {},
        "expected_relations": {},
        "runtime_evidence": runtime_evidence,
    }


_CONTEXT_CACHE: OrderedDict[str, dict[str, Any]] = OrderedDict()
_CONTEXT_CACHE_LIMIT = 4


def _reconstruct(graph: dict[str, Any]) -> dict[str, Any]:
    """Reconstruct the admitted workflow without retaining the supplied graph."""
    try:
        artifacts = graph.get("artifacts")
        if not isinstance(artifacts, list):
            return _failure("FAIL", "native graph artifacts are not a list")
        grouped: dict[str, list[dict[str, Any]]] = {}
        for artifact in artifacts:
            if isinstance(artifact, dict):
                grouped.setdefault(artifact.get("kind"), []).append(artifact)
        if set(grouped) != set(EXPECTED_KINDS) or any(
            len(grouped[kind]) != 1 for kind in EXPECTED_KINDS
        ):
            return _failure(
                "FAIL",
                "native graph must contain exactly one source, intent, representation, "
                "execution, observation and assessment artifact",
            )
        by_kind = {kind: grouped[kind][0] for kind in EXPECTED_KINDS}
        source_payload = by_kind["source"].get("payload")
        if not isinstance(source_payload, dict):
            return _failure("FAIL", "native source payload is not an object")
        if source_payload.get("format") != "e7q":
            return _failure("UNSUPPORTED", "native source format is not e7q")
        content = source_payload.get("content")
        if not isinstance(content, str):
            return _failure("FAIL", "native source content is not UTF-8 text")
        raw = content.encode("utf-8")
        from .legacy import MAX_BYTES  # lazy to keep semantic registration acyclic

        if len(raw) > MAX_BYTES:
            return _failure("BLOCKED", "native source exceeds the preservation byte budget")
        replay = _run_native_replay_isolated(content)
        runtime_evidence = _runtime_evidence(replay)
        if replay["status"] != "PASS":
            return _failure(replay["status"], replay["message"], runtime_evidence)
        program = replay["program"]
        native_result = replay["native_result"]

        expected_payloads = {
            "source": _expected_source_payload(raw),
            "intent": {
                "format": "e7q.native-intent/v1",
                "name": program["name"],
                "path": program["path"],
                "require_normalized": program["require_normalized"],
                "allowed_outcomes": program["allowed_outcomes"],
                "shots": program["shots"],
                "seed": program["seed"],
                "backend": program["backend"],
                "source_trust": "trusted-local-source",
            },
            "representation": {
                "format": "e7q.native-program/v1",
                "program": program,
            },
            "execution": {
                "format": "e7q.native-execution/v1",
                "backend_profile": replay["backend_profile"],
                "seed": program["seed"],
                "shots": program["shots"],
                "implementation": implementation_versions(),
                "proof": native_result["proof"],
            },
            "observation": {
                "format": "e7q.native-observation/v1",
                "counts": native_result["counts"],
                "probabilities": native_result["probabilities"],
                "label_order": "clbit-ascending",
                "bit_width": program["bits"],
                "probability_basis": "reference-statevector-computational-basis",
            },
            "assessment": {
                "format": "e7q.native-assessment/v1",
                "criterion": "e7q.language.verify",
                "tolerance": 1e-12,
                "native_result": native_result,
            },
        }
        ids = {kind: by_kind[kind]["artifact_id"] for kind in EXPECTED_KINDS}
        expected_relations = {
            (ids["source"], ids["intent"]): build_relation(
                "represents", ids["source"], ids["intent"], validation_status="validated"
            ),
            (ids["source"], ids["representation"]): build_relation(
                "transforms",
                ids["source"],
                ids["representation"],
                criterion=PARSER_CRITERION,
                preserves=PARSER_PRESERVES,
                loses=PARSER_LOSES,
                assumptions=PARSER_ASSUMPTIONS,
                validation_status="validated",
            ),
            (ids["representation"], ids["execution"]): build_relation(
                "produces", ids["representation"], ids["execution"], validation_status="validated"
            ),
            (ids["execution"], ids["observation"]): build_relation(
                "produces", ids["execution"], ids["observation"], validation_status="validated"
            ),
            (ids["assessment"], ids["observation"]): build_relation(
                "assesses", ids["assessment"], ids["observation"], validation_status="validated"
            ),
        }
        relations = graph.get("relations")
        actual_pairs = (
            [(item.get("source"), item.get("target")) for item in relations]
            if isinstance(relations, list) and all(isinstance(item, dict) for item in relations)
            else []
        )
        if len(actual_pairs) != len(expected_relations) or set(actual_pairs) != set(expected_relations):
            return _failure(
                "FAIL",
                "native graph must contain exactly the five required workflow relations",
            )
        return {
            "status": "PASS",
            "message": MAXIMUM_CONCLUSION,
            "artifact_ids": ids,
            "expected_payloads": expected_payloads,
            "expected_relations": expected_relations,
            "expected_source_refs": {
                "source": [],
                "intent": [ids["source"]],
                "representation": [ids["source"], ids["intent"]],
                "execution": [ids["representation"]],
                "observation": [ids["execution"]],
                "assessment": [ids["intent"], ids["execution"], ids["observation"]],
            },
            "created_at": by_kind["source"].get("provenance", {}).get("created_at"),
            "runtime_evidence": runtime_evidence,
        }
    except Exception as exc:
        return _failure("FAIL", f"native semantic reconstruction failed: {type(exc).__name__}")


def _context(graph: dict[str, Any]) -> dict[str, Any]:
    graph_id = graph.get("graph_id")
    cache_key = None
    if isinstance(graph_id, str):
        cache_key = "sha256:" + sha256(json.dumps(
            {
                "graph_id": graph_id,
                "validator_id": VALIDATOR_ID,
                "policy": native_resource_policy(),
                "implementation": implementation_versions(),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()).hexdigest()
    if cache_key is not None and cache_key in _CONTEXT_CACHE:
        _CONTEXT_CACHE.move_to_end(cache_key)
        return _CONTEXT_CACHE[cache_key]
    context = _reconstruct(graph)
    if cache_key is not None:
        _CONTEXT_CACHE[cache_key] = context
        _CONTEXT_CACHE.move_to_end(cache_key)
        while len(_CONTEXT_CACHE) > _CONTEXT_CACHE_LIMIT:
            _CONTEXT_CACHE.popitem(last=False)
    return context


def _semantic_result(
    *,
    check_id: str,
    status: str,
    subject_kind: str,
    subject_id: str,
    evidence_refs: Iterable[str],
    message: str,
    criterion: dict[str, Any] | None = None,
    runtime_evidence: dict[str, Any] | None = None,
) -> SemanticResult:
    return SemanticResult(
        check_id=check_id,
        status=status,
        subject_kind=subject_kind,
        subject_id=subject_id,
        profile_id=PROFILE_ID,
        profile_version=PROFILE_VERSION,
        evidence_refs=tuple(evidence_refs),
        message=message,
        boundaries=BOUNDARIES,
        criterion=criterion,
        runtime_evidence=runtime_evidence,
    )


class NativeExecutionValidator:
    """Reparse, replay and reverify bounded native-execution evidence."""

    profile_id = PROFILE_ID
    profile_version = PROFILE_VERSION
    validator_id = VALIDATOR_ID

    def validate_artifact(
        self, artifact: dict[str, Any], graph: dict[str, Any]
    ) -> Iterable[SemanticResult]:
        context = _context(graph)
        all_refs = tuple(item["artifact_id"] for item in graph["artifacts"])
        if context["status"] != "PASS":
            yield _semantic_result(
                check_id="native-execution.reconstruction",
                status=context["status"],
                subject_kind="artifact",
                subject_id=artifact["artifact_id"],
                evidence_refs=(artifact["artifact_id"],),
                message=context["message"],
                runtime_evidence=context["runtime_evidence"],
            )
            return
        kind = artifact.get("kind")
        if (
            kind not in EXPECTED_KINDS
            or context["artifact_ids"].get(kind) != artifact.get("artifact_id")
        ):
            yield _semantic_result(
                check_id="native-execution.artifact.inventory",
                status="FAIL",
                subject_kind="artifact",
                subject_id=artifact["artifact_id"],
                evidence_refs=all_refs,
                message="Artifact is not the unique expected native workflow subject.",
                runtime_evidence=context["runtime_evidence"],
            )
            return
        provenance = artifact.get("provenance")
        envelope_ok = (
            artifact.get("profile")
            == {
                "id": PROFILE_ID,
                "version": PROFILE_VERSION,
                "capabilities_required": list(CAPABILITIES_BY_KIND[kind]),
            }
            and artifact.get("limitations") == LIMITS
            and isinstance(provenance, dict)
            and provenance.get("actor") == ACTOR
            and provenance.get("created_at") == context["created_at"]
            and provenance.get("source_refs") == context["expected_source_refs"][kind]
        )
        yield _semantic_result(
            check_id=f"native-execution.artifact.{kind}.profile-and-provenance",
            status="PASS" if envelope_ok else "FAIL",
            subject_kind="artifact",
            subject_id=artifact["artifact_id"],
            evidence_refs=all_refs,
            message=(
                "Profile capabilities, boundary declarations and provenance references match."
                if envelope_ok
                else "Profile capabilities, boundary declarations or provenance references differ."
            ),
            runtime_evidence=context["runtime_evidence"],
        )
        payload_ok = artifact.get("payload") == context["expected_payloads"][kind]
        criterion = PARSER_CRITERION if kind == "representation" else None
        yield _semantic_result(
            check_id=f"native-execution.artifact.{kind}.recomputed",
            status="PASS" if payload_ok else "FAIL",
            subject_kind="artifact",
            subject_id=artifact["artifact_id"],
            evidence_refs=all_refs,
            message=(
                f"The {kind} payload matches independent reconstruction from preserved source."
                if payload_ok
                else f"The {kind} payload differs from independent reconstruction from preserved source."
            ),
            criterion=criterion,
            runtime_evidence=context["runtime_evidence"],
        )

    def validate_relation(
        self, relation: dict[str, Any], graph: dict[str, Any]
    ) -> Iterable[SemanticResult]:
        context = _context(graph)
        refs = (relation["source"], relation["target"])
        if context["status"] != "PASS":
            yield _semantic_result(
                check_id="native-execution.reconstruction",
                status=context["status"],
                subject_kind="relation",
                subject_id=relation["relation_id"],
                evidence_refs=refs,
                message=context["message"],
                runtime_evidence=context["runtime_evidence"],
            )
            return
        expected = context["expected_relations"].get(refs)
        matches = expected is not None and relation == expected
        kind_by_id = {
            artifact_id: kind for kind, artifact_id in context["artifact_ids"].items()
        }
        relation_name = (
            f"{expected['kind']}.{kind_by_id[relation['source']]}"
            f"-to-{kind_by_id[relation['target']]}"
            if expected is not None
            else "unexpected"
        )
        yield _semantic_result(
            check_id=f"native-execution.relation.{relation_name}",
            status="PASS" if matches else "FAIL",
            subject_kind="relation",
            subject_id=relation["relation_id"],
            evidence_refs=refs,
            message=(
                "Relation endpoints, criterion, preservation, loss, assumptions and validation status match."
                if matches
                else "Relation endpoints, criterion, preservation, loss, assumptions or validation status differ."
            ),
            criterion=expected.get("criterion") if expected is not None else None,
            runtime_evidence=context["runtime_evidence"],
        )
