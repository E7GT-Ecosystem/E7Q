# SPDX-License-Identifier: Apache-2.0
import copy
import itertools
import json
from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).parent))
from adapter import QECCase, make_case, cases, evaluate_case, circuit, oracle_syndrome
from conventional import check as stabilizer_check
from decoder_table import ccx, table_source
from e7q.language import parse, run, verify


class AdapterChecks(unittest.TestCase):
    def test_corpus_matches_two_independent_oracles(self):
        for c in cases():
            with self.subTest(c.case_id):
                r=evaluate_case(c)
                self.assertEqual(r['e7q']['status']=='PASS',r['oracle']['passes'])
                self.assertEqual(stabilizer_check(c)['passes'],r['oracle']['passes'])

    def test_fault_sensitivity(self):
        rows=[evaluate_case(c) for c in cases()]
        counts={prefix:sum(r['e7q']['status']=='FAIL' for r in rows if r['case']['case_id'].startswith(prefix)) for prefix in ('good-','swapped-decoder-','wrong-syndrome-','wrong-recovery-','phase-control-')}
        self.assertEqual(counts,{'good-':0,'swapped-decoder-':8,'wrong-syndrome-':16,'wrong-recovery-':16,'phase-control-':1})

    def test_strict_exchange_rejects_malformed_and_unsupported(self):
        from dataclasses import asdict
        base=json.loads(json.dumps(asdict(make_case('plus','XII'))))
        bad=[]
        for key,value in [('schema','other'),('preparation','arbitrary'),('amplitudes',[[float('nan'),0]]*8),('expected_syndrome',[True,0]),('expected_fidelity',0.9),('generators',['IZZ','ZZI']),('error','XXXZ')]:
            bad.append({**base,key:value})
        bad += [{**base,'unknown':1},{k:v for k,v in base.items() if k!='recovery'}]
        for item in bad:
            with self.assertRaises((ValueError,TypeError)):QECCase.from_json(item)
        self.assertEqual(QECCase.from_json(base),make_case('plus','XII'))

    def test_native_bit_order_bridge(self):
        for e,expected in [('XII','00010'),('IXI','00011'),('IIX','00001')]:
            self.assertEqual(set(evaluate_case(make_case('zero',e))['e7q']['probabilities']),{expected})

    def test_coherent_decoder_uses_table_not_selected_recovery(self):
        from dataclasses import replace
        c=make_case('plus','XII')
        # The table circuit must ignore a conflicting specialized recovery field.
        self.assertEqual(table_source(c),table_source(replace(c,recovery='III')))
        for c in cases()[:32]:
            result=verify(run(parse(table_source(c))))
            self.assertEqual(result['status']=='PASS',evaluate_case(c)['oracle']['passes'])

    def test_ccx_on_all_basis_states(self):
        for bits in itertools.product((0,1),repeat=3):
            gates=[f'X q[{i}]' for i,x in enumerate(bits) if x]+ccx(0,1,2)
            expected=''.join(map(str,(bits[0],bits[1],bits[2]^(bits[0]&bits[1]))))
            src='context T {\n shots: 1\n backend: statevector\n seed: 1\n}\nqubits q[3]\nbits c[3]\ninvariant outcomes in {'+expected+'}\npath P {\n'+'\n'.join(gates)+'\nmeasure q -> c\n}\nverify P\n'
            self.assertEqual(verify(run(parse(src)))['status'],'PASS')

    def test_normalization_does_not_prove_recovery(self):
        c=make_case('plus','ZII')
        self.assertEqual(verify(run(parse(circuit(c,include_claim=False))))['status'],'PASS')
        self.assertEqual(evaluate_case(c)['e7q']['status'],'FAIL')

    def test_stabilizer_backend_support_request_not_assessed(self):
        c=make_case('plus','XII')
        self.assertEqual(verify(run(parse(circuit(c,backend='stabilizer'))))['status'],'NOT_ASSESSED')

    def test_algebra_all_paulis_and_generator_rejections(self):
        from e7q.qec import syndrome, StabilizerCode, QECError
        from adapter import CODE
        for p in itertools.product('IXYZ',repeat=3):
            e=''.join(p)
            self.assertEqual(syndrome(CODE,e),oracle_syndrome(e))
        for generators in [('ZZI','XII'),('ZZI','ZZI'),('III',)]:
            with self.assertRaises(QECError):StabilizerCode('invalid',generators)

if __name__ == "__main__": unittest.main()
