# E7Q-IR Conformance

E7Q-IR separates conformance dimensions so that a lower-level result cannot be
mistaken for a higher-level assurance claim.

| Level | Establishes | Does not establish |
| --- | --- | --- |
| F0 Structural | Required fields, admitted object kinds, valid content identities | Reference resolution or semantics |
| F1 Referential | Unique identities and resolvable artifact/relation references | Quantum correctness |
| F2 Profile semantic | Named profile rules under a pinned criterion | Provider authenticity or physical fidelity |
| F3 Authenticated | Declared signatures, identities, timestamps, or provider attestations | Truth of every semantic or scientific claim |
| F4 Reproduced | Replication under declared conditions | Universal validity or causation |

The v0alpha1 implementation supports F0/F1 and the F2 validation framework.
`e7q.ir.circuit-basic/0alpha1` supplies its bounded circuit criteria separately.
`e7q.ir.native-execution/0alpha1` supplies installed bounded native reconstruction
without registering semantics for `e7q.ir.core/0alpha1`. Core-profile and
historical graphs therefore remain inspectable at F0/F1 but F2 `BLOCKED`.
F3-F4 remain `NOT_IMPLEMENTED`.

Capability negotiation is separate from F0/F1. An artifact using an unknown
profile may remain structurally inspectable, but its semantic readiness is
`BLOCKED`.

Use:

```bash
e7q ir validate graph.json --level F2 -o conformance.json
```

F2 uses five non-interchangeable states:

- `PASS` — every required installed profile check passed;
- `FAIL` — a semantic rule or validator-result contract failed;
- `BLOCKED` — a required profile, validator, relation profile, or resource was
  unavailable;
- `UNSUPPORTED` — the subject lies outside the validator's declared domain;
- `NOT_ASSESSED` — no semantic conclusion was attempted.

An F2 request runs only after F0 and F1 pass. Unknown profiles remain fully
inspectable at F0/F1 but produce F2 `BLOCKED`. Every semantic result identifies
its subject, profile, stable check identifier, evidence references, boundaries,
and deterministic content identity. Optional validator-runtime evidence records
the validation policy/enforcement separately from graph evidence. A non-PASS result never upgrades a
transformation declaration or claim.
# Phase 1B implementation update

The bounded Phase 1B payload validator now supersedes the framework-only
implementation notes below. See [Phase 1B scope and limits](PHASE_1B.md).
Digest-only graphs remain inspectable but block byte-dependent semantic checks;
transformation equivalence and execution semantics remain unassessed.
# Bounded Phase 1C implementation note

The optional [signed-permutation criterion](EXACT_UNITARY.md) additionally
establishes exact unitary-prefix equality under its explicitly restricted gate
table. It does not imply general unitary, global-phase or channel support.

The built-in circuit profile now implements versioned UTF-8 byte-identity and parsed structural-identity
criteria described in [PHASE_1C.md](PHASE_1C.md). A graph containing only admitted
source/representation endpoints and an admitted identity relation can pass F2. That result does
not cover execution, provider identity or broader quantum-equivalence criteria.

The optional [global-phase criterion](GLOBAL_PHASE.md) admits one overall sign
within the signed-permutation fragment and declares phase loss explicitly.
It cannot confer exact equality or authorize controlled-subcircuit replacement.

The optional [basis-measurement criterion](BASIS_MEASUREMENT.md) checks all basis
inputs in the signed-permutation fragment and explicitly loses phase. Its PASS
does not establish unitary or quantum-channel equivalence.

[Unitary-channel comparison](UNITARY_CHANNEL.md) is available only for the
noiseless signed-permutation fragment and checks off-diagonal matrix units.
No noisy-channel support follows from a PASS.

The optional [real H-unitary criterion](REAL_H_UNITARY.md) establishes the
bounded H/u2 acceptance pair with exact rational/sqrt(2) arithmetic. Existing
signed-permutation criteria retain their narrower gate domains.
