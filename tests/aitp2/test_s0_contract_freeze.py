#!/usr/bin/env python3
"""Tests for S0 freeze validator — decisions-only mode.

Stdlib unittest only. Each test copies valid decisions JSON into a
TemporaryDirectory, mutates it, runs the validator as a real subprocess,
and asserts exit codes and JSON/error codes.
"""

import ast
import copy
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_VALIDATOR = _REPO_ROOT / "tests" / "aitp2" / "check_s0_freeze.py"
_DECISIONS_FIXTURE = _REPO_ROOT / "tests" / "fixtures" / "aitp2" / "S0_DECISIONS.json"

# stdlib allowlist for import check (validator file only, not this test file)
_STDLIB_ALLOWLIST = frozenset({
    "argparse", "json", "re", "subprocess", "sys", "pathlib",
    "ast", "copy", "tempfile", "unittest", "typing", "dataclasses",
    "textwrap", "io", "contextlib", "functools",
    "itertools", "collections", "enum", "math", "hashlib", "datetime",
    "string", "types", "warnings", "traceback", "logging",
})


def _load_decisions():
    with open(_DECISIONS_FIXTURE, encoding="utf-8") as f:
        return json.load(f)


def _run_validator(decisions_path: pathlib.Path, repo_root: pathlib.Path,
                   extra_args: list | None = None) -> subprocess.CompletedProcess:
    cmd = [
        sys.executable, str(_VALIDATOR),
        "--decisions-only",
        "--decisions-path", str(decisions_path),
        "--repo-root", str(repo_root),
    ]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


def _run_validator_json(decisions_path, repo_root, extra_args=None):
    cp = _run_validator(decisions_path, repo_root, extra_args)
    try:
        data = json.loads(cp.stdout)
    except json.JSONDecodeError:
        data = {"_raw_stdout": cp.stdout[:500], "_raw_stderr": cp.stderr[:500]}
    return cp, data


class TestDecisionsOnlyPass(unittest.TestCase):
    """Valid committed artifact must pass."""

    def test_valid_committed_artifact(self):
        """The committed S0_DECISIONS.json must pass decisions-only validation."""
        cp, data = _run_validator_json(_DECISIONS_FIXTURE, _REPO_ROOT)
        self.assertEqual(cp.returncode, 0,
                         f"stdout: {cp.stdout[:500]}\nstderr: {cp.stderr[:500]}")
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("frozen_count"), 10)
        self.assertEqual(data.get("total_decisions"), 10)
        self.assertEqual(data.get("user_decision_required_count"), 0)
        self.assertEqual(data.get("explicitly_deferred_count"), 0)
        self.assertIsNone(data.get("primary_error"))
        self.assertEqual(len(data.get("errors", [])), 0)


