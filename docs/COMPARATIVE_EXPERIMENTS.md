# Comparative quantum experiments

E7Q v1.0.0rc11 adds a bounded descriptive profile for supplied one- or
two-factor experiments. It is intended for comparisons such as compiler path,
backend, mitigation method, model architecture, sampler, or other declared
experimental factors.

```bash
e7q assess-experiment experiment.json -o comparative-report.json
```

The input schema is `e7q.comparative-experiment/v1alpha1`; the output schema is
`e7q.comparative-experiment-report/v1alpha1`.

## Input contract

An input manifest declares:

- an experiment identifier, title, inquiry, and whether the profile was
  predeclared;
- one or two factors, each with an ordered baseline and candidate level;
- exactly one primary metric and any secondary metrics;
- for every metric, direction, unit, and minimum descriptive effect;
- at least two runs, each with its factor cell, all metric values, resource
  budget, independence status, and evidence references;
- an optional UC5 `relative_support` declaration.

The v1alpha1 profile intentionally supports only binary factors. Wider or
continuous designs require a later, separately validated statistical profile.

## Reported evidence

E7Q aggregates each observed cell with its run identifiers, count, mean,
minimum, and maximum. It then reports:

- baseline-to-candidate effects within every available context;
- raw and direction-adjusted differences;
- metric-specific improved, worsened, or no-material-difference status;
- a metric trade-off vector with no automatic aggregate verdict;
- for a complete two-factor matrix, a descriptive difference-of-differences
  interaction contrast;
- missing cells, replication posture, exact resource-budget comparability,
  and warnings;
- a deterministic manifest digest and Proof-of-Path.

The interaction contrast is descriptive. It does not establish statistical
significance, mechanism, or causation.

## Claim ladder

The report keeps six claim levels separate:

1. `FEASIBILITY`;
2. `OBSERVED_DIFFERENCE`;
3. `REPEATABLE_EFFECT`;
4. `QUALITY_ADVANTAGE`;
5. `PRACTICAL_ADVANTAGE`;
6. `COMPUTATIONAL_QUANTUM_ADVANTAGE`.

This bounded command can automatically support only the first two. Even when
the manifest contains repeated runs, it does not perform the inferential test
needed to establish repeatability. Domain relevance, matched cost/time/energy
budgets, adequate classical competitors, and a computational resource boundary
remain responsibilities of stronger domain methods.

The report therefore cannot be cited by itself as evidence of quantum
advantage, supremacy, provider authenticity, run independence, hardware
fidelity, or causal attribution.

## Annealing boundary

The profile may describe supplied metrics from an annealing experiment, but it
does not implement D-Wave Ocean, QUBO/Ising execution, logical-to-physical
embedding, chain-break analysis, gauge transforms, annealing schedules, or
effective-temperature validation. Any future annealing adapter must be a
separate evidence profile rather than an implicit extension of E7Q's circuit
semantics.
