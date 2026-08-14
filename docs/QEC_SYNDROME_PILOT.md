# QEC syndrome-homomorphism pilot

**Profile:** `e7q.qec-syndrome-pilot/v1alpha1`

**Release:** E7Q 1.0.0-rc7

**Status:** experimental, independently reviewable software pilot

## Result in one line

For the three-qubit repetition code with ordered stabilizer generators
`(ZZI, IZZ)`, E7Q reproduces

\[
\sigma(EF)=\sigma(E)\oplus\sigma(F)
\]

for `E = XII`, `F = IXI`, and `EF = XXI`:

\[
(1,0)\oplus(1,1)=(0,1).
\]

This is a reproducibility pilot for standard stabilizer mathematics, not a new
quantum-error-correction theorem.

## Why the zero syndrome matters

The syndrome is a projection: it preserves commutation parity with each
declared generator, but it does not identify the Pauli operator. The pilot
makes that loss visible:

| Pauli | Syndrome `(ZZI, IZZ)` | Pilot classification | Meaning here |
| --- | --- | --- | --- |
| `III` | `00` | stabilizer | identity, the empty stabilizer product |
| `XII` | `10` | detectable | anticommutes with `ZZI` |
| `IXI` | `11` | detectable | anticommutes with both generators |
| `XXI` | `01` | detectable | product of the preceding two errors |
| `ZZI` | `00` | stabilizer | acts trivially on the code space |
| `XXX` | `00` | logical | normalizer member outside the stabilizer |

Thus zero syndrome does not mean “no error.” It contains the stabilizer and
also undetectable logical Pauli operators. In the phase-insensitive Pauli
representation used here, the kernel of the syndrome map is the stabilizer
normalizer/centralizer.

## Reproduce it

Install the checkout, then produce a deterministic JSON report:

```bash
python -m pip install -e ".[test]"

e7q qec-homomorphism XII IXI \
  --generator ZZI \
  --generator IZZ \
  --name "three-qubit repetition code" \
  -o syndrome-homomorphism.json
```

Inspect one operator independently:

```bash
e7q qec-syndrome XXX \
  --generator ZZI \
  --generator IZZ
```

Run the dependency-free reference checker, which does not import the E7Q QEC
module:

```bash
python pilots/qec_syndrome/reference_checker.py
```

Run all reference circuits and regression tests:

```bash
pytest -q tests/test_qec_syndrome_pilot.py
```

The six files under [`examples/qec-syndrome/`](../examples/qec-syndrome/)
insert explicit Pauli gates, extract the two syndrome bits with ancillas, and
assert both syndrome and data-register outcomes. The committed
[`expected_results.json`](../pilots/qec_syndrome/expected_results.json) is the
machine-readable oracle.

## Mathematical convention

An `n`-qubit Pauli is represented modulo global phase by a binary vector
`(x | z)` in `F2^(2n)`. A syndrome bit is the symplectic product of the error
vector with one stabilizer-generator vector. Bilinearity over `F2` gives the
homomorphism law.

Generators are rejected unless they are non-identity, equal-width, mutually
commuting, and linearly independent over `F2`. Syndrome bits follow the exact
order supplied by the caller.

The example is the three-qubit repetition code under a **restricted X-error
model**. It must not be presented as a code that corrects every arbitrary
single-qubit Pauli error.

## Evidence boundary

The pilot establishes tested behavior of phase-insensitive stabilizer algebra
and small state-vector reference circuits. It does not establish hardware
execution, provider authenticity, decoder performance, physical fidelity, a
fault-tolerance threshold, a surface-code result, or a new QEC theorem.

The pilot was prompted by a public discussion of why QEC syndromes add modulo
two. Independent mathematical review of this E7Q implementation remains
welcome and is not claimed by the release.
