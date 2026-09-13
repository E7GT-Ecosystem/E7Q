# E7Q-IR v0.12 component audit

Direction: `E7-ECO-DIR-2026-09-12.2`  
Reviewed baseline: `16bd96c36b0e659ffc6798ff1a88e72cc56d11dc`  
Kernel: E7G-T v0.12-experimental/CFS1 at
`b7a30b2d56375a5a0646e0c1cab4f621b4de99ca`  
Status: `ALIGNED_THROUGH_Q_A2` within the finite declared contract boundary.

## Audit boundary

This audit compares the default-branch implementation, schemas, profiles,
fixtures and public plans with the v0.12 distinctions that can change E7Q
program meaning. It is a code-and-contract inventory, not full-kernel
conformance, hardware validation, independent review or product validation.

## Component dispositions

| Component or interface | Evidence inspected | Disposition | Required action |
|---|---|---:|---|
| Artifact envelopes and canonical identity | `src/e7q/ir/envelope.py`, `canonical.py`, envelope schema | retain | Preserve current IDs and byte identity |
| Evidence graph and typed relations | `graph.py`, graph schema and F0/F1 tests | retain | Keep source and representation nodes distinct |
| Semantic profiles and F2 results | `profiles.py`, `semantic.py`, `conformance.py` | retain | Preserve criterion-specific verdicts and non-PASS states |
| Native, legacy and external adapters | `native.py`, `legacy*.py`, workflow modules | retain | No silent promotion of imported declarations |
| Isolated QCEC and PyZX assessment | `qcec.py`, `pyzx.py`, process/resource tests | retain | Keep numerical/exact criteria and inconclusive outcomes separate |
| Compiler path | `compiler_workflow.py` and compiler Proof-of-Path fixture | adapt | Retain native execution; adapt remaining planning/compiler surfaces to the implemented declared domains and ordered histories where required |
| Candidate families and restriction | `candidate_family.py`, schemas, profiles and tests | retain | Retain the implemented finite dependence contract and partial, identity and terminal-empty restriction paths |
| Views and identification | versioned candidate-family view/restriction records and history declarations | retain/adapt | Retain source-return and declared loss; general identification execution remains unproved |
| Ordered histories | `transformation_history.py`, schema, profile and tests | retain | Preserve order-sensitive identity and typed validation without claiming compiler execution |
| Complete compilation construction | source, candidates, transforms, realisation and receipt | adapt | Add Q-A3 realisation and Q-A4 family/realisation receipt binding before considering whole-construction quotation |
| EEC-Q coefficient arithmetic | no native quantum mapping | not applicable | Prohibit use as amplitudes, probabilities or evidence weights |

No component requires replacement or retirement on current evidence.

## Hazard findings

1. Existing evidence graphs preserve source/representation separation and
   criterion-bound verdicts; a rewrite would risk losing tested compatibility.
2. Q-A1 now provides a finite versioned dependence contract for admitted candidate families; remaining native planning/compiler surfaces are not automatically covered by that contract.
3. Q-A2 validates declared ordered histories and view/identify/restrict step kinds, but does not execute compiler transformations or prove their quantum correctness.
4. Existing non-PASS states and isolated external-tool outcomes already satisfy
   the v0.12 requirement not to collapse failure into algebraic zero or success.
5. Whole-construction quotation is not yet a native E7Q-IR contract. Adding it
   must not distribute one compilation family's authority or evidence to its
   members.

## Delivered compatibility vectors through Q-A2

- a shared layout/target choice remains two correlated alternatives, not four
  independent cross-products;
- an explicitly independent candidate pair expands as declared;
- restriction records excluded candidates and never masquerades as a view;
- identification records its many-to-one loss;
- partial, retain-all identity and retain-none terminal-empty restriction results interoperate with ordered histories;
- changing transform order changes history identity even when final circuit bytes happen to match;
- packing the complete candidate construction differs from packing each
  candidate independently;
- old E7Q-IR graphs, profiles and F0-F2 reports remain byte- and verdict-stable.

## Current delivered boundary and multi-package target

Q-A1 candidate families and corrected restriction/view profiles, together with Q-A2 ordered-history contracts, are implemented and internally tested at the cited commit. Partial, identity and terminal-empty restriction paths are covered. Declared domains and validated history records do not execute compiler transformations or prove quantum correctness.

The multi-package target is a complete family → transformation → realisation → receipt demonstration. Native compiler execution integration, Q-A3 realisation, Q-A4 family/realisation receipt binding and whole-construction quotation remain outside this delivered boundary. Existing native receipts are retained; the missing work is the new binding between the source family, ordered history, residual family, selected realisation and receipt.

Stop or narrow the lane if it invents independence, changes existing quantum
meaning, weakens fail-closed behavior, or supplies no observable assurance
advantage over an ordinary candidate table.

Implementations include `src/e7q/ir/candidate_family.py` and `src/e7q/ir/transformation_history.py` with their versioned schemas, profiles and regression tests. PR #74 closed the reproduced partial/identity/terminal-empty interoperability paths. This boundary is not full SF, EEC-Q or CFS conformance and does not promote any result to F2.
