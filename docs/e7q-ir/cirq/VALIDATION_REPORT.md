# E7Q-CIRQ/0.1 local validation — 2026-10-16

> Latest checkpoint: **publication preparation**, 2026-10-16. A second fresh environment verifies the unchanged adapter/CI: **83 focused passes/no skips; 1191 full passes/one optional Stim skip**. Only audit/handoff/report documentation is repaired in this continuation. Publication, hosted CI and external acceptance remain unperformed.

## Publication-preparation fresh verification — 2026-10-16

Primary and research candidates remain uncommitted at `58d4e927869e0228b32ce7cd034bf06bb799dc48`; live upstream `main` and cached `origin/main` match. Local `main` is seventeen commits older and was left untouched. No reset, rebase, merge, staging or remote write occurred. The current PR inventory replaces unreliable older audit labels; other open PRs overlap only shared workflow/registration/build-plan paths. Recheck them before approved publication.

New evidence root: `/home/luxaeternum/Work/Dev/E7-ECosystem/.tunc/tmp/e7q-cirq-publication-20261016-guda837h`. Fresh `venv` and `core-only` environments were created here, not reused from prior results. Linux x86_64/Python3.12.3, Cirq1.6.1, NumPy2.5.4, pytest8.4.2 and jsonschema4.26.0 retain the tested snapshot. Installation uses the exact requirements-plus-constraints and editable extras command recorded in the earlier reproduction recipe, with RUN changed to this root. All listed verification commands below were newly executed with a 1800-second harness budget, thread caps and no bytecode writes.

| Newly executed command/check | Actual result |
|---|---|
| Snapshot/constraints + editable `.[test,cirq]` installation, module/distribution pin | PASS; Cirq1.6.1 |
| `python -m pip check` | PASS; no broken requirements |
| `python -B scripts/test_cirq_ci.py -v` | 10 passed, 0.177s |
| Licensing boundary / `scripts/test_licensing_boundary.py` | PASS declared scope / 11 passed, 5.555s |
| `python -B -m pytest -q -ra tests/test_cirq_interop.py --junitxml=...` | **83 passed, 0 skipped, 27.14s** |
| `scripts/check_cirq_ci.py report` against actual focused XML | PASS; all three required SDK identities present |
| `scripts/check_cirq_ci.py bell` to a new exclusive output path | Native tolerance PASS, actual F1 PASS, analytic Bell probability PASS, actual recomputing fresh replay PASS, tamper rejected |
| `python -B -m pytest -q -ra --junitxml=...` | **1191 passed, 1 skipped, 120.46s** |
| Separate no-Cirq environment | E7Q import PASS; focused pytest returns0 with **72 passed/11 SDK skips, 0.89s**; CI gate correctly returns1: `focused suite has skipped` |
| Workflow inspection | YAML parse, preserved old jobs/triggers/permissions, new Bash and inline Python syntax PASS; actionlint unavailable; not hosted schema/runner execution |
| Whitespace and custody | `git diff --check` PASS; candidate source/test/CI/dependency/Bell bytes retained; research and other checkout HEAD/status/files preserved against initial snapshots |

The single full-suite skip is `tests/test_stabilizer_execution.py:11`, optional `stim` absent. No focused SDK skip is accepted in the dedicated job. No warning/deprecation lines appeared in focused/full test logs or either installation log. The smaller candidate does **not** include research tests: the historical research result of1243 passes is not its acceptance count. This actual result is1191 passes, without dropping assertions or changing feature scope.

Fresh and historical Bell graph IDs match `sha256:e34ce3fd7599edb688a79ef96b7da037a46d0deceeeab2b8fd447c3273bd0d55`; historical replay succeeds. Independent expected probabilities `[0.5,0,0,0.5]` match observed `[0.5000000000000001,0,0,0.5000000000000001]`. Historical JSON remains24065 bytes/SHA256 `cc083415b15b943de503a8450462d50498ccc11f340bcefc4d14d05288c5bde1`. All three evidence layers remain distinct: SDK mapping observation, native criterion assessment and F1 integrity; no F2/F3/hardware claim.

