# SPDX-License-Identifier: Apache-2.0
import itertools
import numpy as np
import pytest
from test_e7q_ir_unitary import graph
from test_e7q_ir_global_phase import phase_graph
from e7q.ir.conformance import validate_graph
from e7q.ir.measurement import CRITERION, PRESERVES, LOSSES, outcomes


def measurement_graph(left, right, n=2, **overrides):
    args = dict(criterion=dict(CRITERION), preserves=list(PRESERVES), loses=list(LOSSES))
    args.update(overrides)
    return graph(left, right, n, **args)


@pytest.mark.parametrize('left,right', [('z q[0];', ''), ('cz q[0],q[1];', ''),
    ('x q[0]; z q[0];', 'x q[0];')])
def test_phase_loss_is_not_unitary_equivalence(left, right):
    g = measurement_graph(left, right)
    r = validate_graph(g, level='F2')
    assert r['highest_level_passed'] == 'F2'
    assert r == validate_graph(g, level='F2')
    assert validate_graph(graph(left, right), level='F2')['level_results']['F2'] == 'FAIL'
    assert validate_graph(phase_graph(left, right), level='F2')['level_results']['F2'] == 'FAIL'


@pytest.mark.parametrize('left,right', [('x q[0];', ''), ('cx q[0],q[1];', ''),
    ('swap q[0],q[1];', ''), ('cx q[0],q[1];', 'cx q[1],q[0];')])
def test_all_inputs_not_just_zero(left, right):
    assert validate_graph(measurement_graph(left, right), level='F2')['level_results']['F2'] == 'FAIL'


@pytest.mark.parametrize('args', [dict(loses=[]), dict(assumptions=[]),
    dict(criterion={**CRITERION, 'tolerance': 0.01}),
    dict(criterion={'id': CRITERION['id'], 'version': '2'})])
def test_rejects_overclaims(args):
    assert validate_graph(measurement_graph('', '', **args), level='F2')['level_results']['F2'] == 'UNSUPPORTED'


def test_domain_and_budgets():
    for gates in ['h q[0];', 'reset q[0];', 'if(c==0) x q[0];', 'measure q[0] -> c[0]; x q[1];']:
        assert validate_graph(measurement_graph(gates, ''), level='F2')['level_results']['F2'] == 'UNSUPPORTED'
    for n, gates in [(9, ''), (2, 'x q[0];'*257)]:
        assert validate_graph(measurement_graph(gates, '', n), level='F2')['level_results']['F2'] == 'BLOCKED'
    assert validate_graph(measurement_graph('', '', validation_status='not-assessed'), level='F2')['level_results']['F2'] == 'FAIL'


def test_classical_bit_mapping():
    assert outcomes([(0, 1), (1, -1), (2, 1), (3, -1)], [(0, 1), (1, 0)]) == [0, 2, 1, 3]


def test_independent_dense_probability_oracle():
    gates = {'x q[0];': np.kron(np.eye(2, dtype=int), [[0,1],[1,0]]),
             'z q[1];': np.diag([1,1,-1,-1]),
             'cx q[0],q[1];': np.array([[1,0,0,0],[0,0,0,1],[0,0,1,0],[0,1,0,0]])}
    words = [()] + list(itertools.product(gates, repeat=1)) + list(itertools.product(gates, repeat=2))
    matrices = []
    for word in words:
        matrix = np.eye(4, dtype=int)
        for gate in word:
            matrix = gates[gate] @ matrix
        matrices.append(matrix ** 2)
    for i, left in enumerate(words):
        for j, right in enumerate(words):
            expected = 'PASS' if np.array_equal(matrices[i], matrices[j]) else 'FAIL'
            assert validate_graph(measurement_graph(''.join(left), ''.join(right)), level='F2')['level_results']['F2'] == expected
