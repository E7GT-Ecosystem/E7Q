# SPDX-License-Identifier: Apache-2.0
"""Explicit, fail-closed integration gates for the unchanged historical QEC pilot.

No pilot main is invoked: those mains overwrite historical result files.
Profile execution is opt-in and does not migrate E7Q's architecture pin.
"""
import argparse
import hashlib
import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "pilots/qec_0_1"
COMPANION_COMMIT = "4d6e02f16363f2333961cf4350d584c92d51bbc6"
SUITES = {"pilot": ("test_adapter", 9), "profiles": ("test_profiles", 3)}


def require_module(name, version=None):
    try:
        module = importlib.import_module(name)
        distribution = importlib.metadata.distribution(name)
        installed = distribution.version
    except (ImportError, importlib.metadata.PackageNotFoundError) as error:
        raise ValueError(f"required dependency {name!r} is unavailable: {error}") from error
    if version is not None and installed != version:
        raise ValueError(f"{name} {version} required; found {installed}")
    # Editable E7Q has a separate exact-checkout origin check below.
    if name != "e7q":
        owned_files = {Path(distribution.locate_file(file)).resolve()
                       for file in distribution.files or ()}
        if Path(module.__file__).resolve() not in owned_files:
            raise ValueError(f"required dependency {name!r} has an unexpected module origin")
        if getattr(module, "__version__", None) != installed:
            raise ValueError(f"required dependency {name!r} module/metadata version mismatch")
    print(f"DEPENDENCY {name} {installed} {module.__file__}", flush=True)
    return module


def verify_files(root, entries):
    for relative, expected in entries.items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError(f"manifest path escapes source root: {relative}")
        if not path.is_file():
            raise ValueError(f"required source is missing: {path}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"source digest mismatch: {path}")
    print(f"SOURCE_DIGESTS {root} {len(entries)} verified", flush=True)


def require_companion(path, manifest):
    if path is None:
        raise ValueError("profiles requires --companion PATH at the declared Git pin")
    path = path.resolve()
    if not path.is_dir():
        raise ValueError(f"required companion checkout is missing: {path}")
    def git(*arguments):
        result = subprocess.run(["git", "-C", str(path), *arguments],
                                capture_output=True, text=True, check=False)
        if result.returncode:
            raise ValueError(f"required companion is not a readable Git checkout: {path}")
        return result.stdout.strip()
    if Path(git("rev-parse", "--show-toplevel")).resolve() != path:
        raise ValueError("--companion must name the companion Git root")
    head = git("rev-parse", "HEAD")
    if head != COMPANION_COMMIT or manifest["e7gt_commit"] != COMPANION_COMMIT:
        raise ValueError(f"companion pin mismatch: required {COMPANION_COMMIT}; found {head}")
    verify_files(path, manifest["kernel_files"])
    os.environ["E7GT_CHECKOUT"] = str(path)
    print(f"COMPANION {head} {path}", flush=True)


def check_result(result, expected):
    if (result.testsRun != expected or not result.wasSuccessful()
            or result.skipped or result.expectedFailures or result.unexpectedSuccesses):
        raise ValueError("required QEC suite did not fully pass: "
                         f"executed={result.testsRun}, expected={expected}, "
                         f"failures={len(result.failures)}, errors={len(result.errors)}, "
                         f"skipped={len(result.skipped)}, "
                         f"expected_failures={len(result.expectedFailures)}, "
                         f"unexpected_successes={len(result.unexpectedSuccesses)}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lane", choices=SUITES)
    parser.add_argument("--companion", type=Path,
                        help="required only for profiles: exact pinned E7G-T Git checkout")
    args = parser.parse_args(argv)
    sys.dont_write_bytecode = True
    try:
        require_module("numpy")
        e7q = require_module("e7q")
        if Path(e7q.__file__).resolve() != ROOT / "src/e7q/__init__.py":
            raise ValueError("E7Q must be installed from this checkout (use pip install -e .)")
        manifest = json.loads((PILOT / "SOURCE_MANIFEST.json").read_text())
        verify_files(PILOT, manifest["pilot_sources"])
        if args.lane == "pilot":
            require_module("stim", "1.16.0")
        else:
            require_companion(args.companion, manifest)
        name, expected = SUITES[args.lane]
        suite = unittest.TestLoader().discover(str(PILOT), pattern=f"{name}.py")
        if suite.countTestCases() != expected:
            raise ValueError(f"partial/empty discovery: required {expected} tests; "
                             f"found {suite.countTestCases()}")
        for module_name in (name, "adapter") + (("profiles",) if args.lane == "profiles" else ("conventional",)):
            module = sys.modules.get(module_name)
            if module is None or Path(module.__file__).resolve() != PILOT / f"{module_name}.py":
                raise ValueError(f"unexpected historical module origin: {module_name}")
            print(f"MODULE {module_name} {module.__file__}", flush=True)
        result = unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(suite)
        check_result(result, expected)
        if args.lane == "profiles":
            for module_name, relative in (
                    ("test_msc", "proposals/msc-0.1/e7gt_msc_v0_1.py"),
                    ("test_rec", "packages/rec-0.1/e7gt_rec_v0_1.py"),
                    ("test_replay", "packages/rec-0.1/check_trace.py")):
                module = sys.modules.get(module_name)
                if module is None or Path(module.__file__).resolve() != args.companion.resolve() / relative:
                    raise ValueError(f"unexpected companion module origin: {module_name}")
                print(f"MODULE {module_name} {module.__file__}", flush=True)
    except (ValueError, OSError, ImportError, KeyError, TypeError) as error:
        print(f"QEC INTEGRATION ERROR: {error}", file=sys.stderr)
        return 1
    print(f"QEC INTEGRATION PASS: {args.lane}; {expected} executed; zero skips", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
