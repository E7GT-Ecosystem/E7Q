# Circuit-equivalence direction

**Status:** planned, evidence-bounded development track  
**Decision date:** 2026-09-07  
**Inspected baseline:** `ea0eeec3e379888bb383ebd4afd72887f5efbcf6`

## Why this track exists

External technical discussion of the bounded real-H criterion surfaced two
separate questions: which equivalence relation a caller needs, and how E7Q-IR
can move beyond a small exact reference calculation. Those comments are design
input, not validation evidence. Progress is established only by implemented
contracts, reproducible fixtures, test results, and declared resource bounds.

This track refines
[R1 — Bounded verification and an external circuit corpus](BUILD_PLAN.md).
It does not create a parallel equivalence subsystem or weaken the current
H2/H3 and Phase 2 gates.

## Product decision

E7Q-IR will treat exact unitary equality and equality up to one global phase as
different, versioned criteria. A caller must declare the relation required for
the intended use. Reports must retain the outcome of every criterion actually
run and must not collapse them into an unqualified `equivalent: true` result.

The minimum decision table is:

| Exact criterion | Global-phase criterion | Admissible conclusion |
| --- | --- | --- |
| `PASS` | `PASS` | Exact equality is established in the common admitted domain. |
| `FAIL` | `PASS` | Equality only up to global phase is established; exact replacement is not supported. |
| `FAIL` | `FAIL` | The tested relation is unequal in the admitted domain. |
| non-PASS | non-PASS | Preserve `BLOCKED`, `UNSUPPORTED`, or `NOT_ASSESSED`; do not infer inequality. |

An exact result may support a global-phase conclusion only through an explicit,
named derivation rule or a separately executed applicable criterion. A
global-phase result never upgrades exact equality. Measurement behaviour,
channel equality, tolerance-based agreement, and dynamic/noisy semantics remain
separate relations.

## Reference-oracle boundary

The existing exact real-H/u2 criterion remains the deterministic reference
oracle for its current domain: the documented gate set, at most four qubits,
at most 64 expanded gates, one quantum and one classical register, and complete
terminal measurement. Its exact arithmetic is valuable precisely because its
scope is narrow and auditable.

The four-qubit bound is not a product scalability target. Raising that bound by
allocating larger dense matrices is not an accepted implementation path.

## Work packages

### E1 — Dual-relation request and report contract

- Define how a caller selects the required relation without changing the
  meanings of existing criterion identifiers.
- Emit separate exact and global-phase semantic results, with their own status,
  evidence, boundaries, method, and resource use.
- Make aggregate support depend on the caller's declared relation.
- Preserve checker disagreement and every non-PASS state.
- Keep the change additive within `v0alpha1`; old reports are not
  retrospectively upgraded.

Acceptance:

- exact PASS / phase PASS, exact FAIL / phase PASS, both FAIL, unsupported,
  blocked, and not-assessed fixtures;
- deterministic result identities and ordering;
- no unqualified binary equivalence field;
- F0/F1 and existing criterion behaviour remain compatible.

### E2 — Bounded real-H global-phase criterion

- Add a global-phase criterion over the same admitted real-H/u2 domain as the
  exact reference oracle.
- Check phase-sensitive counterexamples, including cases differing only by
  overall sign.
- Require identical register and terminal-measurement maps where the criterion
  contract requires them.
- Cross-check the bounded implementation against an independent test oracle;
  the oracle is regression evidence, not the source of the F2 verdict.

Acceptance:

- a phase-only pair fails exact equality and passes global-phase equality;
- non-global relative phase fails both;
- domain and resource violations remain distinct from semantic failure;
- the existing four-qubit/64-gate bounds remain explicit.

### E3 — Optional structure-aware backends

Evaluate MQT QCEC first and PyZX second as optional adapters. Any adopted backend
must be pinned and record:

- criterion and supported circuit fragment;
- input/output permutations and phase convention;
- tool and dependency versions;
- raw verdict, method, assumptions, elapsed time, memory/resource budget, and
  timeout;
- deterministic mapping of equivalent, non-equivalent, inconclusive, timeout,
  unsupported, and internal-error outcomes into existing E7Q-IR states.

An unsuccessful reduction, timeout, or backend error is not non-equivalence.
Backend choice must not change criterion meaning. No external backend becomes a
mandatory dependency of the Evidence Core.

### E4 — Compositional compiler evidence

Prefer local, structure-aware evidence where a compiler transformation exposes
it. Record transformation steps, affected qubits/cones, declared invariants,
preservation/loss, and optional proof or certificate artifacts. Composition may
support a whole-circuit claim only under a named rule whose assumptions are
checked. A compiler assertion by itself is not an F2 proof.

### E5 — Scalability benchmark ladder

Publish a reproducible ladder at 4, 8, 12, 16, 20, and 25+ qubits using
structured compiler-generated equivalent pairs, phase-only pairs, altered-gate
non-equivalent pairs, permutations, unsupported dynamic/noisy cases, and
resource-exhaustion cases.

For every case record circuit family, depth/gate count, relation, backend,
version, configuration, status, runtime, memory or declared proxy, and evidence
identity. Report completion rate and non-PASS reasons; do not report only
successful cases.

The 25+ qubit rung is an evaluation gate for supported structured instances, not
a promise that arbitrary 25-qubit circuit equivalence is tractable. No
scalability claim is allowed until the pinned corpus and resource results are
published and reproducible.

## Compatibility, preservation, and loss

Affected consumers include F2 conformance reports, transformation relations,
the CLI, Proof-of-Path exports, native/compiler adapters, and optional external
verification workflows.

The first contract change must be additive. It preserves existing criterion
identifiers, artifact identities, F0/F1 meanings, source/executable separation,
terminal measurement maps, and non-PASS states. A reduced or quotient relation
must declare the information it intentionally loses, including global phase
where applicable. Existing reports remain readable and retain their original
meaning; no migration may reinterpret an earlier PASS as a stronger result.

## Public progress and accountability

Progress posts may use AI-assisted drafting, but a named project contributor is
responsible for the published claims. Every technical progress claim should
link to an inspectable commit or pull request, the exact tests run, skipped or
unsupported cases, current bounds, and the next acceptance gate. Discussion,
votes, and reviewer identity are not substitutes for technical evidence.
