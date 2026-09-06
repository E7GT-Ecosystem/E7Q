# SPDX-License-Identifier: Apache-2.0
import itertools
import numpy as np
import pytest
from test_e7q_ir_unitary import graph
from e7q.ir.conformance import validate_graph
from e7q.ir.unitary import GLOBAL_PHASE_CRITERION, GLOBAL_PHASE_PRESERVES, GLOBAL_PHASE_LOSSES


def phase_graph(left, right, n=2, **overrides):
    args = dict(criterion=dict(GLOBAL_PHASE_CRITERION),
                preserves=list(GLOBAL_PHASE_PRESERVES), loses=list(GLOBAL_PHASE_LOSSES))
    args.update(overrides)
    return graph(left, right, n, **args)


@pytest.mark.parametrize('left,right', [('', ''),
    ('x q[0]; z q[0];', 'z q[0]; x q[0];'),
    ('x q[0]; z q[0]; x q[0]; z q[0];', '')])
def test_global_sign_passes_but_exact_remains_strict(left, right):
    g = phase_graph(left, right)
    report = validate_graph(g, level='F2')
    assert report['highest_level_passed'] == 'F2'
    assert report == validate_graph(g, level='F2')
    if left != right:
        assert validate_graph(graph(left, right), level='F2')['level_results']['F2'] == 'FAIL'


@pytest.mark.parametrize('left,right', [('z q[0];', ''), ('cz q[0],q[1];', ''),
    ('x q[0];', ''), ('cx q[0],q[1];', 'cx q[1],q[0];')])
def test_relative_phase_and_permutation_differences_fail(left, right):
    assert validate_graph(phase_graph(left, right), level='F2')['level_results']['F2'] == 'FAIL'


@pytest.mark.parametrize('overrides', [dict(loses=['source-spelling-and-gate-decomposition']),
    dict(preserves=['unitary-prefix', 'terminal-measurement-map']),
    dict(criterion={'id': GLOBAL_PHASE_CRITERION['id'], 'version': '2'}),
    dict(criterion={**GLOBAL_PHASE_CRITERION, 'tolerance': 0.1})])
def test_unsupported_contract(overrides):
    assert validate_graph(phase_graph('', '', **overrides), level='F2')['level_results']['F2'] == 'UNSUPPORTED'


def test_inherited_boundaries():
    for gates in ['h q[0];', 'if(c==0) x q[0];', 'measure q[0] -> c[0]; x q[1];']:
        assert validate_graph(phase_graph(gates, ''), level='F2')['level_results']['F2'] == 'UNSUPPORTED'
    for n, gates in [(9, ''), (2, 'x q[0];'*257)]:
        assert validate_graph(phase_graph(gates, '', n), level='F2')['level_results']['F2'] == 'BLOCKED'
    assert validate_graph(phase_graph('', '', validation_status='not-assessed'), level='F2')['level_results']['F2'] == 'FAIL'


def test_dense_oracle_for_all_pairs_of_short_one_qubit_words():
    # Independently multiply explicit matrices and compare U=V or U=-V.
    gates = {'x q[0];': np.array([[0, 1], [1, 0]]), 'z q[0];': np.diag([1, -1])}
    words = [()] + [w for length in range(1, 4) for w in itertools.product(gates, repeat=length)]
    matrices = []
    for word in words:
        matrix = np.eye(2, dtype=int)
        for gate in word:
            matrix = gates[gate] @ matrix
        matrices.append(matrix)
    for i, left in enumerate(words):
        for j, right in enumerate(words):
            equal = np.array_equal(matrices[i], matrices[j]) or np.array_equal(matrices[i], -matrices[j])
            result = validate_graph(phase_graph(''.join(left), ''.join(right), 1), level='F2')
            assert result['level_results']['F2'] == ('PASS' if equal else 'FAIL')
