"""M1e reviewed workstream backfill command contract."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from aitp.backfill import backfill_workspace
from aitp.core import (
    AITPError,
    atomic_write,
    init_workspace,
    parse_markdown,
    prepare_entry,
    prepare_note,
    render_markdown,
    save_entry,
    save_note,
)


DECISION_BODY = """## Durable Summary

A human approves the pinned backfill mapping.

## Decision And Alternatives

Adopt the mapping as reviewed.

## Reason, Scope, And Revisit Condition

Revisit only with a new reviewed mapping.
"""


def initialized(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    init_workspace(root, "bf", "Backfill test")
    return root


def save_decision(root: Path, *, refs: list[dict[str, str]]) -> str:
    prepared = prepare_entry(root, "decision", "human")
    path = root / prepared["path"]
    fm, _, _ = parse_markdown(path)
    fm.update(
        {
            "summary": "Human approves the backfill mapping.",
            "refs": refs,
            "limitations": ["Mapping is scoped to the listed records."],
            "resolves": [],
            "supersedes": [],
            "next_action": "",
        }
    )
    atomic_write(path, render_markdown(fm, DECISION_BODY))
    return save_entry(root, prepared["path"])["path"]


def save_result(root: Path, *, summary: str = "Record.") -> str:
    prepared = prepare_entry(root, "decision", "agent", created_by="agent:test")
    path = root / prepared["path"]
    fm, _, _ = parse_markdown(path)
    fm.update(
        {
            "summary": summary,
            "refs": [],
            "limitations": [],
            "resolves": [],
            "supersedes": [],
            "next_action": "",
        }
    )
    body = """## Durable Summary

Record.

## Decision And Alternatives

Use this record for backfill tests.

## Reason, Scope, And Revisit Condition

Test only.
"""
    atomic_write(path, render_markdown(fm, body))
    return save_entry(root, prepared["path"])["path"]


def save_working_note(root: Path, title: str = "Working state") -> str:
    prepared = prepare_note(root, "working", title, created_by="agent:test")
    path = root / prepared["path"]
    evidence = root / "theory" / "note-evidence.md"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text("evidence\n", encoding="utf-8")
    fm, _, _ = parse_markdown(path)
    fm.update(
        {
            "summary": "Working note summary.",
            "basis_refs": [
                {
                    "target": "theory/note-evidence.md",
                    "at": f"sha256:{hashlib.sha256(evidence.read_bytes()).hexdigest()}",
                }
            ],
            "supersedes": [],
        }
    )
    body = """## Purpose

Synthesis.

## Scope And Basis

Recorded state.

## Synthesis

State.

## Evidence Map

No refs.

## Uncertainty And Omissions

None.

## Open Questions

None.

## Next Actions

None.
"""
    atomic_write(path, render_markdown(fm, body))
    return save_note(root, prepared["path"])["path"]


def write_mapping(root: Path, data: dict) -> str:
    path = root / "backfills" / "mapping.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(path, json.dumps(data) + "\n")
    return str(path.relative_to(root))


def anchor(root: Path, mapping_rel: str) -> dict[str, str]:
    digest = hashlib.sha256((root / mapping_rel).read_bytes()).hexdigest()
    return {"target": mapping_rel, "at": f"sha256:{digest}", "locator": "whole mapping"}


def test_backfill_dry_run_then_apply_is_idempotent(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    entry = save_result(root)
    note = save_working_note(root)
    entry_id = entry.split("/")[-1].removesuffix(".md")
    note_id = note.split("/")[-1].removesuffix(".md")
    mapping_rel = write_mapping(
        root,
        {
            "schema": "aitp/backfill-workstreams-0.1",
            "entries": {"crpa": [entry_id]},
            "notes": {"algebra-flow": [note_id]},
        },
    )
    decision = save_decision(root, refs=[anchor(root, mapping_rel)])
    decision_id = decision.split("/")[-1].removesuffix(".md")

    dry = backfill_workspace(root, mapping=mapping_rel, decision=decision_id, apply=False)
    assert dry["status"] == "dry_run"
    assert len(dry["changed"]) == 2
    assert parse_markdown(root / entry).__getitem__(0).get("workstreams") is None

    applied = backfill_workspace(root, mapping=mapping_rel, decision=decision_id, apply=True)
    assert applied["status"] == "applied"
    assert {(c["path"], tuple(c["workstreams"])) for c in applied["changed"]} == {
        (entry, ("crpa",)),
        (note, ("algebra-flow",)),
    }
    entry_fm, entry_body, _ = parse_markdown(root / entry)
    assert entry_fm["workstreams"] == ["crpa"]
    assert "Record." in entry_body
    again = backfill_workspace(root, mapping=mapping_rel, decision=decision_id, apply=True)
    assert again["changed"] == []
    assert again["unchanged"] == [entry_id, note_id]


def test_backfill_rejects_non_human_or_unanchored_decision(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    entry = save_result(root)
    entry_id = entry.split("/")[-1].removesuffix(".md")
    mapping_rel = write_mapping(
        root, {"schema": "aitp/backfill-workstreams-0.1", "entries": {"crpa": [entry_id]}, "notes": {}}
    )
    # Agent decision is rejected.
    prepared = prepare_entry(root, "decision", "agent", created_by="agent:test")
    path = root / prepared["path"]
    fm, _, _ = parse_markdown(path)
    fm.update({"summary": "Agent decision.", "refs": [anchor(root, mapping_rel)], "limitations": [], "resolves": [], "supersedes": [], "next_action": ""})
    atomic_write(path, render_markdown(fm, DECISION_BODY))
    agent_decision = save_entry(root, prepared["path"])["path"].split("/")[-1].removesuffix(".md")
    with pytest.raises(AITPError, match="human"):
        backfill_workspace(root, mapping=mapping_rel, decision=agent_decision, apply=False)

    # Human decision that does not pin the mapping is rejected.
    human = save_decision(root, refs=[]).split("/")[-1].removesuffix(".md")
    with pytest.raises(AITPError, match="pin the mapping"):
        backfill_workspace(root, mapping=mapping_rel, decision=human, apply=False)


def test_backfill_rejects_invalid_mapping_and_missing_ids(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    entry = save_result(root)
    entry_id = entry.split("/")[-1].removesuffix(".md")
    decision = save_decision(root, refs=[]).split("/")[-1].removesuffix(".md")

    bad_slug = write_mapping(
        root, {"schema": "aitp/backfill-workstreams-0.1", "entries": {"Bad Slug": [entry_id]}, "notes": {}}
    )
    with pytest.raises(AITPError, match="invalid workstream"):
        backfill_workspace(root, mapping=bad_slug, decision=decision, apply=False)

    duplicate = write_mapping(
        root,
        {
            "schema": "aitp/backfill-workstreams-0.1",
            "entries": {"crpa": [entry_id, entry_id]},
            "notes": {},
        },
    )
    with pytest.raises(AITPError, match="duplicate record ID"):
        backfill_workspace(root, mapping=duplicate, decision=decision, apply=False)

    missing = write_mapping(
        root,
        {
            "schema": "aitp/backfill-workstreams-0.1",
            "entries": {"crpa": ["entry-" + "0" * 32]},
            "notes": {},
        },
    )
    anchored_decision = save_decision(root, refs=[anchor(root, missing)]).split("/")[-1].removesuffix(".md")
    with pytest.raises(AITPError, match="cannot read"):
        backfill_workspace(root, mapping=missing, decision=anchored_decision, apply=False)
