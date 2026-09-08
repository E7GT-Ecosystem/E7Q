# Roadmap

## E7Q-IR v0.1 — Evidence-native IR foundation

The authoritative [build plan](docs/e7q-ir/BUILD_PLAN.md) v0.8 includes
[research-backed extensions](docs/e7q-ir/RESEARCH_FOUNDATIONS.md) under the
E7G-T extension/projection contract. Added packages are planned, not completed.

### Optional v0.12 family-state planning lane

- [ ] K12-A pin E7G-T v0.12/CFS1 profiles, models, limits and non-claims;
- [ ] K12-B define additive candidate-family contracts for circuits, layouts, targets and calibration contexts;
- [ ] K12-C preserve transformation, residual-family, objective order, ties and selected-mapping membership;
- [ ] K12-D run a public-safe external-compiler/topology pilot through the existing evidence workflow;
- [ ] K12-E decide from two-consumer evidence whether any shared runtime contract should be extracted.

This lane follows the applicable H2/H3 and Phase 2 gates. It does not change quantum semantics, reinterpret EEC coefficients as amplitudes/probabilities, or recreate a separate quantum Fabric.

- [x] content-addressed universal artifact envelope;
- [x] typed evidence graph and transformation contract;
- [x] bounded claim contract;
- [x] versioned profile and capability negotiation model;
- [x] F0 structural and F1 referential conformance;
- [x] external OpenQASM/counts workflow demonstrator independent of the E7Q language;
- [x] consolidate the experimental quantum Fabric namespace into E7Q-IR;
- [x] F2 semantic-validation framework, registry, status model, and CLI;
- [ ] F2 `circuit-basic` profile semantic validators;
- [x] bounded Phase 1B embedded OpenQASM 2, single-register counts, TVD,
  claim-support and assessment/support relation checks;
- [ ] OpenQASM 3 production bridge and cross-SDK round trips;
- [ ] QIR bridge;
- [ ] F3 provider authentication and signed attestations;
- [ ] F4 declared replication conformance.
- [x] bounded exact signed-permutation unitary-prefix criterion;
- [ ] [dual-relation request/report contract](docs/e7q-ir/EQUIVALENCE_DIRECTION.md)
  with exact and global-phase outcomes kept separate and the required relation
  selected by the caller;
- [ ] bounded real-H global-phase criterion with paired exact/phase fixtures
  under the existing four-qubit and 64-gate reference-oracle limits;
- [ ] optional pinned QCEC/PyZX backends and an external conformance corpus,
  preserving inconclusive, unsupported, blocked, and resource-limit outcomes
  (QCEC adapter, external pair workflow and bounded native/external unitary-prefix
  comparison implemented; PyZX and the complete corpus remain pending);
- [ ] structured equivalence benchmark ladder through 25+ qubits with published
  runtime/resource evidence and no arbitrary-circuit scalability claim
  (structured 26/32-qubit QCEC corpus and one complete 32-qubit evidence graph
  implemented; 4/8/12/16/20 rungs and repeated measurements remain pending);
- [ ] compositional compiler-transformation evidence with named rules and
  inspectable preservation/loss;
- [x] Phase 1C UTF-8 byte identity and parsed structural identity with F2 fixtures;
- [ ] typed result adapters, PROV mapping and hybrid trace capture;
- [ ] benchmark and pyGSTi characterization evidence adapters;
- [ ] separate QEC, hybrid, annealing, measurement-based, analog/pulse and
  photonic profiles, following Phase 7's dependencies and research gates;
- [ ] proof-artifact evaluation and independent extension conformance.

## Review-driven hardening — planned

See [H1–H10 acceptance gates](docs/e7q-ir/REVIEW_HARDENING.md).

- [ ] H1 reproducible external-review package (local runner implemented; original reproduction pending);
- [ ] H2 adversarial E7Q-IR semantic campaign;
- [ ] H3 external-bundle security and interpretation checks;
- [ ] H4 capability-to-evidence matrix and maintained current status;
- [x] H5 native/legacy evidence continuity adapters, including installed bounded native/default F2 reconstruction;
- [ ] H6 optional Aer reference workflow;
- [ ] H7 end-to-end supporting-module campaigns;
- [ ] H8 independent mathematical cross-checks;
- [ ] H9 bounded dynamic noisy execution contract and implementation;
- [ ] H10 resource budgets, compatibility and release gates.

