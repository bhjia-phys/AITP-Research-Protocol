"""Method-card distillation contract (AITP 0.8.0, Skill-only change).

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

0.8.0 additions (Skill-only, no runtime/CLI/schema change):

- method-observation markers as ordinary Entry body first lines are
  compatible with the existing save gate and ``check`` — the runtime never
  validates marker grammar, slug, position, or uniqueness;
- pre-card execution Entries can be pinned as a card's ``basis_refs`` while
  the card stays ``agent_draft`` and the pre-card Entries never carry a
  card pin;
- two post-card Entries exact-``sha256:``-pinning the same card revision
  are ordinary clean records — the test does not fake a runtime trial
  counter or proposal state;
- a second human ``decision`` Entry (the publication choice) saves clean
  with the same pin shape and does not change the Note ``review_state`` or
  create a Skill;
- the static Skill text covers the full 0.8 rule surface: marker
  grammar/candidate/trigger, pre-card basis vs post-card exact trial,
  two-step human decision (Approve/Defer/Reject then Publish now/Keep
  local), main-agent-only, fallback/native boundary, and the platform
  tool/card/Skill three-layer relationship.
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

PUBLISH_BODY = """\
## Durable Summary

A human requests publication of the pinned method card into the plugin Skill.

## Decision And Alternatives

Publish now; the card has been approved and two qualifying trials are recorded.

## Reason, Scope, And Revisit Condition

Revisit only if a new revision is created or the researcher explicitly reopens.
"""

OBSERVATION_RUN_BODY = """\
> method-observation: shell-fit

## Durable Summary

The shell-fitting procedure ran once end to end on the small-q setup.

## Question, Command, And Inputs

Run the pinned procedure with the standard convergence parameters.

## Outputs, Result, And Status

Outputs matched expectations; status completed.
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


# ---------------------------------------------------------------------------
# 0.8.0 runtime-compatibility tests: observation marker, pre-card basis,
# post-card exact trials, second human publication-choice decision.
# These prove only that the existing runtime accepts these ordinary
# Entry/Note/decision records; they never fake runtime trial counters,
# proposal state, or auto-discovery behavior.
# ---------------------------------------------------------------------------


def _save_run_entry(
    root: Path,
    *,
    summary: str,
    refs: list[dict[str, str]],
    limitations: list[str],
    body: str,
    idempotency_key: str | None = None,
) -> dict[str, str]:
    """CLI ``record prepare --kind run`` -> fill -> ``record save``; returns
    the prepared payload."""
    args = [
        "record", "prepare", "--kind", "run",
        "--authority", "agent", "--created-by", "agent:test", "--json",
    ]
    if idempotency_key is not None:
        args += ["--idempotency-key", idempotency_key]
    prepared = run_cli(root, *args)
    assert prepared.returncode == 0, prepared.stderr
    payload = json.loads(prepared.stdout)
    fill_entry(root, payload, summary=summary, refs=refs, limitations=limitations, body=body)
    saved = run_cli(root, "record", "save", payload["path"], "--json")
    assert saved.returncode == 0, saved.stderr
    assert json.loads(saved.stdout)["status"] == "saved"
    return payload


def _save_decision_entry(
    root: Path,
    *,
    summary: str,
    refs: list[dict[str, str]],
    body: str,
    idempotency_key: str,
) -> dict[str, str]:
    """CLI ``record prepare --kind decision --authority human`` -> fill ->
    ``record save``; returns the prepared payload."""
    prepared = run_cli(
        root,
        "record", "prepare", "--kind", "decision",
        "--authority", "human", "--created-by", "researcher",
        "--idempotency-key", idempotency_key,
        "--json",
    )
    assert prepared.returncode == 0, prepared.stderr
    payload = json.loads(prepared.stdout)
    fill_entry(root, payload, summary=summary, refs=refs, limitations=[], body=body)
    saved = run_cli(root, "record", "save", payload["path"], "--json")
    assert saved.returncode == 0, saved.stderr
    assert json.loads(saved.stdout)["status"] == "saved"
    return payload


