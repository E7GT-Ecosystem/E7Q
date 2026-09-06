# SPDX-License-Identifier: Apache-2.0
from hashlib import sha256
import itertools
import pytest
import numpy as np

from e7q.ir.envelope import build_artifact
from e7q.ir.graph import build_graph, build_relation
from e7q.ir.conformance import validate_graph
from e7q.ir.unitary import CRITERION, PRESERVES, LOSSES, ASSUMPTIONS, action
from e7q.openqasm2 import import_openqasm2


def source(gates, n=2):
    return f'OPENQASM 2.0; include "qelib1.inc"; qreg q[{n}]; creg c[{n}]; {gates} measure q -> c;'


def graph(left, right, n=2, **overrides):
    artifacts = []
    for kind, gates in [('source', left), ('representation', right)]:
        text = source(gates, n)
        artifacts.append(build_artifact(kind, dict(format='openqasm-2', content=text,
            byte_length=len(text.encode()), content_digest='sha256:'+sha256(text.encode()).hexdigest()),
            profile_id='e7q.ir.circuit-basic', created_at='2026-09-06T00:00:00Z'))
    args = dict(criterion=dict(CRITERION), preserves=list(PRESERVES), loses=list(LOSSES),
                assumptions=list(ASSUMPTIONS), validation_status='validated')
    args.update(overrides)
    return build_graph(artifacts, [build_relation('transforms', artifacts[0]['artifact_id'],
        artifacts[1]['artifact_id'], **args)], name='exact signed permutation')


@pytest.mark.parametrize('left,right', [
    ('x q[0]; x q[0];', ''), ('z q[1]; z q[1];', ''),
    ('cx q[0],q[1]; cx q[0],q[1];', ''),
    ('swap q[0],q[1];', 'cx q[0],q[1]; cx q[1],q[0]; cx q[0],q[1];'),
    ('cz q[0],q[1];', 'cz q[1],q[0];')])
def test_exact_equivalence(left, right):
    g = graph(left, right)
    r = validate_graph(g, level='F2')
    assert r['highest_level_passed'] == 'F2'
    assert r == validate_graph(g, level='F2')


@pytest.mark.parametrize('left,right', [
    ('x q[0];', ''), ('z q[0];', ''),
    ('x q[0]; z q[0];', 'z q[0]; x q[0];'),
    ('cx q[0],q[1];', 'cx q[1],q[0];')])
def test_exact_difference_including_phase(left, right):
    assert validate_graph(graph(left, right), level='F2')['level_results']['F2'] == 'FAIL'


@pytest.mark.parametrize('gates', ['h q[0];', 'rz(pi) q[0];', 'if(c==0) x q[0];',
    'cx q[0],q[0];', 'barrier q;', 'measure q[0] -> c[0]; x q[1];'])
def test_unsupported_is_not_inequality(gates):
    assert validate_graph(graph(gates, ''), level='F2')['level_results']['F2'] == 'UNSUPPORTED'


@pytest.mark.parametrize('n,gates', [(9, ''), (2, 'x q[0];'*257)])
def test_budgets(n, gates):
    assert validate_graph(graph(gates, '', n), level='F2')['level_results']['F2'] == 'BLOCKED'


def test_contract_and_declared_status():
    assert validate_graph(graph('', '', loses=[]), level='F2')['level_results']['F2'] == 'UNSUPPORTED'
    assert validate_graph(graph('', '', validation_status='not-assessed'), level='F2')['level_results']['F2'] == 'FAIL'


def test_against_independent_dense_gate_matrices():
    # Reference matrices use q[0] as the least significant bit. Exhaust all
    # length-three words, comparing every signed column, including phase.
    x = np.array([[0, 1], [1, 0]], dtype=int)
    z = np.diag([1, -1])
    eye = np.eye(2, dtype=int)
    gates = {
        'x q[0];': np.kron(eye, x), 'z q[1];': np.kron(z, eye),
        'cx q[0],q[1];': np.array([[1,0,0,0],[0,0,0,1],[0,0,1,0],[0,1,0,0]]),
        'cz q[0],q[1];': np.diag([1,1,1,-1]),
        'swap q[0],q[1];': np.array([[1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]])}
    for word in itertools.product(gates, repeat=3):
        expected = np.eye(4, dtype=int)
        for gate in word:
            expected = gates[gate] @ expected
        columns, _ = action(import_openqasm2(source(''.join(word))))
        actual = np.zeros((4,4), dtype=int)
        for col, (row, sign) in enumerate(columns):
            actual[row, col] = sign
        assert np.array_equal(actual, expected)
