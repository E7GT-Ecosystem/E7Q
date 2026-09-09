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

### H5 — Native/legacy evidence continuity (P1; Phase 2) — COMPLETE

Source/legacy preservation, bounded native execution, external QCEC evidence,
criterion-bound native/external unitary-prefix comparison, typed topology-compiler
Proof-of-Path conversion and offline legacy execution receipt mapping are linked by
inspectable evidence paths. The distinct `e7q.ir.native-execution/0alpha1` profile
now supplies the remaining installed native/default F2 semantic reconstruction.

The validator retains and checks original source bytes, native IDs, source
references, execution settings, complete native Proof-of-Path, observation and
assessment boundaries. Parser projection loss remains explicit. Historical core-
profile graphs and legacy formats remain readable at F0/F1 and are neither
rewritten nor retrospectively promoted.

Gate satisfied: the public native Bell workflow reaches F2 through independent
reparse/readmission/reference replay/native verification; external OpenQASM,
compiler and legacy receipt workflows retain their bounded inspectable paths;
supported round trips retain identity or declare loss; and imported verdicts,
compiler traces and optional QCEC results cannot become default native F2 truth.
A faithfully recomputed native invariant FAIL may pass semantic conformance while
remaining a FAIL program verdict.

H1/H2/H3/H6/H8, E3/E5, provider authentication, OpenQASM 3, QIR and K12/CFS
remain separate open packages. H5 completion establishes no hardware execution,
fidelity, provider identity, chronology, external-circuit equivalence, scalability
or computational advantage.

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

Native F2 bounded increment (2026-09-08): parser expansion is now stopped before
operation/path/statement lists exceed the installed policy, including compact
acyclic fan-out and use-only/deep nesting cases. Validator replay is isolated in
a spawned worker with a parent deadline, bounded terminate/kill/reap cleanup and
POSIX `RLIMIT_AS`; unsupported enforcement, exhaustion, timeout, signal, crash and
protocol outcomes remain distinct and non-PASS. Runtime enforcement evidence is
attached to semantic results, and cache keys include policy/implementation identity.
This closes the audited native-replay gap only; representative-family measurement,
clean-install/release compatibility and the complete H10 gate remain open.

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


## H2/H3 declaration and field-shape increment (2026-09-08)

Baseline: `9365105a4490ce5e52b879ef708d15f2f6ce9bde`.
Rehashed transformation artifacts and relations can no longer declare the same
property as both preserved and lost, or repeat preservation, loss or assumption
entries. These contradictions now fail F0 before an installed validator can lend
them semantic credibility; existing F0/F1/F2 meanings and artifact identities are
unchanged for valid graphs.

External bundle ingestion now type-checks circuit names, circuit depths, creation
and completion timestamps, and initial/final index layouts. Every supplied
completion alias is validated and mutually consistent; malformed or conflicting
aliases cannot be hidden behind one valid field. Index layouts require unique,
non-negative in-range integer indices. Rehashed manifests therefore preserve
content-integrity PASS while malformed interpretation fields force consistency
FAIL. Valid synthetic directory and ZIP fixtures remain compatible.

Focused H2/H3 verification passes 82 tests; the full suite and repository campaign
pass 577 cases with zero skips or collection errors. This is another bounded
increment, not completion of either package. Remaining work includes assertion-
level adversarial coverage, broader calibration/IR field semantics, ancestor
directory races,
provider authentication and independent external reproduction.


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
The later repeated E5 checkpoint completes the ladder; PyZX comparison remains
pending under E3.

This checkpoint does not complete H2/H3, E3, E5, Phase 2 or H5. Proof-of-Path
conversion, typed legacy receipt mapping and criterion-bound native/external
workflow comparison remain required.

## Repeated E5 equivalence benchmark checkpoint (2026-09-09)

