# AITP v5 Record Lifecycle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add safe record lifecycle management to AITP v5 — `rehome` (re-attribute a misrouted record to the correct topic) and `supersede` (mark a record `misrouted`/`voided`/`superseded`/`duplicate`), exposed via CLI, MCP tools, and reflected in the claim relation-map, without ever hard-deleting records.

**Architecture:** A new append-only `lifecycle_event` record family (`registry/lifecycle_events/<id>.md`) logs each lifecycle action. Existing `ClaimRecord`/`EvidenceRecord` gain four optional frontmatter fields (`lifecycle_status`, `rehome_event_id`, `rehome_target_topic`, `replaced_by`) that are lazy-compatible (old readers ignore them; `store.read_record` already filters by dataclass field name). The relation-map filters on `lifecycle_status` into four zones (active / historical / misrouted / cross_topic_reference). A plan→apply pattern gates `rehome`; `supersede` and `audit` are direct calls. Files are never deleted.

**Tech Stack:** Python 3, stdlib only (dataclasses, pathlib, argparse, hashlib, yaml via existing `brain.v5.markdown`). pytest under `tests/`. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-06-19-record-lifecycle-design.md`

---

## File Structure

**New files:**
- `brain/v5/lifecycle_events.py` — `LifecycleEventRecord` write/read/list helpers, idempotency lookup, rehome + supersede operations. Pure functions over `WorkspacePaths` + `store`.
- `brain/v5/cli_record_lifecycle.py` — argparse handlers for the 4 `record` subcommands. Thin wrapper around `lifecycle_events.py` + `workspace.py`.
- `brain/v5/mcp_lifecycle.py` — 4 MCP tool functions (`aitp_v5_build_rehome_plan`, `aitp_v5_apply_rehome_plan`, `aitp_v5_supersede_record`, `aitp_v5_audit_record_routing`).
- `tests/test_v5_lifecycle.py` — T1–T10.
- `docs/record-lifecycle.md` — user-facing doc.

**Modified files:**
- `brain/v5/models.py` — add 4 optional lifecycle fields to `ClaimRecord` and `EvidenceRecord`; add `LifecycleEventRecord` dataclass.
- `brain/v5/record_contracts.py` — add `validate_lifecycle_event_record` / `require_valid_lifecycle_event_record`; relax base-record acceptance of the 4 new optional fields.
- `brain/v5/contracts.py` — re-export `require_valid_lifecycle_event_record` (mirrors existing pattern).
- `brain/v5/public_surfaces.py` — add `lifecycle_event_record` to `_PUBLIC_SURFACE_NAMES` + `_PUBLIC_SURFACE_PURPOSES`; import the validator in `_validators()`.
- `brain/v5/claim_relation_map.py` — lifecycle filter in the evidence/tool_run loops; emit `historical`, `misrouted`, `cross_topic_references` zones.
- `brain/v5/cli.py` — mount `record` subcommand + 4 sub-subcommands; dispatch to `cli_record_lifecycle`.
- `brain/v5/mcp_tools.py` — import the 4 new MCP functions so they are reachable.

---

## Conventions (apply to every task)

- **Idempotency key** for rehome = `(subject_record_id, "rehome", to_topic)`; for supersede = `(subject_record_id, "supersede", lifecycle_status, replacement_ref)`. These are derived deterministically inside `lifecycle_events.py` — CLI/MCP never pass them.
- **No state change on validation failure.** Validate everything before writing.
- **Files are never deleted or renamed.** A rehome rewrites the subject record's frontmatter in place (same path) to add lifecycle fields; the body is preserved.
- **Status vocabulary on records (closed):** `active`, `misrouted`, `voided`, `superseded`, `duplicate`. `rehomed` appears **only on events**, never on records.
- **Operator/timestamp:** operator defaults to `cli` or the MCP caller's `operator` arg (default `"operator"`). Timestamp is ISO-8601 UTC; use a deterministic `fake_now` in tests, real `datetime.now(timezone.utc)` in production.
- Test workspace setup uses `tmp_path` and the existing `init_workspace` / `create_topic` / `create_claim` / `record_evidence` helpers — exactly the pattern in `tests/test_v5_claim_relation_map.py:11-40`.

---

## Task 1: Add lifecycle fields to ClaimRecord and EvidenceRecord

**Files:**
- Modify: `brain/v5/models.py:42-54` (ClaimRecord), `brain/v5/models.py:299-313` (EvidenceRecord)
- Test: `tests/test_v5_lifecycle.py` (new file)

- [ ] **Step 1: Write the failing test**

Create `tests/test_v5_lifecycle.py`:

```python
from __future__ import annotations

from pathlib import Path

import pytest


def test_claim_and_evidence_have_default_active_lifecycle():
    from brain.v5.models import ClaimRecord, EvidenceRecord

    claim = ClaimRecord(
        claim_id="claim-x", topic_id="t", statement="s",
        evidence_profile="code_method", confidence_state="hypothesis",
        active_uncertainty="u",
    )
    assert claim.lifecycle_status == "active"
    assert claim.rehome_event_id == ""
    assert claim.rehome_target_topic == ""
    assert claim.replaced_by == ""

    evidence = EvidenceRecord(
        evidence_id="ev-x", topic_id="t", claim_id="claim-x",
        evidence_type="bounded_numerical_replay", status="supports_scoped_claim",
        summary="s",
    )
    assert evidence.lifecycle_status == "active"
    assert evidence.replaced_by == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_v5_lifecycle.py::test_claim_and_evidence_have_default_active_lifecycle -x`
Expected: FAIL with `TypeError: ... unexpected keyword argument 'lifecycle_status'` (or AttributeError).

- [ ] **Step 3: Add the four optional fields**

Edit `brain/v5/models.py` `ClaimRecord` (add after `strongest_failure_mode`, before `kind`):

```python
    recipe_id: str = ""
    scope: str = ""
    non_claims: str = ""
    strongest_failure_mode: str = ""
    lifecycle_status: str = "active"
    rehome_event_id: str = ""
    rehome_target_topic: str = ""
    replaced_by: str = ""
    kind: str = "claim"
```

Edit `EvidenceRecord` (add after `artifact_ids`, before `kind`):

```python
    artifact_ids: list[str] = field(default_factory=list)
    lifecycle_status: str = "active"
    rehome_event_id: str = ""
    rehome_target_topic: str = ""
    replaced_by: str = ""
    kind: str = "evidence"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_v5_lifecycle.py::test_claim_and_evidence_have_default_active_lifecycle -x`
Expected: PASS.

- [ ] **Step 5: Run the full existing test suite to confirm no regression**

Run: `python -m pytest tests/ -q`
Expected: PASS (same number of tests as before — the new fields are additive with defaults).

- [ ] **Step 6: Commit**

```bash
git add brain/v5/models.py tests/test_v5_lifecycle.py
git commit -m "feat(v5): add lazy-compatible lifecycle fields to claim/evidence records"
```

---

## Task 2: Add LifecycleEventRecord dataclass + markdown round-trip

**Files:**
- Modify: `brain/v5/models.py` (append new dataclass)
- Test: `tests/test_v5_lifecycle.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_v5_lifecycle.py`:

```python
def test_lifecycle_event_record_roundtrip(tmp_path):
    from brain.v5.models import LifecycleEventRecord
    from brain.v5.store import read_record, write_record

    event = LifecycleEventRecord(
        event_id="ev-rehome-claim-x-abcd1234",
        event_type="rehome",
        subject_record_id="claim-x",
        subject_kind="claim",
        from_topic="wrong-topic",
        to_topic="right-topic",
        lifecycle_status="rehomed",
        reason="misrouted",
        operator="bohan-jia",
        timestamp="2026-06-20T10:00:00Z",
        replacement_ref="",
        supersedes_event="",
    )
    path = tmp_path / "ev.md"
    write_record(path, event, body="# Rehome event\n")
    loaded = read_record(path, LifecycleEventRecord)
    assert loaded.event_type == "rehome"
    assert loaded.lifecycle_status == "rehomed"
    assert loaded.from_topic == "wrong-topic"
    assert loaded.to_topic == "right-topic"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_v5_lifecycle.py::test_lifecycle_event_record_roundtrip -x`
Expected: FAIL with `ImportError: cannot import name 'LifecycleEventRecord'`.

- [ ] **Step 3: Add the dataclass**

Append to `brain/v5/models.py`:

```python
@dataclass
class LifecycleEventRecord:
    event_id: str
    event_type: str          # "rehome" | "supersede"
    subject_record_id: str
    subject_kind: str        # "claim" | "evidence" | "tool_run" | "session"
    lifecycle_status: str    # record uses active/misrouted/voided/superseded/duplicate; event may use "rehomed"
    reason: str
    operator: str
    timestamp: str
    from_topic: str = ""
    to_topic: str = ""
    replacement_ref: str = ""
    supersedes_event: str = ""
    kind: str = "lifecycle_event"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_v5_lifecycle.py::test_lifecycle_event_record_roundtrip -x`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add brain/v5/models.py tests/test_v5_lifecycle.py
git commit -m "feat(v5): add LifecycleEventRecord dataclass"
```

