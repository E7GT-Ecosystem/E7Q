# WP0 reconciliation — fresh verification and custody

Date: 18 October 2026. Status: **computational reconciliation recorded; scope PROPOSED; owner acceptance and independent scientific review NOT recorded**.

This is not retrospective preregistration or G0–G3 acceptance. Read with the [inventory](BASELINE_INVENTORY.md), [claim register](CLAIM_REGISTER.md), [scope ADR](ADR-0001-SCOPE.md) and [dependency plan](WP1-WP3_PLAN.md).

## Exact source custody

- Upstream baseline: `b7989c647e5d0e22ed1128c41aceb2dda2f23405`.
- Original local pilot: `4be5125c3198c9db980865c57814cb41aa4b13b5`. Its Git object is unavailable here. Equal-tree provenance remains the supplied handoff's attestation, not independent original-object verification.
- Published pilot: `6f66233e68d3cd52a3f01f6548259003e497b2c5`, sole parent exactly the baseline, tree `f58a7e4d41afb7bef68244ca333309e9e55b06f6`.
- Reconciliation starts at handoff `88467d51b21d3e072baae583fc4f23e676db59d6`; the handoff and developer buildmap are later additions, not files retrospectively inserted into the pilot commit.
- Published pilot versus baseline: nineteen additions under `pilots/qec_0_1/`, no baseline modification/deletion/rename. All historical pilot/result bytes remain unchanged.
- Verified all seven declared pilot source digests, six historical result digests and seven companion source digests from the preserved manifest. These unkeyed digests establish byte equality, not authenticated execution or scientific truth.
- Governing architecture pin remains `fc4cdf95c6434e653efbe017587aab60b4b2a86c` (v0.12.1-experimental/RGP2). Optional companion checkout `4d6e02f16363f2333961cf4350d584c92d51bbc6` is a separately pinned finite experiment, not an architecture migration.

Reconciliation used an isolated local checkout. Baseline execution came from a `git archive` scratch copy; pilot scripts ran from a separate scratch copy; the original pilot was never used as an output directory. Companion source was downloaded at the exact commit and its manifest-listed evaluator files checked before execution. Existing checkout HEAD/status/index and dirty-file custody are checked separately in the evidence record.

## Clean environment and command provenance

A new virtual environment used Python 3.12.3, NumPy 2.5.4, pytest 8.4.2, Stim 1.16.0 and jsonschema 4.26.0. Baseline package metadata was installed from its scratch archive as E7Q 1.0.0rc12; imports remained bound to that archive's `src/e7q`, not a globally installed or edited package. Installed distribution versions, exact command arguments, source/result hashes and raw logs are retained under [evidence](evidence/wp0-20261018/).

Commands used `PYTHONDONTWRITEBYTECODE=1`, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`, `PYTHONPATH=<baseline>/src`, and `E7GT_CHECKOUT=<pinned companion>`. No optional-reference absence is silently treated as agreement. Qiskit, Cirq, MQT QCEC and PyZX were not installed for this check; skipped coverage is not claimed.

The evidence bundle records exact host paths for this execution. Portable replay substitutes `B` (archive of the exact baseline), `C` (scratch copy of the published pilot), `K` (the exact companion checkout), `V` (clean environment) and `OUT` (fresh scratch logs):

```bash
export PYTHONPATH="$B/src" PYTHONDONTWRITEBYTECODE=1
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
export E7GT_CHECKOUT="$K"
"$V/bin/python" -m pip install --no-deps --no-build-isolation "$B"
(cd "$C/reference" && "$V/bin/python" -B qec_probe.py)
for script in adapter conventional decoder_table claim_controls; do
  "$V/bin/python" -B "$C/$script.py"
done
"$V/bin/python" -B "$C/profiles.py" "$K"
"$V/bin/python" -B -m unittest discover -s "$C" -p 'test_*.py' -v
(cd "$B" && "$V/bin/python" -B -m pytest -q -p no:cacheprovider \
  --basetemp="$OUT/pytest" tests)
"$V/bin/python" -B "$K/proposals/msc-0.1/test_e7gt_msc_v0_1.py"
"$V/bin/python" -B "$K/packages/rec-0.1/test_e7gt_rec_v0_1.py"
"$V/bin/python" -B -m e7q.cli qec-homomorphism XII IXI \
  --generator ZZI --generator IZZ
