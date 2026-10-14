# SPDX-License-Identifier: Apache-2.0
"""Independent synthetic Q-A3 contract probes (no execution/backend evidence).

Authored from QA3-PACKAGE/2026-10-14/1 and the existing public Q-A1/Q-A2
contracts, without reading the realisation implementation.  Rehashing in
negative tests is deliberate: a digest alone must not certify membership.
"""
import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from e7q.ir.candidate_family import (
    assess_candidate_restriction,
    build_candidate_family,
    factor,
)
from e7q.ir.canonical import identified_digest
from e7q.ir.realisation import (
    PROFILE,
    TIE_POLICY,
    RealisationError,
    assess_realisation,
    build_realisation_request,
    validate_realisation_request,
    validate_realisation_result,
)
from e7q.ir.transformation_history import (
    build_transformation_history,
    transformation_step,
)


SOURCE = "sha256:" + "1" * 64
FOREIGN = "sha256:" + "f" * 64
EVIDENCE = "sha256:" + "e" * 64
LOW = -(2 ** 127)
HIGH = 2 ** 127 - 1
SCHEMA = Path(__file__).resolve().parents[1] / "schemas/e7q-ir-realisation-v0alpha1.schema.json"
OBJECTIVES = [
    {"id": "latency", "edition": "synthetic-1", "direction": "min", "unit": "ticks"},
    {"id": "quality", "edition": "synthetic-1", "direction": "max", "unit": "points"},
]


def rehash(record, identity_field):
    record[identity_field] = identified_digest(record, identity_field)
    return record


def rehash_request(request):
    rehash(request["objective_table"], "table_id")
    return rehash(request, "request_id")


def synthetic_family():
    return build_candidate_family(
        SOURCE,
        [factor("placement", ["layout", "target"], [
            {"layout": "line-a", "target": "backend-a"},
            {"layout": "line-b", "target": "backend-b"},
            {"layout": "line-c", "target": "backend-c"},
        ])],
        assumptions=["Synthetic inert identifiers only."],
        limitations=["No execution, feasibility or physical interpretation."],
    )


def linked_history(family, restriction, **step_overrides):
    residual = restriction["result_family"]
    kwargs = dict(
        index=0, kind="restrict", rule_id=restriction["criterion"]["id"],
        rule_edition=restriction["criterion"]["edition"],
        input_family_id=family["family_id"],
        admitted_member_ids=restriction["retained_member_ids"],
        excluded_member_ids=restriction["excluded_member_ids"],
        outcome=restriction["outcome"],
        output_family_id=residual["family_id"] if residual else None,
        message=restriction["message"],
    )
    kwargs.update(step_overrides)
    return build_transformation_history(
        family["family_id"], [transformation_step(**kwargs)],
        context="synthetic planning", inquiry="ordered objectives",
    )


def objective_rows(member_ids, vectors=None, objectives=None):
    objectives = copy.deepcopy(OBJECTIVES if objectives is None else objectives)
    vectors = vectors if vectors is not None else [(9, 2), (1, 4), (5, 8)]
    return [
        {"member_id": member_id, "values": [
            {"objective_id": objective["id"], "value": value, "evidence_ref": EVIDENCE}
            for objective, value in zip(objectives, vector)
        ]}
        for member_id, vector in zip(member_ids, vectors)
    ]


def request_kwargs(family, history, restriction, rows, objectives=None):
    return dict(
        source_family_id=family["family_id"], history_id=history["history_id"],
        restriction_id=restriction["restriction_id"] if restriction else None,
        input_residual_family_id=history["residual_family_id"],
        objectives=copy.deepcopy(OBJECTIVES if objectives is None else objectives),
        objective_rows=copy.deepcopy(rows), context=history["context"], inquiry=history["inquiry"],
    )


def synthetic_case(mode="all", vectors=None):
    family = synthetic_family()
    members = [member["member_id"] for member in family["members"]]
    keep = members if mode == "all" else members[:2] if mode == "partial" else []
    restriction = assess_candidate_restriction(
        family, keep, criterion_id="synthetic-domain", criterion_edition="1",
        criterion_text="retain the explicitly supplied synthetic domain",
    )
    history = linked_history(family, restriction)
    rows = objective_rows(keep, vectors) if keep else []
    request = build_realisation_request(**request_kwargs(family, history, restriction, rows))
    return request, family, history, restriction


