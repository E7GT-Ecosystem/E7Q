# SPDX-License-Identifier: Apache-2.0
"""Exact classical outcomes for all basis inputs in the pinned gate fragment."""
from .circuit import CheckError, parse_source, require
from .unitary import action, ASSUMPTIONS

CRITERION = {'id': 'e7q.ir.signed-permutation-basis-measurement', 'version': '1'}
PRESERVES = ['terminal-outcome-for-every-computational-basis-input', 'terminal-measurement-map']
LOSSES = ['source-spelling-and-gate-decomposition', 'global-and-relative-phase']


def outcomes(columns, mapping):
    # Outcome integer bit c corresponds to classical register index c.
    return [sum(((row >> q) & 1) << c for q, c in mapping) for row, _ in columns]


def validate(relation, graph):
    by_id = {a['artifact_id']: a for a in graph['artifacts']}
    try:
        require(relation['criterion'] == CRITERION,
                'Unsupported basis-measurement criterion version or options.', 'UNSUPPORTED')
        require(relation['preserves'] == PRESERVES and relation['loses'] == LOSSES
                and relation['assumptions'] == ASSUMPTIONS,
                'The basis-measurement preservation/loss/assumption contract is required.', 'UNSUPPORTED')
        left, right = by_id[relation['source']], by_id[relation['target']]
        require(left['kind'] in {'source', 'representation'} and right['kind'] in {'source', 'representation'},
                'Basis-measurement comparison needs circuit endpoints.')
        p, q = parse_source(left), parse_source(right)
        pa, pm = action(p)
        qa, qm = action(q)
        require(p['registers'] == q['registers'] and pm == qm,
                'Register identity or ordered measurement mapping differs.', 'UNSUPPORTED')
        po, qo = outcomes(pa, pm), outcomes(qa, qm)
        for basis, (a, b) in enumerate(zip(po, qo)):
            require(a == b, f'Basis input {basis} yields source outcome {a} and target outcome {b}; classical index 0 is the least significant bit.')
        require(relation['validation_status'] == 'validated',
                'Relation status contradicts established basis-measurement equality.')
    except CheckError as exc:
        return exc.status, exc.message
    return 'PASS', f'Terminal classical outcomes agree exactly for all {len(po)} computational-basis inputs. No unitary, phase, channel or hardware equality is assessed.'
