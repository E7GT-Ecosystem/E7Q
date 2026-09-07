import json
from pathlib import Path

import pytest

from e7q.ir.canonical import identified_digest
from e7q.ir.conformance import validate_graph
from e7q.ir.workflow import build_external_circuit_graph, load_external_circuit_manifest

EXAMPLE = Path(__file__).parents[1] / 'examples/e7q-ir/external-circuit-workflow.json'


def fixture():
    manifest, base = load_external_circuit_manifest(EXAMPLE)
    manifest['assessment']['expected_label_order'] = 'clbit-descending'
    return build_external_circuit_graph(manifest, base, include_circuit_content=True)


def rehash(graph):
    mapping = {}
    def rewrite(value):
        if isinstance(value, str):
            return mapping.get(value, value)
        if isinstance(value, list):
            return [rewrite(x) for x in value]
        if isinstance(value, dict):
            return {k: rewrite(v) for k,v in value.items()}
        return value
    for a in graph['artifacts']:
        old = a['artifact_id']
        a.update(rewrite(a))
        a['artifact_id'] = identified_digest(a, 'artifact_id')
        mapping[old] = a['artifact_id']
    for r in graph['relations']:
        r.update(rewrite(r))
        r['relation_id'] = identified_digest(r, 'relation_id')
    graph['graph_id'] = identified_digest(graph, 'graph_id')


def test_embedded_graph_checks_real_payloads_without_equivalence():
    graph = fixture()
    assert graph == fixture()
    report = validate_graph(graph, level='F2')
    assert report['status'] == 'NOT_ASSESSED'
    results = {r['subject']['id']:r for r in report['semantic_results']}
    for a in graph['artifacts']:
        assert results[a['artifact_id']]['status'] == ('NOT_ASSESSED' if a['kind'] in {'execution','transformation'} else 'PASS')
    assert report == validate_graph(graph, level='F2')
    assert report == json.loads((EXAMPLE.parent / 'f2-phase1b.json').read_text())


@pytest.mark.parametrize('kind,field,value,expected', [
    ('assessment','total_variation_distance',0.9,'FAIL'),
    ('assessment','observed_distribution',{'00':1.0},'FAIL'),
    ('assessment','maximum_total_variation',-1,'FAIL'),
    ('claim','support_status','unsupported','FAIL'),
    ('observation','shots',False,'FAIL'),
    ('observation','counts',{'000':1000},'BLOCKED'),
    ('observation','label_order','unknown','BLOCKED'),
    ('assessment','expected_label_order','clbit-ascending','BLOCKED'),
    ('source','content','wrong','FAIL'),
    ('source','format','openqasm-3','UNSUPPORTED'),
    ('source','content','x'*262145,'BLOCKED'),
])
def test_rehashed_tampering_fails_semantic_checks(kind, field, value, expected):
    graph = fixture()
    artifact = next(a for a in graph['artifacts'] if a['kind']==kind)
    artifact['payload'][field] = value
    rehash(graph)
    report = validate_graph(graph, level='F2')
    assert report['level_results']['F1'] == 'PASS'
    result = next(r for r in report['semantic_results'] if r['subject']['id']==artifact['artifact_id'])
    assert result['status'] == expected


def test_digest_only_legacy_graph_is_inspectable():
    manifest, base = load_external_circuit_manifest(EXAMPLE)
    graph = build_external_circuit_graph(manifest, base)
    assert validate_graph(graph)['status']=='PASS'
    assert validate_graph(graph, level='F2')['status']=='BLOCKED'


@pytest.mark.parametrize('observed', [{'00': True, '11': False}, {'00': 1, '11': False}])
def test_boolean_observed_probabilities_cannot_pass_after_rehash(observed):
    graph = fixture()
    observation = next(a for a in graph['artifacts'] if a['kind'] == 'observation')
    assessment = next(a for a in graph['artifacts'] if a['kind'] == 'assessment')
    observation['payload']['counts'] = {'00': 1000, '11': 0}
    assessment['payload'].update(expected_distribution={'00': 1.0, '11': 0.0},
                                 observed_distribution=observed, total_variation_distance=0.0,
                                 status='PASS')
    rehash(graph)
    report = validate_graph(graph, level='F2')
    assert report['level_results']['F1'] == 'PASS'
    result = next(r for r in report['semantic_results'] if r['subject']['id'] == assessment['artifact_id'])
    assert result['status'] == 'FAIL'
    assert result['check_id'] != 'e7q.ir.framework.validator-exception'
    claim = next(a for a in graph['artifacts'] if a['kind'] == 'claim')
    claim_result = next(r for r in report['semantic_results'] if r['subject']['id'] == claim['artifact_id'])
    assert claim_result['status'] == 'FAIL'
    assert report == validate_graph(graph, level='F2')


@pytest.mark.parametrize('order', [[], {}, ['clbit-descending'], None])
def test_malformed_label_order_has_scoped_blocked_result(order):
    graph = fixture()
    observation = next(a for a in graph['artifacts'] if a['kind'] == 'observation')
    observation['payload']['label_order'] = order
    rehash(graph)
    report = validate_graph(graph, level='F2')
    assert report['level_results']['F1'] == 'PASS'
    result = next(r for r in report['semantic_results'] if r['subject']['id'] == observation['artifact_id'])
    assert result['status'] == 'BLOCKED'
    assert result['check_id'] != 'e7q.ir.framework.validator-exception'


@pytest.mark.parametrize('field', ['total_variation_distance', 'maximum_total_variation'])
def test_extreme_finite_integer_is_rejected_without_validator_exception(field):
    graph = fixture()
    assessment = next(a for a in graph['artifacts'] if a['kind'] == 'assessment')
    assessment['payload'][field] = 10 ** 400
    rehash(graph)
    report = validate_graph(graph, level='F2')
    assert report['level_results']['F1'] == 'PASS'
    result = next(r for r in report['semantic_results'] if r['subject']['id'] == assessment['artifact_id'])
    assert result['status'] == 'FAIL'
    assert result['check_id'] != 'e7q.ir.framework.validator-exception'


def test_numeric_zero_one_probabilities_remain_valid():
    graph = fixture()
    observation = next(a for a in graph['artifacts'] if a['kind'] == 'observation')
    assessment = next(a for a in graph['artifacts'] if a['kind'] == 'assessment')
    observation['payload']['counts'] = {'00': 1000, '11': 0}
    assessment['payload'].update(expected_distribution={'00': 1, '11': 0},
                                 observed_distribution={'00': 1, '11': 0},
                                 total_variation_distance=0, status='PASS')
    rehash(graph)
    report = validate_graph(graph, level='F2')
    result = next(r for r in report['semantic_results'] if r['subject']['id'] == assessment['artifact_id'])
    assert result['status'] == 'PASS'
