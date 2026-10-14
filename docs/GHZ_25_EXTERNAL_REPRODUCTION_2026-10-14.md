# GHZ-25: externally reported reproduction

**Recorded:** 2026-10-14. **Evidence class:** externally reported reproduction,
narrative only. **Source:** a tester account supplied by the operator; tester
identity, original execution date and custody are not supplied. Project author
attribution remains **Oleksandr Razinkov**.

This report records the supplied account, not an authenticated execution receipt.
No tester logs, commands, circuit bytes or execution artifacts were received.
Missing fields below remain unknown; current repository files and new local runs
are not substitutes for them. The resource-aware/Clifford implementation was
already merged through PR #83; this update does not reimplement it.

## 1. Supplied observations and their scope

Every observation in this table is **reported by the tester**, not newly
reproduced here as an external CLI experiment.

| Reported observation | Evidence scope / limitation |
|---|---|
| A fresh checkout produced **659 passing tests and one skipped test**. | The tester did not investigate the skip. Checkout SHA, dependency inventory, selection and raw pytest output were not supplied. |
| Package version remained **`1.0.0rc12`**. | A version string is not a source-commit pin or complete environment identity. |
| Plain GHZ-25 CLI `verify` took **approximately 0.23 seconds**, including Python startup, in the tester's sandbox. | **No Pauli checks** were included in this timed call. Exact command, shots, timing method and sandbox details are unknown. Any other requested invariants were not specified. |
| Separate exact premeasurement checks passed for **all 24 neighboring ZZ=+1** expectations and **X⊗25=+1**. | These supported simulator-property checks were **untimed**. They are not a claim of exact verification in 0.23 seconds. |
| **Z₀=0** passed. | One balanced marginal was assessed; the tester did **not** check all 25 marginals. |
| On the GHZ+ preparation, requests **X⊗25=-1** and **Z₀=+1** failed with **exit code 1**. | These are incompatible-expectation rejection controls on the original preparation, not independently prepared GHZ− or incoherent-mixture controls. |
| A **T gate** returned **UNSUPPORTED / NOT_ASSESSED**, without implicit dense fallback. | Reported capability refusal, not a failed supported quantum property. Exact source and raw result were not supplied. |
| A **dense GHZ-25** request was refused **before allocation**, with **exit code 3** and verification unassessed. | Reported resource refusal. Requested/effective budget and measured memory were not supplied; this is not an OOM experiment or a minimum-hardware measurement. |
| The tester found repository tests for opposite-phase GHZ and a small incoherent mixture, including a Qiskit density-matrix reference. | Identification of repository coverage is not separate external reproduction of those CLI controls. |

The reported exact ZZ correlations and X⊗25 coherence check concern the admitted
premeasurement simulator state. The Z₀ check adds one marginal observation within
that model. Neither Z correlations alone nor a plain CLI call establishes GHZ
coherence; this account does not claim a full marginal inventory.

### Alternative-state controls are a different obligation

Rejecting X⊗25=-1 or Z₀=+1 **on GHZ+** checks consistency against incompatible
expectations. It does not test GHZ− or a mixture against the original GHZ+
criteria. Opposite-relative-phase GHZ should retain ZZ=+1 and change X⊗25 to -1;
an equal incoherent zero/one mixture should retain ZZ=+1 but have X⊗25=0.
Those are distinctions exercised by the repository's scoped developer tests,
not externally reproduced alternative-state CLI results in this supplied account.

## 2. Provenance gaps — not inferred

| Field | External account |
|---|---|
| Checkout/commit SHA and dirty state | Not supplied |
| Exact install, pytest and CLI commands, flags and test selection | Not supplied |
| Original circuit bytes/hash, preparation details and bit mapping | Not supplied beyond the GHZ-25/GHZ+ description |
| Shots and seed | Not supplied |
| Python/OS/CPU/container configuration and hardware limits | Not supplied; only a sandbox was described |
| Dependency versions, including Stim, Qiskit, NumPy and pytest | Not supplied |
| Timing method/repetitions and checked-run duration | Not supplied; checked run was not timed |
| Requested/effective memory budget, estimates and measured peak RSS | Not supplied |
| Raw stdout/stderr, exit-status records, result JSON, skip reason and custody | Not supplied; exit codes above are narrative observations |

