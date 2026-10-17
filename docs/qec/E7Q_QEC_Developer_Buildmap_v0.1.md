# E7Q-QEC — Developer Buildmap and AI Engineering Handoff

**Edition:** 0.1 / 18 October 2026  
**Status:** proposed implementation programme; **not** evidence of completed QEC capability  
**Product:** E7Q-QEC — Evidence-Native Quantum Error-Correction Verification  
**Owner / principal architect:** Oleksandr Razinkov  
**Delivery model:** architecture-led, AI-assisted coding, independent numerical and scientific review  
**Repository:** https://github.com/E7GT-Ecosystem/E7Q  
**Upstream:** E7G-T v0.15-experimental-MSC1 (2026-09-25), separately versioned  
**Primary outcome:** reproducible, externally assessable QEC execution/verification workflow and evidence pack; NOT a claim of novel QEC algorithm, fault-tolerance threshold or physical advantage.

> **Developer directive:** Treat this file as a dependency-ordered development contract. Before coding, confirm actual repository status and existing open work; create issues and ADRs instead of assuming proposed features already exist. Keep the E7Q stable core backward compatible. Do not silently migrate upstream kernel profiles or blend evidential assessment with quantum truth.

## 0. Executive decision / scope

**Track A (build first):** an opt-in QEC domain profile for E7Q-IR, a reference experiment runner/adapters, syndrome-to-decoder evaluation, and deterministic Proof-of-Path evidence. The principal customer question: *For this code, circuit, error model, decoder and run, what was checked, what was observed, what was lost in projections, and what conclusions are admissible?*

**Track B (research only until admitted by independent results):** E7G-T-inspired representations, invariants, geometry-first candidate constructions, alternative decoders or codes. Register as hypotheses, not features; do not claim novelty without literature examination and review.

**Initial non-goals:** novel physical theory; replacement of Stim/PyMatching/Deltakit/Qiskit; hardware pulse control; FPGA/real-time decoding; verified threshold; universal fault tolerance; automatically extending REC verdicts to physical correctness; invention of a new QEC code by renaming standard stabilizer mathematics.

### Source-of-truth inventory (verified 18 October 2026)

| Source | Verified baseline | Developer implication |
|---|---|---|
| E7Q `README.md` | E7Q-IR evidence-native architecture; optional Stim 1.16.0 stabilizer backend; resource-aware native simulation; `qec-homomorphism` pilot; external receipts, deterministic assessment | Extend these mechanisms, avoid parallel evidence stores or competing IRs. |
| `docs/QEC_SYNDROME_PILOT.md` | `e7q.qec-syndrome-pilot/v1alpha1`, three-qubit repetition example, restricted X error model, independent checker, six cases; Pauli phase suppressed | Preserve existing commands and oracle; promote nothing beyond demonstrated algebra. |
| `docs/e7q-ir/ARCHITECTURE.md` | Versioned artifact kinds and F0/F1/F2 conformance model; separate claim boundaries; QEC domain profile planned | QEC-IR must be a semantic profile/additive extension, **not** a new independent E7Q Fabric. |
| `ROADMAP.md` | Dedicated Clifford QEC execution/evidence demonstrator explicitly **unimplemented** as of repository text; generic QEC profile planned | Start with gap analysis and deliver that demonstrator first. |
| `docs/E7GT_Quantum_Mapping.md` | Mapping is an engineering correspondence, not physical identity; graph `topology` is only coupling graph | Use mapping only within declared scope. |
| Local E7G-T v0.15 canonical reference | EEC-Q, RGP, WPC, REC, MSC have different experimental and conditional profiles | Pin upstream by source hash and named profile; no automatic cross-domain conformance. |

**Version/pinning caution:** E7Q README still states an E7G-T v0.11-UC5 pin for E7Q rc12; v0.15 is an available upstream experimental canonical reference, **not an automatically adopted dependency**. QEC work must run an explicit versioned adaptation/compatibility review before using REC/WPC/MSC obligations.

## 1. Architectural invariants and governance rules

