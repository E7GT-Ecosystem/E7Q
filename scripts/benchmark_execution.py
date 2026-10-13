#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Bounded execution benchmark with external completion/signal accounting.

Run from a clean committed checkout. Baseline replay admits only GHZ-12/14,
never the unsafe reported GHZ-25 dense experiment. All circuits are synthetic.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version, PackageNotFoundError
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import time
import types

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "ce9d969a3337ee76b894dae11e8e243ff09a7390"
TIMEOUT_SECONDS = 30
WORKER_EXTRA_ADDRESS_BYTES = 512 * 1024**2


def source(n, backend, mode="full", *, shots=8, variant="plus"):
    gates = " H q[0]\n" + "".join(f" CX q[0], q[{i}]\n" for i in range(1, n))
    if variant == "minus":
        gates += " Z q[0]\n"
    elif variant == "mixture":
        gates += " noise phase_flip(0.5) q[0]\n"
    elif variant == "nonclifford":
        gates += " T q[0]\n"
    measure = " measure q -> c\n" if mode == "full" else "".join(f" measure q[{i}] -> c[{i}]\n" for i in range(n))
    return f"context GHZ{n} {{\n shots: {shots}\n backend: {backend}\n seed: 42\n}}\nqubits q[{n}]\nbits c[{n}]\ninvariant normalized\npath GHZ {{\n" + gates + measure + "}\nverify GHZ\n"


def versions():
    output = {"python": platform.python_version()}
    for name in ["e7q", "numpy", "stim", "qiskit", "jsonschema"]:
        try:
            output[name] = version(name)
        except PackageNotFoundError:
            output[name] = "unavailable"
    return output


def ghz_checks(n):
    return ([{"pauli": "X"*n, "expected": 1}] +
            [{"pauli": "I"*i + "ZZ" + "I"*(n-i-2), "expected": 1} for i in range(n-1)] +
            [{"pauli": "I"*i + "Z" + "I"*(n-i-1), "expected": 0} for i in range(n)])


def cases(baseline=False):
    output = [{"id": f"ghz-{n}-{mode}-dense", "width": n, "backend": "statevector", "mode": mode, "shots": 8, "variant": "plus", "budget": 256*1024**2}
              for n, mode in [(12, "full"), (12, "individual"), (14, "individual")]]
    if not baseline:
        output += [{"id": f"ghz-25-{mode}-stabilizer", "width": 25, "backend": "stabilizer", "mode": mode, "shots": 1024, "variant": "plus", "budget": 128*1024**2} for mode in ["full", "individual"]]
        output += [
            {"id": "ghz-25-opposite-phase", "width": 25, "backend": "stabilizer", "mode": "full", "shots": 1024, "variant": "minus", "budget": 128*1024**2},
            {"id": "ghz-3-incoherent-mixture", "width": 3, "backend": "densitymatrix", "mode": "full", "shots": 8, "variant": "mixture", "budget": 128*1024**2},
            {"id": "ghz-25-dense-blocked", "width": 25, "backend": "statevector", "mode": "individual", "shots": 8, "variant": "plus", "budget": 128*1024**2},
            {"id": "ghz-25-density-blocked", "width": 25, "backend": "densitymatrix", "mode": "full", "shots": 8, "variant": "plus", "budget": 128*1024**2},
            {"id": "nonclifford-refused", "width": 3, "backend": "stabilizer", "mode": "full", "shots": 8, "variant": "nonclifford", "budget": 128*1024**2},
        ]
    for case in output:
        case["expected_status"] = ("RESOURCE_BLOCKED" if "blocked" in case["id"] else
                                   "UNSUPPORTED" if case["variant"] == "nonclifford" else
                                   "FAIL" if case["variant"] == "minus" else "PASS")
    return output


