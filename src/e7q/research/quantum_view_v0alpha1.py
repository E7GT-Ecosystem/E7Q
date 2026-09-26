# SPDX-License-Identifier: Apache-2.0
"""Opt-in exact qubit quantum-view adapter, version 0alpha1.

This bounded research adapter computes Born distributions for exact 2x2 density
operators and verifies only the declared Pauli X/Z joint-device fixtures. It is
not an E7Q-IR execution profile, a physical measurement system, or a general
POVM compatibility solver.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
import random
from typing import Generic, TypeVar

PROFILE_ID = "e7q.quantum-view/0alpha1"


class Status(str, Enum):
    SUCCESS = "success"
    INCOMPATIBLE = "incompatible"
    INVALID_INPUT = "invalid_input"
    UNSUPPORTED = "unsupported"
    UNDETERMINED = "undetermined"
    RESOURCE_LIMIT = "resource_limit"


T = TypeVar("T")


@dataclass(frozen=True)
class Result(Generic[T]):
    status: Status
    value: T | None = None
    reason: str | None = None
    operations: int = 0


@dataclass(frozen=True)
class ResourcePolicy:
    """Bounds adapter-accounted Born work units, not Fraction bit complexity.

    Each requested state/context Born distribution is charged 12 fixed work
    units. Aggregate views and fibres preflight their full charge. Python's
    arbitrary-precision rational arithmetic is exact; numerator/denominator
    bit growth is outside this accounting measure.
    """
    max_operations: int = 128


@dataclass(frozen=True)
class GaussianRational:
    """Exact complex number whose real and imaginary parts are Fractions."""

    real: Fraction = Fraction(0)
    imag: Fraction = Fraction(0)

    def __post_init__(self) -> None:
        object.__setattr__(self, "real", _fraction(self.real))
        object.__setattr__(self, "imag", _fraction(self.imag))

    def __add__(self, other: GaussianRational | Fraction | int) -> GaussianRational:
        rhs = _gc(other)
        return GaussianRational(self.real + rhs.real, self.imag + rhs.imag)

    def __radd__(self, other: GaussianRational | Fraction | int) -> GaussianRational:
        return self + other

    def __neg__(self) -> GaussianRational:
        return GaussianRational(-self.real, -self.imag)

    def __sub__(self, other: GaussianRational | Fraction | int) -> GaussianRational:
        return self + (-_gc(other))

    def __mul__(self, other: GaussianRational | Fraction | int) -> GaussianRational:
        rhs = _gc(other)
        return GaussianRational(
            self.real * rhs.real - self.imag * rhs.imag,
            self.real * rhs.imag + self.imag * rhs.real,
        )

    def __rmul__(self, other: GaussianRational | Fraction | int) -> GaussianRational:
        return self * other

    def __truediv__(self, other: Fraction | int) -> GaussianRational:
        divisor = _fraction(other)
        if divisor == 0:
            raise ZeroDivisionError
        return GaussianRational(self.real / divisor, self.imag / divisor)

    def conjugate(self) -> GaussianRational:
        return GaussianRational(self.real, -self.imag)


def _fraction(value: Fraction | int) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (int, Fraction)):
        raise TypeError("exact rational input must be int or fractions.Fraction")
    return value if isinstance(value, Fraction) else Fraction(value)


def _gc(value: GaussianRational | Fraction | int) -> GaussianRational:
    if isinstance(value, GaussianRational):
        return value
    return GaussianRational(_fraction(value), Fraction(0))


@dataclass(frozen=True)
class Matrix2:
    entries: tuple[tuple[GaussianRational, GaussianRational], tuple[GaussianRational, GaussianRational]]


@dataclass(frozen=True)
class DensityOperator:
    matrix: Matrix2


@dataclass(frozen=True)
class PredictedDistribution:
    """Born-rule probabilities; never an actual run result."""

    axis: str
    probabilities: tuple[tuple[int, Fraction], tuple[int, Fraction]]

    def as_mapping(self) -> dict[int, Fraction]:
        return dict(self.probabilities)


@dataclass(frozen=True)
class PreparationDescription:
    description_id: str
    state: DensityOperator


@dataclass(frozen=True)
class PhysicalOutcomeRecord:
    """Imported physical observation. Construction does not imply validation."""

    record_id: str
    run_id: str
    preparation_id: str
    axis: str
    outcome: int
    source_id: str
    provenance: str


@dataclass(frozen=True)
class ValidatedPhysicalOutcome:
    record: PhysicalOutcomeRecord
    validation: str = "record-shape-context-outcome-validated-only"


@dataclass(frozen=True)
class SimulatedOutcomeRecord:
    """Seeded model sample; explicitly not a physical measurement record."""

    axis: str
    outcome: int
    seed: int
    simulator_id: str
    source_distribution: PredictedDistribution
    record_kind: str = "simulated"


@dataclass(frozen=True)
class SharpXZObstructionCertificate:
    certificate_id: str
    pair: tuple[str, str]
    overlap_squared_by_sign: tuple[tuple[int, int, Fraction], ...]
    lemma: str
    conclusion: str


@dataclass(frozen=True)
class VerifiedParentPOVM:
    eta: Fraction
    effects: tuple[tuple[int, int, Matrix2], ...]
    positivity_checked: bool
    normalization_checked: bool
    x_marginals_checked: bool
    z_marginals_checked: bool


def _matrix(rows: tuple[tuple[GaussianRational | Fraction | int, ...], ...]) -> Matrix2:
    if len(rows) != 2 or any(len(row) != 2 for row in rows):
        raise ValueError("qubit matrices must be 2 by 2")
    return Matrix2(tuple(tuple(_gc(v) for v in row) for row in rows))  # type: ignore[arg-type]


ZERO = GaussianRational()
ONE = GaussianRational(Fraction(1))
I2 = _matrix(((1, 0), (0, 1)))
PAULI = {
    "X": _matrix(((0, 1), (1, 0))),
    "Y": _matrix(((0, GaussianRational(Fraction(0), Fraction(-1))),
                   (GaussianRational(Fraction(0), Fraction(1)), 0))),
    "Z": _matrix(((1, 0), (0, -1))),
}


def _add(a: Matrix2, b: Matrix2) -> Matrix2:
    return _matrix(tuple(tuple(a.entries[i][j] + b.entries[i][j] for j in range(2)) for i in range(2)))


def _scale(k: Fraction | int, a: Matrix2) -> Matrix2:
    scalar = _fraction(k)
    return _matrix(tuple(tuple(scalar * a.entries[i][j] for j in range(2)) for i in range(2)))


def _mul(a: Matrix2, b: Matrix2) -> Matrix2:
    return _matrix(tuple(tuple(sum((a.entries[i][k] * b.entries[k][j] for k in range(2)), ZERO) for j in range(2)) for i in range(2)))


def _trace(a: Matrix2) -> GaussianRational:
    return a.entries[0][0] + a.entries[1][1]


def _det_real_if_hermitian(a: Matrix2) -> Fraction:
    off = a.entries[0][1]
    return a.entries[0][0].real * a.entries[1][1].real - off.real * off.real - off.imag * off.imag


def _is_hermitian(a: Matrix2) -> bool:
    return (
        a.entries[0][0].imag == 0
        and a.entries[1][1].imag == 0
        and a.entries[1][0] == a.entries[0][1].conjugate()
    )


def _positive_semidefinite(a: Matrix2) -> bool:
    return (
        _is_hermitian(a)
        and a.entries[0][0].real >= 0
        and a.entries[1][1].real >= 0
        and _det_real_if_hermitian(a) >= 0
    )


def _matrix_well_formed(matrix: object) -> bool:
    return (
        isinstance(matrix, Matrix2)
        and isinstance(matrix.entries, tuple)
        and len(matrix.entries) == 2
        and all(isinstance(row, tuple) and len(row) == 2 for row in matrix.entries)
        and all(isinstance(value, GaussianRational) for row in matrix.entries for value in row)
    )


def _valid_density(state: DensityOperator) -> bool:
    if not isinstance(state, DensityOperator) or not _matrix_well_formed(state.matrix):
        return False
    tr = _trace(state.matrix)
    return tr == ONE and _positive_semidefinite(state.matrix)


def _valid_resource_policy(policy: ResourcePolicy) -> bool:
    return (
        isinstance(policy, ResourcePolicy)
        and type(policy.max_operations) is int
        and policy.max_operations >= 0
    )


def _validate_observed_view(
    axes: tuple[str, ...], observed: tuple[PredictedDistribution, ...]
) -> Result[None]:
    if not isinstance(axes, tuple) or not axes or any(not isinstance(axis, str) for axis in axes):
        return Result(Status.INVALID_INPUT, reason="axes must be a non-empty tuple of context names")
    if any(axis not in PAULI for axis in axes):
        unsupported = next(axis for axis in axes if axis not in PAULI)
        return Result(Status.UNSUPPORTED, reason=f"unsupported Pauli context: {unsupported!r}")
    if not isinstance(observed, tuple) or len(axes) != len(observed):
        return Result(Status.INVALID_INPUT, reason="observed view must contain one distribution per selected context")
    for axis, item in zip(axes, observed):
        if not isinstance(item, PredictedDistribution) or item.axis != axis:
            return Result(Status.INVALID_INPUT, reason="observed distribution context does not match the selected context")
        probabilities = item.probabilities
        if (
            not isinstance(probabilities, tuple)
            or len(probabilities) != 2
            or any(not isinstance(pair, tuple) or len(pair) != 2 for pair in probabilities)
        ):
            return Result(Status.INVALID_INPUT, reason="observed probabilities must contain two outcome/probability pairs")
        if (
            tuple(label for label, _ in probabilities) != (1, -1)
            or any(type(label) is not int or type(probability) is not Fraction for label, probability in probabilities)
            or any(not 0 <= probability <= 1 for _, probability in probabilities)
            or sum((probability for _, probability in probabilities), Fraction(0)) != 1
        ):
            return Result(Status.INVALID_INPUT, reason="observed probabilities must be exact, normalized values for outcomes +1 and -1")
    return Result(Status.SUCCESS)


def density_from_bloch_y(sign: int, a: Fraction = Fraction(1, 2)) -> DensityOperator:
    """Construct rho=(I+sign*a*Y)/2, exactly; `sign` must be +/-1."""
    if type(sign) is not int or sign not in {-1, 1}:
        raise ValueError("sign must be exactly -1 or +1")
    a = _fraction(a)
    if not 0 <= a <= 1:
        raise ValueError("a must be in [0, 1]")
    return DensityOperator(_scale(Fraction(1, 2), _add(I2, _scale(sign * a, PAULI["Y"]))))


def effect(axis: str, outcome: int, eta: Fraction = Fraction(1)) -> Result[Matrix2]:
    if not isinstance(axis, str):
        return Result(Status.INVALID_INPUT, reason="context axis must be text")
    if axis not in PAULI:
        return Result(Status.UNSUPPORTED, reason=f"unsupported Pauli context: {axis!r}")
    if type(outcome) is not int or outcome not in {-1, 1}:
        return Result(Status.INVALID_INPUT, reason="outcome must be exactly -1 or +1")
    try:
        eta = _fraction(eta)
    except TypeError as exc:
        return Result(Status.INVALID_INPUT, reason=str(exc))
    if not 0 <= eta <= 1:
        return Result(Status.INVALID_INPUT, reason="eta must be in [0, 1]")
    return Result(Status.SUCCESS, _scale(Fraction(1, 2), _add(I2, _scale(outcome * eta, PAULI[axis]))))


def born_distribution(
    state: DensityOperator,
    axis: str,
    policy: ResourcePolicy = ResourcePolicy(),
) -> Result[PredictedDistribution]:
    required = 12
    if not _valid_resource_policy(policy):
        return Result(Status.INVALID_INPUT, reason="invalid resource policy")
    if policy.max_operations < required:
        return Result(Status.RESOURCE_LIMIT, reason=f"requires {required} bounded matrix operations", operations=policy.max_operations)
    if not isinstance(axis, str):
        return Result(Status.INVALID_INPUT, reason="context axis must be text", operations=0)
    if axis not in PAULI:
        return Result(Status.UNSUPPORTED, reason=f"unsupported Pauli context: {axis!r}", operations=0)
    if not _valid_density(state):
        return Result(Status.INVALID_INPUT, reason="state is not a positive trace-one qubit density operator", operations=0)
    values: list[tuple[int, Fraction]] = []
    for outcome in (1, -1):
        e = effect(axis, outcome)
        assert e.status is Status.SUCCESS and e.value is not None
        probability = _trace(_mul(state.matrix, e.value))
        if probability.imag != 0 or not 0 <= probability.real <= 1:
            return Result(Status.INVALID_INPUT, reason="Born expression is not a probability", operations=required)
        values.append((outcome, probability.real))
    if sum((p for _, p in values), Fraction(0)) != 1:
        return Result(Status.INVALID_INPUT, reason="Born distribution does not normalize", operations=required)
    return Result(Status.SUCCESS, PredictedDistribution(axis, tuple(values)), operations=required)  # type: ignore[arg-type]


def view(
    state: DensityOperator,
    axes: tuple[str, ...] = ("X", "Z"),
    policy: ResourcePolicy = ResourcePolicy(),
) -> Result[tuple[PredictedDistribution, ...]]:
    if not _valid_resource_policy(policy):
        return Result(Status.INVALID_INPUT, reason="invalid resource policy")
    if not isinstance(state, DensityOperator) or not _valid_density(state):
        return Result(Status.INVALID_INPUT, reason="invalid density operator")
    if not isinstance(axes, tuple) or not axes or any(not isinstance(axis, str) for axis in axes):
        return Result(Status.INVALID_INPUT, reason="axes must be a non-empty tuple of context names")
    unsupported_axes = tuple(axis for axis in axes if axis not in PAULI)
    if unsupported_axes:
        return Result(Status.UNSUPPORTED, reason=f"unsupported Pauli context: {unsupported_axes[0]!r}")
    required = 12 * len(axes)
    if required > policy.max_operations:
        return Result(Status.RESOURCE_LIMIT, reason=f"view requires {required} accounted Born work units", operations=0)
    distributions: list[PredictedDistribution] = []
    for axis in axes:
        result = born_distribution(state, axis, policy)
        if result.status is not Status.SUCCESS or result.value is None:
            return Result(result.status, reason=result.reason, operations=result.operations)
        distributions.append(result.value)
    return Result(Status.SUCCESS, tuple(distributions), operations=required)


def state_fibre(
    states: tuple[DensityOperator, ...], axes: tuple[str, ...], observed: tuple[PredictedDistribution, ...],
    policy: ResourcePolicy = ResourcePolicy(),
) -> Result[tuple[DensityOperator, ...]]:
    """Distinct admitted density operators matching the selected distributions."""
    if (
        not isinstance(states, tuple)
        or any(not isinstance(state, DensityOperator) or not _valid_density(state) for state in states)
        or not _valid_resource_policy(policy)
    ):
        return Result(Status.INVALID_INPUT, reason="states, contexts, and observed views must be well-formed tuples")
    observed_check = _validate_observed_view(axes, observed)
    if observed_check.status is not Status.SUCCESS:
        return Result(observed_check.status, reason=observed_check.reason)
    required = 12 * len(states) * len(axes)
    if required > policy.max_operations:
        return Result(Status.RESOURCE_LIMIT, reason=f"state fibre requires {required} accounted Born work units", operations=0)
    matches: list[DensityOperator] = []
    for state in states:
        candidate = view(state, axes, policy)
        if candidate.status is not Status.SUCCESS or candidate.value is None:
            return Result(candidate.status, reason=candidate.reason, operations=candidate.operations)
        if candidate.value == observed:
            if state not in matches:
                matches.append(state)
    return Result(Status.SUCCESS, tuple(matches), operations=required)


def preparation_description_fibre(
    descriptions: tuple[PreparationDescription, ...], axes: tuple[str, ...], observed: tuple[PredictedDistribution, ...],
    policy: ResourcePolicy = ResourcePolicy(),
) -> Result[tuple[PreparationDescription, ...]]:
    """Preparation descriptions matching a view; aliases remain distinct."""
    if (
        not isinstance(descriptions, tuple)
        or any(not isinstance(d, PreparationDescription) or not _valid_density(d.state) for d in descriptions)
        or not _valid_resource_policy(policy)
    ):
        return Result(Status.INVALID_INPUT, reason="descriptions, contexts, and observed views must be well-formed tuples")
    observed_check = _validate_observed_view(axes, observed)
    if observed_check.status is not Status.SUCCESS:
        return Result(observed_check.status, reason=observed_check.reason)
    required = 12 * len(descriptions) * len(axes)
    if required > policy.max_operations:
        return Result(Status.RESOURCE_LIMIT, reason=f"preparation-description fibre requires {required} accounted Born work units", operations=0)
    matches: list[PreparationDescription] = []
    for description in descriptions:
        candidate = view(description.state, axes, policy)
        if candidate.status is not Status.SUCCESS or candidate.value is None:
            return Result(candidate.status, reason=candidate.reason, operations=candidate.operations)
        if candidate.value == observed:
            matches.append(description)
    return Result(Status.SUCCESS, tuple(matches), operations=required)


def import_physical_record(record: PhysicalOutcomeRecord) -> Result[ValidatedPhysicalOutcome]:
    """Validate imported record metadata only; no outcome is inferred from rho."""
    if not isinstance(record, PhysicalOutcomeRecord):
        return Result(Status.INVALID_INPUT, reason="expected an imported PhysicalOutcomeRecord")
    if not all(isinstance(x, str) and x.strip() for x in (record.record_id, record.run_id, record.preparation_id, record.source_id, record.provenance)):
        return Result(Status.INVALID_INPUT, reason="physical record requires non-empty provenance and identity fields")
    if not isinstance(record.axis, str):
        return Result(Status.INVALID_INPUT, reason="physical record context must be text")
    if record.axis not in PAULI:
        return Result(Status.UNSUPPORTED, reason=f"unsupported context: {record.axis!r}")
    if type(record.outcome) is not int or record.outcome not in {-1, 1}:
        return Result(Status.INVALID_INPUT, reason="physical outcome must be exactly -1 or +1")
    return Result(Status.SUCCESS, ValidatedPhysicalOutcome(record))


def simulate_outcome(state: DensityOperator, axis: str, seed: int, simulator_id: str) -> Result[SimulatedOutcomeRecord]:
    """Seeded pseudo-random model sample; it is not a physical record."""
    if type(seed) is not int or not isinstance(simulator_id, str) or not simulator_id.strip():
        return Result(Status.INVALID_INPUT, reason="simulation needs an integer seed and simulator id")
    predicted = born_distribution(state, axis)
    if predicted.status is not Status.SUCCESS or predicted.value is None:
        return Result(predicted.status, reason=predicted.reason, operations=predicted.operations)
    # Draw an exactly represented 53-bit uniform variate; this is simulation only.
    threshold = random.Random(seed).getrandbits(53)
    p_plus = predicted.value.as_mapping()[1]
    outcome = 1 if threshold * p_plus.denominator < p_plus.numerator * (1 << 53) else -1
    return Result(Status.SUCCESS, SimulatedOutcomeRecord(axis, outcome, seed, simulator_id, predicted.value), operations=predicted.operations)


def _sharp_projector(axis: str, sign: int) -> Matrix2:
    return _scale(Fraction(1, 2), _add(I2, _scale(sign, PAULI[axis])))


def sharp_xz_obstruction_certificate() -> SharpXZObstructionCertificate:
    values = tuple((x, z, Fraction(1, 2)) for x in (1, -1) for z in (1, -1))
    return SharpXZObstructionCertificate(
        certificate_id="qubit-sharp-pauli-xz-no-parent/v1",
        pair=("X", "Z"),
        overlap_squared_by_sign=values,
        lemma="positive-parent-effect-below-two-rank-one-marginals-has-support-in-range-intersection",
        conclusion="all-parent-effects-zero-contradicts-normalization",
    )


def verify_sharp_xz_obstruction(certificate: SharpXZObstructionCertificate) -> bool:
    """Check the exact 2D projector-overlap certificate for sharp Pauli X/Z.

    This checks the exact projector-overlap data and certificate fields. The
    support-intersection lemma is an elementary mathematical argument stated
    here and in the audit record; this function does not formally verify that
    lemma. For positive effects under a sharp marginal, each joint effect is
    bounded above by its corresponding rank-one projector. The checked
    overlap 1/2 makes each X/Z projector pair have distinct one-dimensional
    ranges, so their range intersection is zero. Thus every joint effect is
    zero, which cannot sum to I.
    """
    if not isinstance(certificate, SharpXZObstructionCertificate):
        return False
    if certificate.certificate_id != "qubit-sharp-pauli-xz-no-parent/v1" or certificate.pair != ("X", "Z"):
        return False
    if certificate.lemma != "positive-parent-effect-below-two-rank-one-marginals-has-support-in-range-intersection":
        return False
    if certificate.conclusion != "all-parent-effects-zero-contradicts-normalization":
        return False
    expected = tuple((x, z, Fraction(1, 2)) for x in (1, -1) for z in (1, -1))
    if certificate.overlap_squared_by_sign != expected:
        return False
    for x in (1, -1):
        for z in (1, -1):
            px = _sharp_projector("X", x)
            pz = _sharp_projector("Z", z)
            overlap = _trace(_mul(px, pz))
            if overlap.imag != 0 or overlap.real != Fraction(1, 2):
                return False
    return True


def _parent_effects(eta: Fraction) -> tuple[tuple[int, int, Matrix2], ...]:
    effects: list[tuple[int, int, Matrix2]] = []
    for x in (1, -1):
        for z in (1, -1):
            total = _add(_add(I2, _scale(x * eta, PAULI["X"])), _scale(z * eta, PAULI["Z"]))
            effects.append((x, z, _scale(Fraction(1, 4), total)))
    return tuple(effects)


def _verify_parent(eta: Fraction, effects: tuple[tuple[int, int, Matrix2], ...]) -> tuple[bool, bool, bool, bool]:
    if tuple((x, z) for x, z, _ in effects) != tuple((x, z) for x in (1, -1) for z in (1, -1)):
        return False, False, False, False
    positive = all(_positive_semidefinite(g) for _, _, g in effects)
    total = _matrix(((0, 0), (0, 0)))
    for _, _, g in effects:
        total = _add(total, g)
    normalized = total == I2
    x_ok = all(
        _sum_matrices(g for xx, _, g in effects if xx == x) == effect("X", x, eta).value
        for x in (1, -1)
    )
    z_ok = all(
        _sum_matrices(g for _, zz, g in effects if zz == z) == effect("Z", z, eta).value
        for z in (1, -1)
    )
    return positive, normalized, x_ok, z_ok


def _sum_matrices(matrices) -> Matrix2:
    total = _matrix(((0, 0), (0, 0)))
    for matrix in matrices:
        total = _add(total, matrix)
    return total


def check_joint_device_xz(
    eta: Fraction | int,
    *,
    candidate_parent: tuple[tuple[int, int, Matrix2], ...] | None = None,
    policy: ResourcePolicy = ResourcePolicy(),
) -> Result[VerifiedParentPOVM | SharpXZObstructionCertificate]:
    """Check only declared unbiased X/Z cases, with exact rational arithmetic.

    eta=1 yields the checked sharp incompatibility certificate. eta=1/2 yields
    a constructed and fully checked parent. Other valid values without a
    constructive witness/certificate return undetermined, never a guess.
    """
    required = 64
    if not isinstance(policy, ResourcePolicy) or type(policy.max_operations) is not int or policy.max_operations < 0:
        return Result(Status.INVALID_INPUT, reason="invalid resource policy")
    if policy.max_operations < required:
        return Result(Status.RESOURCE_LIMIT, reason=f"joint check requires {required} bounded exact operations", operations=policy.max_operations)
    try:
        eta = _fraction(eta)
    except TypeError as exc:
        return Result(Status.INVALID_INPUT, reason=str(exc))
    if not 0 <= eta <= 1:
        return Result(Status.INVALID_INPUT, reason="eta must be in [0, 1]")
    if candidate_parent is not None:
        if not isinstance(candidate_parent, tuple) or any(
            not isinstance(item, tuple) or len(item) != 3 or
            type(item[0]) is not int or item[0] not in {-1, 1} or
            type(item[1]) is not int or item[1] not in {-1, 1} or
            not _matrix_well_formed(item[2])
            for item in candidate_parent
        ):
            return Result(Status.INVALID_INPUT, reason="candidate parent must contain (sign, sign, Matrix2) entries")
        expected_labels = tuple((x, z) for x in (1, -1) for z in (1, -1))
        if tuple((x, z) for x, z, _ in candidate_parent) != expected_labels:
            return Result(Status.INVALID_INPUT, reason="candidate parent needs exactly one effect per outcome pair in canonical order")
        if not all(_positive_semidefinite(g) for _, _, g in candidate_parent):
            return Result(Status.INVALID_INPUT, reason="candidate parent contains a non-positive effect")
        total = _sum_matrices(g for _, _, g in candidate_parent)
        if total != I2:
            return Result(Status.INVALID_INPUT, reason="candidate effects do not form a normalized POVM")
        checks = _verify_parent(eta, candidate_parent)
        if all(checks):
            return Result(Status.SUCCESS, VerifiedParentPOVM(eta, candidate_parent, *checks), operations=required)
        if eta == 1:
            certificate = sharp_xz_obstruction_certificate()
            if verify_sharp_xz_obstruction(certificate):
                return Result(
                    Status.INCOMPATIBLE,
                    certificate,
                    reason="candidate is a valid POVM but misses the sharp marginals; exact projector overlaps are checked, and the stated support-intersection argument yields incompatibility",
                    operations=required,
                )
            return Result(Status.UNDETERMINED, reason="candidate misses target marginals and obstruction verification did not complete", operations=required)
        if eta == Fraction(1, 2):
            effects = _parent_effects(eta)
            constructed_checks = _verify_parent(eta, effects)
            if all(constructed_checks):
                return Result(
                    Status.SUCCESS,
                    VerifiedParentPOVM(eta, effects, *constructed_checks),
                    reason="supplied candidate misses the target marginals; a separate constructed parent passed exact positivity, normalization, and both marginal checks",
                    operations=required,
                )
            return Result(Status.UNDETERMINED, reason="candidate misses target marginals and constructed parent did not verify", operations=required)
        return Result(Status.UNDETERMINED, reason="valid candidate POVM has wrong target marginals; no checked parent or obstruction is available for this eta", operations=required)
    if eta == 1:
        certificate = sharp_xz_obstruction_certificate()
        if verify_sharp_xz_obstruction(certificate):
            return Result(Status.INCOMPATIBLE, certificate, reason="exact projector-overlap data checked; the stated support-intersection argument yields incompatibility", operations=required)
        return Result(Status.UNDETERMINED, reason="obstruction certificate verification did not complete", operations=required)
    if eta == Fraction(1, 2):
        effects = _parent_effects(eta)
        checks = _verify_parent(eta, effects)
        if all(checks):
            return Result(Status.SUCCESS, VerifiedParentPOVM(eta, effects, *checks), operations=required)
        return Result(Status.UNDETERMINED, reason="constructed parent did not verify", operations=required)
    return Result(Status.UNDETERMINED, reason="no parent witness or obstruction certificate is implemented for this eta", operations=required)