Two read-only AI audits found no blocking implementation/CI issue. One additionally reran eight real SDK case outcomes, analytic/F1 assertions and fresh/stored Bell replay/tamper controls in the earlier SDK venv; that cross-check is not the new fresh full run or external independent acceptance. Current residuals remain: version-only rather than hash locks, moving runner/Python patch/action inputs, environment-sensitive historical graph identity and a frozen83-case gate rather than a complete future identity manifest.

Only `CAPABILITY_AUDIT.md`, this report and `NEXT_AGENT_PROMPTS.md` change in the primary candidate during publication preparation. No new/duplicate CI job, adapter repair, licensing/register change, kernel repin or research integration was needed. The separate coordinator proposal and sixteen-file hash manifest are local-only approval material. Proposed final scope is one PR/two logical commits; the older PR-A/PR-B split below is superseded, not publication authority.

**Approval gates:** obtain explicit exact-file/hash-bound public-term and commit/push/one-PR approval to `E7GT-Ecosystem/E7Q`, base `main`. Licensing PASS certifies only declared boundary consistency; the adjacent adapter lies outside checker-protected IR/schema prefixes and existing register decisions grant it no publication authority. Core/criteria/schemas/licenses/kernel/historical evidence remain unchanged. Research demonstrations and optional v0.15 interpretation remain separate and experimental; no unique scientific benefit is established.

**Statuses:** local implementation/tests READY for scoped review; commit/push/PR NOT PERFORMED; hosted CI NOT RUN; external reproduction/acceptance NOT PERFORMED; merge/deployment NOT PERFORMED or authorized. External contact requires separate owner approval.

Initial read-only discovery failed because the workspace container is not a Git repository and `rg` is unavailable. Recovery used the exact named checkout, Git and Python inspection; no write was attempted by the failed command. Subsequent HEAD/status/file custody and diff checks confirm **tool-error recovery verified**. Raw logs/XML, dependency freeze, Bell check, live-main/open-PR snapshots and custody/manifest sidecars are retained under the new evidence root. No cloud upload or secrets disclosure occurred.

## Earlier local checkpoints

The following records retain earlier observations and their original limitations; they do not supersede the new checkpoint or authorize publication.

## Decision

The smallest missing executed return/evidence path is implemented locally on branch `feature/e7q-cirq-interoperability-20261016`, based on **58d4e927869e0228b32ce7cd034bf06bb799dc48** of `E7GT-Ecosystem/E7Q`. No implementation commit, push, PR, merge, release or deployment has been made. PR-A and PR-B are proposals only; publication requires explicit owner authorization. Full /0.1 acceptance remains pending a published pinned candidate and actual external reproduction. No production environment is involved.

WP0 confirmed an existing dependency-free exporter but no executed safe Cirq return path. Existing `Program`, exporter, comparer, preflight, artifact and graph contracts are reused. See [audit](CAPABILITY_AUDIT.md), [contract](INTEGRATION_CONTRACT.md), [machine capabilities](capabilities.json), [tested environment](requirements-tested.txt) and [next chat prompts](NEXT_AGENT_PROMPTS.md).

New code is one optional `src/e7q/cirq_interop.py` module. Cirq is not added to default dependencies; `pyproject.toml` adds only `[cirq]`. Existing CLI, exporter, comparer, kernel pins, schemas, native F2 validators and licensing register remain unchanged. Build-plan and review-campaign registration are additive, not replacements. The full-suite coverage gate requires the new test module to be declared in `REVIEW_CAMPAIGN.json`; existing campaign records remain byte-semantically unchanged. New code/tests retain Apache-2.0 SPDX. The licensing checker reports declared-boundary consistency, not legal ownership or contributor-rights certification.

## Observed verification

Environment: Linux x86_64, Python3.12.3, cirq-core1.6.1, NumPy2.5.4, pytest8.4.2, jsonschema4.26.0; all observed transitive distribution versions are in `requirements-tested.txt`. Isolated environment `/tmp/e7q-cirq-016-20261016`; E7Q installed editable, not copied into another project. No credentials or device access used.