def terminal_case(outcome, kind="restrict"):
    family = synthetic_family()
    step = transformation_step(
        index=0, kind=kind, rule_id="synthetic-domain", rule_edition="1",
        input_family_id=family["family_id"],
        admitted_member_ids=[member["member_id"] for member in family["members"]],
        outcome=outcome, message="Synthetic linked terminal declaration only.",
    )
    history = build_transformation_history(
        family["family_id"], [step], context="synthetic planning", inquiry="ordered objectives",
    )
    request = build_realisation_request(**request_kwargs(family, history, None, []))
    return request, family, history, None


@pytest.fixture(scope="module")
def schema_validator():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert len(schema["oneOf"]) == 2
    assert schema["$defs"]
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def checked_result(case, schema_validator, outcome):
    request, family, history, restriction = case
    assert validate_realisation_request(request) is None
    schema_validator.validate(request)
    result = assess_realisation(request, family, history, restriction)
    assert result["outcome"] == outcome
    schema_validator.validate(result)
    assert validate_realisation_result(result, request, family, history, restriction) is None
    assert result["result_id"] == identified_digest(result, "result_id")
    return result


def assert_no_selection(result):
    assert result["best_member_ids"] == []
    assert result["selected_member_id"] is None
    assert result["witness"] is None


def assert_error(outcome, function, *args, **kwargs):
    with pytest.raises(RealisationError) as error:
        function(*args, **kwargs)
    assert error.value.outcome == outcome


def rejected_assessment(case, outcome="invalid_input"):
    request, family, history, restriction = case
    result = assess_realisation(request, family, history, restriction)
    assert result["outcome"] == outcome
    assert_no_selection(result)
    return result


def test_profile_constants_and_canonical_replay_without_mutation(schema_validator):
    assert PROFILE == "e7q.ir.finite-integer-lexicographic/v0alpha1"
    assert TIE_POLICY == "retain_all_best"
    case = synthetic_case()
    before = copy.deepcopy(case)
    result = checked_result(case, schema_validator, "unique")
    assert assess_realisation(*case) == result
    assert case == before
    request = case[0]
    assert request["request_id"] == identified_digest(request, "request_id")
    assert request["objective_table"]["table_id"] == identified_digest(request["objective_table"], "table_id")
    witness = result["witness"]
    assert witness["witness_id"] == identified_digest(witness, "witness_id")
    assert witness["objective_table_id"] == request["objective_table"]["table_id"]
    assert witness["best_value_vector"] == [1, 4]
    assert witness["best_member_ids"] == result["best_member_ids"]


def test_builder_canonicalises_rows_and_values_without_mutating_arguments(schema_validator):
    request, family, history, restriction = synthetic_case()
    rows = copy.deepcopy(request["objective_table"]["rows"])
    rows.reverse()
    for row in rows:
        row["values"].reverse()
    kwargs = request_kwargs(family, history, restriction, rows)
    before = copy.deepcopy(kwargs)
    rebuilt = build_realisation_request(**kwargs)
    assert kwargs == before
    assert rebuilt == request
    assert checked_result((rebuilt, family, history, restriction), schema_validator, "unique") == assess_realisation(request, family, history, restriction)
    assert [row["member_id"] for row in rebuilt["objective_table"]["rows"]] == sorted(restriction["retained_member_ids"])
    assert all([v["objective_id"] for v in row["values"]] == [o["id"] for o in OBJECTIVES] for row in rebuilt["objective_table"]["rows"])


@pytest.mark.parametrize("mode", ["all", "partial", "none"])
def test_actual_q_a1_q_a2_subset_chain_and_correlations(mode, schema_validator):
    case = synthetic_case(mode)
    request, family, history, restriction = case
    assert len(family["members"]) == 3
    assert {(m["bindings"]["layout"], m["bindings"]["target"]) for m in family["members"]} == {
        ("line-a", "backend-a"), ("line-b", "backend-b"), ("line-c", "backend-c"),
    }
    result = checked_result(case, schema_validator, "empty" if mode == "none" else "unique")
    assert result["source_family_id"] == family["family_id"]
    assert result["history_id"] == history["history_id"]
    assert result["restriction_id"] == restriction["restriction_id"]
    if mode == "none":
        assert_no_selection(result)
        assert result["input_residual_family_id"] is None
        assert result["upstream_outcome"] == "empty"
        assert request["objective_table"]["rows"] == []
    else:
        residual = restriction["result_family"]["family_id"]
        assert residual == identified_digest(restriction["result_family"], "family_id")
        assert residual != family["family_id"]
        assert request["input_residual_family_id"] == history["residual_family_id"] == residual
        assert result["input_residual_family_id"] == result["witness"]["input_residual_family_id"] == residual
        winner = restriction["retained_member_ids"][1]
        assert result["best_member_ids"] == [winner]
        assert result["selected_member_id"] == winner
        # The middle digest wins: inventory sort order is not objective preference.
        assert winner != min(restriction["retained_member_ids"])
        assert winner != max(restriction["retained_member_ids"]) or mode == "partial"


