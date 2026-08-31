# E7G-T upstream relationship

E7Q is a downstream experimental application of the E7G-T Unified
Geometry-Thinking Kernel. The upstream kernel contributes a disciplined
vocabulary for configuration, possibility families, transformations, paths,
structured objects, processes, projections, results, contexts, invariants,
operational equivalence, Proof-of-Path, and temporal geometry.

E7Q pins the following upstream reference for this release candidate:

- **Version:** E7G-T v0.11-UC5
- **Title:** *E7G-T Unified Geometry-Thinking Kernel — Extensional–Projective–Phase Geometry of Configurations and Time*
- **Immutable source:** [kernel at commit `4eb9c49082ab89a423de66f17229c2feeb7b3f0e`](https://github.com/wingate-ag/E7G-T/blob/4eb9c49082ab89a423de66f17229c2feeb7b3f0e/E7G-T_Kernel_v0.11_UC5_Unified_Public_Reference_Specification.md)
- **Git blob:** `a248133be280b3f3415f8dd8f5342833195f08df`
- **Compatibility review:** 2026-08-31

E7Q operationalizes a bounded subset of the upstream temporal architecture:
temporal carriers, declared order, temporal projection, preservation and loss,
inquiry-relative temporal phase, and boundary-crossing evidence. It does not
copy the complete upstream kernel.

UC2 preserves the UC1 normative core and adds an informative observational-
claim pilot module. E7Q exposes that module only through the opt-in
`e7q.observational-claim-pilot/v1alpha1` profile. Omission of the pilot does not
make an E7Q artifact non-conforming. The pilot distinguishes observer-indexed
records, bounded observational claims, interpretations, shared divergence and
unknowns, and any declared temporal-extension bridge.

UC3 preserves the normative core and the UC2 pilot, and adds a separate
informative temporal-orientation module. E7Q exposes it only through the
opt-in `e7q.temporal-orientation-pilot/v1alpha1` profile. The pilot declares
observer locality and directional relation kinds, separates reverse
representation from time-reversal symmetry and causal reversal, distinguishes
history-whole membership from simultaneity, and treats compatible-history
relevance narrowing as epistemic unless a stronger bridge is supplied.

The UC3 profile is independent of E7Q's computational-basis measurement update.
It does not reinterpret quantum state update as observer-relative history
relevance, retrocausation, time neutrality, or ontological collapse.

UC4 retains the UC3 temporal-orientation module, including Candidate Law T0:
temporal extension, admitted order, representational orientation, and
directional meaning are distinct modelling ingredients. E7Q already reflects
this separation by emitting temporal evidence independently while the
orientation pilot remains explicitly opt-in; a temporal carrier or ordered
artifact does not by itself select an orientation.

UC4 additionally introduces an informative topological-overlay pilot. E7Q does
not invoke that pilot merely by using its established `topology` option or JSON
field. In those legacy E7Q interfaces, `topology` means an undirected quantum
hardware coupling graph used for adjacency and SWAP routing. It is not a
declared mathematical topological space `(X, tau)`, and graph adjacency,
routing paths, and routing boundaries are not asserted to be topological
neighbourhoods, topological paths, or topological boundaries. A future E7Q use
of the UC4 overlay would require an explicit carrier, topology, construction,
and inquiry-relevant topological claim.

UC5 retains the preceding core and pilots and adds the informative
relative-support overlay. E7Q exposes it only through the opt-in
`e7q.relative-support-pilot/v1alpha1` profile. The profile declares the
alternative carrier, support semantics, provenance, update rule, calibration
posture, dependencies, separate exclusion rule, validity window, and reopen
condition. It preserves low-support alternatives until separately excluded
and does not treat stronger support as truth, probability, phase determinacy,
causation, or an action rule.

The comparative-experiment profile supplies one quantum-domain case relevant
to UC5 Pilot J. This does not satisfy Pilot J's cross-domain promotion gate or
promote the upstream module into E7G-T's normative core.

E7Q does not infer quantum physics from that vocabulary. Executable meaning
comes from established quantum theory: Hilbert spaces, tensor products,
unitary operators, channels where supported, the Born rule, classical control,
and declared backend constraints.

This repository must not silently fork or rewrite the upstream kernel. A future
upstream pin requires an explicit compatibility review and release note.
