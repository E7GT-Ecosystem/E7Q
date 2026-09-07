# SPDX-License-Identifier: Apache-2.0
import multiprocessing
import os
import signal
import sys
import time

import pytest

from e7q.ir.qcec import (
    FIDELITY_THRESHOLD,
    NUMERICAL_EXACT_CRITERION,
    NUMERICAL_GLOBAL_PHASE_CRITERION,
    NUMERICAL_TOLERANCE,
    evaluate,
    map_verdict,
)
from e7q.ir.unitary import CRITERION, GLOBAL_PHASE_CRITERION

STAMP = '2026-09-07T00:00:00Z'
REFS = ('sha256:' + '1' * 64, 'sha256:' + '2' * 64)


@pytest.mark.parametrize(('raw', 'criterion', 'timed_out', 'expected'), [
    ('equivalent', NUMERICAL_EXACT_CRITERION['id'], False, ('PASS', 'ESTABLISHED')),
    ('equivalent', NUMERICAL_GLOBAL_PHASE_CRITERION['id'], False, ('PASS', 'ESTABLISHED')),
    ('equivalent_up_to_global_phase', NUMERICAL_EXACT_CRITERION['id'], False,
     ('FAIL', 'REFUTED')),
    ('equivalent_up_to_global_phase', NUMERICAL_GLOBAL_PHASE_CRITERION['id'], False,
     ('PASS', 'ESTABLISHED')),
    ('not_equivalent', NUMERICAL_EXACT_CRITERION['id'], False, ('FAIL', 'REFUTED')),
    ('probably_equivalent', NUMERICAL_EXACT_CRITERION['id'], False,
     ('NOT_ASSESSED', 'INCONCLUSIVE')),
    ('probably_not_equivalent', NUMERICAL_EXACT_CRITERION['id'], False,
     ('NOT_ASSESSED', 'INCONCLUSIVE')),
    ('no_information', NUMERICAL_EXACT_CRITERION['id'], False,
     ('NOT_ASSESSED', 'INCONCLUSIVE')),
    ('no_information', NUMERICAL_EXACT_CRITERION['id'], True,
     ('BLOCKED', 'INCONCLUSIVE')),
    ('equivalent_up_to_phase', NUMERICAL_GLOBAL_PHASE_CRITERION['id'], False,
     ('NOT_ASSESSED', 'INCONCLUSIVE')),
    ('unknown_future_verdict', NUMERICAL_EXACT_CRITERION['id'], False,
     ('NOT_ASSESSED', 'INCONCLUSIVE')),
])
def test_verdict_mapping_never_upgrades_weaker_results(raw, criterion, timed_out, expected):
    assert map_verdict(raw, criterion, timed_out=timed_out) == expected


@pytest.mark.parametrize('criterion', [
    NUMERICAL_EXACT_CRITERION['id'],
    NUMERICAL_GLOBAL_PHASE_CRITERION['id'],
])
@pytest.mark.parametrize('raw', [
    'no_information', 'equivalent_up_to_phase', 'probably_equivalent',
    'probably_not_equivalent', 'unsupported_input', 'backend_error', 'unknown',
])
def test_every_inconclusive_or_unknown_verdict_is_non_pass(criterion, raw):
    status, conclusion = map_verdict(raw, criterion, timed_out=raw == 'no_information')
    assert status != 'PASS'
    assert conclusion == 'INCONCLUSIVE'


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


class Backend:
    """Spawn-pickleable fake backend used by isolated-worker tests."""

    def __init__(self, verdict, check_time=0.01, expected_timeout=5.0):
        self.verdict = verdict
        self.check_time = check_time
        self.expected_timeout = expected_timeout

    def __call__(self, *args, **kwargs):
        assert kwargs == {
            'timeout': self.expected_timeout, 'nthreads': 1, 'parallel': False,
            'max_sims': 4, 'seed': 7,
            'numerical_tolerance': NUMERICAL_TOLERANCE,
            'fidelity_threshold': FIDELITY_THRESHOLD,
        }
        return Result(self.verdict, self.check_time)


class MalformedResult:
    def json(self):
        return 'not-a-mapping'


