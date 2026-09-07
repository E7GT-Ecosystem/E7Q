# SPDX-License-Identifier: Apache-2.0
import json
import subprocess
import sys
import pytest
from e7q.ir.legacy import import_evidence, recover_source, MAX_BYTES
from e7q.ir.conformance import validate_graph
from e7q.language import E7QError
from e7q.external_bundles import verify_external_bundle

STAMP = '2026-09-07T00:00:00Z'


def test_external_receipt_roundtrip_and_no_assurance_upgrade():
    receipt = verify_external_bundle('examples/external-evidence-synthetic', include_counts=True)
    raw = json.dumps(receipt, indent=3).encode() + b'\n\n'
    graph = import_evidence(raw, format='legacy-json', created_at=STAMP)
    assert graph == import_evidence(raw, format='legacy-json', created_at=STAMP)
    assert recover_source(graph) == raw
    assert graph['artifacts'][1]['payload']['legacy_payload'] == receipt
    report = validate_graph(graph, level='F2')
    assert report['highest_level_passed'] == 'F1'
    assert report['level_results']['F2'] != 'PASS'
    assert graph['relations'][0]['validation_status'] == 'not-assessed'


def test_native_source_is_preserved_without_execution():
    raw = b'// native source preserved without parsing\nprogram Bell {}\n'
    graph = import_evidence(raw, format='e7q', created_at=STAMP)
    assert recover_source(graph) == raw
    assert validate_graph(graph, level='F1')['status'] == 'PASS'
    assert validate_graph(graph, level='F2')['status'] != 'PASS'


@pytest.mark.parametrize('raw', [b'{"schema":"x"}', b'{"schema":"x","schema":"y"}', b'{"x":NaN}', b'{"x":1e999}', b'\xff', b'['*70+b'0'+b']'*70, b' '* (MAX_BYTES+1)])
def test_invalid_or_excessive_legacy_input(raw):
    with pytest.raises(E7QError):
        import_evidence(raw, format='legacy-json', created_at=STAMP)


def test_failed_legacy_status_is_retained():
    raw = b'{"schema":"e7q.execution-result/v1","status":"FAIL","proof":[],"custom_id":"original"}'
    graph = import_evidence(raw, format='legacy-json', created_at=STAMP)
    assert graph['artifacts'][1]['payload']['legacy_payload']['status'] == 'FAIL'
    assert recover_source(graph) == raw


def test_cli_native_import(tmp_path):
    source = tmp_path / 'source.e7q'
    output = tmp_path / 'graph.json'
    source.write_bytes(b'// preserved source\n')
    subprocess.run([sys.executable, '-m', 'e7q.ir.legacy', str(source), '--format', 'e7q', '--created-at', STAMP, '--output', str(output)], check=True)
    assert recover_source(json.loads(output.read_text())) == source.read_bytes()

def test_recovery_rejects_rehashed_digest_mismatch():
    from e7q.ir.envelope import build_artifact
    from e7q.ir.graph import build_graph
    graph = import_evidence(b'original', format='e7q', created_at=STAMP)
    payload = dict(graph['artifacts'][0]['payload'], content_digest='sha256:' + '0' * 64)
    altered = build_graph([build_artifact('source', payload, created_at=STAMP)], [], name='altered')
    assert validate_graph(altered, level='F1')['status'] == 'PASS'
    with pytest.raises(E7QError, match='digest mismatch'):
        recover_source(altered)


def test_cli_rejects_source_hardlink(tmp_path):
    source = tmp_path / 'source.e7q'
    output = tmp_path / 'alias.e7q'
    source.write_bytes(b'original')
    output.hardlink_to(source)
    result = subprocess.run([sys.executable, '-m', 'e7q.ir.legacy', str(source),
        '--format', 'e7q', '--created-at', STAMP, '--output', str(output)], capture_output=True)
    assert result.returncode == 2
    assert source.read_bytes() == b'original'
