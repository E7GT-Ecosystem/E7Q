# SPDX-License-Identifier: Apache-2.0
"""Deterministic JSON encoding and content identities for E7Q-IR artifacts."""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Any


def canonical_bytes(value: Any) -> bytes:
    """Encode the v0alpha1 canonical JSON subset.

    The protocol deliberately names this encoding rather than claiming full
    RFC 8785 conformance.  Non-finite JSON numbers fail closed.
    """
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + sha256(canonical_bytes(value)).hexdigest()


def identified_digest(value: dict[str, Any], identity_field: str) -> str:
    content = {key: item for key, item in value.items() if key != identity_field}
    return digest(content)
