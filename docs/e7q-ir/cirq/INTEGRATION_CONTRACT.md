# E7Q-CIRQ/0.1 — bounded optional local candidate

Status: local candidate, not a merged/released profile or complete handoff acceptance. G0 decision: `CAPABILITY_AUDIT.md`. Reuse E7Q's `Program`, exporter, native comparison criteria and E7Q-IR v0alpha1 envelopes/graph. No kernel, released schema or existing criterion is changed. Code remains public Apache-2.0 beside `adapters.py`; documentation retains repository documentation terms. No material is moved across the component-register/commercial boundary.

## Interface and trust boundary

`e7q.cirq_interop.admit_cirq_source(text)` returns an existing `Program` or raises `CirqInteropError` with `status` and `reason`. This is NOT a general Cirq/Python importer. It accepts only the bounded AST dialect of the current `adapters.cirq_source`: unaliased `import cirq`; `qubits = cirq.LineQubit.range(N)`; `circuit = cirq.Circuit()`; zero to 64 whitelisted `circuit.append(cirq.GATE(qubits[...]))` expressions; exactly one final `circuit.append(cirq.measure(qubits[0], ..., key="c"))`. The exporter uses explicit measurement operands, not star expansion. Whitespace/comments are syntax trivia; byte identity is nevertheless retained separately.

N is 1 or 2, and declared idle wires remain in the `Program`. Gates: X, Y, Z, H, S, T, CNOT→CX, CZ, SWAP at canonical powers only. Operation order and operand order are preserved. No aliases, assignments beyond these declarations, calls beyond the allowlist, gate powers/decompositions, symbols, rotations, channels, reset, custom gates, object/protocol loading, imports besides cirq, control flow, tags, callable constructors, serialization hooks, partial/repeated/mid-circuit measurement, key changes, inversion/confusion maps or ambiguous classical destinations. No `exec`, `eval`, pickle, general Cirq JSON or arbitrary object pickling is used. This importer does not execute even the admitted import statement.

`evaluate_roundtrip(native_source, *, returned_source=None, criterion="tolerance", tolerance=1e-9, timeout_seconds=15.0)`:
1. Bound/parse and preflight native E7Q input; require statevector backend, admitted gates, equal quantum/classical widths and a terminal complete identity measurement.
2. Call the existing exporter unchanged. Preserve exact native, exported and returned UTF-8 source in separate source artifacts. Returned source defaults to exporter output; explicit returned source may represent a different admitted circuit, so mismatch/counterexample tests are meaningful.
3. Safely admit the returned dialect into `Program`; require equal declared width.
4. Run existing `language.compare`/`comparison_result` on original and admitted Programs under the requested existing criterion.
5. Start the pinned optional SDK in a resource-limited child, passing only validated primitive JSON operations. Construct known Cirq gates, not untrusted source. Simulate the unitary prefix without terminal measurement using `cirq.Simulator(dtype=complex128, split_untangled_states=False)`, explicit ascending LineQubit order and every computational-basis input. Compare Cirq's finite matrix to E7Q's independent native unitary with fixed 1e-9 max-entry consistency tolerance.
6. Emit source/representation/execution/observation/assessment/claim artifacts and typed links; run actual existing F1 validation. Include the native comparer proof, simulator matrix, zero-input probability diagnostics, actual Python/NumPy/Cirq versions and limitations.

`replay(result, native_source, **same_explicit_options)` recomputes admission, native assessment, SDK observations and the complete deterministic graph, comparing full canonical content. Caller supplies independent source/options; values in an untrusted result are not treated as the recipe authority. Only complete PASS/FAIL domain results are replayable. This is local same-implementation consistency, not appointed independent reproduction or authentication.

## Preservation/loss table

| Concern | Preservation and loss |
|---|---|
| Input identity | Exact source UTF-8 is in existing hashed artifact payloads; semantic/typed normalization is separately represented. No claim of source-byte equality for transformed returned circuits. |
| Quantum order | Declared width includes idle wires. q0 is first tensor axis/MSB in both admitted E7Q and explicit Cirq order. Gate control/target order stays explicit. Moment scheduling is not exported as timing evidence. |
| Measurement | Only one full ascending q→c map and key `c` admitted. Bit/key changes are refused, not ignored. Measurement is excluded from unitary simulation and this projection is named before assessment. |
| Native metadata | Original source retains context, seed, shots, invariants and path definitions. Exported circuit does not preserve these as SDK execution semantics; imported Program does not recover them. Native invariants are not evaluated as Cirq claims. |
| Parameters | Canonical gate constants only. Arbitrary numeric rotations and symbols are unsupported, not rounded into equality. |
| Initial state | Each computational-basis state for mapping consistency; initial zero separately for state/probability diagnostics. No arbitrary state-family theorem inferred from one input. |
| Precision | Cirq complex128 and actual NumPy version; finite observations required. Native criteria retain their existing exact/numerical meanings. |
| Seeds/shots | No sampling or measurement collapse; `method.sampling_status=NOT_ASSESSED`; no stochastic seed or finite-shot claim. Native source metadata cannot silently become a simulator run parameter. |
| Identity/time | Artifact `created_at=1970-01-01T00:00:00Z` is a documented identity sentinel, not event time. Actual execution telemetry is not hashed into immutable input identity. Different environment or tolerance/recipe may produce different evidence. |

