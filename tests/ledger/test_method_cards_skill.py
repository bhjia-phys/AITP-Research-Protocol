"""Method-card distillation contract (AITP 0.6.0, Skill-only change).

Test-only file: it pins the ``distilling-methods`` Skill's contract against
the canonical runtime and CLI without touching the implementation. Under
test:

- the bundled ``method-card-template.md`` shape: first line exactly
  ``> method-card: <slug>``, the six headings exactly equal to
  ``aitp.notes.NOTE_SECTIONS["theory"]``, and no ``<!-- aitp:`` prompt
  comments;
- the real CLI path: ``note prepare --mode theory`` -> fill a nonempty
  ``summary``/``basis_refs`` and the full template body -> ``note save`` ->
  ``check`` clean;
- the card stays an ordinary theory Note: it never becomes
  ``latest_working_note`` (working-mode Notes only), the save gate rejects
  missing summary / missing refs / an empty section / a non-``agent_draft``
  ``review_state`` / a missing ``supersedes`` target, a revision supersedes
  the old card while the old file's bytes stay untouched, a trial ``run``
  Entry sha256-pins the exact card file and tampering makes ``check``
  report ``hash_mismatch``, and a human ``decision`` Entry may pin the card
  while the card remains ``agent_draft`` (the runtime never auto-approves);
- the Skill text teaches the two human gates (approval, then publication)
  and the never-list, and contains neither of the wrong claims
  ``open matching cards with show`` nor ``visible as superseded in
  list/show``: ``list``/``show`` are Entry-only projections, so cards are
  never opened or listed there — this test never calls them with a Note,
  and there is no runtime auto-proposal/auto-publication behavior to fake;
- the bundled Skills' static text contracts: using-aitp's automatic
  current-state maintenance (fail-closed on ``enter``/``check`` exit 2,
  no durable delta -> zero-write, pre/post verification around every
  save, agent closeout provenance ``--kind closeout --authority agent
  --created-by agent:<name>``, working Notes carry ``created_by`` never
  ``authority``, supersession never touches human ``decision``/``result``
  Entries) and distilling-methods' trial/revision gates (only post-card
  exact ``sha256:`` trials count, pre-card Entries are never backfilled,
  revisions inherit no trials or approval, each revision restarts the
  two-trials + human decision + publish request chain, placeholder/slug
  completion is a Skill check, never a runtime gate).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from aitp import notes
from aitp.core import (
    AITPError,
    atomic_write,
    init_workspace,
    parse_markdown,
    prepare_note,
    render_markdown,
    save_note,
)

REPOSITORY = Path(__file__).resolve().parents[2]
VENDOR = REPOSITORY / "plugins" / "aitp-research-protocol" / "scripts" / "vendor"
PLUGIN = REPOSITORY / "plugins" / "aitp-research-protocol"
TEMPLATE = PLUGIN / "skills" / "distilling-methods" / "method-card-template.md"

WORKING_BODY = """\
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

RUN_BODY = """\
## Durable Summary

The card procedure ran once end to end.

## Question, Command, And Inputs

Run the pinned card procedure on the small-q setup.

## Outputs, Result, And Status

Outputs matched the card's Main Result; status completed.
"""

