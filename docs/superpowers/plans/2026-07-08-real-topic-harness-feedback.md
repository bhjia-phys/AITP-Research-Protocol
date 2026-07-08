# Real-Topic Harness Feedback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the repo-local Phase 1 AITP real-topic harness feedback slice: trust-neutral monitor snapshots, skill patch proposals, NiO case/backlog draft generation, and run-dir provenance extractor planning.

**Architecture:** Add small v5 kernel record models, validators, and public surfaces. Keep all surfaces orientation-only or explicitly non-trust-changing, with generated NiO material returned as reviewable payloads rather than writing the external topics root. CLI and MCP wrappers stay thin over `brain/v5/harness_feedback.py`.

**Tech Stack:** Python dataclasses, existing AITP v5 Markdown store helpers, pytest, current `brain.v5.public_surfaces.require_valid_public_surface` validator registry.

## Global Constraints

- Do not create or edit `F:/AI_Workspace/Theoretical-Physics/research/aitp-topics` in Phase 1.
- Do not install or overwrite an official skill.
- Do not auto-promote diagnostic run output into evidence.
- Do not add trust-update shortcuts.
- Do not treat one failed run as a hard scientific rule.
- `monitor_snapshot.claim_trust_mutation` must be exactly `none`.
- `monitor_snapshot.can_update_claim_trust` must be false.
- `skill_patch_proposal.requires_human_review` must be true.
- `skill_patch_proposal.application_status="applied"` is valid only when `review_status="approved"`.
- Generated bundles must set `orientation_only=true`, `summary_inputs_trusted=false`, and `can_update_claim_trust=false`.

---

## File Structure

- Create `brain/v5/harness_feedback_contracts.py`: validators for monitor snapshots, skill patch proposals, harness feedback bundles, and run-dir extractor plans.
- Create `brain/v5/harness_feedback.py`: kernel functions to write trust-neutral records, build the NiO seed bundle, and return a non-writing extractor plan.
- Create `brain/v5/cli_harness_feedback.py`: focused CLI parser/dispatcher for harness feedback commands.
- Modify `brain/v5/models.py`: add `MonitorSnapshotRecord` and `SkillPatchProposalRecord` dataclasses.
- Modify `brain/v5/public_surfaces.py`: register the four new public surface names and validators.
- Modify `brain/v5/mcp_tools.py`: expose thin MCP wrappers.
- Modify `brain/v5/cli.py`: attach the harness-feedback parser and dispatcher.
- Create `tests/test_v5_harness_feedback.py`: focused tests for contracts, kernel functions, CLI, and MCP wrappers.

## Task 1: Record Models And Contract Validators

**Files:**
- Modify: `brain/v5/models.py`
- Create: `brain/v5/harness_feedback_contracts.py`
- Modify: `brain/v5/public_surfaces.py`
- Test: `tests/test_v5_harness_feedback.py`

**Interfaces:**
- Consumes: existing `ContractResult`, `_require_mapping`, `_require_nonempty_str`, `_require_list` from `brain.v5.contracts`.
- Produces:
  - `MonitorSnapshotRecord`
  - `SkillPatchProposalRecord`
  - `require_valid_monitor_snapshot_record(payload: dict[str, Any]) -> dict[str, Any]`
  - `require_valid_skill_patch_proposal_record(payload: dict[str, Any]) -> dict[str, Any]`

- [ ] **Step 1: Write failing tests for the two record contracts**

Add this test file:

