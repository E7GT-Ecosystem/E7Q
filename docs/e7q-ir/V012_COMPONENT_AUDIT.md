# E7Q-IR v0.12 component audit

Direction: `E7-ECO-DIR-2026-09-12.2`  
Reviewed baseline: `a9fd841d47ea4ed434fabad3bc9a9a406b33c9a8`  
Kernel: E7G-T v0.12-experimental/CFS1 at
`b7a30b2d56375a5a0646e0c1cab4f621b4de99ca`  
Status: `ALIGNED_IN_DESIGN`; Q-A1 bounded candidate-family contract implemented.

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
| Compiler path | `compiler_workflow.py` and compiler Proof-of-Path fixture | adapt | Add explicit transform domain, order and loss contract |
| Candidate selection | current planning and calibration modules | adapt | Introduce dependence-aware candidate family without changing quantum semantics |
| Views and pruning | report/inspection and candidate filtering surfaces | adapt | Type each as `view`, `identify` or `restrict` |
| Complete compilation construction | source, candidates, transforms, selection and receipt | adapt | Add immutable quotation metadata and source-linked receipt |
| EEC-Q coefficient arithmetic | no native quantum mapping | not applicable | Prohibit use as amplitudes, probabilities or evidence weights |

No component requires replacement or retirement on current evidence.

## Hazard findings

1. Existing evidence graphs preserve source/representation separation and
   criterion-bound verdicts; a rewrite would risk losing tested compatibility.
2. Current candidate and calibration surfaces do not yet provide a single
   versioned dependence contract for circuit/layout/target/calibration choices.
3. Transformation evidence exists, but a general ordered domain and
   view/identify/restrict declaration is not yet shared across all compiler
   stages.
4. Existing non-PASS states and isolated external-tool outcomes already satisfy
   the v0.12 requirement not to collapse failure into algebraic zero or success.
5. Whole-construction quotation is not yet a native E7Q-IR contract. Adding it
   must not distribute one compilation family's authority or evidence to its
   members.

## Compatibility vectors required for Q-A1

- a shared layout/target choice remains two correlated alternatives, not four
  independent cross-products;
- an explicitly independent candidate pair expands as declared;
- restriction records excluded candidates and never masquerades as a view;
- identification records its many-to-one loss;
- unsupported and resource-limited candidate evaluation cannot realise a
  mapping;
- changing transform order changes history identity even when final circuit
  bytes happen to match;
- packing the complete candidate construction differs from packing each
  candidate independently;
- old E7Q-IR graphs, profiles and F0-F2 reports remain byte- and verdict-stable.

## Bounded Q-A1 demonstration

Represent one topology-sensitive program as a family over circuit, layout,
target, calibration snapshot and constraints. Apply an ordered transformation
sequence, retain the residual family, and realise one mapping under declared
lexicographic objectives. Produce a source-preserving inspection view and a
receipt binding the source family, transformation history, residual family,
selection criterion and selected mapping.

Stop or narrow the lane if it invents independence, changes existing quantum
meaning, weakens fail-closed behavior, or supplies no observable assurance
advantage over an ordinary candidate table.

Implementation: `src/e7q/ir/candidate_family.py` and
`tests/test_ir_candidate_family.py`. Q-A1 deliberately stops before semantic
selection, quotation, realization, or F2 promotion.
