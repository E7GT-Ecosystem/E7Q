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
    validate_transformation_step,
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


@pytest.mark.parametrize("field", ["rule", "domain"])
@pytest.mark.parametrize("malformed", [None, 7, "text", [], [None], ["x"]])
def test_nested_rule_and_domain_require_objects(field, malformed):
    value = step()
    value[field] = malformed
    with pytest.raises(TransformationHistoryError, match="objects"):
        validate_transformation_step(value)
    with pytest.raises(TransformationHistoryError, match="objects"):
        build_transformation_history(D1, [value], context="c", inquiry="i")


@pytest.mark.parametrize("field", ["kind", "outcome"])
@pytest.mark.parametrize("malformed", [None, 7, "unknown", [], {}])
def test_step_enumerations_reject_unhashable_and_unknown_values(field, malformed):
    value = step()
    value[field] = malformed
    with pytest.raises(TransformationHistoryError, match="unsupported transformation"):
        validate_transformation_step(value)


@pytest.mark.parametrize("field", ["preserves", "loses", "limitations"])
@pytest.mark.parametrize("malformed", [None, 7, "text", [None], [[]], [{}]])
def test_malformed_declarations_are_typed(field, malformed):
    value = step()
    value[field] = malformed
    with pytest.raises(TransformationHistoryError):
        validate_transformation_step(value)


@pytest.mark.parametrize("field", ["admitted_member_ids", "excluded_member_ids"])
@pytest.mark.parametrize("malformed", [None, 7, "text", [None], [[]], ["unknown"]])
def test_malformed_domain_references_are_typed(field, malformed):
    value = step()
    value["domain"][field] = malformed
    with pytest.raises(TransformationHistoryError):
        validate_transformation_step(value)


@pytest.mark.parametrize("field", ["rule", "domain"])
def test_missing_nested_object_is_rejected(field):
    value = step()
    del value[field]
    with pytest.raises(TransformationHistoryError):
        validate_transformation_step(value)


def test_existing_declaration_member_and_history_bounds_remain_typed():
    value = step()
    value["preserves"] = ["declared"] * 129
    with pytest.raises(TransformationHistoryError, match="supported bound"):
        validate_transformation_step(value)
    value = step()
    value["domain"]["admitted_member_ids"] = [M1] * 65_537
    with pytest.raises(TransformationHistoryError, match="supported bound"):
        validate_transformation_step(value)
    with pytest.raises(TransformationHistoryError, match="supported bound"):
        build_transformation_history(D1, [step()] * 257, context="c", inquiry="i")


def test_unknown_family_reference_cannot_continue_chain():
    with pytest.raises(TransformationHistoryError, match="continue"):
        build_transformation_history(D1, [step(source=D3)], context="c", inquiry="i")


@pytest.mark.parametrize("outcome", ["invalid_input", "domain_error", "unsupported", "resource_limit"])
def test_declared_failure_outcomes_remain_distinct(outcome):
    history = build_transformation_history(D1, [step(outcome=outcome)], context="c", inquiry="i")
    assert history["terminal_outcome"] == outcome
    assert history["residual_family_id"] is None


@pytest.mark.parametrize("field", ["id", "edition"])
@pytest.mark.parametrize("malformed", [None, 7, "", [], {}])
def test_malformed_rule_fields_are_typed(field, malformed):
    value = step()
    value["rule"][field] = malformed
    with pytest.raises(TransformationHistoryError):
        validate_transformation_step(value)


