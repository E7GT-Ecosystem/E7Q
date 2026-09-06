# E7Q-IR Architecture

## Architecture v0.1

**Status:** experimental `v0alpha1` foundation

**Conceptual basis:** E7G-T v0.11-UC5 and the complementary E2CI evidence-to-claim discipline

E7Q-IR is E7Q's evidence-native, hardware-aware quantum intermediate
representation and execution-assurance protocol. It connects source programs,
compiler transformations, executable representations, hardware context,
observations, assessments, and bounded claims without requiring adoption of
the native E7Q language.

E7Q-IR does not replace a quantum SDK, source language, compiler, simulator,
provider, OpenQASM, QIR, or domain-specific verification method. It imports,
references, and connects such representations while making their provenance,
transformation boundaries, and admissible claims inspectable.

## Consolidation decision

The experimental quantum implementation previously developed under the name
"E7Q Fabric" is absorbed into E7Q-IR as its Evidence Core. E7Q-IR is the sole
authoritative name and namespace for this quantum protocol. No independent
quantum Fabric architecture remains.

This decision does not remove the separately proposed **E7 Global Architecture
Fabric**: that name is reserved for a possible future cross-domain integration
layer spanning E7Q-IR, E2CI, E7DB, E7 Boundary, E7FS, and external systems. It
is outside this repository and outside E7Q-IR's current implementation scope.

See [ADR-0001](ADR-0001-E7Q-IR-CONSOLIDATION.md) for the binding consolidation
decision and namespace policy.

## Layer model

1. **Evidence Core** — content-addressed artifacts, provenance, typed relations,
   transformation declarations, claim contracts, profiles, and conformance.
2. **Transformation IR** — quantum-specific lowering, compilation, routing,
   scheduling, preservation, loss, and equivalence semantics.
3. **Execution Protocol** — provider, device, calibration, job, observation,
   authentication, and witnessing records.
4. **Assurance Layer** — semantic checks, invariants, receipts, replication,
   drift, and comparative assessment.
5. **Interoperability Layer** — adapters for the native E7Q language, OpenQASM,
   QIR, SDKs, providers, and future quantum modalities.

Only the Evidence Core and a bounded circuit workflow demonstrator are
implemented in `v0alpha1`; the other layers describe the controlled direction
of extension and must not be represented as complete.

Its Evidence Core answers seven questions:

1. What was the identified source or declared intent?
2. Which representation was used?
3. What transformation connected them?
4. What did that transformation claim to preserve or lose?
5. What execution or observation was supplied?
6. What assessment was actually performed?
7. Which bounded claim, if any, does that evidence support?

## Constitutional object model

Every node is a content-addressed artifact envelope. The admitted kinds are
`intent`, `source`, `representation`, `transformation`, `execution`,
`observation`, `assessment`, and `claim`. Typed relations connect those nodes.

The core describes accountability, identity, references, capability needs,
and claim boundaries. Quantum meaning is supplied by a versioned semantic
profile. Consequently, a circuit profile cannot silently define annealing,
QEC, analog, photonic, or other semantics.

## Non-conflation rules

- representation is not source;
- transformation declaration is not semantic validation;
- structural conformance is not correctness;
- a digest establishes content identity, not authorship or truth;
- supplied execution metadata is not provider authentication;
- an observation is not an interpretation;
- a statistical assessment is not physical-fidelity evidence;
- stronger support is not automatically truth;
- a claim must retain its evidence references, boundaries, and prohibited
  inferences.

## Initial implementation boundary

E7Q-IR v0alpha1 implements F0 structural and F1 referential conformance. Its
external-circuit demonstrator hashes supplied OpenQASM files, validates supplied
aggregate counts, computes total-variation distance against a declared reference,
and emits a bounded claim artifact. It does not parse or execute the circuit.

F2 semantic verification, F3 authenticated evidence, and F4 replication remain
future milestones and are reported as such.
