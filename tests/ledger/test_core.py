from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from aitp.core import (
    AITPError,
    atomic_write,
    enter_workspace,
    init_workspace,
    parse_markdown,
    prepare_entry,
    prepare_note,
    render_markdown,
    resolve_root,
    save_entry,
    save_note,
)


def initialized(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    result = init_workspace(root, "nio", "Magnetic NiO")
    assert result["status"] == "initialized"
    return root


def test_resolve_root_ignores_invalid_git_marker(tmp_path: Path):
    container = tmp_path / "container"
    project = container / "project"
    (container / ".git").mkdir(parents=True)
    project.mkdir()

    assert resolve_root(project) == project


def pinned_file(root: Path, relative: str, text: str = "evidence\n") -> dict[str, str]:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return {
        "target": relative,
        "at": f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}",
        "locator": "whole file",
    }


def fill_entry(
    root: Path,
    prepared: dict[str, str],
    *,
    summary: str,
    limitations: list[str],
    refs: list[dict[str, str]],
    body: str,
    resolves: list[str] | None = None,
    supersedes: list[str] | None = None,
    next_action: str = "",
    created_at: str | None = None,
) -> Path:
    path = root / prepared["path"]
    frontmatter, _, _ = parse_markdown(path)
    frontmatter.update(
        {
            "summary": summary,
            "limitations": limitations,
            "refs": refs,
            "resolves": resolves or [],
            "supersedes": supersedes or [],
            "next_action": next_action,
        }
    )
    if created_at:
        frontmatter["created_at"] = created_at
    atomic_write(path, render_markdown(frontmatter, body))
    return path


def test_init_creates_fixed_repository_and_empty_enter(tmp_path: Path):
    root = initialized(tmp_path)

    assert (root / ".aitp" / "topic" / "TOPIC.md").is_file()
    assert (root / ".aitp" / "local" / "drafts").is_dir()
    assert (root / "theory" / "CONVENTIONS.md").is_file()
    assert (root / "calculations" / "README.md").is_file()

    brief = enter_workspace(root)
    assert brief["memory_status"] == "not_established"
    assert brief["topic"]["id"] == "nio"
    assert brief["recent_entries"] == []
    assert brief["next_action"]["status"] == "not_established"

    with pytest.raises(AITPError, match="already exists"):
        init_workspace(root, "nio", "Magnetic NiO")


def test_result_round_trip_is_grounded_and_idempotent(tmp_path: Path):
    root = initialized(tmp_path)
    ref = pinned_file(root, "theory/head-wing/derivations/update.md")
    prepared = prepare_entry(
        root,
        "result",
        "agent",
        created_by="agent:codex",
        idempotency_key="turn-1-result",
    )
    body = """\
## Durable Summary

Under assumptions A and B, the update removes the recorded discontinuity.

## Basis And Checks

The pinned derivation gives the formula and the three-point check.

## Validity And Implication

Only three momentum points were checked; repeat with three cutoffs.
"""
    draft = fill_entry(
        root,
        prepared,
        summary="Under assumptions A and B, the update removes the recorded discontinuity.",
        limitations=["Checked at three momentum points; no analytic proof recorded."],
        refs=[ref],
        body=body,
        next_action="Repeat with three cutoffs.",
    )

    saved = save_entry(root, draft)
    assert saved["status"] == "saved"
    assert save_entry(root, draft)["status"] == "already_saved"

    retry = prepare_entry(
        root,
        "result",
        "agent",
        created_by="agent:test",
        idempotency_key="turn-1-result",
    )
    assert retry["status"] == "existing"
    assert retry["path"] == saved["path"]

    brief = enter_workspace(root)
    assert brief["memory_status"] == "available"
    entry = brief["recent_entries"][0]
    assert entry["summary"].startswith("Under assumptions")
    assert entry["limitations"] == [
        "Checked at three momentum points; no analytic proof recorded."
    ]
    assert entry["refs"] == [ref]
    assert entry["source"] == saved["path"]
    assert brief["next_action"]["text"] == "Repeat with three cutoffs."