def test_pre_b1_canonical_restriction_view_step_and_history_bytes_and_ids():
    from e7q.ir.canonical import canonical_bytes
    from e7q.ir.candidate_family import (
        candidate_family_view, candidate_family_view_v2, restrict_candidate_family,
    )

    # Golden bytes captured from accepted main, NOT the B1-modified runtime:
    # 86447771544e836222847ed04b0236cc27f2881b, isolated qr2_baseline namespace.
    # git-show source SHA-256: candidate_family 035b56a0bb9240f1ba2cd629a7f129e46c15a0b4b034f635de95826ddb7ae0d4;
    # transformation_history 33884950ab843df12614acd2f68d3ed683ccaf208150b6a96166c6dbf1f2f617;
    # canonical a13acfcabbdfa86fec9dda073850d5c3eb5d550b2e9911a5b44e4d6e89f3e997.
    # Capture: source 1*64, layout a/b, first canonical member, criterion below.
    # Pretty-JSON capture SHA-256: 8f714df239b3d20ecbb2ad9d7b0441a2d64bbba11c986f7923071a1bb7e167cf.
    # Fixed byte literals are durable; test execution never regenerates them.
    expected = {
        'legacy_restriction': (
            b'{"criterion":"declared topology filter","excluded_member_ids":["sha256:989bcfc42b93537a0ec00285f46ee'
            b'2ea6c686a68929bd8911cb32234e29a2a85"],"limitations":["Restriction records exclusion; it is not a sou'
            b'rce-preserving view.","No feasibility, optimality, or quantum-semantic conclusion is established."],'
            b'"operation":"restrict","restriction_id":"sha256:ee7756fbd7835c8c7d6623a7af57b1d42a684db99cf2e595479d'
            b'24c761e5267a","retained_member_ids":["sha256:21ecb82b206638676b5721bf4c64ba42afd55fb4c1b54aef784ae37'
            b'64c234586"],"schema":"e7q.ir.candidate-restriction/v0alpha1","source_family_id":"sha256:e438ca5798c2'
            b'70d3f296571f71c88ffcdb749efc3b41f6b67655374250502cf9"}'
        ),
        'restriction': (
            b'{"criterion":{"edition":"1","id":"e7q.topology-filter","text":"retain the declared topology domain"}'
            b',"excluded_member_ids":["sha256:989bcfc42b93537a0ec00285f46ee2ea6c686a68929bd8911cb32234e29a2a85"],"'
            b'limitations":["Restriction records exclusion; it is not a source-preserving view.","No feasibility, '
            b'optimality, or quantum-semantic conclusion is established."],"message":"Restriction retained a non-e'
            b'mpty subset of the source family.","operation":"restrict","outcome":"success","restriction_id":"sha2'
            b'56:76bbbda045480571bfdf16e7e30de97e8f8f6b1aad21cd07556bd9b3fc61956a","result_family":{"family_id":"s'
            b'ha256:ece1024ff4302118bc7b8139d8efd277312fbd48b747b68fa8d948652fb7d46a","member_ids":["sha256:21ecb8'
            b'2b206638676b5721bf4c64ba42afd55fb4c1b54aef784ae3764c234586"],"schema":"e7q.ir.candidate-family-subse'
            b't/v0alpha1","source_family_id":"sha256:e438ca5798c270d3f296571f71c88ffcdb749efc3b41f6b67655374250502'
            b'cf9"},"retained_member_ids":["sha256:21ecb82b206638676b5721bf4c64ba42afd55fb4c1b54aef784ae3764c23458'
            b'6"],"schema":"e7q.ir.candidate-restriction/v0alpha2","source_family_id":"sha256:e438ca5798c270d3f296'
            b'571f71c88ffcdb749efc3b41f6b67655374250502cf9","source_return":{"required":true,"source_family_id":"s'
            b'ha256:e438ca5798c270d3f296571f71c88ffcdb749efc3b41f6b67655374250502cf9"}}'
        ),
        'legacy_view': (
            b'{"dimensions":["layout"],"factor_count":1,"limitations":["This inventory view does not select, ident'
            b'ify, or restrict candidates."],"member_count":2,"member_ids":["sha256:21ecb82b206638676b5721bf4c64ba'
            b'42afd55fb4c1b54aef784ae3764c234586","sha256:989bcfc42b93537a0ec00285f46ee2ea6c686a68929bd8911cb32234'
            b'e29a2a85"],"operation":"view","schema":"e7q.ir.candidate-family-view/v0alpha1","source_family_id":"s'
            b'ha256:e438ca5798c270d3f296571f71c88ffcdb749efc3b41f6b67655374250502cf9","view_id":"sha256:a451f0eb23'
            b'd8fdb8852c15c97b7d25aa3894a857b38819e6d9c346c1f4a8fda5"}'
        ),
        'view': (
            b'{"dimensions":["layout"],"factor_count":1,"limitations":["This inventory view does not select, ident'
            b'ify, or restrict candidates."],"loses":["alternative bindings","assumption and limitation text","fac'
            b'tor correlation structure beyond the listed inventory"],"member_count":2,"member_ids":["sha256:21ecb'
            b'82b206638676b5721bf4c64ba42afd55fb4c1b54aef784ae3764c234586","sha256:989bcfc42b93537a0ec00285f46ee2e'
            b'a6c686a68929bd8911cb32234e29a2a85"],"operation":"view","preserves":["factor and member inventory","m'
            b'ember identities","source-family linkage"],"schema":"e7q.ir.candidate-family-view/v0alpha2","source_'
            b'family_id":"sha256:e438ca5798c270d3f296571f71c88ffcdb749efc3b41f6b67655374250502cf9","source_return"'
            b':{"required":true,"source_family_id":"sha256:e438ca5798c270d3f296571f71c88ffcdb749efc3b41f6b67655374'
            b'250502cf9"},"view_id":"sha256:11305adc9a918759d8afa4bc93ddbddd8f019790256f9f864c66c7c729e0cce1"}'
        ),
        'step': (
            b'{"domain":{"admitted_member_ids":["sha256:21ecb82b206638676b5721bf4c64ba42afd55fb4c1b54aef784ae3764c'
            b'234586"],"excluded_member_ids":["sha256:989bcfc42b93537a0ec00285f46ee2ea6c686a68929bd8911cb32234e29a'
            b'2a85"]},"index":0,"input_family_id":"sha256:e438ca5798c270d3f296571f71c88ffcdb749efc3b41f6b676553742'
            b'50502cf9","kind":"restrict","limitations":[],"loses":["excluded candidates"],"message":"Restriction '
            b'retained a non-empty subset of the source family.","outcome":"success","output_family_id":"sha256:ec'
            b'e1024ff4302118bc7b8139d8efd277312fbd48b747b68fa8d948652fb7d46a","preserves":[],"rule":{"edition":"1"'
            b',"id":"e7q.topology-filter"},"schema":"e7q.ir.transformation-step/v0alpha1","step_id":"sha256:a9bef1'
            b'd07513886db2ccef6c668ac48392af4e0cc54adca4ee44de0d73360a9b"}'
        ),
        'history': (
            b'{"context":"compiler","history_id":"sha256:c6b216eb3672c515522af72b114bac7d3d6a07549cb34815c89a9300c'
            b'35e55b9","inquiry":"topology","limitations":["This record preserves declared order and domains; it d'
            b'oes not prove rule correctness.","No feasibility, optimality, hardware, fidelity, or quantum-advanta'
            b'ge conclusion is established."],"residual_family_id":"sha256:ece1024ff4302118bc7b8139d8efd277312fbd4'
            b'8b747b68fa8d948652fb7d46a","schema":"e7q.ir.transformation-history/v0alpha1","source_family_id":"sha'
            b'256:e438ca5798c270d3f296571f71c88ffcdb749efc3b41f6b67655374250502cf9","steps":[{"domain":{"admitted_'
            b'member_ids":["sha256:21ecb82b206638676b5721bf4c64ba42afd55fb4c1b54aef784ae3764c234586"],"excluded_me'
            b'mber_ids":["sha256:989bcfc42b93537a0ec00285f46ee2ea6c686a68929bd8911cb32234e29a2a85"]},"index":0,"in'
            b'put_family_id":"sha256:e438ca5798c270d3f296571f71c88ffcdb749efc3b41f6b67655374250502cf9","kind":"res'
            b'trict","limitations":[],"loses":["excluded candidates"],"message":"Restriction retained a non-empty '
            b'subset of the source family.","outcome":"success","output_family_id":"sha256:ece1024ff4302118bc7b813'
            b'9d8efd277312fbd48b747b68fa8d948652fb7d46a","preserves":[],"rule":{"edition":"1","id":"e7q.topology-f'
            b'ilter"},"schema":"e7q.ir.transformation-step/v0alpha1","step_id":"sha256:a9bef1d07513886db2ccef6c668'
            b'ac48392af4e0cc54adca4ee44de0d73360a9b"}],"terminal_outcome":"success"}'
        ),
    }
    family = build_candidate_family(
        D1, (factor("layout", ("layout",), ({"layout": "a"}, {"layout": "b"})),)
    )
    retained = family["members"][0]["member_id"]
    restriction = assess_candidate_restriction(
        family, [retained], criterion_id="e7q.topology-filter", criterion_edition="1",
        criterion_text="retain the declared topology domain",
    )
    record = transformation_step(
        index=0, kind="restrict", rule_id="e7q.topology-filter", rule_edition="1",
        input_family_id=family["family_id"], admitted_member_ids=restriction["retained_member_ids"],
        excluded_member_ids=restriction["excluded_member_ids"], outcome="success",
        output_family_id=restriction["result_family"]["family_id"],
        loses=("excluded candidates",), message=restriction["message"],
    )
    actual = {
        "legacy_restriction": restrict_candidate_family(
            family, [retained], criterion="declared topology filter"
        ),
        "restriction": restriction,
        "legacy_view": candidate_family_view(family),
        "view": candidate_family_view_v2(family),
        "step": record,
        "history": build_transformation_history(
            family["family_id"], [record], context="compiler", inquiry="topology"
        ),
    }
    for name, value in actual.items():
        assert canonical_bytes(value) == expected[name], name
        id_field = {
            "legacy_restriction": "restriction_id", "restriction": "restriction_id",
            "legacy_view": "view_id", "view": "view_id", "step": "step_id", "history": "history_id",
        }[name]
        assert value[id_field] == json.loads(expected[name])[id_field], name


