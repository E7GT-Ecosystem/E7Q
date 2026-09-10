# E7Q-IR Research Foundations

**Register version:** 0.2
**Reviewed:** 2026-09-10
**Role:** primary-source inputs to [BUILD_PLAN.md](BUILD_PLAN.md) v0.13.

This register records research findings and proposed uses, not implemented
capabilities or dependency approvals. The build plan governs implementation
order; its existing QEC-first Phase 7 order takes precedence over any earlier
research suggestion to start with BQM. All entries were publicly readable during
research, subject to the access limitations stated below. Living URLs must be
pinned before adoption. Public access is not a blanket redistribution license.

Sources inform domain methods under the E7G-T extension/projection contract;
they do not establish E7G-T as a validated physical theory. Preserve source,
representation, transformation, observation and claim distinctions.

## [01] The Theory of Quantum Information

John Watrous, University of Waterloo; freely available author text of the 2018 book. [Author’s book and chapter downloads](https://cs.uwaterloo.ca/~watrous/TQI/).

Use the mathematical treatment of states, channels, measurements and distances to define criterion domains precisely. E7Q should distinguish equality of unitary operators, equality up to global phase, agreement of a specified measurement distribution, and equality of channels. A check on one input state cannot establish agreement for every input. The book provides foundations, not a scalable implementation or a blanket redistribution license.

## [02] MQT QCEC: Quantum Circuit Equivalence Checking

Munich Quantum Toolkit; living documentation, retrieved development label 3.9.1.dev25. [Methods and limitations](https://mqt.readthedocs.io/projects/qcec/en/latest/equivalence_checking.html).

The strongest first external checker candidate. Decision-diagram methods can decide equivalence or non-equivalence in their admitted setting, but representations may grow exponentially. Simulation can find a disagreement; sampled success does not prove universal equality. ZX reduction can prove equality when successful, while failure to simplify is inconclusive. Record the actual method, numerical thresholds, layout, phase convention, resource budget and raw result.

## [03] PyZX: circuit equality API

PyZX authors; living API, retrieved version 0.10.6. [verify_equality reference](https://pyzx.readthedocs.io/en/latest/api.html#pyzx.circuit.Circuit.verify_equality).

The API returns True when its reduction succeeds and None otherwise. Its options separately allow swaps and global phase. Preserve those choices in the criterion identity; never reinterpret None as a counterexample. Use as a complementary checker after the core criterion contract exists. A library’s success result is not automatically an independently checked proof certificate.

## [04] A Verified Optimizer for Quantum Circuits

Hietala et al.; open manuscript submitted 4 December 2019, POPL 2021. [Paper](https://arxiv.org/abs/1912.02250) and [SQIR/VOQC implementation](https://github.com/inQWIRE/SQIR).

VOQC provides transformations proved correct in Coq against specified circuit semantics. Use its approach to design later proof-bearing transformation evidence: theorem identity, assumptions, formalization version and extraction/build provenance. Its guarantees do not extend automatically to arbitrary imported transformations, parsers, wrappers or physical execution.

## [05] RFC 8785: JSON Canonicalization Scheme

RFC Editor, June 2020; informational RFC. [JCS specification](https://www.rfc-editor.org/rfc/rfc8785).

Use as a comparison reference for cross-language content identity: number serialization, string handling and property ordering require exact agreement. Do not silently replace E7Q’s existing canonicalization with JCS. First document differences and create shared test vectors; any identity-changing migration needs versioning. Canonical bytes identify content, not its author or scientific correctness.

## [06] OpenQASM Live Specification

OpenQASM contributors; living specification. [Language, grammar, timing and calibration](https://openqasm.com/).

Phase 3’s normative starting point. Publish a construct-level support matrix covering types, gates, measurement, classical control, includes, timing and calibration. Keep original source bytes and imported representation separate. Each accepted transformation needs a declared preservation relation; inspection must not execute included source. Pin a release or commit: the live specification is broader than a bounded OpenQASM 3 implementation.

## [07] QIR specification: model and version compatibility

QIR Alliance; living specification. [Core representation and compatibility](https://github.com/qir-alliance/qir-spec/blob/main/specification/README.md).

QIR is LLVM-based and uses profiles to constrain target capabilities. The inspected specification distinguishes QIR 1 typed pointers from QIR 2 opaque pointers, with the latter requiring LLVM 16 or later. Phase 4 should declare both versions and the target profile. LLVM module validity must remain distinct from a verified quantum transformation or evidence of execution.

## [08] QIR Base Profile

QIR Alliance; living normative profile. [Base Profile specification](https://github.com/qir-alliance/qir-spec/blob/main/specification/profiles/Base_Profile.md).

A bounded starting contract for entry points, quantum instruction sets, module metadata and output recording. The profile addresses unitary transformations followed by measurements and requires explicit output selection/order. Profile membership does not select one universal gate set. Preserve output labels and mapping; defer adaptive features until a separately pinned profile and capability contract support them.

## [09] Catalyst: hybrid quantum program compilation

PennyLane/Xanadu; living reference repository. [Architecture, examples and compiler source](https://github.com/PennyLaneAI/catalyst).

A useful integration candidate for hybrid workflows, rather than a reason to build a second compiler inside E7Q. Capture classical parameter assignments, compiler configuration and intermediate/executable artifacts along the evidence path. The dedicated developer-overview URL failed during this research; the repository was accessible. Detailed dialect/version compatibility remains an implementation-time check.

## [10] Qiskit primitives

IBM Quantum; living API documentation. [Sampler and Estimator interfaces](https://quantum.cloud.ibm.com/docs/en/api/qiskit/primitives).

Use the primitive interfaces to distinguish sampled measurement data from expectation-value estimates, and to retain parameters and result metadata. Design separate result contracts instead of treating every provider result as counts. An SDK object is an interchange input; it does not by itself authenticate the hardware, job chronology or measurement origin.

## [11] Bit-ordering in the Qiskit SDK

IBM Quantum; living guide. [Bit-ordering conventions](https://quantum.cloud.ibm.com/docs/en/guides/bit-ordering).

Use for cross-SDK fixtures involving integer significance, displayed bitstrings and circuit indices. E7Q needs explicit qubit, classical-register and measurement-order maps. Test non-palindromic outcomes, reordered measurements and multiple registers: Bell counts alone can hide a reversed ordering convention. A normalized histogram should retain the original record and normalization transformation.

## [12] PROV-DM: The PROV Data Model

W3C Recommendation, 30 April 2013. [Entities, activities, agents and derivations](https://www.w3.org/TR/prov-dm/).

A mature vocabulary for mapping source artifacts, compilation, execution and responsible agents. Consider a documented export mapping from E7Q evidence graphs rather than replacing the existing graph. PROV can describe asserted provenance, including provenance of provenance; it does not make those assertions authentic or scientifically sufficient.

## [13] Dead Simple Signing Envelope protocol

Secure Systems Lab; living protocol. [DSSE envelope and signing protocol](https://github.com/secure-systems-lab/dsse/blob/master/protocol.md).

A candidate foundation for signing typed evidence payloads in Phase 5. It provides a signing envelope, not a provider trust policy. The required security ADR must still define trusted identities, key distribution, revocation, replay handling, signature scope and chronology evidence. An E7Q-signed import proves the importer’s attestation under its key; it must not be presented as a provider-signed execution receipt.

## [14] QUBOs and Ising Models

D-Wave; living technical documentation. [Model definitions and conversion](https://docs.dwavequantum.com/en/latest/quantum_research/qubo_ising.html).

Define an annealing-bqm profile with variable domain, ordered labels, linear/quadratic coefficients and energy offset. For small models, enumerate energies to test QUBO-to-Ising conversion under the declared variable mapping. Retaining the offset is essential. Correct model conversion establishes an energy relation; it does not prove that returned samples are optimal.

## [15] Minor-Embedding: Best Practices

D-Wave; living technical documentation. [Embedding and chains](https://docs.dwavequantum.com/en/latest/quantum_research/embedding_guidance.html).

Separate the logical problem from the physical graph, embedding, chain strengths, broken-chain treatment and unembedding. These belong to distinct transformation/execution steps. Logical variable count and physical-qubit count are different resource measures. An embedding success should not be used as evidence of solution quality or quantum advantage.

## [16] Submit an analog program using QuEra Aquila

Amazon Braket; living developer guide with program/result schemas. [Analog program and per-shot results](https://docs.aws.amazon.com/braket/latest/developerguide/braket-quera-submitting-analog-program-aquila.html).

The most concrete analog contract in this corpus: atom coordinates/filling, drive amplitude/phase/detuning, waveform times and per-shot pre/post sequences. Define an ahs-rydberg profile with units, ordered sites and capability snapshots. Preserve pre-sequence data: a post-sequence zero can indicate a Rydberg state or an empty site. Record filtering and discarded shots. Aquila’s model is not a specification for every analog device.

## [17] Bloqade Analog

QuEra Computing; living SDK repository. [Program construction, sweeps and backends](https://github.com/QuEraComputing/bloqade-analog).

Reference code for geometry/waveform programs, parameter sweeps and backend separation. Each concretized sweep instance should have its own identity and parameter record. Pin the SDK and exported format; repository restructuring and migration guidance make internal types unsuitable as an unversioned external standard. Emulator acceptance must be distinguished from hardware capability acceptance.

## [18] Blackbird: Syntax and grammar

Xanadu; documentation identifies a 0.6.0-dev line. [Photonic program syntax](https://quantum-blackbird.readthedocs.io/en/latest/syntax.html).

Use for a photonic import profile preserving language version, target, typed parameters, mode indices, measurement order and feed-forward dependencies. Measurement records follow program measurement order. Included/template inputs need their own identities. The older development documentation is a reason to pin parser fixtures; it is not evidence of current service availability.

## [19] Strawberry Fields: A Software Platform for Photonic Quantum Computing

Killoran et al.; submitted 9 April 2018, revised 4 March 2019. [Open architecture paper](https://arxiv.org/abs/1804.03159).

Foundational reference for continuous-variable programs, specialized simulation and compilation. Use a photonic-cv profile instead of forcing modes and continuous measurement values into qubit-count contracts. Preserve backend approximations, such as truncation choices where applicable. This architecture paper does not establish current backend capabilities or unrestricted simulation accuracy.

## [20] Stim circuit file format

quantumlib/Stim; living format specification. [Circuit, measurement and detector syntax](https://github.com/quantumlib/Stim/blob/main/doc/file_format_stim_circuit.md).

Define a qec-stabilizer artifact profile with measurements, detector declarations, logical observables, noise operations and repetition structure. Preserve measurement-record references and source identity. Bound repeat expansion and resource consumption. Stabilizer/QEC simulation support does not imply efficient arbitrary universal-circuit simulation.

## [21] Stim Detector Error Model format

quantumlib/Stim; living format specification. [DEM error mechanisms and detector relations](https://github.com/quantumlib/Stim/blob/main/doc/file_format_dem_detector_error_model.md).

Retain probabilities, detector symptoms, logical frame changes, offsets and repeats. The model expresses independent error mechanisms; the ^ separator indicates a suggested decomposition and must not be reinterpreted as independent errors. Link circuit-to-model options and decoder configuration as separate artifacts. A decoded logical-error estimate inherits the assumptions and adequacy of its noise model.

## [22] QASMBench

PNNL publication, 12 April 2023; repository reports version 1.4. [Paper description](https://www.pnnl.gov/publications/qasmbench-low-level-quantum-benchmark-suite-nisq-evaluation-and-simulation) and [circuit corpus](https://github.com/pnnl/QASMBench).

Use a small pinned OpenQASM 2 subset for external F2 regression. Include supported, rejected and mutated programs; record exclusions. Circuit breadth helps reveal interoperability defects but does not prove arbitrary-program correctness. Read the actual Battelle license rather than inferring a standard SPDX identifier from a README’s “BSD” shorthand.

## [23] MQT Bench

Quetschlich, Burgholzer and Wille; Quantum 7, 1062, 20 July 2023. [Open paper](https://quantum-journal.org/papers/q-2023-07-20-1062/) and [reference implementation](https://github.com/munich-quantum-toolkit/bench).

Use its abstraction levels to organize comparable algorithm, compiler and target artifacts. Preserve algorithm instance, compiler configuration, target model and resulting hash separately. The paper’s corpus size is a publication snapshot, not E7Q coverage; only exercised, versioned fixtures should count toward conformance.

## [24] SupermarQ: A Scalable Quantum Benchmark Suite

Tomesh et al.; open preprint, 22 February 2022, HPCA 2022. [Application benchmark paper](https://arxiv.org/abs/2202.11045).

Basis for application-oriented F4 evidence. Store workload parameters, expected-output/scoring method and raw observations. Keep application score separate from transformation equivalence, hardware gate fidelity and advantage. Use comparable compiler and resource disclosures when comparing backends.

## [25] Gate Set Tomography

Nielsen et al.; Quantum 5, 557, 5 October 2021. [Open paper](https://quantum-journal.org/papers/q-2021-10-05-557/).

Defines a model-based characterization approach with gauge choices and uncertainty. An E7Q record should preserve model family, state-preparation/measurement assumptions, gauge convention and fit diagnostics. GST does not authenticate a provider or establish correctness of every workload. One follow-up fetch failed; the research lane had accessed the publisher page.

## [26] Probing quantum processor performance with pyGSTi

Nielsen et al.; open preprint, 2020. [Paper](https://arxiv.org/abs/2002.12476) and [Sandia implementation](https://github.com/sandialabs/pyGSTi).

Prefer an adapter for established characterization workflows over rebuilding tomography. Import experiment definitions, raw data, analysis configuration and reports. Re-running analysis on identical data is distinct from reproducing an experiment on independently collected observations.

## [27] Randomized benchmarking with gate-dependent noise

Wallman; Quantum 2, 47, 29 January 2018. [Open manuscript](https://arxiv.org/abs/1703.09835).

Use to bound interpretation of benchmarking decay under the stated model. Preserve protocol variant, gate set, sequence lengths, seeds, repetitions, fitted model and uncertainty. An aggregate RB metric must not be substituted for arbitrary application fidelity or worst-case error.

## [28] A subexponential-time quantum algorithm for the DHSP

Greg Kuperberg; submitted 14 February 2003, SIAM Journal on Computing 2005.
[Open manuscript](https://arxiv.org/abs/quant-ph/0302112).

The reference sieve constructs dihedral phase states and combines their labels
to approach a label that reveals the hidden reflection. Use its ideal state and
combination identities as the first DHSP laboratory baseline. The published
subexponential complexity is a comparison boundary: reproducing small states or
one transition does not reproduce the algorithm or improve its asymptotics.

## [29] Polynomial-space subexponential DHSP algorithm

Oded Regev; submitted 21 June 2004.
[Open manuscript](https://arxiv.org/abs/quant-ph/0406151).

This modifies the Kuperberg approach to require polynomial space while retaining
subexponential time. Use it as a second future baseline for time/space recurrence
records. A candidate may not hide exponential work in state preparation,
postselection, subset-sum processing or classical memory.

## [30] Quantum computation and lattice problems

Oded Regev; submitted 1 April 2003.
[Open manuscript](https://arxiv.org/abs/cs/0304005).

This connects dihedral coset sampling with lattice problems and average-case
subset sum. It motivates careful consequence and oracle-contract tracking. E7Q
must not infer a lattice or cryptographic result from a bounded DHSP simulation;
every reduction premise and complexity obligation requires separate evidence.

## Adoption and unresolved scope

For each implementation dependency or vendored fixture, pin its version and
record its content identity, actual license/notice text, supported requirement
and positive/negative/unsupported fixtures. Research identified MIT licensing
for QCEC, SQIR/VOQC and MQT Bench; Apache-2.0 for PyZX, dimod, Bloqade Analog,
Blackbird, Stim and pyGSTi. Recheck exact pinned files and transitive dependencies.
QASMBench uses Battelle BSD-style terms; inspect its actual LICENSE rather than
substituting a generic SPDX label. Documentation and manuscript rights must be
tracked separately from code. The linked repositories and publisher pages are
the evidence locations for these preliminary findings.

Measurement-based execution, detailed pulse calibration, distributed protocols,
fault-tolerant resource estimation and decoder interoperability require further
primary-source and domain review. Provider-origin attestations, private
calibration records and independent hardware replication require actual access;
this research did not test their availability or execute provider jobs.

The canonical research report was prepared on 2026-09-06. This repository
register preserves its actionable source entries so future engineers need not
rely on a chat attachment. The plan's R1-R6 packages define the commitments;
source descriptions here are informative.
