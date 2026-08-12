from __future__ import annotations

from collections import Counter
from datetime import UTC, date, datetime, timedelta
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
MARKER = "> legacy-derived: recovery orientation only — not re-validated"

ENTRY_BODIES = {
    "decision": """\
## Durable Summary

Decision summary.

## Decision And Alternatives

The selected alternative is recorded.

## Reason, Scope, And Revisit Condition

Revisit if the check changes.
""",
    "result": """\
## Durable Summary

Result summary.

## Basis And Checks

The pinned check was performed.

## Validity And Implication

The result remains conditional.
""",
    "failure": """\
## Durable Summary

Failure summary.

## Attempt, Expected, And Observed

The expected behavior was not observed.

## Evidence And Next Diagnostic

Repeat the diagnostic.
""",
    "closeout": """\
## Durable Summary

Closeout summary.

## Accomplished And Unresolved

The current work is recorded.

## Next Action And Resume Refs

Resume from the next action.
""",
}
NOTE_BODIES = {
    "working": """\
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
""",
    "theory": """\
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
""",
}


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
    payload["root"] = "<golden-store>"
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


def make_entry(
    root: Path,
    char: str,
    *,
    kind: str = "decision",
    created_at: str = "2026-01-01T00:00:00Z",
    summary: str = "Decision summary.",
    next_action: str = "",
    supersedes: list[str] | None = None,
    body: str | None = None,
) -> Path:
    prepared = prepare_entry(root, kind, "agent", created_by="agent:test")
    draft = root / prepared["path"]
    frontmatter, _, _ = parse_markdown(draft)
    needs_refs = kind in {"result", "failure", "source", "code_change", "run"}
    needs_limits = kind in {"observation", "result", "source", "run"}
    frontmatter.update(
        {
            "id": entry_id(char),
            "created_at": created_at,
            "summary": summary,
            "refs": [fake_ref()] if needs_refs else [],
            "limitations": ["Test limitation"] if needs_limits else [],
            "resolves": [],
            "supersedes": supersedes or [],
            "next_action": next_action,
        }
    )
    path = root / ".aitp" / "topic" / "entries" / f"{entry_id(char)}.md"
    atomic_write(path, render_markdown(frontmatter, body or ENTRY_BODIES[kind]))
    return path


def make_note(
    root: Path,
    char: str,
    *,
    mode: str = "working",
    created_at: str = "2026-01-01T00:00:00Z",
    title: str = "Working note",
    summary: str = "Working note summary.",
    body: str | None = None,
    basis_refs: list[dict[str, str]] | None = None,
) -> Path:
    prepared = prepare_note(root, mode, title)
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
    path = root / ".aitp" / "topic" / "notes" / f"{note_id(char)}.md"
    atomic_write(path, render_markdown(frontmatter, body or NOTE_BODIES[mode]))
    return path


