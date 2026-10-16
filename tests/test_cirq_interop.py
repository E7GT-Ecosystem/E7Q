# SPDX-License-Identifier: Apache-2.0
"""Independent bounded Cirq acceptance probes; no implementation-derived oracle.

The expected matrices below are analytic, in big-endian q[0], q[1] order.
Only the real-worker fixture uses Cirq; admission and native comparisons remain
usable without that optional dependency. Exact means existing floating-point
native comparison, not symbolic/algebraic identity.
"""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import ast
import importlib
import json
import math
import os
import subprocess
import sys

import numpy as np
import pytest

from e7q.adapters import adapt
from e7q.ir.canonical import identified_digest
from e7q.ir.conformance import validate_graph
from e7q.language import E7QError, Program, circuit_unitary, compare, comparison_result, parse

ROOT = Path(__file__).resolve().parents[1]


def native(operations="", qubits=1):
    return (f"context Acceptance {{\n  backend: statevector\n  seed: 7\n}}\n"
            f"qubits q[{qubits}]\nbits c[{qubits}]\n"
            f"path Circuit {{\n{operations}\n  measure q -> c\n}}\nverify Circuit\n")


def sdk(operations="", qubits=1):
    """Literal exporter dialect, deliberately not generated through adapt()."""
    refs = ", ".join(f"qubits[{index}]" for index in range(qubits))
    return ("import cirq\n\n"
            f"qubits = cirq.LineQubit.range({qubits})\n"
            "circuit = cirq.Circuit()\n" + operations
            + f'circuit.append(cirq.measure({refs}, key="c"))\n')


def gate(name, *qubits):
    refs = ", ".join(f"qubits[{index}]" for index in qubits)
    return f"circuit.append(cirq.{name}({refs}))\n"


@pytest.fixture(scope="module")
def interop():
    return importlib.import_module("e7q.cirq_interop")


def assert_refused(interop, source, status="UNSUPPORTED"):
    with pytest.raises(E7QError) as caught:
        interop.admit_cirq_source(source)
    assert getattr(caught.value, "status", None) == status


@pytest.mark.parametrize("name,expected", [
    ("X", [[0, 1], [1, 0]]),
    ("Y", [[0, -1j], [1j, 0]]),
    ("Z", [[1, 0], [0, -1]]),
    ("H", np.array([[1, 1], [1, -1]]) / math.sqrt(2)),
    ("S", [[1, 0], [0, 1j]]),
    ("T", [[1, 0], [0, (1 + 1j) / math.sqrt(2)]]),
])
def test_c01_single_qubit_gate_admission_analytic_oracles(interop, name, expected):
    program = interop.admit_cirq_source(sdk(gate(name, 0)))
    assert isinstance(program, Program)
    assert program.qubits == program.bits == 1
    assert [op.gate for op in program.operations] == [name, "MEASURE"]
    assert program.operations[-1].full_register
    np.testing.assert_allclose(circuit_unitary(program), expected, atol=1e-14, rtol=0)


@pytest.mark.parametrize("name,expected", [
    ("CNOT", [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]]),
    ("CZ", np.diag([1, 1, 1, -1])),
    ("SWAP", [[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]]),
])
def test_c02_two_qubit_gate_admission_analytic_oracles(interop, name, expected):
    program = interop.admit_cirq_source(sdk(gate(name, 0, 1), 2))
    assert program.operations[0].qubits == (0, 1)
    assert program.operations[0].gate == ("CX" if name == "CNOT" else name)
    np.testing.assert_allclose(circuit_unitary(program), expected, atol=1e-14, rtol=0)


def test_c03_order_direction_and_idle_wire_are_not_inferred_from_bell(interop):
    x0 = interop.admit_cirq_source(sdk(gate("X", 0), 2))
    x1 = interop.admit_cirq_source(sdk(gate("X", 1), 2))
    np.testing.assert_array_equal(circuit_unitary(x0)[:, 0], [0, 0, 1, 0])
    np.testing.assert_array_equal(circuit_unitary(x1)[:, 0], [0, 1, 0, 0])
    assert x0.qubits == x1.qubits == 2
    reverse = interop.admit_cirq_source(sdk(gate("CNOT", 1, 0), 2))
    np.testing.assert_array_equal(circuit_unitary(reverse),
                                  [[1, 0, 0, 0], [0, 0, 0, 1],
                                   [0, 0, 1, 0], [0, 1, 0, 0]])