## v0.1 — Minimum Executable Language

- [x] parser, state-vector simulator, verifier, CLI, and CI;
- [x] core gates, terminal measurement, invariants, OpenQASM export;
- [x] JSON Proof-of-Path and Bell-state reference test.

## v0.2 — Circuit equivalence

- [x] exact, global-phase, computational-basis measurement, and tolerance equivalence;
- [x] comparison CLI and Proof-of-Path reports;
- [x] optimisation examples and regression tests.

## v0.3 — Dynamic algorithms

- [x] partial and mid-circuit measurement;
- [x] classical-bit feed-forward;
- [x] quantum teleportation reference program;
- [x] Deutsch–Jozsa balanced-oracle reference program;
- [x] aggregate dynamic Proof-of-Path tracing;
- [x] OpenQASM 3 export for dynamic operations;
- [x] channel-level equivalence for non-unitary programs.

## v0.4 — Composition and diagnostics

- [x] reusable path composition with recursion rejection;
- [x] executable classical assertions;
- [x] first-failing-step diagnostics in verification reports;
- [x] OpenQASM 3 subset import and round-trip validation.

## v0.5 — Noise and backend bridge

- [x] density-matrix reference backend;
- [x] bit-flip, phase-flip, and depolarizing channels;
- [x] trace, purity, and channel evidence in Proof-of-Path;
- [x] backend capability profiles and an explicit simulator/hardware boundary;
- [ ] vendor IR adapters and topology-aware mapping;
- [ ] compilation traces for physical backends;
- [x] channel-level equivalence for non-unitary programs.

## v0.6 — Channel equivalence

- [x] exact and tolerance-based density-matrix channel comparison;
- [x] computational-basis measurement-behaviour comparison for channels;
- [x] superoperator Proof-of-Path evidence;
- [x] explicit rejection of incompatible or dynamic programs.

## v0.7 — Topology-aware compilation

- [x] backend-neutral linear, ring, and all-to-all coupling maps;
- [x] shortest-path routing for non-adjacent two-qubit gates;
- [x] semantics-preserving SWAP insertion with restored logical layout;
- [x] native-gate capability validation;
- [x] compilation Proof-of-Path with routing and overhead evidence;
- [x] IBM Qiskit and Google Cirq source adapters;
- [ ] credential-dependent hardware submission;
- [ ] calibrated cost models and hardware-derived fidelity estimates.

## v0.8 — Vendor SDK adapters

- [x] dependency-free IBM Qiskit Python source export;
- [x] dependency-free Google Cirq Python source export;
- [x] adapter Proof-of-Path evidence and CLI integration;
- [x] explicit rejection of unsupported dynamic and noisy programs;
- [ ] credential-dependent hardware submission;
- [ ] calibrated cost models and hardware-derived fidelity estimates.


## v0.9 — Resource estimation and target planning

- [x] deterministic logical and routed gate counts;
- [x] dependency-aware circuit depth and two-qubit depth;
- [x] routing-overhead comparison;
- [x] machine-readable planning Proof-of-Path;
- [x] explicit static-estimate boundary;
- [ ] credential-dependent hardware submission;
- [ ] calibration-derived cost and fidelity estimates.

## v0.10 — Calibration snapshots and target selection

- [x] versioned, timestamped offline calibration snapshots;
- [x] compatibility filtering and topology-aware candidate planning;
- [x] transparent success-proxy ranking with deterministic ties;
- [x] observed-versus-estimated Proof-of-Path evidence;
- [x] explicit rejection of live-data, submission, cost, and fidelity claims;
- [ ] credential-dependent hardware submission;
- [x] vendor calibration ingestion adapters.

## v0.11 — Offline calibration ingestion

- [x] IBM/Qiskit-style supplied-export normalization;
- [x] Google/Cirq-style supplied-export normalization;
- [x] schema, timestamp, error-rate, and freshness validation;
- [x] provider and source-schema provenance;
- [x] CLI integration and normalized snapshot output;
- [x] explicit offline and authenticity boundary;
- [ ] credential-dependent live vendor retrieval;
- [ ] credential-dependent hardware submission.