def hash_tree(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_list_unfiltered_matches_golden(tmp_path: Path) -> None:
    root = copy_store(tmp_path)
    assert normalized(list_workspace(root)) == golden("list.json")


def test_list_json_field_shape(tmp_path: Path) -> None:
    payload = list_workspace(copy_store(tmp_path))
    assert payload["schema"] == "aitp/list-0.1"
    assert payload["count"] == len(payload["entries"]) == 7
    assert set(payload["entries"][0]) == {
        "id", "kind", "status", "created_at", "authority", "summary", "legacy_derived", "source"
    }
    assert all("…" not in entry["summary"] for entry in payload["entries"])


def test_list_kind_filter(tmp_path: Path) -> None:
    root = copy_store(tmp_path)
    result = run_cli(root, "list", "--kind", "result", "--json")
    assert result.returncode == 0, result.stderr
    assert [item["id"] for item in json.loads(result.stdout)["entries"]] == [
        entry_id("5"), entry_id("4")
    ]
    hyphen = run_cli(root, "list", "--kind", "code-change", "--json")
    underscore = run_cli(root, "list", "--kind", "code_change", "--json")
    assert json.loads(hyphen.stdout) == json.loads(underscore.stdout)
    invalid = run_cli(root, "list", "--kind", "bogus", "--json")
    assert invalid.returncode == 2
    payload = json.loads(invalid.stdout)
    assert payload["code"] == "invalid_kind"
    assert payload["message"] == (
        "unsupported Entry kind: bogus (allowed: observation, result, failure, decision, "
        "source, code_change, run, closeout)"
    )


def test_list_since_inclusive(tmp_path: Path) -> None:
    root = copy_store(tmp_path)
    def ids(value: str) -> list[str]:
        result = run_cli(root, "list", "--since", value, "--json")
        assert result.returncode == 0, result.stderr
        return [item["id"] for item in json.loads(result.stdout)["entries"]]
    assert entry_id("4") in ids("2026-07-03")
    assert entry_id("4") in ids("2026-07-03T09:00:00Z")
    assert entry_id("4") not in ids("2026-07-03T09:00:01Z")
    assert entry_id("4") not in ids("2026-07-04")
    invalid = run_cli(root, "list", "--since", "bogus", "--json")
    assert invalid.returncode == 2
    assert json.loads(invalid.stdout)["code"] == "invalid_since"


def test_list_invalid_timestamp_no_since(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    make_entry(root, "a", created_at="2026-01-02T00:00:00Z")
    make_entry(root, "b", created_at="not-a-date")
    payload = list_workspace(root)
    assert payload["entries"][-1]["id"] == entry_id("b")
    assert payload["entries"][-1]["created_at"] == "not-a-date"
    assert any(w["code"] == "invalid_timestamp" for w in payload["warnings"])


def test_list_invalid_timestamp_with_since(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    make_entry(root, "a", created_at="2026-01-02T00:00:00Z")
    make_entry(root, "b", created_at="not-a-date")
    payload = list_workspace(root, since="2026-01-01")
    assert [item["id"] for item in payload["entries"]] == [entry_id("a")]
    assert any(w["code"] == "invalid_timestamp" for w in payload["warnings"])


def test_list_text_truncation(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    summary = "x" * 120
    make_entry(root, "a", summary=summary)
    text = run_cli(root, "list")
    assert text.returncode == 0, text.stderr
    row = text.stdout.strip()
    assert row.endswith("…")
    assert len(row.split(" ", 4)[4]) == 111
    payload = json.loads(run_cli(root, "list", "--json").stdout)
    assert payload["entries"][0]["summary"] == summary


def test_show_json_matches_golden(tmp_path: Path) -> None:
    root = copy_store(tmp_path)
    payload = show_entry(root, entry_id("4"))
    assert normalized(payload) == golden("show.json")
    assert payload["status"] == "superseded"


def test_show_errors(tmp_path: Path) -> None:
    root = copy_store(tmp_path)
    invalid = run_cli(root, "show", "entry-nope", "--json")
    assert invalid.returncode == 2
    assert json.loads(invalid.stdout) == {
        "status": "error", "code": "invalid_id", "message": "invalid Entry ID"
    }
    missing = run_cli(root, "show", entry_id("d"), "--json")
    assert missing.returncode == 2
    assert json.loads(missing.stdout)["code"] == "entry_not_found"
    text = run_cli(root, "show", "entry-nope")
    assert text.returncode == 2
    assert text.stdout == ""
    assert text.stderr.startswith("error[invalid_id]: invalid Entry ID")
    usage = run_cli(root, "show")
    assert usage.returncode == 2
    assert "usage:" in usage.stderr


def test_enter_v2_closeout_first(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    closeout = make_entry(
        root, "a", kind="closeout", created_at="2026-01-01T00:00:00Z", next_action="X"
    )
    make_entry(
        root, "b", created_at="2026-01-02T00:00:00Z", next_action="Y"
    )
    entered = enter_workspace(root)
    assert entered["next_action"]["text"] == "X"
    assert entered["next_action"]["entry_id"] == entry_id("a")
    make_entry(
        root,
        "c",
        created_at="2026-01-03T00:00:00Z",
        supersedes=[entry_id("a")],
    )
    entered = enter_workspace(root)
    assert entered["next_action"]["text"] == "Y"
    assert closeout.is_file()


def test_enter_v2_closeout_fallback(tmp_path: Path) -> None:
    entered = enter_workspace(copy_store(tmp_path))
    assert entered["next_action"]["entry_id"] == entry_id("7")
    assert entered["schema"] == "aitp/enter-0.2"


def test_enter_v2_note_order(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    make_note(root, "a", created_at="2026-01-02T00:00:00Z", title="new")
    make_note(root, "e", created_at="2026-01-01T00:00:00Z", title="old")
    assert [item["id"] for item in enter_workspace(root)["recent_notes"]] == [
        note_id("a"), note_id("e")
    ]


def test_enter_v2_working_note_age_count(tmp_path: Path) -> None:
    root = initialized(tmp_path, "with-note")
    make_entry(root, "a", created_at="2026-01-03T00:00:00Z")
    make_entry(root, "b", created_at="2026-01-01T00:00:00Z")
    make_note(root, "a", created_at="2026-01-02T00:00:00Z")
    state = enter_workspace(root)
    assert state["counts"]["active_newer_than_latest_working_note"] == 1
    no_note = enter_workspace(initialized(tmp_path, "no-note"))
    assert no_note["latest_working_note"] is None
    assert no_note["counts"]["active_newer_than_latest_working_note"] is None
    invalid_root = initialized(tmp_path, "invalid-note")
    make_note(invalid_root, "a", created_at="not-a-date")
    invalid = enter_workspace(invalid_root)
    assert invalid["latest_working_note"]["created_at"] == "not-a-date"
    assert invalid["counts"]["active_newer_than_latest_working_note"] is None
    zero_root = initialized(tmp_path, "zero-age")
    make_entry(zero_root, "a", created_at="2026-01-01T00:00:00Z")
    make_note(zero_root, "a", created_at="2026-01-02T00:00:00Z")
    assert enter_workspace(zero_root)["counts"]["active_newer_than_latest_working_note"] == 0


def test_enter_v2_legacy_marker(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    exact_body = MARKER + "\n\n" + ENTRY_BODIES["decision"]
    make_entry(root, "a", body=exact_body)
    make_entry(root, "b", body="intro\n" + MARKER + "\n\n" + ENTRY_BODIES["decision"])
    make_entry(root, "c", body="intro\nlegacy-derived: recovery orientation only — not re-validated\n\n" + ENTRY_BODIES["decision"])
    make_entry(root, "d", body="> legacy-derived: recovery orientation only - not re-validated\n\n" + ENTRY_BODIES["decision"])
    make_note(root, "a", body=MARKER + "\n\n" + NOTE_BODIES["working"])
    entered = enter_workspace(root)
    entries = {item["id"]: item for item in entered["recent_entries"]}
    notes = {item["id"]: item for item in entered["recent_notes"]}
    assert entries[entry_id("a")]["legacy_derived"] is True
    assert all(entries[entry_id(char)]["legacy_derived"] is False for char in "bcd")
    assert notes[note_id("a")]["legacy_derived"] is True
    assert list_workspace(root)["entries"][0]["legacy_derived"] is False
    assert list_workspace(root)["entries"][-1]["legacy_derived"] is True
    assert show_entry(root, entry_id("a"))["legacy_derived"] is True


def test_enter_v2_note_read_only_validator(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    make_note(root, "a", basis_refs=[fake_ref()])
    malformed = root / ".aitp" / "topic" / "notes" / f"{note_id('b')}.md"
    malformed.write_text("not markdown\n", encoding="utf-8")
    before = hash_tree(root)
    state = enter_workspace(root)
    after = hash_tree(root)
    assert before == after
    assert note_id("a") in {item["id"] for item in state["recent_notes"]}
    assert state["latest_working_note"]["id"] == note_id("a")
    assert state["counts"]["malformed"] == 1
    assert any(w["path"].endswith(f"{note_id('b')}.md") for w in state["warnings"])


def test_seed_regression_s1_s2(tmp_path: Path) -> None:
    expected = {
        "S1": {
            "entries": 31, "results": 7, "failures": 3, "active": 29,
            "superseded": 2, "omitted": 9, "age": 10,
            "next": "entry-0a210000000000000000000000000000",
        },
        "S2": {
            "entries": 30, "results": 8, "failures": 3, "active": 28,
            "superseded": 2, "omitted": 8, "age": 11,
            "next": "entry-0b200000000000000000000000000000",
        },
    }
    for name, values in expected.items():
        root = tmp_path / name
        shutil.copytree(REPOSITORY / "suite" / "seeds" / name, root)
        before = hash_tree(root)
        listed_proc = run_cli(root, "list", "--json")
        assert listed_proc.returncode == 0, listed_proc.stderr
        listed = json.loads(listed_proc.stdout)
        assert listed["count"] == values["entries"]
        assert listed["warnings"] == []
        assert sum(item["kind"] == "result" for item in listed["entries"]) == values["results"]
        assert sum(item["kind"] == "failure" for item in listed["entries"]) == values["failures"]
        assert sum(item["status"] == "active" for item in listed["entries"]) == values["active"]
        assert sum(item["status"] == "superseded" for item in listed["entries"]) == values["superseded"]
        for kind, count in (("result", values["results"]), ("failure", values["failures"])):
            filtered = run_cli(root, "list", "--kind", kind, "--json")
            assert filtered.returncode == 0, filtered.stderr
            assert json.loads(filtered.stdout)["count"] == count
        entered_proc = run_cli(root, "enter", "--json")
        assert entered_proc.returncode == 0, entered_proc.stderr
        entered = json.loads(entered_proc.stdout)
        assert entered["memory_status"] == "available"
        assert entered["warnings"] == []
        assert entered["counts"] == {
            "active": values["active"], "superseded": values["superseded"],
            "unresolved_failures": 1, "malformed": 0, "omitted_active": values["omitted"],
            "active_newer_than_latest_working_note": values["age"],
        }
        assert len(entered["unresolved_failures"]) == 1
        assert entered["latest_working_note"]["id"] == "note-0a010000000000000000000000000000"
        assert entered["next_action"]["entry_id"] == values["next"]
        if name == "S1":
            shown = run_cli(root, "show", "entry-0a030000000000000000000000000000", "--json")
            assert shown.returncode == 0, shown.stderr
            payload = json.loads(shown.stdout)
            assert payload["frontmatter"]["kind"] == "failure"
            assert payload["status"] == "active"
        assert hash_tree(root) == before


def test_error_payload_compat(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    listing = run_cli(root, "list", "--kind", "bogus", "--json")
    shown = run_cli(root, "show", "entry-nope", "--json")
    assert listing.returncode == shown.returncode == 2
    assert set(json.loads(listing.stdout)) == {"status", "code", "message"}
    assert set(json.loads(shown.stdout)) == {"status", "code", "message"}
    text = run_cli(root, "list", "--kind", "bogus")
    assert text.stdout == ""
    assert text.stderr.startswith("error[invalid_kind]:")


def test_hash_mismatch_message(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    evidence = root / "theory" / "check.md"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text("evidence\n", encoding="utf-8")
    prepared = prepare_entry(root, "result", "agent")
    draft = root / prepared["path"]
    frontmatter, _, _ = parse_markdown(draft)
    frontmatter.update(
        {
            "summary": "A result.",
            "limitations": ["Only a test check."],
            "refs": [{"target": "theory/check.md", "at": "sha256:" + "0" * 64, "locator": "whole file"}],
        }
    )
    atomic_write(draft, render_markdown(frontmatter, ENTRY_BODIES["result"]))
    with pytest.raises(AITPError) as error:
        save_entry(root, draft)
    actual = hashlib.sha256(evidence.read_bytes()).hexdigest()
    assert "expected " + "0" * 64 in str(error.value)
    assert "actual " + actual in str(error.value)


def test_query_scans_each_entry_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = copy_store(tmp_path)
    import aitp.query as query
    original = query.parse_markdown
    calls: list[Path] = []
    def counted(path: Path):
        calls.append(path)
        return original(path)
    monkeypatch.setattr(query, "parse_markdown", counted)
    show_entry(root, entry_id("4"))
    assert len(calls) == 7


def rewrite_frontmatter(path: Path, **updates: object) -> None:
    frontmatter, body, _ = parse_markdown(path)
    frontmatter.update(updates)
    atomic_write(path, render_markdown(frontmatter, body))


def test_nonstring_created_at_is_structural_malformed(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    make_entry(root, "a", created_at=datetime(2026, 1, 1, tzinfo=UTC))
    make_entry(root, "b", created_at=date(2026, 1, 2))
    make_entry(root, "c", created_at=[])
    make_entry(root, "d", created_at={"date": "2026-01-04"})
    listed = run_cli(root, "list", "--json")
    assert listed.returncode == 0, listed.stderr
    payload = json.loads(listed.stdout)
    assert payload["entries"] == []
    assert len(payload["warnings"]) == 4
    assert {warning["code"] for warning in payload["warnings"]} == {"invalid_timestamp"}
    entered = run_cli(root, "enter", "--json")
    assert entered.returncode == 0, entered.stderr
    state = json.loads(entered.stdout)
    assert state["memory_status"] == "partial"
    assert state["counts"]["malformed"] == 4
    assert state["recent_entries"] == []
    shown = run_cli(root, "show", entry_id("a"), "--json")
    assert shown.returncode == 2
    assert json.loads(shown.stdout)["code"] == "invalid_timestamp"
    assert "Traceback" not in shown.stderr


def test_typed_note_is_omitted_with_structural_warning(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    malformed = {
        "a": {"title": []},
        "b": {"created_by": {"agent": "test"}},
        "c": {"created_at": date(2026, 1, 1)},
        "d": {"basis_refs": {"target": "evidence.md"}},
        "e": {"supersedes": "not-a-list"},
    }
    for char, updates in malformed.items():
        path = make_note(root, char)
        rewrite_frontmatter(path, **updates)
    state = enter_workspace(root)
    assert state["recent_notes"] == []
    assert state["latest_working_note"] is None
    assert state["counts"]["malformed"] == len(malformed)
    assert len(state["warnings"]) == len(malformed)
    assert all(warning["code"] in {"invalid_type", "invalid_timestamp", "invalid_refs", "invalid_relation"} for warning in state["warnings"])


def test_show_uses_requested_canonical_target_with_duplicates(tmp_path: Path) -> None:
    malformed_root = initialized(tmp_path, "malformed-target")
    target = make_entry(malformed_root, "a")
    target.write_text("not markdown\n", encoding="utf-8")
    duplicate = make_entry(malformed_root, "b")
    rewrite_frontmatter(duplicate, id=entry_id("a"))
    malformed = run_cli(malformed_root, "show", entry_id("a"), "--json")
    assert malformed.returncode == 2
    assert json.loads(malformed.stdout)["code"] == "malformed_record"
    valid_root = initialized(tmp_path, "valid-target")
    target = make_entry(valid_root, "a")
    duplicate = make_entry(valid_root, "b")
    rewrite_frontmatter(duplicate, id=entry_id("a"))
    valid = run_cli(valid_root, "show", entry_id("a"), "--json")
    assert valid.returncode == 0, valid.stderr
    payload = json.loads(valid.stdout)
    assert payload["source"].endswith(f"{entry_id('a')}.md")
    assert payload["frontmatter"]["id"] == entry_id("a")
    missing_root = initialized(tmp_path, "missing-target")
    duplicate = make_entry(missing_root, "b")
    rewrite_frontmatter(duplicate, id=entry_id("a"))
    missing = run_cli(missing_root, "show", entry_id("a"), "--json")
    assert missing.returncode == 2
    assert json.loads(missing.stdout)["code"] == "entry_not_found"


def test_show_text_preserves_frontmatter_order_lists_and_verbatim_body(tmp_path: Path) -> None:
    root = copy_store(tmp_path)
    api_payload = show_entry(root, entry_id("4"))
    text = run_cli(root, "show", entry_id("4"))
    assert text.returncode == 0, text.stderr
    lines = text.stdout.splitlines()
    assert lines[:4] == [
        f"id: {entry_id('4')}", "status: superseded",
        "source: .aitp/topic/entries/entry-44444444444444444444444444444444.md",
        "legacy_derived: false",
    ]
    start = 4
    keys = list(api_payload["frontmatter"])
    assert [line.split(":", 1)[0] for line in lines[start : start + len(keys)]] == keys
    assert 'refs: [{"target": "theory/check.md"' in text.stdout
    assert text.stdout.endswith(api_payload["body"])
    target = root / api_payload["source"]
    target.write_bytes(target.read_bytes().rstrip(b"\n"))
    no_final_newline = show_entry(root, entry_id("4"))
    text = run_cli(root, "show", entry_id("4"))
    assert text.stdout.endswith(no_final_newline["body"])
    assert not text.stdout.endswith(no_final_newline["body"] + "\n")


def test_list_text_warning_stream_whitespace_boundary_and_legacy_label(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    make_entry(root, "a", summary="  alpha \n beta\t gamma  ")
    make_entry(root, "b", summary="x" * 110)
    make_entry(root, "c", summary="y" * 111)
    make_entry(root, "d", created_at="not-a-date", summary="invalid")
    make_entry(root, "e", body=MARKER + "\n\n" + ENTRY_BODIES["decision"])
    result = run_cli(root, "list")
    assert result.returncode == 0, result.stderr
    rows = {line.split()[1]: line for line in result.stdout.splitlines()}
    assert "alpha beta gamma" in rows[entry_id("a")]
    assert rows[entry_id("b")].endswith("x" * 110)
    assert rows[entry_id("c")].endswith("y" * 110 + "…")
    assert f"{entry_id('e')} decision active legacy-derived" in rows[entry_id("e")]
    assert "warning[invalid_timestamp]:" in result.stderr
    assert "warning[invalid_timestamp]:" not in result.stdout


def test_read_validators_do_not_call_evidence_or_write_hooks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = initialized(tmp_path)
    make_entry(root, "a")
    make_entry(root, "b")
    make_note(root, "a")
    make_note(root, "b", mode="theory")
    import aitp.notes as notes
    import aitp.query as query
    import aitp.state as state
    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("read path invoked a save/evidence hook")
    monkeypatch.setattr(notes, "validate_refs", fail)
    monkeypatch.setattr(notes, "store_lock", fail)
    monkeypatch.setattr(notes, "atomic_write", fail)
    query_calls: list[Path] = []
    state_calls: list[Path] = []
    query_parse = query.parse_markdown
    state_parse = state.parse_markdown
    def count_query(path: Path):
        query_calls.append(path)
        return query_parse(path)
    def count_state(path: Path):
        state_calls.append(path)
        return state_parse(path)
    monkeypatch.setattr(query, "parse_markdown", count_query)
    monkeypatch.setattr(state, "parse_markdown", count_state)
    entries = sorted((root / ".aitp/topic/entries").glob("entry-*.md"))
    notes_paths = sorted((root / ".aitp/topic/notes").glob("note-*.md"))
    list_workspace(root)
    assert Counter(query_calls) == Counter(entries)
    query_calls.clear()
    show_entry(root, entry_id("a"))
    assert Counter(query_calls) == Counter(entries)
    query_calls.clear()
    enter_workspace(root)
    assert Counter(query_calls) == Counter(entries)
    assert Counter(path for path in state_calls if path in notes_paths) == Counter(notes_paths)


def test_parse_time_offsets_tie_break_and_marker_variations(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    make_entry(root, "a", created_at="2026-01-01T02:00:00+02:00")
    make_entry(root, "b", created_at="2026-01-01T00:00:01Z")
    make_entry(root, "c", created_at="2026-01-01T00:00:00Z")
    make_entry(root, "d", created_at="2025-12-31T00:00:00Z", body="intro\n" + MARKER + "\n\n" + ENTRY_BODIES["decision"])
    listed = list_workspace(root)
    assert [item["id"] for item in listed["entries"][:3]] == [entry_id("b"), entry_id("c"), entry_id("a")]
    assert listed["entries"][3]["legacy_derived"] is False


def test_sort_key_contract_and_invalid_order(tmp_path: Path) -> None:
    from aitp.query import _sort_key

    valid_time = datetime.fromisoformat("2026-01-01T00:00:00+00:00")
    assert _sort_key("2026-01-01T00:00:00Z", entry_id("a")) == (
        0, valid_time, entry_id("a")
    )
    assert _sort_key("not-a-date", entry_id("b")) == (
        1, "not-a-date", entry_id("b")
    )
    root = initialized(tmp_path)
    make_entry(root, "a", created_at="2026-01-01T00:00:00Z")
    make_entry(root, "c", created_at="2026-01-01T00:00:00Z")
    make_entry(root, "b", created_at="not-a-date")
    assert [item["id"] for item in list_workspace(root)["entries"]] == [
        entry_id("c"), entry_id("a"), entry_id("b")
    ]


def test_enter_entry_projection_key_order(tmp_path: Path) -> None:
    root = copy_store(tmp_path)
    expected = [
        "id", "kind", "summary", "limitations", "authority", "created_at",
        "refs", "source", "legacy_derived",
    ]
    result = run_cli(root, "enter", "--json")
    assert result.returncode == 0, result.stderr
    assert list(json.loads(result.stdout)["recent_entries"][0]) == expected
    entry = json.loads(result.stdout)["recent_entries"][0]
    text = run_cli(root, "enter")
    assert text.returncode == 0, text.stderr
    line = next(line for line in text.stdout.splitlines() if line.startswith("  "))
    assert line == f"  {entry['created_at']} {entry['id']} {entry['kind']} {entry['summary']}"


def test_read_commands_load_store_metadata_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = copy_store(tmp_path)
    import aitp.notes as notes
    import aitp.query as query
    import aitp.records as records
    import aitp.state as state

    modules = {"notes": notes, "query": query, "records": records, "state": state}
    calls = {name: 0 for name in modules}
    for name, module in modules.items():
        original = module.load_store
        def counted(*args, _name=name, _original=original, **kwargs):
            calls[_name] += 1
            return _original(*args, **kwargs)
        monkeypatch.setattr(module, "load_store", counted)

    for operation, expected in (
        (lambda: list_workspace(root), {"notes": 0, "query": 1, "records": 0, "state": 0}),
        (lambda: show_entry(root, entry_id("4")), {"notes": 0, "query": 1, "records": 0, "state": 0}),
        (lambda: enter_workspace(root), {"notes": 0, "query": 0, "records": 0, "state": 1}),
    ):
        for name in calls:
            calls[name] = 0
        operation()
        assert calls == expected


def test_save_note_still_validates_basis_refs(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    prepared = prepare_note(root, "working", "Evidence")
    draft = root / prepared["path"]
    frontmatter, _, _ = parse_markdown(draft)
    evidence = root / "evidence.md"
    evidence.write_text("evidence\n", encoding="utf-8")
    cases = (
        ([fake_ref()], "missing_ref"),
        ([{"target": "evidence.md", "at": "sha256:" + "0" * 64, "locator": "whole file"}], "hash_mismatch"),
    )
    for basis_refs, code in cases:
        frontmatter.update({"summary": "Evidence note.", "basis_refs": basis_refs})
        atomic_write(draft, render_markdown(frontmatter, NOTE_BODIES["working"]))
        with pytest.raises(AITPError) as error:
            save_note(root, draft)
        assert error.value.code == code
