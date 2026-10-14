# Q-A4 offline supplied-receipt binding

## Scope and verification boundary

This product-local, opt-in profile links a validated unique Q-A3 selection to exact supplied legacy bundle/result/receipt bytes. It does not execute, compile, authenticate or accept a physical run. The supplied receipt's internal consistency is necessary, not authenticated truth or proof that source compiles to the recorded OpenQASM. No objective truth, feasibility, hardware, provider or F2/F3 acceptance follows.

Profile: `e7q.ir.selected-legacy-receipt-binding/v0alpha1`. Supported workflow dialect: existing `e7q.ir.legacy-execution-receipt-workflow/v1`. Kernel architecture pin remains E7G-T v0.12.1-experimental/RGP2 `fc4cdf95c6434e653efbe017587aab60b4b2a86c`; no pin migration or shared-runtime extraction. Owner selected QA4-PACKAGE/2026-10-14/1, SHA256 `065d43e1c4434d9c50f6c9630d54f08ec17829898c4177288f23047c9c0f21df`, with eight versioned paths and five offline test suites.

**Local technical verification passed on October 14, 2026:** 311 focused offline tests and independent implementation/adversarial review. A separate unauthorized 450-byte worker-note write is preserved and disclosed below; this is not an unqualified procedural-compliance PASS. No publication, execution-acceptance or broader release decision follows.

## Public API and backing records

`e7q.ir.receipt_binding` provides `ReceiptBindingError` with fixed typed `.outcome`, request construction/validation, assessment and whole-result validation. Exports are additive through `e7q.ir`; pre-existing names remain unchanged.

```python
build_receipt_binding_request(
    *, realisation_request_id, realisation_result_id, context, inquiry,
    source_digest=None, receipt_graph_id=None,
    profile=PROFILE, kernel_commit=KERNEL_COMMIT, editions=None,
    max_graph_bytes=16 * 1024 * 1024, max_artifacts=64,
    max_relations=128, max_source_bytes=1024 * 1024,
)
validate_receipt_binding_request(request)
assess_receipt_binding(
    request, family, history, realisation_request, realisation_result,
    restriction=None, *, source_bytes=None, receipt_graph=None,
)
validate_receipt_binding_result(
    result, request, family, history, realisation_request, realisation_result,
    restriction=None, *, source_bytes=None, receipt_graph=None,
)
```

Request construction checks canonical shape, not truth of backing records. `editions=None` means a fresh expected edition map, not a mutable shared default. Assessment receives records directly. It resolves no digest through storage/network and accepts source as exact `bytes`, never a path/bytearray/callback. Finite plain built-in JSON records only; no custom mapping accessors or arbitrary iterators. Backing objects are not mutated.

Public upstream Q-A3 assessment/result validation establish the actual residual, history and rank. Public F1 graph validation, `recover_legacy_source` and `validate_legacy_receipt_evidence` establish supplied-carrier structure and consistency. No private parser/helper or semantic F2 engine is a cross-module API.

## Selected-member commitments

A unique selected member must contain these four bindings, precommitted before Q-A3 selection:

| Selected binding | Required exact equality |
|---|---|
| `qa4_source_digest` | SHA256 of separately supplied exact original source bytes, also equal to family's `source_id` and parsed bundle's `source_digest`. |
| `qa4_bundle_digest` | SHA256 of exact bundle bytes recovered from the graph, including all whitespace, field ordering, shots and other carrier fields. |
| `qa4_openqasm_digest` | SHA256 of UTF-8 bytes of the parsed bundle's exact OpenQASM string, without normalization. |
| `qa4_target` | Exact target string in validated bundle/result/receipt. No provider alias or calibration tie-break. |

Digest syntax is `sha256:` followed by 64 lowercase hexadecimal digits. Target must be nonempty and at most 128 UTF-8 bytes. Other valid member bindings remain intact and are not rescored/refactorised. Missing reserved keys or an otherwise well-formed unsupported representation is `unsupported`; malformed reserved values or contradictory commitments are `invalid_input`. These are opt-in Q-A4 requirements, not changes to the valid upstream family profile.

The whole-bundle commitment is deliberate: another independently valid bundle with the same program/target but changed shots or whitespace cannot satisfy an old raw commitment. Rebuilding all source/family/selection/receipt inputs as a different coherent claim is not a cryptographic forgery of the old claim. Digests do not authenticate either claim.

Original source bytes are not inserted into or substituted for a legacy carrier. Their digest agrees with the bundle declaration; this does not establish compilation correctness, source-program semantics or causal execution.

## Canonical records

