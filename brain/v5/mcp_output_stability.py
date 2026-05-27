"""MCP wrappers for stable final-output profiles."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from brain.v5.output_stability import record_final_output_profile
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.workspace import init_workspace


def _ws(base: str):
    return init_workspace(Path(base))


def aitp_v5_record_final_output_profile(
    base: str, *, topic_id: str, output_version: str, audience: str,
    stable_sections: list[str] | None = None, flexible_sections: list[str] | None = None,
    change_policy: str = "", compatibility_note: str = "", status: str = "active",
) -> dict:
    profile = record_final_output_profile(
        _ws(base),
        topic_id=topic_id,
        output_version=output_version,
        audience=audience,
        stable_sections=stable_sections,
        flexible_sections=flexible_sections,
        change_policy=change_policy,
        compatibility_note=compatibility_note,
        status=status,
    )
    return require_valid_public_surface("final_output_profile", {"ok": True, **asdict(profile)})
