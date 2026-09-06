# SPDX-License-Identifier: Apache-2.0
"""Bounded exact real unitary matrices over Q(sqrt(2))."""
from copy import deepcopy
from fractions import Fraction
from .circuit import CheckError, parse_source, require
from .unitary import action, PRESERVES, LOSSES

CRITERION = {'id': 'e7q.ir.real-h-unitary', 'version': '1'}
ASSUMPTIONS = ['real-h-gate-table-v1']
MAX_QUBITS = 4
MAX_GATES = 64


def exact_columns(parsed):
    # Replace H only in a temporary validation projection, retaining operands,
    # conditions and measurement placement for the shared domain checks.
    projected = deepcopy(parsed)
    for op in projected['operations']:
        if op['name'] == 'u2':
            require(op['parameters'] == ['0', 'pi'],
                    'Only literal u2(0,pi) is admitted.', 'UNSUPPORTED')
            op['parameters'] = []
            op['name'] = 'h'
        if op['name'] == 'h':
            op['name'] = 'id'
    registers = parsed['registers']['quantum']
    require(sum(r['width'] for r in registers) <= MAX_QUBITS,
            'Exact real-unitary qubit budget exceeded.', 'BLOCKED')
    gates = [op for op in parsed['operations'] if op['name'] != 'measure']
    require(len(gates) <= MAX_GATES, 'Exact real-unitary gate budget exceeded.', 'BLOCKED')
    _, measurements = action(projected)
    size = 1 << registers[0]['width']
    h_count = sum(op['name'] in {'h', 'u2'} for op in gates)
    # Every entry has integer numerator / sqrt(2)**h_count. Canonicalize to
    # (rational coefficient, sqrt(2) coefficient) to compare different H counts.
    divisor = 1 << ((h_count + 1) // 2)
    columns = []
    for basis in range(size):
        state = [int(i == basis) for i in range(size)]
        for op in gates:
            name = op['name']
            indices = [q['index'] for q in op['qubits']]
            mask = 1 << indices[0]
            if name in {'h', 'u2'}:
                for i in range(size):
                    if not i & mask:
                        a, b = state[i], state[i | mask]
                        state[i], state[i | mask] = a + b, a - b
                continue
            updated = [0] * size
            for i, amplitude in enumerate(state):
                dest, sign = i, 1
                if name == 'x':
                    dest ^= mask
                elif name == 'z' and i & mask:
                    sign = -1
                elif name == 'cx' and i & mask:
                    dest ^= 1 << indices[1]
                elif name == 'cz' and i & mask and i & (1 << indices[1]):
                    sign = -1
                elif name == 'swap':
                    other = 1 << indices[1]
                    if bool(i & mask) != bool(i & other):
                        dest ^= mask | other
                updated[dest] = sign * amplitude
            state = updated
        columns.append(tuple((0, Fraction(v, divisor)) if h_count % 2
                             else (Fraction(v, divisor), 0) for v in state))
    return columns, measurements


def validate(relation, graph):
    by_id = {a['artifact_id']: a for a in graph['artifacts']}
    try:
        require(relation['criterion'] == CRITERION, 'Unsupported real-unitary criterion options.', 'UNSUPPORTED')
        require(relation['preserves'] == PRESERVES and relation['loses'] == LOSSES
                and relation['assumptions'] == ASSUMPTIONS,
                'Exact real-unitary accounting contract is required.', 'UNSUPPORTED')
        left, right = by_id[relation['source']], by_id[relation['target']]
        require(left['kind'] in {'source', 'representation'} and right['kind'] in {'source', 'representation'},
                'Real-unitary comparison needs circuit endpoints.')
        p, q = parse_source(left), parse_source(right)
        pa, pm = exact_columns(p)
        qa, qm = exact_columns(q)
        require(p['registers'] == q['registers'] and pm == qm,
                'Register identity or ordered measurement mapping differs.', 'UNSUPPORTED')
        require(pa == qa, 'Exact real unitary matrices differ, including phase.')
        require(relation['validation_status'] == 'validated', 'Relation status contradicts exact real-unitary equality.')
    except CheckError as exc:
        return exc.status, exc.message
    return 'PASS', 'Every real unitary matrix entry agrees exactly in Q(sqrt(2)), including phase; terminal measurement maps match. No hardware claim is assessed.'
