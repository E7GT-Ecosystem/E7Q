# Milestone 21 — E7G-T UC5 relative-support alignment

E7Q v1.0.0rc10 pins E7G-T v0.11-UC5 and adds the opt-in
`e7q.relative-support-pilot/v1alpha1` profile.

The implementation preserves admissibility separately from support, requires
support semantics, provenance, update, calibration and exclusion rules, and
keeps weakly supported alternatives visible until separately excluded. It does
not modify circuit execution or promote the upstream informative module.

See [RELATIVE_SUPPORT_PILOT.md](RELATIVE_SUPPORT_PILOT.md).
