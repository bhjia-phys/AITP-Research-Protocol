from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path


class MaintainabilityBudgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[3]
        config_path = cls.repo_root / "research" / "knowledge-hub" / "maintainability_budgets.json"
        cls.config = json.loads(config_path.read_text(encoding="utf-8"))

    def _iter_python_files(self) -> list[Path]:
        files: list[Path] = []
        for root_value in self.config["roots"]:
            root = self.repo_root / root_value
            for path in root.rglob("*.py"):
                if "__pycache__" in path.parts:
                    continue
                files.append(path)
        return sorted(files)

    def _metrics_for(self, path: Path) -> dict[str, object]:
        text = path.read_text(encoding="utf-8")
        lines = len(text.splitlines())
        tree = ast.parse(text)
        longest_name = ""
        longest_lines = 0
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            start = getattr(node, "lineno", 0)
            end = getattr(node, "end_lineno", start)
            span = max(0, end - start + 1)
            if span > longest_lines:
                longest_lines = span
                longest_name = node.name
        return {
            "lines": lines,
            "longest_function_lines": longest_lines,
            "longest_function_name": longest_name,
        }

    def test_every_large_or_long_file_is_explicitly_watchlisted(self) -> None:
        thresholds = self.config["default_watch_thresholds"]
        watchlist = self.config["watchlist"]
        offenders: list[str] = []
        for path in self._iter_python_files():
            rel = path.relative_to(self.repo_root).as_posix()
            metrics = self._metrics_for(path)
            if (
                int(metrics["lines"]) > int(thresholds["max_lines"])
                or int(metrics["longest_function_lines"]) > int(thresholds["max_longest_function_lines"])
            ) and rel not in watchlist:
                offenders.append(
                    f"{rel} lines={metrics['lines']} longest_function={metrics['longest_function_name']}:{metrics['longest_function_lines']}"
                )
        self.assertEqual(
            offenders,
            [],
            msg="Large or long-function Python files must be explicitly watchlisted:\n" + "\n".join(offenders),
        )

    def test_watchlisted_files_stay_within_declared_budgets(self) -> None:
        failures: list[str] = []
        for rel, budget in sorted(self.config["watchlist"].items()):
            path = self.repo_root / rel
            self.assertTrue(path.exists(), msg=f"Watchlisted path is missing: {rel}")
            self.assertTrue(str(budget.get("reason") or "").strip(), msg=f"Watchlisted path lacks rationale: {rel}")
            metrics = self._metrics_for(path)
            max_lines = int(budget["max_lines"])
            max_longest_function_lines = int(budget["max_longest_function_lines"])
            if int(metrics["lines"]) > max_lines:
                failures.append(
                    f"{rel} lines={metrics['lines']} exceeds max_lines={max_lines}"
                )
            if int(metrics["longest_function_lines"]) > max_longest_function_lines:
                failures.append(
                    f"{rel} longest_function={metrics['longest_function_name']}:{metrics['longest_function_lines']} exceeds max_longest_function_lines={max_longest_function_lines}"
                )
        self.assertEqual(
            failures,
            [],
            msg="Watchlisted files exceeded maintainability budgets:\n" + "\n".join(failures),
        )


if __name__ == "__main__":
    unittest.main()
