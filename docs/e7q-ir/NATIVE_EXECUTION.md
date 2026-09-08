# Native execution into E7Q-IR

The explicit execution adapter is the installed native semantic path for Phase 2.
It links preserved source, intent, parsed representation, execution, observation
and assessment artifacts while reusing the existing native `parse()`, `run()`,
`verify()` and `backend_profile()` implementations. It introduces no parser,
simulator, verifier, QCEC dependency or external runtime dependency.

## Run and replay

```sh
python -m e7q.ir.native examples/bell.e7q \
  --created-at 2026-09-07T00:00:00Z \
  --output /tmp/bell-native-ir.json
python -m e7q.cli ir validate /tmp/bell-native-ir.json \
  --level F2 -o /tmp/bell-native-f2.json
```

Python callers use `execute_native(raw_bytes, created_at=...)`. This API executes
trusted local native source. The legacy preservation importer remains non-executing.
The supplied record timestamp is retained but is not authenticated chronology.

## Versioned profile

New graphs use `e7q.ir.native-execution/0alpha1` and require an exact installed
`e7q.ir.validator.native-execution/0alpha1`. The generic `e7q.ir.core/0alpha1`
profile deliberately remains validator-free. Historical native graphs using the
core profile remain readable at F0/F1 and stay F2 `BLOCKED`; their envelopes,
identifiers and meanings are not rewritten or retrospectively upgraded. Generic
legacy, compiler and core-profile artifacts likewise cannot acquire native F2.

Every native artifact uses the native profile so relation endpoints negotiate one
profile. Capabilities are specific to source preservation, intent, parser
projection, reference execution, observation and native verification. The five
relations are `validated`: source-to-intent representation, source-to-parsed
projection, representation-to-execution, execution-to-observation and
assessment-to-observation.

## Admitted scope

The profile admits only:

- trusted local UTF-8 E7Q source up to 1 MiB;
- the statevector backend with an explicit seed;
- at most 8 qubits, 8 classical bits, 100,000 shots and 1,024 expanded operations;
- static gates followed by exactly one terminal full-register measurement;
- no noise, dynamic measurement/control or assertions.

The existing parser runs first. The remaining admission limits are reapplied before
reference-simulator allocation. Unsupported features are `UNSUPPORTED`; exceeded
resource limits are `BLOCKED`; mismatched recomputed evidence is `FAIL`; missing
or malformed validator results remain `NOT_ASSESSED` or `FAIL`. No exception,
unknown format, stale declaration or inconclusive state can become `PASS`.

## Independent semantic reconstruction

The installed validator starts from the preserved source content rather than
trusting graph verdicts. It:

1. verifies the exact UTF-8 bytes, byte length and SHA-256 declaration;
2. reparses with the existing native parser and reapplies all admission limits;
3. reconstructs intent and the complete ordered expanded representation;
4. executes the existing seeded reference statevector implementation;
5. calls the existing native verifier;
6. compares the execution backend profile, implementation versions and complete
   Proof-of-Path;
7. compares counts, probabilities, bit width, label order and probability basis;
8. compares every assessment field, including checks, status and first failure;
9. validates profile capabilities, limitations, provenance references and all
   relation endpoints, criteria, preservation, loss, assumptions and status.

Semantic conformance is separate from native program success. A graph that
faithfully records and recomputes a native invariant `FAIL` can pass F2 while its
assessment remains `FAIL`; neither the graph nor the validator rewrites that
program verdict as success or as a supported scientific claim.

## Mapping and loss

| Artifact | Retained and checked information |
| --- | --- |
| Source | Exact content, byte length, SHA-256 and stable source envelope |
| Intent | Path, invariants, backend, shots, seed and trusted-local-source boundary |
| Representation | Every parsed Program field and ordered expanded operation |
| Execution | Backend capability boundary, package versions, seed, shots and complete Proof-of-Path |
| Observation | Counts, model probabilities, bit width and explicit clbit-ascending labels |
| Assessment | Entire native verifier result, including checks, FAIL and first-failure fields |

The parser projection declares preservation of parsed fields, expanded operation
order and the original source reference. It loses comments/formatting and subpath
call boundaries only from the parsed projection; the source artifact still retains
them. State amplitudes and per-shot trajectories are not exported. Counts lose
phase information and model probabilities are not hardware observations.

## F2 conclusion and exclusions

The maximum conclusion is:

> Under the installed bounded native-execution profile, this graph faithfully
> records the deterministic parsing, admitted reference execution, observation
> and native-verifier result recomputed from the preserved source.

F2 does not establish hardware execution or fidelity, provider authentication,
authenticated chronology, compiler correctness, equivalence to an external
circuit, exact-algebraic equivalence, scalability, computational advantage, F3
authentication or F4 reproduction.

## Public evidence and completion status

The deterministic Bell graph is
`examples/e7q-ir/native-execution-bell-graph.json`; its F2 report is
`examples/e7q-ir/native-execution-bell-f2.json`. The graph ID is
`sha256:c9fe173151778dcae3df500674a53c063c32119c6b600bfe40c0b82f00e59598`.
All 17 artifact/relation semantic checks pass and the highest level is F2.
Focused verification passes 80 tests; the integrated IR/native/compiler/QCEC/
receipt surface passes 250; and the full suite passes 567.

Phase 2 and H5 are complete because the native and external paths, topology
compiler Proof-of-Path, legacy preservation and receipt mapping are all linked
through inspectable E7Q-IR evidence; legacy formats remain readable; declared
losses remain explicit; and only the separately versioned native profile is
installed as default semantic truth. Optional Aer, PyZX, provider authentication,
K12/CFS, OpenQASM 3, QIR, independent review and broader benchmark work remain
separate gates and are not started by this package.