```python
from __future__ import annotations

import pytest

from brain.v5.contracts import ContractError
from brain.v5.public_surfaces import require_valid_public_surface


def _valid_monitor_snapshot() -> dict:
    return {
        "ok": True,
        "kind": "monitor_snapshot",
        "snapshot_id": "monitor-snapshot-nio-1",
        "topic_id": "g0w0-magnetic-nio",
        "claim_id": "claim-nio",
        "tool_run_id": "tool-run-nio",
        "run_dir": "/remote/nio/run1",
        "job_id": "12345",
        "scheduler_state": {"squeue": "RUNNING", "sacct": "RUNNING"},
        "elapsed": "00:10:00",
        "output_file_sizes": {"librpa.out": 2048},
        "latest_log_markers": ["Reading librpa.in", "Self-energy"],
        "memory_status": {"MaxRSS": "2G"},
        "failure_markers": [],
        "interpretation_boundary": "Live scheduler state only; not physics evidence.",
        "claim_trust_mutation": "none",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_claim_trust": False,
    }


def test_monitor_snapshot_public_surface_accepts_trust_neutral_payload():
    payload = require_valid_public_surface("monitor_snapshot_record", _valid_monitor_snapshot())

    assert payload["kind"] == "monitor_snapshot"
    assert payload["claim_trust_mutation"] == "none"
    assert payload["can_update_claim_trust"] is False


def test_monitor_snapshot_public_surface_rejects_claim_trust_mutation():
    payload = _valid_monitor_snapshot()
    payload["claim_trust_mutation"] = "candidate"

    with pytest.raises(ContractError):
        require_valid_public_surface("monitor_snapshot_record", payload)


def test_monitor_snapshot_public_surface_rejects_claim_trust_authority():
    payload = _valid_monitor_snapshot()
    payload["can_update_claim_trust"] = True

    with pytest.raises(ContractError):
        require_valid_public_surface("monitor_snapshot_record", payload)


def _valid_skill_patch_proposal() -> dict:
    return {
        "ok": True,
        "kind": "skill_patch_proposal",
        "proposal_id": "skill-patch-nio-1",
        "skill_name": "fhi-aims-librpa-magnetic-gw-workflow",
        "current_version": "draft-0",
        "proposed_version": "draft-1",
        "patch_summary": "Add NiO magnetic G0W0/QSGW workflow checks.",
        "patch_body": "## Monitoring checklist\n- Record monitor snapshots.\n",
        "supporting_records": ["case:g0w0-magnetic-nio"],
        "trust_level": "diagnostic",
        "review_status": "draft",
        "application_status": "not_applied",
        "requires_human_review": True,
        "can_update_claim_trust": False,
        "summary_inputs_trusted": False,
        "orientation_only": True,
    }


def test_skill_patch_proposal_public_surface_accepts_review_gated_payload():
    payload = require_valid_public_surface("skill_patch_proposal_record", _valid_skill_patch_proposal())

    assert payload["requires_human_review"] is True
    assert payload["application_status"] == "not_applied"


def test_skill_patch_proposal_public_surface_requires_human_review():
    payload = _valid_skill_patch_proposal()
    payload["requires_human_review"] = False

    with pytest.raises(ContractError):
        require_valid_public_surface("skill_patch_proposal_record", payload)


def test_skill_patch_proposal_public_surface_rejects_unapproved_application():
    payload = _valid_skill_patch_proposal()
    payload["review_status"] = "draft"
    payload["application_status"] = "applied"

    with pytest.raises(ContractError):
        require_valid_public_surface("skill_patch_proposal_record", payload)
```

- [ ] **Step 2: Run contract tests to verify they fail**

Run:

```powershell
pytest tests/test_v5_harness_feedback.py -q
```

Expected: fail because `monitor_snapshot_record` and `skill_patch_proposal_record` are not registered public surfaces.

- [ ] **Step 3: Add dataclasses**

Append these dataclasses near `ToolRunRecord` and related evidence models in `brain/v5/models.py`:

