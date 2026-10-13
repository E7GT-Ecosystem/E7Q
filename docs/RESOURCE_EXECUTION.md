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

## Reproduction and benchmark provenance

From a clean committed repository, install `.[test,simulation-test]`, then run:

```bash
python -m pytest -q
python scripts/benchmark_execution.py --baseline --output /tmp/baseline-new.json
python scripts/benchmark_execution.py --output /tmp/current-new.json
```

The runner refuses existing output files or a dirty checkout. `--baseline` loads
exactly the language module from the starting commit and admits only GHZ-12 full,
GHZ-12 individual and GHZ-14 individual measurement, at 8 shots/seed 42. It never
runs dense GHZ-25. Current mode reproduces those cases, GHZ-25 full/individual
stabilizer (1024 shots), opposite phase, a small density mixture, resource
refusals and non-Clifford refusal. Each row records original circuit bytes/hash,
commands, code-module hash, backend/shots/seed, versions, wall time and fresh-worker
peak RSS. Exact simulator checks and sampled observations are named separately.

Workers use one BLAS/OpenMP thread, a 30-second external timeout, and on Linux
RLIMIT_AS capped at the post-import virtual footprint plus 512 MiB (or any lower
inherited bound). This is a separate address-space limit, not an RSS budget.
Timeout and signal termination are supervisor observations with INCOMPLETE status,
no fabricated worker receipt/RSS, and no inferred confirmed OOM. Unexpected worker
errors are FAILED. Supplied third-party GHZ-25 observations remain explicitly
unreproduced, distinct from the new bounded measurements.

Versioned checked-in baseline/current artifacts will identify the exact clean
implementation/harness commits measured. Later documentation/result-only commits
need not be the measured code commit; compare the recorded module hashes.

## Recorded milestone result

Measured implementation/harness commit:
`e6f26e81a7a0313e429a58596d852eef74468877`. Starting implementation:
`ce9d969a3337ee76b894dae11e8e243ff09a7390`.
[Baseline artifact](../benchmarks/execution/baseline-20261013-v1.json) and
[current artifact](../benchmarks/execution/resource-clifford-20261013-v1.json)
include exact commands/hashes and fresh-process measurements on Linux x86_64,
Python 3.12.3, NumPy 2.5.4, Stim 1.16.0, Qiskit 2.5.2 and jsonschema 4.26.0.

| Synthetic case | Shots | Baseline seconds | Current seconds | Current peak RSS |
|---|---:|---:|---:|---:|
| GHZ-12 dense/full measurement | 8 | 0.113184 | 0.015129 | 39.15 MiB |
| GHZ-12 dense/individual measurement | 8 | 1.104536 | 0.022725 | 38.37 MiB |
| GHZ-14 dense/individual measurement | 8 | 5.319354 | 0.036948 | 39.40 MiB |
| GHZ-25 stabilizer/full measurement | 1024 | not run | 0.118530 | 42.88 MiB |
| GHZ-25 stabilizer/individual measurement | 1024 | not run | 0.156816 | 42.86 MiB |

GHZ-25 used a declared 128 MiB budget. Working estimates were 64.94/64.99 MiB,
**not** the measured 42.88/42.86 MiB RSS. Both runs passed 50 exact Pauli checks:
X⊗25=+1, all 24 neighboring ZZ=+1, and all 25 single Z=0. Normalization is a
separate tableau-construction check. Counts are finite-shot observations.

Opposite-phase GHZ-25 completed but failed the requested +1 coherence check
(X⊗25=-1), while correlations/balance remained correct. The small incoherent
mixture completed and passed trace normalization; its separately assessed GHZ
coherence failed (XXX=0) although ZZI=+1. Its native verification PASS is **not**
a GHZ-property PASS; `ghz_property_status: FAIL` and scoped checks preserve this
distinction. Over-budget dense/density GHZ-25 were refused before state allocation;
T was UNSUPPORTED. No uncontrolled memory-exhaustion test was run.

One timed observation per synthetic case is recorded, not a statistical
performance distribution or independent performance audit. Improvements are
attributed to bounded NumPy kernels/preparation reuse or the selected Stim backend.
They are not arbitrary-width guarantees, hardware superiority or quantum advantage.

Final implementation regression at the measured commit: `python -m pytest -q`,
**672 passed in 57.00 s**, with optional independent-reference/schema extras
installed. Core usability without Stim was checked by a subprocess blocking its
import. QCEC/PyZX were not requalified, and no hardware/provider/live/production
validation or broader release/security/physics gate is closed by these results.
All seven software milestone acceptance criteria are met by this bounded evidence;
external review/merge and broader release qualification remain separate.