| Check | Actual result |
|---|---|
| Existing baseline, excluding new adapter tests | **1098 passed, 1 skipped, 96.53s** |
| Independent adapter acceptance corpus | **83 passed, 25.89s**; eight real pinned SDK evaluations plus actual timeout/import-blocked worker probes |
| Complete combined suite | **1181 passed, 1 skipped, 129.32s**; exit0 after additive review-manifest registration. Skip: `tests/test_stabilizer_execution.py:11`, optional `stim` absent |
| Independent final read-only review | PASS: no remaining concrete safety/semantic/regression findings in adapter, focused tests, contract and packaging. Additional 71 fast probes passed; actual reverse-CNOT FAIL, real replay/tamper and malicious-AST/worker-record checks passed. This is an AI review, not external human reproduction. |
| Licensing boundary | `python -B scripts/check_licensing_boundary.py`: PASS, declared scope only |
| Dependency consistency | `python -B -m pip check`: no broken requirements |
| Whitespace | `git diff --check`: PASS |
| Capabilities vs runtime constants | SDK pin, gate map, width/operation/source/CPU/address-space bounds, mapping tolerance and observed sampling marker match |
| Inspectable Bell example | PASS; actual F1 validation and full real-worker replay; all-basis mapping error 1.1102230246251565e-16; ideal initial-zero probabilities [0.5,0,0,0.5] within 1e-14 |
| Protected custody | All 262 Q-A3, 281 Q-A4 and 432 kernel snapshot file hashes and HEADs preserved; no existing tracked source/schema/fixture/register changes in candidate |

Original failed runs are not counted as passes. First baseline attempt: 51 failed/1047 passed/1 skipped because the isolated environment lacked E7Q installed distribution metadata (`PackageNotFoundError`), repaired by `pip install --no-deps -e .`. First focused corpus: 69 passed/3 failed (one invalid test fixture; proposed missing-SDK status label mismatched agreed existing UNSUPPORTED vocabulary; absent explicit sampling marker). Next run:82 passed/1 failed because the test still expected sampling at top level. Fixed the valid fixture, retained explicit missing-dependency reason and existing status vocabulary, and added `method.sampling_status=NOT_ASSESSED` inside the hashed execution recipe; then all83 passed. No semantic assertions were removed to mask a product failure.

First combined-suite attempt hit the harness's 120s deadline after progress through67% without reported failures; process absence was checked before rerunning with600s. It is a verification-harness timeout, not a circuit TIMEOUT or quantum FAIL. The longer-budget run then reported1180 passed/1 failed/1 skipped: the existing review-campaign coverage gate required registration of the new test file. Added exactly one capability entry, structurally checked that every historical campaign field was preserved, reran the four campaign tests (4 passed), then reran the complete suite (1181 passed/1 skipped). No source or test assertion changed for that repair. The original failure/timeout logs remain in coordinator history. Read-only guessed-path failures were recovered by discovering/reading actual paths (`docs/e7q-ir/BUILD_PLAN.md`, actual IR package). **tool-error recovery verified** for corrected inspection and installed-metadata baseline recovery; the final full-suite result is reported separately above.

Coordinator raw evidence paths (not repository files): `.tunc/background-bash/d617ade8-3742-4544-8017-be6898f67237/stdout.log` (baseline), `daa6401a-d446-4c52-8b9d-3cd6fc9ecefd/stdout.log` under that same background-bash directory (focused), `53630f77-82ee-410f-b525-a8b51404a381/stdout.log` (combined harness timeout), `c3564521-550b-4148-9302-906df230dc6c/stdout.log` (longer-budget combined exposing registration omission), `3f5d3884-4cc0-411f-b0a3-a91136bc1b8c/stdout.log` (final full-suite PASS). Raw failure baseline: `787068cc-893c-4bbd-aa1d-50b606da7f11/stdout.log`.

## Acceptance matrix: bounded dispositions, not blanket completion

The independent initial admission/matrix expectations were written before implementation inspection; result accessors were subsequently aligned with the actual API. Test functions use finer-grained suffixes and sometimes group multiple handoff concerns; this table follows the handoff C01–C15 meanings.

