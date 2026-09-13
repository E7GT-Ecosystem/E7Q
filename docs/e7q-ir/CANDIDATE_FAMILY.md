# Dependence-aware candidate families

Status: Q-A1 family `v0alpha1`; additive restriction/view correction `v0alpha2`.

The candidate-family contract represents a finite compilation search space
without silently inventing independence. Alternatives placed in one factor are
correlated. Only separate factors are combined by Cartesian product, which is
an explicit caller declaration that those choices may vary independently.

For example, two valid `(layout, target)` pairs belong in one factor and yield
two members, not the four-member cross-product. A separately declared pass
ordering factor may then combine with either placement.

The implementation provides:

- canonical factor, alternative, member and family identities;
- bounded expansion with typed errors instead of an empty-family result;
- versioned, byte-bounded restriction criteria with canonical residual-family
  identities and distinct `success`, `empty`, `invalid_input`, and
  `resource_limit` outcomes;
- source-linked inventory `view` records that explicitly declare preserved and
  lost information and require return to the exact source; and
- validation that reconstructs the canonical family and rejects stale IDs.

The original `v0alpha1` restriction and view functions remain available for
compatibility, but new work must use the corrected additive profiles. Q-A2
ordered histories consume the residual-family identity only from a successful
restriction; empty and other non-success records publish no residual family.

This contract does not establish circuit equivalence, executable feasibility,
hardware availability, topology quality, optimality, probability, amplitude,
evidence weight, or scalability beyond its declared finite bounds. It does not
yet implement v0.12 `Pack`/`Quote`, identification, or candidate realization.
Those remain separate later gates.
