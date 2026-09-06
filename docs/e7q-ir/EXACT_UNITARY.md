# Exact signed-permutation unitary-prefix equality

Criterion: `e7q.ir.signed-permutation-unitary`, version `1`.
Capability: `circuit.unitary.signed-permutation`.

This bounded Phase 1C increment compares every column of the unitary prefix
using integer destination indices and signs. It uses no floating-point tolerance
and no sampling. The native E7Q dense unitary engine uses floating-point matrices;
this restricted evaluator supplies exact arithmetic without a new dependency.

## Admitted carrier and semantics

Both endpoints must pass the circuit profile's source identity, parser and
resource checks. They must have one equally named/sized quantum register and
one equally named/sized classical register, with at most eight qubits and 256
gates per endpoint. Each qubit and classical bit must appear exactly once in
terminal measurements, in the same ordered mapping at both endpoints.

The admitted normalized gates are `id`, `x`, `z`, `cx`, `cz`, `swap` with no
parameters, conditions or repeated operands. `q[0]` is the least significant
basis bit. X flips its bit; Z multiplies by minus one when its bit is set;
CX flips its second bit when its first is set; CZ changes sign when both are
set; SWAP exchanges its two bits; ID is identity. These definitions pin the
criterion's gate table. No include is executed or resolved. The include list
must be exactly `["qelib1.inc"]`; equality is conditional on the declared gate
table, not a certification of an arbitrary external file bearing that name.
Gate spellings inherit the existing importer's lowercase projection.

Each basis input produces one output basis index and a sign. Equality of all
columns establishes equality of the represented linear operators, including
phase, under this table. Terminal measurement mapping is checked separately;
measurements are not called unitary operations. Barriers, arbitrary rotations,
H/u2, reset, classical control, intermediate measurement and custom gates are
unsupported. Different registers/maps require another criterion, not inferred
renaming or permutation. Limits block assessment before enumerating columns.

## Exact relation contract

```json
{
  "criterion": {"id":"e7q.ir.signed-permutation-unitary","version":"1"},
  "preserves": ["unitary-prefix", "terminal-measurement-map"],
  "loses": ["source-spelling-and-gate-decomposition"],
  "assumptions": ["signed-permutation-gate-table-v1"],
  "validation_status": "validated"
}
```

Other options/contracts are unsupported. A mismatch of exact operators fails
this criterion even if the operators differ only by a global phase. Matching
operators with a contradictory declared relation status fail consistency.
Evidence cites the original endpoints and relation, preserving source identity
and decomposition despite their omission from the comparison carrier.

```bash
python -m e7q.cli ir validate examples/e7q-ir/exact-unitary-graph.json --level F2
```

The example checks SWAP against three CNOTs. Tests cover gate cancellation,
control order, phase-sensitive XZ/ZX, unsupported cases and budgets; an
independent integer dense-matrix oracle checks all 125 length-three words in a
five-gate test alphabet. This is software validation, not independent hardware
replication, provider authentication or arbitrary circuit-equivalence support.

## Compatibility and next gate

F0/F1, artifact IDs and existing criteria are unchanged. The new capability and
relation criterion are additive and optional. Consumers of F2 reports must retain
the criterion and its scope. Phase 1C remains incomplete: global-phase,
measurement/channel criteria and H/u2 support require their own implementation.