class MalformedCheckersResult:
    def json(self):
        return {
            'equivalence': 'equivalent',
            'check_time': 0.001,
            'checkers': None,
        }


class MappingResult:
    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload


def unsupported_backend(*args, **kwargs):
    raise ValueError('unsupported operation')


def broken_backend(*args, **kwargs):
    raise RuntimeError('backend internal failure')


def sleeping_backend(*args, **kwargs):
    time.sleep(10)
    return Result('equivalent')


def resource_exhaustion_backend(*args, **kwargs):
    raise MemoryError('allocation denied by resource bound')


def crash_backend(*args, **kwargs):
    os._exit(23)


def signal_backend(*args, **kwargs):
    os.kill(os.getpid(), signal.SIGKILL)


def malformed_backend(*args, **kwargs):
    return MalformedResult()


def malformed_checkers_backend(*args, **kwargs):
    return MalformedCheckersResult()


def rlimit_observer_backend(*args, **kwargs):
    import resource

    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    payload = Result('equivalent').json()
    payload['observed_rlimit_as'] = {'soft': soft, 'hard': hard}
    return MappingResult(payload)


def backend(verdict, check_time=0.01, expected_timeout=5.0):
    return Backend(verdict, check_time, expected_timeout)


def assessment(verdict, criterion=NUMERICAL_EXACT_CRITERION, check_time=0.01):
    return evaluate(
        'left.qasm', 'right.qasm', criterion=criterion, source_refs=REFS,
        created_at=STAMP, timeout_seconds=5.0, nthreads=1,
        max_simulations=4, seed=7,
        verify_backend=backend(verdict, check_time),
    )


def assert_non_pass_reason(artifact, reason):
    outcome = artifact['payload']['outcome']
    assert outcome['status'] != 'PASS'
    assert outcome['conclusion'] == 'INCONCLUSIVE'
    assert outcome['reason'] == reason
    return artifact['payload']


def test_assessment_records_backend_criterion_method_resources_and_raw_result():
    artifact = assessment('equivalent_up_to_global_phase', NUMERICAL_GLOBAL_PHASE_CRITERION)
    payload = artifact['payload']
    assert artifact['kind'] == 'assessment'
    assert artifact['provenance']['source_refs'] == list(REFS)
    assert payload['criterion'] == NUMERICAL_GLOBAL_PHASE_CRITERION
    assert payload['backend']['id'] == 'mqt.qcec'
    assert payload['configuration']['timeout_seconds'] == 5.0
    assert payload['configuration']['numerical_tolerance'] == NUMERICAL_TOLERANCE
    assert payload['configuration']['fidelity_threshold'] == FIDELITY_THRESHOLD
    assert payload['method']['kind'] == 'tolerance-based-numerical'
    assert payload['method']['exact_algebraic'] is False
    assert payload['outcome']['status'] == 'PASS'
    assert payload['outcome']['raw_verdict'] == 'equivalent_up_to_global_phase'
    assert payload['outcome']['reason'] == 'backend_verdict'
    assert payload['resource_use']['worker_peak_rss_bytes'] > 0
    assert payload['resource_use']['memory_measurement_scope'] == 'isolated-worker-process-peak'
    assert payload['resource_use']['wall_clock_limit_enforced'] is True
    assert payload['worker']['start_method'] == 'spawn'
    assert payload['worker']['exit_code'] == 0
    assert payload['worker']['reaped'] is True
    assert payload['raw_result']['checkers'][0]['checker'] == 'decision_diagram_alternating'
    assert any('not default' in item for item in artifact['limitations'])


def test_parent_wall_timeout_terminates_and_reaps_worker():
    artifact = evaluate(
        'left.qasm', 'right.qasm', criterion=NUMERICAL_EXACT_CRITERION,
        source_refs=REFS, created_at=STAMP, timeout_seconds=0.05,
        verify_backend=sleeping_backend,
    )
    payload = assert_non_pass_reason(artifact, 'wall_clock_timeout')
    assert payload['outcome']['status'] == 'BLOCKED'
    assert payload['outcome']['timed_out'] is True
    assert payload['outcome']['raw_verdict'] == 'wall_clock_timeout'
    assert payload['worker']['termination_mechanism'] in {'terminate', 'kill'}
    assert payload['worker']['reaped'] is True
    assert payload['resource_use']['wall_clock_limit_enforced'] is True
    worker_pid = payload['worker']['pid']
    assert all(child.pid != worker_pid for child in multiprocessing.active_children())