def test_ties_retain_every_best_member_and_never_pick_digest(schema_validator):
    case = synthetic_case(vectors=[(1, 4), (9, 2), (1, 4)])
    result = checked_result(case, schema_validator, "ambiguous")
    members = case[3]["retained_member_ids"]
    assert result["best_member_ids"] == sorted([members[0], members[2]])
    assert result["selected_member_id"] is None
    assert result["witness"]["best_member_ids"] == result["best_member_ids"]
    assert result["witness"]["best_value_vector"] == [1, 4]


def test_objective_order_changes_identity_and_winner(schema_validator):
    first = synthetic_case(vectors=[(0, 0), (1, 9), (2, 3)])
    request, family, history, restriction = first
    objectives = list(reversed(copy.deepcopy(OBJECTIVES)))
    rows = copy.deepcopy(request["objective_table"]["rows"])
    second_request = build_realisation_request(**request_kwargs(family, history, restriction, rows, objectives))
    a = checked_result(first, schema_validator, "unique")
    b = checked_result((second_request, family, history, restriction), schema_validator, "unique")
    assert a["selected_member_id"] == restriction["retained_member_ids"][0]
    assert b["selected_member_id"] == restriction["retained_member_ids"][1]
    assert a["witness"]["best_value_vector"] == [0, 0]
    assert b["witness"]["best_value_vector"] == [9, 1]
    assert request["request_id"] != second_request["request_id"]
    assert request["objective_table"]["table_id"] != second_request["objective_table"]["table_id"]
    assert a["result_id"] != b["result_id"]


@pytest.mark.parametrize("direction,expected", [("min", 0), ("max", 2)])
def test_signed_integer_endpoints_and_direction(direction, expected, schema_validator):
    _, family, history, restriction = synthetic_case()
    objectives = [{"id": "integer", "edition": "1", "direction": direction, "unit": "count"}]
    rows = objective_rows(restriction["retained_member_ids"], [(LOW,), (0,), (HIGH,)], objectives)
    request = build_realisation_request(**request_kwargs(family, history, restriction, rows, objectives))
    result = checked_result((request, family, history, restriction), schema_validator, "unique")
    assert result["selected_member_id"] == restriction["retained_member_ids"][expected]
    assert result["witness"]["best_value_vector"] == [LOW if direction == "min" else HIGH]


@pytest.mark.parametrize("outcome", ["invalid_input", "domain_error", "unsupported", "resource_limit"])
def test_upstream_non_success_is_a_linked_declaration_only(outcome, schema_validator):
    case = terminal_case(outcome)
    before = copy.deepcopy(case)
    result = checked_result(case, schema_validator, outcome)
    assert_no_selection(result)
    assert result["upstream_outcome"] == outcome
    assert result["input_residual_family_id"] is None
    assert result["restriction_id"] is None
    assert result["source_family_id"] == case[1]["family_id"]
    assert result["history_id"] == case[2]["history_id"]
    assert case == before
    # A declared failed step does not accept fabricated restriction/residual links.
    for field in ("restriction_id", "input_residual_family_id"):
        forged = copy.deepcopy(case)
        forged[0][field] = FOREIGN
        rehash_request(forged[0])
        rejected_assessment(forged)


