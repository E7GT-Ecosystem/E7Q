# Synthetic legacy execution receipt mapping

This public offline example exercises the existing legacy engines without changing
their formats:

- [`program.e7q`](program.e7q) and [`calibration.json`](calibration.json) generate
  [`bundle.json`](bundle.json) through `e7q.bundles.build_execution_bundle()`;
- [`result.json`](result.json) is a supplied synthetic execution-result declaration;
- [`receipt.json`](receipt.json) is generated through
  `e7q.results.build_execution_receipt()` with both optional pilot records;
- [`benchmarks/e7q-ir/legacy-receipt-results.json`](../../../benchmarks/e7q-ir/legacy-receipt-results.json)
  maps the three supplied files into typed E7Q-IR.

The graph identity is
`sha256:2461fac5f5a9c5472280b9ae1daf2789167851d91f3a40df8ec388c22f3fff29`.
The workflow preserves each supplied file byte-for-byte with its own digest, byte
length, schema and stable source reference. It records the bundle intent, the
supplied unauthenticated provider/job/completion declarations, an ordered two-bit
count observation, the complete legacy receipt Proof-of-Path, 36 independent
consistency checks and a receipt reconstructed through the existing legacy engine.

The synthetic observation declares `clbit-descending` label order and contains
`{"00": 4, "01": 0, "11": 4}` over eight shots. The typed probabilities are
`0.5`, `0.0` and `0.5`; the zero-count `01` outcome remains present. The supplied
and independently reconstructed receipts agree, so the bounded offline consistency
claim is supported. Provider identity, job identity, chronology, submission,
execution authenticity, hardware fidelity and circuit correctness remain explicitly
unestablished.

Conformance is F0 PASS, F1 PASS and F2 BLOCKED. Twenty-five installed semantic
checks run, but no legacy-receipt semantic validator is registered as default F2
truth. F3 authentication and F4 scalability are not implemented.

Reproduce the mapping:

```bash
python -m e7q.ir.legacy_receipt_workflow \
  examples/e7q-ir/legacy-receipt/bundle.json \
  --result examples/e7q-ir/legacy-receipt/result.json \
  --receipt examples/e7q-ir/legacy-receipt/receipt.json \
  --count-label-order clbit-descending \
  --created-at 2026-09-08T00:00:00Z \
  --bundle-source-ref fixture:legacy-receipt:bundle \
  --result-source-ref fixture:legacy-receipt:result \
  --receipt-source-ref fixture:legacy-receipt:receipt \
  --output benchmarks/e7q-ir/legacy-receipt-results.json
```

This package does not begin provider integration, authenticated execution,
K12/CFS implementation, or default native F2 validation. Phase 2 and H5 remain
open.
