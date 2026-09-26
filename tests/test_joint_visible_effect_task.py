from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json

import pytest

from tools.run_joint_visible_effect_review import (
    FILTER_IDENTITIES, ORACLE_SCHEMA, SCHEMA, TaskFormatError,
    check_success_oracle, comparison_disposition, load_oracle,
    task_scope_limit, validate_task,
)


def task(rows=None):
    return {
        "schema": SCHEMA,
        "task_kind": "real_workflow",
        "task_id": "private-task-01",
        "origin_ref": "private-source-hash",
        "source_intent": "sanitized real planning task",
        "dimension_mapping": {
            "layout": {"L0": "local option alpha", "L1": "local option beta"},
            "target": {"T0": "target group gamma", "T1": "target group delta"},
        },
        "filter_rules": [
            {**FILTER_IDENTITIES[0], "description": "real task rule one"},
            {**FILTER_IDENTITIES[1], "description": "real task rule two"},
        ],
        "expected_result": {"ref": "private-oracle.json", "sha256": "a" * 64},
        "rows": rows or [{"layout": "L0", "target": "T0", "coefficient": "1/2"}],
    }


def test_accepts_exact_signed_rational_rows_and_labels_result_as_real_task():
    value = task([
        {"layout": "L0", "target": "T0", "coefficient": "1/2"},
        {"layout": "L1", "target": "T1", "coefficient": "-1/3"},
    ])
    document, pairs, coefficients = validate_task(value)
    assert document["task_kind"] == "real_workflow"
    assert pairs == [("L0", "T0"), ("L1", "T1")]
    assert coefficients == [Fraction(1, 2), Fraction(-1, 3)]
    scope = task_scope_limit(document)
    assert "real-workflow task" in scope
    assert "synthetic" not in scope
    # Inherited run_case limitation text is overridden for a real task input.
    assert scope == "Finite real-workflow task 'private-task-01' as declared in the frozen input; one-task machine replay only, with no human reviewer timing or decision."


def test_rejects_synthetic_task_label_instead_of_treating_it_as_real():
    value = task()
    value["task_kind"] = "synthetic_fixture"
    with pytest.raises(TaskFormatError, match="real_workflow"):
        validate_task(value)


@pytest.mark.parametrize("bad_coefficient", ["0", "2/4", "1/0", "not-a-rational"])
def test_rejects_zero_noncanonical_or_invalid_coefficients(bad_coefficient):
    with pytest.raises(TaskFormatError):
        validate_task(task([{"layout": "L0", "target": "T0", "coefficient": bad_coefficient}]))


def test_rejects_duplicate_pairs_and_non_string_dimensions():
    duplicate = task([
        {"layout": "L0", "target": "T0", "coefficient": "1/2"},
        {"layout": "L0", "target": "T0", "coefficient": "1/3"},
    ])
    with pytest.raises(TaskFormatError, match="duplicates"):
        validate_task(duplicate)
    malformed = task([{"layout": ["L0"], "target": "T0", "coefficient": "1/2"}])
    with pytest.raises(TaskFormatError, match="L0/L1"):
        validate_task(malformed)


def test_requires_frozen_mapping_and_exact_ordered_filter_identities():
    value = task()
    value["dimension_mapping"]["layout"]["L0"] = value["dimension_mapping"]["layout"]["L1"]
    with pytest.raises(TaskFormatError, match="meanings must be distinct"):
        validate_task(value)
    value = task()
    value["filter_rules"][0]["rule_id"] = "some-other-rule/v1"
    with pytest.raises(TaskFormatError, match="rule_id"):
        validate_task(value)
    value = task()
    value["filter_rules"].reverse()
    with pytest.raises(TaskFormatError, match="stage"):
        validate_task(value)


def test_requires_provenance_and_hashed_oracle_reference():
    value = task()
    value["origin_ref"] = " "
    with pytest.raises(TaskFormatError, match="origin_ref"):
        validate_task(value)
    value = task()
    value["expected_result"]["sha256"] = "bad-hash"
    with pytest.raises(TaskFormatError, match="sha256"):
        validate_task(value)


def test_oracle_bytes_are_checked_against_the_frozen_sha256(tmp_path):
    value = task()
    oracle = {
        "schema": ORACLE_SCHEMA,
        "task_id": value["task_id"],
        "terminal_status": "success",
        "retained": [{"layout": "L0", "target": "T0", "coefficient": "1/2"}],
        "first_excluded": [{"layout": "L1", "target": "T1", "coefficient": "1/2"}],
        "second_excluded": [],
        "exclusion_reasons": [{
            "layout": "L1", "target": "T1",
            "rule_id": FILTER_IDENTITIES[0]["rule_id"], "reason": "fails the first task filter",
        }],
    }
    raw = json.dumps(oracle, sort_keys=True).encode()
    value["expected_result"]["sha256"] = sha256(raw).hexdigest()
    path = tmp_path / "oracle.json"
    path.write_bytes(raw)
    loaded, checked_sha = load_oracle(value, path)
    assert loaded["terminal_status"] == "success"
    assert checked_sha == value["expected_result"]["sha256"]
    path.write_bytes(raw + b" ")
    with pytest.raises(TaskFormatError, match="do not match"):
        load_oracle(value, path)


def test_resource_limit_has_separate_disposition_and_no_decision_comparison():
    assert comparison_disposition("resource_limit") == (
        "separate_resource_limit_outcome_no_decision_comparison"
    )
    assert comparison_disposition("success") == "compare_retained_and_excluded_sets"
    assert comparison_disposition("unsupported").startswith("not_comparable_terminal_outcome")
    oracle = {"terminal_status": "resource_limit"}
    replay = {"e7c_source_result": {"terminal_outcome": {"tag": "resource_limit"}}}
    result = check_success_oracle(oracle, replay)
    assert result["status"] == "separate_resource_limit_outcome_no_decision_comparison"
    assert "retained_and_exclusion_sets_match_oracle" not in result
