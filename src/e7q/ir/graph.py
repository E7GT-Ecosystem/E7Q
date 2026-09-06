# SPDX-License-Identifier: Apache-2.0
"""Evidence graph and typed relation construction."""
from __future__ import annotations

from typing import Any, Iterable

from .canonical import digest, identified_digest


SCHEMA = "e7q.ir.graph/v0alpha1"
RELATION_KINDS = frozenset({
    "represents",
    "transforms",
    "produces",
    "observes",
    "assesses",
    "supports",
    "constrains",
    "derived-from",
})


def build_relation(
    kind: str,
    source: str,
    target: str,
    *,
    criterion: dict[str, Any] | None = None,
    preserves: Iterable[str] = (),
    loses: Iterable[str] = (),
    assumptions: Iterable[str] = (),
    validation_status: str = "not-assessed",
) -> dict[str, Any]:
    if kind not in RELATION_KINDS:
        raise ValueError(f"unsupported E7Q-IR relation kind: {kind}")
    relation: dict[str, Any] = {
        "kind": kind,
        "source": source,
        "target": target,
        "validation_status": validation_status,
    }
    if criterion is not None:
        relation["criterion"] = criterion
    if kind == "transforms":
        relation.update({
            "preserves": list(preserves),
            "loses": list(loses),
            "assumptions": list(assumptions),
        })
    relation["relation_id"] = identified_digest(relation, "relation_id")
    return relation


def build_graph(
    artifacts: Iterable[dict[str, Any]],
    relations: Iterable[dict[str, Any]],
    *,
    name: str,
    extensions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    graph: dict[str, Any] = {
        "schema": SCHEMA,
        "name": name,
        "artifacts": list(artifacts),
        "relations": list(relations),
    }
    if extensions is not None:
        graph["extensions"] = extensions
    graph["graph_id"] = identified_digest(graph, "graph_id")
    return graph


def graph_summary(graph: dict[str, Any]) -> dict[str, Any]:
    artifacts = graph.get("artifacts", [])
    relations = graph.get("relations", [])
    kinds: dict[str, int] = {}
    for artifact in artifacts if isinstance(artifacts, list) else []:
        if isinstance(artifact, dict):
            kind = str(artifact.get("kind", "unknown"))
            kinds[kind] = kinds.get(kind, 0) + 1
    return {
        "schema": "e7q.ir.graph-summary/v0alpha1",
        "graph_id": graph.get("graph_id"),
        "name": graph.get("name"),
        "artifact_count": len(artifacts) if isinstance(artifacts, list) else 0,
        "relation_count": len(relations) if isinstance(relations, list) else 0,
        "artifact_kinds": dict(sorted(kinds.items())),
        "content_digest": digest(graph),
    }
