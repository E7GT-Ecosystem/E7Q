# SPDX-License-Identifier: Apache-2.0
"""Opt-in E7G-T UC5 relative-support pilot records."""
from __future__ import annotations

from typing import Any


SCHEMA = "e7q.relative-support-pilot/v1alpha1"
UPSTREAM_MODULE = "E7G-T v0.11-UC5 section 9.15 and Pilot J"

SUPPORT_SEMANTICS = {
    "ordinal",
    "score",
    "probability",
    "likelihoodLike",
    "confidenceLike",
    "domainSpecific",
}

CALIBRATION_STATUSES = {
    "notApplicable",
    "uncalibrated",
    "partiallyCalibrated",
    "calibrated",
    "unknown",
}

CARRIER_KINDS = {
    "reconstructionCandidates",
    "historyCandidates",
    "phaseCandidates",
    "jointCandidates",
    "other",
}


def relative_support_pilot(
    *,
    pilot_id: str,
    carrier_ref: str,
    carrier_kind: str,
    support_semantics: str,
    support_domain_ref: str,
    relation_or_scoring_rule_ref: str,
    evidence_and_provenance_refs: list[str],
    prior_or_initialisation_rule_ref: str,
    update_rule_ref: str,
    calibration_status: str,
    normalisation_rule_ref: str,
    independence_assumptions: list[str],
    known_dependencies: list[str],
    current_support_assignments: list[dict[str, object]],
    exclusion_rule_ref: str,
    admissible_use: object,
    non_admissible_use: object,
    validity_window: object,
    stop_or_reopen_condition: object,
) -> dict[str, object]:
    """Build an explicitly invoked, substrate-neutral UC5 pilot envelope."""
    return {
        "schema": SCHEMA,
        "upstream_module": UPSTREAM_MODULE,
        "status": "informative-pilot",
        "invoked": True,
        "pilot_id": pilot_id,
        "carrier_ref": carrier_ref,
        "carrier_kind": carrier_kind,
        "support_semantics": support_semantics,
        "support_domain_ref": support_domain_ref,
        "relation_or_scoring_rule_ref": relation_or_scoring_rule_ref,
        "evidence_and_provenance_refs": evidence_and_provenance_refs,
        "prior_or_initialisation_rule_ref": prior_or_initialisation_rule_ref,
        "update_rule_ref": update_rule_ref,
        "calibration_status": calibration_status,
        "normalisation_rule_ref": normalisation_rule_ref,
        "independence_assumptions": independence_assumptions,
        "known_dependencies": known_dependencies,
        "current_support_assignments": current_support_assignments,
        "exclusion_rule_ref": exclusion_rule_ref,
        "admissible_use": admissible_use,
        "non_admissible_use": non_admissible_use,
        "validity_window": validity_window,
        "stop_or_reopen_condition": stop_or_reopen_condition,
        "separation_laws": [
            "admissibility is not degree of support",
            "stronger support is not truth",
            "weaker support is not falsehood or exclusion",
            "numerical support is not probability unless a probability model is declared",
            "support does not by itself determine action",
        ],
    }


def from_declaration(
    declaration: dict[str, Any], *, pilot_id: str
) -> dict[str, object]:
    """Build the pilot from a JSON declaration using the public field names."""
    return relative_support_pilot(
        pilot_id=pilot_id,
        carrier_ref=declaration.get("carrier_ref"),
        carrier_kind=declaration.get("carrier_kind"),
        support_semantics=declaration.get("support_semantics"),
        support_domain_ref=declaration.get("support_domain_ref"),
        relation_or_scoring_rule_ref=declaration.get(
            "relation_or_scoring_rule_ref"
        ),
        evidence_and_provenance_refs=declaration.get(
            "evidence_and_provenance_refs"
        ),
        prior_or_initialisation_rule_ref=declaration.get(
            "prior_or_initialisation_rule_ref"
        ),
        update_rule_ref=declaration.get("update_rule_ref"),
        calibration_status=declaration.get("calibration_status"),
        normalisation_rule_ref=declaration.get("normalisation_rule_ref"),
        independence_assumptions=declaration.get("independence_assumptions"),
        known_dependencies=declaration.get("known_dependencies"),
        current_support_assignments=declaration.get(
            "current_support_assignments"
        ),
        exclusion_rule_ref=declaration.get("exclusion_rule_ref"),
        admissible_use=declaration.get("admissible_use"),
        non_admissible_use=declaration.get("non_admissible_use"),
        validity_window=declaration.get("validity_window"),
        stop_or_reopen_condition=declaration.get("stop_or_reopen_condition"),
    )


