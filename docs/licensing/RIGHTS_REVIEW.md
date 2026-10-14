# Licensing evidence and remaining rights review

Snapshot date: 2026-10-14. Main: `c519484bccdbe411b05acdba9c24ef1cd852d041`.

## Established repository facts

- `LICENSE`: Apache-2.0. `LICENSE-DOCS`: CC-BY-SA-4.0.
- `NOTICE`, package metadata and `CITATION.cff` name Oleksandr Razinkov.
- `CONTRIBUTING.md` previously accepted Apache code and CC-BY-SA documentation
  unless a file specified otherwise. No commercial contributor agreement was found
  among the tracked files inspected at this baseline.
- Merged PRs #83/#84 contain public software and co-author acknowledgements.
  Public open PRs #59/#77/#79/#80/#81/#85 retain their granted terms. We do not
  relabel them or infer ownership assignments from attribution edits.
- The latest 100 commits were inspected for attribution and licensing context;
  that is a bounded history inspection, not the entire contribution history.
- [published-baseline-20261014.json](published-baseline-20261014.json) inventories
  277 tracked main files, Git blob IDs and content SHA-256 digests. It records
  publication identity/default declarations, not title to copyright.
- No new commercially designated implementation is included in this package.

## Required before adding commercially licensed implementation

| Review | Current status / next evidence |
|---|---|
| Licensor identity and authority | Owner attribution exists; verify rights and contracting authority per component |
| Human/AI-assisted contributions | Inspect relevant history and any collaborator/employer/platform agreements; no assignments inferred |
| Third-party and copied material | Retain original terms; review notices and compatibility before incorporation |
| Upstream E7G-T text | Supplied references use CC-BY-SA; identify copied/adapted expression and rights-holder permissions separately |
| Contributor commercial permissions | Written agreement required for new outside contributions; no agreement represented as executed |
| Standard public licence | PolyForm Noncommercial 1.0.0 copied verbatim from the official tagged source; review scope/patent clause |
| Commercial customer agreement | Not executed; scope, fees, law and remedies require an actual negotiated agreement |
| Brand protection | No trademark registration or exclusivity asserted; develop a separate policy if needed |

Declared dependencies at this baseline: NumPy; pytest/jsonschema test extras;
optional Stim 1.16.0, Qiskit 2.5.2, MQT QCEC 3.9.0 and PyZX 0.10.6. This task
does not vendor, replace or relicense them. Verify the actual distributed
versions, transitive dependencies, notices and terms before any commercial build;
this list is not a completed software bill of materials or compatibility opinion.

## Sources and preservation

- Apache 2.0: https://www.apache.org/licenses/LICENSE-2.0 (sections 2, 4, 5 and 6).
- CC BY-SA 4.0: https://creativecommons.org/licenses/by-sa/4.0/legalcode.en
  and https://creativecommons.org/faq/ (prior grants and adaptations).
- PolyForm official tagged text:
  https://github.com/polyformproject/polyform-licenses/blob/1.0.0/PolyForm-Noncommercial-1.0.0.md
- Public repository visibility: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository

No source-code licence can retract already granted Apache/CC permissions or
create ownership of abstract quantum/IR ideas. The commercial boundary controls
only rights the licensor can lawfully grant in designated new expression.

## Validation of this licensing package

Builder: Codex; issue #86. Local checks on Python 3.12:

- `python scripts/check_licensing_boundary.py`: PASS.
- `python scripts/test_licensing_boundary.py`: 10 negative/positive controls PASS.
- `git diff --check`: PASS.
- Built wheel and source archive using the installed setuptools backend with a
  temporary, synthetic `commercial/e7q_ir/packaging_probe.py`. Both excluded all
  commercial files, retained the existing Q-A3 module and Apache package metadata.
  The probe and local build directory were removed; neither is committed.
- Standard PolyForm text matches the official tagged download byte-for-byte;
  its SHA-256 is pinned in the component register. Root LICENSE and LICENSE-DOCS
  remain byte-for-byte unchanged.

No quantum runtime source or semantics changed. The full quantum regression suite
was not rerun locally for this policy/package-discovery change; hosted CI runs
the existing suites plus the new boundary checks. Setuptools reported the
existing TOML licence-table deprecation; a metadata format migration is separate.
These checks assess repository/package boundaries, not legal enforceability.
