# Synthetic topology compiler Proof-of-Path example

This public example exercises the existing `e7q.language.compile_topology()`
implementation. It does not define a second compiler.

[`nonlocal-cx.e7q`](nonlocal-cx.e7q) contains `CX q[0], q[3]`. The declared
undirected linear coupling graph is `0-1-2-3`, with native gates `H`, `CX` and
`SWAP`. The compiler selects physical path `[0, 1, 2, 3]`, inserts forward
SWAPs `(0,1)`, `(1,2)`, applies `CX` on `(2,3)`, then inserts reverse SWAPs
`(1,2)`, `(0,1)`. The final trace asserts restored logical layout.

The generated E7Q-IR graph is
[`benchmarks/e7q-ir/compiler-proof-nonlocal-cx-results.json`](../../../benchmarks/e7q-ir/compiler-proof-nonlocal-cx-results.json),
with identity
`sha256:17265fa58a1a46f47db36ba800ca5613e374fd3dd6a687c1dde832c5c74a5827`.
It preserves the source bytes, parsed program, complete original compiler
Proof-of-Path, typed routing steps, independently identified source and compiled
representations, terminal-measurement projection boundary, QCEC assessment and
bounded claim.

MQT QCEC 3.9.0 returned deterministic `equivalent` under
`e7q.ir.qcec-numerical-unitary`. The worker used an enforced parent wall-clock
deadline and POSIX `RLIMIT_AS`, exited zero and was reaped. F0/F1 pass. F2 is
`BLOCKED` because no compiler-proof semantic validator is installed; the local
trace consistency checker is not promoted to default F2 truth.

Reproduction:

```bash
python -m e7q.ir.compiler_workflow \
  examples/e7q-ir/compiler-proof/nonlocal-cx.e7q \
  --edge 0:1 --edge 1:2 --edge 2:3 \
  --native-gate H --native-gate CX --native-gate SWAP \
  --criterion e7q.ir.qcec-numerical-unitary \
  --numerical-tolerance 2.2737367544323206e-13 \
  --fidelity-threshold 1e-8 \
  --timeout-seconds 10 \
  --memory-limit-bytes 68719476736 \
  --created-at 2026-09-08T00:00:00Z \
  --source-ref fixture:compiler-proof:nonlocal-cx \
  --output benchmarks/e7q-ir/compiler-proof-nonlocal-cx-results.json
```

This evidence does not establish hardware feasibility, topology quality,
physical fidelity, provider authentication, execution success, exact-algebraic
equivalence, arbitrary scalability, Phase 2 completion or H5 completion.