```python
@dataclass
class MonitorSnapshotRecord:
    snapshot_id: str
    topic_id: str
    claim_id: str
    tool_run_id: str
    run_dir: str
    job_id: str
    scheduler_state: dict = field(default_factory=dict)
    elapsed: str = ""
    output_file_sizes: dict = field(default_factory=dict)
    latest_log_markers: list[str] = field(default_factory=list)
    memory_status: dict = field(default_factory=dict)
    failure_markers: list[str] = field(default_factory=list)
    interpretation_boundary: str = ""
    claim_trust_mutation: str = "none"
    summary_inputs_trusted: bool = False
    orientation_only: bool = True
    can_update_claim_trust: bool = False
    kind: str = "monitor_snapshot"


@dataclass
class SkillPatchProposalRecord:
    proposal_id: str
    skill_name: str
    current_version: str
    proposed_version: str
    patch_summary: str
    patch_body: str
    supporting_records: list[str] = field(default_factory=list)
    trust_level: str = "open"
    review_status: str = "draft"
    application_status: str = "not_applied"
    requires_human_review: bool = True
    can_update_claim_trust: bool = False
    summary_inputs_trusted: bool = False
    orientation_only: bool = True
    kind: str = "skill_patch_proposal"
```

- [ ] **Step 4: Add contract validators**

Create `brain/v5/harness_feedback_contracts.py` with:

```python
"""Contracts for trust-neutral real-topic harness feedback surfaces."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_list, _require_mapping, _require_nonempty_str


def validate_monitor_snapshot_record(payload: dict[str, Any], *, path: str = "monitor_snapshot_record") -> ContractResult:
    result = _validate_base(payload, path, kind="monitor_snapshot")
    if result.issues:
        return result
    for key in ("snapshot_id", "topic_id", "claim_id", "tool_run_id", "run_dir", "job_id", "elapsed", "interpretation_boundary"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("scheduler_state", "output_file_sizes", "memory_status"):
        _require_mapping(payload.get(key), f"{path}.{key}", result)
    for key in ("latest_log_markers", "failure_markers"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    _require_false_flags(payload, path, result)
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    if payload.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")
    return result


def require_valid_monitor_snapshot_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_monitor_snapshot_record(payload), payload)


def validate_skill_patch_proposal_record(payload: dict[str, Any], *, path: str = "skill_patch_proposal_record") -> ContractResult:
    result = _validate_base(payload, path, kind="skill_patch_proposal")
    if result.issues:
        return result
    for key in ("proposal_id", "skill_name", "current_version", "proposed_version", "patch_summary", "patch_body", "trust_level", "review_status", "application_status"):
        _require_nonempty_str(payload, key, path, result)
    _require_list(payload.get("supporting_records"), f"{path}.supporting_records", result)
    if payload.get("trust_level") not in {"diagnostic", "validated", "deprecated", "open"}:
        result.add(f"{path}.trust_level", "must be diagnostic, validated, deprecated, or open")
    if payload.get("review_status") not in {"draft", "ready_for_review", "approved", "rejected", "applied"}:
        result.add(f"{path}.review_status", "must be draft, ready_for_review, approved, rejected, or applied")
    if payload.get("application_status") not in {"not_applied", "applied", "superseded"}:
        result.add(f"{path}.application_status", "must be not_applied, applied, or superseded")
    if payload.get("application_status") == "applied" and payload.get("review_status") != "approved":
        result.add(f"{path}.application_status", "cannot be applied unless review_status is approved")
    if payload.get("requires_human_review") is not True:
        result.add(f"{path}.requires_human_review", "must be true")
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    _require_false_flags(payload, path, result)
    return result


def require_valid_skill_patch_proposal_record(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_skill_patch_proposal_record(payload), payload)


def _validate_base(payload: Any, path: str, *, kind: str) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("kind") != kind:
        result.add(f"{path}.kind", f"must be {kind!r}")
    return result


def _require_false_flags(payload: dict[str, Any], path: str, result: ContractResult) -> None:
    if payload.get("summary_inputs_trusted") is not False:
        result.add(f"{path}.summary_inputs_trusted", "must be false")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")


def _require_valid(result: ContractResult, payload: dict[str, Any]) -> dict[str, Any]:
    if not result.ok:
        raise ContractError(result)
    return payload
```

