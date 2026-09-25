# SPDX-License-Identifier: Apache-2.0
"""Reproduce the bounded E7Q × E7C pilot from a pinned E7G-T checkout.

Usage: PYTHONPATH=src python tools/run_e7c_joint_pilot.py --e7c-root PATH --output DIR
"""
from __future__ import annotations

import argparse
import copy
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

from e7q.ir.canonical import canonical_bytes, digest
from e7q.ir.candidate_family import assess_candidate_restriction
from e7q.ir.e7c_joint_pilot import (
    LAYOUT_TAG, TARGET_TAG, full_table_baseline, map_joint,
    marginal_cartesian_baseline, validate_mapping,
)

E7C_COMMIT = "5b5cb5f10ddd913df66f5d9f65fbe059a2e33193"


def import_e7c(root: Path):
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if head != E7C_COMMIT:
        raise ValueError(f"E7C source must be pinned to {E7C_COMMIT}, got {head}")
    directory = root / "research" / "e7c-0.1"
    sys.path[:0] = [str(directory), str(directory / "adapters")]
    from eec_q_fg3_b1 import Config
    from eec_q_fg3_joint_b1 import joint
    import e7c_eecq_two_stage_b1 as source
    import e7_ir_eecq_two_stage_b1 as ir
    import e7_ir_eecq_joint_restrict_b1 as nested
    return Config, joint, source, ir, nested


def make_joint(config, joint, pairs, *, coefficients=None):
    coefficients = coefficients or [Fraction(1, 2)] * len(pairs)
    return joint([(coefficient, (
        config(("AB",) if layout == "L1" else (), LAYOUT_TAG),
        config(("BC",) if target == "T1" else (), TARGET_TAG)))
        for (layout, target), coefficient in zip(pairs, coefficients)], arity=2)


def _project(rows, mapping):
    by_id = {r["source_row_identity"]: r for r in mapping["rows_in_source_order"]}
    return [by_id[digest(row)] for row in rows]


def run_case(e7c, name, value, *, step_bound=20, ledger_bound=20):
    _config, _joint, source, ir, nested = e7c
    doc = source.document(value, step_bound=step_bound, ledger_bound=ledger_bound)
    mapping, family = map_joint(doc, admit_source=source.admit)
    validate_mapping(doc, mapping, family, admit_source=source.admit)
    source_events = []
    actual = source.evaluate(doc, _transition_sink=source_events.append)
    package = ir.lower(doc)
    ir_events = []
    independent = ir.execute(package, _transition_sink=ir_events.append)
    if actual["witness"]["claim"] != independent or source_events != ir_events:
        raise AssertionError("source and independent IR observations differ")
    child = package["first_ir"]
    first_size = len(nested.serialize(child))
    outer_size = len(ir.serialize(package))
    if first_size > nested.MAX_BYTES or outer_size > ir.MAX_BYTES:
        raise AssertionError("package budget exceeded on admitted IR")
    full = full_table_baseline(mapping)
    terminal = actual["terminal_outcome"]
    q_a1 = None
    if terminal["tag"] == "success":
        result = terminal["value"]
        for field, baseline in (("retained", "final"), ("first_excluded", "first_excluded"),
                                ("second_excluded", "second_excluded")):
            if _project(result[field], mapping) != full[baseline]:
                raise AssertionError(f"full correlated table differs on {field}")
        # Full-table audit uses source row indices while stage-two E7C uses
        # retained-child row indices; compare the ordered event kinds only.
        baseline_trace = [(event["stage"], event["event"], event.get("decision"))
                          for event in full["audit_trace"]]
        source_trace = [
            ("first" if event["event"] in ("restriction_attempt", "joint_row_checked") else "second",
             "row_checked" if "row_checked" in event["event"] else "restriction_attempt",
             event.get("decision")) for event in actual["ordered_ledger"]]
        if baseline_trace != source_trace:
            raise AssertionError("full table omitted an ordered decision")
        first_ids = [row["member_id"] for row in mapping["rows_in_source_order"]
                     if row["bindings"]["layout"] == "L0"]
        first_q = assess_candidate_restriction(family, first_ids,
                    criterion_id="PilotFirst", criterion_edition="0alpha1",
                    criterion_text="Exclude AB at coordinate 0: L1")
        final_ids = [row["member_id"] for row in full["final"]]
        final_q = assess_candidate_restriction(family, final_ids,
                    criterion_id="PilotComposed", criterion_edition="0alpha1",
                    criterion_text="After L1 exclusion, exclude T1 using retained source Joint")
        if first_q["outcome"] != "success" or final_q["outcome"] != (
                "success" if final_ids else "empty"):
            raise AssertionError("Q-A1 outcome mismatch")
        if not final_ids and final_q["result_family"] is not None:
            raise AssertionError("Q-A1 empty must not invent a residual family")
        q_a1 = {"first_restriction": first_q, "composed_final_restriction": final_q,
                "outcome_translation": "E7C success contains empty retained Joint; Q-A1 records empty"
                if not final_ids else "E7C success maps to Q-A1 success"}
    return {"case": name, "e7c_pinned_commit": E7C_COMMIT,
            "source_document": doc, "mapping": mapping, "q_a1_family": family,
            "e7c_source_result": actual, "e7c_source_transition_events": source_events,
            "ir_package": package, "ir_independent_result": independent,
            "ir_transition_events": ir_events,
            "ir_package_bounds": {"nested_edition": child["ir_edition"],
                                  "nested_size": first_size, "nested_max": nested.MAX_BYTES,
                                  "outer_edition": package["ir_edition"],
                                  "outer_size": outer_size, "outer_max": ir.MAX_BYTES},
            "q_a1_restrictions": q_a1, "full_correlated_table": full,
            "lossy_marginal_cartesian": marginal_cartesian_baseline(mapping),
            "limits": ["Finite synthetic planning case; no reviewer timing/error sample.",
                       "Independent IR replay is finite evidence, not an all-input code-to-Lean proof."]}