class TestDecisionsOnlyFail(unittest.TestCase):
    """Mutated decisions must produce validation errors."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = pathlib.Path(self.tmp.name)
        self.base = _load_decisions()

    def tearDown(self):
        self.tmp.cleanup()

    def _write_and_run(self, data) -> tuple[subprocess.CompletedProcess, dict]:
        p = self.tmp_path / "decisions.json"
        p.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return _run_validator_json(p, _REPO_ROOT)

    # ── malformed / structural ───────────────────────────────────────

    def test_malformed_json(self):
        p = self.tmp_path / "decisions.json"
        p.write_text("{not valid json", encoding="utf-8")
        cp, data = _run_validator_json(p, _REPO_ROOT)
        self.assertNotEqual(cp.returncode, 0)
        self.assertEqual(data.get("status"), "error")
        self.assertEqual(data.get("primary_error"), "validation_failed")

    def test_not_a_json_object(self):
        p = self.tmp_path / "decisions.json"
        p.write_text("[1, 2, 3]", encoding="utf-8")
        cp, data = _run_validator_json(p, _REPO_ROOT)
        self.assertNotEqual(cp.returncode, 0)
        self.assertEqual(data.get("status"), "error")

    def test_non_object_decision_item(self):
        """Non-dict items in decisions list must produce structured error."""
        d = copy.deepcopy(self.base)
        d["decisions"][3] = ["not", "a", "dict"]
        cp, data = self._write_and_run(d)
        self.assertNotEqual(cp.returncode, 0)
        errors = data.get("errors", [])
        self.assertTrue(any("not an object" in e.get("detail", "")
                          for e in errors), f"errors: {errors}")

    def test_non_string_authority_path(self):
        """Non-string authority_refs path must produce structured error."""
        d = copy.deepcopy(self.base)
        d["decisions"][0]["authority_refs"][0]["path"] = 12345
        cp, data = self._write_and_run(d)
        self.assertNotEqual(cp.returncode, 0)
        errors = data.get("errors", [])
        self.assertTrue(any("path is not a string" in e.get("detail", "")
                          for e in errors), f"errors: {errors}")

    # ── top-level exact-value checks ────────────────────────────────

    def test_wrong_artifact_stage_state(self):
        """artifact, stage, state must have exact committed values."""
        cases = [
            ("artifact", "Wrong/Value", "artifact"),
            ("stage", "S1_PRODUCTION", "stage"),
            ("state", "not_ready", "state"),
        ]
        for field, bad_val, match_str in cases:
            with self.subTest(field=field):
                d = copy.deepcopy(self.base)
                d[field] = bad_val
                _, data = self._write_and_run(d)
                self.assertIn("error", data.get("status", ""),
                              f"Expected error for {field}={bad_val!r}")
                errors = data.get("errors", [])
                self.assertTrue(any(match_str in e.get("detail", "")
                                  for e in errors),
                                f"Expected '{match_str}' in errors for {field}")

    # ── required sections ───────────────────────────────────────────

    def test_section_problems(self):
        """Missing/non-object meta, t0_metadata, approval_evidence must fail."""
        # Missing sections
        for section in ("meta", "t0_metadata", "approval_evidence"):
            with self.subTest(missing=section):
                d = copy.deepcopy(self.base)
                del d[section]
                _, data = self._write_and_run(d)
                errors = data.get("errors", [])
                self.assertTrue(any(f"missing top-level key: {section}"
                                  in e.get("detail", "")
                                  for e in errors),
                                f"Missing {section} not flagged")
        # Non-object sections
        for section in ("meta", "t0_metadata", "approval_evidence"):
            with self.subTest(non_object=section):
                d = copy.deepcopy(self.base)
                d[section] = [1, 2, 3]
                _, data = self._write_and_run(d)
                errors = data.get("errors", [])
                self.assertTrue(any(f"{section} is not an object"
                                  in e.get("detail", "")
                                  for e in errors),
                                f"Non-object {section} not flagged")

    def test_approval_method_missing(self):
        """approval_evidence.method must be nonempty string."""
        d = copy.deepcopy(self.base)
        d["approval_evidence"]["method"] = ""
        _, data = self._write_and_run(d)
        errors = data.get("errors", [])
        self.assertTrue(any("method" in e.get("detail", "") for e in errors))

    # ── forbidden status tokens ──────────────────────────────────────

    def test_tbd_status(self):
        d = copy.deepcopy(self.base)
        d["decisions"][0]["status"] = "TBD"
        _, data = self._write_and_run(d)
        errors = data.get("errors", [])
        self.assertTrue(any("forbidden status" in e.get("detail", "")
                          for e in errors), f"errors: {errors}")

    def test_unrecognized_status(self):
        d = copy.deepcopy(self.base)
        d["decisions"][0]["status"] = "unknown-status"
        _, data = self._write_and_run(d)
        errors = data.get("errors", [])
        self.assertTrue(any("unrecognized status" in e.get("detail", "")
                          for e in errors), f"errors: {errors}")

    # ── user-decision-required ───────────────────────────────────────

    def test_user_decision_required_blocking(self):
        d = copy.deepcopy(self.base)
        d["decisions"][0]["status"] = "user-decision-required"
        _, data = self._write_and_run(d)
        errors = data.get("errors", [])
        self.assertTrue(any("user-decision-required" in e.get("detail", "")
                          and "requires zero unresolved" in e.get("detail", "")
                          for e in errors), f"errors: {errors}")
        self.assertEqual(data.get("user_decision_required_count"), 1)

    # ── missing / duplicate / extra IDs ──────────────────────────────

    def test_missing_u1(self):
        d = copy.deepcopy(self.base)
        d["decisions"] = [e for e in d["decisions"] if e["id"] != "U1"]
        _, data = self._write_and_run(d)
        errors = data.get("errors", [])
        self.assertTrue(any("IDs mismatch" in e.get("detail", "")
                          for e in errors), f"errors: {errors}")

    def test_duplicate_id(self):
        d = copy.deepcopy(self.base)
        dup = copy.deepcopy(d["decisions"][0])
        d["decisions"].append(dup)
        _, data = self._write_and_run(d)
        errors = data.get("errors", [])
        self.assertTrue(any("duplicate" in e.get("detail", "")
                          for e in errors), f"errors: {errors}")

    def test_extra_id(self):
        d = copy.deepcopy(self.base)
        extra = copy.deepcopy(d["decisions"][0])
        extra["id"] = "D10"
        d["decisions"].append(extra)
        _, data = self._write_and_run(d)
        errors = data.get("errors", [])
        self.assertTrue(any("IDs mismatch" in e.get("detail", "")
                          for e in errors), f"errors: {errors}")

    # ── authority_refs ───────────────────────────────────────────────

    def test_frozen_missing_authority_refs(self):
        d = copy.deepcopy(self.base)
        d["decisions"][0]["authority_refs"] = []
        _, data = self._write_and_run(d)
        errors = data.get("errors", [])
        self.assertTrue(any("missing authority_refs" in e.get("detail", "")
                          for e in errors), f"errors: {errors}")

    def test_traversal_authority_path(self):
        d = copy.deepcopy(self.base)
        d["decisions"][0]["authority_refs"][0]["path"] = "../etc/passwd"
        _, data = self._write_and_run(d)
        errors = data.get("errors", [])
        self.assertTrue(any("path error" in e.get("detail", "")
                          for e in errors), f"errors: {errors}")

    def test_absolute_authority_path(self):
        d = copy.deepcopy(self.base)
        d["decisions"][0]["authority_refs"][0]["path"] = "/etc/passwd"
        _, data = self._write_and_run(d)
        errors = data.get("errors", [])
        self.assertTrue(any("path error" in e.get("detail", "")
                          for e in errors), f"errors: {errors}")

    def test_wrong_authority_commit(self):
        d = copy.deepcopy(self.base)
        d["decisions"][0]["authority_refs"][0]["commit"] = \
            "0000000000000000000000000000000000000000"
        _, data = self._write_and_run(d)
        errors = data.get("errors", [])
        self.assertTrue(any("commit" in e.get("detail", "")
                          for e in errors), f"errors: {errors}")

    def test_missing_authority_section(self):
        d = copy.deepcopy(self.base)
        d["decisions"][0]["authority_refs"][0]["section"] = ""
        _, data = self._write_and_run(d)
        errors = data.get("errors", [])
        self.assertTrue(any("section" in e.get("detail", "")
                          for e in errors), f"errors: {errors}")

    # ── D7 / U1 must be frozen ───────────────────────────────────────

    def test_d7_not_frozen(self):
        d = copy.deepcopy(self.base)
        for e in d["decisions"]:
            if e["id"] == "D7":
                e["status"] = "user-decision-required"
        _, data = self._write_and_run(d)
        errors = data.get("errors", [])
        self.assertTrue(any("D7" in e.get("detail", "")
                          and "frozen" in e.get("detail", "")
                          for e in errors), f"errors: {errors}")

    def test_u1_not_frozen(self):
        d = copy.deepcopy(self.base)
        for e in d["decisions"]:
            if e["id"] == "U1":
                e["status"] = "explicitly-deferred"
        _, data = self._write_and_run(d)
        errors = data.get("errors", [])
        self.assertTrue(any("U1" in e.get("detail", "")
                          and "frozen" in e.get("detail", "")
                          for e in errors), f"errors: {errors}")

    # ── meta count mismatch ──────────────────────────────────────────

    def test_meta_frozen_count_mismatch(self):
        d = copy.deepcopy(self.base)
        d["meta"]["frozen_count"] = 5
        _, data = self._write_and_run(d)
        errors = data.get("errors", [])
        self.assertTrue(any("frozen_count" in e.get("detail", "")
                          for e in errors), f"errors: {errors}")

    def test_meta_total_mismatch(self):
        d = copy.deepcopy(self.base)
        d["meta"]["total_decisions"] = 99
        _, data = self._write_and_run(d)
        errors = data.get("errors", [])
        self.assertTrue(any("total_decisions" in e.get("detail", "")
                          for e in errors), f"errors: {errors}")

    def test_forbidden_statuses_absent_malformed(self):
        """Non-string elements like [[]] must not traceback."""
        d = copy.deepcopy(self.base)
        d["meta"]["forbidden_statuses_absent"] = [[]]
        cp, data = self._write_and_run(d)
        self.assertNotEqual(cp.returncode, 0)
        self.assertEqual(data.get("status"), "error")
        self.assertEqual(data.get("primary_error"), "validation_failed",
                         f"Expected primary validation_failed, got {data}")
        errors = data.get("errors", [])
        self.assertTrue(any("forbidden_statuses_absent" in e.get("detail", "")
                          for e in errors),
                        f"forbidden_statuses_absent not flagged: {errors}")

    # ── explicitly-deferred fields ───────────────────────────────────

    def test_explicitly_deferred_missing_fields(self):
        d = copy.deepcopy(self.base)
        d["decisions"][0]["status"] = "explicitly-deferred"
        _, data = self._write_and_run(d)
        errors = data.get("errors", [])
        self.assertTrue(any("explicitly-deferred" in e.get("detail", "")
                          for e in errors), f"errors: {errors}")

    def test_explicitly_deferred_positive(self):
        """Non-D7/U1 explicitly-deferred entry passes decisions-only
        when all other entries are frozen and meta counts are correct."""
        d = copy.deepcopy(self.base)
        # Convert D1 to fully-qualified explicitly-deferred
        d["decisions"][0].update({
            "status": "explicitly-deferred",
            "named_slice": "test-slice-1",
            "rationale": "Deferred for future S1 implementation",
            "acceptance_criteria": "All S1 CLI tests pass",
        })
        # Remove frozen-only fields that might cause false conflicts
        d["decisions"][0].pop("decided_by", None)
        d["decisions"][0].pop("decided_at", None)
        d["decisions"][0].pop("authority_refs", None)
        # Fix meta counts: 9 frozen, 1 deferred, 0 user-decision-required
        d["meta"]["frozen_count"] = 9
        d["meta"]["explicitly_deferred_count"] = 1
        d["meta"]["user_decision_required_count"] = 0
        cp, data = self._write_and_run(d)
        self.assertEqual(cp.returncode, 0,
                         f"Explicitly-deferred positive should pass. "
                         f"stdout: {cp.stdout[:500]}")
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("explicitly_deferred_count"), 1)
        self.assertEqual(data.get("frozen_count"), 9)
        self.assertEqual(data.get("user_decision_required_count"), 0)

    # ── frozen missing summary ───────────────────────────────────────

    def test_frozen_missing_summary(self):
        d = copy.deepcopy(self.base)
        d["decisions"][0]["summary"] = ""
        _, data = self._write_and_run(d)
        errors = data.get("errors", [])
        self.assertTrue(any("nonempty summary" in e.get("detail", "")
                          for e in errors), f"errors: {errors}")

    # ── D2 identity enforcement ──────────────────────────────────────

    def test_d2_identity_violations(self):
        """agent: prefix, long slug, and invalid identity must be rejected."""
        d = copy.deepcopy(self.base)
        d["decisions"][0]["decided_by"] = "agent:assessor-bot"
        d["approval_evidence"]["decided_by"] = "agent:reviewer-ai"
        d["decisions"][1]["decided_by"] = "human:" + ("x" * 65)
        _, data = self._write_and_run(d)
        errors = data.get("errors", [])
        self.assertTrue(any(("agent:assessor-bot" in e.get("detail", "")
                           or "agent:reviewer-ai" in e.get("detail", ""))
                          for e in errors),
                        f"agent: identity not rejected. errors: {errors}")
        self.assertTrue(any("length" in e.get("detail", "")
                          for e in errors),
                        f"long slug not rejected. errors: {errors}")

    # ── primary error ordering ───────────────────────────────────────

    def test_primary_error_ordering(self):
        """Simultaneous profile_mismatch + validation_failed must
        produce primary profile_mismatch (priority 6 < 8)."""
        d = copy.deepcopy(self.base)
        # Wrong protocol → profile_mismatch (priority 6)
        d["protocol"] = "aitp/1.0"
        # Also remove a key to trigger validation_failed (priority 8)
        d.pop("state", None)
        cp, data = self._write_and_run(d)
        self.assertNotEqual(cp.returncode, 0)
        self.assertEqual(data.get("primary_error"), "profile_mismatch",
                         f"Expected primary profile_mismatch, got "
                         f"{data.get('primary_error')}. data: {data}")

    # ── non-hex authority commit ─────────────────────────────────────

    def test_nonhex_authority_commit(self):
        """Non-hex authority_commit must be rejected."""
        d = copy.deepcopy(self.base)
        d["t0_metadata"]["authority_commit"] = "not-a-hex-commit!!"
        _, data = self._write_and_run(d)
        errors = data.get("errors", [])
        self.assertTrue(any("not a valid hex" in e.get("detail", "")
                          for e in errors),
                        f"Non-hex commit not rejected. errors: {errors}")

    # ── decisions path not found ─────────────────────────────────────

    def test_decisions_path_not_found(self):
        cp, data = _run_validator_json(
            self.tmp_path / "nonexistent.json", _REPO_ROOT)
        self.assertNotEqual(cp.returncode, 0)
        self.assertEqual(data.get("status"), "error")
        self.assertEqual(data.get("primary_error"), "validation_failed")


class TestNoMode(unittest.TestCase):
    """No supported mode must return not_available_in_stage with primary_error."""

    def test_no_mode(self):
        cp = subprocess.run(
            [sys.executable, str(_VALIDATOR)],
            capture_output=True, text=True, timeout=15,
            cwd=str(_REPO_ROOT),
        )
        self.assertNotEqual(cp.returncode, 0)
        try:
            data = json.loads(cp.stdout)
        except json.JSONDecodeError:
            data = {}
        self.assertEqual(data.get("status"), "error")
        self.assertEqual(data.get("primary_error"), "not_available_in_stage",
                         f"Expected not_available_in_stage, got {data}")
        errors = data.get("errors", [])
        self.assertTrue(
            any(e.get("code") == "not_available_in_stage" for e in errors),
            f"Expected not_available_in_stage, got: {errors}")


class TestPathHelper(unittest.TestCase):
    """Unit-test _validate_path helper for POSIX path rules."""

    def test_validate_path_posix(self):
        from tests.aitp2 import check_s0_freeze as v
        # Benign double-dot in filename
        self.assertIsNone(v._validate_path("foo..bar.md"))
        self.assertIsNone(v._validate_path("dir/foo..bar/readme.md"))
        self.assertIsNone(v._validate_path("docs/specs/2026-07-20-aitp-2-0.md"))
        # Rejected patterns
        self.assertIsNotNone(v._validate_path("../etc/passwd"))
        self.assertIsNotNone(v._validate_path("foo/../bar"))
        self.assertIsNotNone(v._validate_path("."))
        self.assertIsNotNone(v._validate_path(".."))
        self.assertIsNotNone(v._validate_path(""))
        self.assertIsNotNone(v._validate_path("/etc/passwd"))
        self.assertIsNotNone(v._validate_path("C:\\foo"))
        self.assertIsNotNone(v._validate_path("foo/\x00bar"))
        self.assertIsNotNone(v._validate_path(12345))
        self.assertIsNotNone(v._validate_path("foo/"))
        self.assertIsNotNone(v._validate_path("foo//bar"))


class TestStaticImports(unittest.TestCase):
    """Validator must use stdlib only — no aitp, no third-party, no network."""

    def test_stdlib_only_imports(self):
        source = _VALIDATOR.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    imports.append(top)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top = node.module.split(".")[0]
                    imports.append(top)
        non_stdlib = [i for i in imports if i not in _STDLIB_ALLOWLIST]
        self.assertEqual(
            non_stdlib, [],
            f"Non-stdlib imports found: {non_stdlib}. "
            f"Validator must use stdlib only."
        )

    def test_no_aitp_import(self):
        source = _VALIDATOR.read_text(encoding="utf-8")
        self.assertNotIn("import aitp", source)
        self.assertNotIn("from aitp", source)

    def test_no_network_modules(self):
        source = _VALIDATOR.read_text(encoding="utf-8")
        for mod in ("urllib", "http", "socket", "requests", "httpx"):
            self.assertNotIn(f"import {mod}", source,
                             f"Network module {mod} found in validator")
            self.assertNotIn(f"from {mod}", source,
                             f"Network module {mod} found in validator")

    def test_no_external_aitp_access(self):
        source = _VALIDATOR.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if ".aitp" in node.value:
                    if "tests/fixtures/aitp2" in node.value:
                        continue
                    if "no external .aitp" in node.value.lower():
                        continue
                    self.fail(
                        f"AST string constant contains .aitp outside "
                        f"allowed artifact path: {node.value!r}"
                    )

    def test_no_pyyaml(self):
        source = _VALIDATOR.read_text(encoding="utf-8")
        self.assertNotIn("yaml", source.lower(),
                         "Validator must not import yaml/PyYAML")


class TestLineCount(unittest.TestCase):
    """Each file must be under 500 nonblank noncomment lines."""

    def _count_lines(self, path: pathlib.Path) -> int:
        source = path.read_text(encoding="utf-8")
        count = 0
        for line in source.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                count += 1
        return count

    def test_validator_line_count(self):
        count = self._count_lines(_VALIDATOR)
        self.assertLess(count, 500,
                        f"Validator has {count} nonblank noncomment lines "
                        f"(limit 500)")

    def test_test_line_count(self):
        count = self._count_lines(pathlib.Path(__file__))
        self.assertLess(count, 500,
                        f"Test file has {count} nonblank noncomment lines "
                        f"(limit 500)")


if __name__ == "__main__":
    unittest.main()
