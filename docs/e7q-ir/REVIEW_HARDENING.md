# Review-driven hardening programme

Plan revision 0.3, 2026-09-06. Baseline: `c1608b11464b5a5b0a45f221907a8c27b1bb51ff`.
All packages below are **PROPOSED**, not completed by publishing this document.
They refine the [build plan](BUILD_PLAN.md), including research packages R1–R6.

## Evidence basis and interpretation

The user supplied a white-box report, a quality opinion and an Aer comparison.
Treat the opinions as planning input, not an independent certification or a
comparative benchmark. The white-box report names a commit family, reports 32
checks, and provides 25 grouped PASS log lines. Grouping may explain that count;
an assertion-level manifest is needed to resolve it. A full executable harness,
exact environment and complete commit identifier are needed for reproduction.
Do not label its results independently reproduced by this project yet.

The campaign explicitly omitted E7Q-IR and external-bundle execution; supporting
modules were inspected structurally. Repository tests already exist for these
areas. Missing campaign coverage is not proof of missing implementation, tests,
or a defect. A claim that every proof step includes trace/purity also needs
field-level reconciliation: the terminal project record does not supply those
fields. Preserve reported findings separately from reproduced observations.

No external harness delivery is a prerequisite for internal hardening. Build
local reproducible cases with their own provenance; do not attribute those cases
to the reviewer. No report text or third-party code needs to be vendored here.

## Work packages and acceptance gates

### H1 — Review reproduction (P0; begins now, maintained through Phase 8)

Deliver an executable review runner and assertion manifest with exact repository
SHA, Python/dependency versions, seeds, commands, fixture identities, expected
results, tolerances and machine-readable actual results. Distinguish reported,
internally reproduced and independently reproduced findings.

Gate: a clean environment reproduces the local campaign; every grouped report
line maps to assertions or an explicit unresolved item. Reproducing the original
third-party campaign remains pending until its missing materials are available.

### H2 — Adversarial IR semantics (P0; Phase 1 regression gate)

Audit existing IR suites before adding cases. Cover payload tampering after
rehashing, dangling and contradictory evidence, unsupported criteria/profiles,
digest-only versus byte-dependent checks, incorrect preservation/loss claims,
register mapping and resource boundaries. Include a valid end-to-end F2 graph.

Gate: content/referential validity cannot conceal semantic failure; each expected
PASS, FAIL, BLOCKED, UNSUPPORTED or NOT_ASSESSED has a criterion and evidence
reference. Do not collapse states or change existing F0/F1 meanings.

### H3 — Bundle safety and interpretation (P0; Phase 2 prerequisite)

Extend `tests/test_external_bundles.py` where its existing coverage leaves gaps.
Exercise path traversal, absolute paths, symlink entries, duplicate members,
decompression/member/total-size limits, manifest discrepancies and invalid JSON.
Check shot totals, non-finite values, count widths and explicit bit/register order.

Gate: unsafe archives cannot write outside the destination or exceed declared
budgets; ambiguous results cannot silently acquire an interpretation. Digests
establish content identity, not authenticated provenance. Valid legacy fixtures
continue to import. No supplied source or archive content is executed.

### H4 — Capability-to-evidence matrix (P0; continuous)

Create a versioned matrix: public capability/claim, module, supported domain,
criterion, fixture/test IDs, exact tested revision, internal/external review
status, exclusions and next gate. Reconcile docs against code, including the
field-level Proof-of-Path description. Separate historical checkpoints from
current status. Existing test counts alone cannot complete this package.

Gate: every advertised capability has evidence or an explicit proposed/unsupported
label; adapters and semantic validators have distinct entries. Assign a builder
in each implementation PR and update affected rows with each capability change.

### H5 — Native/legacy evidence continuity (P1; Phase 2)

Implement the existing Phase 2 adapters, retaining original bytes, native IDs,
source references, compiler traces, execution settings and assessment boundaries.
Describe omitted/derived fields and irreversible losses; do not fabricate values.

