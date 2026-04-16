from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from knowledge_hub.frontdoor_support import pip_show_package


class PublicInstallContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.kernel_root = Path(__file__).resolve().parents[1]

    def test_docs_reference_public_install_smoke(self) -> None:
        kernel_readme = (self.kernel_root / "README.md").read_text(encoding="utf-8")
        runtime_readme = (self.kernel_root / "runtime" / "README.md").read_text(encoding="utf-8")
        runbook = (self.kernel_root / "runtime" / "AITP_TEST_RUNBOOK.md").read_text(encoding="utf-8")

        self.assertIn("run_public_install_smoke.py", kernel_readme)
        self.assertIn("run_public_install_smoke.py", runtime_readme)
        self.assertIn("run_public_install_smoke.py", runbook)
        self.assertIn("aitp-kernel", kernel_readme)
        self.assertIn("AITP_HOME", runtime_readme)

    def test_public_install_smoke_script_exists_and_exercises_installed_cli(self) -> None:
        script = (
            self.kernel_root / "runtime" / "scripts" / "run_public_install_smoke.py"
        ).read_text(encoding="utf-8")

        self.assertIn("venv.EnvBuilder", script)
        self.assertIn("\"aitp-kernel\"", script)
        self.assertIn("\"doctor\"", script)
        self.assertIn("\"bootstrap\"", script)
        self.assertIn("\"loop\"", script)
        self.assertIn("\"status\"", script)
        self.assertIn("AITP_HOME", script)

    def test_pip_show_package_falls_back_to_python_when_console_entrypoint_is_not_python(self) -> None:
        commands: list[list[str]] = []

        def fake_run(argv, check=False, capture_output=True, text=True, stdin=None):  # noqa: ANN001
            commands.append(list(argv))

            class Result:
                returncode = 0
                stdout = "Name: aitp-kernel\nVersion: 0.4.1\nLocation: C:\\temp\\venv\\Lib\\site-packages\n"
                stderr = ""

            return Result()

        with patch("knowledge_hub.frontdoor_support.sys.executable", "C:\\temp\\venv\\Scripts\\aitp.exe"):
            with patch(
                "knowledge_hub.frontdoor_support.shutil.which",
                side_effect=lambda name: "C:\\temp\\venv\\Scripts\\python.exe" if name == "python" else "",
            ):
                with patch("knowledge_hub.frontdoor_support.subprocess.run", side_effect=fake_run):
                    payload = pip_show_package("aitp-kernel")

        self.assertEqual(
            commands[0][:4],
            ["C:\\temp\\venv\\Scripts\\python.exe", "-m", "pip", "show"],
        )
        self.assertEqual(payload["name"], "aitp-kernel")
        self.assertEqual(payload["version"], "0.4.1")


if __name__ == "__main__":
    unittest.main()
