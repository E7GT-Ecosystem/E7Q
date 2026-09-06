# SPDX-License-Identifier: Apache-2.0
"""Deterministic F2 semantic-validator contracts and orchestration."""
from __future__ import annotations

from dataclasses import dataclass
from itertools import islice
import re
from typing import Any, Iterable, Protocol

from .canonical import digest
from .profiles import negotiate, semantic_validator_id


STATUSES = frozenset({"PASS", "FAIL", "BLOCKED", "UNSUPPORTED", "NOT_ASSESSED"})
MAX_RESULTS_PER_SUBJECT = 128
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


@dataclass(frozen=True)
class SemanticResult:
    """One profile-scoped semantic conclusion about one graph subject."""

    check_id: str
    status: str
    subject_kind: str
    subject_id: str
    profile_id: str | None
    profile_version: str | None
    evidence_refs: tuple[str, ...]
    message: str
    boundaries: tuple[str, ...] = ()
    criterion: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.check_id or not isinstance(self.check_id, str):
            raise ValueError("semantic check_id must be a non-empty string")
        if self.status not in STATUSES:
            raise ValueError(f"unsupported semantic status: {self.status}")
        if self.subject_kind not in {"artifact", "relation"}:
            raise ValueError("semantic subject_kind must be artifact or relation")
        if not isinstance(self.subject_id, str) or not _DIGEST.fullmatch(self.subject_id):
            raise ValueError("semantic subject_id must be a SHA-256 identity")
        if (self.profile_id is None) != (self.profile_version is None):
            raise ValueError("semantic profile identity must be complete or absent")
        if self.profile_id is not None and not self.profile_id:
            raise ValueError("semantic profile_id must be non-empty")
        if self.profile_version is not None and not self.profile_version:
            raise ValueError("semantic profile_version must be non-empty")
        if not self.evidence_refs or any(
            not isinstance(ref, str) or not _DIGEST.fullmatch(ref)
            for ref in self.evidence_refs
        ):
            raise ValueError("semantic evidence_refs must contain SHA-256 identities")
        if not isinstance(self.message, str) or not self.message:
            raise ValueError("semantic message must be non-empty")
        if any(not isinstance(item, str) or not item for item in self.boundaries):
            raise ValueError("semantic boundaries must be non-empty strings")
        if self.criterion is not None and not isinstance(self.criterion, dict):
            raise ValueError("semantic criterion must be an object when supplied")

    def as_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "check_id": self.check_id,
            "status": self.status,
            "subject": {"kind": self.subject_kind, "id": self.subject_id},
            "profile": (
                {"id": self.profile_id, "version": self.profile_version}
                if self.profile_id is not None
                else None
            ),
            "evidence_refs": sorted(set(self.evidence_refs)),
            "message": self.message,
            "boundaries": sorted(set(self.boundaries)),
        }
        if self.criterion is not None:
            value["criterion"] = self.criterion
        value["result_id"] = digest(value)
        return value


class SemanticValidator(Protocol):
    """Profile validator interface; capability negotiation is separate."""

    profile_id: str
    profile_version: str
    validator_id: str

    def validate_artifact(
        self, artifact: dict[str, Any], graph: dict[str, Any]
    ) -> Iterable[SemanticResult]: ...

    def validate_relation(
        self, relation: dict[str, Any], graph: dict[str, Any]
    ) -> Iterable[SemanticResult]: ...


class SemanticRegistry:
    """Explicit profile/version-to-validator registry."""

    def __init__(self) -> None:
        self._validators: dict[tuple[str, str], SemanticValidator] = {}

    def register(self, validator: SemanticValidator) -> None:
        key = (validator.profile_id, validator.profile_version)
        if key in self._validators:
            raise ValueError(f"semantic validator already registered for {key[0]}/{key[1]}")
        expected = semantic_validator_id(
            {"id": validator.profile_id, "version": validator.profile_version}
        )
        if expected is not None and validator.validator_id != expected:
            raise ValueError(
                f"validator id {validator.validator_id} does not match profile metadata {expected}"
            )
        self._validators[key] = validator

    def resolve(self, profile_id: str, version: str) -> SemanticValidator | None:
        return self._validators.get((profile_id, version))


