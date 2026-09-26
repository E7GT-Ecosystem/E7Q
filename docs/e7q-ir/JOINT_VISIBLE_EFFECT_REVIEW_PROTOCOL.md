# E7Q Joint visible-effect reviewer protocol

**Status:** ready to run when an independently supplied real task and independent reviewer are available. No such task/session is recorded yet; the adoption gate remains open. The existing diagonal/crossed fixtures are already compared and must not be counted as reviewer evidence or replayed as a substitute.

## Purpose

Measure one real bounded planning task using the same frozen source intent in three conditions:

1. **Joint path:** pinned E7C source replay, independent IR replay, and the opt-in E7Q mapping with ordered filters, exact coefficients, row events and typed outcome.
2. **Competent full correlated table:** independently prepared two-column table preserving every source row, signed exact coefficient, correlation, filter order, exclusion and terminal outcome.
3. **Lossy marginal Cartesian table:** diagnostic reconstruction from separate layout and target marginals. It is intentionally lossy and must not be presented as an equivalent competent table.

Compare Joint primarily with the competent full table. The marginal baseline demonstrates what correlation loss does; it is not evidence that Joint is better than an ordinary table that preserves correlation.

## Eligibility and freeze

- Obtain one task independently from actual reviewer work, with the task owner’s permission to use a sanitized copy. Do not invent a prompt or use a synthetic fixture. Store no client-confidential text in the public PR; use a pseudonymous `origin_ref` and keep the source mapping privately if needed.
- The reviewer must not have built the adapter or prepared either baseline. Record their relevant experience and independence without unnecessary personal information.
- The task must be representable by the pinned pilot’s admitted two dimensions: `L0/L1` and `T0/T1`, with a finite unique Joint support and nonzero reduced signed rational coefficients. Record how each label maps to an actual task alternative. Reject or separately scope a task that does not fit; do not coerce it into the fixture.
- The frozen task JSON must identify itself as `real_workflow`, include a nonempty independent `origin_ref`, freeze the exact label meanings in `dimension_mapping`, and list both fixed filter identities in order. The implemented rules are stage 1: exclude `layout=L1`; then stage 2: among stage-one retained rows, exclude `target=T1`. Task-specific descriptions do not change these rules.
- Before replay, freeze the expected-result oracle in a separate JSON file. Record its reference and SHA-256 in `expected_result`; the runner verifies the bytes and task ID. The oracle includes the expected terminal status, ordered retained/excluded rows with exact coefficients, and a reason plus filter identity for every exclusion. Freeze and independently assess this oracle before any condition is shown.
- Randomize the order of the Joint and full-table conditions for the single reviewer session and record the draw and actual order. One session is not counterbalanced; acknowledge possible carryover in the record. Estimating order effects requires multiple independent sessions with a planned counterbalanced sequence.
- Run in a sandbox with no external side effects. Do not let choices from one condition alter the task shown in another.

## Prepare and execute

1. Create and freeze the task JSON and separate expected-result oracle. Map real alternative IDs and meanings explicitly. Compute the oracle digest with `sha256sum frozen-oracle.json`, put that digest and a stable reference in the task JSON, then record the final task JSON digest. Do not edit either file after freezing.
2. Check out E7G-T at the exact E7C source pin required by #79. The runner rejects any other HEAD:

       git -C "$E7C_ROOT" rev-parse HEAD
       # must equal 5b5cb5f10ddd913df66f5d9f65fbe059a2e33193

3. Run the single-task replay utility from the E7Q checkout:

       PYTHONPATH=src python tools/run_joint_visible_effect_review.py \
         --e7c-root "$E7C_ROOT" \
         --task /path/to/frozen-real-task.json \
         --oracle /path/to/frozen-oracle.json \
         --output /path/to/private-run/machine-replay.json

   The output records the task and oracle hashes, E7C source result, independent IR result, mapped rows, ordered events, Q-A1 outcome, full correlated table, lossy marginal table, and oracle check. Its task-limit text refers to the supplied task record. It does not contain human review metrics.
