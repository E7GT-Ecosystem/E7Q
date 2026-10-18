# QEC WP1–WP3 — dependency-ordered local issue/PR drafts

**Status: PROPOSED; LOCAL DRAFTS ONLY.** Prepared 18 October 2026.

No issue, PR, publication, implementation authorization or reviewer sign-off is created by this document. Owner acceptance of [ADR-0001](ADR-0001-SCOPE.md) and completion of G0 remain prerequisites.

## Current state and evidence boundary

Use the [WP0 handoff](WP0_PILOT_HANDOFF.md) and [actual buildmap §4](E7Q_QEC_Developer_Buildmap_v0.1.md) with upstream baseline `b7989c647e5d0e22ed1128c41aceb2dda2f23405`, original pilot `4be5125c3198c9db980865c57814cb41aa4b13b5`, published equivalent `6f66233e68d3cd52a3f01f6548259003e497b2c5`, handoff-declared tree `f58a7e4d41afb7bef68244ca333309e9e55b06f6` and inspected handoff HEAD `88467d51b21d3e072baae583fc4f23e676db59d6`.

These anchors are not a live remote inventory. The completed [baseline inventory](BASELINE_INVENTORY.md), [claim register](CLAIM_REGISTER.md) and [verification record](WP0_VERIFICATION.md) record fresh reproduction, custody, commands, outputs, skips, discrepancies and environment. Prior [pilot report](../../pilots/qec_0_1/REPORT.md) results remain historical evidence; fresh replay does not retrospectively preregister them or establish owner/scientific acceptance. This plan adds no such acceptance.

Architecture remains v0.12.1-experimental/RGP2 at `fc4cdf95c6434e653efbe017587aab60b4b2a86c`. Optional MSC/REC experiment source `4d6e02f16363f2333961cf4350d584c92d51bbc6` is not a migration; preserve historical edition labels. `src/e7q/qec.py`, its imports/APIs, current schemas/identities and generic F0/F1/F2 meanings remain intact.

## Sequencing and meaning of milestones

```text
WP0 inventory + claim reconciliation + fresh verification + explicit ADR acceptance
  -> G0 accepted (not currently recorded)
  -> WP1 contract/minimal schema review -> algebra/adversarial corpus -> G1 review
  -> WP2 bounded evaluator contract -> executed corpus/oracle review -> slice acceptance
  -> HOLD: applicable FULL G2, including measured-syndrome classical correction
  -> WP3 bounded evidence contract/integration only after full G2 -> compatibility/adversarial review
```

WP1 is the buildmap's **algebra foundation and negative cases**, not a decoder package. WP2 is its **execution/evidence demonstrator**, not evidence-only schema work. WP3 is its **QEC-IR schema, semantic adapter and evidence pack**, not decoder evaluation (that belongs to WP4).

**Explicit proposed narrowing:** first WP2 work evaluates the existing noiseless, coherent, definite-syndrome repetition-three domain. It excludes adaptive classical feedforward. It may be called a bounded evaluator milestone, **not full WP2/G2 or MVP completion**. The buildmap calls for a classically chosen recovery in a focused Clifford workflow; the pilot's full-table decomposed controls do not implement that. Owner acceptance of the coherent-first milestone does not waive G2: WP3 implementation remains blocked until the applicable full G2 gate is met. A future sequencing change would require a separately reviewed ADR, not this WP0 acceptance. No decoder or adaptive implementation is authorized here.

All future paths below are **proposed exact write scopes**, not approvals or installed interfaces. Existing paths are named only where future work may need surgical additive edits. Before opening implementation, reconcile actual files and licensing; revise scope for owner review if a different leaf is needed. Do not silently expand scope to directories, shared formats or `src/e7q/qec/`.

## Local draft A — WP1 mathematical contract and minimal shape

**Issue title draft:** QEC-WP1: Specify bounded algebra contract and adversarial acceptance corpus.

**PR title draft:** Define repetition-three algebra obligations without changing legacy QEC contracts.

**Dependency:** G0 explicitly accepted.

**Proposed write scope:** `docs/qec/MATH_CONTRACT.md`, `docs/qec/QEC_PROFILE.md`, `docs/qec/VALIDATION_MATRIX.md` (documentation first).

Specify ordered symplectic representation, rank/commutation/independence checks, centralizer and stabilizer membership, logical equivalence modulo stabilizers and phase limitations. Use standard stabilizer mathematics. Define logical representatives and exact generator/bit-order conventions from the ADR. Do not claim arbitrary-Pauli correction or derive distance from the repetition-code name.

