# v0.12 refoundation decision — 2026-09-13

Repository: `E7GT-Ecosystem/E7Q`  
Role: quantum verification and first direct executable candidate  
Inspected main: `47fd2d8461f55bb55bd9f3d0fe3e5d226d089225`  
Decision status: `RETAIN_NATIVE_REBUILD_PLANNING_LANE`

## Governing sources

- E7G-T v0.12-experimental, revision CFS1, source commit `b7a30b2d56375a5a0646e0c1cab4f621b4de99ca`.
- E7G-T Ecosystem Operating Kernel v0.2, direction `E7-ECO-DIR-2026-09-12.2`.
- v0.11-UC5 is retained as constitutional predecessor and compatibility baseline, not as the source for new architecture.

## Cross-kernel conclusion

v0.12 does not invalidate the evidence, cryptographic, storage or quantum engines already built. It changes the kind of new layer that must be built around them. Repository-wide rewrites are prohibited unless a compatibility test proves that a native abstraction irreversibly collapses a required distinction.

Clean-room product-local contracts are required where the new meaning did not previously exist: dependent families, typed realisation, whole-construction quotation, source-preserving views, explicit identification/restriction, ordered transformation domains and typed non-success outcomes. These contracts must adapt native objects; they must not rename old records and claim v0.12 conformance.

## Mandatory semantic invariants

1. `View`, `Identify` and `Restrict` are distinct and loss is explicit.
2. Shared, independent and constrained alternatives are never silently interchanged.
3. Zero, empty, invalid input, domain error, unsupported and resource limit remain distinct.
4. `Pack(S)` is a quoted whole and is not distributed branchwise.
5. A quote is immutable and inert until an admitted explicit operation acts on it.
6. Phase-level execution requires domain saturation and result congruence.
7. Complete operation order, failure behavior and source identity remain replayable.
8. EEC-Q coefficients are never probabilities, evidence weights, authorization values, deletion semantics or quantum amplitudes.
9. SF realisation is selection under declared criteria, not proof of truth, permission or physical preparation.
10. CFS combines SF-outside with a declared inner algebra; it does not license cross-domain reinterpretation.

## Migration rule

Existing IDs, schemas, APIs, artifacts and evidence remain stable until a versioned migration, positive and negative compatibility vectors, rollback posture and product-specific acceptance gate exist. A new adapter starts namespaced and experimental. Only its own bounded evidence may support its claims.

## Repository decision

Retain all verified quantum semantics, F0–F2 criteria, receipts, resource isolation, external backends and DHSP research. Build the candidate-family, ordered-transform and declared-realisation layer as a new adapter with native quantum types inside; never use EEC-Q coefficients as amplitudes.

## Component disposition

- **Retain:** all currently verified native behavior and immutable published artifacts.
- **Adapt:** only mappings that preserve native identities and expose the additional v0.12 distinctions.
- **Replace:** none at repository level. A product-local adapter may be replaced if adversarial fixtures show semantic collapse.
- **Retire:** no existing native component on the basis of kernel version alone.

## Next bounded package

Q-A1 is already implemented by `e7q.ir.candidate-family/v0alpha1` on the inspected baseline. Preserve it. Make Q-A2 ordered transformation history the next architecture package, followed by Q-A3 declared realisation and Q-A4 receipt binding. Release-wide H10 may continue only as bounded hardening; do not add unrelated capability tracks first.

## Falsification and stop gate

Stop or narrow the v0.12 lane if it adds only vocabulary, changes native meaning without migration, invents independence, hides excluded material, collapses typed failures, distributes whole-construction quotation, loses operation order, or performs worse than the simpler native baseline on the declared product mechanism.

## Claim boundary

This record establishes a development decision, not full-kernel conformance, production readiness, security, hardware validity, professional correctness, market demand or commercial validation.
