# E7Q-QEC/0.1 implementation and comparison

Date: 18 October 2026 (Europe/Warsaw). Builder: Codex, bounded QEC adapter workstream.

**Result:** the existing E7Q circuit verifier independently reproduces the supplied repetition-code reference outcomes. No new QEC algorithm, additional correction power or speed advantage is established. The additive implementation is a typed exchange adapter, executable fault corpus, full decoder-table circuit, conventional comparisons and opt-in MSC/REC experiments. It changes no existing E7Q simulator, verifier, quantum semantics, IR identity, shared schema or architecture pin.

## Exact sources and work package

- E7Q baseline: `b7989c647e5d0e22ed1128c41aceb2dda2f23405`, default branch main at retrieval.
- Local branch: `codex/qec-0.1-reference-adapter`. Only `pilots/qec_0_1/` is added.
- E7G-T checkout: `4d6e02f16363f2333961cf4350d584c92d51bbc6`. The v0.15 kernel and MSC/REC source digests are in `SOURCE_MANIFEST.json`.
- E7Q's retained architecture pin is v0.12.1/RGP2, `fc4cdf95c6434e653efbe017587aab60b4b2a86c`. This experiment does not migrate it.
- The supplied operating kernels v0.1/v0.2 and kernel v0.12/v0.12.1 are historical context, not sources for MSC/REC definitions. The retrieved v0.15 canonical source and its versioned companions supply those definitions.
- Open PRs were inspected. Current QEC syndrome functionality already exists on main; this work does not restart it or take over the separate entanglement, Joint-planning or quantum-view branches. No central coordination write, external message, remote publication or merge was performed.
- Dispositions: retain E7Q quantum execution, syndrome algebra and evidence boundaries; adapt only exchange and experiment construction; opt into MSC-B1/REC-B1; do not select EEC-Q/SF/CFS/RGP/WPC execution; no replacement or retirement.

## Existing interfaces identified

| Interface | Accepted description / actual capability | Boundary |
|---|---|---|
| `e7q.language.parse`, `load`, `run`, `verify` | Native gate circuits, normalization, declared output support, dynamic assertions | PASS covers requested checks only. Dense output support is numerical with verifier tolerance 1e-12. |
| `e7q.language.from_openqasm` | Restricted OpenQASM 2 circuit descriptions | Import is not verification; call execution/verification separately. |
| `e7q.language.compare` | Two circuit programs; declared unitary, measurement or channel criteria | No named universal QEC correctness criterion. |
| `e7q.qec.StabilizerCode`, `syndrome`, `analyze_error` | Phase-insensitive Pauli errors and ordered generators | Validates commutation/independence and classifies stabilizer/detectable/logical errors; not a decoder-fidelity verifier. |
| Explicit `stabilizer` backend / Pauli requests | Clifford circuits and exact terminal Pauli expectations | Uses optional Stim; exact classical support request returns NOT_ASSESSED. |
| Dense execution state | Internally computed statevector | No public arbitrary-amplitude initial-state loader was found in the inspected native parser. This adapter admits only the four supplied preparations. |

The adapter does not inject a reference vector into an `Execution` object and call that independent verification. It supplies actual circuit source to the existing parser, simulator and verifier and preserves their complete output in JSON.

## Exchange format and quantum experiment

`QECCase` has an edition, identity, eight complex amplitudes as real/imaginary pairs, declared preparation, ordered generators, Pauli error, expected syndrome, four-entry decoder, recovery operation and expected unit fidelity. Admission rejects unknown/missing fields, non-finite amplitudes, unsupported preparations/codes, invalid operators, non-binary syndrome and unsupported fidelity claims. This is a pilot-local interchange contract, not an ecosystem schema promotion.

The Python reference numbers statevector bits from least significant q[0]. Native E7Q full-register labels put q[0] first. The adapter records that bridge explicitly: syndrome `(1,0)` after successful recovery is native label `00010`; `(0,1)` is `00001`. Initial experimental output had the labels reversed and failed 12 valid cases; the corrected mapping and explicit ordering regression preserve this finding rather than treating it as an E7Q defect.

For each case, E7Q prepares the logical state, encodes with two CNOTs, applies the physical error, coherently extracts Z0Z1 and Z1Z2 into two ancillas, applies recovery, then reverses the encoding and state preparation. Its exact numerical output-support invariant requires data `000` and the declared syndrome bits. For this definite-syndrome pure-state domain, unit probability of data `000` after inverse preparation is unit restoration fidelity up to global phase. No finite-shot agreement is substituted for exhaustive dense support.

