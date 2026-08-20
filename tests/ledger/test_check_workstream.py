"""M1d scoped `check --workstream` (`aitp/check-report-0.2`).

Contract under test (per the frozen implementation spec
``docs/archive/m1d-workstream-health-spec.md``):

- ``check --workstream SLUG`` accepts **exactly one** slug and emits
  ``aitp/check-report-0.2``: the complete v0.1 payload plus one additive
  top-level singular ``workstream`` key and two additive ``counts`` keys —
  ``by_code`` (``code -> {"errors": n, "warnings": m}``, keys sorted
  lexicographically, always present) and ``outside_scope`` (global minus
  scoped level totals, always present, never a finding, never a ``malformed``
  key). Key order is frozen: top level ``schema, status, root, counts,
  findings, workstream``; ``counts`` ``entries, notes, errors, warnings,
  by_code, outside_scope``.
- Attribution is strict: a finding is scoped iff its path is an **admitted**
  record (parse and structure passed and the ID was unique) whose frontmatter
  ``workstreams`` explicitly contains the slug. Malformed, duplicate-ID,
  invalid-``workstreams``, and structural-failure findings are unattributable
  and never scoped; unscoped and out-of-scope records are excluded; TOPIC.md
  findings are excluded. Relations validate on the global ``entry_map``
  first, so an out-of-scope target still resolves.
- The scoped report is the global report **restricted**: same findings,
  levels, codes, messages, and ``(path, code, message)`` order — a strict
  subset projection, never re-sorted or re-graded.
- Scoped ``counts.entries``/``counts.notes`` are **admitted in-scope**
  record counts (deliberately different from the global per-file count);
  ``errors``/``warnings`` are scoped findings by level; ``status`` and the
  exit code follow the scoped findings alone. A well-formed slug with no
  admitted in-scope records is a valid **empty scope** (exit 0), with
  ``outside_scope`` carrying the global remainder.
- Scoped text is exactly four frozen lines (``workstream`` / ``check`` /
  ``by_code`` compact JSON / ``outside_scope`` with the literal ``(run "aitp
  check" for the whole store)`` suffix), always, including a clean scope; no
  per-finding lines; stderr empty on exit 0/1.
- Without the flag every output surface is byte-identical
  ``aitp/check-report-0.1`` (JSON, text, exit 0/1/2, zero-write).
- Distribution contract (spec §Version and docs sync): the bundled Skill
  teaches the same frozen surface and claim boundaries, documents the frozen
  ref shape and mutable-pin discipline, and links a natural-use template copy
  byte-identical to the authoritative repo-root template.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
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
)

REPOSITORY = Path(__file__).resolve().parents[2]
VENDOR = REPOSITORY / "plugins" / "aitp-research-protocol" / "scripts" / "vendor"
PLUGIN = REPOSITORY / "plugins" / "aitp-research-protocol"
AUTHORITATIVE_TEMPLATE = REPOSITORY / "feedback" / "natural-use-session-template.md"
GOLDEN = Path(__file__).parent / "fixtures" / "golden"
STORE = GOLDEN / "store"
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
}

# Expected scoped by_code for the ``scoped_store`` fixture under ``crpa``:
# keys in the frozen lexicographic order ("missing_refs" < "missing_relation").
CRPA_BY_CODE = {
    "invalid_timestamp": {"errors": 0, "warnings": 1},
    "missing_refs": {"errors": 1, "warnings": 0},
    "missing_relation": {"errors": 1, "warnings": 0},
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
    payload["root"] = ROOT_MARKER
    return payload


def skill_doc() -> str:
    """The bundled using-aitp Skill, whitespace-folded for stable matching."""
    skill = (PLUGIN / "skills" / "using-aitp" / "SKILL.md").read_text(encoding="utf-8")
    return re.sub(r"\s+", " ", skill)


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
    created_at: object = "2026-01-01T00:00:00Z",
    summary: str = "Decision summary.",
    next_action: str = "",
    supersedes: list[str] | None = None,
    resolves: list[str] | None = None,
    refs: list[dict[str, str]] | None = None,
    limitations: list[str] | None = None,
    workstreams: list[str] | None = None,
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
    if workstreams is not None:
        frontmatter["workstreams"] = list(workstreams)
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
    path = root / ".aitp" / "topic" / "notes" / f"{note_id(char)}.md"
    atomic_write(path, render_markdown(frontmatter, NOTE_BODIES[mode]))
    return path


def hash_tree(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def fill_goal(root: Path, text: str = "Determine the exponents.") -> None:
    topic = root / ".aitp" / "topic" / "TOPIC.md"
    frontmatter, body, _ = parse_markdown(topic)
    body = body.replace("Not established yet\n\n## Scope", f"{text}\n\n## Scope")
    atomic_write(topic, render_markdown(frontmatter, body))


def scoped_store(root: Path) -> None:
    """Deterministic mixed store. Goal stays unfilled so the TOPIC warning
    is global-only. Records (Entry IDs are hex-only, per the lite schema):

    - e1 (crpa) clean, admitted; e2 (crpa) legacy ``banana`` timestamp;
    - e3 (qsgw-semiconductor) missing ref; e4 unscoped missing ref;
    - e5 (crpa) missing relation (absent target); e6 (crpa) clean relation
      to the out-of-scope e3;
    - e7 malformed; e8 duplicate of e1 (itself crpa-tagged); e9 invalid
      ``workstreams`` (duplicate slug); ea (qsgw-semiconductor) missing
      relation; eb (crpa) non-string ``created_at`` (structural failure);
    - n1 (crpa) missing ``basis_refs``; n2 (qsgw-semiconductor) missing ref;
      n3 (crpa) clean with a real pinned file.

    Global: 10 errors / 2 warnings (12 findings). Scoped ``crpa``: 4
    admitted entries + 2 admitted notes, 2 errors / 1 warning,
    ``outside_scope`` {8, 1}. Scoped ``qsgw-semiconductor``: 3 errors /
    0 warnings, ``outside_scope`` {7, 2}. ``lone``: empty scope,
    ``outside_scope`` {10, 2}.
    """
    make_entry(root, "1", workstreams=["crpa"])
    make_entry(root, "2", created_at="banana", workstreams=["crpa"])
    make_entry(root, "3", refs=[fake_ref()], workstreams=["qsgw-semiconductor"])
    make_entry(root, "4", refs=[fake_ref()])
    make_entry(root, "5", resolves=[entry_id("c")], workstreams=["crpa"])
    make_entry(root, "6", resolves=[entry_id("3")], workstreams=["crpa"])
    malformed = root / ".aitp" / "topic" / "entries" / f"{entry_id('7')}.md"
    malformed.write_text("not markdown\n", encoding="utf-8")
    duplicate = make_entry(root, "8", workstreams=["crpa"])
    rewrite_frontmatter(duplicate, id=entry_id("1"))
    bad_ws = make_entry(root, "9", workstreams=["crpa"])
    rewrite_frontmatter(bad_ws, workstreams=["crpa", "crpa"])
    make_entry(root, "a", resolves=[entry_id("d")], workstreams=["qsgw-semiconductor"])
    make_entry(root, "b", created_at=["2026-01-01"], workstreams=["crpa"])
    make_note(root, "1", basis_refs=[], workstreams=["crpa"])
    make_note(root, "2", basis_refs=[fake_ref()], workstreams=["qsgw-semiconductor"])
    make_note(root, "3", basis_refs=[pinned_file(root, "theory/evidence.md")], workstreams=["crpa"])


def golden_store(root: Path) -> None:
    """Deterministic workstream-tagged store for the regenerated scoped
    golden ``check-workstream.json`` (test 15). Global: 4 errors (e1, e3,
    e4, e5) / 2 warnings (e2, TOPIC); scoped ``crpa``: 2 admitted entries,
    1 error / 1 warning, ``by_code`` {hash_mismatch, invalid_timestamp},
    ``outside_scope`` {3, 1}.
    """
    drifted = pinned_file(root, "theory/check.md")
    drifted["at"] = "sha256:" + "0" * 64
    make_entry(root, "1", kind="result", refs=[drifted], limitations=["L"], workstreams=["crpa"])
    make_entry(root, "2", created_at="banana", workstreams=["crpa"])
    make_entry(root, "3", refs=[fake_ref()], workstreams=["qsgw-semiconductor"])
    make_entry(root, "4", refs=[fake_ref()])
    malformed = root / ".aitp" / "topic" / "entries" / f"{entry_id('5')}.md"
    malformed.write_text("not markdown\n", encoding="utf-8")


def _has_key(payload: dict, needle: str) -> bool:
    if needle in payload:
        return True
    return any(_has_key(value, needle) for value in payload.values() if isinstance(value, dict))


def test_no_flag_byte_parity(tmp_path: Path) -> None:
    root = copy_store(tmp_path)
    assert normalized(check_workspace(root)) == golden("check.json")
    result = run_cli(root, "check", "--json")
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert normalized(payload) == golden("check.json")
    assert not _has_key(payload, "workstream")
    assert not _has_key(payload, "by_code")
    assert not _has_key(payload, "outside_scope")
    text = run_cli(root, "check")
    assert text.returncode == 1
    assert text.stdout == (
        "warning[empty_topic_goal]: .aitp/topic/TOPIC.md: Research Goal is not established\n"
        "check: 0 error(s), 1 warning(s)\n"
    )
    # Distribution contract (spec §Version and docs sync): the bundle is
    # self-contained — the Skill's natural-use template link must resolve to a
    # file inside the bundle, and the bundled copy must stay byte-identical to
    # the authoritative repo-root template, matching the byte-identity this
    # test pins for the no-flag surface.
    skill = (PLUGIN / "skills" / "using-aitp" / "SKILL.md").read_text(encoding="utf-8")
    link_line = next(
        line for line in skill.splitlines()
        if "natural-use-session-template.md" in line and "](" in line
    )
    link_target = link_line.split("](", 1)[1].split(")", 1)[0].split("#", 1)[0]
    bundled = (PLUGIN / "skills" / "using-aitp" / link_target).resolve()
    assert bundled.is_relative_to(PLUGIN.resolve()), link_target
    assert bundled.is_file(), link_target
    assert bundled.read_text(encoding="utf-8") == AUTHORITATIVE_TEMPLATE.read_text(
        encoding="utf-8"
    )


def test_scoped_schema_and_additive_keys(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    scoped_store(root)
    payload = check_workspace(root, workstream="crpa")
    assert payload["schema"] == "aitp/check-report-0.2"
    assert list(payload) == ["schema", "status", "root", "counts", "findings", "workstream"]
    assert payload["workstream"] == "crpa"
    assert "workstreams" not in payload
    assert list(payload["counts"]) == ["entries", "notes", "errors", "warnings", "by_code", "outside_scope"]
    assert "malformed" not in payload["counts"]


def test_scope_attribution_filter(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    scoped_store(root)
    global_run = check_workspace(root)
    scoped = check_workspace(root, workstream="crpa")
    assert {(f["path"], f["code"]) for f in scoped["findings"]} == {
        (f".aitp/topic/entries/{entry_id('2')}.md", "invalid_timestamp"),
        (f".aitp/topic/entries/{entry_id('5')}.md", "missing_relation"),
        (f".aitp/topic/notes/{note_id('1')}.md", "missing_refs"),
    }
    excluded = {
        f".aitp/topic/entries/{entry_id('3')}.md",  # out-of-scope
        f".aitp/topic/entries/{entry_id('4')}.md",  # unscoped
        f".aitp/topic/entries/{entry_id('7')}.md",  # malformed
        f".aitp/topic/entries/{entry_id('8')}.md",  # duplicate ID
        f".aitp/topic/entries/{entry_id('9')}.md",  # invalid workstreams
        f".aitp/topic/entries/{entry_id('b')}.md",  # structural failure
        ".aitp/topic/TOPIC.md",
    }
    assert all(f["path"] not in excluded for f in scoped["findings"])
    global_codes = {f["code"] for f in global_run["findings"]}
    assert {"missing_ref", "missing_relation", "missing_refs", "malformed_record",
            "duplicate_id", "invalid_workstreams", "invalid_timestamp",
            "empty_topic_goal"} <= global_codes
    assert len(global_run["findings"]) == 12
    assert len(scoped["findings"]) == 3


def test_scoped_counts_and_by_code(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    scoped_store(root)
    scoped = check_workspace(root, workstream="crpa")
    assert scoped["counts"]["entries"] == 4  # admitted in-scope, not per-file
    assert scoped["counts"]["notes"] == 2
    assert scoped["counts"]["errors"] == 2
    assert scoped["counts"]["warnings"] == 1
    by_code = scoped["counts"]["by_code"]
    assert by_code == CRPA_BY_CODE
    assert list(by_code) == sorted(by_code)
    assert sum(bucket["errors"] for bucket in by_code.values()) == scoped["counts"]["errors"]
    assert sum(bucket["warnings"] for bucket in by_code.values()) == scoped["counts"]["warnings"]
    assert sum(bucket["errors"] + bucket["warnings"] for bucket in by_code.values()) == len(scoped["findings"])
    assert scoped["counts"]["entries"] + scoped["counts"]["notes"] >= 1


def test_relations_global_then_scope(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    scoped_store(root)
    scoped = check_workspace(root, workstream="crpa")
    global_run = check_workspace(root)
    # in-scope resolver whose target exists out-of-scope validates clean
    e6 = f".aitp/topic/entries/{entry_id('6')}.md"
    assert not any(f["path"] == e6 for f in scoped["findings"])
    assert not any(f["path"] == e6 for f in global_run["findings"])
    # in-scope resolver with a store-absent target fires in the scope
    e5 = f".aitp/topic/entries/{entry_id('5')}.md"
    assert any(f["path"] == e5 and f["code"] == "missing_relation" for f in scoped["findings"])
    # an out-of-scope resolver's own findings stay out of the scope
    ea = f".aitp/topic/entries/{entry_id('a')}.md"
    assert any(f["path"] == ea and f["code"] == "missing_relation" for f in global_run["findings"])
    assert not any(f["path"] == ea for f in scoped["findings"])


def test_duplicate_id_excluded_from_scope(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    scoped_store(root)
    global_run = check_workspace(root)
    duplicate_path = f".aitp/topic/entries/{entry_id('8')}.md"
    assert [f for f in global_run["findings"] if f["code"] == "duplicate_id"] == [{
        "level": "error", "code": "duplicate_id", "path": duplicate_path,
        "message": f"duplicate Entry ID: {entry_id('1')}",
    }]
    for slug in ("crpa", "qsgw-semiconductor"):
        assert not any(f["code"] == "duplicate_id" for f in check_workspace(root, workstream=slug)["findings"])
    # the first structurally valid file wins the ID, as today: e1 is admitted
    assert check_workspace(root, workstream="crpa")["counts"]["entries"] == 4
    assert global_run["counts"]["entries"] == 11  # global per-file rule unchanged


def test_invalid_workstreams_unattributable(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    scoped_store(root)
    bad_path = f".aitp/topic/entries/{entry_id('9')}.md"
    assert any(f["path"] == bad_path and f["code"] == "invalid_workstreams"
               for f in check_workspace(root)["findings"])
    for slug in ("crpa", "qsgw-semiconductor"):
        assert not any(f["path"] == bad_path for f in check_workspace(root, workstream=slug)["findings"])
    # the record still fails save with the same code/message
    draft = root / ".aitp" / "local" / "drafts" / f"{entry_id('9')}.md"
    shutil.copy(root / bad_path, draft)
    with pytest.raises(AITPError) as error:
        save_entry(root, draft)
    assert error.value.code == "invalid_workstreams"
    assert str(error.value) == "invalid workstreams: duplicate workstream: crpa"


def test_legacy_timestamp_warning_scoped(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    scoped_store(root)
    scoped = check_workspace(root, workstream="crpa")
    e2 = f".aitp/topic/entries/{entry_id('2')}.md"
    assert [f for f in scoped["findings"] if f["path"] == e2] == [{
        "level": "warning", "code": "invalid_timestamp", "path": e2,
        "message": "unparseable created_at: banana",
    }]
    # a non-string created_at is a structural failure: global only
    eb = f".aitp/topic/entries/{entry_id('b')}.md"
    assert [f for f in check_workspace(root)["findings"] if f["path"] == eb] == [{
        "level": "error", "code": "invalid_timestamp", "path": eb,
        "message": "Entry created_at must be a string",
    }]
    assert not any(f["path"] == eb for f in scoped["findings"])


def test_topic_global_excluded(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    scoped_store(root)
    global_run = check_workspace(root)
    topic_path = ".aitp/topic/TOPIC.md"
    assert any(f["path"] == topic_path and f["code"] == "empty_topic_goal" for f in global_run["findings"])
    for slug in ("crpa", "qsgw-semiconductor", "lone"):
        assert not any(f["path"] == topic_path for f in check_workspace(root, workstream=slug)["findings"])
    crpa = check_workspace(root, workstream="crpa")
    assert crpa["counts"]["outside_scope"]["warnings"] == 1


def test_exit_codes_scoped(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    scoped_store(root)
    findings_scope = run_cli(root, "check", "--workstream", "crpa", "--json")
    assert findings_scope.returncode == 1
    assert json.loads(findings_scope.stdout)["status"] == "findings"
    clean_scope = run_cli(root, "check", "--workstream", "lone", "--json")
    assert clean_scope.returncode == 0
    clean_payload = json.loads(clean_scope.stdout)
    assert clean_payload["status"] == "clean"
    assert clean_payload["counts"]["outside_scope"]["errors"] > 0
    # payload/exit consistency in both directions
    assert (json.loads(findings_scope.stdout)["status"] == "findings") == (findings_scope.returncode == 1)
    assert (clean_payload["status"] == "findings") == (clean_scope.returncode == 1)
    # pre-scope conditions stay exit 2
    not_store = run_cli(tmp_path, "check", "--workstream", "crpa", "--json")
    assert not_store.returncode == 2
    assert json.loads(not_store.stdout)["code"] == "not_initialized"
    # resolve/load precede scope validation (§1): a non-store with an invalid
    # slug still reports not_initialized, never invalid_workstreams
    bad_slug_not_store = run_cli(tmp_path, "check", "--workstream", "Bad", "--json")
    assert bad_slug_not_store.returncode == 2
    assert json.loads(bad_slug_not_store.stdout)["code"] == "not_initialized"
    store = root / ".aitp" / "STORE.toml"
    original = store.read_bytes()
    store.write_bytes(b"\xff\xfe\x00bad")
    malformed = run_cli(root, "check", "--workstream", "crpa", "--json")
    assert malformed.returncode == 2
    assert json.loads(malformed.stdout)["code"] == "malformed_store"
    store.write_bytes(original)
    # repeated --workstream is CLI misuse
    repeated = run_cli(root, "check", "--workstream", "crpa", "--workstream", "qsgw-semiconductor", "--json")
    assert repeated.returncode == 2
    assert "usage:" in repeated.stderr
    assert "may only be given once" in repeated.stderr
    assert repeated.stdout == ""
    # invalid slugs: JSON error envelope, exit 2
    for slug, detail in (("Bad", "invalid slug: 'Bad'"), ("", "empty element")):
        result = run_cli(root, "check", "--workstream", slug, "--json")
        assert result.returncode == 2
        assert json.loads(result.stdout) == {
            "status": "error", "code": "invalid_workstreams",
            "message": f"invalid workstreams: {detail}",
        }
    # API-level non-string scope is rejected, never a union
    with pytest.raises(AITPError) as error:
        check_workspace(root, workstream=["crpa"])
    assert error.value.code == "invalid_workstreams"
    assert str(error.value) == "invalid workstreams: exactly one slug required"
    # frozen help strings (§1): the flag help and the check command line
    flag_help = run_cli(root, "check", "--help")
    assert flag_help.returncode == 0
    assert ("only findings on records that explicitly list this workstream (single slug)"
            in re.sub(r"\s+", " ", flag_help.stdout))
    top_help = run_cli(root, "--help")
    assert top_help.returncode == 0
    assert ("validate the whole store read-only and report findings "
            "(exit 0 clean, 1 findings, 2 cannot run)"
            in re.sub(r"\s+", " ", top_help.stdout))


def test_scoped_text_exact_four_lines(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    scoped_store(root)
    text = run_cli(root, "check", "--workstream", "crpa")
    assert text.returncode == 1
    assert text.stderr == ""
    assert text.stdout == (
        "workstream: crpa\n"
        "check: 2 error(s), 1 warning(s)\n"
        f"by_code: {json.dumps(CRPA_BY_CODE, ensure_ascii=False)}\n"
        'outside_scope: 8 error(s), 1 warning(s) (run "aitp check" for the whole store)\n'
    )
    assert "error[" not in text.stdout  # no per-finding lines
    clean = run_cli(root, "check", "--workstream", "lone")
    assert clean.returncode == 0
    assert clean.stderr == ""  # stderr empty on a clean scoped run too (§6)
    assert clean.stdout == (
        "workstream: lone\n"
        "check: 0 error(s), 0 warning(s)\n"
        "by_code: {}\n"
        'outside_scope: 10 error(s), 2 warning(s) (run "aitp check" for the whole store)\n'
    )
    plain = run_cli(root, "check")
    assert not any(line.startswith("workstream: ") for line in plain.stdout.splitlines())
    assert plain.stdout.startswith("warning[empty_topic_goal]: .aitp/topic/TOPIC.md: ")
    assert plain.stdout.endswith("check: 10 error(s), 2 warning(s)\n")


def test_empty_scope_valid(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    scoped_store(root)
    global_run = check_workspace(root)
    scoped = check_workspace(root, workstream="lone")
    assert scoped["schema"] == "aitp/check-report-0.2"
    assert scoped["workstream"] == "lone"
    assert scoped["counts"] == {
        "entries": 0, "notes": 0, "errors": 0, "warnings": 0,
        "by_code": {},
        "outside_scope": {"errors": global_run["counts"]["errors"],
                          "warnings": global_run["counts"]["warnings"]},
    }
    assert scoped["findings"] == []
    assert scoped["status"] == "clean"
    result = run_cli(root, "check", "--workstream", "lone", "--json")
    assert result.returncode == 0
    assert json.loads(result.stdout) == scoped


def test_zero_write(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    scoped_store(root)
    before = hash_tree(root)
    for args in (("check", "--workstream", "crpa", "--json"),
                 ("check", "--workstream", "crpa"),
                 ("check", "--json"),
                 ("check",)):
        result = run_cli(root, *args)
        assert result.returncode in (0, 1)
    assert hash_tree(root) == before
    assert not (root / ".aitp" / "local" / "locks" / "write.lock").exists()


def test_determinism(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    scoped_store(root)
    before = hash_tree(root)
    first = run_cli(root, "check", "--workstream", "crpa", "--json")
    text_first = run_cli(root, "check", "--workstream", "crpa")
    plain = run_cli(root, "check", "--json")  # unscoped run in between
    second = run_cli(root, "check", "--workstream", "crpa", "--json")
    text_second = run_cli(root, "check", "--workstream", "crpa")
    plain_again = run_cli(root, "check", "--json")
    assert first.returncode == second.returncode == 1
    assert first.stdout == second.stdout
    assert text_first.stdout == text_second.stdout
    assert plain.stdout == plain_again.stdout
    assert hash_tree(root) == before


def test_scoped_golden(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    golden_store(root)
    report = check_workspace(root, workstream="crpa")
    assert normalized(report) == golden("check-workstream.json")
    result = run_cli(root, "check", "--workstream", "crpa", "--json")
    assert result.returncode == 1
    assert json.loads(result.stdout) == report


def test_unscoped_legacy_store_empty_scope(tmp_path: Path) -> None:
    root = copy_store(tmp_path)
    for slug in ("crpa", "magnetic-symmetry"):
        scoped = check_workspace(root, workstream=slug)
        assert scoped["schema"] == "aitp/check-report-0.2"
        assert scoped["counts"] == {
            "entries": 0, "notes": 0, "errors": 0, "warnings": 0,
            "by_code": {}, "outside_scope": {"errors": 0, "warnings": 1},
        }
        assert scoped["findings"] == []
        assert scoped["status"] == "clean"
        assert run_cli(root, "check", "--workstream", slug, "--json").returncode == 0
    global_run = check_workspace(root)
    assert any(f["code"] == "empty_topic_goal" for f in global_run["findings"])
    assert normalized(global_run) == golden("check.json")
    # Distribution contract (spec §Version and docs sync): the Skill must
    # teach the surface this test exercises and the claim boundary it
    # demonstrates — unscoped legacy records are in no scope, so a scoped
    # clean/exit 0 may mean nothing is attributable, not health; health
    # requires records explicitly carrying the slug or a reviewed manual
    # backfill (the runtime never backfills).
    skill = skill_doc()
    assert "check --workstream" in skill
    assert "aitp/check-report-0.2" in skill
    assert "by_code" in skill
    assert "outside_scope" in skill
    assert "nothing is attributable" in skill
    assert "health certificate" in skill
    assert "manual backfill" in skill
    assert "never backfill" in skill


def test_by_code_per_level_same_code(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    fill_goal(root)
    make_entry(root, "1", kind="result", limitations=["L"],
               refs=[{"target": "https://example.com/x", "at": "git:abc123", "locator": "whole file"}],
               workstreams=["crpa"])
    make_entry(root, "2", kind="result", limitations=["L"],
               refs=[{"target": "theory/check.md", "at": "git:abc123", "locator": "whole file"}],
               workstreams=["crpa"])
    scoped = check_workspace(root, workstream="crpa")
    assert scoped["counts"]["by_code"] == {"invalid_git_ref": {"errors": 1, "warnings": 1}}
    assert scoped["counts"]["errors"] == 1
    assert scoped["counts"]["warnings"] == 1
    git = [f for f in scoped["findings"] if f["code"] == "invalid_git_ref"]
    assert {(f["level"], f["path"]) for f in git} == {
        ("error", f".aitp/topic/entries/{entry_id('1')}.md"),
        ("warning", f".aitp/topic/entries/{entry_id('2')}.md"),
    }
    assert scoped["counts"]["outside_scope"] == {"errors": 0, "warnings": 0}
    # Distribution contract (spec §Version and docs sync): the Skill must
    # document the frozen ref shape (target + at + locator, docs/design.md
    # §Evidence pins) and the mutable-pin discipline for evidence that may
    # change — the exact shape this test's refs exercise.
    skill = skill_doc()
    assert "target:" in skill
    assert "at:" in skill
    assert "evidence that may change" in skill


def test_outside_scope_derived(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    scoped_store(root)
    global_run = check_workspace(root)
    scoped = check_workspace(root, workstream="crpa")
    assert scoped["counts"]["outside_scope"] == {
        "errors": global_run["counts"]["errors"] - scoped["counts"]["errors"],
        "warnings": global_run["counts"]["warnings"] - scoped["counts"]["warnings"],
    }
    assert scoped["counts"]["outside_scope"] == {"errors": 8, "warnings": 1}
    assert "outside_scope" not in scoped["counts"]["by_code"]
    assert all(f["code"] != "outside_scope" for f in scoped["findings"])
    # a clean scope with global-only findings still exits 0 with non-zero remainder
    lone = run_cli(root, "check", "--workstream", "lone", "--json")
    assert lone.returncode == 0
    assert json.loads(lone.stdout)["counts"]["outside_scope"] == {"errors": 10, "warnings": 2}
    # a scope containing every finding of the store reports a zero remainder
    complete = initialized(tmp_path, "complete")
    fill_goal(complete)
    make_entry(complete, "1", created_at="banana", workstreams=["crpa"])
    make_entry(complete, "2", refs=[fake_ref()], workstreams=["crpa"])
    scoped_all = check_workspace(complete, workstream="crpa")
    assert scoped_all["findings"] == check_workspace(complete)["findings"]
    assert scoped_all["counts"]["outside_scope"] == {"errors": 0, "warnings": 0}


def test_scoped_subset_invariant(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    scoped_store(root)
    # admitted in-scope records, hand-enumerated per the frozen fixture:
    # structure passed and ID unique, frontmatter contains the slug.
    admitted_crpa = {
        f".aitp/topic/entries/{entry_id('1')}.md",
        f".aitp/topic/entries/{entry_id('2')}.md",
        f".aitp/topic/entries/{entry_id('5')}.md",
        f".aitp/topic/entries/{entry_id('6')}.md",
        f".aitp/topic/notes/{note_id('1')}.md",
        f".aitp/topic/notes/{note_id('3')}.md",
    }
    global_run = check_workspace(root)
    scoped = check_workspace(root, workstream="crpa")
    assert scoped["findings"] == [f for f in global_run["findings"] if f["path"] in admitted_crpa]
    assert check_workspace(root) == global_run
    assert run_cli(root, "check", "--json").stdout == json.dumps(global_run, ensure_ascii=False, indent=2) + "\n"
    admitted_qsgw = {
        f".aitp/topic/entries/{entry_id('3')}.md",
        f".aitp/topic/entries/{entry_id('a')}.md",
        f".aitp/topic/notes/{note_id('2')}.md",
    }
    qsgw = check_workspace(root, workstream="qsgw-semiconductor")
    assert qsgw["findings"] == [f for f in global_run["findings"] if f["path"] in admitted_qsgw]
