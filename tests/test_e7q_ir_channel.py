# SPDX-License-Identifier: Apache-2.0
import itertools
import numpy as np
import pytest
from test_e7q_ir_unitary import graph, source
from test_e7q_ir_measurement import measurement_graph
from e7q.ir.conformance import validate_graph
from e7q.ir.channel import CRITERION, PRESERVES, LOSSES, matrix_units
from e7q.ir.unitary import action
from e7q.openqasm2 import import_openqasm2
from e7q.language import Operation, Program, channel_superoperator


def channel_graph(left, right, n=2, **overrides):
    args = dict(criterion=dict(CRITERION), preserves=list(PRESERVES), loses=list(LOSSES))
    args.update(overrides)
    return graph(left, right, n, **args)


@pytest.mark.parametrize('left,right', [('', ''), ('x q[0]; z q[0];', 'z q[0]; x q[0];'),
    ('swap q[0],q[1];', 'cx q[0],q[1]; cx q[1],q[0]; cx q[0],q[1];')])
def test_equal_channels(left, right):
    g = channel_graph(left, right)
    r = validate_graph(g, level='F2')
    assert r['highest_level_passed'] == 'F2'
    assert r == validate_graph(g, level='F2')


@pytest.mark.parametrize('left', ['z q[0];', 'cz q[0],q[1];'])
def test_coherence_is_not_population(left):
    assert validate_graph(measurement_graph(left, ''), level='F2')['highest_level_passed'] == 'F2'
    assert validate_graph(channel_graph(left, ''), level='F2')['level_results']['F2'] == 'FAIL'


@pytest.mark.parametrize('args', [dict(loses=['global-and-relative-phase']), dict(assumptions=[]),
    dict(criterion={**CRITERION, 'tolerance': 1e-10}),
    dict(criterion={'id': CRITERION['id'], 'version': '2'})])
def test_contract(args):
    assert validate_graph(channel_graph('', '', **args), level='F2')['level_results']['F2'] == 'UNSUPPORTED'


def test_domain_budgets_and_status():
    for gates in ['h q[0];', 'reset q[0];', 'noise q[0];', 'if(c==0) x q[0];']:
        assert validate_graph(channel_graph(gates, ''), level='F2')['level_results']['F2'] == 'UNSUPPORTED'
    for n, gates in [(9, ''), (2, 'x q[0];'*257)]:
        assert validate_graph(channel_graph(gates, '', n), level='F2')['level_results']['F2'] == 'BLOCKED'
    assert validate_graph(channel_graph('', '', validation_status='not-assessed'), level='F2')['level_results']['F2'] == 'FAIL'


def test_against_native_superoperator_with_explicit_endianness():
    # IR q0 is least significant; native q0 is most significant. Reverse indices
    # in this test-only bridge; this does not publish a general native adapter.
    gates = {'x q[0];': Operation('X', (1,)), 'z q[1];': Operation('Z', (0,)),
             'cx q[0],q[1];': Operation('CX', (1,0)),
             'cz q[0],q[1];': Operation('CZ', (1,0)),
             'swap q[0],q[1];': Operation('SWAP', (1,0))}
    for word in itertools.product(gates, repeat=3):
        program = Program('oracle', 1, 'densitymatrix', None, 2, 2, 'oracle',
                          tuple(gates[g] for g in word), None, False)
        expected = channel_superoperator(program)
        columns, _ = action(import_openqasm2(source(''.join(word))))
        actual = np.zeros((16,16), dtype=int)
        for index, (row, col, sign) in enumerate(matrix_units(columns)):
            actual[row*4+col,index] = sign
        assert np.array_equal(actual, expected)


def test_independent_coherent_state_counterexample():
    # Z flips the off-diagonal entries of |+><+| while preserving its diagonal.
    rho = np.array([[1,1],[1,1]])  # common normalization cancels
    z = np.diag([1,-1])
    assert not np.array_equal(z @ rho @ z, rho)
    assert validate_graph(channel_graph('z q[0];', '', 1), level='F2')['level_results']['F2'] == 'FAIL'
