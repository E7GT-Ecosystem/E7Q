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

This package is partially implemented through source/legacy preservation, bounded
native execution, external QCEC evidence and criterion-bound native/external
unitary-prefix comparison. H5 and Phase 2 remain incomplete.

Complete the remaining Phase 2 adapters, retaining original bytes, native IDs,
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

## H3 field-type consistency increment (2026-09-07)

Baseline: `29105bd4353e8d795dec6ae2f02962742c8df437`.
Malformed metadata status containers now produce a failed type check instead of
raising TypeError. Declared shot/outcome/gate counts and register widths require
integers, excluding booleans and floating-point lookalikes. Gate-count keys that
collide under case normalization are rejected rather than overwritten. This also
covers the optional legacy IR gate-count field.

Rehashed-manifest tests preserve integrity PASS while requiring consistency FAIL;
valid synthetic ZIP/directory fixtures remain compatible. The receipt schema and
identity rules are unchanged; an additional status-type check is emitted. Missing
or non-string status is now an error; unrecognized strings retain their prior
terminal-status warning. This intentionally tightens malformed-input admission.
Remaining H3 work includes ordering semantics, directory races and resource bounds;
this increment does not establish complete schema validation or authentication.

## H3 bounded directory inspection (2026-09-07)

Baseline: `3fc7188160903c95d9802b639653733c561acdb7`.
Directory inspection now traverses incrementally with a 1,024-entry budget
(including empty directories) and maximum directory depth 32. Existing 512-file,
32 MiB per-file and 128 MiB aggregate limits remain. Reads are bounded by the
remaining byte budget plus one detection byte; actual received bytes determine
the total and digests. Special files are rejected rather than silently ignored.

The reader checks opened file identity/type, observed size and modification time;
platform-supported no-follow/nonblocking flags reduce leaf replacement risks.
These checks do not create an atomic directory snapshot or protect every ancestor
replacement race. Use an immutable trusted-local snapshot when concurrent mutation
is in the threat model; full race-resistant traversal remains pending.

Tests cover empty-directory/depth budgets, FIFO rejection where available,
file/count/aggregate limits and growth between inspection and bounded read.
Canonical member digest ordering is unchanged and valid fixtures retain their
receipt meanings. Traversal beyond the new limits intentionally fails admission.
Next: explicit ordering semantics and remaining IR coverage; no complete security
or provider-authentication claim is added.

## H3 count-order preservation and consumer check (2026-09-07)

Baseline: `fce025491e685914958520b8c88bb2510be308df`.
The external-bundle producer accepts optional `raw_counts.json.label_order` with
`clbit-ascending` or `clbit-descending`. These describe left-to-right classical
bit index order in the admitted single-register profile. Values are retained
unchanged; the receipt adds `circuits[].counts.label_order`. Missing input is
recorded as null/unknown with a warning. Explicit invalid/null input fails.
A supplied declaration is not independent authentication of its convention.

Affected consumer: deterministic-reference assessment now rejects a receipt order
that conflicts with the reference, or an invalid non-null receipt order. Old
receipts lacking the field, and new receipts marked unknown, still require the
reference's explicit convention; this is a user-supplied assumption, not an
inferred or verified fact. Matching declarations use the existing canonicalization.
Future native/IR adapters must preserve this distinction and must not promote an
unknown order into F2-validated ordering without separate support.

This additive experimental receipt field preserves source digests, raw labels,
existing required fields and legacy readability. Rehashed manifests, unsupported
orders, unknown legacy order, conflict rejection and non-palindromic downstream
fixtures cover the compatibility gate. Ten new cases failed before implementation.
Next: Phase 2 native/legacy adapter contract, with remaining H2/H3 gaps tracked;
no full hardening completion or hardware provenance claim is made.


## Phase 2 preservation checkpoint (2026-09-07)

Baseline: `5c163aa3d72d0efc2724252b19696c8080aad79f`.
The [native/legacy preservation adapter](LEGACY_PRESERVATION.md) retains original
UTF-8 source bytes and exposes supported legacy JSON in a linked representation.
Original verdicts, IDs, proof, count order and limits remain supplied data.
This increment establishes structural preservation, not semantic validation:
F2 and typed native/compiler/execution mapping remain pending. H5 and Phase 2
are still open. Focused acceptance covers recovery, malformed/bounded input,
deterministic graphs, failed verdict retention and refusal to upgrade assurance.


## Phase 2 native execution checkpoint (2026-09-07)

Baseline: `e223603a634762c429dcc962f47e33fa26fa4a95`.
The [native execution adapter](NATIVE_EXECUTION.md) now constructs source, intent,
representation, execution, observation and assessment artifacts for a bounded
static statevector program. It retains original source, complete native proof
and verifier result, including FAIL, with explicit count ordering and projection
loss. Native APIs and formats are unchanged. F0/F1 structural checks do not confer
F2 semantics. Phase 2/H5 remain open pending compilation/typed legacy mapping and
criterion-bound native/external comparison.

## Optional QCEC evaluation inventory (2026-09-07)

Baseline: `4210bd595566af0f6458cac2c4870a6d98a3410e`.
The first optional-backend inventory pins MIT-licensed MQT QCEC 3.9.0 and records
its raw `equivalent`, `equivalent_up_to_global_phase`, `not_equivalent`,
probabilistic and `no_information` meanings without making it default F2 truth.
Callers select `e7q.ir.qcec-numerical-unitary` or
`e7q.ir.qcec-numerical-global-phase` version 1 explicitly. Both criteria retain
the configured numerical and fidelity tolerances. The adapter rejects E7Q-IR's exact-algebraic
signed-permutation criteria, so backend selection cannot weaken them.
Unsupported input, backend errors, probabilistic/per-state-phase/unknown outcomes
and timeout remain distinct from inequality and cannot become PASS.