Propose a minimal versioned input shape and review admission rules: exact fields, finite values, dimensions, positive stabilizer signs or explicit rejection of unsupported signed inputs, supported named preparations, error/recovery operators, complete table and criterion. No future schema identifier is selected here. Review how signed phases and forbidden `-I` will be handled; a phase-quotiented representation must not claim it checks signed physics.

**Acceptance/review gates:**
- Positive: mathematical reviewer can derive the restricted-X syndrome/recovery table and declared logical relationships independently.
- Negative: contract explicitly separates zero-syndrome stabilizer from logical; malformed, dependent, noncommuting, reordered and unsupported signed cases have expected behavior.
- Regression: map each proposed object to existing `e7q.qec` APIs and existing report identities; no renaming or schema promotion by prose.
- Review: owner approves scope/shape; mathematical review is recorded, including whether reviewer independence is established. AI-authored documentation or local tests are not external scientific review.

## Local draft B — WP1 additive checker/oracle corpus

**Issue title draft:** QEC-WP1: Add independent algebra controls and compatibility vectors.

**PR title draft:** Add bounded QEC algebra regression corpus and oracle comparison.

**Dependencies:** draft A contract/shape accepted; G0 still valid.

**Proposed write scope:** `tests/test_qec_algebra_contract.py`, `scripts/check_qec_algebra_reference.py`, `docs/qec/WP1_ORACLE_REPORT.md`; if a reviewed gap actually requires it, surgical additive edits to `src/e7q/qec.py` under a separately recorded API-preservation review. No module/package conversion.

Do not duplicate a completed utility merely to follow the buildmap's word “factor.” Reuse existing implementation and existing independent syndrome checker; any new independent oracle must not import the implementation under test. Capture its exact algorithm, domain and source. No decoder implementation.

**Acceptance/review gates (G1 evidence, not a present verdict):**
- Positive: all 64 three-qubit phase-insensitive Pauli syndromes agree with the independent reference; commuting independent generators and stabilizer/logical representatives behave as specified. Seeded small-domain properties have declared sizes and seeds.
- Negative: malformed lengths/symbols, nonbinary vectors, dependent/noncommuting generators, unsupported phases and forbidden signed cases reject or remain explicitly unassessed. `XXX` zero syndrome is not identity; a phase control is not waved through as harmless.
- Permutations: generator reorder changes syndrome ordering consistently; changing one convention without the bridge is detected.
- Regression: unchanged `qec-homomorphism` example and existing independent checker, old imports, API signatures, report identities and focused legacy tests. Preserve historical fixtures byte-for-byte unless a separately reviewed correction is necessary.
- Review: compare raw per-case results, not only totals; explain any oracle disagreement before continuing. G1 acceptance requires named reviewer disposition and complete evidence, not just green tests.

## Local draft C — WP2 evaluator contract and execution slice

**Issue title draft:** QEC-WP2: Evaluate the bounded coherent repetition-three corpus against independent references.

**PR title draft:** Add opt-in state-restoration evaluator with explicit unsupported outcomes.

**Dependencies:** accepted ADR narrowing, G1, reviewed evaluator contract and dependency/licensing/resource policy.

**Proposed write scope:** `docs/qec/EXECUTION_CONTRACT.md`, `src/e7q/qec_evaluation.py`, `tests/test_qec_evaluation.py`, `docs/qec/WP2_EVALUATION_REPORT.md`. The additive sibling module name is proposed, not an approved namespace. Existing pilot files are read-only reference evidence, not modified or automatically copied.

Implement only after approval: admission, actual source execution via existing E7Q APIs, independent comparison and typed assessment of the tiny criterion. Separate supplied-recovery checks from coherent full-table circuit checks and table bookkeeping. Do not call a normalization-only check restoration. Capture source bytes, generator order, reference-vector/native-label bridge, numerical tolerances, exact versions, seed/shots and enforcement outcomes.

The baseline path must not require optional MSC/REC. Pin NumPy/Stim versions actually tested; do not invent compatibility or copy third-party code without rights review. Optional Stim reference comparison must not be confused with E7Q's stabilizer backend support: the pilot's exact dense-support request is NOT_ASSESSED by that backend. No advertised CLI commands until separately implemented and reviewed.

