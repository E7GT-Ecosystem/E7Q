# Dependence-aware candidate families

Status: Q-A1 bounded contract, `v0alpha1`.

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
- explicit `restrict` receipts that enumerate excluded members;
- source-linked inventory `view` records that do not prune or identify; and
- validation that reconstructs the canonical family and rejects stale IDs.

This contract does not establish circuit equivalence, executable feasibility,
hardware availability, topology quality, optimality, probability, amplitude,
evidence weight, or scalability beyond its declared finite bounds. It does not
yet implement v0.12 `Pack`/`Quote`, ordered transformation histories,
identification, or candidate realization. Those remain Q-A2 through Q-A4.

