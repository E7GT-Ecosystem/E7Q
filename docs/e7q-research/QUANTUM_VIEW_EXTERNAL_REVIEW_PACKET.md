# Independent mathematical-physics review packet

**Repository:** E7GT-Ecosystem/E7Q, pull request [#81](https://github.com/E7GT-Ecosystem/E7Q/pull/81), draft.
**Pinned implementation and audit baseline:** `e71869c78ab2595c97b48b85bda14f1c93dc8a4`.
**Review artifact:** [`QUANTUM_VIEW_MATHEMATICAL_AUDIT.md`](QUANTUM_VIEW_MATHEMATICAL_AUDIT.md).

The pinned baseline is the exact head whose implementation and mathematical audit were checked. The review packet and trailing-whitespace cleanup are documentation-only successor changes. Before reviewing, confirm the current PR head and inspect the diff from the pinned baseline; if any executable code or mathematical claim changed, stop and agree a new pin.

## Scope and assumptions

Please review only the finite-dimensional `e7q.quantum-view/0alpha1` proposal:

- Hilbert space is exactly \(\mathbb C^2\); \(X,Y,Z\) are the standard Pauli matrices with outcomes \(\pm1\).
- States are Hermitian positive semidefinite 2×2 matrices of trace one. Probabilities are Born probabilities for the projectors \(P_{n,s}=(I+s n)/2\).
- The example uses \(\rho_\pm=(I\pm Y/2)/2\). Its fibres are over explicitly supplied finite state and preparation tuples, not unrestricted sets.
- Joint-device claims concern unbiased binary effects \(E^X_x=(I+x\eta X)/2\), \(E^Z_z=(I+z\eta Z)/2\), and four positive parent effects \(G_{xz}\) summing to \(I\) with those marginals.

The audit does not claim a general POVM compatibility theorem, continuous-variable result, physical measurement, or product adoption.

## Derivations to examine

### Sharp X/Z obstruction

For rank-one sharp projectors \(P^X_x=(I+xX)/2\) and \(P^Z_z=(I+zZ)/2\), the audit calculates

\[
\operatorname{Tr}(P^X_xP^Z_z)=\tfrac14\operatorname{Tr}(I+xX+zZ+xzXZ)=\tfrac12.
\]

If a positive parent existed, its effects would satisfy \(0\preceq G_{xz}\preceq P^X_x\) and \(0\preceq G_{xz}\preceq P^Z_z\). For positive operators, \(0\preceq A\preceq P\) with projector \(P\) implies \(\operatorname{ran}(A)\subseteq\operatorname{ran}(P)\): vectors in \(\ker P\) have zero quadratic form under \(A\), hence are annihilated by \(A^{1/2}\) and by \(A\). The X and Z rank-one ranges have overlap squared 1/2, so are distinct and intersect only at zero. Each \(G_{xz}\) must therefore vanish, contradicting \(\sum G_{xz}=I\).

The adapter checks the exact overlap data and certificate fields. It does **not** formally prove the support/range lemma; assess the written argument independently.

### Unsharp parent at \(\eta=1/2\)

The proposed effects are

\[
G_{xz}=\tfrac14(I+x\eta X+z\eta Z),\quad x,z\in\{\pm1\}.
\]

For \(\eta=1/2\), the matrix diagonals are 1/8 and 3/8, each determinant is 1/32, and each effect is positive. Their sum is \(I\); summing over \(z\) gives \((I+xX/2)/2\), and summing over \(x\) gives \((I+zZ/2)/2\). Exact rational calculations are in `math_audit_calculations.json`; an independent Python `Fraction` script imports no adapter code.

## Questions for the reviewer

1. Are the observable, state, outcome, and parent-POVM definitions appropriate for the intended bounded claim? Identify any unstated convention that changes it.
2. Do the density-operator eigenvalues and X/Y/Z Born distributions follow under these conventions? Are the state and preparation-description fibres correctly distinguished and limited to their supplied finite domains?
3. Is the implication \(0\preceq A\preceq P\Rightarrow\operatorname{ran}(A)\subseteq\operatorname{ran}(P)\) correctly applied here? Does the overlap calculation establish the required zero intersections and sharp-pair obstruction?
4. Are all four proposed \(\eta=1/2\) effects positive, normalized, and equal to the declared X/Z marginals? Is any assumption missing from the construction?
5. Do `incompatible`, `success`, `undetermined`, and `unsupported` say no more than the derivations and implemented checks warrant? Give a counterexample if not.
6. Are there additional boundary or adversarial cases that invalidate any bounded claim? State the exact assumptions/domain and the smallest useful correction.

## Reproduction

From the E7Q checkout at the pinned or confirmed documentation-only successor head, run:

    python scripts/audit_quantum_view_math.py
    PYTHONPATH=src python -m pytest tests/test_quantum_view_v0alpha1.py tests/test_review_campaign.py -q

The NumPy calculation is a secondary floating-point cross-check, not a proof. Please return a verdict, line-specific findings, reasoning, and any domain/expertise limitations. Do not characterize the whole package as “physics reviewed” based on this bounded review.