1. Preserve existing CLI commands, JSON schemas and baseline test behaviour unless a versioned change and migration are approved.
2. One evidence core: use E7Q-IR artifact envelopes and typed relations. QEC objects are domain artifacts/profiles, not a second provenance graph.
3. Separate **mathematical oracle**, **simulation**, **supplied hardware result**, **statistical assessment**, **semantic conformance** and **research interpretation**.
4. Standard stabilizer mathematics and decoder algorithms remain the physical/mathematical reference, not E7G-T-specific invented arithmetic.
5. Declare code family, qubit count, distance (only if derived/verified), stabilizer generator order, logical operators, error channel, measurement conventions, circuit schedule, decoder, seed and shots.
6. Zero syndrome is not no error: logical errors and stabilizers can share it. Treat degeneracy explicitly.
7. A `PASS` of a structural or algebraic checker must not be relabelled `CORRECTION_SUCCESS`, `FAULT_TOLERANCE`, `HARDWARE_FIDELITY` or `THRESHOLD_ESTABLISHED`.
8. Every adapter specifies its supported gate set, bit ordering, round semantics and fidelity boundary. Unsupported cases fail closed as `NOT_ASSESSED`, `UNSUPPORTED`, `BLOCKED` or `RESOURCE_LIMIT`, never silently `PASS`.
9. Limit memory, runtime and shot allocation; benchmark with explicit hardware/software environment and preserved failure outcomes.
10. Always reproduce baselines without E7-specific extensions before claiming their added value.
11. Keep owner-assigned background IP and existing licences visible; do not copy third-party reference code into incompatible licensing scope.
12. Human scientific review is required before public research conclusions, regardless of number of AI-generated tests.

### FPF work discipline (internal; not necessarily public product branding)

Use the attached **First Principles Framework** as work-control vocabulary, especially A.1.1/A.2.6 (bounded context/scope), A.7 (strict distinction), A.10/B.3 (evidence and assurance), A.9 (cross-scale consistency) and E.17/F.9 (traceability/bridges). Maintain artifacts: **Claim register**, **assumption register**, **risk register**, **evidence ledger**, **decision/ADR log**, **release gate report**, and **falsification queue**. A domain/physics claim must have a target, conditions, reference oracle, evidence, limitations and reviewer. Claims without required evidence remain *unassessed*, not provisionally proven.

## 2. Mathematical substrate — required before feature work

Use conventional qubit stabilizer formalism with phase-aware Pauli multiplication where needed. For an `n`-qubit Pauli, binary symplectic encoding `(x|z) in F_2^(2n)` with product parity 

`<a,b>_s = x_a · z_b + z_a · x_b (mod 2)`.

An ordered independent commuting stabilizer generating set `S_1…S_r` defines syndrome `sigma(E)_i = <E,S_i>_s`. For phase-quotiented operators, `sigma(EF)=sigma(E) xor sigma(F)`. This alone does not distinguish stabilizer vs nontrivial logical operator. Provide a phase-aware implementation or explicit restrictions whenever signs, `-I`, phases or measured outcomes matter.

**Definition contract:** record `S`, centralizer `N(S)`, logical class `N(S)/S`, and any code-space distance claim only after verifying assumptions. The existing three-qubit bit-flip repetition example corrects **restricted X-type errors**, not arbitrary single-qubit Pauli noise. Do not label it a general `[[3,1,3]]` quantum code correcting arbitrary errors.

**Minimum independent reference set:** linear algebra/symplectic checker not importing E7Q QEC code; Stim (pinned supported release), PyMatching (pinned suitable release), NumPy/SciPy small-model oracle, and where useful Qiskit or Cirq. Record exact tested versions rather than assume compatibility. Deltakit interoperability is a *later candidate* and needs an explicit interface assessment and licence review.

**Metrics:** logical error probability with binomial uncertainty interval; syndrome detection consistency; decoder failure rate/latency measured separately; throughput; memory; evidence-artifact size; replay completeness; unsupported-case rate. Do **not** combine these into an arbitrary scalar or use sample sizes so small that apparent improvements lack precision. Compare equivalent problem definitions, noise models and compute budgets.

## 3. Canonical QEC domain object model

Implement a distinct, **versioned** `e7q.qec-profile/v0alpha1` under E7Q-IR; do not imply that generic F2 already validates QEC semantics.