Historical report `sha256:a19e91087e60359a57257e20ba0b171c70d74a40126a58bbb78eb9dd5218fece`
is explicitly invalid for its exact-algebraic claims because it labelled numerical
results with signed-permutation criterion identifiers. Its observations remain
preserved in the history record, while replacement report
`sha256:814c7d874c2b8856c6d28f392afb57ef6c8ff8b4e8b8b5755f40b32232de3b82`
uses only the numerical criterion identifiers.

The rerun seven-case 26/32-qubit corpus has report ID
`sha256:36b852c1e7cc9dc2479b63c9174e4add963d2731a4844b0d4fe5b3c3db154516`.
It records gate set, depth, gate count, backend and dependency versions,
configuration, numerical tolerances, isolated-worker wall time and peak RSS,
parent deadline enforcement, memory-limit enforcement state, worker exit/signal
and reaping evidence, and every non-PASS outcome. It produced six PASS, six FAIL
and two BLOCKED/INCONCLUSIVE criterion runs. Both forced controls were terminated
and reaped by the parent deadline and report `wall_clock_timeout`; they are not
backend inequality. POSIX `RLIMIT_AS` is applied when requested and supported,
with actual success/effective limit recorded. Native termination without an
explicit `MemoryError` remains a signal/crash rather than guessed exhaustion.
The full E5 ladder, repeated measurements and PyZX comparison remain pending.

This checkpoint does not complete H2/H3, E3, E5, Phase 2 or H5. Proof-of-Path
conversion, typed legacy receipt mapping and criterion-bound native/external
workflow comparison remain required.

## External QCEC pair evidence checkpoint (2026-09-08)

Baseline: `6454a26326ecfa1a654548e131910be2a1ef5be2`.
The new external pair workflow captures both supplied circuit files once, retains
recoverable base64 bytes, digests and stable caller references, and stores bounded
OpenQASM 2 parsed projections in separate representation artifacts. Successful
projections are evaluated from immutable temporary snapshots only through the
isolated QCEC worker. The workflow requires explicit criterion, numerical and
fidelity tolerances, wall-clock limit and memory limit.

The F1-valid graph links source → representation → assessment → bounded claim.
QCEC version/configuration, raw and normalized outcomes, runtime, worker lifecycle,
resource enforcement, assumptions and limitations remain inspectable. Unsupported
syntax does not start QCEC. Timeout, resource exhaustion, worker failure,
probabilistic/no-information/unknown verdicts and numerical inequality remain
non-PASS; exact-unitary requests do not inherit global-phase acceptance. Original
bytes recover only after envelope, size and digest checks.

Focused coverage includes identical, global-phase-only, altered, unsupported,
timeout, enforced-memory exhaustion, worker crash, deterministic request/source/
representation identities, exact recovery, inconclusive assurance isolation and
a structured 32-qubit fixture. The measured fixture graph is
`sha256:cac37f3d4d78b8ae0a9dc4bb084f9eac786a23680efe7e6b9447ea4deae187c4`:
PASS/`equivalent`, 0.38135 seconds, 40,460,288 bytes peak worker RSS, with Linux
`RLIMIT_AS` enforcement recorded. This is a single structured observation, not
a general scalability, exact-algebraic, default-F2, hardware or provider claim.

H5 and Phase 2 remain open because native/compiler/receipt mapping and actual
criterion-bound native-to-external comparison are still absent. E3 remains open
pending PyZX and broader backend evaluation; E5 remains open pending lower rungs,
unsupported/dynamic cases and repeated measurements. Historical evidence files
and verdicts are unchanged.

## Phase 2 native/external comparison checkpoint (2026-09-08)

Baseline: `95f8c8d15cc311753fe746b1c641a07e2453bea4`.
The bounded native/external workflow preserves one native `.e7q` input and one
external OpenQASM 2 input byte-for-byte, parses them independently and admits only
one-register static noiseless circuits with compatible widths, terminal identity
measurement and the supported X/Y/Z/H/S/T/CX/CZ/SWAP gate set. It constructs
separate unitary-prefix evaluation representations and explicit transformation
artifacts recording terminal-measurement removal, preserved gate order/operands,
lost classical/measurement information and the criterion boundary.

QCEC receives only immutable projections and runs through the isolated worker.
The assessment and claim retain the selected numerical criterion, tolerances,
backend/raw verdict, normalized result, resource enforcement and worker lifecycle.
Global-phase-only equality remains criterion-sensitive. Parser/admission failures,
timeout, exhaustion, worker crashes and all inconclusive verdicts remain non-PASS;
exact-algebraic criterion requests are rejected. The native local Proof-of-Path is
retained where an explicit seed permits deterministic execution, but it is not the
QCEC verdict or an F2 semantic result.

Regression coverage includes equivalent Bell, phase-only, altered, width/mapping,
dynamic control, noise/assertion, unsupported gate, timeout/crash, exact recovery,
deterministic identities, inconclusive isolation, exact-criterion rejection and
CLI paths. The public Bell graph is
`sha256:765272d4001adcca95743714f158ad44c62e4944a2705ca99667c2ac903433f1`.
It passes F0/F1; all applicable installed F2 checks run, while overall F2 remains
`BLOCKED` and projection relations remain `not-assessed` because no semantic
validator exists for this adapter contract.

This is partial H5/Phase 2 implementation, not completion. Typed compiler trace
conversion, legacy execution/receipt mapping, native/default F2 validators,
independent review, PyZX and the full repeated benchmark ladder remain pending.
No compiler provenance, provider authentication, hardware fidelity or arbitrary
scalability claim is added.
