# SPDX-License-Identifier: Apache-2.0
"""Check declared publication/licensing boundaries, not legal ownership."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import tomllib


REGISTER = "docs/licensing/component-register.json"
BASELINE = "docs/licensing/published-baseline-20261014.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_path(value: object) -> bool:
    return (isinstance(value, str) and bool(value) and "\\" not in value
            and not PurePosixPath(value).is_absolute()
            and all(part not in {"", ".", ".."} for part in value.split("/")))


def review_records(records: object, errors: list[str], *, commercial: bool) -> dict:
    if not isinstance(records, list):
        errors.append("Review records must be lists")
        return {}
    result = {}
    for item in records:
        if not isinstance(item, dict) or not safe_path(item.get("path")):
            errors.append("Review record has invalid path/shape")
            continue
        path = item["path"]
        if path in result:
            errors.append(f"Duplicate review record: {path}")
        for field in ("rights_basis" if commercial else "reason", "approval_reference"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                errors.append(f"Missing {field}: {path}")
        expected = item.get("sha256")
        if not (expected is None and not commercial):
            if (not isinstance(expected, str) or len(expected) != 64
                    or any(c not in "0123456789abcdef" for c in expected)):
                errors.append(f"Invalid SHA-256: {path}")
        if not commercial and item.get("decision") != "retain_public_terms":
            errors.append(f"Open-core decision must explicitly retain public terms: {path}")
        if commercial and item.get("rights_status") != "cleared":
            errors.append(f"Commercial rights not recorded as cleared: {path}")
        result[path] = item
    return result


def check(root: Path, paths: list[str] | None = None) -> list[str]:
    errors: list[str] = []
    policy = json.loads((root / REGISTER).read_text())
    baseline = json.loads((root / BASELINE).read_text())
    if policy.get("schema") != "e7q.component-licensing/1":
        errors.append("Unknown component-register schema")
    if baseline.get("schema") != "e7q.licensing-baseline/1":
        errors.append("Unknown published-baseline schema")
    if policy.get("baseline_commit") != baseline.get("baseline_commit"):
        errors.append("Baseline identities differ")
    if policy.get("commercial_prefix") != "commercial/e7q_ir/":
        errors.append("Unexpected commercial boundary")
    if policy.get("commercial_license") != "PolyForm-Noncommercial-1.0.0":
        errors.append("Unexpected commercial licence")
    if policy.get("protected_open_prefixes") != ["src/e7q/ir/", "schemas/e7q-ir-"]:
        errors.append("Protected IR boundary changed without checker edition")
    originals = {entry["path"]: entry["sha256"] for entry in baseline["files"]}
    if len(originals) != len(baseline["files"]):
        errors.append("Duplicate published baseline path")
    if any(not safe_path(p) for p in originals):
        errors.append("Invalid published baseline path")
    for path in ("LICENSE", "LICENSE-DOCS"):
        if (policy["preserved_license_sha256"].get(path) != originals.get(path)
                or not (root / path).is_file() or digest(root / path) != originals.get(path)):
            errors.append(f"Published licence document changed: {path}")
    licence = root / "commercial/e7q_ir/LICENSE"
    if not licence.is_file() or digest(licence) != policy.get("license_text_sha256"):
        errors.append("Standard PolyForm licence text missing or changed")

    approved = review_records(policy.get("open_core_decisions"), errors, commercial=False)
    components = review_records(policy.get("commercial_components"), errors, commercial=True)
    if paths is None:
        raw = subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=root)
        paths = raw.decode().rstrip("\0").split("\0") if raw else []
    files = set(paths)
    if any(not safe_path(p) for p in files):
        errors.append("Invalid working-tree path")
        return errors

    prefixes = policy["protected_open_prefixes"]
    protected = {p for p in originals if any(p.startswith(prefix) for prefix in prefixes)}
    protected |= {p for p in files if any(p.startswith(prefix) for prefix in prefixes)}
    for path in sorted(protected):
        file = root / path
        actual = digest(file) if path in files and file.is_file() and not file.is_symlink() else None
        if actual == originals.get(path) and actual is not None:
            continue
        decision = approved.get(path)
        if decision is None or decision.get("sha256") != actual:
            errors.append(f"IR publication needs hash-bound retain_public_terms decision: {path}")
        if actual is not None and path.endswith(".py"):
            header = file.read_text()[:2048]
            if "SPDX-License-Identifier: Apache-2.0" not in header:
                errors.append(f"Reviewed open-core change needs Apache designation: {path}")
            if "SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0" in header:
                errors.append(f"Commercial designation in Apache package: {path}")
    for path, record in approved.items():
        if path not in protected:
            errors.append(f"Open-core decision outside protected boundary: {path}")

    commercial_prefix = policy["commercial_prefix"]
    exempt = {commercial_prefix + p for p in ("README.md", "LICENSE", "NOTICE")}
    for path in sorted(files):
        file = root / path
        if not path.startswith(commercial_prefix) or path in exempt:
            continue
        if file.is_symlink() or not file.is_file():
            errors.append(f"Commercial component must be a regular file: {path}")
            continue
        record = components.get(path)
        if record is None or record.get("sha256") != digest(file):
            errors.append(f"Unregistered/stale commercial component: {path}")
        try:
            text = file.read_text()
        except UnicodeError:
            errors.append(f"Commercial component needs separately designed binary notice rules: {path}")
            continue
        if "SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0" not in text[:2048]:
            errors.append(f"Missing PolyForm designation: {path}")
        if "Required Notice: Copyright 2026 Oleksandr Razinkov" not in text[:2048]:
            errors.append(f"Missing commercial required notice: {path}")
        if "SPDX-License-Identifier: Apache-2.0" in text[:2048]:
            errors.append(f"Mixed software designation requires separate rights review: {path}")
    for path in components:
        if not path.startswith(commercial_prefix) or path in exempt or path not in files:
            errors.append(f"Commercial record has no designated file: {path}")

    project = tomllib.loads((root / "pyproject.toml").read_text())
    tool = project.get("tool", {}).get("setuptools", {})
    finder = tool.get("packages", {}).get("find", {}) if isinstance(tool.get("packages"), dict) else {}
    if finder != {"where": ["src"], "include": ["e7q", "e7q.*"], "namespaces": False}:
        errors.append("Apache package discovery must be limited to src/e7q")
    if "package-dir" in tool or "py-modules" in tool:
        errors.append("Extra package/module mapping needs separate distribution review")
    if project["project"].get("license") != {"text": "Apache-2.0"}:
        errors.append("Current Apache package metadata changed")
    manifest = (root / "MANIFEST.in").read_text().splitlines()
    commands = [line.strip() for line in manifest if line.strip() and not line.lstrip().startswith("#")]
    if commands != ["prune commercial"]:
        errors.append("Source archive must explicitly exclude commercial components")
    for path in sorted(p for p in files if p.startswith("src/") and p.endswith(".py")):
        file = root / path
        if file.is_symlink():
            errors.append(f"Package source must not be a symlink: {path}")
            continue
        tree = ast.parse(file.read_text(), filename=path)
        for node in ast.walk(tree):
            names = ([item.name for item in node.names] if isinstance(node, ast.Import)
                     else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
            if any(name == "commercial" or name.startswith("commercial.")
                   or name == "e7q_ir_commercial" or name.startswith("e7q_ir_commercial.") for name in names):
                errors.append(f"Apache package imports a separate commercial component: {path}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        errors = check(args.root.resolve())
    except (OSError, ValueError, KeyError, TypeError, SyntaxError, subprocess.CalledProcessError) as exc:
        print(f"Licensing boundary ERROR: {exc}")
        return 2
    for message in errors:
        print(f"Licensing boundary FAIL: {message}")
    if errors:
        return 1
    print("Licensing boundary PASS (declared scope only; not rights certification)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
