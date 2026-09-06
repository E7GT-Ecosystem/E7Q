# E7Q-IR ecosystem handoff

The quantum direction remains E7Q-IR. The former quantum Fabric is incorporated here; there is no second quantum Fabric roadmap. The authoritative engineering sequence is [BUILD_PLAN.md](BUILD_PLAN.md).

## Verified starting point

The inspected main commit is `b7dc357715529ecc7f0426b708ae56320a204e2b`. It provides the existing quantum runtime plus experimental IR F0/F1 validation and the external circuit/counts demonstrator. The build plan was prepared locally as `f98db61` and is published by this integration branch. Recheck current main before starting a new implementation, because other contributors may have advanced it.

Run `python -m pytest -q` in the product's test environment. Read the actual test result and IR conformance documentation; the historical count of 181 tests is not a permanent acceptance threshold. Passing F1 does not establish quantum semantic equivalence, provider authenticity or physical fidelity.

## Cross-product experiment

An optional ecosystem adapter can wrap the exact native graph bytes, archive them as external evidence and restore them for native verification. E7Q's own canonicalizer, IDs and schemas remain unchanged. Product consumers own the wrapper and their native assurance checks; E7Q gains no dependency on an ecosystem service or database.

The experiment must preserve source references, context, temporal scope, transformation declarations and bounded claims. A transport digest cannot upgrade any of them. Future interoperability changes need independently checked compatibility vectors and explicit versioning.

## Next work

1. Phase 1A, bounded Phase 1B and two Phase 1C identity criteria are implemented in this integration. Continue with bounded quantum-semantic criteria after reviewing the current build plan; do not restart the framework.
2. Run a bounded workflow supplied independently of the bundled examples. Compare review/reproduction effort and unsupported-claim detection against ordinary manifests and logs.
3. Keep authentication, provider execution and additional modalities as separate gates. Do not make E7FS or universal orchestration prerequisites.

Before handing work to another AI, record the exact baseline, work branch, diff, commands/results, unsupported capabilities and session authorisations. A document edit does not authorise live provider jobs, third-party outreach or publication of private collaborator material.
