# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import pytest

from e7q.research.quantum_view_v0alpha1 import (
    DensityOperator,
    GaussianRational,
    I2,
    Matrix2,
    PhysicalOutcomeRecord,
    PreparationDescription,
    ResourcePolicy,
    SimulatedOutcomeRecord,
    Status,
    born_distribution,
    check_joint_device_xz,
    density_from_bloch_y,
    import_physical_record,
    preparation_description_fibre,
    simulate_outcome,
    state_fibre,
    verify_sharp_xz_obstruction,
    view,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples/quantum-view/v0alpha1/qubit_xzy_fixture.json"


def expected_to_mapping(obj):
    return {int(k): Fraction(v) for k, v in obj.items()}


def test_exact_pauli_distributions_and_two_reconstruction_fibres():
    fixture = json.loads(FIXTURE.read_text())
    a = Fraction(fixture["model"]["a"]["numerator"], fixture["model"]["a"]["denominator"])
    rho_plus = density_from_bloch_y(+1, a)
    rho_minus = density_from_bloch_y(-1, a)
    for state_name, state in (("rho_plus", rho_plus), ("rho_minus", rho_minus)):
        for axis in ("X", "Y", "Z"):
            result = born_distribution(state, axis)
            assert result.status is Status.SUCCESS
            assert result.value is not None
            expected = expected_to_mapping(fixture["expected_exact"][state_name][axis])
            assert result.value.as_mapping() == expected
    axes = ("X", "Z")
    plus_view = view(rho_plus, axes).value
    minus_view = view(rho_minus, axes).value
    assert plus_view == minus_view
    assert plus_view is not None

    state_result = state_fibre((rho_plus, rho_minus), axes, plus_view)
    descriptions = (
        PreparationDescription("prep-plus", rho_plus),
        PreparationDescription("prep-plus-alias", rho_plus),
        PreparationDescription("prep-minus", rho_minus),
    )
    prep_result = preparation_description_fibre(descriptions, axes, plus_view)
    assert state_result.status is Status.SUCCESS
    assert state_result.value == (rho_plus, rho_minus)
    assert prep_result.status is Status.SUCCESS
    assert prep_result.value == descriptions
    assert len(state_result.value) == 2
    assert len(prep_result.value) == 3
    assert [item.description_id for item in prep_result.value] == fixture["expected_exact"]["xz_reconstruction_fibres"]["preparation_description_ids"]
    assert ["rho_plus", "rho_minus"] == fixture["expected_exact"]["xz_reconstruction_fibres"]["state_density_operator_ids"]
    assert born_distribution(rho_plus, "Y").value != born_distribution(rho_minus, "Y").value


def test_sharp_xz_is_rejected_with_verified_obstruction_certificate():
    result = check_joint_device_xz(Fraction(1))
    assert result.status is Status.INCOMPATIBLE
    assert result.value is not None
    assert verify_sharp_xz_obstruction(result.value)
    assert result.value.overlap_squared_by_sign == tuple(
        (x, z, Fraction(1, 2)) for x in (1, -1) for z in (1, -1)
    )


def test_unsharp_eta_half_parent_and_both_marginals_are_verified():
    result = check_joint_device_xz(Fraction(1, 2))
    assert result.status is Status.SUCCESS
    parent = result.value
    assert parent is not None
    assert parent.positivity_checked
    assert parent.normalization_checked
    assert parent.x_marginals_checked
    assert parent.z_marginals_checked
    assert len(parent.effects) == 4


def test_valid_but_wrong_parent_candidate_is_undetermined_not_a_no_go_claim():
    # A valid POVM that ignores z has the correct X marginals but not the
    # declared sharp/unsharp Z marginals. It disproves neither existence nor
    # non-existence of some other parent.
    eta = Fraction(1, 2)
    wrong = tuple(
        (x, z, Matrix2((
            (GaussianRational(Fraction(1, 4)), GaussianRational(Fraction(x, 8))),
            (GaussianRational(Fraction(x, 8)), GaussianRational(Fraction(1, 4))),
        )))
        for x in (1, -1) for z in (1, -1)
    )
    result = check_joint_device_xz(eta, candidate_parent=wrong)
    assert result.status is Status.UNDETERMINED
    assert result.value is None


def test_physical_records_are_imported_and_simulated_records_stay_separate():
    imported = PhysicalOutcomeRecord(
        record_id="rec-1", run_id="run-1", preparation_id="prep-plus",
        axis="X", outcome=1, source_id="lab-log-1", provenance="signed-lab-export",
    )
    physical_result = import_physical_record(imported)
    assert physical_result.status is Status.SUCCESS
    assert physical_result.value.record is imported

    simulated = simulate_outcome(density_from_bloch_y(1), "X", 7, "reference-sampler/1")
    assert simulated.status is Status.SUCCESS
    assert isinstance(simulated.value, SimulatedOutcomeRecord)
    assert simulated.value.record_kind == "simulated"
    assert not isinstance(simulated.value, PhysicalOutcomeRecord)
    assert import_physical_record(simulated.value).status is Status.INVALID_INPUT
    assert simulate_outcome(density_from_bloch_y(1), "X", 7, "reference-sampler/1").value == simulated.value


def test_required_failure_statuses_remain_distinct():
    valid = density_from_bloch_y(1)
    invalid_density = DensityOperator(I2)
    assert born_distribution(invalid_density, "X").status is Status.INVALID_INPUT
    assert born_distribution(valid, "W").status is Status.UNSUPPORTED
    assert born_distribution(valid, "X", ResourcePolicy(max_operations=0)).status is Status.RESOURCE_LIMIT
    assert check_joint_device_xz(Fraction(2)).status is Status.INVALID_INPUT
    assert check_joint_device_xz(Fraction(3, 4)).status is Status.UNDETERMINED


def test_invalid_physical_record_does_not_become_a_predicted_result():
    bad = PhysicalOutcomeRecord("", "", "", "X", 1, "", "")
    assert import_physical_record(bad).status is Status.INVALID_INPUT
    assert born_distribution(density_from_bloch_y(1), "X").value is not None


def test_adapter_matches_saved_independent_numpy_result():
    fixture = json.loads(FIXTURE.read_text())
    independent_path = FIXTURE.with_name("independent_numpy_result.json")
    independent = json.loads(independent_path.read_text())
    assert independent["method"].startswith("direct 2x2 NumPy matrices")
    assert independent["unsharp_parent_normalizes"]
    assert independent["unsharp_x_marginals_verified"]
    assert independent["unsharp_z_marginals_verified"]
    assert independent["sharp_xz_rank_one_projector_overlap_squared"] == {
        "+1,+1": 0.5, "+1,-1": 0.5, "-1,+1": 0.5, "-1,-1": 0.5,
    }
    a = Fraction(fixture["model"]["a"]["numerator"], fixture["model"]["a"]["denominator"])
    states = {"rho_plus": density_from_bloch_y(1, a), "rho_minus": density_from_bloch_y(-1, a)}
    for state_name, axes in independent["probabilities"].items():
        for axis, probabilities in axes.items():
            exact = born_distribution(states[state_name], axis)
            assert exact.status is Status.SUCCESS and exact.value is not None
            for outcome, probability in probabilities.items():
                assert float(exact.value.as_mapping()[int(outcome)]) == pytest.approx(probability, abs=1e-12)


def test_malformed_matrix_and_candidate_parent_fail_closed():
    malformed = DensityOperator(Matrix2(((GaussianRational(1),), (GaussianRational(0), GaussianRational(1)))))  # type: ignore[arg-type]
    assert born_distribution(malformed, "X").status is Status.INVALID_INPUT
    assert check_joint_device_xz(Fraction(1, 2), candidate_parent=((1, 1, malformed.matrix),)).status is Status.INVALID_INPUT
