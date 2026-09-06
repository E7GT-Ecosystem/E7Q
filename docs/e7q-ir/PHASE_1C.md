# Phase 1C: bounded UTF-8 byte identity

Implemented criterion: `{"id":"e7q.ir.utf8-byte-identity","version":"1"}`.
Optional required capability: `circuit.identity.utf8-bytes`.

The criterion compares embedded UTF-8 bytes of source/representation endpoints
under `e7q.ir.circuit-basic/0alpha1`. Both endpoints must pass the bounded
OpenQASM 2 importer, content digest and byte-length checks. Each source has a
262144-byte limit. No files are fetched and no supplied code is executed.

The relation must declare `preserves: ["utf8-bytes"]`, `loses: []`, and
`assumptions: []`. Other preservation claims, versions or criterion options are
unsupported. Matching content passes only with `validation_status: "validated"`;
a contradictory declaration fails rather than being rewritten. Missing content
or excessive size blocks assessment. Corrupt digests/lengths fail, including
after the artifact envelope is rehashed. Unsupported formats/syntax remain
unsupported. Unknown criterion IDs remain `NOT_ASSESSED`.

Different bytes fail byte identity, including comments and whitespace. This
does not establish quantum-semantic inequality. No normalization, phase
tolerance or permutation is applied. Results cite the endpoint IDs, relation
subject and versioned criterion. F0/F1 meanings are unchanged; the new capability
is additive within the experimental profile.

## Fixture and scope

```bash
python -m e7q.cli ir validate examples/e7q-ir/byte-identity-graph.json --level F2
```

The fixture contains a source, representation and identity relation. Its F2 PASS
is scoped to this graph and criterion; it contains no execution or observations.
It does not authenticate a provider or establish physical fidelity, or that a
compiler actually produced an output.

Full Phase 1B and Phase 1C remain incomplete. Broader
unitary/global-phase, measurement and channel criteria remain pending. The H
versus u2 demonstrator is not promoted to verified equivalence. Execution and
standalone transformation-artifact semantics remain unassessed. The byte-identity increment
implements the first transformation criterion in build-plan package R1.

## Parsed structural identity, version 1

The next R1 increment implements
`{"id":"e7q.ir.openqasm2-structural-identity","version":"1"}` with capability
`circuit.identity.parsed-structure`. This compares the existing
`e7q.openqasm2-circuit/v1alpha1` importer projection: `schema`, `language`
(including ordered, unresolved include names), `registers`, and `operations`.
Source hashes, source character counts, proof wrappers and derived summaries
are excluded. Original artifact identities and source text remain retained.

Required relation contract:

```json
{
  "preserves": ["parsed-circuit-structure"],
  "loses": ["source-text-and-comments", "gate-name-case",
            "register-expansion-spelling", "numeric-index-spelling",
            "declaration-interleaving"],
  "assumptions": []
}
```

Loss-list ordering is immaterial; duplicate or missing entries are unsupported.
The importer strips comments/outer whitespace, lowercases gate names, expands
whole-register measurements/barriers, parses indices as integers and groups
quantum/classical declarations separately. These are explicitly declared
projection losses, not an assertion that every spelling is valid standard QASM
or universally interchangeable. Parameter strings retain internal whitespace;
no algebraic evaluation, renaming, operation reordering or gate equivalence is
performed. Conditions, barriers, measurement destinations and operand order
remain in the compared operations. Changed include names fail identity; matching
names do not prove matching external definitions. No includes are loaded.

Matching projections require a declared `validated` status. Different structures
fail this criterion without establishing quantum-semantic inequality. Unknown
options/versions are unsupported. The H/u2 example remains unverified.

```bash
python -m e7q.cli ir validate examples/e7q-ir/structural-identity-graph.json --level F2
```

### Shared pre-parser resource guard

All circuit-profile checks now reject declared register widths above 4096,
aggregate widths above 8192, width literals longer than 128 characters, or a
conservative expansion estimate (aggregate widths times semicolon count after
line-comment stripping) above 262144. These checks occur before the legacy
importer can allocate whole-register expansions or compute large conditions.
They supplement the existing source-byte limit and may block otherwise valid
large programs. The conservative guard intentionally does not change the legacy
importer for unrelated callers. Parser projection changes require review of the
versioned identity criterion and its fixtures.
