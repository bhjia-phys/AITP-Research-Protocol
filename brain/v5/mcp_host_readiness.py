"""MCP wrapper for dynamic runtime host-readiness audits."""

from __future__ import annotations

from pathlib import Path

from brain.v5.host_readiness import audit_priority_host_production_loops, audit_runtime_host_lifecycle, audit_runtime_host_readiness
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.workspace import init_workspace


def aitp_v5_audit_runtime_host_readiness(
    base: str,
    *,
    runtime: str,
    command: str = "",
    version_args: list[str] | None = None,
    timeout_seconds: int = 20,
    settings_path: str = "",
    plugin_path: str = "",
    output_path: str = "",
    check_installation: bool = True,
    session_id: str = "",
    run_session_start_smoke: bool = False,
) -> dict:
    return require_valid_public_surface(
        "runtime_host_readiness_audit",
        audit_runtime_host_readiness(
            init_workspace(Path(base)),
            runtime=runtime,
            command=command,
            version_args=version_args,
            timeout_seconds=timeout_seconds,
            settings_path=settings_path,
            plugin_path=plugin_path,
            output_path=output_path,
            check_installation=check_installation,
            session_id=session_id,
            run_session_start_smoke=run_session_start_smoke,
        ),
    )


def aitp_v5_audit_runtime_host_lifecycle(
    base: str,
    *,
    runtime: str,
    command: str = "",
    args: list[str] | None = None,
    timeout_seconds: int = 60,
) -> dict:
    return require_valid_public_surface(
        "runtime_host_lifecycle_audit",
        audit_runtime_host_lifecycle(
            init_workspace(Path(base)),
            runtime=runtime,
            command=command,
            args=args,
            timeout_seconds=timeout_seconds,
        ),
    )


def aitp_v5_audit_priority_host_production_loops(
    base: str,
    *,
    command: str = "",
    version_args: list[str] | None = None,
    timeout_seconds: int = 20,
    check_installation: bool = True,
    session_id: str = "",
    run_session_start_smoke: bool = False,
    run_lifecycle_smoke: bool = False,
) -> dict:
    return require_valid_public_surface(
        "runtime_host_production_loop_audit",
        audit_priority_host_production_loops(
            init_workspace(Path(base)),
            command=command,
            version_args=version_args,
            timeout_seconds=timeout_seconds,
            check_installation=check_installation,
            session_id=session_id,
            run_session_start_smoke=run_session_start_smoke,
            run_lifecycle_smoke=run_lifecycle_smoke,
        ),
    )
