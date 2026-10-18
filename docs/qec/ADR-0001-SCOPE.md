# ADR-0001 — Additive, bounded QEC profile scope

**Status: PROPOSED — pending explicit owner acceptance.**

Prepared: 18 October 2026. Scope: WP0 reconciliation only.

Decision owner: Oleksandr Razinkov. Acceptance: **not recorded**.

G0: **OPEN**; G1–G3: **not assessed by this ADR**.

## Context and authority

This proposal reconciles the [WP0 handoff](WP0_PILOT_HANDOFF.md), the [proposed buildmap](E7Q_QEC_Developer_Buildmap_v0.1.md), [kernel alignment](../KERNEL_ALIGNMENT.md), the actual [pilot report](../../pilots/qec_0_1/REPORT.md), [adapter](../../pilots/qec_0_1/adapter.py) and [optional profile bridge](../../pilots/qec_0_1/profiles.py). The buildmap is not a completion record. Its v0.15 heading and older README warning do not override the retained architecture pin or actual implementation.

| Evidence anchor | Exact identity / interpretation |
|---|---|
| Upstream baseline / pilot parent | `b7989c647e5d0e22ed1128c41aceb2dda2f23405`; historical baseline, not a claim about today's remote main |
| Original local pilot | `4be5125c3198c9db980865c57814cb41aa4b13b5` |
| Published equivalent pilot | `6f66233e68d3cd52a3f01f6548259003e497b2c5` |
| Handoff-declared common tree | `f58a7e4d41afb7bef68244ca333309e9e55b06f6`; equal tree does not imply equal commit metadata |
| Inspected handoff HEAD | `88467d51b21d3e072baae583fc4f23e676db59d6` |
| Governing architecture | E7G-T v0.12.1-experimental/RGP2, `fc4cdf95c6434e653efbe017587aab60b4b2a86c` |
| Optional experimental companion | E7G-T `4d6e02f16363f2333961cf4350d584c92d51bbc6`; separate experiment, not a migration |

The pilot predates this reconciliation. Publication, stored result files and this proposal cannot retrospectively close G0 or constitute owner acceptance, preregistration or external review. Fresh reproduction is recorded in [WP0 verification](WP0_VERIFICATION.md), including environment, commands, failures/recoveries, skips and reviewer disposition. This ADR must be considered together with the [baseline inventory](BASELINE_INVENTORY.md) and [claim register](CLAIM_REGISTER.md); fresh computational agreement does not itself close G0 or establish independent scientific review.

## Proposed decision

Select one **opt-in, additive repetition-three, definite-syndrome circuit-restoration profile** within E7Q-IR. This phrase describes a proposed domain, **not an approved schema or profile identifier**. Retain all existing identities and formats. The pilot-local `e7q.qec-case/0.1` remains a pilot exchange contract, not a product schema. The buildmap's suggested `e7q.qec-profile/v0alpha1` is not installed or approved by this ADR. WP1 must review any eventual identifier and minimal schema before implementation/admission.

### First domain and exact selection

- Code: three data qubits, positive ordered generators `(ZZI, IZZ)`, Pauli strings ordered `q[0]..q[2]`. Logical representatives: `X_L = XXX`, `Z_L = ZII`. No general `[[3,1,3]]` arbitrary-Pauli-correction claim.
- Admitted preparations: logical `zero`, `one`, `plus`, `plus_i` only, encoded from `(a,b)` into `a|000> + b|111>`. The pilot's eight finite complex amplitudes must agree with the named preparation; no arbitrary-amplitude loader is inferred.
- Positive restricted error model: `{III, XII, IXI, IIX}`. Reference recovery table, in generator-bit order: `00 -> III`, `10 -> XII`, `11 -> IXI`, `01 -> IIX`.
- Simulated circuit shape: five-qubit noiseless dense statevector circuit; two ancillas coherently extract the ordered syndrome; apply a supplied recovery, inverse encoding and inverse preparation. E7Q parses, runs and verifies actual submitted source. No injected reference state masquerades as native execution evidence.
- First regression corpus: retain the pilot's 77 specialized-recovery cases, 33 separate coherent full-table cases and 64 phase-insensitive Pauli algebra comparisons as distinct corpora. Z and two-X cases are negative/limitation controls, not expansion of the correction domain.
- Native full-register output labels put `q[0]` first, while reference vector indexing makes `q[0]` least significant. Preserve this explicit bridge and its regression: syndrome `(1,0)` maps to `00010`, `(0,1)` to `00001` after restoration.
- Full-table experiment compiles all table entries into coherent controls. Its decomposed CCX construction is not an exclusively Clifford implementation and is not classical measurement/feedforward. Do not silently route it to a Clifford-only backend.