4. Only a normal E7C `success` terminal result matching a frozen success oracle may enter the retained/excluded decision comparison. An E7C `resource_limit` is recorded as its own typed outcome, with progress, and is not scored as a successful decision comparison. Do not raise resource bounds after seeing the outcome; a changed bound requires a new frozen task and oracle.
5. Have an independent competent table operator prepare the full correlated table from the frozen source data without copying the Joint output. Compare the operator’s table with the generated exact reference, then show it to the reviewer under a neutral condition label.
6. Randomly select and record whether the reviewer sees Joint or full-table first. Use identical instructions and the same source task; obtain and record each decision and reasons before switching. Note the carryover risk. Present the marginal-only condition last as a diagnostic, then explain correlation loss and reconcile invented pairs before the session ends.
7. Record active task time separately for each condition, excluding setup and interruptions; also record preparation time, corrections, errors, assistance, confidence and the reviewer’s own stated reasons. Capture activity logs only with consent. Have the independent assessor score outcomes against the frozen oracle.
8. Preserve the exact PR head, E7C pin, task/oracle hashes, script version, machine output hash, baseline artifacts and completed form. Report descriptive findings for this task only. If Joint and the full table yield the same decision, effort and errors, record that as a no-advantage result. One task does not establish general product adoption.

## Frozen task JSON schema

```json
{
  "schema": "e7q.joint-visible-effect-task/v1",
  "task_kind": "real_workflow",
  "task_id": "pseudonymous-task-id",
  "origin_ref": "private-source-reference-or-approved-hash",
  "source_intent": "sanitized description of the real planning intent",
  "dimension_mapping": {
    "layout": {"L0": "real option alpha", "L1": "real option beta"},
    "target": {"T0": "real target gamma", "T1": "real target delta"}
  },
  "filter_rules": [
    {"stage": 1, "rule_id": "joint.first.exclude-layout-L1/v1", "dimension": "layout", "excluded": "L1", "description": "task-specific explanation"},
    {"stage": 2, "rule_id": "joint.second.exclude-target-T1/v1", "dimension": "target", "excluded": "T1", "description": "task-specific explanation"}
  ],
  "expected_result": {
    "ref": "private-or-approved-oracle-reference",
    "sha256": "64-lowercase-hex-digest-of-oracle-bytes"
  },
  "rows": [
    {"layout": "L0", "target": "T0", "coefficient": "1/2"},
    {"layout": "L1", "target": "T1", "coefficient": "1/2"}
  ],
  "step_bound": 20,
  "ledger_bound": 20
}
```

The example rows and meanings only illustrate the schema; replace them with the independently supplied real task. The fixed rule IDs and order must match the implemented filter semantics.

The separate oracle uses schema `e7q.joint-visible-effect-oracle/v1`, the same `task_id`, and `terminal_status` `success` or `resource_limit`. For a success comparison it contains `retained`, `first_excluded`, `second_excluded` arrays of `{layout,target,coefficient}` rows and `exclusion_reasons` entries `{layout,target,rule_id,reason}`. Each excluded row must have exactly one reason bound to its filter ID. A resource-limit oracle gives a `resource_limit_reason`; it is never used for retained/excluded scoring.

## Decision and error definitions

Before the session, the independent assessor freezes the correct allowed, retained and excluded sets plus each reason. Count an error when the reviewer selects a disallowed pair; misses or invents an exclusion; changes/misreads a signed coefficient; treats an E7C successful empty Joint as a non-empty Q-A1 family; or reports a terminal status unsupported by the frozen source. Record each error, whether self-corrected, and its consequence. Do not classify another admissible choice as an error unless the frozen task oracle rules it out.

Use the accompanying recording form for raw observations. Keep participant and task-owner identity out of public artifacts unless they explicitly consent.
