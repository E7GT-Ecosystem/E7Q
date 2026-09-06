# E7Q-IR Build Plan and AI Engineering Handoff

**Plan version:** 0.1

**Status:** authoritative implementation plan for the experimental E7Q-IR line

**Baseline:** repository `E7GT-Ecosystem/E7Q`, `main` at commit `b7dc357`

**Baseline verification:** 181 tests passing; E7Q-IR F0 and F1 implemented

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

## 4. Current verified baseline

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
  comparative-experiment components outside the new IR package.

### 4.2 Not implemented

- F2 profile-semantic conformance;
- verified transformation equivalence in the E7Q-IR graph;
- a production OpenQASM 3 bridge;
- a QIR bridge;
- authenticated provider execution evidence;
- F3 signature/identity/attestation conformance;
- F4 replication conformance;
- stable third-party profile loading and governance;
- annealing, analog, photonic, measurement-based, or full QEC profiles;
- a remote registry, server, dashboard, or hosted service.

### 4.3 Important boundary in the present demonstrator

The current workflow hashes supplied circuit files and parses supplied counts.
It does not execute the circuits, authenticate the provider, prove that the
declared transpiler produced the executable file, or verify that source and
executable circuits are semantically equivalent. The current graph therefore
must not be retrospectively labelled F2-conformant.

## 5. Repository map

| Area | Current responsibility |
| --- | --- |
| `src/e7q/ir/` | E7Q-IR Evidence Core and workflow demonstrator |
| `src/e7q/ir/conformance.py` | F0/F1 validation and conformance report |
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

## 8. Cross-cutting implementation requirements

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
- test evidence requires a material change in the agreed product direction.

## 10. Immediate executable assignment

The next AI or engineer should receive this assignment verbatim:

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
