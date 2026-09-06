# Bounded circuit-basic semantic validation

Verification: 203 repository tests pass, including 34 focused IR tests.
The deterministic report is stored as `examples/e7q-ir/f2-phase1b.json`.
No remote branch, pull request or merge is created by this increment.

This increment builds locally on Phase 1A. It adds real payload checks without
passing the complete Phase 1 gate or implementing Phase 1C equivalence.

## Evidence inputs

`e7q ir build manifest.json --include-circuit-content -o graph.json` embeds
the original UTF-8 source and executable text in their content-addressed
payloads. This option discloses circuit text and is deliberately opt-in.
The manifest assessment must declare `expected_label_order`, identical to
the observation's `label_order`. No ordering is silently inferred or reversed.
Without the flag the historical builder output is unchanged.

Run `e7q ir validate graph.json --level F2 -o report.json` to check:

- embedded byte length and SHA-256 against the declared identities;
- the bounded existing OpenQASM 2 importer, without executing circuit content;
- positive integer shots, nonnegative integer binary counts and totals;
- explicit bit ordering and width against one classical register;
- observed probabilities, normalised reference probabilities, TVD and threshold;
- assessment status, claim support, direct evidence/provenance agreement,
  retained boundaries, and assessment/support relation status.

Every artifact result carries the pinned `e7q.ir.circuit-basic-payload@1b`
criterion and graph artifact evidence references. Relations retain their
declared transformation criterion, which is not implemented here.

## Limits and non-claims

Maximum embedded source size: 262,144 UTF-8 bytes per circuit. Maximum count
or reference outcomes: 65,536. Multiple classical registers require an ordering
profile and are `UNSUPPORTED`. Unembedded bytes, unspecified label conventions,
width conflicts, and resource limits are `BLOCKED`. Invalid or unsupported
QASM returns a bounded importer `UNSUPPORTED` result, not semantic inequality.
No filesystem or network resolution is performed by validation.

Transformation and execution artifacts and other relation kinds remain
`NOT_ASSESSED`. A complete example therefore remains below F2 PASS even when
its payload checks pass. A failed statistical assessment can be semantically
consistent: recomputation validates the negative result rather than erasing it.
Free-text claim truth, adequacy of scientific boundaries, provider identity,
chronology, circuit equivalence, and physical fidelity are not established.

The Phase 1A golden report remains a historical fixture. New payload results
use the same additive experimental envelopes, without reinterpreting old PASS
reports. Existing F0/F1 validation is unchanged.
