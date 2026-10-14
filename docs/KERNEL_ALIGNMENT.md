# E7Q and E7Q-IR kernel alignment

Direction: `E7-ECO-DIR-2026-09-13.1`  
Baseline reviewed: main `48a3999bb2068a8666eae7bec05c0c070665a3b7`
Status: `ALIGNED_THROUGH_Q_A2` after the additive Q-A1 restriction/view
correction and Q-A2 interoperability revalidation. Q-A3 realisation and Q-A4
receipt binding remain unimplemented.

Interoperability includes partial, identity (retain-all), and terminal-empty
restrictions. `empty` is retained as a non-success history outcome with no
residual family; retain-all success is not rejected merely because it excludes
no member.

## Source and profiles

- Kernel: E7G-T v0.12.1-experimental, revision RGP2, commit `fc4cdf95c6434e653efbe017587aab60b4b2a86c`.
- EEC-Q/0.1: `experimental` for formal construction semantics only.
- SF/0.1: `experimental` for circuit/layout/target/calibration candidate families.
- CFS/0.1: `experimental` for an SF-outside/product-state-inside planning adapter.
- RGP/0.1: `experimental` for forward-compatible Q-A4 layer and generation-edge receipt binding; not active in Q-A1/Q-A2.

EEC-Q rational coefficients are not quantum amplitudes or probabilities. Physical state, channel, measurement and backend semantics remain in E7Q's quantum layer.

## Current mapping and disposition

| Current component | v0.12 relationship | Provisional disposition |
|---|---|---|
| Typed quantum programs and IR artifacts | Product configurations with native quantum semantics | retain |
| Invariants, equivalence criteria and assessments | Criterion-bound product rules and findings | retain |
| Proof-of-Path and deterministic receipts | History/provenance and replay evidence | retain |
| Provider/import artifacts | Explicit external references; never automatically trusted or executed | retain |
| Candidate circuits, layouts and targets | Q-A1 dependence-aware family plus corrected bounded restriction/view profiles | retain family v0alpha1; adapt restriction/view additively |
| Lowering, routing, scheduling and binding | Q-A2 ordered typed declaration with domains, loss and terminal outcomes | retain as bounded contract; adapt to native executors later |
| Selected hardware mapping | Declared realization from a residual family | adapt |
| Complete compilation path | Candidate immutable quoted construction | adapt |

No replacement or retirement is authorized before compatibility vectors show a semantic defect.

## Semantic hazards to test

- correlated circuit/layout/target choices must not become independent marginals;
- inspection views must retain their exact source;
- pruning is explicit restriction, not an unlabelled view;
- equivalence-class execution requires domain saturation and result congruence;
- transform order and failed operations remain part of program meaning;
- unsupported hardware or compiler behavior is not successful empty output;
- packaging a compilation family preserves the whole and its dependence structure.

## Bounded v0.12-native demonstration

Represent one topology-sensitive program as a candidate family over circuit, layout, target and calibration context. Apply ordered lowering/routing/scheduling transformations, retain the residual family, realize one mapping under declared lexicographic objectives, and bind source, transforms, selected mapping and execution evidence in an E7Q receipt.

Falsification gate: stop the CFS planning lane if it cannot preserve shared dependence, integrate without material semantic distortion, or improve auditability over an ordinary candidate table.

## Additive local Q-A4 adapter checkpoint — 2026-10-14

The preceding Q-A2-only/unimplemented status is the historical alignment
checkpoint. Q-A3 merged through PR #84 at
`c519484bccdbe411b05acdba9c24ef1cd852d041`. A separately owner-selected Q-A4
local slice binds validated unique selection to exact supplied legacy receipt
bytes and original-source/OpenQASM/target commitments. The selected five offline
suites passed 311 tests, and independent implementation/adversarial review passed
with no open technical finding. An unauthorized 450-byte worker-note write
outside the product checkout remains a separately disclosed procedural exception
in the receipt-binding verification record; it is not erased by technical PASS.

The architecture pin remains **v0.12.1-experimental/RGP2** at
`fc4cdf95c6434e653efbe017587aab60b4b2a86c`, not a newer executable reference.
Product-local wrappers expose all ten pinned components
`Sigma,B,G,I,A,E,D,Pi,K,M` and independent `place=<r,rho,tau,alpha,c>`.
A/E/D/Pi and all coordinates are explicitly unknown; K establishes only partial
canonical/receipt consistency checks, not semantic or authenticated execution
invariants. Typed metadata-generation rules reconstruct wrapper fields; the
realisation-to-supplied-receipt edge references evidence and never claims causal
execution or kernel Generates for a physical observation.

This is a partial experimental **RGP2-inspired adapter**, not full RGP
conformance, SR1–SR4, source-retention tier or shared-runtime acceptance.
Original family/history/realisation IDs, core graph relation kinds and receipt
engines remain unchanged. No compiler/simulator/provider/native/hardware run,
kernel migration or deployment is selected. See the product-local contract at
`docs/e7q-ir/RECEIPT_BINDING.md`; broader execution/domain gates remain separate.

## Local open-core alignment after PR #87 — 2026-10-14

The owner selected retention of existing public terms and separately approved
the licensing-fixture repair, extending the local increment to ten paths on
`8193a2818c849bc20caf5ff1c20f2e0b2ce49e20`. This licensing merge is not a
kernel migration. The pinned RGP2 architecture and Q-A4 partial-adapter scope
above remain unchanged. Three exact-hash register decisions, an Apache notice
in the export module and a test-fixture-only repair change no quantum semantics,
source-retention claims or runtime acceptance.

Aligned verification passed the licensing boundary, eleven licensing controls
and 311 focused offline tests; independent read-only alignment review returned
technical PASS with no actionable findings.
The original checkout/history and earlier worker-note procedural exception are
preserved. No publication, package build, native/provider/hardware run, remote
CI, deployment or broader execution/domain gate is selected.
