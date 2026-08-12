"""M1b-R1 diagnostics: `aitp check` contracts and the compact `enter` text.

The CLI/exit-code contracts use the ``run_cli`` helper; API payloads are
checked test_golden-style.  Existing test files are not modified (except
``test_enter_entry_projection_key_order`` in ``test_query.py``, whose text
assertion asserted the pre-R1 generic renderer and now asserts the frozen
compact line).
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
    init_workspace,
    parse_markdown,
    prepare_entry,
    prepare_note,
    render_markdown,
    save_entry,
    save_note,
)

REPOSITORY = Path(__file__).resolve().parents[2]
VENDOR = REPOSITORY / "plugins" / "aitp-research-protocol" / "scripts" / "vendor"
FIXTURES = Path(__file__).parent / "fixtures" / "golden"
STORE = FIXTURES / "store"
ROOT_MARKER = "<golden-store>"

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


def golden(name: str):
    if name.endswith(".json"):
        return json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return (FIXTURES / name).read_text(encoding="utf-8")


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


def pinned_file(root: Path, relative: str, text: str = "evidence\n") -> dict[str, str]:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return {
        "target": relative,
        "at": f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}",
        "locator": "whole file",
    }


def rewrite_frontmatter(path: Path, **updates: object) -> None:
    frontmatter, body, _ = parse_markdown(path)
    frontmatter.update(updates)
    atomic_write(path, render_markdown(frontmatter, body))


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
    refs: list[dict[str, str]] | None = None,
    limitations: list[str] | None = None,
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
            "refs": refs if refs is not None else ([fake_ref()] if needs_refs else []),
            "limitations": limitations if limitations is not None else (["Test limitation"] if needs_limits else []),
            "resolves": resolves or [],
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
    supersedes: list[str] | None = None,
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
            "supersedes": supersedes or [],
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


def fill_goal(root: Path, text: str) -> None:
    topic = root / ".aitp" / "topic" / "TOPIC.md"
    frontmatter, body, _ = parse_markdown(topic)
    body = body.replace("Not established yet\n\n## Scope", f"{text}\n\n## Scope")
    atomic_write(topic, render_markdown(frontmatter, body))


def test_check_golden_matches(tmp_path: Path) -> None:
    root = copy_store(tmp_path)
    assert normalized(check_workspace(root)) == golden("check.json")
    result = run_cli(root, "check", "--json")
    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "findings"


def test_check_clean_exit_zero(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    fill_goal(root, "Determine the critical exponents.")
    payload = check_workspace(root)
    assert payload["status"] == "clean"
    assert payload["counts"] == {"entries": 0, "notes": 0, "errors": 0, "warnings": 0}
    assert payload["findings"] == []
    result = run_cli(root, "check")
    assert result.returncode == 0
    assert result.stdout == "check: 0 error(s), 0 warning(s)\n"


def test_check_cannot_run(tmp_path: Path) -> None:
    plain = run_cli(tmp_path, "check", "--json")
    assert plain.returncode == 2
    payload = json.loads(plain.stdout)
    assert payload["code"] == "not_initialized"
    assert payload["message"] == f"no AITP store at {tmp_path.resolve()}"
    assert set(payload) == {"status", "code", "message"}
    missing = run_cli(tmp_path, "check", "--json", "--cwd", str(tmp_path / "nope"))
    assert missing.returncode == 2
    assert json.loads(missing.stdout)["code"] == "invalid_root"
    root = initialized(tmp_path)
    store = root / ".aitp" / "STORE.toml"
    store.write_bytes(b"\xff\xfe\x00bad")
    malformed = run_cli(root, "check", "--json")
    assert malformed.returncode == 2
    payload = json.loads(malformed.stdout)
    assert payload["code"] == "malformed_store"
    assert payload["message"].startswith(f"store metadata is unreadable: {store}: ")
    store.write_text('schema = "aitp/lite-store-0.1"\n', encoding="utf-8")
    store.chmod(0)
    if os.access(store, os.R_OK):
        store.chmod(0o644)
        pytest.skip("cannot simulate an unreadable STORE.toml as root")
    blocked = run_cli(root, "check", "--json")
    assert blocked.returncode == 2
    assert json.loads(blocked.stdout)["code"] == "malformed_store"
    store.chmod(0o644)


def test_check_malformed_error(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    fill_goal(root, "Determine the exponents.")
    make_entry(root, "a")
    bad = root / ".aitp" / "topic" / "entries" / f"{entry_id('b')}.md"
    bad.write_text("not markdown\n", encoding="utf-8")
    yaml_bad = root / ".aitp" / "topic" / "entries" / f"{entry_id('c')}.md"
    yaml_bad.write_text("---\nid: [unclosed\n---\n\nbody\n", encoding="utf-8")
    payload = check_workspace(root)
    assert payload["counts"]["entries"] == 3
    assert {finding["code"] for finding in payload["findings"]} == {"malformed_record"}
    result = run_cli(root, "check")
    assert result.returncode == 1
    assert result.stdout.count("error[malformed_record]:") == 2
    assert "Traceback" not in result.stdout + result.stderr


def test_check_utf8_unreadable(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    make_entry(root, "a")
    bad = root / ".aitp" / "topic" / "entries" / f"{entry_id('b')}.md"
    bad.write_bytes(b"\xff\xff\xff\xff\n")
    topic = root / ".aitp" / "topic" / "TOPIC.md"
    topic.write_bytes(b"---\nid: nio\n\xff\xfe\x00")
    result = run_cli(root, "check", "--json")
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    unreadable = [finding for finding in payload["findings"] if finding["code"] == "unreadable_record"]
    assert len(unreadable) == 2
    assert {finding["path"] for finding in unreadable} == {
        f".aitp/topic/entries/{entry_id('b')}.md",
        ".aitp/topic/TOPIC.md",
    }
    assert all(finding["level"] == "error" for finding in unreadable)
    assert "Traceback" not in result.stdout + result.stderr


def test_check_structural_error(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    fill_goal(root, "Determine the exponents.")
    make_entry(root, "a")
    missing = make_entry(root, "b")
    frontmatter, body, _ = parse_markdown(missing)
    del frontmatter["authority"]
    atomic_write(missing, render_markdown(frontmatter, body))
    rewrite_frontmatter(make_entry(root, "c"), kind="bogus")
    rewrite_frontmatter(make_entry(root, "d"), summary="")
    template = make_entry(root, "e")
    frontmatter, body, _ = parse_markdown(template)
    atomic_write(template, render_markdown(frontmatter, body + "<!-- aitp:fill -->\n"))
    empty = make_entry(root, "f")
    frontmatter, body, _ = parse_markdown(empty)
    atomic_write(empty, render_markdown(frontmatter, body.replace("Decision summary.", "")))
    payload = check_workspace(root)
    assert {finding["code"] for finding in payload["findings"]} == {
        "missing_field", "invalid_kind", "missing_summary", "unfilled_template", "empty_section",
    }
    assert payload["counts"]["entries"] == 6
    result = run_cli(root, "check")
    assert result.returncode == 1
    assert result.stdout.count("error[") == 5


def test_check_duplicate_error(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    fill_goal(root, "Determine the exponents.")
    make_entry(root, "a")
    second = make_entry(root, "b")
    rewrite_frontmatter(second, id=entry_id("a"))
    payload = check_workspace(root)
    assert payload["findings"] == [{
        "level": "error", "code": "duplicate_id",
        "path": f".aitp/topic/entries/{entry_id('b')}.md",
        "message": f"duplicate Entry ID: {entry_id('a')}",
    }]
    root2 = initialized(tmp_path, "notes")
    make_note(root2, "a", basis_refs=[pinned_file(root2, "theory/evidence.md")])
    second_note = make_note(root2, "b", basis_refs=[pinned_file(root2, "theory/evidence.md")])
    rewrite_frontmatter(second_note, id=note_id("a"))
    payload = check_workspace(root2)
    duplicates = [finding for finding in payload["findings"] if finding["code"] == "duplicate_id"]
    assert len(duplicates) == 1
    assert duplicates[0]["path"] == f".aitp/topic/notes/{note_id('b')}.md"
    assert duplicates[0]["message"] == f"duplicate Note ID: {note_id('a')}"


def test_check_counts_per_file(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    make_entry(root, "a")
    make_entry(root, "b", created_at="not-a-date")
    malformed = root / ".aitp" / "topic" / "entries" / f"{entry_id('c')}.md"
    malformed.write_text("not markdown\n", encoding="utf-8")
    make_note(root, "a", basis_refs=[pinned_file(root, "notes-evidence.md")])
    bad_note = root / ".aitp" / "topic" / "notes" / f"{note_id('b')}.md"
    bad_note.write_text("not markdown\n", encoding="utf-8")
    make_note(root, "c", basis_refs=[pinned_file(root, "notes-evidence.md")], created_at="not-a-date")
    payload = check_workspace(root)
    assert payload["counts"]["entries"] == 3
    assert payload["counts"]["notes"] == 3
    assert payload["status"] == "findings"


def test_check_pin_matrix(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = initialized(tmp_path)
    (root / "data" / "dir").mkdir(parents=True)
    (root / "blocked.dat").write_text("x\n", encoding="utf-8")
    (root / "runs" / "out").mkdir(parents=True)
    (root / "runs" / "out" / "x").write_text("x\n", encoding="utf-8")
    wrong = pinned_file(root, "theory/check.md")
    wrong["at"] = "sha256:" + "0" * 64
    original_read = Path.read_bytes

    def denied(self, *args, **kwargs):
        if str(self).endswith("blocked.dat"):
            raise OSError("simulated unreadable")
        return original_read(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_bytes", denied)
    cases = [
        ("a", {"target": "missing/evidence.md", "at": "sha256:" + "0" * 64}, "missing_ref"),
        ("b", {"target": "data/dir", "at": "sha256:" + "0" * 64}, "unreadable_ref"),
        ("c", {"target": "blocked.dat", "at": "sha256:" + "0" * 64}, "unreadable_ref"),
        ("d", wrong, "hash_mismatch"),
        ("e", {"target": "https://example.com/x", "at": "git:abc123"}, "invalid_git_ref"),
        ("f", {"target": "theory/check.md", "at": "git:abc123"}, "invalid_git_ref"),
        ("1", {"target": "runs/out", "at": "run:runs/out"}, "invalid_run_ref"),
        ("2", {"target": "theory/check.md", "at": "version:1.0"}, "invalid_version_ref"),
        ("3", {"target": "arxiv:1234", "at": "retrieved:2026-01-01T00:00:00Z"}, "invalid_retrieved_ref"),
        ("4", {"target": "theory/check.md", "at": "bogus:xyz"}, "invalid_ref_pin"),
        ("5", {"target": "../escape.md", "at": "sha256:" + "0" * 64}, "ref_escape"),
    ]
    for char, ref, _ in cases:
        make_entry(root, char, kind="result", refs=[ref], limitations=["L"])
    payload = check_workspace(root)
    codes = {finding["code"] for finding in payload["findings"]}
    assert {code for _, _, code in cases} <= codes
    unreadable = [finding for finding in payload["findings"] if finding["code"] == "unreadable_ref"]
    assert {finding["message"] for finding in unreadable} == {
        "reference target is not a file: data/dir",
        "reference target is unreadable: blocked.dat: simulated unreadable",
    }
    git = [finding for finding in payload["findings"] if finding["code"] == "invalid_git_ref"]
    assert {finding["level"] for finding in git} == {"error", "warning"}
    warnings = [finding for finding in git if finding["level"] == "warning"]
    assert len(warnings) == 1
    assert warnings[0]["path"] == f".aitp/topic/entries/{entry_id('f')}.md"
    repo_root = initialized(tmp_path, "repo")
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A"], cwd=repo_root, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "seed"], cwd=repo_root, check=True)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_root, capture_output=True, text=True, check=True).stdout.strip()
    make_entry(repo_root, "a", kind="result",
               refs=[{"target": "never-committed.md", "at": f"git:{commit}", "locator": "whole file"}],
               limitations=["L"])
    payload = check_workspace(repo_root)
    git = [finding for finding in payload["findings"] if finding["code"] == "invalid_git_ref"]
    assert len(git) == 1
    assert git[0]["level"] == "error"
    assert git[0]["message"] == f"Git ref does not contain target: never-committed.md@{commit}"


def test_check_multiref_first_failure(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    (root / "runs").mkdir()
    (root / "runs" / "out").write_text("x\n", encoding="utf-8")
    refs = [
        {"target": "https://example.com/x", "at": "git:abc123", "locator": "whole file"},
        {"target": "runs/out", "at": "run:runs/out", "locator": "whole file"},
        {"target": "missing/evidence.md", "at": "sha256:" + "0" * 64, "locator": "whole file"},
    ]
    make_entry(root, "a", kind="result", refs=refs, limitations=["L"])
    payload = check_workspace(root)
    ref_findings = [finding for finding in payload["findings"]
                    if finding["path"].endswith(f"{entry_id('a')}.md")]
    assert [finding["code"] for finding in ref_findings] == [
        "invalid_git_ref", "invalid_run_ref", "missing_ref",
    ]
    assert ref_findings[0]["message"] == "Git ref does not contain target: https://example.com/x@abc123"
    prepared = prepare_entry(root, "result", "agent", created_by="agent:test")
    draft = root / prepared["path"]
    frontmatter, _, _ = parse_markdown(draft)
    frontmatter.update({"summary": "A result.", "limitations": ["L"], "refs": refs})
    atomic_write(draft, render_markdown(frontmatter, ENTRY_BODIES["result"]))
    with pytest.raises(AITPError) as error:
        save_entry(root, draft)
    assert error.value.code == "invalid_git_ref"
    assert str(error.value) == "Git ref does not contain target: https://example.com/x@abc123"


def test_check_relation_failure_skips_refs_same_record(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    fill_goal(root, "Determine the exponents.")
    make_entry(root, "a", kind="decision", refs=[fake_ref()], resolves=[entry_id("zz")])
    make_entry(root, "b", kind="decision", refs=[fake_ref()])
    payload = check_workspace(root)
    a_path = f".aitp/topic/entries/{entry_id('a')}.md"
    b_path = f".aitp/topic/entries/{entry_id('b')}.md"
    assert {(finding["path"], finding["code"]) for finding in payload["findings"]} == {
        (a_path, "missing_relation"),
        (b_path, "missing_ref"),
    }
    relation = next(finding for finding in payload["findings"] if finding["path"] == a_path)
    assert relation["level"] == "error"
    assert relation["message"] == f"resolves target does not exist: {entry_id('zz')}"
    ref_only = next(finding for finding in payload["findings"] if finding["path"] == b_path)
    assert ref_only["level"] == "error"
    assert ref_only["message"] == "reference target does not exist: missing/evidence.md"
    first = run_cli(root, "check", "--json")
    second = run_cli(root, "check", "--json")
    assert first.returncode == second.returncode == 1
    assert first.stdout == second.stdout


def test_check_git_env_warning(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    refs = [{"target": "theory/check.md", "at": "git:abc123", "locator": "whole file"}]
    make_entry(root, "a", kind="result", refs=refs, limitations=["L"])
    result = run_cli(root, "check", "--json")
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    finding = [finding for finding in payload["findings"] if finding["code"] == "invalid_git_ref"]
    assert len(finding) == 1
    assert finding[0]["level"] == "warning"
    assert finding[0]["message"] == "Git ref does not contain target: theory/check.md@abc123"
    prepared = prepare_entry(root, "result", "agent", created_by="agent:test")
    draft = root / prepared["path"]
    frontmatter, _, _ = parse_markdown(draft)
    frontmatter.update({"summary": "A result.", "limitations": ["L"], "refs": refs})
    atomic_write(draft, render_markdown(frontmatter, ENTRY_BODIES["result"]))
    saved = run_cli(root, "record", "save", prepared["path"], "--json")
    assert saved.returncode == 2
    payload = json.loads(saved.stdout)
    assert payload == {
        "status": "error", "code": "invalid_git_ref",
        "message": "Git ref does not contain target: theory/check.md@abc123",
    }


def test_check_invalid_timestamp_warning(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    fill_goal(root, "Determine the exponents.")
    make_entry(root, "a", created_at="+now+")
    payload = check_workspace(root)
    timestamp = [finding for finding in payload["findings"] if finding["code"] == "invalid_timestamp"]
    assert len(timestamp) == 1
    assert timestamp[0]["level"] == "warning"
    assert timestamp[0]["message"] == "unparseable created_at: +now+"
    assert payload["counts"]["entries"] == 1
    result = run_cli(root, "check")
    assert result.returncode == 1
    assert "warning[invalid_timestamp]: " in result.stdout
    assert "check: 0 error(s), 1 warning(s)" in result.stdout
    listed = run_cli(root, "list", "--json")
    assert listed.returncode == 0


def test_check_empty_goal_warning(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    payload = check_workspace(root)
    goal = [finding for finding in payload["findings"] if finding["code"] == "empty_topic_goal"]
    assert goal == [{
        "level": "warning", "code": "empty_topic_goal",
        "path": ".aitp/topic/TOPIC.md", "message": "Research Goal is not established",
    }]
    empty = initialized(tmp_path, "empty")
    topic = empty / ".aitp" / "topic" / "TOPIC.md"
    frontmatter, body, _ = parse_markdown(topic)
    atomic_write(topic, render_markdown(frontmatter, body.replace("Not established yet\n\n## Scope", "\n\n## Scope")))
    assert any(f["code"] == "empty_topic_goal" for f in check_workspace(empty)["findings"])
    missing = initialized(tmp_path, "missing")
    topic = missing / ".aitp" / "topic" / "TOPIC.md"
    frontmatter, body, _ = parse_markdown(topic)
    atomic_write(topic, render_markdown(frontmatter, body.replace("## Research Goal\n\nNot established yet\n\n", "")))
    assert any(f["code"] == "empty_topic_goal" for f in check_workspace(missing)["findings"])
    filled = initialized(tmp_path, "filled")
    fill_goal(filled, "Determine the exponents.")
    assert check_workspace(filled)["status"] == "clean"


def test_check_note_rules(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    make_note(root, "a", basis_refs=[])
    malformed = root / ".aitp" / "topic" / "notes" / f"{note_id('b')}.md"
    malformed.write_text("not markdown\n", encoding="utf-8")
    make_note(root, "c", basis_refs=[pinned_file(root, "theory/evidence.md")])
    drifted = pinned_file(root, "theory/evidence.md")
    drifted["at"] = "sha256:" + "0" * 64
    make_note(root, "d", basis_refs=[drifted])
    make_note(root, "f", basis_refs=[pinned_file(root, "theory/evidence.md")])
    make_note(root, "e", supersedes=[note_id("f")],
              basis_refs=[pinned_file(root, "theory/evidence.md")])
    payload = check_workspace(root)
    codes = {finding["code"] for finding in payload["findings"]}
    assert "malformed_record" in codes
    missing_refs = [finding for finding in payload["findings"] if finding["code"] == "missing_refs"]
    assert len(missing_refs) == 1
    assert missing_refs[0]["message"] == "Note requires nonempty basis_refs"
    hash_mismatch = [finding for finding in payload["findings"] if finding["code"] == "hash_mismatch"]
    assert len(hash_mismatch) == 1
    assert hash_mismatch[0]["path"] == f".aitp/topic/notes/{note_id('d')}.md"
    assert not any(finding["path"].endswith(f"{note_id('e')}.md") for finding in payload["findings"])


def test_check_deterministic_order(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    make_entry(root, "a")
    make_entry(root, "b", created_at="not-a-date")
    make_entry(root, "c", kind="result", refs=[fake_ref()], limitations=["L"])
    fill_goal(root, "Filled.")
    first = run_cli(root, "check", "--json")
    second = run_cli(root, "check", "--json")
    assert first.returncode == second.returncode == 1
    assert first.stdout == second.stdout
    payload = json.loads(first.stdout)
    assert sorted(payload) == ["counts", "findings", "root", "schema", "status"]
    assert payload["findings"] == sorted(payload["findings"], key=lambda f: (f["path"], f["code"], f["message"]))
    assert all(finding["level"] in {"error", "warning"} and finding["code"] and finding["message"]
               for finding in payload["findings"])


def test_check_read_only_byte_identity(tmp_path: Path) -> None:
    root = copy_store(tmp_path)
    before = hash_tree(root)
    result = run_cli(root, "check", "--json")
    assert result.returncode == 1
    assert not (root / ".aitp" / "local" / "locks" / "write.lock").exists()
    text = run_cli(root, "check")
    assert text.returncode == 1
    assert hash_tree(root) == before


def test_enter_text_compact(tmp_path: Path) -> None:
    root = copy_store(tmp_path)
    result = run_cli(root, "enter")
    assert result.returncode == 0, result.stderr
    assert result.stdout == golden("enter.txt")
    lines = result.stdout.splitlines()
    assert "recent_entries: 6 of 6 active (0 omitted)" in lines
    assert any(line.startswith("recent_notes: 2; latest_working_note: note-11111111111111111111111111111111 @ ")
               and line.endswith("; active_newer: 0") for line in lines)
    assert not any(line.startswith("handoff_status") for line in lines)
    assert not any(line.startswith("warnings:") for line in lines)
    assert not any(line.startswith(("refs", "limitations", "schema", "root")) for line in lines)
    review = initialized(tmp_path, "review")
    make_entry(review, "a", kind="decision", created_at="2026-01-01T00:00:00Z", next_action="Check X.")
    make_entry(review, "b", kind="failure", created_at="2026-01-02T00:00:00Z")
    text = run_cli(review, "enter")
    assert "handoff_status: review" in text.stdout
    older = initialized(tmp_path, "older")
    make_entry(older, "a", kind="decision", created_at="2026-01-02T00:00:00Z", next_action="Check X.")
    make_entry(older, "b", kind="failure", created_at="2026-01-01T00:00:00Z")
    text = run_cli(older, "enter")
    assert "handoff_status: review" not in text.stdout
    empty_goal = initialized(tmp_path, "empty-goal")
    topic = empty_goal / ".aitp" / "topic" / "TOPIC.md"
    frontmatter, body, _ = parse_markdown(topic)
    atomic_write(topic, render_markdown(frontmatter, body.replace("Not established yet\n\n## Scope", "\n\n## Scope")))
    assert "goal_status: not_established" in run_cli(empty_goal, "enter").stdout
    missing_goal = initialized(tmp_path, "missing-goal")
    topic = missing_goal / ".aitp" / "topic" / "TOPIC.md"
    frontmatter, body, _ = parse_markdown(topic)
    atomic_write(topic, render_markdown(frontmatter, body.replace("## Research Goal\n\nNot established yet\n\n", "")))
    assert "goal_status: not_established" in run_cli(missing_goal, "enter").stdout
    filled_goal = initialized(tmp_path, "filled-goal")
    fill_goal(filled_goal, "Determine the exponents.")
    text = run_cli(filled_goal, "enter")
    assert "goal: Determine the exponents." in text.stdout
    assert "goal_status:" not in text.stdout
    no_note = initialized(tmp_path, "no-note")
    make_entry(no_note, "a")
    assert "; active_newer: unknown" in run_cli(no_note, "enter").stdout
    warn = initialized(tmp_path, "warn")
    make_entry(warn, "a", created_at="not-a-date")
    assert 'warnings: 1 (run "aitp check" for details)' in run_cli(warn, "enter").stdout
    first = run_cli(root, "enter", "--json")
    second = run_cli(root, "enter", "--json")
    assert first.stdout == second.stdout
    assert json.loads(first.stdout)["schema"] == "aitp/enter-0.2"


def test_save_envelope_exact(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    ref = pinned_file(root, "theory/check.md")
    prepared = prepare_entry(root, "result", "agent", created_by="agent:test")
    assert set(prepared) == {"status", "id", "path", "save_command"}
    draft = root / prepared["path"]
    frontmatter, _, _ = parse_markdown(draft)
    frontmatter.update({"summary": "A result.", "limitations": ["L"], "refs": [ref]})
    atomic_write(draft, render_markdown(frontmatter, ENTRY_BODIES["result"]))
    path = f".aitp/topic/entries/{prepared['id']}.md"
    assert save_entry(root, draft) == {"status": "saved", "path": path}
    assert save_entry(root, draft) == {"status": "already_saved", "path": path}
    note_prepared = prepare_note(root, "working", "Evidence", created_by="agent:test")
    assert set(note_prepared) == {"status", "id", "path", "save_command"}
    note_draft = root / note_prepared["path"]
    frontmatter, _, _ = parse_markdown(note_draft)
    frontmatter.update({"summary": "Evidence note.", "basis_refs": [ref]})
    atomic_write(note_draft, render_markdown(frontmatter, NOTE_BODIES["working"]))
    note_path = f".aitp/topic/notes/{note_prepared['id']}.md"
    assert save_note(root, note_draft) == {"status": "saved", "path": note_path}
    assert save_note(root, note_draft) == {"status": "already_saved", "path": note_path}


def test_save_pin_parity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = initialized(tmp_path)
    (root / "blocked.dat").write_text("x\n", encoding="utf-8")
    original_read = Path.read_bytes

    def denied(self, *args, **kwargs):
        if str(self).endswith("blocked.dat"):
            raise OSError("simulated unreadable")
        return original_read(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_bytes", denied)
    cases = [
        ("a", {"target": "missing/evidence.md", "at": "sha256:" + "0" * 64},
         "missing_ref", "reference target does not exist: missing/evidence.md"),
        ("b", {"target": "data", "at": "sha256:" + "0" * 64},
         "unreadable_ref", "reference target is not a file: data"),
        ("c", {"target": "blocked.dat", "at": "sha256:" + "0" * 64},
         "unreadable_ref", "reference target is unreadable: blocked.dat: simulated unreadable"),
        ("d", {"target": "../escape.md", "at": "sha256:" + "0" * 64},
         "ref_escape", "reference escapes workspace: ../escape.md"),
        ("e", {"target": "theory/check.md", "at": "bogus:1"},
         "invalid_ref_pin", "unsupported ref pin: bogus"),
        ("f", {"target": "https://example.com/x", "at": "git:abc123"},
         "invalid_git_ref", "Git ref does not contain target: https://example.com/x@abc123"),
    ]
    for char, ref, code, message in cases:
        make_entry(root, char, kind="result", refs=[ref], limitations=["L"])
        prepared = prepare_entry(root, "result", "agent", created_by="agent:test")
        draft = root / prepared["path"]
        frontmatter, _, _ = parse_markdown(draft)
        frontmatter.update({"summary": "A result.", "limitations": ["L"], "refs": [ref]})
        atomic_write(draft, render_markdown(frontmatter, ENTRY_BODIES["result"]))
        with pytest.raises(AITPError) as error:
            save_entry(root, draft)
        assert error.value.code == code
        assert str(error.value) == message
    payload = check_workspace(root)
    pairs = {(finding["code"], finding["message"]) for finding in payload["findings"]}
    for _, _, code, message in cases:
        assert (code, message) in pairs


def test_cli_misuse(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    bogus = run_cli(root, "check", "--bogus")
    assert bogus.returncode == 2
    assert "usage:" in bogus.stderr
    assert bogus.stdout == ""
    cannot = run_cli(root, "check", "--json", "--cwd", str(root / "nope"))
    assert cannot.returncode == 2
    payload = json.loads(cannot.stdout)
    assert set(payload) == {"status", "code", "message"}
    assert payload["code"] == "invalid_root"


def test_seed_regression_s1_s2(tmp_path: Path) -> None:
    for name in ("S1", "S2"):
        root = tmp_path / name
        shutil.copytree(REPOSITORY / "suite" / "seeds" / name, root)
        before = hash_tree(root)
        first = run_cli(root, "check", "--json")
        second = run_cli(root, "check", "--json")
        assert first.returncode == second.returncode
        assert first.stdout == second.stdout
        payload = json.loads(first.stdout)
        assert payload["schema"] == "aitp/check-report-0.1"
        assert payload["status"] in {"clean", "findings"}
        entered = run_cli(root, "enter")
        assert entered.returncode == 0, entered.stderr
        assert "recent_entries:" in entered.stdout
        assert "recent_notes:" in entered.stdout
        assert "latest_working_note:" in entered.stdout
        assert "active_newer:" in entered.stdout
        assert hash_tree(root) == before
