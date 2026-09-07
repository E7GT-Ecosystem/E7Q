#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Run the pinned optional MQT QCEC evaluation corpus above 25 qubits."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import tempfile

from e7q.ir.canonical import canonical_bytes, digest
from e7q.ir.qcec import evaluate
from e7q.ir.unitary import CRITERION, GLOBAL_PHASE_CRITERION


def qasm(n: int, gates: list[str]) -> str:
    return 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[%d];\n%s\n' % (n, '\n'.join(gates))


def source_ref(text: str) -> str:
    return 'sha256:' + sha256(text.encode()).hexdigest()


def cases():
    for n in (26, 32):
        swap = [f'swap q[{i}],q[{i + 1}];' for i in range(0, n - 1, 2)]
        swap_rewrite = [gate for i in range(0, n - 1, 2) for gate in (
            f'cx q[{i}],q[{i + 1}];', f'cx q[{i + 1}],q[{i}];',
            f'cx q[{i}],q[{i + 1}];')]
        yield {
            'id': f'swap-rewrite-{n}', 'family': 'disjoint-swap-decomposition',
            'qubits': n, 'expected': 'exact-equivalent',
            'left': swap, 'right': swap_rewrite,
            'depth': {'left': 1, 'right': 3}, 'gate_set': ['swap', 'cx'],
            'timeout_seconds': 10.0,
        }
        yield {
            'id': f'global-phase-{n}', 'family': 'pauli-anticommutation',
            'qubits': n, 'expected': 'global-phase-only',
            'left': ['x q[0];', 'z q[0];'], 'right': ['z q[0];', 'x q[0];'],
            'depth': {'left': 2, 'right': 2}, 'gate_set': ['x', 'z'],
            'timeout_seconds': 10.0,
        }
        yield {
            'id': f'altered-gate-{n}', 'family': 'intentional-single-gate-error',
            'qubits': n, 'expected': 'not-equivalent',
            'left': ['x q[0];'], 'right': ['z q[0];'],
            'depth': {'left': 1, 'right': 1}, 'gate_set': ['x', 'z'],
            'timeout_seconds': 10.0,
        }
    n = 26
    deep = [gate for i in range(300) for gate in (
        f'h q[{i % n}];', f'cx q[{i % n}],q[{(i + 1) % n}];')]
    yield {
        'id': 'forced-timeout-26', 'family': 'resource-exhaustion-control',
        'qubits': n, 'expected': 'inconclusive-timeout',
        'left': deep, 'right': deep,
        'depth': {'left': 600, 'right': 600}, 'gate_set': ['h', 'cx'],
        'timeout_seconds': 1e-9,
    }


def run(created_at: str) -> dict:
    results = []
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for case in cases():
            left_text = qasm(case['qubits'], case.pop('left'))
            right_text = qasm(case['qubits'], case.pop('right'))
            left = root / f"{case['id']}-left.qasm"
            right = root / f"{case['id']}-right.qasm"
            left.write_text(left_text)
            right.write_text(right_text)
            assessments = []
            for criterion in (CRITERION, GLOBAL_PHASE_CRITERION):
                assessments.append(evaluate(
                    left, right, criterion=criterion,
                    source_refs=(source_ref(left_text), source_ref(right_text)),
                    created_at=created_at,
                    timeout_seconds=case['timeout_seconds'], nthreads=1,
                    max_simulations=4, seed=7,
                ))
            case['gate_count'] = {
                'left': left_text.count(';') - 3,
                'right': right_text.count(';') - 3,
            }
            case['assessments'] = assessments
            results.append(case)
    report = {
        'schema': 'e7q.ir.qcec-benchmark/v1',
        'created_at': created_at,
        'backend_requirement': 'mqt.qcec==3.9.0',
        'scope': 'structured evaluation corpus; not arbitrary-circuit scalability',
        'results': results,
    }
    report['report_id'] = digest(report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--created-at', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    report = run(args.created_at)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_bytes(report) + b'\n')
    statuses = {}
    for case in report['results']:
        for artifact in case['assessments']:
            status = artifact['payload']['outcome']['status']
            statuses[status] = statuses.get(status, 0) + 1
    print(json.dumps({'report_id': report['report_id'], 'cases': len(report['results']),
                      'criterion_runs': sum(statuses.values()), 'statuses': statuses}, sort_keys=True))


if __name__ == '__main__':
    main()