| Object | Minimum fields | Required checks |
|---|---|---|
| `QECCodeSpec` | name, family, `n`, `k`, `r`, ordered generators, logical X/Z, convention, source | dimensions, commutation, independence, forbidden `-I`, representative logical relationships |
| `QECCircuitSpec` | logical intent, physical qubits/ancillas, preparation, syndrome extraction rounds, reset/measurement, classical mapping | gate support, register width, round consistency, non-destructive assumptions if claimed |
| `QECNoiseSpec` | channel, scope, parameterisation, timing, correlation assumption, provenance | proper parameter domains; no covert equivalence of phenomenological/circuit-level noise |
| `QECDecoderSpec` | implementation/version, inputs, syndrome/detection-event conventions, outputs, configuration | declared compatibility and reproducibility |
| `QECExperimentSpec` | predeclared hypotheses, comparator, design, seeds, shots, environment, resource cap | immutable registration snapshot; no post-hoc prospective claims |
| `QECObservation` | raw/aggregate measurement data, detection events, supplied/simulated flag, bit order, timing | consistency and count reconciliation; provenance claims not invented |
| `QECAssessment` | checks, failures, estimates, intervals, baseline comparisons, limits | scope/claim-ladder guards; insufficient evidence -> unassessed |
| `QECClaim` | proposition, scope, evaluation rule, support/refutation links, prohibited inferences | deny escalation from structural to physical claims |

Relations: `implements`, `generated_from`, `uses_noise_model`, `decoded_by`, `observed_in`, `assessed_against`, `supports`, `refutes`, `transformed_from`, `loss_declared`, `supersedes`, with schema-level type guards. Prefer reuse of existing E7Q-IR relation kinds; add new kinds only with rationale and migration tests.

### Claim ladder

`STRUCTURALLY_VALID` -> `ALGEBRA_CHECK_PASSED` -> `SIMULATION_REPRODUCED` -> `DECODER_BASELINE_AGREEMENT` -> `EMPIRICAL_COMPARISON_SUPPORTED` -> `EXTERNAL_REVIEWED` -> `HARDWARE_EVIDENCE_SUPPORTED` (requires authenticated/properly qualified external evidence) -> `FAULT_TOLERANCE_OR_THRESHOLD_SUPPORTED` (new rigorous experimental/theoretical gate). Higher levels are never inferred from lower ones. Some categories are orthogonal: external review is a process property; hardware evidence is a provenance/measurement property. Implement this as **typed independent statuses**, not a single increasing numeric score.

## 4. Dependency-ordered work packages

### WP0 — Repository reconnaissance, baseline freeze and ADR (mandatory)

**Tasks:** inspect latest default branch, issues, PRs, tags and CI; run fresh clean-room tests; inventory QEC pilot, Stim backend, IR schemas, CLI entry points, test fixtures and licensing; check Python dependencies; identify existing work that supersedes this map; log deviations. Pin commit SHA and current E7Q/E7G-T hashes. Generate `docs/qec/BASELINE_INVENTORY.md`, `docs/qec/ADR-0001-SCOPE.md`, `docs/qec/CLAIM_REGISTER.md`.

**Exit gate G0:** no regressions; reproducible existing `qec-homomorphism` example and independent checker; all proposed capabilities explicitly labelled new or already present; owner accepts scope. **Do not code until passed.**

### WP1 — QEC algebra foundation and negative cases

**Tasks:** factor existing syndrome utility for reuse without breaking CLI; build robust symplectic/rank/commutation/centralizer/logical-equivalence tests; phase-aware safeguards where needed; generator reorder/reference permutations; malformed or dependent stabilizers; zero-syndrome stabilizer vs logical cases; properties over small `n` with seeded randomized testing and independent reference implementation.

**Deliverables:** `docs/qec/MATH_CONTRACT.md`, checker/test corpus, oracle comparison report and minimal versioned schema.

**Gate G1:** independent reference agreement for all fixtures; counterexamples fail as expected; no unjustified classification of zero syndrome as no error; repeated existing pilot remains unchanged.

### WP2 — Focused Clifford QEC execution/evidence demonstrator (FIRST RELEASE TARGET)

**Tasks:** implement bounded 3-qubit repetition-code encode -> inject restricted X faults -> extract ancilla syndrome -> classically choose recovery -> assess logical outcome. Use optional Stim stabilizer backend if appropriate; include explicit round/measurement/bit-order handling; provide one fault-free and multiple faulted cases; compare a separate reference runner. E7Q-IR must link circuit intent, input fault, transformation, measurement, decoder/recovery step, output and bounded claim. Limit width, shots and allocation. No hard-coded expected PASS unrelated to run result.

**Suggested commands (interface proposal; names subject to ADR):**

