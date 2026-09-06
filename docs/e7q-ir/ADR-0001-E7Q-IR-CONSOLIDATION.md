# ADR-0001: Consolidate the Quantum Fabric into E7Q-IR

**Status:** accepted

**Decision date:** 2026-09-06

**Applies from:** E7Q-IR `v0alpha1`

## Context

The experimental `fabric-v0.1` branch introduced a content-addressed artifact
envelope, typed evidence graph, transformation and claim contracts, capability
profiles, F0/F1 conformance, and an external OpenQASM/counts demonstrator. The
E7G-T Ecosystem Operating Kernel subsequently identifies E7Q-IR as the proposed
evidence-native, hardware-aware quantum intermediate representation and
execution protocol.

The two concepts address the same quantum evidence path. Keeping them as
independent architectures would create overlapping schemas, commands,
extension mechanisms, and product claims.

## Decision

E7Q-IR is the sole authoritative quantum protocol. The experimental E7Q Fabric
implementation becomes E7Q-IR's Evidence Core and uses the `e7q.ir.*` schema
namespace, `e7q.ir` Python package, and `e7q ir` CLI command.

The native E7Q language is one front end into E7Q-IR. OpenQASM, QIR, quantum
SDKs, provider formats, and future modalities may enter through independently
versioned adapters and semantic profiles without adopting that language.

Because the discarded `e7q.fabric.*` namespace was unpublished experimental
work, no permanent compatibility alias or wire-format migration is provided.
All repository fixtures and consumers move directly to `e7q.ir.*`.

The separately proposed E7 Global Architecture Fabric is not implemented here.
That term is reserved for a possible future cross-domain integration layer and
must not be used as a second name for E7Q-IR.

## Consequences

- Quantum architecture, implementation, conformance, and roadmap work has one
  direction and one vocabulary.
- Existing Evidence Core functionality is preserved rather than rewritten.
- E7Q-IR remains honest about maturity: v0alpha1 establishes F0/F1 evidence
  structure, not a complete executable quantum IR or verified hardware path.
- F2 semantic profiles, transformation validation, provider authentication,
  and replication can evolve without introducing another umbrella protocol.
- Any future cross-domain Fabric must consume explicit E7Q-IR contracts rather
  than sharing its internal namespace.

## Superseded terminology

| Superseded | Authoritative |
| --- | --- |
| E7Q Fabric | E7Q-IR |
| `e7q.fabric.*` | `e7q.ir.*` |
| `e7q fabric` | `e7q ir` |
| `src/e7q/fabric` | `src/e7q/ir` |
