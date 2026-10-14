# SPDX-License-Identifier: Apache-2.0
"""Negative controls for licensing/publication checks; no legal verdicts."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from check_licensing_boundary import BASELINE, REGISTER, check


class BoundaryControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        repo = Path(__file__).resolve().parents[1]
        paths = [REGISTER, BASELINE, "LICENSE", "LICENSE-DOCS", "pyproject.toml", "MANIFEST.in",
                 "commercial/e7q_ir/LICENSE", "commercial/e7q_ir/NOTICE", "commercial/e7q_ir/README.md"]
        baseline = json.loads((repo / BASELINE).read_text())
        paths += [e["path"] for e in baseline["files"]
                  if e["path"].startswith(("src/e7q/ir/", "schemas/e7q-ir-"))]
        for path in paths:
            dest = self.root / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(repo / path, dest)
        self.paths = paths

    def write(self, path, text):
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text)
        if path not in self.paths:
            self.paths.append(path)
        return hashlib.sha256(file.read_bytes()).hexdigest()

    def update(self, field, record):
        policy = json.loads((self.root / REGISTER).read_text())
        policy[field].append(record)
        (self.root / REGISTER).write_text(json.dumps(policy))

    def test_existing_published_ir_remains_allowed(self):
        self.assertEqual(check(self.root, self.paths), [])

    def test_new_ir_code_needs_explicit_publication_decision(self):
        self.write("src/e7q/ir/future.py", "# SPDX-License-Identifier: Apache-2.0\nx = 1\n")
        self.assertTrue(any("retain_public_terms" in e for e in check(self.root, self.paths)))

    def test_review_hash_cannot_cover_changed_content(self):
        path = "src/e7q/ir/future.py"
        sha = self.write(path, "# SPDX-License-Identifier: Apache-2.0\nx = 1\n")
        self.update("open_core_decisions", {"path": path, "sha256": sha, "decision": "retain_public_terms",
                                           "reason": "Explicit synthetic open-core choice", "approval_reference": "synthetic-review"})
        self.assertEqual(check(self.root, self.paths), [])
        self.write(path, "# SPDX-License-Identifier: Apache-2.0\nx = 2\n")
        self.assertTrue(any("retain_public_terms" in e for e in check(self.root, self.paths)))

    def test_modified_and_deleted_published_ir_are_reviewed(self):
        path = "src/e7q/ir/canonical.py"
        with (self.root / path).open("a") as file:
            file.write("\n# new implementation\n")
        self.assertTrue(any("retain_public_terms" in e for e in check(self.root, self.paths)))
        (self.root / path).unlink()
        self.paths.remove(path)
        self.assertTrue(any(path in e for e in check(self.root, self.paths)))

    def test_unregistered_commercial_code_is_blocked(self):
        self.write("commercial/e7q_ir/future.py", "x = 1\n")
        errors = check(self.root, self.paths)
        self.assertTrue(any("Unregistered" in e for e in errors))
        self.assertTrue(any("Missing PolyForm" in e for e in errors))

    def test_registered_component_still_needs_cleared_rights(self):
        path = "commercial/e7q_ir/future.py"
        text = "# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0\n# Required Notice: Copyright 2026 Oleksandr Razinkov\nx = 1\n"
        sha = self.write(path, text)
        record = {"path": path, "sha256": sha, "rights_status": "pending",
                  "rights_basis": "synthetic evidence only", "approval_reference": "synthetic-review"}
        self.update("commercial_components", record)
        self.assertTrue(any("not recorded as cleared" in e for e in check(self.root, self.paths)))
        policy = json.loads((self.root / REGISTER).read_text())
        policy["commercial_components"][0]["rights_status"] = "cleared"
        (self.root / REGISTER).write_text(json.dumps(policy))
        self.assertEqual(check(self.root, self.paths), [])

    def test_public_licence_and_standard_terms_cannot_silently_change(self):
        self.write("LICENSE", "All rights reserved\n")
        self.write("commercial/e7q_ir/LICENSE", "Modified standard terms\n")
        errors = check(self.root, self.paths)
        self.assertTrue(any("Published licence" in e for e in errors))
        self.assertTrue(any("PolyForm licence text" in e for e in errors))

    def test_packaging_and_import_leaks_are_rejected(self):
        self.write("MANIFEST.in", "graft commercial\n")
        self.write("src/leak.py", "import commercial.e7q_ir.future\n")
        errors = check(self.root, self.paths)
        self.assertTrue(any("Source archive" in e for e in errors))
        self.assertTrue(any("imports a separate commercial" in e for e in errors))
        project = (self.root / "pyproject.toml").read_text().replace('where = ["src"]', 'where = ["src", "commercial"]')
        self.write("pyproject.toml", project)
        self.assertTrue(any("package discovery" in e for e in check(self.root, self.paths)))

    def test_approval_does_not_relicense_open_package(self):
        path = "src/e7q/ir/future.py"
        sha = self.write(path, "# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0\nx = 1\n")
        self.update("open_core_decisions", {"path": path, "sha256": sha, "decision": "retain_public_terms",
                                           "reason": "synthetic invalid licence choice", "approval_reference": "synthetic-review"})
        self.assertTrue(any("Commercial designation" in e for e in check(self.root, self.paths)))

    def test_invalid_review_paths_fail_closed(self):
        self.update("commercial_components", {"path": "../outside.py"})
        self.assertTrue(any("invalid path" in e for e in check(self.root, self.paths)))


if __name__ == "__main__":
    unittest.main()
