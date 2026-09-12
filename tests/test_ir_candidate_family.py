# SPDX-License-Identifier: Apache-2.0
import copy
import json
from pathlib import Path

import pytest

from e7q.ir.candidate_family import (
    CandidateFamilyError,
    build_candidate_family,
    candidate_family_view,
    factor,
    restrict_candidate_family,
    validate_candidate_family,
)


SOURCE = "sha256:" + "1" * 64
SCHEMA = Path(__file__).resolve().parents[1] / "schemas/e7q-ir-candidate-family-v0alpha1.schema.json"


def test_correlated_layout_target_choices_do_not_invent_cross_product():
    placement = factor(
        "placement",
        ("layout", "target"),
        (
            {"layout": "line-0-1", "target": "backend-a"},
            {"layout": "line-2-3", "target": "backend-b"},
        ),
    )
    family = build_candidate_family(SOURCE, (placement,))
    assert len(family["members"]) == 2
    assert {tuple(item["bindings"].values()) for item in family["members"]} == {
        ("line-0-1", "backend-a"),
        ("line-2-3", "backend-b"),
    }


def test_separate_factors_expand_only_declared_independence():
    layout = factor("layout-choice", ("layout",), ({"layout": "a"}, {"layout": "b"}))
    pass_order = factor("pass-choice", ("passes",), ({"passes": "x-y"}, {"passes": "y-x"}))
    family = build_candidate_family(SOURCE, (layout, pass_order))
    assert len(family["members"]) == 4
    validate_candidate_family(family)


def test_family_identity_is_deterministic_under_input_order():
    first = factor("layout", ("layout",), ({"layout": "b"}, {"layout": "a"}))
    second = factor("target", ("target",), ({"target": "z"},))
    assert build_candidate_family(SOURCE, (first, second)) == build_candidate_family(
        SOURCE, (second, first)
    )


def test_member_identity_is_bound_to_source():
    choice = factor("layout", ("layout",), ({"layout": "a"},))
    first = build_candidate_family(SOURCE, (choice,))
    second = build_candidate_family("sha256:" + "2" * 64, (choice,))
    assert first["members"][0]["member_id"] != second["members"][0]["member_id"]


def test_published_schema_names_the_executable_contract():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert schema["properties"]["schema"]["const"] == "e7q.ir.candidate-family/v0alpha1"
    assert schema["properties"]["members"]["maxItems"] == 65_536


def test_overlapping_dimensions_fail_closed():
    first = factor("first", ("layout",), ({"layout": "a"},))
    second = factor("second", ("layout",), ({"layout": "b"},))
    with pytest.raises(CandidateFamilyError, match="only one factor"):
        build_candidate_family(SOURCE, (first, second))


def test_stale_member_identity_is_rejected():
    family = build_candidate_family(
        SOURCE, (factor("layout", ("layout",), ({"layout": "a"},)),)
    )
    tampered = copy.deepcopy(family)
    tampered["members"][0]["bindings"]["layout"] = "hidden-change"
    with pytest.raises(CandidateFamilyError, match="stale identity"):
        validate_candidate_family(tampered)


def test_restriction_records_exclusions_and_is_not_a_view():
    family = build_candidate_family(
        SOURCE,
        (factor("layout", ("layout",), ({"layout": "a"}, {"layout": "b"})),),
    )
    keep = family["members"][0]["member_id"]
    result = restrict_candidate_family(family, (keep,), criterion="declared topology filter")
    assert result["operation"] == "restrict"
    assert result["retained_member_ids"] == [keep]
    assert len(result["excluded_member_ids"]) == 1
    assert result["restriction_id"].startswith("sha256:")


def test_view_preserves_source_link_and_does_not_prune():
    family = build_candidate_family(
        SOURCE, (factor("layout", ("layout",), ({"layout": "a"},)),)
    )
    view = candidate_family_view(family)
    assert view["operation"] == "view"
    assert view["source_family_id"] == family["family_id"]
    assert view["member_ids"] == [family["members"][0]["member_id"]]
    assert "retained_member_ids" not in view


def test_resource_bound_is_reported_not_collapsed_to_empty_family():
    too_many = ({"choice": str(index)} for index in range(257))
    with pytest.raises(CandidateFamilyError, match="supported bound"):
        factor("bounded", ("choice",), too_many)


@pytest.mark.parametrize("malformed", [None, "layout", 7])
def test_malformed_collections_raise_typed_error(malformed):
    with pytest.raises(CandidateFamilyError, match="collection"):
        factor("bounded", malformed, ({"layout": "a"},))