def test_observation_marker_compatible_with_runtime(tmp_path: Path) -> None:
    """An Entry whose body first line is a ``> method-observation:`` marker
    is a perfectly ordinary Entry: the runtime treats it as body text and
    ``check`` is clean.  The runtime never validates marker grammar, slug,
    position, or uniqueness — these are Skill completeness checks."""
    root = initialized(tmp_path)
    fill_goal(root)
    basis = pinned_file(root, "theory/obs-evidence.md")
    payload = _save_run_entry(
        root,
        summary="The shell-fitting procedure ran once end to end.",
        refs=[basis],
        limitations=["One run; single setup."],
        body=OBSERVATION_RUN_BODY,
    )

    # the marker is literally the body's first line
    entry_path = root / ".aitp" / "topic" / "entries" / f"{payload['id']}.md"
    _, body, _ = parse_markdown(entry_path)
    assert body.splitlines()[0] == "> method-observation: shell-fit"

    # check is clean — the marker is ordinary body text to the runtime
    report = run_cli(root, "check", "--json")
    assert report.returncode == 0, report.stdout
    assert json.loads(report.stdout)["status"] == "clean"


def test_pre_card_entries_as_basis_refs(tmp_path: Path) -> None:
    """Pre-card execution Entries are pinned as the card's ``basis_refs``.
    The card stays ``agent_draft`` and the pre-card Entries never carry a
    card pin — they are basis, not trials."""
    root = initialized(tmp_path)
    fill_goal(root)
    basis_file = pinned_file(root, "theory/pre-card-basis.md")

    # two pre-card execution Entries
    pre1 = _save_run_entry(
        root,
        summary="First execution of the procedure.",
        refs=[basis_file],
        limitations=["Single setup."],
        body=RUN_BODY,
        idempotency_key="pre-card-run-1",
    )
    pre2 = _save_run_entry(
        root,
        summary="Second execution of the procedure.",
        refs=[basis_file],
        limitations=["Single setup."],
        body=RUN_BODY,
        idempotency_key="pre-card-run-2",
    )

    # pin both pre-card Entries as the card's basis_refs
    pre1_path = root / ".aitp" / "topic" / "entries" / f"{pre1['id']}.md"
    pre2_path = root / ".aitp" / "topic" / "entries" / f"{pre2['id']}.md"
    pre1_pin = {
        "target": f".aitp/topic/entries/{pre1['id']}.md",
        "at": f"sha256:{hashlib.sha256(pre1_path.read_bytes()).hexdigest()}",
        "locator": "whole file",
    }
    pre2_pin = {
        "target": f".aitp/topic/entries/{pre2['id']}.md",
        "at": f"sha256:{hashlib.sha256(pre2_path.read_bytes()).hexdigest()}",
        "locator": "whole file",
    }

    # create the card with both pre-card Entries as basis
    prepared = run_cli(
        root, "note", "prepare", "--mode", "theory",
        "--title", "Method card: shell-fit", "--created-by", "agent:test", "--json",
    )
    assert prepared.returncode == 0, prepared.stderr
    card_payload = json.loads(prepared.stdout)
    fill_note(
        root, card_payload,
        summary="Card generalizing two pre-card executions.",
        basis_refs=[pre1_pin, pre2_pin],
        body=card_body("shell-fit"),
    )
    saved = run_cli(root, "note", "save", card_payload["path"], "--json")
    assert saved.returncode == 0, saved.stderr

    # the card is agent_draft
    card_fm, card_body_text, _ = parse_markdown(
        root / ".aitp" / "topic" / "notes" / f"{card_payload['id']}.md"
    )
    assert card_fm["review_state"] == "agent_draft"
    assert card_body_text.splitlines()[0] == "> method-card: shell-fit"

    # the pre-card Entries do NOT carry a card pin (they are basis, not trials)
    for pre_id in (pre1["id"], pre2["id"]):
        pre_fm, _, _ = parse_markdown(
            root / ".aitp" / "topic" / "entries" / f"{pre_id}.md"
        )
        for ref in pre_fm.get("refs", []):
            assert "notes" not in ref["target"], (
                "pre-card Entry must not carry a card pin"
            )

    report = run_cli(root, "check", "--json")
    assert report.returncode == 0, report.stdout
    assert json.loads(report.stdout)["status"] == "clean"


