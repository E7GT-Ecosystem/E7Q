# E7Q-CIRQ/0.1 — WP0 capability audit

Date: 2026-10-16. Status: developer-confirmed local G0 decision; not maintainer acceptance, publication permission or a completed /0.1 milestone.

## Inspected sources and protected work

GitHub `E7GT-Ecosystem/E7Q` main was fetched explicitly and inspected at **58d4e927869e0228b32ce7cd034bf06bb799dc48** (PR93 maintenance). A fresh worktree/branch `feature/e7q-cirq-interoperability-20261016` isolates this candidate. The local `E7Q/` directory contains the handoff and an older copied source tree, not the active Git checkout. Existing checkouts were inventoried, not reset or cleaned. In particular, the dirty `coordination/checkouts/e7q` Q-A3 and `e7q-qa4-20261014` worktrees retain their edits. Initial per-file custody is in coordinator `coordination/status/e7q-cirq-20261016-custody.json`.

Publication-preparation reconciliation, 2026-10-16: authenticated live `main` remains **58d4e927869e0228b32ce7cd034bf06bb799dc48**, equal to candidate HEAD and `origin/main`. The checkout's local `main` is older (`ce9d969a3337ee76b894dae11e8e243ff09a7390`, 17 commits behind); it was not checked out or changed. Earlier PR labels/head metadata in this audit were not reliable current coordination evidence and are superseded by the following live inventory: PR92 Joint planning reconciliation, PR91 two-qubit entanglement reconciliation, PR90 v0.15 capability-map reconciliation, PR89 capability-map refresh, PR81 exact-qubit quantum-view adapter, PR80 quantum-view adapter plan, PR79 Joint planning pilot, PR77 v0.15 capability map and PR59 entanglement assurance. None is incorporated or modified here. Current open-PR path overlap is limited to shared workflow/review registration (PR92/79), review registration (PR91/81/59) and build-plan documentation (PR90/89/77); path overlap does not establish a semantic conflict. Recheck exact live heads before approved publication. Historical build-plan language saying Q-A4 is uncommitted is not current main: Q-A4 merged via PR88, followed by PR93. Protect current APIs rather than reimplementing those milestones.

`E7GT-Ecosystem/E7G-T` main: **4d6e02f16363f2333961cf4350d584c92d51bbc6**. Its v0.15/MSC1 canonical reference is 428315 bytes, SHA256 `2ff03589387cbd216bb2559957c1d6959ca132b251d484826168d1b19d33341a`. Release manifest `E7G-T_v0.15_Experimental_Release_Manifest.md`: 4910 bytes, SHA256 `0569f21cf769fe30bd42a776132a5236aa90833192047aa2e65384f3d185fa66`; manifest baseline 86653557f5b5780a984f3a2dab226213ebbe3702. E7Q's constitutional RGP/0.1 reference remains v0.12.1-RGP2. New mathematical canonical authority is not automatic runtime migration. No kernel file, consumer pin or historical identity is changed.

## Inventory at the exact E7Q base

