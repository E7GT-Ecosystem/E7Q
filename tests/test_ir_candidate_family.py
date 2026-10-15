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


@pytest.mark.parametrize("malformed", [None, "layout", 7, b"layout"])
def test_malformed_collections_raise_typed_error(malformed):
    with pytest.raises(CandidateFamilyError, match="collection"):
        factor("bounded", malformed, ({"layout": "a"},))


@pytest.mark.parametrize("malformed", [None, 7, "alternatives", [], [None], [7], ["x"], [[]], [{"bindings": None}]])
def test_nested_alternatives_are_typed_invalid_not_empty(malformed):
    family = _two_member_family()
    family["factors"][0]["alternatives"] = malformed
    with pytest.raises(CandidateFamilyError):
        validate_candidate_family(family)
    result = assess_candidate_restriction(
        family, (), criterion_id="none", criterion_edition="1", criterion_text="retain none"
    )
    assert result["outcome"] == "invalid_input"
    assert result["result_family"] is None
    assert result["retained_member_ids"] == []


@pytest.mark.parametrize("field", ["factors", "assumptions", "limitations"])
@pytest.mark.parametrize("malformed", [None, 7, "text", [None], [[]], [{}]])
def test_family_nested_collections_fail_with_typed_error(field, malformed):
    family = _two_member_family()
    family[field] = malformed
    with pytest.raises(CandidateFamilyError):
        validate_candidate_family(family)


def test_nested_alternatives_enforce_existing_bound_before_reconstruction():
    family = _two_member_family()
    family["factors"][0]["alternatives"] = [family["factors"][0]["alternatives"][0]] * 257
    result = assess_candidate_restriction(
        family, (), criterion_id="bounded", criterion_edition="1", criterion_text="retain none"
    )
    assert result["outcome"] == "resource_limit"
    assert result["result_family"] is None


@pytest.mark.parametrize("malformed", [None, 7, "text", [[]], [{}], ["unknown"]])
def test_malformed_retained_references_are_typed_in_both_editions(malformed):
    family = _two_member_family()
    with pytest.raises(CandidateFamilyError):
        restrict_candidate_family(family, malformed, criterion="declared")
    result = assess_candidate_restriction(
        family, malformed, criterion_id="filter", criterion_edition="1", criterion_text="declared"
    )
    assert result["outcome"] == "invalid_input"
    assert result["result_family"] is None


def test_legacy_duplicate_references_preserve_existing_identity():
    family = _two_member_family()
    retained = family["members"][0]["member_id"]
    assert restrict_candidate_family(family, [retained] * 65_537, criterion="declared") == (
        restrict_candidate_family(family, [retained], criterion="declared")
    )


def test_valid_family_keeps_accepted_main_identity():
    # Captured from accepted main 86447771544e836222847ed04b0236cc27f2881b.
    assert _two_member_family()["family_id"] == (
        "sha256:e438ca5798c270d3f296571f71c88ffcdb749efc3b41f6b67655374250502cf9"
    )


def test_nested_alternative_stream_stops_after_one_overflow_observation():
    from e7q.ir.candidate_family import MAX_ALTERNATIVES_PER_FACTOR

    class GuardedAlternatives:
        def __init__(self, alternative):
            self.alternative = alternative
            self.consumed = 0

        def __iter__(self):
            return self

        def __next__(self):
            # A regression cannot hang: the first extra read fails immediately.
            if self.consumed >= MAX_ALTERNATIVES_PER_FACTOR + 1:
                raise AssertionError("alternative stream read past the overflow observation")
            self.consumed += 1
            return self.alternative

    family = _two_member_family()
    stream = GuardedAlternatives(family["factors"][0]["alternatives"][0])
    family["factors"][0]["alternatives"] = stream
    result = assess_candidate_restriction(
        family, (), criterion_id="bounded", criterion_edition="1", criterion_text="retain none"
    )
    assert MAX_ALTERNATIVES_PER_FACTOR == 256
    assert stream.consumed == MAX_ALTERNATIVES_PER_FACTOR + 1
    assert result["outcome"] == "resource_limit"
    assert result["retained_member_ids"] == []
    assert result["result_family"] is None


def test_maintenance_member_product_refusal_is_resource_before_expansion(monkeypatch):
    from e7q.ir import candidate_family as candidate

    factors = [
        factor(name, [name], [{name: str(index)} for index in range(count)])
        for name, count in (("first", 256), ("second", 256), ("third", 2))
    ]

    def forbidden_expansion(*args, **kwargs):
        raise AssertionError("oversized Cartesian product must not be expanded")

    family = _two_member_family()
    monkeypatch.setattr(candidate, "product", forbidden_expansion)
    with pytest.raises(CandidateFamilyError, match="supported member bound"):
        build_candidate_family(SOURCE, factors)
    family["factors"] = factors
    result = assess_candidate_restriction(
        family, (), criterion_id="bounded", criterion_edition="1", criterion_text="retain none"
    )
    assert result["outcome"] == "resource_limit"
    assert result["criterion"] is None
    assert result["retained_member_ids"] == result["excluded_member_ids"] == []
    assert result["result_family"] is None


@pytest.mark.parametrize("field", ["criterion_edition", "criterion_text"])
@pytest.mark.parametrize("malformed", ["\ud800", "prefix\udfff"])
def test_maintenance_surrogate_criterion_is_typed_invalid(field, malformed):
    kwargs = dict(criterion_id="filter", criterion_edition="1", criterion_text="declared")
    kwargs[field] = malformed
    result = assess_candidate_restriction(_two_member_family(), (), **kwargs)
    assert result["outcome"] == "invalid_input"
    assert result["criterion"] is None
    assert result["retained_member_ids"] == result["excluded_member_ids"] == []
    assert result["result_family"] is None


@pytest.mark.parametrize("text", ["é", "e\u0301", "\U0001f680"])
def test_maintenance_valid_unicode_criterion_keeps_bytes_and_identity(text):
    from e7q.ir.canonical import canonical_bytes, identified_digest

    family = _two_member_family()
    result = assess_candidate_restriction(
        family, [family["members"][0]["member_id"]], criterion_id="filter",
        criterion_edition=text, criterion_text=text,
    )
    assert result["outcome"] == "success"
    assert result["criterion"] == {"id": "filter", "edition": text, "text": text}
    assert text.encode("utf-8") in canonical_bytes(result)
    assert result["restriction_id"] == identified_digest(result, "restriction_id")


@pytest.mark.parametrize("malformed", [None, 7, b"alternatives", [], [None], [7], [[]]])
def test_maintenance_direct_factor_rejects_malformed_alternatives(malformed):
    with pytest.raises(CandidateFamilyError):
        factor("layout", ["layout"], malformed)


@pytest.mark.parametrize("field", ["factors", "assumptions", "limitations"])
def test_maintenance_bytes_family_collections_are_typed(field):
    family = _two_member_family()
    family[field] = b"collection"
    with pytest.raises(CandidateFamilyError, match="collection"):
        validate_candidate_family(family)


def test_maintenance_bytes_retained_references_are_typed_in_both_editions():
    family = _two_member_family()
    with pytest.raises(CandidateFamilyError):
        restrict_candidate_family(family, b"member", criterion="declared")
    result = assess_candidate_restriction(
        family, b"member", criterion_id="filter", criterion_edition="1", criterion_text="declared"
    )
    assert result["outcome"] == "invalid_input"
    assert result["result_family"] is None
