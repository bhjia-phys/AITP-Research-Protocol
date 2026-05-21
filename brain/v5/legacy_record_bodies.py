"""Shared Markdown body builders for legacy migration records."""

from __future__ import annotations


def legacy_evidence_body(
    *,
    title: str,
    summary: str,
    display_path: str,
    body: str,
) -> str:
    original = body.strip() or "(Legacy artifact had no Markdown body.)"
    return (
        f"# {title}\n\n"
        f"{summary}\n\n"
        f"Source path: `{display_path}`\n\n"
        "## Migrated Legacy Body\n\n"
        f"{original}\n"
    )