The 77-case specialized-recovery corpus checks the declared recovery operation directly. `decoder_action_consistent` is separately labelled adapter bookkeeping; it is not an E7Q verdict on a JSON lookup table. To test the whole table, `decoder_table.py` compiles every decoder entry into a coherent circuit controlled by the syndrome ancillas, independently of the supplied error or selected recovery field. CCX is decomposed into H/T/CX gates and regression-tested on all eight basis states. That experiment runs the 16 valid, 16 swapped-table and one phase-control cases. It is a coherent decoder on definite syndromes, not a demonstrated adaptive measurement-and-feedforward decoder or a noise channel.

## Measured results

| Experiment | Cases | E7Q PASS | E7Q FAIL | Interpretation |
|---|---:|---:|---:|---|
| Valid reference cases | 16 | 16 | 0 | Four logical preparations, no error / each single X |
| Swapped decoder instructions | 16 | 8 | 8 | The eight inputs using swapped entries fail |
| Incorrect syndrome assignment | 16 | 0 | 16 | Explicit output-support contract rejects wrong syndrome |
| Incorrect recovery operation | 16 | 0 | 16 | Added residual X0 violates restoration contract |
| Single Z on logical plus | 1 | 0 | 1 | Syndrome 00; inverse-preparation test detects lost phase |
| Two X errors | 12 | 3 | 9 | Residual logical X; logical plus is unchanged in three cases |
| **Total specialized corpus** | **77** | **27** | **50** | **77/77 agreement with both conventional oracles** |
| Complete coherent decoder table | 33 | 24 | 9 | Reproduces 16/16 valid, 8/16 swapped, failed phase control |

There were no E7Q false positives or false negatives relative to the requested state-specific assertions on this corpus. This does not establish all-input channel correctness or correction of arbitrary states. In particular, the three two-error passes on logical plus are state-specific and must not be called code-wide recovery: E7Q's existing residual-error analysis classifies `XXX` as logical. This illustrates why checking one protected state can conceal a logical fault.

Additional negative controls in `claim-controls.json`:

- A normalization-only E7Q verification passes the phase-corrupted state. Explicit restoration claims are necessary.
- Z versus identity passes the existing `measurement` comparison and fails `global-phase` comparison. Computational-basis measurement equivalence does not certify phase preservation.
- The invented criterion `qec-corrects-all-errors` is rejected as unknown.
- Noncommuting and dependent generator sets are rejected by `StabilizerCode`.
- The compact stabilizer backend returns NOT_ASSESSED for the requested exact output-support invariant; it does not manufacture a dense-equivalent PASS.

## Independent conventional comparison

Neither comparator imports or calls `reference/qec_probe.py`.

1. A dense NumPy oracle constructs independent tensor-product Pauli matrices, calculates generator eigenvalues on the supplied complex vector and computes restored-state overlap fidelity.
2. A separate Stim 1.16.0 tableau oracle constructs the original state from three signed independent stabilizers, applies the physical error and recovery, then checks the three original stabilizer expectations. It does not use E7Q's simulator, verifier or stabilizer backend wrapper.

Both agree with E7Q on all 77 cases. E7Q's syndrome algebra additionally agrees with independent parity calculations on all 64 phase-insensitive three-qubit Paulis.

| Dimension | Existing E7Q plus adapter | Conventional verification |
|---|---|---|
| Correctness on supplied domain | Same outcomes as both oracles | Same outcomes |
| Diagnostics | Complete gate Proof-of-Path, allowed/observed support, error and residual classification | Dense oracle exposes syndrome/fidelity; tableau oracle exposes violated signed stabilizers |
| Defect localisation | Failed support identifies a violated combined claim; not automatic root-cause identification | Algebra/tableau gives direct residual/stabilizer information |
| General code-wide recovery | Not demonstrated | Conventional stabilizer theory can establish recovery modulo stabilizers over a declared error model; this harness checks finite inputs only |
| Scale | Five-qubit dense circuits here; no scaling study | Tableau method handles this Clifford problem compactly |

Warm, same-process timings, five repeats over all 77 specialized cases (385 calls), captured in the result JSON:

- E7Q parse + dense simulation + verification: median **1.319351 ms**, minimum **0.727881 ms**.
- Dense conventional calculation: median **0.338617 ms**, minimum **0.215818 ms**.
- Conventional Stim tableau calculation: median **0.047359 ms**, minimum **0.039721 ms**.

These compare the actual workflows, not equal instruction counts: E7Q includes source parsing, two syndrome ancillas, output sampling and a full trace. Conventional methods compute the required syndrome/restoration checks directly. The full-table circuit has extra decomposed controls and separate per-case elapsed times in `decoder-table.json`; those timings must not be conflated with the specialized run. No speed or complexity advantage is established. Timings exclude dependency install and process startup and are not a statistical benchmark across machines.

## MSC/REC investigation without semantic changes

