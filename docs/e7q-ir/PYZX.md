# Optional PyZX equality evidence

E7Q-IR pins the optional adapter to PyZX 0.10.6. PyZX documents
`Circuit.verify_equality(other, up_to_swaps=False, up_to_global_phase=True)`
as composing one circuit with the other's adjoint and attempting full
ZX-calculus reduction to identity. It explicitly states that success is strong
evidence of equality and failure to reduce proves nothing:
https://pyzx.readthedocs.io/en/latest/api.html#pyzx.circuit.Circuit.verify_equality

PyPI records 0.10.6 as the 1 September 2026 Apache-2.0 release:
https://pypi.org/project/pyzx/

## E7Q-IR mapping

| PyZX result | E7Q-IR status | Conclusion |
| --- | --- | --- |
| `True` | `PASS` | `ESTABLISHED` under the selected PyZX criterion |
| `False` or `None` | `NOT_ASSESSED` | `INCONCLUSIVE` |
| parent deadline or explicit memory exhaustion | `BLOCKED` | `INCONCLUSIVE` |
| unsupported admitted input | `UNSUPPORTED` | `INCONCLUSIVE` |
| crash, signal, protocol or internal error | `NOT_ASSESSED` | `INCONCLUSIVE` |

Exact and global-phase relations are separate criterion IDs. Qubit swaps are
always disabled. The adapter does not turn a failed reduction into
non-equivalence and does not use PyZX to satisfy E7Q's exact-algebraic
signed-permutation criteria.

## Admission and projection

The adapter first applies E7Q's bounded OpenQASM 2 parser and admits one
equally wide register pair, qelib1.inc, static noiseless operations, terminal
identity measurement, at most 64 qubits, 2,048 gates and 262,144 source bytes.
Terminal measurement is validated and removed before unitary comparison.
PyZX never receives rejected input.

Every worker has a parent-owned wall deadline and requested POSIX
`RLIMIT_AS` bound. Reports retain actual enforcement, resource observations,
worker termination/reaping, raw one-sided result and all limitations.

The captured four-case evaluation is
`benchmarks/e7q-ir/pyzx-0.10.6-results.json`. It is evaluation evidence for
the named corpus—not default F2 conformance, a proof of arbitrary 25+ qubit
tractability, hardware execution, provider identity or physical fidelity.