No source SHA, default shot count, dependency version or budget is backfilled
from current main. No reconstructed command or synthetic log is labeled as a
tester artifact. The external environment cannot presently be reconstructed.

## 3. Relationship to developer evidence and implementation

Keep this narrative separate from the developer's preserved
[baseline](../benchmarks/execution/baseline-20261013-v1.json) and
[resource/Clifford benchmark](../benchmarks/execution/resource-clifford-20261013-v1.json)
artifacts and [execution contract](RESOURCE_EXECUTION.md). Those artifacts have
their own pinned code, commands, environment, 1024-shot GHZ-25 measurements and
50-check scope; their fields do not fill the gaps in this external account.

Clifford simulation is provided by **Stim**. E7Q contributes explicit execution
integration/backend selection, declared verification criteria, resource preflight,
capability refusal and evidence reporting. This report claims neither a new
simulation algorithm nor comprehensive correctness, arbitrary-width scaling,
hardware fidelity/validation, fault tolerance or computational advantage.

A declared working-memory estimate, actual measured peak RSS and minimum usable
hardware are different quantities. The tester supplied no memory measurement.
The developer's resource estimate/RSS and configured budgets are not the tester's
measurements or a universal minimum-hardware requirement. Preflight is not a
guarantee against every interruption; refusal is not completed execution.

## 4. Test-count and skipped-test investigation

The external **659 passed / 1 skipped** remains supplied narrative. The developer's
**672 passed** is separately recorded at implementation/harness commit
`e6f26e81a7a0313e429a58596d852eef74468877`, with simulation-reference/schema extras.
Equal package versions do not make these environments identical.

At the documentation branch's starting main
`3f5ecb03c3596f667271b1f705cffe354023d0b4`:

- [Test extras](../pyproject.toml) distinguish `test` (pytest) from `stabilizer`
  (Stim) and `simulation-test` (Stim, Qiskit and jsonschema).
- [CI](../.github/workflows/ci.yml) has core-only `.[test]` jobs and a distinct
  `.[test,simulation-test]` job.
- [Optional simulator tests](../tests/test_stabilizer_execution.py) use
  module-level `pytest.importorskip("stim")`, then `importorskip("qiskit")`.
  Missing either dependency can skip the **whole module**, reported as one skip,
  rather than one omitted test case. The schema test also has a separate
  function-level `importorskip("jsonschema")`.
- PR #84 was open when inspected and proposes adding `jsonschema>=4` to `test`.
  It does not add Stim or Qiskit to that extra. This may matter to schema-test
  selection but must not be assumed to explain the tester's skip. Its Q-A3
  implementation is outside this evidence branch.

### Our configuration-only validation — separate from the external test

On **2026-10-14**, before documentation edits, a fresh isolated environment on
exact source commit `3f5ecb03c3596f667271b1f705cffe354023d0b4` used Linux x86_64
(`Linux-7.0.0-38-generic-x86_64-with-glibc2.39`), Python **3.12.3**, E7Q
**1.0.0rc12**, NumPy **2.5.4**, pytest **9.1.1**; Stim, Qiskit and jsonschema were
**not installed**. Import provenance was checked against this checkout.

Commands from repository root, using that environment's `python`:

```bash
python3 -m venv /tmp/e7q-ghz-evidence-core-20261014
/tmp/e7q-ghz-evidence-core-20261014/bin/pip install -e '.[test]'
/tmp/e7q-ghz-evidence-core-20261014/bin/python -m pytest --collect-only -q -rs
/tmp/e7q-ghz-evidence-core-20261014/bin/python -m pytest -q -rs
```

Observed locally: **659 tests collected**; execution **659 passed, 1 skipped in
56.85 s**, exit 0. The local skip reason was missing **Stim** at
`tests/test_stabilizer_execution.py:11`. This is an actual controlled local run,
not a substitute tester log. It establishes one way to obtain that summary,
**not the cause of the tester's result**. In particular, this core-only environment
could not execute the reported Stim-backed CLI checks; test and CLI environments
must not be assumed identical.

