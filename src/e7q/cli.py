# SPDX-License-Identifier: Apache-2.0
"""Command-line interface for E7Q."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .adapters import adapt, adapter_result
from .assessment import assess_receipt, load_reference, load_receipt
from .artifacts import load_artifact, validate_artifact
from .bundles import build_execution_bundle
from .campaigns import assess_replication, load_replication_receipts
from .deterministic import (
    assess_deterministic_reference,
    load_deterministic_reference,
    load_external_receipt,
)
from .drift import assess_drift, load_replication_report
from .external_bundles import verify_external_bundle
from .experiments import assess_comparative_experiment, load_comparative_experiment
from .ir import (
    build_external_circuit_graph,
    load_external_circuit_manifest,
    validate_graph,
)
from .ir.graph import graph_summary
from .openqasm2 import import_openqasm2
from .trends import assess_trend, load_trend_reports
from .calibration import load_snapshot, select_target
from .ingestion import load_vendor_export
from .language import (
    E7QError, backend_profile, compare, comparison_result, compilation_result,
    compile_topology, load, openqasm, proof_json, run, topology_edges, verify,
)
from .planning import plan, plan_result
from .qec import (
    QECError, StabilizerCode, analyze_error, qec_proof_json,
    syndrome_homomorphism_report,
)
from .results import build_execution_receipt, load_execution_bundle, load_execution_result


def _native_gates(value: str) -> frozenset[str]:
    return frozenset(item.strip().upper() for item in value.split(",") if item.strip())


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="e7q")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "verify"):
        command = commands.add_parser(name)
        command.add_argument("source")
        command.add_argument("--proof", type=Path)
    export = commands.add_parser("export")
    export.add_argument("source")
    export.add_argument(
        "--format", choices=["openqasm", "qiskit", "cirq"], default="openqasm"
    )
    export.add_argument("--proof", type=Path)
    export.add_argument("-o", "--output", type=Path)
    compare_command = commands.add_parser("compare")
    compare_command.add_argument("first")
    compare_command.add_argument("second")
    compare_command.add_argument(
        "--criterion",
        choices=[
            "exact", "global-phase", "measurement", "tolerance",
            "channel-exact", "channel-tolerance", "channel-measurement",
        ],
        default="global-phase",
    )
    compare_command.add_argument("--tolerance", type=float, default=1e-12)
    compare_command.add_argument("--proof", type=Path)
    capabilities = commands.add_parser("capabilities")
    capabilities.add_argument("source")
    ingest = commands.add_parser("ingest-calibration")
    ingest.add_argument("source", type=Path)
    ingest.add_argument("--provider", choices=["ibm", "google"], required=True)
    ingest.add_argument("--max-age-hours", type=float)
    ingest.add_argument("--observation-pilot", action="store_true")
    ingest.add_argument("-o", "--output", required=True, type=Path)
    bundle = commands.add_parser("bundle")
    bundle.add_argument("source", type=Path)
    bundle.add_argument("--snapshot", required=True, type=Path)
    bundle.add_argument("--shots", type=int, default=1000)
    bundle.add_argument("--temporal-orientation-pilot", action="store_true")
    bundle.add_argument("-o", "--output", required=True, type=Path)
    receipt = commands.add_parser("receipt")
    receipt.add_argument("bundle", type=Path)
    receipt.add_argument("--result", required=True, type=Path)
    receipt.add_argument("--observation-pilot", action="store_true")
    receipt.add_argument("--temporal-orientation-pilot", action="store_true")
    receipt.add_argument("-o", "--output", required=True, type=Path)
    assess = commands.add_parser("assess")
    assess.add_argument("receipt", type=Path)
    assess.add_argument("--reference", required=True, type=Path)
    assess.add_argument("-o", "--output", required=True, type=Path)
    replicate = commands.add_parser("replicate")
    replicate.add_argument("receipts", nargs="+", type=Path)
    replicate.add_argument("--max-pairwise-tvd", type=float, default=0.1)
    replicate.add_argument("--significance-level", type=float, default=0.05)
    replicate.add_argument("--observation-pilot", action="store_true")
    replicate.add_argument("--temporal-orientation-pilot", action="store_true")
    replicate.add_argument("-o", "--output", required=True, type=Path)
    drift = commands.add_parser("drift")
    drift.add_argument("baseline", type=Path)
    drift.add_argument("candidate", type=Path)
    drift.add_argument("--max-total-variation", type=float, default=0.1)
    drift.add_argument("--significance-level", type=float, default=0.05)
    drift.add_argument("--observation-pilot", action="store_true")
    drift.add_argument("--temporal-orientation-pilot", action="store_true")
    drift.add_argument("-o", "--output", required=True, type=Path)
    trend = commands.add_parser("trend")
    trend.add_argument("campaigns", nargs="+", type=Path)
    trend.add_argument("--max-total-variation", type=float, default=0.1)
    trend.add_argument("--significance-level", type=float, default=0.05)
    trend.add_argument("--observation-pilot", action="store_true")
    trend.add_argument("--temporal-orientation-pilot", action="store_true")
    trend.add_argument("-o", "--output", required=True, type=Path)
    experiment = commands.add_parser(
        "assess-experiment",
        help="assess a bounded one- or two-factor comparative experiment",
    )
    experiment.add_argument("source", type=Path)
    experiment.add_argument("--relative-support-pilot", action="store_true")
    experiment.add_argument("-o", "--output", required=True, type=Path)
    artifact = commands.add_parser("validate-artifact")
    artifact.add_argument("source", type=Path)
    artifact.add_argument("-o", "--output", type=Path)
    ir = commands.add_parser(
        "ir",
        help="build, validate, and inspect E7Q-IR evidence graphs",
    )
    ir_actions = ir.add_subparsers(dest="ir_action", required=True)
    ir_build = ir_actions.add_parser(
        "build",
        help="build an external circuit workflow graph without executing it",
    )
    ir_build.add_argument("manifest", type=Path)
    ir_build.add_argument("-o", "--output", required=True, type=Path)
    ir_validate = ir_actions.add_parser(
        "validate",
        help="validate F0 structural or F1 referential conformance",
    )
    ir_validate.add_argument("source", type=Path)
    ir_validate.add_argument("--level", choices=["F0", "F1"], default="F1")
    ir_validate.add_argument("-o", "--output", type=Path)
    ir_inspect = ir_actions.add_parser(
        "inspect",
        help="print a bounded graph inventory without semantic claims",
    )
    ir_inspect.add_argument("source", type=Path)
    ir_inspect.add_argument("-o", "--output", type=Path)
    external_bundle = commands.add_parser(
        "external-bundle",
        help="safely inspect a supplied external execution-evidence package",
    )
    external_actions = external_bundle.add_subparsers(
        dest="external_bundle_action", required=True
    )
    external_verify = external_actions.add_parser(
        "verify",
        help="verify a ZIP or directory and emit a bounded E7Q receipt",
    )
    external_verify.add_argument("source", type=Path)
    external_verify.add_argument(
        "--include-counts",
        action="store_true",
        help="embed normalized raw counts in the receipt",
    )
    external_verify.add_argument("-o", "--output", type=Path)
    qasm2_import = commands.add_parser(
        "import-openqasm2",
        help="import a bounded OpenQASM 2.0 circuit as an auditable artifact",
    )
    qasm2_import.add_argument("source", type=Path)
    qasm2_import.add_argument("--name", default="ImportedCircuit")
    qasm2_import.add_argument("-o", "--output", type=Path)
    deterministic = commands.add_parser(
        "assess-deterministic",
        help="assess embedded external counts against deterministic bit expectations",
    )
    deterministic.add_argument("receipt", type=Path)
    deterministic.add_argument("--reference", required=True, type=Path)
    deterministic.add_argument("-o", "--output", required=True, type=Path)
    qec_syndrome = commands.add_parser(
        "qec-syndrome",
        help="analyze a phase-insensitive Pauli error against stabilizer generators",
    )
    qec_syndrome.add_argument("error")
    qec_syndrome.add_argument("--generator", action="append", required=True)
    qec_syndrome.add_argument("--name", default="declared stabilizer code")
    qec_syndrome.add_argument("-o", "--output", type=Path)
    qec_homomorphism = commands.add_parser(
        "qec-homomorphism",
        help="check sigma(EF) = sigma(E) xor sigma(F)",
    )
    qec_homomorphism.add_argument("left")
    qec_homomorphism.add_argument("right")
    qec_homomorphism.add_argument("--generator", action="append", required=True)
    qec_homomorphism.add_argument("--name", default="declared stabilizer code")
    qec_homomorphism.add_argument("-o", "--output", type=Path)
    select = commands.add_parser("select")
    select.add_argument("source")
    select.add_argument("--snapshot", required=True, type=Path)
    select.add_argument("--proof", type=Path)
    for name in ("compile", "plan"):
        command = commands.add_parser(name)
        command.add_argument("source")
        command.add_argument(
            "--topology",
            choices=["linear", "ring", "all-to-all"],
            default="linear",
            help=(
                "hardware coupling-graph layout (legacy option name; not an "
                "E7G-T UC4 mathematical topology)"
            ),
        )
        command.add_argument(
            "--native-gates",
            default="X,Y,Z,H,S,T,CX,CZ,SWAP",
            help="comma-separated native gate set",
        )
        command.add_argument("--proof", type=Path)
        if name == "compile":
            command.add_argument("-o", "--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "ir":
            if args.ir_action == "build":
                manifest, base = load_external_circuit_manifest(args.manifest)
                graph = build_external_circuit_graph(manifest, base)
                args.output.write_text(
                    json.dumps(graph, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                print(f"E7Q-IR evidence graph: {args.output}")
                return 0
            graph = load_artifact(args.source)
            report = (
                validate_graph(graph, level=args.level)
                if args.ir_action == "validate"
                else graph_summary(graph)
            )
            content = json.dumps(report, indent=2, sort_keys=True) + "\n"
            if args.output:
                args.output.write_text(content, encoding="utf-8")
                label = (
                    "conformance report"
                    if args.ir_action == "validate"
                    else "graph summary"
                )
                print(f"E7Q-IR {label}: {args.output}")
            else:
                print(content, end="")
            return 0 if args.ir_action == "inspect" or report["status"] == "PASS" else 1
        if args.command == "import-openqasm2":
            try:
                source = args.source.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                raise E7QError(f"invalid OpenQASM 2 source: {exc}") from exc
            report = import_openqasm2(source, name=args.name)
            content = json.dumps(report, indent=2, sort_keys=True) + "\n"
            if args.output:
                args.output.write_text(content, encoding="utf-8")
                print(f"OpenQASM 2 import artifact: {args.output}")
            else:
                print(content, end="")
            return 0
        if args.command == "assess-deterministic":
            report = assess_deterministic_reference(
                load_external_receipt(args.receipt),
                load_deterministic_reference(args.reference),
            )
            args.output.write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            print(f"Deterministic assessment: {args.output}")
            return 0 if report["status"] == "PASS" else 1
        if args.command == "external-bundle":
            report = verify_external_bundle(
                args.source,
                include_counts=args.include_counts,
            )
            content = json.dumps(report, indent=2, sort_keys=True) + "\n"
            if args.output:
                args.output.write_text(content, encoding="utf-8")
                print(f"External evidence receipt: {args.output}")
            else:
                print(content, end="")
            return 0 if report["status"] == "PASS" else 1
        if args.command in {"qec-syndrome", "qec-homomorphism"}:
            code = StabilizerCode(args.name, tuple(args.generator))
            report = (
                analyze_error(code, args.error)
                if args.command == "qec-syndrome"
                else syndrome_homomorphism_report(code, args.left, args.right)
            )
            content = qec_proof_json(report)
            if args.output:
                args.output.write_text(content, encoding="utf-8")
                print(f"QEC pilot report: {args.output}")
            else:
                print(content, end="")
            return 0 if report.get("status", "PASS") == "PASS" else 1
        if args.command == "ingest-calibration":
            result = load_vendor_export(
                args.source,
                args.provider,
                max_age_hours=args.max_age_hours,
                include_observational_claim_pilot=args.observation_pilot,
            )
            args.output.write_text(
                json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            print(f"Calibration snapshot: {args.output}")
            return 0
        if args.command == "bundle":
            source = args.source.read_bytes()
            result = build_execution_bundle(
                load(args.source),
                source,
                load_snapshot(args.snapshot),
                shots=args.shots,
                include_temporal_orientation_pilot=args.temporal_orientation_pilot,
            )
            args.output.write_text(
                json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            print(f"Execution bundle: {args.output}")
            return 0
        if args.command == "receipt":
            bundle_value, bundle_bytes = load_execution_bundle(args.bundle)
            result_value, result_bytes = load_execution_result(args.result)
            receipt = build_execution_receipt(
                bundle_value,
                bundle_bytes,
                result_value,
                result_bytes,
                include_observational_claim_pilot=args.observation_pilot,
                include_temporal_orientation_pilot=args.temporal_orientation_pilot,
            )
            args.output.write_text(
                json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            print(f"Execution receipt: {args.output}")
            return 0
        if args.command == "assess":
            assessment = assess_receipt(
                load_receipt(args.receipt), load_reference(args.reference)
            )
            args.output.write_text(
                json.dumps(assessment, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            print(f"Execution assessment: {args.output}")
            return 0 if assessment["status"] == "PASS" else 1
        if args.command == "replicate":
            report = assess_replication(
                load_replication_receipts(args.receipts),
                max_pairwise_tvd=args.max_pairwise_tvd,
                significance_level=args.significance_level,
                include_observational_claim_pilot=args.observation_pilot,
                include_temporal_orientation_pilot=args.temporal_orientation_pilot,
            )
            args.output.write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            print(f"Replication report: {args.output}")
            return 0 if report["status"] == "PASS" else 1
        if args.command == "drift":
            report = assess_drift(
                load_replication_report(args.baseline),
                load_replication_report(args.candidate),
                max_total_variation=args.max_total_variation,
                significance_level=args.significance_level,
                include_observational_claim_pilot=args.observation_pilot,
                include_temporal_orientation_pilot=args.temporal_orientation_pilot,
            )
            args.output.write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            print(f"Drift report: {args.output}")
            return 0 if report["status"] == "NO_DRIFT" else 1
        if args.command == "trend":
            report = assess_trend(
                load_trend_reports(args.campaigns),
                max_total_variation=args.max_total_variation,
                significance_level=args.significance_level,
                include_observational_claim_pilot=args.observation_pilot,
                include_temporal_orientation_pilot=args.temporal_orientation_pilot,
            )
            args.output.write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            print(f"Trend report: {args.output}")
            return 0 if report["status"] == "NO_TREND_DETECTED" else 1
        if args.command == "assess-experiment":
            report = assess_comparative_experiment(
                load_comparative_experiment(args.source),
                include_relative_support_pilot=args.relative_support_pilot,
            )
            args.output.write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            print(f"Comparative experiment report: {args.output}")
            return 0 if report["status"] == "ASSESSED" else 1
        if args.command == "validate-artifact":
            report = validate_artifact(load_artifact(args.source))
            content = json.dumps(report, indent=2, sort_keys=True) + "\n"
            if args.output:
                args.output.write_text(content, encoding="utf-8")
                print(f"Conformance report: {args.output}")
            else:
                print(content, end="")
            return 0 if report["status"] == "PASS" else 1
        if args.command == "compare":
            comparison = compare(
                load(args.first), load(args.second), args.criterion, args.tolerance
            )
            result = comparison_result(comparison)
            print(
                f"{result['status']}  equivalent under "
                f"{result['criterion']} criterion"
            )
            print(f"Maximum error: {result['maximum_error']:.3e}")
            if args.proof:
                args.proof.write_text(proof_json(result), encoding="utf-8")
                print(f"Proof-of-Path: {args.proof}")
            return 0 if comparison.equivalent else 1
        program = load(args.source)
        if args.command == "select":
            result = select_target(program, load_snapshot(args.snapshot))
            print(json.dumps({
                "status": result["status"],
                "selected": result["selected"],
                "score": result["score"],
                "captured_at": result["captured_at"],
            }, indent=2, sort_keys=True))
            if args.proof:
                args.proof.write_text(proof_json(result), encoding="utf-8")
                print(f"Proof-of-Path: {args.proof}", file=sys.stderr)
            return 0
        if args.command == "plan":
            result = plan_result(
                plan(program, args.topology, _native_gates(args.native_gates))
            )
            print(json.dumps({
                "status": result["status"],
                "source": result["source"],
                "compiled": result["compiled"],
                "overhead": result["overhead"],
            }, indent=2, sort_keys=True))
            if args.proof:
                args.proof.write_text(proof_json(result), encoding="utf-8")
                print(f"Proof-of-Path: {args.proof}", file=sys.stderr)
            return 0
        if args.command == "compile":
            compilation = compile_topology(
                program,
                topology_edges(program.qubits, args.topology),
                _native_gates(args.native_gates),
            )
            content = openqasm(compilation.program)
            if args.output:
                args.output.write_text(content, encoding="utf-8")
            else:
                print(content, end="")
            if args.proof:
                args.proof.write_text(
                    proof_json(compilation_result(compilation)), encoding="utf-8"
                )
                print(f"Proof-of-Path: {args.proof}", file=sys.stderr)
            return 0
        if args.command == "capabilities":
            print(json.dumps(backend_profile(program), indent=2, sort_keys=True))
            return 0
        if args.command == "export":
            if args.format == "openqasm":
                content = openqasm(program)
                result = None
            else:
                output = adapt(program, args.format)
                content = output.source
                result = adapter_result(output)
            if args.output:
                args.output.write_text(content, encoding="utf-8")
            else:
                print(content, end="")
            if args.proof:
                if result is None:
                    raise E7QError("adapter proof requires qiskit or cirq format")
                args.proof.write_text(proof_json(result), encoding="utf-8")
                print(f"Proof-of-Path: {args.proof}", file=sys.stderr)
            return 0
        result = verify(run(program))
        if args.proof:
            args.proof.write_text(proof_json(result), encoding="utf-8")
        if args.command == "run":
            print(json.dumps(result["counts"], sort_keys=True))
        else:
            for check in result["checks"]:
                print(f"{'PASS' if check['passed'] else 'FAIL'}  {check['name']}")
            print("\nProbabilities:")
            for outcome, probability in sorted(result["probabilities"].items()):
                print(f"{outcome}  {probability:.3f}")
            if args.proof:
                print(f"\nProof-of-Path: {args.proof}")
        return 0 if result["status"] == "PASS" else 1
    except (E7QError, QECError, OSError) as exc:
        print(f"e7q: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