| ID | Disposition and evidence |
|---|---|
| C01 | PASS in declared domain: Bell all-basis analytic matrix, initial-zero vector/probabilities, native assessment and F1 graph; stored example and full real replay. |
| C02 | PASS/domain-qualified: canonical cancellation controls and analytic matrices. H;H is tolerance PASS but existing floating-point exact FAIL (~roundoff), honestly reported; Z;Z gives literal I. No symbolic proof is claimed. |
| C03 | PASS: X;Z;X;Z = −I independently derived; existing exact FAIL/global-phase PASS. Z;Z is not misused as phase-only evidence. |
| C04 | PASS diagnostic boundary: Z vs I has zero initial-zero state/probability error but all-input unitary FAIL. No new state-equivalence engine invented. |
| C05 | PASS: H;Z vs H has same Z probabilities but distinct state; measurement PASS cannot become a unitary PASS. Independent matrix/probability oracle. |
| C06 | PASS: asymmetric X wire and reversed CX yield native FAIL even where zero input hides difference; reordered/unknown readout maps are refused. |
| C07 | UNSUPPORTED by contract: rx/ry/rz, arbitrary powers and symbols refused before assessment. A numerical rotation-perturbation comparison is NOT ASSESSED, rather than silently rounded. |
| C08 | PASS refusal controls: noise, reset, partial/mid/repeated measurement, dynamic/custom constructs explicitly non-PASS. No noisy semantics implemented. |
| C09 | PASS: source/native-assessment/result changes rejected; even consistently rehashed F1-valid altered graphs fail recomputing replay. F1 alone is not semantic replay. |
| C10 | PASS: width, 64/65 operation boundary, UTF-8 bytes, AST node/depth limits, malformed inputs/options, actual microsecond wall deadline. Worker RLIMIT_AS3GiB/CPU10s independently inspected. No peak-RSS benchmark or general sandbox claim. |
| C11 | PASS: import-blocked subprocess still exports/admit sources without Cirq; worker returns UNSUPPORTED + informative reason. Primitive records only; resource limits installed before SDK import. |
| C12 | PASS: historical native/external/not-assessed fixture byte hashes and native Bell graph ID retained; existing conformance regression suite included. |
| C13 | Bounded regression evidence: existing suite passes in installed environment, optional backends absent are not claimed independently live-tested. No changes to native/QCEC/PyZX/Stim code. |
| C14 | PARTIAL/deferred sampling: explicit `method.sampling_status=NOT_ASSESSED`, no counts/shots in observation; original seed/shots remain source metadata, not ideal simulation parameters. Finite-shot seed/count experiments not implemented. |
| C15 | PASS refusal: only final full ascending identity measurement key c; unknown/reordered/duplicate/partial/inverted maps refused, not normalized away. |

G0 completed/developer-confirmed; G1 local contract provided; G2 bounded Bell traverses path with native semantic assessment; G3 criteria/negative boundaries tested; G4 F1 content/reference validation plus recomputing local replay, **not** new SDK F2 conformance. G5 noise deferred; G6 mathematical bridge research deferred without kernel changes; G7 comparative runtime/memory/value study not performed. Public commercial/performance/scalability claims are not justified. Maintainer acceptance, publication/CI and external reproduction remain open.

## Inspectable example and reproducible commands

Source: `examples/e7q-ir/cirq/bell.e7q`, SHA256 `568724034835814e92d6ca7c26d079aa8e16ed924e5e1c095bebf2544ebec1a7`.
Result: `examples/e7q-ir/cirq/bell-result.json`, SHA256 `cc083415b15b943de503a8450462d50498ccc11f340bcefc4d14d05288c5bde1` (24065 bytes).
Graph ID: `sha256:e34ce3fd7599edb688a79ef96b7da037a46d0deceeeab2b8fd447c3273bd0d55`.
Adapter SHA256 `6106a63ad8c3bc1b3c2bc90bd6259bd010cba3d9e38000b5495fecd266f4264c`; independent test module SHA256 `a9819bb8f07a6f85b6088ab51985a25b37714b1f2cab6f6b13289f2e81ff896f`.

The preserved native invariant is source intent, not falsely labeled as evaluated by this adapter. The example's analytic probability assertion checks Bell correlations separately. The named native criterion assesses original/returned Program semantics. The original sources, admitted projection, method, matrix, diagnostics, native proof and limited claim are content-linked. Artifact timestamps are fixed identity sentinels, not authenticated chronology. Replay identity can differ on another environment/float implementation; a failed exact replay must be investigated rather than relabeling an old result.

