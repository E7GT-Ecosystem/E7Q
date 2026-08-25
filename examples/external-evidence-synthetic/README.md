# Synthetic external evidence fixture

This directory is a public, entirely synthetic fixture for the experimental
`e7q external-bundle verify` command. It resembles the external package shape
used during importer development but contains no provider job, account data,
private compiler output, or real hardware result.

Verify the directory directly:

```bash
e7q external-bundle verify examples/external-evidence-synthetic \
  -o synthetic-external-receipt.json
```

The receipt validates archive/file integrity and cross-file consistency only.
It does not treat the synthetic counts as evidence of hardware execution or
algorithmic performance.