```bash
# Provisional CLI; developer must implement and document before advertising it.
e7q qec validate examples/qec/repetition3/spec.json -o artifacts/qec-validate.json
e7q qec run examples/qec/repetition3/experiment.json --backend stim --seed 17 -o artifacts/qec-run.json
e7q qec assess artifacts/qec-run.json -o artifacts/qec-assessment.json
```

**Gate G2:** deterministic fixture replay; independent oracle agreement; proven restricted-model scope in output; all evidence links resolve; corrupt input or unknown gate fails closed; no simulated data presented as hardware evidence. Required negative fixture: `XXX` logical operation with zero syndrome is *not* reported as harmless identity.

### WP3 — QEC-IR schema, semantic adapter and evidence pack

**Tasks:** integrate object model in E7Q-IR without replacing evidence core; version F0/F1/F2 QEC checks; add `NOT_ASSESSED` for unimplemented F2 rules; design canonical JSON and data provenance; integrity/cross-file checks; digest and environment manifest; compatibility/migration tests. Source links to existing receipts; no invented F3 provider authenticity. Implement deterministic report rendering and inspect command.

**Gate G3:** schema round-trip and backward compatibility pass; malicious/corrupt/mismatched/partial artifact test suite; byte-identical deterministic artifacts under fixed inputs and toolchain; clear distinction of structural vs semantic verdicts.

### WP4 — Decoder evaluation and logical-error experiments

**Tasks:** implement reference adapters to existing decoders (begin with simple repetition-code majority vote; then PyMatching as justified); capture matching graph/weights/version/config; execute seeded Monte Carlo over explicitly declared code/noise regimes; confidence intervals and raw counts; bounded performance metrics. Introduce rotated surface-code *only after* specifying circuit-level vs phenomenological noise, detection events, boundaries and reference fixtures. Run independently built baseline without E7Q layer first.

**Gate G4:** reproducible logical-error estimates consistent with independently reproduced reference within predeclared statistical tolerance; paired baseline data; no cherry-picked seeds or unexplained exclusions; no threshold claim.

### WP5 — Comparative assurance and E7G-T alignment (opt-in)

**Tasks:** compare existing tooling-alone path to identical experiments with E7Q evidence layer. Define *measurable* additions: provenance completeness, ability to replay claims, detection of deliberate metadata tampering, transparency of transformation loss, failure on unsupported scope, review time if measured with human reviewers. Publish overhead for run time, memory and artifact size. Apply E7G-T v0.15 **selectively**:

| Profile | Permitted use | Required guard |
|---|---|---|
| D0–D7 / transformations & views | circuit/decoder histories, observations, projected syndrome/counts | mapping is interpretation, not new QEC physics |
| REC/0.1 | claims with support/refutation, rules, scopes and replayable witnesses | REC does not certify physical correctness or source truth |
| MSC/0.1 | compare evidence/coherence between declared runs/scopes | model-relative compatibility, not cross-backend identity |
| WPC/0.2 | optional decomposition/constitution of code, circuit and experiment | must distinguish component relationship from quantum entanglement |
| RGP / EEC-Q | optional modelling/constructive candidate tools | EEC coefficients are not amplitudes, probabilities or evidence weights |

**Prerequisite:** ADR with exact source pin, profile selection, migration and admission tests. Never retrofit every E7Q component automatically because v0.15 exists.

**Gate G5:** measurable evidence-layer effect and overhead disclosed; mapping test vectors; no category mistakes; baseline remains executable without E7G-T optional profiles.

### WP6 — Independent evaluation package and external scientific review

**Tasks:** construct one-command reproduction (container or locked environment), raw and derived artifacts, environment SBOM/versions, fixtures, seeds, expected failure cases and exact commands. Recruit QEC domain reviewer unaffiliated with the implementation; capture written feedback, rejected claims and corrective changes. Offer a bounded partner pilot to universities or industry; do not imply endorsement before written permission.

**Gate G6:** reviewer reproduces the core results on an independent machine, reviews mathematical assumptions and signs a limited-scope assessment; all unresolved findings listed. Release candidate may ship without external sign-off but must be marked `EXTERNAL_REVIEW_PENDING`.

### WP7 — Research Track B: E7G-T-inspired candidates (separate proposal, NO automatic product admission)