def test_failed_q_a1_unknown_member_must_not_be_replayed_as_empty(schema_validator):
    request, family, history, _ = terminal_case("invalid_input")
    failed = assess_candidate_restriction(
        family, [FOREIGN], criterion_id="synthetic-domain", criterion_edition="1",
        criterion_text="unknown member cannot be admitted",
    )
    assert failed["outcome"] == "invalid_input"
    assert failed["retained_member_ids"] == []
    replay = assess_candidate_restriction(
        family, failed["retained_member_ids"], criterion_id=failed["criterion"]["id"],
        criterion_edition=failed["criterion"]["edition"], criterion_text=failed["criterion"]["text"],
    )
    assert replay["outcome"] == "empty"  # Not reproduction of the original cause.
    result = rejected_assessment((request, family, history, failed))
    schema_validator.validate(result)
    assert validate_realisation_result(result, request, family, history, failed) is None
    # Even a correctly linked empty history must refuse the failed backing object.
    empty_request, _, empty_history, _ = synthetic_case("none")
    empty_request["restriction_id"] = failed["restriction_id"]
    rehash_request(empty_request)
    rejected_assessment((empty_request, family, empty_history, failed))


def test_wrong_history_kind_and_multistep_precede_terminal_pass_through(schema_validator):
    case = terminal_case("domain_error", kind="transform")
    result = assess_realisation(*case)
    assert result["outcome"] == "unsupported"
    assert_no_selection(result)
    schema_validator.validate(case[0])
    schema_validator.validate(result)
    assert validate_realisation_result(result, *case) is None
    request, family, history, restriction = synthetic_case()
    first = history["steps"][0]
    second = transformation_step(
        index=1, kind="restrict", rule_id="synthetic-next", rule_edition="1",
        input_family_id=history["residual_family_id"], admitted_member_ids=[],
        outcome="resource_limit", message="Synthetic second-step refusal.",
    )
    multiple = build_transformation_history(family["family_id"], [first, second], context=history["context"], inquiry=history["inquiry"])
    multi_request = build_realisation_request(**request_kwargs(family, multiple, None, []))
    multi_result = rejected_assessment((multi_request, family, multiple, None), "unsupported")
    schema_validator.validate(multi_request)
    schema_validator.validate(multi_result)
    # A canonical successful transform to an arbitrary output is not a restriction.
    arbitrary_step = transformation_step(
        index=0, kind="transform", rule_id="synthetic-transform", rule_edition="1",
        input_family_id=family["family_id"], admitted_member_ids=[],
        outcome="success", output_family_id=FOREIGN, message="Unbacked output declaration.",
    )
    arbitrary_history = build_transformation_history(
        family["family_id"], [arbitrary_step], context=history["context"], inquiry=history["inquiry"],
    )
    arbitrary_request = build_realisation_request(**request_kwargs(family, arbitrary_history, None, []))
    arbitrary_case = (arbitrary_request, family, arbitrary_history, None)
    arbitrary_result = rejected_assessment(arbitrary_case, "unsupported")
    schema_validator.validate(arbitrary_request)
    schema_validator.validate(arbitrary_result)
    assert validate_realisation_result(arbitrary_result, *arbitrary_case) is None


def test_nonlinked_failure_result_has_actual_schema_and_recomputable_body(schema_validator):
    case = synthetic_case()
    case[0]["source_family_id"] = FOREIGN
    rehash_request(case[0])
    schema_validator.validate(case[0])
    result = rejected_assessment(case)
    schema_validator.validate(result)
    assert validate_realisation_result(result, *case) is None
    # No unresolved backing identity can become a membership witness.
    assert result["input_residual_family_id"] is None


@pytest.mark.parametrize("field,alternative", [("profile", "synthetic.other/v1"), ("tie_policy", "pick_lowest_digest")])
def test_well_formed_unknown_profile_or_policy_is_unsupported(field, alternative, schema_validator):
    case = synthetic_case()
    case[0][field] = alternative
    rehash_request(case[0])
    schema_validator.validate(case[0])
    result = rejected_assessment(case, "unsupported")
    schema_validator.validate(result)
    assert result["input_residual_family_id"] is None
    assert validate_realisation_result(result, *case) is None


@pytest.mark.parametrize("winner_kind", ["foreign", "excluded", "retained_but_worse"])
def test_rehashed_false_winner_is_rejected(winner_kind):
    case = synthetic_case("partial")
    result = assess_realisation(*case)
    assert result["outcome"] == "unique"
    wrong = FOREIGN if winner_kind == "foreign" else case[3]["excluded_member_ids"][0] if winner_kind == "excluded" else case[3]["retained_member_ids"][0]
    result["best_member_ids"] = [wrong]
    result["selected_member_id"] = wrong
    result["witness"]["best_member_ids"] = [wrong]
    rehash(result["witness"], "witness_id")
    rehash(result, "result_id")
    assert_error("invalid_input", validate_realisation_result, result, *case)


