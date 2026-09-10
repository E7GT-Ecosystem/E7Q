# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from e7q.ir.canonical import digest
from e7q.research.dhsp import (
    REFERENCE_RULE,
    combine_phase_states,
    evaluate_affine_candidate,
    phase_state,
)

ROOT = Path(__file__).resolve().parents[1]


def density(state):
    return np.outer(state, state.conjugate())


def test_cnot_measurement_identity_for_bounded_phase_states():
    for modulus in range(2, 11):
        for hidden_shift in range(modulus):
            for left_label in range(modulus):
                for right_label in range(modulus):
                    for outcome in (0, 1):
                        result = combine_phase_states(
                            modulus,
                            left_label,
                            right_label,
                            hidden_shift,
                            outcome,
                        )
                        expected = phase_state(
                            modulus, result.resulting_label, hidden_shift
                        )
                        assert result.probability == pytest.approx(0.5)
                        assert np.allclose(
                            density(result.state), density(expected), atol=1e-12
                        )


def test_combination_evidence_names_preservation_loss_and_nonclaims():
    evidence = combine_phase_states(7, 2, 5, 3, 1).evidence()
    assert evidence["transformation"]["resulting_label"] == 4
    assert evidence["transformation"]["discarded_global_phase_exponent_mod_n"] == 1
    assert "absolute-global-phase" in evidence["lost"]
    assert "hidden-shift-dependent-relative-phase" in evidence["preserved"]
    assert "polynomial-time-dhsp-algorithm" in evidence["nonclaims"]
    assert digest(
        {k: v for k, v in evidence.items() if k != "evidence_id"}
    ) == evidence["evidence_id"]


def test_reference_affine_rule_has_no_bounded_counterexample():
    result = evaluate_affine_candidate(
        {"id": "reference", **REFERENCE_RULE}, moduli=range(2, 17)
    )
    assert result["outcome"] == {
        "status": "PASS",
        "conclusion": "NO_COUNTEREXAMPLE_IN_ENUMERATED_DOMAIN",
        "counterexample": None,
        "universal_correctness_established": False,
        "polynomial_time_established": False,
    }
    assert result["domain"]["comparisons_performed"] == 2990


def test_wrong_affine_rule_retains_first_counterexample():
    result = evaluate_affine_candidate(
        {
            "id": "sum-only",
            "outcome_0": {"k": 1, "l": 1},
            "outcome_1": {"k": 1, "l": 1},
        },
        moduli=range(2, 17),
    )
    assert result["outcome"]["status"] == "FAIL"
    assert result["outcome"]["conclusion"] == "COUNTEREXAMPLE_FOUND"
    assert result["outcome"]["counterexample"] == {
        "modulus": 3,
        "hidden_shift_witness": 1,
        "left_label": 0,
        "right_label": 1,
        "measurement_outcome": 1,
        "expected_label": 2,
        "candidate_label": 1,
    }
    assert result["domain"]["enumeration_complete"] is False


@pytest.mark.parametrize(
    "candidate, error",
    [
        ({"id": "missing"}, ValueError),
        (
            {
                "id": "bad",
                "outcome_0": {"k": True, "l": 1},
                "outcome_1": {"k": 1, "l": -1},
            },
            TypeError,
        ),
        (
            {
                "id": "bad",
                "outcome_0": {"k": 1, "l": 1},
                "outcome_1": {"k": 1, "l": -1},
                "extra": 0,
            },
            ValueError,
        ),
    ],
)
def test_candidate_shape_fails_closed(candidate, error):
    with pytest.raises(error):
        evaluate_affine_candidate(candidate, moduli=(2, 3))


def test_resource_and_domain_limits_fail_before_enumeration():
    candidate = {"id": "reference", **REFERENCE_RULE}
    with pytest.raises(ValueError, match="between 2"):
        evaluate_affine_candidate(candidate, moduli=(65,))
    with pytest.raises(ValueError, match="duplicates"):
        evaluate_affine_candidate(candidate, moduli=(2, 2))
    with pytest.raises(ValueError, match="at most"):
        evaluate_affine_candidate(candidate, moduli=range(2, 35))
    with pytest.raises(TypeError, match="integer"):
        phase_state(4, True, 0)
    too_large = {
        "id": "coefficient-over-budget",
        "outcome_0": {"k": 65, "l": 1},
        "outcome_1": {"k": 1, "l": -1},
    }
    with pytest.raises(ValueError, match="absolute value"):
        evaluate_affine_candidate(too_large, moduli=(2,))


def test_published_corpus_is_deterministic_and_bounded():
    report = json.loads(
        (ROOT / "benchmarks/e7q-research/dhsp-affine-corpus.json").read_text()
    )
    assert report["summary"] == {
        "candidates": 3,
        "pass": 1,
        "fail": 2,
        "counterexamples": 2,
    }
    assert digest(
        {k: v for k, v in report.items() if k != "report_id"}
    ) == report["report_id"]
    assert all(
        not assessment["outcome"]["universal_correctness_established"]
        and not assessment["outcome"]["polynomial_time_established"]
        for assessment in report["assessments"]
    )
