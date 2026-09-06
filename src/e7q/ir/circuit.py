# SPDX-License-Identifier: Apache-2.0
"""Bounded circuit-basic payload checks; never execute supplied programs."""
from hashlib import sha256
import math
import re

from ..language import E7QError
from ..openqasm2 import import_openqasm2

MAX_SOURCE_BYTES = 262144
MAX_OUTCOMES = 65536
BYTE_IDENTITY_CRITERION = {'id': 'e7q.ir.utf8-byte-identity', 'version': '1'}
STRUCTURAL_IDENTITY_CRITERION = {'id': 'e7q.ir.openqasm2-structural-identity', 'version': '1'}
STRUCTURAL_LOSSES = ['source-text-and-comments', 'gate-name-case',
                     'register-expansion-spelling', 'numeric-index-spelling',
                     'declaration-interleaving']


class CheckError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message


def require(condition, message, status="FAIL"):
    if not condition:
        raise CheckError(status, message)


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def parse_source(artifact):
    p = artifact['payload']
    require(p.get('format') == 'openqasm-2', 'Only declared openqasm-2 is supported.', 'UNSUPPORTED')
    text = p.get('content')
    require(isinstance(text, str), 'Source bytes are not embedded; identity alone cannot validate syntax.', 'BLOCKED')
    require(len(text) <= MAX_SOURCE_BYTES, 'Source exceeds parser byte budget.', 'BLOCKED')
    raw = text.encode('utf-8')
    require(len(raw) <= MAX_SOURCE_BYTES, 'Source exceeds parser byte budget.', 'BLOCKED')
    require(type(p.get('byte_length')) is int and len(raw) == p['byte_length'], 'Source byte length mismatch.')
    require('sha256:' + sha256(raw).hexdigest() == p.get('content_digest'), 'Source byte digest mismatch.')
    # Bound register expansion and conditional arithmetic before invoking the
    # legacy importer, whose whole-register operations allocate per bit.
    clean = '\n'.join(line.split('//', 1)[0] for line in text.splitlines())
    widths = re.findall(r'\b(?:qreg|creg)\s+[A-Za-z_][A-Za-z0-9_]*\[(\d+)\]', clean)
    require(all(len(w) <= 128 and len(w.lstrip('0')) <= 4 for w in widths), 'Register width exceeds budget.', 'BLOCKED')
    sizes = [int(w) for w in widths]
    require(all(w <= 4096 for w in sizes) and sum(sizes) <= 8192,
            'Register width exceeds budget.', 'BLOCKED')
    require(sum(sizes) * clean.count(';') <= 262144,
            'Conservative expanded-operation budget exceeded.', 'BLOCKED')
    try:
        return import_openqasm2(text)
    except E7QError:
        raise CheckError('UNSUPPORTED', 'Source is invalid or outside the bounded OpenQASM 2 importer surface.')


def parent(artifact, by_id, kind):
    found = [by_id[r] for r in artifact['provenance']['source_refs'] if by_id[r]['kind'] == kind]
    require(len(found) == 1, f'Exactly one {kind} provenance parent is required.', 'BLOCKED')
    return found[0]


def counts(artifact, by_id):
    p = artifact['payload']
    values, shots = p.get('counts'), p.get('shots')
    require(isinstance(values, dict) and bool(values), 'Counts must be nonempty.')
    require(len(values) <= MAX_OUTCOMES, 'Outcome budget exceeded.', 'BLOCKED')
    require(type(shots) is int and shots > 0, 'Shots must be positive integers.')
    require(all(isinstance(k, str) and k and not set(k)-{'0','1'} and type(v) is int and v >= 0 for k,v in values.items()), 'Invalid binary counts.')
    require(sum(values.values()) == shots, 'Count total differs from shots.')
    require(p.get('label_order') in {'clbit-ascending','clbit-descending'}, 'Explicit label order is required.', 'BLOCKED')
    execution = parent(artifact, by_id, 'execution')
    representation = parent(execution, by_id, 'representation')
    parsed = parse_source(representation)
    registers = parsed['registers']['classical']
    require(len(registers) == 1, 'Multiple classical registers require a separate ordering profile.', 'UNSUPPORTED')
    require(all(len(k) == registers[0]['width'] for k in values), 'Count width differs from classical register.', 'BLOCKED')
    return {k: v/shots for k,v in sorted(values.items())}


