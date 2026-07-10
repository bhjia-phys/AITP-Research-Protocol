"""Read-only compatibility audit for canonical registry record envelopes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from brain.v5.markdown import read_md
from brain.v5.paths import WorkspacePaths
from brain.v5.record_envelope import read_envelope_compat
from brain.v5.record_family_registry import registry_family_specs


@dataclass(frozen=True)
class EnvelopeAuditFamilyCount:
    checked_count: int = 0
    loaded_count: int = 0
    malformed_count: int = 0


@dataclass(frozen=True)
class EnvelopeAuditIssue:
    family: str
    path: str
    error: str


@dataclass(frozen=True)
class EnvelopeCompatibilityAudit:
    workspace_root: str
    checked_count: int
    loaded_count: int
    malformed_count: int
    issue_count: int
    family_counts: dict[str, EnvelopeAuditFamilyCount]
    issues: tuple[EnvelopeAuditIssue, ...]
    orientation_only: bool = True
    can_update_kernel_state: bool = False
    can_update_claim_trust: bool = False


def audit_record_envelope_compatibility(
    workspace_base: str | Path,
    *,
    families: Iterable[str] | None = None,
    issue_limit: int = 50,
) -> EnvelopeCompatibilityAudit:
    """Audit registry Markdown records without changing canonical state."""

    if issue_limit < 0:
        raise ValueError("issue_limit must be non-negative")

    specs = registry_family_specs()
    selected = tuple(sorted(set(families) if families is not None else specs))
    unknown = [family for family in selected if family not in specs]
    if unknown:
        raise ValueError(f"unknown record families: {', '.join(unknown)}")

    ws = WorkspacePaths(Path(workspace_base))
    counts: dict[str, EnvelopeAuditFamilyCount] = {}
    issues: list[EnvelopeAuditIssue] = []
    checked_total = 0
    loaded_total = 0
    malformed_total = 0

    for family in selected:
        checked = 0
        loaded = 0
        malformed = 0
        for path in sorted(ws.registry_dir(family).glob("*.md")):
            checked += 1
            checked_total += 1
            try:
                frontmatter, body = read_md(path)
                read_envelope_compat(frontmatter, specs[family], path, body=body)
            except Exception as exc:  # noqa: BLE001 - audit must inventory every failure.
                malformed += 1
                malformed_total += 1
                if len(issues) < issue_limit:
                    issues.append(
                        EnvelopeAuditIssue(
                            family=family,
                            path=str(path),
                            error=str(exc),
                        )
                    )
            else:
                loaded += 1
                loaded_total += 1
        counts[family] = EnvelopeAuditFamilyCount(
            checked_count=checked,
            loaded_count=loaded,
            malformed_count=malformed,
        )

    return EnvelopeCompatibilityAudit(
        workspace_root=str(ws.root),
        checked_count=checked_total,
        loaded_count=loaded_total,
        malformed_count=malformed_total,
        issue_count=malformed_total,
        family_counts=counts,
        issues=tuple(issues),
    )