def test_backend_reported_timeout_remains_distinct_and_inconclusive():
    artifact = evaluate(
        'left.qasm', 'right.qasm', criterion=NUMERICAL_EXACT_CRITERION,
        source_refs=REFS, created_at=STAMP, timeout_seconds=5.0,
        nthreads=1, max_simulations=4, seed=7,
        verify_backend=backend('no_information', 5.0),
    )
    payload = assert_non_pass_reason(artifact, 'backend_timeout')
    assert payload['outcome']['status'] == 'BLOCKED'
    assert payload['outcome']['raw_verdict'] == 'no_information'
    assert payload['outcome']['timed_out'] is True


def test_memory_limit_enforcement_and_resource_exhaustion_are_recorded():
    requested = 64 * 1024**3
    artifact = evaluate(
        'left.qasm', 'right.qasm', criterion=NUMERICAL_EXACT_CRITERION,
        source_refs=REFS, created_at=STAMP, timeout_seconds=5.0,
        memory_limit_bytes=requested, verify_backend=resource_exhaustion_backend,
    )
    payload = assert_non_pass_reason(artifact, 'resource_exhaustion')
    assert payload['outcome']['status'] == 'BLOCKED'
    assert payload['outcome']['resource_exhausted'] is True
    assert payload['outcome']['raw_verdict'] == 'resource_exhaustion'
    resources = payload['resource_use']
    assert resources['memory_limit_requested_bytes'] == requested
    if sys.platform.startswith('linux'):
        assert resources['memory_limit_enforced'] is True
        assert resources['memory_limit_mechanism'] == 'posix-rlimit-as'
        assert resources['memory_limit_effective_bytes'] <= requested
    else:
        assert isinstance(resources['memory_limit_enforced'], bool)


@pytest.mark.skipif(not sys.platform.startswith('linux'), reason='Linux RLIMIT_AS observation')
def test_memory_limit_lowers_worker_soft_and_hard_address_space_bounds():
    requested = 64 * 1024**3
    artifact = evaluate(
        'left.qasm', 'right.qasm', criterion=NUMERICAL_EXACT_CRITERION,
        source_refs=REFS, created_at=STAMP, timeout_seconds=5.0,
        memory_limit_bytes=requested, verify_backend=rlimit_observer_backend,
    )
    payload = artifact['payload']
    assert payload['outcome']['status'] == 'PASS'
    resources = payload['resource_use']
    observed = payload['raw_result']['observed_rlimit_as']
    assert resources['memory_limit_enforced'] is True
    assert observed['soft'] == observed['hard']
    assert observed['soft'] == resources['memory_limit_effective_bytes']
    assert resources['memory_limit_soft_bytes'] == observed['soft']
    assert resources['memory_limit_hard_bytes'] == observed['hard']
    assert observed['soft'] <= requested


@pytest.mark.skipif(os.name != 'posix', reason='POSIX signal exit metadata')
def test_worker_signal_is_distinct_from_resource_exhaustion_and_reaped():
    artifact = evaluate(
        'left.qasm', 'right.qasm', criterion=NUMERICAL_EXACT_CRITERION,
        source_refs=REFS, created_at=STAMP, timeout_seconds=5.0,
        verify_backend=signal_backend,
    )
    payload = assert_non_pass_reason(artifact, 'worker_signal')
    assert payload['outcome']['resource_exhausted'] is False
    assert payload['worker']['signal'] == signal.SIGKILL
    assert payload['worker']['signal_name'] == 'SIGKILL'
    assert payload['worker']['reaped'] is True


def test_worker_nonzero_exit_is_distinct_and_reaped():
    artifact = evaluate(
        'left.qasm', 'right.qasm', criterion=NUMERICAL_EXACT_CRITERION,
        source_refs=REFS, created_at=STAMP, timeout_seconds=5.0,
        verify_backend=crash_backend,
    )
    payload = assert_non_pass_reason(artifact, 'worker_crash')
    assert payload['worker']['exit_code'] == 23
    assert payload['worker']['signal'] is None
    assert payload['worker']['reaped'] is True


