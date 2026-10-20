# QEC G0 integration repair — local verification

**Date:** 19 October 2026  
**Builder/thread:** QEC G0 integration repair local / Trejo Mansfield  
**Status:** ready for coordinator — QEC G0 integration repair local  
**Boundary:** integration prerequisite only; G0 remains OPEN, WP1 not started, no scientific acceptance.

## 1. Baseline, authority and custody

This is the expressly authorized local correction to test discovery and CI integration, not implementation of the proposed QEC programme. No runtime implementation, historical test, mathematical expectation, JSON schema, architecture pin or accepted WP0 artifact was changed.

Authenticated live refs were checked before work and rechecked during final preservation verification:

| Ref | Exact SHA |
|---|---|
| E7Q `main` | `b7989c647e5d0e22ed1128c41aceb2dda2f23405` |
| Published `docs/qec-wp0-review-20261018` | `ec6fbd91982ed7204ebb8b2e3e3b2e8b5ddeab57` |
| Optional E7G-T companion | `4d6e02f16363f2333961cf4350d584c92d51bbc6` |

The repair is uncommitted on `local/qec-g0-integration-repair-20261019`; HEAD remains the published review SHA. Its isolated [worktree](/home/luxaeternum/Work/Dev/E7-ECosystem/coordination/checkouts/e7q-qec-g0-integration-local-20261019) is separate from the untouched published checkout. Seventeen pre-existing E7Q worktrees, including 46 dirty paths, were fingerprinted before work; their HEADs, exact status bytes, staged diffs and dirty-file bytes remain unchanged.

Governing boundaries remain the [buildmap](/home/luxaeternum/Work/Dev/E7-ECosystem/coordination/checkouts/e7q-qec-g0-integration-local-20261019/docs/qec/E7Q_QEC_Developer_Buildmap_v0.1.md), [scope ADR](/home/luxaeternum/Work/Dev/E7-ECosystem/coordination/checkouts/e7q-qec-g0-integration-local-20261019/docs/qec/ADR-0001-SCOPE.md), and [WP1–WP3 plan](/home/luxaeternum/Work/Dev/E7-ECosystem/coordination/checkouts/e7q-qec-g0-integration-local-20261019/docs/qec/WP1-WP3_PLAN.md). E7G-T v0.12.1-experimental/RGP2 at `fc4cdf95c6434e653efbe017587aab60b4b2a86c` still governs new architecture. The companion pin above identifies only the opt-in historical finite MSC/REC experiment, not a constitutional migration; historical edition labels were retained.

## 2. Cause and smallest correction

Unrestricted root pytest discovery reached two optional historical pilot modules. The base CI environment lacks Stim; the simulation-reference environment supplies Stim but not the external MSC/REC source checkout. Root collection therefore coupled normal regression execution to undeclared optional pilot prerequisites.

Exactly four product-tree paths comprise this repair:

| Path | Change |
|---|---|
| [pyproject.toml](/home/luxaeternum/Work/Dev/E7-ECosystem/coordination/checkouts/e7q-qec-g0-integration-local-20261019/pyproject.toml) | Add `testpaths = ["tests", "scripts"]`; retain existing source pythonpath. |
| [.github/workflows/ci.yml](/home/luxaeternum/Work/Dev/E7-ECosystem/coordination/checkouts/e7q-qec-g0-integration-local-20261019/.github/workflows/ci.yml) | Preserve the existing three jobs byte-for-byte; add explicit pilot and separately selected profile jobs. |
| [scripts/check_qec_ci.py](/home/luxaeternum/Work/Dev/E7-ECosystem/coordination/checkouts/e7q-qec-g0-integration-local-20261019/scripts/check_qec_ci.py) | Small standard-library integration guard around unchanged historical unittest entrypoints. |
| This new report | Record local commands, evidence, preservation and acceptance limits separately from immutable WP0 evidence. |

Both normal discovery roots matter: using only `tests` would silently drop the existing licensing and Cirq integration script controls. Static inventory is 54 regression modules, two script-control modules, and two separately selected historical pilot modules. Runtime collection confirmed default discovery is exactly equivalent to explicitly selecting `tests scripts`: **1,234 node IDs**, including all **21 script-control tests**. There are no new blanket exclusions, manufactured skips, modified tests or relaxed mathematical assertions.