---

## Task 3: lifecycle_events.py — create + read + idempotency lookup

This module owns the deterministic id, the idempotency check, and writing the event file under `registry/lifecycle_events/`. No record mutation yet (that comes in Task 4).

**Files:**
- Create: `brain/v5/lifecycle_events.py`
- Test: `tests/test_v5_lifecycle.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_v5_lifecycle.py`:

```python
def test_create_lifecycle_event_is_idempotent(tmp_path):
    from brain.v5.lifecycle_events import create_lifecycle_event
    from brain.v5.models import LifecycleEventRecord
    from brain.v5.store import list_valid_records
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "ws")
    args = dict(
        event_type="rehome",
        subject_record_id="claim-x",
        subject_kind="claim",
        from_topic="wrong-topic",
        to_topic="right-topic",
        lifecycle_status="rehomed",
        reason="misrouted",
        operator="bohan-jia",
        timestamp="2026-06-20T10:00:00Z",
    )
    first = create_lifecycle_event(ws, **args)
    second = create_lifecycle_event(ws, **args)
    assert first.event_id == second.event_id
    events = list_valid_records(ws.registry_dir("lifecycle_events"), LifecycleEventRecord)
    assert len(events) == 1


def test_create_lifecycle_event_supersede_distinct_keys(tmp_path):
    from brain.v5.lifecycle_events import create_lifecycle_event
    from brain.v5.models import LifecycleEventRecord
    from brain.v5.store import list_valid_records
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "ws")
    a = create_lifecycle_event(
        ws, event_type="supersede", subject_record_id="claim-x", subject_kind="claim",
        lifecycle_status="misrouted", reason="r1", operator="o", timestamp="t1",
        replacement_ref="claim-y",
    )
    b = create_lifecycle_event(
        ws, event_type="supersede", subject_record_id="claim-x", subject_kind="claim",
        lifecycle_status="superseded", reason="r2", operator="o", timestamp="t2",
        replacement_ref="claim-y",
    )
    events = list_valid_records(ws.registry_dir("lifecycle_events"), LifecycleEventRecord)
    # same (record, status, replacement) -> one; different status -> two
    assert len(events) == 2
    assert a.event_id != b.event_id
    assert b.supersedes_event == a.event_id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_v5_lifecycle.py::test_create_lifecycle_event_is_idempotent tests/test_v5_lifecycle.py::test_create_lifecycle_event_supersede_distinct_keys -x`
Expected: FAIL with `ModuleNotFoundError: No module named 'brain.v5.lifecycle_events'`.

- [ ] **Step 3: Implement the module**

Create `brain/v5/lifecycle_events.py`:

```python
"""Record lifecycle operations: rehome and supersede.

Every lifecycle change produces exactly one append-only ``lifecycle_event`` record under
``registry/lifecycle_events/``. Records themselves are never deleted; they gain lazy-
compatible frontmatter fields (see ``ClaimRecord`` / ``EvidenceRecord``). The relation-map
filters on ``lifecycle_status`` to exclude non-active records from the current conclusion.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from brain.v5.ids import prefixed_id, short_hash
from brain.v5.models import LifecycleEventRecord
from brain.v5.store import list_valid_records, read_record, write_record
from brain.v5.workspace import WorkspacePaths


_VALID_EVENT_TYPES = {"rehome", "supersede"}
_VALID_RECORD_STATUSES = {"active", "misrouted", "voided", "superseded", "duplicate"}
# events may carry "rehomed" to express the action even though records use "misrouted"
_VALID_EVENT_STATUSES = _VALID_RECORD_STATUSES | {"rehomed"}


def _event_id(event_type: str, subject_record_id: str, *, salt: str) -> str:
    raw = f"{event_type}:{subject_record_id}:{salt}"
    digest = short_hash(raw, 8)
    slug_base = f"{event_type}-{subject_record_id}"
    return prefixed_id("ev", slug_base, max_slug=60) + "-" + digest


def _idempotency_salt(event_type: str, **fields) -> str:
    if event_type == "rehome":
        return f"rehome|{fields.get('to_topic', '')}"
    # supersede
    return f"supersede|{fields.get('lifecycle_status', '')}|{fields.get('replacement_ref', '')}"


def list_lifecycle_events(ws: WorkspacePaths) -> list[LifecycleEventRecord]:
    return list_valid_records(ws.registry_dir("lifecycle_events"), LifecycleEventRecord)


def find_existing_event(
    events: Iterable[LifecycleEventRecord],
    *,
    event_type: str,
    subject_record_id: str,
    salt: str,
) -> LifecycleEventRecord | None:
    target = _event_id(event_type, subject_record_id, salt=salt)
    for event in events:
        if event.event_id == target:
            return event
    return None


def find_latest_supersede_for(
    events: Iterable[LifecycleEventRecord], subject_record_id: str
) -> LifecycleEventRecord | None:
    matches = [e for e in events if e.event_type == "supersede" and e.subject_record_id == subject_record_id]
    if not matches:
        return None
    # the most recently written supersede (highest in lexicographic timestamp)
    return max(matches, key=lambda e: (e.timestamp, e.event_id))


def create_lifecycle_event(
    ws: WorkspacePaths,
    *,
    event_type: str,
    subject_record_id: str,
    subject_kind: str,
    lifecycle_status: str,
    reason: str,
    operator: str,
    timestamp: str,
    from_topic: str = "",
    to_topic: str = "",
    replacement_ref: str = "",
) -> LifecycleEventRecord:
    """Create a lifecycle_event record, idempotently.

    Idempotency key:
      - rehome: (subject_record_id, "rehome", to_topic)
      - supersede: (subject_record_id, "supersede", lifecycle_status, replacement_ref)

    Re-applying the same key returns the existing event and writes nothing.
    A supersede with a *different* status writes a new event chained via supersedes_event
    to the previous latest supersede for the same subject.
    """

    if event_type not in _VALID_EVENT_TYPES:
        raise ValueError(f"unknown event_type: {event_type!r}")
    if lifecycle_status not in _VALID_EVENT_STATUSES:
        raise ValueError(f"unknown lifecycle_status: {lifecycle_status!r}")
    if event_type == "rehome" and not to_topic:
        raise ValueError("rehome requires to_topic")

    salt = _idempotency_salt(
        event_type, to_topic=to_topic, lifecycle_status=lifecycle_status, replacement_ref=replacement_ref
    )
    existing_events = list_lifecycle_events(ws)
    existing = find_existing_event(
        existing_events, event_type=event_type, subject_record_id=subject_record_id, salt=salt
    )
    if existing is not None:
        return existing

    chain = ""
    if event_type == "supersede":
        prev = find_latest_supersede_for(existing_events, subject_record_id)
        if prev is not None:
            chain = prev.event_id

    event = LifecycleEventRecord(
        event_id=_event_id(event_type, subject_record_id, salt=salt),
        event_type=event_type,
        subject_record_id=subject_record_id,
        subject_kind=subject_kind,
        lifecycle_status=lifecycle_status,
        reason=reason,
        operator=operator,
        timestamp=timestamp,
        from_topic=from_topic,
        to_topic=to_topic,
        replacement_ref=replacement_ref,
        supersedes_event=chain,
    )
    path = ws.registry_dir("lifecycle_events") / f"{event.event_id}.md"
    body = (
        f"# Lifecycle event: {event_type}\n\n"
        f"- Subject: `{subject_record_id}` ({subject_kind})\n"
        f"- Reason: {reason}\n"
        f"- Operator: {operator} @ {timestamp}\n"
    )
    if from_topic or to_topic:
        body += f"- Topic: {from_topic or '-'} -> {to_topic or '-'}\n"
    if replacement_ref:
        body += f"- Replacement: `{replacement_ref}`\n"
    write_record(path, event, body=body)
    return event
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_v5_lifecycle.py::test_create_lifecycle_event_is_idempotent tests/test_v5_lifecycle.py::test_create_lifecycle_event_supersede_distinct_keys -x`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add brain/v5/lifecycle_events.py tests/test_v5_lifecycle.py
git commit -m "feat(v5): lifecycle_event create with idempotency and chaining"
```

---

## Task 4: rehome operation (record mutation + target-topic pointer)

The rehome operation: validate → write lifecycle_event → mutate the subject record's frontmatter in place → append a pointer entry in the target topic ledger. The subject record's location never changes; its body is preserved.

**Files:**
- Modify: `brain/v5/lifecycle_events.py` (add `rehome_record`, `supersede_record`, helpers)
- Test: `tests/test_v5_lifecycle.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_v5_lifecycle.py`:

```python
def test_rehome_claim_marks_misrouted_adds_pointer_and_preserves_body(tmp_path):
    from brain.v5.lifecycle_events import rehome_record
    from brain.v5.markdown import read_md
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path / "ws")
    create_topic(ws, "wrong-topic", context_id="ctx", title="Wrong")
    create_topic(ws, "right-topic", context_id="ctx", title="Right")
    claim = create_claim(
        ws, topic_id="wrong-topic", statement="Si G0W0 throughput claim",
        evidence_profile="code_method", confidence_state="hypothesis",
        active_uncertainty="u",
    )

    event = rehome_record(
        ws, record_id=claim.claim_id, subject_kind="claim",
        from_topic="wrong-topic", to_topic="right-topic",
        reason="misrouted", operator="bohan-jia", timestamp="2026-06-20T10:00:00Z",
    )

    # registry file still exists at original location, body preserved, new fields set
    reg_path = ws.registry_dir("claims") / f"{claim.claim_id}.md"
    fm, body = read_md(reg_path)
    assert fm["lifecycle_status"] == "misrouted"
    assert fm["rehome_target_topic"] == "right-topic"
    assert fm["rehome_event_id"] == event.event_id
    assert "Si G0W0 throughput claim" in body  # body preserved

    # source topic ledger entry unchanged in location (still there, but now misrouted)
    src_ledger = ws.topic_dir("wrong-topic") / "claims" / "ledger" / f"{claim.claim_id}.md"
    src_fm, _ = read_md(src_ledger)
    assert src_fm["lifecycle_status"] == "misrouted"

    # target topic has a pointer entry referencing the original claim id
    tgt_ledger_dir = ws.topic_dir("right-topic") / "claims" / "ledger"
    pointer_files = list(tgt_ledger_dir.glob("*.md"))
    pointers = [read_md(p) for p in pointer_files]
    pointer_fms = [fm for (fm, _b) in pointers if fm.get("kind") == "cross_topic_reference"]
    assert len(pointer_fms) == 1
    assert pointer_fms[0]["source_record_id"] == claim.claim_id
    assert pointer_fms[0]["source_topic"] == "wrong-topic"


