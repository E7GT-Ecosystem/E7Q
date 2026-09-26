from fractions import Fraction

import pytest

from tools.run_joint_visible_effect_review import (
    SCHEMA, TaskFormatError, validate_task,
)


def task(rows=None):
    return {
        "schema": SCHEMA,
        "task_id": "private-task-01",
        "origin_ref": "private-source-hash",
        "source_intent": "sanitized real planning task",
        "rows": rows or [{"layout": "L0", "target": "T0", "coefficient": "1/2"}],
    }


def test_accepts_exact_signed_rational_rows_and_returns_typed_values():
    value = task([
        {"layout": "L0", "target": "T0", "coefficient": "1/2"},
        {"layout": "L1", "target": "T1", "coefficient": "-1/3"},
    ])
    _document, pairs, coefficients = validate_task(value)
    assert pairs == [("L0", "T0"), ("L1", "T1")]
    assert coefficients == [Fraction(1, 2), Fraction(-1, 3)]


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


def test_rejects_missing_real_task_provenance_fields():
    value = task()
    value["origin_ref"] = " "
    with pytest.raises(TaskFormatError, match="origin_ref"):
        validate_task(value)
