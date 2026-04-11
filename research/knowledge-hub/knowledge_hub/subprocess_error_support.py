from __future__ import annotations

import shlex


def format_subprocess_failure(
    command: list[str],
    *,
    returncode: int,
    stdout: str = "",
    stderr: str = "",
    context: str = "subprocess",
) -> str:
    rendered_command = shlex.join([str(part) for part in command])
    trimmed_stderr = str(stderr or "").strip()
    trimmed_stdout = str(stdout or "").strip()
    parts = [
        f"{context} failed",
        f"returncode={returncode}",
        f"command={rendered_command}",
    ]
    if trimmed_stderr:
        parts.append(f"stderr={trimmed_stderr}")
    if trimmed_stdout:
        parts.append(f"stdout={trimmed_stdout}")
    if not trimmed_stderr and not trimmed_stdout:
        parts.append("stderr/stdout empty")
    return "; ".join(parts)