### Explicit required lanes

- `qec-pilot-reference`: Python 3.12, existing `.[test,stabilizer]` extras, dependency consistency check, then `python3 -B scripts/check_qec_ci.py pilot`. Requires NumPy, installed E7Q metadata and Stim **1.16.0**; executes all nine historical adapter tests. No Qiskit or companion requirement is introduced into this job.
- `qec-profile-reference`: opt-in via `workflow_dispatch` boolean `qec_profiles`, default false. When selected, checks out the exact companion SHA into `.qec-companion`, installs `.[test]`, checks dependency consistency, then invokes the profile guard with an explicit absolute companion path. Executes all three historical profile tests; Stim is not intrinsically required.
- An unselected profile job is **not requested**, not proof of profile execution. Once selected, dependency absence, checkout failure, wrong pin or wrong source digest is a nonzero failure. No `continue-on-error`, `importorskip`, `|| true` or implicit dependency fallback was added.
- No existing baseline/simulation job depends on the optional profile job. Manual hosted dispatch remains a future action after normal workflow availability/admission; no dispatch was performed here.

The guard checks package imports and installed metadata, NumPy/Stim distribution-owned module paths and matching module versions, exact E7Q/pilot module origins, source-manifest digests, complete expected test counts and successful execution with zero skips/xfails. Profile mode verifies companion Git root, exact HEAD and all seven manifest-bound companion files **before importing** the historical profile suite; it sets `E7GT_CHECKOUT` before its module-level capture and checks actual loaded MSC/REC/replay origins afterward.

No historical `adapter.py`, `conventional.py` or `profiles.py` main was invoked in place: those overwrite historical results. Only their existing test entrypoints ran.

## 3. Reproduction and local results

All execution below used Linux x86_64 and Python **3.12.3**, with fresh isolated virtual environments and editable E7Q installed from the repair checkout. Actual runtime package origins, editable-install metadata, installed versions and dependency consistency are retained in the local [audit bundle](/home/luxaeternum/Work/Dev/E7-ECosystem/.tunc/tmp/qec-g0-integration-20261019-5hddmkek).

Common observed versions: E7Q `1.0.0rc12`, NumPy `2.5.4`, pytest `9.1.1`, jsonschema `4.26.0`. The pilot environment adds Stim `1.16.0`; the separate simulation environment adds the declared Stim `1.16.0` and Qiskit `2.5.2`. Base/profile-only execution had no importable Stim, Qiskit or Cirq, and no inherited `E7GT_CHECKOUT`. The optional checkout resided only in the audit directory and was passed explicitly for profile execution. All three environments passed `pip check`.

Commands were run from the repair root. These variables identify the retained local evidence, not additional product dependencies:

```bash
R=/home/luxaeternum/Work/Dev/E7-ECosystem/coordination/checkouts/e7q-qec-g0-integration-local-20261019
A=/home/luxaeternum/Work/Dev/E7-ECosystem/.tunc/tmp/qec-g0-integration-20261019-5hddmkek
cd "$R"
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
unset E7GT_CHECKOUT

# Separate fresh venvs were installed with these existing extras:
"$A/baseline-venv/bin/python3" -m pip install -e "$R[test]"
"$A/pilot-venv/bin/python3" -m pip install -e "$R[test,stabilizer]"
"$A/simulation-venv/bin/python3" -m pip install -e "$R[test,simulation-test]"

"$A/baseline-venv/bin/python3" -B -m pytest -q -ra -p no:cacheprovider \
  --basetemp="$A/baseline-pytest-temp" --junitxml="$A/baseline.xml"
"$A/simulation-venv/bin/python3" -B -m pytest -q -ra -p no:cacheprovider \
  --basetemp="$A/simulation-pytest-temp" --junitxml="$A/simulation.xml"
"$A/pilot-venv/bin/python3" -B scripts/check_qec_ci.py pilot
"$A/baseline-venv/bin/python3" -B scripts/check_qec_ci.py profiles \
  --companion "$A/companion"
```

