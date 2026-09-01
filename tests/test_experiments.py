# SPDX-License-Identifier: Apache-2.0
import json

import pytest

from e7q.artifacts import validate_artifact
from e7q.cli import main
from e7q.experiments import assess_comparative_experiment
from e7q.language import E7QError


def manifest():
    runs = []
    values = {
        ("classical", "old"): [(52.2, 99.9), (52.4, 99.8)],
        ("quantum", "old"): [(71.9, 95.1), (72.1, 95.0)],
        ("classical", "new"): [(62.0, 98.1), (62.2, 98.0)],
        ("quantum", "new"): [(97.0, 51.9), (96.8, 52.0)],
    }
    for (sampler, method), observations in values.items():
        for index, (validity, uniqueness) in enumerate(observations):
            runs.append(
                {
                    "run_id": f"{sampler}-{method}-{index}",
                    "cell": {"sampler": sampler, "method": method},
                    "metrics": {
                        "validity": validity,
                        "uniqueness": uniqueness,
                    },
                    "resource_budget": {"generated_outputs": 10000},
                    "independence_status": "reported-independent",
                    "evidence_refs": [f"evidence:{sampler}:{method}:{index}"],
                }
            )
    return {
        "schema": "e7q.comparative-experiment/v1alpha1",
        "experiment_id": "synthetic-factorial",
        "title": "Synthetic two-factor example",
        "inquiry": "Describe factor effects without assigning causal advantage.",
        "predeclared": False,
        "factors": [
            {"factor_id": "sampler", "levels": ["classical", "quantum"]},
            {"factor_id": "method", "levels": ["old", "new"]},
        ],
        "metrics": [
            {
                "metric_id": "validity",
                "direction": "higher-is-better",
                "role": "primary",
                "minimum_effect": 1.0,
                "unit": "percent",
            },
            {
                "metric_id": "uniqueness",
                "direction": "higher-is-better",
                "role": "secondary",
                "minimum_effect": 1.0,
                "unit": "percent",
            },
        ],
        "runs": runs,
        "relative_support": {
            "carrier_ref": "synthetic-factorial:hypotheses",
            "carrier_kind": "other",
            "support_semantics": "ordinal",
            "support_domain_ref": "higher, lower, and unranked labels",
            "relation_or_scoring_rule_ref": "higher > lower; unranked is incomparable",
            "evidence_and_provenance_refs": ["synthetic-factorial"],
            "prior_or_initialisation_rule_ref": "all declared alternatives admitted",
            "update_rule_ref": "revise only when supplied evidence or framing changes",
            "calibration_status": "notApplicable",
            "normalisation_rule_ref": "notApplicable for ordinal support",
            "independence_assumptions": [],
            "known_dependencies": ["all assignments use the same manifest"],
            "current_support_assignments": [
                {
                    "alternative_ref": "hypothesis:sampler-effect",
                    "admissible": True,
                    "support_value": "higher",
                    "evidence_refs": ["synthetic-factorial"],
                },
                {
                    "alternative_ref": "hypothesis:run-variation",
                    "admissible": True,
                    "support_value": "lower",
                    "evidence_refs": [],
                },
            ],
            "exclusion_rule_ref": "separate incompatibility evidence; support alone cannot exclude",
            "admissible_use": "choose a next replication or baseline check",
            "non_admissible_use": "truth, causation, or quantum-advantage claim",
            "validity_window": "this supplied synthetic manifest",
            "stop_or_reopen_condition": "new evidence, changed model, or changed metric",
        },
    }


def test_factorial_report_preserves_interaction_and_metric_tradeoff():
    report = assess_comparative_experiment(manifest())
    assert report["status"] == "ASSESSED"
    assert report["claim_assessment"]["highest_supported_level"] == "OBSERVED_DIFFERENCE"
    validity = next(
        item for item in report["interactions"] if item["metric_id"] == "validity"
    )
    assert validity["difference_of_differences"] == pytest.approx(15.1)
    quantum_new = next(
        comparison
        for comparison in report["comparisons"]
        if comparison["factor_id"] == "sampler"
        and comparison["context"] == {"method": "new"}
    )
    assert quantum_new["tradeoff"]["improved"] == ["validity"]
    assert quantum_new["tradeoff"]["worsened"] == ["uniqueness"]
    assert quantum_new["tradeoff"]["aggregate_verdict"] == "not-computed"


def test_report_never_promotes_descriptive_difference_to_advantage():
    report = assess_comparative_experiment(manifest())
    statuses = {
        entry["level"]: entry["status"]
        for entry in report["claim_assessment"]["ladder"]
    }
    assert statuses["MANIFEST_ASSESSABLE"] == "SUPPORTED"
    assert statuses["FEASIBILITY"] == "NOT_ESTABLISHED"
    assert statuses["OBSERVED_DIFFERENCE"] == "SUPPORTED"
    assert statuses["REPEATABLE_EFFECT"] == "NOT_ESTABLISHED"
    assert statuses["QUALITY_ADVANTAGE"] == "NOT_ESTABLISHED"
    assert statuses["PRACTICAL_ADVANTAGE"] == "NOT_ESTABLISHED"
    assert statuses["COMPUTATIONAL_QUANTUM_ADVANTAGE"] == "NOT_ESTABLISHED"


def test_no_material_difference_supports_only_manifest_assessability():
    value = manifest()
    for run in value["runs"]:
        run["metrics"] = {"validity": 50.0, "uniqueness": 50.0}
    report = assess_comparative_experiment(value)
    assert (
        report["claim_assessment"]["highest_supported_level"]
        == "MANIFEST_ASSESSABLE"
    )
    statuses = {
        entry["level"]: entry["status"]
        for entry in report["claim_assessment"]["ladder"]
    }
    assert statuses["FEASIBILITY"] == "NOT_ESTABLISHED"


def test_relative_support_is_opt_in_and_structurally_valid():
    plain = assess_comparative_experiment(manifest())
    assert "relative_support_pilot" not in plain
    report = assess_comparative_experiment(
        manifest(), include_relative_support_pilot=True
    )
    assert report["relative_support_pilot"]["invoked"] is True
    assert validate_artifact(report)["status"] == "PASS"


def test_invalid_or_incomplete_manifest_fails_closed():
    value = manifest()
    value["runs"][0]["metrics"]["validity"] = float("nan")
    with pytest.raises(E7QError, match="non-finite metric"):
        assess_comparative_experiment(value)
    value = manifest()
    value["metrics"][1]["metric_id"] = "validity"
    with pytest.raises(E7QError, match="metric_id values must be unique"):
        assess_comparative_experiment(value)


def test_assess_experiment_cli_writes_registered_report(tmp_path):
    source = tmp_path / "experiment.json"
    output = tmp_path / "report.json"
    source.write_text(json.dumps(manifest()), encoding="utf-8")
    assert main(
        [
            "assess-experiment",
            str(source),
            "--relative-support-pilot",
            "-o",
            str(output),
        ]
    ) == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["schema"] == "e7q.comparative-experiment-report/v1alpha1"
    assert validate_artifact(report)["status"] == "PASS"