def test_malformed_worker_result_is_protocol_error_not_pass():
    artifact = evaluate(
        'left.qasm', 'right.qasm', criterion=NUMERICAL_EXACT_CRITERION,
        source_refs=REFS, created_at=STAMP, timeout_seconds=5.0,
        verify_backend=malformed_backend,
    )
    payload = assert_non_pass_reason(artifact, 'worker_protocol_error')
    assert payload['worker']['exit_code'] == 0
    assert payload['error']['type'] == 'TypeError'


def test_malformed_checker_container_is_protocol_error_not_parent_exception():
    artifact = evaluate(
        'left.qasm', 'right.qasm', criterion=NUMERICAL_EXACT_CRITERION,
        source_refs=REFS, created_at=STAMP, timeout_seconds=5.0,
        verify_backend=malformed_checkers_backend,
    )
    payload = assert_non_pass_reason(artifact, 'worker_protocol_error')
    assert payload['worker']['exit_code'] == 0
    assert payload['error']['message'] == 'backend checkers must be a list'


def test_unpickleable_backend_is_worker_start_error_not_pass():
    artifact = evaluate(
        'left.qasm', 'right.qasm', criterion=NUMERICAL_EXACT_CRITERION,
        source_refs=REFS, created_at=STAMP, timeout_seconds=5.0,
        verify_backend=lambda *args, **kwargs: Result('equivalent'),
    )
    payload = assert_non_pass_reason(artifact, 'worker_start_error')
    assert payload['worker']['started'] is False
    assert payload['worker']['reaped'] is True


def test_unsupported_input_is_distinct_from_inequality():
    artifact = evaluate(
        'left.qasm', 'right.qasm', criterion=NUMERICAL_EXACT_CRITERION,
        source_refs=REFS, created_at=STAMP, timeout_seconds=5.0,
        verify_backend=unsupported_backend,
    )
    payload = artifact['payload']
    assert payload['outcome']['status'] == 'UNSUPPORTED'
    assert payload['outcome']['conclusion'] == 'INCONCLUSIVE'
    assert payload['outcome']['raw_verdict'] == 'unsupported_input'
    assert payload['outcome']['reason'] == 'unsupported_input'


def test_backend_error_is_retained_without_becoming_inequality():
    artifact = evaluate(
        'left.qasm', 'right.qasm', criterion=NUMERICAL_EXACT_CRITERION,
        source_refs=REFS, created_at=STAMP, timeout_seconds=5.0,
        verify_backend=broken_backend,
    )
    payload = artifact['payload']
    assert payload['outcome']['status'] == 'NOT_ASSESSED'
    assert payload['outcome']['conclusion'] == 'INCONCLUSIVE'
    assert payload['outcome']['raw_verdict'] == 'backend_error'
    assert payload['outcome']['reason'] == 'backend_error'
    assert payload['error']['type'] == 'RuntimeError'


@pytest.mark.parametrize('criterion', [CRITERION, GLOBAL_PHASE_CRITERION])
def test_regression_qcec_equivalent_cannot_satisfy_exact_algebraic_criterion(criterion):
    called = False

    def would_report_equivalent(*args, **kwargs):
        nonlocal called
        called = True
        return Result('equivalent')

    with pytest.raises(ValueError, match='selected explicitly'):
        evaluate(
            'left.qasm', 'right.qasm', criterion=criterion,
            source_refs=REFS, created_at=STAMP, timeout_seconds=5.0,
            verify_backend=would_report_equivalent,
        )
    assert called is False


def test_caller_must_select_complete_supported_numerical_criterion():
    with pytest.raises(ValueError, match='selected explicitly'):
        evaluate(
            'left.qasm', 'right.qasm',
            criterion={'id': NUMERICAL_EXACT_CRITERION['id']},
            source_refs=REFS, created_at=STAMP, timeout_seconds=5.0,
            verify_backend=backend('equivalent'),
        )