def worker(case, baseline):
    import numpy as np
    if baseline:
        # Load exactly the retained baseline module, not the editable current code.
        raw = subprocess.check_output(["git", "show", BASELINE+":src/e7q/language.py"], cwd=ROOT)
        module = types.ModuleType("e7q_benchmark_baseline")
        sys.modules[module.__name__] = module
        exec(compile(raw, BASELINE+":src/e7q/language.py", "exec"), module.__dict__)
        language = module
        assert case["width"] <= 14 and case["backend"] == "statevector"
    else:
        import e7q.language as language
        raw = Path(language.__file__).read_bytes()
    # Enforce a bounded extra address-space margin after importing NumPy. This is
    # not an RSS limit and is separate from the simulator's declared budget.
    enforcement = {"requested_additional_bytes": WORKER_EXTRA_ADDRESS_BYTES, "enforced": False}
    if sys.platform.startswith("linux"):
        current = int(Path("/proc/self/statm").read_text().split()[0]) * os.sysconf("SC_PAGE_SIZE")
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        limit = min([current + WORKER_EXTRA_ADDRESS_BYTES] + [x for x in [soft, hard] if x != resource.RLIM_INFINITY])
        resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
        enforcement.update(enforced=True, mechanism="posix-RLIMIT_AS", effective_address_space_bytes=limit)
    text = source(case["width"], case["backend"], case["mode"], shots=case["shots"], variant=case["variant"])
    row = {**case, "source": text, "circuit_sha256": hashlib.sha256(text.encode()).hexdigest(),
           "language_sha256": hashlib.sha256(raw).hexdigest(), "versions": versions(), "seed": 42,
           "worker_address_limit": enforcement, "assessed_properties": []}
    start = time.perf_counter()
    try:
        p = language.parse(text)
        if baseline:
            execution = language.run(p)
        else:
            from e7q.resources import ExecutionPolicy, preflight
            policy = ExecutionPolicy(case["budget"])
            row["resource_estimate"] = preflight(p, policy)
            execution = language.run(p, policy=policy)
        if case["backend"] == "stabilizer":
            result = language.verify(execution, pauli_checks=ghz_checks(p.qubits))
            row["assessed_properties"] = result["checks"]
        else:
            result = language.verify(execution)
            row["assessed_properties"] = [*result["checks"], {"name": "Z counts", "method": "finite-shot observation only; no coherence assessment", "counts": execution.counts}]
        row.update(status=result["status"], counts=execution.counts, result=result)
        if case["variant"] == "mixture":
            # Small independent density oracle only (n=3). No dense 25-qubit path.
            from qiskit.quantum_info import DensityMatrix, Pauli
            rho = execution.state
            expected = np.zeros((8, 8), complex)
            expected[0, 0] = expected[-1, -1] = .5
            np.testing.assert_allclose(rho, expected, atol=1e-14)
            reference = DensityMatrix(expected)
            coherence = float(np.trace(rho[:, ::-1]).real)
            corr = float(sum(rho[i, i].real * (1 if ((i >> 2)&1) == ((i >> 1)&1) else -1) for i in range(8)))
            assert abs(coherence - reference.expectation_value(Pauli("XXX")).real) < 1e-14
            assert abs(corr - reference.expectation_value(Pauli("ZZI")).real) < 1e-14
            row["assessed_properties"] += [
                {"name": "XXX coherence", "method": "numerical density expectation plus independent Qiskit reference", "value": coherence, "GHZ_plus_expected": 1, "status": "FAIL", "scope": "premeasurement density"},
                {"name": "ZZI correlation", "method": "numerical density expectation plus independent Qiskit reference", "value": corr, "status": "PASS", "scope": "premeasurement density"}]
            row["ghz_property_status"] = "FAIL"
    except Exception as exc:
        from e7q.resources import ResourceBlocked, AllocationFailed, failure_result
        from e7q.stabilizer import BackendUnsupported
        if isinstance(exc, (ResourceBlocked, AllocationFailed)):
            row.update(status=failure_result(exc)["status"], result=failure_result(exc))
        elif isinstance(exc, BackendUnsupported):
            row.update(status="UNSUPPORTED", detail=exc.assessment)
        else:
            row.update(status="FAILED", detail={"exception": type(exc).__name__, "message": str(exc)})
    row.update(elapsed_seconds=time.perf_counter()-start,
               peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1024 if sys.platform.startswith("linux") else 1),
               rss_scope="whole fresh worker including imports, execution, verification and reference (when used)")
    print(json.dumps(row, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--baseline", action="store_true")
    parser.add_argument("--worker", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        worker(json.loads(args.worker), args.baseline)
        return
    if args.output is None:
        parser.error("--output is required")
    if args.output.exists():
        parser.error("output already exists; use a new artifact path")
    current = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)
    if dirty:
        parser.error("commit the benchmark and implementation before recording results")
    env = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1")
    rows = []
    for case in cases(args.baseline):
        command = [sys.executable, "scripts/benchmark_execution.py", "--worker", json.dumps(case, sort_keys=True)]
        if args.baseline:
            command.append("--baseline")
        start = time.perf_counter()
        try:
            process = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            row = {**case, "status": "INCOMPLETE", "supervisor_reason": "timeout", "peak_rss_bytes": None, "confirmed_oom": False}
        else:
            if process.returncode == 0:
                try:
                    row = json.loads(process.stdout)
                    if not isinstance(row, dict) or not {"status", "elapsed_seconds", "peak_rss_bytes"} <= row.keys():
                        raise ValueError("missing worker completion fields")
                except (ValueError, TypeError):
                    row = {**case, "status": "FAILED", "supervisor_reason": "invalid-worker-receipt",
                           "peak_rss_bytes": None, "confirmed_oom": False}
            else:
                row = {**case, "status": "INCOMPLETE" if process.returncode < 0 else "FAILED",
                       "supervisor_reason": "termination-signal" if process.returncode < 0 else "worker-error",
                       "signal": -process.returncode if process.returncode < 0 else None,
                       "exit_code": process.returncode, "confirmed_oom": False, "peak_rss_bytes": None,
                       "stderr_tail": process.stderr[-2000:]}
        row.update(command=command, supervisor_elapsed_seconds=time.perf_counter()-start,
                   timeout_seconds=TIMEOUT_SECONDS, completion_receipt_received="elapsed_seconds" in row)
        row["expected_outcome_met"] = row["status"] == case["expected_status"]
        rows.append(row)
    result = {"schema": "e7q.execution-benchmark/1", "created_at": datetime.now(timezone.utc).isoformat(),
              "implementation_commit": BASELINE if args.baseline else current, "harness_commit": current,
              "environment": {"platform": platform.platform(), "machine": platform.machine(), "versions": versions(),
                              "thread_settings": {"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"}},
              "scope": "synthetic local simulator execution; no hardware, advantage, universal equivalence or E7G-T conformance",
              "supplied_observations": {"reproduced": False, "GHZ25": "Reported signal 9 near 1 GiB RSS; structural import/schema/planning passed; smaller native cases slow/timed out. Not confirmed OOM."},
              "results": rows, "benchmark_status": "PASS" if all(row["expected_outcome_met"] for row in rows) else "FAIL"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"output": str(args.output), "benchmark_status": result["benchmark_status"], "statuses": {row["id"]: row["status"] for row in rows}}, indent=2))
    raise SystemExit(0 if result["benchmark_status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
