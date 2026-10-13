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
