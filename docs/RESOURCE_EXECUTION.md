# Resource-aware native execution

Starting main: `ce9d969a3337ee76b894dae11e8e243ff09a7390` (2026-10-13).
This milestone retains native quantum semantics, bit order and existing IR
identities/criteria. It adapts dense execution and adds optional compact Clifford
simulation; it neither migrates existing evidence nor changes equivalence budgets.
New conceptual guidance uses E7G-T v0.15/MSC1 at
`2cba2045bb22036ce489083a5ac853a9d867eb21`. Downstream architecture guidance
still pins v0.12.1-experimental/RGP2 (`fc4cdf95c6434e653efbe017587aab60b4b2a86c`),
with the legacy v0.11-UC5 compatibility reference. No pin migration or v0.15
conformance is claimed. Formal construction coefficients are not amplitudes.

## Allocation preflight

`run(program, policy=ExecutionPolicy(...))`, `compare(..., policy=...)`,
`circuit_unitary` and `channel_superoperator` check resource requirements before
state/matrix allocation. CLI run/verify/compare accept `--memory-budget-bytes`.
The default is **256 MiB**, including a declared **64 MiB runtime allowance**.
These are conservative estimates, not measured peak RSS or hard sandbox limits.

complex128 statevector storage is `16 * 2**n` bytes, density/unitary storage is
`16 * 4**n`, and superoperator storage is `16 * 16**n`. Working estimates include
multiple live states/matrices, gate/measurement/comparison temporaries, sample
arrays and worst-case exact-support probability dictionaries. Dense widths above
30 are refused without constructing huge powers/arrays. Program width/bits,
shots and operation count also have finite admission limits (4096, 4096,
1,000,000 and 100,000 respectively).

When available, Linux MemAvailable, cgroup-v2 ancestor memory headroom and POSIX
RLIMIT_AS address-space headroom reduce the usable budget to the minimum of the
configured budget and half of reported headroom. Missing/ambiguous signals are
omitted. These observations are racy and do not enforce a process limit. API
callers may explicitly disable host observations for deterministic tests; the CLI
respects them. The `e7q.resource-preflight/1` assessment records the calculation.

Over-budget API calls raise `ResourceBlocked` with the assessment; catchable
simulation/comparison `MemoryError` becomes `AllocationFailed`. CLI writes a
versioned `e7q.execution-outcome/1` failure result and exits 3. Such results have
`verification_status: NOT_ASSESSED`, never a successful empty check list.
Structural validation and planning are separate from execution completion.
A killed process cannot emit its own final receipt. A supervisor must record
missing completion, timeout or signal externally; signal 9 is not confirmed OOM.
Preflight does not guarantee survival under every interruption or native failure.

## Dense sampling and evidence

Full-register sampling draws integer basis indices and counts observed indices
once; only supported exact probabilities and observed count labels are formatted.
Support discovery uses bounded chunks rather than a full-basis string/index list.
Exact probabilities are not replaced by sampled frequencies. Seeded categorical
draw order is retained. Dynamic probabilities retain their existing finite-shot
meaning; a final collapsed state is not the premeasurement ensemble.

Neither correlated Z counts nor measuring one bit proves GHZ coherence. A
phase-sensitive check is required. Simulation is not hardware fidelity,
provider authenticity, quantum advantage or all-input circuit equivalence.
QCEC/PyZX assessments and the eight-qubit signed-permutation criterion remain
separate; raising that cap does not admit H or solve GHZ execution.

## Optional Clifford backend

Install `pip install -e '.[stabilizer]'` and explicitly declare
`backend: stabilizer` in the native context (or replace the Program backend in
Python). Core imports and dense execution require no Stim installation. The
admitted optional version is **Stim 1.16.0** (`stim.TableauSimulator`), pinned in
the extra and recorded in every compact result; other versions fail closed.

Supported: X/Y/Z/H/S/CX/CZ/SWAP, initial |0…0> (X prepares other computational
basis states), Z measurement, native q0/c0-leftmost order, bit mapping and
mid-circuit one-bit equality feed-forward. The parser supports conditional
one-qubit gates; direct Program callers may condition admitted two-qubit gates
as well. Classical assertions assess executed shots, not all possible branches.
T, noise/mixed states, unknown operations and implicit dense fallback are refused.
Shots remain finite and resource-preflighted. No runtime deadline is implied by
polynomial tableau storage; long shot/operation streams may still take time.

For an unconditional Clifford preparation followed only by terminal measurements,
`verify(execution, pauli_checks=[{'pauli': 'XXX', 'expected': 1}])` evaluates the
**premeasurement** state exactly, without expanding it. Requests admit full-width
I/X/Y/Z strings and expected -1/0/+1, with at most 64 checks. CLI accepts repeated
`--pauli-check XXX=1` options. These are simulator expectations, not shot estimates.
For GHZ-n, check each neighboring ZZ expectation (+1), each single Z expectation
(0, balanced marginals), and X⊗n (+1). The single-Z checks distinguish an all-zero
product state, which also has perfect ZZ correlations. Opposite-phase GHZ has
ZZ=+1 but X⊗n=-1. The equal incoherent 0…0/1…1 mixture has ZZ=+1 and X⊗n=0;
the density backend and an independent small Qiskit reference exercise that
negative control. Mixed states are not silently admitted as pure stabilizer states.

Expectations after genuine mid-circuit measurement/conditional control are
**unsupported**: a final shot branch is not the ensemble. Exact classical output
support (`invariant outcomes`) is also unsupported on this backend; counts are
not substituted for that exact check. Unsupported requests produce
`NOT_ASSESSED` with individual `UNSUPPORTED` checks. No requested checks likewise
produce `NOT_ASSESSED`, not a vacuous property PASS. Failed supported checks produce
FAIL even when simulation itself COMPLETED.

`e7q.stabilizer-result/1` serializes counts, explicitly finite-shot
`sample_frequencies`, null exhaustive probabilities, compact final-shot stabilizer
generators, resource estimates, capability/dependency identity and check scope.
It does not materialize a statevector or exhaustive probability dictionary.
Both new result formats have additive JSON schemas; existing native graph/IR
profiles, identities, seeded dense outcomes and comparison budgets are retained.
The installed eight-qubit native F2 replay profile is not expanded to admit this
new backend or promote these compact results automatically to F2.

Stim seeds are repeatable only for the same version, calls and compatible machine
SIMD behavior; there is no promise that Stim counts match dense counts for the same
seed. Compare exact small-state properties or properly scoped distributions,
not cross-backend sample identity. Test extras: `.[test,simulation-test]`.
