# External evidence importer

**Profile:** `e7q.external-evidence-receipt/v1alpha1`

**Introduced:** E7Q 1.0.0-rc8

**Current integration:** E7Q 1.0.0-rc9

**Status:** experimental, provider-neutral offline verifier

## Purpose

The external evidence importer lets E7Q inspect an execution package produced
outside E7Q without pretending that E7Q submitted or witnessed the job. It
accepts either a ZIP archive or an already-extracted directory and emits a
deterministic, machine-readable receipt.

```bash
e7q external-bundle verify external-package.zip \
  -o external-evidence-receipt.json
```

Raw counts are represented by digest and summary by default. Include the
normalized values only when a downstream assessment needs them:

```bash
e7q external-bundle verify external-package.zip \
  --include-counts \
  -o external-evidence-with-counts.json
```

The importer is not an IBM, Qiskit, or Hieroglyphs schema implementation. Its
input contract is a small provider-neutral evidence-package profile derived
from actual supplied single-circuit and multi-circuit packages.

## Record discovery

A record is any directory in the package containing `job_metadata.json`. The
same package may contain one record or several records from a batched job.

Each record requires:

- `job_metadata.json`;
- `raw_counts.json`;
- `final_circuit.qasm`;
- `mapping.json`;
- `calibration.json`;
- `versions.json`.

The importer also understands these optional artifacts:

- `MANIFEST.md`;
- `pre_transpile_circuit.qasm`;
- `hieroglyphs_ir.json`;
- `hieroglyphs_output.hglyph`;
- `final_circuit.qpy`;
- explanatory README files.

Optional files remain part of the full received-file digest inventory even
when the dependency-free verifier cannot semantically decode them.

## Checks

The receipt keeps materially different judgments separate.

| Judgment | What is checked | What it does not establish |
| --- | --- | --- |
| Archive safety | traversal, symlinks, encryption, duplicate names, expansion and size limits | that file content is benign outside this verifier |
| Artifact integrity | supplied manifest hashes against received bytes | signer identity or custody before receipt |
| Internal consistency | JSON shape, shots, counts, QASM operations, mappings, active qubits and calibration coverage | provider authenticity or physical fidelity |
| External provenance | presence of job, backend and reported time fields | independent authentication of those fields |
| Reproducibility | retained circuit/compiler artifacts and build identity | reproduction of a proprietary compiler or provider execution |
| Algorithmic claim validation | deliberately not performed | QFT correctness, QEC behavior, fidelity or performance |

`PASS` therefore means that no error-level archive, integrity, or
cross-artifact consistency check failed. It is accompanied by
`INTERNALLY_CONSISTENT_WITH_LIMITATIONS`. A `PARTIAL` sub-judgment is not
silently promoted to `PASS`.

## Manifest handling

Full 64-character SHA-256 entries support an artifact-integrity `PASS` when
they match and cover all required files. Correct abbreviated prefixes are
reported as `PARTIAL`; a mismatching digest is `FAIL`. The receipt computes and
records a full SHA-256 for every received record file regardless of manifest
quality.

## OpenQASM boundary

The verifier now invokes the shared dependency-free OpenQASM 2 importer for
the evidence surface used by the package profile:

- `qreg` and `creg` widths;
- operation counts;
- physical qubits used;
- two-qubit edges;
- explicit measurement destinations.

It is a bounded implementation rather than a complete language runtime.
Unsupported statements and gates fail the QASM consistency check rather than
being ignored. The normalized typed artifact can also be produced directly
with `e7q import-openqasm2`; see
[`OPENQASM2_AND_DETERMINISTIC_ASSESSMENT.md`](OPENQASM2_AND_DETERMINISTIC_ASSESSMENT.md).

QPY artifacts are hashed but not decoded, and reported circuit depth is not
independently recomputed. Those checks would require a separately versioned
Qiskit-backed adapter.

## Safety limits

ZIP members are read directly without extracting or executing them. The
importer rejects path traversal, absolute paths, backslash paths, symlinks,
encrypted entries, duplicates, oversized members, excessive expansion and
unsafe compression ratios. Directory inputs reject symlinks and use the same
file-count and size limits.

## Synthetic fixture

The public fixture under
[`examples/external-evidence-synthetic/`](../examples/external-evidence-synthetic/)
contains no provider job, account information, private compiler output, or
real hardware result. It exercises the same record-discovery, manifest,
counts, QASM, mapping and calibration checks used for private development
packages.

## Evidence boundary

The importer validates received artifacts. It does not:

- authenticate a provider, submitter, job identifier, timestamp or calibration;
- prove that a retained QASM or QPY object was the object executed;
- recompute a proprietary compiler path;
- assess an algorithm-specific expected result;
- establish hardware fidelity, fault tolerance, causation or novelty.

An algorithm-specific assessment must be a separate artifact whose oracle,
bit-order convention, thresholds and admissible claims are declared explicitly.