def _maintenance_step(**overrides):
    kwargs = dict(
        index=0, kind="transform", rule_id="e7q.lower", rule_edition="1",
        input_family_id=D1, admitted_member_ids=[M1], outcome="success",
        output_family_id=D2, message="declared",
    )
    kwargs.update(overrides)
    return transformation_step(**kwargs)


@pytest.mark.parametrize("field", ["kind", "outcome"])
@pytest.mark.parametrize("malformed", [None, 7, [], {}, b"transform", "unknown"])
def test_maintenance_direct_step_enumerations_are_typed(field, malformed):
    with pytest.raises(TransformationHistoryError, match="unsupported transformation"):
        _maintenance_step(**{field: malformed})


@pytest.mark.parametrize("malformed", ["\ud800", "prefix\udfff"])
def test_maintenance_direct_step_surrogate_edition_is_typed(malformed):
    with pytest.raises(TransformationHistoryError):
        _maintenance_step(rule_edition=malformed)


@pytest.mark.parametrize("text", ["é", "e\u0301", "\U0001f680"])
def test_maintenance_valid_unicode_rule_edition_keeps_bytes_and_identity(text):
    from e7q.ir.canonical import canonical_bytes, identified_digest

    value = _maintenance_step(rule_edition=text)
    assert value["rule"]["edition"] == text
    assert text.encode("utf-8") in canonical_bytes(value)
    assert value["step_id"] == identified_digest(value, "step_id")
    validate_transformation_step(value)


@pytest.mark.parametrize("field", [
    "admitted_member_ids", "excluded_member_ids", "preserves", "loses", "limitations",
])
def test_maintenance_direct_step_bytes_collections_are_typed(field):
    with pytest.raises(TransformationHistoryError, match="collection"):
        _maintenance_step(**{field: b"collection"})
