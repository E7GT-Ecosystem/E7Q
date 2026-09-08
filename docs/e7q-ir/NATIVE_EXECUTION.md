# Native execution into E7Q-IR

The explicit execution adapter extends Phase 2 preservation with linked source,
intent, parsed representation, execution, observation and assessment artifacts.
It runs the existing native parser, simulator and verifier. Existing native APIs
and formats remain unchanged; no new external dependency is required.

## Run

```sh
python -m e7q.ir.native examples/bell.e7q \
  --created-at 2026-09-07T00:00:00Z --output /tmp/bell-native-ir.json
```

Python callers use `execute_native(raw_bytes, created_at=...)`. This API executes
the native program locally; the separate legacy preservation importer never does.
The record timestamp is caller supplied, not authenticated execution time.

## Admitted scope

Statevector only, explicit seed, static gates and one terminal full-register
measurement. Limits: UTF-8 source up to 1 MiB, 8 qubits, 8 classical bits,
100,000 shots and 1,024 expanded operations. Noise, dynamic measurement/control
and assertions are rejected. Execution limits are checked after parsing and
before simulator allocation; this is not a sandbox or a hardened parser resource
boundary. Use trusted local source for execution.

## Mapping and loss

| Artifact | Retained information |
| --- | --- |
| Source | Original bytes recoverable through the preservation API |
| Intent | Selected path, invariants, backend, shots and seed |
| Representation | All parsed Program fields and ordered expanded operations |
| Execution | Backend capability boundary, package versions, seed, shots and complete native Proof-of-Path |
| Observation | Counts, model probabilities, bit width and explicit clbit-ascending labels |
| Assessment | Entire native verifier result, including checks, FAIL and first failure fields |

Projection loses comments/formatting and subpath call boundaries in expanded
operations; original source retains these. The graph does not serialize state
amplitudes or per-shot trajectories. Model probabilities are not hardware
observations; counts cannot establish phase-sensitive equivalence.
The extra classical bits in this static native path are retained as trailing zeros.
The complete verifier result remains inspectable even when its status is FAIL.

A fixed source, timestamp and package environment give reproducible seeded output;
this does not promise cross-version random-stream identity. Package versions
describe the environment, not authenticated implementation provenance.

## Acceptance boundary

All generated envelopes use the core profile and pass F0/F1. Relations remain
not-assessed. The native verifier's PASS is recorded inside the assessment payload;
it is not an F2 conformance verdict. There is no native semantic validator,
compiler conversion, provider authentication or physical fidelity claim here.

Tests cover direct native-result agreement, byte recovery, deterministic seeded
graphs, failed invariants, non-palindromic labels with an extra bit, admission
rejection before execution and the CLI. The separate bounded native/external QCEC
workflow now preserves this native Proof-of-Path while comparing compatible
unitary prefixes under one explicitly selected numerical criterion. Phase 2/H5
remain open: next gates are compiler Proof-of-Path conversion, typed legacy
execution/receipt adapters and native/default F2 semantic validation.
