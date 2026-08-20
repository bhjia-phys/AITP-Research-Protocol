"""M1c workstreams: optional `workstreams` membership and single-slug scoped views.

Contract under test (per the frozen implementation spec
``docs/archive/m1c-workstreams-spec.md``):

- ``workstreams`` is an optional Entry/Note frontmatter list. Absence is
  **unscoped legacy**: unscoped records appear only in the unfiltered global
  view and are excluded from every ``--workstream`` scoped view. When the
  field is present it must be a non-empty, no-duplicate slug list; empty
  lists are invalid. Membership is explicit in the frontmatter and never
  inferred; cross-line records list several workstreams.
- Slug grammar is the Topic slug rule ``[a-z0-9][a-z0-9-]{0,62}``; any
  violation (not-a-list, empty list, empty element, invalid slug, duplicate
  element) is error code ``invalid_workstreams`` with message
  ``invalid workstreams: <detail>``.
- ``record prepare``/``note prepare`` accept a **repeatable** ``--workstream``
  flag; repeated distinct slugs seed the draft's list in flag order, a
  repeated identical slug is rejected as a duplicate (no silent dedup), no
  flag writes no field, and the prepare/save envelopes are unchanged.
- ``enter --workstream SLUG`` and ``list --workstream SLUG`` accept **exactly
  one** slug (the CLI parser rejects a repeated flag); a valid slug with no
  matching records is an empty scoped view. Scoped payloads are
  ``aitp/enter-0.3``/``aitp/list-0.2`` with one additive top-level singular
  ``workstream: SLUG`` key; without the flag the payloads are byte-identical
  old schemas (``aitp/enter-0.2``/``aitp/list-0.1``).
- Relations run on the full store first: superseded/resolved sets are global,
  so an out-of-scope resolver/superseder still closes/replaces its target
  without reviving old records. The scoped lists, ``unresolved_failures``,
  ``next_action`` (handoff), ``recent_notes``, ``latest_working_note``, Note
  age, and the active/superseded/omitted counts are strictly scoped; an
  out-of-scope handoff is never shown. ``warnings`` and ``counts.malformed``
  stay global.
- ``check`` gains the M1d single-slug ``--workstream`` flag variant
  (``aitp/check-report-0.2``; without the flag ``aitp/check-report-0.1`` is
  byte-unchanged); the validator reports invalid ``workstreams`` as error
  findings. ``show`` is unchanged.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from aitp.core import (
    AITPError,
    atomic_write,
    check_workspace,
    enter_workspace,
    init_workspace,
    list_workspace,
    parse_markdown,
    prepare_entry,
    prepare_note,
    render_markdown,
    save_entry,
    save_note,
    show_entry,
)

REPOSITORY = Path(__file__).resolve().parents[2]
VENDOR = REPOSITORY / "plugins" / "aitp-research-protocol" / "scripts" / "vendor"
GOLDEN = Path(__file__).parent / "fixtures" / "golden"
STORE = GOLDEN / "store"
ROOT_MARKER = "<golden-store>"

ENTRY_BODY = """\
## Durable Summary

Decision summary.

## Decision And Alternatives

The selected alternative is recorded.

## Reason, Scope, And Revisit Condition

Revisit if the check changes.
"""
FAILURE_BODY = """\
## Durable Summary

Failure summary.

## Attempt, Expected, And Observed

The expected behavior was not observed.

## Evidence And Next Diagnostic

Repeat the diagnostic.
"""
NOTE_BODY = """\
## Purpose

Record the current purpose.

## Scope And Basis

The available basis is listed.

## Synthesis

The current synthesis is conditional.

## Evidence Map

The synthesis maps to the basis.

## Uncertainty And Omissions

Further checks remain.

## Open Questions

What changes under the next cutoff?

## Next Actions

Run the next check.
"""
THEORY_BODY = """\
## Question And Obstruction

State the question.

## Setup And Assumptions

State the assumptions.

## Central Construction Or Argument

Give the construction.

## Main Result

State the result.

## Checks, Examples, And Failure Modes

Record the checks.