Strict JSON Schema request/result/nested definitions are in `schemas/e7q-ir-receipt-binding-v0alpha1.schema.json`; executable validators additionally establish type-sensitive identity and cross-record equalities. Extra properties are rejected. Each new record uses existing `identified_digest(record, own_id_field)` excluding only its own identity field. This is named deterministic JSON, not a full RFC8785 claim. Array orders below are meaningful.

The request is exactly:

```text
schema, request_id, profile, kernel_commit, editions, context, inquiry,
realisation_request_id, realisation_result_id, source_digest,
receipt_graph_id, limits
```

`limits` contains exactly `max_graph_bytes`, `max_artifacts`, `max_relations`, `max_source_bytes`. Alternative bounded profile/kernel/edition strings are structurally admitted so executable assessment can report `unsupported` rather than misclassify malformed input. Expected editions are family `e7q.ir.candidate-family/v0alpha1`, history `e7q.ir.transformation-history/v0alpha1`, realisation `e7q.ir.realisation-result/v0alpha1`, and `RGP2@v0.12.1-experimental`. Corrected restriction schema remains separately `e7q.ir.candidate-restriction/v0alpha2`.

The result is exactly:

```text
schema, binding_id, outcome, request_id, realisation_request_id,
realisation_result_id, source_family_id, history_id, restriction_id,
input_residual_family_id, realisation_outcome, best_member_ids,
selected_member_id, source_digest, receipt_graph_id, evidence_digests,
layer_records, edge_records, witness, message
```

`outcome` is `bound|unbound|invalid_input|unsupported|resource_limit`, distinct from Q-A3's outcome and the supplied legacy receipt assessment. Evidence digests, when present, are exactly `{bundle,result,receipt}` of recovered raw bytes. Messages are fixed outcome-specific constants, with no paths, input echoes, exception text or secrets. Identity references are null until independently established.

| Binding outcome | Publication rule |
|---|---|
| `bound` | Valid unique Q-A3 result; exactly one best/selected member; all evidence checks; five layers, three edges and a witness. Means supplied consistency/byte linkage, not execution acceptance. |
| `unbound` | A supported replayed nonunique/terminal Q-A3 declaration; no selection, witness, receipt/source/evidence digests or layer/edge success. Full best inventory only for ambiguity. No receipt decoding. |
| `invalid_input` | Malformed/rehashed/contradictory backing or any non-PASS legacy evidence validation; no best/selection/witness/layers/edges/evidence. Retain established input IDs only. |
| `unsupported` | Independently admitted alternative profile/kernel/edition/dialect or unsupported member representation; no fabricated success/empty result. |
| `resource_limit` | Valid supported input exceeds its declared new-profile budget; no selection/witness. Not empty or acceptance. |

The witness binds actual Q-A3 witness/selection, original source, graph, all three raw carrier digests, OpenQASM digest, target and ordered layer/edge IDs. Whole-result validation independently repeats assessment and compares canonical contents, not just a rehashed result ID. Canonical comparison must distinguish Python's `True == 1` equality trap.

## Assessment precedence and resource admission

1. Guard request shapes/limits before canonical hashing; reject malformed exact-int declarations (`bool` is not int). Alternative well-formed profile/kernel/edition is unsupported before graph processing.
2. Validate Q-A3 request/context/inquiry and independently reconstruct the entire supplied Q-A3 result using public APIs. Invalid supplied result is not an upstream declaration. Preserve only input IDs actually established by that replay; a terminal declaration does not certify a failed restriction's lost cause.
3. Replayed nonunique/terminal Q-A3 requires request source/graph digests null and actual optional source/graph absent. Return unbound without receipt/source-profile work. Extraneous evidence in this branch is invalid input.
4. Unique requires bounded exact source bytes and a plain graph with matching request references and actual residual membership. Check reserved member commitments. Refuse unsupported representation rather than inventing source/target interpretation.
5. Structural F1 must pass. On an F1-valid graph, an admitted different dialect is unsupported. Recover exactly three role carriers through public recovery; malformed/duplicate roles, base64/digest mismatches or recovery failures are invalid input. Enforce actual recovered lengths **before** public evidence parsing/recomputation. Recovery itself performs bounded decoding allocation: a smaller declared limit does not avoid all allocation.
6. Only after length admission call `validate_legacy_receipt_evidence`. Every non-PASS/malformed report, including FAIL/BLOCKED/NOT_ASSESSED, maps to Q-A4 invalid_input. A success report has exactly `status`, `reason`, `checks`; reason is a nonempty string and checks is a nonempty plain list of exactly `{name,passed,message}` records with nonempty string names/messages and literal `passed=True`. PASS with a failed check is invalid input too. This legacy report shape is separate from the public F1 report shape; required check names are not hardcoded. Unsupported is not inferred from ambiguous reason strings. Existing legacy outcome semantics are unchanged. After PASS, standard JSON decoding only reads already strictly validated fields; compare every raw/representation/target commitment and construct the bound result. The bundle's declared `openqasm_digest` must also equal the digest of its exact parsed OpenQASM: a contradictory declaration is invalid input, not a compiler-equivalence assessment.

