# E7Q-IR × E7C/EEC-Q opt-in Joint planning pilot

Status: executable **synthetic pilot for substantive review**, not product adoption or E7C implementation proof. This implements the first increment scoped in [#78](SECOND_PRODUCT_JOINT_PILOT_SCOPE.md). New work uses E7G-T v0.15/MSC1 (`2cba2045bb22036ce489083a5ac853a9d867eb21`) as its source; the already existing Q-A1 and selected E7C source/IR operations keep their own edition pins. This explicit user direction supersedes the old new-work v0.12.1 sentence in `AGENTS.md`; no prior Q-A1/E7C result is relabelled as v0.15.

## Replay and provenance

The runner requires the E7G-T checkout at exact `5b5cb5f10ddd913df66f5d9f65fbe059a2e33193` (merged #128/#129). It fails closed on any other head. It imports the *actual* E7C source admission/evaluator, nested E7-IR `/0.5` and outer E7-IR `/0.6` lowering and independent evaluator. The new E7Q mapping is `e7q.ir.e7c-joint-q-a1-mapping/v0alpha1`, additive and opt-in. None of the native Q-A1 members, schemas, IDs, Q-A2 histories, receipts, quantum execution APIs or historical proofs changes.

```sh
git clone https://github.com/E7GT-Ecosystem/E7G-T.git pinned-e7c
git -C pinned-e7c checkout 5b5cb5f10ddd913df66f5d9f65fbe059a2e33193
PYTHONPATH=src python tools/run_e7c_joint_pilot.py --e7c-root pinned-e7c --output fixtures/e7c-joint-pilot
E7C_ROOT=pinned-e7c PYTHONPATH=src python -m pytest -q tests/test_e7c_joint_pilot.py
```

The [manifest](../../fixtures/e7c-joint-pilot/manifest.json) binds every saved canonical JSON replay byte stream. Each case includes the complete source document and witness, the complete independently executed IR package, source and IR ordered transition traces and results, Q-A1 family and opt-in mapping, both conventional baselines, and the separate package bounds. Runner compares source and independent IR observations; it never substitutes source claims for the IR result. CI checks out the pinned E7G-T commit and reproduces saved bytes; there is no implicit sibling checkout or skipped replay.

## Admission and result translation

The E7C `admit` function validates the source *first*. The narrower pilot mapping additionally admits one named intent, binary graph pairs with exact known `pilot.layout` and `pilot.target` tags, layout edges `[]`/`[AB]`, target edges `[]`/`[BC]`, at most four unique canonically ordered support rows, and reduced nonzero signed fractions. `L1` means coordinate 0 contains `AB`; `T1` means coordinate 1 contains `BC`. The two predicates remain E7C `FG3-JOINT-COORD0-ABSENT-AB/0.1-provisional` and `FG3-JOINT-COORD1-ABSENT-BC/0.1-provisional`. Every mapping row binds its original source index, source row digest, Q-A1 member ID and rational numerator/positive denominator. Revalidation rebuilds all IDs and rejects stale family, altered row order/coefficient, missing row, unknown member or ambiguous mapping. Member sorting in Q-A1 is kept distinct from canonical source Joint order.

| Case | Source correlated rows with exact formal coefficients | Final retained | First excluded | Second excluded | E7C / Q-A1 final |
|---|---|---|---|---|---|
| A diagonal | `(L0,T0): 1/2`, `(L1,T1): 1/2` | `(L0,T0): 1/2` | `(L1,T1): 1/2` | none | `success` / `success` |
| B crossed | `(L0,T1): 1/2`, `(L1,T0): 1/2` | none | `(L1,T0): 1/2` | `(L0,T1): 1/2` | `success` with empty retained Joint / `empty` with no residual family |
| Signed | `(L0,T0): 1/2`, `(L1,T1): −1/2` | `(L0,T0): 1/2` | `(L1,T1): −1/2` | none | `success` / `success`; signed coefficients remain formal |
| Failed second append (A) | same input rows as A, ledger bound `3` | **no completed partition** | first excluded `L1,T1` available as progress | none recorded | `resource_limit`, charged `4` steps, `3` ledger entries, `secondStarted=true` / no Q-A1 final restriction |

On A/B success, event order is first attempt; two first-stage row checks; second attempt; one retained-stage row check. Source and IR serialize the same event payloads and ordered ledger. On failed second append, the second attempt charges a step, sets `secondStarted=true`, fails to append to a full ledger, and returns `resource_limit` without a fabricated success. The `full_correlated_table` stored with that non-success case is a *separate conventional mathematical baseline*, never an E7C result. An input `2/4` is canonicalised to `1/2` before document creation; an explicit zero row stays invalid even when a later duplicate could otherwise mask it. [Hostile mutation outcomes](../../fixtures/e7c-joint-pilot/hostile_mutations.json) retain rejection evidence.

## Both baselines and measured limits

A conventional full correlated two-column table with an exact rational cell and two ordered filters reproduces A **and** B, including the separate exclusion lists, coefficients and ordered attempt/row audit trace. In these examples it requires two source rows, two filters and explicit audit recording; we have measured no reviewer time, error rate or artifact usability difference. The table baseline has no budget-sensitive execution model, so its complete prediction in the failed-append case cannot replace the typed E7C `resource_limit` result. The deliberately lossy marginal-only Cartesian reconstruction reports identical `L0/L1 = 1/2` and `T0/T1 = 1/2` for both A and B, invents four pairs of `1/4` and produces an artificial retained `(L0,T0)` for B. This establishes a loss-of-correlation counterexample, **not superiority to competent full tables**.

For the four saved cases nested `/0.5` packages are `4,551–4,558` bytes; outer `/0.6` packages are `13,654–14,160` bytes, each against its own `1,000,000` byte bound. Separate deterministic oversized-tag tests exercise the underlying E7C IR boundaries *outside this narrow opt-in tag mapping*: at 80,000 tag characters nested `/0.5` is `403,437` bytes and admits, while attempted outer `/0.6` is `1,290,639` bytes and refuses; at 200,000 tag characters nested `/0.5` would be `1,003,437` bytes and refuses before outer lowering. Because `/0.6` embeds `/0.5`, an overflowing child and admitted outer are not a reachable actual lowering path. These are IR package-size outcomes, distinct from E7C step/ledger outcomes.

## Open gates

The examples are synthetic identifiers, not a measured device topology or an independently reviewed real task. Rational coefficients are formal construction coefficients, never amplitudes, probabilities, evidence weights, backend scores or hardware observations. The old E7C source and IR editions remain provisional. Executing source and independent IR on these examples is finite evidence; the all-input Python/IR-to-Lean correspondence (admission, serialization, two-stage control, failure/resource paths) remains open in E7C. Q-A3 selected-mapping realisation, Q-A4 binding and independent product source/assessor provenance also remain open. Product adoption needs an independently reviewed task and a real workflow comparison against the *full correlated table*.
