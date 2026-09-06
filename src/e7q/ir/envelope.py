# SPDX-License-Identifier: Apache-2.0
"""Universal content-addressed artifact envelope for E7Q-IR."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

from .canonical import identified_digest


SCHEMA = "e7q.ir.artifact/v0alpha1"
KINDS = frozenset({
    "intent",
    "source",
    "representation",
    "transformation",
    "execution",
    "observation",
    "assessment",
    "claim",
})


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_artifact(
    kind: str,
    payload: dict[str, Any],
    *,
    profile_id: str = "e7q.ir.core",
    profile_version: str = "0alpha1",
    capabilities_required: Iterable[str] = (),
    created_at: str | None = None,
    actor: str = "unspecified",
    source_refs: Iterable[str] = (),
    limitations: Iterable[str] = (),
    extensions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a deterministic envelope when ``created_at`` is supplied."""
    if kind not in KINDS:
        raise ValueError(f"unsupported E7Q-IR artifact kind: {kind}")
    artifact: dict[str, Any] = {
        "schema": SCHEMA,
        "kind": kind,
        "profile": {
            "id": profile_id,
            "version": profile_version,
            "capabilities_required": sorted(set(capabilities_required)),
        },
        "provenance": {
            "created_at": created_at or _timestamp(),
            "actor": actor,
            "source_refs": list(source_refs),
        },
        "payload": payload,
        "limitations": list(limitations),
    }
    if extensions is not None:
        artifact["extensions"] = extensions
    artifact["artifact_id"] = identified_digest(artifact, "artifact_id")
    return artifact
