# SPDX-License-Identifier: Apache-2.0
"""Execute every decoder table entry coherently, without specializing by error.

Syndrome ancillas are controls. CCX uses the standard H/T/CX decomposition;
T-dagger is seven T gates. No reference implementation or E7Q QEC oracle used.
"""
import json
from pathlib import Path
import time
from adapter import cases, circuit
from e7q.language import parse, run, verify


def ccx(a,b,t):
    def g(gate,q):return f'{gate} q[{q}]'
    def cx(x,y):return f'CX q[{x}], q[{y}]'
    def td(q):return [g('T',q)]*7
    return ([g('H',t),cx(b,t)]+td(t)+[cx(a,t),g('T',t),cx(b,t)]+td(t)+
            [cx(a,t),g('T',b),g('T',t),g('H',t),cx(a,b),g('T',a)]+td(b)+[cx(a,b)])


def table_gates(decoder):
    gates=[]
    for s,action in decoder:
        controls=[i+3 for i,v in enumerate(s) if v=='0']
        gates += [f'X q[{i}]' for i in controls]
        for i,p in enumerate(action):
            if p=='I':continue
            if p=='Y':gates += [f'S q[{i}]']*3
            if p=='Z':gates += [f'H q[{i}]']
            gates += ccx(3,4,i)
            if p=='Y':gates += [f'S q[{i}]']
            if p=='Z':gates += [f'H q[{i}]']
        gates += [f'X q[{i}]' for i in reversed(controls)]
    return gates


def table_source(c):
    # Replace only the recovery span using parsed operation position, not text matching.
    src=circuit(c)
    lines=src.splitlines()
    start=lines.index('CX q[2], q[4]')+1
    end=lines.index('CX q[0], q[2]',start)
    return '\n'.join(lines[:start]+table_gates(c.decoder)+lines[end:])+'\n'


def main():
    out=Path(__file__).parent/'results'
    rows=[]
    for c in cases():
        if not c.case_id.startswith(('good-','swapped-decoder-','phase-control-')):continue
        src=table_source(c)
        start=time.perf_counter_ns()
        report=verify(run(parse(src)))
        rows.append({'case_id':c.case_id,'source':src,'e7q':report,'elapsed_ns':time.perf_counter_ns()-start})
    (out/'decoder-table.json').write_text(json.dumps(rows,indent=2)+'\n')
    print({name:sum(r['e7q']['status']=='FAIL' for r in rows if r['case_id'].startswith(name)) for name in ('good-','swapped-decoder-','phase-control-')})

if __name__=='__main__':main()
