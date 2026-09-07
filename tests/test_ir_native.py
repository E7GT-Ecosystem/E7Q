# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
import json
import subprocess
import sys
import pytest
from e7q.language import E7QError, parse, run, verify
from e7q.ir.native import execute_native
from e7q.ir.legacy import recover_source
from e7q.ir.conformance import validate_graph

STAMP = '2026-09-07T00:00:00Z'
BELL = Path('examples/bell.e7q').read_bytes()


def by_kind(graph, kind):
    return next(a['payload'] for a in graph['artifacts'] if a['kind'] == kind)


def test_native_bell_full_path_and_preservation():
    graph = execute_native(BELL, created_at=STAMP)
    assert [a['kind'] for a in graph['artifacts']] == [
        'source', 'intent', 'representation', 'execution', 'observation', 'assessment']
    assert recover_source(graph) == BELL
    result = verify(run(parse(BELL.decode())))
    assert by_kind(graph, 'assessment')['native_result'] == result
    assert by_kind(graph, 'execution')['proof'] == result['proof']
    assert by_kind(graph, 'observation')['counts'] == result['counts']
    assert graph == execute_native(BELL, created_at=STAMP)
    report = validate_graph(graph, level='F2')
    assert report['highest_level_passed'] == 'F1'
    assert report['status'] != 'PASS'
    assert all(r['validation_status'] == 'not-assessed' for r in graph['relations'])


def test_failed_invariant_is_not_lost():
    graph = execute_native(BELL.replace(b'{00, 11}', b'{00}'), created_at=STAMP)
    assert by_kind(graph, 'assessment')['native_result']['status'] == 'FAIL'
    assert validate_graph(graph, level='F1')['status'] == 'PASS'


def test_asymmetric_count_order_and_extra_bits():
    raw = BELL.replace(b'H q[0]', b'X q[0]').replace(b'  CX q[0], q[1]\n', b'')
    raw = raw.replace(b'bits c[2]', b'bits c[3]').replace(b'{00, 11}', b'{100}')
    observation = by_kind(execute_native(raw, created_at=STAMP), 'observation')
    assert observation['counts'] == {'100': 1000}
    assert observation['probabilities'] == {'100': 1.0}
    assert observation['label_order'] == 'clbit-ascending'
    assert observation['bit_width'] == 3


@pytest.mark.parametrize('old,new', [
    (b'backend: statevector', b'backend: densitymatrix'),
    (b'  seed: 7\n', b''),
    (b'shots: 1000', b'shots: 100001'),
    (b'q[2]', b'q[9]'),
    (b'c[2]', b'c[9]'),
    (b'  H q[0]', b'  measure q[0] -> c[0]\n  H q[0]'),
    (b'  H q[0]', b'  X q[0]\n' * 1024),
])
def test_unsupported_or_excessive_execution_rejected_before_run(monkeypatch, old, new):
    def forbidden(*args):
        pytest.fail('simulation must not run')
    monkeypatch.setattr('e7q.ir.native.run', forbidden)
    with pytest.raises(E7QError):
        execute_native(BELL.replace(old, new), created_at=STAMP)


def test_cli_native_execution(tmp_path):
    output = tmp_path / 'graph.json'
    subprocess.run([sys.executable, '-m', 'e7q.ir.native', 'examples/bell.e7q',
        '--created-at', STAMP, '--output', str(output)], check=True)
    graph = json.loads(output.read_text())
    assert recover_source(graph) == BELL
    assert by_kind(graph, 'assessment')['native_result']['status'] == 'PASS'
