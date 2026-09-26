# Bounded quantum-view mathematics audit

**Subject:** E7Q PR #81, bounded adapter `e7q.quantum-view/0alpha1`  
**Audited source head:** `fe1795bfcdd072e41e02b193da6724df14474ff9`  
**Audit result:** the stated finite-qubit fixture calculations are correct under the assumptions below. One result-path under-report and one proof-wording overstatement were corrected in the successor head. This record is a bounded mathematical audit; it does not certify the package as “physics reviewed.”

## Assumptions and domain

1. The Hilbert space is exactly \(\mathbb C^2\). The matrices \(X,Y,Z\) are the standard Pauli matrices, with eigenvalues \(\pm1\).
2. A state is a Hermitian positive semidefinite \(2\times2\) matrix of trace one. Outcome distributions use the Born rule and projective effects \(P_{n,s}=(I+s n)/2\) for \(s\in\{+1,-1\}\) and \(n\in\{X,Y,Z\}\).
3. \(\rho_\pm=(I\pm aY)/2\) uses the declared \(a=1/2\). The construction admits \(0\le a\le1\); it is not a statement about arbitrary qubit states.
4. A reconstruction fibre is relative to the finite tuple explicitly supplied to the function. The state fibre is a set of distinct matrix values from that tuple. The preparation-description fibre is a set of matching descriptions and preserves aliases. Neither API computes an unrestricted fibre over all possible density operators or preparations.
5. Joint-device claims concern unbiased binary Pauli observables \(E^X_x=(I+x\eta X)/2\) and \(E^Z_z=(I+z\eta Z)/2\), with \(0\le\eta\le1\). A parent is a four-effect POVM \(G_{xz}\succeq0\) summing to \(I\), with the stated X and Z marginals.

## Independent exact derivation: states and distributions

Write a qubit state as \(\rho(r)=(I+r_xX+r_yY+r_zZ)/2\). The Pauli trace identities are \(\operatorname{Tr}(I)=2\), \(\operatorname{Tr}(\sigma_i)=0\), and \(\operatorname{Tr}(\sigma_i\sigma_j)=2\delta_{ij}\). They imply

\[
\operatorname{Tr}\bigl(\rho(r)P_{n,s}\bigr)=\frac{1+s\,r\cdot n}{2}.
\]

Here \(r_+=(0,1/2,0)\), \(r_-=(0,-1/2,0)\). The eigenvalues of each density operator are \((1+|r|)/2=3/4\) and \((1-|r|)/2=1/4\); each has trace one and is positive. Substitution gives:

| State | X: \((p_+,p_-)\) | Y: \((p_+,p_-)\) | Z: \((p_+,p_-)\) |
|---|---|---|---|
| \(\rho_+\) | \((1/2,1/2)\) | \((3/4,1/4)\) | \((1/2,1/2)\) |
| \(\rho_-\) | \((1/2,1/2)\) | \((1/4,3/4)\) | \((1/2,1/2)\) |

Thus the selected X/Z views are equal and the Y distributions differ. These are distributions for separate identically prepared runs per context; they do not predict an individual physical run record.

### Independent calculation artifact

[`scripts/audit_quantum_view_math.py`](../../scripts/audit_quantum_view_math.py) evaluates the Bloch trace identities and the parent matrix entries using only Python `Fraction`; it imports no adapter code. Its reproducible exact output is [`math_audit_calculations.json`](../../examples/quantum-view/v0alpha1/math_audit_calculations.json). The prior NumPy calculation remains a separate floating-point cross-check, not a proof.

## Reconstruction fibres

For the selected context tuple \((X,Z)\), both states in the admitted state tuple map to the same view. Therefore the state fibre over that supplied tuple has cardinality two: \((\rho_+,\rho_-)\). The preparation tuple contains `prep-plus` and `prep-plus-alias`, both naming \(\rho_+\), and `prep-minus`, naming \(\rho_-\); all three match, so the description fibre has cardinality three. This distinction is correct even if `prepare` is many-to-one.

Adversarial boundary checks:

- At \(a=0\), \(\rho_+=\rho_-=I/2\); the X/Z views still agree, but Y no longer differs. The adapter allows this endpoint, so the differing-Y claim is properly fixture-specific to \(a>0\).
- At \(a=1\), both are valid pure states; X/Z still agree and Y differs. At \(a>1\), an eigenvalue is negative and the constructor rejects the input.
- Repeating the same density matrix in the supplied state tuple is deduplicated by matrix equality; repeated distinct preparation descriptions remain distinct. An empty admitted tuple yields an empty fibre after the observation itself validates. None of this establishes a global, unbounded reconstruction set.
- An observed distribution with probability \(-1\) or \(2\), non-normalizing values, wrong outcome labels, or a context mismatch is invalid input; an unrecognized selected Pauli context is unsupported. These branches are input/domain classifications, not quantum-mechanical conclusions.

## Sharp X/Z obstruction

The sharp effects are rank-one projectors \(P^X_x=(I+xX)/2\) and \(P^Z_z=(I+zZ)/2\). For every sign pair,

\[
\operatorname{Tr}(P^X_xP^Z_z)=\frac14\operatorname{Tr}(I+xX+zZ+xzXZ)=\frac12,
\]

since the three non-identity terms have zero trace. For rank-one projectors this is \(|\langle x_X|z_Z\rangle|^2\); the value lies strictly between zero and one, so their one-dimensional ranges are distinct and have zero intersection.

Suppose a parent \(G_{xz}\succeq0\) existed. Positivity and the sharp marginals give

\[
0\preceq G_{xz}\preceq \sum_{z'}G_{xz'}=P^X_x,
\qquad
0\preceq G_{xz}\preceq \sum_{x'}G_{x'z}=P^Z_z.
\]

