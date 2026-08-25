# Milestone 19 — External Evidence Importer

Milestone 19 extends E7Q's offline evidence boundary to execution packages
produced by external toolchains. It adds safe ZIP/directory ingestion,
single-job and batched-record discovery, full received-file digests,
cross-artifact consistency checks, and a bounded external-evidence receipt.

## Command

```bash
e7q external-bundle verify external-package.zip \
  -o external-evidence-receipt.json
```

The verifier never submits a job, contacts a provider, executes archive
content, or treats a supplied identifier as authenticated. It distinguishes
archive safety, integrity, internal consistency, provenance, reproducibility,
and algorithmic validation rather than collapsing them into one verdict.

The bundled public fixture is synthetic. Real collaborator packages remain
private development inputs unless their owner separately authorizes release.

See [External evidence importer](EXTERNAL_EVIDENCE_IMPORTER.md) for the input
profile, checks, limits, and evidence boundary.
