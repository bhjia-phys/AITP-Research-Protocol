from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .runtime_schema_promotion_bridge import collect_runtime_schema_context
from .runtime_projection_handler import append_transition_history


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _normalize_human_modifications(
    rows: list[dict[str, Any]] | None,
    *,
    recorded_at: str,
    recorded_by: str,
) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        field = str(row.get("field") or "").strip()
        change = str(row.get("change") or "").strip()
        reason = str(row.get("reason") or "").strip()
        if not field or not change or not reason:
            continue
        key = (field.lower(), change.lower(), reason.lower())
        if key in seen:
            continue
        seen.add(key)
        normalized.append(
            {
                "field": field,
                "change": change,
                "reason": reason,
                "recorded_at": recorded_at,
                "recorded_by": recorded_by,
            }
        )
    return normalized


def promotion_gate_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# L2 promotion gate",
        "",
        f"- Topic slug: `{payload['topic_slug']}`",
        f"- Run id: `{payload['run_id']}`",
        f"- Candidate id: `{payload['candidate_id']}`",
        f"- Candidate type: `{payload['candidate_type']}`",
        f"- Title: `{payload['title']}`",
        f"- Status: `{payload['status']}`",
        f"- Route: `{payload['route']}`",
        f"- Backend id: `{payload.get('backend_id') or '(missing)'}`",
        f"- Target backend root: `{payload.get('target_backend_root') or '(missing)'}`",
        f"- Review mode: `{payload.get('review_mode') or 'human'}`",
        f"- Canonical layer: `{payload.get('canonical_layer') or 'L2'}`",
        f"- Source layer: `{payload.get('source_layer') or 'L4'}`",
        f"- Requested destination layer: `{payload.get('requested_destination_layer') or payload.get('canonical_layer') or 'L2'}`",
        f"- Resolved destination layer: `{payload.get('resolved_destination_layer') or '(pending)'}`",
        f"- Approval change kind: `{payload.get('approval_change_kind') or '(pending)'}`",
        f"- Coverage status: `{payload.get('coverage_status') or 'not_audited'}`",
        f"- Consensus status: `{payload.get('consensus_status') or 'not_requested'}`",
        f"- Regression gate status: `{payload.get('regression_gate_status') or 'not_audited'}`",
        f"- Topic completion status: `{payload.get('topic_completion_status') or 'not_assessed'}`",
        f"- Split required: `{payload.get('split_required')}`",
        f"- Cited recovery required: `{payload.get('cited_recovery_required')}`",
        f"- Requested by: `{payload['requested_by']}` at `{payload['requested_at']}`",
        f"- Approved by: `{payload.get('approved_by') or '(pending)'}` at `{payload.get('approved_at') or '(pending)'}`",
        f"- Rejected by: `{payload.get('rejected_by') or '(n/a)'}` at `{payload.get('rejected_at') or '(n/a)'}`",
        "",
        "## Intended L2 targets",
        "",
    ]
    for target in payload.get("intended_l2_targets") or ["(missing)"]:
        lines.append(f"- `{target}`")
    lines.extend(["", "## Regression support", ""])
    for target in payload.get("supporting_regression_question_ids") or ["(missing)"]:
        lines.append(f"- question: `{target}`")
    for target in payload.get("supporting_oracle_ids") or []:
        lines.append(f"- oracle: `{target}`")
    for target in payload.get("supporting_regression_run_ids") or []:
        lines.append(f"- run: `{target}`")
    lines.extend(["", "## Promotion blockers", ""])
    for blocker in payload.get("promotion_blockers") or ["(none)"]:
        lines.append(f"- {blocker}")
    lines.extend(["", "## Runtime Schema Context", ""])
    for artifact_type in payload.get("runtime_schema_types") or ["(none)"]:
        lines.append(f"- `{artifact_type}`")
    lines.extend(["", "## Human modifications", ""])
    for row in payload.get("human_modifications") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('field') or '(missing)'}` -> {row.get('change') or '(missing)'}"
            )
            lines.append(f"  reason: {row.get('reason') or '(missing)'}")
            lines.append(
                f"  recorded: `{row.get('recorded_at') or '(missing)'}` by `{row.get('recorded_by') or '(missing)'}`"
            )
        else:
            lines.append(f"- {row}")
    lines.extend(
        [
            "",
            "## Candidate summary",
            "",
            payload.get("summary") or "(missing)",
            "",
            "## Operator rule",
            "",
        ]
    )
    if payload["status"] == "approved":
        if payload.get("review_mode") == "ai_auto":
            lines.append("- Auto review passed. `aitp promote ...` may write the distilled unit into the configured `L2_auto` backend layer.")
        else:
            lines.append("- Human approval is present. `aitp promote ...` may write the distilled unit into the configured L2 backend.")
    elif payload["status"] == "promoted":
        lines.append("- Promotion already ran. Re-check the decision and backend writeback artifacts before editing further.")
    else:
        if payload.get("review_mode") == "ai_auto":
            lines.append("- Auto promotion is blocked until coverage, consensus, regression, split-clearance, and gap-honesty artifacts satisfy the configured gate.")
        else:
            lines.append("- L2 promotion is blocked until a human explicitly approves or rejects this request.")
    if payload.get("notes"):
        lines.extend(["", "## Notes", "", payload["notes"], ""])
    return "\n".join(lines) + "\n"


def write_promotion_gate(self, topic_slug: str, payload: dict[str, Any]) -> dict[str, str]:
    paths = self._promotion_gate_paths(topic_slug)
    _write_json(paths["json"], payload)
    _write_text(paths["note"], promotion_gate_markdown(payload))
    return {
        "promotion_gate_path": str(paths["json"]),
        "promotion_gate_note_path": str(paths["note"]),
    }


def load_promotion_gate(self, topic_slug: str) -> dict[str, Any] | None:
    return _read_json(self._promotion_gate_paths(topic_slug)["json"])


def append_promotion_gate_log(self, topic_slug: str, run_id: str, row: dict[str, Any]) -> str:
    log_path = self._promotion_gate_log_path(topic_slug, run_id)
    rows = _read_jsonl(log_path)
    rows.append(row)
    _write_jsonl(log_path, rows)
    return str(log_path)


def request_promotion(
    self,
    *,
    topic_slug: str,
    candidate_id: str,
    run_id: str | None = None,
    route: str = "L3->L4->L2",
    backend_id: str | None = None,
    target_backend_root: str | None = None,
    requested_by: str = "aitp-cli",
    notes: str | None = None,
) -> dict[str, Any]:
    resolved_run_id = self._resolve_run_id(topic_slug, run_id)
    if not resolved_run_id:
        raise FileNotFoundError(f"Unable to resolve a feedback/validation run for topic {topic_slug}")
    candidate = self._load_candidate(topic_slug, resolved_run_id, candidate_id)
    runtime_schema_context = collect_runtime_schema_context(
        self,
        topic_slug=topic_slug,
        run_id=resolved_run_id,
        candidate_id=candidate_id,
    )
    gate_payload = {
        "topic_slug": topic_slug,
        "run_id": resolved_run_id,
        "candidate_id": candidate_id,
        "candidate_type": str(candidate.get("candidate_type") or ""),
        "title": str(candidate.get("title") or ""),
        "summary": str(candidate.get("summary") or ""),
        "route": route,
        "status": "pending_human_approval",
        "intended_l2_targets": self._dedupe_strings(list(candidate.get("intended_l2_targets") or [])),
        "backend_id": str(backend_id or ""),
        "target_backend_root": str(target_backend_root or ""),
        "review_mode": "human",
        "canonical_layer": "L2",
        "coverage_status": "not_audited",
        "consensus_status": "not_requested",
        "regression_gate_status": "not_audited",
        "topic_completion_status": str(candidate.get("topic_completion_status") or "not_assessed"),
        "source_layer": "L4",
        "requested_destination_layer": "L2",
        "resolved_destination_layer": None,
        "approval_change_kind": "pending_review",
        "human_modifications": [],
        "supporting_regression_question_ids": self._dedupe_strings(
            list(candidate.get("supporting_regression_question_ids") or [])
        ),
        "supporting_oracle_ids": self._dedupe_strings(list(candidate.get("supporting_oracle_ids") or [])),
        "supporting_regression_run_ids": self._dedupe_strings(
            list(candidate.get("supporting_regression_run_ids") or [])
        ),
        "runtime_schema_types": list(runtime_schema_context.get("artifact_types") or []),
        "runtime_schema_paths": dict(runtime_schema_context.get("schema_paths") or {}),
        "runtime_artifact_paths": dict(runtime_schema_context.get("artifact_paths") or {}),
        "runtime_schema_context": runtime_schema_context,
        "promotion_blockers": self._dedupe_strings(list(candidate.get("promotion_blockers") or [])),
        "split_required": _as_bool(candidate.get("split_required")),
        "cited_recovery_required": _as_bool(candidate.get("cited_recovery_required")),
        "followup_gap_ids": self._dedupe_strings(list(candidate.get("followup_gap_ids") or [])),
        "merge_outcome": "pending",
        "requested_by": requested_by,
        "requested_at": _now_iso(),
        "approved_by": None,
        "approved_at": None,
        "rejected_by": None,
        "rejected_at": None,
        "promoted_by": None,
        "promoted_at": None,
        "promoted_units": [],
        "notes": notes or "",
    }
    gate_payload["requested_destination_layer"] = str(gate_payload.get("canonical_layer") or "L2")
    paths = write_promotion_gate(self, topic_slug, gate_payload)
    log_path = append_promotion_gate_log(
        self,
        topic_slug,
        resolved_run_id,
        {
            "event": "requested",
            "candidate_id": candidate_id,
            "status": gate_payload["status"],
            "updated_by": requested_by,
            "updated_at": gate_payload["requested_at"],
            "backend_id": gate_payload["backend_id"],
            "target_backend_root": gate_payload["target_backend_root"],
            "notes": gate_payload["notes"],
        },
    )
    return {
        **gate_payload,
        **paths,
        "promotion_gate_log_path": log_path,
    }


def approve_promotion(
    self,
    *,
    topic_slug: str,
    candidate_id: str,
    run_id: str | None = None,
    approved_by: str = "aitp-cli",
    notes: str | None = None,
    human_modifications: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    gate_payload = load_promotion_gate(self, topic_slug)
    if gate_payload is None:
        raise FileNotFoundError(f"Promotion gate missing for topic {topic_slug}")
    resolved_run_id = self._resolve_run_id(topic_slug, run_id or str(gate_payload.get("run_id") or ""))
    if not resolved_run_id:
        raise FileNotFoundError(f"Unable to resolve a validation run for topic {topic_slug}")
    if str(gate_payload.get("candidate_id") or "") != candidate_id:
        raise ValueError(f"Promotion gate candidate mismatch: expected {gate_payload.get('candidate_id')}, got {candidate_id}")
    gate_payload["status"] = "approved"
    gate_payload["approved_by"] = approved_by
    gate_payload["approved_at"] = _now_iso()
    gate_payload["resolved_destination_layer"] = str(gate_payload.get("canonical_layer") or "L2")
    normalized_modifications = _normalize_human_modifications(
        human_modifications,
        recorded_at=str(gate_payload["approved_at"]),
        recorded_by=approved_by,
    )
    gate_payload["human_modifications"] = normalized_modifications
    gate_payload["approval_change_kind"] = (
        "approved_with_modifications" if normalized_modifications else "approved_as_submitted"
    )
    if notes is not None:
        gate_payload["notes"] = notes
    paths = write_promotion_gate(self, topic_slug, gate_payload)
    log_path = append_promotion_gate_log(
        self,
        topic_slug,
        resolved_run_id,
        {
            "event": "approved",
            "candidate_id": candidate_id,
            "status": gate_payload["status"],
            "updated_by": approved_by,
            "updated_at": gate_payload["approved_at"],
            "approval_change_kind": gate_payload["approval_change_kind"],
            "human_modification_count": len(gate_payload.get("human_modifications") or []),
            "human_modifications": gate_payload.get("human_modifications") or [],
            "notes": gate_payload.get("notes") or "",
        },
    )
    return {
        **gate_payload,
        **paths,
        "promotion_gate_log_path": log_path,
    }


def reject_promotion(
    self,
    *,
    topic_slug: str,
    candidate_id: str,
    run_id: str | None = None,
    rejected_by: str = "aitp-cli",
    notes: str | None = None,
) -> dict[str, Any]:
    gate_payload = load_promotion_gate(self, topic_slug)
    if gate_payload is None:
        raise FileNotFoundError(f"Promotion gate missing for topic {topic_slug}")
    resolved_run_id = self._resolve_run_id(topic_slug, run_id or str(gate_payload.get("run_id") or ""))
    if not resolved_run_id:
        raise FileNotFoundError(f"Unable to resolve a validation run for topic {topic_slug}")
    if str(gate_payload.get("candidate_id") or "") != candidate_id:
        raise ValueError(f"Promotion gate candidate mismatch: expected {gate_payload.get('candidate_id')}, got {candidate_id}")
    gate_payload["status"] = "rejected"
    gate_payload["rejected_by"] = rejected_by
    gate_payload["rejected_at"] = _now_iso()
    gate_payload["resolved_destination_layer"] = "L3"
    gate_payload["approval_change_kind"] = "rejected"
    if notes is not None:
        gate_payload["notes"] = notes
    paths = write_promotion_gate(self, topic_slug, gate_payload)
    log_path = append_promotion_gate_log(
        self,
        topic_slug,
        resolved_run_id,
        {
            "event": "rejected",
            "candidate_id": candidate_id,
            "status": gate_payload["status"],
            "updated_by": rejected_by,
            "updated_at": gate_payload["rejected_at"],
            "notes": gate_payload.get("notes") or "",
        },
    )
    append_transition_history(
        topic_slug,
        {
            "run_id": resolved_run_id,
            "event_kind": "promotion_rejected",
            "from_layer": str(gate_payload.get("source_layer") or "L4"),
            "to_layer": str(gate_payload.get("resolved_destination_layer") or "L3"),
            "reason": str(gate_payload.get("notes") or "Promotion was rejected and the topic returned to a lower layer."),
            "evidence_refs": [
                self._relativize(self._promotion_gate_paths(topic_slug)["json"]),
                self._relativize(self._promotion_gate_paths(topic_slug)["note"]),
                self._relativize(Path(log_path)),
            ],
            "candidate_id": candidate_id,
            "recorded_at": str(gate_payload.get("rejected_at") or _now_iso()),
            "recorded_by": rejected_by,
        },
        kernel_root=self.kernel_root,
    )
    return {
        **gate_payload,
        **paths,
        "promotion_gate_log_path": log_path,
    }
