# SPDX-License-Identifier: Apache-2.0
"""Installed semantic profile for bounded native E7Q reference execution."""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import asdict
from hashlib import sha256
from importlib.metadata import version
import json
from typing import Any, Iterable

from ..language import E7QError, backend_profile, parse, run, verify
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


def _failure(status: str, message: str) -> dict[str, Any]:
    return {
        "status": status,
        "message": message,
        "artifact_ids": {},
        "expected_payloads": {},
        "expected_relations": {},
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
        try:
            program = parse(content)
        except E7QError as exc:
            status = (
                "UNSUPPORTED"
                if str(exc) == "noise channels require the densitymatrix backend"
                else "FAIL"
            )
            return _failure(status, f"native source could not be admitted by the parser: {exc}")
        except (UnicodeError, ValueError, TypeError) as exc:
            return _failure("FAIL", f"native source could not be parsed: {exc}")
        admission_status, admission_message = native_admission_status(program)
        if admission_status != "PASS":
            return _failure(admission_status, admission_message or "native source was not admitted")
        try:
            native_result = verify(run(program))
        except Exception as exc:  # existing runtime is isolated by the semantic boundary
            return _failure("FAIL", f"native reference execution failed: {type(exc).__name__}")

        expected_payloads = {
            "source": _expected_source_payload(raw),
            "intent": {
                "format": "e7q.native-intent/v1",
                "name": program.name,
                "path": program.path,
                "require_normalized": program.require_normalized,
                "allowed_outcomes": (
                    sorted(program.allowed_outcomes)
                    if program.allowed_outcomes is not None
                    else None
                ),
                "shots": program.shots,
                "seed": program.seed,
                "backend": program.backend,
                "source_trust": "trusted-local-source",
            },
            "representation": {
                "format": "e7q.native-program/v1",
                "program": program_payload(program),
            },
            "execution": {
                "format": "e7q.native-execution/v1",
                "backend_profile": backend_profile(program),
                "seed": program.seed,
                "shots": program.shots,
                "implementation": implementation_versions(),
                "proof": native_result["proof"],
            },
            "observation": {
                "format": "e7q.native-observation/v1",
                "counts": native_result["counts"],
                "probabilities": native_result["probabilities"],
                "label_order": "clbit-ascending",
                "bit_width": program.bits,
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
        }
    except Exception as exc:
        return _failure("FAIL", f"native semantic reconstruction failed: {type(exc).__name__}")


def _context(graph: dict[str, Any]) -> dict[str, Any]:
    graph_id = graph.get("graph_id")
    if isinstance(graph_id, str) and graph_id in _CONTEXT_CACHE:
        _CONTEXT_CACHE.move_to_end(graph_id)
        return _CONTEXT_CACHE[graph_id]
    context = _reconstruct(graph)
    if isinstance(graph_id, str):
        _CONTEXT_CACHE[graph_id] = context
        _CONTEXT_CACHE.move_to_end(graph_id)
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
        )
