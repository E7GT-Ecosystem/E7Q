# E7Q-IR Build Plan and AI Engineering Handoff

**Plan version:** 0.8

**Status:** authoritative implementation plan for the experimental E7Q-IR line.

**Current inspected baseline (2026-09-08):** `main` at
`538ac31e064ebddebb43f441ef316f0551581863` (PR #60).
That merge added typed conversion of the existing topology compiler Proof-of-Path
without changing the compiler or default F2 truth.

**Current bounded Phase 2 increment:** maps supplied legacy execution-bundle,
execution-result and execution-receipt files into typed E7Q-IR. It preserves each
input byte-for-byte, records intent/event/observation separately, reruns the
existing `build_execution_receipt()` semantics, compares the complete supplied
receipt and proof, and supports only a bounded offline consistency claim. It does
not authenticate providers or execution, complete Phase 2/H5, promote default F2
truth or begin K12/CFS implementation.

**Revision 0.8:** adopts ecosystem direction `E7-ECO-DIR-2026-09-08.1` and pins E7G-T v0.12 experimental canonical revision CFS1 at commit `b7a30b2d56375a5a0646e0c1cab4f621b4de99ca`. It adds an optional, additive family-state planning lane after the applicable H2/H3 and Phase 2 gates. EEC coefficients remain formal construction coefficients, never quantum amplitudes, probabilities or evidence weights. Existing artifacts, IDs, APIs and F0-F2 meanings are not migrated.

**Revision 0.7:** adds a bounded external circuit-pair workflow that captures two
supplied files byte-for-byte, records separate bounded OpenQASM 2 projections,
evaluates immutable snapshots only through the isolated QCEC worker, and links
source, representation, assessment and claim artifacts. Callers must explicitly
select one numerical criterion, both tolerances, and time/memory limits. Claims
pass only with the selected numerical criterion; parser rejection and every
inconclusive or worker/resource outcome remain non-PASS.

**Revision 0.6:** hardens the optional QCEC increment with one spawned process
per assessment, a parent-owned wall-clock deadline, bounded terminate/kill/join
cleanup, POSIX `RLIMIT_AS` memory enforcement where successfully applied, and
explicit enforcement and worker-exit evidence. Timeout, resource exhaustion,
signal termination, nonzero exit, startup and protocol failures remain distinct
non-PASS outcomes.

**Revision 0.5:** records the first bounded E1/E3/E5 evaluation increment:
separate exact/global-phase relation results for one pair, a pinned optional
MQT QCEC 3.9.0 assessment adapter, and a seven-case 26/32-qubit structured
corpus. The adapter records raw verdicts, criterion, configuration, numerical
method, runtime, process-peak memory and resource outcomes. It is not default
F2 conformance truth, and the full E5 ladder remains incomplete.

**Revision 0.4:** adds the
[dual-relation and scalable circuit-equivalence track](EQUIVALENCE_DIRECTION.md).
It makes caller-selected exact/global-phase semantics, the bounded reference
oracle, optional structure-aware backends, compositional evidence, and a 25+
qubit structured benchmark gate explicit. These are planned work packages, not
current capability or an arbitrary-circuit scalability claim.

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

**Next package:** add native/default F2 semantic validation without promoting
legacy declarations, compiler traces or optional QCEC evidence beyond their
admitted criteria. Source preservation, bounded native execution, criterion-bound
comparisons, compiler Proof-of-Path conversion and offline legacy receipt mapping
are implemented Phase 2 increments. Extend the benchmark ladder below 25 qubits,
evaluate PyZX separately, and repeat resource measurements across the supported
corpus. Phase 2, H5, E3 and E5 remain open; optional evidence must not bypass
compatibility or conformance requirements.

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
- complete Phase 2 native/default F2 semantic validation and the proposed Aer adapter; preservation, bounded native execution, native/external QCEC comparison, typed topology-compiler Proof-of-Path conversion and offline legacy receipt mapping are implemented increments;
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

## H2 assessment type-safety increment (2026-09-07)

Baseline: `7f6fa0f4ab931f06b483afd336d5be26b06736c9`.
Adversarial rehashed graphs exposed an assessment-level false PASS: boolean
observed probabilities compared equal to numeric zero/one. Explicit finite-number
validation now rejects them and propagates failure to dependent claims. Genuine
numeric zero/one probabilities remain valid. Malformed ordering containers return
BLOCKED, and out-of-range integers return scoped FAIL rather than a framework
exception. Artifact identities, profile criteria and F0/F1 semantics are unchanged.

The initial regression cases reproduced seven failures before the fix. This is
a bounded H2 increment; it does not complete general IR adversarial coverage or
H3's remaining field-shape/directory analysis. Existing golden F2 fixtures remain
the valid-path gate. Next: remaining graph/criterion and bundle field-shape gaps.

## H3 field-type consistency increment (2026-09-07)

Baseline: `29105bd4353e8d795dec6ae2f02962742c8df437`.
Malformed metadata status containers now produce a failed type check instead of
raising TypeError. Declared shot/outcome/gate counts and register widths require
integers, excluding booleans and floating-point lookalikes. Gate-count keys that
collide under case normalization are rejected rather than overwritten. This also
covers the optional legacy IR gate-count field.

Rehashed-manifest tests preserve integrity PASS while requiring consistency FAIL;
valid synthetic ZIP/directory fixtures remain compatible. The receipt schema and
identity rules are unchanged; an additional status-type check is emitted. Missing
or non-string status is now an error; unrecognized strings retain their prior
terminal-status warning. This intentionally tightens malformed-input admission.
Remaining H3 work includes ordering semantics, directory races and resource bounds;
this increment does not establish complete schema validation or authentication.

## H3 bounded directory inspection (2026-09-07)

Baseline: `3fc7188160903c95d9802b639653733c561acdb7`.
Directory inspection now traverses incrementally with a 1,024-entry budget
(including empty directories) and maximum directory depth 32. Existing 512-file,
32 MiB per-file and 128 MiB aggregate limits remain. Reads are bounded by the
remaining byte budget plus one detection byte; actual received bytes determine
the total and digests. Special files are rejected rather than silently ignored.

The reader checks opened file identity/type, observed size and modification time;
platform-supported no-follow/nonblocking flags reduce leaf replacement risks.
These checks do not create an atomic directory snapshot or protect every ancestor
replacement race. Use an immutable trusted-local snapshot when concurrent mutation
is in the threat model; full race-resistant traversal remains pending.

Tests cover empty-directory/depth budgets, FIFO rejection where available,
file/count/aggregate limits and growth between inspection and bounded read.
Canonical member digest ordering is unchanged and valid fixtures retain their
receipt meanings. Traversal beyond the new limits intentionally fails admission.
Next: explicit ordering semantics and remaining IR coverage; no complete security
or provider-authentication claim is added.

## H3 count-order preservation and consumer check (2026-09-07)

Baseline: `fce025491e685914958520b8c88bb2510be308df`.
The external-bundle producer accepts optional `raw_counts.json.label_order` with
`clbit-ascending` or `clbit-descending`. These describe left-to-right classical
bit index order in the admitted single-register profile. Values are retained
unchanged; the receipt adds `circuits[].counts.label_order`. Missing input is
recorded as null/unknown with a warning. Explicit invalid/null input fails.
A supplied declaration is not independent authentication of its convention.

Affected consumer: deterministic-reference assessment now rejects a receipt order
that conflicts with the reference, or an invalid non-null receipt order. Old
receipts lacking the field, and new receipts marked unknown, still require the
reference's explicit convention; this is a user-supplied assumption, not an
inferred or verified fact. Matching declarations use the existing canonicalization.
Future native/IR adapters must preserve this distinction and must not promote an
unknown order into F2-validated ordering without separate support.

This additive experimental receipt field preserves source digests, raw labels,
existing required fields and legacy readability. Rehashed manifests, unsupported
orders, unknown legacy order, conflict rejection and non-palindromic downstream
fixtures cover the compatibility gate. Ten new cases failed before implementation.
Next: Phase 2 native/legacy adapter contract, with remaining H2/H3 gaps tracked;
no full hardening completion or hardware provenance claim is made.


## Phase 2 preservation checkpoint (2026-09-07)

Baseline: `5c163aa3d72d0efc2724252b19696c8080aad79f`.
The [native/legacy preservation adapter](LEGACY_PRESERVATION.md) retains original
UTF-8 source bytes and exposes supported legacy JSON in a linked representation.
Original verdicts, IDs, proof, count order and limits remain supplied data.
This increment establishes structural preservation, not semantic validation:
F2 and typed native/compiler/execution mapping remain pending. H5 and Phase 2
are still open. Focused acceptance covers recovery, malformed/bounded input,
deterministic graphs, failed verdict retention and refusal to upgrade assurance.


## Phase 2 native execution checkpoint (2026-09-07)

Baseline: `e223603a634762c429dcc962f47e33fa26fa4a95`.
The [native execution adapter](NATIVE_EXECUTION.md) now constructs source, intent,
representation, execution, observation and assessment artifacts for a bounded
static statevector program. It retains original source, complete native proof
and verifier result, including FAIL, with explicit count ordering and projection
loss. Native APIs and formats are unchanged. F0/F1 structural checks do not confer
F2 semantics. Phase 2/H5 remain open pending compilation/typed legacy mapping and
criterion-bound native/external comparison.

## Equivalence direction checkpoint (2026-09-07)

Baseline: `ea0eeec3e379888bb383ebd4afd72887f5efbcf6`.
The [equivalence direction](EQUIVALENCE_DIRECTION.md) sharpens R1 in response to
external technical questions about relation choice and scale. The discussion is
design input, not acceptance evidence.

Planned dependency order:

1. **E1 — dual-relation contract:** the caller declares exact or global-phase
   equivalence as the required relation; reports retain separate criterion
   outcomes and every non-PASS state.
2. **E2 — bounded phase oracle:** add global-phase checking to the existing
   real-H/u2 exact-arithmetic domain without increasing its four-qubit/64-gate
   bounds.
3. **E3 — structure-aware adapters:** evaluate optional pinned MQT QCEC and PyZX
   adapters with raw verdicts, phase/permutation conventions, time/memory limits,
   and fail-closed inconclusive mappings.
4. **E4 — compositional evidence:** retain compiler steps and optional
   certificates; whole-circuit support requires an applicable named composition
   rule.
5. **E5 — benchmark ladder:** publish reproducible 4, 8, 12, 16, 20 and 25+
   qubit structured cases, including negative, unsupported and exhausted cases.
   The 25+ rung is an evidence gate, not a general tractability promise.

E1/E2 may proceed as bounded subpackages while Phase 2 reaches
criterion-bound native/external comparison. E3 introduces no mandatory Evidence
Core dependency. E4/E5 cannot upgrade a claim beyond their named criteria,
corpus, versions and observed resource envelope. Existing criterion identifiers,
F0/F1 meanings, reports and native APIs remain compatible; no earlier PASS is
reinterpreted.

### Bounded QCEC evaluation increment (2026-09-07)

Baseline: `4210bd595566af0f6458cac2c4870a6d98a3410e`.
The optional adapter pins `mqt.qcec==3.9.0` (MIT) and uses separate,
tolerance-bearing criteria: `e7q.ir.qcec-numerical-unitary` and
`e7q.ir.qcec-numerical-global-phase`, both version 1. It rejects the
exact-algebraic signed-permutation criteria rather than satisfying them with a
numerical result. Assessment artifacts retain backend/dependency versions,
configuration, numerical tolerances, raw
verdict/checker data, assumptions, runtime, process-peak RSS, declared memory
limit and outcome. The method is explicitly tolerance-based numerical, never
reported as exact algebraic verification.

The original report `sha256:a19e91087e60359a57257e20ba0b171c70d74a40126a58bbb78eb9dd5218fece`
used exact-algebraic criterion identifiers for numerical results. It is invalid
as evidence for those exact-algebraic claims, but its complete history is retained
at `benchmarks/e7q-ir/history/qcec-3.9.0-results-a19e9108-invalid-exact-criteria.json`.

The process-isolated rerun corpus at
`benchmarks/e7q-ir/qcec-3.9.0-results.json` has report ID
`sha256:36b852c1e7cc9dc2479b63c9174e4add963d2731a4844b0d4fe5b3c3db154516`
and contains seven 26/32-qubit cases and 14 criterion runs: six PASS, six FAIL
and two BLOCKED. It covers exact-equivalent SWAP rewrites, global-phase-only
Pauli pairs, intentional gate errors and a forced timeout. Each assessment uses
one spawned worker. The parent owns the monotonic wall-clock deadline and records
terminate/kill cleanup, exit code or signal, and successful reaping. Both forced
controls remain `BLOCKED/INCONCLUSIVE` with reason `wall_clock_timeout`.
Probabilistic, per-state-phase, unknown and no-information verdicts remain
non-PASS inconclusive outcomes.

Worker-local peak RSS replaces the earlier whole-adapter-process metric. A
requested memory limit is enforced with POSIX `RLIMIT_AS` when that mechanism is
available and successfully applied; the report records the requested/effective
limit, mechanism and actual enforcement state. Explicit `MemoryError` is
`resource_exhaustion`; native signals and nonzero exits remain distinct worker
failures rather than guessed out-of-memory events. Regression coverage also
keeps startup and malformed/missing worker responses non-PASS.

This is evidence for supported structured instances above 25 qubits, not general
25-qubit tractability. E3 remains open pending broader backend/domain isolation
and PyZX evaluation. E5 remains open pending the 4/8/12/16/20 rungs, unsupported
and dynamic/noisy fixtures, repeated resource measurements and reproducibility
review. Phase 2/H5 remain open pending Proof-of-Path conversion, typed legacy
receipt mapping and criterion-bound native/external workflow comparison.

Public progress for this track must identify the accountable project
contributor, disclose current limits, and cite exact commits, tests, skipped or
unsupported cases, and the next acceptance gate. AI-assisted drafting and public
discussion are not implementation or validation evidence.

### External circuit-pair evidence workflow checkpoint (2026-09-08)

Baseline: `6454a26326ecfa1a654548e131910be2a1ef5be2`.
The additive `e7q.ir.external-qcec-workflow/v1` API and CLI accept two supplied
circuit files, stable caller references, one explicit QCEC numerical criterion,
numerical/fidelity tolerances, and wall-clock/memory limits. Each input is read
once within the existing 256 KiB circuit budget, retained losslessly as base64
with byte length and SHA-256 identity, and separately projected through the
bounded non-executing OpenQASM 2 importer. QCEC receives only temporary files
created from those captured bytes, and runs only through PR #54's spawned worker.

The resulting F1-valid graph links two source artifacts to two parsed
representations, one QCEC assessment and one bounded claim. The assessment
retains backend/dependency versions, complete configuration, raw verdict,
normalized status/conclusion/reason, checker output, runtime, worker lifecycle,
limit-enforcement metadata, assumptions and limitations. Unsupported syntax is
preserved in an `UNSUPPORTED/INCONCLUSIVE` graph without starting QCEC. Timeout,
resource exhaustion, worker failure, probabilistic/no-information/unknown
verdicts and numerical non-equivalence remain distinct non-PASS outcomes. A
claim is supported only when the requested criterion itself reports PASS;
unitary requests never inherit global-phase acceptance.

The measured 32-qubit disjoint-SWAP fixture is preserved at
`benchmarks/e7q-ir/external-qcec-32-results.json`, graph ID
`sha256:cac37f3d4d78b8ae0a9dc4bb084f9eac786a23680efe7e6b9447ea4deae187c4`.
MQT QCEC 3.9.0 returned deterministic `equivalent`/PASS in 0.38135 seconds of
parent-observed wall time, with 40,460,288 bytes worker peak RSS and an enforced
68,719,476,736-byte POSIX `RLIMIT_AS` bound. This one structured case is not
evidence of general tractability above 25 qubits.

This checkpoint does not complete Phase 2/H5 native comparison, default F2
integration, PyZX evaluation, the full E5 ladder, OpenQASM 3, QIR, provider
authentication, hardware fidelity or arbitrary-circuit scalability. Historical
QCEC evidence remains unchanged. The next gate is criterion-bound native/external
comparison plus the missing benchmark rungs and independent backend evaluation.

### Native E7Q to external OpenQASM 2 comparison checkpoint (2026-09-08)

Baseline: `95f8c8d15cc311753fe746b1c641a07e2453bea4`.
The additive `e7q.ir.native-external-qcec-workflow/v1` API and CLI accept one
native `.e7q` snapshot and one external OpenQASM 2 snapshot with stable source
references, one explicitly selected numerical criterion, numerical/fidelity
tolerances, and wall-clock/memory limits. Both sources are retained byte-for-byte
with SHA-256 identities and parsed independently.

The first common subset is deliberately bounded to eight qubits and 256 unitary
gates: one equally wide quantum/classical register on each side, the static
noiseless `x`, `y`, `z`, `h`, `s`, `t`, `cx`, `cz` and `swap` gate set, no
conditions/assertions/noise/barriers/ancillas, and terminal identity measurement
mapping. Width or mapping differences and unsupported constructs stop before
QCEC. The two evaluation representations are reconstructed from parsed operations,
not by deleting source text. Separate transformation artifacts and relations
record preserved width/gate order/operands, removal of terminal measurement and
classical state from the evaluation projection, loss of measurement outcomes and
formatting, and the unitary-prefix-only criterion boundary.

Only immutable OpenQASM 2 unitary-prefix projections reach PR #54's isolated QCEC
worker. The assessment retains backend/dependency versions, raw verdict,
normalized outcome, exact configuration, recorded tolerances, runtime, memory
and wall-limit enforcement, worker exit/signal and reaping evidence. The bounded
claim passes only when the requested numerical criterion passes. Numerical results
cannot satisfy exact-algebraic criteria; global-phase-only equality fails
`e7q.ir.qcec-numerical-unitary` and passes
`e7q.ir.qcec-numerical-global-phase`. Unsupported, blocked, timeout, exhaustion,
worker failure, probabilistic, unknown and no-information outcomes remain non-PASS.
No compiler origin is inferred from the supplied external file.

The public-safe Bell graph at
`benchmarks/e7q-ir/native-external-qcec-bell-results.json` has graph ID
`sha256:765272d4001adcca95743714f158ad44c62e4944a2705ca99667c2ac903433f1`.
MQT QCEC 3.9.0 returned deterministic `equivalent`/PASS in 0.43561 seconds of
parent-observed wall time, with 60,375,040 bytes peak worker RSS, an enforced
68,719,476,736-byte POSIX `RLIMIT_AS` limit and a reaped zero-exit worker. F0 and
F1 pass. All 19 applicable installed F2 checks ran; overall F2 remains `BLOCKED`
because no semantic validator exists for these adapter profiles, while the
unitary-prefix projection relations remain explicitly `not-assessed`.

This increment partially advances Phase 2/H5 but does not complete either. Native
preservation, bounded native execution, external QCEC, criterion-bound comparison,
topology compiler conversion and offline legacy receipt mapping are implemented
increments; native/default F2 semantic validation and independent external review
remain pending. E3, E5 and K12/CFS implementation remain open.

### Typed topology compiler Proof-of-Path checkpoint (2026-09-08)

Baseline: `89531ebe1b01d8268d8756227ddaa77ce7096ee5`.
The additive `e7q.ir.topology-compiler-proof-workflow/v1` API and CLI adapt the
existing deterministic `e7q.language.compile_topology()` and
`compilation_result()` behavior; no second compiler is introduced. One preserved
native source is parsed, admitted to the PR #57 static noiseless unitary-prefix
subset, compiled under caller-declared coupling edges and native gates, and
compared with the compiled result through PR #54's isolated QCEC worker.

The E7Q-IR path records source bytes and digest, parsed native representation,
explicit compilation request/context, typed transformation trace, independently
identified compiled representation, criterion-bound assessment and bounded claim.
The request includes coupling edges, logical width, native gate set, compiler
implementation/version, selected program/path, selected numerical criterion,
tolerances and resource limits. The transformation preserves the complete original
compiler Proof-of-Path verbatim and adds ordered typed evidence for the initial
context, each source two-qubit operation, deterministic physical path, forward and
reverse SWAP operations, routed physical operands, per-route restored-layout
assertion, final counts and routing overhead.

The compiler declaration is explicitly non-semantic. Claim support requires
successful compilation, deterministic recompilation matching the trace and compiled
representation, restored layout/register compatibility and PASS from the requested
QCEC numerical criterion. Exact-algebraic criteria are rejected. Malformed or
duplicate edges, disconnected topology, missing SWAP/native gate support, trace or
compiled-representation tampering, QCEC inequality, timeout, exhaustion, worker
crash and every inconclusive verdict remain non-PASS with distinct statuses.

The public synthetic non-adjacent-CX example is under
`examples/e7q-ir/compiler-proof/`; its evidence graph at
`benchmarks/e7q-ir/compiler-proof-nonlocal-cx-results.json` has graph ID
`sha256:17265fa58a1a46f47db36ba800ca5613e374fd3dd6a687c1dde832c5c74a5827`.
The linear `0-1-2-3` route inserts four SWAP operations around `CX q[0],q[3]`,
restores logical layout and increases the complete operation count from three to
seven. MQT QCEC 3.9.0 returned deterministic `equivalent`/PASS in 0.38756 seconds
of parent-observed wall time, with 59,174,912 bytes peak worker RSS, an enforced
68,719,476,736-byte POSIX `RLIMIT_AS` limit and a reaped zero-exit worker.
F0/F1 pass. All 19 applicable installed F2 checks run, while overall F2 remains
`BLOCKED` because no compiler-proof semantic validator is installed; the local
trace-consistency validator is not promoted to default F2 truth.

This checkpoint advances Phase 2/H5 without completing either. Offline legacy
execution/receipt mapping is now implemented; native/default F2 semantic validation,
independent external review, PyZX and the repeated benchmark ladder remain pending.
It makes no hardware feasibility, topology quality, physical fidelity, provider
authentication, execution-success, exact-algebraic or arbitrary-scalability claim.
K12/CFS implementation remains unstarted.

### Typed legacy execution receipt checkpoint (2026-09-08)

Baseline: `538ac31e064ebddebb43f441ef316f0551581863` (PR #60).
The additive `e7q.ir.legacy-execution-receipt-workflow/v1` API and CLI reuse
`src/e7q/results.py`, `src/e7q/artifacts.py` and `src/e7q/ir/legacy.py`. Existing
bundle, result and receipt schemas and `build_execution_receipt()` semantics are
unchanged; no second receipt engine is introduced.

The workflow preserves the bundle, result and receipt independently as exact bytes
with SHA-256 identity, length, schema and stable source reference. Typed
representations retain the complete original object, proof, status, unknown fields
and limitations. Separate intent, supplied execution, count observation,
receipt-consistency assessment and bounded claim artifacts keep interpretation
boundaries explicit. Four transformation artifacts record deterministic identities,
input/output references, criteria, preservation, loss, assumptions and validation
status.

Independent validation strictly reparses the preserved inputs and calls the existing
legacy receipt builder over the exact bundle/result bytes. The supplied receipt PASS,
digests, probabilities and Proof-of-Path are compared field by field rather than
trusted. Count-label order is explicit workflow context. Malformed or duplicate JSON,
non-finite values, missing/unknown schemas, unsupported count semantics, invalid
outcomes, target/shot/digest mismatch, altered probabilities/proof, forged PASS,
rehashed tampering and all imported non-PASS statuses remain non-PASS.

The public deterministic fixture under `examples/e7q-ir/legacy-receipt/` produces
`benchmarks/e7q-ir/legacy-receipt-results.json`, graph ID
`sha256:2461fac5f5a9c5472280b9ae1daf2789167851d91f3a40df8ec388c22f3fff29`.
It records the offline target, eight shots, unauthenticated synthetic provider/job
and completion declarations, `clbit-descending` counts `00=4`, `01=0`, `11=4`,
width two, deterministic outcome order, empirical probabilities and both optional
pilot records. All 36 workflow checks pass. F0/F1 pass; 25 installed semantic checks
run while F2 remains `BLOCKED` because no legacy-receipt validator is registered as
default semantic truth.

The bounded PASS establishes only internal consistency of the supplied bundle/result
and agreement with independently recomputed legacy receipt semantics. It does not
establish submission, execution authenticity, provider identity, chronology,
physical fidelity, circuit correctness, computational advantage, F3 authentication
or arbitrary scalability. Phase 2/H5 remain open for native/default F2 semantic
validation. Provider integration, authenticated execution and K12/CFS implementation
remain unstarted.


## 12. E7G-T v0.12 optional family-state planning lane

**Disposition:** EEC-Q/0.1, SF/0.1 and CFS/0.1 are `experimental` for E7Q-IR planning. E7Q verification uses only the resulting explicit records and does not adopt EEC-Q as quantum state semantics.

**Dependency rule:** this lane does not displace current H2/H3 hardening, criterion-bound Phase 2 native/external comparison, the missing benchmark rungs or independent backend evaluation. Begin it only as an additive package whose inputs and outputs preserve all current Evidence Core identities.

| Package | Deliverable | Acceptance gate |
|---|---|---|
| K12-A — source and profile pin | Record exact kernel commit, EEC/SF/CFS model editions, limits and non-claims in schemas and receipts | Unknown or mismatched editions fail closed; legacy artifacts remain byte- and meaning-compatible |
| K12-B — candidate-family contract | Typed configurations for source circuit, candidate representation, layout, target snapshot, calibration reference and constraints | Canonical round trip plus invalid-domain, empty, ambiguous and resource-limit fixtures |
| K12-C — transformation and realisation trace | Additive records for lowering/routing/scheduling steps, residual candidates, ordered objectives and selected mapping | Every step names preservation/loss; a selected state is proven to belong to the residual family; ties remain explicit |
| K12-D — external compiler/topology pilot | Public-safe supplied circuit pair or compiler output linked through planning and the existing evidence workflow | Pre-registered comparison separates topology, depth, gate count, calibration timing and selection effects; positive, negative and null results retained |
| K12-E — reuse decision | Compare the local adapter with an ordinary candidate table and with any second ecosystem consumer | Extract shared runtime contracts only if two consumers pass the same compatibility vectors without semantic distortion |

The initial objective order is proposed, not universal: admission and declared semantic preservation precede topology/signal proxies, routing cost and depth. Each pilot must publish the actual order, tie policy and unsupported cases.

### Protected boundaries

- CFS is a planning representation, not a physical superposition or measurement model.
- Realisation is a declared optimisation/selection result, not wave-function collapse.
- EEC rational coefficients are neither amplitudes nor probabilities.
- Calibration and backend descriptions are time-bounded supplied evidence unless separately authenticated.
- A better observed signal on selected hardware does not establish that topology is generally more important than gates or depth.
- No private collaborator identity, unpublished implementation or confidential artifact enters the public repository.

### AI handoff

At the start of any K12 package, report the exact E7Q main baseline, active branch, kernel pin, profile disposition, files/interfaces, preservation/loss, migration effect, focused tests and next gate. If current hardening changes the required interface, reconcile it rather than creating a parallel planner.
