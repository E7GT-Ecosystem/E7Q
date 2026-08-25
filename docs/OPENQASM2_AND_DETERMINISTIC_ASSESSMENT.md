# OpenQASM 2 import and deterministic assessment

**Profiles:** `e7q.openqasm2-circuit/v1alpha1` and
`e7q.deterministic-assessment/v1alpha1`

**Release:** E7Q 1.0.0-rc9

**Status:** experimental, provider-neutral offline analysis

## Why these are separate operations

The external-bundle importer introduced in RC8 answers whether supplied files
form a safe and internally consistent evidence package. It deliberately does
not turn a circuit file into E7Q's executable language and does not judge an
algorithmic expectation.

RC9 adds two bounded operations:

1. import a supported OpenQASM 2.0 circuit into a typed artifact;
2. compare embedded external counts with a declared deterministic-bit
   reference.

The operations remain separate because syntactic circuit import, package
integrity, statistical alignment, provider identity and physical fidelity are
materially different judgments.

## OpenQASM 2.0 import

```bash
e7q import-openqasm2 final_circuit.qasm \
  --name supplied-circuit \
  -o openqasm2-import.json
```

The importer preserves:

- quantum and classical register names and widths;
- physical qubit indices;
- supported qelib1 and native ISA gate names;
- unevaluated arithmetic parameter expressions;
- register-wide classical conditions;
- barriers;
- explicit qubit-to-classical-bit measurements.

It fails closed on unknown gates, malformed parameters, out-of-range indices,
duplicate registers or measurement destinations, custom gate definitions and
unsupported statements. Includes are recorded but never opened or executed.

The result is intentionally non-executable. A submitted circuit may declare a
156-qubit device register even while using only a small physical subset.
Allocating a `2^156` reference state would be impossible and would confuse
structural import with semantic simulation.

## Count-label order

E7Q defines the canonical single-register outcome string as classical indices
in ascending order:

```text
c[0] c[1] ... c[n-1]
```

Qiskit count labels conventionally display the same register in descending
index order:

```text
c[n-1] ... c[1] c[0]
```

For example, Qiskit label `00101` normalizes to canonical E7Q label `10100`.
RC9 never infers or silently applies that reversal. A deterministic reference
must declare either `clbit-ascending` or `clbit-descending`. The current
normalizer is deliberately limited to one classical register; multi-register
spacing and register ordering require a future profile.

## Deterministic reference assessment

First generate an external receipt that embeds counts:

```bash
e7q external-bundle verify package.zip \
  --include-counts \
  -o external-evidence-with-counts.json
```

Then assess it:

```bash
e7q assess-deterministic external-evidence-with-counts.json \
  --reference pilots/qec_syndrome/hardware_reference.json \
  -o deterministic-assessment.json
```

For each named circuit, the assessment reports:

- the expected canonical full outcome;
- the expected and modal primary-bit projection;
- primary-bit and full-outcome success counts and observed probabilities;
- a two-sided Wilson confidence interval;
- whether the primary interval's lower bound clears the declared minimum
  success probability.

The QEC hardware profile makes the two syndrome bits primary and retains the
three data bits as descriptive full-outcome evidence. Its `0.5` threshold means
that the expected syndrome must be more than a bare majority with the declared
confidence. It is not a fidelity threshold or a fault-tolerance threshold.

The profile also checks whether aggregate modal syndromes reproduce the
declared XOR relation and whether identity, stabilizer and logical-X cases all
retain modal zero syndrome. These are comparisons across separate circuit
aggregates; they are not paired shot-level products.

## Retrospective and prospective use

The committed QEC hardware profile is marked `exploratory` because its first
application follows receipt of the first hardware bundle. That prevents a
retrospective threshold from being described as preregistered evidence.

The same unchanged profile may be used prospectively for a later execution,
but changing `claim_mode` alone is insufficient: the profile and relevant
execution controls must actually be frozen before the job.

## Evidence boundary

An assessment `PASS` establishes only finite-sample alignment with the declared
primary deterministic-bit expectation, count-label convention, threshold and
confidence method. It does not:

- authenticate a provider, job, timestamp, submitter or calibration;
- prove that the supplied circuit was executed;
- establish full circuit-distribution agreement or physical fidelity;
- establish decoder performance or a fault-tolerance threshold;
- prove the syndrome homomorphism theorem, causation, novelty or quantum
  advantage.