### Tiny semantic criterion

For each admitted pure-state, definite-syndrome case, assess **both** the declared ordered syndrome and restoration of that particular named logical input. After inverse encoding/preparation, require dense output support only at `000s0s1`, using the existing verifier's declared numerical tolerance (pilot report: `1e-12`). Unit probability on data `000` in this restricted setting means state restoration up to global phase. The separate dense oracle compares syndrome and overlap fidelity using its own recorded tolerance (pilot adapter: `1e-10`); tolerance differences must remain visible.

This criterion is not normalization alone, computational-basis measurement equivalence, decoder-table correctness, all-logical-input channel equivalence or code-wide correctability. The specialized corpus evaluates the supplied recovery operation; `decoder_action_consistent` is adapter bookkeeping, not an E7Q lookup-table verdict. The separate coherent circuit addresses its submitted full-table circuit only.

The reported three two-X passes on logical plus are expected state-specific invariance under residual logical X. They do **not** show correction of two errors. `XXX` can have zero syndrome and act nontrivially on the code space. Every report must preserve that distinction.

### Proposed input/evidence shapes and outcomes

These are review requirements, not approved schemas, relation names or new status enums.

| Shape / evidence | Required meaning |
|---|---|
| Case declaration | Exact source/corpus identity, named preparation and amplitudes, ordered generators, Pauli fault, expected syndrome, complete four-entry table, supplied recovery and unit-restoration claim |
| Execution record | Actual source bytes/digest, backend and versions, seed/shots, gate/bit-order bridge, resource policy, full native report/trace and raw outcome; simulated provenance explicit |
| Reference assessment | Independent dense/tableau inputs, versions, numerical criteria and results; distinguish independence of implementation from external reviewer independence |
| Domain assessment | Admission, syndrome match, state-restoration result, residual classification and table bookkeeping separately; unsupported rules remain visibly unassessed |
| Evidence integration | Existing E7Q-IR envelopes/identities and compatible typed links; source return, projection loss, environment and replay dependencies recorded; no parallel graph |

Use existing outcome contracts at each layer. A supported executed assertion may PASS or FAIL; malformed input is rejected, unsupported semantics remain UNSUPPORTED/NOT_ASSESSED as applicable, unavailable required dependencies are BLOCKED/NOT_ASSESSED, and enforced caps produce RESOURCE_LIMIT rather than mathematical failure. Retain raw backend outcomes and reasons instead of manufacturing one universal status. Missing expected data, missing recovery, ambiguous ordering or unknown criteria never become PASS.

The source-to-syndrome projection preserves commutation bits but loses phase and identity within each syndrome fibre. A state-specific restoration verdict loses all-input channel information. Statevector simulation establishes no physical observation. Evidence links and hashes establish bounded consistency, not provider authenticity or causal execution.

## Profile and component dispositions

| Component/profile | Disposition | Boundary |
|---|---|---|
| `src/e7q/qec.py` and `e7q.qec` imports | **retain** | Preserve `QECError`, `StabilizerCode`, algebra/report APIs, existing CLI and emitted identities; no module-to-package replacement |
| Native parser/simulator/verifier and comparison criteria | **retain** | Evaluate submitted circuits under existing criteria; no semantic promotion |
| Existing E7Q-IR, receipts, F0/F1/F2, IDs and relation contracts | **retain** | Generic/native F2 does not validate QEC semantics; QEC-specific coverage requires separately reviewed rules |
| Pilot adapter/corpora | **adapt prospectively**, retain original evidence | No pilot edits in WP0; product adoption only after gates and licensing review |
| v0.12.1/RGP2 architecture pin | **retain** | No source or downstream migration |
| MSC-B1 finite-carrier exact-agreement experiment | **optional experimental evidence only** | At companion pin above, evaluate supplied parity maps/coherence; not quantum measurement or correctability |
| REC-B1 scoped evidence/replay experiment | **optional experimental evidence only** | At companion pin above, support/conflict/absence/replay; not numerical truth or hardware validation |
| EEC-Q, SF, CFS, RGP execution, WPC | **not selected for this QEC slice** | Existing unrelated uses remain intact; no coefficients treated as amplitudes/probabilities |
| Replacement/retirement | **none** | No approved migration or deletion |