## v0.12 — Reproducible execution bundles

- [x] deterministic provider-neutral execution bundle schema;
- [x] selected-target and routed OpenQASM capture;
- [x] source, snapshot, and compiled-artifact hashes;
- [x] resource plan, shot count, and Proof-of-Path evidence;
- [x] explicit ready-versus-submitted state;
- [x] CLI integration and regression tests;
- [ ] credential-dependent live vendor retrieval;
- [ ] credential-dependent hardware submission.

## v0.13 — Execution-result receipts

- [x] provider-neutral supplied-result schema;
- [x] strict bundle, target, shot, and count linkage validation;
- [x] deterministic receipt with empirical probabilities and input digests;
- [x] Proof-of-Path provenance and evidence boundary;
- [x] CLI integration, documentation, and regression tests;
- [ ] credential-dependent provider authentication and hardware submission.


## v0.14 — Statistical result assessment

- [x] explicit reference-distribution schema and validation;
- [x] total-variation distance and Pearson chi-square evidence;
- [x] dependency-free asymptotic p-value calculation;
- [x] configurable distance and significance thresholds;
- [x] deterministic assessment report and Proof-of-Path boundary;
- [x] CLI integration, documentation, examples, and regression tests;
- [ ] provider-authenticated result retrieval and hardware attribution.

## v0.15 — Replication campaigns

- [x] same-bundle and same-target receipt validation;
- [x] duplicate-result rejection and pooled count evidence;
- [x] pairwise total-variation repeatability diagnostics;
- [x] chi-square homogeneity assessment and low-cell warnings;
- [x] deterministic replication Proof-of-Path and CLI integration;
- [x] explicit offline, independence, authenticity, and fidelity boundary;
- [ ] provider-authenticated campaign retrieval and run independence attestation.

## v0.16 — Campaign drift assessment

- [x] common-target and outcome-space validation;
- [x] pooled-distribution total-variation comparison;
- [x] two-sample chi-square homogeneity evidence;
- [x] configurable drift thresholds and low-cell warnings;
- [x] deterministic drift Proof-of-Path and CLI integration;
- [x] explicit chronology, causality, authenticity, stability, and fidelity boundary;
- [ ] provider-authenticated longitudinal retrieval and causal diagnostics.

## v0.17 — Longitudinal trend assessment

- [x] baseline-relative assessment across three or more supplied campaigns;
- [x] common-target and outcome-space validation;
- [x] Bonferroni control for repeated significance tests;
- [x] first-breach detection and deterministic trend Proof-of-Path;
- [x] explicit ordering, chronology, causality, authenticity, stability, and fidelity boundary;
- [ ] provider-authenticated scheduled monitoring and causal diagnostics.

## v1.0rc1 — Offline release conformance

- [x] registered stable offline artifact families;
- [x] deterministic structural conformance reports;
- [x] CLI integration and regression tests;
- [x] explicit offline completion and evidence boundary;
- [x] credential-free roadmap complete;
- [ ] optional provider integrations, maintained outside the offline core.

## v1.0rc2 — E7G-T v0.11 temporal alignment

- [x] immutable upstream pin to E7G-T v0.11-UC1;
- [x] bounded `e7q.temporal-evidence/v1` profile;
- [x] temporal carrier, order, chronology-status, projection, phase, and
  boundary-crossing records;
- [x] temporal evidence in calibration, handoff, receipt, replication, drift,
  and trend artifacts;
- [x] structural conformance checks for embedded temporal evidence;
- [x] explicit boundary against physical-time, chronology-authentication, and
  many-worlds claims.

## v1.0rc3 — E7G-T v0.11-UC2 observational-claim pilot

- [x] immutable upstream pin to E7G-T v0.11-UC2;
- [x] corrected TD0--TD7 order-role terminology in
  `e7q.temporal-evidence/v2`;
- [x] stable criterion identifiers, editions, and parameters for temporal
  phase records;
- [x] backward structural validation of `e7q.temporal-evidence/v1`;
- [x] opt-in `e7q.observational-claim-pilot/v1alpha1` records;
- [x] record/claim/interpretation separation for calibration, receipts,
  replication, drift, and trend workflows;
- [x] shared-field preservation of divergence, unknowns, and independence
  limits;
