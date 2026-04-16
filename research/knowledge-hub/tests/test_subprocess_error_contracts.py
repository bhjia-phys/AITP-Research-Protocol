from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys


def _bootstrap_path() -> None:
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


_bootstrap_path()

from knowledge_hub.aitp_service import AITPService


class _Completed:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class SubprocessErrorContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[3]

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.kernel_root = Path(self._tmpdir.name) / "kernel"
        self.kernel_root.mkdir(parents=True, exist_ok=True)
        self.service = AITPService(kernel_root=self.kernel_root, repo_root=self.repo_root)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_run_failure_includes_command_and_returncode(self) -> None:
        with patch(
            "knowledge_hub.aitp_service.subprocess.run",
            return_value=_Completed(17, stdout="", stderr="demo stderr"),
        ):
            with self.assertRaises(RuntimeError) as raised:
                self.service._run(["demo-tool", "--flag", "value"])

        message = str(raised.exception)
        self.assertIn("AITP could not finish", message)
        self.assertIn("Exit code: 17", message)
        self.assertIn("Command: demo-tool --flag value", message)
        self.assertIn("Error: demo stderr", message)
        self.assertIn("Try:", message)
        self.assertNotIn("Traceback", message)

    def test_migrate_local_install_failure_includes_context_command_and_returncode(self) -> None:
        workspace_root = Path(self._tmpdir.name) / "workspace"
        workspace_root.mkdir(parents=True, exist_ok=True)

        def fake_run(argv, check=False, capture_output=True, text=True, stdin=None):  # noqa: ANN001
            if argv[:4] == [sys.executable, "-m", "pip", "uninstall"]:
                return _Completed(0, stdout="uninstalled", stderr="")
            if argv[:4] == [sys.executable, "-m", "pip", "install"]:
                return _Completed(23, stdout="", stderr="access denied")
            raise AssertionError(f"Unexpected command: {argv}")

        with patch.object(self.service, "ensure_cli_installed", return_value={"overall_status": "mixed_install"}):
            with patch.object(self.service, "_workspace_legacy_entrypoints", return_value=[]):
                with patch.object(self.service, "_claude_legacy_command_paths", return_value=[]):
                    with patch.object(
                        self.service,
                        "_pip_show_package",
                        return_value={"editable project location": str(Path(self._tmpdir.name) / "old-workspace")},
                    ):
                        with patch("knowledge_hub.frontdoor_support.subprocess.run", side_effect=fake_run):
                            with self.assertRaises(RuntimeError) as raised:
                                self.service.migrate_local_install(
                                    workspace_root=str(workspace_root),
                                    agents=["codex"],
                                    with_mcp=False,
                                )

        message = str(raised.exception)
        self.assertIn("migrate-local-install pip install", message)
        self.assertIn("Exit code: 23", message)
        self.assertIn("-m pip install -e", message)
        self.assertIn("access denied", message)
        self.assertIn("Check that Python and pip can write to the target environment", message)


if __name__ == "__main__":
    unittest.main()