def test_c04_phase_criteria_are_native_not_new_symbolic_claims(interop):
    identity = parse(native())
    minus_identity = interop.admit_cirq_source(sdk(
        gate("X", 0) + gate("Z", 0) + gate("X", 0) + gate("Z", 0)))
    np.testing.assert_array_equal(circuit_unitary(minus_identity), -np.eye(2))
    assert comparison_result(compare(identity, minus_identity, "exact"))["status"] == "FAIL"
    assert comparison_result(compare(identity, minus_identity, "global-phase"))["status"] == "PASS"
    assert comparison_result(compare(identity, minus_identity, "measurement"))["status"] == "PASS"
    zz = interop.admit_cirq_source(sdk(gate("Z", 0) * 2))
    np.testing.assert_array_equal(circuit_unitary(zz), np.eye(2))
    hh = interop.admit_cirq_source(sdk(gate("H", 0) * 2))
    assert compare(identity, hh, "tolerance", 1e-9).equivalent
    # H uses floating-point 1/sqrt(2); exact is intentionally not symbolic H²=I.
    exact = comparison_result(compare(identity, hh, "exact"))
    assert exact["status"] == "FAIL"
    assert 0 < exact["maximum_error"] < 1e-14


def test_c05_state_zero_and_measurement_zero_do_not_establish_unitary_equivalence(interop):
    identity = parse(native())
    z = interop.admit_cirq_source(sdk(gate("Z", 0)))
    np.testing.assert_array_equal(circuit_unitary(z)[:, 0], [1, 0])
    assert not compare(identity, z, "tolerance", 1e-9).equivalent
    assert compare(identity, z, "measurement").equivalent
    h = parse(native("  H q[0]"))
    hz = interop.admit_cirq_source(sdk(gate("H", 0) + gate("Z", 0)))
    np.testing.assert_allclose(circuit_unitary(hz)[:, 0],
                               np.array([1, -1]) / math.sqrt(2), atol=1e-14)
    assert not compare(h, hz, "tolerance", 1e-9).equivalent
    assert compare(h, hz, "measurement").equivalent


@pytest.mark.parametrize("operation", [
    "circuit.append(cirq.rx(0.5)(qubits[0]))\n",
    "circuit.append(cirq.ry(0.5)(qubits[0]))\n",
    "circuit.append(cirq.rz(0.5)(qubits[0]))\n",
    "circuit.append(cirq.XPowGate(exponent=0.5)(qubits[0]))\n",
    "circuit.append(cirq.X(qubits[0]) ** 0.5)\n",
    "circuit.append(cirq.X(sympy.Symbol('theta')))\n",
    "circuit.append(CustomGate()(qubits[0]))\n",
])
def test_c07_rotations_symbols_custom_gates_are_outside_subset(interop, operation):
    assert_refused(interop, sdk(operation))


@pytest.mark.parametrize("operation", [
    "circuit.append(cirq.depolarize(0.1)(qubits[0]))\n",
    "circuit.append(cirq.reset(qubits[0]))\n",
    'circuit.append(cirq.measure(qubits[0], key="c"))\n' + gate("X", 0),
    'circuit.append(cirq.measure(qubits[0], key="c"))\n',
])
def test_c08_noise_reset_mid_and_repeated_measurements_refused(interop, operation):
    assert_refused(interop, sdk(operation))


@pytest.mark.parametrize("change", [
    lambda text: text.replace('key="c"', 'key="other"'),
    lambda text: text.replace('qubits[0], qubits[1], key=', 'qubits[1], qubits[0], key='),
    lambda text: text.replace('qubits[0], qubits[1], key=', 'qubits[0], key='),
    lambda text: text.replace('qubits[0], qubits[1], key=', 'qubits[0], qubits[0], key='),
    lambda text: text.replace('key="c"', 'key="c", invert_mask=(True, False)'),
    lambda text: text.replace('circuit.append(cirq.measure(qubits[0], qubits[1], key="c"))', ''),
])
def test_c15_complete_terminal_identity_measurement_map_required(interop, change):
    assert_refused(interop, change(sdk(qubits=2)))


