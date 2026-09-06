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

The v0alpha1 implementation supports F0 and F1 only. F2-F4 are emitted as
`NOT_IMPLEMENTED` rather than optimistically inferred.

Capability negotiation is separate from F0/F1. An artifact using an unknown
profile may remain structurally inspectable, but its semantic readiness is
`BLOCKED`.

Use:

```bash
e7q ir validate graph.json --level F1 -o conformance.json
```