For the optional companion, preserve exact historical edition labels, including REC's `kernel: 0.14-experimental-draft`, `profile: REC/0.1-proposed`, `model: REC-B1/0.1`, and MSC's existing `msc-diagram-v1` exchange label. Consult [source manifest](../../pilots/qec_0_1/SOURCE_MANIFEST.json) for source/result digests. Do not relabel these as newly v0.15-conformant or make them mandatory for the base workflow. Retain same-session provenance grouping and distinguish a replay checker from independent scientific review.

## Explicit exclusions and buildmap deviation

No decoder implementation in WP0 or automatic product admission of the pilot decoder. No noisy/mixed channels, stochastic syndrome ensembles, arbitrary states, hardware, authenticated provider receipts, adaptive classical feedforward, full QEC, thresholds/fault tolerance, surface/Steane codes, native/F2 promotion, novel algorithm/code, scaling or performance advantage is selected. Timing comparisons involve unequal workflow overheads and are not a speed claim. No issues, PRs, commits, pushes or contacts are authorized by this proposal.

The actual buildmap WP1 is **algebra foundation and negative cases**, WP2 is the **focused execution/evidence demonstrator**, and WP3 is **QEC-IR semantic/evidence integration**. The proposed first WP2 evaluator slice deliberately stops at the existing coherent definite-syndrome domain. It does **not** satisfy the buildmap's classically chosen recovery requirement or close full G2. Owner must accept this first bounded evaluator milestone explicitly or request revision. This ADR does not waive the original G2 gate: WP3 implementation remains blocked until full applicable G2 is met, unless a later separately reviewed ADR explicitly changes sequencing. Bounded coherent results may inform WP3 design, not authorize integration or imply completion of M2/M3 or the MVP.

## Acceptance and stop gates

1. G0 requires completed inventory, unchanged baseline reproduction and independent checker, reconciled claim register, dependency/licensing record, no regressions, and explicit owner acceptance of this ADR. No historical pilot result substitutes for these.
2. WP1/G1 requires independent algebra agreement, phase/sign safeguards, malformed/dependent/noncommuting and zero-syndrome-logical counterexamples, generator-order tests, compatibility evidence and mathematical review.
3. First WP2 slice requires positive and adverse corpus replay, independent reference agreement, explicit state-specific criterion and resource/unsupported controls. Full buildmap G2 remains open without its separately accepted adaptive execution work.
4. WP3/G3 requires reviewed schema/semantic contracts, deterministic canonical evidence apart from declared volatile observations, corruption/partial-input tests, identity/API compatibility and no F2 escalation.
5. Oracle discrepancy, hidden ordering loss, unsupported semantics presented as success, unresolved rights or source-pin change stops the affected lane. Record the discrepancy; do not weaken the expected check to obtain green tests.

## Decisions the owner must accept explicitly

- The exact first code/preparation/error domain, state-specific criterion and nonclaims above.
- Retention of the RGP2 pin, legacy QEC module/APIs and all current identity formats; no namespace refactor.
- Whether optional MSC/REC remains isolated replay evidence at the companion source, or is excluded entirely; neither choice migrates architecture.
- The coherent-first WP2 evaluator milestone, with classical feedforward and full G2/MVP still open; WP3 implementation remains behind the original applicable G2 gate. No sequencing waiver is part of this acceptance request.
- The dependency gates, proposed future write scopes and schema/licensing/scientific review requirements in [WP1–WP3 plan](WP1-WP3_PLAN.md).

Record a dated owner decision against an exact document revision and the completed WP0 verification record. Until then this ADR remains **PROPOSED**, and further implementation is blocked on G0.
