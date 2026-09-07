# SPDX-License-Identifier: Apache-2.0
from types import SimpleNamespace

import pytest

from e7q.ir.qcec import evaluate, map_verdict
from e7q.ir.unitary import CRITERION, GLOBAL_PHASE_CRITERION

STAMP = '2026-09-07T00:00:00Z'
REFS = ('sha256:' + '1' * 64, 'sha256:' + '2' * 64)


@pytest.mark.parametrize(('raw', 'criterion', 'timed_out', 'expected'), [
    ('equivalent', CRITERION['id'], False, ('PASS', 'ESTABLISHED')),
    ('equivalent', GLOBAL_PHASE_CRITERION['id'], False, ('PASS', 'ESTABLISHED')),
    ('equivalent_up_to_global_phase', CRITERION['id'], False, ('FAIL', 'REFUTED')),
    ('equivalent_up_to_global_phase', GLOBAL_PHASE_CRITERION['id'], False, ('PASS', 'ESTABLISHED')),
    ('not_equivalent', CRITERION['id'], False, ('FAIL', 'REFUTED')),
    ('probably_equivalent', CRITERION['id'], False, ('NOT_ASSESSED', 'INCONCLUSIVE')),
    ('probably_not_equivalent', CRITERION['id'], False, ('NOT_ASSESSED', 'INCONCLUSIVE')),
    ('no_information', CRITERION['id'], False, ('NOT_ASSESSED', 'INCONCLUSIVE')),
    ('no_information', CRITERION['id'], True, ('BLOCKED', 'INCONCLUSIVE')),
])
def test_verdict_mapping_never_upgrades_weaker_results(raw, criterion, timed_out, expected):
    assert map_verdict(raw, criterion, timed_out=timed_out) == expected


class Result:
    def __init__(self, verdict, check_time=0.01):
        self.verdict = verdict
        self.check_time = check_time

    def json(self):
        return {
            'equivalence': self.verdict,
            'preprocessing_time': 0.001,
            'check_time': self.check_time,
            'checkers': [{'checker': 'decision_diagram_alternating', 'runtime': 0.009,
                          'equivalence': self.verdict}],
        }


def backend(verdict, check_time=0.01):
    def run(*args, **kwargs):
        assert kwargs == {
            'timeout': 1.0, 'nthreads': 1, 'parallel': False,
            'max_sims': 4, 'seed': 7,
        }
        return Result(verdict, check_time)
    return run


def assessment(verdict, criterion=CRITERION, check_time=0.01):
    return evaluate(
        'left.qasm', 'right.qasm', criterion=criterion, source_refs=REFS,
        created_at=STAMP, timeout_seconds=1.0, nthreads=1,
        max_simulations=4, seed=7,
        verify_backend=backend(verdict, check_time),
    )


def test_assessment_records_backend_criterion_method_resources_and_raw_result():
    artifact = assessment('equivalent_up_to_global_phase', GLOBAL_PHASE_CRITERION)
    payload = artifact['payload']
    assert artifact['kind'] == 'assessment'
    assert artifact['provenance']['source_refs'] == list(REFS)
    assert payload['criterion'] == GLOBAL_PHASE_CRITERION
    assert payload['backend']['id'] == 'mqt.qcec'
    assert payload['configuration']['timeout_seconds'] == 1.0
    assert payload['method']['kind'] == 'tolerance-based-numerical'
    assert payload['method']['exact_algebraic'] is False
    assert payload['outcome']['status'] == 'PASS'
    assert payload['outcome']['raw_verdict'] == 'equivalent_up_to_global_phase'
    assert payload['resource_use']['process_peak_rss_bytes'] > 0
    assert payload['raw_result']['checkers'][0]['checker'] == 'decision_diagram_alternating'
    assert any('not default' in item for item in artifact['limitations'])


def test_timeout_is_resource_blocked_and_still_inconclusive():
    artifact = evaluate(
        'left.qasm', 'right.qasm', criterion=CRITERION, source_refs=REFS,
        created_at=STAMP, timeout_seconds=0.001,
        verify_backend=lambda *args, **kwargs: Result('no_information', 0.001),
    )
    assert artifact['payload']['outcome'] == {
        'status': 'BLOCKED',
        'conclusion': 'INCONCLUSIVE',
        'raw_verdict': 'no_information',
        'timed_out': True,
        'universal_equivalence_established': False,
    }


def test_unsupported_input_is_distinct_from_inequality():
    def unsupported(*args, **kwargs):
        raise ValueError('unsupported operation')

    artifact = evaluate(
        'left.qasm', 'right.qasm', criterion=CRITERION, source_refs=REFS,
        created_at=STAMP, timeout_seconds=1.0, verify_backend=unsupported,
    )
    payload = artifact['payload']
    assert payload['outcome']['status'] == 'UNSUPPORTED'
    assert payload['outcome']['conclusion'] == 'INCONCLUSIVE'
    assert payload['outcome']['raw_verdict'] == 'unsupported_input'


def test_backend_error_is_retained_without_becoming_inequality():
    def broken(*args, **kwargs):
        raise RuntimeError('backend internal failure')

    artifact = evaluate(
        'left.qasm', 'right.qasm', criterion=CRITERION, source_refs=REFS,
        created_at=STAMP, timeout_seconds=1.0, verify_backend=broken,
    )
    payload = artifact['payload']
    assert payload['outcome']['status'] == 'NOT_ASSESSED'
    assert payload['outcome']['conclusion'] == 'INCONCLUSIVE'
    assert payload['outcome']['raw_verdict'] == 'backend_error'
    assert payload['error']['type'] == 'RuntimeError'


def test_caller_must_select_exact_supported_criterion():
    with pytest.raises(ValueError, match='selected explicitly'):
        evaluate(
            'left.qasm', 'right.qasm', criterion={'id': CRITERION['id']},
            source_refs=REFS, created_at=STAMP, timeout_seconds=1.0,
            verify_backend=backend('equivalent'),
        )