**Acceptance/review gates:**
- Positive: reproduce actual submitted circuits for the 16 valid restricted cases, matching independent dense/tableau results; retain native evidence and named input identity.
- Negative: preserve the pilot's 16 swapped-table, 16 wrong-syndrome, 16 wrong-recovery, phase and 12 two-X controls as separate groups. Expected historical distributions are comparison targets, not canned evaluator responses. The three two-X logical-plus passes remain state-specific, never code-wide correction.
- Separate full-table corpus: 33 submitted circuits; compare controls and basis truth-table checks for decomposed CCX without falsely calling the circuit Clifford-only or classical feedforward.
- Fail closed: unknown preparation/code/order/gate/criterion, malformed amplitudes, unsupported channel or missing dependency is not PASS. Enforced time/memory/shot/width limits and worker failure retain non-success reasons, distinct from a supported assertion failing.
- Regression: old module/API/CLI outputs unchanged; native parser/simulator/comparer criteria untouched; original pilot source/results remain unchanged.
- Review: audit semantic criterion and the original bit-order defect/bridge; record exact environment, raw results and discrepancies. Same-session independent implementations do not count as external reproduction.

**Exit label:** bounded WP2 evaluator slice accepted only if review records it. Full buildmap G2 remains OPEN pending separately approved classically selected recovery and all original G2 obligations. Do not claim MVP or G0–G3 completion.

## Local draft D — WP3 evidence contract and semantic integration

**Issue title draft:** QEC-WP3: Bind bounded QEC assessments into existing E7Q-IR evidence.

**PR title draft:** Add opt-in QEC evidence linkage without promoting legacy F2.

**Dependencies:** applicable full G2 under the original buildmap; reviewed minimal schema and licensed publication scope. No G2 sequencing waiver is proposed by this package.

**Proposed documentation/test write scope:** `docs/qec/EVIDENCE_CONTRACT.md`, `docs/qec/REPRODUCTION.md`, `docs/qec/WP3_VALIDATION_REPORT.md`, `tests/test_qec_evidence.py`.

Implementation leaf paths inside the existing IR must be selected by a contract review before coding: this draft intentionally grants **no shared IR implementation write scope**. Do not invent a future schema filename/identifier, relation kind or competing identity format. The follow-up PR must declare its exact approved schema/validator leaves and consumers. This is a real blocking dependency, not permission to touch all of `src/e7q/ir/`.

Reuse existing envelopes, canonicalization, artifact IDs, relation guards, source snapshots, receipts and bounded replay. Bind code/case, source, fault, circuit transformation, syndrome/recovery observation, native assertion and bounded assessment. Record losses and simulated provenance; references to existing receipts do not authenticate hardware. Proposed new fields/relations need rationale and compatibility tests, not assumed object-model adoption.

**Acceptance/review gates (G3 obligations, not present results):**
- Positive: schema round-trip, complete resolvable links and deterministic semantic/report payload under fixed inputs/toolchain. Separate elapsed times/environment observations from canonical deterministic identities using existing contracts, without rewriting old identities.
- Negative: altered circuit/count/result bytes, wrong digest, wrong case identity, incompatible generator order, orphan links, missing/partial files, contradictory assessment, malicious fields and unknown semantic rules reject or remain unassessed. Rehashing a false verdict is not sufficient evidence.
- Conformance: distinguish F0 structure, F1 integrity/linkage and individually implemented QEC semantic checks. Generic/native F2 PASS must never manufacture QEC correctness; unimplemented QEC rules are NOT_ASSESSED. No F3 provider-authenticity claim.
- Regression: old artifacts and hashes unchanged; old CLI/API/report fixtures remain valid; baseline works without the new profile or MSC/REC; no kernel/source repin.
- Review: independent reconstruction of evidence links and declared semantics; source-retention/loss and licensing check; unresolved shared-format findings block integration.

Optional MSC/REC replay must be a separately approved test lane, using companion source hashes and historical labels from the original bridge. Check finite ambiguity/incompatibility/missing-map/resource distinctions and REC support/conflict/absence/scope-expansion/forgery controls. None establishes numerical truth, new correction power or full profile conformance.

## Review record required for every future PR

Record: accepted predecessor gate and exact baseline; exact leaf write scope; changed contracts/consumers; rights/publication disposition; positive/negative/regression commands and raw outcomes; environment/tool versions; optional skips and resource enforcement; preserved/lost information; unsupported claims; mathematical/implementation reviewer status; owner decisions still open. Recheck current branch/head before any separately authorized publication. Stop on unexplained oracle disagreement, compatibility drift or source/rights ambiguity.

No gates are closed by this local drafting work. No noisy/hardware/feedforward decoder, general QEC, performance advantage, native promotion, namespace migration or remote action is included.

## Owner decisions and next PR

Accept/reject ADR domain and criterion; approve legacy API/identity/pin preservation; select whether optional MSC/REC replay remains in scope; accept or revise the coherent-first WP2 milestone while retaining full buildmap G2 before WP3 implementation; require completed fresh WP0 verification and inventory/claim review. After explicit G0 acceptance, the **first proposed implementation-programme PR is draft A, WP1 contract documentation**, followed by draft B only after its contract review. External issue/PR creation requires separate authorization.
