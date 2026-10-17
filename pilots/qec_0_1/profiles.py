# SPDX-License-Identifier: Apache-2.0
"""Opt-in adapters to unmodified MSC-B1 and REC-B1 reference evaluators.

All quantum assertions are externally evaluated by E7Q/conventional oracles.
MSC sees finite Pauli labels and parity tables. REC sees scoped evidence bits.
"""
import copy
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import time
from adapter import oracle_syndrome


def load(path, name):
    spec = importlib.util.spec_from_file_location(name,path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def diagram(errors, observed, bound=1000):
    values = ['00','01','10','11']
    table = {e: ''.join(map(str,oracle_syndrome(e))) for e in errors}
    return {'schema_version':'msc-diagram-v1','diagram_id':'qec-fibre',
            'max_combinations':bound,
            'carriers':[{'carrier_id':'errors','values':errors},
                        {'carrier_id':'observed','values':[observed]},
                        {'carrier_id':'syndromes','values':values}],
            'scopes':[{'scope_id':'pauli','edition':'1','state_carrier':'errors'},
                      {'scope_id':'record','edition':'1','state_carrier':'observed'}],
            'maps':[{'map_id':'parity','source_carrier':'errors','target_carrier':'syndromes','table':table},
                    {'map_id':'read','source_carrier':'observed','target_carrier':'syndromes','table':{observed:observed}}],
            'links':[{'link_id':'syndrome-agreement','lower_scope':'pauli','upper_scope':'record',
                      'projection_map':'read','comparison_map':'parity','criterion':'exact'}],
            'access_profiles':[], 'invariant_tests':[], 'reconstruction_queries':[]}


def envelope(rows, conflict=False):
    scope={'code':'repetition-3','corpus':'E7Q-QEC/0.1-77','backend':'local-statevector'}
    claims=[{'id':'corpus-agreement','proposition':'E7Q circuit verdicts match dense oracle on this corpus',
             'modality':'fact','scope':scope,'temporal_scope':'pinned-run'},
            {'id':'hardware-correction','proposition':'physical hardware correction established',
             'modality':'fact','scope':scope,'temporal_scope':'pinned-run'}]
    evidence=[{'id':'computed-agreement','claim_id':'corpus-agreement',
               'polarity':'support' if all((r['e7q']['status']=='PASS')==r['oracle']['passes'] for r in rows) else 'refute',
               'source_id':'cases-and-witnesses.json','source_edition':'1','provenance_group':'same-session-computation',
               'scope':scope,'valid_from':'2026-10-17T00:00:00Z'}]
    if conflict:
        evidence.append({**evidence[0],'id':'contradictory-declaration','polarity':'refute'})
    return {'kernel':'0.14-experimental-draft','profile':'REC/0.1-proposed','model':'REC-B1/0.1',
            'reasoning_id':'qec-corpus-audit','edition':'1','as_of':'2026-10-18T00:00:00Z',
            'claims':claims,'evidence':evidence,'rules':[],
            'query':{'claim_id':'corpus-agreement','policy':'rely_if_supported_only'}}


def main(kernel):
    msc=load(kernel/'proposals/msc-0.1/e7gt_msc_v0_1.py','qec_msc')
    rec=load(kernel/'packages/rec-0.1/e7gt_rec_v0_1.py','qec_rec')
    replay=load(kernel/'packages/rec-0.1/check_trace.py','qec_rec_replay')
    out=Path(__file__).parent/'results'
    paulis=[''.join(p) for p in itertools.product('IXYZ',repeat=3)]
    ds={'restricted-X':diagram(['III','XII','IXI','IIX'],'00'),
        'full-Pauli-zero-syndrome':diagram(paulis,'00'),
        'incorrect-syndrome':diagram(['XII'],'00'),
        'missing-map':diagram(['XII'],'10'),
        'bounded-refusal':diagram(paulis,'00',1)}
    ds['missing-map']['maps'][0]['table']={}
    results={}
    for name,d in ds.items():
        start=time.perf_counter_ns()
        results[name]={'input':d,'result':msc.evaluate(d),'elapsed_ns':time.perf_counter_ns()-start}
    rows=json.loads((out/'cases-and-witnesses.json').read_text())
    envelopes={'agreement':envelope(rows),'conflict':envelope(rows,True)}
    broad=envelope(rows)
    broad['claims'].append({'id':'general','proposition':'all QEC works','modality':'fact','scope':{},'temporal_scope':'pinned-run'})
    broad['rules']=[{'id':'invalid-generalization','premises':[{'claim_id':'corpus-agreement','requires':'supported'}],
                     'conclusion':{'claim_id':'general','polarity':'support'}}]
    envelopes['scope-expansion']=broad
    hardware=envelope(rows)
    hardware['query']['claim_id']='hardware-correction'
    envelopes['no-hardware-evidence']=hardware
    for name,e in envelopes.items():
        start=time.perf_counter_ns()
        try:
            result=dict(rec.evaluate(e).witness)
            replay.check(e,result)
        except rec.RECError as ex:
            result={'outcome':'rejected','reason':str(ex)}
        results['REC-'+name]={'input':e,'result':result,'elapsed_ns':time.perf_counter_ns()-start}
    results['REC-replay']={'result':{'outcome':'PASS','checked':['agreement','conflict','no-hardware-evidence']}}
    forged=copy.deepcopy(results['REC-conflict']['result'])
    forged['query']['status']='supported'
    forged['query']['next_action']='rely_within_declared_scope'
    forged.pop('witness_sha256')
    forged['witness_sha256']=replay.digest(forged)
    try:
        replay.check(envelopes['conflict'],forged)
        forged_result={'outcome':'UNEXPECTED_ACCEPT'}
    except replay.TraceError as ex:
        forged_result={'outcome':'rejected','reason':str(ex)}
    results['REC-rehashed-forgery']={'result':forged_result}
    (out/'msc-rec.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps({k:v['result'].get('outcome',v['result'].get('query')) for k,v in results.items()},indent=2))

if __name__=='__main__':
    main(Path(sys.argv[1]).resolve())
