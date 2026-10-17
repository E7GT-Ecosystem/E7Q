# E7Q-QEC/0.1

Read [REPORT.md](REPORT.md) for results, interface audit, semantic limits and reproduction commands.

- `adapter.py`: typed cases, independent dense Pauli oracle, actual E7Q circuit calls, 77-case mutation corpus.
- `conventional.py`: independent Stim stabilizer-code verification.
- `decoder_table.py`: complete coherent decoder-table circuit, 33 cases.
- `claim_controls.py`: native E7Q claim/criterion negative controls.
- `profiles.py`: opt-in calls to unchanged MSC-B1/REC-B1 and separate REC replay checker.
- `test_*.py`: differential and adversarial regressions.
- `results/`: full native reports, circuit source, oracle outputs and measured timing.
- `reference/`: supplied reference files, preserved without modification; not imported by the adapters.
- `SOURCE_MANIFEST.json`: exact upstream and delivered-source identities.

This is an additive local pilot. Existing E7Q verifies the submitted circuits; the adapter is not a new quantum decoder or proof of general QEC capability.