def test_hash_mismatch_blocks_save(tmp_path: Path):
    root = initialized(tmp_path)
    ref = pinned_file(root, "theory/check.md")
    ref["at"] = f"sha256:{'0' * 64}"
    prepared = prepare_entry(root, "result", "agent", created_by="agent:test")
    body = """\
## Durable Summary

Result.

## Basis And Checks

Pinned check.

## Validity And Implication

Conditional result.
"""
    draft = fill_entry(
        root,
        prepared,
        summary="Conditional result.",
        limitations=["Only the stated check was performed."],
        refs=[ref],
        body=body,
    )

    with pytest.raises(AITPError) as error:
        save_entry(root, draft)
    assert error.value.code == "hash_mismatch"


def test_active_state_reopens_failure_when_resolution_is_superseded(tmp_path: Path):
    root = initialized(tmp_path)
    ref = pinned_file(root, "calculations/small-q/input.txt")
    base_time = datetime.now(UTC).replace(microsecond=0)

    failure_prepared = prepare_entry(root, "failure", "agent", created_by="agent:test")
    failure_body = """\
## Durable Summary

The small-q fit is unstable.

## Attempt, Expected, And Observed

The fit was expected to converge but oscillated.

## Evidence And Next Diagnostic

The pinned input reproduces the failure; vary the cutoff.
"""
    failure_draft = fill_entry(
        root,
        failure_prepared,
        summary="The small-q fit is unstable.",
        limitations=[],
        refs=[ref],
        body=failure_body,
        next_action="Vary the cutoff.",
        created_at=base_time.isoformat().replace("+00:00", "Z"),
    )
    save_entry(root, failure_draft)

    resolution_prepared = prepare_entry(root, "decision", "human")
    resolution_body = """\
## Durable Summary

Treat the failure as resolved by the corrected cutoff.

## Decision And Alternatives

Use the corrected cutoff rather than discarding the fit.

## Reason, Scope, And Revisit Condition

Revisit if another material fails.
"""
    resolution_draft = fill_entry(
        root,
        resolution_prepared,
        summary="Treat the failure as resolved by the corrected cutoff.",
        limitations=[],
        refs=[],
        body=resolution_body,
        resolves=[failure_prepared["id"]],
        created_at=(base_time + timedelta(seconds=1)).isoformat().replace(
            "+00:00", "Z"
        ),
    )
    save_entry(root, resolution_draft)
    assert enter_workspace(root)["unresolved_failures"] == []

    correction_prepared = prepare_entry(root, "decision", "human")
    correction_body = """\
## Durable Summary

Withdraw the resolution because the correction was incomplete.

## Decision And Alternatives

Reopen the failure rather than treating it as resolved.

## Reason, Scope, And Revisit Condition

Require a new diagnostic before resolving it again.
"""
    correction_draft = fill_entry(
        root,
        correction_prepared,
        summary="Withdraw the resolution because the correction was incomplete.",
        limitations=[],
        refs=[],
        body=correction_body,
        supersedes=[resolution_prepared["id"]],
        created_at=(base_time + timedelta(seconds=2)).isoformat().replace(
            "+00:00", "Z"
        ),
    )
    save_entry(root, correction_draft)

    brief = enter_workspace(root)
    assert [item["id"] for item in brief["unresolved_failures"]] == [
        failure_prepared["id"]
    ]
    assert brief["counts"]["superseded"] == 1


def test_note_template_round_trip(tmp_path: Path):
    root = initialized(tmp_path)
    ref = pinned_file(root, "theory/summary.md")
    prepared = prepare_note(root, "working", "Current Status", created_by="agent:test")
    draft = root / prepared["path"]
    frontmatter, _, _ = parse_markdown(draft)
    frontmatter["summary"] = "Current evidence and open checks."
    frontmatter["basis_refs"] = [ref]
    body = """\
## Purpose

Summarize current evidence.

## Scope And Basis

The pinned theory summary is included.

## Synthesis

The recorded result remains conditional.

## Evidence Map

The main statement maps to the pinned summary.

## Uncertainty And Omissions

No numerical cross-check is included.

## Open Questions

Does the result survive another cutoff?

## Next Actions

Run the cutoff check.
"""
    atomic_write(draft, render_markdown(frontmatter, body))

    saved = save_note(root, draft)
    assert saved["status"] == "saved"
    assert save_note(root, draft)["status"] == "already_saved"
    assert enter_workspace(root)["recent_notes"][0]["title"] == "Current Status"
