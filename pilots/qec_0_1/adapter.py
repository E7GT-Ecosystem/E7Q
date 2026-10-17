# SPDX-License-Identifier: Apache-2.0
"""Bounded QEC exchange adapter; delegates quantum verdicts to existing E7Q.

No reference-probe imports. q[0] is the least significant state-vector bit;
Pauli strings run q[0]..q[2]. Native full-register labels run q[0] first. Only the four reference preparations are admitted.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict, replace
from itertools import product
from pathlib import Path
import hashlib
import json
import math
import platform
import statistics
import subprocess
import time
import numpy as np
from e7q.language import parse, run, verify
from e7q.qec import StabilizerCode, analyze_error, multiply_paulis

CODE = StabilizerCode('repetition-3', ('ZZI', 'IZZ'))
PREP = {'zero': [], 'one': ['X'], 'plus': ['H'], 'plus_i': ['H', 'S']}
AMP = {'zero': (1, 0), 'one': (0, 1), 'plus': (2**-.5, 2**-.5),
       'plus_i': (2**-.5, 1j*2**-.5)}
DECODER = {'00': 'III', '10': 'XII', '11': 'IXI', '01': 'IIX'}

@dataclass(frozen=True)
class QECCase:
    case_id: str
    preparation: str
    amplitudes: tuple[tuple[float, float], ...]
    generators: tuple[str, ...]
    error: str
    expected_syndrome: tuple[int, int]
    decoder: tuple[tuple[str, str], ...]
    recovery: str
    expected_fidelity: float = 1.0
    schema: str = 'e7q.qec-case/0.1'

    def __post_init__(self):
        if self.schema != 'e7q.qec-case/0.1' or not isinstance(self.case_id,str) or not self.case_id.strip():
            raise ValueError('invalid schema or identity')
        if self.preparation not in PREP:
            raise ValueError('unsupported preparation: no arbitrary amplitude loader')
        if self.generators != CODE.generators:
            raise ValueError('unsupported code/generator order')
        for p in (self.error, self.recovery):
            if not isinstance(p, str) or len(p) != 3 or set(p)-set('IXYZ'):
                raise ValueError('invalid Pauli operator')
        if len(self.amplitudes) != 8 or any(len(a) != 2 or any(type(x) not in (int,float) or not math.isfinite(x) for x in a) for a in self.amplitudes):
            raise ValueError('eight finite complex amplitudes required')
        expected = np.zeros(8, complex)
        expected[0], expected[7] = AMP[self.preparation]
        if not np.allclose([complex(*a) for a in self.amplitudes], expected, atol=1e-12, rtol=0):
            raise ValueError('amplitudes do not match declared preparation')
        if len(self.expected_syndrome) != 2 or any(type(x) is not int or x not in (0,1) for x in self.expected_syndrome):
            raise ValueError('invalid syndrome')
        if len(self.decoder) != 4 or set(dict(self.decoder)) != set(DECODER) or len(dict(self.decoder)) != 4:
            raise ValueError('complete unique decoder required')
        if any(len(p)!=3 or set(p)-set('IXYZ') for _,p in self.decoder):
            raise ValueError('invalid decoder Pauli')
        if type(self.expected_fidelity) not in (int,float) or self.expected_fidelity != 1:
            raise ValueError('only unit-fidelity restoration claims supported')

    @classmethod
    def from_json(cls, obj):
        if set(obj) != set(cls.__dataclass_fields__):
            raise ValueError('unknown or missing exchange fields')
        return cls(**{**obj, 'amplitudes': tuple(tuple(a) for a in obj['amplitudes']),
                      'generators': tuple(obj['generators']),
                      'expected_syndrome': tuple(obj['expected_syndrome']),
                      'decoder': tuple(tuple(a) for a in obj['decoder'])})


def make_case(prep, error, label='good', decoder=None):
    # Conventional independent parity table, not E7Q's syndrome routine.
    s = oracle_syndrome(error)
    d = decoder or DECODER
    a,b = AMP[prep]
    amplitudes = tuple((complex(x).real, complex(x).imag) for x in [a,0,0,0,0,0,0,b])
    return QECCase(f'{label}-{prep}-{error}', prep, amplitudes, CODE.generators,
                   error, s, tuple(sorted(d.items())), d[''.join(map(str,s))])


def oracle_syndrome(error):
    # Local Pauli matrix anticommutation with Z; no E7Q imports used here.
    x = [int(p in 'XY') for p in error]
    return (x[0]^x[1], x[1]^x[2])


def pauli_matrix(pauli):
    matrices = {'I': np.eye(2), 'X': np.array([[0,1],[1,0]]),
                'Y': np.array([[0,-1j],[1j,0]]), 'Z': np.diag([1,-1])}
    out = np.ones((1,1), complex)
    for p in reversed(pauli):
        out = np.kron(out, matrices[p])
    return out


def oracle(case):
    state = np.array([complex(*a) for a in case.amplitudes])
    received = pauli_matrix(case.error) @ state
    corrected = pauli_matrix(case.recovery) @ received
    fidelity = float(abs(np.vdot(state, corrected))**2)
    # Simultaneous generator eigenvalues, independently calculated on amplitudes.
    means = [float(np.vdot(received, pauli_matrix(g) @ received).real) for g in case.generators]
    syndrome = tuple(int(x < 0) for x in means)
    return {'syndrome': syndrome, 'fidelity': fidelity,
            'passes': syndrome == case.expected_syndrome and abs(fidelity-1)<1e-10}


def circuit(case, backend='statevector', include_claim=True):
    gates = [f'{g} q[0]' for g in PREP[case.preparation]]
    gates += ['CX q[0], q[1]', 'CX q[0], q[2]']
    gates += [f'{g} q[{i}]' for i,g in enumerate(case.error) if g != 'I']
    # Coherent extraction: definite-syndrome inputs only. No stochastic collapse claim.
    gates += ['CX q[0], q[3]', 'CX q[1], q[3]', 'CX q[1], q[4]', 'CX q[2], q[4]']
    gates += [f'{g} q[{i}]' for i,g in enumerate(case.recovery) if g != 'I']
    gates += ['CX q[0], q[2]', 'CX q[0], q[1]']
    for g in reversed(PREP[case.preparation]):
        gates += [f'{h} q[0]' for h in (['S']*3 if g == 'S' else [g])]
    expected = f'000{case.expected_syndrome[0]}{case.expected_syndrome[1]}'
    invariant = f'invariant outcomes in {{{expected}}}' if include_claim else ''
    return (f'context QEC {{\n shots: 32\n backend: {backend}\n seed: 710\n}}\n'
            f'qubits q[5]\nbits c[5]\ninvariant normalized\n{invariant}\n'
            'path Check {\n'+'\n'.join(gates)+'\nmeasure q -> c\n}\nverify Check\n')


def evaluate_case(case):
    source = circuit(case)
    start = time.perf_counter_ns()
    report = verify(run(parse(source)))
    elapsed = time.perf_counter_ns()-start
    start = time.perf_counter_ns()
    conventional = oracle(case)
    oracle_ns = time.perf_counter_ns()-start
    residual = multiply_paulis(case.recovery, case.error)
    return {'case': asdict(case), 'source': source,
            'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
            'e7q': report, 'e7q_ns': elapsed, 'oracle': conventional,
            'oracle_ns': oracle_ns, 'error_analysis': analyze_error(CODE, case.error),
            'residual_analysis': analyze_error(CODE, residual),
            'decoder_action_consistent': dict(case.decoder)[''.join(map(str,case.expected_syndrome))] == case.recovery,
            'boundary': 'E7Q verdict verifies submitted circuit support, not decoder-table semantics or all logical inputs.'}


def cases():
    good = [make_case(p,e) for p in PREP for e in ('III','XII','IXI','IIX')]
    bad = {**DECODER, '10':'IXI', '11':'XII'}
    faulty = [make_case(p,e,'swapped-decoder',bad) for p in PREP for e in ('III','XII','IXI','IIX')]
    wrong_s = [replace(c,case_id='wrong-syndrome-'+c.case_id,
                       expected_syndrome=(1-c.expected_syndrome[0],c.expected_syndrome[1])) for c in good]
    wrong_r = [replace(c,case_id='wrong-recovery-'+c.case_id,
                       recovery=multiply_paulis(c.recovery,'XII')) for c in good]
    phase = [make_case('plus','ZII','phase-control')]
    double = [make_case(p,e,'double-X') for p in PREP for e in ('XXI','XIX','IXX')]
    return good+faulty+wrong_s+wrong_r+phase+double


def main():
    out = Path(__file__).parent/'results'
    out.mkdir(exist_ok=True)
    rows = [evaluate_case(c) for c in cases()]
    groups = {}
    for label in ('good','swapped-decoder','wrong-syndrome','wrong-recovery','phase-control','double-X'):
        rs = [r for r in rows if r['case']['case_id'].startswith(label+'-')]
        groups[label] = {'cases':len(rs),'PASS':sum(r['e7q']['status']=='PASS' for r in rs),
                         'FAIL':sum(r['e7q']['status']=='FAIL' for r in rs),
                         'oracle_agreement':sum((r['e7q']['status']=='PASS')==r['oracle']['passes'] for r in rs)}
    control = make_case('plus','ZII','normalization-only')
    weak = verify(run(parse(circuit(control, include_claim=False))))
    timings = []
    for _ in range(5):
        for c in cases():
            timings.append(evaluate_case(c))
    summary = {'baseline': 'b7989c647e5d0e22ed1128c41aceb2dda2f23405',
               'python':platform.python_version(),'numpy':np.__version__, 'groups':groups,
               'normalization_only_phase_control':weak,
               'timing':{key: {'median_ns':statistics.median(r[key] for r in timings),
                               'min_ns':min(r[key] for r in timings), 'calls':len(timings)} for key in ('e7q_ns','oracle_ns')},
               'independence': 'No qec_probe imports; existing E7Q simulator/verifier compared with dense Pauli-matrix oracle. Same author/session, not independent external review.'}
    (out/'cases-and-witnesses.json').write_text(json.dumps(rows,indent=2)+'\n')
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='normalization_only_phase_control'},indent=2))

if __name__ == '__main__':
    main()
