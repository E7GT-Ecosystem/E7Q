"""Opt-in product pilot checks using the exact pinned E7C source and IR code."""
from __future__ import annotations

import copy
from fractions import Fraction
import importlib.util
import os
from pathlib import Path

import pytest

from e7q.ir.canonical import canonical_bytes
from e7q.ir.e7c_joint_pilot import MappingAdmission, map_joint, validate_mapping
_runner_file = Path(__file__).resolve().parents[1] / "tools" / "run_e7c_joint_pilot.py"
_runner_spec = importlib.util.spec_from_file_location("e7q_joint_pilot_runner", _runner_file)
_runner = importlib.util.module_from_spec(_runner_spec)
_runner_spec.loader.exec_module(_runner)
import_e7c, make_joint, output_cases = _runner.import_e7c, _runner.make_joint, _runner.output_cases


@pytest.fixture(scope="module")
def e7c():
    # No fallback or skip: CI must check out the pinned repository explicitly.
    return import_e7c(Path(os.environ["E7C_ROOT"]))


def test_saved_replays_and_distinct_empty_outcome(e7c, tmp_path):
    cases = output_cases(Path(os.environ["E7C_ROOT"]), tmp_path)
    saved = Path(__file__).resolve().parents[1] / "fixtures" / "e7c-joint-pilot"
    for case in cases:
        assert (tmp_path / (case["case"] + ".json")).read_bytes() == (
            saved / (case["case"] + ".json")).read_bytes()
        assert case["e7c_source_transition_events"] == case["ir_transition_events"]
    assert (tmp_path / "hostile_mutations.json").read_bytes() == (
        saved / "hostile_mutations.json").read_bytes()
    assert (tmp_path / "manifest.json").read_bytes() == (saved / "manifest.json").read_bytes()
    assert cases[0]["lossy_marginal_cartesian"] == cases[1]["lossy_marginal_cartesian"]
    assert cases[0]["full_correlated_table"] != cases[1]["full_correlated_table"]
    assert cases[1]["e7c_source_result"]["terminal_outcome"]["tag"] == "success"
    assert cases[1]["e7c_source_result"]["terminal_outcome"]["value"]["retained"] == []
    assert cases[1]["q_a1_restrictions"]["composed_final_restriction"]["outcome"] == "empty"
    assert cases[1]["q_a1_restrictions"]["composed_final_restriction"]["result_family"] is None
    failed = cases[2]
    assert failed["e7c_source_result"]["witness"]["second_started"] is True
    assert failed["e7c_source_result"]["resource_progress"]["completed_steps"] == 4
    assert len(failed["e7c_source_result"]["ordered_ledger"]) == 3
    assert failed["q_a1_restrictions"] is None


def test_mapping_rechecks_actual_source_admission_and_identity(e7c):
    config, joint, source, _ir, _nested = e7c
    value = make_joint(config, joint, [("L0", "T0"), ("L1", "T1")])
    doc = source.document(value)
    mapping, family = map_joint(doc, admit_source=source.admit)
    for bad in ("resource", "foreign_field", "source_order", "rational", "mapping"):
        altered = copy.deepcopy(doc)
        changed = copy.deepcopy(mapping)
        if bad == "resource": altered["first"]["resource_policy"]["step_bound"] = -1
        if bad == "foreign_field": altered["extra"] = True
        if bad == "source_order": altered["first"]["rows"].reverse()
        if bad == "rational": altered["first"]["rows"][0]["coefficient"]["numerator"] = 0
        if bad == "mapping": changed["rows_in_source_order"][0]["coefficient"]["numerator"] = 4
        with pytest.raises(ValueError):
            validate_mapping(altered, changed, family, admit_source=source.admit)
    with pytest.raises(MappingAdmission):
        map_joint(doc, admit_source=None)


def test_nested_and_outer_ir_bounds_are_separate(e7c):
    config, joint, source, ir, nested = e7c
    def document(length):
        return source.document(joint([(Fraction(1),
            (config((), "x" * length), config((), "y")))], arity=2))

    # At 80k source tag bytes the nested /0.5 package fits, while /0.6
    # embeds both child and outer witness and is refused at its own bound.
    moderate = document(80_000)
    child = nested.lower(moderate["first"])
    assert len(nested.serialize(child)) <= nested.MAX_BYTES
    with pytest.raises(ir.TwoStageIRAdmission):
        ir.lower(moderate)

    # At 200k tag bytes the nested package itself exceeds /0.5's bound;
    # failure is attributed before any outer /0.6 execution or result.
    huge = document(200_000)
    with pytest.raises(nested.JointRestrictionIRAdmission):
        nested.lower(huge["first"])
    with pytest.raises(nested.JointRestrictionIRAdmission):
        ir.lower(huge)
