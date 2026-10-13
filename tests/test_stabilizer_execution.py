# SPDX-License-Identifier: Apache-2.0
"""Optional independent-reference checks; no hardware or universal claim."""
from dataclasses import replace
import itertools
import json
import sys
import subprocess
import numpy as np
import pytest

stim = pytest.importorskip("stim")
qiskit = pytest.importorskip("qiskit")
from qiskit.quantum_info import Statevector, DensityMatrix, Pauli
from e7q.language import Program, Operation, parse, run, verify, _ONE_QUBIT
from e7q.resources import ExecutionPolicy, ResourceBlocked
from e7q.stabilizer import BackendUnsupported


def program(n=3, operations=None, shots=128):
    if operations is None:
        operations = (Operation("H", (0,)), *(Operation("CX", (0, i)) for i in range(1, n)), Operation("MEASURE", full_register=True))
    return Program("Clifford", shots, "stabilizer", 42, n, n, "main", tuple(operations), None, True)


def independent_state(p):
    qc = qiskit.QuantumCircuit(p.qubits)
    for op in p.operations:
        if op.gate == "MEASURE":
            continue
        assert op.condition is None
        method = {"CX": "cx", "CZ": "cz", "SWAP": "swap"}.get(op.gate, op.gate.lower())
        getattr(qc, method)(*(p.qubits - 1 - q for q in op.qubits))
    return Statevector.from_instruction(qc)


@pytest.mark.parametrize("n", [2, 3, 5])
def test_bell_ghz_exact_against_dense_and_qiskit(n):
    p = program(n)
    e = run(p)
    dense = run(replace(p, backend="statevector"))
    reference = independent_state(p)
    np.testing.assert_allclose(dense.state, reference.data, atol=1e-14)
    for pauli in ("X"*n, "ZZ"+"I"*(n-2), "Z"+"I"*(n-1), "Y"*n):
        value = e.premeasurement.peek_observable_expectation(stim.PauliString(pauli))
        assert value == pytest.approx(reference.expectation_value(Pauli(pauli)).real, abs=1e-14)
    assert set(e.counts) <= {"0"*n, "1"*n}
    assert verify(e, pauli_checks=[{"pauli": "X"*n, "expected": 1}])["status"] == "PASS"


def test_operand_order_all_gates_against_independent_reference():
    rng = np.random.default_rng(142)
    for n in [2, 3, 4]:
        for case in range(8):
            ops = []
            for _ in range(16):
                gate = rng.choice(["X", "Y", "Z", "H", "S", "CX", "CZ", "SWAP"])
                qs = tuple(map(int, rng.choice(n, size=2 if gate in {"CX", "CZ", "SWAP"} else 1, replace=False)))
                ops.append(Operation(str(gate), qs))
            ops.append(Operation("MEASURE", full_register=True))
            p = program(n, ops)
            e = run(p)
            reference = independent_state(p)
            np.testing.assert_allclose(run(replace(p, backend="statevector")).state, reference.data, atol=1e-14)
            for pauli in itertools.product("IXYZ", repeat=n):
                label = "".join(pauli)
                assert e.premeasurement.peek_observable_expectation(stim.PauliString(label)) == pytest.approx(reference.expectation_value(Pauli(label)).real, abs=1e-14)


def test_individual_and_full_measurement_classical_mapping():
    p = program(3, [Operation("X", (2,)), Operation("MEASURE", (2,), (0,)), Operation("MEASURE", (0,), (2,))])
    assert run(p).counts == {"100": p.shots}
    assert run(replace(p, backend="statevector")).counts == {"100": p.shots}
    full = replace(p, operations=(Operation("X", (2,)), Operation("MEASURE", full_register=True)))
    assert run(full).counts == {"001": p.shots}
    parsed = parse("context a { backend: stabilizer seed: 42 shots: 4 }\nqubits q[1]\nbits c[1]\npath a {\n X q[0]\n measure q -> c\n}\nverify a\n")
    assert run(parsed).counts == {"1": 4}


