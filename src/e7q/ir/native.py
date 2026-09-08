# SPDX-License-Identifier: Apache-2.0
"""Explicit local execution of a bounded native E7Q subset into evidence artifacts."""
from __future__ import annotations

import argparse
from pathlib import Path

from ..language import E7QError, backend_profile, parse, run, verify
from .canonical import canonical_bytes
from .conformance import validate_graph
from .envelope import build_artifact
from .graph import build_graph, build_relation
from .legacy import MAX_BYTES, import_evidence
from .native_semantic import (
    ACTOR,
    CAPABILITIES_BY_KIND,
    LIMITS,
    PARSER_ASSUMPTIONS,
    PARSER_CRITERION,
    PARSER_LOSES,
    PARSER_PRESERVES,
    PROFILE_ID,
    PROFILE_VERSION,
    admit_native_program,
    implementation_versions,
    program_payload,
)


def execute_native(raw: bytes, *, created_at: str):
    """Parse and execute source explicitly; never execute imported legacy evidence."""
    preserved = import_evidence(raw, format="e7q", created_at=created_at)
    program = parse(raw.decode("utf-8"))
    admit_native_program(program)

    core_source = preserved["artifacts"][0]
    source = build_artifact(
        "source",
        core_source["payload"],
        profile_id=PROFILE_ID,
        profile_version=PROFILE_VERSION,
        capabilities_required=CAPABILITIES_BY_KIND["source"],
        created_at=created_at,
        actor=ACTOR,
        limitations=LIMITS,
    )
    artifacts, relations = [source], []

    def artifact(kind, payload, refs):
        item = build_artifact(
            kind,
            payload,
            profile_id=PROFILE_ID,
            profile_version=PROFILE_VERSION,
            capabilities_required=CAPABILITIES_BY_KIND[kind],
            created_at=created_at,
            actor=ACTOR,
            source_refs=[ref["artifact_id"] for ref in refs],
            limitations=LIMITS,
        )
        artifacts.append(item)
        return item

    def link(kind, left, right, **kwargs):
        relations.append(
            build_relation(
                kind,
                left["artifact_id"],
                right["artifact_id"],
                validation_status="validated",
                **kwargs,
            )
        )

    intent = artifact(
        "intent",
        {
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
        [source],
    )
    representation = artifact(
        "representation",
        {"format": "e7q.native-program/v1", "program": program_payload(program)},
        [source, intent],
    )
    link("represents", source, intent)
    link(
        "transforms",
        source,
        representation,
        criterion=PARSER_CRITERION,
        preserves=PARSER_PRESERVES,
        loses=PARSER_LOSES,
        assumptions=PARSER_ASSUMPTIONS,
    )

    result = verify(run(program))
    execution = artifact(
        "execution",
        {
            "format": "e7q.native-execution/v1",
            "backend_profile": backend_profile(program),
            "seed": program.seed,
            "shots": program.shots,
            "implementation": implementation_versions(),
            "proof": result["proof"],
        },
        [representation],
    )
    observation = artifact(
        "observation",
        {
            "format": "e7q.native-observation/v1",
            "counts": result["counts"],
            "probabilities": result["probabilities"],
            "label_order": "clbit-ascending",
            "bit_width": program.bits,
            "probability_basis": "reference-statevector-computational-basis",
        },
        [execution],
    )
    assessment = artifact(
        "assessment",
        {
            "format": "e7q.native-assessment/v1",
            "criterion": "e7q.language.verify",
            "tolerance": 1e-12,
            "native_result": result,
        },
        [intent, execution, observation],
    )
    link("produces", representation, execution)
    link("produces", execution, observation)
    link("assesses", assessment, observation)
    graph = build_graph(artifacts, relations, name=program.name)
    if validate_graph(graph, level="F2")["status"] != "PASS":
        raise E7QError("native execution graph failed installed semantic conformance")
    return graph


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--created-at", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.input.resolve() == args.output.resolve() or (
            args.output.exists() and args.input.samefile(args.output)
        ):
            raise E7QError("output must not overwrite source")
        with args.input.open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
        graph = execute_native(raw, created_at=args.created_at)
        args.output.write_bytes(canonical_bytes(graph) + b"\n")
    except (OSError, E7QError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
