# SPDX-License-Identifier: Apache-2.0
"""Record native E7Q criterion boundaries and phase-blind claim controls."""
import json
from pathlib import Path
from e7q.language import parse, run, verify, compare, comparison_result, E7QError
from e7q.qec import StabilizerCode, QECError
from adapter import circuit, make_case


def program(gates):
    return parse('context P {\n shots: 8\n backend: statevector\n seed: 1\n}\nqubits q[1]\nbits c[1]\npath P {\n'+gates+'\nmeasure q -> c\n}\nverify P\n')


def main():
    result={}
    for criterion in ('measurement','global-phase'):
        result['Z-vs-I-'+criterion]=comparison_result(compare(program('Z q[0]'),program('X q[0]\nX q[0]'),criterion))
    try:
        compare(program('Z q[0]'),program('Z q[0]'),'qec-corrects-all-errors')
    except E7QError as ex:result['unknown-QEC-criterion']={'status':'rejected','reason':str(ex)}
    result['stabilizer-exact-support']=verify(run(parse(circuit(make_case('plus','XII'),backend='stabilizer'))))
    for label,generators in [('anticommuting',('ZZI','XII')),('dependent',('ZZI','ZZI'))]:
        try:StabilizerCode(label,generators)
        except QECError as ex:result[label]={'status':'rejected','reason':str(ex)}
    out=Path(__file__).parent/'results'/'claim-controls.json'
    out.write_text(json.dumps(result,indent=2)+'\n')
    print({k:v.get('status') for k,v in result.items()})

if __name__=='__main__':main()