@pytest.mark.parametrize("extra", [
    "import os\n", "from cirq import X\n", "exec('pass')\n",
    "eval('1')\n", "circuit.clear()\n", "qubits.reverse()\n",
    "for _ in range(2):\n    pass\n", "def hidden():\n    pass\n",
    "circuit.append(__import__('os'))\n",
])
def test_c06_unsupported_python_is_not_executed(interop, extra):
    assert_refused(interop, sdk() + extra)


def test_c06_poison_import_never_creates_marker(interop, tmp_path):
    marker = tmp_path / "source-executed"
    poison = ("import os\n"
              f"open({str(marker)!r}, 'w').write('unsafe')\n")
    assert_refused(interop, sdk() + poison)
    result = interop.evaluate_roundtrip(native(), returned_source=sdk() + poison)
    assert result["status"] == "UNSUPPORTED"
    assert not marker.exists()


@pytest.mark.parametrize("source", [
    sdk() + "#" + "a" * (16 * 1024),
    sdk(gate("X", 0) * 65),
    sdk(qubits=3),
    sdk() + "x = " + "[" * 35 + "0" + "]" * 35 + "\n",
    sdk() + "x = [" + ",".join("0" for _ in range(2100)) + "]\n",
])
def test_c10_known_source_resource_limits_are_not_inequality(interop, source):
    assert len(list(ast.walk(ast.parse(source)))) > 0
    assert_refused(interop, source, "RESOURCE_REFUSED")
    result = interop.evaluate_roundtrip(native(), returned_source=source)
    assert result["status"] == "RESOURCE_REFUSED"


def test_c10_operation_boundary_is_inclusive(interop):
    admitted = interop.admit_cirq_source(sdk(gate("X", 0) * 64))
    assert len(admitted.operations) == 65  # 64 unitaries plus terminal measurement


@pytest.mark.parametrize("source", [
    native("  X q[0]\n" * 65), native(qubits=3),
    native().replace("backend: statevector", "backend: densitymatrix"),
    native().replace("backend: statevector", "backend: stabilizer"),
    native("  measure q[0] -> c[0]\n  X q[0]"),
    native("  noise bit_flip(0.10) q[0]").replace("backend: statevector", "backend: densitymatrix"),
    native().replace("measure q -> c", "measure q[0] -> c[0]"),
])
def test_c08_c10_native_side_domain_also_fails_closed(interop, source):
    result = interop.evaluate_roundtrip(source)
    expected = "RESOURCE_REFUSED" if source in {native("  X q[0]\n" * 65), native(qubits=3)} else "UNSUPPORTED"
    assert result["status"] == expected


def test_c12_existing_graph_fixtures_keep_exact_historical_bytes_and_ids():
    fixtures = {
        "native-execution-bell-graph.json": "6f87323108011255ddfea928b4180f612d8af8a51053a1a28c44910d84b74a1f",
        "external-circuit-workflow.json": "dee50e36239b0049e3b2aff59b95207be205fcdc6f158d6f4ffb23076d7834c9",
        "f2-framework-not-assessed.json": "26d3e2a1b5dba5bbb0dfd41f1ebf4a1c923083faa6badf4125af92899fb828a0",
    }
    for name, digest in fixtures.items():
        assert sha256((ROOT / "examples" / "e7q-ir" / name).read_bytes()).hexdigest() == digest
    graph = json.loads((ROOT / "examples/e7q-ir/native-execution-bell-graph.json").read_text())
    assert graph["graph_id"] == "sha256:c9fe173151778dcae3df500674a53c063c32119c6b600bfe40c0b82f00e59598"
    assert validate_graph(graph, level="F1")["status"] == "PASS"