From the candidate repository root:

```sh
python3.12 -m venv /tmp/e7q-cirq-review
/tmp/e7q-cirq-review/bin/python -m pip install -r docs/e7q-ir/cirq/requirements-tested.txt
/tmp/e7q-cirq-review/bin/python -m pip install --no-deps -e .
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
/tmp/e7q-cirq-review/bin/python -B -m pytest -q tests/test_cirq_interop.py
/tmp/e7q-cirq-review/bin/python -B -m pytest -q -ra
/tmp/e7q-cirq-review/bin/python -B scripts/check_licensing_boundary.py
git diff --check
/tmp/e7q-cirq-review/bin/python -B - <<'PY'
from pathlib import Path
import json
import numpy as np
from e7q.cirq_interop import evaluate_roundtrip, replay
from e7q.ir import validate_graph
p = Path('examples/e7q-ir/cirq')
s = (p/'bell.e7q').read_text()
r = evaluate_roundtrip(s)
assert r['status'] == 'PASS', r
assert validate_graph(r['graph'], level='F1')['status'] == 'PASS'
np.testing.assert_allclose(r['diagnostics']['zero_input_ideal_probabilities'],
                           [.5, 0, 0, .5], atol=1e-14, rtol=0)
assert replay(r, s)
stored = json.loads((p/'bell-result.json').read_text())
print('Fresh graph:', r['graph']['graph_id'])
print('Stored same-environment replay:', replay(stored, s))
# Do not overwrite or relabel historical stored evidence on environment drift.
PY
```

No UI or server is introduced. The JSON graph and source are inspectable repository evidence, not a deployed service or cloud-uploaded artifact. Rollback removes the optional adapter/extra/callers without changing existing core contracts; preserve new evidence rather than rewriting historic IDs.

## CI/reproducibility increment — new local verification, 2026-10-16

### Scope and exact source state

Actual HEAD remains `58d4e927869e0228b32ce7cd034bf06bb799dc48`, branch `feature/e7q-cirq-interoperability-20261016`, with the intentionally uncommitted candidate preserved. The initial dirty paths were BUILD_PLAN.md, REVIEW_CAMPAIGN.json, pyproject.toml, the Cirq documentation/example directories, adapter and focused tests. This task changes **only** `.github/workflows/ci.yml`, adds `scripts/check_cirq_ci.py` and `scripts/test_cirq_ci.py`, and updates this report plus `NEXT_AGENT_PROMPTS.md`. It changes no adapter behavior, exporter, criterion, schema, manifest entry, dependency pin, licensing/register file, kernel or historical example. The helper tests follow the existing `scripts/test_licensing_boundary.py` standard-library pattern and are also discovered by the complete pytest run; no new `tests/test_*.py` file bypasses campaign registration.

The separate core-matrix and simulation-reference job definitions are structurally unchanged. New `cirq-reference` uses ubuntu-latest/Python3.12 and a 15-minute job budget. It installs **both** the tested snapshot and editable `.[test,cirq]`, using the same snapshot as constraints; it checks imported/distribution Cirq1.6.1 and `pip check`. It runs licensing/negative controls, helper controls, the full focused module with JUnit XML, then the gate and real Bell check. No continue-on-error/skip-as-success path exists. Core dependencies still do not include Cirq.

The standard-library JUnit gate rejects skipped/xfail, failure/error tags and nonzero counters independently, empty/malformed reports, duplicate/missing/foreign identities, inconsistent counts, fewer than83 executed cases and absent named real-SDK Bell/composition/direction tests. Test exit0 alone is not accepted. The actual absent-SDK negative run below establishes this against real pytest output, not only synthetic reports. The minimum83 is intentionally tied to this frozen83-case corpus, **not a complete future collected-test identity manifest**: future corpus/selection changes require re-review of the gate, not blind reliance on the threshold.

### Fresh environments, versions and results