def test_rehashed_tie_subset_and_implicit_unique_pick_are_rejected():
    case = synthetic_case(vectors=[(1, 4), (9, 2), (1, 4)])
    original = assess_realisation(*case)
    assert original["outcome"] == "ambiguous"
    for make_unique in (False, True):
        forged = copy.deepcopy(original)
        one = forged["best_member_ids"][:1]
        forged["best_member_ids"] = one
        forged["witness"]["best_member_ids"] = one
        if make_unique:
            forged["outcome"] = "unique"
            forged["selected_member_id"] = one[0]
        rehash(forged["witness"], "witness_id")
        rehash(forged, "result_id")
        assert_error("invalid_input", validate_realisation_result, forged, *case)


def test_rehashed_result_body_is_recomputed_not_just_authenticated():
    case = synthetic_case()
    result = assess_realisation(*case)
    mutations = [
        ("message", "A different but rehashed claim."),
        ("source_family_id", FOREIGN), ("history_id", FOREIGN),
        ("restriction_id", FOREIGN), ("input_residual_family_id", FOREIGN),
        ("request_id", FOREIGN), ("upstream_outcome", "empty"),
    ]
    for field, value in mutations:
        forged = copy.deepcopy(result)
        forged[field] = value
        rehash(forged, "result_id")
        assert_error("invalid_input", validate_realisation_result, forged, *case)
    for field, value in [("best_value_vector", [0, 0]), ("objective_table_id", FOREIGN), ("input_residual_family_id", FOREIGN)]:
        forged = copy.deepcopy(result)
        forged["witness"][field] = value
        rehash(forged["witness"], "witness_id")
        rehash(forged, "result_id")
        assert_error("invalid_input", validate_realisation_result, forged, *case)


@pytest.mark.parametrize("field", ["source_family_id", "history_id", "context", "inquiry", "input_residual_family_id", "restriction_id"])
def test_rehashed_wrong_request_binding_is_invalid(field):
    case = synthetic_case()
    case[0][field] = "different synthetic text" if field in {"context", "inquiry"} else FOREIGN
    rehash_request(case[0])
    rejected_assessment(case)


def test_canonical_history_must_match_restriction_rule_domain_outcome_and_output():
    request, family, history, restriction = synthetic_case("partial")
    all_members = [m["member_id"] for m in family["members"]]
    mismatches = [
        {"rule_id": "different-rule"}, {"rule_edition": "2"},
        {"admitted_member_ids": all_members, "excluded_member_ids": []},
        {"outcome": "empty", "admitted_member_ids": [], "excluded_member_ids": all_members, "output_family_id": None},
        {"output_family_id": FOREIGN},
    ]
    for overrides in mismatches:
        wrong_history = linked_history(family, restriction, **overrides)
        wrong_request = copy.deepcopy(request)
        wrong_request["history_id"] = wrong_history["history_id"]
        wrong_request["input_residual_family_id"] = wrong_history["residual_family_id"]
        rehash_request(wrong_request)
        rejected_assessment((wrong_request, family, wrong_history, restriction))


def test_full_restriction_replay_rejects_rehashed_forgery():
    request, family, history, restriction = synthetic_case("partial")
    for field in ("message", "limitations", "source_return", "excluded_member_ids", "result_family"):
        forged = copy.deepcopy(restriction)
        if field == "message":
            forged[field] = "Invented restriction claim."
        elif field == "limitations":
            forged[field] = []
        elif field == "source_return":
            forged[field]["required"] = False
        elif field == "excluded_member_ids":
            forged[field] = []
        else:
            forged[field]["member_ids"] = [FOREIGN]
            rehash(forged[field], "family_id")
        rehash(forged, "restriction_id")
        bound_request = copy.deepcopy(request)
        bound_request["restriction_id"] = forged["restriction_id"]
        rehash_request(bound_request)
        rejected_assessment((bound_request, family, history, forged))
    # Subset-only evidence cannot stand in for the full corrected restriction.
    rejected_assessment((request, family, history, restriction["result_family"]))
    rejected_assessment((request, family, history, None))


