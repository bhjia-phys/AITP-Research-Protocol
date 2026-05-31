"""MCP wrappers for QSGW/LibRPA cockpit surfaces."""

from __future__ import annotations

from pathlib import Path

from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.qsgw_cockpit import (
    DEFAULT_QSGW_TOPIC_ID,
    compact_qsgw_cockpit_bundle,
    write_qsgw_cockpit_surfaces,
)
from brain.v5.workspace import init_workspace


def _ws(base: str):
    return init_workspace(Path(base))


def aitp_v5_write_qsgw_cockpit_surfaces(
    base: str,
    *,
    topic_id: str = DEFAULT_QSGW_TOPIC_ID,
    reports_dir: str = "",
    scripts_dir: str = "",
) -> dict:
    return require_valid_public_surface(
        "qsgw_cockpit_bundle",
        write_qsgw_cockpit_surfaces(
            _ws(base),
            topic_id=topic_id,
            reports_dir=reports_dir or None,
            scripts_dir=scripts_dir or None,
        ),
    )


def aitp_v5_write_qsgw_cockpit_surfaces_compact(
    base: str,
    *,
    topic_id: str = DEFAULT_QSGW_TOPIC_ID,
    reports_dir: str = "",
    scripts_dir: str = "",
) -> dict:
    bundle = aitp_v5_write_qsgw_cockpit_surfaces(
        base,
        topic_id=topic_id,
        reports_dir=reports_dir,
        scripts_dir=scripts_dir,
    )
    return compact_qsgw_cockpit_bundle(bundle)