- [ ] **Step 5: Register public surfaces**

Modify `brain/v5/public_surfaces.py`:

1. Add surface names to `_PUBLIC_SURFACE_NAMES`:

```python
"harness_feedback_bundle",
"monitor_snapshot_record",
"run_dir_provenance_extractor_plan",
"skill_patch_proposal_record",
```

2. Add purposes:

```python
"monitor_snapshot_record": "contracted live scheduler/run observation that is orientation-only and cannot update claim trust",
"skill_patch_proposal_record": "contracted review-gated skill patch proposal derived from real-topic experience without applying the patch or updating claim trust",
"harness_feedback_bundle": "reviewable real-topic harness feedback case/backlog/skill-draft bundle that targets the meta-topic without writing it",
"run_dir_provenance_extractor_plan": "non-writing plan for extracting reviewable tool-run, artifact, monitor snapshot, and validation checklist payload candidates from a run directory",
```

3. Import validators inside `_public_surface_validators`:

```python
from brain.v5.harness_feedback_contracts import (
    require_valid_harness_feedback_bundle,
    require_valid_monitor_snapshot_record,
    require_valid_run_dir_provenance_extractor_plan,
    require_valid_skill_patch_proposal_record,
)
```

4. Add validator mapping entries with the same keys.

- [ ] **Step 6: Run contract tests**

Run:

```powershell
pytest tests/test_v5_harness_feedback.py -q
```

Expected: the first six tests pass after the public surface registration is complete.

## Task 2: Harness Feedback Kernel Bundle And Extractor Plan

**Files:**
- Modify: `brain/v5/harness_feedback_contracts.py`
- Create: `brain/v5/harness_feedback.py`
- Test: `tests/test_v5_harness_feedback.py`

**Interfaces:**
- Consumes: `MonitorSnapshotRecord`, `SkillPatchProposalRecord`, `WorkspacePaths`, `write_record`.
- Produces:
  - `record_monitor_snapshot(ws: WorkspacePaths, **kwargs) -> MonitorSnapshotRecord`
  - `record_skill_patch_proposal(ws: WorkspacePaths, **kwargs) -> SkillPatchProposalRecord`
  - `monitor_snapshot_payload(record: MonitorSnapshotRecord) -> dict[str, Any]`
  - `skill_patch_proposal_payload(record: SkillPatchProposalRecord) -> dict[str, Any]`
  - `build_nio_harness_feedback_bundle() -> dict[str, Any]`
  - `plan_run_dir_provenance_extractor(case_id: str = "g0w0-magnetic-nio") -> dict[str, Any]`

- [ ] **Step 1: Extend tests for kernel records and generated bundle**

Append tests to `tests/test_v5_harness_feedback.py`:

