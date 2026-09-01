# E7Q 1.0.0rc12 release notes

Release date: 2026-09-01

This maintenance release hardens the evidence contracts added in rc10 and
rc11 without changing core circuit semantics.

## Changed

- Replaced structurally inferred `FEASIBILITY` with
  `MANIFEST_ASSESSABLE`.
- Retained `FEASIBILITY` as a separate claim level that requires verified
  execution evidence and is not established by an offline manifest alone.
- Added semantics-aware support-value validation for probability, score,
  likelihood-like, confidence-like, ordinal, and domain-specific declarations.
- Aligned the Language Specification, package metadata, citation metadata, and
  README at version `1.0.0rc12`.

## Compatibility

The comparative-experiment and relative-support schemas remain experimental
`v1alpha1` profiles. Reports and declarations that relied on non-numeric
probability, score, likelihood-like, or confidence-like values are now
correctly rejected as nonconformant. Consumers of comparative reports should
recognize the new `MANIFEST_ASSESSABLE` level and must not infer feasibility
from structural validation.