REAL_CASES = {
    "bell": (native("  H q[0]\n  CX q[0], q[1]", 2), None, "tolerance", "PASS"),
    "asymmetric": (native("  X q[0]", 2), sdk(gate("X", 1), 2), "tolerance", "FAIL"),
    "direction": (native("  CX q[0], q[1]", 2), sdk(gate("CNOT", 1, 0), 2), "tolerance", "FAIL"),
    "phase": (native(), sdk(gate("X", 0) + gate("Z", 0) + gate("X", 0) + gate("Z", 0)), "exact", "FAIL"),
    "hidden_phase": (native(), sdk(gate("Z", 0)), "tolerance", "FAIL"),
    "measurement": (native("  H q[0]"), sdk(gate("H", 0) + gate("Z", 0)), "measurement", "PASS"),
    "hh": (native(), sdk(gate("H", 0) * 2), "tolerance", "PASS"),
    "all_gates": (native("  X q[0]\n  Y q[1]\n  Z q[0]\n  H q[1]\n"
                         "  S q[0]\n  T q[1]\n  CX q[0], q[1]\n  CZ q[0], q[1]\n  SWAP q[0], q[1]", 2),
                  None, "tolerance", "PASS"),
}


@pytest.fixture(scope="module")
def real_results(interop):
    # Exactly eight real Cirq evaluations, reused by schema/oracle/replay tests.
    # The normal dependency-free repository suite still runs refusal probes.
    if importlib.util.find_spec("cirq") is None:
        pytest.skip("optional Cirq is absent; real simulator probes need Cirq 1.6.1")
    results = {}
    for name, (source, returned, criterion, expected) in REAL_CASES.items():
        value = interop.evaluate_roundtrip(source, returned_source=returned,
                                          criterion=criterion)
        assert value["status"] == expected, (name, value)
        results[name] = value
    return results


def observed_matrix(result):
    observation = result["simulator"]
    return np.array(observation["real"], dtype=float) + 1j * np.array(observation["imag"], dtype=float)


def test_c01_real_cirq_bell_all_basis_analytic_matrix(real_results):
    result = real_results["bell"]
    # Columns are |00>, |01>, |10>, |11> inputs, NOT four samples of |00>.
    expected = np.array([[1, 0, 1, 0], [0, 1, 0, 1],
                         [0, 1, 0, -1], [1, 0, -1, 0]]) / math.sqrt(2)
    np.testing.assert_allclose(observed_matrix(result), expected, atol=1e-14, rtol=0)
    np.testing.assert_allclose(observed_matrix(result)[:, 0],
                               np.array([1, 0, 0, 1]) / math.sqrt(2), atol=1e-14, rtol=0)
    assert result["method"]["basis_inputs"] == [0, 1, 2, 3]
    assert "q0 tensor MSB" in result["method"]["qubit_order"]
    assert result["method"]["dtype"] == "complex128"
    assert result["environment"]["cirq"] == "1.6.1"
    assert result["method"]["simulator"] == "cirq.Simulator"
    assert "excluded" in result["method"]["terminal_measurement"]
    np.testing.assert_allclose(result["diagnostics"]["zero_input_ideal_probabilities"],
                               [0.5, 0, 0, 0.5], atol=1e-14, rtol=0)


def test_c02_real_cirq_nine_gate_composition_analytic_oracle(real_results):
    # Tensor products and literal matrices here are independent of native gates.
    x = np.array([[0, 1], [1, 0]], complex)
    y = np.array([[0, -1j], [1j, 0]], complex)
    z = np.diag([1, -1])
    h = np.array([[1, 1], [1, -1]]) / math.sqrt(2)
    s = np.diag([1, 1j])
    t = np.diag([1, (1 + 1j) / math.sqrt(2)])
    cx = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]])
    cz = np.diag([1, 1, 1, -1])
    swap = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]])
    eye = np.eye(2)
    expected = swap @ cz @ cx @ np.kron(eye, t) @ np.kron(s, eye) @ np.kron(eye, h) @ np.kron(z, eye) @ np.kron(eye, y) @ np.kron(x, eye)
    np.testing.assert_allclose(observed_matrix(real_results["all_gates"]), expected, atol=1e-14, rtol=0)


