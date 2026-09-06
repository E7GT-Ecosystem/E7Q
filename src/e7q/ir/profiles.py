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


CORE = Profile(
    "e7q.ir.core",
    "0alpha1",
    frozenset({
        "artifact.identity",
        "claim.boundary",
        "observation.record",
        "transformation.accounting",
    }),
)

CIRCUIT_BASIC = Profile(
    "e7q.ir.circuit-basic",
    "0alpha1",
    CORE.capabilities | frozenset({
        "circuit.openqasm.source",
        "circuit.counts.observation",
        "circuit.distribution.tvd",
    }),
)

BUILTIN_PROFILES = {
    (profile.profile_id, profile.version): profile
    for profile in (CORE, CIRCUIT_BASIC)
}


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