```python
def test_kernel_records_monitor_snapshot_without_trust_mutation(tmp_path):
    from brain.v5.harness_feedback import monitor_snapshot_payload, record_monitor_snapshot
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    record = record_monitor_snapshot(
        ws,
        snapshot_id="monitor-snapshot-nio-1",
        topic_id="g0w0-magnetic-nio",
        claim_id="claim-nio",
        tool_run_id="tool-run-nio",
        run_dir="/remote/nio/run1",
        job_id="12345",
        scheduler_state={"squeue": "RUNNING"},
        elapsed="00:10:00",
        output_file_sizes={"librpa.out": 2048},
        latest_log_markers=["Self-energy"],
        memory_status={"MaxRSS": "2G"},
        failure_markers=[],
        interpretation_boundary="Live scheduler state only.",
    )

    payload = monitor_snapshot_payload(record)
    assert payload["claim_trust_mutation"] == "none"
    assert payload["can_update_claim_trust"] is False
    assert (ws.registry_dir("monitor_snapshots") / f"{record.snapshot_id}.md").exists()


def test_kernel_records_review_gated_skill_patch_proposal(tmp_path):
    from brain.v5.harness_feedback import record_skill_patch_proposal, skill_patch_proposal_payload
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path)
    record = record_skill_patch_proposal(
        ws,
        proposal_id="skill-patch-nio-1",
        skill_name="fhi-aims-librpa-magnetic-gw-workflow",
        current_version="draft-0",
        proposed_version="draft-1",
        patch_summary="Add NiO checks.",
        patch_body="## Trust-update gate\nDiagnostic runs do not update trust.\n",
        supporting_records=["case:g0w0-magnetic-nio"],
        trust_level="diagnostic",
    )

    payload = skill_patch_proposal_payload(record)
    assert payload["requires_human_review"] is True
    assert payload["application_status"] == "not_applied"
    assert (ws.registry_dir("skill_patch_proposals") / f"{record.proposal_id}.md").exists()


def test_nio_harness_feedback_bundle_contains_required_sections():
    from brain.v5.harness_feedback import build_nio_harness_feedback_bundle

    payload = require_valid_public_surface("harness_feedback_bundle", build_nio_harness_feedback_bundle())
    case_markdown = payload["files"]["cases/g0w0-magnetic-nio.md"]
    for heading in (
        "## Timeline",
        "## Major Run Directory Classes",
        "## AIMS Input-Contract Lessons",
        "## LibRPA Input-Contract Lessons",
        "## G0W0 Diagnostic/Results Boundary",
        "## QSGW Smoke Workflow",
        "## Proposed Skill Outline",
    ):
        assert heading in case_markdown
    assert payload["orientation_only"] is True
    assert payload["can_update_claim_trust"] is False


def test_nio_backlog_items_have_required_fields():
    from brain.v5.harness_feedback import build_nio_harness_feedback_bundle

    payload = build_nio_harness_feedback_bundle()
    required = {
        "title",
        "source_case",
        "real_topic_evidence",
        "pain_point",
        "proposed_change",
        "minimal_implementation_slice",
        "acceptance_test",
        "risk",
        "linked_topic_records_artifacts",
        "status",
    }
    assert len(payload["backlog_items"]) >= 10
    for item in payload["backlog_items"]:
        assert required <= set(item)


def test_run_dir_provenance_extractor_plan_is_non_writing():
    from brain.v5.harness_feedback import plan_run_dir_provenance_extractor

    payload = require_valid_public_surface("run_dir_provenance_extractor_plan", plan_run_dir_provenance_extractor())
    assert payload["writes_records"] is False
    assert payload["can_update_claim_trust"] is False
    assert "monitor_snapshot_candidate" in payload["outputs"]
```

- [ ] **Step 2: Run tests to verify bundle functions are missing**

Run:

```powershell
pytest tests/test_v5_harness_feedback.py -q
```

Expected: tests fail because `brain.v5.harness_feedback` and bundle validators are not implemented.

- [ ] **Step 3: Add bundle and plan validators**

Extend `brain/v5/harness_feedback_contracts.py` with:

