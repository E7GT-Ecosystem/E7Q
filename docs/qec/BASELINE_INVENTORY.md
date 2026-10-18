# QEC WP0 — baseline inventory and interface reconciliation

Status: **proposed documentation; unaccepted; G0 OPEN**. Snapshot: 18 October 2026.
Reconciler: Trejo Mansfield; no implementation authority inferred.
This inventory distinguishes main, the published experimental pilot, and proposed product work.
No runtime, test, pilot, shared format, source pin or existing API is changed by this document.

## 1. Baseline and custody

| Object | Exact identity | Evidence/status |
|---|---|---|
| Frozen upstream baseline | `b7989c647e5d0e22ed1128c41aceb2dda2f23405` | Locally present; authenticated current-main lookup agrees. |
| Published pilot | `6f66233e68d3cd52a3f01f6548259003e497b2c5` | Locally inspected commit; sole parent is frozen baseline. |
| Published pilot tree | `f58a7e4d41afb7bef68244ca333309e9e55b06f6` | Verified with `git show -s --format='%H %P %T'`. |
| Original local pilot | `4be5125c3198c9db980865c57814cb41aa4b13b5` | Object unavailable locally; identical-tree provenance is handoff attestation, not independently reverified here. |
| Reconciliation handoff HEAD | `88467d51b21d3e072baae583fc4f23e676db59d6` | Local starting HEAD; branch `wp0/qec-reconciliation-20261018`; starting worktree clean. |

