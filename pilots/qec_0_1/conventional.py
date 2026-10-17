# SPDX-License-Identifier: Apache-2.0
"""Conventional Stim tableau oracle independent of E7Q's simulator and verifier."""
import json
from pathlib import Path
import statistics
import time
import stim
from adapter import QECCase

STABILIZERS={'zero':['ZII','IZI','IIZ'], 'one':['-ZII','-IZI','-IIZ'],
             'plus':['XXX','ZZI','IZZ'], 'plus_i':['YXX','ZZI','IZZ']}


def check(c):
    sim=stim.TableauSimulator()
    sim.set_inverse_tableau(stim.Tableau.from_stabilizers([stim.PauliString(p) for p in STABILIZERS[c.preparation]]).inverse())
    for i,p in enumerate(c.error):
        if p!='I':getattr(sim,p.lower())(i)
    observed=tuple(int(sim.peek_observable_expectation(stim.PauliString(g))==-1) for g in c.generators)
    for i,p in enumerate(c.recovery):
        if p!='I':getattr(sim,p.lower())(i)
    restored=[sim.peek_observable_expectation(stim.PauliString(p)) for p in STABILIZERS[c.preparation]]
    return {'syndrome':observed,'restoration_expectations':restored,
            'passes':observed==c.expected_syndrome and all(x==1 for x in restored)}


def main():
    out=Path(__file__).parent/'results'
    rows=json.loads((out/'cases-and-witnesses.json').read_text())
    timings=[]
    results=[]
    for row in rows:
        c=QECCase.from_json(row['case'])
        start=time.perf_counter_ns()
        report=check(c)
        results.append({'case_id':c.case_id,'stim':report,'elapsed_ns':time.perf_counter_ns()-start,
                        'agrees_with_e7q':report['passes']==(row['e7q']['status']=='PASS'),
                        'agrees_with_dense_oracle':report['passes']==row['oracle']['passes']})
    for _ in range(5):
        for r in rows:
            c=QECCase.from_json(r['case'])
            start=time.perf_counter_ns()
            check(c)
            timings.append(time.perf_counter_ns()-start)
    result={'stim_version':stim.__version__,'cases':results,'all_agree':all(r['agrees_with_e7q'] and r['agrees_with_dense_oracle'] for r in results),
            'timing':{'median_ns':statistics.median(timings),'min_ns':min(timings),'calls':len(timings)},
            'boundary':'Separate mathematical implementation and backend; same-session author, no external review. Checks three independent signed stabilizers of each prepared pure state, not a universal recovery theorem.'}
    (out/'conventional-stim.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='cases'},indent=2))

if __name__=='__main__':main()
