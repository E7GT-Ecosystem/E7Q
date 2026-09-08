# E7Q pure two-qubit entanglement-assurance pilot

**Profile:** `e7q.entanglement-assurance/pure-two-qubit-v1alpha1`  
**Report:** `e7q.entanglement-assessment/v1alpha1`  
**Status:** optional bounded pilot; not part of E7Q-IR F2 conformance

## Purpose

This pilot assesses whether the ideal pre-measurement state computed for a
supported E7Q program is entangled or separable across the fixed partition
`q[0] | q[1]`. It uses the state-vector reference backend and does not infer
entanglement from sampled measurement counts.

Run the Bell example:

```bash
e7q assess-entanglement examples/bell.e7q -o bell-entanglement.json
```

Run the separable comparison fixture:

```bash
e7q assess-entanglement examples/product-two-qubit.e7q \
  -o product-entanglement.json
```

## Criterion

For a normalized pure state

```math
|\psi\rangle = \sum_{i,j \in \{0,1\}} c_{ij}|i\rangle|j\rangle,
```

form its coefficient matrix `C = (c_ij)` and the reduced density matrix

```math
\rho_0 = C C^\dagger.
```

The joint pure state is separable exactly when `rho_0` is pure. The bounded
numerical rule is therefore:

```text
ENTANGLED_ESTABLISHED  when 1 - Tr(rho_0^2) > tolerance
SEPARABLE_ESTABLISHED  otherwise, within the declared tolerance
```

The report records the joint amplitudes, reduced-density eigenvalues, purity,
linear entropy, partition, tolerance, projection loss, source digest when
invoked through the CLI, and prohibited inferences.

## Supported boundary

The profile supports only:

- exactly two qubits;
- the `statevector` reference backend;
- a static unitary path;
- terminal full-register measurement;
- the fixed bipartition `q[0] | q[1]`.

Valid E7Q programs outside that boundary return `UNSUPPORTED`. Failure to
establish a normalized four-amplitude state returns `UNDETERMINED`. Malformed
arguments, including a non-finite or non-positive tolerance, remain invalid
inputs.

## Evidence boundary

`ENTANGLED_ESTABLISHED` means only that the ideal state calculated by the E7Q
reference simulator is non-separable under the declared criterion. It does not
establish that:

- sampled `00`/`11` correlation alone proves entanglement;
- a provider or physical device prepared the ideal state;
- Bell nonlocality was experimentally demonstrated;
- a hardware execution is faithful to the reference model;
- all entities or systems are physically interconnected.

Hardware entanglement requires a separately specified evidence profile, such
as an entanglement witness, measurements in multiple bases, stabilizer
observations, Bell-test evidence, or tomography, together with provider,
calibration, independence and statistical conditions appropriate to the
claim.

## E7G-T relationship

The joint state is the source object. Partial trace is an explicit projection:
it preserves one subsystem's reduced state while hiding the other subsystem
and the full joint correlation structure. The report therefore retains the
joint amplitudes as the source-return path.

This profile uses established quantum separability mathematics supplied by
E7Q. E7G-T supplies the source/view, projection-loss, criterion and bounded-
claim discipline. EEC-Q rational coefficients, SF families and CFS family
states are not used as quantum amplitudes or entanglement semantics.

The pilot is additive. It does not alter existing E7Q language syntax,
execution semantics, E7Q-IR artifacts, conformance levels, compiler paths or
receipts, and it does not complete the open H2/H3 or Phase 2 gates.
