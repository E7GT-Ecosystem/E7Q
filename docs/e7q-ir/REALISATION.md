# Q-A3 finite residual-family realisation

## Scope

This opt-in **product-local planning profile** adds canonical requests, lexicographic selection, explicit tied-best inventories and independently recomputable membership/ranking witnesses. It does not execute a circuit, authenticate objective values, infer semantic preservation, assess hardware, or integrate a native receipt. Q-A4 receipt binding and shared-runtime extraction remain separate gates.

Profile: `e7q.ir.finite-integer-lexicographic/v0alpha1`. Tie policy: `retain_all_best`. Named deterministic JSON and existing `sha256:` identity helpers are reused; full RFC 8785 conformance is not claimed. Existing Q-A1/Q-A2 identities and contracts are unchanged.

## Public API

The additive API is in `e7q.ir.realisation` and exported through `e7q.ir`:

- `build_realisation_request(...)`: builds a bounded canonical request and objective table. It raises `RealisationError` for malformed input or exceeded construction limits; `.outcome` distinguishes the refusal.
- `validate_realisation_request(request)`: reconstructs identities and exact canonical contents.
- `assess_realisation(request, family, history, restriction=None)`: returns a typed canonical result. All backing records are supplied directly; IDs are never resolved through storage/network.
- `validate_realisation_result(result, request, family, history, restriction=None)`: independently recomputes the assessment, not merely its digest.

Only plain finite JSON-compatible inputs are admitted. No custom mappings, getters, callbacks, arbitrary iterators, evaluation functions or solver are part of this profile. Inputs are not mutated. Bounds are software validation, not universal memory/time containment.

## Request and objective table

Request fields are `schema`, `request_id`, `profile`, `tie_policy`, `context`, `inquiry`, `source_family_id`, `history_id`, nullable `restriction_id`, nullable `input_residual_family_id`, `objectives`, `objective_table` and `limits`.

An objective is exactly `{id, edition, direction, unit}`. IDs use the existing ASCII name form. Direction is `min` or `max`. Edition/unit are non-empty UTF-8 labels, not conversion functions. The ordered objective list is meaningful: reversing it changes request identity and can change the winner. There is no universal preference order or hidden calibration/name/digest tie-break.

A table is `{schema, rows, table_id}`. Each row is `{member_id, values}`; each value is `{objective_id, value, evidence_ref}`. Rows canonicalise by member ID; values follow declared objective order. Successful residuals require exactly one complete row per retained member and one value per objective. Evidence references are supplied provenance declarations, not signatures, truth, measurements or receipt acceptance.

Supported values are exact Python `int` objects, not booleans, integral floats, decimal strings, fractions or amplitudes. The inclusive signed interval is **−2^127 to 2^127−1**. Adjacent exact integers are a resource refusal; wrong numeric types and non-finite values are invalid input. Check integers before canonical serialization.

Limits:

| Item | Bound |
|---|---|
| Retained candidates | 4096, or a smaller positive declared limit |
| Ordered objectives | 1–16, or a smaller positive declared maximum |
| Declared limit types | Exact integer, not bool; no zero, negative or above-profile declaration |
| Objective ID/edition/unit | At most 128 UTF-8 bytes |
| Profile/tie-policy labels | At most 128 UTF-8 bytes |
| Context/inquiry | Non-empty, at most 1024 UTF-8 bytes |

Source-family Q-A1 limits remain independent. A valid actual demand exceeding a valid declared limit is `resource_limit`, not `empty`. Malformed limit declarations are `invalid_input`.

## Residual and history validation

The first slice supports one canonical Q-A2 **restriction step**, with matching context/inquiry and backing Q-A1 source family. Multiple-step or non-restriction histories are unsupported before any terminal-declaration propagation.

For upstream `success` or `empty`, supply the complete corrected Q-A1 v0alpha2 restriction record. The assessor replays its retained-member/criterion inputs using the public restriction assessment helper and compares the entire canonical record. It checks source, rule/edition, admitted/excluded domain, outcome, output family and history residual linkage. A hash-shaped or rehashed subset is not membership evidence. Partial and retain-all residuals use the actual reference-subset identity; correlated source bindings are never refactorised.

A valid retain-none record remains `empty`, with no residual, best members, selected member or witness. Its objective table must have zero rows.

Failed Q-A1 restriction records can discard their original retained inputs or criterion. Their published empty inventory **must not be replayed as if it reproduced the original failure**. This slice excludes failed restriction objects from its request backing shape. For a canonical supported Q-A2 terminal `invalid_input`, `domain_error`, `unsupported` or `resource_limit`, pass `restriction=None`, null restriction/residual IDs and zero table rows. The result preserves the linked **declared terminal outcome**, without reconstructing its cause, certifying inventory or producing membership/selection. No objectives are scored on empty or failure branches.