Gate: native Bell and external OpenQASM workflows retain inspectable evidence
paths, pass applicable F0/F1/F2 checks and preserve legacy readability. Supported
round trips retain identity or explicitly report why identity is not preserved.

### H6 — Optional Aer reference integration (P1; Phase 2, after H2/H3)

Provide an optional producer adapter and pinned offline fixtures, keeping the
core dependency set independent of Aer. Capture source and compiled circuits,
compiler settings, simulator method, software versions, noise configuration,
seeds, shots, original results and explicit qubit/classical-register mappings.
Record missing metadata as unknown. Review upstream API and licensing at the
implementation checkpoint before pinning versions or adopting fixtures.

Gate: one ideal and one noisy external workflow enter IR without requiring native
E7Q syntax or a live provider job. Use non-palindromic outcomes to expose ordering
errors. Available checks produce scoped verdicts; unsupported noisy equivalence
remains unsupported. Importing large outputs must not allocate a full state or
expand the small-circuit equivalence domain. No hardware-authentication claim.

### H7 — Supporting-module campaigns (P1; Phases 2 and 6)

Audit and extend drift, temporal, assessment, calibration ingestion/selection and
resource-planning tests. Add public CLI/API workflows with realistic synthetic
replication fixtures, stale calibration, missing clocks, conflicting observations,
incomparable runs and inadequate evidence. Label synthetic data explicitly.

Gate: results preserve conflicts, null outcomes and uncertainty; absent temporal
support cannot imply chronology or stability. Analysis replay, simulator rerun
and independent replication remain distinct. F4 is still a separate Phase 6 gate.

### H8 — Independent mathematical checks (P1; continuous)

Use analytical fixtures and a pinned external implementation on the overlapping
supported domain. Cover gate/channel invariants, phase versus measurement
criteria, bit order, parameter boundaries and deliberate non-equivalence.
Keep external reference generation optional; preserve fixture provenance.

Gate: comparisons name their domain, criterion and numerical tolerance. Sampled
comparisons declare shots, statistical method and error assumptions; equal seeds
across different engines need not produce equal counts. Retain checker conflicts
and prevent a combined proof claim until resolved. Agreement is not a formal
proof or a hardware result.

### H9 — Dynamic noisy semantics (P2; after Phase 2, coordinated with Phase 3)

Write a bounded extension contract before implementation: branch probabilities,
measurement collapse, classical state/feed-forward, conditional channels,
normalisation, trace accounting, aggregation and resource limits. Native runtime
support and IR/OpenQASM support require separate capability declarations.

Gate: analytical branch fixtures and independent comparisons cover admitted
measurement/noise/control combinations. Unsupported combinations fail closed;
terminal-only legacy behaviour remains valid. No general dynamic/noisy support
claim follows from one admitted subset.

### H10 — Operational and release gates (P2; continuous, final Phase 8 gate)

Measure time and peak memory under a recorded environment and representative
input families. Enforce inspection and execution budgets separately. Verify clean
installation, supported Python versions, CLI examples, artifact compatibility,
dependency/license notices and reproducible release contents.

Gate: documented limits match measured/enforced behaviour; invalid or oversized
inputs fail predictably. Release evidence identifies passed, skipped and blocked
checks. Experimental, internally tested and independently exercised are distinct
statuses; no performance comparison or production-readiness claim without its
own measurements and criteria.

## Extension contract and sequence

Every package that changes behaviour declares source/carrier, context/inquiry,
representation and transformation, preservation/loss, assumptions, versioned
criterion, temporal support, resource limits, evidence output and maximum claim.
Reuse existing contracts; new schemas require consumer and migration review.
Informative E7G-T pilots do not become established domain semantics by adoption.

Sequence: H1/H4 reconciliation → H2/H3 hardening → H5/H6 adapters → H7 campaigns.
H8 accompanies semantic changes; H10 accompanies releases. H9 follows its explicit
semantic gate. Broader Phase 3–8 dependencies remain intact. Each implementation
PR records exact baseline, builder, scope, acceptance results and remaining gaps.

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