def test_two_post_card_trials_pin_same_revision(tmp_path: Path) -> None:
    """Two post-card Entries that exact-``sha256:``-pin the same card
    revision are ordinary clean records.  The test does not fake a runtime
    trial counter or proposal state — it only proves the pins verify and
    ``check`` is clean."""
    root = initialized(tmp_path)
    fill_goal(root)

    # save the card first
    card = save_card(root, "shell-fit", basis=pinned_file(root, "theory/basis.md"))
    pin = card_pin(root, card["id"])

    # two post-card trial Entries pinning the exact same card revision
    trial1 = _save_run_entry(
        root,
        summary="Post-card trial one.",
        refs=[pin],
        limitations=["One run."],
        body=RUN_BODY,
        idempotency_key="post-card-trial-1",
    )
    trial2 = _save_run_entry(
        root,
        summary="Post-card trial two.",
        refs=[pin],
        limitations=["One run."],
        body=RUN_BODY,
        idempotency_key="post-card-trial-2",
    )

    # both trials pin the same card Note with the same sha256
    for trial_id in (trial1["id"], trial2["id"]):
        trial_fm, _, _ = parse_markdown(
            root / ".aitp" / "topic" / "entries" / f"{trial_id}.md"
        )
        assert trial_fm["refs"] == [pin]

    report = run_cli(root, "check", "--json")
    assert report.returncode == 0, report.stdout
    assert json.loads(report.stdout)["status"] == "clean"

    # the card remains agent_draft — the runtime never auto-approves or
    # creates a proposal state
    card_fm, _, _ = parse_markdown(
        root / ".aitp" / "topic" / "notes" / f"{card['id']}.md"
    )
    assert card_fm["review_state"] == "agent_draft"


def test_second_human_publication_decision_saves_clean(tmp_path: Path) -> None:
    """A second human ``decision`` Entry (the publication choice) saves clean
    with the same pin shape.  It does not change the Note ``review_state``
    or create a Skill — the runtime has no publication state machine."""
    root = initialized(tmp_path)
    fill_goal(root)
    card = save_card(root, "shell-fit", basis=pinned_file(root, "theory/basis.md"))
    pin = card_pin(root, card["id"])

    # first decision: approval
    approval = _save_decision_entry(
        root,
        summary="A human approves the pinned method card.",
        refs=[pin],
        body=DECISION_BODY,
        idempotency_key="shell-fit-approve",
    )

    # second decision: publication choice
    publish = _save_decision_entry(
        root,
        summary="A human requests publication of the pinned method card.",
        refs=[pin],
        body=PUBLISH_BODY,
        idempotency_key="shell-fit-publish",
    )

    # both decisions are separate Entries with human authority
    for dec_id in (approval["id"], publish["id"]):
        fm, _, _ = parse_markdown(
            root / ".aitp" / "topic" / "entries" / f"{dec_id}.md"
        )
        assert fm["kind"] == "decision"
        assert fm["authority"] == "human"
        assert fm["refs"] == [pin]

    # the card stays agent_draft — no runtime publication state
    card_fm, _, _ = parse_markdown(
        root / ".aitp" / "topic" / "notes" / f"{card['id']}.md"
    )
    assert card_fm["review_state"] == "agent_draft"

    report = run_cli(root, "check", "--json")
    assert report.returncode == 0, report.stdout
    assert json.loads(report.stdout)["status"] == "clean"


# ---------------------------------------------------------------------------
# 0.8.0 static Skill/manifest contract tests: the full rule surface.
# ---------------------------------------------------------------------------


