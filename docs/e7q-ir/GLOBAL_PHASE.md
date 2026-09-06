# Bounded global-phase equivalence

`e7q.ir.signed-permutation-global-phase` version `1` compares the unitary
prefixes of two circuits up to one global phase. It is separate from exact
unitary equality and never weakens the existing exact criterion.

## Domain and algorithm

All [exact signed-permutation restrictions](EXACT_UNITARY.md) apply: the pinned
id/x/z/cx/cz/swap gate table, at most eight qubits and 256 expanded gates,
one quantum and one classical register, and complete terminal measurements.
Register descriptors and ordered measurement maps must match. Includes are
not resolved or executed. Dynamic, noisy, arbitrary-angle and other gates
remain unsupported. Existing source/parser resource guards also apply.

For this real signed-permutation domain, an admissible global phase can only
be +1 or -1. Each basis column has one nonzero coefficient in that set.
The first column determines a candidate sign. Every column must have the same
output row on both sides and its coefficients must satisfy that same sign.
The test is exact, with no numerical tolerance. The PASS message reports the
witness as `U_source = (+1) U_target` or `U_source = (-1) U_target`.

Thus XZ and ZX pass this criterion but fail exact equality. Z and identity
fail both: their signs differ between basis columns. Matching a subset of
inputs or matching computational-basis counts is insufficient.

## Relation contract

```json
{
  "criterion": {"id": "e7q.ir.signed-permutation-global-phase", "version": "1"},
  "preserves": ["unitary-prefix-up-to-global-phase", "terminal-measurement-map"],
  "loses": ["source-spelling-and-gate-decomposition", "global-phase"],
  "assumptions": ["signed-permutation-gate-table-v1"],
  "validation_status": "validated"
}
```

The circuit-basic profile advertises optional capability
`circuit.unitary.signed-permutation-global-phase`. F2 reports use a dedicated
criterion check ID with the two endpoint artifact IDs as evidence references.
Unsupported contracts or syntax return UNSUPPORTED, exhausted budgets BLOCKED,
and an assessed difference or contradictory validation status FAIL.
Existing F0/F1 meanings and native artifact identities are unchanged.

This equivalence concerns the entire admitted prefix. It does not authorize
replacement inside a controlled operation: controlling two operators that
differ by a global phase can introduce a relative phase. No controlled
embedding, hardware fidelity or provider authenticity is assessed. Full
Phase 1C, H versus u2(0,pi), general complex gates and channels remain pending.

## Example and acceptance

```sh
python -m e7q.cli ir validate examples/e7q-ir/global-phase-graph.json --level F2
python -m pytest -q tests/test_e7q_ir_global_phase.py tests/test_e7q_ir_unitary.py
```

The example compares XZ with ZX. Acceptance includes unchanged exact-equality
failures for opposite signs, relative-phase and permutation counterexamples,
unsupported declarations, resource bounds and deterministic reports. An
independent dense integer-matrix oracle checks all 225 pairs of one-qubit
X/Z words of length zero through three.