| Capability | Disposition | Evidence, method and precise boundary |
|---|---|---|
| Cirq export | EXISTS | `src/e7q/adapters.py:72–101`, `cirq_source`/`adapt(..., "cirq")`; `tests/test_vendor_adapters.py`. Dependency-free generated Python, canonical built-in gates and full-register key `c`; existing PASS means generation, not SDK execution. |
| Safe Cirq return/admission and executed round trip | ABSENT | Repository-wide code/test search and dedicated source reads found no inbound Cirq or executed SDK verifier. Missing work is an optional bounded admission/execution path, not another exporter. |
| Native circuit representation | EXISTS | `src/e7q/language.py`: frozen `Program`/`Operation`, `parse`, `validate_program`, `run`, `verify`. Do not create another Circuit IR. q0 is first tensor axis/MSB; measurement destinations must be explicit. |
| QASM interchange | EXISTS | `src/e7q/openqasm2.py` typed non-executing admission; `src/e7q/ir/circuit.py` guards resource expansion. Includes are declarations, not Python execution. Not a Cirq round-trip implementation. |
| Numerical full-operator comparison | EXISTS | `language.compare`/`comparison_result`, `tests/test_equivalence.py`: exact, tolerance, global-phase and measurement criteria are separate. Exact means zero floating-point error, not symbolic algebra. Existing measurement compares all basis-column probabilities, not merely initial-zero samples. |
| Algebraic reference relations | EXISTS | `ir/unitary.py`, `ir/real_unitary.py`: bounded signed permutation and real-H criteria. Do not broaden them to Cirq simulator observations. |
| Optional SDK comparers / stabilizer | EXISTS / PARTIAL | `ir/qcec.py`, `ir/pyzx.py`, `ir/native_qcec_workflow.py`, `stabilizer.py`; optional SDK workflows remain separate; no open PR is incorporated. Optional-package execution availability is environment-specific, not inferred from code existence. |
| E7Q-IR evidence and conformance | EXISTS | `ir/envelope.py`, `graph.py`, `conformance.py`: `e7q.ir.artifact/v0alpha1`, `e7q.ir.graph/v0alpha1`; eight artifact kinds, typed relations, canonical content identities and F0/F1/F2 distinctions. Native F2 is implemented, but does not authenticate external SDK execution. |
| Source/receipt/candidate paths | EXISTS | `ir/native_semantic.py`, `ir/receipt_binding.py`, `ir/candidate_family.py`, `ir/transformation_history.py`. Q-A3/Q-A4 and PR93 are reused/preserved, not duplicated. |
| Resource controls | EXISTS | `resources.py` preflight; qcec/PyZX child-process deadlines and native semantic controls. Resource preflight alone is not a sandbox. New SDK execution needs its own bounded child, not arbitrary Cirq-object pickling. |
| Cirq dependency pin/extra | ABSENT at base | `pyproject.toml` has no Cirq optional group. New local choice is cirq-core 1.6.1, lazy-loaded. Default core dependencies must remain unchanged. |
| Licensing | EXISTS | Root Apache-2.0 code, CC BY-SA documentation, `docs/licensing/COMMERCIAL_POLICY.md`, five exact open-core decisions in component register. New adapter is adjacent to public `adapters.py`, not moved into protected/commercial E7Q-IR code. Existing five hashes/licenses stay unchanged; no relicensing or ownership certification. |
| Current Google hardware or authenticated external execution | NOT_YET_VERIFIED / excluded | No credentials, device submission or provider-authentication work is authorized or necessary. |

## G0 decision and minimal local slice

Developer confirms the missing slice: **existing native source → unchanged exporter bytes → restricted non-executing admission of that exact dialect → pinned isolated Cirq pure-state simulation → native E7Q assessment and versioned existing E7Q-IR graph**. Restrict to two qubits, 64 gates, one terminal complete identity-map measurement. No arbitrary Python file execution, arbitrary Cirq object/gate protocol, general JSON deserializer, new equivalence engine, new repository, kernel adoption or schema migration.

Native E7Q comparison assesses the original and returned admitted Programs. A separate all-basis Cirq/native numerical consistency check tests the SDK mapping. The graph is validated at F1. The SDK observation is **not** promoted into native F2 scientific validity, F3 authentication, actual hardware evidence or an exact algebraic theorem. Independent small analytic test oracles are required to avoid shared-map agreement masquerading as independent validation.

## Impact and staging

Changes proposed after G0: one optional public adapter module, one focused test module, a Cirq optional dependency group, additive workstream registration, additive `REVIEW_CAMPAIGN.json` test registration (required by the existing coverage gate), and this audit/contract/capability/environment/validation documentation. No edits to existing exporters, language, comparers, kernel, E7Q-IR schemas, fixture bytes, receipt/candidate interfaces or licensing register.

PR-A proposal: audit and contract with pinned sources, clear loss table and rejection/security rules; G0/G1 documentary review. PR-B proposal: safe adapter and independently authored tests; optional dependency, native semantic evidence, F1 graph and tamper/replay tests. PR-C remains a separately reviewed F2 semantic-adapter question if a concrete missing validator is demonstrated; do not invent it to satisfy a label. No PR is automatically published, merged, tagged or deployed by this local implementation mandate.

Test outcomes, environment and residual gates belong to `VALIDATION_REPORT.md`. Initial baseline execution lacked installed E7Q distribution metadata, producing 51 environment errors; the original failure is retained in coordinator logs. Editable installation in the isolated environment repairs the prerequisite, not product behavior.
