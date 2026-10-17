# E7Q-QEC/0.1 — First reproducible test

This is a **conventional QEC reference test**, not an implementation of E7Q or E7G-T. It uses standard-library Python only, and models encoded complex quantum state vectors (not simply classical votes).

## Run

```bash
python3 qec_probe.py
```

The script produces `qec_results.json` and prints the results. Expected outcomes:

- **16/16** reference cases pass: four normalized logical states, each with no error or one of three individual X bit flips.
- **8/16** faulty-decoder cases fail: the experiment deliberately swaps two recovery instructions.
- A **Z phase error is not corrected**. This is expected: the three-qubit repetition code protects against one X error, not arbitrary Pauli errors.
- Logical bit-flip rate across independent physical flips is **3p² − 2p³**.

## What to do next with the actual projects

1. Implement a strictly typed `QECCase` exchange format: complex amplitudes, declared stabilizer generators, error operators, expected syndrome, decoder, recovery action, and expected code-space fidelity.
2. Run the existing E7Q verifier against the 16 positive reference cases, 16 corrupted-decoder cases, and one negative phase-error control. Record *which exact E7Q contract* rejects errors, and capture reproducible witnesses. Do not score simple Python assertion failures as E7Q findings.
3. Implement a separate, opt-in E7G-T MSC/REC adapter from stabilizer syndrome relations to explicitly defined carriers, scopes, overlaps, and maps. The adapter MUST document how it represents quantum measurements and which quantum assertions are externally verified. Record rejected or unrepresentable cases; do not silently reinterpret EEC-Q coefficients as amplitudes.
4. Compare actual E7Q outputs against a conventional oracle on correctness, defects detected, false positives, analysis time and diagnostic usefulness. For E7G-T, compare the additional adapter's results to the same oracle. Do not claim improved QEC performance without comparative evidence.
5. Extend to two-bit flips (expected failure modes) and then a distance-three code (Steane [[7,1,3]] or a surface-code patch) only after the first adapter is real and tested.

## Reference

IBM Quantum Learning: https://learning.quantum.ibm.com/course/foundations-of-quantum-error-correction/correcting-quantum-errors
