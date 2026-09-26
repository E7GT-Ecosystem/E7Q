# E7Q quantum-view adapter plan

**Status:** draft plan only; no schema, executor, native identity, or product semantics are changed by this document. Depends on review of the companion E7G-T v0.15 reuse/gap audit.

## Exact dependencies and non-migration

- E7Q `main`: `86447771544e836222847ed04b0236cc27f2881b` (2026-09-26 inspection).
- E7Q merged #78 pilot scope: `docs/e7q-ir/SECOND_PRODUCT_JOINT_PILOT_SCOPE.md`, a synthetic planning pilot using correlated alternatives and signed rational **formal construction coefficients**.
- E7Q #79 review head: `140608632a8fe8883b87a45e23a85259a42783e6`; it is a separate formal-rational Joint-to-Q-A1 mapping. It does not supply quantum state, probability, amplitude, measurement, or joint-device semantics.
- E7G-T source for new mapping: v0.15/MSC1, kernel SHA-256 `5b1e9913cf24b80612f81014b8cc7efc7574d43402a2a188a17daa096c0c621a`, manifest baseline `86653557f5b5780a984f3a2dab226213ebbe3702`. E7G-T public `main` `5b5cb5f10ddd913df66f5d9f65fbe059a2e33193` contains v0.15 as the canonical experimental source for new specifications. This does not establish implementation fidelity or calculus completion; those gates remain open.
- E7C / E7G-T check suites and #134/#135 Python-to-Lean proof links remain separate gates. This plan does not close them.

The adapter should be independently versioned and opt-in, e.g. `e7q.quantum-view/0alpha1` only after review. Keep Q-A1/Q-A2/Q-A3/Q-A4 identities, circuit evidence, receipts and outcomes unchanged. No edits to #79 or to current E7Q execution schemas belong in this source-map increment.

## Proposed typed contract

For a finite-dimensional declared Hilbert space `H`, a versioned preparation domain `D`, context set `C`, and finite outcome set `O_c` per context:

```text
QuantumViewAdapter/0alpha1:
  system: HilbertSpace[dimension, basis, numeric_policy]
  preparations: D
  prepare: D -> DensityOperator[H]               # rho >= 0, tr(rho)=1
  context: ContextId[edition]
  effects: (c: C, o: O_c) -> PositiveOperator[H]  # sum_o effects(c,o) = I
  distribution: (rho,c) -> Dist[O_c]              # Born trace rule
  import_physical_record: (record, provenance, preparation_id, run_id, c, protocol) -> ValidatedRecord | typed failure
  simulated_sampler: optional (rho,c,seed,simulator_edition) -> SimulatedOutcomeRecord[O_c]
  instrument: optional (c,o) -> CPMap[H -> H]
  post_state: optional (rho,c,o) -> DensityOperator[H]
  state_fibre: (view_family, v, W) -> {rho in W | observations(rho) ≈ v}
  preparation_fibre: (view_family, v, D) -> {d in D | observations(prepare(d)) ≈ v}
  joint_device: (c1,c2) -> success(parent, verified_marginals) | incompatible(obstruction_certificate) | invalid_input(diagnostic) | unsupported(capability) | undetermined(reason) | resource_limit(bound)
```

The adapter must keep five things distinct: (1) preparation description, (2) operational whole `rho`, (3) predicted outcome distribution, (4) imported physical outcome record from one run (or a separately typed simulated record), and (5) post-measurement state. Include the system, preparation and context editions, domains, partiality, canonical identity/equality policy, provenance, numeric precision/tolerance, and resource bounds in any eventual artifact.

A physical outcome record is imported with provenance and run identity. The Born rule gives a distribution; it does not determine the result of a particular physical run. An optional simulator may sample only a separately typed simulated record, binding its seed and simulator edition. Distributions collected on separately prepared runs do not imply two actual outcomes on one run. If a state transition is needed, specify an instrument `I_o`; probability is `tr(I_o(rho))`, and the normalized conditional state is `I_o(rho)/tr(I_o(rho))` only for nonzero probability. Otherwise omit state update from the first build.

## Operational joint-observation rule

A positive coupling of two state-specific marginals is insufficient for a device claim. For contexts `c1,c2` with POVMs `E[a]`, `F[b]`, joint measurability means a single parent POVM `G[a,b]` such that

```text
G[a,b] >= 0
sum_(a,b) G[a,b] = I
sum_b G[a,b] = E[a]       for every a
sum_a G[a,b] = F[b]       for every b
```

