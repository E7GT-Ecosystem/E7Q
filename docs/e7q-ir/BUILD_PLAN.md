# E7Q-IR Build Plan and AI Engineering Handoff

**Plan version:** 0.3

**Status:** authoritative implementation plan for the experimental E7Q-IR line.

**Current inspected baseline (2026-09-06):** `main` at
`c1608b11464b5a5b0a45f221907a8c27b1bb51ff` (PR #41).
The last implementation milestone passed 306 tests and GitHub CI.
This documentation revision changes no executable capability or conformance meaning.

**Revision 0.3:** integrates the agreed review-driven hardening packages in
[REVIEW_HARDENING.md](REVIEW_HARDENING.md). All H1–H10 packages remain planned;
existing tests are inputs to their gap analysis, not evidence of completing them.
Research packages R1–R6 and their [source register](RESEARCH_FOUNDATIONS.md)
remain in force. Phase dependencies and F0–F4 meanings are unchanged.

**Completed bounded increments:** F2 framework; embedded OpenQASM 2/counts/TVD
and claim-support checks; byte and parsed structural identity; exact and
global-phase signed-permutation criteria; all-basis measurement comparison;
noiseless unitary-channel comparison; exact real H/u2(0,pi) criterion.
Each retains its own domain and limits. General angles, complex-gate IR criteria,
noisy-channel IR criteria and general Phase 1C coverage remain incomplete.

**Next package:** H1/H4 review evidence and capability reconciliation, then H2/H3
IR and bundle hardening before extending Phase 2 native/legacy adapters and the
optional external Aer demonstration (H5/H6). The initial reconciliation in this
revision does not complete the executable review harness or capability matrix.

**Historical baseline:** `b7dc357` had 181 passing tests and F0/F1 only.
PRs #35–#37 merged framework/identity/exact signed-permutation work at `83b273a4`;
#38 global phase at `328b00ff`; #39 basis measurement at `676d34fa`;
#40 noiseless channel at `1226a1a9`; #41 exact real H/u2 at `c1608b11`.
Earlier local/queued checkpoints are historical and do not override current status.

## 1. Purpose

This document allows a new engineer or AI coding agent to continue E7Q-IR
without reconstructing architectural decisions from prior conversations.
It defines the required reading, current implementation boundary, dependency
order, work packages, acceptance gates, prohibited shortcuts, and the first
executable assignment.

This plan is subordinate to:

1. E7G-T v0.11-UC5 as the constitutional modelling and reasoning kernel;
2. the E7G-T Ecosystem Operating Kernel and its E7Q-IR instruction;
3. [ADR-0001](ADR-0001-E7Q-IR-CONSOLIDATION.md);
4. [ARCHITECTURE.md](ARCHITECTURE.md);
5. [PROTOCOL.md](PROTOCOL.md); and
6. [CONFORMANCE.md](CONFORMANCE.md).

If an implementation proposal conflicts with those sources, stop and record
the conflict. Do not silently redefine the architecture in code.

## 2. Product direction

E7Q-IR is E7Q's evidence-native, hardware-aware quantum intermediate
representation and execution-assurance protocol. Its role is to connect:

```text
source intent
-> source representation
-> transformations
-> executable representation
-> execution context
-> observations
-> assessments
-> bounded claims
```

E7Q-IR is not a replacement for Qiskit, Cirq, OpenQASM, QIR, a provider SDK,
or a domain verification method. It makes their relationships, transformations,
evidence, limitations, and permitted claims inspectable.

The native E7Q language is one front end into E7Q-IR. External users must be
able to use E7Q-IR without adopting that language.

The former quantum "E7Q Fabric" name is retired. Do not recreate a parallel
Fabric package, schema namespace, CLI, registry, or roadmap. The future
cross-domain E7 Global Architecture Fabric is outside this repository.

## 3. Constitutional engineering rules

Every increment must preserve these rules:

1. A representation is not automatically its source.
2. A transformation declaration is not semantic validation.
3. Equivalence exists only under a named, versioned criterion.
4. Every material transformation records preservation, loss, assumptions, and
   validation status.
5. Observation, assessment, interpretation, and claim remain distinct.
6. Content identity does not establish authorship, chronology, correctness, or
   truth.
7. Structural conformance does not establish quantum-semantic correctness.
8. Semantic conformance does not authenticate a provider or establish physical
   fidelity.
9. A claim cannot be stronger than its evidence path.
10. Unsupported capabilities fail closed and remain inspectable.
11. `NOT_ASSESSED`, `BLOCKED`, `UNSUPPORTED`, `FAIL`, and `PASS` must not be
    collapsed into a binary success flag.
12. Negative, null, conflicting, and inconclusive results are retained.
13. Time, calibration, provider identity, and execution chronology are claims
    requiring their own support.
14. No test, digest, signature, simulation, or formal-looking report may be
    described as more than it establishes.

## 4. Current implementation boundary

### 4.1 Implemented

- content-addressed artifact envelopes;
- deterministic canonical JSON encoding;
- typed evidence graphs and relation identities;
- transformation preservation/loss declarations;
- bounded claim contracts;
- profile and capability negotiation;
- F0 structural conformance;
- F1 referential conformance;
- an external OpenQASM/counts demonstrator independent of the E7Q language;
- a descriptive total-variation-distance assessment;
- CLI commands `e7q ir build`, `e7q ir validate`, and `e7q ir inspect`;
- schemas, examples, documentation, and adversarial tests;
- existing E7Q language, simulators, equivalence machinery, compiler traces,
  external evidence importer, receipts, replication, drift, trend, QEC, and
  comparative-experiment components outside the new IR package;
- F2 semantic framework and bounded circuit payload checks;
- separately versioned transformation criteria: [identity](PHASE_1C.md),
  [exact signed permutation](EXACT_UNITARY.md), [global phase](GLOBAL_PHASE.md),
  [basis measurement](BASIS_MEASUREMENT.md), [noiseless channel](UNITARY_CHANNEL.md)
  and [exact real H/u2](REAL_H_UNITARY.md).

### 4.2 Not implemented

- general circuit semantics beyond the implemented bounded F2 criteria;
- Phase 2 native/legacy-to-IR adapters and the proposed Aer adapter;
- a production OpenQASM 3 bridge;
- a QIR bridge;
- authenticated provider execution evidence;
- F3 signature/identity/attestation conformance;
- F4 replication conformance;
- stable third-party profile loading and governance;
- annealing, analog, photonic, measurement-based, or full QEC profiles;
- a remote registry, server, dashboard, or hosted service.

### 4.3 Important boundary in the present demonstrator

The external builder preserves supplied circuit identities and counts. Applicable
F2 validators can inspect embedded bytes and establish separately named bounded
transformation criteria. Hashing or parsing alone establishes no equivalence.
The original H/u2 pair now has an applicable exact-real criterion; earlier graph
artifacts must not be retrospectively upgraded without validation under that
criterion. No such check executes hardware, authenticates a provider or proves
that a declared transpiler produced a supplied file.

## 5. Repository map

| Area | Current responsibility |
| --- | --- |
| `src/e7q/ir/` | E7Q-IR Evidence Core and workflow demonstrator |
| `src/e7q/ir/conformance.py` | conformance orchestration and per-level report |
| `src/e7q/ir/profiles.py` | built-in profile declarations and negotiation |
| `src/e7q/ir/workflow.py` | external circuit evidence-graph builder |
| `schemas/e7q-ir/` | public experimental JSON schemas |
| `profiles/` | serialised semantic profile declarations |
| `examples/e7q-ir/` | executable handoff fixtures |
| `tests/test_e7q_ir.py` | current IR regression and adversarial suite |
| `src/e7q/openqasm2.py` | bounded non-executing OpenQASM 2 importer |
| `src/e7q/language.py` | native language, execution, comparison, and compilation |
| `src/e7q/artifacts.py` | legacy registered E7Q artifact validation |
| `src/e7q/results.py` | execution bundle/result/receipt handling |
| `src/e7q/campaigns.py` | replication assessment |
| `src/e7q/drift.py` | drift assessment |

Do not immediately move all legacy E7Q components into `src/e7q/ir/`. Integrate
them through explicit adapters and contracts first. Physical reorganisation is
permitted only after behaviour and compatibility are covered by tests.

## 6. Conformance model

| Level | Required conclusion | Explicitly excluded conclusion |
| --- | --- | --- |
| F0 Structural | object shape and content identities conform | references or semantics are valid |
| F1 Referential | graph references and identities resolve | quantum meaning is correct |
| F2 Profile semantic | named profile rules pass under named criteria | execution is authentic or physically faithful |
| F3 Authenticated | declared identities/signatures/attestations verify | all scientific claims are true |
| F4 Reproduced | declared replication conditions are satisfied | universal validity, advantage, or causation |

Passing one level never implies a later level. A report must provide per-level
results and the highest level actually passed.

## 7. Dependency-ordered build programme

The order below is normative unless an ADR records a justified change.

### Phase 0 — Evidence Core foundation

**Status:** complete at baseline `b7dc357`.

Do not redesign Phase 0 while implementing later phases unless a failing test,
security defect, or documented protocol contradiction requires it.

### Phase 1 — F2 circuit-profile semantic validation

**Objective:** add real profile-specific validation without representing
declarations as verified semantics.

#### Phase 1A — Semantic validation framework

Deliver:

- a validator interface and registry separate from capability negotiation;
- deterministic semantic-result objects with check identifiers and evidence
  references;
- per-artifact and per-relation results;
- explicit `PASS`, `FAIL`, `BLOCKED`, `UNSUPPORTED`, and `NOT_ASSESSED` states;
- F2 aggregation that passes only when all required semantic checks pass;
- continued structural inspection when a profile is missing;
- CLI support for requesting F2 without changing F0/F1 meanings.

Acceptance:

- F0/F1 outputs remain backward-compatible within `v0alpha1`;
- an unknown profile is F0/F1-inspectable and F2 `BLOCKED`;
- a malformed profile payload fails deterministically;
- an unimplemented transformation criterion is `NOT_ASSESSED`, not `PASS`;
- report ordering and content identities are deterministic;
- focused valid, invalid, blocked, tampered, and adversarial tests pass;
- the complete pre-existing suite passes.

#### Phase 1B — `circuit-basic` validators

Deliver validators for:

- supported OpenQASM 2 syntax and declared format consistency using the bounded
  importer in `src/e7q/openqasm2.py`;
- source/executable byte identities and format declarations;
- count outcome width, label order, shot totals, and register compatibility;
- deterministic recomputation of observed distributions and TVD;
- assessment threshold and claim-support consistency;
- evidence-reference and prohibited-inference retention.

Do not claim general circuit equivalence in this subphase.

Acceptance:

- corrupt or unsupported QASM fails or blocks the relevant F2 check;
- count width inconsistent with the declared classical register blocks F2;
- a tampered TVD or claim-support status fails F2 after identities are rehashed;
- source/executable parsing success does not validate their transformation;
- every semantic verdict cites the artifacts and criterion used.

#### Phase 1C — First bounded transformation criteria

Implement criteria incrementally:

1. byte identity;
2. parsed structural identity under a pinned OpenQASM 2 normalisation;
3. supported exact unitary equivalence;
4. supported global-phase equivalence;
5. supported computational-basis measurement equivalence;
6. supported channel criteria only where the existing E7Q engine can establish
   them without ignoring dynamic or noisy semantics.

Each criterion must state its domain, exclusions, tolerances, resource limits,
and evidence output. Unsupported syntax or scale is `UNSUPPORTED` or `BLOCKED`,
not semantic inequality.

Acceptance:

- at least one identity-transform fixture passes F2 end to end;
- the current `H` versus `u2(0,pi)` example passes only after an applicable
  criterion genuinely establishes the declared equivalence;
- non-equivalent, unsupported, excessive-resource, and ambiguous cases have
  separate expected results;
- transformation `validation_status` agrees with the criterion report.

**Phase 1 gate:** E7Q-IR can produce at least one honest F2-conformant external
circuit graph, while current unsupported cases remain explicitly bounded.

### Phase 2 — Native E7Q and legacy evidence adapters

**Objective:** connect existing E7Q capability to E7Q-IR without making the
native language mandatory.

Deliver:

- a native E7Q source/intent adapter;
- conversion of existing compilation Proof-of-Path into transformation and
  representation artifacts;
- conversion of execution bundles and receipts into execution/observation
  artifacts;
- adapters for existing external-bundle and deterministic-assessment outputs;
- stable source references back to original legacy artifacts;
- round-trip or declared-loss reports for every adapter.

Acceptance:

- existing artifact schemas remain readable;
- adapter output passes F0/F1 and applicable F2 checks;
- no adapter silently upgrades legacy evidence;
- a native E7Q Bell workflow and an external OpenQASM Bell workflow produce
  comparable E7Q-IR paths under explicitly declared criteria;
- all existing rc12 behaviour remains operational.

**Phase 2 gate:** E7Q-IR is the shared evidence path for both the native E7Q
front end and at least one external workflow.

### Phase 3 — Production OpenQASM 3 bridge

**Objective:** support a documented production subset with honest preservation
and loss accounting.

Deliver:

- a pinned OpenQASM 3 compatibility profile;
- parser/import adapter for the admitted subset;
- export adapter where representable;
- classical control, measurement, timing, calibration, and external-definition
  boundaries declared separately;
- import/export/round-trip transformation artifacts;
- versioned negative corpus for unsupported constructs.

Acceptance:

- grammar coverage is documented construct by construct;
- unsupported constructs fail closed with source location;
- round trips compare under named criteria rather than textual equality alone;
- no included or linked source is executed during inspection;
- cross-SDK fixtures cover at least two independent producers when available.

### Phase 4 — QIR interoperability bridge

**Objective:** allow LLVM/QIR-based workflows to emit and consume E7Q-IR
evidence without treating QIR as equivalent to source intent or hardware
execution.

Deliver:

- pinned QIR and LLVM compatibility declarations;
- module identity and metadata capture;
- entry point, callable, result, qubit, runtime, and profile accounting;
- transformation contracts between supported OpenQASM/E7Q representations and
  QIR modules;
- static inspection separated from runtime execution;
- resource and capability limits.

Acceptance:

- valid reference modules are inspectable and content-addressed;
- unsupported dialect/profile features block semantic processing;
- module verification does not imply quantum-semantic equivalence;
- at least one external QIR-producing workflow enters an F0/F1 E7Q-IR path;
- applicable F2 claims require a separate verified criterion.

### Phase 5 — Execution protocol and F3 authentication

**Objective:** bind jobs and results to explicit identities and attestations.

Before implementation, add a security ADR defining:

- signed bytes and canonicalisation;
- signer/provider/key identity;
- trust roots and delegation;
- revocation and key rotation;
- timestamp and clock assumptions;
- nonce, replay, and job-binding rules;
- calibration binding;
- disclosure and redaction semantics;
- the maximum conclusion each attestation permits.

Deliver provider-neutral contracts first. Provider adapters follow as separate
profiles. E7 Boundary integration may protect or authenticate artifacts, but a
cryptographic envelope must not be treated as evidence that the enclosed
scientific assertions are true.

Acceptance:

- signature, identity, chronology, provider attribution, and physical fidelity
  are independent checks;
- replay, wrong-job, wrong-result, expired-key, revoked-key, and altered-context
  fixtures fail;
- an unauthenticated receipt remains inspectable and does not pass F3;
- no live job is submitted by tests;
- credentialed integration tests are opt-in and secret-safe.

### Phase 6 — F4 replication conformance

**Objective:** connect existing replication/drift machinery to explicit
replication protocols and evidence paths.

Deliver:

- a replication protocol artifact;
- declared invariants, controlled variables, permitted variations, temporal
  windows, stopping rules, and statistical method identity;
- links among original and replicated graphs;
- conflict, null-result, and drift preservation;
- F4 aggregation distinct from F3 and scientific generalisation.

Acceptance:

- replication cannot pass from two unrelated count files;
- comparability and independence assumptions are explicit;
- reproduced-under-declared-conditions does not imply universal validity;
- negative and inconclusive replications remain first-class outputs;
- existing campaign, drift, and trend tests remain valid.

### Phase 7 — Additional quantum semantic profiles

Add profiles only after the core extension boundary survives Phases 1-4.
Recommended order:

1. stabilizer/QEC evidence;
2. hybrid quantum-classical workflows;
3. annealing/QUBO/Ising evidence;
4. measurement-based computation;
5. analog and pulse-level computation;
6. photonic computation.

Each profile requires independent semantics, fixtures, limitations, and domain
review. Circuit terminology must not be silently reused for another modality.

### Phase 8 — Conformance suite, governance, and release

Deliver:

- versioned golden, invalid, adversarial, unsupported, and resource-limit
  vectors;
- a third-party implementer conformance runner;
- profile registration and namespace rules;
- protocol compatibility and deprecation policy;
- security and threat-model review;
- packaging and reproducible release process;
- at least one implementation or exercise independent of the core team;
- buyer/pilot validation before commercial claims.

Do not call E7Q-IR a standard merely because a schema and test suite exist.

### Research-backed work packages within the existing phases

The following packages are part of this build plan. Source identifiers refer to
[RESEARCH_FOUNDATIONS.md](RESEARCH_FOUNDATIONS.md). They refine the phases above;
they do not create a parallel product or authorise skipping a phase gate.

#### R1 — Bounded verification and an external circuit corpus (Phases 1B/1C)

- Complete outstanding Phase 1B acceptance criteria, then implement byte and
  parsed structural identity before broader semantic criteria.
- Define unitary equality, equality up to global phase, measurement-behaviour
  agreement and channel equality as distinct, versioned criteria [01].
- After a criterion contract exists, add an optional MQT QCEC adapter [02],
  followed by a complementary PyZX adapter [03]. Record method, supported
  fragment, input/output permutation, phase convention, tolerance, tool version,
  raw verdict and time/memory limits. Backend choice must not change the meaning
  of the criterion.
- Preserve inconclusive outcomes with a documented mapping to existing
  non-PASS states and reasons. Simulation agreement is not universal equality;
  unsuccessful ZX reduction is not non-equivalence. Do not add a public status
  enum without a protocol change.
- Select a small pinned QASMBench/MQT Bench corpus [22-23], with documented
  exclusions. Add identity, altered gate, phase-only, swapped output,
  measurement/reset, unsupported and resource-exhaustion cases. Include
  non-palindromic results to expose bit-order mistakes [11].

Acceptance: at least one external transformation passes its named F2 criterion;
negative and inconclusive cases remain distinguishable; checker disagreement
is retained and prevents a combined proof claim until resolved. No sampled
histogram agreement is promoted to a universal semantic claim.

#### R2 — Versioned interoperability and hybrid trace capture (Phases 2-4)

- Adapt legacy/native artifacts without strengthening their original evidence.
- Pin OpenQASM grammar and include-resolution rules; publish a construct-level
  matrix for classical control, measurement, timing and calibration [06].
- Pin QIR and LLVM versions, profile, QIS and output schema; start with a bounded
  Base Profile import and preserve output ordering [07-08]. Adaptive-profile
  support requires a separate verified compatibility contract.
- Distinguish sampled measurements from expectation-value estimates in result
  adapters [10]. Retain original records and register/measurement maps [11].
- Evaluate Catalyst as an external hybrid producer [09]. Capture parameter
  bindings, compiler options and intermediate artifacts; the complete hybrid
  semantic profile remains Phase 7 work.

Acceptance: original bytes and transformed artifacts remain separately
addressable; round trips declare preservation/loss; unsupported constructs
block their semantic checks; static inspection never invokes source, LLVM
runtime functions or provider jobs. Module verification alone cannot pass a
quantum-equivalence criterion.

#### R3 — Provenance interoperability and attestations (Phases 2 and 5)

- Define a PROV-DM export mapping for artifacts, activities, agents and
  derivations [12]. Report unmapped E7Q claims, uncertainty and relation types;
  a lossy export must not be represented as a lossless round trip.
- Evaluate DSSE as an envelope candidate under the required Phase 5 security
  ADR [13], coordinated with E7 Boundary rather than duplicating its remit.
- Bind submitted/executed artifact IDs, job identity, backend capability
  snapshot, parameters, requested/completed shots, calibration references and
  timestamp origins. Preserve unsigned provider imports as such.

Acceptance: test altered payloads, wrong signer/job, replay, revoked keys and
missing trust material. An importer signature cannot be labelled a provider
signature; asserted provenance cannot become authenticated provenance merely
through conversion. Provider attestation availability remains an explicit
integration dependency.

#### R4 — Replication, benchmarks and characterization (Phase 6)

- Separate deterministic analysis replay, simulator rerun and independent
  hardware replication in protocol artifacts.
- Add MQT Bench/SupermarQ workload evidence adapters [23-24]: algorithm instance,
  abstraction level, compiler/target configuration, scoring method, raw outputs
  and resource disclosures must accompany a comparison.
- Add a pyGSTi import/analysis adapter rather than rebuilding tomography [25-27].
  Preserve model family, preparation/measurement assumptions, gauge convention,
  fit diagnostics, uncertainty, protocol variant, sequence lengths, seeds and
  repetitions where applicable.

Acceptance: identical-data replay cannot pass an independent-experiment
criterion; missing comparability assumptions block the relevant claim; negative,
null and conflicting observations survive aggregation. Benchmark scores, RB
metrics, GST estimates and workload fidelity remain distinct claims. Classical
baselines and resource accounting are required before any advantage assessment.

#### R5 — Modality-specific extensions (Phase 7, existing order retained)

1. **Stabilizer/QEC [20-21]:** import Stim circuits and detector error models;
   retain measurement references, detectors, logical observables, noise,
   repeats, circuit-to-DEM options and decoder identity/configuration. Test
   record offsets and repeat limits. Preserve DEM suggested decomposition
   semantics; do not turn decomposed components into independent errors.
   Synthetic-noise results cannot certify hardware thresholds.
2. **Hybrid [09-11]:** record classical parameter updates, optimizer state and
   stopping rule, objective/observable definitions, circuit instances and
   per-evaluation observations. Test parameter-to-result binding and incomplete
   histories. A final circuit is not the entire hybrid experiment.
3. **Annealing/BQM [14-15]:** retain BINARY/SPIN domains, ordered variables,
   coefficients and offsets; separately capture physical embedding, chains,
   chain strength and unembedding. Exhaustively test small-model QUBO/Ising
   energy correspondence. Correct conversion does not establish optimality.
4. **Measurement-based:** first obtain and review a dedicated formalism and
   execution-format corpus. Require measurement dependencies, adaptive
   corrections, outcome semantics and a bounded equivalence criterion before
   implementation. ZX circuit rewriting alone does not satisfy this gate.
5. **Analog/pulse [16-17, 06]:** start with an Aquila/AHS-specific profile:
   site coordinates/filling, explicit units, waveforms, Hamiltonian parameters,
   capabilities and per-shot pre/post sequences. Test site/result widths,
   units and waveform constraints; retain missing atoms and postselection.
   Pin Bloqade exports per sweep instance. Pulse calibration and other analog
   families require separate domain-reviewed semantics and source corpora.
6. **Photonic [18-19]:** import a pinned Blackbird subset; preserve modes,
   parameter/template bindings, target, feed-forward and measurement order.
   Record continuous-variable result types and simulation approximations.
   Test missing bindings, result ordering and unsupported operations; do not
   coerce continuous measurements into qubit-count semantics.

Acceptance for each: independent positive, negative, unsupported and
resource-limit fixtures; explicit assumptions and maximum claims; domain review;
and F0/F1 inspection even when F2 semantics are unavailable. These proposed
profile families are not registered capability promises until implemented.

#### R6 — Proof artifacts, extension governance and research gates (Phase 8)

- Evaluate VOQC/SQIR-style proof-bearing transformations [04] as an optional
  assurance class. Bind theorem, assumptions, formalization version and
  extraction/build provenance; distinguish imported proof assertions from
  independently checked proof artifacts.
- Publish source-to-requirement-to-fixture mappings, adapter coverage, migrations
  and third-party conformance vectors. Independently exercise at least one
  extension and one intentionally unsupported case.
- Maintain research gates for distributed/networked quantum protocols,
  fault-tolerant resource estimation and decoder interoperability. Each needs
  primary sources, domain semantics, a concrete user workflow and acceptance
  criteria before becoming an implementation commitment.

Acceptance: no proof claim exceeds the checked theorem/domain; an unimplemented
or unreviewed extension cannot advertise F2 support; independent conformance
results identify exact profile and tool versions.

### Review-driven hardening packages

[REVIEW_HARDENING.md](REVIEW_HARDENING.md) defines H1–H10, priorities,
phase placement, dependencies and acceptance evidence. These refine the existing
programme; they do not register new capabilities or bypass later phase gates.
Start conformance work now and maintain it through Phase 8.

## 8. Cross-cutting implementation requirements

### 8.0 E7G-T extension and projection contract

Apply the kernel's smallest-use rule: existing domain mathematics and checks
remain authoritative for their domains. E7G-T structures the evidence and
boundaries; it does not replace quantum semantics or constitute a physical
theory. Informative kernel pilots remain informative unless separately admitted.

Every extension proposal must declare:

- its source object, carrier, modality, context and intended inquiry;
- which representation is a projection/view and which operation constructs or
  transforms an object; neither implies a valid inverse reconstruction;
- preserved invariants, lost information, assumptions and reconstruction limits;
- a named equivalence criterion, temporal/calibration support and resource limits;
- observations separately from assessments, interpretations and claims;
- supporting sources, validator identity, evidence outputs and maximum conclusion;
- how unknown, conflicting and unsupported evidence remains inspectable.

Keep one shared Evidence Core with separately versioned semantic profiles.
Use adapters for mature external tools. Do not equate counts, expectation values,
energies, atom outcomes, photonic measurements and logical errors without an
explicit comparison bridge. Information discarded by a projection must not be
silently reconstructed as observed fact. Reuse current fields where sufficient;
new schemas need compatibility review rather than speculative redesign.

### 8.0.1 Source adoption and reuse

For each adopted source, record its register ID, publisher, URL, access date,
pinned release/commit and content digest where obtained, document and code
licenses separately, supported requirements, fixture IDs and limitations.
Preserve license/notice obligations for vendored material. Public reading access
does not imply unrestricted redistribution or free hardware access.

Compare existing canonicalisation against RFC 8785 [05] using cross-language
vectors before claiming JCS compatibility. Do not change artifact identity rules
silently; discrepancies require an explicit versioned migration decision.

### 8.1 Determinism

- Pin every criterion and profile version.
- Sort checks and collections where ordering is not semantically material.
- Reject non-finite numeric values.
- Make generated identities reproducible under declared inputs.
- Avoid environment-dependent paths, timestamps, and provider data in golden
  fixtures unless deliberately normalised.

### 8.2 Resource safety

- Declare parser, graph, qubit, matrix, shot, recursion, and file-size limits.
- Reject or block work beyond the supported resource envelope.
- Do not allocate exponential state representations merely to inspect an
  artifact.
- Treat supplied code, archives, QASM, LLVM, and metadata as untrusted data.

### 8.3 Compatibility

- Preserve the existing E7Q CLI and rc12 tests unless an ADR approves a break.
- Use additive experimental schemas until a deliberate version transition.
- Never reinterpret an old PASS as a stronger new conformance level.
- Include migration notes for every schema or status change.

### 8.4 Evidence and reporting

Every consequential report should identify:

```text
claim
supporting evidence
source and provenance
transformation path
assumptions
preservation and loss
scope and temporal support
conflicts and unknowns
validation status
maximum admissible conclusion
next responsible move
```

### 8.5 Testing

Every work package requires:

- focused unit tests;
- at least one valid golden fixture;
- malformed and tampered fixtures;
- unsupported-capability fixtures;
- boundary/resource-limit fixtures where relevant;
- deterministic repeat-build comparison;
- complete repository regression.

The baseline command is:

```bash
python -m pytest -q
```

Record the actual test count. Do not report success from a subset as though the
complete suite passed.

## 9. Git and change discipline for AI agents

1. Start from the latest verified `main` commit.
2. Read the governing documents before editing.
3. Create one bounded branch per work package, for example
   `e7q-ir-f2-framework`.
4. Inspect the existing implementation and tests before proposing new types.
5. Keep unrelated changes out of the branch.
6. Update protocol, profile, conformance, security, and roadmap documents when
   their contracts change.
7. Run focused tests, then the complete suite.
8. Review `git diff --check`, the final diff, and generated artifacts.
9. Commit an inspectable checkpoint with limitations recorded.
10. Follow the user's current session authorisation for publishing and merging.
    Existing authorisation persists; do not request it repeatedly. An authorised
    implementation may be prepared as an isolated review branch and draft PR.
    Live provider expenditure, private-code publication and external messages
    still require applicable authorisation. This document grants none by itself.

Resolve routine implementation choices and complete reviewable work within the
authorised scope. Ask the user only when an unresolved decision exceeds that
scope, for example when:

- a change would redefine an architectural boundary;
- a new external dependency, licence, service, or credential is required;
- a result requires live provider expenditure;
- an existing public schema must break;
- a security or IP decision is material;
- a stronger scientific or commercial claim is proposed;
- test evidence conflicts with the roadmap or documentation.

## 10. Phase 1A executable assignment — completed

**Completion status:** implemented and locally verified on
`e7q-ir-f2-framework`; not pushed or merged.

Historical Phase 1A assignment (completed; do not restart):

> Work in `E7GT-Ecosystem/E7Q` from the latest `main`. Read
> `docs/e7q-ir/BUILD_PLAN.md`, `ARCHITECTURE.md`, `PROTOCOL.md`,
> `CONFORMANCE.md`, `PROFILE_AUTHORING.md`, `SECURITY_AND_TRUST.md`, and
> ADR-0001, then load E7G-T v0.11-UC5 and the E7G-T Ecosystem Operating Kernel.
> Implement **Phase 1A only: the E7Q-IR F2 semantic-validation framework**.
> Do not yet claim circuit equivalence, provider authenticity, execution, or
> physical fidelity. Add a deterministic validator interface and registry,
> per-artifact and per-relation semantic results, fail-closed status handling,
> F2 aggregation, CLI support, documentation, and valid/invalid/blocked/
> unsupported/adversarial tests. Preserve F0/F1 meanings and every existing
> E7Q behaviour. Run the focused suite and the complete suite. Commit locally
> on `e7q-ir-f2-framework`; follow the current session's publishing and merge
> authorisation and preserve any required repository checks.

### Phase 1A expected file surface

The implementing agent should first evaluate, not blindly assume, this surface:

```text
src/e7q/ir/semantic.py              new validator/result contracts
src/e7q/ir/profiles.py              validator registration metadata
src/e7q/ir/conformance.py           F2 orchestration and aggregation
src/e7q/ir/__init__.py              intentional public exports only
src/e7q/cli.py                      permit --level F2
schemas/e7q-ir/                     semantic-result/report updates as required
profiles/circuit-basic-v0alpha1.json explicit F2 validator/capability declaration
tests/test_e7q_ir.py                framework and regression coverage
docs/e7q-ir/                        protocol/conformance/profile updates
ROADMAP.md                          mark only actually completed scope
```

If inspection shows a smaller or safer surface, use it and document why.

## 11. Definition of project completion

E7Q-IR is not complete when every planned adapter exists. A credible first
public protocol release requires all of the following:

- stable Evidence Core contracts;
- independently testable F0-F2 conformance;
- at least one external workflow not using the E7Q language;
- at least one verified transformation criterion;
- OpenQASM interoperability with explicit coverage boundaries;
- QIR interoperability exercised on external artifacts;
- a reviewed security model before any F3 claim;
- explicit replication semantics before any F4 claim;
- conformance vectors usable by a third-party implementer;
- documented limitations and migration policy;
- independent exercise or reproduction;
- no unsupported quantum-advantage, hardware-fidelity, security, or standard
  status claim.

Commercialisation, hosted services, certification programmes, and an ecosystem
registry are later product decisions. They must be supported by technical and
buyer evidence rather than inferred from implementation progress.

## H1/H4 first executable increment

The [local review runner](REVIEW_RUNNER.md) and versioned manifest connect all
current repository test files to per-case outcomes and input/environment identity.
This is an internal reproduction facility and initial inventory, not completion
of H1/H4 or independent reproduction of the external report. Remaining gates
include assertion-level observations, detailed public-claim coverage and external
reproduction. Next: H2/H3 adversarial gap analysis.

## H3 bounded ingestion hardening increment

Baseline: `5bb11722f7f5fc0ef8abaa8f5c1af6963d0c815a`.
External bundle JSON now rejects duplicate keys at any nesting level, non-finite
constants and floating-point overflow. Invalid/deep JSON produces a failed JSON
check. ZIP input is capped at 128 MiB before bounded reading; digest and inspection
use the same snapshot. Noncanonical dot/empty path segments and duplicate directory
entries are rejected; existing member, expanded-size and symlink limits remain.

Regression fixtures distinguish valid manifest digests from failed JSON semantics,
and exercise input/member/total/count budgets. Valid synthetic directory and ZIP
workflows retain their prior receipt schema and bounded judgments. No member is
extracted or executed. Previously tolerated ambiguous inputs are intentionally
rejected; no schema or identity algorithm is migrated.

This is a partial H3 gate, not a complete security review. Remaining work includes
broader field-type/ordering validation, directory race/resource analysis and H2 IR
adversarial gap analysis. Existing limits do not certify provider authenticity.
