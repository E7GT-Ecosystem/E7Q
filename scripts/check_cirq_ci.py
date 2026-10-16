# SPDX-License-Identifier: Apache-2.0
"""CI-only focused-result gate and real-worker Bell/replay probe; no new SDK API."""
from copy import deepcopy
from hashlib import sha256
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SDK_TESTS = frozenset({
    "test_c01_real_cirq_bell_all_basis_analytic_matrix",
    "test_c02_real_cirq_nine_gate_composition_analytic_oracle",
    "test_c03_real_cirq_order_control_direction_and_idle_wire",
})


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_report(path):
    """Reject empty/partial, skipped/xfail, failed or foreign focused JUnit reports."""
    root = ET.parse(path).getroot()
    require(root.tag == "testsuites", "expected pytest testsuites root")
    suites = list(root)
    require(bool(suites) and all(s.tag == "testsuite" for s in suites),
            "expected pytest testsuite children")
    names = set()
    total = 0
    for suite in suites:
        cases = suite.findall("testcase")
        require(bool(cases), "empty test suite")
        require(int(suite.attrib["tests"]) == len(cases), "inconsistent test count")
        for key in ("skipped", "failures", "errors"):
            require(int(suite.attrib[key]) == 0, f"focused suite has {key}")
        for case in cases:
            require(case.get("classname") == "tests.test_cirq_interop",
                    "unexpected focused test module")
            name = case.get("name")
            require(bool(name) and name not in names, "missing/duplicate test name")
            require(not any(case.find(tag) is not None
                            for tag in ("skipped", "failure", "error")),
                    "focused test did not pass")
            names.add(name)
        total += len(cases)
    require(total >= 83, "focused corpus was empty or only partially executed")
    require(SDK_TESTS <= names, "required SDK-backed tests were not executed")
    return {"status": "PASS", "executed": total, "skipped": 0,
            "required_sdk_tests": sorted(SDK_TESTS)}


def check_bell(output):
    """Generate NEW evidence; never rewrite the historical Bell result."""
    import numpy as np
    from e7q.cirq_interop import evaluate_roundtrip, replay
    from e7q.ir import validate_graph

    directory = ROOT / "examples/e7q-ir/cirq"
    historical_path = directory / "bell-result.json"
    historical_bytes = historical_path.read_bytes()
    source = (directory / "bell.e7q").read_text(encoding="utf-8")
    options = {"returned_source": None, "criterion": "tolerance",
               "tolerance": 1e-9, "timeout_seconds": 15.0}
    result = evaluate_roundtrip(source, **options)
    require(result.get("status") == "PASS", f"Bell evaluation failed: {result}")
    assessment = result["native_assessment"]
    require(assessment["criterion"] == options["criterion"]
            and assessment["status"] == "PASS", "native assessment failed")
    require(result["environment"]["cirq"] == "1.6.1", "wrong worker Cirq")
    require(validate_graph(result["graph"], level="F1")["status"] == "PASS",
            "F1 integrity failed")
    probabilities = np.asarray(result["diagnostics"]["zero_input_ideal_probabilities"])
    require(probabilities.shape == (4,) and np.allclose(
        probabilities, [0.5, 0, 0, 0.5], atol=1e-14, rtol=0),
        "independent Bell probability oracle failed")
    require(replay(result, source, **options), "fresh real-worker replay failed")
    tampered = deepcopy(result)
    tampered["native_assessment"]["maximum_error"] = 0.25
    require(not replay(tampered, source, **options), "tampered result replayed")
    historical = json.loads(historical_bytes)
    historical_replay = replay(historical, source, **options)
    require(historical_path.read_bytes() == historical_bytes,
            "historical Bell evidence changed")
    # Exclusive creation also prevents overwriting an explicitly supplied old path.
    with Path(output).open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    return {"status": "PASS", "native_criterion": options["criterion"],
            "native_assessment": assessment["status"], "graph_integrity": "F1 PASS",
            "zero_input_probabilities": probabilities.tolist(),
            "fresh_replay": True, "tamper_rejected": True,
            "fresh_graph_id": result["graph"]["graph_id"],
            "historical_graph_id": historical["graph"]["graph_id"],
            "historical_replay": historical_replay,
            "fresh_environment": result["environment"],
            "historical_environment": historical["environment"],
            "historical_sha256": sha256(historical_bytes).hexdigest(),
            "limitations": "SDK observation, native assessment and F1 are distinct; "
                           "no SDK F2, authentication, hardware or external reproduction"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("report").add_argument("path", type=Path)
    commands.add_parser("bell").add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        result = check_report(args.path) if args.command == "report" else check_bell(args.output)
    except (ValueError, KeyError, OSError, ET.ParseError) as exc:
        parser.exit(1, f"Cirq CI check failed: {exc}\n")
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
