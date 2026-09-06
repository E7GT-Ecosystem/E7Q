# E7Q-IR Phase 1A: F2 semantic-validation framework

Phase 1A introduces the validator interface, explicit registry, typed semantic
results, F2 aggregation, and CLI support without claiming circuit semantics.

## Delivered

- deterministic per-artifact and per-relation semantic results;
- stable result identities, check identifiers, evidence references, criteria,
  explanations, and retained boundaries;
- separate `PASS`, `FAIL`, `BLOCKED`, `UNSUPPORTED`, and `NOT_ASSESSED` states;
- F2 aggregation that passes only when every required result passes;
- fail-closed handling for unknown profiles, missing validators, endpoint
  profile mismatch, exceptions, malformed results, foreign evidence, duplicate
  checks, and excessive result counts;
- `e7q ir validate --level F2` and public experimental schemas;
- valid, malformed, blocked, unsupported, deterministic, resource-limit, and
  CLI regression coverage.

## Present boundary

`e7q.ir.validator.circuit-basic/0alpha1` is registered as framework-only. It
returns `NOT_ASSESSED` for current artifacts and relations, including declared
transformation criteria. Phase 1A therefore creates no built-in F2 PASS and
does not establish circuit equivalence, provider authenticity, execution, or
physical fidelity.
