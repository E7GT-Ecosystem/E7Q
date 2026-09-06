# SPDX-License-Identifier: Apache-2.0
"""Exact noiseless channel action on every matrix unit in a bounded fragment."""
from .circuit import CheckError, parse_source, require
from .unitary import action, ASSUMPTIONS

CRITERION = {'id': 'e7q.ir.signed-permutation-unitary-channel', 'version': '1'}
PRESERVES = ['premeasurement-unitary-channel', 'terminal-measurement-map']
LOSSES = ['source-spelling-and-gate-decomposition', 'global-phase']


def matrix_units(columns):
    # U |i><j| U† = s_i s_j |p(i)><p(j)|; all signs are real.
    for row, sign in columns:
        for column, other_sign in columns:
            yield row, column, sign * other_sign


def validate(relation, graph):
    by_id = {a['artifact_id']: a for a in graph['artifacts']}
    try:
        require(relation['criterion'] == CRITERION,
                'Unsupported unitary-channel criterion version or options.', 'UNSUPPORTED')
        require(relation['preserves'] == PRESERVES and relation['loses'] == LOSSES
                and relation['assumptions'] == ASSUMPTIONS,
                'The unitary-channel preservation/loss/assumption contract is required.', 'UNSUPPORTED')
        left, right = by_id[relation['source']], by_id[relation['target']]
        require(left['kind'] in {'source', 'representation'} and right['kind'] in {'source', 'representation'},
                'Unitary-channel comparison needs circuit endpoints.')
        p, q = parse_source(left), parse_source(right)
        pa, pm = action(p)
        qa, qm = action(q)
        require(p['registers'] == q['registers'] and pm == qm,
                'Register identity or ordered measurement mapping differs.', 'UNSUPPORTED')
        for index, (a, b) in enumerate(zip(matrix_units(pa), matrix_units(qa))):
            require(a == b, f'Channel actions differ on matrix unit ({index // len(pa)}, {index % len(pa)}), with quantum index 0 least significant.')
        require(relation['validation_status'] == 'validated',
                'Relation status contradicts established unitary-channel equality.')
    except CheckError as exc:
        return exc.status, exc.message
    return 'PASS', f'Premeasurement channel actions agree exactly on all {len(pa)**2} matrix units, including off-diagonal coherence. No noisy-channel or hardware claim is assessed.'