The unmodified v0.15 companion evaluators are executed through `profiles.py`. Their implementations retain their historical edition labels: REC-B1 explicitly requires `0.14-experimental-draft`, even though its formal profile is inherited by v0.15. The adapter preserves that label; this is not a claim that the evaluator is newly repinned or fully v0.15-conformant.

MSC uses string-valued finite Pauli carriers and syndrome-record carriers, typed total maps into a common two-bit comparison carrier and exact equality. The scope link is an adapter-defined relationship between the Pauli-description and a wider record containing its syndrome, not physical containment. The parity table is supplied by the conventional domain adapter. MSC checks coherence of that table and assignments; it does not independently derive quantum commutation or implement a quantum measurement.

| MSC input | Actual evaluator outcome | Meaning |
|---|---|---|
| Restricted `{III, XII, IXI, IIX}`, observed 00 | unique | III within this restricted error model |
| All 64 phase-insensitive Paulis, observed 00 | ambiguous, 16 families | Zero syndrome does not identify no error |
| XII with claimed 00 | incompatible | Defined maps disagree |
| Required parity map unavailable | unsupported | Missing computation is not incompatibility |
| 64 candidates with limit 1 | resource_limit | Declared finite bound is respected |

Quantum probabilities, amplitudes, signed stabilizer phases and stochastic measurement outcomes are not interpreted as MSC coefficients or raw equal-value observations. General probabilistic observation criteria, arbitrary quantum states and recovery-channel semantics remain outside this MSC-B1 demonstration.

REC receives scoped corpus-agreement evidence and an unrelated hardware-correction claim with no evidence. The bounded evaluator reports supported for corpus agreement, both/abstain when contradictory evidence is added, and neither/seek evidence for hardware correction. A rule that broadens the corpus scope is rejected with `rule expands scope`. The existing separate `check_trace.py`, which does not import the REC evaluator, replays the three admitted witnesses. A forged supported-only query with a recomputed witness hash is rejected with `trace mismatch: query`.

The REC source edition field binds the labelled result file edition, not cryptographic source authentication. The included manifest hashes the actual files. Evidence from this session shares one provenance group; the two implementations are not counted as independent external reviewers. REC validates information flow and replay, not whether the imported numerical result is true.

**Additional value demonstrated:** MSC preserves ambiguity and distinguishes missing maps from inconsistency; REC preserves conflicting evidence, prevents the tested scope expansion and rejects the tested forged witness. Conventional typed relations, finite constraint solving and evidence bookkeeping can supply equivalent controls. No unique mathematical or quantum advantage of E7G-T is established by these experiments.

## Validation and limitations

- New pilot: 12 unittest methods, including full 77-case differential checks, mutation sensitivity, ordering, strict exchange admission, full-table controls, CCX basis truth table, all-Pauli algebra comparison and MSC/REC negative controls.
- Existing focused E7Q suites: 62 passed, one module skipped because optional Qiskit is absent. The new Stim oracle is installed and exercised; the skipped Qiskit comparison is not counted as independent evidence.
- Existing MSC model tests: 26 passed. Existing REC model tests: 24 passed. REC suite initially failed to import when invoked outside its required repository working directory; rerunning from the E7G-T root passed without code modification.
- Licensing boundary check: PASS, declared scope only, not rights certification.
- The complete E7Q test suite, remote CI and independent external review were not run.

Unsupported or not established: arbitrary initial complex states, stochastic/coherent superpositions of different syndromes as measurement ensembles, mixed/noisy channel correction, adaptive decoder execution, hardware execution/authenticity/fidelity, fault tolerance, thresholds, universal single-Pauli correction, Steane/surface codes, all-logical-input channel equivalence, scaling or new QEC capability. The supplied 3p²−2p³ analytic rate is conventional reference material, not a measured E7Q threshold or error-rate advantage.

## Reproduction

From the E7Q root with NumPy and Stim 1.16.0 installed, and the pinned E7G-T checkout alongside it:

```bash
PYTHONPATH=src python pilots/qec_0_1/adapter.py
PYTHONPATH=src python pilots/qec_0_1/conventional.py
PYTHONPATH=src python pilots/qec_0_1/decoder_table.py
PYTHONPATH=src python pilots/qec_0_1/claim_controls.py
PYTHONPATH=src python pilots/qec_0_1/profiles.py ../E7GT
PYTHONPATH=src python -m unittest discover -s pilots/qec_0_1 -p 'test_*.py' -v
```

For a different kernel checkout location, set `E7GT_CHECKOUT` for profile tests. All witness files retain case descriptions and native output. Fresh timing values and NumPy metadata can differ by runtime. The final source manifest identifies the delivered adapter bytes separately from upstream baseline identities.

Next acceptance gate: independent reproduction of this package and review of the adapter's ordering, circuit-restoration claim and coherent decoder-table construction. No expansion to another code is justified by calling this result a new QEC method.
