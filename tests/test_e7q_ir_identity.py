# SPDX-License-Identifier: Apache-2.0
import copy
from hashlib import sha256

import pytest

from e7q.ir.canonical import identified_digest
from e7q.ir.circuit import BYTE_IDENTITY_CRITERION, MAX_SOURCE_BYTES
from e7q.ir.circuit import STRUCTURAL_IDENTITY_CRITERION, STRUCTURAL_LOSSES
from e7q.ir.conformance import validate_graph
from e7q.ir.envelope import build_artifact
from e7q.ir.graph import build_graph, build_relation

QASM = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\ncreg c[1];\nh q[0];\nmeasure q[0] -> c[0];\n'


def identity_graph(target_text=QASM, *, payload_change=None, relation_change=None):
    artifacts = []
    for kind, text in [('source', QASM), ('representation', target_text)]:
        raw = text.encode('utf-8')
        payload = dict(format='openqasm-2', content=text, byte_length=len(raw),
                       content_digest='sha256:' + sha256(raw).hexdigest())
        if kind == 'representation' and payload_change:
            payload_change(payload)
        artifacts.append(build_artifact(kind, payload,
            profile_id='e7q.ir.circuit-basic', created_at='2026-09-06T00:00:00Z'))
    relation = build_relation('transforms', artifacts[0]['artifact_id'], artifacts[1]['artifact_id'],
        criterion=copy.deepcopy(BYTE_IDENTITY_CRITERION), preserves=['utf8-bytes'],
        validation_status='validated')
    if relation_change:
        relation_change(relation)
        relation['relation_id'] = identified_digest(relation, 'relation_id')
    return build_graph(artifacts, [relation], name='bounded UTF-8 identity')


def test_byte_identity_end_to_end_and_deterministic():
    graph = identity_graph()
    report = validate_graph(graph, level='F2')
    assert report == validate_graph(graph, level='F2')
    assert report['status'] == 'PASS'
    assert report['highest_level_passed'] == 'F2'
    result = next(r for r in report['semantic_results'] if r['subject']['kind'] == 'relation')
    assert result['criterion'] == BYTE_IDENTITY_CRITERION
    assert result['evidence_refs'] == sorted(a['artifact_id'] for a in graph['artifacts'])


@pytest.mark.parametrize('text', [QASM + '// same behaviour\n', QASM.replace('h q', 'x q')])
def test_different_bytes_fail_without_semantic_inequality(text):
    report = validate_graph(identity_graph(text), level='F2')
    result = next(r for r in report['semantic_results'] if r['subject']['kind'] == 'relation')
    assert result['status'] == 'FAIL'
    assert 'quantum equivalence is not assessed' in result['message']


@pytest.mark.parametrize('change,status', [
    (lambda p: p.pop('content'), 'BLOCKED'),
    (lambda p: p.update(byte_length=1), 'FAIL'),
    (lambda p: p.update(content_digest='sha256:' + '0'*64), 'FAIL'),
    (lambda p: p.update(format='openqasm-3'), 'UNSUPPORTED'),
])
def test_identity_rechecks_payload_after_envelope_rehash(change, status):
    report = validate_graph(identity_graph(payload_change=change), level='F2')
    assert report['highest_level_passed'] == 'F1'
    result = next(r for r in report['semantic_results'] if r['subject']['kind'] == 'relation')
    assert result['status'] == status


@pytest.mark.parametrize('change,status', [
    (lambda r: r['criterion'].update(version='2'), 'UNSUPPORTED'),
    (lambda r: r['criterion'].update(ignore_whitespace=True), 'UNSUPPORTED'),
    (lambda r: r.update(preserves=['quantum-behaviour']), 'UNSUPPORTED'),
    (lambda r: r.update(validation_status='not-assessed'), 'FAIL'),
    (lambda r: r['criterion'].update(id='unknown'), 'NOT_ASSESSED'),
])
def test_identity_contract_is_bounded(change, status):
    report = validate_graph(identity_graph(relation_change=change), level='F2')
    assert report['level_results']['F2'] == status


def test_identity_resource_budget_blocks_before_parsing():
    report = validate_graph(identity_graph(QASM + ' ' * MAX_SOURCE_BYTES), level='F2')
    assert report['level_results']['F2'] == 'BLOCKED'


def structural_graph(text=QASM, change=None):
    def relation_change(r):
        r.update(criterion=copy.deepcopy(STRUCTURAL_IDENTITY_CRITERION),
                 preserves=['parsed-circuit-structure'], loses=list(STRUCTURAL_LOSSES))
        if change:
            change(r)
    return identity_graph(text, relation_change=relation_change)


@pytest.mark.parametrize('text', [QASM + '// comment\n', QASM.replace('h q', 'H q'),
    QASM.replace('measure q[0] -> c[0]', 'measure q -> c'),
    QASM.replace('h q[0]', 'h q[00]')])
def test_structural_projection_accepts_declared_normalizations(text):
    graph = structural_graph(text)
    report = validate_graph(graph, level='F2')
    assert report['highest_level_passed'] == 'F2'
    assert report == validate_graph(graph, level='F2')
    result = next(r for r in report['semantic_results'] if r['subject']['kind'] == 'relation')
    assert result['criterion'] == STRUCTURAL_IDENTITY_CRITERION


@pytest.mark.parametrize('text', [QASM.replace('h q', 'x q'),
    QASM.replace('qelib1.inc', 'other.inc'), QASM.replace('q[1]', 'q[2]'),
    QASM.replace('h q[0];', 'h q[0]; barrier q;'),
    QASM.replace('h q[0];', 'if(c==0) h q[0];')])
def test_structural_projection_preserves_material_fields(text):
    report = validate_graph(structural_graph(text), level='F2')
    assert report['level_results']['F2'] == 'FAIL'


@pytest.mark.parametrize('change,status', [
    (lambda r: r.update(loses=[]), 'UNSUPPORTED'),
    (lambda r: r['criterion'].update(version='2'), 'UNSUPPORTED'),
    (lambda r: r.update(validation_status='failed'), 'FAIL')])
def test_structural_contract_and_status(change, status):
    assert validate_graph(structural_graph(change=change), level='F2')['level_results']['F2'] == status


def test_huge_register_blocked_before_legacy_importer(monkeypatch):
    import e7q.ir.circuit as circuit
    def unexpected(*args, **kwargs):
        raise AssertionError('Parser must not run for excessive width')
    graph = identity_graph(QASM.replace('q[1]', 'q[999999999999]'))
    monkeypatch.setattr(circuit, 'import_openqasm2', unexpected)
    status, _ = circuit.validate_payload(graph['artifacts'][1], graph)
    assert status == 'BLOCKED'


def test_parameter_strings_are_not_algebraically_normalized():
    graph = structural_graph()
    texts = [QASM.replace('h q[0]', 'rz(pi/2) q[0]'),
             QASM.replace('h q[0]', 'rz(pi / 2) q[0]')]
    artifacts = []
    for kind, text in zip(['source', 'representation'], texts):
        raw = text.encode()
        artifacts.append(build_artifact(kind, dict(format='openqasm-2', content=text,
            byte_length=len(raw), content_digest='sha256:'+sha256(raw).hexdigest()),
            profile_id='e7q.ir.circuit-basic', created_at='2026-09-06T00:00:00Z'))
    r = graph['relations'][0]
    r.update(source=artifacts[0]['artifact_id'], target=artifacts[1]['artifact_id'])
    r['relation_id'] = identified_digest(r, 'relation_id')
    report = validate_graph(build_graph(artifacts, [r], name='parameters'), level='F2')
    assert report['level_results']['F2'] == 'FAIL'
