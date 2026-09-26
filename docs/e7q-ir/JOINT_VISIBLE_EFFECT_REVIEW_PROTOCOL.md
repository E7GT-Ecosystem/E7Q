# E7Q Joint visible-effect reviewer protocol

**Status:** ready to run when an independently supplied real task and independent reviewer are available. No such task/session is recorded yet; the adoption gate remains open. The existing diagonal/crossed fixtures are already compared and must not be counted as reviewer evidence or replayed as a substitute.

## Purpose

Measure one real bounded planning task using the same frozen source intent in three conditions:

1. **Joint path:** pinned E7C source replay, independent IR replay, and the opt-in E7Q mapping with ordered filters, exact coefficients, row events and typed outcome.
2. **Competent full correlated table:** an independently prepared two-column table preserving every source row, signed exact coefficient, correlation, filter order, exclusion and terminal outcome.
3. **Lossy marginal Cartesian table:** the diagnostic baseline that reconstructs candidates from separate layout and target marginals. It is intentionally lossy and must not be presented as an equivalent competent table.

Compare Joint primarily with the competent full table. The marginal baseline demonstrates what correlation loss does; it is not evidence that Joint is better than an ordinary table that preserves correlation.

## Eligibility and freeze

- Obtain one task independently from actual reviewer work, with the task owner’s permission to use a sanitized copy. Do not invent a prompt or use a synthetic fixture. Store no client-confidential text in the public PR; use a pseudonymous `origin_ref` and keep the source mapping privately if needed.
- The reviewer must not have built the adapter or prepared either baseline. Record their relevant experience and independence without unnecessary personal information.
- The task must be representable by the pinned pilot’s admitted two dimensions: `L0/L1` and `T0/T1`, with a finite unique Joint support and nonzero reduced signed rational coefficients. Record how these symbols map to the task’s actual alternatives. Reject or separately scope a task that does not fit; do not coerce it into the fixture.
- Before exposing any condition, freeze the source-intent identifier, admissible candidate set, source Joint, mapping, two ordered filter rules, exact coefficients, resource policy and correctness oracle. Hash the task JSON and replay artifacts. Have an independent assessor verify the expected result and exclusion reasons.
- Run in a sandbox with no external side effects. Do not let choices from one condition alter the task shown in another.

## Prepare and execute

1. Convert the frozen task into the JSON schema below. Keep the real task’s provenance in `origin_ref`; keep source-intent meaning in `source_intent`; list each admitted correlated row exactly once. Use canonical reduced fractions such as `1/2` or `-1/3`.
2. Check out E7G-T at the exact E7C source pin required by #79. The runner rejects any other HEAD:

       git -C "$E7C_ROOT" rev-parse HEAD
       # must equal 5b5cb5f10ddd913df66f5d9f65fbe059a2e33193

3. Run the new single-task replay utility from the E7Q checkout:

       PYTHONPATH=src python tools/run_joint_visible_effect_review.py \
         --e7c-root "$E7C_ROOT" \
         --task /path/to/frozen-real-task.json \
         --output /path/to/private-run/machine-replay.json

   The output contains the E7C source result, independent IR result, mapped rows, ordered events, Q-A1 outcome, full correlated table and lossy marginal table. It does not contain reviewer effort or judgement.
4. Have an independent competent table operator prepare the full correlated table from the frozen source data without copying the Joint output. Compare the operator’s table with the generated reference, then show it to the reviewer under a neutral condition label.
5. Present the Joint and full-table conditions in counterbalanced order, using identical instructions and the same source task. Record a decision and reasons before switching conditions. Present the marginal-only condition last as a diagnostic, then explain the correlation loss and reconcile any invented pairs before the session ends.
6. Record active task time separately for each condition, excluding setup and interruptions; also record preparation time, corrections, errors, assistance, confidence and the reviewer’s own stated reasons. Capture screen/activity logs only with consent. Have the independent assessor score outcomes against the frozen oracle.
7. Preserve the exact PR head, E7C pin, task hash, script version, output hash, baseline artifacts and completed form. Report descriptive findings for this task only. If Joint and the full table yield the same decision, effort and errors, record that as a no-advantage result. One task does not establish general product adoption.

## Frozen task JSON schema

```json
{
  "schema": "e7q.joint-visible-effect-task/v1",
  "task_id": "pseudonymous-task-id",
  "origin_ref": "private-source-reference-or-approved-hash",
  "source_intent": "sanitized description of the real planning intent",
  "rows": [
    {"layout": "L0", "target": "T0", "coefficient": "1/2"},
    {"layout": "L1", "target": "T1", "coefficient": "1/2"}
  ],
  "step_bound": 20,
  "ledger_bound": 20
}
```

The two rows above only illustrate the schema; they are synthetic and must not be used as the real reviewer task.

## Decision and error definitions

Before the session, the independent assessor freezes the correct allowed, retained and excluded sets plus the reason for each exclusion. Count an error when the reviewer: selects a disallowed pair; misses or invents an exclusion; changes/misreads a signed coefficient; treats an E7C successful empty Joint as a non-empty Q-A1 family; or reports a terminal status unsupported by the frozen source. Record each error, whether self-corrected, and its consequence. Do not classify a different but admissible choice as an error unless the frozen task oracle rules it out.

Use the accompanying recording form for raw observations. Keep participant and task-owner identity out of public artifacts unless they explicitly consent.