| Check | Observed result |
|---|---|
| Complete default baseline without optional QEC dependencies | **1,223 passed, 12 skipped; 9 subtests passed** in 93.71 seconds |
| Complete simulation-reference dependency environment | **1,236 passed, 11 skipped; 9 subtests passed** in 93.85 seconds |
| Required historical adapter lane, final guard | **9 passed, zero skipped** |
| Selected MSC/REC lane, final guard, no Stim | **3 passed, zero skipped** |
| Existing licensing boundary checker | PASS, declared scope only; not rights certification |
| Standalone licensing negative controls | **11 passed** |
| Standalone Cirq CI/script controls | **10 passed**; existing Cirq workflow remains byte-preserved |
| Existing syndrome CLI and dependency-free reference checker | PASS; six syndromes and one homomorphism checked |
| Integration guard audit harness | **26 checks passed**, including the required positive executions and negative/synthetic controls below |
| Default vs explicit baseline collection | Identical node IDs; all 21 script-control tests retained |
| Workflow YAML and structural preservation checks | Parsed successfully; original jobs, permissions, optional input/condition and exact companion checkout pin verified |

The baseline's pre-existing optional skips are one absent-Stim module and eleven absent-Cirq simulator probes. Simulation-reference has the same eleven absent-Cirq probes. These are disclosed existing optional-backend boundaries, not new skips or substitutes for the required QEC lanes. The nine passing subtests are reported separately by pytest and included in JUnit totals; they must not be confused with additional top-level test methods.

The unchanged syndrome commands were also exercised explicitly:

```bash
"$A/baseline-venv/bin/e7q" qec-homomorphism XII IXI \
  --generator ZZI --generator IZZ --name "three-qubit repetition code" \
  -o "$A/syndrome-homomorphism.json"
"$A/baseline-venv/bin/e7q" qec-syndrome XXX --generator ZZI --generator IZZ
"$A/baseline-venv/bin/python3" -B pilots/qec_syndrome/reference_checker.py
"$A/baseline-venv/bin/python3" -B scripts/check_licensing_boundary.py
"$A/baseline-venv/bin/python3" -B scripts/test_licensing_boundary.py
"$A/baseline-venv/bin/python3" -B scripts/test_cirq_ci.py
```

The CLI reports the original homomorphism with `passed: true`; `XXX` has syndrome `00` but remains classified **logical**, not harmless identity.

### Fail-closed evidence

The [audit harness](/home/luxaeternum/Work/Dev/E7-ECosystem/.tunc/tmp/qec-g0-integration-20261019-5hddmkek/verify-integration-guards.py) and [guard results](/home/luxaeternum/Work/Dev/E7-ECosystem/.tunc/tmp/qec-g0-integration-20261019-5hddmkek/guard-results.json) distinguish actual subprocess failures from in-memory synthetic integration controls. All expected failures were asserted, not ignored:

- Real missing Stim: exit 1, `required dependency 'stim' is unavailable`.
- Python without site packages: exit 1, `required dependency 'numpy' is unavailable`.
- Missing companion argument/path, wrong companion Git pin, and a nested directory instead of its Git root: nonzero failures with explicit diagnostics.
- A separate synthetic copy of the pinned companion with one altered replay file: exit 1, `source digest mismatch`; the altered file was never executed. The real pinned checkout remained unchanged.
- Synthetic missing installed E7Q metadata, wrong Stim metadata version, shadow NumPy/Stim/E7Q origins and module/metadata version mismatches: rejected.
- Synthetic empty/partial discovery, incomplete execution, failures, errors, skips, expected failures and unexpected successes: rejected. A complete clean synthetic result was accepted as a positive control.

An internal read-only implementation review found the initial dependency-origin check insufficient. The guard was tightened to verify distribution ownership and module version, and the final delta was re-reviewed with no remaining findings. This is an AI code review, **not independent QEC scientific review**.