- [x] structural and reference-integrity validation for embedded pilot records;
- [ ] Pilot G comparison against ordinary review and the UC1 profile across
  four materially different domains before any normative promotion claim.

## v1.0rc4 — Parser validation hardening

- [x] reject unknown context-setting keys instead of silently applying defaults;
- [x] reject negative seeds during E7Q and OpenQASM import validation;
- [x] preserve `#` and `//` markers inside quoted context values;
- [x] add adversarial regression coverage for all reported parser findings.

## v1.0rc5 — E7G-T v0.11-UC3 temporal-orientation pilot

- [x] immutable upstream pin to E7G-T v0.11-UC3;
- [x] opt-in `e7q.temporal-orientation-pilot/v1alpha1` records;
- [x] explicit observer locality and typed directional relations;
- [x] separation of reverse representation, time-reversal symmetry, and causal reversal;
- [x] history-whole and compatible-history relevance boundaries;
- [x] artifact validation and CLI support for bundle, receipt, replication,
  drift, and trend workflows;
- [x] explicit separation from computational-basis measurement update and
  ontological collapse claims;
- [ ] Pilot H comparison across materially different settings before any
  normative promotion claim.

## v1.0rc6 — E7G-T v0.11-UC4 alignment

- [x] immutable upstream pin to E7G-T v0.11-UC4;
- [x] incorporate Candidate Law T0's extension-orientation separation without
  changing executable quantum semantics;
- [x] define legacy E7Q `topology` terminology as hardware coupling-graph
  structure rather than an implicit mathematical topological overlay;
- [x] preserve existing `--topology`, artifact fields, and routing APIs for
  backward compatibility;
- [x] add proof and regression guards against UC4 topology conflation;
- [x] leave the UC4 topological-overlay pilot uninvoked until an inquiry has a
  separately declared carrier, topology, construction, and material
  topological claim.

## v1.0rc7 — QEC syndrome-homomorphism pilot

- [x] phase-insensitive Pauli and binary symplectic representation;
- [x] fail-closed validation of commuting, independent stabilizer generators;
- [x] syndrome, stabilizer-membership, and zero-syndrome classification;
- [x] deterministic proof artifact for `sigma(EF) = sigma(E) xor sigma(F)`;
- [x] six executable three-qubit repetition-code reference circuits;
- [x] dependency-free oracle and regression coverage;
- [x] explicit restricted-X-error, hardware, decoder, threshold, and novelty boundaries;
- [ ] independent external mathematical review before any stable API claim.

## v1.0rc8 — External evidence importer

- [x] safe ZIP and directory ingestion without archive extraction or execution;
- [x] single-circuit and batched multi-circuit record discovery;
- [x] manifest, count-total, OpenQASM, mapping, operation-count, active-qubit,
  and calibration-coverage checks;
- [x] deterministic `e7q.external-evidence-receipt/v1alpha1` with complete
  received-file digests;
- [x] separate archive-safety, integrity, internal-consistency, provenance,
  reproducibility, and algorithmic-validation judgments;
- [x] synthetic public fixture, CLI integration, artifact registration, and
  adversarial regression coverage;
- [ ] provider-authenticated job retrieval or attestation;
- [ ] versioned Qiskit adapter for QPY decoding and independent depth recomputation;
- [ ] separately versioned algorithm-specific hardware assessment profiles.

## v1.0rc9 — OpenQASM 2 import and deterministic hardware assessment

- [x] bounded OpenQASM 2.0 parser for qelib1 and the supplied native ISA gate surface;
- [x] preservation of register widths, physical indices, gate parameters,
  conditions, barriers, and measurement destinations;
- [x] non-executable typed artifact for device-width circuits that cannot be
  represented safely by the small reference simulator;
- [x] explicit `clbit-ascending` and `clbit-descending` count-label semantics;
- [x] deterministic-bit assessment using a declared success threshold and
  Wilson confidence interval;
- [x] QEC hardware-reference profile with syndrome-primary and full-outcome
  evidence kept separate;
- [x] aggregate modal XOR and equal-syndrome relation checks;
- [x] explicit exploratory/prospective and provider/fidelity/fault-tolerance boundaries;
- [ ] provider-authenticated execution evidence;
- [ ] prospective replication under a profile frozen before execution.

