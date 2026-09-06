# Exact real H-unitary criterion

`e7q.ir.real-h-unitary` version `1` establishes exact premeasurement unitary
matrix equality, including global phase, for id/x/z/cx/cz/swap, H, and the
literal parameter form `u2(0,pi)`. It uses its own `real-h-gate-table-v1`
assumption and does not expand any existing signed-permutation criterion.

The H table is [[1,1],[1,-1]]/sqrt(2). The u2 alias follows the
[Qiskit standard header](https://github.com/Qiskit/qiskit/blob/main/qiskit/qasm/libs/qelib1.inc),
inspected on 2026-09-06, which defines H through u2(0,pi). The local versioned
gate table governs this criterion; validation never fetches or executes includes.
Only trimmed parameter strings `0` and `pi` are admitted; approximate decimal pi,
`0.0`, symbolic rearrangements, general u2 angles and complex gates are unsupported.

## Domain and arithmetic

At most four qubits and 64 expanded gates, one quantum/classical register of
equal width, and complete terminal measurement. Ordered measurement maps and
register descriptors must match. The source/parser guards and domain checks
from the signed-permutation implementation are retained. A temporary projection
replaces H by identity only to reuse structural/domain validation; actual unitary
comparison evaluates H. It never uses that projection to establish equivalence.

For each input basis vector, integer numerators evolve under permutations,
signs and Hadamard sum/difference operations. If the circuit has k Hadamards,
the common denominator is sqrt(2)^k. Entries are canonical pairs (a,b) meaning
a+b*sqrt(2), with exact rational coefficients. This compares circuits with
different H counts, including H H versus identity. No floating-point arithmetic,
expression evaluation, sampling or tolerance participates in a verdict.
There are at most 256 matrix entries and 64 Hadamards per circuit, bounding
both matrix size and numerator growth. Quantum index zero is least significant.

## Contract

```json
{
  "criterion": {"id": "e7q.ir.real-h-unitary", "version": "1"},
  "preserves": ["unitary-prefix", "terminal-measurement-map"],
  "loses": ["source-spelling-and-gate-decomposition"],
  "assumptions": ["real-h-gate-table-v1"],
  "validation_status": "validated"
}
```

Optional profile capability: `circuit.unitary.real-h-exact`. The dedicated F2
check cites both endpoint artifacts. Unsupported syntax/options/contracts yield
UNSUPPORTED; exceeded resources BLOCKED; unequal exact matrices or inconsistent
validation status FAIL. Existing F0/F1 and native artifact formats are unchanged.
No global-phase quotient, measurement-only result, noisy channel or hardware
claim follows from this new criterion; each needs its own declared criterion.

## Acceptance evidence

```sh
python -m e7q.cli ir validate examples/e7q-ir/real-h-unitary-graph.json --level F2
python -m pytest -q tests/test_e7q_ir_real_unitary.py
```

The fixture embeds unchanged bytes from the existing source.qasm and
transpiled.qasm files, establishing the build-plan H versus u2(0,pi) case.
The historical broader workflow declaration remains unchanged; a new scoped
relation records only the equivalence established here. Tests also cover
H H = I, H Z H = X, target-H conjugation of CX, strict phase distinctions,
unsupported parameters and budgets. A separately constructed dense numerical
oracle checks 256 four-gate circuits; its tolerance is test-only. Exact identity
regressions exercise canonicalization across different Hadamard counts.

This closes the specific H/u2 acceptance gap, not arbitrary-gate or noisy-channel
support. Phase 2 native/legacy adapter work can use the available bounded F2
criteria while preserving unsupported outcomes for the remaining domains.