**Tasks:** preregister one falsifiable research question at a time, e.g. whether an E7G-T relational representation can (i) identify inconsistent QEC specification constraints, (ii) reduce review effort, or (iii) yield a measurable decoder search-space improvement. Survey baseline literature and established tools first. Formalise external QEC meaning; build adversarial cases. Run matched compute budgets across publicly reproducible baselines. For claims of a new code require precise parameters, correctability proof, stabilizer/logical relations, distance and comparative evidence; for decoder claims require latency/error/scale metrics and complexity analysis. Do not attribute novelty to notation alone.

**Gate G7:** independent peer challenge and positive reproducible evidence before describing a hypothesis as demonstrated; negative findings and null results are publishable and must be retained.

## 5. Sequencing, milestones and ownership

| Milestone | Planned window* | Dependencies | Demonstrable acceptance |
|---|---|---|---|
| M0 baseline / ADR | Week 1 | none | G0 |
| M1 mathematics / fixtures | Weeks 1–3 | M0 | G1 |
| M2 executed repetition-code demo | Weeks 3–6 | M1 | G2 |
| M3 QEC-IR evidence integration | Weeks 5–8 | M2 | G3 |
| M4 decoder/reference evaluation | Weeks 7–11 | M3 | G4 |
| M5 comparative, profile alignment | Weeks 10–13 | M4 | G5 |
| M6 outside review and RC | Weeks 13–16+ | M5 | G6 |
| R1 new-theory questions | parallel only after M2 | owner approval | G7 independently |

*Indicative only, not a delivery guarantee. Reprioritise after WP0 inventory, staffing review and measured complexity. Developer must log blockers and cannot silently mark a gate done.

**Owner (Oleksandr):** problem formulation, architecture/ADR approval, user outcomes, IP and partner outreach. **AI/developer:** implementation, test evidence, documentation, reproducible artifacts, candid status. **Independent QEC reviewer:** mathematical checks, methodological critique, external replication. A developer's local green CI is not independent review.

## 6. Testing and evaluation matrix

| Test class | Required examples | Criterion |
|---|---|---|
| Algebra | commuting/anticommuting, dependent generators, identity, zero-syndrome logical, phase convention | independent oracle agreement or explicit reject |
| Code/noise scope | restricted X repetition; Z/Y and mixed Pauli counterexamples | correct limitation; never mislabel as fully correctable |
| Circuit execution | fault-free, single fault, multi-fault, mid-circuit measurement and reset as supported | reproducible, physically correctly interpreted |
| Decoder | success/failure cases, degenerate syndromes, inconsistent detector data | baseline agreement and explicit undecidable states |
| Statistics | fixed seed, repeated seeds, zero failures, extreme probabilities, variable shots | counts reproducible; intervals and uncertainty sound |
| Evidence | missing hash, mismatched circuit, altered count file, missing calibration, ambiguous order | reject, quarantine or unassessed; never fabricate authentication |
| Cross-backend | supported Stim vs independent reference; unsupported non-Clifford | agreement where supported, explicit refusal elsewhere |
| Resources | memory cap, shot cap, timeouts, 3/5/7/9-qubit ladder as feasible | bounded allocations; separate refusal from quantum failure |
| Compatibility | existing QEC CLI, other E7Q commands, RC schemas | no unexpected regressions |
| External reproduction | clean host, pinned dependencies, one command, raw artifacts | same substantive output and documented environment variance |

**Metric dashboard:** pass/fail per bounded predicate; simulator execution duration; decoder duration; peak memory; evidence completeness; failure detection under planted corruption; logical-error point estimate and interval; reproducibility rate; reviewer findings; unassessed-claim count. Publish adverse outcomes and total work, not only selected successes.

## 7. Implementation layout (proposal, adapt to repository conventions)

```text
docs/qec/
  BASELINE_INVENTORY.md
  ADR-0001-SCOPE.md
  MATH_CONTRACT.md
  QEC_PROFILE.md
  CLAIM_REGISTER.md
  VALIDATION_MATRIX.md
  E7GT_V015_ADAPTATION.md
  EXPERIMENT_PROTOCOL.md
  REPRODUCTION.md
  INDEPENDENT_REVIEW.md
src/e7q/qec/                 # exact package layout decided after WP0
  algebra.py
  profile.py
  runner.py
  decoders.py
  assessments.py
  evidence.py
  adapters/
examples/qec/repetition3/
examples/qec/surface_code/  # add only after scope gate
pilots/qec_syndrome/         # preserve existing; do not fork oracle
schemas/qec/                # or existing schema home
scripts/reproduce_qec.py
tests/qec/
```