Profile maxima/defaults: canonical graph 16 MiB, 64 artifacts, 128 relations, 1,048,576 bytes per original source and per recovered carrier. Smaller positive exact-int declarations are supported; above-profile/zero/negative/bool declarations are invalid input. Existing legacy maximum is independently enforced. Context/inquiry max 1024 UTF-8 bytes; profile/kernel/edition labels and selected target max 128 UTF-8 bytes.

Before graph serialization, iterative admission rejects custom objects/cycles, depth >64, more than 200,000 visited values, non-finite numeric values and lone surrogates. Reject an individual string longer than the graph-byte budget in code points before encoding; accumulate exact UTF-8 key/value text bytes and short-circuit over-budget. Exact graph integers have absolute value <=2**127 before decimal conversion. Only then compute canonical graph bytes and enforce the complete byte ceiling. These are declared limits on Q-A4 graph inputs, not new string/aggregate limits on upstream family/history backing.

No universal RSS, allocation, timeout, process or recursive-capacity containment is claimed. Schema maxLength/integer semantics cannot by themselves enforce UTF-8 bytes or exact Python ints; executable validation is required.

## Explicit partial RGP2 mapping

Pinned §X.18 R.1 defines `L=<Sigma,B,G,I,A,E,D,Pi,K,M>` and independent `place=<r,rho,tau,alpha,c>`. The adapter exposes all ten fields plus place; it never substitutes a five-field shorthand or spatial/circuit-depth coordinate.

Five ordered layer roles: source-family, ordered-history, residual-family, realisation, supplied-receipt. Sigma/I explicitly identify the primary record schema, product-local adapter operations and offline/no-execution boundary. B binds complete correlated record IDs. G declares supported metadata rules only. K is partial: canonical/receipt consistency checks are recomputed, while semantic preservation and execution authentication are not assessed. M declares the unchanged kernel pin, adapter edition, role and source IDs. A/E/D/Pi and every place coordinate are explicit `{status:"unknown",value:null}`, not passed checks, open access or lossless-retention claims.

Three ordered edges:

- source-family → residual-family: `generates-metadata`, `qa4.restrict-metadata/1`, exact history/step/restriction and retained-member parameters;
- residual-family → realisation: `generates-metadata`, `qa4.rank-metadata/1`, exact Q-A3 request/result/witness parameters;
- realisation → supplied-receipt: `references-evidence`, `qa4.link-supplied-bytes/1`, checked member/source/graph/raw/representation/target parameters.

Every component has an explicit reconstruction or unresolved disposition. Unknown fields/coordinates are not silently inherited. The evidence-reference edge is **not kernel Generates or causal execution**. Metadata generation describes reconstruction of immutable wrappers, not generation of a physical observation. These are product-local nested records, not new `graph.RELATION_KINDS`.

This is a partial experimental RGP2-inspired adapter, not full RGP conformance, SR1–SR4, registered source-retention tier, generic shared-runtime API or recursive-capacity acceptance. Upstream Q-A1/Q-A2/Q-A3 IDs and historical declarations remain unchanged.

## Focused offline verification