class PendingCircuitBasicValidator:
    """Bounded payload checks and the first Phase 1C identity criterion."""

    profile_id = "e7q.ir.circuit-basic"
    profile_version = "0alpha1"
    validator_id = "e7q.ir.validator.circuit-basic/0alpha1"

    def validate_artifact(
        self, artifact: dict[str, Any], graph: dict[str, Any]
    ) -> Iterable[SemanticResult]:
        from .circuit import validate_payload
        status, message = validate_payload(artifact, graph)
        yield SemanticResult(
            check_id=f"circuit-basic.artifact.{artifact['kind']}.phase-1b",
            status=status,
            subject_kind="artifact",
            subject_id=artifact["artifact_id"],
            profile_id=self.profile_id,
            profile_version=self.profile_version,
            evidence_refs=tuple(a['artifact_id'] for a in graph['artifacts']),
            message=message,
            criterion={'id': 'e7q.ir.circuit-basic-payload', 'edition': '1b'},
            boundaries=("No quantum-semantic conclusion is established.",),
        )

    def validate_relation(
        self, relation: dict[str, Any], graph: dict[str, Any]
    ) -> Iterable[SemanticResult]:
        from .circuit import BYTE_IDENTITY_CRITERION, STRUCTURAL_IDENTITY_CRITERION, validate_relation_payload
        status, message = validate_relation_payload(relation, graph)
        criterion = relation.get("criterion") if relation.get("kind") == "transforms" else None
        byte_identity = criterion is not None and criterion.get('id') == BYTE_IDENTITY_CRITERION['id']
        structural_identity = criterion is not None and criterion.get('id') == STRUCTURAL_IDENTITY_CRITERION['id']
        exact_unitary = criterion is not None and criterion.get('id') == 'e7q.ir.signed-permutation-unitary'
        global_phase = criterion is not None and criterion.get('id') == 'e7q.ir.signed-permutation-global-phase'
        basis_measurement = criterion is not None and criterion.get('id') == 'e7q.ir.signed-permutation-basis-measurement'
        unitary_channel = criterion is not None and criterion.get('id') == 'e7q.ir.signed-permutation-unitary-channel'
        message = message if status != 'NOT_ASSESSED' else (
            "The declared transformation criterion has no Phase 1A implementation."
            if criterion is not None
            else "Phase 1A does not yet assess this circuit-profile relation."
        )
        yield SemanticResult(
            check_id=("circuit-basic.relation.transforms.utf8-byte-identity-v1" if byte_identity
                      else "circuit-basic.relation.transforms.openqasm2-structural-identity-v1" if structural_identity
                      else "circuit-basic.relation.transforms.signed-permutation-unitary-v1" if exact_unitary
                      else "circuit-basic.relation.transforms.signed-permutation-global-phase-v1" if global_phase
                      else "circuit-basic.relation.transforms.signed-permutation-basis-measurement-v1" if basis_measurement
                      else "circuit-basic.relation.transforms.signed-permutation-unitary-channel-v1" if unitary_channel
                      else f"circuit-basic.relation.{relation['kind']}.phase-1a"),
            status=status,
            subject_kind="relation",
            subject_id=relation["relation_id"],
            profile_id=self.profile_id,
            profile_version=self.profile_version,
            evidence_refs=((relation['source'], relation['target']) if byte_identity or structural_identity or exact_unitary or global_phase or basis_measurement or unitary_channel
                           else tuple(a['artifact_id'] for a in graph['artifacts'])),
            message=message,
            boundaries=(
                "A transformation declaration is not semantic validation.",
                "No provider-authenticity or physical-fidelity conclusion is established.",
            ),
            criterion=criterion,
        )


DEFAULT_REGISTRY = SemanticRegistry()
DEFAULT_REGISTRY.register(PendingCircuitBasicValidator())


def _profile(value: dict[str, Any]) -> tuple[str, str] | None:
    profile = value.get("profile")
    if not isinstance(profile, dict):
        return None
    profile_id = profile.get("id")
    version = profile.get("version")
    if not isinstance(profile_id, str) or not isinstance(version, str):
        return None
    return profile_id, version


def _framework_result(
    *,
    status: str,
    subject_kind: str,
    subject: dict[str, Any],
    profile: tuple[str, str] | None,
    check_id: str,
    message: str,
) -> SemanticResult:
    evidence = (
        (subject["artifact_id"],)
        if subject_kind == "artifact"
        else (subject["source"], subject["target"])
    )
    return SemanticResult(
        check_id=check_id,
        status=status,
        subject_kind=subject_kind,
        subject_id=subject[f"{subject_kind}_id"],
        profile_id=profile[0] if profile else None,
        profile_version=profile[1] if profile else None,
        evidence_refs=evidence,
        message=message,
        boundaries=("No F2 PASS is inferred from this framework result.",),
    )


