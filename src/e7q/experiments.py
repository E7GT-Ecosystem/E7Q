# SPDX-License-Identifier: Apache-2.0
"""Bounded comparative-experiment evidence for quantum workflows."""
from __future__ import annotations

from collections import defaultdict
import hashlib
import itertools
import json
import math
from pathlib import Path
from typing import Any, Iterable

from .language import E7QError
from .support import conformance_checks as support_conformance_checks
from .support import from_declaration


INPUT_SCHEMA = "e7q.comparative-experiment/v1alpha1"
REPORT_SCHEMA = "e7q.comparative-experiment-report/v1alpha1"

CLAIM_LEVELS = (
    "MANIFEST_ASSESSABLE",
    "FEASIBILITY",
    "OBSERVED_DIFFERENCE",
    "REPEATABLE_EFFECT",
    "QUALITY_ADVANTAGE",
    "PRACTICAL_ADVANTAGE",
    "COMPUTATIONAL_QUANTUM_ADVANTAGE",
)

INDEPENDENCE_STATUSES = {
    "not-established",
    "reported-independent",
    "known-dependent",
}


def load_comparative_experiment(path: str | Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise E7QError(f"invalid comparative-experiment JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise E7QError("comparative experiment must be a JSON object")
    return value


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: object, *, allow_empty: bool = True) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(_nonempty(item) for item in value)
    )


