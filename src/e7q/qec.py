# SPDX-License-Identifier: Apache-2.0
"""Small, auditable stabilizer-syndrome pilot for E7Q.

The representation is phase-insensitive: Pauli strings are considered modulo
the center of the Pauli group and are ordered from q[0] to q[n-1].
"""
from __future__ import annotations

from dataclasses import dataclass
import json


class QECError(ValueError):
    """Raised when a QEC pilot input is invalid."""


_PAULI_TO_BITS = {
    "I": (0, 0),
    "X": (1, 0),
    "Y": (1, 1),
    "Z": (0, 1),
}
_BITS_TO_PAULI = {value: key for key, value in _PAULI_TO_BITS.items()}
_BOUNDARY = (
    "Phase-insensitive stabilizer algebra and state-vector reference-circuit "
    "evidence only; no hardware execution, decoder performance, physical "
    "fidelity, fault-tolerance threshold, or new QEC theorem is established."
)


def _canonical_pauli(value: str, *, length: int | None = None) -> str:
    if not isinstance(value, str):
        raise QECError("Pauli operator must be a string")
    result = value.upper()
    if not result or any(symbol not in _PAULI_TO_BITS for symbol in result):
        raise QECError("Pauli operator must contain only I, X, Y, and Z")
    if length is not None and len(result) != length:
        raise QECError(f"Pauli operator must have length {length}")
    return result


def pauli_to_symplectic(pauli: str) -> tuple[int, ...]:
    """Return the binary ``(x | z)`` vector for a Pauli string."""
    canonical = _canonical_pauli(pauli)
    pairs = [_PAULI_TO_BITS[symbol] for symbol in canonical]
    return tuple(pair[0] for pair in pairs) + tuple(pair[1] for pair in pairs)


def symplectic_product(left: tuple[int, ...], right: tuple[int, ...]) -> int:
    """Return the binary commutation parity of two symplectic vectors."""
    if len(left) != len(right) or len(left) % 2:
        raise QECError("symplectic vectors must have equal even length")
    if any(value not in {0, 1} for value in left + right):
        raise QECError("symplectic vectors must be binary")
    size = len(left) // 2
    return sum(
        left[index] * right[size + index]
        + left[size + index] * right[index]
        for index in range(size)
    ) % 2


def multiply_paulis(left: str, right: str) -> str:
    """Multiply Pauli strings modulo global phase."""
    first = _canonical_pauli(left)
    second = _canonical_pauli(right, length=len(first))
    product = []
    for a, b in zip(first, second):
        ax, az = _PAULI_TO_BITS[a]
        bx, bz = _PAULI_TO_BITS[b]
        product.append(_BITS_TO_PAULI[(ax ^ bx, az ^ bz)])
    return "".join(product)


def _gf2_rank(rows: list[tuple[int, ...]]) -> int:
    if not rows:
        return 0
    width = len(rows[0])
    matrix = [list(row) for row in rows]
    rank = 0
    for column in range(width):
        pivot = next(
            (index for index in range(rank, len(matrix)) if matrix[index][column]),
            None,
        )
        if pivot is None:
            continue
        matrix[rank], matrix[pivot] = matrix[pivot], matrix[rank]
        for index in range(len(matrix)):
            if index != rank and matrix[index][column]:
                matrix[index] = [
                    left ^ right
                    for left, right in zip(matrix[index], matrix[rank])
                ]
        rank += 1
    return rank


@dataclass(frozen=True)
class StabilizerCode:
    """Validated phase-insensitive stabilizer generators."""

    name: str
    generators: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise QECError("stabilizer code name must not be empty")
        if not self.generators:
            raise QECError("at least one stabilizer generator is required")
        canonical = tuple(_canonical_pauli(item) for item in self.generators)
        size = len(canonical[0])
        canonical = tuple(_canonical_pauli(item, length=size) for item in canonical)
        if any(set(item) == {"I"} for item in canonical):
            raise QECError("identity is not an independent generator")
        vectors = [pauli_to_symplectic(item) for item in canonical]
        for index, left in enumerate(vectors):
            for right in vectors[index + 1:]:
                if symplectic_product(left, right):
                    raise QECError("stabilizer generators must commute")
        if _gf2_rank(vectors) != len(vectors):
            raise QECError("stabilizer generators must be independent over F2")
        object.__setattr__(self, "generators", canonical)

    @property
    def qubits(self) -> int:
        return len(self.generators[0])