## v1.0rc10 — E7G-T v0.11-UC5 relative-support alignment

- [x] immutable upstream pin to E7G-T v0.11-UC5;
- [x] opt-in `e7q.relative-support-pilot/v1alpha1` records;
- [x] declared support carrier, semantics, provenance, update rule,
  calibration posture, dependencies, validity window, and stop conditions;
- [x] separate admissibility, support, exclusion, phase determinacy, and
  decision-use boundaries;
- [x] structural conformance and fail-closed exclusion-basis checks;
- [ ] E7G-T Pilot J comparison across the required materially different
  domains before any normative promotion claim.

## v1.0rc11 — Comparative-experiment evidence

- [x] bounded one- or two-factor binary experiment manifest;
- [x] fail-closed metric, factor, run, resource, independence, and provenance
  validation;
- [x] deterministic cell aggregation and baseline-to-candidate effects;
- [x] metric-vector trade-offs without an undeclared aggregate verdict;
- [x] descriptive two-factor difference-of-differences interaction contrast;
- [x] explicit manifest-assessability-to-computational-advantage claim ladder;
- [x] Proof-of-Path, CLI, example, artifact registration, and regression tests;
- [ ] inferential replication profile using an independently reviewed
  statistical method;
- [ ] separate annealing-evidence adapter if real QUBO/Ising evidence becomes
  available.

## v1.0rc12 — Evidence-contract hardening

- [x] distinguish structural `MANIFEST_ASSESSABLE` from experimental
  `FEASIBILITY`;
- [x] require verified execution evidence before feasibility can be
  established;
- [x] enforce finite numeric and semantics-specific domains for relative
  support values;
- [x] align package, citation, README, and Language Specification versions;
- [x] add formal release notes and regression tests for the corrected
  contracts;
- [ ] add an evidence-linked execution verifier capable of establishing
  feasibility under a declared profile.

- [x] Bounded signed-permutation global-phase criterion (separate from exact equality; broader Phase 1C remains pending).

- [x] Bounded signed-permutation computational-basis measurement equivalence for all basis inputs, with explicit phase loss.

- [x] Exact noiseless signed-permutation unitary-channel comparison, including off-diagonal coherence; noisy channels remain pending.

- [x] Exact real H-unitary criterion and original H/u2(0,pi) F2 acceptance fixture (four-qubit, 64-gate bounds).

- [x] Phase 2 first preservation adapter: original native/legacy source recovery and explicit assurance limits. See [contract](docs/e7q-ir/LEGACY_PRESERVATION.md).
- [x] Phase 2 typed native compiler/execution/legacy adapters: preservation, native execution, criterion-bound comparison, topology compiler Proof-of-Path conversion, offline legacy receipt mapping and installed native/default F2 reconstruction are complete within their declared bounds.

- [x] Bounded native source/intent/execution/observation/assessment path with preserved Proof-of-Path and verdicts plus installed `e7q.ir.native-execution/0alpha1` F2 reconstruction; [scope and limits](docs/e7q-ir/NATIVE_EXECUTION.md).

- [x] External circuit-pair QCEC evidence workflow with byte-preserved sources, separate OpenQASM 2 projections, isolated numerical assessment, explicit tolerances/resource limits and bounded claim support. Default F2 integration, PyZX and general scalability remain pending.

- [x] Bounded criterion-selected native E7Q to external OpenQASM 2 unitary-prefix comparison with explicit terminal-measurement projection loss, preserved native Proof-of-Path and fail-closed unsupported/resource outcomes. Its optional QCEC evidence remains separate from native/default F2 truth.

- [x] Typed conversion of the existing topology-reference compiler Proof-of-Path into E7Q-IR, with explicit compilation request, verbatim and typed traces, independently identified source/compiled representations, isolated criterion-bound QCEC evidence and a bounded compiler-preservation claim. Imported compiler declarations are not native/default F2 truth.

- [x] Typed offline mapping of existing legacy execution bundles, supplied results and receipts into distinct intent, execution, observation, assessment and bounded-claim artifacts, with byte-perfect recovery and independent `build_execution_receipt()` recomputation. Imported verdicts remain excluded from native/default F2 truth; provider/authentication work remains separate.