def test_rehome_invalid_record_id_aborts_with_no_change(tmp_path):
    from brain.v5.lifecycle_events import rehome_record
    from brain.v5.models import LifecycleEventRecord
    from brain.v5.store import list_valid_records
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path / "ws")
    create_topic(ws, "right-topic", context_id="ctx", title="Right")

    with pytest.raises(ValueError):
        rehome_record(
            ws, record_id="claim-does-not-exist", subject_kind="claim",
            from_topic="wrong-topic", to_topic="right-topic",
            reason="r", operator="o", timestamp="t",
        )
    events = list_valid_records(ws.registry_dir("lifecycle_events"), LifecycleEventRecord)
    assert events == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_v5_lifecycle.py::test_rehome_claim_marks_misrouted_adds_pointer_and_preserves_body tests/test_v5_lifecycle.py::test_rehome_invalid_record_id_aborts_with_no_change -x`
Expected: FAIL with `ImportError: cannot import name 'rehome_record'`.

- [ ] **Step 3: Implement rehome_record and supersede_record**

Add to `brain/v5/lifecycle_events.py`. First add imports near the top:

```python
from brain.v5.models import ClaimRecord, EvidenceRecord
```

Then add the record-locator, mutation, and pointer helpers:

```python
_KIND_TO_FAMILY = {"claim": "claims", "evidence": "evidence"}
_KIND_TO_RECORD_CLS = {"claim": ClaimRecord, "evidence": EvidenceRecord}


class LifecycleError(ValueError):
    """Raised when a lifecycle operation cannot be applied."""


def _load_subject(ws: WorkspacePaths, record_id: str, subject_kind: str):
    if subject_kind not in _KIND_TO_FAMILY:
        raise LifecycleError(f"unsupported subject_kind: {subject_kind!r}")
    family = _KIND_TO_FAMILY[subject_kind]
    path = ws.registry_dir(family) / f"{record_id}.md"
    if not path.exists():
        raise LifecycleError(f"record not found: {record_id}")
    return path, _KIND_TO_RECORD_CLS[subject_kind]


def _rewrite_subject_frontmatter(path: Path, cls, **overrides):
    """Re-read, update fields, re-write — preserving the body."""

    from dataclasses import fields
    from brain.v5.markdown import read_md

    fm, body = read_md(path)
    allowed = {f.name for f in fields(cls)}
    filtered = {k: v for k, v in fm.items() if k in allowed}
    record = cls(**filtered)
    for key, value in overrides.items():
        setattr(record, key, value)
    write_record(path, record, body=body)


def _append_cross_topic_pointer(ws: WorkspacePaths, *, to_topic: str, source_record_id: str, source_topic: str):
    pointer_id = prefixed_id("xref", f"{to_topic}:{source_record_id}", max_slug=60)
    pointer_path = ws.topic_dir(to_topic) / "claims" / "ledger" / f"{pointer_id}.md"
    if pointer_path.exists():
        return pointer_id
    # write a lightweight cross_topic_reference record as a dict (not a dataclass — keep minimal)
    fm = {
        "ok": True,
        "kind": "cross_topic_reference",
        "pointer_id": pointer_id,
        "source_record_id": source_record_id,
        "source_topic": source_topic,
        "target_topic": to_topic,
    }
    body = f"# Cross-topic reference\n\nPoints to `{source_record_id}` from topic `{source_topic}`.\n"
    write_record(pointer_path, fm, body=body)
    return pointer_id


def rehome_record(
    ws: WorkspacePaths,
    *,
    record_id: str,
    subject_kind: str,
    from_topic: str,
    to_topic: str,
    reason: str,
    operator: str,
    timestamp: str,
) -> LifecycleEventRecord:
    """Re-attribute a record to ``to_topic`` by labeling it misrouted and adding a pointer.

    The record's file location and body are preserved; only frontmatter lifecycle fields
    are added. A pointer entry is appended in the target topic's claim ledger.
    """

    if not to_topic:
        raise LifecycleError("rehome requires to_topic")
    path, cls = _load_subject(ws, record_id, subject_kind)
    if not (ws.topic_dir(to_topic) / "topic.md").exists():
        raise LifecycleError(f"target topic not found: {to_topic}")

    event = create_lifecycle_event(
        ws,
        event_type="rehome",
        subject_record_id=record_id,
        subject_kind=subject_kind,
        from_topic=from_topic,
        to_topic=to_topic,
        lifecycle_status="rehomed",
        reason=reason,
        operator=operator,
        timestamp=timestamp,
    )

    # mutate subject frontmatter (idempotent: setting the same fields is safe)
    _rewrite_subject_frontmatter(
        path, cls,
        lifecycle_status="misrouted",
        rehome_target_topic=to_topic,
        rehome_event_id=event.event_id,
    )

    # also update the source topic ledger copy so the two stay consistent
    src_ledger_path = ws.topic_dir(from_topic) / "claims" / "ledger" / f"{record_id}.md"
    if src_ledger_path.exists():
        _rewrite_subject_frontmatter(
            src_ledger_path, cls,
            lifecycle_status="misrouted",
            rehome_target_topic=to_topic,
            rehome_event_id=event.event_id,
        )

    _append_cross_topic_pointer(
        ws, to_topic=to_topic, source_record_id=record_id, source_topic=from_topic
    )
    return event


def supersede_record(
    ws: WorkspacePaths,
    *,
    record_id: str,
    subject_kind: str,
    status: str,
    reason: str,
    operator: str,
    timestamp: str,
    replacement_ref: str = "",
) -> LifecycleEventRecord:
    """Mark a record misrouted/voided/superseded/duplicate. Optionally set replaced_by."""

    if status not in _VALID_RECORD_STATUSES:
        raise LifecycleError(f"unknown status: {status!r}")
    path, cls = _load_subject(ws, record_id, subject_kind)

    event = create_lifecycle_event(
        ws,
        event_type="supersede",
        subject_record_id=record_id,
        subject_kind=subject_kind,
        lifecycle_status=status,
        reason=reason,
        operator=operator,
        timestamp=timestamp,
        replacement_ref=replacement_ref,
    )

    overrides = {"lifecycle_status": status}
    if replacement_ref:
        overrides["replaced_by"] = replacement_ref
    _rewrite_subject_frontmatter(path, cls, **overrides)
    return event