Source: [WP0_PILOT_HANDOFF.md, lines 9–20, 39–43](https://github.com/E7GT-Ecosystem/E7Q/blob/88467d51b21d3e072baae583fc4f23e676db59d6/docs/qec/WP0_PILOT_HANDOFF.md#L9-L43).
The handoff describes publication via API after shell authentication failed; publication is not merge, release or G0 acceptance.
Its assertion about the original/published tree must not be silently upgraded into local original-object verification.

Executed preservation check:

```text
git diff --name-status b7989c647e5d0e22ed1128c41aceb2dda2f23405 6f66233e68d3cd52a3f01f6548259003e497b2c5
=> 19 additions, all under pilots/qec_0_1/; no modifications, deletions or renames
```

Therefore every baseline-tracked file is unchanged in the published pilot tree, including `src/e7q/qec.py`.
This establishes file preservation, not semantic correctness of additions or original commit provenance.
Handoff/buildmap documents are subsequent additions, not historical constituents of the published pilot commit.

## 2. Authenticated upstream snapshot

Read-only `gh api` queries completed around **2026-10-18T18:37:52Z**, repository `E7GT-Ecosystem/E7Q`.
These are point-in-time remote observations, not a guarantee that main or review state remains unchanged.

| Surface | Observed result | Source |
|---|---|---|
| `branches/main` | main at frozen baseline above; `protected=false` | [Main branch API](https://api.github.com/repos/E7GT-Ecosystem/E7Q/branches/main) |
| Open issues | E7GT-Ecosystem/E7Q#58 (two-qubit entanglement), E7GT-Ecosystem/E7Q#29 (historical external execution evidence import) | [Open issues API](https://api.github.com/repos/E7GT-Ecosystem/E7Q/issues?state=open&per_page=100) |
| Open PRs | Nine; listed below, all target `main` | [Open PR API](https://api.github.com/repos/E7GT-Ecosystem/E7Q/pulls?state=open&per_page=100) |
| Tags | Zero returned (`per_page=100`); package version is not a release tag | [Tags API](https://api.github.com/repos/E7GT-Ecosystem/E7Q/tags?per_page=100) |
| Exact-baseline CI | Two completed successful CI runs, exact `head_sha` match | [39077816846](https://github.com/E7GT-Ecosystem/E7Q/actions/runs/39077816846), [39054923798](https://github.com/E7GT-Ecosystem/E7Q/actions/runs/39054923798) |

| Open PR | Topic | Draft | Observed head |
|---|---|---|---|
| E7GT-Ecosystem/E7Q#92 | Joint-planning reconciliation/licensing/review gates | yes | `f437025ea6750c3045559911a5035d26dbdad4b3` |
| E7GT-Ecosystem/E7Q#91 | Bounded entanglement reconciliation | no | `9d78a57d8edc596843acd59b8554ea2dea9e06f5` |
| E7GT-Ecosystem/E7Q#90 | v0.15 map reconciled with merged Q-A3/Q-A4 | no | `4a6a57cd3fe44a8e19e8dce0ffcd1079d39a1dca` |
| E7GT-Ecosystem/E7Q#89 | Capability-map refresh | no | `fd77f1725a5c396bfb1f047e404470681c2be322` |
| E7GT-Ecosystem/E7Q#81 | Exact-qubit quantum-view adapter | yes | `56e856984cc49430be9a9f76b62ee69dae0e514b` |
| E7GT-Ecosystem/E7Q#80 | Versioned quantum-view plan | yes | `f7997a866cbdf7c71e8e8e17cbc9de576ac7a51f` |
| E7GT-Ecosystem/E7Q#79 | Joint-planning pilot | yes | `38d3c22903d78174e9b252969d449612108c5205` |
| E7GT-Ecosystem/E7Q#77 | v0.15 capability map | yes | `bb9e242f54f7d3ce715823f5915041684b8ffdf9` |
| E7GT-Ecosystem/E7Q#59 | Two-qubit entanglement assurance | no | `2735af369a75e05a142e3123c17c193905a2ca05` |

No open-PR content is presumed merged or adopted; no QEC ownership transfer is inferred.
CI metadata was retrieved, not independently rerun by this worker or exhaustively reviewed job-by-job.
Workflow [ci.yml, lines 11–40, 42–77](https://github.com/E7GT-Ecosystem/E7Q/blob/b7989c647e5d0e22ed1128c41aceb2dda2f23405/.github/workflows/ci.yml#L11-L77) defines Python 3.11/3.12/3.13 core, simulation-reference and constrained Cirq lanes.

## 3. Existing QEC algebra and compatibility surface

Source anchor: [src/e7q/qec.py](https://github.com/E7GT-Ecosystem/E7Q/blob/b7989c647e5d0e22ed1128c41aceb2dda2f23405/src/e7q/qec.py).

| Existing interface | Exact source lines | Contract/boundary to retain |
|---|---|---|
| `QECError`, Pauli canonicalization | 13–39 | Accept I/X/Y/Z strings, uppercase canonicalization, declared length; no signed/phase-aware Pauli group. |
| `pauli_to_symplectic`, `symplectic_product`, `multiply_paulis` | 42–72 | Binary `(x|z)`, commutation parity, product modulo phase; q[0] first. |
| `StabilizerCode(name, generators)` | 99–127 | Frozen ordered generators; reject empty name/list, identity, unequal width, noncommuting or dependent generators. |
| `syndrome(code,error)`, `in_stabilizer` | 130–143 | Ordered anticommutation bits; GF(2) span membership, phase suppressed. |
| `analyze_error` | 146–177 | `detectable`, `stabilizer` or `logical`; zero syndrome is normalizer membership, not absence of error. |
| `syndrome_homomorphism_report` | 180–216 | Check `sigma(EF)=sigma(E) xor sigma(F)` for submitted inputs; not recovery correctness. |
| `qec_proof_json` | 219–221 | Sorted-key indented JSON with trailing newline. |

CLI source: [cli.py, lines 194–210 and 305–315](https://github.com/E7GT-Ecosystem/E7Q/blob/b7989c647e5d0e22ed1128c41aceb2dda2f23405/src/e7q/cli.py#L194-L210).
Retain `qec-syndrome ERROR` and `qec-homomorphism LEFT RIGHT`, repeated required `--generator`, optional `--name`, `-o/--output` and existing imports.
Existing output labels are `e7q.qec-error-analysis/v1alpha1` and `e7q.qec-syndrome-homomorphism/v1alpha1`.
The legacy documented pilot profile `e7q.qec-syndrome-pilot/v1alpha1` is distinct from these report schema labels.

[QEC_SYNDROME_PILOT.md, lines 15–49, 51–84](https://github.com/E7GT-Ecosystem/E7Q/blob/b7989c647e5d0e22ed1128c41aceb2dda2f23405/docs/QEC_SYNDROME_PILOT.md#L15-L84) specifies `(ZZI,IZZ)`, `XII/IXI/XXI`, and zero-syndrome `III/ZZI/XXX` controls.
The [independent checker, lines 10–48](https://github.com/E7GT-Ecosystem/E7Q/blob/b7989c647e5d0e22ed1128c41aceb2dda2f23405/pilots/qec_syndrome/reference_checker.py#L10-L48) imports no E7Q code: it computes six fixture commutation syndromes and checks the fixture XOR equation.
Its success alone does not independently verify arbitrary homomorphism inputs, classification, decoder behaviour or all circuit executions.
The six legacy circuit fixtures and tests are separate evidence; preserve both rather than replacing the checker with pilot self-assertions.

## 4. Simulator, verifier and E7Q-IR interfaces

There is no baseline `src/e7q/simulator.py` or `verifier.py`; execution/verification live in `language.py` and `stabilizer.py`.

| Existing mechanism | Source | Retention and limits |
|---|---|---|
| `parse`, `load`, `run` | [language.py, lines 204, 483–501, 1198](https://github.com/E7GT-Ecosystem/E7Q/blob/b7989c647e5d0e22ed1128c41aceb2dda2f23405/src/e7q/language.py#L483-L501) | Actual native programs; dynamic paths have measurement/conditional semantics; explicit backend, no implicit fallback. |
| Resource preflight | [resources.py, lines 155–185](https://github.com/E7GT-Ecosystem/E7Q/blob/b7989c647e5d0e22ed1128c41aceb2dda2f23405/src/e7q/resources.py#L155-L185) | Admission/allocation budget and host limits before simulation; measurement required for execution. |
| `verify(execution,tolerance=1e-12,pauli_checks=())` | [language.py, lines 1041–1099](https://github.com/E7GT-Ecosystem/E7Q/blob/b7989c647e5d0e22ed1128c41aceb2dda2f23405/src/e7q/language.py#L1041-L1099) | Requested normalization/trace, allowed support and assertion checks only; Pauli requests require stabilizer backend. |
| Optional Stim | [stabilizer.py, lines 23–44, 68–80, 134–181](https://github.com/E7GT-Ecosystem/E7Q/blob/b7989c647e5d0e22ed1128c41aceb2dda2f23405/src/e7q/stabilizer.py#L23-L44) | Exact version admission; Clifford, basis measurements, one-bit classical equality controls; native q0/c0 leftmost. |
| Stim exclusions | same capability declaration, lines 40–44 | No T/non-Clifford, noise/mixed-state execution, exhaustive probabilities, exact support or unitary/channel comparison; no mid-measurement ensemble-expectation claim. |
| `compare`, OpenQASM bridge | [language.py, lines 821–888, 1106–1196](https://github.com/E7GT-Ecosystem/E7Q/blob/b7989c647e5d0e22ed1128c41aceb2dda2f23405/src/e7q/language.py#L821-L888) | Explicit comparison criteria/restricted import; neither import nor comparison is a universal QEC correctness test. |
| `validate_graph(...,level,semantic_registry)` | [conformance.py, lines 150–175, 247–264](https://github.com/E7GT-Ecosystem/E7Q/blob/b7989c647e5d0e22ed1128c41aceb2dda2f23405/src/e7q/ir/conformance.py#L247-L264) | F0 structure, F1 identities/references, F2 installed profile validators after F1 passes. |
| Profile registry | [profiles.py, lines 29–64](https://github.com/E7GT-Ecosystem/E7Q/blob/b7989c647e5d0e22ed1128c41aceb2dda2f23405/src/e7q/ir/profiles.py#L29-L64) | Built-ins are core, circuit-basic and native-execution; no QEC domain profile. |
| Semantic extension contract | [semantic.py, lines 14–32, 86–123, 325–358](https://github.com/E7GT-Ecosystem/E7Q/blob/b7989c647e5d0e22ed1128c41aceb2dda2f23405/src/e7q/ir/semantic.py#L325-L358) | Profile/version registry, evidence references, explicit PASS/FAIL/BLOCKED/UNSUPPORTED/NOT_ASSESSED; unavailable validator blocks. |

**Generic F2 is not QEC semantic validation.** A valid native-execution graph does not establish code distance, decoder correctness or recovery across a code space.
Native dynamic execution already exists; the pilot's coherent decoder-table circuit is nevertheless not classical measured-syndrome/feedforward decoding.

## 5. Schemas, dependencies, licensing and source pins

Baseline `schemas/` contains 15 JSON schemas across root/subdirectories; no QEC-named schema file was found.
Existing schema families include IR graph/envelope, transformation history, candidate family/view/restriction, realisation and receipt binding; execution outcome, stabilizer result and Cirq evidence are separate contracts.
Do not infer that report `schema` strings already have standalone JSON Schema or QEC-specific semantic admission.

[pyproject.toml, lines 1–25, 30–34](https://github.com/E7GT-Ecosystem/E7Q/blob/b7989c647e5d0e22ed1128c41aceb2dda2f23405/pyproject.toml#L1-L34) declares:

| Layer | Declared requirement |
|---|---|
| Build/runtime | setuptools>=68; Python>=3.11; numpy>=1.26; package `1.0.0rc12`; `e7q=e7q.cli:main` |
| Test | pytest>=8; jsonschema>=4 |
| Stabilizer / simulation-test | stim==1.16.0; simulation-test additionally qiskit==2.5.2 and jsonschema>=4 |
| Other opt-ins | mqt.qcec==3.9.0; pyzx==0.10.6; cirq-core==1.6.1 |

Version ranges are declarations, not the fresh environment's resolved lock; parent reproduction must record actual installed versions and skipped optional coverage.
The [commercial policy, lines 8–33, 70–91](https://github.com/E7GT-Ecosystem/E7Q/blob/b7989c647e5d0e22ed1128c41aceb2dda2f23405/docs/licensing/COMMERCIAL_POLICY.md#L8-L33) retains Apache-2.0 code and CC-BY-SA-4.0 documentation.
Current `src/e7q/ir/` stays Apache; designated future `commercial/e7q_ir/` code requires rights clearance and separate PolyForm notices/packaging.
The [component register, lines 4–15 and 17–53](https://github.com/E7GT-Ecosystem/E7Q/blob/b7989c647e5d0e22ed1128c41aceb2dda2f23405/docs/licensing/component-register.json#L4-L53) has protected open prefixes, hash-bound retain-public decisions and no commercial implementations.
This inventory grants no new licensing clearance and does not relicense third-party code or copied source material.

| Source/profile layer | Pin/disposition |
|---|---|
| Governing E7Q architecture | Retain E7G-T v0.12.1-experimental/RGP2 `fc4cdf95c6434e653efbe017587aab60b4b2a86c`. |
| Compatibility history | v0.11-UC5 predecessor labels remain historical, not the current new-architecture pin. |
| Optional planning profiles | EEC-Q/SF/CFS remain opt-in; formal coefficients are not quantum amplitudes/probabilities. |
| Pilot MSC/REC references | Separate E7G-T checkout `4d6e02f16363f2333961cf4350d584c92d51bbc6`; source digests in pilot manifest, not automatic runtime adoption. |
| Proposed v0.15 adaptation | Exact named profiles/source editions and migration/admission review still required; no blanket migration. |

Sources: [KERNEL_ALIGNMENT.md, lines 14–37, 65–70](https://github.com/E7GT-Ecosystem/E7Q/blob/b7989c647e5d0e22ed1128c41aceb2dda2f23405/docs/KERNEL_ALIGNMENT.md#L14-L37), [BUILD_PLAN.md, lines 183–191, 278–288](https://github.com/E7GT-Ecosystem/E7Q/blob/b7989c647e5d0e22ed1128c41aceb2dda2f23405/docs/e7q-ir/BUILD_PLAN.md#L183-L191), [SOURCE_MANIFEST.json, lines 2–12](https://github.com/E7GT-Ecosystem/E7Q/blob/6f66233e68d3cd52a3f01f6548259003e497b2c5/pilots/qec_0_1/SOURCE_MANIFEST.json#L2-L12).
The buildmap's v0.11 README caution is stale relative to governing alignment instructions; retain the owner-supplied buildmap unchanged and record this reconciliation here.
Historical evaluator edition labels must remain intact even where their checkout contains a newer canonical kernel.

## 6. Existing versus proposed — disposition register

Source: [owner buildmap, lines 68–84, 91–124, 194–224](https://github.com/E7GT-Ecosystem/E7Q/blob/88467d51b21d3e072baae583fc4f23e676db59d6/docs/qec/E7Q_QEC_Developer_Buildmap_v0.1.md#L68-L124).
“Adapt” below is a proposal, not accepted work or permission to implement before G0.

| Disposition | Capability/component | Existing versus proposed / next boundary |
|---|---|---|
| Retained | `e7q.qec` module, API, CLI, legacy checker/fixtures | Already on main; retain paths, imports, output conventions and generator order. |
| Retained | Native execution, verification, resource gates, Stim opt-in | Already on main; reuse actual submitted-circuit execution and evidence. |
| Retained | IR identities, graph links, receipts, F0–F2 contracts | Existing substrate; no competing evidence store or silent semantic expansion. |
| Adapted | Algebra foundation / independent negative/property corpus | WP1 proposal; factor only with import/CLI compatibility; signed-phase cases require explicit rejection or safeguards. |
| Adapted | Experimental adapter and 77-case corpus | Published pilot outside main; candidate fixtures/adaptation evidence, not released domain profile. |
| Adapted / deferred | Coherent-first three-qubit X-error evaluator; later measured recovery | First WP2 slice is coherent definite-syndrome simulation only. Native dynamic primitives already exist, but a measured-syndrome/classical-recovery workflow is not supplied by this pilot and remains a separate full-G2 obligation; WP3 implementation stays behind applicable G2. |
| Adapted | `e7q.qec-profile/v0alpha1` and domain objects | WP3 proposal; `QECCodeSpec`, `QECCircuitSpec`, `QECNoiseSpec`, `QECDecoderSpec`, `QECExperimentSpec`, `QECObservation`, `QECAssessment`, `QECClaim` need versioned admission and QEC-specific checks. |
| Deferred | `src/e7q/qec/` package restructuring | Buildmap layout is provisional; conflicts with existing module; reviewed migration required. |
| Deferred | General decoder evaluation, logical-error statistics, repeated-round noise | Later WP4; not established by finite noiseless controls or timings. |
| Deferred | Selective MSC/REC/WPC product integration; external scientific review | WP5–WP6 gates; experimental finite witnesses are not blanket conformance or external review. |
| Excluded | Decoder implementation, kernel-pin migration, runtime/schema changes in WP0 | Outside this documentation-only reconciliation. |
| Excluded | New correction theorem, hardware fidelity, threshold, speed advantage, full QEC platform | Unsupported by these sources and finite simulations. |
| Excluded | Research Track B admission; automatic v0.15/FPF branding or licensing changes | Separate explicit review/owner decisions required. |

No component is replaced or retired by WP0. G1/G2/G3 cannot be backdated because an earlier experiment resembles a proposed deliverable.

## 7. Executed evidence and clean-environment integration status

Fresh execution, source custody, failures/recoveries and exact commands are recorded in [WP0_VERIFICATION.md](WP0_VERIFICATION.md) and the hash-bound [evidence bundle](evidence/wp0-20261018/). Historical observations are kept separate rather than overwritten.

| Required fresh check | Recorded result |
|---|---|
| Environment and dependency resolution | New virtual environment: Python 3.12.3, NumPy 2.5.4, pytest 8.4.2, jsonschema 4.26.0, Stim 1.16.0; E7Q 1.0.0rc12 metadata installed from baseline archive. Qiskit/Cirq/MQT/PyZX absent; no skipped coverage claimed. |
| Unchanged `qec-homomorphism XII IXI --generator ZZI --generator IZZ` | PASS; existing CLI invoked through `python -m e7q.cli`; source-bound report retained. |
| Dependency-free syndrome reference checker | PASS; six fixture syndromes and one XOR case, not a universal theorem. |
| Existing QEC tests and full baseline suite | Focused 40 passed/one skipped; recovered complete baseline **1202 passed, 12 skipped**. Original source-only run's 51 missing-distribution-metadata failures remain in evidence. |
| Pilot/oracle and coherent-table cases | 77/77 native/dense and Stim agreement; good 16 PASS; swapped eight FAIL; wrong-syndrome/recovery 16 FAIL each; phase FAIL; double-X three state-specific PASS/nine FAIL. Separate coherent table: 24 PASS/nine FAIL. Twelve pilot tests passed. |
| Optional MSC/REC custody and evaluations | All seven pilot source, six historical result and seven companion digests verified. Finite profiles replayed at exact companion pin; MSC 26 and REC 24 tests passed. |
| Licensing boundary and preservation | Licensing checker PASS; final documentation/custody verification retained with the acceptance revision. No runtime/test/schema/pilot changes; remote CI metadata is not a substitute for these checks. |

The [pilot report, lines 5–28](https://github.com/E7GT-Ecosystem/E7Q/blob/6f66233e68d3cd52a3f01f6548259003e497b2c5/pilots/qec_0_1/REPORT.md#L5-L28) and handoff describe historical results, not fresh WP0 execution.
Those include valid 16/16, swapped-decoder 8/16 failures, wrong-syndrome/recovery 16 failures each, a phase control and state-specific two-X passes.
They do not prove code-wide correction; a logical X can preserve a particular logical-plus input.
Stored MSC/REC witnesses establish only tested finite structural/evidence behaviour; Python assertions and independent-oracle results must not be counted as E7Q findings.

## 8. Risks, decisions and next package

Primary risks: stale remote snapshot, optional-dependency gaps, confusing phase-insensitive algebra with signed stabilizer physics, bit-order bridge mistakes, and counting fixture expectations as fresh execution.
The original/published commit metadata differs; only published-tree/parent preservation was independently verified here.
Tool-read recovery used `python3` because `rg`/`python` are unavailable; guessed simulator filenames were corrected to actual modules. No read-only failure changed repository files.
Owner decisions still needed: accept additive scope, select exact optional profiles/source editions, approve compatibility strategy and first WP1 implementation slice.
G0 also requires the completed fresh baseline record, claim register, scope ADR and **explicit owner acceptance**; this inventory does not supply acceptance.
Next PR is a proposed **WP0 documentation-only reconciliation**, followed by owner scope review; WP1–WP3 remain dependency-ordered future implementation packages.
No commit, publication, external posting/contact, decoder addition or source-pin migration is authorized by this document.
