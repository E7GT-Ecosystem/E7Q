# Architecture

1. **E7Q source** declares context, registers, invariants, paths, views, and criteria.
2. **Parser and typed IR** resolve syntax, resources, types, and source locations.
3. **Quantum semantics engine** uses standard linear algebra for evolution and measurement.
4. **Verification engine** checks invariants and equivalence profiles at declared stages.
5. **Adapters** lower verified IR to simulators, OpenQASM, and later hardware-oriented IRs.
6. **Proof-of-Path reporter** records operations, assumptions, property status, projection loss, backend changes, and evidence.
7. **Temporal-evidence profile** records the concrete carrier description,
   TD0--TD7 order roles, declared order, chronology status, temporal
   projection, preservation and loss, versioned criterion, phase, and boundary
   crossing supported by each offline artifact.
8. **Observational-claim pilot** optionally separates supplied records and
   bounded observational claims from E7Q's statistical interpretations, while
   preserving shared divergence, unknowns, and temporal-extension boundaries.
9. **Temporal-orientation pilot** optionally declares observer locality,
   directional relation kinds, reverse-representation limits, and
   compatible-history relevance without changing executable quantum semantics.
10. **External evidence importer** safely reads supplied ZIP/directory packages,
    discovers one or more circuit records, cross-checks manifests, counts,
    QASM, mappings and calibration coverage, and emits a bounded receipt without
    executing archive content or authenticating provider claims.
11. **OpenQASM 2 importer** parses a bounded gate surface into a typed,
    non-executable artifact, preserving device-register indices, parameters,
    conditions and classical measurement destinations without allocating a
    state vector.
12. **Deterministic-reference assessor** normalizes supplied count labels under
    an explicit classical-bit order and compares declared primary bits with a
    threshold and Wilson confidence interval, separately from provenance and
    physical-fidelity judgments.

## Boundary

The E7G-T mapping organises modelling and accountability. It does not manufacture amplitudes, probabilities, unitary dynamics, or empirical validity. Those originate in the declared quantum semantics profile.

The temporal profile organises evidence about order and history. It does not
authenticate a timestamp, infer elapsed physical time, establish causation, or
claim additional physical time dimensions.

The observation pilot is an informative E7G-T UC2 experiment. It does not make
an observer's available records equivalent to reality, turn agreement into
truth, or upgrade an offline verdict into provider or hardware validation.

The temporal-orientation pilot is an informative E7G-T UC3 experiment retained
by the pinned UC4 kernel. It does
not equate reverse audit traversal with reversed dynamics or causation, equate
history-whole membership with simultaneity, or turn evidential relevance
narrowing into quantum measurement collapse or an ontological claim.

E7Q's hardware routing uses undirected coupling graphs. The legacy API and
artifact term `topology` names that graph structure only and does not invoke
the E7G-T UC4 mathematical topological-overlay pilot. In particular, graph
adjacency and routing paths are not silently treated as topological
neighbourhoods or topological paths.

## v0.1 implementation

The first implementation uses a deliberately small parser, typed structures, a NumPy state-vector engine, deterministic seeded measurement, invariant checks, and JSON/Markdown reports.