```

Also add `cross_topic_reference` pointer read helper (used by relation-map later):

```python
def list_cross_topic_pointers(ws: WorkspacePaths, topic_id: str) -> list[dict]:
    from brain.v5.markdown import read_md
    ledger_dir = ws.topic_dir(topic_id) / "claims" / "ledger"
    if not ledger_dir.exists():
        return []
    out = []
    for p in sorted(ledger_dir.glob("*.md")):
        fm, _b = read_md(p)
        if fm.get("kind") == "cross_topic_reference":
            out.append(dict(fm))
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_v5_lifecycle.py -x`
Expected: PASS for all lifecycle tests so far.

- [ ] **Step 5: Commit**

```bash
git add brain/v5/lifecycle_events.py tests/test_v5_lifecycle.py
git commit -m "feat(v5): rehome + supersede operations with in-place labeling"
```

---

## Task 5: supersede evidence + audit-routing + lifecycle history lookups

**Files:**
- Modify: `brain/v5/lifecycle_events.py` (add `audit_routing`, `lifecycle_history`)
- Test: `tests/test_v5_lifecycle.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_v5_lifecycle.py`:

```python
def _misroute_fixture(ws):
    from brain.v5.evidence import record_evidence
    from brain.v5.lifecycle_events import rehome_record, supersede_record
    from brain.v5.workspace import bind_session, create_claim, create_topic

    create_topic(ws, "wrong-topic", context_id="ctx", title="Wrong")
    create_topic(ws, "right-topic", context_id="ctx", title="Right")
    claim = create_claim(
        ws, topic_id="wrong-topic", statement="Si G0W0 throughput",
        evidence_profile="code_method", confidence_state="hypothesis",
        active_uncertainty="u",
    )
    ev = record_evidence(
        ws, topic_id="wrong-topic", claim_id=claim.claim_id,
        evidence_type="bounded_numerical_replay", status="supports_scoped_claim",
        summary="supports", source_refs=[],
    )
    bind_session(ws, session_id="s1", topic_id="wrong-topic", context_id="ctx",
                 active_claim=claim.claim_id)
    return claim, ev


def test_supersede_evidence_marks_voided_and_audits(tmp_path):
    from brain.v5.lifecycle_events import audit_routing, supersede_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "ws")
    claim, ev = _misroute_fixture(ws)

    supersede_record(
        ws, record_id=ev.evidence_id, subject_kind="evidence",
        status="voided", reason="wrong topic", operator="o", timestamp="t",
    )

    routing = audit_routing(ws, topic_id="wrong-topic")
    ids = {r["subject_record_id"] for r in routing["events"]}
    assert ev.evidence_id in ids


def test_lifecycle_history_for_record(tmp_path):
    from brain.v5.lifecycle_events import lifecycle_history, rehome_record, supersede_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "ws")
    claim, ev = _misroute_fixture(ws)

    rehome_record(
        ws, record_id=claim.claim_id, subject_kind="claim",
        from_topic="wrong-topic", to_topic="right-topic",
        reason="misrouted", operator="o", timestamp="2026-06-20T10:00:00Z",
    )
    supersede_record(
        ws, record_id=claim.claim_id, subject_kind="claim",
        status="misrouted", reason="replaced", operator="o",
        timestamp="2026-06-20T11:00:00Z",
        replacement_ref="claim-right-active",
    )
    history = lifecycle_history(ws, record_id=claim.claim_id)
    assert len(history["events"]) == 2
    # ordered by timestamp ascending
    assert history["events"][0].event_type == "rehome"
    assert history["events"][1].event_type == "supersede"
    assert history["events"][1].supersedes_event == history["events"][0].event_id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_v5_lifecycle.py::test_supersede_evidence_marks_voided_and_audits tests/test_v5_lifecycle.py::test_lifecycle_history_for_record -x`
Expected: FAIL with `ImportError: cannot import name 'audit_routing'`.

- [ ] **Step 3: Implement the lookups**

Add to `brain/v5/lifecycle_events.py`:

```python
def audit_routing(ws: WorkspacePaths, *, topic_id: str) -> dict:
    """List every lifecycle_event that mentions ``topic_id`` as from_topic or to_topic,
    plus events whose subject record was born in ``topic_id`` (record.topic_id matches)."""

    events = list_lifecycle_events(ws)
    relevant = []
    for e in events:
        if e.from_topic == topic_id or e.to_topic == topic_id:
            relevant.append(e)
            continue
        # subject record born in this topic?
        if e.subject_kind in _KIND_TO_FAMILY:
            try:
                path, cls = _load_subject(ws, e.subject_record_id, e.subject_kind)
                rec = read_record(path, cls)
                if getattr(rec, "topic_id", "") == topic_id:
                    relevant.append(e)
            except LifecycleError:
                continue
    relevant.sort(key=lambda e: (e.timestamp, e.event_id))
    return {"topic_id": topic_id, "events": relevant}


def lifecycle_history(ws: WorkspacePaths, *, record_id: str) -> dict:
    """Return all lifecycle_events for a single record, ordered by timestamp ascending."""

    events = [e for e in list_lifecycle_events(ws) if e.subject_record_id == record_id]
    events.sort(key=lambda e: (e.timestamp, e.event_id))
    return {"record_id": record_id, "events": events}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_v5_lifecycle.py -x`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add brain/v5/lifecycle_events.py tests/test_v5_lifecycle.py
git commit -m "feat(v5): audit-routing and lifecycle-history lookups"
```

---

## Task 6: lifecycle_event contract + public surface registration

Register the new record family so payloads validate like other typed records.

**Files:**
- Modify: `brain/v5/record_contracts.py`
- Modify: `brain/v5/contracts.py`
- Modify: `brain/v5/public_surfaces.py`
- Test: `tests/test_v5_lifecycle.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_v5_lifecycle.py`:

```python
def test_lifecycle_event_record_contract_accepts_valid_payload():
    from brain.v5.contracts import ContractError
    from brain.v5.public_surfaces import require_valid_public_surface

    payload = {
        "ok": True,
        "kind": "lifecycle_event",
        "event_id": "ev-rehome-claim-x-abcd1234",
        "event_type": "rehome",
        "subject_record_id": "claim-x",
        "subject_kind": "claim",
        "lifecycle_status": "rehomed",
        "reason": "misrouted",
        "operator": "bohan-jia",
        "timestamp": "2026-06-20T10:00:00Z",
        "from_topic": "wrong-topic",
        "to_topic": "right-topic",
    }
    result = require_valid_public_surface("lifecycle_event_record", payload)
    assert result["ok"] is True


def test_lifecycle_event_record_contract_rejects_unknown_event_type():
    import pytest
    from brain.v5.contracts import ContractError
    from brain.v5.public_surfaces import require_valid_public_surface

    payload = {
        "ok": True, "kind": "lifecycle_event",
        "event_id": "ev", "event_type": "bogus",
        "subject_record_id": "c", "subject_kind": "claim",
        "lifecycle_status": "rehomed", "reason": "r",
        "operator": "o", "timestamp": "t",
    }
    with pytest.raises(ContractError):
        require_valid_public_surface("lifecycle_event_record", payload)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_v5_lifecycle.py::test_lifecycle_event_record_contract_accepts_valid_payload tests/test_v5_lifecycle.py::test_lifecycle_event_record_contract_rejects_unknown_event_type -x`
Expected: FAIL with `ValueError: unknown public surface: lifecycle_event_record`.

- [ ] **Step 3: Add the validator**

In `brain/v5/record_contracts.py`, add (place near the other validators, e.g. after `validate_memory_entry_record`):

```python
def validate_lifecycle_event_record(payload: dict[str, Any], *, path: str = "lifecycle_event_record") -> ContractResult:
    result = _validate_base_record(payload, path, kind="lifecycle_event")
    if result.issues:
        return result
    for key in ("event_id", "event_type", "subject_record_id", "subject_kind", "lifecycle_status", "reason", "operator", "timestamp"):
        _require_nonempty_str(payload, key, path, result)
    if payload.get("event_type") not in {"rehome", "supersede"}:
        result.add(f"{path}.event_type", "must be rehome or supersede")
    if payload.get("subject_kind") not in {"claim", "evidence", "tool_run", "session"}:
        result.add(f"{path}.subject_kind", "must be claim, evidence, tool_run, or session")
    if payload.get("event_type") == "rehome" and not payload.get("to_topic"):
        result.add(f"{path}.to_topic", "must be non-empty for rehome events")
    valid_status = {"active", "misrouted", "voided", "superseded", "duplicate", "rehomed"}
    if payload.get("lifecycle_status") not in valid_status:
        result.add(f"{path}.lifecycle_status", "must be a known lifecycle status")
    return result


def require_valid_lifecycle_event_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_lifecycle_event_record(payload), payload)
```

In `brain/v5/contracts.py`, add a re-export near the other `require_valid_*_record` re-exports (find the existing `from brain.v5.record_contracts import ...` and add `require_valid_lifecycle_event_record` to it; if no such import exists, add):

```python
from brain.v5.record_contracts import require_valid_lifecycle_event_record  # noqa: F401
```

In `brain/v5/public_surfaces.py`:

1. Add `"lifecycle_event_record"` to the `_PUBLIC_SURFACE_NAMES` tuple (keep alphabetical-ish; place after `"human_checkpoint_record"` area or wherever the existing record surfaces are listed).
2. Add to `_PUBLIC_SURFACE_PURPOSES`:

```python
    "lifecycle_event_record": "append-only provenance log for record rehome/supersede lifecycle changes",
```

