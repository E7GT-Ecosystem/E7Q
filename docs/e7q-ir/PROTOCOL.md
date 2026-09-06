# E7Q-IR Protocol v0alpha1

E7Q-IR is the authoritative quantum protocol namespace. The `e7q.ir.*`
identifiers below replace the unpublished experimental `e7q.fabric.*`
identifiers; no wire-compatibility claim is made for the discarded alpha
namespace.

## Artifact envelope

An artifact contains:

- `schema`: stable object-family identifier;
- `artifact_id`: SHA-256 content identity computed with `artifact_id` omitted;
- `kind`: the role played in the evidence path;
- `profile`: profile identifier, version, and required capabilities;
- `provenance`: creation time, declared actor, and source artifact references;
- `payload`: kind- and profile-specific content;
- `limitations`: explicit boundaries retained with the artifact;
- optional `extensions`: namespaced experimental material.

Canonicalization in v0alpha1 uses UTF-8 JSON with keys sorted, no insignificant
whitespace, Unicode retained, and non-finite numbers rejected. This is the
named E7Q v0alpha1 encoding and does not claim full RFC 8785 conformance.

## Evidence graph

A graph embeds its artifacts and typed relations. Its `graph_id` is computed
over the complete graph with `graph_id` omitted. Relation identities use the
same rule with `relation_id` omitted.

Relations are deliberately small: `represents`, `transforms`, `produces`,
`observes`, `assesses`, `supports`, `constrains`, and `derived-from`.

A `transforms` relation must state a criterion, preservation declarations, loss
declarations, assumptions, and validation status. A declaration of preservation
does not pass semantic verification merely by being present.

## Claim contract

A claim payload must contain:

- a human-readable statement;
- a claim type;
- direct evidence references;
- support status;
- boundaries;
- prohibited inferences.

The evidence path remains inspectable through both the claim references and
typed graph relations. E7Q-IR does not infer a broader claim from a narrower
assessment.

## Versioning

`v0alpha1` is intentionally unstable. A future breaking schema uses a new
schema identifier. Implementations must reject unknown required capabilities
for semantic processing, while remaining able to report structural facts about
an otherwise valid envelope.