Key evidence: [baseline log](/home/luxaeternum/Work/Dev/E7-ECosystem/.tunc/tmp/qec-g0-integration-20261019-5hddmkek/baseline-pytest.log), [simulation log](/home/luxaeternum/Work/Dev/E7-ECosystem/.tunc/tmp/qec-g0-integration-20261019-5hddmkek/simulation-pytest.log), [final pilot log](/home/luxaeternum/Work/Dev/E7-ECosystem/.tunc/tmp/qec-g0-integration-20261019-5hddmkek/pilot-positive-final.log), [final profile/origin log](/home/luxaeternum/Work/Dev/E7-ECosystem/.tunc/tmp/qec-g0-integration-20261019-5hddmkek/profiles-positive-final-no-stim.log), [discovery checks](/home/luxaeternum/Work/Dev/E7-ECosystem/.tunc/tmp/qec-g0-integration-20261019-5hddmkek/discovery-checks.json). Installation logs, freezes, pip checks and individual negative-control logs remain in the same audit bundle. A freeze's VCS HEAD is not a binding of the uncommitted repair; use the changed-file digests below and final preservation record.

## 4. Preservation and exact local repair identity

The [preservation verifier](/home/luxaeternum/Work/Dev/E7-ECosystem/.tunc/tmp/qec-g0-integration-20261019-5hddmkek/verify-preservation.py) compares actual bytes of **351 protected tracked blobs** against HEAD, not merely Git status. It also verifies the 27 manifest-bound WP0 files, all 19 historical pilot files and pre-existing worktree custody. The final [preservation record](/home/luxaeternum/Work/Dev/E7-ECosystem/.tunc/tmp/qec-g0-integration-20261019-5hddmkek/preservation-final.json) binds all four repair paths, including this report. No changes are staged.

- WP0 acceptance manifest SHA-256 remains `aaa99bd09d52e3bfb5fbad54ad86c05d586a11610d2c6ed4366c2a257f24561a`.
- Actual `pilots/qec_0_1` Git subtree is `f71f57258eb2186a5abf3e611baa6580192de151`, recomputed identically at published pilot commit `6f66233e68d3cd52a3f01f6548259003e497b2c5` and review HEAD. This is the subtree identifier, not the pilot commit's full repository tree.
- All seven pilot-source, six stored-result and seven companion-file source-manifest digests remain valid. All historical files, accepted evidence, schemas, runtime code, existing tests and architecture documents remain byte-identical.
- Isolated environment installation generated normal ignored editable-build metadata; these are not source changes or included repair deliverables.

| Repair source | SHA-256 |
|---|---|
| `pyproject.toml` | `85c62e5014eca735e54d28175b13584c14d52c81846e3b11162ec6fc67370106` |
| `.github/workflows/ci.yml` | `4520cb37e8e5ba0dbcf4975c99d25710041264b98787f0d00be1a79ad3969506` |
| `scripts/check_qec_ci.py` | `d6e8085ac57a3ba22958a3ad9e9f2a3a16cd8230a5901424eca6bd41990c6320` |

Final preservation command, after this report exists:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B "$A/verify-preservation.py" --final
```

## 5. Acceptance limits and coordinator decision

**Recommendation:** ready for coordinator — QEC G0 integration repair local. The two observed collection-coupling defects have a bounded, locally verified correction. This is not a declaration that the complete G0 gate passed.

Still unrun here: hosted GitHub Actions, the Python 3.11/3.13 matrix, the actual Cirq SDK/simulator gate, external reproduction, independent scientific assessment, standalone companion self-test suites, and full historical result regeneration. `actionlint` is unavailable; YAML parsing, structural assertions, existing workflow controls and literal byte-preservation checks ran instead. No hosted CI success is claimed.

G0 owner acceptance remains open; the ADR remains proposed. WP1 has not started. The full G2 measured-syndrome/classical-feedforward requirement remains open and unwaived; WP3 remains blocked accordingly. Generic IR F2 is not QEC semantic acceptance. No new decoder, algebra package, QEC capability, theorem, hardware result, threshold, fidelity, novelty or provider authenticity is established by this repair.

No commit, push, PR, merge, release, deployment, cloud upload, external reviewer contact or coordinator message was performed. Coordinator review of this local diff and any subsequent hosted/publication action require the appropriate separate authorization. Historical WP0 documentation and manifest have not been rewritten to absorb this new evidence.

Trejo Mansfield · AI · Tunc