```python
def validate_harness_feedback_bundle(payload: dict[str, Any], *, path: str = "harness_feedback_bundle") -> ContractResult:
    result = _validate_base(payload, path, kind="harness_feedback_bundle")
    if result.issues:
        return result
    for key in ("case_id", "meta_topic_path", "case_report_path", "backlog_path", "skill_draft_path"):
        _require_nonempty_str(payload, key, path, result)
    _require_mapping(payload.get("files"), f"{path}.files", result)
    _require_list(payload.get("backlog_items"), f"{path}.backlog_items", result)
    for index, item in enumerate(payload.get("backlog_items") or []):
        if not isinstance(item, dict):
            result.add(f"{path}.backlog_items[{index}]", "must be a mapping")
            continue
        for key in ("title", "source_case", "real_topic_evidence", "pain_point", "proposed_change", "minimal_implementation_slice", "acceptance_test", "risk", "linked_topic_records_artifacts", "status"):
            _require_nonempty_str(item, key, f"{path}.backlog_items[{index}]", result)
    _require_list(payload.get("record_schemas"), f"{path}.record_schemas", result)
    _require_false_flags(payload, path, result)
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    if payload.get("writes_external_topics_root") is not False:
        result.add(f"{path}.writes_external_topics_root", "must be false")
    return result


def require_valid_harness_feedback_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_harness_feedback_bundle(payload), payload)


def validate_run_dir_provenance_extractor_plan(payload: dict[str, Any], *, path: str = "run_dir_provenance_extractor_plan") -> ContractResult:
    result = _validate_base(payload, path, kind="run_dir_provenance_extractor_plan")
    if result.issues:
        return result
    for key in ("case_id", "purpose", "acceptance_test"):
        _require_nonempty_str(payload, key, path, result)
    for key in ("inputs", "outputs", "extractors", "review_gates"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    if payload.get("writes_records") is not False:
        result.add(f"{path}.writes_records", "must be false")
    _require_false_flags(payload, path, result)
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    return result


def require_valid_run_dir_provenance_extractor_plan(payload: dict[str, Any]) -> dict[str, Any]:
    return _require_valid(validate_run_dir_provenance_extractor_plan(payload), payload)
```

- [ ] **Step 4: Implement `brain/v5/harness_feedback.py`**

Create a focused kernel module with these functions:

```python
"""Trust-neutral real-topic harness feedback records and generated bundles."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from brain.v5.models import MonitorSnapshotRecord, SkillPatchProposalRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import write_record


def record_monitor_snapshot(ws: WorkspacePaths, **kwargs: Any) -> MonitorSnapshotRecord:
    record = MonitorSnapshotRecord(**kwargs)
    record.claim_trust_mutation = "none"
    record.summary_inputs_trusted = False
    record.orientation_only = True
    record.can_update_claim_trust = False
    write_record(
        ws.registry_dir("monitor_snapshots") / f"{record.snapshot_id}.md",
        record,
        body=f"# Monitor Snapshot\n\n{record.interpretation_boundary}\n",
    )
    return record


def monitor_snapshot_payload(record: MonitorSnapshotRecord) -> dict[str, Any]:
    return {"ok": True, **asdict(record)}


def record_skill_patch_proposal(ws: WorkspacePaths, **kwargs: Any) -> SkillPatchProposalRecord:
    record = SkillPatchProposalRecord(**kwargs)
    record.requires_human_review = True
    record.summary_inputs_trusted = False
    record.orientation_only = True
    record.can_update_claim_trust = False
    write_record(
        ws.registry_dir("skill_patch_proposals") / f"{record.proposal_id}.md",
        record,
        body=f"# Skill Patch Proposal\n\n{record.patch_body}\n",
    )
    return record


def skill_patch_proposal_payload(record: SkillPatchProposalRecord) -> dict[str, Any]:
    return {"ok": True, **asdict(record)}
```

Then add constants/functions for `build_nio_harness_feedback_bundle()` and
`plan_run_dir_provenance_extractor()` using the content and backlog items from
the approved design spec. The bundle must include:

```python
{
    "ok": True,
    "kind": "harness_feedback_bundle",
    "case_id": "g0w0-magnetic-nio",
    "meta_topic_path": "research/aitp-topics/_meta/aitp-harness-real-topic-feedback",
    "case_report_path": "cases/g0w0-magnetic-nio.md",
    "backlog_path": "backlog.md",
    "skill_draft_path": "skill-patch-drafts/fhi-aims-librpa-magnetic-gw-workflow.SKILL.draft.md",
    "files": {...},
    "backlog_items": [...],
    "record_schemas": ["monitor_snapshot", "skill_patch_proposal"],
    "writes_external_topics_root": False,
    "summary_inputs_trusted": False,
    "orientation_only": True,
    "can_update_claim_trust": False,
}
```