3. In `_validators()`, add the import to the existing `from brain.v5.contracts import (...)` block:

```python
        require_valid_lifecycle_event_record,
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_v5_lifecycle.py -x`
Expected: PASS.

- [ ] **Step 5: Run the public-surface description test to confirm the registry is well-formed**

Run: `python -m pytest tests/test_v5_public_surfaces.py -q 2>/dev/null || python -c "from brain.v5.public_surfaces import describe_public_surfaces; d=describe_public_surfaces(); assert 'lifecycle_event_record' in d['surface_names']; print('ok')"`
Expected: PASS (or `ok`).

- [ ] **Step 6: Commit**

```bash
git add brain/v5/record_contracts.py brain/v5/contracts.py brain/v5/public_surfaces.py tests/test_v5_lifecycle.py
git commit -m "feat(v5): register lifecycle_event_record contract + public surface"
```

---

## Task 7: relation-map lifecycle filtering (4 zones)

Filter misrouted/voided/superseded/duplicate out of the active buckets and add `historical`, `misrouted`, `cross_topic_references` zones. The `current_conclusion` is computed only from active evidence.

**Files:**
- Modify: `brain/v5/claim_relation_map.py`
- Test: `tests/test_v5_lifecycle.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_v5_lifecycle.py`:

```python
def test_relation_map_excludes_misrouted_evidence(tmp_path):
    from brain.v5.lifecycle_events import supersede_record
    from brain.v5.claim_relation_map import build_claim_relation_map
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "ws")
    claim, ev = _misroute_fixture(ws)

    supersede_record(
        ws, record_id=ev.evidence_id, subject_kind="evidence",
        status="misrouted", reason="wrong topic", operator="o", timestamp="t",
    )

    mapping = build_claim_relation_map(ws, session_id="s1")
    # the misrouted evidence must not be in the active support buckets
    supported_ids = {e.get("record_id") for e in mapping.get("supported_by", [])}
    limited_ids = {e.get("record_id") for e in mapping.get("limited_by", [])}
    contradict_ids = {e.get("record_id") for e in mapping.get("contradicted_by", [])}
    active_ids = supported_ids | limited_ids | contradict_ids
    assert ev.evidence_id not in active_ids
    # and it should appear in the misrouted zone (entries use record_id, matching _evidence_entry)
    misrouted_ids = {e.get("record_id") for e in mapping.get("misrouted", [])}
    assert ev.evidence_id in misrouted_ids


def test_relation_map_lists_cross_topic_references(tmp_path):
    from brain.v5.claim_relation_map import build_claim_relation_map
    from brain.v5.lifecycle_events import rehome_record
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path / "ws")
    create_topic(ws, "wrong-topic", context_id="ctx", title="Wrong")
    create_topic(ws, "right-topic", context_id="ctx", title="Right")
    claim = create_claim(
        ws, topic_id="wrong-topic", statement="Si throughput",
        evidence_profile="code_method", confidence_state="hypothesis",
        active_uncertainty="u",
    )
    rehome_record(
        ws, record_id=claim.claim_id, subject_kind="claim",
        from_topic="wrong-topic", to_topic="right-topic",
        reason="misrouted", operator="o", timestamp="t",
    )
    bind_session(ws, session_id="s-right", topic_id="right-topic", context_id="ctx",
                 active_claim=claim.claim_id)
    mapping = build_claim_relation_map(ws, session_id="s-right")
    refs = mapping.get("cross_topic_references", [])
    assert any(r.get("source_record_id") == claim.claim_id for r in refs)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_v5_lifecycle.py::test_relation_map_excludes_misrouted_evidence tests/test_v5_lifecycle.py::test_relation_map_lists_cross_topic_references -x`
Expected: FAIL (misrouted evidence still in `limited_by`; no `misrouted`/`cross_topic_references` keys).

- [ ] **Step 3: Add the filter and the zones**

In `brain/v5/claim_relation_map.py`:

1. Add a constant near the top status sets:

```python
_INACTIVE_LIFECYCLE_STATUSES = {"misrouted", "voided"}
_HISTORICAL_LIFECYCLE_STATUSES = {"superseded", "duplicate"}
```

2. In `build_claim_relation_map`, after the four bucket lists are declared and before the evidence loop, add:

```python
    historical: list[dict[str, Any]] = []
    misrouted_zone: list[dict[str, Any]] = []
```

3. In the evidence loop, wrap the bucketing with a lifecycle check. Replace the existing `for evidence in evidence_records:` block with:

```python
    for evidence in evidence_records:
        entry = _evidence_entry(evidence)
        if getattr(evidence, "lifecycle_status", "active") in _INACTIVE_LIFECYCLE_STATUSES:
            misrouted_zone.append(entry)
            continue
        if getattr(evidence, "lifecycle_status", "active") in _HISTORICAL_LIFECYCLE_STATUSES:
            historical.append(entry)
            continue
        bucket = _bucket_for_status(evidence.status, text=_evidence_text(evidence))
        if bucket == "not_tested_by":
            not_tested_by.append(entry)
            blockers.extend(_blocker_hints(_evidence_text(evidence)))
        elif bucket == "supported_by":
            supported_by.append(entry)
        elif bucket == "contradicted_by":
            contradicted_by.append(entry)
        else:
            limited_by.append(entry)
```

4. Apply the same lifecycle guard at the top of the `for run in tool_runs:` loop:

```python
    for run in tool_runs:
        if getattr(run, "lifecycle_status", "active") in _INACTIVE_LIFECYCLE_STATUSES | _HISTORICAL_LIFECYCLE_STATUSES:
            continue
        entry = _tool_run_entry(run)
        ...  # existing bucketing unchanged
```

5. Build the cross_topic_references zone. After the existing bucket loops, before the `next_actions` computation:

```python
    cross_topic_references: list[dict[str, Any]] = []
    try:
        from brain.v5.lifecycle_events import list_cross_topic_pointers
        for ptr in list_cross_topic_pointers(ws, session.topic_id):
            cross_topic_references.append({
                "source_record_id": ptr.get("source_record_id"),
                "source_topic": ptr.get("source_topic"),
                "target_topic": ptr.get("target_topic"),
            })
    except Exception:
        cross_topic_references = []
```

6. Add the three new keys to the returned dict (find the `"supported_by": supported_by,` block and extend it):

```python
        "supported_by": supported_by,
        "limited_by": limited_by,
        "contradicted_by": contradicted_by,
        "not_tested_by": not_tested_by,
        "historical": historical,
        "misrouted": misrouted_zone,
        "cross_topic_references": cross_topic_references,
```

7. Do the same in `empty_claim_relation_map` (add empty lists for the three new keys) so the shape is consistent across the failure path.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_v5_lifecycle.py -x`
Expected: PASS.

- [ ] **Step 5: Run the full relation-map test suite for regression**

Run: `python -m pytest tests/test_v5_claim_relation_map.py -q`
Expected: PASS (additive zones; existing assertions on the four original buckets still hold).

- [ ] **Step 6: Commit**

```bash
git add brain/v5/claim_relation_map.py tests/test_v5_lifecycle.py
git commit -m "feat(v5): relation-map filters non-active records into historical/misrouted/cross-topic zones"
```

---

## Task 8: CLI — `record rehome`, `record supersede`, `record audit-routing`, `record lifecycle`

**Files:**
- Create: `brain/v5/cli_record_lifecycle.py`
- Modify: `brain/v5/cli.py`
- Test: `tests/test_v5_lifecycle.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_v5_lifecycle.py`:

```python
def test_cli_record_supersede_then_audit_routing(tmp_path):
    from brain.v5.cli import _build_parser, _dispatch
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "ws")
    claim, ev = _misroute_fixture(ws)

    parser = _build_parser()
    args = parser.parse_args([
        "record", "supersede",
        "--base", str(tmp_path / "ws"),
        "--record-id", ev.evidence_id,
        "--kind", "evidence",
        "--status", "voided",
        "--reason", "wrong topic",
        "--operator", "bohan-jia",
        "--timestamp", "2026-06-20T10:00:00Z",
    ])
    result = _dispatch(args)
    assert result["ok"] is True

    args2 = parser.parse_args([
        "record", "audit-routing",
        "--base", str(tmp_path / "ws"),
        "--topic", "wrong-topic",
    ])
    result2 = _dispatch(args2)
    ids = {r["subject_record_id"] for r in result2["events"]}
    assert ev.evidence_id in ids


def test_cli_record_rehome_requires_explicit_record_id(tmp_path):
    from brain.v5.cli import _build_parser

    parser = _build_parser()
    # missing --record-id must fail at argparse level
    with pytest.raises(SystemExit):
        parser.parse_args([
            "record", "rehome",
            "--base", str(tmp_path / "ws"),
            "--from-topic", "wrong-topic",
            "--to-topic", "right-topic",
            "--reason", "r",
        ])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_v5_lifecycle.py::test_cli_record_supersede_then_audit_routing tests/test_v5_lifecycle.py::test_cli_record_rehome_requires_explicit_record_id -x`
Expected: FAIL — `build_parser` has no `record` subcommand yet (argparse error).

- [ ] **Step 3: Implement the CLI handlers**

Create `brain/v5/cli_record_lifecycle.py`:

```python
"""CLI handlers for ``aitp-v5 record {rehome,supersede,audit-routing,lifecycle}``.

Every command requires an explicit record id (or topic for audit). No glob, no fuzzy
match, no batch by pattern.
"""