def test_stale_request_table_result_witness_and_backing_identities():
    case = synthetic_case()
    for field in ("request_id", "table_id"):
        forged = copy.deepcopy(case)
        target = forged[0] if field == "request_id" else forged[0]["objective_table"]
        target[field] = FOREIGN
        if field == "table_id":
            rehash(forged[0], "request_id")
        assert_error("invalid_input", validate_realisation_request, forged[0])
        rejected_assessment(forged)
    result = assess_realisation(*case)
    for field in ("result_id", "witness_id"):
        forged = copy.deepcopy(result)
        target = forged if field == "result_id" else forged["witness"]
        target[field] = FOREIGN
        if field == "witness_id":
            rehash(forged, "result_id")
        assert_error("invalid_input", validate_realisation_result, forged, *case)
    for index, field in [(1, "family_id"), (2, "history_id"), (3, "restriction_id")]:
        forged = copy.deepcopy(case)
        forged[index][field] = FOREIGN
        rejected_assessment(forged)


@pytest.mark.parametrize("mutation", ["missing_row", "duplicate_row", "foreign_row", "missing_value", "duplicate_value", "foreign_value"])
def test_complete_member_and_objective_coverage(mutation):
    case = synthetic_case()
    rows = case[0]["objective_table"]["rows"]
    if mutation == "missing_row":
        rows.pop()
    elif mutation == "duplicate_row":
        rows.append(copy.deepcopy(rows[0]))
    elif mutation == "foreign_row":
        rows[0]["member_id"] = FOREIGN
    elif mutation == "missing_value":
        rows[0]["values"].pop()
    elif mutation == "duplicate_value":
        rows[0]["values"].append(copy.deepcopy(rows[0]["values"][0]))
    else:
        rows[0]["values"][0]["objective_id"] = "foreign-objective"
    rehash_request(case[0])
    rejected_assessment(case)


@pytest.mark.parametrize("value", [True, 1.0, float("nan"), float("inf"), "1"])
def test_runtime_requires_exact_integer_not_json_schema_integer(value):
    request, family, history, restriction = synthetic_case()
    rows = copy.deepcopy(request["objective_table"]["rows"])
    rows[0]["values"][0]["value"] = value
    assert_error("invalid_input", build_realisation_request, **request_kwargs(family, history, restriction, rows))
    request["objective_table"]["rows"] = rows
    # Do not hash NaN/infinity: runtime must classify them before serialization.
    rejected_assessment((request, family, history, restriction))


def test_schema_integer_semantics_are_not_runtime_acceptance(schema_validator):
    case = synthetic_case()
    case[0]["objective_table"]["rows"][0]["values"][0]["value"] = 1.0
    rehash_request(case[0])
    schema_validator.validate(case[0])  # Draft 2020-12 accepts mathematically integral floats.
    assert_error("invalid_input", validate_realisation_request, case[0])
    rejected_assessment(case)


@pytest.mark.parametrize("value", [LOW - 1, HIGH + 1])
def test_adjacent_integer_overflow_is_resource_refusal(value, schema_validator):
    request, family, history, restriction = synthetic_case()
    rows = copy.deepcopy(request["objective_table"]["rows"])
    rows[0]["values"][0]["value"] = value
    assert_error("resource_limit", build_realisation_request, **request_kwargs(family, history, restriction, rows))
    request["objective_table"]["rows"] = rows
    rehash_request(request)
    result = rejected_assessment((request, family, history, restriction), "resource_limit")
    schema_validator.validate(result)
    assert validate_realisation_result(result, request, family, history, restriction) is None


def test_invalid_limit_declarations_and_actual_smaller_limit_refusals(schema_validator):
    request, family, history, restriction = synthetic_case()
    kwargs = request_kwargs(family, history, restriction, request["objective_table"]["rows"])
    for field, ceiling in [("max_candidates", 4096), ("max_objectives", 16)]:
        for value in (0, -1, True, ceiling + 1):
            assert_error("invalid_input", build_realisation_request, **kwargs, **{field: value})
    exact = build_realisation_request(**kwargs, max_candidates=3, max_objectives=2)
    checked_result((exact, family, history, restriction), schema_validator, "unique")
    for field, smaller in [("max_candidates", 2), ("max_objectives", 1)]:
        assert_error("resource_limit", build_realisation_request, **kwargs, **{field: smaller})
        bounded = copy.deepcopy(exact)
        bounded["limits"][field] = smaller
        rehash_request(bounded)
        result = rejected_assessment((bounded, family, history, restriction), "resource_limit")
        schema_validator.validate(result)