Additional **collection-only** observations on the same source commit, in the
same isolated environment after sequential optional-extra installations:

```bash
/tmp/e7q-ghz-evidence-core-20261014/bin/pip install -e '.[test,stabilizer]'
/tmp/e7q-ghz-evidence-core-20261014/bin/python -m pytest --collect-only -q -rs
/tmp/e7q-ghz-evidence-core-20261014/bin/pip install -e '.[test,simulation-test]'
/tmp/e7q-ghz-evidence-core-20261014/bin/python -m pytest --collect-only -q -rs
/tmp/e7q-ghz-evidence-core-20261014/bin/python -m pytest --collect-only -q tests/test_stabilizer_execution.py
```

| Local configuration | Observed collection result (not a test execution result) |
|---|---|
| Core + Stim **1.16.0**, Qiskit/jsonschema absent | **659 collected**, one module skip for missing **Qiskit** at line 12 |
| Simulation-reference extras: Stim **1.16.0**, Qiskit **2.5.2**, jsonschema **4.26.0** | **672 collected**, no skip; optional simulator module contributes **13 collected cases** |

Python 3.12.3, E7Q 1.0.0rc12, NumPy 2.5.4 and pytest 9.1.1 were unchanged across
these local configurations. The arithmetic **659 + 13 = 672** demonstrates a
configuration-dependent selection mechanism. A module skip can hide all 13
cases even when Stim is installed and a CLI execution could use it. This does
not identify which dependencies, interpreter or test selection the tester used.
The 672-case collection is **not a fresh claim of 672 passing tests**. No new GHZ
CLI timing or external alternative-state experiment was performed here.

Adding jsonschema alone does not remove the Stim/Qiskit module guards. If both
optional simulators were installed but jsonschema were absent, the separate
schema test could instead skip; that mechanism alone does not establish the
reported 13-case difference. PR #84's dependency change is relevant context,
not an inferred explanation and not adopted in this documentation branch.

The tester's source, selection and installed packages remain unknown. Obtain the
original `pytest -rs` output and environment inventory before declaring the
external discrepancy resolved. Configuration evidence can explain a matching
count without authenticating the tester's environment or comprehensive coverage.

## 5. Evidence roadmap and proposed follow-up

**Checkpoint:** independent GHZ-25 reproduction is **reported** within the narrow
scope in section 1, not received as a full-provenance/raw-artifact reproduction.
Remaining work:

- [ ] Capture checkout SHA/dirty state, original source/hash, commands, shots/seed,
  environment/dependency inventory, budgets, raw results and skip reason.
- [ ] Time the **checked** run separately, with exact criterion inventory, startup
  boundary, repetitions and separately measured resource use.
- [ ] Prepare actual opposite-phase and incoherent-mixture controls and assess
  the original GHZ+ criteria; preserve unsupported/refused outcomes and the
  distinction between pure-tableau and mixed-state reference paths.
- [ ] Progressively test larger widths under declared budgets, recording exact
  checks, finite-shot observations, latency/RSS, refusals and missing completion.
  GHZ-25 alone is not an arbitrary-width scalability claim.
- [ ] **Proposed, not implemented:** a focused Clifford QEC demonstrator linking
  declared preparation, syndrome extraction, admitted injected Pauli errors,
  measurement/feed-forward and logical-property checks to compact evidence.
  Start from an explicitly bounded code/error model and an independent oracle;
  include negative/unsupported controls. This is execution evidence follow-up to
  the existing [syndrome-homomorphism pilot](QEC_SYNDROME_PILOT.md), not a new theorem,
  decoder benchmark, noise-model capability, threshold or hardware claim.

This documentation PR does not implement QEC, duplicate/modify/merge Q-A3 PR #84,
change author attribution, migrate kernel pins or claim full E7G-T v0.15
conformance. Existing native F2 and exact-equivalence boundaries remain unchanged.
