# Milestone 23: evidence-contract hardening

E7Q v1.0.0rc12 corrects two overbroad structural claims introduced with the
UC5 comparative-evidence profile and aligns the public release metadata.

## Corrections

- Structural validation now supports `MANIFEST_ASSESSABLE`, not
  `FEASIBILITY`.
- `FEASIBILITY` remains `NOT_ESTABLISHED` until an evidence-linked profile
  verifies that the declared workflow actually executed and produced
  assessable output.
- Relative-support values now obey minimum contracts implied by their declared
  semantics. Probability values must be finite numbers in `[0,1]`;
  likelihood-like values must be finite and non-negative; scores and
  confidence-like values must be finite numbers; ordinal and domain-specific
  values must be finite numbers or non-empty labels.
- Package, citation, README, and Language Specification versions now agree on
  `1.0.0rc12`.

These changes do not modify E7Q circuit grammar, gate semantics, execution,
measurement, equivalence, QEC, or temporal semantics. They tighten only the
experimental evidence and release contracts.