The extractor plan must return `outputs` containing
`tool_run_candidate`, `artifact_candidates`, `monitor_snapshot_candidate`, and
`validation_checklist_prefill`.

- [ ] **Step 5: Run tests**

Run:

```powershell
pytest tests/test_v5_harness_feedback.py -q
```

Expected: all tests in `test_v5_harness_feedback.py` pass.

## Task 3: CLI And MCP Access

**Files:**
- Create: `brain/v5/cli_harness_feedback.py`
- Modify: `brain/v5/cli.py`
- Modify: `brain/v5/mcp_tools.py`
- Test: `tests/test_v5_harness_feedback.py`

**Interfaces:**
- Consumes: kernel functions from `brain.v5.harness_feedback`.
- Produces:
  - CLI: `aitp-v5 harness-feedback nio-seed`
  - CLI: `aitp-v5 harness-feedback extractor-plan`
  - MCP wrapper: `aitp_v5_build_harness_feedback_seed_bundle(base: str = "") -> dict`
  - MCP wrapper: `aitp_v5_plan_run_dir_provenance_extractor(base: str = "", case_id: str = "g0w0-magnetic-nio") -> dict`

- [ ] **Step 1: Add CLI/MCP tests**

Append tests:

```python
def test_cli_harness_feedback_nio_seed_returns_bundle(capsys, tmp_path):
    from brain.v5.cli import main

    assert main(["--base", str(tmp_path), "harness-feedback", "nio-seed"]) == 0
    payload = __import__("json").loads(capsys.readouterr().out)
    assert payload["kind"] == "harness_feedback_bundle"
    assert payload["case_id"] == "g0w0-magnetic-nio"
    assert payload["writes_external_topics_root"] is False


def test_cli_harness_feedback_extractor_plan_returns_non_writing_plan(capsys, tmp_path):
    from brain.v5.cli import main

    assert main(["--base", str(tmp_path), "harness-feedback", "extractor-plan"]) == 0
    payload = __import__("json").loads(capsys.readouterr().out)
    assert payload["kind"] == "run_dir_provenance_extractor_plan"
    assert payload["writes_records"] is False


def test_mcp_harness_feedback_wrappers(tmp_path):
    from brain.v5.mcp_tools import (
        aitp_v5_build_harness_feedback_seed_bundle,
        aitp_v5_plan_run_dir_provenance_extractor,
    )

    bundle = aitp_v5_build_harness_feedback_seed_bundle(str(tmp_path))
    plan = aitp_v5_plan_run_dir_provenance_extractor(str(tmp_path))
    assert bundle["kind"] == "harness_feedback_bundle"
    assert plan["kind"] == "run_dir_provenance_extractor_plan"
```

- [ ] **Step 2: Run tests to verify wrappers are missing**

Run:

```powershell
pytest tests/test_v5_harness_feedback.py -q
```

Expected: wrapper tests fail because CLI/MCP entrypoints do not exist yet.

- [ ] **Step 3: Create CLI dispatcher**

Create `brain/v5/cli_harness_feedback.py`:

```python
"""CLI parser and dispatcher for trust-neutral harness feedback surfaces."""

from __future__ import annotations

import argparse

from brain.v5.harness_feedback import build_nio_harness_feedback_bundle, plan_run_dir_provenance_extractor
from brain.v5.public_surfaces import require_valid_public_surface


def add_harness_feedback_parser(sp: argparse._SubParsersAction) -> None:
    parser = sp.add_parser("harness-feedback")
    sub = parser.add_subparsers(dest="harness_feedback_command", required=True)
    sub.add_parser("nio-seed")
    extractor = sub.add_parser("extractor-plan")
    extractor.add_argument("--case-id", default="g0w0-magnetic-nio")


def dispatch_harness_feedback_command(args: argparse.Namespace, ws) -> dict:
    if args.harness_feedback_command == "nio-seed":
        return require_valid_public_surface("harness_feedback_bundle", build_nio_harness_feedback_bundle())
    if args.harness_feedback_command == "extractor-plan":
        return require_valid_public_surface(
            "run_dir_provenance_extractor_plan",
            plan_run_dir_provenance_extractor(case_id=args.case_id),
        )
    raise SystemExit(f"unsupported harness-feedback command: {args.harness_feedback_command}")
```

