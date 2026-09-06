# SPDX-License-Identifier: Apache-2.0
"""Exact signed-permutation unitary comparison; no floating-point tolerance."""
from .circuit import CheckError, parse_source, require

CRITERION = {'id': 'e7q.ir.signed-permutation-unitary', 'version': '1'}
PRESERVES = ['unitary-prefix', 'terminal-measurement-map']
LOSSES = ['source-spelling-and-gate-decomposition']
ASSUMPTIONS = ['signed-permutation-gate-table-v1']
ARITIES = {'id': 1, 'x': 1, 'z': 1, 'cx': 2, 'cz': 2, 'swap': 2}
MAX_QUBITS = 8
MAX_GATES = 256


def action(parsed):
    registers = parsed['registers']
    require(len(registers['quantum']) == len(registers['classical']) == 1,
            'Exactly one quantum and classical register is admitted.', 'UNSUPPORTED')
    qreg, creg = registers['quantum'][0], registers['classical'][0]
    n = qreg['width']
    require(n <= MAX_QUBITS, 'Exact unitary qubit budget exceeded.', 'BLOCKED')
    require(creg['width'] == n, 'Complete terminal measurement is required.', 'UNSUPPORTED')
    require(parsed['language']['includes'] == ['qelib1.inc'],
            'Only the declared qelib1.inc gate-table convention is admitted.', 'UNSUPPORTED')
    gates, measurements = [], []
    for op in parsed['operations']:
        if op['name'] == 'measure':
            measurements.append((op['qubits'][0]['index'], op['clbits'][0]['index']))
            continue
        require(not measurements, 'Nonterminal measurement is unsupported.', 'UNSUPPORTED')
        require(op['name'] in ARITIES and not op.get('condition') and not op['parameters'],
                'Operation is outside the exact signed-permutation fragment.', 'UNSUPPORTED')
        indices = [q['index'] for q in op['qubits']]
        require(len(indices) == ARITIES[op['name']] and len(set(indices)) == len(indices),
                'Gate operands must be distinct and have the specified arity.', 'UNSUPPORTED')
        gates.append((op['name'], indices))
    require(len(gates) <= MAX_GATES, 'Exact unitary gate budget exceeded.', 'BLOCKED')
    require(len(measurements) == n and {q for q, _ in measurements} == set(range(n))
            and {c for _, c in measurements} == set(range(n)),
            'Every qubit and classical bit must occur once in terminal measurement.', 'UNSUPPORTED')
    # Each column is exactly one signed computational-basis vector. Comparing
    # all columns therefore compares the linear operator, not sampled counts.
    columns = []
    for basis in range(1 << n):
        output, sign = basis, 1
        for name, indices in gates:
            a = 1 << indices[0]
            if name == 'x':
                output ^= a
            elif name == 'z' and output & a:
                sign = -sign
            elif name == 'cx' and output & a:
                output ^= 1 << indices[1]
            elif name == 'cz' and output & a and output & (1 << indices[1]):
                sign = -sign
            elif name == 'swap':
                b = 1 << indices[1]
                if bool(output & a) != bool(output & b):
                    output ^= a | b
        columns.append((output, sign))
    return columns, measurements


def validate(relation, graph):
    by_id = {a['artifact_id']: a for a in graph['artifacts']}
    try:
        require(relation['criterion'] == CRITERION,
                'Unsupported exact unitary criterion version or options.', 'UNSUPPORTED')
        require(relation['preserves'] == PRESERVES and relation['loses'] == LOSSES
                and relation['assumptions'] == ASSUMPTIONS,
                'Exact unitary preservation/loss/assumption contract is required.', 'UNSUPPORTED')
        left, right = by_id[relation['source']], by_id[relation['target']]
        require(left['kind'] in {'source', 'representation'} and right['kind'] in {'source', 'representation'},
                'Unitary comparison needs circuit endpoints.')
        p, q = parse_source(left), parse_source(right)
        pa, pm = action(p)
        qa, qm = action(q)
        require(p['registers'] == q['registers'] and pm == qm,
                'Register identity or ordered measurement mapping differs.', 'UNSUPPORTED')
        require(pa == qa, 'Exact unitary prefixes differ, including phase; no hardware claim is assessed.')
        require(relation['validation_status'] == 'validated',
                'Relation status contradicts established exact unitary equality.')
    except CheckError as exc:
        return exc.status, exc.message
    return 'PASS', 'All signed-permutation columns agree exactly under the declared gate table; terminal measurement maps match.'
