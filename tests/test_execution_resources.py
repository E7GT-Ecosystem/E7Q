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