From the approved isolated checkout, after verifying the existing interpreter/dependencies and planning import origins:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
PYTHONPATH="$PWD/src" /tmp/e7q-resource-20261013-venv/bin/python -B -m pytest \
-p no:cacheprovider -q tests/test_ir_receipt_binding.py \
tests/test_ir_candidate_family.py tests/test_ir_transformation_history.py \
tests/test_ir_realisation.py tests/test_review_campaign.py
```

The interpreter path is the reviewed local environment, not a portable setup guarantee. No installation is authorized. Only these five explicit suites are selected, not the full suite, simulation benchmark, existing compiling/F2/CLI legacy suite or provider/native execution. New inert carriers may be written only into test-owned temporary files to call the existing path-based `build_legacy_receipt_graph`; assessment itself stays in-memory. No new byte-argument mapper is assumed.

Required checks cover exact successful linkage and whole-result/schema replay; correlated/partial/retain-all membership; ambiguity/empty/failure and zero evidence access; forged/rehashed/foreign/excluded winners; wrong source/target/whole-bundle/OpenQASM/graph/role refs; raw PASS and mixed legacy refusals; ten components/five independent unknown coordinates and edge/rule order; inclusive/smaller budgets and admission precedence; UTF-8/finite-number/type/cycle/resource refusals; nonmutation; unchanged prior assertions/campaign entries and negative remove/duplicate campaign-entry probes.

### Local verification record

The exact five-suite command above completed with **311 passed in 23.07s**, exit 0: 223 new Q-A4 cases and 88 unchanged planning/campaign cases. The test author independently wrote the new suite against the approved package without reading the implementation; its initial 195-case run passed in 20.00s before the final adversarial additions. No failing product-test run was observed in this slice.

Independent read-only verifier `65279fc0-34f8-455f-923c-e74cc638eaa9` returned **technical PASS, no open implementation/schema findings**. Its own unchanged planning/campaign selection passed 87 cases with the temporary-writing fingerprint case deliberately deselected (1 deselected, 1.58s). The parent five-suite run included that case. Independent in-memory public-fixture probes established F1/evidence PASS (15 legacy checks), exact three-carrier recovery, bound replay/schema/nonmutation, six unbound terminal/tie outcomes without evidence access, all-role pre-evidence byte limits, exact F1 → recovery → evidence → JSON order, finite/type/depth/node/cycle admission and 133 nested extra-property schema refusals. Both unrehashed Python-equal bool/int and rehashed wrapper attacks were refused. Semantically equal reserialized bundle bytes remained legacy-PASS but failed the old Q-A4 raw commitment. Original fixture bytes were preserved.

Parent and reviewer independently exercised the unchanged campaign coverage assertion against removed and duplicated new entries; both were rejected. Existing imports/exports were checked additive, core relation kinds and prior sources/tests unchanged. Exactly eight checkout paths differ from merge `c519484bccdbe411b05acdba9c24ef1cd852d041`; original BUILD_PLAN/alignment bytes remain prefixes, and all 52 prior campaign entries/order/top-level data remain intact. Six other checkout inventories (277+273+262+160+457+436 tracked/untracked files plus HEAD/branch/index/status) matched their prework aggregate SHA pins. Coordination README/MASTER_PLAN, Q-A3/Q-A4 packages and prior custody receipt also matched their pins. No caches, bytecode, staged changes or commits were produced in the product checkout.

Preserved corrections/recoveries: the reviewer saw a transitional report-shape patch whose call site had not yet enabled the legacy-specific guard. Final `validate_legacy_receipt_evidence` admission uses `legacy=True`, independently rechecked; F1 retains its distinct report format. The final suite includes otherwise plausible malformed-PASS reports, literal-bool checks and a no-rehash Python-equality trap. **tool-error recovery verified**: initial Git help exit 129 occurred before checkout mutation and was followed by verified clean checkout/base/origin; schema constant-folding inspection recovered from multiplication unsupported by literal_eval; missing shell ripgrep and a mistyped patch anchor were recovered through dedicated reads/correct exact matching; reviewer fixture-field and optional pilot-reference probe mistakes were corrected and rerun successfully. These inspection failures are not erased or presented as product-test passes. Prior paper-review failures remain in the unchanged approved coordination package.

**Procedural exception, not repaired by passing tests:** module worker `ea5a5d5f-d2d6-4ce6-b89e-edd31d62ea72` accidentally used `agent_write_output` contrary to its no-output-artifact instruction, producing the local coordinator-root file `.tunc/agent-outputs/ea5a5d5f-d2d6-4ce6-b89e-edd31d62ea72/final-call-verification.txt` (450 bytes; SHA256 `02205c5112d40660dd6a3fa4572e427ae171675dc2e882bc9e4afaf72830bf16`). The parent inspected it, preserved it without deletion/upload, and disclosed the exception to the operator/reviewer. It is outside the product checkout and does not add a ninth versioned product path. Technical PASS must not be relabelled as perfect authorization compliance; disposition of that note remains with the owner.

Work is local/uncommitted on `feat/qa4-supplied-receipt-binding-20261014`. No installation, compiler/simulator/native/F2/provider/hardware execution, CLI/subprocess test, commit, push, PR, remote CI, upload or deployment was performed for this increment. Evidence-only/internal-consistency and partial-RGP nonclaims remain in force. Publication, broader execution/domain acceptance, CSR-01–04 and shared-runtime/release gates remain separate.

## Open-core alignment after PR #87 — October 14, 2026

The preceding eight-file/base/branch/test record is the original historical checkpoint, preserved in full. PR #87 merged a licensing boundary, not Q-A4, at `8193a2818c849bc20caf5ff1c20f2e0b2ce49e20`. The owner subsequently selected **Retain open-core terms**, including the ninth licensing-register path and local alignment/checks, then separately selected **Approve the fixture fix**, adding `scripts/test_licensing_boundary.py` as the tenth path. Neither selection authorizes a commit, push, public PR, merge or deployment.

Alignment is local on `feat/qa4-open-core-alignment-20261014`, based exactly on that PR #87 merge. The original `e7q-qa4-20261014` checkout is untouched. `receipt_binding.py`, its schema and independent test suite remain byte-identical to the original verified files. The sole export-module change is an Apache-2.0 SPDX comment; executable AST and public exports are unchanged. No kernel/profile/schema ID or evidence semantics changed.

`docs/licensing/component-register.json` contains exactly three new `retain_public_terms` decisions, each bound to the actual local file SHA256 and the owner's explicit selection. All other policy fields, the baseline inventory, public licence texts, commercial terms/empty commercial register, packaging and the checker implementation remain unchanged. This records the selected existing public terms; it does not authenticate ownership, certify rights clearance, infer commercial agreements or authorize publication. Any future protected-file byte change requires a corresponding refreshed approval record under the policy.

| Approved protected file | Exact SHA256 |
|---|---|
| `src/e7q/ir/receipt_binding.py` | `4298d1bd4abb8e92d1d08b6a6a6350cb32eb70be49c1adc40643e5d47a356434` |
| `src/e7q/ir/__init__.py` | `c1b996f18abe3ffee30db94da2c9086abb9006d0e35c77325a86ab4539433bce` |
| `schemas/e7q-ir-receipt-binding-v0alpha1.schema.json` | `70ac8412d25fd5c8c5db75596c69f47d5d5bb4488752529fdff38e1172c1f377` |

### Observed alignment failures and repair

The first licensing check failed because the modified export module lacked an explicit Apache designation. Adding the SPDX comment and refreshing that file's hash-bound record corrected the failure; no execution behavior was changed. The checker then passed, but **3 of the original 10 licensing controls failed**: their baseline-only temporary fixture omitted the newly registered adapter/schema and therefore reported decisions outside its supplied path inventory. This was a fixture defect, not an authorization bypass or a reason to weaken the checker. The actual failed run remains part of the history.

After the owner's separate tenth-path approval, the fixture now copies both published baseline files and registered open-core files, deduplicates paths and rejects absolute/parent-traversal paths. All ten original test-method bodies/assertions remain identical by AST comparison. One new regression copies a synthetic approved addition not in the baseline, confirms the copied bytes/hash pass, then changes those bytes and confirms stale approval is rejected. The production checker and all its refusal rules remain unchanged.

### Verification on the aligned base

From this aligned checkout, using the already installed interpreter and no bytecode/cache:

```sh
PYTHONDONTWRITEBYTECODE=1 /tmp/e7q-resource-20261013-venv/bin/python -B scripts/check_licensing_boundary.py
PYTHONDONTWRITEBYTECODE=1 /tmp/e7q-resource-20261013-venv/bin/python -B scripts/test_licensing_boundary.py
```

Observed results: **licensing boundary PASS** (declared scope only, not rights certification); **11 licensing controls passed in 4.336s**; the same exact five offline suites documented above completed with **311 passed in 22.92s**, exit 0, on base `8193a2818c849bc20caf5ff1c20f2e0b2ce49e20`. These are new-base results, distinct from the preserved original-base 23.07s run. No full suite, package build, compiler/simulator/native/provider/hardware/F2 execution or remote CI was run.

Independent read-only alignment verifier `a5f17d9c-d19c-4391-b518-3e2b48f79aef` returned **technical PASS, no actionable findings**. It independently verified the unchanged checker and all ten original control bodies by AST, three exact owner-referenced register additions, the actual licensing check, fifteen in-memory missing/stale/blank-approval/wrong-decision/null-hash attacks across the three protected files, three invalid fixture paths, and original-byte/notice-only/scope/campaign preservation. A controlled no-write reproduction yielded exactly the two omitted-file errors under the old fixture inventory and no errors under the repaired inventory. The verifier corrected an initial probe assumption that the new campaign entry was last; exclusion-by-ID confirmed preserved original order. This recovered inspection error is not a product-test failure. No review files or scratch artifacts were written.

The prior 450-byte unauthorized worker-note exception remains preserved and disclosed; it has not been deleted, uploaded or retrospectively authorized. **tool-error recovery verified:** the missing workspace-root AGENTS read was read-only and recovered by reading the actual product instructions; checkout/base/hash and post-repair tests confirm the recovered state. Current work remains local/uncommitted and exactly ten product paths; publication and broader execution/domain/release gates still require separate approval.