def test_utf8_byte_ceilings_and_surrogates_without_large_allocations():
    request, family, history, restriction = synthetic_case()
    kwargs = request_kwargs(family, history, restriction, request["objective_table"]["rows"])
    for field, limit in [("context", 1024), ("inquiry", 1024)]:
        accepted = dict(kwargs, **{field: "é" * (limit // 2)})
        assert validate_realisation_request(build_realisation_request(**accepted)) is None
        assert_error("resource_limit", build_realisation_request, **dict(kwargs, **{field: "é" * (limit // 2 + 1)}))
        assert_error("invalid_input", build_realisation_request, **dict(kwargs, **{field: "\ud800"}))
    for field in ("edition", "unit"):
        accepted = copy.deepcopy(kwargs)
        accepted["objectives"][0][field] = "é" * 64
        assert validate_realisation_request(build_realisation_request(**accepted)) is None
        oversized = copy.deepcopy(accepted)
        oversized["objectives"][0][field] += "é"
        assert_error("resource_limit", build_realisation_request, **oversized)
        malformed = copy.deepcopy(accepted)
        malformed["objectives"][0][field] = "\ud800"
        assert_error("invalid_input", build_realisation_request, **malformed)
    # The ASCII name boundary is independently checked, not Python character count.
    named = copy.deepcopy(kwargs)
    named["objectives"][0]["id"] = "a" * 128
    for row in named["objective_rows"]:
        row["values"][0]["objective_id"] = "a" * 128
    assert validate_realisation_request(build_realisation_request(**named)) is None
    for row in named["objective_rows"]:
        row["values"][0]["objective_id"] += "a"
    named["objectives"][0]["id"] += "a"
    assert_error("resource_limit", build_realisation_request, **named)


def test_objective_declarations_evidence_and_fixed_count_ceiling():
    request, family, history, restriction = synthetic_case()
    kwargs = request_kwargs(family, history, restriction, request["objective_table"]["rows"])
    for malformed in ([], [OBJECTIVES[0], OBJECTIVES[0]], [{"id": "bad name", "edition": "1", "direction": "min", "unit": "count"}]):
        assert_error("invalid_input", build_realisation_request, **dict(kwargs, objectives=copy.deepcopy(malformed)))
    for field, value in [("direction", "ascending"), ("edition", ""), ("unit", ""), ("id", "é")]:
        bad = copy.deepcopy(kwargs)
        bad["objectives"][0][field] = value
        assert_error("invalid_input", build_realisation_request, **bad)
    for evidence in ("sha256:" + "E" * 64, "sha256:" + "e" * 63, "http://example.invalid/provenance", None):
        bad = copy.deepcopy(kwargs)
        bad["objective_rows"][0]["values"][0]["evidence_ref"] = evidence
        assert_error("invalid_input", build_realisation_request, **bad)
    objectives = [{"id": f"o{i}", "edition": "1", "direction": "min", "unit": "count"} for i in range(16)]
    rows = objective_rows(restriction["retained_member_ids"], [tuple([i] * 16) for i in range(3)], objectives)
    assert validate_realisation_request(build_realisation_request(**request_kwargs(family, history, restriction, rows, objectives))) is None
    objectives.append({"id": "o16", "edition": "1", "direction": "min", "unit": "count"})
    rows = objective_rows(restriction["retained_member_ids"], [tuple([i] * 17) for i in range(3)], objectives)
    assert_error("resource_limit", build_realisation_request, **request_kwargs(family, history, restriction, rows, objectives))


def test_empty_and_terminal_branches_never_score_rows():
    for case in [synthetic_case("none"), terminal_case("domain_error")]:
        baseline = assess_realisation(*case)
        assert baseline["outcome"] in {"empty", "domain_error"}
        assert_no_selection(baseline)
        request, family, history, restriction = case
        for numeric in (0, HIGH):
            forged = copy.deepcopy(request)
            forged["objective_table"]["rows"] = objective_rows([family["members"][0]["member_id"]], [(numeric, numeric)])
            rehash_request(forged)
            rejected_assessment((forged, family, history, restriction))


def test_malformed_builtin_records_fail_with_typed_errors_not_attribute_errors():
    case = synthetic_case()
    for malformed in (None, [], {}, {"schema": []}):
        assert_error("invalid_input", validate_realisation_request, malformed)
        rejected_assessment((malformed, *case[1:]))
        assert_error("invalid_input", validate_realisation_result, malformed, *case)
    for index, field, malformed in [
        (1, "factors", None), (1, "factors", [{"alternatives": None}]),
        (2, "steps", None), (2, "steps", [None]),
        (2, "steps", [{"schema": "e7q.ir.transformation-step/v0alpha1", "rule": [], "domain": []}]),
        (3, "criterion", []), (3, "result_family", []),
    ]:
        forged = copy.deepcopy(case)
        forged[index][field] = malformed
        before = copy.deepcopy(forged)
        rejected_assessment(forged)
        assert forged == before
    for field in ("objectives", "objective_rows"):
        kwargs = request_kwargs(case[1], case[2], case[3], case[0]["objective_table"]["rows"])
        for malformed in (None, {}, [None]):
            assert_error("invalid_input", build_realisation_request, **dict(kwargs, **{field: malformed}))


def test_actual_schema_rejects_extra_properties_at_every_record_level(schema_validator):
    case = synthetic_case()
    result = assess_realisation(*case)
    for path in [(), ("limits",), ("objectives", 0), ("objective_table",), ("objective_table", "rows", 0), ("objective_table", "rows", 0, "values", 0)]:
        forged = copy.deepcopy(case[0])
        target = forged
        for component in path:
            target = target[component]
        target["extra"] = "not admitted"
        assert list(schema_validator.iter_errors(forged)), path
        rehash_request(forged)
        assert_error("invalid_input", validate_realisation_request, forged)
    for path in [(), ("witness",)]:
        forged = copy.deepcopy(result)
        target = forged if not path else forged["witness"]
        target["extra"] = "not admitted"
        assert list(schema_validator.iter_errors(forged)), path
        if path:
            rehash(forged["witness"], "witness_id")
        rehash(forged, "result_id")
        assert_error("invalid_input", validate_realisation_result, forged, *case)


def test_schema_outcome_specific_null_and_inventory_constraints(schema_validator):
    unique_case = synthetic_case()
    unique = assess_realisation(*unique_case)
    ambiguous = assess_realisation(*synthetic_case(vectors=[(1, 1)] * 3))
    empty = assess_realisation(*synthetic_case("none"))
    failed = assess_realisation(*terminal_case("domain_error"))
    probes = []
    for field in ("request_id", "source_family_id", "history_id", "restriction_id", "input_residual_family_id", "selected_member_id", "witness"):
        forged = copy.deepcopy(unique)
        forged[field] = None
        probes.append(forged)
    forged = copy.deepcopy(unique)
    forged["best_member_ids"] = []
    probes.append(forged)
    forged = copy.deepcopy(ambiguous)
    forged["selected_member_id"] = ambiguous["best_member_ids"][0]
    probes.append(forged)
    forged = copy.deepcopy(ambiguous)
    forged["best_member_ids"] = ambiguous["best_member_ids"][:1]
    probes.append(forged)
    for terminal in (empty, failed):
        for field, value in [("selected_member_id", FOREIGN), ("witness", unique["witness"]), ("best_member_ids", [FOREIGN]), ("input_residual_family_id", FOREIGN)]:
            forged = copy.deepcopy(terminal)
            forged[field] = value
            probes.append(forged)
    for forged in probes:
        assert list(schema_validator.iter_errors(forged)), forged
    for field in ("source_family_id", "history_id", "objectives", "objective_table", "limits"):
        forged = copy.deepcopy(unique_case[0])
        forged[field] = None
        assert list(schema_validator.iter_errors(forged)), field


@pytest.mark.parametrize("binding", ["x" * 16385, "😀" * 16385], ids=["long-ascii", "long-unicode"])
def test_valid_backing_binding_strings_keep_source_bounds(binding, schema_validator):
    from e7q.ir.candidate_family import validate_candidate_family

    family = build_candidate_family(
        SOURCE, [factor("placement", ["layout"], [{"layout": binding}])],
    )
    validate_candidate_family(family)
    restriction = assess_candidate_restriction(
        family, [family["members"][0]["member_id"]],
        criterion_id="domain", criterion_edition="1", criterion_text="synthetic",
    )
    assert restriction["outcome"] == "success"
    history = linked_history(family, restriction)
    request = build_realisation_request(**request_kwargs(
        family, history, restriction,
        objective_rows(restriction["retained_member_ids"], [(0, 0)]),
    ))
    result = assess_realisation(request, family, history, restriction)
    assert result["outcome"] == "unique"
    assert result["selected_member_id"] == family["members"][0]["member_id"]
    validate_realisation_result(result, request, family, history, restriction)
    schema_validator.validate(request)
    schema_validator.validate(result)
