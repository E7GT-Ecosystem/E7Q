#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Generate the deterministic bounded DHSP affine-candidate corpus."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from e7q.ir.canonical import canonical_bytes, digest
from e7q.research.dhsp import REFERENCE_RULE, evaluate_affine_candidate


CANDIDATES = (
    {"id": "reference-k-plus-or-minus-l", **REFERENCE_RULE},
    {
        "id": "wrong-sum-for-both-outcomes",
        "outcome_0": {"k": 1, "l": 1},
        "outcome_1": {"k": 1, "l": 1},
    },
    {
        "id": "wrong-reversed-difference",
        "outcome_0": {"k": 1, "l": 1},
        "outcome_1": {"k": -1, "l": 1},
    },
)


def build(created_at: str) -> dict:
    assessments = [
        evaluate_affine_candidate(candidate, moduli=range(2, 17))
        for candidate in CANDIDATES
    ]
    report = {
        "schema": "e7q.research.dhsp-affine-corpus/v1",
        "created_at": created_at,
        "research_status": "experimental-bounded-counterexample-harness",
        "primary_sources": [
            "https://arxiv.org/abs/quant-ph/0302112",
            "https://arxiv.org/abs/quant-ph/0406151",
            "https://arxiv.org/abs/cs/0304005",
        ],
        "assessments": assessments,
        "summary": {
            "candidates": len(assessments),
            "pass": sum(a["outcome"]["status"] == "PASS" for a in assessments),
            "fail": sum(a["outcome"]["status"] == "FAIL" for a in assessments),
            "counterexamples": sum(
                a["outcome"]["counterexample"] is not None for a in assessments
            ),
        },
        "maximum_conclusion": (
            "bounded affine phase-label rules were exhaustively checked on the "
            "listed moduli"
        ),
        "nonclaims": [
            "new-dhsp-algorithm",
            "polynomial-time-complexity",
            "quantum-advantage",
            "hardware-feasibility",
        ],
    }
    report["report_id"] = digest(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--created-at", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.created_at)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_bytes(report) + b"\n")
    print(json.dumps({"report_id": report["report_id"], **report["summary"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