def test_distilling_text_0_8_marker_and_candidate_rules() -> None:
    distilling = re.sub(
        r"\s+", " ",
        (PLUGIN / "skills" / "distilling-methods" / "SKILL.md").read_text(encoding="utf-8"),
    )

    # marker grammar: first line, blank next line, single marker, slug rule
    for phrase in (
        "> method-observation: <slug>",
        "must be the Entry body's first line",
        "at most one marker per Entry",
        "[a-z0-9][a-z0-9-]{0,62}",
        "The runtime does not validate the marker",
    ):
        assert phrase in distilling, phrase

    # candidate-not-proof: marker does not prove repetition or independence
    for phrase in (
        "does not prove the procedure ran twice",
        "does not prove independent sessions",
        "Never auto-draft by marker count",
    ):
        assert phrase in distilling, phrase

    # eligible kinds and non-eligible kinds
    for phrase in (
        "`run`, `result`, `observation` are preferred kinds",
        "`failure` alone is not a successful workaround occurrence",
        "`source`, `decision`, `closeout` are not eligible",
        "never backfill or rewrite an old Entry",
    ):
        assert phrase in distilling, phrase

    # rg discovery + show canonical review + exit 2 fail closed
    for phrase in (
        'rg "^> method-observation:" .aitp/topic/entries/',
        "read the canonical record with",
        "`aitp show <entry-id> --json`",
        "fail closed immediately",
    ):
        assert phrase in distilling, phrase

    # distinct logical execution and independence unknown boundary
    for phrase in (
        "two distinct logical execution roots",
        "when the current schema cannot prove it",
        "no-op or ask the researcher",
    ):
        assert phrase in distilling, phrase

    # pre-card basis: never count as trials
    for phrase in (
        "do not count them as trials",
        "Pre-card Entries can only enter the card's `basis_refs`",
        "never retroactively reinterpreted as post-card trials",
    ):
        assert phrase in distilling, phrase


def test_distilling_text_0_8_post_card_trial_rules() -> None:
    distilling = re.sub(
        r"\s+", " ",
        (PLUGIN / "skills" / "distilling-methods" / "SKILL.md").read_text(encoding="utf-8"),
    )

    # post-card trial: card must exist first, exact pin at creation
    for phrase in (
        "`run`/`result` are the preferred trial kinds",
        "count only when the Entry body itself directly records one card execution",
        "do not automatically equal independent sessions",
        "different Note ID, a different hash",
        "Entries with a different Note ID",
        "old-revision trials, and backfill pins do not count",
    ):
        assert phrase in distilling, phrase

    # contradictory trial stops; no auto-resolve; no silent edit
    for phrase in (
        "contradictory trial is recorded as an ordinary `failure`",
        "the card never auto-resolves a failure",
        "never silent-edited",
    ):
        assert phrase in distilling, phrase

    # auto-drafted card stays agent_draft; two trials = proposal only
    for phrase in (
        "An auto-drafted card always stays `review_state: agent_draft`",
        "without at least one qualifying post-card trial",
        "Two qualifying trials trigger a publication proposal only",
    ):
        assert phrase in distilling, phrase


def test_distilling_text_0_8_two_step_human_decision() -> None:
    distilling = re.sub(
        r"\s+", " ",
        (PLUGIN / "skills" / "distilling-methods" / "SKILL.md").read_text(encoding="utf-8"),
    )

    # proposal packet contents
    for phrase in (
        "assembles a proposal packet",
        "exact card Note ID, path, and SHA",
        "two qualifying trial IDs and their exact pins",
        "proposed Skill routing boundary",
    ):
        assert phrase in distilling, phrase

    # first question: Approve / Defer / Reject
    for phrase in (
        "`Approve` / `Defer` / `Reject`",
        "only an unambiguous mapping to one outcome continues",
        "`Other`, dismiss, timeout, or no answer means zero-write",
        "--idempotency-key <card-revision-approval-outcome>",
        "The researcher does not run commands, edit drafts, or fill YAML",
    ):
        assert phrase in distilling, phrase

    # Defer and Reject recorded as decisions; re-prompt conditions
    for phrase in (
        "`Defer` and `Reject` are also recorded as human `decision` Entries",
        "`Defer` re-prompts only on new qualifying evidence",
        "`Reject` re-prompts only on a new revision",
    ):
        assert phrase in distilling, phrase

    # second question: Publish now / Keep local, separate, independent
    for phrase in (
        "`Publish now` / `Keep local`",
        "separate second question",
        "independent human `decision` Entry with a separate stable idempotency key",
        "`Keep local` records the choice and stops",
        "`Publish now` is a durable, recoverable explicit human publish request",
        "does not authorize Hakimi runtime or any agent to mutate the installed plugin",
    ):
        assert phrase in distilling, phrase

    # main-agent-only; no hardcoded model/preset
    for phrase in (
        "initiated by the main agent only",
        "must not ask the researcher approval/publication questions",
        "must not answer on the researcher's behalf",
        "hardcodes no model or new preset",
    ):
        assert phrase in distilling, phrase


