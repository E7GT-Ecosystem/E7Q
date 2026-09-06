# SPDX-License-Identifier: Apache-2.0
import itertools
from pathlib import Path
import numpy as np
import pytest
from test_e7q_ir_unitary import graph, source
from e7q.ir.real_unitary import CRITERION, ASSUMPTIONS, exact_columns
from e7q.ir.conformance import validate_graph
from e7q.openqasm2 import import_openqasm2


def real_graph(left, right, n=2, **overrides):
    args = dict(criterion=dict(CRITERION), assumptions=list(ASSUMPTIONS))
    args.update(overrides)
    return graph(left, right, n, **args)


@pytest.mark.parametrize('left,right', [('h q[0];', 'u2(0,pi) q[0];'),
    ('h q[0]; h q[0];', ''), ('h q[0]; z q[0]; h q[0];', 'x q[0];'),
    ('h q[1]; cx q[0],q[1]; h q[1];', 'cz q[0],q[1];'),
    ('h q[0]; h q[0]; h q[0];', 'h q[0];')])
def test_exact_identities_across_h_counts(left, right):
    g = real_graph(left, right)
    r = validate_graph(g, level='F2')
    assert r['highest_level_passed'] == 'F2'
    assert r == validate_graph(g, level='F2')


@pytest.mark.parametrize('left,right', [('h q[0];', ''), ('h q[0];', 'h q[1];'),
    ('x q[0]; z q[0];', 'z q[0]; x q[0];'),
    ('h q[0]; x q[0];', 'x q[0]; h q[0];')])
def test_exact_difference(left, right):
    assert validate_graph(real_graph(left, right), level='F2')['level_results']['F2'] == 'FAIL'


@pytest.mark.parametrize('gates', ['u2(0,3.141592653589793) q[0];', 'u2(0,pi+0) q[0];',
    'u2(0.0,pi) q[0];', 's q[0];', 'if(c==0) h q[0];',
    'measure q[0] -> c[0]; h q[0];'])
def test_outside_fragment(gates):
    assert validate_graph(real_graph(gates, ''), level='F2')['level_results']['F2'] == 'UNSUPPORTED'


def test_budgets_and_contract():
    for n, gates in [(5, ''), (2, 'h q[0];'*65)]:
        assert validate_graph(real_graph(gates, '', n), level='F2')['level_results']['F2'] == 'BLOCKED'
    for args in [dict(assumptions=[]), dict(loses=[]), dict(criterion={**CRITERION, 'tolerance': 1e-9})]:
        assert validate_graph(real_graph('', '', **args), level='F2')['level_results']['F2'] == 'UNSUPPORTED'
    assert validate_graph(real_graph('', '', validation_status='not-assessed'), level='F2')['level_results']['F2'] == 'FAIL'
    assert validate_graph(graph('h q[0];', 'h q[0];'), level='F2')['level_results']['F2'] == 'UNSUPPORTED'


def original_external_graph():
    # Use the existing repository files, not rewritten circuit literals.
    from hashlib import sha256
    from e7q.ir.envelope import build_artifact
    from e7q.ir.graph import build_graph, build_relation
    from e7q.ir.unitary import PRESERVES, LOSSES
    artifacts = []
    root = Path(__file__).resolve().parents[1] / 'examples/e7q-ir'
    for kind, name in [('source', 'source.qasm'), ('representation', 'transpiled.qasm')]:
        text = (root / name).read_text()
        artifacts.append(build_artifact(kind, dict(format='openqasm-2', content=text,
            byte_length=len(text.encode()), content_digest='sha256:'+sha256(text.encode()).hexdigest()),
            profile_id='e7q.ir.circuit-basic', created_at='2026-09-06T00:00:00Z'))
    g = build_graph(artifacts, [build_relation('transforms', artifacts[0]['artifact_id'], artifacts[1]['artifact_id'],
        criterion=CRITERION, preserves=PRESERVES, loses=LOSSES, assumptions=ASSUMPTIONS, validation_status='validated')], name='Original H/u2 acceptance pair')
    return g


def test_original_external_source_pair():
    assert validate_graph(original_external_graph(), level='F2')['highest_level_passed'] == 'F2'


def test_independent_dense_matrix_oracle():
    h = np.array([[1,1],[1,-1]]) / np.sqrt(2)
    gates = {'h q[0];': np.kron(np.eye(2), h), 'x q[1];': np.kron([[0,1],[1,0]],np.eye(2)),
             'z q[0];': np.diag([1,-1,1,-1]),
             'cx q[0],q[1];': np.array([[1,0,0,0],[0,0,0,1],[0,0,1,0],[0,1,0,0]])}
    for word in itertools.product(gates, repeat=4):
        expected = np.eye(4)
        for gate in word:
            expected = gates[gate] @ expected
        columns, _ = exact_columns(import_openqasm2(source(''.join(word))))
        actual = np.array([[float(a)+float(b)*np.sqrt(2) for a,b in col] for col in columns]).T
        # Tolerance is only for this independent floating oracle, never the validator.
        assert np.allclose(actual, expected, atol=1e-14, rtol=0)