- [ ] **Step 4: Wire CLI into `brain/v5/cli.py`**

Add imports near existing CLI parser imports:

```python
from brain.v5.cli_harness_feedback import add_harness_feedback_parser, dispatch_harness_feedback_command
```

In `_build_parser()` after other `add_*_parser` calls:

```python
add_harness_feedback_parser(sp)
```

In `_dispatch(args)` before the final unsupported command check:

```python
if args.command == "harness-feedback":
    return dispatch_harness_feedback_command(args, ws)
```

- [ ] **Step 5: Add MCP wrappers**

In `brain/v5/mcp_tools.py`, import:

```python
from brain.v5.harness_feedback import build_nio_harness_feedback_bundle, plan_run_dir_provenance_extractor
```

Add functions:

```python
def aitp_v5_build_harness_feedback_seed_bundle(base: str = "") -> dict:
    return require_valid_public_surface("harness_feedback_bundle", build_nio_harness_feedback_bundle())


def aitp_v5_plan_run_dir_provenance_extractor(base: str = "", *, case_id: str = "g0w0-magnetic-nio") -> dict:
    return require_valid_public_surface(
        "run_dir_provenance_extractor_plan",
        plan_run_dir_provenance_extractor(case_id=case_id),
    )
```

- [ ] **Step 6: Run wrapper tests**

Run:

```powershell
pytest tests/test_v5_harness_feedback.py -q
```

Expected: all harness-feedback tests pass.

## Task 4: Targeted Regression And Commit

**Files:**
- Verify all files touched in Tasks 1-3.

**Interfaces:**
- Consumes: all new harness-feedback surfaces.
- Produces: committed repo-local Phase 1 implementation.

- [ ] **Step 1: Run targeted tests**

Run:

```powershell
pytest tests/test_v5_harness_feedback.py tests/test_v5_hpc_cockpit.py tests/test_v5_evidence_tools.py -q
```

Expected: all selected tests pass. These cover the new surfaces plus adjacent HPC/tool-run behavior.

- [ ] **Step 2: Inspect public surfaces smoke**

Run:

```powershell
python -m brain.v5.cli --base . harness-feedback nio-seed
```

Expected JSON contains:

```json
"kind": "harness_feedback_bundle"
```

Run:

```powershell
python -m brain.v5.cli --base . harness-feedback extractor-plan
```

Expected JSON contains:

```json
"kind": "run_dir_provenance_extractor_plan"
```

- [ ] **Step 3: Inspect git diff**

Run:

```powershell
git diff --stat
git diff --check
git status --short --branch
```

Expected: no whitespace errors; only planned files are modified or added.

- [ ] **Step 4: Commit implementation**

Run:

```powershell
git add brain/v5/models.py brain/v5/harness_feedback_contracts.py brain/v5/harness_feedback.py brain/v5/cli_harness_feedback.py brain/v5/public_surfaces.py brain/v5/mcp_tools.py brain/v5/cli.py tests/test_v5_harness_feedback.py docs/superpowers/plans/2026-07-08-real-topic-harness-feedback.md
git commit -m "v5: add trust-neutral harness feedback slice"
```

Expected: commit succeeds and only planned files are included.

## Self-Review

- Spec coverage: Tasks 1-3 cover `monitor_snapshot`, `skill_patch_proposal`, NiO case/backlog drafting, and run-dir provenance extractor planning. Task 4 covers verification and commit.
- Placeholder scan: the plan contains no undefined placeholders or deferred implementation language.
- Type consistency: public surface names, function names, dataclass names, and test payload keys match across tasks.