def test_distilling_text_0_8_platform_and_fallback_boundary() -> None:
    distilling = re.sub(
        r"\s+", " ",
        (PLUGIN / "skills" / "distilling-methods" / "SKILL.md").read_text(encoding="utf-8"),
    )

    # platform tool/card/Skill three-layer boundary
    for phrase in (
        "Tool/adapter executes",
        "Method card records a stable procedure",
        "Skill routes",
        "AITP Python never implements these platform mechanisms",
        "a card never dispatches tools",
        "a Skill never copies scheduler/SSH/rsync implementations",
        "bare `host:path` is never accepted as locally verified evidence",
        "Host/session Goal belongs to Hakimi",
    ):
        assert phrase in distilling, phrase

    # fallback best-effort, not runtime hook or exactly-once
    for phrase in (
        "model/Skill-driven best-effort fallback",
        "not a runtime callback, post-save hook, or exactly-once guarantee",
        "no exactly-once claim is made",
        "native host (Hakimi future Feature, planned but not implemented)",
        "Hakimi never copies the AITP parser/validator",
        "never writes `.aitp` canonical files directly",
    ):
        assert phrase in distilling, phrase


def test_distilling_text_0_8_extended_never_list() -> None:
    distilling = re.sub(
        r"\s+", " ",
        (PLUGIN / "skills" / "distilling-methods" / "SKILL.md").read_text(encoding="utf-8"),
    )

    for phrase in (
        "auto-draft a card by marker count alone",
        "count a pre-card Entry as a post-card trial",
        "let a subagent ask or answer approval/publication questions",
        "hardcode a model or preset for distillation",
        "accept a bare `host:path` as locally verified evidence",
        "claim exactly-once, runtime auto-discovery, scientific correctness",
    ):
        assert phrase in distilling, phrase


def test_using_aitp_text_0_8_observation_and_fallback() -> None:
    using = re.sub(
        r"\s+", " ",
        (PLUGIN / "skills" / "using-aitp" / "SKILL.md").read_text(encoding="utf-8"),
    )

    # session start: search observation markers after card retrieval
    for phrase in (
        'rg "^> method-observation:" .aitp/topic/entries/',
        "load `../distilling-methods/SKILL.md` for a bounded candidate review",
    ):
        assert phrase in using, phrase

    # durable Entry creation: observation marker or post-card trial pin
    for phrase in (
        "> method-observation: <slug>",
        "low-trust candidate tag",
        "create the Entry as a post-card trial that exact-`sha256:` pins that card",
    ):
        assert phrase in using, phrase

    # session end: review observations, cards, trials; best-effort fallback
    for phrase in (
        "review new observation markers",
        "best-effort fallback",
        "no runtime hook fires after every save",
        "no exactly-once claim",
        "native host has explicitly provided a current-session AITP distillation coordinator",
    ):
        assert phrase in using, phrase


def test_openai_yaml_manifests_0_8_descriptions() -> None:
    """The two ``agents/openai.yaml`` files carry updated descriptions that
    mention the 0.8 rule surface without fabricating runtime behavior."""
    distilling_yaml = (PLUGIN / "skills" / "distilling-methods" / "agents" / "openai.yaml").read_text(encoding="utf-8")
    using_yaml = (PLUGIN / "skills" / "using-aitp" / "agents" / "openai.yaml").read_text(encoding="utf-8")

    assert "method-observation markers" in distilling_yaml
    assert "two-step human decisions" in distilling_yaml
    assert "platform tool/card/Skill three-layer boundary" in distilling_yaml

    assert "observation-marker retrieval" in using_yaml
    assert "best-effort fallback" in using_yaml
    assert "no runtime hook or exactly-once guarantee" in using_yaml
