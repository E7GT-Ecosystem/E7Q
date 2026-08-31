# E7Q relative-support pilot

E7Q v1.0.0rc10 aligns with E7G-T v0.11-UC5 and implements its informative
relative-support overlay as the opt-in schema
`e7q.relative-support-pilot/v1alpha1`.

The pilot records differences in support among alternatives that remain
admissible. It does not silently turn support into truth, probability,
exclusion, causation, phase determinacy, or a decision rule.

## Invocation

The comparative-experiment workflow can embed the pilot when its input
manifest contains a conforming `relative_support` declaration:

```bash
e7q assess-experiment examples/comparative-experiment-synthetic.json \
  --relative-support-pilot \
  -o comparative-report.json
```

Without the flag, the declaration is not emitted. Without a declaration, use
of the flag fails closed.

## Required declaration

The declaration names:

- the carrier and carrier kind;
- ordinal, scored, probabilistic, likelihood-like, confidence-like, or
  domain-specific support semantics;
- the support domain and relation or scoring rule;
- evidence and provenance;
- initialisation and update rules;
- calibration and normalisation posture;
- independence assumptions and known dependencies;
- current assignments;
- a separate exclusion rule;
- admitted and blocked uses, validity window, and reopen condition.

Every assignment has an `alternative_ref`, an explicit `admissible` value, a
`support_value`, and evidence references. An alternative marked inadmissible
must also supply an `exclusion_basis_ref`. A low support value alone is not an
exclusion basis.

Numerical values are not treated as probabilities unless the declaration uses
`probability` semantics and supplies the probability model through its
referenced rules. Structural conformance does not validate that model,
calibration, evidence, or empirical adequacy.

## Pilot boundary

This is one quantum-domain application contributing evidence toward E7G-T
Pilot J. It is not enough to promote the UC5 module into the normative core.
The profile must still survive cross-domain use, independent review, and
counterexample testing.
