# SPDX-License-Identifier: Apache-2.0
from e7q.support import conformance_checks, relative_support_pilot


def pilot():
    return relative_support_pilot(
        pilot_id="test-support",
        carrier_ref="experiment:test:hypotheses",
        carrier_kind="other",
        support_semantics="ordinal",
        support_domain_ref="declared ordinal labels",
        relation_or_scoring_rule_ref="higher > lower; unranked remains incomparable",
        evidence_and_provenance_refs=["evidence:test"],
        prior_or_initialisation_rule_ref="all alternatives initially admitted",
        update_rule_ref="revise ordinal labels when declared evidence changes",
        calibration_status="notApplicable",
        normalisation_rule_ref="notApplicable for ordinal support",
        independence_assumptions=[],
        known_dependencies=["alternatives use the same supplied runs"],
        current_support_assignments=[
            {
                "alternative_ref": "hypothesis:effect",
                "admissible": True,
                "support_value": "higher",
                "evidence_refs": ["evidence:test"],
            },
            {
                "alternative_ref": "hypothesis:variation",
                "admissible": True,
                "support_value": "lower",
                "evidence_refs": [],
            },
        ],
        exclusion_rule_ref="incompatibility evidence only; support alone does not exclude",
        admissible_use="prioritise the next evidence-acquisition step",
        non_admissible_use="truth, probability, causation, or automatic action",
        validity_window="the supplied experiment evidence",
        stop_or_reopen_condition="new, retracted, or reinterpreted evidence",
    )


def test_relative_support_pilot_is_structurally_valid():
    value = pilot()
    assert value["status"] == "informative-pilot"
    assert all(check["passed"] for check in conformance_checks(value))


def test_low_support_does_not_remove_an_admitted_alternative():
    value = pilot()
    low = value["current_support_assignments"][1]
    assert low["support_value"] == "lower"
    assert low["admissible"] is True
    assert all(check["passed"] for check in conformance_checks(value))


def test_excluded_alternative_requires_separate_exclusion_basis():
    value = pilot()
    value["current_support_assignments"][1]["admissible"] = False
    failed = {
        check["name"]
        for check in conformance_checks(value)
        if not check["passed"]
    }
    assert "relative-support-pilot:assignment-1-exclusion-basis" in failed