## Outcomes and witness

| Outcome | Best inventory / selected member / witness |
|---|---|
| `unique` | Exactly one best member; selected ID is that member; recomputable witness |
| `ambiguous` | Every equally best member; no selected ID; recomputable witness |
| `empty` | No best member, selection, residual or witness |
| `invalid_input` | No selection or witness; only independently established bindings retained |
| `domain_error` | Preserved supported upstream declaration, not a new domain evaluation |
| `unsupported` | No selection/witness or implicit fallback |
| `resource_limit` | No selection/witness, never manufactured empty/acceptance |

Result fields are `schema`, `result_id`, `outcome`, nullable `request_id`, `source_family_id`, `history_id`, `restriction_id`, `input_residual_family_id`, `best_member_ids`, `selected_member_id`, `witness`, `upstream_outcome` and bounded fixed `message`.

A ranking witness binds `input_residual_family_id`, `objective_table_id`, the best ordered value vector and the full best-member inventory, with its own schema/identity. Input residual and best/tied subset are distinct. The result validator resolves selected/best IDs against backing members and recomputes ranking; changing a winner and recomputing hashes is insufficient to pass.

The supplied values determine a preference, not factual validity, physical feasibility, preservation or quantum advantage. Sorting member IDs merely canonicalises tied output inventory; it must never turn ambiguity into a unique winner.

## Schema versus executable acceptance

`schemas/e7q-ir-realisation-v0alpha1.schema.json` contains request/result definitions and strict outcome-specific shapes. JSON Schema does not establish identity, actual membership, full row coverage, UTF-8 byte limits or exact Python integer typing. For example, its mathematical integer semantics can accept `1.0`; executable validation rejects that value. Both layers are required.

## Focused verification

From the isolated reviewed checkout, using the verified existing interpreter and that checkout's source root:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
PYTHONPATH="$PWD/src" /tmp/e7q-resource-20261013-venv/bin/python -B -m pytest \
-p no:cacheprovider -q tests/test_ir_realisation.py \
tests/test_ir_candidate_family.py tests/test_ir_transformation_history.py
```

The interpreter path is the reviewed local environment, not a portable installation guarantee. Verify imports resolve to the intended checkout before running; if dependencies/setup are missing, seek separate permission rather than installing.

Tests cover canonical replay, min/max and objective order, ties, non-mutation, correlated residuals, actual schema fixtures, retain-all/none, terminal declarations, forged/foreign/excluded selections despite rehashing, wrong backing/linkage, malformed rows/types, numeric/UTF-8/declared-budget boundaries and unsupported profiles/history. No simulator, native receipt, provider, hardware or benchmark call is part of this focused suite.

## Local verification result — 2026-10-14

The permitted three-suite planning check passed **84 tests**: 55 realisation cases and 29 retained Q-A1/Q-A2 cases. Independent verifier `a49c946a-6b1a-4d52-a805-78be7d383016` repeated the suite (**84 passed in 1.24 s**) and independently checked 135 malformed backing variations, rehashed forgeries, numeric admission, cycles/custom dictionaries, non-mutation and actual schema fixtures.

Initial verifier **FAIL** concerned undeclared backing-data string/aggregate ceilings on module SHA256 `d8190324fa2d43e5bc14329b5ddc505cd447eef615bc29a32dea44b594081dd7`. The correction removed those backing-only limits without changing the selected profile or Q-A1/Q-A2 bounds. Added regressions accept source-valid 16,385-character ASCII and Unicode inert bindings; requests/results remain schema-valid and independently recomputable. The same verifier returned **PASS** at corrected module SHA256 `a8276ae0ebd2761b2dcc1a1d6bbeea507b64a9eab9351fe02fbd25836406c7b8` and test SHA256 `317304551bc1d360681e34d72a1a25dea237b86a576b30768810c352ecbe278b`. The initial finding/verdict is retained, not retroactively described as a pass.

The original 35,740-byte new-test prefix is preserved exactly, including all assertions; the two regressions are appended. Initial schema testing also found and corrected a missing terminal-failure null constraint. A temporary regression insertion error was corrected by restoring the original function boundary, not dropping assertions.

Request graph admission additionally guards depth, cycles, exact built-ins, one million visited nodes and 32 MiB aggregate UTF-8 text. It does not impose new backing-only string/aggregate limits. These checks are not hard process/RSS/deadline containment. No large-stress allocation or quantum execution was used.

Source-only metadata edits recording this result do not change the independently reviewed API/profile rules. No broader full-suite, performance, production, release, privacy, hard-resource or kernel-pin qualification is claimed. Work remains local and uncommitted; no push or deployment occurred.
