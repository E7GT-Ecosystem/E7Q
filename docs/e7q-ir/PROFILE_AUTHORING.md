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

Profiles declare a validator identifier separately from their capabilities.
An installed validator implements deterministic per-artifact and per-relation
methods and returns typed semantic results. It must not return a result for a
foreign subject or cite evidence absent from the graph. A validator returning
no results yields `NOT_ASSESSED`; an unknown profile or missing validator yields
`BLOCKED`; unsupported syntax or scale yields `UNSUPPORTED`; and a violated
semantic rule yields `FAIL`.

The installed `e7q.ir.circuit-basic/0alpha1` and
`e7q.ir.native-execution/0alpha1` profiles remain distinct. Circuit criteria do
not validate native execution, and native deterministic replay does not validate
generic core, legacy, compiler or external-circuit artifacts. The universal
`e7q.ir.core/0alpha1` profile intentionally has no semantic validator.

The native profile admits only bounded trusted-local statevector source and
independently reparses, readmits, reruns and reverifies its complete evidence path.
Its F2 PASS establishes faithful graph semantics, not native invariant success,
hardware execution, provider authenticity, physical fidelity or broader circuit
equivalence.

Future QIR, QEC, hybrid, annealing, analog, photonic, and measurement-based
profiles should be independently testable. They may share the core protocol but
must not borrow each other's semantics without an explicit bridge and criterion.
# Phase 1B implementation update

The bounded Phase 1B payload validator now supersedes the framework-only
implementation notes below. See [Phase 1B scope and limits](PHASE_1B.md).
Digest-only graphs remain inspectable but block byte-dependent semantic checks;
transformation equivalence and execution semantics remain unassessed.