def _number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _validate_manifest(
    value: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    if value.get("schema") != INPUT_SCHEMA:
        raise E7QError(f"comparative experiment must use schema {INPUT_SCHEMA}")
    for field in ("experiment_id", "title", "inquiry"):
        if not _nonempty(value.get(field)):
            raise E7QError(f"comparative experiment requires non-empty {field}")
    if not isinstance(value.get("predeclared"), bool):
        raise E7QError("comparative experiment requires boolean predeclared")

    factors = value.get("factors")
    if not isinstance(factors, list) or not 1 <= len(factors) <= 2:
        raise E7QError("comparative profile supports one or two declared factors")
    factor_ids: list[str] = []
    for index, factor in enumerate(factors):
        if not isinstance(factor, dict) or not _nonempty(factor.get("factor_id")):
            raise E7QError(f"factor {index} requires factor_id")
        levels = factor.get("levels")
        if (
            not isinstance(levels, list)
            or len(levels) != 2
            or not all(_nonempty(level) for level in levels)
            or len(set(levels)) != 2
        ):
            raise E7QError(f"factor {factor['factor_id']} requires two unique levels")
        factor_ids.append(factor["factor_id"])
    if len(factor_ids) != len(set(factor_ids)):
        raise E7QError("factor_id values must be unique")

    metrics = value.get("metrics")
    if not isinstance(metrics, list) or not metrics:
        raise E7QError("comparative experiment requires metrics")
    metric_ids: list[str] = []
    primary_count = 0
    for index, metric in enumerate(metrics):
        if not isinstance(metric, dict) or not _nonempty(metric.get("metric_id")):
            raise E7QError(f"metric {index} requires metric_id")
        if metric.get("direction") not in {"higher-is-better", "lower-is-better"}:
            raise E7QError(
                f"metric {metric['metric_id']} requires a supported direction"
            )
        if metric.get("role") not in {"primary", "secondary"}:
            raise E7QError(f"metric {metric['metric_id']} requires role")
        if metric.get("role") == "primary":
            primary_count += 1
        if not _number(metric.get("minimum_effect")) or float(
            metric["minimum_effect"]
        ) < 0:
            raise E7QError(
                f"metric {metric['metric_id']} requires non-negative minimum_effect"
            )
        if not _nonempty(metric.get("unit")):
            raise E7QError(f"metric {metric['metric_id']} requires unit")
        metric_ids.append(metric["metric_id"])
    if len(metric_ids) != len(set(metric_ids)):
        raise E7QError("metric_id values must be unique")
    if primary_count != 1:
        raise E7QError("comparative experiment requires exactly one primary metric")

    runs = value.get("runs")
    if not isinstance(runs, list) or len(runs) < 2:
        raise E7QError("comparative experiment requires at least two runs")
    run_ids: list[str] = []
    expected_factors = set(factor_ids)
    expected_metrics = set(metric_ids)
    level_map = {factor["factor_id"]: set(factor["levels"]) for factor in factors}
    for index, run in enumerate(runs):
        if not isinstance(run, dict) or not _nonempty(run.get("run_id")):
            raise E7QError(f"run {index} requires run_id")
        run_ids.append(run["run_id"])
        cell = run.get("cell")
        if not isinstance(cell, dict) or set(cell) != expected_factors:
            raise E7QError(f"run {run['run_id']} must declare every factor once")
        for factor_id, level in cell.items():
            if level not in level_map[factor_id]:
                raise E7QError(
                    f"run {run['run_id']} uses unknown level for {factor_id}"
                )
        measured = run.get("metrics")
        if not isinstance(measured, dict) or set(measured) != expected_metrics:
            raise E7QError(f"run {run['run_id']} must report every metric")
        if not all(_number(result) for result in measured.values()):
            raise E7QError(f"run {run['run_id']} has a non-finite metric")
        if not isinstance(run.get("resource_budget"), dict):
            raise E7QError(f"run {run['run_id']} requires resource_budget object")
        if run.get("independence_status") not in INDEPENDENCE_STATUSES:
            raise E7QError(f"run {run['run_id']} has invalid independence_status")
        if not _string_list(run.get("evidence_refs"), allow_empty=False):
            raise E7QError(f"run {run['run_id']} requires evidence_refs")
    if len(run_ids) != len(set(run_ids)):
        raise E7QError("run_id values must be unique")
    return factors, metrics, runs


def _cell_key(cell: dict[str, str], factor_ids: Iterable[str]) -> tuple[str, ...]:
    return tuple(cell[factor_id] for factor_id in factor_ids)


def _cell_id(factor_ids: list[str], key: tuple[str, ...]) -> str:
    return "|".join(f"{factor_id}={level}" for factor_id, level in zip(factor_ids, key))


def _aggregate(
    factors: list[dict[str, Any]],
    metrics: list[dict[str, Any]],
    runs: list[dict[str, Any]],
) -> tuple[list[dict[str, object]], dict[tuple[str, ...], dict[str, float]]]:
    factor_ids = [factor["factor_id"] for factor in factors]
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        grouped[_cell_key(run["cell"], factor_ids)].append(run)

    cells: list[dict[str, object]] = []
    means: dict[tuple[str, ...], dict[str, float]] = {}
    for key in sorted(grouped):
        cell_runs = grouped[key]
        summaries: dict[str, dict[str, float | int]] = {}
        cell_means: dict[str, float] = {}
        for metric in metrics:
            metric_id = metric["metric_id"]
            values = [float(run["metrics"][metric_id]) for run in cell_runs]
            mean = math.fsum(values) / len(values)
            cell_means[metric_id] = mean
            summaries[metric_id] = {
                "n": len(values),
                "mean": mean,
                "minimum": min(values),
                "maximum": max(values),
            }
        means[key] = cell_means
        cells.append(
            {
                "cell_id": _cell_id(factor_ids, key),
                "levels": dict(zip(factor_ids, key)),
                "run_ids": sorted(run["run_id"] for run in cell_runs),
                "summaries": summaries,
            }
        )
    return cells, means


def _comparisons(
    factors: list[dict[str, Any]],
    metrics: list[dict[str, Any]],
    means: dict[tuple[str, ...], dict[str, float]],
) -> list[dict[str, object]]:
    factor_ids = [factor["factor_id"] for factor in factors]
    results: list[dict[str, object]] = []
    for factor_index, factor in enumerate(factors):
        other_indices = [index for index in range(len(factors)) if index != factor_index]
        contexts = sorted({tuple(key[index] for index in other_indices) for key in means})
        baseline_level, candidate_level = factor["levels"]
        for context in contexts:
            baseline_key: list[str] = []
            candidate_key: list[str] = []
            context_index = 0
            context_value: dict[str, str] = {}
            for index, factor_id in enumerate(factor_ids):
                if index == factor_index:
                    baseline_key.append(baseline_level)
                    candidate_key.append(candidate_level)
                else:
                    level = context[context_index]
                    context_index += 1
                    baseline_key.append(level)
                    candidate_key.append(level)
                    context_value[factor_id] = level
            baseline_tuple = tuple(baseline_key)
            candidate_tuple = tuple(candidate_key)
            if baseline_tuple not in means or candidate_tuple not in means:
                continue
            metric_results: list[dict[str, object]] = []
            for metric in metrics:
                metric_id = metric["metric_id"]
                baseline_mean = means[baseline_tuple][metric_id]
                candidate_mean = means[candidate_tuple][metric_id]
                raw_delta = candidate_mean - baseline_mean
                adjusted = (
                    raw_delta
                    if metric["direction"] == "higher-is-better"
                    else -raw_delta
                )
                minimum_effect = float(metric["minimum_effect"])
                if adjusted > minimum_effect:
                    effect_status = "improved"
                elif adjusted < -minimum_effect:
                    effect_status = "worsened"
                else:
                    effect_status = "no-material-difference"
                metric_results.append(
                    {
                        "metric_id": metric_id,
                        "role": metric["role"],
                        "direction": metric["direction"],
                        "unit": metric["unit"],
                        "baseline_mean": baseline_mean,
                        "candidate_mean": candidate_mean,
                        "raw_delta": raw_delta,
                        "direction_adjusted_delta": adjusted,
                        "minimum_effect": minimum_effect,
                        "effect_status": effect_status,
                    }
                )
            results.append(
                {
                    "comparison_id": (
                        f"{factor['factor_id']}:{baseline_level}-to-{candidate_level}:"
                        + (json.dumps(context_value, sort_keys=True) if context_value else "all")
                    ),
                    "factor_id": factor["factor_id"],
                    "baseline_level": baseline_level,
                    "candidate_level": candidate_level,
                    "context": context_value,
                    "baseline_cell_id": _cell_id(factor_ids, baseline_tuple),
                    "candidate_cell_id": _cell_id(factor_ids, candidate_tuple),
                    "metrics": metric_results,
                    "tradeoff": {
                        "improved": [
                            item["metric_id"]
                            for item in metric_results
                            if item["effect_status"] == "improved"
                        ],
                        "worsened": [
                            item["metric_id"]
                            for item in metric_results
                            if item["effect_status"] == "worsened"
                        ],
                        "no_material_difference": [
                            item["metric_id"]
                            for item in metric_results
                            if item["effect_status"] == "no-material-difference"
                        ],
                        "aggregate_verdict": "not-computed",
                    },
                }
            )
    return results


def _interactions(
    factors: list[dict[str, Any]],
    metrics: list[dict[str, Any]],
    means: dict[tuple[str, ...], dict[str, float]],
) -> list[dict[str, object]]:
    if len(factors) != 2:
        return []
    first, second = factors
    first_base, first_candidate = first["levels"]
    second_base, second_candidate = second["levels"]
    required = {
        (first_base, second_base),
        (first_candidate, second_base),
        (first_base, second_candidate),
        (first_candidate, second_candidate),
    }
    if not required.issubset(means):
        return []
    results: list[dict[str, object]] = []
    for metric in metrics:
        metric_id = metric["metric_id"]
        effect_at_second_base = (
            means[(first_candidate, second_base)][metric_id]
            - means[(first_base, second_base)][metric_id]
        )
        effect_at_second_candidate = (
            means[(first_candidate, second_candidate)][metric_id]
            - means[(first_base, second_candidate)][metric_id]
        )
        results.append(
            {
                "metric_id": metric_id,
                "first_factor": first["factor_id"],
                "second_factor": second["factor_id"],
                "first_factor_effect_at_second_baseline": effect_at_second_base,
                "first_factor_effect_at_second_candidate": effect_at_second_candidate,
                "difference_of_differences": (
                    effect_at_second_candidate - effect_at_second_base
                ),
                "interpretation_boundary": (
                    "Descriptive interaction contrast only; no sampling-variation, "
                    "causal, or significance claim is established."
                ),
            }
        )
    return results


def assess_comparative_experiment(
    value: dict[str, Any], *, include_relative_support_pilot: bool = False
) -> dict[str, object]:
    """Assess a bounded one- or two-factor supplied experiment manifest."""
    factors, metrics, runs = _validate_manifest(value)
    cells, means = _aggregate(factors, metrics, runs)
    comparisons = _comparisons(factors, metrics, means)
    interactions = _interactions(factors, metrics, means)
    factor_ids = [factor["factor_id"] for factor in factors]
    expected_cells = set(itertools.product(*(factor["levels"] for factor in factors)))
    observed_cells = set(means)
    missing_cells = sorted(expected_cells - observed_cells)

    budgets = [
        json.dumps(run["resource_budget"], sort_keys=True, separators=(",", ":"))
        for run in runs
    ]
    budgets_identical = len(set(budgets)) == 1
    replicated = all(len(cell["run_ids"]) >= 2 for cell in cells)
    independence_reported = all(
        run["independence_status"] == "reported-independent" for run in runs
    )

    material_differences = [
        result
        for comparison in comparisons
        for result in comparison["metrics"]
        if result["effect_status"] != "no-material-difference"
    ]
    highest_supported = (
        "OBSERVED_DIFFERENCE"
        if material_differences
        else "MANIFEST_ASSESSABLE"
    )
    ladder = [
        {
            "level": "MANIFEST_ASSESSABLE",
            "status": "SUPPORTED",
            "basis": "The supplied manifest passed bounded structural validation.",
        },
        {
            "level": "FEASIBILITY",
            "status": "NOT_ESTABLISHED",
            "basis": (
                "Supplied run records and evidence references are not, by themselves, "
                "verified evidence that the declared workflow executed successfully."
            ),
        },
        {
            "level": "OBSERVED_DIFFERENCE",
            "status": "SUPPORTED" if material_differences else "NOT_TRIGGERED",
            "basis": (
                "At least one descriptive cell-mean difference exceeds its declared minimum effect."
                if material_differences
                else "No descriptive cell-mean difference exceeds its declared minimum effect."
            ),
        },
        {
            "level": "REPEATABLE_EFFECT",
            "status": "NOT_ESTABLISHED",
            "basis": (
                "Replicates and reported independence are recorded, but this bounded profile "
                "does not perform an inferential replication test."
                if replicated and independence_reported
                else "Independent replicated evidence is incomplete or not established."
            ),
        },
        {
            "level": "QUALITY_ADVANTAGE",
            "status": "NOT_ESTABLISHED",
            "basis": "Domain relevance, replication, and endpoint sufficiency require separate evidence.",
        },
        {
            "level": "PRACTICAL_ADVANTAGE",
            "status": "NOT_ESTABLISHED",
            "basis": "Matched time, cost, energy, and operational constraints are not adjudicated by descriptive effects.",
        },
        {
            "level": "COMPUTATIONAL_QUANTUM_ADVANTAGE",
            "status": "NOT_ESTABLISHED",
            "basis": "Classical-baseline adequacy and a declared computational resource boundary require stronger methods.",
        },
    ]

    warnings: list[str] = []
    if missing_cells:
        warnings.append("factorial matrix is incomplete")
    if not replicated:
        warnings.append("one or more cells have fewer than two supplied runs")
    if not independence_reported:
        warnings.append("run independence is not uniformly reported")
    if not budgets_identical:
        warnings.append("resource budgets are not declared identical across runs")
    if not value["predeclared"]:
        warnings.append("profile is retrospective rather than predeclared")
    warnings.append("effects and interactions are descriptive; no significance test is performed")

    canonical = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    manifest_digest = "sha256:" + hashlib.sha256(canonical).hexdigest()
    status = "ASSESSED" if comparisons else "INCOMPLETE"
    report: dict[str, object] = {
        "schema": REPORT_SCHEMA,
        "status": status,
        "experiment_id": value["experiment_id"],
        "title": value["title"],
        "inquiry": value["inquiry"],
        "manifest_digest": manifest_digest,
        "predeclared": value["predeclared"],
        "factors": factors,
        "metrics": metrics,
        "runs": len(runs),
        "cells": cells,
        "matrix": {
            "expected_cells": len(expected_cells),
            "observed_cells": len(observed_cells),
            "missing_cells": [
                dict(zip(factor_ids, key)) for key in missing_cells
            ],
        },
        "resource_budget_comparability": (
            "declared-identical" if budgets_identical else "not-established"
        ),
        "replication_posture": (
            "reported-independent-replicates"
            if replicated and independence_reported
            else "not-established"
        ),
        "comparisons": comparisons,
        "interactions": interactions,
        "claim_assessment": {
            "highest_supported_level": highest_supported,
            "ladder": ladder,
            "decision_rule": "not-supplied; metric trade-offs are not collapsed",
        },
        "warnings": warnings,
        "proof": [
            {
                "step": 0,
                "kind": "manifest-validation",
                "manifest_digest": manifest_digest,
                "factors": len(factors),
                "metrics": len(metrics),
                "runs": len(runs),
            },
            {
                "step": 1,
                "kind": "cell-aggregation",
                "expected_cells": len(expected_cells),
                "observed_cells": len(observed_cells),
            },
            {
                "step": 2,
                "kind": "descriptive-comparison",
                "comparisons": len(comparisons),
                "interaction_contrasts": len(interactions),
            },
            {
                "step": 3,
                "kind": "claim-boundary",
                "highest_supported_level": highest_supported,
                "blocked_levels": [
                    entry["level"]
                    for entry in ladder
                    if entry["status"] == "NOT_ESTABLISHED"
                ],
            },
            {
                "step": 4,
                "kind": "evidence-boundary",
                "boundary": (
                    "Offline descriptive assessment of user-supplied values only; not "
                    "provider authentication, run-independence proof, causal attribution, "
                    "domain validation, practical advantage, or computational quantum advantage."
                ),
            },
        ],
    }

    if include_relative_support_pilot:
        declaration = value.get("relative_support")
        if not isinstance(declaration, dict):
            raise E7QError(
                "--relative-support-pilot requires relative_support declaration"
            )
        pilot = from_declaration(
            declaration, pilot_id=f"comparative-experiment:{value['experiment_id']}"
        )
        failed = [
            check["name"]
            for check in support_conformance_checks(pilot)
            if not check["passed"]
        ]
        if failed:
            raise E7QError(
                "relative_support declaration is nonconformant: " + ", ".join(failed)
            )
        report["relative_support_pilot"] = pilot
    return report