def assessment(artifact, by_id):
    p = artifact['payload']
    require(p.get('method') == 'total-variation-distance', 'Assessment method is not supported.', 'UNSUPPORTED')
    observation = parent(artifact, by_id, 'observation')
    require(p.get('observation_ref') == observation['artifact_id'], 'Assessment observation reference mismatch.')
    observed = counts(observation, by_id)
    expected = p.get('expected_distribution')
    require(isinstance(expected, dict) and bool(expected), 'Expected distribution required.')
    require(len(expected) <= MAX_OUTCOMES, 'Distribution budget exceeded.', 'BLOCKED')
    width = len(next(iter(observed)))
    require(all(isinstance(k,str) and len(k)==width and not set(k)-{'0','1'} and number(v) and 0 <= v <= 1 for k,v in expected.items()), 'Invalid reference distribution.')
    require(abs(math.fsum(expected.values())-1) <= 1e-9, 'Reference probabilities must sum to one.')
    require(p.get('expected_label_order') == observation['payload']['label_order'], 'Reference and observed label orders must be explicitly identical.', 'BLOCKED')
    require(p.get('observed_distribution') == observed, 'Observed distribution was not correctly recomputed.')
    tvd = 0.5 * math.fsum(abs(observed.get(k,0)-expected.get(k,0)) for k in sorted(set(observed)|set(expected)))
    require(number(p.get('total_variation_distance')) and abs(p['total_variation_distance']-tvd) <= 1e-12, 'TVD mismatch.')
    threshold = p.get('maximum_total_variation')
    require(number(threshold) and 0 <= threshold <= 1, 'Invalid TVD threshold.')
    status = 'PASS' if tvd <= threshold else 'FAIL'
    require(p.get('status') == status, 'Assessment status disagrees with threshold.')
    return status


def validate_payload(artifact, graph):
    by_id = {a['artifact_id']:a for a in graph['artifacts']}
    kind, p = artifact['kind'], artifact['payload']
    try:
        if kind in {'source','representation'}:
            parse_source(artifact)
        elif kind == 'observation':
            counts(artifact, by_id)
        elif kind == 'assessment':
            assessment(artifact, by_id)
        elif kind == 'claim':
            source = parent(artifact, by_id, 'assessment')
            require(p.get('evidence_refs') == [source['artifact_id']], 'Claim evidence must identify its assessment.')
            status = assessment(source, by_id)
            require(p.get('support_status') == ('supported-within-declared-scope' if status == 'PASS' else 'unsupported'), 'Claim support contradicts assessment.')
            require(bool(p.get('boundaries')) and bool(p.get('prohibited_inferences')) and all(b in artifact['limitations'] for b in p['boundaries']), 'Claim boundaries must be retained in limitations.')
        else:
            return 'NOT_ASSESSED', 'Execution and transformation semantics remain outside Phase 1B.'
    except CheckError as exc:
        return exc.status, exc.message
    return 'PASS', 'Pinned circuit-basic payload checks passed; not equivalence, execution authentication, or truth.'