def syndrome(code: StabilizerCode, error: str) -> tuple[int, ...]:
    """Return ordered anticommutation bits, one per generator."""
    vector = pauli_to_symplectic(_canonical_pauli(error, length=code.qubits))
    return tuple(
        symplectic_product(pauli_to_symplectic(generator), vector)
        for generator in code.generators
    )


def in_stabilizer(code: StabilizerCode, pauli: str) -> bool:
    """Return whether a Pauli is in the generator span, modulo phase."""
    vector = pauli_to_symplectic(_canonical_pauli(pauli, length=code.qubits))
    rows = [pauli_to_symplectic(item) for item in code.generators]
    return _gf2_rank(rows) == _gf2_rank(rows + [vector])


def analyze_error(code: StabilizerCode, error: str) -> dict[str, object]:
    """Classify an error using its syndrome and stabilizer membership."""
    canonical = _canonical_pauli(error, length=code.qubits)
    bits = syndrome(code, canonical)
    zero = not any(bits)
    stabilizer_member = in_stabilizer(code, canonical)
    classification = (
        "detectable" if not zero else "stabilizer" if stabilizer_member else "logical"
    )
    return {
        "schema": "e7q.qec-error-analysis/v1alpha1",
        "code": {
            "name": code.name,
            "qubits": code.qubits,
            "generators": list(code.generators),
            "syndrome_order": list(code.generators),
        },
        "error": canonical,
        "is_identity": set(canonical) == {"I"},
        "syndrome": list(bits),
        "zero_syndrome": zero,
        "normalizer_member": zero,
        "stabilizer_member": stabilizer_member,
        "classification": classification,
        "projection": {
            "source": "phase-insensitive Pauli operator",
            "view": "ordered stabilizer-commutation bits",
            "preserved": "commutation parity with each declared generator",
            "hidden": ["global phase", "operator identity within a syndrome class"],
        },
        "boundary": _BOUNDARY,
    }


def syndrome_homomorphism_report(
    code: StabilizerCode, left: str, right: str
) -> dict[str, object]:
    """Produce an auditable report for ``sigma(EF)=sigma(E) xor sigma(F)``."""
    first = _canonical_pauli(left, length=code.qubits)
    second = _canonical_pauli(right, length=code.qubits)
    product = multiply_paulis(first, second)
    left_bits = syndrome(code, first)
    right_bits = syndrome(code, second)
    product_bits = syndrome(code, product)
    expected = tuple(a ^ b for a, b in zip(left_bits, right_bits))
    passed = product_bits == expected
    return {
        "schema": "e7q.qec-syndrome-homomorphism/v1alpha1",
        "status": "PASS" if passed else "FAIL",
        "claim": "sigma(EF) = sigma(E) xor sigma(F)",
        "code": {
            "name": code.name,
            "qubits": code.qubits,
            "generators": list(code.generators),
            "syndrome_order": list(code.generators),
        },
        "operators": {"left": first, "right": second, "product": product},
        "syndromes": {
            "left": list(left_bits),
            "right": list(right_bits),
            "product": list(product_bits),
            "left_xor_right": list(expected),
        },
        "passed": passed,
        "assumptions": [
            "Pauli operators are represented modulo global phase.",
            "Syndrome bits are ordered exactly as the declared generators.",
            "Each syndrome bit records commutation parity over F2.",
        ],
        "boundary": _BOUNDARY,
    }


def qec_proof_json(report: dict[str, object]) -> str:
    """Serialize a QEC pilot report deterministically."""
    return json.dumps(report, indent=2, sort_keys=True) + "\n"