DECISION_BODY = """\
## Durable Summary

A human approves the pinned method card as the recorded procedure.

## Decision And Alternatives

Adopt the pinned card; no alternative procedure was selected.

## Reason, Scope, And Revisit Condition

Revisit when a trial contradicts the card's stated outputs.
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


def initialized(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    init_workspace(root, "test", "Test topic")
    return root


def fill_goal(root: Path, text: str = "Determine the exponents.") -> None:
    """Fill the Research Goal so ``check`` has no empty-topic-goal warning."""
    topic = root / ".aitp" / "topic" / "TOPIC.md"
    frontmatter, body, _ = parse_markdown(topic)
    body = body.replace("Not established yet\n\n## Scope", f"{text}\n\n## Scope")
    atomic_write(topic, render_markdown(frontmatter, body))


def pinned_file(root: Path, relative: str, text: str = "card evidence\n") -> dict[str, str]:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return {
        "target": relative,
        "at": f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}",
        "locator": "whole file",
    }


def card_body(slug: str, *, empty_last_section: bool = False) -> str:
    """The template body with ``<slug>`` filled and the usage blockquote
    removed, exactly as the Skill prescribes; optionally leaves the final
    heading empty for save-gate tests."""
    lines = TEMPLATE.read_text(encoding="utf-8").splitlines()
    kept = [lines[0]]
    in_usage = False
    for line in lines[1:]:
        if line.startswith("> Usage"):
            in_usage = True
            continue
        if in_usage:
            if line == "":
                in_usage = False
            continue
        kept.append(line)
    body = "\n".join(kept).replace("<slug>", slug)
    if empty_last_section:
        body = body[: body.index("## Limitations And Open Questions")] + "## Limitations And Open Questions\n"
    return body


def fill_note(
    root: Path,
    prepared: dict[str, str],
    *,
    summary: str,
    basis_refs: list[dict[str, str]],
    body: str,
    supersedes: list[str] | None = None,
    created_at: str | None = None,
    review_state: str | None = None,
) -> Path:
    path = root / prepared["path"]
    frontmatter, _, _ = parse_markdown(path)
    frontmatter.update(
        {
            "summary": summary,
            "basis_refs": basis_refs,
            "supersedes": supersedes or [],
        }
    )
    if created_at is not None:
        frontmatter["created_at"] = created_at
    if review_state is not None:
        frontmatter["review_state"] = review_state
    atomic_write(path, render_markdown(frontmatter, body))
    return path


def fill_entry(
    root: Path,
    prepared: dict[str, str],
    *,
    summary: str,
    refs: list[dict[str, str]],
    limitations: list[str],
    body: str,
) -> Path:
    path = root / prepared["path"]
    frontmatter, _, _ = parse_markdown(path)
    frontmatter.update({"summary": summary, "refs": refs, "limitations": limitations})
    atomic_write(path, render_markdown(frontmatter, body))
    return path


def save_card(
    root: Path,
    slug: str,
    *,
    basis: dict[str, str],
    summary: str = "Method card summary.",
    created_at: str | None = None,
    supersedes: list[str] | None = None,
) -> dict[str, str]:
    """CLI ``note prepare`` -> fill -> CLI ``note save``; returns the
    prepared payload (status/id/path)."""
    prepared = run_cli(
        root,
        "note",
        "prepare",
        "--mode",
        "theory",
        "--title",
        f"Method card: {slug}",
        "--created-by",
        "agent:test",
        "--json",
    )
    assert prepared.returncode == 0, prepared.stderr
    payload = json.loads(prepared.stdout)
    assert payload["status"] == "prepared"
    fill_note(
        root,
        payload,
        summary=summary,
        basis_refs=[basis],
        body=card_body(slug),
        created_at=created_at,
        supersedes=supersedes,
    )
    saved = run_cli(root, "note", "save", payload["path"], "--json")
    assert saved.returncode == 0, saved.stderr
    assert json.loads(saved.stdout)["status"] == "saved"
    return payload


def card_pin(root: Path, note_id: str) -> dict[str, str]:
    path = root / ".aitp" / "topic" / "notes" / f"{note_id}.md"
    return {
        "target": str(path.relative_to(root)),
        "at": f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}",
        "locator": "whole file",
    }


def draft_card(
    root: Path,
    *,
    summary: str = "Card summary.",
    basis_refs: list[dict[str, str]] | None = None,
    body: str | None = None,
    supersedes: list[str] | None = None,
    review_state: str | None = None,
) -> Path:
    prepared = prepare_note(root, "theory", "Method card: gate", created_by="agent:test")
    draft = root / prepared["path"]
    frontmatter, _, _ = parse_markdown(draft)
    frontmatter.update({"summary": summary, "basis_refs": basis_refs, "supersedes": supersedes or []})
    if review_state is not None:
        frontmatter["review_state"] = review_state
    atomic_write(draft, render_markdown(frontmatter, body or card_body("gate")))
    return draft


def test_template_first_line_is_card_marker() -> None:
    lines = TEMPLATE.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "> method-card: <slug>"


def test_template_headings_equal_theory_sections() -> None:
    text = TEMPLATE.read_text(encoding="utf-8")
    headings = re.findall(r"^## (.+)$", text, re.M)
    assert headings == notes.NOTE_SECTIONS["theory"]
    assert len(headings) == 6
    assert len(set(headings)) == 6


def test_template_has_no_aitp_prompt_comments() -> None:
    assert "<!-- aitp:" not in TEMPLATE.read_text(encoding="utf-8")


def test_cli_prepare_fill_save_then_check_clean(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    fill_goal(root)
    payload = save_card(root, "shell-fit", basis=pinned_file(root, "theory/card-basis.md"))

    path = root / ".aitp" / "topic" / "notes" / f"{payload['id']}.md"
    frontmatter, body, _ = parse_markdown(path)
    assert body.splitlines()[0] == "> method-card: shell-fit"
    assert re.findall(r"^## (.+)$", body, re.M) == notes.NOTE_SECTIONS["theory"]
    assert frontmatter["mode"] == "theory"
    assert frontmatter["title"] == "Method card: shell-fit"
    assert frontmatter["review_state"] == "agent_draft"
    assert frontmatter["summary"] == "Method card summary."

    report = run_cli(root, "check", "--json")
    assert report.returncode == 0, report.stdout
    payload_check = json.loads(report.stdout)
    assert payload_check["status"] == "clean"
    assert payload_check["findings"] == []
    assert payload_check["counts"]["notes"] == 1


def test_card_note_does_not_replace_latest_working_note(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    basis = pinned_file(root, "theory/basis.md")
    working = run_cli(
        root,
        "note",
        "prepare",
        "--mode",
        "working",
        "--title",
        "Current Status",
        "--created-by",
        "agent:test",
        "--json",
    )
    assert working.returncode == 0, working.stderr
    working_payload = json.loads(working.stdout)
    fill_note(
        root,
        working_payload,
        summary="Current evidence and open checks.",
        basis_refs=[basis],
        body=WORKING_BODY,
        created_at="2026-01-01T00:00:00Z",
    )
    saved = run_cli(root, "note", "save", working_payload["path"], "--json")
    assert saved.returncode == 0, saved.stderr

    # the method-card theory Note is newer than the working Note
    card = save_card(
        root,
        "shell-fit",
        basis=pinned_file(root, "theory/card-basis.md"),
        created_at="2026-01-01T00:00:01Z",
    )
    assert card["id"] != working_payload["id"]

    entered = run_cli(root, "enter", "--json")
    assert entered.returncode == 0, entered.stderr
    payload = json.loads(entered.stdout)
    assert payload["latest_working_note"]["id"] == working_payload["id"]
    assert payload["latest_working_note"]["id"] != card["id"]
    assert payload["recent_notes"][0]["id"] == card["id"]  # newest note is the card
    assert payload["recent_notes"][0]["mode"] == "theory"
    assert payload["recent_notes"][0]["review_state"] == "agent_draft"
    assert len(payload["recent_notes"]) == 2


def test_save_gate_rejects_invalid_card_drafts(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    basis = pinned_file(root, "theory/basis.md")
    missing = "note-" + "a" * 32

    with pytest.raises(AITPError) as error:
        save_note(root, draft_card(root, summary=""))
    assert error.value.code == "missing_summary"
    assert str(error.value) == "Note summary must not be empty"

    with pytest.raises(AITPError) as error:
        save_note(root, draft_card(root, basis_refs=[]))
    assert error.value.code == "missing_refs"
    assert str(error.value) == "Note requires nonempty basis_refs"

    with pytest.raises(AITPError) as error:
        save_note(root, draft_card(root, basis_refs=[basis], body=card_body("gate", empty_last_section=True)))
    assert error.value.code == "empty_section"
    assert str(error.value) == "required section is empty: Limitations And Open Questions"

    with pytest.raises(AITPError) as error:
        save_note(root, draft_card(root, review_state="approved"))
    assert error.value.code == "review_required"
    assert str(error.value) == "save only creates agent_draft Notes"

    with pytest.raises(AITPError) as error:
        save_note(root, draft_card(root, basis_refs=[basis], supersedes=[missing]))
    assert error.value.code == "missing_relation"
    assert str(error.value) == f"supersedes target does not exist: {missing}"

    # the same gate surfaces on the CLI: exit 2 with the JSON error envelope
    cli = run_cli(
        root,
        "note",
        "save",
        str(draft_card(root, basis_refs=[basis], supersedes=[missing]).relative_to(root)),
        "--json",
    )
    assert cli.returncode == 2
    assert json.loads(cli.stdout)["code"] == "missing_relation"


def test_revision_supersedes_old_card_and_preserves_old_bytes(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    fill_goal(root)
    basis = pinned_file(root, "theory/basis.md")
    old = save_card(root, "shell-fit", basis=basis)
    old_path = root / ".aitp" / "topic" / "notes" / f"{old['id']}.md"
    old_bytes = old_path.read_bytes()

    revision = save_card(
        root,
        "shell-fit",
        basis=pinned_file(root, "theory/revision-basis.md"),
        summary="Revised card summary.",
        supersedes=[old["id"]],
    )
    assert revision["id"] != old["id"]
    new_path = root / ".aitp" / "topic" / "notes" / f"{revision['id']}.md"

    # the old card file is never edited: same path, same bytes
    assert old_path.is_file()
    assert old_path.read_bytes() == old_bytes
    frontmatter, body, _ = parse_markdown(new_path)
    assert frontmatter["supersedes"] == [old["id"]]
    assert body.splitlines()[0] == "> method-card: shell-fit"

    report = run_cli(root, "check", "--json")
    assert report.returncode == 0, report.stdout
    assert json.loads(report.stdout)["status"] == "clean"


def test_trial_run_pins_card_and_tamper_reports_hash_mismatch(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    fill_goal(root)
    card = save_card(root, "shell-fit", basis=pinned_file(root, "theory/basis.md"))
    card_path = root / ".aitp" / "topic" / "notes" / f"{card['id']}.md"
    pin = card_pin(root, card["id"])

    prepared = run_cli(
        root,
        "record",
        "prepare",
        "--kind",
        "run",
        "--authority",
        "agent",
        "--created-by",
        "agent:test",
        "--json",
    )
    assert prepared.returncode == 0, prepared.stderr
    entry_payload = json.loads(prepared.stdout)
    draft = fill_entry(
        root,
        entry_payload,
        summary="The card procedure ran end to end.",
        refs=[pin],
        limitations=["One run; single setup."],
        body=RUN_BODY,
    )
    saved = run_cli(root, "record", "save", str(draft.relative_to(root)), "--json")
    assert saved.returncode == 0, saved.stderr
    assert run_cli(root, "check", "--json").returncode == 0

    # tamper with the card file: the trial Entry's sha256 pin now mismatches
    card_path.write_text(card_path.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8")
    actual = hashlib.sha256(card_path.read_bytes()).hexdigest()
    report = run_cli(root, "check", "--json")
    assert report.returncode == 1
    expected = {
        "level": "error",
        "code": "hash_mismatch",
        "path": f".aitp/topic/entries/{entry_payload['id']}.md",
        "message": (
            f"sha256 mismatch: {str(card_path.relative_to(root))}: "
            f"expected {pin['at'].split(':', 1)[1]}, actual {actual}"
        ),
    }
    assert json.loads(report.stdout)["findings"] == [expected]


def test_human_decision_pin_saves_clean_but_card_stays_agent_draft(tmp_path: Path) -> None:
    root = initialized(tmp_path)
    fill_goal(root)
    card = save_card(root, "shell-fit", basis=pinned_file(root, "theory/basis.md"))
    pin = card_pin(root, card["id"])

    prepared = run_cli(
        root,
        "record",
        "prepare",
        "--kind",
        "decision",
        "--authority",
        "human",
        "--created-by",
        "researcher",
        "--json",
    )
    assert prepared.returncode == 0, prepared.stderr
    decision_payload = json.loads(prepared.stdout)
    draft = fill_entry(
        root,
        decision_payload,
        summary="A human approves the pinned method card.",
        refs=[pin],
        limitations=[],
        body=DECISION_BODY,
    )
    saved = run_cli(root, "record", "save", str(draft.relative_to(root)), "--json")
    assert saved.returncode == 0, saved.stderr

    report = run_cli(root, "check", "--json")
    assert report.returncode == 0, report.stdout
    assert json.loads(report.stdout)["status"] == "clean"

    decision_fm, _, _ = parse_markdown(root / ".aitp" / "topic" / "entries" / f"{decision_payload['id']}.md")
    assert decision_fm["kind"] == "decision"
    assert decision_fm["authority"] == "human"
    assert decision_fm["refs"] == [pin]

    # the approval is expressed by the external human decision Entry only:
    # the runtime never auto-approves, so the card stays an agent_draft Note
    card_fm, card_body_text, _ = parse_markdown(root / ".aitp" / "topic" / "notes" / f"{card['id']}.md")
    assert card_fm["review_state"] == "agent_draft"
    assert card_fm["mode"] == "theory"
    assert card_body_text.splitlines()[0] == "> method-card: shell-fit"


def test_skill_text_gates_never_list_and_no_wrong_claims() -> None:
    distilling = re.sub(
        r"\s+", " ",
        (PLUGIN / "skills" / "distilling-methods" / "SKILL.md").read_text(encoding="utf-8"),
    )
    using = re.sub(
        r"\s+", " ",
        (PLUGIN / "skills" / "using-aitp" / "SKILL.md").read_text(encoding="utf-8"),
    )

    # the two human gates: approval (an external human decision Entry pinning
    # the card Note file) then publication (an explicit human publish
    # request); two pinned trials propose only
    for phrase in (
        "**Approval gate (human).**",
        "**Publication gate (human).**",
        "`decision` Entry (`authority: human`) that pins the card Note file",
        "never automatic",
        "**Proposal after two pinned trials.**",
    ):
        assert phrase in distilling, phrase

    # the never-list
    for phrase in (
        "Never: auto-publish",
        "propagate cards across Topics",
        "infer `workstreams`",
        "generate or summarize card content in Python",
        "card index, registry, or enumerating dispatcher",
    ):
        assert phrase in distilling, phrase

    # the correct teaching instead of the wrong claims: list/show project
    # Entries only and never show Notes
    assert "project Entries only" in distilling
    assert "never show Notes" in distilling

    # wrong claims absent: cards are never opened with `show` nor visible in
    # `list`/`show` (Entry-only projections), so no Skill may promise either
    for doc in (distilling, using):
        assert "open matching cards with show" not in doc
        assert "visible as superseded in list/show" not in doc


def test_using_aitp_text_automatic_maintenance_contract() -> None:
    using = re.sub(
        r"\s+", " ",
        (PLUGIN / "skills" / "using-aitp" / "SKILL.md").read_text(encoding="utf-8"),
    )

    # automatic current-state maintenance is agent judgment, never a runtime
    # rule, and writes only through the normal prepare/save path
    assert "Maintenance is automatic, but it is **judgment, not a runtime rule**" in using

    # fail closed on exit 2: unverified enter/check state is never treated as clean
    for phrase in (
        "**fail closed** on it, never treat it as clean",
        "fail closed on exit 2",
        "do not proceed on unverified state",
    ):
        assert phrase in using, phrase

    # no durable delta => zero-write
    for phrase in (
        "no durable delta ⇒ zero-write",
        "**No-op is the default.**",
        "write nothing: no closeout, no Note, no record — zero writes",
    ):
        assert phrase in using, phrase

    # pre/post verification around every save
    for phrase in (
        "**Pre/post verification**",
        "after any save, re-run both",
        "The save is not verified until the post-run confirms it",
    ):
        assert phrase in using, phrase

    # the closeout the agent appends carries full agent provenance
    assert "--kind closeout --authority agent --created-by agent:<name>" in using
    # working Notes carry created_by only, never authority
    assert "Notes carry `created_by`, never `authority`" in using
    # automatic supersession never touches human decision/result Entries
    for phrase in (
        "never supersede a human `decision` or `result` Entry",
        "Never re-issue with `agent` authority a decision the ledger already records as `human`",
    ):
        assert phrase in using, phrase


def test_distilling_text_trial_revision_approval_contract() -> None:
    distilling = re.sub(
        r"\s+", " ",
        (PLUGIN / "skills" / "distilling-methods" / "SKILL.md").read_text(encoding="utf-8"),
    )

    # only post-card trials count, and only with an exact sha256 pin on the
    # saved card file
    for phrase in (
        "counts toward the two pinned trials only when",
        "sha256-pins that exact saved card file",
        "same Note ID, same pinned `sha256:` digest",
    ):
        assert phrase in distilling, phrase

    # pre-card Entries are never backfilled or repurposed as trials
    for phrase in (
        "Entries recorded before the card Note existed never pin it",
        "never backfill or rewrite a pre-card Entry to add a pin",
    ):
        assert phrase in distilling, phrase

    # a revision inherits no trials and no approval from the old revision
    for phrase in (
        "trials pinned to the old revision do not count for the new one",
        "the old revision's approval does not inherit",
        "Approval does not carry across revisions",
    ):
        assert phrase in distilling, phrase

    # each new revision restarts the full gate chain: two trials on that
    # exact revision + a fresh human decision pin + a new publish request
    for phrase in (
        "requires two pinned trials on that exact new revision",
        "a fresh human `decision` pin on it",
        "a new explicit publish request",
    ):
        assert phrase in distilling, phrase

    # placeholder/slug completion is a Skill check, never a runtime gate
    for phrase in (
        "Slug substitution and placeholder removal are Skill completion checks, not runtime gates",
        "it never checks the title, the marker line, or leftover placeholder text",
    ):
        assert phrase in distilling, phrase