def output_cases(root: Path, output: Path):
    e7c = import_e7c(root)
    config, joint, source, ir, nested = e7c
    a = make_joint(config, joint, [("L0", "T0"), ("L1", "T1")])
    b = make_joint(config, joint, [("L0", "T1"), ("L1", "T0")])
    cases = [run_case(e7c, "diagonal_A", a),
             run_case(e7c, "crossed_B", b),
             run_case(e7c, "failed_second_append_A", a, ledger_bound=3),
             run_case(e7c, "signed_counterexample", make_joint(config, joint,
                 [("L0", "T0"), ("L1", "T1")],
                 coefficients=[Fraction(1, 2), Fraction(-1, 2)]))]
    if (cases[0]["lossy_marginal_cartesian"] != cases[1]["lossy_marginal_cartesian"]):
        raise AssertionError("same-marginals counterexample lost")
    failed = cases[2]
    if (failed["e7c_source_result"]["terminal_outcome"]["tag"] != "resource_limit"
            or not failed["e7c_source_result"]["witness"]["second_started"]
            or failed["e7c_source_result"]["resource_progress"]["completed_steps"] != 4
            or any(event["event"] == "second_restriction_attempt"
                   for event in failed["e7c_source_result"]["ordered_ledger"])):
        raise AssertionError("charged failed second append was erased")
    reduced = make_joint(config, joint, [("L0", "T0")], coefficients=[Fraction(2, 4)])
    canonical = make_joint(config, joint, [("L0", "T0")], coefficients=[Fraction(1, 2)])
    if reduced != canonical or map_joint(source.document(reduced), admit_source=source.admit) != map_joint(source.document(canonical), admit_source=source.admit):
        raise AssertionError("reduced equivalent rational failed")
    hostile = []
    for mutation in ("zero", "zero_masked", "duplicate", "altered_coefficient", "reorder", "unsupported_tag",
                     "missing_exclusion", "unknown_member"):
        try:
            original = cases[0]
            if mutation in ("zero", "zero_masked", "duplicate", "reorder", "unsupported_tag"):
                broken = copy.deepcopy(original["source_document"])
                rows = broken["first"]["rows"]
                if mutation == "zero": rows[0]["coefficient"]["numerator"] = 0
                if mutation == "zero_masked":
                    valid = copy.deepcopy(rows[0])
                    rows[0]["coefficient"]["numerator"] = 0
                    rows.append(valid)  # collection would mask the invalid zero row
                if mutation == "duplicate": rows.append(copy.deepcopy(rows[0]))
                if mutation == "reorder": rows.reverse()
                if mutation == "unsupported_tag": rows[0]["atoms"][0]["tag"] = ""
                source.admit(broken)
                map_joint(broken, admit_source=source.admit)
            else:
                broken = copy.deepcopy(original["mapping"])
                if mutation == "altered_coefficient": broken["rows_in_source_order"][0]["coefficient"]["numerator"] = 9
                if mutation == "missing_exclusion": broken["rows_in_source_order"].pop()
                if mutation == "unknown_member": broken["rows_in_source_order"][0]["member_id"] = "sha256:" + "0" * 64
                validate_mapping(original["source_document"], broken, original["q_a1_family"], admit_source=source.admit)
        except (ValueError, KeyError):
            hostile.append({"mutation": mutation, "outcome": "rejected"})
        else:
            raise AssertionError(f"hostile mutation accepted: {mutation}")
    output.mkdir(parents=True, exist_ok=True)
    for case in cases:
        (output / (case["case"] + ".json")).write_bytes(canonical_bytes(case) + b"\n")
    (output / "hostile_mutations.json").write_bytes(canonical_bytes(hostile) + b"\n")
    files = sorted(f for f in output.glob("*.json") if f.name != "manifest.json")
    manifest = {"schema": "e7q.ir.e7c-joint-pilot-manifest/v0alpha1",
                "e7c_commit": E7C_COMMIT,
                "artifacts": {f.name: "sha256:" + sha256(f.read_bytes()).hexdigest() for f in files},
                "generation_command": "PYTHONPATH=src python tools/run_e7c_joint_pilot.py --e7c-root PINNED_E7C --output fixtures/e7c-joint-pilot"}
    (output / "manifest.json").write_bytes(canonical_bytes(manifest) + b"\n")
    return cases


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--e7c-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    opts = parser.parse_args()
    results = output_cases(opts.e7c_root, opts.output)
    print(json.dumps([{"case": r["case"], "outcome": r["e7c_source_result"]["terminal_outcome"]["tag"],
                       "source_sha256": digest(r["source_document"]),
                       "nested_bytes": r["ir_package_bounds"]["nested_size"],
                       "outer_bytes": r["ir_package_bounds"]["outer_size"]} for r in results], indent=2))