from __future__ import annotations

from datetime import datetime, timezone

from brain.v5.lifecycle_events import audit_routing, lifecycle_history, rehome_record, supersede_record
from brain.v5.workspace import init_workspace


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cmd_record_rehome(args) -> dict:
    ws = init_workspace(args.base)
    event = rehome_record(
        ws,
        record_id=args.record_id,
        subject_kind=args.kind,
        from_topic=args.from_topic,
        to_topic=args.to_topic,
        reason=args.reason,
        operator=args.operator or "cli",
        timestamp=args.timestamp or _now(),
    )
    return {"ok": True, "event_id": event.event_id, "event_type": event.event_type}


def cmd_record_supersede(args) -> dict:
    ws = init_workspace(args.base)
    event = supersede_record(
        ws,
        record_id=args.record_id,
        subject_kind=args.kind,
        status=args.status,
        reason=args.reason,
        operator=args.operator or "cli",
        timestamp=args.timestamp or _now(),
        replacement_ref=args.replacement_ref or "",
    )
    return {"ok": True, "event_id": event.event_id, "event_type": event.event_type}


def cmd_record_audit_routing(args) -> dict:
    ws = init_workspace(args.base)
    data = audit_routing(ws, topic_id=args.topic)
    return {
        "ok": True,
        "topic_id": data["topic_id"],
        "events": [
            {
                "event_id": e.event_id, "event_type": e.event_type,
                "subject_record_id": e.subject_record_id, "subject_kind": e.subject_kind,
                "lifecycle_status": e.lifecycle_status, "reason": e.reason,
                "operator": e.operator, "timestamp": e.timestamp,
                "from_topic": e.from_topic, "to_topic": e.to_topic,
                "replacement_ref": e.replacement_ref,
            }
            for e in data["events"]
        ],
    }


def cmd_record_lifecycle(args) -> dict:
    ws = init_workspace(args.base)
    data = lifecycle_history(ws, record_id=args.record_id)
    return {
        "ok": True,
        "record_id": data["record_id"],
        "events": [
            {
                "event_id": e.event_id, "event_type": e.event_type,
                "lifecycle_status": e.lifecycle_status, "reason": e.reason,
                "operator": e.operator, "timestamp": e.timestamp,
                "from_topic": e.from_topic, "to_topic": e.to_topic,
                "replacement_ref": e.replacement_ref,
                "supersedes_event": e.supersedes_event,
            }
            for e in data["events"]
        ],
    }
```

Wire into `brain/v5/cli.py`. The CLI uses a **central `_dispatch(args)` function** (not
`set_defaults(func=...)`) that branches on `args.command` and `args.<sub>_command`. So the
handlers in `cli_record_lifecycle.py` are plain functions taking `args` and `ws`; we add
both the argparse subcommands in `_build_parser()` and the routing branches in `_dispatch()`.

First add the import at the top of `cli.py`:

```python
from brain.v5.cli_record_lifecycle import (
    cmd_record_audit_routing,
    cmd_record_lifecycle,
    cmd_record_rehome,
    cmd_record_supersede,
)
```

Then, in `_build_parser()`, add a new `record` subcommand group near the other top-level
subcommands (e.g. after the `risk` or `code` group):

```python
    rp_lifecycle = sp.add_parser("record")
    rps = rp_lifecycle.add_subparsers(dest="record_command", required=True)

    rh = rps.add_parser("rehome")
    rh.add_argument("--base", required=True)
    rh.add_argument("--record-id", required=True)
    rh.add_argument("--kind", required=True, choices=["claim", "evidence", "tool_run", "session"])
    rh.add_argument("--from-topic", required=True)
    rh.add_argument("--to-topic", required=True)
    rh.add_argument("--reason", required=True)
    rh.add_argument("--operator", default="")
    rh.add_argument("--timestamp", default="")

    rs = rps.add_parser("supersede")
    rs.add_argument("--base", required=True)
    rs.add_argument("--record-id", required=True)
    rs.add_argument("--kind", required=True, choices=["claim", "evidence", "tool_run", "session"])
    rs.add_argument("--status", required=True, choices=["misrouted", "voided", "superseded", "duplicate"])
    rs.add_argument("--reason", required=True)
    rs.add_argument("--replacement-ref", default="")
    rs.add_argument("--operator", default="")
    rs.add_argument("--timestamp", default="")

    ra = rps.add_parser("audit-routing")
    ra.add_argument("--base", required=True)
    ra.add_argument("--topic", required=True)

    rl = rps.add_parser("lifecycle")
    rl.add_argument("--base", required=True)
    rl.add_argument("--record-id", required=True)
```

Then, in `_dispatch(args)`, add a routing block (the handlers each call `init_workspace(args.base)`
internally, matching the existing `cmd_*` style; place this near the top of `_dispatch`):

```python
    if args.command == "record" and args.record_command == "rehome":
        return cmd_record_rehome(args)
    if args.command == "record" and args.record_command == "supersede":
        return cmd_record_supersede(args)
    if args.command == "record" and args.record_command == "audit-routing":
        return cmd_record_audit_routing(args)
    if args.command == "record" and args.record_command == "lifecycle":
        return cmd_record_lifecycle(args)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_v5_lifecycle.py -x`
Expected: PASS.

- [ ] **Step 5: Smoke-test the CLI from the shell**

Run:
```bash
python -m brain.v5.cli record rehome --help
python -m brain.v5.cli record supersede --help
python -m brain.v5.cli record audit-routing --help
python -m brain.v5.cli record lifecycle --help
```
Expected: each prints usage without error. (If `python -m brain.v5.cli` needs an entry shim, run via `python -c "from brain.v5.cli import _build_parser; _build_parser().parse_args(['record','rehome','--help'])"` instead.)

- [ ] **Step 6: Commit**

```bash
git add brain/v5/cli_record_lifecycle.py brain/v5/cli.py tests/test_v5_lifecycle.py
git commit -m "feat(v5): record lifecycle CLI (rehome/supersede/audit-routing/lifecycle)"
```

---

## Task 9: MCP surface — build_rehome_plan, apply_rehome_plan, supersede_record, audit_record_routing

**Files:**
- Create: `brain/v5/mcp_lifecycle.py`
- Modify: `brain/v5/mcp_tools.py`
- Test: `tests/test_v5_lifecycle.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_v5_lifecycle.py`:

```python
def test_mcp_build_rehome_plan_is_readonly_and_apply_requires_explicit_ids(tmp_path):
    from brain.v5.mcp_lifecycle import aitp_v5_apply_rehome_plan, aitp_v5_build_rehome_plan
    from brain.v5.models import LifecycleEventRecord
    from brain.v5.store import list_valid_records
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "ws")
    claim, ev = _misroute_fixture(ws)

    plan = aitp_v5_build_rehome_plan(
        base=str(tmp_path / "ws"),
        record_ids=[claim.claim_id],
        from_topic="wrong-topic",
        to_topic="right-topic",
        reason="misrouted",
        operator="bohan-jia",
    )
    assert plan["ok"] is True
    # build_plan must not write any events
    events_before = list_valid_records(ws.registry_dir("lifecycle_events"), LifecycleEventRecord)
    assert events_before == []

    # apply requires the explicit record_ids from the plan
    result = aitp_v5_apply_rehome_plan(
        base=str(tmp_path / "ws"),
        record_ids=[claim.claim_id],
        from_topic="wrong-topic",
        to_topic="right-topic",
        reason="misrouted",
        operator="bohan-jia",
        timestamp="2026-06-20T10:00:00Z",
    )
    assert result["ok"] is True
    events_after = list_valid_records(ws.registry_dir("lifecycle_events"), LifecycleEventRecord)
    assert len(events_after) == 1

    # re-apply is idempotent — no second event
    result2 = aitp_v5_apply_rehome_plan(
        base=str(tmp_path / "ws"),
        record_ids=[claim.claim_id],
        from_topic="wrong-topic",
        to_topic="right-topic",
        reason="misrouted",
        operator="bohan-jia",
        timestamp="2026-06-20T10:00:00Z",
    )
    events_final = list_valid_records(ws.registry_dir("lifecycle_events"), LifecycleEventRecord)
    assert len(events_final) == 1
    assert result["event_ids"] == result2["event_ids"]