def test_c03_real_cirq_order_control_direction_and_idle_wire(real_results):
    np.testing.assert_array_equal(observed_matrix(real_results["asymmetric"])[:, 0], [0, 1, 0, 0])
    np.testing.assert_array_equal(observed_matrix(real_results["direction"]),
                                  [[1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0]])
    # Direction differs only away from zero input; report this separately.
    diagnostics = real_results["direction"]["diagnostics"]
    assert diagnostics["state_relative_zero_input_max_error"] == 0
    assert diagnostics["measurement_relative_zero_input_max_error"] == 0
    assert real_results["direction"]["native_assessment"]["status"] == "FAIL"


def test_c05_real_zero_diagnostics_do_not_upgrade_native_scope(real_results):
    z = real_results["hidden_phase"]
    np.testing.assert_array_equal(observed_matrix(z), [[1, 0], [0, -1]])
    assert z["diagnostics"]["state_relative_zero_input_max_error"] == 0
    assert z["diagnostics"]["measurement_relative_zero_input_max_error"] == 0
    assert z["native_assessment"]["maximum_error"] == 2
    assert z["status"] == "FAIL"
    hz = real_results["measurement"]
    assert hz["diagnostics"]["state_relative_zero_input_max_error"] == pytest.approx(math.sqrt(2))
    assert hz["diagnostics"]["measurement_relative_zero_input_max_error"] < 1e-14
    assert hz["native_assessment"]["criterion"] == "measurement"
    assert hz["native_assessment"]["status"] == "PASS"


def test_c04_real_native_assessment_is_existing_comparison_result(interop, real_results, monkeypatch):
    for name, result in real_results.items():
        source, returned, criterion, expected = REAL_CASES[name]
        admitted = interop.admit_cirq_source(returned or adapt(parse(source), "cirq").source)
        # Equality checks delegation/API shape; analytic tests above supply truth.
        assert result["native_assessment"] == comparison_result(compare(parse(source), admitted, criterion, 1e-9))
        assert result["status"] == expected
    phase = real_results["phase"]
    np.testing.assert_array_equal(observed_matrix(phase), -np.eye(2))
    monkeypatch.setattr(interop, "_child_transport", lambda records, timeout: deepcopy(phase["simulator"]))
    source, returned, _, _ = REAL_CASES["phase"]
    global_phase = interop.evaluate_roundtrip(source, returned_source=returned, criterion="global-phase")
    assert global_phase["status"] == "PASS"
    assert global_phase["native_assessment"]["global_phase"] == {"real": -1.0, "imag": 0.0}
    assert real_results["hh"]["status"] == "PASS"
    assert 0 < real_results["hh"]["native_assessment"]["maximum_error"] < 1e-14


def test_c06_worker_transport_receives_primitive_records_never_python_source(interop, real_results, monkeypatch):
    seen = []
    def transport(records, timeout):
        seen.append((deepcopy(records), timeout))
        return deepcopy(real_results["bell"]["simulator"])
    monkeypatch.setattr(interop, "_child_transport", transport)
    result = interop.evaluate_roundtrip(REAL_CASES["bell"][0])
    assert result["status"] == "PASS"
    assert seen == [({"qubits": 2, "operations": [
        {"gate": "H", "qubits": [0]}, {"gate": "CX", "qubits": [0, 1]}]}, 15.0)]


def test_c09_graph_binds_all_three_source_bytes_and_native_assessment(real_results):
    result = real_results["bell"]
    graph = result["graph"]
    assert validate_graph(graph, level="F1")["status"] == "PASS"
    source = REAL_CASES["bell"][0]
    sources = {a["payload"]["format"]: a for a in graph["artifacts"] if a["kind"] == "source"}
    assert set(sources) == {"e7q", "cirq-export", "cirq-return"}
    assert sources["e7q"]["payload"]["source"].encode() == source.encode()
    exported = adapt(parse(source), "cirq").source
    assert sources["cirq-export"]["payload"]["source"].encode() == exported.encode()
    assert sources["cirq-return"]["payload"]["source"].encode() == exported.encode()
    for item in sources.values():
        assert item["artifact_id"] == identified_digest(item, "artifact_id")
        assert any(r["source"] == item["artifact_id"] for r in graph["relations"])
    assessment = next(a["payload"] for a in graph["artifacts"] if a["kind"] == "assessment")
    assert assessment["native_assessment"] == result["native_assessment"]
    assert graph["graph_id"] == identified_digest(graph, "graph_id")