Created a **new** Linux x86_64 Python3.12.3 venv at `/tmp/e7q-cirq-ci-20261016-jmgPBP/venv`; the previous `/tmp/e7q-cirq-016-20261016` was not reused. Installed with resolver constraints and package extras, not `--no-deps`. Key versions: cirq-core1.6.1, NumPy2.5.4, pytest8.4.2, jsonschema4.26.0. All pinned transitive versions remain those in unchanged `requirements-tested.txt`; installation succeeded and dependency consistency passed. `freeze.txt` records the resolved set. An editable VCS line in pip freeze describes a dirty local checkout/base, **not a published reproducible candidate commit**. Snapshot versions are not artifact hashes or a signed supply-chain lock. Workflow pip bootstrap follows existing conventions and is not pinned by this dependency snapshot.

| Newly executed local check | Actual outcome |
|---|---|
| Installed Cirq module + distribution version / pip check | 1.6.1 / no broken requirements |
| `scripts/test_cirq_ci.py -v` | **10 passed**, including false-zero skip/error/failure counters, missing SDK names, partial/empty/malformed reports and actual CLI nonzero rejection |
| Existing licensing check / licensing negative controls | PASS declared boundary / **11 passed**; not rights certification |
| Focused SDK module + structured gate | **83 passed, 0 skipped, 22.76s**, required SDK cases present; gate PASS |
| Fresh Bell via real isolated worker | Native `tolerance` assessment PASS; separate F1 integrity PASS; analytic initial-zero probabilities PASS at atol1e-14/rtol0 |
| Bell replay/tamper | Actual fresh-worker recomputation with original source and **explicit** returned-source/criterion/tolerance/deadline PASS; altered native maximum_error=0.25 rejected |
| Review-campaign tests | **4 passed, 0.08s**; existing coverage requirements retained |
| Complete regression, 900-second harness budget | **1191 passed, 1 skipped, 115.21s**; only skip `tests/test_stabilizer_execution.py:11`, missing optional Stim |
| Separate new core-only venv (`core-only`) without Cirq | E7Q import works; focused pytest exits0 with **72 passed/11 skipped, 0.92s**; new CI gate exits1 with `focused suite has skipped`, as required |
| Workflow configuration | Existing PyYAML6.0.1 BaseLoader parses YAML; old jobs/triggers/permissions structurally equal; Bash syntax for new run steps and Python AST for inline pin assertion pass; helper checks validate gate wiring. No actionlint available/installed; not GitHub runner/schema validation |
| Local whitespace / custody | `git diff --check` PASS; original candidate bytes outside five owned paths, historical Bell and dirty Q-A3/Q-A4 worktrees are checked against pre-task custody |

The optional Stim skip remains allowed in the **full/core** suite; **none** is permitted in the dedicated focused Cirq gate. No skipped focused test is counted as SDK execution. The helper control expectations deliberately include failures; these are successful negative checks, not hidden verification failures. No product assertion was weakened or tests suppressed.

### Fresh Bell versus historical identity

Fresh evidence written **exclusively to** `/tmp/e7q-cirq-ci-20261016-jmgPBP/bell-fresh.json`, never the historical repository path. Fresh/old environment metadata both report Python3.12.3/NumPy2.5.4/Cirq1.6.1. Both graph IDs are `sha256:e34ce3fd7599edb688a79ef96b7da037a46d0deceeeab2b8fd447c3273bd0d55`; stored replay also succeeds. No environment-dependent identity mismatch occurred locally. Historical `bell-result.json` remains 24065 bytes, SHA256 `cc083415b15b943de503a8450462d50498ccc11f340bcefc4d14d05288c5bde1`.

Observed probabilities `[0.5000000000000001, 0, 0, 0.5000000000000001]` match the independent analytic `[0.5,0,0,0.5]` within the documented tolerance. The SDK observation, native all-basis criterion assessment and F1 content/reference integrity are checked **separately**, not promoted to SDK F2, provider authentication, hardware or physical fidelity. Fresh replay uses `returned_source=None`, `criterion="tolerance"`, `tolerance=1e-9`, `timeout_seconds=15.0`. Hosted Python3.12 patch/platform floats may differ: the helper reports both environments/graph IDs and historical replay, without making old-result equality a false universal portability gate. A mismatch must be inspected, not repaired by relabeling history. Fresh same-recipe replay and tamper refusal are mandatory everywhere.

