# E7Q / E7Q-IR direction

Direction ID: `E7-ECO-DIR-2026-09-06.1`. Product repository: `E7GT-Ecosystem/E7Q`.

## Destination and ownership

E7Q-IR is the single quantum representation and evidence direction, including the former quantum Fabric. It connects intent, source/compiled representations, transformations, hardware/execution context, observations and bounded claims. The native E7Q language is one front end; ordinary external workflows must be usable without adopting it.

E7Q-IR owns quantum-specific semantics. Shared ecosystem transport preserves native artifacts and cannot confer semantic equivalence, provider authentication or physical fidelity. Preserve existing native formats and IDs. Do not recreate a parallel quantum Fabric or require a universal ecosystem platform.

## Next work

Read the actual `ROADMAP.md`, `docs/e7q-ir/ARCHITECTURE.md`, `PROTOCOL.md`, `CONFORMANCE.md`, `PROFILE_AUTHORING.md` and `SECURITY_AND_TRUST.md`. The authoritative build plan is being published in [PR #34](https://github.com/E7GT-Ecosystem/E7Q/pull/34); use `docs/e7q-ir/BUILD_PLAN.md` when present, or the reviewed plan in that PR.

The inspected code baseline `b7dc357715529ecc7f0426b708ae56320a204e2b` implements F0/F1. If the F2 framework is still absent, implement that bounded framework first. If another builder has already implemented it, review its actual acceptance evidence and continue from the next incomplete phase. Do not restart or replace their work.

Acceptance must preserve F0/F1 meanings, expose unsupported validators/relations, reject semantic overclaims and retain deterministic results. Run meaningful focused cases and the existing product regression suite (`python -m pytest -q`). Separately exercise an independently supplied external workflow. Hardware execution, authentication, QEC and additional modalities require their own gates.

## Coordination

Declare the current work package and shared interfaces in your PR check-in. The user sponsors overall ecosystem coordination; the builder retains responsibility for its product implementation. A queued run or a draft PR is not a completed gate. A collaborator or compiler integration must not become an undeclared mandatory dependency.