def rehash_graph(graph):
    """Independent envelope rehash: proves F1 alone is not semantic replay."""
    replacements = {}
    def rewrite(value):
        if isinstance(value, str):
            return replacements.get(value, value)
        if isinstance(value, list):
            return [rewrite(item) for item in value]
        if isinstance(value, dict):
            return {key: rewrite(item) for key, item in value.items()}
        return value
    for artifact in graph["artifacts"]:
        old = artifact["artifact_id"]
        artifact.update(rewrite(artifact))
        artifact["artifact_id"] = identified_digest(artifact, "artifact_id")
        replacements[old] = artifact["artifact_id"]
    for relation in graph["relations"]:
        relation.update(rewrite(relation))
        relation["relation_id"] = identified_digest(relation, "relation_id")
    graph["graph_id"] = identified_digest(graph, "graph_id")


def test_c09_replay_rejects_tampering_even_after_consistent_f1_rehash(interop, real_results, monkeypatch):
    original = real_results["bell"]
    source = REAL_CASES["bell"][0]
    monkeypatch.setattr(interop, "_child_transport", lambda records, timeout: deepcopy(original["simulator"]))
    assert interop.replay(original, source)
    wrong = deepcopy(original)
    wrong["native_assessment"]["maximum_error"] = 0.25
    assert not interop.replay(wrong, source)
    wrong = deepcopy(original)
    assessment = next(a for a in wrong["graph"]["artifacts"] if a["kind"] == "assessment")
    wrong["native_assessment"]["maximum_error"] = 0.25
    assessment["payload"]["native_assessment"]["maximum_error"] = 0.25
    rehash_graph(wrong["graph"])
    assert validate_graph(wrong["graph"], level="F1")["status"] == "PASS"
    assert not interop.replay(wrong, source)
    wrong = deepcopy(original)
    preserved = next(a for a in wrong["graph"]["artifacts"] if a["kind"] == "source")
    preserved["payload"]["source"] += "# same semantics, different bytes\n"
    rehash_graph(wrong["graph"])
    assert validate_graph(wrong["graph"], level="F1")["status"] == "PASS"
    assert not interop.replay(wrong, source)
    assert not interop.replay(original, source + "# changed bytes\n")
    assert not interop.replay(original, source, criterion="measurement")
    assert not interop.replay({"status": "ERROR"}, source)


def test_c10_real_child_deadline_is_typed_noncomparison(interop):
    result = interop.evaluate_roundtrip(native(), timeout_seconds=1e-6)
    assert result["status"] == "TIMEOUT"
    assert result["native_assessment"] is None


@pytest.mark.parametrize("arguments,status", [
    ({"timeout_seconds": 31}, "RESOURCE_REFUSED"),
    ({"timeout_seconds": 0}, "ERROR"),
    ({"timeout_seconds": float("inf")}, "ERROR"),
    ({"timeout_seconds": True}, "ERROR"),
    ({"tolerance": 0}, "ERROR"),
    ({"tolerance": float("nan")}, "ERROR"),
    ({"criterion": "sampling"}, "UNSUPPORTED"),
])
def test_c10_invalid_options_never_produce_inequality(interop, arguments, status):
    result = interop.evaluate_roundtrip(native(), **arguments)
    assert result["status"] == status
    assert result["native_assessment"] is None


def test_c10_real_worker_declares_bounded_resource_policy(real_results):
    limits = real_results["bell"]["limits"]
    assert limits["memory_bytes"] == 3 * 1024**3
    assert limits["timeout_seconds"] == 15.0
    assert limits["ast_nodes"] == 2048
    assert limits["ast_depth"] == 32
    assert limits["source_bytes"] == 16 * 1024
    assert limits["unitary_gates"] == 64
    assert limits["qubits"] == 2