### Commands actually reproduced

From this candidate root (commands abbreviated only by the declared variables):

```sh
RUN=/tmp/e7q-cirq-ci-20261016-jmgPBP
python3.12 -m venv "$RUN/venv"
PY="$RUN/venv/bin/python"
"$PY" -m pip install -r docs/e7q-ir/cirq/requirements-tested.txt \
  -c docs/e7q-ir/cirq/requirements-tested.txt -e '.[test,cirq]'
"$PY" -c 'import cirq; from importlib.metadata import version; assert cirq.__version__ == version("cirq-core") == "1.6.1"'
"$PY" -m pip check
"$PY" -m pip freeze > "$RUN/freeze.txt"
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
"$PY" -B scripts/test_cirq_ci.py -v
"$PY" -B scripts/check_licensing_boundary.py
"$PY" -B scripts/test_licensing_boundary.py
"$PY" -B -m pytest -q tests/test_cirq_interop.py --junitxml="$RUN/focused.xml"
"$PY" -B scripts/check_cirq_ci.py report "$RUN/focused.xml"
"$PY" -B scripts/check_cirq_ci.py bell "$RUN/bell-fresh.json"
"$PY" -B -m pytest -q tests/test_review_campaign.py
"$PY" -B -m pytest -q -ra --junitxml="$RUN/full.xml"
python3.12 -m venv "$RUN/core-only"
"$RUN/core-only/bin/python" -m pip install \
  -c docs/e7q-ir/cirq/requirements-tested.txt -e '.[test]'
"$RUN/core-only/bin/python" -c 'import importlib.util; assert importlib.util.find_spec("cirq") is None; import e7q'
"$RUN/core-only/bin/python" -B -m pytest -q tests/test_cirq_interop.py --junitxml="$RUN/core-focused.xml"
# This final negative control MUST exit1, although pytest immediately above exited0:
"$RUN/core-only/bin/python" -B scripts/check_cirq_ci.py report "$RUN/core-focused.xml"
git diff --check
```

A new run must choose a new temp directory/output file: Bell helper intentionally refuses to overwrite an existing output. Actual logs are under RUN: `install.log`, `freeze.txt`, `helper.log`, `licensing.log`, `licensing-controls.log`, `focused.log`, `focused.xml`, `focused-gate.json`, `bell-check.json`, `campaign.log`, `full.log`, `full.xml`, `core-install.log`, `core-focused.log`, `core-focused.xml`, `core-gate.log`, `workflow-validation.json`, `before.json`; final custody/diff manifest is `custody-after.json`. These are local scratch evidence, not repository inputs or uploaded artifacts. Runtime stdout records also exist in coordinator `.tunc/background-bash/d7e3a232-bd08-4796-a6d5-97b49c0e4786/` and `1e032fb1-d391-413a-9316-50270873e5ba/`.

### Remaining gates and exact publication status

A separate read-only AI review found no concrete blocking CI/Bell defect; it was static-only (reviewer verdict PARTIAL), not independently executed external reproduction. Main-worker runtime evidence above closes **local** verification only. Remaining risks: future corpus changes need matching gate review; version pins are not hash-locked; platform/patch floating differences may change historical identity; hosted package/index availability and actual GitHub runner behavior remain untested.

**Hosted CI: NOT RUN. External reproduction: NOT PERFORMED. No implementation commit/push/PR/merge/tag, publication, deployment, reviewer contact, relicensing or kernel changes.** Existing candidate remains uncommitted on its exact base; no remote operation was performed. Next approval needed: explicit owner grant for an exact-file/hash-bound commit/push/reviewable PR publication to E7GT-Ecosystem/E7Q, preserving rights/terms. Recheck target main/in-flight work only within that subsequent grant; do not reset dirty worktrees. After publication, obtain actual hosted Cirq-job evidence and separately authorized external reviewer reproduction at the exact published SHA; maintainer/security/scientific acceptance remain separate. Do not add F2/noise/rotations/sampling/hardware/general imports or a comparison engine to close a reporting gate. A same-fixture plain-Cirq comparison is merely a possible later proposal.
