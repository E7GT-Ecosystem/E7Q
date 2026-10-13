# SPDX-License-Identifier: Apache-2.0
"""Preallocation refusals and unchanged dense probability/seed semantics."""
from dataclasses import replace
import json
import numpy as np
import pytest
from e7q import language as l
from e7q.resources import ExecutionPolicy, ResourceBlocked, AllocationFailed, preflight


def program(n=3, backend="statevector"):
    return l.Program("GHZ", 64, backend, 42, n, n, "GHZ", (
        l.Operation("H", (0,)),
        *(l.Operation("CX", (0, i)) for i in range(1, n)),
        l.Operation("MEASURE", full_register=True),
    ), None, True)


@pytest.mark.parametrize("action", ["run", "unitary", "compare", "density", "channel"])
def test_budget_refusal_precedes_allocation(monkeypatch, action):
    p = program(25, "densitymatrix" if action in {"density", "channel"} else "statevector")
    def forbidden(*args, **kwargs):
        pytest.fail("state allocation attempted before resource refusal")
    monkeypatch.setattr(np, "zeros", forbidden)
    with pytest.raises(ResourceBlocked) as caught:
        if action in {"run", "density"}:
            l.run(p)
        elif action == "unitary":
            l.circuit_unitary(p)
        elif action == "channel":
            l.channel_superoperator(p)
        else:
            l.compare(p, p)
    assert caught.value.assessment["status"] == "RESOURCE_BLOCKED"
    assert caught.value.assessment["estimate_not_measured_rss"]


def test_storage_and_policy():
    p = program()
    r = preflight(p, ExecutionPolicy(respect_host_limits=False))
    assert r["state_storage_bytes"] == 16 * 2**3
    assert r["usable_budget_bytes"] == 256 * 1024**2
    assert preflight(replace(p, backend="densitymatrix"))["state_storage_bytes"] == 16 * 4**3
    with pytest.raises(ResourceBlocked):
        l.run(p, policy=ExecutionPolicy(1, False))
    for invalid in [0, -1, True, 1.2]:
        with pytest.raises(ValueError):
            ExecutionPolicy(invalid)


def test_catchable_allocation_is_not_oom(monkeypatch):
    def fail(*args, **kwargs):
        raise MemoryError("simulated")
    monkeypatch.setattr(l, "_initial_state", fail)
    with pytest.raises(AllocationFailed) as caught:
        l.run(program())
    assert caught.value.assessment["confirmed_oom"] is False
    assert caught.value.assessment["verification_status"] == "NOT_ASSESSED"


def test_integer_samples_preserve_legacy_counts_and_exact_support():
    p = program()
    execution = l.run(p)
    raw = np.abs(execution.state)**2
    labels = [f"{i:03b}" for i in range(8)]
    draws = np.random.default_rng(42).choice(labels, size=64, p=raw)
    expected = {label: int(np.count_nonzero(draws == label)) for label in labels if np.any(draws == label)}
    assert execution.counts == expected
    assert execution.probabilities == pytest.approx({"000": .5, "111": .5})
    # Exact probability support is retained even if one shot misses an outcome.
    assert len(l.run(replace(p, shots=1)).probabilities) == 2


def test_cli_budget_receipt(tmp_path, capsys):
    from e7q.cli import main
    source = tmp_path / "small.e7q"
    source.write_text("context a { shots: 1 }\nqubits q[1]\nbits c[1]\npath a {\nmeasure q -> c\n}\nverify a\n")
    proof = tmp_path / "proof.json"
    assert main(["run", str(source), "--memory-budget-bytes", "1", "--proof", str(proof)]) == 3
    result = json.loads(proof.read_text())
    assert result["execution_status"] == "RESOURCE_BLOCKED"
    assert result["verification_status"] == "NOT_ASSESSED"