## Criterion and status discipline

Allowed existing names: `exact`, `tolerance`, `global-phase`, `measurement`. Exact is native zero floating-point difference, NOT a symbolic theorem. Global-phase allows one input-independent scalar. Measurement compares all basis-column ideal probabilities in the native existing implementation, not just initial-zero or sampled counts. State-zero and measurement-zero diagnostics remain separately labeled numbers; they do not introduce or broaden an E7Q criterion.

A phase-only fixture is X; Z; X; Z = −I, not Z; Z. Z versus I has equal initial-zero states/probabilities but is not all-input unitary equivalent. H; Z versus H has equal initial-zero Z probabilities, but different states and an interference counterexample. Independent test oracles derive these small matrices/distributions explicitly.

PASS/FAIL are only the existing native domain comparison result, after SDK mapping consistency. Non-assessment outcomes include UNSUPPORTED (missing/wrong SDK or out-of-profile semantics), RESOURCE_REFUSED (known size/allocation/resource control), TIMEOUT and ERROR (bad input/worker/inconsistent mapping). None is quantum inequality. SDK mismatch is ERROR, never a forwarded equivalent=true assertion. Claims explicitly state the evaluated criterion/outcome and limited scope; a graph supporting a reported negative assessment does not claim equivalence.

## Bounds and process control

Per-source UTF-8: 16384 bytes; AST: 2048 nodes/depth32; qubits: 2; unitary operations: 64; primitive worker request/response: 32768 bytes; native preflight budget: 256MiB. Parent checks source character lower bound before UTF-8 allocation. SDK child requests POSIX address-space limit 3GiB and CPU limit 10s before importing Cirq. Parent wall deadline defaults15s and cannot exceed30s; timeout kills and reaps the child. Failure to install POSIX limits fails closed. Thread-count environment changes are per child, not parent-global. There are no arbitrary decompositions or circuit-object serialization. These bounds are an engineering envelope, not a general hostile-Python sandbox or measured RSS guarantee. Larger circuits/rotations/noise are refused, not silently degraded.

## Evidence/conformance and remaining gates

Existing graph envelopes/kinds/relations carry content and reference integrity at **F1**. The actual native comparer independently computes the named bounded relation; the numerical cross-SDK check tests gate/axis mapping. There is no new registered Cirq semantic F2 validator, no F3 provider authentication, and no hardware/scalability/new-physics claim. Do not describe F1 as scientific validity of supplied SDK observations. Historical F2 fixtures and validators remain unchanged.

This local slice covers the safe executed return path and independently tested criterion boundaries. Full /0.1 acceptance, external reviewer reproduction, dedicated semantic-conformance extension, optional noise, benchmark differentiation and research mapping remain separate gates. WP5 noise is deferred. WP6 kernel research and WP7 performance/marketing claims are deferred; core dependency weight is unchanged but the optional test environment has substantial SDK dependencies.

## Reproduction and rollback

Use Python3.12, isolated environment, and `requirements-tested.txt` for the exact locally tested dependency set. Install E7Q editable so existing distribution-identity-dependent tests see package metadata. Set `PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`. Run `python -B -m pytest -q tests/test_cirq_interop.py`, then the complete existing suite. Test outputs and skips are in `VALIDATION_REPORT.md`.

Upstream references inspected: https://quantumai.google/reference/python/cirq/Simulator ; https://raw.githubusercontent.com/quantumlib/Cirq/v1.6.1/cirq-core/cirq/sim/sparse_simulator.py ; https://pypi.org/pypi/cirq-core/1.6.1/json . The selected version is a tested pin, not a claim that it is latest.

Rollback: remove/disable the optional adapter/extra and its callers. Default core behavior, historical fixtures and evidence contracts do not depend on it. Do not repurpose existing schema/profile identifiers. Publication/merge/tag/deploy requires separate maintainer authority; no GitHub PR is created automatically by this local mandate.
