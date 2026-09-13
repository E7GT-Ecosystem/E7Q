# SPDX-License-Identifier: Apache-2.0
import copy
import json
from pathlib import Path

import pytest

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