## Limitations And Open Questions

Record the limitations.
"""
CLOSEOUT_BODY = """\
## Durable Summary

Closeout summary.

## Accomplished And Unresolved

The line is closed.

## Next Action And Resume Refs

Resume refs recorded.
"""


def run_cli(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(VENDOR)
    return subprocess.run(
        [sys.executable, "-m", "aitp", *args],
        cwd=repo,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def copy_store(tmp_path: Path) -> Path:
    root = tmp_path / "store"
    shutil.copytree(STORE, root)
    return root


def golden(name: str) -> dict:
    return json.loads((GOLDEN / name).read_text(encoding="utf-8"))


def normalized(payload: dict) -> dict:
    payload = dict(payload)
    payload["root"] = ROOT_MARKER
    return payload


def initialized(tmp_path: Path, name: str = "project") -> Path:
    root = tmp_path / name
    root.mkdir()
    init_workspace(root, "test", "Test topic")
    return root


def entry_id(char: str) -> str:
    return f"entry-{char * 32}"


def note_id(char: str) -> str:
    return f"note-{char * 32}"


def fake_ref() -> dict[str, str]:
    return {"target": "missing/evidence.md", "at": "sha256:" + "0" * 64, "locator": "whole file"}


def real_ref(root: Path) -> dict[str, str]:
    evidence = root / "evidence.md"
    if not evidence.is_file():
        evidence.write_text("evidence\n", encoding="utf-8")
    digest = hashlib.sha256(evidence.read_bytes()).hexdigest()
    return {"target": "evidence.md", "at": "sha256:" + digest, "locator": "whole file"}


def make_entry(
    root: Path,
    char: str,
    *,
    kind: str = "decision",
    created_at: str = "2026-01-01T00:00:00Z",
    summary: str = "Decision summary.",
    next_action: str = "",
    supersedes: list[str] | None = None,
    resolves: list[str] | None = None,
    workstreams: list[str] | None = None,
    body: str | None = None,
) -> Path:
    prepared = prepare_entry(root, kind, "agent", created_by="agent:test")
    draft = root / prepared["path"]
    frontmatter, _, _ = parse_markdown(draft)
    frontmatter.update(
        {
            "id": entry_id(char),
            "created_at": created_at,
            "summary": summary,
            "refs": [fake_ref()] if kind in {"result", "failure", "source", "code_change", "run"} else [],
            "limitations": ["Test limitation"] if kind in {"observation", "result", "source", "run"} else [],
            "resolves": resolves or [],
            "supersedes": supersedes or [],
            "next_action": next_action,
        }
    )
    if workstreams is not None:
        frontmatter["workstreams"] = list(workstreams)
    body = body if body is not None else (ENTRY_BODY if kind == "decision" else FAILURE_BODY)
    path = root / ".aitp" / "topic" / "entries" / f"{entry_id(char)}.md"
    atomic_write(path, render_markdown(frontmatter, body))
    return path


def make_note(
    root: Path,
    char: str,
    *,
    mode: str = "working",
    created_at: str = "2026-01-01T00:00:00Z",
    title: str = "Working note",
    summary: str = "Working note summary.",
    workstreams: list[str] | None = None,
    basis_refs: list[dict[str, str]] | None = None,
) -> Path:
    prepared = prepare_note(root, mode, title, created_by="agent:test")
    draft = root / prepared["path"]
    frontmatter, _, _ = parse_markdown(draft)
    frontmatter.update(
        {
            "id": note_id(char),
            "created_at": created_at,
            "title": title,
            "summary": summary,
            "basis_refs": basis_refs if basis_refs is not None else [fake_ref()],
            "supersedes": [],
        }
    )
    if workstreams is not None:
        frontmatter["workstreams"] = list(workstreams)
    body = NOTE_BODY if mode == "working" else THEORY_BODY
    path = root / ".aitp" / "topic" / "notes" / f"{note_id(char)}.md"
    atomic_write(path, render_markdown(frontmatter, body))
    return path


def hash_tree(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def fill_goal(root: Path) -> None:
    topic = root / ".aitp" / "topic" / "TOPIC.md"
    frontmatter, body, _ = parse_markdown(topic)
    body = body.replace("Not established yet\n\n## Scope", "Determine the exponents.\n\n## Scope")
    atomic_write(topic, render_markdown(frontmatter, body))


def drafts(root: Path) -> list[Path]:
    return sorted((root / ".aitp" / "local" / "drafts").glob("*.md"))


def test_prepare_flag_seeds_draft(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    prepared = run_cli(root, "record", "prepare", "--kind", "decision", "--created-by", "agent:test",
                       "--workstream", "crpa", "--workstream", "magnetic-symmetry", "--json")
    assert prepared.returncode == 0, prepared.stderr
    payload = json.loads(prepared.stdout)
    assert set(payload) == {"status", "id", "path", "save_command"}
    frontmatter, _, _ = parse_markdown(root / payload["path"])
    assert frontmatter["workstreams"] == ["crpa", "magnetic-symmetry"]
    note = json.loads(run_cli(root, "note", "prepare", "--mode", "working", "--title", "N",
                              "--created-by", "agent:test", "--workstream", "crpa",
                              "--workstream", "magnetic-symmetry", "--json").stdout)
    assert set(note) == {"status", "id", "path", "save_command"}
    frontmatter, _, _ = parse_markdown(root / note["path"])
    assert frontmatter["workstreams"] == ["crpa", "magnetic-symmetry"]
    no_flag = run_cli(root, "record", "prepare", "--kind", "decision", "--created-by", "agent:test", "--json")
    assert no_flag.returncode == 0, no_flag.stderr
    frontmatter, _, _ = parse_markdown(root / json.loads(no_flag.stdout)["path"])
    assert "workstreams" not in frontmatter


def test_prepare_duplicate_slug_rejected_no_draft(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    for command in (
        ("record", "prepare", "--kind", "decision"),
        ("note", "prepare", "--mode", "working", "--title", "N"),
    ):
        before = drafts(root)
        result = run_cli(root, *command, "--created-by", "agent:test",
                         "--workstream", "crpa", "--workstream", "crpa", "--json")
        assert result.returncode == 2, (command, result.stderr)
        payload = json.loads(result.stdout)
        assert payload["code"] == "invalid_workstreams"
        assert payload["message"] == "invalid workstreams: duplicate workstream: crpa"
        assert drafts(root) == before, "no draft may be written"
    with pytest.raises(AITPError) as error:
        prepare_entry(root, "decision", "agent", created_by="agent:test", workstreams=["crpa", "crpa"])
    assert error.value.code == "invalid_workstreams"


def test_prepare_flag_invalid_slug(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    for command in (
        ("record", "prepare", "--kind", "decision"),
        ("note", "prepare", "--mode", "working", "--title", "N"),
    ):
        for bad in ("Bad Slug", "a__b", "UPPER", "", "-lead"):
            before = drafts(root)
            result = run_cli(root, *command, "--created-by", "agent:test", f"--workstream={bad}", "--json")
            assert result.returncode == 2, (command, bad)
            assert json.loads(result.stdout)["code"] == "invalid_workstreams"
            assert drafts(root) == before, "no draft may be written"


def test_save_valid_workstreams(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    prepared = prepare_entry(root, "decision", "agent", created_by="agent:test", workstreams=["crpa", "a-"])
    draft = root / prepared["path"]
    frontmatter, _, _ = parse_markdown(draft)
    frontmatter.update({"summary": "Scoped decision.", "refs": [], "limitations": [],
                        "resolves": [], "supersedes": [], "next_action": ""})
    atomic_write(draft, render_markdown(frontmatter, ENTRY_BODY))
    assert save_entry(root, draft) == {"status": "saved", "path": f".aitp/topic/entries/{frontmatter['id']}.md"}
    saved_fm, _, _ = parse_markdown(root / ".aitp" / "topic" / "entries" / f"{frontmatter['id']}.md")
    # the Topic slug grammar allows a trailing hyphen; M1c reuses it unchanged
    assert saved_fm["workstreams"] == ["crpa", "a-"]
    note = prepare_note(root, "working", "Scoped note", created_by="agent:test", workstreams=["crpa"])
    draft = root / note["path"]
    frontmatter, _, _ = parse_markdown(draft)
    frontmatter.update({"summary": "Scoped note summary.", "basis_refs": [real_ref(root)], "supersedes": []})
    atomic_write(draft, render_markdown(frontmatter, NOTE_BODY))
    assert save_note(root, draft) == {"status": "saved", "path": f".aitp/topic/notes/{frontmatter['id']}.md"}


def test_save_invalid_workstreams(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    cases = (
        ("crpa", "not a list"),
        ([], "empty list"),
        (["", "crpa"], "empty element"),
        (["Bad"], "invalid slug: 'Bad'"),
        (["crpa", "crpa"], "duplicate workstream: crpa"),
    )
    for index, (value, detail) in enumerate(cases):
        char = chr(ord("a") + index)
        path = make_entry(root, char)
        frontmatter, body, _ = parse_markdown(path)
        frontmatter["workstreams"] = value
        atomic_write(path, render_markdown(frontmatter, body))
        draft = root / ".aitp" / "local" / "drafts" / path.name
        shutil.copy(path, draft)
        with pytest.raises(AITPError) as error:
            save_entry(root, draft)
        assert error.value.code == "invalid_workstreams"
        assert str(error.value) == f"invalid workstreams: {detail}"
        note = make_note(root, char)
        frontmatter, body, _ = parse_markdown(note)
        frontmatter["workstreams"] = value
        atomic_write(note, render_markdown(frontmatter, body))
        draft = root / ".aitp" / "local" / "drafts" / note.name
        shutil.copy(note, draft)
        with pytest.raises(AITPError) as error:
            save_note(root, draft)
        assert error.value.code == "invalid_workstreams"
        assert str(error.value) == f"invalid workstreams: {detail}"


def test_unscoped_legacy_valid_and_no_flag_schema_unchanged(tmp_path: Path) -> None:
    root = copy_store(tmp_path)
    assert normalized(list_workspace(root)) == golden("list.json")
    assert normalized(enter_workspace(root)) == golden("enter.json")
    text = run_cli(root, "enter")
    assert text.returncode == 0, text.stderr
    assert text.stdout == (GOLDEN / "enter.txt").read_text(encoding="utf-8")


def mixed_store(root: Path) -> None:
    # e1 unscoped and superseded by e3 (qsgw); e2 (crpa) superseded by e9 (ms)
    make_entry(root, "1", created_at="2026-01-01T00:00:00Z")
    make_entry(root, "2", created_at="2026-01-02T00:00:00Z", workstreams=["crpa"])
    make_entry(root, "3", created_at="2026-01-03T00:00:00Z", supersedes=[entry_id("1")],
               workstreams=["qsgw-semiconductor"])
    make_entry(root, "4", kind="failure", created_at="2026-01-04T00:00:00Z", workstreams=["crpa"])
    make_entry(root, "5", created_at="2026-01-05T00:00:00Z", resolves=[entry_id("4")],
               workstreams=["qsgw-semiconductor"])
    make_entry(root, "6", kind="failure", created_at="2026-01-06T00:00:00Z", workstreams=["magnetic-symmetry"])
    make_entry(root, "7", created_at="2026-01-07T00:00:00Z", next_action="Handoff crpa-ms",
               workstreams=["crpa", "magnetic-symmetry"])
    make_entry(root, "8", created_at="2026-01-08T00:00:00Z", next_action="Handoff qsgw",
               workstreams=["qsgw-semiconductor"])
    make_entry(root, "9", created_at="2026-01-09T00:00:00Z", supersedes=[entry_id("2")],
               workstreams=["magnetic-symmetry"])
    make_note(root, "1", created_at="2026-01-05T12:00:00Z", workstreams=["crpa"])
    make_note(root, "2", created_at="2026-01-06T12:00:00Z")
    make_note(root, "3", mode="theory", created_at="2026-01-07T12:00:00Z", workstreams=["magnetic-symmetry"])
    make_note(root, "4", created_at="2026-01-08T12:00:00Z", workstreams=["magnetic-symmetry"])


def test_scoped_enter_schema_and_post_filter(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    mixed_store(root)
    scoped = enter_workspace(root, workstream="crpa")
    assert scoped["schema"] == "aitp/enter-0.3"
    assert scoped["workstream"] == "crpa"
    assert "workstreams" not in scoped
    # strict exact membership: unscoped e1/n2 never appear, multi-slug e7 is in every of its scopes
    assert [item["id"] for item in scoped["recent_entries"]] == [entry_id("7"), entry_id("4")]
    assert [item["id"] for item in scoped["unresolved_failures"]] == []  # e4 resolved by out-of-scope e5
    assert [item["id"] for item in scoped["recent_notes"]] == [note_id("1")]
    assert scoped["latest_working_note"]["id"] == note_id("1")
    unfiltered = enter_workspace(root)
    assert unfiltered["schema"] == "aitp/enter-0.2"
    assert "workstream" not in unfiltered
    ms = enter_workspace(root, workstream="magnetic-symmetry")
    assert [item["id"] for item in ms["recent_entries"]] == [entry_id("9"), entry_id("7"), entry_id("6")]
    assert [item["id"] for item in ms["recent_notes"]] == [note_id("4"), note_id("3")]
    result = run_cli(root, "enter", "--workstream", "crpa", "--json")
    payload = json.loads(result.stdout)
    assert payload["schema"] == "aitp/enter-0.3"
    assert payload["workstream"] == "crpa"


def test_scoped_enter_counts_global_malformed_and_memory(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    mixed_store(root)
    malformed = root / ".aitp" / "topic" / "notes" / f"{note_id('9')}.md"
    malformed.write_text("not markdown\n", encoding="utf-8")
    unfiltered = enter_workspace(root)
    scoped = enter_workspace(root, workstream="crpa")
    assert scoped["counts"] == {
        "active": 2, "superseded": 1, "unresolved_failures": 0, "malformed": 1,
        "omitted_active": 0, "active_newer_than_latest_working_note": 1,
    }
    assert scoped["memory_status"] == unfiltered["memory_status"] == "partial"
    assert scoped["warnings"] == unfiltered["warnings"]
    assert len(scoped["warnings"]) == 1
    for ws in ("crpa", "magnetic-symmetry", "qsgw-semiconductor", "lone"):
        entered = enter_workspace(root, workstream=ws)
        assert entered["counts"]["malformed"] == 1  # malformed stays global
    ms = enter_workspace(root, workstream="magnetic-symmetry")
    assert ms["counts"]["active"] == 3
    assert ms["counts"]["superseded"] == 0
    assert [item["id"] for item in ms["unresolved_failures"]] == [entry_id("6")]
    assert ms["latest_working_note"]["id"] == note_id("4")
    small = enter_workspace(root, recent=2, workstream="qsgw-semiconductor")
    assert small["counts"]["active"] == 3
    assert small["counts"]["omitted_active"] == 1
    assert [item["id"] for item in small["recent_entries"]] == [entry_id("8"), entry_id("5")]
    lone = enter_workspace(root, workstream="lone")
    assert lone["recent_entries"] == []
    assert lone["unresolved_failures"] == []
    assert lone["recent_notes"] == []
    assert lone["latest_working_note"] is None
    assert lone["counts"]["active"] == 0
    assert lone["counts"]["active_newer_than_latest_working_note"] is None


def test_scoped_enter_handoff_scoped(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    mixed_store(root)
    unfiltered = enter_workspace(root)
    assert unfiltered["next_action"]["entry_id"] == entry_id("8")
    assert enter_workspace(root, workstream="crpa")["next_action"]["entry_id"] == entry_id("7")
    assert enter_workspace(root, workstream="magnetic-symmetry")["next_action"]["entry_id"] == entry_id("7")
    assert enter_workspace(root, workstream="qsgw-semiconductor")["next_action"]["entry_id"] == entry_id("8")
    # a scope with no handoff-bearing active entry gets not_established, never an out-of-scope handoff
    assert enter_workspace(root, workstream="lone")["next_action"] == {"status": "not_established", "source": None}


def test_scoped_list_schema_filter_and_composition(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    mixed_store(root)
    scoped = list_workspace(root, workstream="qsgw-semiconductor")
    assert scoped["schema"] == "aitp/list-0.2"
    assert scoped["workstream"] == "qsgw-semiconductor"
    assert "workstreams" not in scoped
    assert [item["id"] for item in scoped["entries"]] == [entry_id("8"), entry_id("5"), entry_id("3")]
    assert all(item["status"] == "active" for item in scoped["entries"])
    assert scoped["count"] == 3
    crpa = list_workspace(root, workstream="crpa")
    ids = {item["id"]: item["status"] for item in crpa["entries"]}
    assert ids == {entry_id("7"): "active", entry_id("4"): "active", entry_id("2"): "superseded"}
    unfiltered = list_workspace(root)
    assert unfiltered["schema"] == "aitp/list-0.1"
    assert "workstream" not in unfiltered
    assert len(unfiltered["entries"]) == 9
    composed = list_workspace(root, workstream="crpa", kind="failure")
    assert [item["id"] for item in composed["entries"]] == [entry_id("4")]
    since = list_workspace(root, workstream="crpa", since="2026-01-07")
    assert [item["id"] for item in since["entries"]] == [entry_id("7")]
    result = run_cli(root, "list", "--workstream", "crpa", "--kind", "failure", "--json")
    payload = json.loads(result.stdout)
    assert payload["schema"] == "aitp/list-0.2"
    assert payload["workstream"] == "crpa"


def test_scoped_superseded_global(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    mixed_store(root)
    # e2 (crpa) is superseded by e9 (magnetic-symmetry): global superseded set applies
    crpa = list_workspace(root, workstream="crpa")
    status = {item["id"]: item["status"] for item in crpa["entries"]}
    assert status[entry_id("2")] == "superseded"
    assert all(item["id"] != entry_id("2") for item in enter_workspace(root, workstream="crpa")["recent_entries"])
    # e4 (crpa failure) is resolved by e5 (qsgw): the out-of-scope resolver still closes it
    assert enter_workspace(root, workstream="crpa")["unresolved_failures"] == []


def test_read_flag_not_repeatable(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    mixed_store(root)
    for command in (("enter",), ("list",)):
        result = run_cli(root, *command, "--workstream", "crpa", "--workstream", "magnetic-symmetry", "--json")
        assert result.returncode == 2, (command, result.stderr)
        assert "usage:" in result.stderr
        assert "may only be given once" in result.stderr
    # API level: a non-string scope (e.g. an old-style list) is rejected, never a union
    for call in (lambda: enter_workspace(root, workstream=["crpa"]),
                 lambda: list_workspace(root, workstream=["crpa", "magnetic-symmetry"])):
        with pytest.raises(AITPError) as error:
            call()
        assert error.value.code == "invalid_workstreams"
        assert str(error.value) == "invalid workstreams: exactly one slug required"


def test_scoped_text_line(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    mixed_store(root)
    text = run_cli(root, "enter", "--workstream", "magnetic-symmetry")
    assert text.returncode == 0, text.stderr
    lines = text.stdout.splitlines()
    assert lines[0] == "workstream: magnetic-symmetry"
    assert "recent_entries: 3 of 3 active (0 omitted)" in lines
    assert any(line.startswith("recent_notes: 2; latest_working_note: ") for line in lines)
    plain = run_cli(root, "enter")
    assert plain.stdout.splitlines()[0].startswith("topic: ")
    assert "workstream:" not in plain.stdout


def test_check_workstreams_finding_and_global(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    fill_goal(root)
    path = make_entry(root, "a", workstreams=["crpa"])
    frontmatter, body, _ = parse_markdown(path)
    frontmatter["workstreams"] = ["crpa", "crpa"]
    atomic_write(path, render_markdown(frontmatter, body))
    report = check_workspace(root)
    assert report["schema"] == "aitp/check-report-0.1"
    assert report["findings"] == [{
        "level": "error", "code": "invalid_workstreams",
        "path": f".aitp/topic/entries/{entry_id('a')}.md",
        "message": "invalid workstreams: duplicate workstream: crpa",
    }]
    result = run_cli(root, "check", "--json")
    assert result.returncode == 1
    before = run_cli(root, "check", "--json").stdout
    run_cli(root, "enter", "--workstream", "crpa", "--json")
    run_cli(root, "list", "--workstream", "crpa", "--json")
    assert run_cli(root, "check", "--json").stdout == before
    scoped = run_cli(root, "check", "--workstream", "crpa", "--json")
    assert scoped.returncode == 0
    payload = json.loads(scoped.stdout)
    assert payload["schema"] == "aitp/check-report-0.2"
    assert payload["workstream"] == "crpa"
    assert payload["status"] == "clean"
    assert payload["findings"] == []
    assert payload["counts"]["entries"] == 0
    assert payload["counts"]["notes"] == 0
    assert payload["counts"]["by_code"] == {}
    # the store's only record has an invalid workstreams field: unattributable,
    # so the global invalid_workstreams error is carried by the derived delta
    assert payload["counts"]["outside_scope"] == {"errors": 1, "warnings": 0}


def test_cli_misuse_bad_slug(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    for command in (("enter",), ("list",)):
        result = run_cli(root, *command, "--workstream", "Bad", "--json")
        assert result.returncode == 2, command
        payload = json.loads(result.stdout)
        assert payload["code"] == "invalid_workstreams"
        assert payload["message"] == "invalid workstreams: invalid slug: 'Bad'"
    with pytest.raises(AITPError) as error:
        enter_workspace(root, workstream="Bad")
    assert error.value.code == "invalid_workstreams"
    with pytest.raises(AITPError) as error:
        list_workspace(root, workstream="Bad")
    assert error.value.code == "invalid_workstreams"


def test_scoped_read_only_byte_identity_and_determinism(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    mixed_store(root)
    before = hash_tree(root)
    first = run_cli(root, "enter", "--workstream", "crpa", "--json")
    listed = run_cli(root, "list", "--workstream", "crpa", "--json")
    second = run_cli(root, "enter", "--workstream", "crpa", "--json")
    assert first.returncode == listed.returncode == 0
    assert first.stdout == second.stdout
    assert json.loads(listed.stdout)["workstream"] == "crpa"
    assert hash_tree(root) == before
    shown = run_cli(root, "show", entry_id("7"), "--json")
    assert json.loads(shown.stdout)["frontmatter"]["workstreams"] == ["crpa", "magnetic-symmetry"]


def test_invalid_timestamp_warning_order_global_and_scoped(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    # a parses; b/c/d/e are valid Notes whose created_at strings do not parse.
    make_note(root, "a", created_at="2026-01-02T00:00:00Z", workstreams=["crpa"])
    make_note(root, "b", created_at="banana", workstreams=["crpa"])
    make_note(root, "c", created_at="not-a-date", workstreams=["qsgw-semiconductor"])
    make_note(root, "d", created_at="junk")
    make_note(root, "e", created_at="junk", workstreams=["crpa"])
    unfiltered = enter_workspace(root)
    warnings = [w for w in unfiltered["warnings"] if w["code"] == "invalid_timestamp"]
    # pre-scope order: parseable items first (no warning), then unparseable by
    # descending raw created_at with descending-id tiebreak (HEAD behavior)
    assert [w["path"] for w in warnings] == [
        f".aitp/topic/notes/{note_id('c')}.md",
        f".aitp/topic/notes/{note_id('e')}.md",
        f".aitp/topic/notes/{note_id('d')}.md",
        f".aitp/topic/notes/{note_id('b')}.md",
    ]
    assert all(w["message"].startswith("unparseable created_at: ") for w in warnings)
    # warnings stay global and identically ordered in every scoped view
    assert enter_workspace(root, workstream="crpa")["warnings"] == unfiltered["warnings"]
    assert enter_workspace(root, workstream="qsgw-semiconductor")["warnings"] == unfiltered["warnings"]


def test_prepare_api_workstreams_boundary(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    cases = (
        ("crpa", "not a list"),
        (5, "not a list"),
        ([], "empty list"),
        (["Bad"], "invalid slug: 'Bad'"),
        (["crpa", "crpa"], "duplicate workstream: crpa"),
    )
    for value, detail in cases:
        for prepare in (
            lambda: prepare_entry(root, "decision", "agent", created_by="agent:test", workstreams=value),
            lambda: prepare_note(root, "working", "N", created_by="agent:test", workstreams=value),
        ):
            with pytest.raises(AITPError) as error:
                prepare()
            assert error.value.code == "invalid_workstreams"
            assert str(error.value) == f"invalid workstreams: {detail}"
    assert drafts(root) == [], "no draft may be written for any invalid value"


def test_idempotency_hit_still_validates_workstreams(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    first = prepare_entry(root, "decision", "agent", created_by="agent:test", idempotency_key="key-1")
    assert first["status"] == "prepared"
    for bad in ("crpa", [], ["Bad"], ["crpa", "crpa"]):
        with pytest.raises(AITPError) as error:
            prepare_entry(root, "decision", "agent", created_by="agent:test",
                          idempotency_key="key-1", workstreams=bad)
        assert error.value.code == "invalid_workstreams"
    again = prepare_entry(root, "decision", "agent", created_by="agent:test",
                          idempotency_key="key-1", workstreams=["crpa"])
    assert again == {"status": "existing", "path": first["path"], "idempotency_key": "key-1"}


def test_scoped_list_empty_scope(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    mixed_store(root)
    lone = list_workspace(root, workstream="lone")
    assert lone["schema"] == "aitp/list-0.2"
    assert lone["workstream"] == "lone"
    assert lone["count"] == 0
    assert lone["entries"] == []
    assert lone["warnings"] == []
    payload = json.loads(run_cli(root, "list", "--workstream", "lone", "--json").stdout)
    assert payload["schema"] == "aitp/list-0.2"
    assert payload["workstream"] == "lone"
    assert payload["count"] == 0
    assert payload["entries"] == []


def test_scoped_closeout_first_handoff(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    # in-scope closeout (older) beats the newer in-scope decision handoff
    make_entry(root, "c", kind="closeout", created_at="2026-01-20T00:00:00Z",
               next_action="Closeout crpa handoff", workstreams=["crpa"], body=CLOSEOUT_BODY)
    make_entry(root, "d", created_at="2026-01-21T00:00:00Z",
               next_action="Decision crpa handoff", workstreams=["crpa"])
    # out-of-scope closeout (newest, handoff-bearing) never shadows the scope
    make_entry(root, "f", kind="closeout", created_at="2026-01-22T00:00:00Z",
               next_action="Closeout qsgw handoff", workstreams=["qsgw-semiconductor"], body=CLOSEOUT_BODY)
    assert enter_workspace(root, workstream="crpa")["next_action"]["entry_id"] == entry_id("c")
    assert enter_workspace(root, workstream="qsgw-semiconductor")["next_action"]["entry_id"] == entry_id("f")
    assert enter_workspace(root)["next_action"]["entry_id"] == entry_id("f")


def test_slug_length_boundary(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    slug63 = "a" * 63
    prepared = prepare_entry(root, "decision", "agent", created_by="agent:test", workstreams=[slug63])
    frontmatter, _, _ = parse_markdown(root / prepared["path"])
    assert frontmatter["workstreams"] == [slug63]
    entered = enter_workspace(root, workstream=slug63)
    assert entered["schema"] == "aitp/enter-0.3"
    assert entered["workstream"] == slug63
    slug64 = "a" * 64
    with pytest.raises(AITPError) as error:
        prepare_entry(root, "decision", "agent", created_by="agent:test", workstreams=[slug64])
    assert error.value.code == "invalid_workstreams"
    result = run_cli(root, "list", "--workstream", slug64, "--json")
    assert result.returncode == 2
    assert json.loads(result.stdout)["code"] == "invalid_workstreams"
