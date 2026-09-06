# Exact signed-permutation unitary channels

Criterion `e7q.ir.signed-permutation-unitary-channel` version `1` compares the
**premeasurement noiseless quantum channel** rho -> U rho U† in the existing
signed-permutation fragment. It is not noisy-channel support.

## Exact semantics and limits

If U|i> = s_i|p(i)>, the action on matrix unit |i><j| is
s_i s_j |p(i)><p(j)|. The validator compares every matrix unit, including
all off-diagonal units. These units span the complex operator space, so equality
establishes the same linear channel on every density operator in this domain.
An overall unitary sign cancels; relative signs do not generally cancel.

The [exact-unitary restrictions](EXACT_UNITARY.md) apply: only id/x/z/cx/cz/swap,
eight qubits maximum, 256 expanded gates, one quantum and one classical register,
and complete terminal measurement. Register descriptors and ordered measurement
maps must match. Quantum index zero is least significant. Source/parser budgets
apply before circuit evaluation. Matrix-unit comparison streams at most 65,536
triples per endpoint without allocating a dense superoperator. Arithmetic is
integer exact; tolerance options are unsupported.

## Contract

```json
{
  "criterion": {"id": "e7q.ir.signed-permutation-unitary-channel", "version": "1"},
  "preserves": ["premeasurement-unitary-channel", "terminal-measurement-map"],
  "loses": ["source-spelling-and-gate-decomposition", "global-phase"],
  "assumptions": ["signed-permutation-gate-table-v1"],
  "validation_status": "validated"
}
```

The optional capability is `circuit.channel.signed-permutation-unitary`.
The dedicated F2 result cites both endpoint artifacts. PASS reports the number
of matrix units checked; FAIL identifies the first differing unit. Invalid
contracts/domains are UNSUPPORTED, resource excess BLOCKED, and contradictory
validation status FAIL. F0/F1 and existing criteria retain their meanings.

XZ and ZX define equal channels but not equal unitaries. Z and identity agree
on basis-measurement outcomes but define different channels: Z reverses the
off-diagonal entries of |+><+|. This criterion compares the prefix before
measurement and does not assess a postmeasurement instrument. Noise, reset,
dynamic control, arbitrary gates, controlled-unitary substitution and hardware
fidelity remain unsupported. Channel equality does not preserve a chosen
unitary global phase for controlled embedding.

## Native-engine feasibility and acceptance

The native engine's `channel_superoperator` constructs the premeasurement
linear map and supports declared noise in its own format. Its general path
uses complex floating-point arrays. This criterion uses exact integers in its
narrow domain rather than importing general numerical results as exact proof.
Tests cross-check every superoperator entry for 125 three-gate circuits against
the native implementation. The test-only bridge explicitly reverses qubit
indices because native q0 is most significant and this IR fragment uses q0
least significant. It does not constitute the Phase 2 native-source adapter.

```sh
python -m e7q.cli ir validate examples/e7q-ir/unitary-channel-graph.json --level F2
python -m pytest -q tests/test_e7q_ir_channel.py
```

Further noisy-channel work needs source/representation support, explicit
probability semantics and numerical error/metric bounds, plus noise-specific
conformance cases. The H/u2 example and broader Phase 1C also remain pending.