"$V/bin/python" -B "$B/pilots/qec_syndrome/reference_checker.py"
```

Install the declared test dependencies before these commands. Run the licensing checker against a real checkout containing its Git index, not an archive: `python -B scripts/check_licensing_boundary.py --root <checkout>`.

## Fresh results

| Surface | Fresh result | Boundary |
|---|---|---|
| Historical independent `qec_probe.py` | Completed successfully | Standalone diagnostic source, not native execution or author-independent review |
| Phase-insensitive algebra comparison | 64/64 match | Two ordered parity bits for three-position Pauli strings, not phase-aware algebra |
| Specialized native corpus | 77/77 agree with dense oracle | Verdict agreement includes expected FAILs, not 77 valid recoveries |
| Good specialized recovery | 16 PASS / 16 | Four declared preparations × `{III,XII,IXI,IIX}` |
| Swapped specialized recovery | 8 PASS / 8 FAIL | Eight FAILs are expected adverse controls; invariant cases remain PASS |
| Wrong syndrome / wrong recovery | 16 FAIL / 16 each | Both are expected negative groups |
| Phase control | One FAIL | Explicitly not phase-error correction |
| Double-X controls | Three PASS / nine FAIL | The three logical-plus passes are state-specific; no code-wide two-error correction claim |
| Independent Stim comparison | All 77 agree with native/dense verdicts | Separate simulator implementation; same authored corpus/expectations, not independent scientific review |
| Coherent full-table corpus | 33 cases completed | Twenty-four PASS, nine FAIL; decomposed coherent controls, not measured-syndrome classical feedforward |
| Claim-boundary controls | Logical-plus-only, dropped quantum info, wrong ordering, false phase claim observed | Limitations were preserved, not reclassified as successes |
| MSC/REC profiles | Expected finite outcomes reproduced | unique/ambiguous/incompatible/unsupported/resource_limit; REC supported/both/neither, scope expansion and rehashed forgery rejected; replay PASS |
| Pilot tests | 12 passed | Historical pilot test assertions, not newly designed feature tests |
| Companion model tests | MSC 26 passed; REC 24 passed | Pinned optional finite models only |
| Baseline focused tests | 40 passed, one skipped | Actual focused selection differs from historical report's 62-test selection |
| Baseline complete suite | **1202 passed, 12 skipped** (98.25 s) | Initial missing-metadata failure and recovered run are both retained; skipped tests are not covered |
| Existing syndrome CLI/checker | CLI PASS and six fixture syndromes plus XOR homomorphism PASS | Existing APIs unchanged; checker is a bounded fixture check |
| Licensing boundary | PASS | Existing declared licensing rules only; no new rights clearance |

Raw observed timings remain in evidence; the unoptimized native path was slower than the dense oracle in this local corpus. No statistical benchmark, speedup, hardware, noise threshold, general recovery theorem or physical fidelity claim follows.

## Ordering history

The historical report describes twelve failures after a reversed-label bridge. Its original failed circuit/log is not supplied or manifested; do not erase or reconstruct that run as fact.

Fresh diagnostic mutations establish that swapping **only the two ancilla positions** produces eight failures, whereas reversing the **whole five-bit label** produces twelve. Thus twelve is compatible with full-register reversal: no historical count contradiction has been established. The fresh mutations and their per-case outcomes are retained in `ordering-hypotheses.json`. They are diagnostic hypotheses, not provenance of the historical failure.

## Failures and recovery ledger

1. Some worker read commands used unavailable `rg`/`python`; corrected inspection used dedicated search or `python3`. A worker launch cwd typo was bypassed by absolute correct paths. Failed messaging without a team ID was replaced by direct parent messaging. No failed read operation changed product files.
2. The first follow-up CLI check incorrectly used `python -m e7q`; this package has no `__main__`. Reading `cli.py` confirmed `python -m e7q.cli` and required positional operands/generators. The corrected invocation passed.
3. The first licensing command used a nonexistent plural filename. Reading the script inventory confirmed `scripts/check_licensing_boundary.py`; its corrected real-checkout invocation passed.
4. The initial complete suite had 51 failures, 1151 passes and 12 skips because a source-only `PYTHONPATH` lacked installed E7Q distribution metadata used by the native IR evaluator. No product fix was made: the exact baseline was installed into the scratch environment, import origins/version checked, and the suite rerun. Both logs remain evidence; final status is taken only from the recovered run.
5. Proposed-document edit hunks initially did not match the actual draft text. They applied no changes. Exact files were reread; anchored edits then clarified simulated execution, retained original G2 sequencing and removed worker-assignment prose. Final paths/content/hashes were checked.

**tool-error recovery verified** applies only to the corrected command/environment/document operations and final checks recorded in evidence; original failures remain visible. It does not convert experimental results into accepted science.

## Internal document QA

A separate read-only document QA pass found three draft defects: stale computational-pending wording, seven manifest-listed pilot sources described incorrectly as nine, and a dependency diagram omitting the full G2 barrier already required by its prose. All three were corrected before submission and the package regenerated. This review checks document/evidence consistency only; it is not independent scientific acceptance. No runtime or historical evidence was changed to resolve these findings.

## Gate disposition

Inventory, claims, proposal and computational reconciliation are available for review. ADR stays **PROPOSED**. G0 requires an explicit owner decision against the exact manifest revision; independent mathematical/scientific review is not recorded. Generic F2 is not QEC validation. Original full G2 remains open; WP3 implementation is not authorized by a coherent-only milestone. Further feature work, commit/push/PR/merge/release/deployment and reviewer contact remain unapproved.