def test_c11_missing_cirq_is_lazy_and_explicit_in_isolated_worker():
    # A process-local import blocker cannot contaminate parent or other tests.
    script = r'''
import importlib.abc, json, sys
class NoCirq(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "cirq" or fullname.startswith("cirq."):
            raise ModuleNotFoundError("optional Cirq deliberately unavailable")
sys.meta_path.insert(0, NoCirq())
from e7q.adapters import adapt
from e7q.language import parse
from e7q.cirq_interop import admit_cirq_source, _worker
source = sys.argv[1]
exported = adapt(parse(source), "cirq").source
assert "cirq" not in sys.modules
assert admit_cirq_source(exported).qubits == 1
result = _worker()
import resource
print(json.dumps({"result": result, "memory": resource.getrlimit(resource.RLIMIT_AS),
                  "cpu": resource.getrlimit(resource.RLIMIT_CPU), "exported": exported}))
'''
    completed = subprocess.run([sys.executable, "-B", "-c", script, native()],
        input=json.dumps({"qubits": 1, "operations": []}), text=True,
        capture_output=True, timeout=15, check=False,
        env=dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1"))
    assert completed.returncode == 0, completed.stderr
    response = json.loads(completed.stdout)
    assert response["result"]["status"] == "UNSUPPORTED"
    assert "Cirq" in response["result"]["reason"]
    assert response["memory"] == [3 * 1024**3] * 2
    assert all(0 < limit <= 15 for limit in response["cpu"])
    assert response["exported"] == sdk()


def test_c14_sampling_is_not_assessed_by_ideal_statevector_results(real_results):
    for result in real_results.values():
        assert result["method"]["observations"] == "ideal probabilities only; no sampling"
        assert result["method"]["sampling_status"] == "NOT_ASSESSED"
        assert "counts" not in result["simulator"]
        assert "shots" not in result["simulator"]
        text = " ".join(result["limitations"]).lower()
        assert "no hardware" in text
        assert "no f2" in text


def test_c06_inconsistent_sdk_observation_is_error_not_quantum_fail(interop, real_results, monkeypatch):
    response = deepcopy(real_results["bell"]["simulator"])
    response["real"] = np.eye(4).tolist()
    response["imag"] = np.zeros((4, 4)).tolist()
    monkeypatch.setattr(interop, "_child_transport", lambda records, timeout: response)
    result = interop.evaluate_roundtrip(REAL_CASES["bell"][0])
    assert result["status"] == "ERROR"
    assert result["native_assessment"] is None


def test_c11_dependency_failure_propagates_without_a_native_inequality(interop, monkeypatch):
    def missing_child(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 0,
            stdout=json.dumps({"status": "UNSUPPORTED", "reason": "missing optional Cirq dependency"}), stderr="")
    monkeypatch.setattr(subprocess, "run", missing_child)
    result = interop.evaluate_roundtrip(native())
    assert result["status"] == "UNSUPPORTED"
    assert "missing optional Cirq dependency" in result["reason"]
    assert result["native_assessment"] is None


@pytest.mark.parametrize("source,status", [
    ("import cirq\nqubits = (", "ERROR"),
    (sdk().replace("qubits[0]", "qubits[True]"), "UNSUPPORTED"),
    (sdk().replace("qubits[0]", "qubits[-1]"), "UNSUPPORTED"),
    (sdk(gate("X", 1)), "UNSUPPORTED"),
    (sdk(gate("CNOT", 0, 0), 2), "UNSUPPORTED"),
    (sdk().replace("import cirq", "import cirq as evil"), "UNSUPPORTED"),
    (sdk().replace("cirq.Circuit()", "cirq.Circuit(__import__('os'))"), "UNSUPPORTED"),
    (sdk().replace("cirq.LineQubit.range(1)", "cirq.LineQubit.range(True)"), "UNSUPPORTED"),
])
def test_c06_literal_arity_index_and_syntax_fail_closed(interop, source, status):
    assert_refused(interop, source, status)


def test_c10_source_budget_counts_utf8_bytes_not_codepoints(interop):
    source = sdk() + "#" + "é" * 8200
    assert len(source) < 16 * 1024 < len(source.encode("utf-8"))
    assert_refused(interop, source, "RESOURCE_REFUSED")
