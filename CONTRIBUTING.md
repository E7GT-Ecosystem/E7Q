# Contributing

Open an issue for substantial language, semantic, architecture, or licensing changes. Pull requests should state intended behaviour, identify affected specification sections, add tests, distinguish exact guarantees from approximations, declare backend assumptions, and describe measurement or information loss where relevant.

By contributing, you agree that code is licensed under Apache-2.0 and documentation/specifications under CC-BY-SA-4.0 unless a file states otherwise, and confirm your right to submit it.

## Commercial E7Q-IR publication boundary

Read [the commercial policy](docs/licensing/COMMERCIAL_POLICY.md) before adding
IR implementation. Current open-core contributions remain Apache-2.0; published
permissions are not withdrawn. Protected IR changes need an explicit hash-bound
`retain_public_terms` decision in the component register before publication. New
commercially designated implementation belongs in `commercial/e7q_ir/`, with
explicit notices and recorded rights clearance, outside the Apache package.

Before accepting an outside contribution to that commercial component, obtain a
separate written contributor agreement authorising the intended public and
commercial licences. A PR, contributor attribution, DCO assertion or submission
under PolyForm alone is not represented as a commercial relicensing grant. Do not
publish private implementation or copied material without the necessary rights.
Documentation retains CC-BY-SA-4.0 unless explicitly licensed otherwise.

Run `python scripts/check_licensing_boundary.py` and
`python scripts/test_licensing_boundary.py` before submitting licensing/IR changes.
