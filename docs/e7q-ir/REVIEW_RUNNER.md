# Local review campaign and evidence inventory

This implements the first H1/H4 increment. It connects the existing repository
suite to an inspectable JSON report and a versioned test-file inventory in
[REVIEW_CAMPAIGN.json](REVIEW_CAMPAIGN.json). It does not reproduce the missing
external harness or complete the claim-level capability matrix.

From a checkout with the test extra installed:

```bash
python -m pip install -e '.[test]'
python scripts/review_campaign.py --output /tmp/e7q-review.json
```

Use a fresh virtual environment and a clean, exact checkout when preparing a
review package. Save its full SHA, report and checkout/fixture archive together.
The runner records a dirty checkout explicitly; a clean Git revision alone does
not identify uncommitted content. Input digests cover local source, tests,
examples, schemas, profiles, scripts, the manifest and project configuration.
They also bind test-defined seeds, tolerances and generated fixtures. The report
records Python, NumPy and pytest versions, platform and the actual command.

The manifest covers every current test file; a regression gate detects additions
without a corresponding entry. Each entry identifies directly imported modules,
test scope, limitations and the next review gate. Direct imports are not a full
transitive dependency map. Report rows add collected parametrized pytest node IDs
and setup/call/teardown outcomes. These are test cases, not individual assertion
counts. A test containing multiple assertions or an exhaustive loop remains one
case. Individual numeric outputs are retained only when tests report them;
this runner does not invent raw observations absent from the tests.

PASS requires successful execution, nonempty results, coverage of every manifest
file, no failed or skipped case, and unchanged input digests/revision during the
run. Collection errors and failed teardown fail the campaign. Skips and expected
failures cannot produce PASS. Extra pytest plugins and PYTEST_ADDOPTS are disabled
so unrelated local configuration cannot silently change selection. Test code is
trusted repository code; this runner is not an untrusted-plugin sandbox.

Output must be outside the repository, preventing accidental input replacement
and self-referential fingerprints. Report ordering is stable; environment fields
and pytest timing text can vary. Compare case IDs/outcomes and input digests for
semantic replay; do not expect byte-identical reports across machines.

## External-review reconciliation

WB-01–WB-25 preserve the reported grouped checks and point to related local test
files. All remain `UNRESOLVED_ORIGINAL_HARNESS`: related coverage is not an assertion
mapping or proof that the original campaign was reproduced. The report claimed
32 checks; grouping may explain the difference. Exact original seeds, environment,
assertion definitions and raw output remain unavailable. Internal development
continues without them. Local campaign PASS never upgrades this external status.

The terminal density-matrix project record currently supplies shots/outcomes;
trace and purity must not be advertised as fields of every step. H4 still needs
an exhaustive public-claim/criterion/domain/fixture matrix and field-level audit.
H1 still needs richer assertion-level numerical observations and clean-environment
independent reproduction. H2/H3 will add cases only after reviewing actual gaps.