def validate_relation_payload(relation, graph):
    by_id = {a['artifact_id']: a for a in graph['artifacts']}
    kind = relation['kind']
    if kind == 'transforms' and relation.get('criterion', {}).get('id') == 'e7q.ir.signed-permutation-unitary-channel':
        from .channel import validate
        return validate(relation, graph)
    if kind == 'transforms' and relation.get('criterion', {}).get('id') == 'e7q.ir.signed-permutation-basis-measurement':
        from .measurement import validate
        return validate(relation, graph)
    if kind == 'transforms' and relation.get('criterion', {}).get('id') in {
            'e7q.ir.signed-permutation-unitary', 'e7q.ir.signed-permutation-global-phase'}:
        from .unitary import validate
        return validate(relation, graph)
    if kind == 'transforms' and relation.get('criterion', {}).get('id') == BYTE_IDENTITY_CRITERION['id']:
        return validate_byte_identity(relation, by_id)
    if kind == 'transforms' and relation.get('criterion', {}).get('id') == STRUCTURAL_IDENTITY_CRITERION['id']:
        return validate_structural_identity(relation, by_id)
    if kind not in {'assesses', 'supports'}:
        return 'NOT_ASSESSED', 'This relation needs a separately implemented criterion.'
    source, target = by_id[relation['source']], by_id[relation['target']]
    try:
        expected = ('observation', 'assessment') if kind == 'assesses' else ('assessment', 'claim')
        require((source['kind'], target['kind']) == expected, 'Relation endpoint kinds do not match the circuit profile.')
        require(parent(target, by_id, source['kind'])['artifact_id'] == source['artifact_id'], 'Relation contradicts payload provenance.')
        status, message = validate_payload(target, graph)
        if status != 'PASS':
            return status, message
        declared = 'validated' if kind == 'assesses' else ('supported' if target['payload']['support_status'] == 'supported-within-declared-scope' else 'failed')
        require(relation['validation_status'] == declared, 'Relation status contradicts recomputed evidence.')
    except CheckError as exc:
        return exc.status, exc.message
    return 'PASS', 'Relation matches its recomputed payload evidence; no broader claim established.'


def validate_byte_identity(relation, by_id):
    """Compare embedded UTF-8 bytes in the bounded OpenQASM 2 profile."""
    try:
        require(relation['criterion'] == BYTE_IDENTITY_CRITERION,
                'Unsupported byte-identity criterion version or options.', 'UNSUPPORTED')
        require(relation['preserves'] == ['utf8-bytes'] and
                relation['loses'] == [] and relation['assumptions'] == [],
                'Byte identity admits only utf8-bytes preservation, with no loss or assumptions.',
                'UNSUPPORTED')
        source, target = by_id[relation['source']], by_id[relation['target']]
        require(source['kind'] in {'source', 'representation'} and
                target['kind'] in {'source', 'representation'},
                'Byte identity requires source or representation endpoints.')
        # Revalidate embedded content, digest, length, format and parser budget.
        # No digest-only, external-file or execution fallback is permitted.
        parse_source(source)
        parse_source(target)
        require(source['payload']['content'].encode('utf-8') ==
                target['payload']['content'].encode('utf-8'),
                'Embedded UTF-8 bytes differ; quantum equivalence is not assessed.')
        require(relation['validation_status'] == 'validated',
                'Declared relation status disagrees with established byte identity.')
    except CheckError as exc:
        return exc.status, exc.message
    return 'PASS', 'Embedded UTF-8 bytes are identical; no execution or general quantum-equivalence claim is established.'


def structural_projection(parsed):
    """Version-1 comparison carrier; source hashes/proof wrappers are excluded."""
    return {key: parsed[key] for key in ('schema', 'language', 'registers', 'operations')}


def validate_structural_identity(relation, by_id):
    try:
        require(relation['criterion'] == STRUCTURAL_IDENTITY_CRITERION,
                'Unsupported structural-identity version or options.', 'UNSUPPORTED')
        require(relation['preserves'] == ['parsed-circuit-structure'] and
                sorted(relation['loses']) == sorted(STRUCTURAL_LOSSES) and
                relation['assumptions'] == [],
                'Structural identity requires its exact preservation and projection-loss contract.',
                'UNSUPPORTED')
        source, target = by_id[relation['source']], by_id[relation['target']]
        require(source['kind'] in {'source', 'representation'} and
                target['kind'] in {'source', 'representation'},
                'Structural identity requires source or representation endpoints.')
        left, right = parse_source(source), parse_source(target)
        require(structural_projection(left) == structural_projection(right),
                'Parsed structures differ; quantum equivalence is not assessed.')
        require(relation['validation_status'] == 'validated',
                'Declared relation status disagrees with established structural identity.')
    except CheckError as exc:
        return exc.status, exc.message
    return 'PASS', 'Pinned parsed structures match; includes are unresolved and quantum equivalence is not assessed.'
