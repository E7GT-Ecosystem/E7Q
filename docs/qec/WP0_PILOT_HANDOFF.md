# QEC WP0 — pilot reconciliation handoff

Prepared 18 October 2026. This brief is subsequent to the experimental pilot; it is not a historical document in the pilot commit or an accepted G0/ADR record.

## Where to find the actual pilot

Repository: https://github.com/E7GT-Ecosystem/E7Q

Branch: `codex/qec-0.1-reference-adapter`

- Upstream baseline / pilot parent: `b7989c647e5d0e22ed1128c41aceb2dda2f23405`.
- Original local pilot commit: `4be5125c3198c9db980865c57814cb41aa4b13b5`.
- Published pilot commit: `6f66233e68d3cd52a3f01f6548259003e497b2c5`.
- Verified identical original/published Git tree: `f58a7e4d41afb7bef68244ca333309e9e55b06f6`.
- The shell push could not authenticate. Publication used the connected GitHub API, which creates new commit metadata and therefore a different commit ID. The original commit object is not claimed to be present upstream; every pilot file and the complete baseline tree are byte-identical. Fetch and inspect the published commit below.
- Pilot directory: `pilots/qec_0_1/`.
- This brief is added in a subsequent commit on the same branch.

The pilot initially existed only in the originating session's checkout. The earlier implementation ZIP contained tracked source snapshots without Git metadata, explaining its absence from other workspaces and upstream at that time. The owner subsequently authorised pushing this branch and handoff. Publication does not constitute merge, release, owner acceptance of G0 or independent scientific review.

Fetch into an existing E7Q clone without changing its current worktree:

```bash
git fetch origin codex/qec-0.1-reference-adapter
git show 6f66233e68d3cd52a3f01f6548259003e497b2c5:pilots/qec_0_1/REPORT.md
git worktree add ../E7Q-qec-wp0 origin/codex/qec-0.1-reference-adapter
```

Alternatively clone this branch into a separate directory. Preserve existing work; do not force-reset another branch.

## Read first

1. `pilots/qec_0_1/REPORT.md`: interface audit, computations, results, failure history and limitations.
2. `pilots/qec_0_1/README.md`: experiment/file map and reproduction entry points.
3. `pilots/qec_0_1/SOURCE_MANIFEST.json`: source, reference and result digests.
4. `pilots/qec_0_1/results/`: actual E7Q reports, circuit source, conventional oracles, MSC/REC witnesses and timings.
5. `docs/qec/E7Q_QEC_Developer_Buildmap_v0.1.md`: owner-supplied proposed programme, retained as supplied.

## Source pins and preservation

E7Q retains its documented v0.12.1/RGP2 architecture pin at `fc4cdf95c6434e653efbe017587aab60b4b2a86c`. The pilot's optional MSC/REC experiments used the separate E7G-T checkout `4d6e02f16363f2333961cf4350d584c92d51bbc6` from https://github.com/E7GT-Ecosystem/E7G-T. Relevant source digests are in the manifest. Retain the companion evaluators' historical edition labels; do not describe their execution as automatic downstream migration to v0.15.

The pilot adds only `pilots/qec_0_1/`. It does not alter existing simulator/verifier code, CLI commands, IR formats, identity semantics or the legacy `src/e7q/qec.py` module. Preserve that module and its imports; the buildmap's proposed `qec/` package layout is not yet approved.

## Bounded WP0 assignment

Reconcile the buildmap with the upstream baseline and the actual pilot. Prepare:

- `docs/qec/BASELINE_INVENTORY.md`: current default branch, issues/PRs/tags/CI, existing interfaces and schemas, source pins, dependencies/licensing, clean-environment checks and existing versus proposed features.
- `docs/qec/ADR-0001-SCOPE.md`: additive profile scope, compatibility, exact profile/source selection, supported domains, exclusions and first implementation package.
- `docs/qec/CLAIM_REGISTER.md`: claim, precise scope, evidence, evaluator, limitations and reviewer status.
- A dependency-ordered WP1–WP3 issue/PR plan. Prepare issue drafts locally unless external posting is separately authorised.

Reproduce the unchanged existing `qec-homomorphism` example and independent syndrome checker. Reproduce the pilot's substantive results with exact dependency/environment records. Record discrepancies, missing optional dependencies and exclusions. Do not manufacture chronology, prospective registration or reviewer acceptance.

Do not add a decoder, migrate the kernel pin, refactor the QEC namespace, or promote generic IR F2 to QEC semantic validation during this WP0 slice.

## Claims available for reconciliation

- Existing E7Q parses, simulates and verifies actual submitted circuits; Python reference assertions are not counted as E7Q findings.
- The specialized-recovery corpus has 77 cases with agreement against a separate dense Pauli-matrix oracle and a separate Stim 1.16.0 tableau oracle.
- Valid cases: 16/16 pass. Swapped decoder: eight of 16 fail as expected. Wrong syndrome and wrong recovery: 16 failures each. Phase control: failed restoration with zero syndrome.
- A separate coherent full-decoder-table circuit reproduces the 33 reference/control cases. It is not classical measurement/feedforward decoding.
- Two-X controls include three logical-plus passes because logical X preserves that particular state. These do not establish code-wide correction.
- MSC/REC results establish only the tested finite structural/evidence behaviour. No new correction capability, physical result, speed advantage or independent external review is established.
- Prior local validation: 12 new tests; 62 existing E7Q tests with the Qiskit module skipped; 26 MSC and 24 REC tests. Re-run rather than treating these reports as independent reproduction.
- Original experiment had a reference/native bit-order mismatch; the corrected bridge and regression are documented. That was an adapter defect, not an E7Q finding.
- Timings compare measured workflows with different parsing, tracing and simulation overheads; they are not a universal algorithmic comparison.

## Gate and decision status

G0 remains incomplete until the required formal inventory, baseline reproduction, scope ADR and owner acceptance are recorded. The experimental pilot predates the buildmap; do not retrospectively mark its gates passed. The next requested deliverable is a reviewable WP0 reconciliation, followed by owner scope acceptance before further product implementation.

Required response format: CURRENT STATE → CHANGES → EXECUTED EVIDENCE → UNSUPPORTED CLAIMS → RISKS → DECISIONS NEEDED → NEXT PR.
