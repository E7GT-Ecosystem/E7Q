# E7Q-IR Profile Authoring

A semantic profile supplies domain meaning that the universal E7Q-IR core must
not manufacture.

Every profile declares:

- a globally distinguishable identifier and explicit version;
- maturity status;
- supported capabilities;
- artifact kinds and payload constraints;
- validation algorithms and their evidence boundaries;
- reference vectors, negative vectors, and unsupported cases;
- compatibility and version-transition rules.

Profile validators must fail closed when a required capability is absent. They
must keep `not assessed`, `unsupported`, and `failed` distinct.

The initial `e7q.ir.circuit-basic/0alpha1` profile admits OpenQASM source
identity, aggregate count observations, and descriptive total-variation
assessment. It does not establish general circuit equivalence, provider
authenticity, or physical fidelity.

Future QIR, QEC, hybrid, annealing, analog, photonic, and measurement-based
profiles should be independently testable. They may share the core protocol but
must not borrow each other's semantics without an explicit bridge and criterion.
