# SPDX-License-Identifier: Apache-2.0
"""Bounded, non-executing preservation adapters for native/legacy evidence."""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
import math
from pathlib import Path

from ..language import E7QError
from .canonical import canonical_bytes
from .conformance import validate_graph
from .envelope import build_artifact
from .graph import build_graph, build_relation

MAX_BYTES = 1024 * 1024
SCHEMAS = frozenset({
    'e7q.external-evidence-receipt/v1alpha1', 'e7q.execution-bundle/v1',
    'e7q.execution-result/v1', 'e7q.execution-receipt/v1',
    'e7q.deterministic-assessment/v1alpha1',
})
LIMITS = [
    'Import preserves supplied records; it does not validate their scientific or execution claims.',
    'Original status, IDs, ordering, proof and limitations are supplied data, not new IR verdicts.',
    'No execution, provider authentication, chronology or semantic equivalence is established.',
]


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def _float(text):
    value = float(text)
    if not math.isfinite(value):
        raise ValueError('non-finite JSON number')
    return value


def _constant(text):
    raise ValueError('non-finite JSON constant')


def _parse(text):
    value = json.loads(text, object_pairs_hook=_pairs, parse_float=_float, parse_constant=_constant)
    stack = [(value, 0)]
    count = 0
    while stack:
        item, depth = stack.pop()
        count += 1
        if depth > 64 or count > 100000:
            raise ValueError('legacy JSON structure exceeds budget')
        if isinstance(item, dict):
            stack.extend((v, depth + 1) for v in item.values())
        elif isinstance(item, list):
            stack.extend((v, depth + 1) for v in item)
    canonical_bytes(value)  # Ensure the projection belongs to the IR JSON subset.
    return value


def import_evidence(raw: bytes, *, format: str, created_at: str, name='Imported evidence'):
    """Preserve bytes and expose legacy JSON, without executing or upgrading it."""
    if not isinstance(raw, bytes) or len(raw) > MAX_BYTES:
        raise E7QError('evidence must be bytes within the 1 MiB input budget')
    if format not in ('e7q', 'legacy-json'):
        raise E7QError('supported import formats are e7q and legacy-json')
    if not isinstance(created_at, str) or not created_at:
        raise E7QError('an explicit import timestamp is required')
    try:
        text = raw.decode('utf-8')
        parsed = _parse(text) if format == 'legacy-json' else None
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise E7QError(f'invalid preserved evidence: {exc}') from exc
    if format == 'legacy-json' and (
        not isinstance(parsed, dict) or not isinstance(parsed.get('schema'), str)
        or parsed['schema'] not in SCHEMAS
    ):
        raise E7QError('unsupported legacy evidence schema')
    source = build_artifact('source', {
        'format': format, 'content': text, 'byte_length': len(raw),
        'content_digest': 'sha256:' + sha256(raw).hexdigest(),
        'adapter': 'e7q.ir.legacy-preservation/v1',
    }, created_at=created_at, actor='e7q.ir.legacy-preservation', limitations=LIMITS)
    artifacts, relations = [source], []
    if parsed is not None:
        representation = build_artifact('representation', {
            'format': 'legacy-json-object', 'legacy_schema': parsed['schema'],
            'legacy_payload': parsed,
        }, created_at=created_at, actor='e7q.ir.legacy-preservation',
           source_refs=[source['artifact_id']], limitations=LIMITS)
        artifacts.append(representation)
        relations.append(build_relation('transforms', source['artifact_id'], representation['artifact_id'],
            criterion={'id': 'e7q.ir.legacy-json-projection', 'version': '1'},
            preserves=['parsed-json-values', 'original-source-reference'],
            loses=['json-whitespace-and-escape-spelling-in-projection',
                   'numeric-spelling-and-possible-float-precision-in-projection'],
            assumptions=['supplied-evidence-is-not-authenticated'], validation_status='not-assessed'))
    graph = build_graph(artifacts, relations, name=name)
    if validate_graph(graph, level='F1')['status'] != 'PASS':
        raise E7QError('import metadata does not conform to the IR envelope')
    return graph


def recover_source(graph):
    """Recover original bytes; digest agreement is not authenticity."""
    if validate_graph(graph, level='F1')['status'] != 'PASS':
        raise E7QError('cannot recover from an invalid graph')
    sources = [a for a in graph['artifacts'] if a['kind'] == 'source']
    if len(sources) != 1:
        raise E7QError('recovery requires exactly one preserved source')
    p = sources[0]['payload']
    try:
        if p.get('adapter') != 'e7q.ir.legacy-preservation/v1' or not isinstance(p.get('content'), str):
            raise ValueError('not a preserved source')
        raw = p['content'].encode('utf-8')
        if len(raw) > MAX_BYTES or type(p.get('byte_length')) is not int or len(raw) != p['byte_length']:
            raise ValueError('source size mismatch')
        if p.get('content_digest') != 'sha256:' + sha256(raw).hexdigest():
            raise ValueError('source digest mismatch')
    except (ValueError, UnicodeError) as exc:
        raise E7QError(str(exc)) from exc
    return raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--format', required=True, choices=['e7q', 'legacy-json'])
    parser.add_argument('--created-at', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.input.resolve() == args.output.resolve() or (
            args.output.exists() and args.input.samefile(args.output)
        ):
            raise E7QError('output must not overwrite the source')
        with args.input.open('rb') as stream:
            raw = stream.read(MAX_BYTES + 1)
        graph = import_evidence(raw, format=args.format, created_at=args.created_at, name=args.input.name)
        args.output.write_bytes(canonical_bytes(graph) + b'\n')
    except (OSError, E7QError) as exc:
        parser.exit(2, f'{exc}\n')


if __name__ == '__main__':
    main()
