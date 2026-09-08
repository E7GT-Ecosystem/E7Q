# Native and legacy preservation adapters

Phase 2 now includes two additive legacy paths. Neither changes existing native
or legacy formats, identifiers, bundle creation or receipt construction.

1. `e7q.ir.legacy` preserves opaque native sources and recognized legacy JSON.
2. `e7q.ir.legacy_receipt_workflow` maps one supplied execution bundle, result
   and receipt into typed offline consistency evidence by rerunning the existing
   `build_execution_receipt()` implementation.

Phase 2 and H5 remain open until native/default F2 semantic validation is added.

## General preservation importer

```sh
python -m e7q.ir.legacy examples/bell.e7q --format e7q \
  --created-at 2026-09-07T00:00:00Z --output /tmp/bell-ir.json
```

Use an existing source path. For JSON evidence use `--format legacy-json`.
The explicit timestamp describes the import record, not authenticated execution
time. The Python API exposes `import_evidence` and `recover_source`.

UTF-8 inputs up to 1 MiB are retained in a core-profile source artifact with
their byte length and SHA-256 digest. Recovery verifies the envelope/references
and source digest and returns the original bytes, including whitespace and line
endings. Digest agreement does not authenticate the source.

Native E7Q is opaque source in this importer. Legacy JSON additionally produces
a representation linked to its source, retaining the entire decoded object,
including IDs, proof, status, count order, unknown fields and limitations. A
failed legacy verdict stays supplied data; it cannot become a new IR PASS.
Unknown count order remains unknown.

Admitted schema labels:

- `e7q.external-evidence-receipt/v1alpha1`
- `e7q.execution-bundle/v1`
- `e7q.execution-result/v1`
- `e7q.execution-receipt/v1`
- `e7q.deterministic-assessment/v1alpha1`

Admission recognizes the label, not conformance to its legacy schema. Duplicate
keys, non-finite numbers, invalid UTF-8, excessive input size, nesting beyond 64
and more than 100,000 decoded values are rejected. The JSON projection uses
Python JSON numeric decoding; original numeric spelling and any precision lost
to floating-point decoding remain recoverable only from the source. Whitespace
and escape spelling are likewise absent from the projection. No external
references are followed and no imported code is executed.

## Typed legacy execution receipt workflow

```sh
python -m e7q.ir.legacy_receipt_workflow \
  examples/e7q-ir/legacy-receipt/bundle.json \
  --result examples/e7q-ir/legacy-receipt/result.json \
  --receipt examples/e7q-ir/legacy-receipt/receipt.json \
  --count-label-order clbit-descending \
  --created-at 2026-09-08T00:00:00Z \
  --bundle-source-ref fixture:legacy-receipt:bundle \
  --result-source-ref fixture:legacy-receipt:result \
  --receipt-source-ref fixture:legacy-receipt:receipt \
  --output /tmp/legacy-receipt-ir.json
```

The Python API exposes `build_legacy_receipt_graph`,
`recover_legacy_source` and `validate_legacy_receipt_evidence`.
The CLI refuses to overwrite any input.

### Evidence path

The workflow preserves the execution bundle, execution result and execution
receipt independently. Each source artifact records exact original bytes,
SHA-256 digest, byte length, declared schema and caller-declared stable source
reference. Each typed representation retains the complete decoded object,
original proof, original status, unknown fields and supplied limitations.

The typed graph keeps these meanings separate:

1. **execution intent** — bundle identity, source/OpenQASM declarations, computed
   compiled-content digest, target, shots, offline handoff and bundle/compiler
   proof;
2. **supplied execution record** — exact result identity, bundle-linkage
   declaration, target/shots and unauthenticated provider, job and completion
   declarations;
3. **observation** — complete count map, explicit label order, width, deterministic
   outcome order, zero-count outcomes and empirical probabilities;
4. **assessment** — strict parsing, registered structural checks, independent
   legacy receipt reconstruction and field-by-field comparison;
5. **bounded claim** — offline bundle/result/receipt consistency only.

Every typed transformation records input/output references, a named and
versioned criterion, preserved information, losses, assumptions, validation
status and deterministic transformation identity.

### Independent legacy recomputation

The supplied receipt is not trusted because it says `PASS`, carries a digest or
contains a plausible Proof-of-Path. The workflow strictly parses the preserved
bundle and result, then calls the existing `e7q.results.build_execution_receipt()`
logic over those exact bytes. Optional observational and temporal pilot fields
are reconstructed only when present in the supplied receipt. All admitted receipt
fields, probabilities and proof steps are compared independently.

A bounded PASS establishes only:

> The supplied bundle and result are internally consistent and the typed mapping
> agrees with independently recomputed legacy receipt semantics under the
> declared offline criterion.

Malformed/duplicate JSON, non-finite values, missing or unknown schemas,
unsupported count-label semantics, inconsistent outcome widths, invalid counts,
target/shot/digest mismatches, altered receipt probabilities/proof, forged PASS,
rehashed source/representation tampering and every supplied `FAIL`, `BLOCKED`,
`UNSUPPORTED` or `NOT_ASSESSED` status remain non-PASS.

### Public deterministic example

The synthetic fixture under `examples/e7q-ir/legacy-receipt/` contains the source,
calibration snapshot, generated bundle, supplied result and generated receipt.
The mapped graph is `benchmarks/e7q-ir/legacy-receipt-results.json`, graph ID
`sha256:2461fac5f5a9c5472280b9ae1daf2789167851d91f3a40df8ec388c22f3fff29`.
It preserves three independent source byte streams, maps `clbit-descending`
counts `00=4`, `01=0`, `11=4`, retains both optional pilot records, passes all
36 workflow consistency checks and supports only the bounded offline claim.

## Assurance limits and next gate

Both workflows produce F0/F1-conformant core-profile graphs. No legacy receipt
semantic validator is registered as default F2 truth, so F2 remains `BLOCKED`;
the local deterministic receipt validator is an explicit workflow check, not a
global semantic promotion.

Neither path establishes submission, execution authenticity, provider identity,
chronology, physical fidelity, correctness of the executed circuit,
computational advantage, F3 authentication or arbitrary scalability. Provider
integration, authenticated execution and K12/CFS implementation remain unstarted.
The next Phase 2/H5 gate is native/default F2 semantic validation.
