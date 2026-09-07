# Native and legacy preservation adapter

This is the first preservation increment of Phase 2, not completion of the
native compiler/execution adapter. Existing native formats and IDs are unchanged.

## Usage

```sh
python -m e7q.ir.legacy examples/bell.e7q --format e7q \
  --created-at 2026-09-07T00:00:00Z --output /tmp/bell-ir.json
```

Use an existing source path. For JSON evidence use `--format legacy-json`.
The explicit timestamp describes the import record, not authenticated execution
time. The Python API exposes `import_evidence` and `recover_source`.

## Preservation contract

UTF-8 inputs up to 1 MiB are retained in a core-profile source artifact with
their byte length and SHA-256 digest. Recovery verifies the envelope/references
and source digest and returns the original bytes, including whitespace and
line endings. Digest agreement does not authenticate the source.

Native E7Q is opaque source in this increment: it is not parsed or executed.
Legacy JSON additionally produces a representation linked to its source, retaining
the entire decoded object, including IDs, proof, status, count order, unknown
fields and limitations. A failed legacy verdict stays supplied data; it cannot
become a new IR PASS. Unknown count order remains unknown.

Admitted schema labels:
- `e7q.external-evidence-receipt/v1alpha1`
- `e7q.execution-bundle/v1`
- `e7q.execution-result/v1`
- `e7q.execution-receipt/v1`
- `e7q.deterministic-assessment/v1alpha1`

Admission recognizes the label, not conformance to its legacy schema.
Duplicate keys, non-finite numbers, invalid UTF-8, excessive input size,
nesting beyond 64 and more than 100,000 decoded values are rejected.
The JSON projection uses Python JSON numeric decoding; original numeric spelling
and any precision lost to floating-point decoding remain recoverable only from
the source. Whitespace and escape spelling are likewise absent from the projection.
No external references are followed and no imported code is executed.

## Assurance and next gate

Generated graphs pass F0/F1. Core-profile payloads have no semantic validator;
F2 is not established. The projection relation is explicitly not-assessed.
No hardware fidelity, provider authentication, chronology or equivalence follows
from preservation. F1 itself does not validate the payload's content digest;
`recover_source` performs that additional integrity check.

Next: typed native intent/compiler/Proof-of-Path and execution/observation mapping,
explicit loss accounting, and native/external Bell comparison under a declared
semantic criterion. Optional simulator integration and H2/H3 hardening remain
separate acceptance gates.