def _invoke(
    validator: SemanticValidator,
    method: str,
    subject_kind: str,
    subject: dict[str, Any],
    graph: dict[str, Any],
    profile: tuple[str, str],
) -> list[SemanticResult]:
    try:
        raw = list(
            islice(
                getattr(validator, method)(subject, graph),
                MAX_RESULTS_PER_SUBJECT + 1,
            )
        )
    except Exception:  # validator isolation is part of the fail-closed boundary
        return [
            _framework_result(
                status="FAIL",
                subject_kind=subject_kind,
                subject=subject,
                profile=profile,
                check_id="e7q.ir.framework.validator-exception",
                message="The semantic validator raised an exception.",
            )
        ]
    if len(raw) > MAX_RESULTS_PER_SUBJECT:
        return [
            _framework_result(
                status="BLOCKED",
                subject_kind=subject_kind,
                subject=subject,
                profile=profile,
                check_id="e7q.ir.framework.validator-result-limit",
                message="The semantic validator exceeded the per-subject result limit.",
            )
        ]
    if not raw:
        return [
            _framework_result(
                status="NOT_ASSESSED",
                subject_kind=subject_kind,
                subject=subject,
                profile=profile,
                check_id="e7q.ir.framework.no-validator-results",
                message="The semantic validator returned no result for this subject.",
            )
        ]
    expected_id = subject[f"{subject_kind}_id"]
    graph_ids = {
        item["artifact_id"] for item in graph["artifacts"]
    } | {item["relation_id"] for item in graph["relations"]}
    malformed = (
        any(not isinstance(item, SemanticResult) for item in raw)
        or any(
            item.subject_kind != subject_kind
            or item.subject_id != expected_id
            or (item.profile_id, item.profile_version) != profile
            or any(ref not in graph_ids for ref in item.evidence_refs)
            for item in raw
            if isinstance(item, SemanticResult)
        )
        or len(
            {
                item.check_id
                for item in raw
                if isinstance(item, SemanticResult)
            }
        )
        != len(raw)
    )
    if malformed:
        return [
            _framework_result(
                status="FAIL",
                subject_kind=subject_kind,
                subject=subject,
                profile=profile,
                check_id="e7q.ir.framework.validator-result-contract",
                message="The semantic validator returned a malformed result.",
            )
        ]
    return raw


def validate_semantics(
    graph: dict[str, Any], *, registry: SemanticRegistry = DEFAULT_REGISTRY
) -> tuple[str, list[dict[str, Any]]]:
    """Run installed validators after F0/F1 have passed."""
    artifacts = graph["artifacts"]
    artifacts_by_id = {item["artifact_id"]: item for item in artifacts}
    readiness = {
        item["artifact_id"]: negotiate(item["profile"])["status"] == "SUPPORTED"
        for item in artifacts
    }
    results: list[SemanticResult] = []
    for artifact in artifacts:
        profile = _profile(artifact)
        validator = registry.resolve(*profile) if profile is not None else None
        if not readiness[artifact["artifact_id"]]:
            results.append(
                _framework_result(
                    status="BLOCKED",
                    subject_kind="artifact",
                    subject=artifact,
                    profile=profile,
                    check_id="e7q.ir.framework.capability-negotiation-blocked",
                    message="Profile or required capability negotiation did not pass.",
                )
            )
        elif validator is None:
            results.append(
                _framework_result(
                    status="BLOCKED",
                    subject_kind="artifact",
                    subject=artifact,
                    profile=profile,
                    check_id="e7q.ir.framework.profile-validator-unavailable",
                    message="No semantic validator is installed for the declared profile.",
                )
            )
        else:
            results.extend(
                _invoke(
                    validator, "validate_artifact", "artifact", artifact, graph, profile
                )
            )
    for relation in graph["relations"]:
        source_profile = _profile(artifacts_by_id[relation["source"]])
        target_profile = _profile(artifacts_by_id[relation["target"]])
        profile = source_profile if source_profile == target_profile else None
        endpoints_ready = readiness[relation["source"]] and readiness[relation["target"]]
        if not endpoints_ready:
            results.append(
                _framework_result(
                    status="BLOCKED",
                    subject_kind="relation",
                    subject=relation,
                    profile=profile,
                    check_id="e7q.ir.framework.capability-negotiation-blocked",
                    message="A relation endpoint did not pass profile capability negotiation.",
                )
            )
            continue
        if profile is None:
            results.append(
                _framework_result(
                    status="BLOCKED",
                    subject_kind="relation",
                    subject=relation,
                    profile=None,
                    check_id="e7q.ir.framework.relation-profile-mismatch",
                    message="Relation endpoints do not share one installed semantic profile.",
                )
            )
            continue
        validator = registry.resolve(*profile)
        if validator is None:
            results.append(
                _framework_result(
                    status="BLOCKED",
                    subject_kind="relation",
                    subject=relation,
                    profile=profile,
                    check_id="e7q.ir.framework.profile-validator-unavailable",
                    message="No semantic validator is installed for the relation profile.",
                )
            )
        else:
            results.extend(
                _invoke(
                    validator, "validate_relation", "relation", relation, graph, profile
                )
            )
    status = aggregate_status(item.status for item in results)
    serialised = [item.as_dict() for item in results]
    serialised.sort(
        key=lambda item: (
            item["subject"]["kind"],
            item["subject"]["id"],
            item["check_id"],
            item["status"],
        )
    )
    return status, serialised


def aggregate_status(statuses: Iterable[str]) -> str:
    values = list(statuses)
    if not values:
        return "NOT_ASSESSED"
    for status in ("FAIL", "BLOCKED", "UNSUPPORTED", "NOT_ASSESSED"):
        if status in values:
            return status
    return "PASS"
