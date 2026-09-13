# SPDX-License-Identifier: Apache-2.0
import copy
import json
from pathlib import Path

import pytest

from e7q.ir.candidate_family import assess_candidate_restriction, build_candidate_family, factor

from e7q.ir.transformation_history import (
    TransformationHistoryError,
    build_transformation_history,
    transformation_step,
    validate_transformation_history,
)


D1 = "sha256:" + "1" * 64
D2 = "sha256:" + "2" * 64
D3 = "sha256:" + "3" * 64
M1 = "sha256:" + "a" * 64
M2 = "sha256:" + "b" * 64
SCHEMA = Path(__file__).resolve().parents[1] / "schemas/e7q-ir-transformation-history-v0alpha1.schema.json"


def step(index=0, source=D1, target=D2, outcome="success", kind="transform"):
    return transformation_step(
        index=index, kind=kind, rule_id="e7q.lower", rule_edition="1",
        input_family_id=source, admitted_member_ids=(M1, M2), outcome=outcome,
        output_family_id=target if outcome == "success" else None,
        excluded_member_ids=(M2,) if kind == "restrict" else (),
        preserves=("logical operation order",), loses=("source syntax",),
        limitations=("declaration only",), message="bounded declared result",
    )


def test_successful_history_is_ordered_and_chain_bound():
    history = build_transformation_history(
        D1, (step(), step(1, D2, D3)), context="compiler", inquiry="mapping"
    )
    assert history["residual_family_id"] == D3
    assert history["terminal_outcome"] == "success"
    validate_transformation_history(history)


def test_published_schema_names_the_executable_contract():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert schema["properties"]["schema"]["const"] == "e7q.ir.transformation-history/v0alpha1"
    assert schema["properties"]["steps"]["maxItems"] == 256


def test_operation_order_changes_identity():
    first = transformation_step(
        index=0, kind="transform", rule_id="e7q.a", rule_edition="1",
        input_family_id=D1, admitted_member_ids=(M1,), outcome="success",
        output_family_id=D2, message="a",
    )
    second = transformation_step(
        index=1, kind="transform", rule_id="e7q.b", rule_edition="1",
        input_family_id=D2, admitted_member_ids=(M1,), outcome="success",
        output_family_id=D3, message="b",
    )
    forward = build_transformation_history(D1, (first, second), context="c", inquiry="i")
    reverse_a = transformation_step(
        index=0, kind="transform", rule_id="e7q.b", rule_edition="1",
        input_family_id=D1, admitted_member_ids=(M1,), outcome="success",
        output_family_id=D2, message="b",
    )
    reverse_b = transformation_step(
        index=1, kind="transform", rule_id="e7q.a", rule_edition="1",
        input_family_id=D2, admitted_member_ids=(M1,), outcome="success",
        output_family_id=D3, message="a",
    )
    reverse = build_transformation_history(D1, (reverse_a, reverse_b), context="c", inquiry="i")
    assert forward["history_id"] != reverse["history_id"]


def test_failure_is_retained_and_stops_history():
    failed = step(outcome="resource_limit", target=None)
    history = build_transformation_history(D1, (failed,), context="c", inquiry="i")
    assert history["terminal_outcome"] == "resource_limit"
    assert history["residual_family_id"] is None
    with pytest.raises(TransformationHistoryError, match="stop"):
        build_transformation_history(D1, (failed, step(1, D1, D2)), context="c", inquiry="i")


def test_strict_transform_cannot_hide_restriction():
    with pytest.raises(TransformationHistoryError, match="silently exclude"):
        transformation_step(
            index=0, kind="transform", rule_id="e7q.route", rule_edition="1",
            input_family_id=D1, admitted_member_ids=(M1,), excluded_member_ids=(M2,),
            outcome="success", output_family_id=D2, message="bad",
        )


def test_non_success_cannot_publish_output():
    with pytest.raises(TransformationHistoryError, match="must not publish"):
        transformation_step(
            index=0, kind="transform", rule_id="e7q.route", rule_edition="1",
            input_family_id=D1, admitted_member_ids=(M1,), outcome="domain_error",
            output_family_id=D2, message="bad",
        )


