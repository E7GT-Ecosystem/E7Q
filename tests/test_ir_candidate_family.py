# SPDX-License-Identifier: Apache-2.0
import copy
import json
from pathlib import Path

import pytest

from e7q.ir.candidate_family import (
    CandidateFamilyError,
    assess_candidate_restriction,
    build_candidate_family,
    candidate_family_view,
    candidate_family_view_v2,
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


def _two_member_family():
    return build_candidate_family(
        SOURCE,
        (factor("layout", ("layout",), ({"layout": "a"}, {"layout": "b"})),),
    )


def test_v2_restriction_has_versioned_bounded_criterion_and_source_return():
    family = _two_member_family()
    keep = family["members"][0]["member_id"]
    result = assess_candidate_restriction(
        family,
        (keep,),
        criterion_id="topology-filter",
        criterion_edition="2026-09-13.1",
        criterion_text="retain members admitted by the declared topology",
    )
    assert result["outcome"] == "success"
    assert result["criterion"]["edition"] == "2026-09-13.1"
    assert result["result_family"]["family_id"].startswith("sha256:")
    assert result["source_return"] == {
        "required": True,
        "source_family_id": family["family_id"],
    }
    assert len(result["excluded_member_ids"]) == 1


def test_v2_empty_is_distinct_from_invalid_input():
    family = _two_member_family()
    empty = assess_candidate_restriction(
        family, (), criterion_id="none", criterion_edition="1", criterion_text="retain none"
    )
    invalid = assess_candidate_restriction(
        family,
        ("sha256:" + "f" * 64,),
        criterion_id="unknown",
        criterion_edition="1",
        criterion_text="retain an unknown member",
    )
    assert empty["outcome"] == "empty"
    assert empty["retained_member_ids"] == []
    assert empty["result_family"] is None
    assert invalid["outcome"] == "invalid_input"


def test_v2_resource_limit_is_not_collapsed_to_empty_or_invalid():
    family = _two_member_family()
    too_many = ("sha256:" + f"{index:064x}" for index in range(65_537))
    result = assess_candidate_restriction(
        family,
        too_many,
        criterion_id="bounded",
        criterion_edition="1",
        criterion_text="exercise the declared input bound",
    )
    assert result["outcome"] == "resource_limit"
    assert result["retained_member_ids"] == []
    assert result["result_family"] is None


def test_v2_criterion_text_is_bounded():
    family = _two_member_family()
    result = assess_candidate_restriction(
        family,
        (),
        criterion_id="oversized",
        criterion_edition="1",
        criterion_text="x" * 1_025,
    )
    assert result["outcome"] == "invalid_input"
    assert result["criterion"] is None


def test_v2_view_declares_loss_and_source_return_without_restriction():
    family = _two_member_family()
    view = candidate_family_view_v2(family)
    assert view["operation"] == "view"
    assert view["preserves"]
    assert view["loses"]
    assert view["source_return"]["source_family_id"] == family["family_id"]
    assert "retained_member_ids" not in view


def test_resource_bound_is_reported_not_collapsed_to_empty_family():
    too_many = ({"choice": str(index)} for index in range(257))
    with pytest.raises(CandidateFamilyError, match="supported bound"):
        factor("bounded", ("choice",), too_many)


@pytest.mark.parametrize("malformed", [None, "layout", 7])
def test_malformed_collections_raise_typed_error(malformed):
    with pytest.raises(CandidateFamilyError, match="collection"):
        factor("bounded", malformed, ({"layout": "a"},))