**PR discipline:** Each PR: change description; declared work package; source claims affected; changed schemas; exact commands and raw tests; oracle comparison; scope/non-claims; compatibility report; outstanding risks; whether AI-generated implementation was reviewed. Keep PRs narrow: WP0 docs, WP1 algebra, WP2 execution, WP3 evidence, WP4 decoder, WP5 extensions, WP6 external reproducibility. Use existing naming and release governance rather than impose this layout if it conflicts.

## 8. Build completion criteria / stop conditions

### Minimum useful release (MVP)

All G0–G3 passed: a verified, bounded repetition-code execution+syndrome+recovery demonstration, independent mathematical oracle, QEC-IR evidence linkage, precise nonclaims and one-command replay. Call it **QEC verification pilot**, not full QEC platform.

### Research-quality candidate

G0–G5 passed plus independent reproduction package, transparent benchmark and statistical design. Publish negative controls; mark external review as pending until G6.

### Stop, redesign or narrow scope if

- independent oracle disagrees and the discrepancy is not understood;
- claimed logical-error gain disappears under equivalent baselines;
- evidence provenance cannot distinguish supplied from authenticated results;
- adapters mask unsupported physical semantics;
- v0.15 mapping changes legacy output without accepted migration;
- current benchmarks show no useful assurance gain relative to cost;
- licensing or research data permissions are unresolved.

## 9. First developer assignment — issue ready to paste

**Title:** `QEC-WP0: Freeze baseline, reconcile existing QEC pilot and approve evidence-native QEC scope`

**Description:** Inspect latest E7Q default branch; reproduce existing `e7q qec-homomorphism` and reference checker; inventory current QEC and Stim capabilities, E7Q-IR status, schemas, active PRs, dependencies and licences; record precise existing vs proposed features. Pin E7Q commit and E7G-T v0.15 reference hash without automatically migrating runtime. Create the baseline inventory, claim register, ADR and scoped WP1–WP3 issues. State blockers and proposed first implementation PR. Do not implement a new decoder or refactor the kernel in this issue.

**Acceptance:** green baseline tests on clean environment, executable reproduction log, justified status table, no duplicate QEC namespace, owner-reviewed ADR and a dependency-ordered PR plan.

**Developer response format for every handoff:** `CURRENT STATE → CHANGES → EXECUTED EVIDENCE → UNSUPPORTED CLAIMS → RISKS → DECISIONS NEEDED → NEXT PR`.

## 10. Partner/employment-facing outputs (after evidence gates, not before)

- Two-page technical brief with precisely stated implemented QEC scope, reproducible commands and link to public repository.
- Five-minute demonstration showing expected fault, measured syndrome, recovery, observable outcome, and bounded claim.
- Independent baseline comparison; evidence-layer overhead and value; negative examples.
- Reviewable third-party technical report or issue/PR from an external QEC specialist.
- Role-specific portfolio for **verification architect / technical product lead / QEC R&D coordination**. Do not assert QEC Engineer qualifications are satisfied merely because the project exists.

## 11. References and traceability

**Checked E7Q GitHub files:**
- https://github.com/E7GT-Ecosystem/E7Q/blob/main/README.md
- https://github.com/E7GT-Ecosystem/E7Q/blob/main/docs/QEC_SYNDROME_PILOT.md
- https://github.com/E7GT-Ecosystem/E7Q/blob/main/docs/E7GT_Quantum_Mapping.md
- https://github.com/E7GT-Ecosystem/E7Q/blob/main/docs/e7q-ir/ARCHITECTURE.md
- https://github.com/E7GT-Ecosystem/E7Q/blob/main/ROADMAP.md

**Project-supplied canonical references:**
- `E7G-T_Kernel_v0.15_Experimental_Canonical_Reference.md`, §X.19 WPC, §X.20 REC, §X.21 MSC and Part I migration boundaries.
- `FPF-Spec (8).md`, A.1.1, A.2.6, A.7, A.9, A.10, and assurance / evidence patterns. FPF is internal engineering discipline, not an assertion that standard QEC mathematics originates in FPF.

**External methods to consult and cite when implemented:** standard stabilizer formalism, Stim and PyMatching documentation, Deltakit/QEC workflow documentation, and primary papers for any code/decoder/threshold claim. Dependency versions and papers must be captured by the developer at implementation time. No external implementation is approved purely because it is mentioned here.