def test_mid_circuit_control_and_assertion():
    ops = [Operation("H", (0,)), Operation("MEASURE", (0,), (1,)), Operation("X", (2,), condition=(1, 1)), Operation("MEASURE", (2,), (0,)), Operation("MEASURE", (0,), (2,))]
    p = program(3, ops, shots=1024)
    for backend in ["stabilizer", "statevector"]:
        e = run(replace(p, backend=backend))
        assert set(e.counts) == {"000", "111"}
        assert abs(e.counts["000"] / p.shots - .5) < .06
    # Independent analytic branch instrument: H measurement gives .5/.5;
    # conditional X records the branch at c0 and repeated q0 records it at c2.
    e = run(p)
    assert verify(e, pauli_checks=[{"pauli": "XXX", "expected": 1}])["status"] == "NOT_ASSESSED"
    asserted = program(1, [Operation("MEASURE", (0,), (0,)), Operation("ASSERT", bits=(0,), condition=(0, 1), label="assert c[0] == 1")])
    assert verify(run(asserted))["status"] == "FAIL"


def test_unsupported_gate_noise_checks_and_empty_verification():
    for op in [Operation("T", (0,)), Operation("NOISE", (0,), label="phase_flip", probability=.5)]:
        p = program(1, [op, Operation("MEASURE", full_register=True)])
        with pytest.raises(BackendUnsupported):
            run(p)
    p = replace(program(2), require_normalized=False)
    assert verify(run(p))["status"] == "NOT_ASSESSED"
    p = replace(p, allowed_outcomes=frozenset({"00", "11"}))
    assert verify(run(p))["checks"][0]["status"] == "UNSUPPORTED"
    assert verify(run(program(2)), pauli_checks=[{"unknown": "XX"}])["status"] == "NOT_ASSESSED"


def test_ghz_25_budget_exact_checks_and_phase_negative():
    p = program(25, shots=256)
    e = run(p, policy=ExecutionPolicy(128*1024**2))
    checks = [{"pauli": "X"*25, "expected": 1}]
    checks += [{"pauli": "I"*i+"ZZ"+"I"*(23-i), "expected": 1} for i in range(24)]
    r = verify(e, pauli_checks=checks)
    assert r["status"] == "PASS"
    assert r["resources"]["estimated_working_bytes"] < 128*1024**2
    assert r["probabilities"] is None
    assert len(r["state"]["generators"]) == 25
    json.dumps(r)
    minus = replace(p, operations=p.operations[:-1]+(Operation("Z", (0,)), p.operations[-1]))
    negative = verify(run(minus), pauli_checks=checks)
    assert negative["status"] == "FAIL"
    assert negative["checks"][1]["value"] == -1
    assert all(c["passed"] for c in negative["checks"][2:])
    with pytest.raises(ResourceBlocked):
        run(p, policy=ExecutionPolicy(1, False))


def test_incoherent_mixture_negative_and_independent_density_reference():
    p = program(3)
    noisy = replace(p, backend="densitymatrix", operations=p.operations[:-1]+(Operation("NOISE", (0,), label="phase_flip", probability=.5), p.operations[-1]))
    density = run(noisy).state
    mixture = np.zeros((8, 8), complex)
    mixture[0, 0] = mixture[-1, -1] = .5
    np.testing.assert_allclose(density, mixture, atol=1e-14)
    reference = DensityMatrix(mixture)
    assert reference.expectation_value(Pauli("ZZI")).real == 1
    assert reference.expectation_value(Pauli("XXX")).real == 0
    assert np.trace(density @ density).real == pytest.approx(.5)
    # Positive and opposite phase also have ZZ=+1, but XXX=+1/-1.
    assert independent_state(p).expectation_value(Pauli("XXX")).real == pytest.approx(1)