Baseline: `34387b069763911fd41f310ef6e63310402b07f9` (PR #64).
The `e7q.ir.qcec-benchmark/v2` corpus contains 31 cases and 174 isolated
criterion attempts over 4/8/12/16/20/26/32 qubits. Four supported families at
every rung are repeated three times under both numerical exact and numerical
global-phase criteria. Unsupported dynamic/noise inputs and a forced deadline
control are retained once per criterion.

The report records 105 PASS, 63 FAIL, 4 UNSUPPORTED and 2 BLOCKED outcomes.
All 174 match their preregistered case/criterion expectation. Each record
retains backend versions, tolerances, seed, deadline, memory policy, runtime,
worker peak RSS, exit/reaping state, raw result and evidence identity. The
manifest/corpus identity is separate from the observation-bearing report
identity so repeated measurements are not misrepresented as byte-identical
performance results. All 168 decisive workers enforced the requested 2 GiB
POSIX address-space bound; all 174 workers were reaped. Recorded decisive wall
time was 0.124–0.213 seconds (median 0.149), with 32,567,296–83,263,488 bytes
worker peak RSS.

This completes E5 for this pinned structured corpus and supplies the
representative-family portion of H10. It does not establish arbitrary-circuit
scalability, exact-algebraic equivalence, default F2 conformance, hardware
execution or fidelity. PyZX/E3, release-wide compatibility, H2/H3 and
independent H1/H8 review remain open.

## Optional PyZX E3 checkpoint (2026-09-09)

Baseline: `61bc936c15869a4eb3f64dfb3b34564a01f3f565` (PR #65).
The optional Apache-2.0 PyZX 0.10.6 adapter supplies a second bounded E3
evaluation backend. Callers must select either
`e7q.ir.pyzx-rewrite-unitary` or
`e7q.ir.pyzx-rewrite-global-phase`; input/output swaps are disabled and these
criteria remain distinct from QCEC's tolerance-bearing criteria and E7Q's
exact-algebraic signed-permutation criteria.

E7Q performs bounded OpenQASM 2 admission before starting PyZX. The admitted
domain has one equally wide quantum/classical register pair per circuit, equal
width across the pair, at most 64 qubits and 2,048 static noiseless gates, and
terminal identity measurement that is explicitly projected away. Each check
runs in a spawned worker with a parent deadline and a recorded POSIX address-
space policy. Projection SHA-256 identities, backend version, resource use,
worker lifecycle, raw outcome and selected criterion remain in the assessment.

PyZX reduction success can PASS only the selected rewrite criterion. False,
absent or unsuccessful reduction is always NOT_ASSESSED/INCONCLUSIVE and never
proves non-equivalence. Timeout and memory exhaustion are BLOCKED; rejected
input is UNSUPPORTED; crashes, signals, protocol failures and other backend
errors remain non-PASS.

The four-case 26-qubit public corpus exercises a SWAP/CX rewrite, global-phase
separation, an altered-gate non-reduction and forced timeout under both
criteria. Its eight attempts record three PASS, three NOT_ASSESSED and two
BLOCKED outcomes, all matching their preregistered expectations and with every
worker reaped. Its report ID is
`sha256:22a2349b04a7cb75a21cd5f43cb3574be9bd84acf0b59abe14fe56ca0b19d561`.
This completes E3 only for the pinned bounded evaluation. It
does not establish arbitrary scalability, negative equivalence, default F2,
provider authenticity, hardware execution or physical fidelity. Release-wide
H10, H2/H3 and independent H1/H8 review remain open.

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

This is partial H5/Phase 2 implementation, not completion. Offline legacy
execution/receipt mapping is now implemented; native/default F2 validators,
independent review, PyZX and the full repeated benchmark ladder remain pending.
No provider authentication, hardware fidelity or arbitrary scalability claim is
added.

## Typed topology compiler Proof-of-Path checkpoint (2026-09-08)

Baseline: `89531ebe1b01d8268d8756227ddaa77ce7096ee5`.
The additive compiler workflow adapts the existing `compile_topology()` and
`compilation_result()` implementation without changing or duplicating compiler
behavior. It preserves the native source bytes, parsed program and complete
original compiler Proof-of-Path, then converts every step into typed ordered
E7Q-IR evidence covering the initial context, source operation index, logical
operands, selected physical path, forward/reverse SWAPs, restored-layout
assertions, final counts and routing overhead.

The declared compilation request records coupling edges, logical width, native
gate set, compiler implementation/version, selected program/path, numerical
criterion, tolerances and resource limits. Source and compiled representations
have independent content identities and explicit terminal-measurement projection
boundaries. The compiler preservation declaration states that it is not semantic
equivalence. A separate isolated QCEC assessment must PASS the requested numerical
criterion before the bounded compiler-preservation claim can be supported.

The local consistency validator reparses the preserved source and deterministically
recompiles it, checking the complete proof, typed trace, compiled representation,
projection, criterion and claim. Recomputed-identity tampering of either compiled
content or trace therefore fails. This validator is not registered as default F2
truth: F0/F1 pass for the public graph, while all 19 applicable F2 checks run and
overall F2 remains `BLOCKED`.

Regression coverage includes adjacent/no-routing, non-adjacent and multiple routes,
forward/reverse SWAP order, disconnected graphs, missing SWAP/native gate support,
invalid/duplicate edges, trace and representation tampering, QCEC inequality,
timeout, exhaustion, worker crash, deterministic identities, exact source/proof
recovery, inconclusive isolation and exact-criterion rejection. The public evidence
graph is
`sha256:17265fa58a1a46f47db36ba800ca5613e374fd3dd6a687c1dde832c5c74a5827`.
It records four inserted SWAPs, restored logical layout, QCEC 3.9.0
`equivalent`/PASS, 0.38756 seconds wall time, 59,174,912 bytes peak worker RSS,
enforced parent deadline/POSIX `RLIMIT_AS` and a reaped zero-exit worker.

Phase 2/H5 remain open for native/default F2 semantic validation. No hardware
feasibility, topology quality, physical fidelity, provider authentication,
execution success, exact-algebraic or arbitrary-scalability claim is added.
K12/CFS implementation remains unstarted.

## Typed legacy execution receipt checkpoint (2026-09-08)

Baseline: `538ac31e064ebddebb43f441ef316f0551581863` (PR #60).
The additive workflow maps the existing legacy execution bundle, supplied result
and supplied receipt without changing their schemas or creating a second receipt
engine. It preserves all three source byte streams independently and retains the
complete original object, status, Proof-of-Path, unknown fields and limitations in
typed representations.

Intent, supplied execution, observation, assessment and claim remain separate.
Provider/job/time values are unauthenticated declarations. The count observation
records explicit label order, width, deterministic outcome sequence, zero-count
outcomes and empirical probabilities without treating them as execution or fidelity
evidence. Four typed transformation records provide deterministic identities,
input/output references, criteria, preservation, loss, assumptions and validation
status.

The workflow strictly reparses the preserved bytes and invokes the existing
`build_execution_receipt()` implementation. Thirty-six explicit checks cover
schemas, registered structures, bundle readiness, source/OpenQASM/compiled
identities, target, shots, bundle linkage, count validity, probabilities and every
receipt proof field. Imported PASS, digests, proof and optional pilot records are
compared rather than trusted. Duplicate keys, non-finite values, unknown schemas,
unsupported count semantics, malformed outcomes, linkage mismatches, forged PASS,
tampering and imported non-PASS statuses remain non-PASS.

Regression coverage includes byte-perfect recovery, deterministic graph/artifact/
relation/transformation identities, extra and zero-count outcomes, target/shot/
digest mismatches, malformed/rehashed evidence, forged PASS, probability/proof
tampering, status retention, optional temporal/observational records, CLI overwrite
protection and the default F2 boundary. The public graph ID is
`sha256:2461fac5f5a9c5472280b9ae1daf2789167851d91f3a40df8ec388c22f3fff29`.
F0/F1 pass; 25 installed semantic checks run and F2 remains `BLOCKED` because no
legacy-receipt validator is registered as default semantic truth.

At this checkpoint the offline legacy receipt mapping increment was complete,
while native/default F2 still blocked Phase 2/H5. The subsequent native checkpoint
below closes that blocker. The receipt workflow itself still establishes no
submission, execution authenticity, provider identity, chronology, physical
fidelity, circuit correctness, computational advantage, F3 authentication or
arbitrary scalability. Provider integration, authenticated execution and K12/CFS
implementation remain unstarted.

## Installed native/default F2 checkpoint (2026-09-08)

Baseline: `1a0a24b3d41f79bfa6a200006e4bf08761b39f52` (PR #61).
`e7q.ir.native-execution/0alpha1` is a distinct installed profile; no validator is
registered for `e7q.ir.core/0alpha1`. Newly generated native graphs use the native
profile on all six artifacts and five relations. Historical core-profile native
graphs and generic legacy/core artifacts remain F1-only and retain their original
identities.

The validator verifies source bytes, length and digest, reparses the preserved E7Q,
reapplies the bounded admission contract before allocation, executes the existing
seeded statevector reference backend, calls the existing native verifier and
compares every intent, expanded operation, backend declaration, implementation
version, Proof-of-Path, count, probability, assessment, provenance and relation
field. It reuses `parse()`, `run()`, `verify()` and `backend_profile()` and requires
no QCEC dependency.

Adversarial tests rehash otherwise valid graphs after source, intent,
representation, execution, observation, assessment, provenance and transformation
tampering. Unknown format, noisy/dynamic/unseeded/excessive programs, validator
exceptions, malformed contracts and missing results remain non-PASS. Native
invariant failure remains separate: a faithfully recorded and recomputed native
FAIL can pass F2 conformance without becoming successful execution or a scientific
claim.

The public Bell graph ID is
`sha256:c9fe173151778dcae3df500674a53c063c32119c6b600bfe40c0b82f00e59598`.
Its deterministic F2 report contains 17 PASS semantic checks. Focused verification
passes 80 tests, the integrated IR/native/compiler/QCEC/receipt surface passes 250
and the full suite passes 567. This satisfies H5 and Phase 2 because all continuity
paths remain inspectable, applicable conformance
checks fail closed, preservation/loss is explicit and imported verdicts cannot
become native/default F2 truth. H1/H2/H3/H6/H8, E3/E5, authentication, broader
interoperability and K12/CFS remain separate open gates.