def conformance_checks(value: Any) -> list[dict[str, object]]:
    """Check structure and the UC5 separation between support and exclusion."""

    def check(name: str, passed: bool) -> dict[str, object]:
        return {"name": f"relative-support-pilot:{name}", "passed": passed}

    def nonempty(item: object) -> bool:
        return isinstance(item, str) and bool(item.strip())

    def string_list(item: object, *, allow_empty: bool = True) -> bool:
        return (
            isinstance(item, list)
            and (allow_empty or bool(item))
            and all(nonempty(entry) for entry in item)
        )

    if not isinstance(value, dict):
        return [check("object", False)]

    assignments = value.get("current_support_assignments")
    checks = [
        check("schema", value.get("schema") == SCHEMA),
        check("invoked", value.get("invoked") is True),
        check("pilot-id", nonempty(value.get("pilot_id"))),
        check("carrier-ref", nonempty(value.get("carrier_ref"))),
        check("carrier-kind", value.get("carrier_kind") in CARRIER_KINDS),
        check(
            "support-semantics",
            value.get("support_semantics") in SUPPORT_SEMANTICS,
        ),
        check("support-domain", nonempty(value.get("support_domain_ref"))),
        check(
            "relation-or-scoring-rule",
            nonempty(value.get("relation_or_scoring_rule_ref")),
        ),
        check(
            "evidence-and-provenance",
            string_list(
                value.get("evidence_and_provenance_refs"), allow_empty=False
            ),
        ),
        check(
            "initialisation-rule",
            nonempty(value.get("prior_or_initialisation_rule_ref")),
        ),
        check("update-rule", nonempty(value.get("update_rule_ref"))),
        check(
            "calibration-status",
            value.get("calibration_status") in CALIBRATION_STATUSES,
        ),
        check(
            "normalisation-rule",
            nonempty(value.get("normalisation_rule_ref")),
        ),
        check(
            "independence-assumptions",
            string_list(value.get("independence_assumptions")),
        ),
        check(
            "known-dependencies", string_list(value.get("known_dependencies"))
        ),
        check("assignments", isinstance(assignments, list) and bool(assignments)),
        check("exclusion-rule", nonempty(value.get("exclusion_rule_ref"))),
        check("admissible-use", value.get("admissible_use") is not None),
        check("non-admissible-use", value.get("non_admissible_use") is not None),
        check("validity-window", value.get("validity_window") is not None),
        check(
            "stop-or-reopen-condition",
            value.get("stop_or_reopen_condition") is not None,
        ),
        check(
            "separation-laws",
            string_list(value.get("separation_laws"), allow_empty=False),
        ),
    ]

    if not isinstance(assignments, list):
        return checks

    alternative_refs: list[str] = []
    for index, assignment in enumerate(assignments):
        valid = isinstance(assignment, dict)
        checks.append(check(f"assignment-{index}-object", valid))
        if not valid:
            continue
        alternative_ref = assignment.get("alternative_ref")
        checks.append(check(f"assignment-{index}-ref", nonempty(alternative_ref)))
        if isinstance(alternative_ref, str):
            alternative_refs.append(alternative_ref)
        checks.append(
            check(
                f"assignment-{index}-admissibility",
                isinstance(assignment.get("admissible"), bool),
            )
        )
        checks.append(
            check(
                f"assignment-{index}-support-value",
                "support_value" in assignment,
            )
        )
        checks.append(
            check(
                f"assignment-{index}-evidence",
                string_list(assignment.get("evidence_refs")),
            )
        )
        if assignment.get("admissible") is False:
            checks.append(
                check(
                    f"assignment-{index}-exclusion-basis",
                    nonempty(assignment.get("exclusion_basis_ref")),
                )
            )
    checks.append(
        check(
            "assignment-refs-unique",
            len(alternative_refs) == len(set(alternative_refs)),
        )
    )
    return checks