For positive operators, \(0\preceq A\preceq P\) implies \(\operatorname{ran}(A)\subseteq\operatorname{ran}(P)\): if \(v\in\ker P\), then \(0\le\langle v,Av\rangle\le0\), hence \(A^{1/2}v=0\) and \(Av=0\). Thus \(\operatorname{ran}(G_{xz})\) lies in both projector ranges. Their intersection is zero, so every \(G_{xz}=0\), contradicting \(\sum_{xz}G_{xz}=I\). Under assumptions 1, 2, and 5, sharp X/Z are incompatible.

**Verifier limit:** the adapter checks the certificate fields and the exact four overlap values. It does not formalize the positive-operator support lemma or the contradiction in a proof assistant. The `incompatible` outcome is justified by the written elementary derivation above plus the checked arithmetic, not by a machine-checked theorem. Successor wording was narrowed accordingly. Changing any overlap value or certificate descriptor makes the adapter certificate check fail; such a failed check means `undetermined`, not that a parent exists.

## The \(\eta=1/2\) parent POVM

Set

\[
G_{xz}=\frac14(I+x\eta X+z\eta Z),\qquad x,z\in\{\pm1\}.
\]

In the computational basis this is

\[
G_{xz}=\begin{pmatrix}(1+z\eta)/4&x\eta/4\\x\eta/4&(1-z\eta)/4\end{pmatrix}.
\]

For \(\eta=1/2\), the diagonal entries are \(1/8\) and \(3/8\), and every determinant is \((1-2\eta^2)/16=1/32\). A Hermitian \(2\times2\) matrix with nonnegative diagonal and determinant is positive semidefinite, so all four effects are positive. Equivalently their eigenvalues are \((1\pm1/\sqrt2)/4\), both nonnegative. Summing all four effects cancels the X and Z terms and gives \(I\). Summing over \(z\) gives \((I+xX/2)/2\); summing over \(x\) gives \((I+zZ/2)/2\). The advertised pair therefore has this verified parent.

The same formula has determinant \((1-2\eta^2)/16\). For \(\eta=3/5\), it is positive, so the formula also constructs a parent, although #81 does not advertise or return a general-eta witness. For \(\eta=3/4\), this proposed formula is not positive. That failure alone proves nothing about other possible parents; #81 correctly returns `undetermined` there rather than `incompatible`. At \(\eta=0\), a trivial parent \(G_{xz}=I/4\) exists, but the current adapter also returns `undetermined`: conservative incompleteness, not a false incompatibility claim. The current adapter's positive compatibility claim remains restricted to its checked \(\eta=1/2\) construction.

The candidate-parent path was checked adversarially. A valid normalized positive POVM with the wrong marginals is not itself an obstruction. At \(\eta=1\), the independent sharp-pair argument still justifies `incompatible`. At \(\eta=1/2\), the successor now reports the separately constructed and checked parent rather than suppressing that known witness with `undetermined`. For other eta values, a mismatched candidate is not enough to determine compatibility, so the result remains `undetermined`.

## Result-label audit

| Result | What the bounded derivation supports | Boundary |
|---|---|---|
| `incompatible` | Sharp unbiased Pauli X/Z at \(\eta=1\), from the support-intersection argument above | Not a machine-checked proof; no general incompatible-pair solver |
| `success` for a parent | An explicitly provided or constructed four-effect matrix passed exact positivity, normalization, and both target-marginal checks | Establishes a witness for that pair, not a characterization of all compatible pairs |
| `undetermined` | No implemented/checkable witness or obstruction is returned for that requested case | Does not mean incompatible; examples \(\eta=0\) and \(\eta=3/5\) are compatible by the elementary witnesses/formula above but remain outside current advertised implementation coverage |
| `unsupported` | A requested measurement context is outside the implemented Pauli set \(\{X,Y,Z\}\) | Does not assert that the context is physically impossible or mathematically undefined |

`invalid_input` and `resource_limit` are operational adapter statuses, not physical conclusions. The documented resource budget counts fixed Born-work units and does not bound rational bit growth or wall time.

## Findings and remaining external review

1. The declared density matrices, exact X/Y/Z distributions, finite supplied-domain fibres, sharp X/Z incompatibility, and \(\eta=1/2\) parent claim are mathematically consistent under the assumptions stated here.
2. The code's sharp certificate checker checks overlap arithmetic and identifiers, not the support-intersection lemma. The result reason, fixture summary, and README now state this boundary explicitly.
3. A mismatched but valid candidate at \(\eta=1/2\) previously hid the adapter's own known parent. The successor falls back to constructing and checking that parent; a regression test covers the path.
4. Independent exact rational output is saved and reproducible. This audit covers a finite qubit model only; it is not an endorsement of any E7Q product claim or a general quantum semantics.

**Specific outside review still required:** an independent mathematical-physics reviewer should assess the joint-measurability setup and the support/range lemma in the context of the intended quantum formalism, including whether the chosen observable/parent definitions match the intended use. Any extension to continuous-variable position/momentum claims requires a separate functional-analysis review of self-adjoint unbounded operators, domains, and the relevant POVM/uncertainty formulation. Any hardware or empirical measurement statement requires separate provider/laboratory evidence and provenance review. Until those reviews occur, call this a bounded exact-qubit mathematical audit, not “physics reviewed.”

## Reproduction

```sh
python scripts/audit_quantum_view_math.py
python scripts/quantum_view_numpy_check.py
PYTHONPATH=src python -m pytest tests/test_quantum_view_v0alpha1.py tests/test_review_campaign.py -q
```
