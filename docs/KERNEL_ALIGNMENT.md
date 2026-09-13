# E7Q and E7Q-IR kernel alignment

Direction: `E7-ECO-DIR-2026-09-12.2`  
Baseline reviewed: main `4a078fb9590e3d936b314dccd09724fdc26b383d`
Status: `ALIGNED_THROUGH_Q_A2` after the additive Q-A1 restriction/view
correction and Q-A2 interoperability revalidation. Q-A3 realisation and Q-A4
receipt binding remain unimplemented.

## Source and profiles

- Kernel: E7G-T v0.12-experimental, revision CFS1, commit `b7a30b2d56375a5a0646e0c1cab4f621b4de99ca`.
- EEC-Q/0.1: `experimental` for formal construction semantics only.
- SF/0.1: `experimental` for circuit/layout/target/calibration candidate families.
- CFS/0.1: `experimental` for an SF-outside/product-state-inside planning adapter.

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