def test_chain_mismatch_and_stale_identity_fail_closed():
    with pytest.raises(TransformationHistoryError, match="continue"):
        build_transformation_history(D1, (step(source=D2),), context="c", inquiry="i")
    history = build_transformation_history(D1, (step(),), context="c", inquiry="i")
    tampered = copy.deepcopy(history)
    tampered["steps"][0]["message"] = "hidden mutation"
    with pytest.raises(TransformationHistoryError, match="stale identity"):
        validate_transformation_history(tampered)


def test_restriction_discloses_exclusion():
    result = transformation_step(
        index=0, kind="restrict", rule_id="e7q.topology-filter", rule_edition="1",
        input_family_id=D1, admitted_member_ids=(M1,), excluded_member_ids=(M2,),
        outcome="success", output_family_id=D2, loses=("excluded candidate",), message="filtered",
    )
    assert result["domain"]["excluded_member_ids"] == [M2]


def test_q_a2_consumes_corrected_q_a1_residual_family_identity():
    family = build_candidate_family(
        D1,
        (factor("layout", ("layout",), ({"layout": "a"}, {"layout": "b"})),),
    )
    retained = family["members"][0]["member_id"]
    restriction = assess_candidate_restriction(
        family,
        (retained,),
        criterion_id="e7q.topology-filter",
        criterion_edition="2026-09-13.1",
        criterion_text="retain the declared topology domain",
    )
    step = transformation_step(
        index=0,
        kind="restrict",
        rule_id=restriction["criterion"]["id"],
        rule_edition=restriction["criterion"]["edition"],
        input_family_id=family["family_id"],
        admitted_member_ids=restriction["retained_member_ids"],
        excluded_member_ids=restriction["excluded_member_ids"],
        outcome=restriction["outcome"],
        output_family_id=restriction["result_family"]["family_id"],
        loses=("excluded candidates",),
        message=restriction["message"],
    )
    history = build_transformation_history(
        family["family_id"], (step,), context="compiler", inquiry="topology"
    )
    assert history["residual_family_id"] == restriction["result_family"]["family_id"]


def test_q_a2_retains_empty_q_a1_restriction_as_terminal_outcome():
    family = build_candidate_family(
        D1,
        (factor("layout", ("layout",), ({"layout": "a"}, {"layout": "b"})),),
    )
    restriction = assess_candidate_restriction(
        family,
        (),
        criterion_id="e7q.reject-all",
        criterion_edition="2026-09-13.1",
        criterion_text="retain no admitted candidate",
    )
    step = transformation_step(
        index=0,
        kind="restrict",
        rule_id=restriction["criterion"]["id"],
        rule_edition=restriction["criterion"]["edition"],
        input_family_id=family["family_id"],
        admitted_member_ids=restriction["retained_member_ids"],
        excluded_member_ids=restriction["excluded_member_ids"],
        outcome=restriction["outcome"],
        message=restriction["message"],
    )
    history = build_transformation_history(
        family["family_id"], (step,), context="compiler", inquiry="topology"
    )
    assert history["terminal_outcome"] == "empty"
    assert history["residual_family_id"] is None


def test_q_a2_accepts_successful_identity_restriction_with_no_exclusions():
    family = build_candidate_family(
        D1,
        (factor("layout", ("layout",), ({"layout": "a"}, {"layout": "b"})),),
    )
    all_members = [item["member_id"] for item in family["members"]]
    restriction = assess_candidate_restriction(
        family,
        all_members,
        criterion_id="e7q.retain-all",
        criterion_edition="2026-09-13.1",
        criterion_text="retain every admitted candidate",
    )
    step = transformation_step(
        index=0,
        kind="restrict",
        rule_id=restriction["criterion"]["id"],
        rule_edition=restriction["criterion"]["edition"],
        input_family_id=family["family_id"],
        admitted_member_ids=restriction["retained_member_ids"],
        excluded_member_ids=restriction["excluded_member_ids"],
        outcome=restriction["outcome"],
        output_family_id=restriction["result_family"]["family_id"],
        message=restriction["message"],
    )
    history = build_transformation_history(
        family["family_id"], (step,), context="compiler", inquiry="topology"
    )
    assert history["terminal_outcome"] == "success"
    assert history["residual_family_id"] == restriction["result_family"]["family_id"]
