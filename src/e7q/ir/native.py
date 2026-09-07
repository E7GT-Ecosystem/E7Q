# SPDX-License-Identifier: Apache-2.0
"""Explicit local execution of a bounded native E7Q subset into evidence artifacts."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from importlib.metadata import version

from ..language import E7QError, backend_profile, parse, run, verify
from .canonical import canonical_bytes
from .conformance import validate_graph
from .envelope import build_artifact
from .graph import build_graph, build_relation
from .legacy import MAX_BYTES, import_evidence

LIMITS = [
    'Local reference simulation only; no provider authentication or hardware fidelity.',
    'Native verifier results are recorded evidence, not IR F2 conformance.',
    'The supplied timestamp identifies this record, not authenticated execution time.',
    'State amplitudes and per-shot trajectories are not exported; counts lose phase information.',
]


def execute_native(raw: bytes, *, created_at: str):
    """Parse and execute source explicitly; never execute imported legacy evidence."""
    preserved = import_evidence(raw, format='e7q', created_at=created_at)
    program = parse(raw.decode('utf-8'))
    if program.backend != 'statevector':
        raise E7QError('native IR execution currently requires statevector')
    if program.qubits > 8 or program.bits > 8 or program.shots > 100000:
        raise E7QError('native IR execution budget: 8 qubits/bits and 100000 shots')
    if len(program.operations) > 1024:
        raise E7QError('native IR execution budget: 1024 operations')
    if program.seed is None:
        raise E7QError('native IR execution requires an explicit seed')
    if (not program.operations or program.operations[-1].gate != 'MEASURE'
        or not program.operations[-1].full_register
        or any(op.gate in {'MEASURE', 'ASSERT', 'NOISE'} or op.condition is not None
               for op in program.operations[:-1])):
        raise E7QError('native IR execution requires static gates and one terminal full-register measurement')

    source = preserved['artifacts'][0]
    artifacts, relations = [source], []

    def artifact(kind, payload, refs):
        item = build_artifact(kind, payload, created_at=created_at,
            actor='e7q.ir.native-execution/v1', source_refs=[r['artifact_id'] for r in refs],
            limitations=LIMITS)
        artifacts.append(item)
        return item

    def link(kind, left, right, **kwargs):
        relations.append(build_relation(kind, left['artifact_id'], right['artifact_id'], **kwargs))

    intent = artifact('intent', {
        'format': 'e7q.native-intent/v1', 'name': program.name, 'path': program.path,
        'require_normalized': program.require_normalized,
        'allowed_outcomes': sorted(program.allowed_outcomes) if program.allowed_outcomes is not None else None,
        'shots': program.shots, 'seed': program.seed, 'backend': program.backend,
    }, [source])
    # JSON normalization removes tuple/set implementation types; source is retained.
    parsed = asdict(program)
    parsed['allowed_outcomes'] = sorted(program.allowed_outcomes) if program.allowed_outcomes is not None else None
    parsed = json.loads(json.dumps(parsed))
    representation = artifact('representation', {
        'format': 'e7q.native-program/v1', 'program': parsed,
    }, [source, intent])
    link('represents', source, intent)
    link('transforms', source, representation,
        criterion={'id': 'e7q.ir.native-parser-projection', 'version': '1'},
        preserves=['parsed-program-fields', 'expanded-operation-order', 'original-source-reference'],
        loses=['comments-and-formatting-in-projection', 'subpath-call-boundaries-in-expanded-operations'],
        assumptions=['native-parser-implementation'])

    result = verify(run(program))
    execution = artifact('execution', {
        'format': 'e7q.native-execution/v1', 'backend_profile': backend_profile(program),
        'seed': program.seed, 'shots': program.shots,
        'implementation': {'e7q': version('e7q'), 'numpy': version('numpy')},
        'proof': result['proof'],
    }, [representation])
    observation = artifact('observation', {
        'format': 'e7q.native-observation/v1',
        'counts': result['counts'], 'probabilities': result['probabilities'],
        'label_order': 'clbit-ascending', 'bit_width': program.bits,
        'probability_basis': 'reference-statevector-computational-basis',
    }, [execution])
    assessment = artifact('assessment', {
        'format': 'e7q.native-assessment/v1', 'criterion': 'e7q.language.verify',
        'tolerance': 1e-12, 'native_result': result,
    }, [intent, execution, observation])
    link('produces', representation, execution)
    link('produces', execution, observation)
    link('assesses', assessment, observation)
    graph = build_graph(artifacts, relations, name=program.name)
    if validate_graph(graph, level='F1')['status'] != 'PASS':
        raise E7QError('native execution graph failed structural conformance')
    return graph


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--created-at', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.input.resolve() == args.output.resolve() or (
            args.output.exists() and args.input.samefile(args.output)
        ):
            raise E7QError('output must not overwrite source')
        with args.input.open('rb') as stream:
            raw = stream.read(MAX_BYTES + 1)
        graph = execute_native(raw, created_at=args.created_at)
        args.output.write_bytes(canonical_bytes(graph) + b'\n')
    except (OSError, E7QError) as exc:
        parser.exit(2, f'{exc}\n')


if __name__ == '__main__':
    main()
