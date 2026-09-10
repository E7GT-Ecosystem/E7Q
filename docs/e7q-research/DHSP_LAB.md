# Bounded DHSP Algorithm-Discovery Laboratory

**Status:** experimental research harness; not a registered E7Q-IR capability.

## Purpose

This lane gives human and AI researchers a fail-closed place to propose and
falsify components of algorithms for the dihedral hidden subgroup problem
(DHSP). It begins by reproducing one elementary identity used by known sieve
approaches. It neither proposes a new DHSP algorithm nor claims polynomial
time, quantum advantage or physical feasibility.

For modulus `N`, label `k` and hidden shift `s`, the reference phase state is

`|psi(k,s)> = (|0> + exp(2*pi*i*k*s/N)|1>)/sqrt(2)`.

Applying CNOT from the first of two phase-state qubits to the second and then
measuring the second gives a remaining label `k+l` on outcome zero and `k-l`
on outcome one, modulo `N`. Each ideal branch has probability one half. The
outcome-one derivation discards a global phase; the hidden-shift-dependent
relative phase is preserved.

## E7G-T extension record

- **Source/carrier:** ideal DHSP phase-state labels and two phase qubits.
- **Context/inquiry:** whether a proposed affine label-combination rule agrees
  with the reference CNOT/measurement transformation.
- **Representation:** integer modulus, hidden shift, labels, measurement branch
  and affine coefficients. EEC coefficients are not used.
- **Transformation:** ideal CNOT, computational-basis measurement and
  postselection on the recorded result.
- **Preserved:** modulus and the resulting hidden-shift-dependent relative phase.
- **Lost:** the measured qubit and absolute global phase.
- **Criterion:** `e7q.research.dhsp.affine-phase-combination/1`.
- **Bounds:** moduli 2–64; at most 32 distinct moduli per candidate evaluation;
  affine two-label rules only.
- **Maximum conclusion:** agreement over the explicitly enumerated domain, or a
  concrete counterexample within it.

A bounded PASS means only that no counterexample occurred in the enumerated
domain. It does not establish universal correctness, an implementable oracle,
success amplification, or polynomial query/time/space complexity.

## Evidence corpus

`scripts/benchmark_dhsp.py` evaluates the known `k+l`/`k-l` rule and two
intentionally incorrect rules over every label pair and measurement outcome for
moduli 2–16. The deterministic report is stored at
`benchmarks/e7q-research/dhsp-affine-corpus.json`. Incorrect candidates stop at
and retain their first counterexample rather than claiming complete enumeration.
The current report ID is
`sha256:b4ce39c5bafedc69a316ba861dcb2af51e2dd97c13bfaa935c7e3ee0714bf735`.

## Primary foundations

- Greg Kuperberg, *A subexponential-time quantum algorithm for the dihedral
  hidden subgroup problem*: https://arxiv.org/abs/quant-ph/0302112
- Oded Regev, *A Subexponential Time Algorithm for the Dihedral Hidden Subgroup
  Problem with Polynomial Space*: https://arxiv.org/abs/quant-ph/0406151
- Oded Regev, *Quantum Computation and Lattice Problems*:
  https://arxiv.org/abs/cs/0304005

The next research gate is a typed proposal format for multi-stage algorithms
with explicit oracle, query, gate, qubit, classical-time, memory and success-
probability recurrences. Simulation or bounded enumeration must never satisfy
that asymptotic proof obligation.
