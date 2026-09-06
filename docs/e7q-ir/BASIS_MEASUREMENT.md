# Bounded computational-basis measurement equivalence

Criterion `e7q.ir.signed-permutation-basis-measurement`, version `1`, establishes
that both circuits produce the same terminal classical outcome for **every
computational-basis input**, under the pinned signed-permutation gate table.
It does not assume that testing only the all-zero input is sufficient.

The domain and limits are those of [exact unitary comparison](EXACT_UNITARY.md):
id/x/z/cx/cz/swap only, at most eight qubits and 256 expanded gates, one quantum
and classical register of equal width, and complete terminal measurement.
Register descriptors and ordered measurement maps must match. Dynamic/noisy
operations, partial measurements, arbitrary gate sets and general channels
remain unsupported. Existing source-byte and parser budgets apply.

For each basis input the exact evaluator gives one output basis vector and a
sign. The measurement criterion discards the sign and applies the qubit-to-
classical-bit map to that output. Every resulting classical outcome must match.
An integer outcome uses classical index zero as its least significant bit.
No sampling or tolerance is used. FAIL includes the first differing input and
both outcomes; PASS reports the number of basis inputs checked. The F2 report
cites the two circuit artifact IDs under a dedicated criterion check ID.

## Required transformation declaration

```json
{
  "criterion": {"id": "e7q.ir.signed-permutation-basis-measurement", "version": "1"},
  "preserves": ["terminal-outcome-for-every-computational-basis-input", "terminal-measurement-map"],
  "loses": ["source-spelling-and-gate-decomposition", "global-and-relative-phase"],
  "assumptions": ["signed-permutation-gate-table-v1"],
  "validation_status": "validated"
}
```

This is optional capability `circuit.measurement.signed-permutation-basis` in
the circuit-basic profile. F0/F1 and native artifact formats do not change.
Missing phase-loss accounting, unsupported options or an unsupported domain
return UNSUPPORTED; resource excess returns BLOCKED. Assessed outcome differences
and contradictory validation status return FAIL.

Z versus identity passes this measurement criterion while failing exact and
global-phase unitary equality. CX versus identity fails despite agreeing on
the all-zero input. Phase-sensitive subsequent processing, other measurement
bases, arbitrary state/quantum-channel equality, controlled embedding and
hardware fidelity are not assessed by this criterion.

## Validation

```sh
python -m e7q.cli ir validate examples/e7q-ir/basis-measurement-graph.json --level F2
python -m pytest -q tests/test_e7q_ir_measurement.py
```

The example compares Z with identity. Tests cover all-input counterexamples,
strict separation from unitary criteria, phase-loss contracts, resource bounds,
classical-bit mapping and deterministic reports. An independent dense-matrix
oracle compares complete squared-magnitude matrices for 169 pairs of short
two-qubit circuits. Full Phase 1C remains incomplete; the H/u2 example and
broader gates require a separately validated extension.