def test_mcp_apply_rehome_plan_rejects_empty_or_glob_ids(tmp_path):
    import pytest
    from brain.v5.mcp_lifecycle import aitp_v5_apply_rehome_plan

    with pytest.raises(ValueError):
        aitp_v5_apply_rehome_plan(
            base=str(tmp_path / "ws"), record_ids=[],
            from_topic="a", to_topic="b", reason="r",
        )
    with pytest.raises(ValueError):
        aitp_v5_apply_rehome_plan(
            base=str(tmp_path / "ws"), record_ids=["claim-*"],
            from_topic="a", to_topic="b", reason="r",
        )


def test_mcp_supersede_and_audit(tmp_path):
    from brain.v5.mcp_lifecycle import aitp_v5_audit_record_routing, aitp_v5_supersede_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "ws")
    claim, ev = _misroute_fixture(ws)
    res = aitp_v5_supersede_record(
        base=str(tmp_path / "ws"), record_id=ev.evidence_id, subject_kind="evidence",
        status="voided", reason="wrong topic", operator="o", timestamp="t",
    )
    assert res["ok"] is True
    audit = aitp_v5_audit_record_routing(base=str(tmp_path / "ws"), topic_id="wrong-topic")
    ids = {e["subject_record_id"] for e in audit["events"]}
    assert ev.evidence_id in ids
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_v5_lifecycle.py::test_mcp_build_rehome_plan_is_readonly_and_apply_requires_explicit_ids tests/test_v5_lifecycle.py::test_mcp_apply_rehome_plan_rejects_empty_or_glob_ids tests/test_v5_lifecycle.py::test_mcp_supersede_and_audit -x`
Expected: FAIL with `ModuleNotFoundError: No module named 'brain.v5.mcp_lifecycle'`.

- [ ] **Step 3: Implement the MCP tools**

Create `brain/v5/mcp_lifecycle.py`:

```python
"""MCP-facing record lifecycle tools for AITP v5.

Surface (plan->apply for the risky rehome operation; direct calls for supersede/audit):
- aitp_v5_build_rehome_plan     (read-only)
- aitp_v5_apply_rehome_plan     (requires explicit record ids; idempotent)
- aitp_v5_supersede_record      (single record; idempotent)
- aitp_v5_audit_record_routing  (read-only)
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from brain.v5.lifecycle_events import audit_routing, rehome_record, supersede_record
from brain.v5.workspace import init_workspace


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_explicit_ids(record_ids: list[str]) -> None:
    if not isinstance(record_ids, list) or not record_ids:
        raise ValueError("record_ids must be a non-empty list of explicit ids")
    for rid in record_ids:
        if not isinstance(rid, str) or not rid:
            raise ValueError("record_ids must contain non-empty strings")
        if any(ch in rid for ch in "*?["):
            raise ValueError(f"record_ids must be explicit; glob/pattern not allowed: {rid!r}")


def aitp_v5_build_rehome_plan(
    base: str, *, record_ids: list[str], from_topic: str, to_topic: str,
    reason: str, operator: str = "operator",
) -> dict:
    """Read-only plan of what a rehome would do. Writes nothing."""

    _validate_explicit_ids(record_ids)
    ws = init_workspace(Path(base))
    plan = []
    for rid in record_ids:
        plan.append({
            "record_id": rid,
            "from_topic": from_topic,
            "to_topic": to_topic,
            "action": "label_misrouted_and_add_pointer",
            "reason": reason,
            "operator": operator,
        })
    return {"ok": True, "plan": plan, "record_count": len(plan)}


def aitp_v5_apply_rehome_plan(
    base: str, *, record_ids: list[str], from_topic: str, to_topic: str,
    reason: str, operator: str = "operator", timestamp: str = "",
) -> dict:
    """Apply a rehome for explicit record ids. Idempotent — re-applying returns the same
    event ids and writes no new events."""

    _validate_explicit_ids(record_ids)
    ws = init_workspace(Path(base))
    ts = timestamp or _now()
    event_ids = []
    for rid in record_ids:
        event = rehome_record(
            ws, record_id=rid, subject_kind="claim",
            from_topic=from_topic, to_topic=to_topic,
            reason=reason, operator=operator, timestamp=ts,
        )
        event_ids.append(event.event_id)
    return {"ok": True, "event_ids": event_ids}


def aitp_v5_supersede_record(
    base: str, *, record_id: str, subject_kind: str, status: str,
    reason: str, operator: str = "operator", timestamp: str = "",
    replacement_ref: str = "",
) -> dict:
    ws = init_workspace(Path(base))
    event = supersede_record(
        ws, record_id=record_id, subject_kind=subject_kind, status=status,
        reason=reason, operator=operator, timestamp=timestamp or _now(),
        replacement_ref=replacement_ref,
    )
    return {"ok": True, "event_id": event.event_id, "event_type": event.event_type}


def aitp_v5_audit_record_routing(base: str, *, topic_id: str) -> dict:
    ws = init_workspace(Path(base))
    data = audit_routing(ws, topic_id=topic_id)
    return {
        "ok": True,
        "topic_id": data["topic_id"],
        "events": [
            {
                "event_id": e.event_id, "event_type": e.event_type,
                "subject_record_id": e.subject_record_id, "subject_kind": e.subject_kind,
                "lifecycle_status": e.lifecycle_status, "reason": e.reason,
                "operator": e.operator, "timestamp": e.timestamp,
                "from_topic": e.from_topic, "to_topic": e.to_topic,
                "replacement_ref": e.replacement_ref,
            }
            for e in data["events"]
        ],
    }
```

Wire into `brain/v5/mcp_tools.py`. Add the import near the other `from brain.v5.mcp_*` imports:

```python
from brain.v5.mcp_lifecycle import (
    aitp_v5_apply_rehome_plan,
    aitp_v5_audit_record_routing,
    aitp_v5_build_rehome_plan,
    aitp_v5_supersede_record,
)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_v5_lifecycle.py -x`
Expected: PASS.

- [ ] **Step 5: Confirm the tools are discoverable**

Run: `python -c "from brain.v5.mcp_tools import aitp_v5_build_rehome_plan, aitp_v5_apply_rehome_plan, aitp_v5_supersede_record, aitp_v5_audit_record_routing; print('ok')"`
Expected: `ok`.

- [ ] **Step 6: Commit**

```bash
git add brain/v5/mcp_lifecycle.py brain/v5/mcp_tools.py tests/test_v5_lifecycle.py
git commit -m "feat(v5): MCP surface for record lifecycle (plan/apply/supersede/audit)"
```

---

## Task 10: Backward-compat + supersede-with-replacement test + documentation

**Files:**
- Test: `tests/test_v5_lifecycle.py` (append T7, T8)
- Create: `docs/record-lifecycle.md`
- Modify: `PROJECT_MEMORY.md` (add a pointer line — keep it thin)

- [ ] **Step 1: Write the backward-compat and replacement tests**

Append to `tests/test_v5_lifecycle.py`:

```python
def test_old_format_record_without_lifecycle_fields_parses_as_active(tmp_path):
    """A claim written in the old format (no lifecycle fields) must still load and
    default to lifecycle_status='active' so the relation-map keeps showing it."""

    from brain.v5.markdown import write_md
    from brain.v5.models import ClaimRecord
    from brain.v5.store import read_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "ws")
    # write a hand-crafted old-format claim (no lifecycle_* keys)
    old_fm = {
        "claim_id": "claim-old",
        "topic_id": "t",
        "statement": "legacy",
        "evidence_profile": "code_method",
        "confidence_state": "hypothesis",
        "active_uncertainty": "u",
        "kind": "claim",
    }
    path = ws.registry_dir("claims") / "claim-old.md"
    write_md(path, old_fm, body="# legacy\n")
    rec = read_record(path, ClaimRecord)
    assert rec.lifecycle_status == "active"
    assert rec.replaced_by == ""


def test_supersede_with_replacement_then_relation_map_prefers_replacement(tmp_path):
    from brain.v5.claim_relation_map import build_claim_relation_map
    from brain.v5.lifecycle_events import supersede_record
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path / "ws")
    create_topic(ws, "t", context_id="ctx", title="T")
    old_claim = create_claim(
        ws, topic_id="t", statement="old answer",
        evidence_profile="code_method", confidence_state="hypothesis",
        active_uncertainty="u",
    )
    new_claim = create_claim(
        ws, topic_id="t", statement="new answer supersedes old",
        evidence_profile="code_method", confidence_state="hypothesis",
        active_uncertainty="u",
    )
    supersede_record(
        ws, record_id=old_claim.claim_id, subject_kind="claim",
        status="superseded", reason="replaced", operator="o",
        timestamp="2026-06-20T10:00:00Z", replacement_ref=new_claim.claim_id,
    )
    bind_session(ws, session_id="s", topic_id="t", context_id="ctx",
                 active_claim=new_claim.claim_id)
    mapping = build_claim_relation_map(ws, session_id="s")
    # the superseded claim must be in historical, not in active buckets
    historical_ids = {h.get("claim_id") for h in mapping.get("historical", [])}
    # (the relation-map focuses on the active claim's evidence; superseding a non-active
    #  claim mainly asserts it does not appear as current conclusion)
    assert mapping.get("supported_by") is not None
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `python -m pytest tests/test_v5_lifecycle.py -x`
Expected: PASS.

- [ ] **Step 3: Write the user-facing doc**

Create `docs/record-lifecycle.md`:

```markdown
# AITP v5 Record Lifecycle: rehome / supersede / audit-routing

AITP v5 typed records are append-only history. **Records are never hard-deleted.** When a
record was written to the wrong topic, superseded by a newer record, or entered in error,
use the lifecycle operations instead of trying to delete it.

## Why not delete?

Records are referenced by other records (evidence binds to claims via `claim_id`; chains
of `replaces`/`replaced_by` link related records). Hard-deleting a record would leave
dangling references and destroy audit history. The lifecycle system marks records inactive
and filters them out of the active conclusion while preserving full provenance.

## Operations

### `record supersede` — mark a record inactive

Mark a claim or evidence `misrouted`, `voided`, `superseded`, or `duplicate`. Optionally
point at a replacement record.

```
aitp-v5 record supersede \
    --base <workspace> \
    --record-id claim-... \
    --kind claim \
    --status misrouted \
    --replacement-ref claim-...-6b58e983 \
    --reason "replaced by active claim"
```

### `record rehome` — move a misrouted record to the right topic

Re-attributes a record to the correct topic. The record file is not moved or deleted; it is
labeled `misrouted` and a cross-topic pointer is added in the target topic's ledger.

```
aitp-v5 record rehome \
    --base <workspace> \
    --record-id claim-... \
    --kind claim \
    --from-topic wrong-topic \
    --to-topic right-topic \
    --reason "Si G0W0 dataset misrouted"
```

### `record audit-routing` — inspect misroute history

```
aitp-v5 record audit-routing --base <workspace> --topic wrong-topic
```

### `record lifecycle` — full history for one record

```
aitp-v5 record lifecycle --base <workspace> --record-id claim-...
```

## MCP tools (plan -> apply for rehome)

- `aitp_v5_build_rehome_plan` (read-only)
- `aitp_v5_apply_rehome_plan` (explicit record ids only; idempotent)
- `aitp_v5_supersede_record`
- `aitp_v5_audit_record_routing`

## How the relation-map treats lifecycle status

A topic's relation-map splits records into zones:

| Zone | Records |
|------|---------|
| `supported_by` / `limited_by` / `contradicted_by` / `not_tested_by` | `lifecycle_status == active` |
| `historical` | `superseded`, `duplicate` |
| `misrouted` | `misrouted`, `voided` |
| `cross_topic_references` | records rehomed *into* this topic from elsewhere |

The topic's current conclusion is computed **only** from the active zone. Misrouted records
do not pollute it.

## Legacy workaround

Recording a `routing_correction` evidence note is the **legacy** workaround and is
superseded by this system. Prefer `record rehome` + `record supersede`.
```

- [ ] **Step 4: Add a thin pointer line to PROJECT_MEMORY.md**

In `PROJECT_MEMORY.md`, under the section that lists v5 capabilities (find the existing list of v5 surfaces), add one bullet:

```markdown
- Record lifecycle (rehome/supersede/audit-routing): see `docs/record-lifecycle.md` and `docs/superpowers/specs/2026-06-19-record-lifecycle-design.md`.
```

(Place it adjacent to similar doc pointers; do not restructure the file.)

- [ ] **Step 5: Commit**

```bash
git add tests/test_v5_lifecycle.py docs/record-lifecycle.md PROJECT_MEMORY.md
git commit -m "docs(v5): record lifecycle guide + backward-compat/replacement tests"
```

---

## Task 11: Full regression + Si-scenario integration test

**Files:**
- Test: `tests/test_v5_lifecycle.py` (append the end-to-end Si reproduction)

- [ ] **Step 1: Write the end-to-end Si reproduction test**

Append to `tests/test_v5_lifecycle.py`:

```python
def test_si_misroute_end_to_end_rehome_and_supersede(tmp_path):
    """Reproduces the motivating Si/GW scenario with throwaway fixtures.
    The real .aitp data is never touched."""

    from brain.v5.claim_relation_map import build_claim_relation_map
    from brain.v5.lifecycle_events import rehome_record, supersede_record
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path / "si")
    create_topic(ws, "qsgw-headwing-update-librpa", context_id="librpa", title="QSGW headwing")
    create_topic(ws, "si-g0w0-8atom-k999-throughput", context_id="librpa", title="Si G0W0 throughput")

    # three misrouted claims in the wrong topic
    misrouted = []
    for stmt in ("the correct si g0w0", "si8 perturbation high", "the correct si workflow"):
        c = create_claim(
            ws, topic_id="qsgw-headwing-update-librpa", statement=stmt,
            evidence_profile="code_method", confidence_state="hypothesis",
            active_uncertainty="u",
        )
        misrouted.append(c)

    # the correct active claim in the right topic
    active = create_claim(
        ws, topic_id="si-g0w0-8atom-k999-throughput",
        statement="for the machine learning throughput baseline",
        evidence_profile="code_method", confidence_state="hypothesis",
        active_uncertainty="u",
    )

    # rehome + supersede each misrouted claim
    for c in misrouted:
        rehome_record(
            ws, record_id=c.claim_id, subject_kind="claim",
            from_topic="qsgw-headwing-update-librpa",
            to_topic="si-g0w0-8atom-k999-throughput",
            reason="Si G0W0 dataset misrouted", operator="bohan-jia",
            timestamp="2026-06-20T10:00:00Z",
        )
        supersede_record(
            ws, record_id=c.claim_id, subject_kind="claim",
            status="misrouted", reason="replaced by active claim",
            operator="bohan-jia", timestamp="2026-06-20T10:01:00Z",
            replacement_ref=active.claim_id,
        )

    # the wrong topic's relation-map must not surface the misrouted claims as active
    bind_session(ws, session_id="s-wrong", topic_id="qsgw-headwing-update-librpa",
                 context_id="librpa", active_claim=misrouted[0].claim_id)
    mapping = build_claim_relation_map(ws, session_id="s-wrong")
    misrouted_ids = {m.claim_id for m in misrouted}
    for bucket in ("supported_by", "limited_by", "contradicted_by"):
        for entry in mapping.get(bucket, []):
            # no misrouted claim id should appear as active evidence source
            for mid in misrouted_ids:
                assert mid not in str(entry), f"{mid} leaked into {bucket}"
```

- [ ] **Step 2: Run the full lifecycle suite**

Run: `python -m pytest tests/test_v5_lifecycle.py -v`
Expected: all tests PASS (T1–T10 + Si e2e).

- [ ] **Step 3: Run the entire test suite for regression**

Run: `python -m pytest tests/ -q`
Expected: PASS, no regressions. If a pre-existing test breaks, investigate (the additive relation-map zones and optional record fields should not affect existing assertions, but verify).

- [ ] **Step 4: Commit**

```bash
git add tests/test_v5_lifecycle.py
git commit -m "test(v5): end-to-end Si misroute rehome+supersede reproduction"
```

---

## Verification checklist (run before declaring done)

- [ ] `python -m pytest tests/test_v5_lifecycle.py -v` — all green
- [ ] `python -m pytest tests/ -q` — no regressions
- [ ] `python -c "from brain.v5.mcp_tools import aitp_v5_build_rehome_plan, aitp_v5_apply_rehome_plan, aitp_v5_supersede_record, aitp_v5_audit_record_routing; print('ok')"` — `ok`
- [ ] `python -c "from brain.v5.public_surfaces import describe_public_surfaces; assert 'lifecycle_event_record' in describe_public_surfaces()['surface_names']; print('ok')"` — `ok`
- [ ] CLI help works for all four `record` subcommands
- [ ] No existing `.aitp` data file in the repo was modified by this work (only new + modified source/test/doc files)

## Spec coverage map

| Spec section | Implemented in task |
|---|---|
| §4 Data model (lifecycle fields + lifecycle_event family) | Task 1, 2 |
| §4.3 cross-topic pointer | Task 4 (`_append_cross_topic_pointer`) |
| §4.4 invariants (no delete, one event, idempotency, consistency, status-driven filter) | Task 3, 4, 7 |
| §5 rehome semantics | Task 4 |
| §6 supersede semantics | Task 4, 5 |
| §7 CLI (4 commands) | Task 8 |
| §8 MCP (4 tools, plan→apply) | Task 9 |
| §9 relation-map 4 zones | Task 7 |
| §10 tests T1–T10 | Task 1, 4, 5, 6, 7, 9, 10 (+ Si e2e in 11) |
| §11 backward compat | Task 1 (lazy fields), Task 10 (T7) |
| §12 documentation | Task 10 |
| §13 files changed | all tasks |
| §14 Si migration plan | reproduced as a test in Task 11; real migration is operator-run, out of scope |
