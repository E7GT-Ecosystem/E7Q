# SPDX-License-Identifier: Apache-2.0
"""Standard-library negative controls for the optional Cirq CI gate."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from check_cirq_ci import ROOT, SDK_TESTS, check_report


def report():
    root = ET.Element("testsuites")
    suite = ET.SubElement(root, "testsuite", tests="83", errors="0",
                          failures="0", skipped="0")
    names = sorted(SDK_TESTS) + [f"test_probe_{i}" for i in range(80)]
    for name in names:
        ET.SubElement(suite, "testcase", classname="tests.test_cirq_interop",
                      name=name, time="0.01")
    return root


class ReportGateTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "focused.xml"

    def save(self, root):
        ET.ElementTree(root).write(self.path, encoding="utf-8")

    def test_complete_report_passes(self):
        self.save(report())
        self.assertEqual(check_report(self.path)["executed"], 83)

    def test_skipped_xfail_failure_and_error_tags_reject_even_with_zero_counters(self):
        for tag in ("skipped", "failure", "error"):
            with self.subTest(tag=tag):
                root = report()
                ET.SubElement(root[0][0], tag)
                self.save(root)
                with self.assertRaises(ValueError):
                    check_report(self.path)

    def test_nonzero_counters_reject_even_without_outcome_tags(self):
        for field in ("skipped", "failures", "errors"):
            with self.subTest(field=field):
                root = report()
                root[0].set(field, "1")
                self.save(root)
                with self.assertRaises(ValueError):
                    check_report(self.path)

    def test_missing_sdk_case_rejects_otherwise_green_counts(self):
        root = report()
        root[0][0].set("name", "test_not_the_required_sdk_case")
        self.save(root)
        with self.assertRaisesRegex(ValueError, "SDK-backed"):
            check_report(self.path)

    def test_partial_corpus_and_wrong_count_reject(self):
        root = report()
        root[0].remove(root[0][-1])
        self.save(root)
        with self.assertRaisesRegex(ValueError, "count"):
            check_report(self.path)
        root[0].set("tests", "82")
        self.save(root)
        with self.assertRaisesRegex(ValueError, "partially"):
            check_report(self.path)

    def test_foreign_duplicate_and_missing_names_reject(self):
        for attribute, value in (("classname", "tests.other"),
                                 ("name", ""),
                                 ("name", "test_probe_0")):
            with self.subTest(attribute=attribute, value=value):
                root = report()
                root[0][0].set(attribute, value)
                self.save(root)
                with self.assertRaises(ValueError):
                    check_report(self.path)

    def test_empty_missing_and_malformed_reports_reject(self):
        for root in (ET.Element("testsuites"), ET.Element("testcase")):
            self.save(root)
            with self.assertRaises(ValueError):
                check_report(self.path)
        self.path.write_text("<broken")
        with self.assertRaises(ET.ParseError):
            check_report(self.path)
        self.path.unlink()
        with self.assertRaises(OSError):
            check_report(self.path)

    def test_invalid_or_missing_counts_reject(self):
        for value in ("not-an-integer", None):
            root = report()
            if value is None:
                del root[0].attrib["tests"]
            else:
                root[0].set("tests", value)
            self.save(root)
            with self.assertRaises((ValueError, KeyError)):
                check_report(self.path)

    def test_cli_zero_and_nonzero_exit_status(self):
        self.save(report())
        command = [sys.executable, "-B", str(ROOT / "scripts/check_cirq_ci.py"),
                   "report", str(self.path)]
        good = subprocess.run(command, capture_output=True, text=True, timeout=15)
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertEqual(json.loads(good.stdout)["executed"], 83)
        root = report()
        ET.SubElement(root[0][0], "skipped", message="optional SDK missing")
        self.save(root)
        bad = subprocess.run(command, capture_output=True, text=True, timeout=15)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("did not pass", bad.stderr)

    def test_workflow_retains_core_jobs_and_enables_the_dedicated_gate(self):
        workflow = (ROOT / ".github/workflows/ci.yml").read_text()
        core, cirq = workflow.split("\n  cirq-reference:\n")
        self.assertIn('python -m pip install -e ".[test]"', core)
        self.assertIn('python -m pip install -e ".[test,simulation-test]"', core)
        self.assertNotIn("test,cirq", core)
        for fragment in ('python-version: "3.12"', 'timeout-minutes: 15',
                         '-r docs/e7q-ir/cirq/requirements-tested.txt',
                         '-c docs/e7q-ir/cirq/requirements-tested.txt',
                         '-e ".[test,cirq]"', 'python -m pip check',
                         'scripts/test_cirq_ci.py', 'scripts/check_licensing_boundary.py',
                         'tests/test_cirq_interop.py --junitxml=',
                         'scripts/check_cirq_ci.py report', 'scripts/check_cirq_ci.py bell'):
            self.assertIn(fragment, cirq)
        self.assertNotIn("continue-on-error", cirq)
        self.assertNotIn("|| true", cirq)


if __name__ == "__main__":
    unittest.main()
