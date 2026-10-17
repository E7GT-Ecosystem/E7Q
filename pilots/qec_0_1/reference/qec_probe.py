#!/usr/bin/env python3
"""E7Q-QEC/0.1 reference probe. Python standard library only.

This tests standard three-qubit bit-flip quantum error correction in a
statevector model. It does NOT test the real E7Q/E7G-T implementation.
"""
import cmath
import json
import math
from itertools import combinations

N = 3

def state(a, b):
    out = [0j] * 8
    out[0], out[7] = a, b
    return out

def xflip(v, qubit):
    out = [0j] * 8
    for index, amplitude in enumerate(v):
        out[index ^ (1 << qubit)] = amplitude
    return out

def zphase(v, qubit):
    return [(-amp if index & (1 << qubit) else amp)
            for index, amp in enumerate(v)]

def syndrome(v):
    """Get simultaneous eigenvalues of Z0Z1 and Z1Z2 as bit parities.

    Every vector after X errors on the encoded code state is in one
    syndrome eigenspace. Reject more general states rather than inventing
    a deterministic measurement outcome.
    """
    parities = {( (i & 1) ^ ((i >> 1) & 1),
                  ((i >> 1) & 1) ^ ((i >> 2) & 1))
                for i, a in enumerate(v) if abs(a) > 1e-11}
    if len(parities) != 1:
        raise ValueError("No definite syndrome: model requires a measurement")
    return next(iter(parities))

DECODER = {(0, 0): None, (1, 0): 0, (1, 1): 1, (0, 1): 2}

def recover(v, decoder=DECODER):
    s = syndrome(v)
    q = decoder[s]
    return (xflip(v, q) if q is not None else v), s, q

def equal_up_to_global_phase(a, b, tol=1e-10):
    pivot = next((i for i, x in enumerate(b) if abs(x) > tol), None)
    if pivot is None:
        return all(abs(x) <= tol for x in a)
    phase = a[pivot] / b[pivot]
    return abs(abs(phase)-1) < tol and all(abs(x-phase*y)<tol for x,y in zip(a,b))

def analyze(decoder=DECODER):
    inputs = [(1+0j, 0j), (0j, 1+0j),
              (1 / math.sqrt(2), 1 / math.sqrt(2)),
              (1 / math.sqrt(2), 1j / math.sqrt(2))]
    patterns = [()] + [(i,) for i in range(N)]
    result = []
    for a,b in inputs:
        original = state(a,b)
        for flips in patterns:
            received = original
            for qubit in flips:
                received = xflip(received,qubit)
            corrected,s,action = recover(received,decoder)
            result.append({"error":list(flips), "syndrome":list(s),
                           "correction":action,
                           "passed":equal_up_to_global_phase(corrected,original)})
    return result

def logical_bitflip_failure(p):
    """Independent analytic check: >= 2 physical bit flips."""
    return 3*p*p*(1-p) + p**3

def main():
    baseline = analyze()
    assert len(baseline)==16 and all(r["passed"] for r in baseline)
    assert {(tuple(r["error"]), tuple(r["syndrome"])) for r in baseline} == {
        ((),(0,0)),((0,),(1,0)),((1,),(1,1)),((2,),(0,1))}

    # Deliberately faulty decoder: two syndrome corrections swapped.
    bad = dict(DECODER)
    bad[(1,0)],bad[(1,1)] = bad[(1,1)],bad[(1,0)]
    broken = analyze(bad)
    bad_detected = sum(not r["passed"] for r in broken)
    assert bad_detected==8

    # Phase-flip on one physical qubit is NOT corrected by this code.
    original = state(1/math.sqrt(2),1/math.sqrt(2))
    phase_corrupted = zphase(original,0)
    phase_recovered,s,_ = recover(phase_corrupted)
    phase_failure = not equal_up_to_global_phase(phase_recovered,original)
    assert phase_failure and s==(0,0)

    examples = [{"physical_bit_flip_p":p,
                 "unencoded_error_rate":p,
                 "encoded_logical_error_rate":round(logical_bitflip_failure(p),8)}
                for p in (0.01,0.05,0.1,0.25,0.5)]
    output = {"name":"E7Q-QEC/0.1 conventional reference probe",
              "quantum_state_model":"three-qubit complex statevectors",
              "single_bit_flip_reference":{"cases":len(baseline),
                  "passed":sum(r["passed"] for r in baseline)},
              "fault_injection":{"fault":"swap two syndrome recovery actions",
                  "cases":len(broken),"detected":bad_detected},
              "negative_control":{"fault":"single Z phase error",
                  "syndrome":list(s),"recovery_fails":phase_failure},
              "independent_logical_error_rate_checks":examples,
              "e7q_adapter_tested":False,
              "e7gt_adapter_tested":False,
              "claim":"Reference baseline only; no E7Q/E7G-T validation"}
    with open("qec_results.json","w",encoding="utf-8") as f:
        json.dump(output,f,indent=2)
    print(json.dumps(output,indent=2))

if __name__=="__main__":
    main()
