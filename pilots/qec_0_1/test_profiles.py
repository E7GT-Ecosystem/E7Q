# SPDX-License-Identifier: Apache-2.0
import copy
import os
from pathlib import Path
import unittest
from profiles import load,diagram,envelope
from adapter import evaluate_case,make_case

KERNEL=Path(os.environ.get('E7GT_CHECKOUT',str(Path(__file__).parents[3]/'E7GT')))

class ProfileChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.msc=load(KERNEL/'proposals/msc-0.1/e7gt_msc_v0_1.py','test_msc')
        cls.rec=load(KERNEL/'packages/rec-0.1/e7gt_rec_v0_1.py','test_rec')
        cls.replay=load(KERNEL/'packages/rec-0.1/check_trace.py','test_replay')

    def test_fibres_and_no_map(self):
        import itertools
        full=[''.join(p) for p in itertools.product('IXYZ',repeat=3)]
        self.assertEqual(self.msc.evaluate(diagram(full,'00'))['compatible_count'],16)
        self.assertEqual(self.msc.evaluate(diagram(['III','XII','IXI','IIX'],'00'))['outcome'],'unique')
        self.assertEqual(self.msc.evaluate(diagram(['XII'],'00'))['outcome'],'incompatible')
        d=diagram(['XII'],'10')
        d['maps'][0]['table']={}
        self.assertEqual(self.msc.evaluate(d)['outcome'],'unsupported')

    def test_rec_conflict_replay_and_resigned_forgery(self):
        e=envelope([evaluate_case(make_case('plus','XII'))],True)
        w=dict(self.rec.evaluate(e).witness)
        self.assertEqual(w['query']['status'],'both')
        self.assertTrue(self.replay.check(e,w))
        w['query']['status']='supported'
        w.pop('witness_sha256')
        w['witness_sha256']=self.replay.digest(w)
        with self.assertRaises(self.replay.TraceError):self.replay.check(e,w)

    def test_rec_expansion_rejected(self):
        e=envelope([evaluate_case(make_case('plus','XII'))])
        e['claims'].append({**e['claims'][0],'id':'universal','scope':{}})
        e['rules']=[{'id':'invalid','premises':[{'claim_id':'corpus-agreement','requires':'supported'}],
                     'conclusion':{'claim_id':'universal','polarity':'support'}}]
        with self.assertRaisesRegex(self.rec.RECError,'expands scope'):self.rec.evaluate(e)

if __name__=='__main__':unittest.main()