def test_seed_replay_and_missing_dependency_keeps_core_usable():
    p = program()
    assert run(p).counts == run(p).counts
    code = '''import builtins
original = builtins.__import__
def blocked(name, *args, **kwargs):
    if name == "stim": raise ImportError("test: optional dependency absent")
    return original(name, *args, **kwargs)
builtins.__import__ = blocked
from e7q.language import parse, run
from e7q.stabilizer import BackendUnsupported
source = "context a { shots: 1 }\\nqubits q[1]\\nbits c[1]\\npath a {\\nmeasure q -> c\\n}\\nverify a\\n"
assert run(parse(source)).counts == {"0": 1}
try: run(parse(source.replace("shots: 1", "shots: 1 backend: stabilizer")))
except BackendUnsupported: pass
else: raise AssertionError("missing backend accepted")
'''
    subprocess.run([sys.executable, "-c", code], check=True, timeout=10)


def test_mid_circuit_against_independent_qiskit_branch_instrument():
    # Implement projective measurement and feed-forward independently of E7Q/Stim.
    qc = qiskit.QuantumCircuit(3)
    qc.h(2)  # native q0
    initial = Statevector.from_instruction(qc).data
    distribution = {}
    for bit in (0, 1):
        branch = initial.copy()
        for index in range(8):
            if (index >> 2) != bit:
                branch[index] = 0
        probability = np.vdot(branch, branch).real
        branch /= np.sqrt(probability)
        if bit:
            conditional = qiskit.QuantumCircuit(3)
            conditional.x(0)  # native q2
            branch = Statevector(branch).evolve(conditional).data
        for index, weight in enumerate(np.abs(branch)**2):
            if weight < 1e-15:
                continue
            # c0<-q2, c1<-first q0 measurement, c2<-second q0 measurement.
            label = f"{index & 1}{bit}{index >> 2}"
            distribution[label] = distribution.get(label, 0) + probability * weight
    assert distribution == pytest.approx({"000": .5, "111": .5})
    p = program(3, [Operation("H", (0,)), Operation("MEASURE", (0,), (1,)), Operation("X", (2,), condition=(1, 1)), Operation("MEASURE", (2,), (0,)), Operation("MEASURE", (0,), (2,))], shots=1024)
    for backend in ["stabilizer", "statevector"]:
        counts = run(replace(p, backend=backend)).counts
        for label, probability in distribution.items():
            assert counts[label]/p.shots == pytest.approx(probability, abs=.06)


def test_versioned_result_and_failure_schemas():
    from pathlib import Path
    jsonschema = pytest.importorskip("jsonschema")
    from e7q.resources import failure_result
    root = Path(__file__).resolve().parents[1]
    schema = json.loads((root/"schemas/stabilizer-result-v1.schema.json").read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(verify(run(program(2))), schema)
    jsonschema.validate(verify(run(replace(program(2), require_normalized=False))), schema)
    schema = json.loads((root/"schemas/execution-outcome-v1.schema.json").read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    with pytest.raises(ResourceBlocked) as caught:
        run(program(25), policy=ExecutionPolicy(1, False))
    jsonschema.validate(failure_result(caught.value), schema)
    from e7q.cli import main
    # Unsupported verification is a completed simulation but not an assessed property.
    result = verify(run(program(2)), pauli_checks=[{"pauli":"XX", "expected":0}])
    assert result["execution_status"] == "COMPLETED"
    assert result["status"] == "FAIL"


def test_unsupported_comparison_does_not_attempt_dense_preflight(monkeypatch):
    from e7q.language import compare
    import e7q.resources as resources
    def forbidden(*args, **kwargs):
        pytest.fail("unsupported compact comparison entered dense preflight")
    monkeypatch.setattr(resources, "preflight", forbidden)
    with pytest.raises(BackendUnsupported, match="no fallback"):
        compare(program(25), program(25))