@pytest.mark.parametrize("gate", ["CX", "CZ", "SWAP"])
def test_dense_two_qubit_kernel_against_independent_index_oracle(gate):
    for n in range(2, 6):
        state = np.random.default_rng(n).normal(size=2**n) + 1j * np.random.default_rng(n+1).normal(size=2**n)
        for first in range(n):
            for second in range(n):
                if first == second:
                    continue
                a, b = 1 << (n-first-1), 1 << (n-second-1)
                expected = np.empty_like(state)
                for i, value in enumerate(state):
                    j = i
                    if gate == "CX" and i & a:
                        j ^= b
                    elif gate == "CZ" and i & a and i & b:
                        value = -value
                    elif gate == "SWAP" and bool(i & a) != bool(i & b):
                        j ^= a | b
                    expected[j] = value
                np.testing.assert_array_equal(l._apply_two(state, gate, first, second, n), expected)


def test_terminal_preparation_reused_without_rng_change(monkeypatch):
    p = program(4)
    p = replace(p, operations=p.operations[:-1] + tuple(l.Operation("MEASURE", (i,), (i,)) for i in range(4)))
    calls = []
    original = l._apply_two
    def tracked(*args):
        calls.append(args[1])
        return original(*args)
    monkeypatch.setattr(l, "_apply_two", tracked)
    execution = l.run(p)
    assert calls == ["CX"] * 3
    # Preserve one draw per measured bit per shot; preparation consumes no RNG.
    rng = np.random.default_rng(42)
    counts = {"0000": 0, "1111": 0}
    for _ in range(64):
        outcome = int(rng.random() < .5)
        rng.random(3)
        counts[str(outcome)*4] += 1
    assert execution.counts == counts
    assert all(step.get("executed", 64) == 64 for step in execution.proof)


def test_detected_headroom_reduces_usable_budget(monkeypatch):
    import e7q.resources as resources
    monkeypatch.setattr(resources, "host_headroom", lambda: [{"source": "test-container", "headroom_bytes": 1024**2}])
    with pytest.raises(ResourceBlocked) as caught:
        l.run(program())
    assert caught.value.assessment["usable_budget_bytes"] == 512*1024
    assert caught.value.assessment["host_headroom"][0]["source"] == "test-container"
    assert preflight(program(), ExecutionPolicy(respect_host_limits=False))["status"] == "ADMITTED"


def test_both_comparison_inputs_admitted_before_allocating_left(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("comparison allocated before admitting both inputs")
    monkeypatch.setattr(np, "zeros", forbidden)
    p = program()
    with pytest.raises(ResourceBlocked):
        l.compare(p, replace(p, bits=4096), policy=ExecutionPolicy(67_160_000, False))


@pytest.mark.parametrize("failure", ["signal", "timeout", "invalid-receipt"])
def test_benchmark_supervisor_never_fabricates_oom_or_worker_receipt(monkeypatch, tmp_path, failure):
    import importlib.util
    from pathlib import Path
    import subprocess
    import sys
    from types import SimpleNamespace
    path = Path(__file__).resolve().parents[1] / "scripts/benchmark_execution.py"
    spec = importlib.util.spec_from_file_location("bounded_benchmark_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module.subprocess, "check_output", lambda args, **kw: "" if "status" in args else "f"*40+"\n")
    def failed_worker(args, **kwargs):
        if failure == "timeout":
            raise subprocess.TimeoutExpired(args, 30)
        return SimpleNamespace(returncode=-9 if failure == "signal" else 0, stdout="not a receipt", stderr="")
    monkeypatch.setattr(module.subprocess, "run", failed_worker)
    output = tmp_path / "result.json"
    monkeypatch.setattr(sys, "argv", [str(path), "--output", str(output)])
    with pytest.raises(SystemExit) as caught:
        module.main()
    assert caught.value.code == 1
    artifact = json.loads(output.read_text())
    assert artifact["benchmark_status"] == "FAIL"
    for row in artifact["results"]:
        assert row["peak_rss_bytes"] is None
        assert row["confirmed_oom"] is False
        assert row["completion_receipt_received"] is False
        assert row["status"] == ("FAILED" if failure == "invalid-receipt" else "INCOMPLETE")
        if failure == "signal":
            assert row["signal"] == 9
