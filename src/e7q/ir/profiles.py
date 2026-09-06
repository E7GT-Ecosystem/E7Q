# SPDX-License-Identifier: Apache-2.0
"""Built-in profile and capability declarations for E7Q-IR v0alpha1."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Profile:
    profile_id: str
    version: str
    capabilities: frozenset[str]
    semantic_validator_id: str | None = None


CORE = Profile(
    "e7q.ir.core",
    "0alpha1",
    frozenset({
        "artifact.identity",
        "claim.boundary",
        "observation.record",
        "transformation.accounting",
    }),
    None,
)

CIRCUIT_BASIC = Profile(
    "e7q.ir.circuit-basic",
    "0alpha1",
    CORE.capabilities | frozenset({
        "circuit.openqasm.source",
        "circuit.counts.observation",
        "circuit.distribution.tvd",
        "circuit.identity.utf8-bytes",
        "circuit.identity.parsed-structure",
        "circuit.unitary.signed-permutation",
    }),
    "e7q.ir.validator.circuit-basic/0alpha1",
)

BUILTIN_PROFILES = {
    (profile.profile_id, profile.version): profile
    for profile in (CORE, CIRCUIT_BASIC)
}


def semantic_validator_id(profile_value: Any) -> str | None:
    """Return declared validator metadata without performing negotiation."""
    if not isinstance(profile_value, dict):
        return None
    profile = BUILTIN_PROFILES.get(
        (profile_value.get("id"), profile_value.get("version"))
    )
    return profile.semantic_validator_id if profile is not None else None


def negotiate(profile_value: Any) -> dict[str, Any]:
    if not isinstance(profile_value, dict):
        return {
            "status": "BLOCKED",
            "profile": None,
            "unsupported_capabilities": [],
            "reason": "profile declaration is not an object",
        }
    profile_id = profile_value.get("id")
    version = profile_value.get("version")
    required = profile_value.get("capabilities_required", [])
    declared = BUILTIN_PROFILES.get((profile_id, version))
    if declared is None:
        return {
            "status": "BLOCKED",
            "profile": {"id": profile_id, "version": version},
            "unsupported_capabilities": list(required) if isinstance(required, list) else [],
            "reason": "profile is not installed",
        }
    unsupported = (
        sorted(set(required) - declared.capabilities)
        if isinstance(required, list) and all(isinstance(item, str) for item in required)
        else []
    )
    return {
        "status": "SUPPORTED" if not unsupported else "BLOCKED",
        "profile": {"id": profile_id, "version": version},
        "unsupported_capabilities": unsupported,
        "reason": None if not unsupported else "required capabilities are not installed",
    }