The parent and equalities are operator-level and therefore hold uniformly over the declared admitted states. The adapter may offer a separate `state_specific_coupling` calculation for comparison, explicitly typed as a probability coupling and never as proof of a joint measurement. Failed numerical optimization may be `undetermined` or `resource_limit`, not `incompatible`; `incompatible` needs an exact certificate/theorem for the declared finite model.

## Bounded qubit fixture to implement after audit review

Use `H=C^2`, exact Pauli matrices and sharp POVMs `E_A(s)=(I+sA)/2` for `A in {X,Y,Z}` and `s=±1`.

### Reconstruction ambiguity

For `rho_±=(I±aY)/2`, `0<a<=1`, calculate:

```text
p(s | rho_+, X) = p(s | rho_-, X) = 1/2
p(s | rho_+, Z) = p(s | rho_-, Z) = 1/2
p(s | rho_±, Y) = (1 ± s*a)/2
```

Declare `D` to contain at least these two preparations, `W` to be qubit density operators, and the selected view family to be the X and Z distributions from identically prepared **separate runs**. Its state fibre `F_W(v)={rho in W | views(rho)=v}` contains both `rho_+` and `rho_-`; adding Y distinguishes them for `a>0`. The separate preparation-description fibre `F_D(v)={d in D | views(prepare(d))=v}` contains their admitted preparation descriptions, possibly more if `prepare` is non-injective. This is non-identifiability under the selected views, not a hidden exact-value assignment.

### Sharp incompatibility

Return `incompatible` only with a verified obstruction certificate. Prove or independently validate that sharp Pauli X and Z have no common parent POVM with those sharp marginals. Positivity plus a sharp projector marginal constrains every parent effect to the corresponding eigenspace. Nonorthogonal X and Z eigenspaces cannot simultaneously contain a nonzero positive effect; all parent effects would be zero, contradicting normalization. For `success`, return the parent POVM and verify positivity, normalization and both marginals. Preserve `invalid_input`, `unsupported`, `undetermined` and `resource_limit` as distinct outcomes. State the exact operator assumptions and all-state scope in the implementation report.

### Permitted unsharp comparison

For `E_X(x)=(I+x*eta*X)/2` and `E_Z(z)=(I+z*eta*Z)/2`, a parent is `G[x,z]=(I+x*eta*X+z*eta*Z)/4`. Its least eigenvalue is `(1-eta*sqrt(2))/4`, so it is positive for `0<=eta<=1/sqrt(2)`, and its marginals are the required POVMs. Include a rationally checkable interior value such as `eta=1/2`; report the boundary separately if numerical arithmetic obscures exactness. This guards against a classifier that rejects every joint observation.

## Positive and negative fixtures

Planned positives: Born normalization; X/Z identical distributions for `rho_±`; Y separation; non-singleton and then singleton-within-fixture reconstruction fibres; exact rejection certificate for sharp X/Z parent; accepted unsharp parent and verified marginals.

Planned negatives: nonpositive or unnormalized density matrix; POVM effects not positive or not summing to identity; forged parent with incorrect marginal; state-specific coupling presented as universal joint device; actual outcome invented from a distribution; same-run identity omitted where an actual pair is asserted; unsupported dimension or operation; undecidable numeric boundary; and configured memory/time/term budget exceedance. Preserve separate outcomes for `invalid_input`, `unsupported`, `incompatible` (with certificate), `undetermined`, and `resource_limit`.

Standard calculations and expected values must be saved in a reference file and independently recomputed by a second implementation or exact hand-check script. An assertion suite by itself is finite exercise evidence, not a universal proof. Compare against a competent full quantum calculation; the marginal-only/coupling comparison is not a meaningful claim of advantage by itself.

## What this adds and what it does not

The adapter can make source identity, contexts, domains, view fibres, operation order and evidence replay explicit alongside standard Hilbert-space calculations. It may improve compositional bookkeeping or reviewability; that benefit requires an actual workflow comparison against a competent conventional representation. The qubit is an analogue of context-dependent views, not a position–momentum derivation. No statement here evades `Delta X Delta P >= hbar/2`, establishes new physics, validates a hidden ontology, or asserts product improvement.

## Next gate

First obtain substantive review of the v0.15 reuse/gap audit and this plan at exact draft heads. Then implement the smallest independently versioned E7Q adapter in a separate draft branch, with exact-head math/physics review. Only after that gate should a continuous-variable X/P model specify operator domains, spectral measures, units, and separate preparation uncertainty, measurement error/disturbance, and joint-measurement unsharpness. Any physical hypothesis beyond standard quantum mechanics needs ontology, response law, observable departure, regime, baseline, falsifier and feasible measurement route.
