from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import hashlib
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .tpkn_bridge import (
    build_tpkn_unit,
    choose_source_row,
    derive_tpkn_unit_id,
    ensure_source_manifest,
    choose_merge_target,
    find_collision_rows,
    load_unit_index_rows,
    map_aitp_candidate_type,
    merge_tpkn_unit,
    run_tpkn_checks,
    unit_path_for,
    write_json as write_external_json,
)


def _looks_like_repo_root(path: Path) -> bool:
    return (path / "AGENTS.md").exists() and (path / "research" / "knowledge-hub").exists()


def _looks_like_kernel_root(path: Path) -> bool:
    return (path / "runtime" / "scripts" / "orchestrate_topic.py").exists()


def _git_toplevel_from(path: Path) -> Path | None:
    completed = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    resolved = Path(completed.stdout.strip()).resolve()
    return resolved if _looks_like_repo_root(resolved) else None


def _detect_repo_root() -> Path:
    env_override = os.environ.get("AITP_REPO_ROOT")
    if env_override:
        return Path(env_override).expanduser()

    pwd_env = os.environ.get("PWD")
    if pwd_env:
        pwd_path = Path(pwd_env).expanduser().resolve()
        for candidate in [pwd_path, *pwd_path.parents]:
            if _looks_like_repo_root(candidate):
                return candidate

    cwd = Path.cwd().resolve()
    for candidate in [cwd, *cwd.parents]:
        if _looks_like_repo_root(candidate):
            return candidate

    git_candidate = _git_toplevel_from(cwd)
    if git_candidate is not None:
        return git_candidate

    file_candidate = Path(__file__).resolve().parents[3]
    if _looks_like_repo_root(file_candidate):
        return file_candidate

    return file_candidate


DEFAULT_REPO_ROOT = _detect_repo_root().expanduser()


def _detect_default_kernel_root() -> Path:
    env_override = os.environ.get("AITP_KERNEL_ROOT")
    if env_override:
        return Path(env_override).expanduser()

    repo_candidate = DEFAULT_REPO_ROOT / "research" / "knowledge-hub"
    cwd_candidates = [Path.cwd().resolve() / "research" / "knowledge-hub", Path.cwd().resolve()]
    for candidate in (repo_candidate, DEFAULT_REPO_ROOT, *cwd_candidates):
        if _looks_like_kernel_root(candidate):
            return candidate

    return repo_candidate


DEFAULT_KERNEL_ROOT = _detect_default_kernel_root()


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def slugify(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-+", "-", lowered).strip("-")
    return lowered or "aitp-topic"


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _coerce_path(value: Path | str) -> Path:
    return Path(value).expanduser().resolve()


@dataclass
class AITPService:
    kernel_root: Path = DEFAULT_KERNEL_ROOT
    repo_root: Path = DEFAULT_REPO_ROOT

    def __post_init__(self) -> None:
        self.kernel_root = _coerce_path(self.kernel_root)
        self.repo_root = _coerce_path(self.repo_root)
        if not _looks_like_repo_root(self.repo_root):
            self.repo_root = _detect_repo_root().resolve()

    def _kernel_script(self, relative_path: str) -> Path:
        script_path = self.kernel_root / relative_path
        if not script_path.exists():
            raise FileNotFoundError(f"Missing kernel script: {script_path}")
        return script_path

    def _run(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(argv, check=False, capture_output=True, text=True)
        if completed.returncode != 0:
            message = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
            raise RuntimeError(message)
        return completed

    def _format_command(self, argv: list[str]) -> str:
        return shlex.join(argv)

    def _mcp_environment(self) -> dict[str, str]:
        return {
            "AITP_KERNEL_ROOT": str(self.kernel_root),
            "AITP_REPO_ROOT": str(self.repo_root),
        }

    def _resolve_aitp_mcp_command(self) -> list[str]:
        installed = shutil.which("aitp-mcp")
        if installed:
            return [installed]

        repo_venv = self.repo_root / "research" / "knowledge-hub" / ".venv" / "bin" / "aitp-mcp"
        if repo_venv.exists():
            return [str(repo_venv)]

        fallback_python = shutil.which("python3") or sys.executable
        fallback_module = self.repo_root / "research" / "knowledge-hub" / "knowledge_hub" / "aitp_mcp_server.py"
        if fallback_module.exists():
            return [fallback_python, str(fallback_module)]

        raise FileNotFoundError("Unable to resolve the aitp-mcp server command.")

    def _runtime_root(self, topic_slug: str) -> Path:
        return self.kernel_root / "runtime" / "topics" / topic_slug

    def _validation_run_root(self, topic_slug: str, run_id: str) -> Path:
        return self.kernel_root / "validation" / "topics" / topic_slug / "runs" / run_id

    def _feedback_run_root(self, topic_slug: str, run_id: str) -> Path:
        return self.kernel_root / "feedback" / "topics" / topic_slug / "runs" / run_id

    def _candidate_ledger_path(self, topic_slug: str, run_id: str) -> Path:
        return self._feedback_run_root(topic_slug, run_id) / "candidate_ledger.jsonl"

    def _promotion_gate_paths(self, topic_slug: str) -> dict[str, Path]:
        runtime_root = self._runtime_root(topic_slug)
        return {
            "json": runtime_root / "promotion_gate.json",
            "note": runtime_root / "promotion_gate.md",
        }

    def _promotion_gate_log_path(self, topic_slug: str, run_id: str) -> Path:
        return self._validation_run_root(topic_slug, run_id) / "promotion_gate_log.jsonl"

    def _consultation_root(self, topic_slug: str) -> Path:
        return self.kernel_root / "consultation" / "topics" / topic_slug

    def _research_root(self) -> Path:
        return self.kernel_root.parent

    def _operation_id(self, value: str) -> str:
        if value.startswith("operation:"):
            return value
        return f"operation:{slugify(value)}"

    def _operation_slug(self, operation_id: str) -> str:
        return operation_id.split(":", 1)[-1]

    def _operation_root(self, topic_slug: str, run_id: str, operation_id: str) -> Path:
        return self._validation_run_root(topic_slug, run_id) / "operations" / self._operation_slug(operation_id)

    def _operation_manifest_path(self, topic_slug: str, run_id: str, operation_id: str) -> Path:
        return self._operation_root(topic_slug, run_id, operation_id) / "operation_manifest.json"

    def _trust_audit_path(self, topic_slug: str, run_id: str) -> Path:
        return self._validation_run_root(topic_slug, run_id) / "trust_audit.json"

    def _trust_report_path(self, topic_slug: str, run_id: str) -> Path:
        return self._validation_run_root(topic_slug, run_id) / "trust_audit.md"

    def _capability_registry_path(self, topic_slug: str) -> Path:
        return self._runtime_root(topic_slug) / "capability_registry.json"

    def _capability_report_path(self, topic_slug: str) -> Path:
        return self._runtime_root(topic_slug) / "capability_report.md"

    def _loop_state_path(self, topic_slug: str) -> Path:
        return self._runtime_root(topic_slug) / "loop_state.json"

    def _loop_history_path(self, topic_slug: str) -> Path:
        return self._runtime_root(topic_slug) / "loop_history.jsonl"

    def _runtime_policy_path(self) -> Path:
        return self.kernel_root / "runtime" / "closed_loop_policies.json"

    def _candidate_split_contract_path(self, topic_slug: str, run_id: str) -> Path:
        return self._feedback_run_root(topic_slug, run_id) / "candidate_split.contract.json"

    def _candidate_split_receipts_path(self, topic_slug: str, run_id: str) -> Path:
        return self._feedback_run_root(topic_slug, run_id) / "candidate_split_receipts.jsonl"

    def _deferred_buffer_paths(self, topic_slug: str) -> dict[str, Path]:
        runtime_root = self._runtime_root(topic_slug)
        return {
            "json": runtime_root / "deferred_candidates.json",
            "note": runtime_root / "deferred_candidates.md",
        }

    def _followup_subtopics_paths(self, topic_slug: str) -> dict[str, Path]:
        runtime_root = self._runtime_root(topic_slug)
        return {
            "jsonl": runtime_root / "followup_subtopics.jsonl",
            "note": runtime_root / "followup_subtopics.md",
        }

    def _followup_return_packet_path(self, topic_slug: str) -> Path:
        policy = self._load_runtime_policy().get("followup_subtopic_policy") or {}
        filename = str(policy.get("return_packet_filename") or "followup_return_packet.json").strip()
        return self._runtime_root(topic_slug) / filename

    def _followup_return_packet_note_path(self, topic_slug: str) -> Path:
        return self._followup_return_packet_path(topic_slug).with_suffix(".md")

    def _research_question_contract_paths(self, topic_slug: str) -> dict[str, Path]:
        runtime_root = self._runtime_root(topic_slug)
        return {
            "json": runtime_root / "research_question.contract.json",
            "note": runtime_root / "research_question.contract.md",
        }

    def _validation_contract_paths(self, topic_slug: str) -> dict[str, Path]:
        runtime_root = self._runtime_root(topic_slug)
        return {
            "json": runtime_root / "validation_contract.active.json",
            "note": runtime_root / "validation_contract.active.md",
        }

    def _topic_dashboard_path(self, topic_slug: str) -> Path:
        return self._runtime_root(topic_slug) / "topic_dashboard.md"

    def _promotion_readiness_path(self, topic_slug: str) -> Path:
        return self._runtime_root(topic_slug) / "promotion_readiness.md"

    def _gap_map_path(self, topic_slug: str) -> Path:
        return self._runtime_root(topic_slug) / "gap_map.md"

    def _followup_gap_writeback_paths(self, topic_slug: str) -> dict[str, Path]:
        runtime_root = self._runtime_root(topic_slug)
        return {
            "jsonl": runtime_root / "followup_gap_writeback.jsonl",
            "note": runtime_root / "followup_gap_writeback.md",
        }

    def _topic_completion_paths(self, topic_slug: str) -> dict[str, Path]:
        runtime_root = self._runtime_root(topic_slug)
        return {
            "json": runtime_root / "topic_completion.json",
            "note": runtime_root / "topic_completion.md",
        }

    def _followup_reintegration_paths(self, topic_slug: str) -> dict[str, Path]:
        runtime_root = self._runtime_root(topic_slug)
        return {
            "jsonl": runtime_root / "followup_reintegration.jsonl",
            "note": runtime_root / "followup_reintegration.md",
        }

    def _lean_bridge_active_paths(self, topic_slug: str) -> dict[str, Path]:
        runtime_root = self._runtime_root(topic_slug)
        return {
            "json": runtime_root / "lean_bridge.active.json",
            "note": runtime_root / "lean_bridge.active.md",
        }

    def _lean_bridge_packet_paths(self, topic_slug: str, run_id: str, candidate_id: str) -> dict[str, Path]:
        root = self._validation_run_root(topic_slug, run_id) / "lean-bridge" / slugify(candidate_id)
        return {
            "root": root,
            "json": root / "lean_ready_packet.json",
            "note": root / "lean_ready_packet.md",
            "proof_obligations": root / "proof_obligations.json",
            "proof_obligations_note": root / "proof_obligations.md",
            "proof_state": root / "proof_state.json",
            "proof_state_note": root / "proof_state.md",
        }

    def _load_runtime_policy(self) -> dict[str, Any]:
        return read_json(self._runtime_policy_path()) or {}

    def _probe(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(argv, check=False, capture_output=True, text=True)

    def _resolve_run_id(self, topic_slug: str, run_id: str | None) -> str | None:
        if run_id:
            return run_id
        try:
            topic_state = self.get_runtime_state(topic_slug)
        except FileNotFoundError:
            return None
        latest_run_id = topic_state.get("latest_run_id")
        return str(latest_run_id) if latest_run_id else None

    def _relativize(self, path: Path) -> str:
        resolved = path.expanduser().resolve()
        for root in (self.kernel_root, self.repo_root):
            try:
                return resolved.relative_to(root.resolve()).as_posix()
            except ValueError:
                continue
        return str(resolved)

    def _dedupe_strings(self, values: list[str] | None) -> list[str]:
        deduped: list[str] = []
        seen: set[str] = set()
        for value in values or []:
            stripped = str(value).strip()
            if stripped and stripped not in seen:
                seen.add(stripped)
                deduped.append(stripped)
        return deduped

    def _topic_display_title(self, topic_slug: str) -> str:
        return topic_slug.replace("-", " ").strip().title() or topic_slug

    def _template_mode_to_research_mode(self, template_mode: str | None) -> str:
        normalized = str(template_mode or "").strip().lower()
        mapping = {
            "formal_theory": "formal_derivation",
            "toy_numeric": "toy_model",
            "code_method": "exploratory_general",
        }
        return mapping.get(normalized, normalized or "exploratory_general")

    def _research_mode_to_template_mode(self, research_mode: str | None) -> str:
        normalized = str(research_mode or "").strip().lower()
        mapping = {
            "formal_derivation": "formal_theory",
            "toy_model": "toy_numeric",
            "first_principles": "toy_numeric",
            "exploratory_general": "code_method",
        }
        return mapping.get(normalized, "code_method")

    def _validation_mode_for_template(self, template_mode: str | None) -> str:
        normalized = str(template_mode or "").strip().lower()
        if normalized == "formal_theory":
            return "formal"
        if normalized == "toy_numeric":
            return "numerical"
        return "hybrid"

    def _coalesce_list(self, existing: Any, defaults: list[str]) -> list[str]:
        if isinstance(existing, list):
            values = self._dedupe_strings([str(item) for item in existing])
            if values:
                return values
        return self._dedupe_strings(defaults)

    def _coalesce_string(self, existing: Any, default: str) -> str:
        resolved = str(existing or "").strip()
        return resolved or default

    def _slug_to_camel(self, value: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9]+", " ", str(value or "").strip())
        parts = [part for part in cleaned.split() if part]
        if not parts:
            return "AitpTopic"
        return "".join(part[:1].upper() + part[1:] for part in parts)

    def _pending_action_context(
        self,
        queue_rows: list[dict[str, Any]],
        decision_surface: dict[str, Any] | None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
        pending_actions = [
            row for row in queue_rows if str(row.get("status") or "pending") == "pending"
        ]
        selected_action_id = str((decision_surface or {}).get("selected_action_id") or "").strip()
        selected_pending_action: dict[str, Any] | None = None
        if selected_action_id:
            selected_pending_action = next(
                (
                    row
                    for row in pending_actions
                    if str(row.get("action_id") or "").strip() == selected_action_id
                ),
                None,
            )
        if selected_pending_action is None and pending_actions:
            selected_pending_action = pending_actions[0]
        return pending_actions, selected_pending_action

    def _fingerprint_payload(self, payload: dict[str, Any]) -> str:
        serialized = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        return hashlib.sha1(serialized.encode("utf-8")).hexdigest()

    def _derive_topic_completion_status(
        self,
        *,
        requested_status: str | None,
        coverage_status: str,
        supporting_regression_question_ids: list[str],
        supporting_oracle_ids: list[str],
        supporting_regression_run_ids: list[str],
        promotion_blockers: list[str],
        split_required: bool,
        cited_recovery_required: bool,
    ) -> str:
        valid_statuses = {
            "not_assessed",
            "gap-aware",
            "regression-seeded",
            "regression-stable",
            "promotion-blocked",
            "promotion-ready",
        }
        normalized_requested = str(requested_status or "").strip()
        if normalized_requested in valid_statuses:
            return normalized_requested
        if promotion_blockers or split_required or cited_recovery_required:
            return "promotion-blocked"
        if (
            coverage_status == "pass"
            and supporting_regression_question_ids
            and supporting_oracle_ids
            and supporting_regression_run_ids
        ):
            return "promotion-ready"
        if supporting_regression_question_ids or supporting_oracle_ids or supporting_regression_run_ids:
            return "regression-stable"
        if coverage_status == "pass":
            return "regression-seeded"
        return "gap-aware"

    def _build_regression_gate(
        self,
        *,
        topic_slug: str,
        run_id: str,
        candidate_id: str,
        updated_by: str,
        coverage_status: str,
        consensus_status: str,
        topic_completion_status: str,
        supporting_regression_question_ids: list[str],
        supporting_oracle_ids: list[str],
        supporting_regression_run_ids: list[str],
        promotion_blockers: list[str],
        split_required: bool,
        cited_recovery_required: bool,
        followup_gap_ids: list[str],
        notes: str,
    ) -> dict[str, Any]:
        blocking_reasons: list[str] = []
        if coverage_status != "pass":
            blocking_reasons.append("coverage_not_passed")
        if consensus_status != "ready":
            blocking_reasons.append("consensus_not_ready")
        if not supporting_regression_question_ids:
            blocking_reasons.append("missing_supporting_regression_questions")
        if not supporting_oracle_ids:
            blocking_reasons.append("missing_supporting_oracles")
        if not supporting_regression_run_ids:
            blocking_reasons.append("missing_supporting_regression_runs")
        if split_required:
            blocking_reasons.append("split_required")
        if promotion_blockers:
            blocking_reasons.append("promotion_blockers_present")
        if cited_recovery_required:
            blocking_reasons.append("cited_recovery_required")

        if not blocking_reasons and topic_completion_status == "promotion-ready":
            status = "pass"
        elif split_required or promotion_blockers or cited_recovery_required:
            status = "blocked"
        else:
            status = "needs_revision"

        return {
            "topic_slug": topic_slug,
            "run_id": run_id,
            "candidate_id": candidate_id,
            "status": status,
            "coverage_status": coverage_status,
            "consensus_status": consensus_status,
            "topic_completion_status": topic_completion_status,
            "supporting_regression_question_ids": supporting_regression_question_ids,
            "supporting_oracle_ids": supporting_oracle_ids,
            "supporting_regression_run_ids": supporting_regression_run_ids,
            "promotion_blockers": promotion_blockers,
            "promotion_blockers_cleared": not promotion_blockers and not cited_recovery_required,
            "split_required": split_required,
            "split_clearance_status": "blocked" if split_required else "clear",
            "cited_recovery_required": cited_recovery_required,
            "followup_gap_ids": followup_gap_ids,
            "blocking_reasons": blocking_reasons,
            "updated_at": now_iso(),
            "updated_by": updated_by,
            "notes": notes,
        }

    def _candidate_rows_for_run(self, topic_slug: str, run_id: str | None) -> list[dict[str, Any]]:
        if not run_id:
            return []
        ledger_path = self._candidate_ledger_path(topic_slug, run_id)
        return [row for row in read_jsonl(ledger_path) if isinstance(row, dict)]

    def _derive_promotion_readiness(
        self,
        *,
        topic_slug: str,
        latest_run_id: str | None,
        promotion_gate: dict[str, Any],
        candidate_rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        ready_candidate_ids: list[str] = []
        blockers: list[str] = []
        for row in candidate_rows:
            candidate_id = str(row.get("candidate_id") or "").strip()
            completion_status = str(row.get("topic_completion_status") or "not_assessed")
            row_blockers = self._dedupe_strings(list(row.get("promotion_blockers") or []))
            if as_bool(row.get("split_required")):
                row_blockers.append(f"{candidate_id or 'candidate'} requires a split contract before promotion.")
            if as_bool(row.get("cited_recovery_required")):
                row_blockers.append(
                    f"{candidate_id or 'candidate'} must return to L0 for cited-source or prior-work recovery."
                )
            if (
                candidate_id
                and completion_status == "promotion-ready"
                and not row_blockers
                and row.get("supporting_regression_question_ids")
                and row.get("supporting_oracle_ids")
                and row.get("supporting_regression_run_ids")
            ):
                ready_candidate_ids.append(candidate_id)
            blockers.extend(row_blockers)

        gate_status = str(promotion_gate.get("status") or "not_requested")
        if gate_status == "promoted":
            status = "promoted"
            summary = "Promotion already ran. Inspect the backend writeback artifacts before changing the topic again."
        elif gate_status == "approved":
            status = "approved"
            summary = "A promotion gate is approved. Promotion may proceed against the configured backend."
        elif gate_status == "pending_human_approval":
            status = "awaiting_human"
            summary = "A promotion request is pending human review."
        elif ready_candidate_ids:
            status = "ready"
            summary = "At least one candidate is promotion-ready once the corresponding gate route is selected."
        elif blockers:
            status = "blocked"
            summary = "Promotion is blocked by explicit split, recovery, or regression-support gaps."
        elif candidate_rows:
            status = "in_progress"
            summary = "Candidate shaping exists, but promotion readiness is not yet established."
        else:
            status = "no_candidates"
            summary = "No candidate ledger entries are present for the latest run yet."

        return {
            "topic_slug": topic_slug,
            "latest_run_id": latest_run_id or "",
            "status": status,
            "gate_status": gate_status,
            "ready_candidate_ids": self._dedupe_strings(ready_candidate_ids),
            "blockers": self._dedupe_strings(blockers),
            "blocker_count": len(self._dedupe_strings(blockers)),
            "summary": summary,
        }

    def _derive_open_gap_summary(
        self,
        *,
        topic_slug: str,
        candidate_rows: list[dict[str, Any]],
        pending_actions: list[dict[str, Any]],
        selected_pending_action: dict[str, Any] | None,
    ) -> dict[str, Any]:
        blockers: list[str] = []
        followup_gap_ids: list[str] = []
        followup_gap_writeback_rows = self._load_followup_gap_writeback_rows(topic_slug)
        capability_gap_active = any(
            str(row.get("action_type") or "").strip() == "skill_discovery" for row in pending_actions
        )
        for row in candidate_rows:
            candidate_id = str(row.get("candidate_id") or "").strip() or "candidate"
            for blocker in row.get("promotion_blockers") or []:
                text = str(blocker).strip()
                if text:
                    blockers.append(f"{candidate_id}: {text}")
            if as_bool(row.get("split_required")):
                blockers.append(f"{candidate_id}: split into narrower units before promotion.")
            if as_bool(row.get("cited_recovery_required")):
                blockers.append(
                    f"{candidate_id}: return to L0 to recover cited definitions, derivations, or prior-work context."
                )
            followup_gap_ids.extend(list(row.get("followup_gap_ids") or []))
        for row in followup_gap_writeback_rows:
            child_topic_slug = str(row.get("child_topic_slug") or "").strip() or "followup-child"
            return_status = str(row.get("return_status") or "").strip() or "returned_with_gap"
            summary = str(row.get("summary") or "").strip()
            blockers.append(
                f"{child_topic_slug}: unresolved child follow-up returned as `{return_status}` and still requires parent gap writeback."
            )
            if summary:
                blockers.append(f"{child_topic_slug}: {summary}")
            followup_gap_ids.extend(list(row.get("parent_gap_ids") or []))

        selected_action_type = str((selected_pending_action or {}).get("action_type") or "").strip()
        selected_action_summary = str((selected_pending_action or {}).get("summary") or "").strip().lower()
        requires_l0_return = any(
            needle in selected_action_summary
            for needle in ("source", "reference", "prior work", "background", "literature", "citation")
        ) or selected_action_type == "l0_source_expansion"
        requires_l0_return = requires_l0_return or any(
            "return to l0" in blocker.lower() or "prior-work" in blocker.lower() or "cited" in blocker.lower()
            for blocker in blockers
        )
        requires_l0_return = requires_l0_return or bool(followup_gap_writeback_rows)

        gap_items = self._dedupe_strings(blockers + [str(value) for value in followup_gap_ids if str(value).strip()])
        if requires_l0_return:
            status = "return_to_L0"
            summary = "Understanding or prior-work gaps are active. Recover sources through L0 before smoothing the topic in prose."
        elif gap_items:
            status = "open"
            summary = "Open gap packets or blockers remain. Keep them explicit and do not silently merge them into the narrative."
        elif capability_gap_active:
            status = "capability_gap"
            summary = "The main blocker is a capability/workflow gap. Resolve it explicitly through the runtime queue."
        else:
            status = "clear"
            summary = "No explicit gap packet is currently open."

        return {
            "topic_slug": topic_slug,
            "status": status,
            "gap_count": len(gap_items),
            "blockers": self._dedupe_strings(blockers),
            "followup_gap_ids": self._dedupe_strings(followup_gap_ids),
            "followup_gap_writeback_count": len(followup_gap_writeback_rows),
            "followup_gap_writeback_child_topics": self._dedupe_strings(
                [str(row.get("child_topic_slug") or "").strip() for row in followup_gap_writeback_rows if str(row.get("child_topic_slug") or "").strip()]
            ),
            "pending_action_summaries": self._dedupe_strings(
                [str(row.get("summary") or "").strip() for row in pending_actions if str(row.get("summary") or "").strip()]
            ),
            "requires_l0_return": requires_l0_return,
            "capability_gap_active": capability_gap_active,
            "summary": summary,
        }

    def _render_research_question_contract_markdown(self, payload: dict[str, Any]) -> str:
        lines = [
            "# Active research question contract",
            "",
            f"- Topic slug: `{payload['topic_slug']}`",
            f"- Question id: `{payload['question_id']}`",
            f"- Title: `{payload['title']}`",
            f"- Status: `{payload['status']}`",
            f"- Template mode: `{payload.get('template_mode') or '(missing)'}`",
            f"- Research mode: `{payload.get('research_mode') or '(missing)'}`",
            "",
            "## Question",
            "",
            payload["question"],
            "",
            "## Scope",
            "",
        ]
        for item in payload.get("scope") or ["(missing)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Assumptions", ""])
        for item in payload.get("assumptions") or ["(missing)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Non-goals", ""])
        for item in payload.get("non_goals") or ["(missing)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Context intake", ""])
        for item in payload.get("context_intake") or ["(missing)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Formalism and notation", ""])
        for item in payload.get("formalism_and_notation") or ["(missing)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Observables", ""])
        for item in payload.get("observables") or ["(missing)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Target claims", ""])
        for item in payload.get("target_claims") or ["(missing)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Deliverables", ""])
        for item in payload.get("deliverables") or ["(missing)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Acceptance tests", ""])
        for item in payload.get("acceptance_tests") or ["(missing)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Forbidden proxies", ""])
        for item in payload.get("forbidden_proxies") or ["(missing)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Uncertainty markers", ""])
        for item in payload.get("uncertainty_markers") or ["(none)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Target layers", ""])
        for item in payload.get("target_layers") or ["(missing)"]:
            lines.append(f"- `{item}`")
        return "\n".join(lines) + "\n"

    def _render_validation_contract_markdown(self, payload: dict[str, Any]) -> str:
        lines = [
            "# Active validation contract",
            "",
            f"- Topic slug: `{payload['topic_slug']}`",
            f"- Validation id: `{payload['validation_id']}`",
            f"- Status: `{payload['status']}`",
            f"- Template mode: `{payload.get('template_mode') or '(missing)'}`",
            f"- Validation mode: `{payload.get('validation_mode') or '(missing)'}`",
            f"- Verification focus: `{payload.get('verification_focus') or '(missing)'}`",
            f"- Confidence cap: `{payload.get('confidence_cap') or '(missing)'}`",
            "",
            "## Acceptance rule",
            "",
            payload["acceptance_rule"],
            "",
            "## Rejection rule",
            "",
            payload["rejection_rule"],
            "",
            "## Target claim ids",
            "",
        ]
        for item in payload.get("target_claim_ids") or ["(missing)"]:
            lines.append(f"- `{item}`")
        lines.extend(["", "## Required checks", ""])
        for item in payload.get("required_checks") or ["(missing)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Oracle artifacts", ""])
        for item in payload.get("oracle_artifacts") or ["(none)"]:
            lines.append(f"- `{item}`")
        lines.extend(["", "## Executed evidence", ""])
        for item in payload.get("executed_evidence") or ["(none yet)"]:
            lines.append(f"- `{item}`")
        lines.extend(["", "## Gap followups", ""])
        for item in payload.get("gap_followups") or ["(none)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Failure modes", ""])
        for item in payload.get("failure_modes") or ["(missing)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Artifact lanes", ""])
        for item in payload.get("artifacts") or ["(missing)"]:
            lines.append(f"- `{item}`")
        return "\n".join(lines) + "\n"

    def _render_topic_dashboard_markdown(
        self,
        *,
        topic_slug: str,
        topic_state: dict[str, Any],
        selected_pending_action: dict[str, Any] | None,
        pending_actions: list[dict[str, Any]],
        research_contract: dict[str, Any],
        validation_contract: dict[str, Any],
        promotion_readiness: dict[str, Any],
        open_gap_summary: dict[str, Any],
        topic_completion: dict[str, Any],
        lean_bridge: dict[str, Any],
    ) -> str:
        selected_action_summary = str((selected_pending_action or {}).get("summary") or "").strip() or "(none)"
        lines = [
            "# Topic dashboard",
            "",
            f"- Topic slug: `{topic_slug}`",
            f"- Title: `{research_contract.get('title') or self._topic_display_title(topic_slug)}`",
            f"- Resume stage: `{topic_state.get('resume_stage') or '(missing)'}`",
            f"- Last materialized stage: `{topic_state.get('last_materialized_stage') or '(missing)'}`",
            f"- Latest run id: `{topic_state.get('latest_run_id') or '(missing)'}`",
            f"- Research mode: `{research_contract.get('research_mode') or topic_state.get('research_mode') or '(missing)'}`",
            f"- Current bounded action: `{selected_action_summary}`",
            f"- Pending action count: `{len(pending_actions)}`",
            "",
            "## Active question",
            "",
            research_contract.get("question") or "(missing)",
            "",
            "## Current status",
            "",
            f"- Research contract: `{research_contract.get('status') or '(missing)'}`",
            f"- Validation contract: `{validation_contract.get('status') or '(missing)'}`",
            f"- Promotion readiness: `{promotion_readiness.get('status') or '(missing)'}`",
            f"- Gap status: `{open_gap_summary.get('status') or '(missing)'}`",
            f"- Topic completion: `{topic_completion.get('status') or '(missing)'}`",
            f"- Lean bridge: `{lean_bridge.get('status') or '(missing)'}`",
            "",
            "## Promotion readiness summary",
            "",
            promotion_readiness.get("summary") or "(missing)",
            "",
            "## Open gap summary",
            "",
            open_gap_summary.get("summary") or "(missing)",
            "",
            "## Topic completion summary",
            "",
            topic_completion.get("summary") or "(missing)",
            "",
            "## Lean bridge summary",
            "",
            lean_bridge.get("summary") or "(missing)",
            "",
            "## Immediate next actions",
            "",
        ]
        for row in pending_actions[:8] or [{"summary": "(none)"}]:
            lines.append(
                f"- [{str(row.get('action_type') or 'unknown')}] {str(row.get('summary') or '(missing)')}"
            )
        lines.extend(
            [
                "",
                "## Operating rule",
                "",
                "- If a definition, proof dependency, or prior-work comparison is missing, return to L0 and persist the recovery artifacts before continuing.",
                "- Keep the research and validation contracts synchronized with any scope change.",
            ]
        )
        return "\n".join(lines) + "\n"

    def _render_promotion_readiness_markdown(self, payload: dict[str, Any]) -> str:
        lines = [
            "# Promotion readiness",
            "",
            f"- Topic slug: `{payload['topic_slug']}`",
            f"- Latest run id: `{payload.get('latest_run_id') or '(missing)'}`",
            f"- Status: `{payload.get('status') or '(missing)'}`",
            f"- Gate status: `{payload.get('gate_status') or '(missing)'}`",
            f"- Ready candidate count: `{len(payload.get('ready_candidate_ids') or [])}`",
            f"- Blocker count: `{payload.get('blocker_count') or 0}`",
            "",
            "## Summary",
            "",
            payload.get("summary") or "(missing)",
            "",
            "## Ready candidates",
            "",
        ]
        for item in payload.get("ready_candidate_ids") or ["(none)"]:
            lines.append(f"- `{item}`")
        lines.extend(["", "## Blockers", ""])
        for item in payload.get("blockers") or ["(none)"]:
            lines.append(f"- {item}")
        return "\n".join(lines) + "\n"

    def _render_gap_map_markdown(self, payload: dict[str, Any]) -> str:
        lines = [
            "# Gap map",
            "",
            f"- Topic slug: `{payload['topic_slug']}`",
            f"- Status: `{payload.get('status') or '(missing)'}`",
            f"- Gap count: `{payload.get('gap_count') or 0}`",
            f"- Requires L0 return: `{str(bool(payload.get('requires_l0_return'))).lower()}`",
            f"- Capability gap active: `{str(bool(payload.get('capability_gap_active'))).lower()}`",
            "",
            "## Summary",
            "",
            payload.get("summary") or "(missing)",
            "",
            "## Blockers",
            "",
        ]
        for item in payload.get("blockers") or ["(none)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Follow-up gap ids", ""])
        for item in payload.get("followup_gap_ids") or ["(none)"]:
            lines.append(f"- `{item}`")
        lines.extend(["", "## Follow-up gap writeback", ""])
        lines.append(f"- Count: `{payload.get('followup_gap_writeback_count') or 0}`")
        for item in payload.get("followup_gap_writeback_child_topics") or ["(none)"]:
            lines.append(f"- `{item}`")
        lines.extend(["", "## Pending action summaries", ""])
        for item in payload.get("pending_action_summaries") or ["(none)"]:
            lines.append(f"- {item}")
        lines.extend(
            [
                "",
                "## Rule",
                "",
                "- When a blocker is really a missing citation, definition, derivation, or prior-work comparison, return to L0 and write back the recovery path instead of hiding it inside prose.",
            ]
        )
        return "\n".join(lines) + "\n"

    def _return_shape_for_status(
        self,
        return_status: str,
        unresolved_statuses: set[str] | None = None,
    ) -> str:
        normalized = str(return_status or "").strip()
        unresolved = unresolved_statuses or set()
        if normalized == "recovered_units":
            return "recovered_units"
        if normalized == "resolved_gap_update":
            return "resolved_gap_update"
        if normalized in unresolved and normalized != "pending_reentry":
            return "still_unresolved_packet"
        return ""

    def _completion_gate_checks(
        self,
        *,
        regression_question_ids: list[str],
        oracle_ids: list[str],
        regression_run_ids: list[str],
        promotion_ready_candidate_ids: list[str],
        blocked_candidate_ids: list[str],
        unresolved_followup_child_topics: list[str],
        returned_with_gap_child_topics: list[str],
    ) -> list[dict[str, str]]:
        followup_blockers = self._dedupe_strings(
            unresolved_followup_child_topics + returned_with_gap_child_topics
        )
        checks = [
            {
                "check": "regression_questions_present",
                "status": "pass" if regression_question_ids else "blocked",
                "summary": "Stable regression questions exist."
                if regression_question_ids
                else "No stable regression question ids are attached to the active topic.",
            },
            {
                "check": "question_oracles_present",
                "status": "pass" if oracle_ids else "blocked",
                "summary": "Stable question oracles exist."
                if oracle_ids
                else "No stable question oracle ids are attached to the active topic.",
            },
            {
                "check": "regression_runs_present",
                "status": "pass" if regression_run_ids else "blocked",
                "summary": "Recent regression runs exist."
                if regression_run_ids
                else "No regression run ids are attached to the active topic.",
            },
            {
                "check": "promotion_ready_candidate_present",
                "status": "pass" if promotion_ready_candidate_ids else "blocked",
                "summary": "At least one candidate is marked promotion-ready."
                if promotion_ready_candidate_ids
                else "No candidate currently satisfies the topic-completion promotion-ready state.",
            },
            {
                "check": "candidate_blockers_clear",
                "status": "pass" if not blocked_candidate_ids else "blocked",
                "summary": "No candidate-level completion blockers remain."
                if not blocked_candidate_ids
                else "One or more candidates still expose split, cited-recovery, or blocker debt.",
            },
            {
                "check": "followup_return_debt_clear",
                "status": "pass" if not followup_blockers else "blocked",
                "summary": "No unreintegrated child follow-up return debt remains."
                if not followup_blockers
                else "At least one child follow-up topic still requires reintegration or further gap routing.",
            },
        ]
        return checks

    def _followup_return_packet_markdown(self, payload: dict[str, Any]) -> str:
        lines = [
            "# Follow-up return packet",
            "",
            f"- Child topic: `{payload.get('child_topic_slug') or '(missing)'}`",
            f"- Parent topic: `{payload.get('parent_topic_slug') or '(missing)'}`",
            f"- Parent run: `{payload.get('parent_run_id') or '(missing)'}`",
            f"- Receipt id: `{payload.get('receipt_id') or '(missing)'}`",
            f"- Query: `{payload.get('query') or '(missing)'}`",
            f"- Source id: `{payload.get('source_id') or '(missing)'}`",
            f"- arXiv id: `{payload.get('arxiv_id') or '(missing)'}`",
            f"- Return status: `{payload.get('return_status') or '(missing)'}`",
            f"- Accepted return shape: `{payload.get('accepted_return_shape') or '(pending)'}`",
            "",
            "## Parent reintegration context",
            "",
            f"- Parent gaps: `{', '.join(payload.get('parent_gap_ids') or []) or '(none)'}`",
            f"- Parent follow-up tasks: `{', '.join(payload.get('parent_followup_task_ids') or []) or '(none)'}`",
            f"- Reentry targets: `{', '.join(payload.get('reentry_targets') or []) or '(none)'}`",
            f"- Supporting regression questions: `{', '.join(payload.get('supporting_regression_question_ids') or []) or '(none)'}`",
            "",
            "## Return route contract",
            "",
            f"- Expected return route: `{payload.get('expected_return_route') or '(missing)'}`",
            f"- Acceptable return shapes: `{', '.join(payload.get('acceptable_return_shapes') or []) or '(none)'}`",
            f"- Unresolved statuses: `{', '.join(payload.get('unresolved_return_statuses') or []) or '(none)'}`",
            f"- Required output artifacts: `{', '.join(payload.get('required_output_artifacts') or []) or '(none)'}`",
            "",
            "## Return summary",
            "",
            payload.get("return_summary") or "(pending)",
            "",
            "## Return artifacts",
            "",
        ]
        for item in payload.get("return_artifact_paths") or ["(none)"]:
            lines.append(f"- `{item}`")
        lines.extend(["", "## Reintegration requirements", ""])
        for key, value in sorted((payload.get("reintegration_requirements") or {}).items()):
            lines.append(f"- `{key}`: `{str(bool(value)).lower()}`")
        child_summary = str(payload.get("child_topic_summary") or "").strip()
        if child_summary:
            lines.extend(["", "## Child topic summary", "", child_summary, ""])
        return "\n".join(lines) + "\n"

    def _compute_topic_completion_payload(
        self,
        *,
        topic_slug: str,
        run_id: str | None,
        candidate_rows: list[dict[str, Any]],
        updated_by: str,
    ) -> dict[str, Any]:
        followup_rows = self._load_followup_subtopic_rows(topic_slug)
        reintegration_rows = self._load_followup_reintegration_rows(topic_slug)
        policy = self._load_runtime_policy().get("followup_subtopic_policy") or {}
        unresolved_statuses = {
            str(value).strip()
            for value in (policy.get("unresolved_return_statuses") or [])
            if str(value).strip()
        }
        unresolved_statuses.discard("pending_reentry")

        regression_question_ids: list[str] = []
        oracle_ids: list[str] = []
        regression_run_ids: list[str] = []
        promotion_ready_candidate_ids: list[str] = []
        blocked_candidate_ids: list[str] = []
        open_gap_ids: list[str] = []
        blockers: list[str] = []
        candidate_ids: list[str] = []

        for row in candidate_rows:
            candidate_id = str(row.get("candidate_id") or "").strip()
            if candidate_id:
                candidate_ids.append(candidate_id)
            regression_question_ids.extend(list(row.get("supporting_regression_question_ids") or []))
            oracle_ids.extend(list(row.get("supporting_oracle_ids") or []))
            regression_run_ids.extend(list(row.get("supporting_regression_run_ids") or []))
            open_gap_ids.extend(list(row.get("followup_gap_ids") or []))
            open_gap_ids.extend(list(row.get("parent_gap_ids") or []))
            if str(row.get("topic_completion_status") or "") == "promotion-ready":
                promotion_ready_candidate_ids.append(candidate_id)
            if (
                list(row.get("promotion_blockers") or [])
                or as_bool(row.get("split_required"))
                or as_bool(row.get("cited_recovery_required"))
            ):
                blocked_candidate_ids.append(candidate_id)
            for blocker in row.get("promotion_blockers") or []:
                text = str(blocker).strip()
                if text:
                    blockers.append(f"{candidate_id or 'candidate'}: {text}")
            if as_bool(row.get("split_required")):
                blockers.append(f"{candidate_id or 'candidate'}: split required before promotion.")
            if as_bool(row.get("cited_recovery_required")):
                blockers.append(
                    f"{candidate_id or 'candidate'}: cited-source or prior-work recovery must return through L0."
                )

        reintegrated_children = {
            str(row.get("child_topic_slug") or "").strip()
            for row in reintegration_rows
            if str(row.get("child_topic_slug") or "").strip()
        }
        unresolved_followup_child_topics: list[str] = []
        returned_with_gap_child_topics: list[str] = []
        for row in followup_rows:
            child_topic_slug = str(row.get("child_topic_slug") or "").strip()
            if not child_topic_slug:
                continue
            return_packet_path = str(row.get("return_packet_path") or "").strip()
            return_packet = read_json(Path(return_packet_path)) if return_packet_path else None
            return_status = str((return_packet or {}).get("return_status") or row.get("status") or "").strip()
            if child_topic_slug in reintegrated_children or str(row.get("status") or "") == "reintegrated":
                continue
            if return_status in unresolved_statuses or str(row.get("status") or "") == "returned_with_gap":
                returned_with_gap_child_topics.append(child_topic_slug)
                blockers.append(f"{child_topic_slug}: returned from follow-up with unresolved gaps.")
                continue
            if return_status in {"spawned", "pending_reentry", ""} or str(row.get("status") or "") == "spawned":
                unresolved_followup_child_topics.append(child_topic_slug)
                blockers.append(f"{child_topic_slug}: follow-up child topic not yet reintegrated.")

        regression_question_ids = self._dedupe_strings(regression_question_ids)
        oracle_ids = self._dedupe_strings(oracle_ids)
        regression_run_ids = self._dedupe_strings(regression_run_ids)
        promotion_ready_candidate_ids = self._dedupe_strings(promotion_ready_candidate_ids)
        blocked_candidate_ids = self._dedupe_strings(blocked_candidate_ids)
        open_gap_ids = self._dedupe_strings(open_gap_ids)
        blockers = self._dedupe_strings(blockers)
        candidate_ids = self._dedupe_strings(candidate_ids)

        regression_manifest_status = "empty"
        if regression_question_ids and oracle_ids and regression_run_ids:
            regression_manifest_status = "ready"
        elif regression_question_ids or oracle_ids or regression_run_ids:
            regression_manifest_status = "partial"

        gate_checks = self._completion_gate_checks(
            regression_question_ids=regression_question_ids,
            oracle_ids=oracle_ids,
            regression_run_ids=regression_run_ids,
            promotion_ready_candidate_ids=promotion_ready_candidate_ids,
            blocked_candidate_ids=blocked_candidate_ids,
            unresolved_followup_child_topics=unresolved_followup_child_topics,
            returned_with_gap_child_topics=returned_with_gap_child_topics,
        )

        if not candidate_rows and not followup_rows:
            status = "not_assessed"
            summary = "No candidate or follow-up completion surface exists yet."
        elif blockers or unresolved_followup_child_topics or returned_with_gap_child_topics:
            status = "promotion-blocked"
            summary = "Topic completion is blocked by explicit candidate blockers or unreintegrated follow-up returns."
        elif promotion_ready_candidate_ids and regression_question_ids and oracle_ids and regression_run_ids:
            status = "promotion-ready"
            summary = "The topic has regression-backed candidates and no unresolved follow-up return debt."
        elif regression_question_ids and oracle_ids and regression_run_ids:
            status = "regression-stable"
            summary = "Regression-backed topic surfaces exist, but promotion readiness is not yet fully established."
        elif regression_question_ids and oracle_ids:
            status = "regression-seeded"
            summary = "Question/oracle surfaces exist, but recent regression run support is still incomplete."
        else:
            status = "gap-aware"
            summary = "The topic can name its blockers, but regression-governed completion is not established."

        return {
            "$schema": "https://aitp.local/schemas/topic-completion.schema.json",
            "completion_version": 1,
            "topic_slug": topic_slug,
            "run_id": run_id or "",
            "status": status,
            "candidate_count": len(candidate_rows),
            "followup_subtopic_count": len(followup_rows),
            "reintegrated_followup_count": len(reintegrated_children),
            "unresolved_followup_child_topics": self._dedupe_strings(unresolved_followup_child_topics),
            "returned_with_gap_child_topics": self._dedupe_strings(returned_with_gap_child_topics),
            "regression_manifest": {
                "status": regression_manifest_status,
                "candidate_ids": candidate_ids,
                "regression_question_ids": regression_question_ids,
                "oracle_ids": oracle_ids,
                "regression_run_ids": regression_run_ids,
                "candidate_count": len(candidate_ids),
                "question_count": len(regression_question_ids),
                "oracle_count": len(oracle_ids),
                "run_count": len(regression_run_ids),
            },
            "completion_gate_checks": gate_checks,
            "promotion_ready_candidate_ids": promotion_ready_candidate_ids,
            "blocked_candidate_ids": blocked_candidate_ids,
            "regression_question_ids": regression_question_ids,
            "oracle_ids": oracle_ids,
            "regression_run_ids": regression_run_ids,
            "open_gap_ids": open_gap_ids,
            "blockers": blockers,
            "summary": summary,
            "updated_at": now_iso(),
            "updated_by": updated_by,
        }

    def _topic_completion_markdown(self, payload: dict[str, Any]) -> str:
        lines = [
            "# Topic completion",
            "",
            f"- Topic slug: `{payload['topic_slug']}`",
            f"- Run id: `{payload.get('run_id') or '(missing)'}`",
            f"- Status: `{payload.get('status') or '(missing)'}`",
            f"- Candidate count: `{payload.get('candidate_count') or 0}`",
            f"- Follow-up subtopic count: `{payload.get('followup_subtopic_count') or 0}`",
            f"- Reintegrated follow-up count: `{payload.get('reintegrated_followup_count') or 0}`",
            "",
            "## Summary",
            "",
            payload.get("summary") or "(missing)",
            "",
            "## Promotion-ready candidates",
            "",
        ]
        for item in payload.get("promotion_ready_candidate_ids") or ["(none)"]:
            lines.append(f"- `{item}`")
        lines.extend(["", "## Blocked candidates", ""])
        for item in payload.get("blocked_candidate_ids") or ["(none)"]:
            lines.append(f"- `{item}`")
        lines.extend(["", "## Regression surface", ""])
        lines.append(f"- Questions: `{', '.join(payload.get('regression_question_ids') or []) or '(none)'}`")
        lines.append(f"- Oracles: `{', '.join(payload.get('oracle_ids') or []) or '(none)'}`")
        lines.append(f"- Runs: `{', '.join(payload.get('regression_run_ids') or []) or '(none)'}`")
        manifest = payload.get("regression_manifest") or {}
        lines.extend(["", "## Regression manifest", ""])
        lines.append(f"- Status: `{manifest.get('status') or 'empty'}`")
        lines.append(f"- Candidate count: `{manifest.get('candidate_count') or 0}`")
        lines.append(f"- Question count: `{manifest.get('question_count') or 0}`")
        lines.append(f"- Oracle count: `{manifest.get('oracle_count') or 0}`")
        lines.append(f"- Run count: `{manifest.get('run_count') or 0}`")
        lines.extend(["", "## Completion gate checks", ""])
        for row in payload.get("completion_gate_checks") or []:
            lines.append(f"- `{row.get('check') or '(missing)'}` => `{row.get('status') or '(missing)'}`: {row.get('summary') or '(missing)'}")
        lines.extend(["", "## Follow-up return debt", ""])
        for item in payload.get("unresolved_followup_child_topics") or ["(none)"]:
            lines.append(f"- unresolved: `{item}`")
        for item in payload.get("returned_with_gap_child_topics") or []:
            lines.append(f"- returned_with_gap: `{item}`")
        lines.extend(["", "## Open gap ids", ""])
        for item in payload.get("open_gap_ids") or ["(none)"]:
            lines.append(f"- `{item}`")
        lines.extend(["", "## Blockers", ""])
        for item in payload.get("blockers") or ["(none)"]:
            lines.append(f"- {item}")
        return "\n".join(lines) + "\n"

    def _render_proof_obligations_markdown(self, rows: list[dict[str, Any]]) -> str:
        lines = [
            "# Proof obligations",
            "",
            f"- Obligation count: `{len(rows)}`",
            "",
        ]
        for row in rows:
            lines.extend(
                [
                    f"## `{row.get('obligation_id') or '(missing)'}`",
                    "",
                    f"- Category: `{row.get('category') or '(missing)'}`",
                    f"- Status: `{row.get('status') or '(missing)'}`",
                    f"- Claim: {row.get('claim') or '(missing)'}",
                    f"- Prerequisites: `{', '.join(row.get('prerequisite_ids') or []) or '(none)'}`",
                    f"- Equation labels: `{', '.join(row.get('equation_labels') or []) or '(none)'}`",
                    f"- Source anchors: `{', '.join(row.get('source_anchor_ids') or []) or '(none)'}`",
                    f"- Required logical move: {row.get('required_logical_move') or '(missing)'}",
                    f"- Expected output: {row.get('expected_output_statement') or '(missing)'}",
                    "",
                ]
            )
        if not rows:
            lines.append("- No proof obligations are currently registered.")
            lines.append("")
        return "\n".join(lines) + "\n"

    def _render_proof_state_markdown(self, payload: dict[str, Any]) -> str:
        lines = [
            "# Proof state",
            "",
            f"- Candidate id: `{payload.get('candidate_id') or '(missing)'}`",
            f"- Status: `{payload.get('status') or '(missing)'}`",
            f"- Total obligations: `{payload.get('obligation_count') or 0}`",
            "",
            "## Status counts",
            "",
        ]
        for key, value in sorted((payload.get("status_counts") or {}).items()):
            lines.append(f"- `{key}`: `{value}`")
        lines.extend(["", "## Obligation ids", ""])
        for item in payload.get("obligation_ids") or ["(none)"]:
            lines.append(f"- `{item}`")
        return "\n".join(lines) + "\n"

    def _lean_declaration_kind(self, candidate_type: str) -> str:
        normalized = str(candidate_type or "").strip()
        mapping = {
            "definition_card": "def",
            "notation_card": "def",
            "regime_card": "def",
            "assumption_card": "axiom",
            "equation_card": "theorem",
            "theorem_card": "theorem",
            "claim_card": "theorem",
            "proof_fragment": "lemma",
            "derivation_step": "lemma",
            "derivation_object": "theorem",
            "method": "def",
            "workflow": "def",
            "bridge": "theorem",
            "equivalence_map": "theorem",
        }
        return mapping.get(normalized, "def")

    def _render_lean_bridge_packet_markdown(self, payload: dict[str, Any]) -> str:
        lines = [
            "# Lean-ready bridge packet",
            "",
            f"- Topic slug: `{payload['topic_slug']}`",
            f"- Run id: `{payload.get('run_id') or '(missing)'}`",
            f"- Candidate id: `{payload.get('candidate_id') or '(missing)'}`",
            f"- Candidate type: `{payload.get('candidate_type') or '(missing)'}`",
            f"- Declaration kind: `{payload.get('declaration_kind') or '(missing)'}`",
            f"- Namespace: `{payload.get('namespace') or '(missing)'}`",
            f"- Declaration name: `{payload.get('declaration_name') or '(missing)'}`",
            f"- Status: `{payload.get('status') or '(missing)'}`",
            "",
            "## Statement",
            "",
            payload.get("statement_text") or "(missing)",
            "",
            "## Dependency ids",
            "",
        ]
        for item in payload.get("dependency_ids") or ["(none)"]:
            lines.append(f"- `{item}`")
        lines.extend(["", "## Notation bindings", ""])
        for row in payload.get("notation_bindings") or []:
            lines.append(f"- `{row.get('symbol') or '(missing)'}` := {row.get('meaning') or '(missing)'}")
        if not payload.get("notation_bindings"):
            lines.append("- (none)")
        lines.extend(["", "## Proof obligations", ""])
        for item in payload.get("proof_obligations") or ["(none)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Proof-state bridge", ""])
        lines.append(f"- Obligation count: `{payload.get('proof_obligation_count') or 0}`")
        lines.append(f"- Proof obligations JSON: `{payload.get('proof_obligations_path') or '(missing)'}`")
        lines.append(f"- Proof state JSON: `{payload.get('proof_state_path') or '(missing)'}`")
        lines.extend(["", "## Theory packet refs", ""])
        for key, value in sorted((payload.get("theory_packet_refs") or {}).items()):
            lines.append(f"- `{key}`: `{value or '(missing)'}`")
        lines.extend(["", "## Skeleton", ""])
        lines.append("```lean")
        lines.extend(payload.get("lean_skeleton_lines") or ["-- no skeleton available"])
        lines.append("```")
        return "\n".join(lines) + "\n"

    def _render_lean_bridge_index_markdown(self, payload: dict[str, Any]) -> str:
        lines = [
            "# Lean bridge",
            "",
            f"- Topic slug: `{payload['topic_slug']}`",
            f"- Run id: `{payload.get('run_id') or '(missing)'}`",
            f"- Status: `{payload.get('status') or '(missing)'}`",
            f"- Packet count: `{payload.get('packet_count') or 0}`",
            f"- Ready packet count: `{payload.get('ready_packet_count') or 0}`",
            "",
            "## Summary",
            "",
            payload.get("summary") or "(missing)",
            "",
            "## Packets",
            "",
        ]
        for row in payload.get("packets") or []:
            lines.append(
                f"- `{row.get('candidate_id') or '(missing)'}` kind=`{row.get('declaration_kind') or '(missing)'}` "
                f"status=`{row.get('status') or '(missing)'}` obligations=`{row.get('proof_obligation_count') or 0}` "
                f"packet=`{row.get('packet_path') or '(missing)'}`"
            )
        if not payload.get("packets"):
            lines.append("- (none)")
        return "\n".join(lines) + "\n"

    def _materialize_lean_bridge(
        self,
        *,
        topic_slug: str,
        run_id: str | None,
        candidate_rows: list[dict[str, Any]],
        updated_by: str,
        candidate_id: str | None = None,
    ) -> dict[str, Any]:
        selected_rows = candidate_rows
        if candidate_id:
            selected_rows = [
                row
                for row in candidate_rows
                if str(row.get("candidate_id") or "").strip() == candidate_id
            ]
        packets: list[dict[str, Any]] = []
        ready_packet_count = 0
        for row in selected_rows:
            current_candidate_id = str(row.get("candidate_id") or "").strip()
            if not current_candidate_id or not run_id:
                continue
            packet_paths = self._lean_bridge_packet_paths(topic_slug, run_id, current_candidate_id)
            theory_packet_paths = self._theory_packet_paths(topic_slug, run_id, current_candidate_id)
            coverage_ledger = read_json(theory_packet_paths["coverage_ledger"]) or {}
            structure_map = read_json(theory_packet_paths["structure_map"]) or {}
            notation_table = read_json(theory_packet_paths["notation_table"]) or {}
            derivation_graph = read_json(theory_packet_paths["derivation_graph"]) or {}
            regression_gate = read_json(theory_packet_paths["regression_gate"]) or {}
            namespace = f"AITP.{self._slug_to_camel(topic_slug)}"
            declaration_kind = self._lean_declaration_kind(str(row.get("candidate_type") or ""))
            declaration_name = slugify(str(row.get("title") or current_candidate_id)).replace("-", "_")
            if not re.match(r"^[A-Za-z_]", declaration_name):
                declaration_name = f"decl_{declaration_name}"
            dependency_ids = self._dedupe_strings(
                [str(node.get("id") or "").strip() for node in derivation_graph.get("nodes") or []]
                + list(row.get("supporting_regression_question_ids") or [])
                + list(row.get("supporting_oracle_ids") or [])
                + list(row.get("supporting_regression_run_ids") or [])
            )
            equation_labels = self._dedupe_strings(list(coverage_ledger.get("equation_labels") or []))
            proof_obligation_rows: list[dict[str, Any]] = []
            for section in structure_map.get("sections") or []:
                if str(section.get("status") or "") == "missing":
                    section_id = str(section.get("section_id") or "(missing)")
                    proof_obligation_rows.append(
                        {
                            "obligation_id": f"proof_obligation:{slugify(current_candidate_id)}:section:{slugify(section_id)}",
                            "category": "source_section_recovery",
                            "status": "source-cited-only",
                            "claim": f"Recover the missing source section `{section_id}` before Lean export.",
                            "prerequisite_ids": [section_id],
                            "equation_labels": equation_labels,
                            "source_anchor_ids": [section_id],
                            "required_logical_move": "Return to L0 and ingest the cited section so the omitted derivation can be grounded.",
                            "expected_output_statement": f"The theorem family regains a grounded section-level derivation for `{section_id}`.",
                        }
                    )
            if str(notation_table.get("status") or "") != "captured":
                proof_obligation_rows.append(
                    {
                        "obligation_id": f"proof_obligation:{slugify(current_candidate_id)}:notation-capture",
                        "category": "notation_capture",
                        "status": "blocked",
                        "claim": "Complete the notation table before Lean export.",
                        "prerequisite_ids": dependency_ids,
                        "equation_labels": equation_labels,
                        "source_anchor_ids": [],
                        "required_logical_move": "Bind every non-trivial symbol to an explicit meaning and regime.",
                        "expected_output_statement": "Notation bindings are complete enough for declaration-level formalization.",
                    }
                )
            if str(derivation_graph.get("status") or "") != "captured":
                proof_obligation_rows.append(
                    {
                        "obligation_id": f"proof_obligation:{slugify(current_candidate_id)}:derivation-capture",
                        "category": "derivation_capture",
                        "status": "blocked",
                        "claim": "Complete the derivation graph before Lean export.",
                        "prerequisite_ids": dependency_ids,
                        "equation_labels": equation_labels,
                        "source_anchor_ids": [],
                        "required_logical_move": "Decompose the derivation into explicit nodes and edges instead of leaving the proof spine implicit.",
                        "expected_output_statement": "The derivation graph exposes the ordered proof spine used by the target declaration.",
                    }
                )
            for blocker in row.get("promotion_blockers") or []:
                text = str(blocker).strip()
                if text:
                    proof_obligation_rows.append(
                        {
                            "obligation_id": f"proof_obligation:{slugify(current_candidate_id)}:blocker:{slugify(text)[:40]}",
                            "category": "candidate_blocker",
                            "status": "blocked",
                            "claim": text,
                            "prerequisite_ids": dependency_ids,
                            "equation_labels": equation_labels,
                            "source_anchor_ids": [],
                            "required_logical_move": "Resolve the declared candidate blocker before exporting this family into Lean.",
                            "expected_output_statement": "The candidate blocker is cleared without widening scope or hiding missing steps.",
                        }
                    )
            if as_bool(row.get("split_required")):
                proof_obligation_rows.append(
                    {
                        "obligation_id": f"proof_obligation:{slugify(current_candidate_id)}:split-before-export",
                        "category": "scope_split",
                        "status": "blocked",
                        "claim": "Split the candidate into narrower formal units before Lean export.",
                        "prerequisite_ids": [current_candidate_id],
                        "equation_labels": equation_labels,
                        "source_anchor_ids": [],
                        "required_logical_move": "Emit a candidate split contract and export only bounded children.",
                        "expected_output_statement": "The Lean bridge targets a bounded theorem/definition family rather than a mixed candidate.",
                    }
                )
            if as_bool(row.get("cited_recovery_required")):
                proof_obligation_rows.append(
                    {
                        "obligation_id": f"proof_obligation:{slugify(current_candidate_id)}:cited-recovery",
                        "category": "cited_recovery",
                        "status": "source-cited-only",
                        "claim": "Return to L0 for cited-source recovery before Lean export.",
                        "prerequisite_ids": [current_candidate_id],
                        "equation_labels": equation_labels,
                        "source_anchor_ids": [],
                        "required_logical_move": "Ingest the cited prerequisite source and route the recovered units back through L1/L3/L4.",
                        "expected_output_statement": "The proof family no longer depends on uncaptured cited background.",
                    }
                )
            for item in regression_gate.get("blocking_reasons") or []:
                text = str(item).strip()
                if text:
                    proof_obligation_rows.append(
                        {
                            "obligation_id": f"proof_obligation:{slugify(current_candidate_id)}:regression:{slugify(text)[:40]}",
                            "category": "regression_gate",
                            "status": "blocked",
                            "claim": f"Regression gate: {text}",
                            "prerequisite_ids": list(row.get("supporting_regression_question_ids") or []),
                            "equation_labels": equation_labels,
                            "source_anchor_ids": [],
                            "required_logical_move": "Repair the regression-backed blocker rather than bypassing the gate.",
                            "expected_output_statement": "The regression gate passes with explicit supporting evidence.",
                        }
                    )
            for item in row.get("followup_gap_ids") or []:
                text = str(item).strip()
                if text:
                    proof_obligation_rows.append(
                        {
                            "obligation_id": f"proof_obligation:{slugify(current_candidate_id)}:gap:{slugify(text)}",
                            "category": "followup_gap",
                            "status": "deferred",
                            "claim": f"Open follow-up gap: {text}",
                            "prerequisite_ids": [text],
                            "equation_labels": equation_labels,
                            "source_anchor_ids": [text],
                            "required_logical_move": "Re-enter L0 and resolve the open gap before claiming a proof-grade export.",
                            "expected_output_statement": "The referenced open gap is either recovered or explicitly routed as future work.",
                        }
                    )
            proof_obligations = self._dedupe_strings(
                [f"{row['status']}: {row['claim']}" for row in proof_obligation_rows]
            )
            status_counts: dict[str, int] = {}
            for proof_row in proof_obligation_rows:
                proof_status = str(proof_row.get("status") or "blocked")
                status_counts[proof_status] = status_counts.get(proof_status, 0) + 1
            status = "ready" if not proof_obligation_rows else "needs_refinement"
            if status == "ready":
                ready_packet_count += 1
            statement_text = str(row.get("summary") or row.get("question") or row.get("title") or current_candidate_id)
            lean_skeleton_lines = [
                "import Mathlib",
                "",
                f"namespace {namespace}",
                "",
                f"{declaration_kind} {declaration_name} : Prop := by",
                "  sorry",
                "",
                "end " + namespace,
            ]
            proof_obligations_payload = {
                "bridge_version": 1,
                "topic_slug": topic_slug,
                "run_id": run_id,
                "candidate_id": current_candidate_id,
                "obligations": proof_obligation_rows,
                "updated_at": now_iso(),
                "updated_by": updated_by,
            }
            proof_state_payload = {
                "bridge_version": 1,
                "topic_slug": topic_slug,
                "run_id": run_id,
                "candidate_id": current_candidate_id,
                "status": status,
                "obligation_count": len(proof_obligation_rows),
                "status_counts": status_counts,
                "obligation_ids": [row["obligation_id"] for row in proof_obligation_rows],
                "dependency_ids": dependency_ids,
                "updated_at": now_iso(),
                "updated_by": updated_by,
            }
            packet_payload = {
                "$schema": "https://aitp.local/schemas/lean-ready-packet.schema.json",
                "bridge_version": 1,
                "topic_slug": topic_slug,
                "run_id": run_id,
                "candidate_id": current_candidate_id,
                "candidate_type": str(row.get("candidate_type") or ""),
                "status": status,
                "namespace": namespace,
                "declaration_kind": declaration_kind,
                "declaration_name": declaration_name,
                "statement_text": statement_text,
                "dependency_ids": dependency_ids,
                "equation_labels": equation_labels,
                "regression_gate_status": str(regression_gate.get("status") or "not_audited"),
                "notation_bindings": list(notation_table.get("bindings") or []),
                "proof_obligations": proof_obligations,
                "proof_obligation_count": len(proof_obligation_rows),
                "proof_obligations_path": self._relativize(packet_paths["proof_obligations"]),
                "proof_state_path": self._relativize(packet_paths["proof_state"]),
                "theory_packet_refs": {
                    "coverage_ledger": self._relativize(theory_packet_paths["coverage_ledger"]),
                    "structure_map": self._relativize(theory_packet_paths["structure_map"]),
                    "notation_table": self._relativize(theory_packet_paths["notation_table"]),
                    "derivation_graph": self._relativize(theory_packet_paths["derivation_graph"]),
                    "regression_gate": self._relativize(theory_packet_paths["regression_gate"]),
                },
                "lean_skeleton_lines": lean_skeleton_lines,
                "updated_at": now_iso(),
                "updated_by": updated_by,
            }
            write_json(packet_paths["proof_obligations"], proof_obligations_payload)
            write_text(
                packet_paths["proof_obligations_note"],
                self._render_proof_obligations_markdown(proof_obligation_rows),
            )
            write_json(packet_paths["proof_state"], proof_state_payload)
            write_text(
                packet_paths["proof_state_note"],
                self._render_proof_state_markdown(proof_state_payload),
            )
            write_json(packet_paths["json"], packet_payload)
            write_text(packet_paths["note"], self._render_lean_bridge_packet_markdown(packet_payload))
            packets.append(
                {
                    "candidate_id": current_candidate_id,
                    "candidate_type": str(row.get("candidate_type") or ""),
                    "declaration_kind": declaration_kind,
                    "status": status,
                    "proof_obligation_count": len(proof_obligation_rows),
                    "packet_path": self._relativize(packet_paths["json"]),
                    "packet_note_path": self._relativize(packet_paths["note"]),
                    "proof_obligations_path": self._relativize(packet_paths["proof_obligations"]),
                    "proof_state_path": self._relativize(packet_paths["proof_state"]),
                }
            )

        active_paths = self._lean_bridge_active_paths(topic_slug)
        if not packets:
            status = "empty"
            summary = "No candidate packet is available for Lean-ready export yet."
        elif ready_packet_count == len(packets):
            status = "ready"
            summary = "All selected packets are Lean-ready at the current shell level."
        else:
            status = "needs_refinement"
            summary = "At least one selected packet still carries proof obligations before Lean export."
        payload = {
            "$schema": "https://aitp.local/schemas/lean-bridge-active.schema.json",
            "bridge_version": 1,
            "topic_slug": topic_slug,
            "run_id": run_id or "",
            "status": status,
            "packet_count": len(packets),
            "ready_packet_count": ready_packet_count,
            "needs_refinement_count": max(len(packets) - ready_packet_count, 0),
            "packets": packets,
            "summary": summary,
            "updated_at": now_iso(),
            "updated_by": updated_by,
        }
        write_json(active_paths["json"], payload)
        write_text(active_paths["note"], self._render_lean_bridge_index_markdown(payload))
        return {
            **payload,
            "lean_bridge_path": str(active_paths["json"]),
            "lean_bridge_note_path": str(active_paths["note"]),
        }

    def ensure_topic_shell_surfaces(
        self,
        *,
        topic_slug: str,
        updated_by: str,
        human_request: str | None = None,
        topic_state: dict[str, Any] | None = None,
        interaction_state: dict[str, Any] | None = None,
        promotion_gate: dict[str, Any] | None = None,
        queue_rows: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        runtime_root = self._ensure_runtime_root(topic_slug)
        resolved_topic_state = dict(topic_state or read_json(runtime_root / "topic_state.json") or {})
        resolved_interaction_state = dict(
            interaction_state or read_json(runtime_root / "interaction_state.json") or {}
        )
        resolved_queue_rows = list(queue_rows or read_jsonl(runtime_root / "action_queue.jsonl"))
        resolved_promotion_gate = dict(promotion_gate or self._load_promotion_gate(topic_slug) or {})
        decision_surface = resolved_interaction_state.get("decision_surface") or {}
        pending_actions, selected_pending_action = self._pending_action_context(
            resolved_queue_rows,
            decision_surface,
        )
        latest_run_id = str(resolved_topic_state.get("latest_run_id") or "").strip()
        candidate_rows = self._candidate_rows_for_run(topic_slug, latest_run_id)
        promotion_readiness = self._derive_promotion_readiness(
            topic_slug=topic_slug,
            latest_run_id=latest_run_id,
            promotion_gate=resolved_promotion_gate,
            candidate_rows=candidate_rows,
        )
        open_gap_summary = self._derive_open_gap_summary(
            topic_slug=topic_slug,
            candidate_rows=candidate_rows,
            pending_actions=pending_actions,
            selected_pending_action=selected_pending_action,
        )
        topic_completion = self.assess_topic_completion(
            topic_slug=topic_slug,
            run_id=latest_run_id or None,
            updated_by=updated_by,
            refresh_runtime_bundle=False,
        )
        lean_bridge = self.prepare_lean_bridge(
            topic_slug=topic_slug,
            run_id=latest_run_id or None,
            updated_by=updated_by,
            refresh_runtime_bundle=False,
        )
        followup_reintegration_paths = self._write_followup_reintegration_rows(
            topic_slug,
            self._load_followup_reintegration_rows(topic_slug),
        )
        followup_gap_writeback_paths = self._write_followup_gap_writeback_rows(
            topic_slug,
            self._load_followup_gap_writeback_rows(topic_slug),
        )

        research_paths = self._research_question_contract_paths(topic_slug)
        validation_paths = self._validation_contract_paths(topic_slug)
        dashboard_path = self._topic_dashboard_path(topic_slug)
        readiness_path = self._promotion_readiness_path(topic_slug)
        gap_map_path = self._gap_map_path(topic_slug)

        existing_research = read_json(research_paths["json"]) or {}
        existing_validation = read_json(validation_paths["json"]) or {}

        research_mode = str(
            resolved_topic_state.get("research_mode")
            or existing_research.get("research_mode")
            or self._template_mode_to_research_mode(existing_research.get("template_mode"))
            or "exploratory_general"
        ).strip()
        template_mode = str(
            existing_research.get("template_mode")
            or self._research_mode_to_template_mode(research_mode)
        ).strip()
        validation_mode = str(
            existing_validation.get("validation_mode")
            or self._validation_mode_for_template(template_mode)
        ).strip()
        title = self._coalesce_string(
            existing_research.get("title"),
            self._topic_display_title(topic_slug),
        )
        selected_action_summary = str((selected_pending_action or {}).get("summary") or "").strip()
        active_question = self._coalesce_string(
            existing_research.get("question"),
            human_request
            or str(resolved_interaction_state.get("human_request") or "").strip()
            or f"Clarify, validate, and persist the bounded theoretical-physics question for {title}.",
        )

        context_defaults = self._dedupe_strings(
            [
                f"Human request: {human_request or resolved_interaction_state.get('human_request') or active_question}",
                f"Resume stage: {resolved_topic_state.get('resume_stage') or 'uninitialized'}",
                f"Latest run id: {latest_run_id or 'missing'}",
                f"Selected action: {selected_action_summary or 'none'}",
            ]
        )
        target_claim_defaults = self._dedupe_strings(
            [str(row.get("candidate_id") or "").strip() for row in candidate_rows if str(row.get("candidate_id") or "").strip()]
            or [str((selected_pending_action or {}).get("action_id") or "").strip()]
        )
        deliverable_defaults = [
            "Persist the active research question, validation route, and bounded next action as durable runtime artifacts.",
            "Write derivation/proof or execution evidence into the appropriate AITP layer before claiming completion.",
            "Produce Layer-appropriate outputs that can later be promoted into durable L2 knowledge when justified.",
        ]
        acceptance_defaults = [
            "The question, scope, deliverables, and acceptance checks remain synchronized with the runtime state.",
            "Missing definitions, cited derivations, or prior-work comparisons trigger a durable return to L0 instead of a prose-only bridge.",
            "Proof or validation claims cite concrete L3/L4 artifacts rather than memory or style confidence.",
        ]
        forbidden_proxy_defaults = [
            "Do not treat polished prose, hidden assumptions, or memory-only agreement as proof.",
            "Do not silently widen scope without updating this contract.",
            "Do not bypass L0 recovery when the blocker is really a missing source, citation chain, or prior-work comparison.",
        ]
        uncertainty_defaults = open_gap_summary["blockers"] or [
            "Mark unresolved notation, source, or regime gaps explicitly before continuing."
        ]
        research_status_default = "blocked" if open_gap_summary["requires_l0_return"] else "active"
        research_contract = {
            "contract_version": 1,
            "question_id": self._coalesce_string(
                existing_research.get("question_id"),
                f"research_question:{topic_slug}",
            ),
            "title": title,
            "topic_slug": topic_slug,
            "status": self._coalesce_string(existing_research.get("status"), research_status_default),
            "template_mode": template_mode,
            "research_mode": research_mode,
            "question": active_question,
            "scope": self._coalesce_list(
                existing_research.get("scope"),
                [
                    f"Keep work bounded to topic `{topic_slug}` and the currently selected action.",
                    "Make derivation dependencies, notation, and validation obligations explicit.",
                ]
                + ([f"Current bounded action: {selected_action_summary}"] if selected_action_summary else []),
            ),
            "assumptions": self._coalesce_list(
                existing_research.get("assumptions"),
                [
                    "Only persisted AITP artifacts count as research progress.",
                    "Missing cited derivations or prior-work context must be recovered through L0 rather than guessed.",
                ],
            ),
            "non_goals": self._coalesce_list(
                existing_research.get("non_goals"),
                [
                    "Do not treat the runtime shell as a generic project manager.",
                    "Do not claim theory completion without layer-addressable derivation or validation evidence.",
                ],
            ),
            "context_intake": self._coalesce_list(existing_research.get("context_intake"), context_defaults),
            "formalism_and_notation": self._coalesce_list(
                existing_research.get("formalism_and_notation"),
                [
                    f"Research mode `{research_mode}` governs the default level of derivation detail.",
                    "Notation bindings must be persisted explicitly when symbols or conventions are non-trivial.",
                ],
            ),
            "observables": self._coalesce_list(
                existing_research.get("observables"),
                [
                    "Declared candidate ids, bounded claims, and validation outcomes.",
                    "Promotion readiness, gap honesty, and whether the topic must return to L0.",
                ],
            ),
            "target_claims": self._coalesce_list(existing_research.get("target_claims"), target_claim_defaults),
            "deliverables": self._coalesce_list(existing_research.get("deliverables"), deliverable_defaults),
            "acceptance_tests": self._coalesce_list(
                existing_research.get("acceptance_tests"),
                acceptance_defaults,
            ),
            "forbidden_proxies": self._coalesce_list(
                existing_research.get("forbidden_proxies"),
                forbidden_proxy_defaults,
            ),
            "uncertainty_markers": self._coalesce_list(
                existing_research.get("uncertainty_markers"),
                uncertainty_defaults,
            ),
            "target_layers": self._coalesce_list(
                existing_research.get("target_layers"),
                ["L1", "L3", "L4", "L2"],
            ),
        }

        artifact_defaults = [
            self._relativize(runtime_root / "runtime_protocol.generated.md"),
            self._relativize(runtime_root / "action_queue.jsonl"),
            self._relativize(research_paths["note"]),
            self._relativize(dashboard_path),
        ]
        if (runtime_root / "conformance_report.md").exists():
            artifact_defaults.append(self._relativize(runtime_root / "conformance_report.md"))
        if (runtime_root / "capability_report.md").exists():
            artifact_defaults.append(self._relativize(runtime_root / "capability_report.md"))
        if self._promotion_gate_paths(topic_slug)["json"].exists():
            artifact_defaults.append(self._relativize(self._promotion_gate_paths(topic_slug)["json"]))

        validation_status_default = "deferred" if open_gap_summary["requires_l0_return"] else "planned"
        validation_contract = {
            "contract_version": 1,
            "validation_id": self._coalesce_string(
                existing_validation.get("validation_id"),
                f"validation:{topic_slug}:active",
            ),
            "topic_slug": topic_slug,
            "status": self._coalesce_string(existing_validation.get("status"), validation_status_default),
            "template_mode": template_mode,
            "verification_focus": self._coalesce_string(
                existing_validation.get("verification_focus"),
                selected_action_summary or promotion_readiness["summary"],
            ),
            "validation_mode": validation_mode,
            "target_claim_ids": self._coalesce_list(
                existing_validation.get("target_claim_ids"),
                target_claim_defaults,
            ),
            "acceptance_rule": self._coalesce_string(
                existing_validation.get("acceptance_rule"),
                "Accept only when the declared claims are supported by persisted derivation or execution artifacts and all active L0-recovery blockers are discharged.",
            ),
            "rejection_rule": self._coalesce_string(
                existing_validation.get("rejection_rule"),
                "Reject whenever missing anchors, missing executed evidence, unresolved cited-source gaps, or contract drift remain active.",
            ),
            "required_checks": self._coalesce_list(
                existing_validation.get("required_checks"),
                [
                    "Check that the research question, scope, and selected action still match the runtime state.",
                    "Check that proof, derivation, or execution evidence is persisted in the declared layer.",
                    "If prior-work or cited-source gaps remain, return to L0 before advancing the claim.",
                ],
            ),
            "oracle_artifacts": self._coalesce_list(
                existing_validation.get("oracle_artifacts"),
                artifact_defaults,
            ),
            "executed_evidence": self._coalesce_list(
                existing_validation.get("executed_evidence"),
                [],
            ),
            "confidence_cap": self._coalesce_string(
                existing_validation.get("confidence_cap"),
                "medium" if open_gap_summary["status"] != "clear" else "high",
            ),
            "gap_followups": self._coalesce_list(
                existing_validation.get("gap_followups"),
                open_gap_summary["blockers"] + open_gap_summary["followup_gap_ids"],
            ),
            "failure_modes": self._coalesce_list(
                existing_validation.get("failure_modes"),
                [
                    "Proof steps remain implicit or depend on unstated notation.",
                    "Executed validation is claimed but no durable evidence path exists.",
                    "A cited derivation or prior-work dependency was glossed over instead of recovered through L0.",
                ],
            ),
            "artifacts": self._coalesce_list(
                existing_validation.get("artifacts"),
                artifact_defaults,
            ),
        }

        write_json(research_paths["json"], research_contract)
        write_text(research_paths["note"], self._render_research_question_contract_markdown(research_contract))
        write_json(validation_paths["json"], validation_contract)
        write_text(validation_paths["note"], self._render_validation_contract_markdown(validation_contract))
        write_text(
            dashboard_path,
            self._render_topic_dashboard_markdown(
                topic_slug=topic_slug,
                topic_state=resolved_topic_state,
                selected_pending_action=selected_pending_action,
                pending_actions=pending_actions,
                research_contract=research_contract,
                validation_contract=validation_contract,
                promotion_readiness=promotion_readiness,
                open_gap_summary=open_gap_summary,
                topic_completion=topic_completion,
                lean_bridge=lean_bridge,
            ),
        )
        write_text(readiness_path, self._render_promotion_readiness_markdown(promotion_readiness))
        write_text(gap_map_path, self._render_gap_map_markdown(open_gap_summary))
        return {
            "research_question_contract_path": str(research_paths["json"]),
            "research_question_contract_note_path": str(research_paths["note"]),
            "validation_contract_path": str(validation_paths["json"]),
            "validation_contract_note_path": str(validation_paths["note"]),
            "topic_dashboard_path": str(dashboard_path),
            "promotion_readiness_path": str(readiness_path),
            "gap_map_path": str(gap_map_path),
            "topic_completion_path": topic_completion["topic_completion_path"],
            "topic_completion_note_path": topic_completion["topic_completion_note_path"],
            "lean_bridge_path": lean_bridge["lean_bridge_path"],
            "lean_bridge_note_path": lean_bridge["lean_bridge_note_path"],
            "followup_reintegration_path": followup_reintegration_paths["followup_reintegration_path"],
            "followup_reintegration_note_path": followup_reintegration_paths["followup_reintegration_note_path"],
            "followup_gap_writeback_path": followup_gap_writeback_paths["followup_gap_writeback_path"],
            "followup_gap_writeback_note_path": followup_gap_writeback_paths["followup_gap_writeback_note_path"],
            "research_question_contract": research_contract,
            "validation_contract": validation_contract,
            "promotion_readiness": promotion_readiness,
            "open_gap_summary": open_gap_summary,
            "topic_completion": topic_completion,
            "lean_bridge": lean_bridge,
        }

    def _deferred_buffer_markdown(self, payload: dict[str, Any]) -> str:
        lines = [
            "# Deferred candidate buffer",
            "",
            f"- Topic slug: `{payload['topic_slug']}`",
            f"- Updated at: `{payload['updated_at']}`",
            f"- Updated by: `{payload['updated_by']}`",
            f"- Entry count: `{len(payload.get('entries') or [])}`",
            "",
        ]
        for entry in payload.get("entries") or []:
            lines.extend(
                [
                    f"## `{entry.get('entry_id') or '(missing)'}`",
                    "",
                    f"- Source candidate: `{entry.get('source_candidate_id') or '(missing)'}`",
                    f"- Title: `{entry.get('title') or '(missing)'}`",
                    f"- Status: `{entry.get('status') or '(missing)'}`",
                    f"- Reason: {entry.get('reason') or '(missing)'}",
                ]
            )
            required_l2_types = self._dedupe_strings(list(entry.get("required_l2_types") or []))
            if required_l2_types:
                lines.append(f"- Missing L2 types: `{', '.join(required_l2_types)}`")
            activated_candidate_id = str(entry.get("activated_candidate_id") or "").strip()
            if activated_candidate_id:
                lines.append(f"- Activated candidate: `{activated_candidate_id}`")
            conditions = entry.get("reactivation_conditions") or {}
            if conditions:
                lines.extend(["", "### Reactivation conditions", ""])
                for key in sorted(conditions):
                    values = self._dedupe_strings(list(conditions.get(key) or []))
                    if values:
                        lines.append(f"- `{key}`: `{', '.join(values)}`")
            notes = str(entry.get("notes") or "").strip()
            if notes:
                lines.extend(["", "### Notes", "", f"- {notes}"])
            lines.append("")
        if not (payload.get("entries") or []):
            lines.append("- No deferred entries are currently buffered.")
            lines.append("")
        return "\n".join(lines)

    def _followup_subtopics_markdown(self, rows: list[dict[str, Any]]) -> str:
        lines = [
            "# Follow-up subtopics",
            "",
            f"- Entry count: `{len(rows)}`",
            "",
        ]
        for row in rows:
            lines.extend(
                [
                    f"## `{row.get('child_topic_slug') or '(missing)'}`",
                    "",
                    f"- Parent topic: `{row.get('parent_topic_slug') or '(missing)'}`",
                    f"- Parent run: `{row.get('parent_run_id') or '(missing)'}`",
                    f"- Query: `{row.get('query') or '(missing)'}`",
                    f"- Source id: `{row.get('source_id') or '(missing)'}`",
                    f"- arXiv id: `{row.get('arxiv_id') or '(missing)'}`",
                    f"- Status: `{row.get('status') or '(missing)'}`",
                    f"- Parent gaps: `{', '.join(row.get('parent_gap_ids') or []) or '(none)'}`",
                    f"- Parent follow-up tasks: `{', '.join(row.get('parent_followup_task_ids') or []) or '(none)'}`",
                    f"- Reentry targets: `{', '.join(row.get('reentry_targets') or []) or '(none)'}`",
                    f"- Return packet: `{row.get('return_packet_path') or '(missing)'}`",
                    "",
                ]
            )
        if not rows:
            lines.append("- No follow-up subtopics have been spawned yet.")
            lines.append("")
        return "\n".join(lines)

    def _followup_reintegration_markdown(self, rows: list[dict[str, Any]]) -> str:
        lines = [
            "# Follow-up reintegration",
            "",
            f"- Receipt count: `{len(rows)}`",
            "",
        ]
        for row in rows:
            lines.extend(
                [
                    f"## `{row.get('child_topic_slug') or '(missing)'}`",
                    "",
                    f"- Parent topic: `{row.get('parent_topic_slug') or '(missing)'}`",
                    f"- Parent run: `{row.get('parent_run_id') or '(missing)'}`",
                    f"- Return status: `{row.get('return_status') or '(missing)'}`",
                    f"- Accepted return shape: `{row.get('accepted_return_shape') or '(missing)'}`",
                    f"- Receipt id: `{row.get('receipt_id') or '(missing)'}`",
                    f"- Return packet: `{row.get('return_packet_path') or '(missing)'}`",
                    f"- Reentry targets: `{', '.join(row.get('reentry_targets') or []) or '(none)'}`",
                    f"- Parent gaps: `{', '.join(row.get('parent_gap_ids') or []) or '(none)'}`",
                    f"- Child completion: `{row.get('child_topic_completion_status') or 'not_assessed'}`",
                    f"- Gap writeback required: `{str(bool(row.get('gap_writeback_required'))).lower()}`",
                    "",
                    row.get("summary") or "(missing)",
                    "",
                ]
            )
        if not rows:
            lines.append("- No follow-up reintegration receipts have been recorded yet.")
            lines.append("")
        return "\n".join(lines)

    def _followup_gap_writeback_markdown(self, rows: list[dict[str, Any]]) -> str:
        lines = [
            "# Follow-up gap writeback",
            "",
            f"- Entry count: `{len(rows)}`",
            "",
        ]
        for row in rows:
            lines.extend(
                [
                    f"## `{row.get('child_topic_slug') or '(missing)'}`",
                    "",
                    f"- Parent topic: `{row.get('parent_topic_slug') or '(missing)'}`",
                    f"- Parent run: `{row.get('parent_run_id') or '(missing)'}`",
                    f"- Return status: `{row.get('return_status') or '(missing)'}`",
                    f"- Parent gaps: `{', '.join(row.get('parent_gap_ids') or []) or '(none)'}`",
                    f"- Parent follow-up tasks: `{', '.join(row.get('parent_followup_task_ids') or []) or '(none)'}`",
                    f"- Reentry targets: `{', '.join(row.get('reentry_targets') or []) or '(none)'}`",
                    "",
                    row.get("summary") or "(missing)",
                    "",
                ]
            )
        if not rows:
            lines.append("- No unresolved child follow-up gap writeback is currently pending.")
            lines.append("")
        return "\n".join(lines)

    def _load_deferred_buffer(self, topic_slug: str) -> dict[str, Any]:
        paths = self._deferred_buffer_paths(topic_slug)
        return read_json(paths["json"]) or {
            "buffer_version": 1,
            "topic_slug": topic_slug,
            "updated_at": now_iso(),
            "updated_by": "aitp-cli",
            "entries": [],
        }

    def _write_deferred_buffer(self, topic_slug: str, payload: dict[str, Any]) -> dict[str, str]:
        paths = self._deferred_buffer_paths(topic_slug)
        payload["buffer_version"] = 1
        payload["topic_slug"] = topic_slug
        write_json(paths["json"], payload)
        write_text(paths["note"], self._deferred_buffer_markdown(payload))
        return {
            "deferred_buffer_path": str(paths["json"]),
            "deferred_buffer_note_path": str(paths["note"]),
        }

    def _load_followup_subtopic_rows(self, topic_slug: str) -> list[dict[str, Any]]:
        return read_jsonl(self._followup_subtopics_paths(topic_slug)["jsonl"])

    def _write_followup_subtopic_rows(self, topic_slug: str, rows: list[dict[str, Any]]) -> dict[str, str]:
        paths = self._followup_subtopics_paths(topic_slug)
        write_jsonl(paths["jsonl"], rows)
        write_text(paths["note"], self._followup_subtopics_markdown(rows))
        return {
            "followup_subtopics_path": str(paths["jsonl"]),
            "followup_subtopics_note_path": str(paths["note"]),
        }

    def _write_followup_return_packet(self, topic_slug: str, payload: dict[str, Any]) -> str:
        path = self._followup_return_packet_path(topic_slug)
        write_json(path, payload)
        write_text(self._followup_return_packet_note_path(topic_slug), self._followup_return_packet_markdown(payload))
        return str(path)

    def _load_followup_reintegration_rows(self, topic_slug: str) -> list[dict[str, Any]]:
        return read_jsonl(self._followup_reintegration_paths(topic_slug)["jsonl"])

    def _write_followup_reintegration_rows(self, topic_slug: str, rows: list[dict[str, Any]]) -> dict[str, str]:
        paths = self._followup_reintegration_paths(topic_slug)
        write_jsonl(paths["jsonl"], rows)
        write_text(paths["note"], self._followup_reintegration_markdown(rows))
        return {
            "followup_reintegration_path": str(paths["jsonl"]),
            "followup_reintegration_note_path": str(paths["note"]),
        }

    def _load_followup_gap_writeback_rows(self, topic_slug: str) -> list[dict[str, Any]]:
        return read_jsonl(self._followup_gap_writeback_paths(topic_slug)["jsonl"])

    def _write_followup_gap_writeback_rows(self, topic_slug: str, rows: list[dict[str, Any]]) -> dict[str, str]:
        paths = self._followup_gap_writeback_paths(topic_slug)
        write_jsonl(paths["jsonl"], rows)
        write_text(paths["note"], self._followup_gap_writeback_markdown(rows))
        return {
            "followup_gap_writeback_path": str(paths["jsonl"]),
            "followup_gap_writeback_note_path": str(paths["note"]),
        }

    def _reactivation_context(self, topic_slug: str) -> tuple[set[str], str, set[str]]:
        source_rows = read_jsonl(self.kernel_root / "source-layer" / "topics" / topic_slug / "source_index.jsonl")
        source_ids = {
            str(row.get("source_id") or "").strip()
            for row in source_rows
            if str(row.get("source_id") or "").strip()
        }
        source_text = " ".join(
            self._dedupe_strings(
                [
                    str(row.get("title") or "")
                    for row in source_rows
                ]
                + [
                    str(row.get("summary") or "")
                    for row in source_rows
                ]
            )
        ).lower()
        child_topics = {
            str(row.get("child_topic_slug") or "").strip()
            for row in self._load_followup_subtopic_rows(topic_slug)
            if str(row.get("child_topic_slug") or "").strip()
        }
        return source_ids, source_text, child_topics

    def _buffer_entry_ready_for_reactivation(
        self,
        entry: dict[str, Any],
        *,
        source_ids: set[str],
        source_text: str,
        child_topics: set[str],
    ) -> bool:
        conditions = entry.get("reactivation_conditions") or {}
        source_id_rules = {
            str(value).strip()
            for value in (conditions.get("source_ids_any") or [])
            if str(value).strip()
        }
        if source_id_rules and source_ids.intersection(source_id_rules):
            return True
        text_rules = [
            str(value).strip().lower()
            for value in (conditions.get("text_contains_any") or [])
            if str(value).strip()
        ]
        if text_rules and any(rule in source_text for rule in text_rules):
            return True
        child_topic_rules = {
            str(value).strip()
            for value in (conditions.get("child_topics_any") or [])
            if str(value).strip()
        }
        if child_topic_rules and child_topics.intersection(child_topic_rules):
            return True
        return not source_id_rules and not text_rules and not child_topic_rules

    def _operation_requirement_defaults(self, kind: str) -> tuple[bool, bool]:
        normalized = slugify(kind)
        baseline_required = normalized in {
            "numerical",
            "diagnostic",
            "backend",
            "execution",
            "simulation",
            "coding",
        }
        atomic_required = normalized in {
            "symbolic",
            "formal",
            "derivation",
            "theoretical",
            "proof",
        }
        return baseline_required, atomic_required

    def _operation_summary_path(self, topic_slug: str, run_id: str, operation_id: str) -> Path:
        return self._operation_root(topic_slug, run_id, operation_id) / "operation_summary.md"

    def _read_operation_manifest(self, topic_slug: str, run_id: str, operation_id: str) -> dict[str, Any]:
        manifest_path = self._operation_manifest_path(topic_slug, run_id, operation_id)
        manifest = read_json(manifest_path)
        if manifest is None:
            raise FileNotFoundError(f"Operation manifest missing: {manifest_path}")
        return manifest

    def _baseline_status_ready(self, status: str) -> bool:
        return status.strip().lower() in {"not_required", "pass", "passed", "satisfied", "complete", "completed"}

    def _atomic_status_ready(self, status: str) -> bool:
        return status.strip().lower() in {
            "not_required",
            "understood",
            "pass",
            "passed",
            "satisfied",
            "complete",
            "completed",
        }

    def _ensure_runtime_root(self, topic_slug: str) -> Path:
        runtime_root = self._runtime_root(topic_slug)
        runtime_root.mkdir(parents=True, exist_ok=True)
        return runtime_root

    def _load_action_queue(self, topic_slug: str) -> tuple[Path, list[dict[str, Any]]]:
        queue_path = self._runtime_root(topic_slug) / "action_queue.jsonl"
        return queue_path, read_jsonl(queue_path)

    def _runtime_protocol_paths(self, topic_slug: str) -> dict[str, Path]:
        runtime_root = self._runtime_root(topic_slug)
        return {
            "json": runtime_root / "runtime_protocol.generated.json",
            "note": runtime_root / "runtime_protocol.generated.md",
        }

    def _load_candidate(self, topic_slug: str, run_id: str, candidate_id: str) -> dict[str, Any]:
        rows = read_jsonl(self._candidate_ledger_path(topic_slug, run_id))
        for row in rows:
            if str(row.get("candidate_id") or "").strip() == candidate_id:
                return row
        raise FileNotFoundError(f"Candidate {candidate_id} not found for topic {topic_slug} run {run_id}")

    def _replace_candidate_row(
        self,
        topic_slug: str,
        run_id: str,
        candidate_id: str,
        updated_row: dict[str, Any],
    ) -> None:
        ledger_path = self._candidate_ledger_path(topic_slug, run_id)
        rows = []
        replaced = False
        for row in read_jsonl(ledger_path):
            if str(row.get("candidate_id") or "").strip() == candidate_id:
                rows.append(updated_row)
                replaced = True
            else:
                rows.append(row)
        if not replaced:
            rows.append(updated_row)
        write_jsonl(ledger_path, rows)

    def _detect_tpkn_root(self) -> Path | None:
        env_override = os.environ.get("AITP_TPKN_ROOT")
        candidates: list[Path] = []
        if env_override:
            candidates.append(Path(env_override).expanduser())
        candidates.extend(
            [
                self.repo_root.parent / "theoretical-physics-knowledge-network",
                self.repo_root.parent / "Theoretical-Physics-Knowledge-Network",
            ]
        )
        for candidate in candidates:
            resolved = candidate.expanduser().resolve()
            if (resolved / "scripts" / "kb.py").exists() and (resolved / "units").exists():
                return resolved
        return None

    def _load_backend_card(self, backend_id: str) -> tuple[Path | None, dict[str, Any] | None]:
        registry_rows = read_jsonl(self.kernel_root / "canonical" / "backends" / "backend_index.jsonl")
        for row in registry_rows:
            if str(row.get("backend_id") or "").strip() != backend_id:
                continue
            card_path = str(row.get("card_path") or "").strip()
            if card_path:
                candidate = Path(card_path).expanduser()
                if not candidate.is_absolute():
                    candidate = self.kernel_root / card_path
                payload = read_json(candidate)
                if payload is not None:
                    return candidate.resolve(), payload

        for card_path in sorted((self.kernel_root / "canonical" / "backends").rglob("*.json")):
            payload = read_json(card_path)
            if payload is None:
                continue
            if str(payload.get("backend_id") or "").strip() == backend_id:
                return card_path.resolve(), payload
        return None, None

    def _resolve_tpkn_root(
        self,
        *,
        backend_id: str | None,
        target_backend_root: str | None,
    ) -> tuple[Path, Path | None, dict[str, Any] | None]:
        if target_backend_root:
            resolved = Path(target_backend_root).expanduser().resolve()
            if not (resolved / "scripts" / "kb.py").exists():
                raise FileNotFoundError(f"TPKN backend root missing scripts/kb.py: {resolved}")
            return resolved, None, None

        if backend_id:
            card_path, card_payload = self._load_backend_card(backend_id)
            if card_payload:
                for root_path in card_payload.get("root_paths") or []:
                    candidate = str(root_path).strip()
                    if not candidate or candidate.startswith("__"):
                        continue
                    resolved = Path(candidate).expanduser().resolve()
                    if (resolved / "scripts" / "kb.py").exists():
                        return resolved, card_path, card_payload
            detected = self._detect_tpkn_root()
            if detected is not None:
                return detected, card_path, card_payload

        detected = self._detect_tpkn_root()
        if detected is not None:
            return detected, None, None
        raise FileNotFoundError("Unable to resolve a TPKN backend root. Pass --target-backend-root or set AITP_TPKN_ROOT.")

    def _backend_supports_candidate_type(self, backend_payload: dict[str, Any] | None, candidate_type: str) -> bool:
        if not backend_payload:
            return True
        targets = {str(value).strip() for value in backend_payload.get("canonical_targets") or [] if str(value).strip()}
        return not targets or candidate_type in targets

    def _backend_allows_auto_promotion(self, backend_payload: dict[str, Any] | None) -> bool:
        source_policy = (backend_payload or {}).get("source_policy") or {}
        return bool(source_policy.get("allows_auto_canonical_promotion"))

    def _promotion_gate_markdown(self, payload: dict[str, Any]) -> str:
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

    def _write_promotion_gate(self, topic_slug: str, payload: dict[str, Any]) -> dict[str, str]:
        paths = self._promotion_gate_paths(topic_slug)
        write_json(paths["json"], payload)
        write_text(paths["note"], self._promotion_gate_markdown(payload))
        return {
            "promotion_gate_path": str(paths["json"]),
            "promotion_gate_note_path": str(paths["note"]),
        }

    def _load_promotion_gate(self, topic_slug: str) -> dict[str, Any] | None:
        return read_json(self._promotion_gate_paths(topic_slug)["json"])

    def _append_promotion_gate_log(self, topic_slug: str, run_id: str, row: dict[str, Any]) -> str:
        log_path = self._promotion_gate_log_path(topic_slug, run_id)
        rows = read_jsonl(log_path)
        rows.append(row)
        write_jsonl(log_path, rows)
        return str(log_path)

    def _theory_packet_root(self, topic_slug: str, run_id: str, candidate_id: str) -> Path:
        return self._validation_run_root(topic_slug, run_id) / "theory-packets" / slugify(candidate_id)

    def _theory_packet_paths(self, topic_slug: str, run_id: str, candidate_id: str) -> dict[str, Path]:
        packet_root = self._theory_packet_root(topic_slug, run_id, candidate_id)
        return {
            "root": packet_root,
            "structure_map": packet_root / "structure_map.json",
            "coverage_ledger": packet_root / "coverage_ledger.json",
            "notation_table": packet_root / "notation_table.json",
            "derivation_graph": packet_root / "derivation_graph.json",
            "agent_consensus": packet_root / "agent_consensus.json",
            "regression_gate": packet_root / "regression_gate.json",
            "merge_report": packet_root / "merge_report.json",
            "auto_promotion_report": packet_root / "auto_promotion_report.json",
        }

    def _consultation_paths(self, topic_slug: str, consultation_slug: str) -> dict[str, Path]:
        call_root = self._consultation_root(topic_slug) / "calls" / f"consult-{consultation_slug}"
        return {
            "request": call_root / "request.json",
            "result": call_root / "result.json",
            "application": call_root / "application.json",
            "index": self._consultation_root(topic_slug) / "consultation_index.jsonl",
        }

    def _record_l2_consultation(
        self,
        *,
        topic_slug: str,
        stage: str,
        run_id: str | None,
        consultation_slug: str,
        context_ref: dict[str, Any],
        purpose: str,
        query_text: str,
        requested_unit_types: list[str],
        retrieved_refs: list[dict[str, Any]],
        result_summary: str,
        effect_on_work: str,
        outcome: str,
        projection_paths: list[str],
        requested_by: str,
        produced_by: str,
        written_by: str,
        retrieval_profile: str,
    ) -> dict[str, str]:
        consultation_id = f"consult:{consultation_slug}"
        timestamp = now_iso()
        paths = self._consultation_paths(topic_slug, consultation_slug)

        request_payload: dict[str, Any] = {
            "consultation_id": consultation_id,
            "topic_slug": topic_slug,
            "stage": stage,
            "context_ref": context_ref,
            "purpose": purpose,
            "query_text": query_text,
            "requested_unit_types": requested_unit_types,
            "requested_by": requested_by,
            "requested_at": timestamp,
            "notes": "Generated by AITP service during backend consultation.",
        }
        result_payload: dict[str, Any] = {
            "consultation_id": consultation_id,
            "topic_slug": topic_slug,
            "stage": stage,
            "retrieval_profile": retrieval_profile,
            "query_text": query_text,
            "retrieved_refs": retrieved_refs,
            "expanded_edge_types": [],
            "result_summary": result_summary,
            "produced_by": produced_by,
            "produced_at": timestamp,
            "notes": "Generated during an explicit backend-aware collision scan.",
        }
        application_payload: dict[str, Any] = {
            "consultation_id": consultation_id,
            "topic_slug": topic_slug,
            "stage": stage,
            "context_ref": context_ref,
            "applied_refs": retrieved_refs,
            "deferred_refs": [],
            "effect_on_work": effect_on_work,
            "outcome": outcome,
            "projection_paths": projection_paths,
            "written_by": written_by,
            "written_at": timestamp,
            "notes": "Generated after applying backend consultation to the promotion path.",
        }
        index_entry: dict[str, Any] = {
            "consultation_id": consultation_id,
            "topic_slug": topic_slug,
            "stage": stage,
            "status": "applied",
            "context_ref": context_ref,
            "request_path": self._relativize(paths["request"]),
            "result_path": self._relativize(paths["result"]),
            "application_path": self._relativize(paths["application"]),
            "summary": result_summary,
        }
        if run_id:
            request_payload["run_id"] = run_id
            result_payload["run_id"] = run_id
            application_payload["run_id"] = run_id
            index_entry["run_id"] = run_id

        write_json(paths["request"], request_payload)
        write_json(paths["result"], result_payload)
        write_json(paths["application"], application_payload)
        index_rows = [row for row in read_jsonl(paths["index"]) if row.get("consultation_id") != consultation_id]
        index_rows.append(index_entry)
        write_jsonl(paths["index"], index_rows)

        if run_id:
            if stage == "L1":
                projection_path = self.kernel_root / "intake" / "topics" / topic_slug / "l2_consultation_log.jsonl"
            elif stage == "L3":
                projection_path = self._feedback_run_root(topic_slug, run_id) / "l2_consultation_log.jsonl"
            else:
                projection_path = self._validation_run_root(topic_slug, run_id) / "l2_consultation_log.jsonl"
            projection_rows = read_jsonl(projection_path)
            projection_rows.append(
                {
                    "consultation_id": consultation_id,
                    "stage": stage,
                    "request_path": self._relativize(paths["request"]),
                    "result_path": self._relativize(paths["result"]),
                    "application_path": self._relativize(paths["application"]),
                    "updated_at": timestamp,
                }
            )
            write_jsonl(projection_path, projection_rows)

        return {
            "consultation_request_path": str(paths["request"]),
            "consultation_result_path": str(paths["result"]),
            "consultation_application_path": str(paths["application"]),
            "consultation_index_path": str(paths["index"]),
        }

    def _runtime_protocol_markdown(self, payload: dict[str, Any]) -> str:
        minimal = payload.get("minimal_execution_brief") or {}
        active_research_contract = payload.get("active_research_contract") or {}
        promotion_readiness = payload.get("promotion_readiness") or {}
        open_gap_summary = payload.get("open_gap_summary") or {}
        topic_completion = payload.get("topic_completion") or {}
        lean_bridge = payload.get("lean_bridge") or {}
        must_read_now = payload.get("must_read_now") or []
        active_hard_constraints = payload.get("active_hard_constraints") or []
        escalation_triggers = payload.get("escalation_triggers") or []
        may_defer_until_trigger = payload.get("may_defer_until_trigger") or []
        recommended_protocol_slices = payload.get("recommended_protocol_slices") or []
        lines = [
            "# AITP runtime protocol bundle",
            "",
            f"- JSON schema: `{payload.get('$schema') or '(missing)'}`",
            f"- Bundle kind: `{payload.get('bundle_kind') or '(missing)'}`",
            f"- Topic slug: `{payload['topic_slug']}`",
            f"- Updated at: `{payload['updated_at']}`",
            f"- Updated by: `{payload['updated_by']}`",
            f"- Human request: `{payload['human_request'] or '(missing)'}`",
            f"- Resume stage: `{payload['resume_stage'] or '(missing)'}`",
            f"- Last materialized stage: `{payload['last_materialized_stage'] or '(missing)'}`",
            f"- Research mode: `{payload['research_mode'] or '(missing)'}`",
            "",
            "## Active research contract",
            "",
            f"- Question id: `{active_research_contract.get('question_id') or '(missing)'}`",
            f"- Title: `{active_research_contract.get('title') or '(missing)'}`",
            f"- Status: `{active_research_contract.get('status') or '(missing)'}`",
            f"- Template mode: `{active_research_contract.get('template_mode') or '(missing)'}`",
            f"- Validation mode: `{active_research_contract.get('validation_mode') or '(missing)'}`",
            f"- Contract JSON: `{active_research_contract.get('path') or '(missing)'}`",
            f"- Contract note: `{active_research_contract.get('note_path') or '(missing)'}`",
            "",
            f"{active_research_contract.get('question') or '(missing)'}",
            "",
            "## Promotion readiness",
            "",
            f"- Status: `{promotion_readiness.get('status') or '(missing)'}`",
            f"- Gate status: `{promotion_readiness.get('gate_status') or '(missing)'}`",
            f"- Summary note: `{promotion_readiness.get('path') or '(missing)'}`",
            f"- Ready candidates: `{', '.join(promotion_readiness.get('ready_candidate_ids') or []) or '(none)'}`",
            "",
            f"{promotion_readiness.get('summary') or '(missing)'}",
            "",
            "## Open gap summary",
            "",
            f"- Status: `{open_gap_summary.get('status') or '(missing)'}`",
            f"- Gap count: `{open_gap_summary.get('gap_count') or 0}`",
            f"- Follow-up gap writeback count: `{open_gap_summary.get('followup_gap_writeback_count') or 0}`",
            f"- Requires L0 return: `{str(bool(open_gap_summary.get('requires_l0_return'))).lower()}`",
            f"- Gap map: `{open_gap_summary.get('path') or '(missing)'}`",
            "",
            f"{open_gap_summary.get('summary') or '(missing)'}",
            "",
            "## Topic completion",
            "",
            f"- Status: `{topic_completion.get('status') or '(missing)'}`",
            f"- Completion note: `{topic_completion.get('path') or '(missing)'}`",
            f"- Promotion-ready candidates: `{', '.join(topic_completion.get('promotion_ready_candidate_ids') or []) or '(none)'}`",
            "",
            f"{topic_completion.get('summary') or '(missing)'}",
            "",
            "## Lean bridge",
            "",
            f"- Status: `{lean_bridge.get('status') or '(missing)'}`",
            f"- Packet count: `{lean_bridge.get('packet_count') or 0}`",
            f"- Bridge note: `{lean_bridge.get('path') or '(missing)'}`",
            "",
            f"{lean_bridge.get('summary') or '(missing)'}",
            "",
            "## Minimal execution brief",
            "",
            f"- Current stage: `{minimal.get('current_stage') or payload['resume_stage'] or '(missing)'}`",
            f"- Current bounded action: `{minimal.get('selected_action_summary') or '(no pending action)'}`",
            f"- Selected action id: `{minimal.get('selected_action_id') or '(none)'}`",
            f"- Selected action type: `{minimal.get('selected_action_type') or '(none)'}`",
            f"- Decision source: `{minimal.get('decision_source') or '(missing)'}`",
            f"- Queue source: `{minimal.get('queue_source') or '(missing)'}`",
            f"- Open next: `{minimal.get('open_next') or '(missing)'}`",
            "",
            "### Allowed now",
            "",
        ]
        for item in minimal.get("immediate_allowed_work") or ["Continue bounded work only after reading the required top-level surfaces."]:
            lines.append(f"- {item}")
        lines.extend(
            [
                "",
                "### Blocked now",
                "",
            ]
        )
        for item in minimal.get("immediate_blocked_work") or ["Do not treat deferred surfaces as optional once their trigger fires."]:
            lines.append(f"- {item}")
        lines.extend(
            [
                "",
                "## Must read now",
                "",
            ]
        )
        for idx, item in enumerate(must_read_now, start=1):
            lines.append(f"{idx}. `{item['path']}` - {item['reason']}")
        lines.extend(
            [
                "",
                "## Active hard constraints",
                "",
            ]
        )
        for item in active_hard_constraints:
            lines.append(f"- {item}")
        lines.extend(
            [
                "",
                "## Escalate only when triggered",
                "",
            ]
        )
        for item in escalation_triggers:
            status = "active" if item.get("active") else "inactive"
            lines.append(f"- `{item['trigger']}` status=`{status}`: {item['condition']}")
            required_reads = item.get("required_reads") or []
            if required_reads:
                lines.append(f"  required_reads=`{', '.join(required_reads)}`")
        lines.extend(
            [
                "",
                "## Deferred protocol surfaces",
                "",
            ]
        )
        if may_defer_until_trigger:
            for item in may_defer_until_trigger:
                lines.append(
                    f"- `{item['path']}` trigger=`{item['trigger']}` reason=`{item['reason']}`"
                )
        else:
            lines.append("- None registered.")
        lines.extend(
            [
                "",
                "## Recommended protocol slices",
                "",
            ]
        )
        if recommended_protocol_slices:
            for item in recommended_protocol_slices:
                trigger = item.get("trigger") or "always"
                lines.append(f"- `{item['slice']}` trigger=`{trigger}`")
                for path in item.get("paths") or []:
                    lines.append(f"  - `{path}`")
        else:
            lines.append("- None registered.")
        lines.extend(
            [
                "",
                "## Why this file exists",
                "",
                "- Keep research behavior governed by durable protocol artifacts instead of hidden Python defaults.",
                "- Limit Python to state materialization, audits, and explicit handler execution.",
                "",
                "## What Python still does",
                "",
            ]
        )
        for item in payload["python_runtime_scope"]:
            lines.append(f"- {item}")
        lines.extend(
            [
                "",
                "## Required read order",
                "",
            ]
        )
        for idx, item in enumerate(payload["agent_required_read_order"], start=1):
            lines.append(f"{idx}. `{item}`")
        lines.extend(
            [
                "",
                "## Decision priority",
                "",
            ]
        )
        for item in payload["priority_rules"]:
            lines.append(f"- [{item['source']}] {item['rule']}")
        lines.extend(
            [
                "",
                "## Reproducibility expectations",
                "",
            ]
        )
        expectations = payload.get("reproducibility_expectations") or ["Persist durable artifacts before claiming progress."]
        for item in expectations:
            lines.append(f"- {item}")
        lines.extend(
            [
                "",
                "## Human-readable note obligations",
                "",
            ]
        )
        notes = payload.get("note_expectations") or ["Write human-readable notes for every layer you update."]
        for item in notes:
            lines.append(f"- {item}")
        lines.extend(
            [
            "",
            "## L2 backend bridge snapshot",
            "",
        ]
        )
        backend_bridges = payload.get("backend_bridges") or []
        if backend_bridges:
            for bridge in backend_bridges:
                lines.extend(
                    [
                        f"- `{bridge['backend_id']}` title=`{bridge['title']}` type=`{bridge['backend_type']}` "
                        f"status=`{bridge['status']}` card_status=`{bridge['card_status']}` sources=`{bridge['source_count']}`",
                        f"  card_path=`{bridge['card_path'] or '(missing)'}`",
                        f"  backend_root=`{bridge['backend_root'] or '(missing)'}`",
                        f"  artifact_kinds=`{', '.join(bridge['artifact_kinds']) or '(missing)'}`",
                        f"  canonical_targets=`{', '.join(bridge['canonical_targets']) or '(missing)'}`",
                        f"  l0_registration_script=`{bridge['l0_registration_script'] or '(missing)'}`",
                    ]
                )
        else:
            lines.append("- None registered.")
        promotion_gate = payload.get("promotion_gate") or {}
        lines.extend(
            [
                "",
                "## L2 promotion gate",
                "",
                f"- Status: `{promotion_gate.get('status') or 'not_requested'}`",
                f"- Candidate id: `{promotion_gate.get('candidate_id') or '(missing)'}`",
                f"- Candidate type: `{promotion_gate.get('candidate_type') or '(missing)'}`",
                f"- Gate JSON: `{promotion_gate.get('path') or '(missing)'}`",
                f"- Gate note: `{promotion_gate.get('note_path') or '(missing)'}`",
                f"- Backend id: `{promotion_gate.get('backend_id') or '(missing)'}`",
                f"- Target backend root: `{promotion_gate.get('target_backend_root') or '(missing)'}`",
                f"- Review mode: `{promotion_gate.get('review_mode') or '(missing)'}`",
                f"- Canonical layer: `{promotion_gate.get('canonical_layer') or '(missing)'}`",
                f"- Coverage status: `{promotion_gate.get('coverage_status') or '(missing)'}`",
                f"- Consensus status: `{promotion_gate.get('consensus_status') or '(missing)'}`",
                f"- Merge outcome: `{promotion_gate.get('merge_outcome') or '(missing)'}`",
                f"- Approved by: `{promotion_gate.get('approved_by') or '(pending)'}`",
                f"- Promoted units: `{', '.join(promotion_gate.get('promoted_units') or []) or '(none)'}`",
                "",
                "## Delivery rule",
                "",
                f"- {payload['delivery_rule'] or 'Outputs must name exact artifact paths and justify the chosen layer.'}",
                "",
                "## Editable protocol surfaces",
                "",
            ]
        )
        surfaces = payload.get("editable_protocol_surfaces") or []
        if surfaces:
            for surface in surfaces:
                lines.append(f"- [{surface['surface']}] `{surface['path']}` {surface['role']}")
        else:
            lines.append("- No editable protocol surfaces are currently registered.")
        queue_surface = payload.get("action_queue_surface") or {}
        decision_surface = payload.get("decision_surface") or {}
        lines.extend(
            [
                "",
                "## Queue contract snapshot",
                "",
                f"- Queue source: `{queue_surface.get('queue_source') or '(missing)'}`",
                f"- Declared contract path: `{queue_surface.get('declared_contract_path') or '(missing)'}`",
                f"- Generated contract JSON: `{queue_surface.get('generated_contract_path') or '(missing)'}`",
                f"- Generated contract note: `{queue_surface.get('generated_contract_note_path') or '(missing)'}`",
                "",
                "## Decision surface snapshot",
                "",
                f"- Decision mode: `{decision_surface.get('decision_mode') or '(missing)'}`",
                f"- Decision source: `{decision_surface.get('decision_source') or '(missing)'}`",
                f"- Decision contract status: `{decision_surface.get('decision_contract_status') or '(missing)'}`",
                f"- Control note path: `{decision_surface.get('control_note_path') or '(missing)'}`",
                f"- Selected action: `{decision_surface.get('selected_action_id') or '(missing)'}`",
                "",
                "## Pending actions snapshot",
                "",
            ]
        )
        pending_actions = payload.get("pending_actions") or []
        if pending_actions:
            for idx, row in enumerate(pending_actions, start=1):
                lines.append(
                    f"{idx}. [{row['action_type']}] {row['summary']} "
                    f"(auto_runnable={str(row['auto_runnable']).lower()}, queue_source={row['queue_source']})"
                )
        else:
            lines.append("- No pending actions are currently registered.")
        return "\n".join(lines) + "\n"

    def _materialize_runtime_protocol_bundle(
        self,
        *,
        topic_slug: str,
        updated_by: str,
        human_request: str | None = None,
    ) -> dict[str, str]:
        runtime_root = self._ensure_runtime_root(topic_slug)
        topic_state = read_json(runtime_root / "topic_state.json") or {}
        interaction_state = read_json(runtime_root / "interaction_state.json") or {}
        promotion_gate = self._load_promotion_gate(topic_slug) or {}
        queue_rows = read_jsonl(runtime_root / "action_queue.jsonl")
        queue_surface = interaction_state.get("action_queue_surface") or {}
        decision_surface = interaction_state.get("decision_surface") or {}
        research_mode_profile = topic_state.get("research_mode_profile") or {}
        pending_actions, selected_pending_action = self._pending_action_context(
            queue_rows,
            decision_surface,
        )
        backend_bridges: list[dict[str, Any]] = []
        for row in topic_state.get("backend_bridges") or []:
            if not isinstance(row, dict):
                continue
            backend_bridges.append(
                {
                    "backend_id": str(row.get("backend_id") or "").strip() or "(missing)",
                    "title": str(row.get("title") or row.get("backend_id") or "").strip() or "(missing)",
                    "backend_type": str(row.get("backend_type") or "").strip() or "(missing)",
                    "status": str(row.get("status") or "").strip() or "(missing)",
                    "card_status": str(row.get("card_status") or "").strip() or "(missing)",
                    "card_path": str(row.get("card_path") or "").strip() or None,
                    "backend_root": str(row.get("backend_root") or "").strip() or None,
                    "artifact_kinds": self._dedupe_strings(list(row.get("artifact_kinds") or [])),
                    "canonical_targets": self._dedupe_strings(list(row.get("canonical_targets") or [])),
                    "l0_registration_script": str(row.get("l0_registration_script") or "").strip() or None,
                    "source_count": int(row.get("source_count") or 0),
                }
            )
        shell_surfaces = self.ensure_topic_shell_surfaces(
            topic_slug=topic_slug,
            updated_by=updated_by,
            human_request=human_request,
            topic_state=topic_state,
            interaction_state=interaction_state,
            promotion_gate=promotion_gate,
            queue_rows=queue_rows,
        )
        research_contract = shell_surfaces["research_question_contract"]
        validation_contract = shell_surfaces["validation_contract"]
        promotion_readiness = dict(shell_surfaces["promotion_readiness"])
        promotion_readiness["path"] = self._relativize(Path(shell_surfaces["promotion_readiness_path"]))
        open_gap_summary = dict(shell_surfaces["open_gap_summary"])
        open_gap_summary["path"] = self._relativize(Path(shell_surfaces["gap_map_path"]))
        topic_completion = dict(shell_surfaces["topic_completion"])
        topic_completion["path"] = self._relativize(Path(shell_surfaces["topic_completion_note_path"]))
        lean_bridge = dict(shell_surfaces["lean_bridge"])
        lean_bridge["path"] = self._relativize(Path(shell_surfaces["lean_bridge_note_path"]))
        active_research_contract = {
            "question_id": str(research_contract.get("question_id") or ""),
            "title": str(research_contract.get("title") or ""),
            "status": str(research_contract.get("status") or ""),
            "template_mode": str(research_contract.get("template_mode") or ""),
            "research_mode": str(research_contract.get("research_mode") or ""),
            "validation_mode": str(validation_contract.get("validation_mode") or ""),
            "target_layers": self._dedupe_strings(list(research_contract.get("target_layers") or [])),
            "question": str(research_contract.get("question") or ""),
            "path": self._relativize(Path(shell_surfaces["research_question_contract_path"])),
            "note_path": self._relativize(Path(shell_surfaces["research_question_contract_note_path"])),
        }

        runtime_protocol_note = self._relativize(runtime_root / "runtime_protocol.generated.md")
        research_guardrails_note = self._relativize(self.kernel_root / "RESEARCH_EXECUTION_GUARDRAILS.md")
        must_read_now: list[dict[str, str]] = [
            {
                "path": runtime_protocol_note,
                "reason": "Top-level execution contract for this topic. Read this file first.",
            }
        ]
        must_read_now.append(
            {
                "path": self._relativize(Path(shell_surfaces["research_question_contract_note_path"])),
                "reason": "Active research question, scope, deliverables, and anti-proxy rules for this topic.",
            }
        )
        must_read_now.append(
            {
                "path": self._relativize(Path(shell_surfaces["topic_dashboard_path"])),
                "reason": "Operator-facing topic snapshot that condenses the active question, next action, readiness, and gaps.",
            }
        )
        must_read_now.append(
            {
                "path": self._relativize(Path(shell_surfaces["topic_completion_note_path"])),
                "reason": "Topic-completion gate over regression support, follow-up return debt, and blocker honesty.",
            }
        )
        must_read_now.append(
            {
                "path": self._relativize(Path(shell_surfaces["validation_contract_note_path"])),
                "reason": "Current validation route, required checks, and failure modes for this topic.",
            }
        )
        must_read_now.append(
            {
                "path": research_guardrails_note,
                "reason": "Global research-contract, bounded-action, and anti-proxy validation guardrails for non-trivial work.",
            }
        )
        for candidate, reason in (
            (
                "agent_brief.md",
                "Stage-specific execution brief with the current bounded action and escalation cues.",
            ),
            (
                "operator_console.md",
                "Operator-visible execution state, pending actions, and current queue/decision status.",
            ),
            (
                "conformance_report.md",
                "Check whether current work is still counting as AITP before deeper execution.",
            ),
        ):
            candidate_path = runtime_root / candidate
            if candidate_path.exists():
                must_read_now.append(
                    {"path": self._relativize(candidate_path), "reason": reason}
                )

        may_defer_until_trigger: list[dict[str, str]] = []
        for candidate, trigger, reason in (
            (
                "interaction_state.json",
                "decision_override_present",
                "Only open when raw control or contract state is needed.",
            ),
            (
                "next_action_decision.md",
                "decision_override_present",
                "Open when you need the full selected-action rationale rather than the brief summary.",
            ),
            (
                "action_queue_contract.generated.md",
                "decision_override_present",
                "Open when queue-contract details matter more than the brief queue snapshot.",
            ),
            (
                "promotion_gate.md",
                "promotion_intent",
                "Only mandatory when current work could create, approve, or execute writeback.",
            ),
            (
                Path(shell_surfaces["promotion_readiness_path"]).name,
                "promotion_intent",
                "Promotion readiness details become mandatory when writeback or gate routing is active.",
            ),
            (
                Path(shell_surfaces["gap_map_path"]).name,
                "capability_gap_blocker",
                "Gap-map details become mandatory when the topic must return to L0 or resolve explicit blockers.",
            ),
            (
                Path(shell_surfaces["lean_bridge_note_path"]).name,
                "proof_completion_review",
                "Lean-bridge packets become mandatory when proof-heavy work is being decomposed into formal obligations.",
            ),
            (
                Path(shell_surfaces["followup_reintegration_note_path"]).name,
                "non_trivial_consultation",
                "Reintegration receipts matter when child follow-up topics are returning evidence to the parent topic.",
            ),
            (
                Path(shell_surfaces["followup_gap_writeback_note_path"]).name,
                "capability_gap_blocker",
                "Open this when unresolved child follow-up returns have written new parent-side gap debt.",
            ),
        ):
            candidate_path = runtime_root / candidate
            if candidate_path.exists():
                may_defer_until_trigger.append(
                    {
                        "path": self._relativize(candidate_path),
                        "trigger": trigger,
                        "reason": reason,
                    }
                )

        consultation_index_path = str((topic_state.get("pointers") or {}).get("consultation_index_path") or "")
        closed_loop_surface = interaction_state.get("closed_loop") or {}
        latest_run_id = str(topic_state.get("latest_run_id") or "").strip()
        selected_action_handler_args = (selected_pending_action or {}).get("handler_args") or {}
        active_run_id = str(selected_action_handler_args.get("run_id") or latest_run_id or "").strip()
        active_candidate_id = str(
            selected_action_handler_args.get("candidate_id") or promotion_gate.get("candidate_id") or ""
        ).strip()
        active_candidate_type = str(
            selected_action_handler_args.get("candidate_type") or promotion_gate.get("candidate_type") or ""
        ).strip()
        theory_packet_reads: list[str] = []
        if active_run_id and active_candidate_id:
            theory_packet_paths = self._theory_packet_paths(topic_slug, active_run_id, active_candidate_id)
            for key in (
                "structure_map",
                "coverage_ledger",
                "notation_table",
                "derivation_graph",
                "agent_consensus",
            ):
                path = theory_packet_paths[key]
                if path.exists():
                    theory_packet_reads.append(self._relativize(path))
        verification_route_reads = [
            path
            for path in (
                str(closed_loop_surface.get("selected_route_path") or ""),
                str(closed_loop_surface.get("execution_task_path") or ""),
                str(closed_loop_surface.get("returned_result_path") or ""),
            )
            if path
        ]
        if consultation_index_path:
            may_defer_until_trigger.append(
                {
                    "path": consultation_index_path,
                    "trigger": "non_trivial_consultation",
                    "reason": "Consultation details are only mandatory when L2 memory materially changes the current work.",
                }
            )
        capability_report_path = runtime_root / "capability_report.md"
        if capability_report_path.exists():
            may_defer_until_trigger.append(
                {
                    "path": self._relativize(capability_report_path),
                    "trigger": "capability_gap_blocker",
                    "reason": "Capability details are only mandatory when a missing workflow or backend is the honest blocker.",
                }
            )
        for path in theory_packet_reads:
            may_defer_until_trigger.append(
                {
                    "path": path,
                    "trigger": "proof_completion_review",
                    "reason": "Theory-packet coverage and derivation surfaces only become mandatory when proof completion is the current concern.",
                }
            )
        for path in verification_route_reads:
            may_defer_until_trigger.append(
                {
                    "path": path,
                    "trigger": "verification_route_selection",
                    "reason": "Closed-loop route and execution details only become mandatory when validation-route selection or execution routing is the current concern.",
                }
            )

        read_order: list[str] = [item["path"] for item in must_read_now]
        if not read_order:
            read_order.append(self._relativize(runtime_root / "topic_state.json"))

        selected_action_summary = str((selected_pending_action or {}).get("summary") or "").strip()
        selected_action_type = str((selected_pending_action or {}).get("action_type") or "").strip()
        selected_action_id = str((selected_pending_action or {}).get("action_id") or "").strip()
        selected_action_auto_runnable = bool((selected_pending_action or {}).get("auto_runnable"))
        selected_action_label = selected_action_summary or (
            f"{selected_action_type} ({selected_action_id})" if selected_action_type else ""
        )
        immediate_allowed_work = []
        if selected_action_label:
            immediate_allowed_work.append(
                f"Continue bounded `{topic_state.get('resume_stage') or '(missing)'}` work on `{selected_action_label}`."
            )
        else:
            immediate_allowed_work.append(
                f"Resume bounded `{topic_state.get('resume_stage') or '(missing)'}` work using the declared decision surface."
            )
        immediate_allowed_work.append(
            "Prefer declared contracts and durable runtime artifacts over ad hoc browsing or memory-only routing."
        )
        if any(str(row.get("action_type") or "") == "skill_discovery" for row in pending_actions):
            immediate_allowed_work.append(
                "Run controlled skill discovery only if the capability gap is the honest blocker for the selected action."
            )
        if not selected_action_auto_runnable and selected_action_label:
            immediate_allowed_work.append(
                "Treat the currently selected action as manual follow-up unless a returned execution artifact proves otherwise."
            )

        immediate_blocked_work = [
            "Do not promote or auto-promote material into Layer 2 unless the promotion trigger fires and the gate artifacts allow it.",
            "Do not bypass conformance, declared control notes, or decision contracts with heuristic queue guesses.",
            "Do not treat consultation as promotion or claim heavy execution happened without the corresponding returned result artifacts.",
            "Do not substitute polished prose, memory agreement, or missing execution evidence for the declared acceptance checks.",
        ]

        control_note_status = str(decision_surface.get("control_note_status") or "missing")
        decision_contract_status = str(decision_surface.get("decision_contract_status") or "missing")
        promotion_status = str(promotion_gate.get("status") or "not_requested")
        capability_gap_active = any(
            str(row.get("action_type") or "") == "skill_discovery" for row in pending_actions
        )
        contradiction_hint = any(
            needle in selected_action_label.lower()
            for needle in ("contradiction", "conflict", "regime mismatch")
        )
        proof_hint = bool(theory_packet_reads) and (
            active_candidate_type
            in {
                "equation_card",
                "theorem_card",
                "proof_fragment",
                "derivation_step",
                "derivation_object",
            }
            or any(
                needle in selected_action_label.lower()
                for needle in ("proof", "derivation", "theorem", "coverage")
            )
        )
        consultation_hint = any(
            needle in selected_action_label.lower()
            for needle in ("consult", "memory", "terminology", "candidate shape")
        )
        verification_route_hint = bool(verification_route_reads) and (
            selected_action_type in {"select_validation_route", "materialize_execution_task", "dispatch_execution_task"}
            or any(
                needle in selected_action_label.lower()
                for needle in ("validation route", "verification route", "execution task", "selected route")
            )
        )
        trust_hint = any(
            needle in selected_action_label.lower()
            for needle in ("trust", "baseline", "atomize")
        )
        promotion_hint = (
            promotion_status in {"requested", "approved"}
            or any(
                needle in selected_action_label.lower()
                for needle in ("promot", "writeback", "candidate")
            )
        )
        escalation_triggers = [
            {
                "trigger": "decision_override_present",
                "active": control_note_status != "missing" or decision_contract_status != "missing",
                "condition": "A control note or decision contract overrides heuristic queue selection.",
                "required_reads": [
                    path
                    for path in (
                        str(decision_surface.get("control_note_path") or ""),
                        str(decision_surface.get("decision_contract_path") or ""),
                        str(decision_surface.get("next_action_decision_note_path") or ""),
                        str(queue_surface.get("generated_contract_note_path") or ""),
                    )
                    if path
                ],
            },
            {
                "trigger": "promotion_intent",
                "active": promotion_hint,
                "condition": "The current work could create, approve, or execute Layer 2 or Layer 2_auto writeback.",
                "required_reads": [
                    path
                    for path in (
                        str(promotion_gate.get("path") or ""),
                        str(promotion_gate.get("note_path") or ""),
                    )
                    if path
                ],
            },
            {
                "trigger": "non_trivial_consultation",
                "active": consultation_hint,
                "condition": "L2 consultation materially changes terminology, candidate shape, validation route, or writeback intent.",
                "required_reads": [
                    path
                    for path in (
                        self._relativize(self.kernel_root / "L2_CONSULTATION_PROTOCOL.md"),
                        consultation_index_path,
                    )
                    if path
                ],
            },
            {
                "trigger": "capability_gap_blocker",
                "active": capability_gap_active,
                "condition": "A missing workflow or backend is the honest blocker for the selected action.",
                "required_reads": [
                    path
                    for path in (
                        self._relativize(self._research_root() / "adapters" / "openclaw" / "SKILL_ADAPTATION_PROTOCOL.md"),
                        self._relativize(capability_report_path) if capability_report_path.exists() else "",
                    )
                    if path
                ],
            },
            {
                "trigger": "proof_completion_review",
                "active": proof_hint,
                "condition": "Proof-heavy or derivation-heavy work must open the current theory-packet coverage and derivation surfaces before claiming completion.",
                "required_reads": theory_packet_reads,
            },
            {
                "trigger": "verification_route_selection",
                "active": verification_route_hint,
                "condition": "Closed-loop validation work must open the selected route and execution handoff surfaces before claiming execution or adjudication.",
                "required_reads": verification_route_reads,
            },
            {
                "trigger": "trust_missing",
                "active": trust_hint,
                "condition": "The current work wants to reuse an operation or method whose trust gate may not be satisfied.",
                "required_reads": [],
            },
            {
                "trigger": "contradiction_detected",
                "active": contradiction_hint,
                "condition": "Validation or family fusion exposes an unresolved contradiction or regime conflict.",
                "required_reads": [
                    path
                    for path in (
                        str((topic_state.get("pointers") or {}).get("promotion_decision_path") or ""),
                        str((topic_state.get("pointers") or {}).get("feedback_status_path") or ""),
                    )
                    if path
                ],
            },
        ]

        recommended_protocol_slices = [
            {
                "slice": "current_execution_lane",
                "trigger": "",
                "paths": [item["path"] for item in must_read_now],
            },
            {
                "slice": "decision_and_queue_details",
                "trigger": "decision_override_present",
                "paths": [
                    path
                    for path in (
                        str(decision_surface.get("next_action_decision_note_path") or ""),
                        str(queue_surface.get("generated_contract_note_path") or ""),
                        str(queue_surface.get("declared_contract_path") or ""),
                    )
                    if path
                ],
            },
            {
                "slice": "consultation_memory",
                "trigger": "non_trivial_consultation",
                "paths": [
                    path
                    for path in (
                        self._relativize(self.kernel_root / "L2_CONSULTATION_PROTOCOL.md"),
                        consultation_index_path,
                    )
                    if path
                ],
            },
            {
                "slice": "promotion_and_writeback",
                "trigger": "promotion_intent",
                "paths": [
                    path
                    for path in (
                        str(promotion_gate.get("path") or ""),
                        str(promotion_gate.get("note_path") or ""),
                    )
                    if path
                ],
            },
            {
                "slice": "capability_and_skill_discovery",
                "trigger": "capability_gap_blocker",
                "paths": [
                    path
                    for path in (
                        self._relativize(self._research_root() / "adapters" / "openclaw" / "SKILL_ADAPTATION_PROTOCOL.md"),
                        self._relativize(capability_report_path) if capability_report_path.exists() else "",
                    )
                    if path
                ],
            },
            {
                "slice": "proof_completion_and_coverage",
                "trigger": "proof_completion_review",
                "paths": theory_packet_reads,
            },
            {
                "slice": "verification_route_selection",
                "trigger": "verification_route_selection",
                "paths": verification_route_reads,
            },
        ]

        active_hard_constraints = [
            "Do not let progressive disclosure hide layer semantics, consultation obligations, trust gates, promotion gates, or conformance failures.",
            "Do not let the active research contract drift silently in scope, observables, deliverables, or acceptance tests.",
            "Do not treat heuristic queue rows as higher priority than declared control notes or decision contracts.",
            "Do not perform Layer 2 or Layer 2_auto writeback unless the corresponding gate artifacts say it is allowed.",
            "Do not treat proxy-success signals as validation when the declared execution or proof evidence is still missing.",
            "If definitions, cited derivations, or prior-work comparisons are missing, return to L0 and persist the recovery artifacts before continuing.",
            "When a named trigger becomes active, read its mandatory deeper surfaces before continuing execution.",
        ]

        editable_surfaces: list[dict[str, str]] = []
        for surface in interaction_state.get("human_edit_surfaces") or []:
            path = str(surface.get("path") or "").strip()
            if not path or (path.startswith("(") and path.endswith(")")) or re.search(r"/\([^)]*missing[^)]*\)$", path):
                continue
            editable_surfaces.append(
                {
                    "surface": str(surface.get("surface") or "unknown"),
                    "path": path,
                    "role": str(surface.get("role") or "").strip(),
                }
            )
        editable_surfaces.extend(
            [
                {
                    "surface": "research_question_contract",
                    "path": self._relativize(Path(shell_surfaces["research_question_contract_note_path"])),
                    "role": "Edit the active question, scope, deliverables, and anti-proxy constraints.",
                },
                {
                    "surface": "validation_contract",
                    "path": self._relativize(Path(shell_surfaces["validation_contract_note_path"])),
                    "role": "Edit the active validation route, required checks, and failure modes.",
                },
                {
                    "surface": "topic_dashboard",
                    "path": self._relativize(Path(shell_surfaces["topic_dashboard_path"])),
                    "role": "Human-readable topic summary for operator review and correction.",
                },
                {
                    "surface": "promotion_readiness",
                    "path": self._relativize(Path(shell_surfaces["promotion_readiness_path"])),
                    "role": "Review promotion blockers, ready candidates, and gate state.",
                },
                {
                    "surface": "gap_map",
                    "path": self._relativize(Path(shell_surfaces["gap_map_path"])),
                    "role": "Review whether the topic must return to L0 or keep bounded gap packets open.",
                },
                {
                    "surface": "topic_completion",
                    "path": self._relativize(Path(shell_surfaces["topic_completion_note_path"])),
                    "role": "Review topic-completion status against regression support and follow-up return debt.",
                },
                {
                    "surface": "lean_bridge",
                    "path": self._relativize(Path(shell_surfaces["lean_bridge_note_path"])),
                    "role": "Review Lean-ready packets, declaration skeletons, and outstanding proof obligations.",
                },
                {
                    "surface": "followup_gap_writeback",
                    "path": self._relativize(Path(shell_surfaces["followup_gap_writeback_note_path"])),
                    "role": "Review unresolved child follow-up returns that were written back into the parent gap surface.",
                },
            ]
        )
        deduped_surfaces: list[dict[str, str]] = []
        seen_surface_paths: set[str] = set()
        for surface in editable_surfaces:
            key = f"{surface['surface']}::{surface['path']}"
            if key in seen_surface_paths:
                continue
            seen_surface_paths.add(key)
            deduped_surfaces.append(surface)
        editable_surfaces = deduped_surfaces

        payload = {
            "$schema": "https://aitp.local/schemas/progressive-disclosure-runtime-bundle.schema.json",
            "bundle_kind": "progressive_disclosure_runtime_bundle",
            "protocol_version": 1,
            "topic_slug": topic_slug,
            "updated_at": now_iso(),
            "updated_by": updated_by,
            "human_request": human_request or str(interaction_state.get("human_request") or ""),
            "resume_stage": topic_state.get("resume_stage"),
            "last_materialized_stage": topic_state.get("last_materialized_stage"),
            "research_mode": topic_state.get("research_mode") or active_research_contract.get("research_mode"),
            "active_research_contract": active_research_contract,
            "promotion_readiness": promotion_readiness,
            "open_gap_summary": open_gap_summary,
            "topic_completion": topic_completion,
            "lean_bridge": lean_bridge,
            "minimal_execution_brief": {
                "current_stage": topic_state.get("resume_stage"),
                "selected_action_id": str((selected_pending_action or {}).get("action_id") or ""),
                "selected_action_type": selected_action_type,
                "selected_action_summary": selected_action_label,
                "decision_source": decision_surface.get("decision_source"),
                "queue_source": queue_surface.get("queue_source")
                or ("declared_contract" if queue_surface.get("declared_contract_path") else "heuristic"),
                "open_next": must_read_now[1]["path"] if len(must_read_now) > 1 else runtime_protocol_note,
                "immediate_allowed_work": immediate_allowed_work,
                "immediate_blocked_work": immediate_blocked_work,
            },
            "must_read_now": must_read_now,
            "may_defer_until_trigger": may_defer_until_trigger,
            "escalation_triggers": escalation_triggers,
            "active_hard_constraints": active_hard_constraints,
            "recommended_protocol_slices": recommended_protocol_slices,
            "python_runtime_scope": [
                "Materialize durable runtime state and protocol snapshots on disk.",
                "Run conformance, capability, and trust audits against persisted artifacts.",
                "Execute explicit auto-runnable handlers declared in runtime state.",
                "Block Layer 2 promotion until a durable human approval artifact exists on disk.",
            ],
            "agent_required_read_order": read_order,
            "priority_rules": [
                {
                    "source": "control_note_or_decision_contract",
                    "rule": "If a control note or decision contract exists, it overrides heuristic next-step selection.",
                },
                {
                    "source": "declared_action_contract",
                    "rule": "Prefer durable `next_actions.contract.json` over queue synthesis from prose or memory.",
                },
                {
                    "source": "generated_queue_contract",
                    "rule": "Treat generated queue-contract snapshots as editable protocol surfaces, not hidden implementation detail.",
                },
                {
                    "source": "heuristic_queue",
                    "rule": "Use heuristic queue rows only as fallback guidance when no durable contract is present.",
                },
            ],
            "reproducibility_expectations": research_mode_profile.get("reproducibility_expectations") or [],
            "note_expectations": research_mode_profile.get("note_expectations") or [],
            "backend_bridges": backend_bridges,
            "promotion_gate": {
                "status": str(promotion_gate.get("status") or "not_requested"),
                "candidate_id": str(promotion_gate.get("candidate_id") or ""),
                "candidate_type": str(promotion_gate.get("candidate_type") or ""),
                "path": self._relativize(self._promotion_gate_paths(topic_slug)["json"])
                if self._promotion_gate_paths(topic_slug)["json"].exists()
                else None,
                "note_path": self._relativize(self._promotion_gate_paths(topic_slug)["note"])
                if self._promotion_gate_paths(topic_slug)["note"].exists()
                else None,
                "backend_id": str(promotion_gate.get("backend_id") or ""),
                "target_backend_root": str(promotion_gate.get("target_backend_root") or ""),
                "review_mode": str(promotion_gate.get("review_mode") or "human"),
                "canonical_layer": str(promotion_gate.get("canonical_layer") or "L2"),
                "coverage_status": str(promotion_gate.get("coverage_status") or "not_audited"),
                "consensus_status": str(promotion_gate.get("consensus_status") or "not_requested"),
                "merge_outcome": str(promotion_gate.get("merge_outcome") or "pending"),
                "approved_by": str(promotion_gate.get("approved_by") or ""),
                "promoted_units": self._dedupe_strings(list(promotion_gate.get("promoted_units") or [])),
            },
            "delivery_rule": str((interaction_state.get("delivery_contract") or {}).get("rule") or ""),
            "editable_protocol_surfaces": editable_surfaces,
            "action_queue_surface": {
                "queue_source": queue_surface.get("queue_source")
                or ("declared_contract" if queue_surface.get("declared_contract_path") else "heuristic"),
                "declared_contract_path": queue_surface.get("declared_contract_path"),
                "generated_contract_path": queue_surface.get("generated_contract_path"),
                "generated_contract_note_path": queue_surface.get("generated_contract_note_path"),
            },
            "decision_surface": {
                "decision_mode": decision_surface.get("decision_mode"),
                "decision_source": decision_surface.get("decision_source"),
                "decision_contract_status": decision_surface.get("decision_contract_status"),
                "control_note_path": decision_surface.get("control_note_path"),
                "selected_action_id": decision_surface.get("selected_action_id"),
            },
            "pending_actions": [
                {
                    "action_id": str(row.get("action_id") or ""),
                    "action_type": str(row.get("action_type") or ""),
                    "summary": str(row.get("summary") or ""),
                    "auto_runnable": bool(row.get("auto_runnable")),
                    "queue_source": str(row.get("queue_source") or queue_surface.get("queue_source") or "heuristic"),
                }
                for row in queue_rows
                if str(row.get("status") or "pending") == "pending"
            ],
        }
        protocol_paths = self._runtime_protocol_paths(topic_slug)
        write_json(protocol_paths["json"], payload)
        write_text(protocol_paths["note"], self._runtime_protocol_markdown(payload))
        return {
            "runtime_protocol_path": str(protocol_paths["json"]),
            "runtime_protocol_note_path": str(protocol_paths["note"]),
        }

    def _discover_skills(
        self,
        *,
        topic_slug: str,
        queries: list[str],
        updated_by: str,
        agent_target: str = "openclaw",
    ) -> dict[str, Any]:
        script_path = self._research_root() / "adapters" / "openclaw" / "scripts" / "discover_external_skills.py"
        if not script_path.exists():
            raise FileNotFoundError(f"Skill discovery script missing: {script_path}")
        output_dir = self._runtime_root(topic_slug)
        command = [
            "python3",
            str(script_path),
            "--topic-slug",
            topic_slug,
            "--updated-by",
            updated_by,
            "--agent-target",
            agent_target,
            "--output-dir",
            str(output_dir),
        ]
        for query in queries:
            command.extend(["--query", query])
        completed = self._run(command)
        return {
            "command": command,
            "stdout": completed.stdout.strip(),
            "skill_discovery_path": str(output_dir / "skill_discovery.json"),
            "skill_recommendations_path": str(output_dir / "skill_recommendations.md"),
        }

    def _resolve_runtime_handler_path(self, handler: str | None, default_relative_path: str) -> Path:
        if handler and str(handler).strip():
            candidate = Path(str(handler).strip()).expanduser()
            if not candidate.is_absolute():
                candidate = self.kernel_root / candidate
        else:
            candidate = self.kernel_root / default_relative_path
        resolved = candidate.resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"Runtime handler missing: {resolved}")
        return resolved

    def _parse_json_stdout(self, stdout: str) -> dict[str, Any]:
        text = stdout.strip()
        if not text:
            return {}
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return {"stdout": text}
        return payload if isinstance(payload, dict) else {"payload": payload}

    def _run_literature_followup(
        self,
        *,
        topic_slug: str,
        row: dict[str, Any],
        updated_by: str,
    ) -> dict[str, Any]:
        handler_args = row.get("handler_args") or {}
        resolved_run_id = str(handler_args.get("run_id") or self._resolve_run_id(topic_slug, None) or "").strip()
        if not resolved_run_id:
            raise RuntimeError("No run_id provided for literature_followup_search.")

        query = str(handler_args.get("query") or "").strip()
        if not query:
            raise RuntimeError("No query provided for literature_followup_search.")

        handler_path = self._resolve_runtime_handler_path(
            row.get("handler"),
            "runtime/scripts/run_literature_followup.py",
        )
        command = [
            "python3",
            str(handler_path),
            "--topic-slug",
            topic_slug,
            "--run-id",
            resolved_run_id,
            "--query",
            query,
            "--updated-by",
            updated_by,
        ]
        optional_args = [
            ("priority", "--priority"),
            ("target_source_type", "--target-source-type"),
            ("max_results", "--max-results"),
        ]
        for key, flag in optional_args:
            value = handler_args.get(key)
            if value is None:
                continue
            string_value = str(value).strip()
            if not string_value:
                continue
            command.extend([flag, string_value])

        completed = self._run(command)
        payload = self._parse_json_stdout(completed.stdout)
        result = {
            "command": command,
            "stdout": completed.stdout.strip(),
            "receipts_path": str(
                self._validation_run_root(topic_slug, resolved_run_id) / "literature_followup_receipts.jsonl"
            ),
            "receipt": payload,
        }
        if completed.stderr.strip():
            result["warning"] = completed.stderr.strip()
        return result

    def _run_generic_auto_handler(
        self,
        *,
        topic_slug: str,
        row: dict[str, Any],
        updated_by: str,
    ) -> dict[str, Any]:
        raw_handler = str(row.get("handler") or "").strip()
        if not raw_handler:
            raise RuntimeError(f"No handler is configured for auto action {row.get('action_id')}.")
        handler_path = Path(raw_handler).expanduser()
        if not handler_path.is_absolute():
            handler_path = self.kernel_root / handler_path
        handler_path = handler_path.resolve()
        if not handler_path.exists():
            raise FileNotFoundError(f"Runtime handler missing: {handler_path}")

        handler_args = dict(row.get("handler_args") or {})
        handler_args.setdefault("topic_slug", topic_slug)
        handler_args.setdefault("updated_by", updated_by)
        command = ["python3", str(handler_path)]
        for key, value in handler_args.items():
            if value is None:
                continue
            flag = f"--{str(key).replace('_', '-')}"
            if isinstance(value, bool):
                if value:
                    command.append(flag)
                continue
            if isinstance(value, list):
                for item in value:
                    command.extend([flag, str(item)])
                continue
            if isinstance(value, dict):
                command.extend([flag, json.dumps(value, ensure_ascii=True, sort_keys=True)])
                continue
            command.extend([flag, str(value)])

        completed = self._run(command)
        result = {
            "command": command,
            "stdout": completed.stdout.strip(),
            "payload": self._parse_json_stdout(completed.stdout),
            "handler_path": str(handler_path),
        }
        if completed.stderr.strip():
            result["warning"] = completed.stderr.strip()
        return result

    def apply_candidate_split_contract(
        self,
        *,
        topic_slug: str,
        run_id: str | None = None,
        updated_by: str = "aitp-cli",
    ) -> dict[str, Any]:
        resolved_run_id = self._resolve_run_id(topic_slug, run_id)
        if not resolved_run_id:
            raise FileNotFoundError(f"Unable to resolve a feedback run for topic {topic_slug}")
        contract_path = self._candidate_split_contract_path(topic_slug, resolved_run_id)
        contract_payload = read_json(contract_path)
        if contract_payload is None:
            raise FileNotFoundError(f"Candidate split contract missing: {contract_path}")

        ledger_path = self._candidate_ledger_path(topic_slug, resolved_run_id)
        ledger_rows = read_jsonl(ledger_path)
        ledger_index = {
            str(row.get("candidate_id") or "").strip(): row
            for row in ledger_rows
            if str(row.get("candidate_id") or "").strip()
        }
        receipts_path = self._candidate_split_receipts_path(topic_slug, resolved_run_id)
        receipt_rows = read_jsonl(receipts_path)
        deferred_buffer = self._load_deferred_buffer(topic_slug)
        deferred_index = {
            str(entry.get("entry_id") or "").strip(): entry
            for entry in deferred_buffer.get("entries") or []
            if str(entry.get("entry_id") or "").strip()
        }

        applied_source_candidates: list[str] = []
        child_candidate_ids: list[str] = []
        buffered_entry_ids: list[str] = []
        skipped_sources: list[str] = []

        for split_payload in contract_payload.get("splits") or []:
            source_candidate_id = str(split_payload.get("source_candidate_id") or "").strip()
            if not source_candidate_id:
                continue
            fingerprint = self._fingerprint_payload(split_payload)
            if any(
                str(row.get("source_candidate_id") or "") == source_candidate_id
                and str(row.get("fingerprint") or "") == fingerprint
                for row in receipt_rows
            ):
                skipped_sources.append(source_candidate_id)
                continue

            source_candidate = ledger_index.get(source_candidate_id)
            if source_candidate is None:
                raise FileNotFoundError(
                    f"Split contract references missing source candidate {source_candidate_id} in {ledger_path}"
                )

            split_child_ids: list[str] = []
            split_buffer_ids: list[str] = []
            for child_payload in split_payload.get("child_candidates") or []:
                child_candidate_id = str(child_payload.get("candidate_id") or "").strip()
                if not child_candidate_id:
                    continue
                existing_child = ledger_index.get(child_candidate_id) or {}
                child_row = {
                    "candidate_id": child_candidate_id,
                    "candidate_type": str(child_payload.get("candidate_type") or existing_child.get("candidate_type") or source_candidate.get("candidate_type") or ""),
                    "title": str(child_payload.get("title") or existing_child.get("title") or child_candidate_id),
                    "summary": str(child_payload.get("summary") or existing_child.get("summary") or ""),
                    "topic_slug": topic_slug,
                    "run_id": resolved_run_id,
                    "origin_refs": list(child_payload.get("origin_refs") or existing_child.get("origin_refs") or source_candidate.get("origin_refs") or []),
                    "question": str(child_payload.get("question") or existing_child.get("question") or source_candidate.get("question") or ""),
                    "assumptions": list(child_payload.get("assumptions") or existing_child.get("assumptions") or source_candidate.get("assumptions") or []),
                    "proposed_validation_route": str(child_payload.get("proposed_validation_route") or existing_child.get("proposed_validation_route") or source_candidate.get("proposed_validation_route") or ""),
                    "intended_l2_targets": list(child_payload.get("intended_l2_targets") or existing_child.get("intended_l2_targets") or []),
                    "status": str(child_payload.get("status") or existing_child.get("status") or "ready_for_validation"),
                    "split_parent_id": source_candidate_id,
                }
                if str(existing_child.get("status") or "") in {"promoted", "auto_promoted"}:
                    child_row = existing_child
                else:
                    self._replace_candidate_row(topic_slug, resolved_run_id, child_candidate_id, child_row)
                    ledger_index[child_candidate_id] = child_row
                split_child_ids.append(child_candidate_id)
                child_candidate_ids.append(child_candidate_id)

            for deferred_payload in split_payload.get("deferred_fragments") or []:
                entry_id = str(deferred_payload.get("entry_id") or "").strip()
                if not entry_id:
                    continue
                existing_entry = deferred_index.get(entry_id) or {}
                entry_row = {
                    "entry_id": entry_id,
                    "source_candidate_id": source_candidate_id,
                    "title": str(deferred_payload.get("title") or existing_entry.get("title") or entry_id),
                    "summary": str(deferred_payload.get("summary") or existing_entry.get("summary") or ""),
                    "reason": str(deferred_payload.get("reason") or existing_entry.get("reason") or ""),
                    "status": str(existing_entry.get("status") or "buffered"),
                    "required_l2_types": self._dedupe_strings(list(deferred_payload.get("required_l2_types") or existing_entry.get("required_l2_types") or [])),
                    "reactivation_conditions": deferred_payload.get("reactivation_conditions") or existing_entry.get("reactivation_conditions") or {},
                    "reactivation_candidate": deferred_payload.get("reactivation_candidate") or existing_entry.get("reactivation_candidate") or {},
                    "activated_candidate_id": str(existing_entry.get("activated_candidate_id") or ""),
                    "activated_at": str(existing_entry.get("activated_at") or ""),
                    "notes": str(deferred_payload.get("notes") or existing_entry.get("notes") or ""),
                }
                deferred_index[entry_id] = entry_row
                split_buffer_ids.append(entry_id)
                buffered_entry_ids.append(entry_id)

            updated_source = dict(source_candidate)
            updated_source["status"] = "split_into_children" if split_child_ids else "deferred_buffered"
            updated_source["split_child_ids"] = self._dedupe_strings(
                list(updated_source.get("split_child_ids") or []) + split_child_ids
            )
            updated_source["buffer_entry_ids"] = self._dedupe_strings(
                list(updated_source.get("buffer_entry_ids") or []) + split_buffer_ids
            )
            self._replace_candidate_row(topic_slug, resolved_run_id, source_candidate_id, updated_source)
            ledger_index[source_candidate_id] = updated_source
            applied_source_candidates.append(source_candidate_id)

            receipt_rows.append(
                {
                    "event": "applied",
                    "source_candidate_id": source_candidate_id,
                    "fingerprint": fingerprint,
                    "child_candidate_ids": split_child_ids,
                    "buffer_entry_ids": split_buffer_ids,
                    "updated_at": now_iso(),
                    "updated_by": updated_by,
                    "reason": str(split_payload.get("reason") or ""),
                }
            )

        deferred_payload = {
            "buffer_version": 1,
            "topic_slug": topic_slug,
            "updated_at": now_iso(),
            "updated_by": updated_by,
            "entries": list(deferred_index.values()),
        }
        buffer_paths = self._write_deferred_buffer(topic_slug, deferred_payload)
        write_jsonl(receipts_path, receipt_rows)
        return {
            "topic_slug": topic_slug,
            "run_id": resolved_run_id,
            "contract_path": str(contract_path),
            "candidate_ledger_path": str(ledger_path),
            "candidate_split_receipts_path": str(receipts_path),
            "applied_source_candidates": applied_source_candidates,
            "child_candidate_ids": child_candidate_ids,
            "buffered_entry_ids": buffered_entry_ids,
            "skipped_source_candidates": skipped_sources,
            **buffer_paths,
        }

    def reactivate_deferred_candidates(
        self,
        *,
        topic_slug: str,
        run_id: str | None = None,
        entry_id: str | None = None,
        updated_by: str = "aitp-cli",
    ) -> dict[str, Any]:
        resolved_run_id = self._resolve_run_id(topic_slug, run_id)
        if not resolved_run_id:
            raise FileNotFoundError(f"Unable to resolve a feedback run for topic {topic_slug}")

        deferred_buffer = self._load_deferred_buffer(topic_slug)
        entries = list(deferred_buffer.get("entries") or [])
        source_ids, source_text, child_topics = self._reactivation_context(topic_slug)
        reactivated_candidate_ids: list[str] = []
        reactivated_entry_ids: list[str] = []

        for row in entries:
            current_entry_id = str(row.get("entry_id") or "").strip()
            if not current_entry_id:
                continue
            if entry_id and current_entry_id != entry_id:
                continue
            if str(row.get("status") or "") != "buffered":
                continue
            if not self._buffer_entry_ready_for_reactivation(
                row,
                source_ids=source_ids,
                source_text=source_text,
                child_topics=child_topics,
            ):
                continue
            candidate_payload = row.get("reactivation_candidate") or {}
            candidate_id = str(candidate_payload.get("candidate_id") or "").strip()
            if not candidate_id:
                continue
            child_row = {
                "candidate_id": candidate_id,
                "candidate_type": str(candidate_payload.get("candidate_type") or ""),
                "title": str(candidate_payload.get("title") or candidate_id),
                "summary": str(candidate_payload.get("summary") or ""),
                "topic_slug": topic_slug,
                "run_id": resolved_run_id,
                "origin_refs": list(candidate_payload.get("origin_refs") or []),
                "question": str(candidate_payload.get("question") or ""),
                "assumptions": list(candidate_payload.get("assumptions") or []),
                "proposed_validation_route": str(candidate_payload.get("proposed_validation_route") or ""),
                "intended_l2_targets": list(candidate_payload.get("intended_l2_targets") or []),
                "status": str(candidate_payload.get("status") or "reactivated"),
                "reactivated_from": current_entry_id,
            }
            self._replace_candidate_row(topic_slug, resolved_run_id, candidate_id, child_row)
            row["status"] = "reactivated"
            row["activated_candidate_id"] = candidate_id
            row["activated_at"] = now_iso()
            reactivated_candidate_ids.append(candidate_id)
            reactivated_entry_ids.append(current_entry_id)

        deferred_buffer["updated_at"] = now_iso()
        deferred_buffer["updated_by"] = updated_by
        deferred_buffer["entries"] = entries
        buffer_paths = self._write_deferred_buffer(topic_slug, deferred_buffer)
        return {
            "topic_slug": topic_slug,
            "run_id": resolved_run_id,
            "reactivated_entry_ids": reactivated_entry_ids,
            "reactivated_candidate_ids": reactivated_candidate_ids,
            **buffer_paths,
        }

    def spawn_followup_subtopics(
        self,
        *,
        topic_slug: str,
        run_id: str | None = None,
        query: str | None = None,
        receipt_id: str | None = None,
        updated_by: str = "aitp-cli",
    ) -> dict[str, Any]:
        resolved_run_id = self._resolve_run_id(topic_slug, run_id)
        if not resolved_run_id:
            raise FileNotFoundError(f"Unable to resolve a validation run for topic {topic_slug}")
        policy = self._load_runtime_policy().get("followup_subtopic_policy") or {}
        allowed_source_types = {
            str(value).strip()
            for value in (policy.get("spawn_target_source_types") or [])
            if str(value).strip()
        }
        max_subtopics = int(policy.get("max_subtopics_per_receipt") or 2)
        bounded_gap_required = bool(policy.get("bounded_gap_required"))
        statement_template = str(policy.get("statement_template") or "")
        human_request_template = str(policy.get("human_request_template") or "")
        expected_return_route = str(policy.get("expected_return_route") or "L0->L1->L3->L4->L2")
        acceptable_return_shapes = self._dedupe_strings(
            list(policy.get("acceptable_return_shapes") or ["recovered_units", "resolved_gap_update", "still_unresolved_packet"])
        )
        required_output_artifacts = self._dedupe_strings(
            list(policy.get("required_output_artifacts") or ["candidate_ledger_or_recovered_units", "gap_or_followup_writeback", "reintegration_summary"])
        )
        unresolved_return_statuses = self._dedupe_strings(
            list(policy.get("unresolved_return_statuses") or ["pending_reentry", "returned_with_gap", "returned_unresolved"])
        )
        reintegration_requirements = policy.get("reintegration_requirements") or {
            "must_write_back_parent_gaps": True,
            "must_update_reentry_targets": True,
            "must_not_patch_parent_directly": True,
            "requires_child_topic_summary": True,
        }

        receipts_path = self._validation_run_root(topic_slug, resolved_run_id) / "literature_followup_receipts.jsonl"
        receipt_rows = read_jsonl(receipts_path)
        followup_rows = self._load_followup_subtopic_rows(topic_slug)
        existing_keys = {
            (str(row.get("query") or ""), str(row.get("arxiv_id") or ""))
            for row in followup_rows
        }
        spawned_rows: list[dict[str, Any]] = []

        for row in receipt_rows:
            if receipt_id and str(row.get("receipt_id") or "") != receipt_id:
                continue
            if query and str(row.get("query") or "") != query:
                continue
            target_source_type = str(row.get("target_source_type") or "paper").strip() or "paper"
            if allowed_source_types and target_source_type not in allowed_source_types:
                continue
            if str(row.get("status") or "") != "completed":
                continue
            parent_gap_ids = self._dedupe_strings(list(row.get("parent_gap_ids") or []))
            raw_parent_followups = row.get("parent_followup_task_ids")
            if raw_parent_followups is None:
                single_parent_followup = str(row.get("parent_followup_task_id") or "").strip()
                raw_parent_followups = [single_parent_followup] if single_parent_followup else []
            parent_followup_task_ids = self._dedupe_strings(list(raw_parent_followups or []))
            reentry_targets = self._dedupe_strings(list(row.get("reentry_targets") or []))
            supporting_regression_question_ids = self._dedupe_strings(
                list(row.get("supporting_regression_question_ids") or [])
            )
            if bounded_gap_required and not (
                parent_gap_ids
                or parent_followup_task_ids
                or reentry_targets
                or supporting_regression_question_ids
            ):
                continue
            for match in list(row.get("matches") or [])[:max_subtopics]:
                arxiv_id = str(match.get("arxiv_id") or "").strip()
                if not arxiv_id:
                    continue
                dedupe_key = (str(row.get("query") or ""), arxiv_id)
                if dedupe_key in existing_keys:
                    continue
                child_topic_slug = f"{topic_slug}--followup--{slugify(arxiv_id)}"
                statement = (
                    statement_template.format(
                        query=str(row.get("query") or ""),
                        topic_slug=topic_slug,
                        arxiv_id=arxiv_id,
                    )
                    if statement_template
                    else f"Follow up the cited-literature gap `{row.get('query') or ''}` through source `{arxiv_id}`."
                )
                human_request = (
                    human_request_template.format(
                        query=str(row.get("query") or ""),
                        topic_slug=topic_slug,
                        arxiv_id=arxiv_id,
                    )
                    if human_request_template
                    else f"Study arXiv:{arxiv_id} for the bounded follow-up gap `{row.get('query') or ''}`."
                )
                bootstrap = self.orchestrate(
                    topic_slug=child_topic_slug,
                    statement=statement,
                    updated_by=updated_by,
                    arxiv_ids=[arxiv_id],
                    human_request=human_request,
                )
                source_id = ""
                child_source_rows = read_jsonl(self.kernel_root / "source-layer" / "topics" / child_topic_slug / "source_index.jsonl")
                if child_source_rows:
                    source_id = str(child_source_rows[-1].get("source_id") or "")
                return_packet = {
                    "return_packet_version": 1,
                    "child_topic_slug": child_topic_slug,
                    "parent_topic_slug": topic_slug,
                    "parent_run_id": resolved_run_id,
                    "receipt_id": str(row.get("receipt_id") or ""),
                    "query": str(row.get("query") or ""),
                    "parent_gap_ids": parent_gap_ids,
                    "parent_followup_task_ids": parent_followup_task_ids,
                    "reentry_targets": reentry_targets,
                    "supporting_regression_question_ids": supporting_regression_question_ids,
                    "source_id": source_id,
                    "arxiv_id": arxiv_id,
                    "expected_return_route": expected_return_route,
                    "acceptable_return_shapes": acceptable_return_shapes,
                    "required_output_artifacts": required_output_artifacts,
                    "unresolved_return_statuses": unresolved_return_statuses,
                    "return_status": "pending_reentry",
                    "reintegration_requirements": reintegration_requirements,
                    "updated_at": now_iso(),
                    "updated_by": updated_by,
                }
                return_packet_path = self._write_followup_return_packet(child_topic_slug, return_packet)
                spawned_row = {
                    "parent_topic_slug": topic_slug,
                    "parent_run_id": resolved_run_id,
                    "receipt_id": str(row.get("receipt_id") or ""),
                    "query": str(row.get("query") or ""),
                    "target_source_type": target_source_type,
                    "triggered_by_result_id": str(row.get("result_id") or row.get("triggered_by_result_id") or ""),
                    "parent_gap_ids": parent_gap_ids,
                    "parent_followup_task_ids": parent_followup_task_ids,
                    "reentry_targets": reentry_targets,
                    "supporting_regression_question_ids": supporting_regression_question_ids,
                    "arxiv_id": arxiv_id,
                    "source_id": source_id,
                    "child_topic_slug": child_topic_slug,
                    "status": "spawned",
                    "statement": statement,
                    "human_request": human_request,
                    "runtime_root": str(bootstrap.get("runtime_root") or ""),
                    "return_packet_path": return_packet_path,
                    "updated_at": now_iso(),
                    "updated_by": updated_by,
                }
                followup_rows.append(spawned_row)
                spawned_rows.append(spawned_row)
                existing_keys.add(dedupe_key)

        followup_paths = self._write_followup_subtopic_rows(topic_slug, followup_rows)
        return {
            "topic_slug": topic_slug,
            "run_id": resolved_run_id,
            "literature_followup_receipts_path": str(receipts_path),
            "spawned_subtopics": spawned_rows,
            **followup_paths,
        }

    def _execute_auto_actions(
        self,
        *,
        topic_slug: str,
        updated_by: str,
        max_auto_steps: int,
        default_skill_queries: list[str] | None,
    ) -> dict[str, Any]:
        queue_path, queue_rows = self._load_action_queue(topic_slug)
        executed: list[dict[str, Any]] = []
        steps_used = 0

        for row in queue_rows:
            if row.get("status") != "pending":
                continue
            if not row.get("auto_runnable"):
                continue
            if steps_used >= max_auto_steps:
                continue

            action_type = row.get("action_type")
            started_at = now_iso()
            result: dict[str, Any]
            try:
                if action_type == "skill_discovery":
                    queries = row.get("handler_args", {}).get("queries") or default_skill_queries or []
                    if not queries:
                        raise RuntimeError("No skill discovery queries were provided.")
                    result = self._discover_skills(
                        topic_slug=topic_slug,
                        queries=[str(query) for query in queries],
                        updated_by=updated_by,
                    )
                elif action_type == "conformance_audit":
                    result = self.audit(topic_slug=topic_slug, phase="entry", updated_by=updated_by)
                elif action_type == "literature_followup_search":
                    result = self._run_literature_followup(
                        topic_slug=topic_slug,
                        row=row,
                        updated_by=updated_by,
                    )
                elif action_type == "apply_candidate_split_contract":
                    result = self.apply_candidate_split_contract(
                        topic_slug=topic_slug,
                        run_id=(row.get("handler_args") or {}).get("run_id"),
                        updated_by=updated_by,
                    )
                elif action_type == "reactivate_deferred_candidate":
                    result = self.reactivate_deferred_candidates(
                        topic_slug=topic_slug,
                        run_id=(row.get("handler_args") or {}).get("run_id"),
                        entry_id=(row.get("handler_args") or {}).get("entry_id"),
                        updated_by=updated_by,
                    )
                elif action_type == "spawn_followup_subtopics":
                    result = self.spawn_followup_subtopics(
                        topic_slug=topic_slug,
                        run_id=(row.get("handler_args") or {}).get("run_id"),
                        query=(row.get("handler_args") or {}).get("query"),
                        receipt_id=(row.get("handler_args") or {}).get("receipt_id"),
                        updated_by=updated_by,
                    )
                elif action_type == "reintegrate_followup_subtopic":
                    result = self.reintegrate_followup_subtopic(
                        topic_slug=topic_slug,
                        child_topic_slug=str((row.get("handler_args") or {}).get("child_topic_slug") or ""),
                        run_id=(row.get("handler_args") or {}).get("run_id"),
                        updated_by=updated_by,
                    )
                elif action_type == "assess_topic_completion":
                    result = self.assess_topic_completion(
                        topic_slug=topic_slug,
                        run_id=(row.get("handler_args") or {}).get("run_id"),
                        updated_by=updated_by,
                    )
                elif action_type == "prepare_lean_bridge":
                    result = self.prepare_lean_bridge(
                        topic_slug=topic_slug,
                        run_id=(row.get("handler_args") or {}).get("run_id"),
                        candidate_id=(row.get("handler_args") or {}).get("candidate_id"),
                        updated_by=updated_by,
                    )
                elif action_type == "auto_promote_candidate":
                    result = self.auto_promote_candidate(
                        topic_slug=topic_slug,
                        candidate_id=str((row.get("handler_args") or {}).get("candidate_id") or ""),
                        run_id=(row.get("handler_args") or {}).get("run_id"),
                        promoted_by=updated_by,
                        backend_id=(row.get("handler_args") or {}).get("backend_id"),
                        target_backend_root=(row.get("handler_args") or {}).get("target_backend_root"),
                        domain=(row.get("handler_args") or {}).get("domain"),
                        subdomain=(row.get("handler_args") or {}).get("subdomain"),
                        source_id=(row.get("handler_args") or {}).get("source_id"),
                        source_section=(row.get("handler_args") or {}).get("source_section"),
                        source_section_title=(row.get("handler_args") or {}).get("source_section_title"),
                        notes=(row.get("handler_args") or {}).get("notes"),
                    )
                elif row.get("handler"):
                    result = self._run_generic_auto_handler(
                        topic_slug=topic_slug,
                        row=row,
                        updated_by=updated_by,
                    )
                else:
                    raise RuntimeError(f"Unsupported auto action type: {action_type}")
                row["status"] = "completed"
                row["started_at"] = started_at
                row["completed_at"] = now_iso()
                row["result"] = result
            except Exception as exc:  # noqa: BLE001
                row["status"] = "failed"
                row["started_at"] = started_at
                row["completed_at"] = now_iso()
                row["error"] = str(exc)
                result = {"error": str(exc)}
            executed.append(
                {
                    "action_id": row.get("action_id"),
                    "action_type": action_type,
                    "status": row.get("status"),
                    "result": result,
                }
            )
            steps_used += 1

        write_jsonl(queue_path, queue_rows)
        remaining = sum(1 for row in queue_rows if row.get("status") == "pending")
        return {
            "queue_path": str(queue_path),
            "executed": executed,
            "remaining_pending": remaining,
        }

    def _operation_summary_markdown(self, manifest: dict[str, Any]) -> str:
        lines = [
            "# Operation trust summary",
            "",
            f"- Operation id: `{manifest['operation_id']}`",
            f"- Title: `{manifest['title']}`",
            f"- Kind: `{manifest['kind']}`",
            f"- Updated at: `{manifest['updated_at']}`",
            f"- Updated by: `{manifest['updated_by']}`",
            "",
            "## Trust requirements",
            "",
            f"- Baseline required: `{str(manifest['baseline_required']).lower()}`",
            f"- Baseline status: `{manifest['baseline_status']}`",
            f"- Atomic understanding required: `{str(manifest['atomic_understanding_required']).lower()}`",
            f"- Atomic understanding status: `{manifest['atomic_understanding_status']}`",
            "",
            "## Summary",
            "",
            f"- {manifest['summary']}",
            "",
        ]
        if manifest.get("notes"):
            lines.extend(["## Notes", "", f"- {manifest['notes']}", ""])
        if manifest.get("references"):
            lines.extend(["## References", ""])
            for reference in manifest["references"]:
                lines.append(f"- `{reference}`")
            lines.append("")
        return "\n".join(lines)

    def _trust_report_markdown(self, payload: dict[str, Any]) -> str:
        lines = [
            "# Operation trust audit",
            "",
            f"- Topic slug: `{payload['topic_slug']}`",
            f"- Run id: `{payload['run_id']}`",
            f"- Updated at: `{payload['updated_at']}`",
            f"- Updated by: `{payload['updated_by']}`",
            f"- Overall status: `{payload['overall_status']}`",
            "",
            "## Operations",
            "",
        ]
        for operation in payload["operations"]:
            lines.extend(
                [
                    f"### `{operation['operation_id']}`",
                    "",
                    f"- Title: `{operation['title']}`",
                    f"- Kind: `{operation['kind']}`",
                    f"- Baseline status: `{operation['baseline_status']}`",
                    f"- Atomic understanding status: `{operation['atomic_understanding_status']}`",
                    f"- Trust ready: `{str(operation['trust_ready']).lower()}`",
                    f"- Manifest path: `{operation['manifest_path']}`",
                    "",
                ]
            )
        if payload["recommendations"]:
            lines.extend(["## Recommendations", ""])
            for recommendation in payload["recommendations"]:
                lines.append(f"- {recommendation}")
            lines.append("")
        return "\n".join(lines)

    def _capability_report_markdown(self, payload: dict[str, Any]) -> str:
        lines = [
            "# Capability audit",
            "",
            f"- Topic slug: `{payload['topic_slug']}`",
            f"- Updated at: `{payload['updated_at']}`",
            f"- Updated by: `{payload['updated_by']}`",
            "",
        ]
        for section_name, entries in payload["sections"].items():
            lines.extend([f"## {section_name.replace('_', ' ').title()}", ""])
            for key, entry in entries.items():
                lines.append(
                    f"- `{key}` status=`{entry['status']}` path=`{entry.get('path') or entry.get('detail') or '(n/a)'}`"
                )
            lines.append("")
        if payload["recommendations"]:
            lines.extend(["## Recommendations", ""])
            for recommendation in payload["recommendations"]:
                lines.append(f"- {recommendation}")
            lines.append("")
        return "\n".join(lines)

    def _codex_mcp_setup_markdown(self) -> str:
        command = ["codex", "mcp", "add", "aitp"]
        for key, value in self._mcp_environment().items():
            command.extend(["--env", f"{key}={value}"])
        command.extend(["--", *self._resolve_aitp_mcp_command()])
        return "\n".join(
            [
                "# Codex MCP setup",
                "",
                "Run this once to register the installable AITP MCP server with Codex:",
                "",
                "```bash",
                self._format_command(command),
                "```",
                "",
                "Verify with:",
                "",
                "```bash",
                "codex mcp get aitp",
                "```",
                "",
            ]
        )

    def _openclaw_mcp_setup_markdown(self, *, scope: str) -> str:
        command = ["mcporter", "config", "add", "aitp"]
        command.extend(["--command", self._resolve_aitp_mcp_command()[0]])
        for arg in self._resolve_aitp_mcp_command()[1:]:
            command.extend(["--arg", arg])
        for key, value in self._mcp_environment().items():
            command.extend(["--env", f"{key}={value}"])
        command.extend(["--scope", "home" if scope == "user" else "project"])
        return "\n".join(
            [
                "# OpenClaw MCP setup via mcporter",
                "",
                "OpenClaw reaches MCP servers through mcporter on this machine.",
                "",
                "```bash",
                self._format_command(command),
                "```",
                "",
                "Verify with:",
                "",
                "```bash",
                "mcporter config get aitp --json",
                "```",
                "",
            ]
        )

    def _opencode_mcp_entry(self) -> dict[str, Any]:
        return {
            "type": "local",
            "command": self._resolve_aitp_mcp_command(),
            "enabled": True,
            "timeout": 20000,
            "environment": self._mcp_environment(),
        }

    def _write_json_file(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _codex_skill_targets(self, *, scope: str, target_root: str | None) -> list[Path]:
        if target_root:
            target_path = Path(target_root)
            if target_path.name == "aitp-runtime" or target_path.parent.name == "skills":
                return [target_path]
            return [target_path / ".agents" / "skills" / "aitp-runtime"]
        if scope == "project":
            return [self.repo_root / ".agents" / "skills" / "aitp-runtime"]

        home = Path.home()
        candidates = []
        if (home / ".codex").exists() or (home / ".codex" / "config.toml").exists():
            candidates.append(home / ".codex" / "skills" / "aitp-runtime")
        if (home / ".codex-home").exists():
            candidates.append(home / ".codex-home" / "skills" / "aitp-runtime")
        if not candidates:
            candidates.append(home / ".codex" / "skills" / "aitp-runtime")

        deduped: list[Path] = []
        seen: set[str] = set()
        for candidate in candidates:
            key = str(candidate)
            if key not in seen:
                seen.add(key)
                deduped.append(candidate)
        return deduped

    def _install_codex_mcp(self, *, force: bool) -> list[dict[str, str]]:
        codex = shutil.which("codex")
        if codex is None:
            raise FileNotFoundError("Codex CLI is not installed or not on PATH.")

        get_cmd = [codex, "mcp", "get", "aitp"]
        exists = subprocess.run(get_cmd, check=False, capture_output=True, text=True)
        if exists.returncode == 0:
            if not force:
                return [{"agent": "codex", "path": str(Path.home() / ".codex" / "config.toml"), "kind": "mcp-server"}]
            subprocess.run([codex, "mcp", "remove", "aitp"], check=False, capture_output=True, text=True)

        add_cmd = [codex, "mcp", "add", "aitp"]
        for key, value in self._mcp_environment().items():
            add_cmd.extend(["--env", f"{key}={value}"])
        add_cmd.extend(["--", *self._resolve_aitp_mcp_command()])
        self._run(add_cmd)
        return [{"agent": "codex", "path": str(Path.home() / ".codex" / "config.toml"), "kind": "mcp-server"}]

    def _install_openclaw_mcp(self, *, force: bool, scope: str) -> list[dict[str, str]]:
        mcporter = shutil.which("mcporter")
        if mcporter is None:
            raise FileNotFoundError("mcporter is not installed or not on PATH.")

        if force:
            subprocess.run([mcporter, "config", "remove", "aitp"], check=False, capture_output=True, text=True)

        command = [mcporter, "config", "add", "aitp", "--command", self._resolve_aitp_mcp_command()[0]]
        for arg in self._resolve_aitp_mcp_command()[1:]:
            command.extend(["--arg", arg])
        for key, value in self._mcp_environment().items():
            command.extend(["--env", f"{key}={value}"])
        command.extend(["--scope", "home" if scope == "user" else "project"])
        self._run(command)
        return [{"agent": "openclaw", "path": f"mcporter:{scope}:aitp", "kind": "mcp-server"}]

    def _install_opencode_mcp(
        self,
        *,
        force: bool,
        scope: str,
        target_root: str | None,
    ) -> list[dict[str, str]]:
        if target_root:
            base = Path(target_root)
            config_path = base / "AITP_MCP_CONFIG.json"
            self._write_json_file(config_path, {"mcp": {"aitp": self._opencode_mcp_entry()}})
            return [{"agent": "opencode", "path": str(config_path), "kind": "mcp-config"}]

        if scope == "project":
            config_path = self.repo_root / ".opencode" / "opencode.json"
        else:
            config_path = Path.home() / ".config" / "opencode" / "opencode.json"

        if config_path.exists():
            payload = json.loads(config_path.read_text(encoding="utf-8"))
        else:
            payload = {"$schema": "https://opencode.ai/config.json"}

        mcp_payload = payload.setdefault("mcp", {})
        if "aitp" in mcp_payload and not force:
            raise FileExistsError(f"Refusing to overwrite existing OpenCode MCP server at {config_path}")
        mcp_payload["aitp"] = self._opencode_mcp_entry()
        self._write_json_file(config_path, payload)
        return [{"agent": "opencode", "path": str(config_path), "kind": "mcp-config"}]

    def get_runtime_state(self, topic_slug: str) -> dict[str, Any]:
        topic_state = read_json(self._runtime_root(topic_slug) / "topic_state.json")
        if topic_state is None:
            raise FileNotFoundError(f"Runtime state missing for topic {topic_slug}")
        return topic_state

    def new_topic(
        self,
        *,
        topic: str,
        question: str,
        mode: str | None = None,
        run_id: str | None = None,
        control_note: str | None = None,
        updated_by: str = "aitp-cli",
        arxiv_ids: list[str] | None = None,
        local_note_paths: list[str] | None = None,
        skill_queries: list[str] | None = None,
        human_request: str | None = None,
    ) -> dict[str, Any]:
        research_mode = self._template_mode_to_research_mode(mode) if mode else None
        payload = self.orchestrate(
            topic=topic,
            statement=question,
            run_id=run_id,
            control_note=control_note,
            updated_by=updated_by,
            arxiv_ids=arxiv_ids,
            local_note_paths=local_note_paths,
            skill_queries=skill_queries,
            human_request=human_request or question,
            research_mode=research_mode,
        )
        payload["template_mode"] = mode or self._research_mode_to_template_mode(
            str((payload.get("topic_state") or {}).get("research_mode") or research_mode or "")
        )
        return payload

    def topic_status(
        self,
        *,
        topic_slug: str,
        updated_by: str = "aitp-cli",
    ) -> dict[str, Any]:
        protocol_paths = self._materialize_runtime_protocol_bundle(
            topic_slug=topic_slug,
            updated_by=updated_by,
        )
        bundle = read_json(Path(protocol_paths["runtime_protocol_path"])) or {}
        minimal = bundle.get("minimal_execution_brief") or {}
        return {
            "topic_slug": topic_slug,
            "title": str(((bundle.get("active_research_contract") or {}).get("title") or self._topic_display_title(topic_slug))),
            "current_stage": bundle.get("resume_stage"),
            "research_mode": bundle.get("research_mode"),
            "selected_action_id": minimal.get("selected_action_id"),
            "selected_action_type": minimal.get("selected_action_type"),
            "selected_action_summary": minimal.get("selected_action_summary"),
            "runtime_protocol_path": protocol_paths["runtime_protocol_path"],
            "runtime_protocol_note_path": protocol_paths["runtime_protocol_note_path"],
            "active_research_contract": bundle.get("active_research_contract") or {},
            "promotion_readiness": bundle.get("promotion_readiness") or {},
            "open_gap_summary": bundle.get("open_gap_summary") or {},
            "topic_completion": bundle.get("topic_completion") or {},
            "lean_bridge": bundle.get("lean_bridge") or {},
            "must_read_now": bundle.get("must_read_now") or [],
        }

    def topic_next(
        self,
        *,
        topic_slug: str,
        updated_by: str = "aitp-cli",
    ) -> dict[str, Any]:
        protocol_paths = self._materialize_runtime_protocol_bundle(
            topic_slug=topic_slug,
            updated_by=updated_by,
        )
        bundle = read_json(Path(protocol_paths["runtime_protocol_path"])) or {}
        minimal = bundle.get("minimal_execution_brief") or {}
        return {
            "topic_slug": topic_slug,
            "selected_action_id": minimal.get("selected_action_id"),
            "selected_action_type": minimal.get("selected_action_type"),
            "selected_action_summary": minimal.get("selected_action_summary"),
            "current_stage": minimal.get("current_stage"),
            "open_next": minimal.get("open_next"),
            "must_read_now": bundle.get("must_read_now") or [],
            "escalation_triggers": bundle.get("escalation_triggers") or [],
            "open_gap_summary": bundle.get("open_gap_summary") or {},
            "topic_completion": bundle.get("topic_completion") or {},
            "runtime_protocol_note_path": protocol_paths["runtime_protocol_note_path"],
        }

    def work_topic(
        self,
        *,
        topic: str | None = None,
        topic_slug: str | None = None,
        question: str | None = None,
        mode: str | None = None,
        run_id: str | None = None,
        control_note: str | None = None,
        updated_by: str = "aitp-cli",
        skill_queries: list[str] | None = None,
        human_request: str | None = None,
        max_auto_steps: int = 1,
    ) -> dict[str, Any]:
        research_mode = self._template_mode_to_research_mode(mode) if mode else None
        if max_auto_steps <= 0:
            return self.orchestrate(
                topic=topic,
                topic_slug=topic_slug,
                statement=question,
                run_id=run_id,
                control_note=control_note,
                updated_by=updated_by,
                skill_queries=skill_queries,
                human_request=human_request or question,
                research_mode=research_mode,
            )
        return self.run_topic_loop(
            topic=topic,
            topic_slug=topic_slug,
            statement=question,
            run_id=run_id,
            control_note=control_note,
            updated_by=updated_by,
            human_request=human_request or question,
            skill_queries=skill_queries,
            max_auto_steps=max_auto_steps,
            research_mode=research_mode,
        )

    def prepare_verification(
        self,
        *,
        topic_slug: str,
        mode: str,
        updated_by: str = "aitp-cli",
    ) -> dict[str, Any]:
        mode_defaults = {
            "proof": {
                "validation_mode": "formal",
                "verification_focus": "Check that every non-trivial proof or derivation step is explicit, anchored, and reusable.",
                "required_checks": [
                    "Open the theory-packet coverage, notation, and derivation surfaces before closing the proof lane.",
                    "Confirm that cited prerequisites and prior-work dependencies have durable L0/L1 support.",
                    "Reject any step that only exists as prose without derivation-step or proof-fragment support.",
                ],
            },
            "comparison": {
                "validation_mode": "comparison",
                "verification_focus": "Compare the active claim set against cited prior work, alternative derivations, or reference formulations.",
                "required_checks": [
                    "Make the comparison target explicit and source-backed.",
                    "Record regime matches and mismatches rather than smoothing them over.",
                    "Return to L0 if the comparison source set is incomplete.",
                ],
            },
            "numeric": {
                "validation_mode": "numerical",
                "verification_focus": "Validate the active topic against executed numeric or benchmark evidence.",
                "required_checks": [
                    "Require executed evidence artifacts, not only planned benchmarks.",
                    "Require declared tolerances or qualitative agreement criteria.",
                    "Reject narrative-only claims that lack result artifacts or route receipts.",
                ],
            },
            "topic-completion": {
                "validation_mode": "hybrid",
                "verification_focus": "Judge whether the whole topic is ready for bounded completion or promotion routing.",
                "required_checks": [
                    "Check promotion blockers, split requirements, cited-recovery flags, and regression support together.",
                    "Ensure the research and validation contracts still match the topic shell surfaces.",
                    "Return to L0 for any unresolved source or prior-work blocker before marking topic completion.",
                ],
            },
        }
        if mode not in mode_defaults:
            raise ValueError(f"Unsupported verification mode: {mode}")

        self.get_runtime_state(topic_slug)
        shell_surfaces = self.ensure_topic_shell_surfaces(
            topic_slug=topic_slug,
            updated_by=updated_by,
        )
        validation_paths = self._validation_contract_paths(topic_slug)
        validation_contract = dict(shell_surfaces["validation_contract"])
        latest_run_id = str((self.get_runtime_state(topic_slug)).get("latest_run_id") or "").strip()
        candidate_rows = self._candidate_rows_for_run(topic_slug, latest_run_id)
        defaults = mode_defaults[mode]
        validation_contract["status"] = "planned"
        validation_contract["validation_mode"] = defaults["validation_mode"]
        validation_contract["verification_focus"] = defaults["verification_focus"]
        validation_contract["required_checks"] = defaults["required_checks"]
        validation_contract["acceptance_rule"] = (
            "Accept only when the requested verification mode is satisfied by durable artifacts and no active L0-recovery blocker is being hidden."
        )
        validation_contract["rejection_rule"] = (
            "Reject when proof, comparison, or execution claims outrun the currently persisted artifacts."
        )
        if mode == "topic-completion":
            validation_contract["target_claim_ids"] = self._dedupe_strings(
                [str(row.get("candidate_id") or "").strip() for row in candidate_rows if str(row.get("candidate_id") or "").strip()]
            )
        write_json(validation_paths["json"], validation_contract)
        write_text(
            validation_paths["note"],
            self._render_validation_contract_markdown(validation_contract),
        )
        protocol_paths = self._materialize_runtime_protocol_bundle(
            topic_slug=topic_slug,
            updated_by=updated_by,
        )
        return {
            "topic_slug": topic_slug,
            "verification_mode": mode,
            "validation_contract_path": str(validation_paths["json"]),
            "validation_contract_note_path": str(validation_paths["note"]),
            "validation_contract": validation_contract,
            "runtime_protocol": protocol_paths,
        }

    def assess_topic_completion(
        self,
        *,
        topic_slug: str,
        run_id: str | None = None,
        updated_by: str = "aitp-cli",
        refresh_runtime_bundle: bool = True,
    ) -> dict[str, Any]:
        resolved_run_id = self._resolve_run_id(topic_slug, run_id)
        candidate_rows = self._candidate_rows_for_run(topic_slug, resolved_run_id)
        payload = self._compute_topic_completion_payload(
            topic_slug=topic_slug,
            run_id=resolved_run_id,
            candidate_rows=candidate_rows,
            updated_by=updated_by,
        )
        paths = self._topic_completion_paths(topic_slug)
        write_json(paths["json"], payload)
        write_text(paths["note"], self._topic_completion_markdown(payload))
        result = {
            **payload,
            "topic_completion_path": str(paths["json"]),
            "topic_completion_note_path": str(paths["note"]),
        }
        if refresh_runtime_bundle:
            result["runtime_protocol"] = self._materialize_runtime_protocol_bundle(
                topic_slug=topic_slug,
                updated_by=updated_by,
            )
        return result

    def update_followup_return_packet(
        self,
        *,
        topic_slug: str,
        run_id: str | None = None,
        return_status: str,
        accepted_return_shape: str | None = None,
        return_summary: str | None = None,
        child_topic_summary: str | None = None,
        return_artifact_paths: list[str] | None = None,
        updated_by: str = "aitp-cli",
        refresh_runtime_bundle: bool = True,
    ) -> dict[str, Any]:
        packet_path = self._followup_return_packet_path(topic_slug)
        packet = read_json(packet_path)
        if packet is None:
            raise FileNotFoundError(f"Follow-up return packet missing for child topic {topic_slug}")

        normalized_status = str(return_status or "").strip()
        if not normalized_status:
            raise ValueError("Return status is required.")

        policy = self._load_runtime_policy().get("followup_subtopic_policy") or {}
        unresolved_statuses = {
            str(value).strip()
            for value in (policy.get("unresolved_return_statuses") or [])
            if str(value).strip()
        }
        if not unresolved_statuses:
            unresolved_statuses = {"pending_reentry", "returned_with_gap", "returned_unresolved"}
        supported_statuses = {"pending_reentry", "recovered_units", "resolved_gap_update"} | unresolved_statuses
        if normalized_status not in supported_statuses:
            raise ValueError(f"Unsupported follow-up return status: {normalized_status}")

        acceptable_return_shapes = self._dedupe_strings(list(packet.get("acceptable_return_shapes") or []))
        resolved_return_shape = (
            str(accepted_return_shape or "").strip()
            or self._return_shape_for_status(normalized_status, unresolved_statuses)
        )
        if normalized_status == "pending_reentry":
            resolved_return_shape = ""
        if resolved_return_shape and acceptable_return_shapes and resolved_return_shape not in acceptable_return_shapes:
            raise ValueError(
                f"Return shape {resolved_return_shape} is not allowed for child topic {topic_slug}."
            )

        resolved_artifact_paths = self._dedupe_strings(list(return_artifact_paths or []))
        if not resolved_artifact_paths:
            resolved_artifact_paths = self._dedupe_strings(list(packet.get("return_artifact_paths") or []))

        resolved_summary = str(return_summary or packet.get("return_summary") or "").strip()
        resolved_child_summary = str(child_topic_summary or packet.get("child_topic_summary") or "").strip()
        if normalized_status in {"recovered_units", "resolved_gap_update"} and not resolved_artifact_paths:
            raise ValueError(
                "Recovered follow-up returns must name at least one durable return artifact path."
            )
        if normalized_status in unresolved_statuses and normalized_status != "pending_reentry" and not resolved_summary:
            raise ValueError("Unresolved follow-up returns must provide a return summary.")

        resolved_child_run_id = self._resolve_run_id(topic_slug, run_id)
        updated_packet = dict(packet)
        updated_packet["return_status"] = normalized_status
        if resolved_return_shape:
            updated_packet["accepted_return_shape"] = resolved_return_shape
        else:
            updated_packet.pop("accepted_return_shape", None)
        if resolved_summary:
            updated_packet["return_summary"] = resolved_summary
        elif normalized_status == "pending_reentry":
            updated_packet.pop("return_summary", None)
        if resolved_artifact_paths:
            updated_packet["return_artifact_paths"] = resolved_artifact_paths
        elif normalized_status == "pending_reentry":
            updated_packet.pop("return_artifact_paths", None)
        if resolved_child_summary:
            updated_packet["child_topic_summary"] = resolved_child_summary
        if resolved_child_run_id:
            updated_packet["child_run_id"] = resolved_child_run_id
        updated_packet["updated_at"] = now_iso()
        updated_packet["updated_by"] = updated_by
        updated_packet["return_updated_at"] = updated_packet["updated_at"]
        updated_packet["return_updated_by"] = updated_by
        self._write_followup_return_packet(topic_slug, updated_packet)

        result = {
            **updated_packet,
            "topic_slug": topic_slug,
            "return_packet_path": str(packet_path),
            "return_packet_note_path": str(self._followup_return_packet_note_path(topic_slug)),
        }
        if refresh_runtime_bundle:
            result["runtime_protocol"] = self._materialize_runtime_protocol_bundle(
                topic_slug=topic_slug,
                updated_by=updated_by,
            )
        return result

    def reintegrate_followup_subtopic(
        self,
        *,
        topic_slug: str,
        child_topic_slug: str,
        run_id: str | None = None,
        updated_by: str = "aitp-cli",
    ) -> dict[str, Any]:
        resolved_run_id = self._resolve_run_id(topic_slug, run_id)
        if not resolved_run_id:
            raise FileNotFoundError(f"Unable to resolve a validation run for topic {topic_slug}")
        followup_rows = self._load_followup_subtopic_rows(topic_slug)
        matching_row = next(
            (
                row
                for row in followup_rows
                if str(row.get("child_topic_slug") or "").strip() == child_topic_slug
            ),
            None,
        )
        if matching_row is None:
            raise FileNotFoundError(f"Follow-up child topic not registered under parent topic {topic_slug}: {child_topic_slug}")
        return_packet_path = str(matching_row.get("return_packet_path") or "").strip() or str(
            self._followup_return_packet_path(child_topic_slug)
        )
        return_packet = read_json(Path(return_packet_path))
        if return_packet is None:
            raise FileNotFoundError(f"Follow-up return packet missing for child topic {child_topic_slug}")
        if str(return_packet.get("parent_topic_slug") or "").strip() != topic_slug:
            raise ValueError("Follow-up return packet parent topic does not match the requested parent topic.")
        return_status = str(return_packet.get("return_status") or "").strip() or "pending_reentry"
        if return_status == "pending_reentry":
            raise ValueError("Child topic still reports pending_reentry and cannot be reintegrated yet.")
        acceptable_return_shapes = self._dedupe_strings(list(return_packet.get("acceptable_return_shapes") or []))
        policy = self._load_runtime_policy().get("followup_subtopic_policy") or {}
        unresolved_statuses = {
            str(value).strip()
            for value in (policy.get("unresolved_return_statuses") or [])
            if str(value).strip()
        }
        if not unresolved_statuses:
            unresolved_statuses = {"pending_reentry", "returned_with_gap", "returned_unresolved"}
        unresolved_statuses.discard("pending_reentry")
        accepted_return_shape = str(return_packet.get("accepted_return_shape") or "").strip()
        if not accepted_return_shape:
            accepted_return_shape = self._return_shape_for_status(return_status, unresolved_statuses)
            if not accepted_return_shape and acceptable_return_shapes and return_status != "pending_reentry":
                accepted_return_shape = acceptable_return_shapes[0]
        if accepted_return_shape and acceptable_return_shapes and accepted_return_shape not in acceptable_return_shapes:
            raise ValueError(
                f"Accepted return shape {accepted_return_shape} is not allowed by the child return packet."
            )
        return_artifact_paths = self._dedupe_strings(list(return_packet.get("return_artifact_paths") or []))
        if return_status in {"recovered_units", "resolved_gap_update"} and not return_artifact_paths:
            raise ValueError("Recovered child follow-up returns must provide durable return artifact paths before reintegration.")
        parent_status = "returned_with_gap" if return_status in unresolved_statuses else "reintegrated"
        child_completion = read_json(self._topic_completion_paths(child_topic_slug)["json"]) or {}
        reintegration_requirements = dict(return_packet.get("reintegration_requirements") or {})
        summary = (
            str(return_packet.get("return_summary") or "").strip()
            or str(return_packet.get("summary") or "").strip()
            or (
                "Child topic returned with unresolved gaps."
                if parent_status == "returned_with_gap"
                else "Child topic return packet was reintegrated into the parent topic."
            )
        )
        receipt_row = {
            "parent_topic_slug": topic_slug,
            "parent_run_id": resolved_run_id,
            "child_topic_slug": child_topic_slug,
            "receipt_id": str(return_packet.get("receipt_id") or matching_row.get("receipt_id") or ""),
            "return_status": return_status,
            "accepted_return_shape": accepted_return_shape,
            "source_id": str(return_packet.get("source_id") or matching_row.get("source_id") or ""),
            "arxiv_id": str(return_packet.get("arxiv_id") or matching_row.get("arxiv_id") or ""),
            "reentry_targets": self._dedupe_strings(list(return_packet.get("reentry_targets") or matching_row.get("reentry_targets") or [])),
            "parent_gap_ids": self._dedupe_strings(list(return_packet.get("parent_gap_ids") or matching_row.get("parent_gap_ids") or [])),
            "parent_followup_task_ids": self._dedupe_strings(
                list(return_packet.get("parent_followup_task_ids") or matching_row.get("parent_followup_task_ids") or [])
            ),
            "supporting_regression_question_ids": self._dedupe_strings(
                list(return_packet.get("supporting_regression_question_ids") or matching_row.get("supporting_regression_question_ids") or [])
            ),
            "return_packet_path": return_packet_path,
            "return_artifact_paths": return_artifact_paths,
            "child_topic_completion_status": str(child_completion.get("status") or "not_assessed"),
            "child_topic_summary": str(return_packet.get("child_topic_summary") or "").strip(),
            "gap_writeback_required": parent_status == "returned_with_gap"
            and bool(reintegration_requirements.get("must_write_back_parent_gaps")),
            "reentry_update_required": bool(reintegration_requirements.get("must_update_reentry_targets")),
            "summary": summary,
            "updated_at": now_iso(),
            "updated_by": updated_by,
        }
        reintegration_rows = [
            row
            for row in self._load_followup_reintegration_rows(topic_slug)
            if str(row.get("child_topic_slug") or "").strip() != child_topic_slug
        ]
        reintegration_rows.append(receipt_row)
        reintegration_paths = self._write_followup_reintegration_rows(topic_slug, reintegration_rows)

        gap_writeback_rows = [
            row
            for row in self._load_followup_gap_writeback_rows(topic_slug)
            if str(row.get("child_topic_slug") or "").strip() != child_topic_slug
        ]
        if receipt_row["gap_writeback_required"]:
            gap_writeback_rows.append(
                {
                    "parent_topic_slug": topic_slug,
                    "parent_run_id": resolved_run_id,
                    "child_topic_slug": child_topic_slug,
                    "receipt_id": receipt_row["receipt_id"],
                    "return_status": return_status,
                    "parent_gap_ids": receipt_row["parent_gap_ids"],
                    "parent_followup_task_ids": receipt_row["parent_followup_task_ids"],
                    "reentry_targets": receipt_row["reentry_targets"],
                    "summary": summary,
                    "return_packet_path": return_packet_path,
                    "return_artifact_paths": return_artifact_paths,
                    "updated_at": now_iso(),
                    "updated_by": updated_by,
                }
            )
        gap_writeback_paths = self._write_followup_gap_writeback_rows(topic_slug, gap_writeback_rows)

        updated_followup_rows: list[dict[str, Any]] = []
        for row in followup_rows:
            if str(row.get("child_topic_slug") or "").strip() != child_topic_slug:
                updated_followup_rows.append(row)
                continue
            updated_row = dict(row)
            updated_row["status"] = parent_status
            updated_row["reintegrated_at"] = now_iso()
            updated_row["reintegrated_by"] = updated_by
            updated_row["reintegration_receipt_path"] = reintegration_paths["followup_reintegration_path"]
            updated_row["return_status"] = return_status
            updated_followup_rows.append(updated_row)
        followup_paths = self._write_followup_subtopic_rows(topic_slug, updated_followup_rows)
        completion = self.assess_topic_completion(
            topic_slug=topic_slug,
            run_id=resolved_run_id,
            updated_by=updated_by,
            refresh_runtime_bundle=False,
        )
        runtime_protocol = self._materialize_runtime_protocol_bundle(
            topic_slug=topic_slug,
            updated_by=updated_by,
        )
        return {
            "topic_slug": topic_slug,
            "run_id": resolved_run_id,
            "child_topic_slug": child_topic_slug,
            "parent_followup_status": parent_status,
            "reintegration_receipt": receipt_row,
            **reintegration_paths,
            **gap_writeback_paths,
            **followup_paths,
            "topic_completion": completion,
            "runtime_protocol": runtime_protocol,
        }

    def prepare_lean_bridge(
        self,
        *,
        topic_slug: str,
        run_id: str | None = None,
        candidate_id: str | None = None,
        updated_by: str = "aitp-cli",
        refresh_runtime_bundle: bool = True,
    ) -> dict[str, Any]:
        resolved_run_id = self._resolve_run_id(topic_slug, run_id)
        candidate_rows = self._candidate_rows_for_run(topic_slug, resolved_run_id)
        payload = self._materialize_lean_bridge(
            topic_slug=topic_slug,
            run_id=resolved_run_id,
            candidate_rows=candidate_rows,
            updated_by=updated_by,
            candidate_id=candidate_id,
        )
        result = dict(payload)
        if refresh_runtime_bundle:
            result["runtime_protocol"] = self._materialize_runtime_protocol_bundle(
                topic_slug=topic_slug,
                updated_by=updated_by,
            )
        return result

    def orchestrate(
        self,
        *,
        topic_slug: str | None = None,
        topic: str | None = None,
        statement: str | None = None,
        run_id: str | None = None,
        control_note: str | None = None,
        updated_by: str = "aitp-cli",
        arxiv_ids: list[str] | None = None,
        local_note_paths: list[str] | None = None,
        skill_queries: list[str] | None = None,
        human_request: str | None = None,
        research_mode: str | None = None,
    ) -> dict[str, Any]:
        if not topic_slug and not topic:
            raise ValueError("Provide topic_slug or topic.")

        resolved_topic_slug = topic_slug or slugify(topic or "")
        command = [
            "python3",
            str(self._kernel_script("runtime/scripts/orchestrate_topic.py")),
            "--updated-by",
            updated_by,
        ]
        if topic_slug:
            command.extend(["--topic-slug", topic_slug])
        if topic:
            command.extend(["--topic", topic])
        if statement:
            command.extend(["--statement", statement])
        if run_id:
            command.extend(["--run-id", run_id])
        if control_note:
            command.extend(["--control-note", control_note])
        if human_request:
            command.extend(["--human-request", human_request])
        if research_mode:
            command.extend(["--research-mode", research_mode])
        for arxiv_id in arxiv_ids or []:
            command.extend(["--arxiv-id", arxiv_id])
        for note_path in local_note_paths or []:
            command.extend(["--local-note-path", note_path])
        for query in skill_queries or []:
            command.extend(["--skill-query", query])

        completed = self._run(command)
        runtime_root = self._runtime_root(resolved_topic_slug)
        protocol_paths = self._materialize_runtime_protocol_bundle(
            topic_slug=resolved_topic_slug,
            updated_by=updated_by,
            human_request=human_request,
        )
        return {
            "topic_slug": resolved_topic_slug,
            "command": command,
            "stdout": completed.stdout.strip(),
            "runtime_root": str(runtime_root),
            "files": {
                "topic_state": str(runtime_root / "topic_state.json"),
                "resume": str(runtime_root / "resume.md"),
                "action_queue": str(runtime_root / "action_queue.jsonl"),
                "agent_brief": str(runtime_root / "agent_brief.md"),
                "interaction_state": str(runtime_root / "interaction_state.json"),
                "operator_console": str(runtime_root / "operator_console.md"),
                "conformance_state": str(runtime_root / "conformance_state.json"),
                "conformance_report": str(runtime_root / "conformance_report.md"),
                "runtime_protocol": protocol_paths["runtime_protocol_path"],
                "runtime_protocol_note": protocol_paths["runtime_protocol_note_path"],
                "research_question_contract": str(self._research_question_contract_paths(resolved_topic_slug)["json"]),
                "research_question_contract_note": str(self._research_question_contract_paths(resolved_topic_slug)["note"]),
                "validation_contract": str(self._validation_contract_paths(resolved_topic_slug)["json"]),
                "validation_contract_note": str(self._validation_contract_paths(resolved_topic_slug)["note"]),
                "topic_dashboard": str(self._topic_dashboard_path(resolved_topic_slug)),
                "promotion_readiness": str(self._promotion_readiness_path(resolved_topic_slug)),
                "gap_map": str(self._gap_map_path(resolved_topic_slug)),
            },
            "topic_state": self.get_runtime_state(resolved_topic_slug),
            "conformance_state": read_json(runtime_root / "conformance_state.json"),
        }

    def audit(self, *, topic_slug: str, phase: str = "entry", updated_by: str = "aitp-cli") -> dict[str, Any]:
        command = [
            "python3",
            str(self._kernel_script("runtime/scripts/audit_topic_conformance.py")),
            "--topic-slug",
            topic_slug,
            "--phase",
            phase,
            "--updated-by",
            updated_by,
        ]
        completed = self._run(command)
        runtime_root = self._runtime_root(topic_slug)
        state = read_json(runtime_root / "conformance_state.json")
        report_path = runtime_root / "conformance_report.md"
        return {
            "topic_slug": topic_slug,
            "phase": phase,
            "command": command,
            "stdout": completed.stdout.strip(),
            "conformance_state": state,
            "conformance_report_path": str(report_path),
        }

    def scaffold_baseline(
        self,
        *,
        topic_slug: str,
        run_id: str,
        title: str,
        reference: str,
        agreement_criterion: str,
        baseline_kind: str = "public_example",
        updated_by: str = "aitp-cli",
        notes: str | None = None,
    ) -> dict[str, Any]:
        run_root = self._validation_run_root(topic_slug, run_id)
        run_root.mkdir(parents=True, exist_ok=True)
        baseline_id = f"baseline:{slugify(title)}"

        plan_path = run_root / "baseline_plan.md"
        results_path = run_root / "baseline_results.jsonl"
        summary_path = run_root / "baseline_summary.md"

        write_text(
            plan_path,
            "\n".join(
                [
                    "# Baseline plan",
                    "",
                    f"- Baseline id: `{baseline_id}`",
                    f"- Title: `{title}`",
                    f"- Kind: `{baseline_kind}`",
                    f"- Reference: `{reference}`",
                    f"- Agreement criterion: `{agreement_criterion}`",
                    f"- Updated by: `{updated_by}`",
                    f"- Updated at: `{now_iso()}`",
                    "",
                    "## Purpose",
                    "",
                    "- Establish method trust before interpreting novel topic-specific signals.",
                    "",
                    "## Notes",
                    "",
                    f"- {notes or 'Pending detailed reproduction instructions.'}",
                    "",
                ]
            ),
        )

        result_row = {
            "baseline_id": baseline_id,
            "title": title,
            "kind": baseline_kind,
            "reference": reference,
            "agreement_criterion": agreement_criterion,
            "status": "planned",
            "updated_by": updated_by,
            "updated_at": now_iso(),
            "artifacts": [],
            "notes": notes or "",
        }
        existing_rows = read_jsonl(results_path)
        existing_rows = [row for row in existing_rows if row.get("baseline_id") != baseline_id]
        existing_rows.append(result_row)
        write_jsonl(results_path, existing_rows)

        write_text(
            summary_path,
            "\n".join(
                [
                    "# Baseline summary",
                    "",
                    f"- Baseline id: `{baseline_id}`",
                    "- Current status: `planned`",
                    "",
                    "## Interpretation",
                    "",
                    "- This baseline has been defined but not yet executed.",
                    "- Novel topic-specific claims remain exploratory until this baseline is updated with results.",
                    "",
                ]
            ),
        )

        return {
            "baseline_id": baseline_id,
            "paths": {
                "baseline_plan": str(plan_path),
                "baseline_results": str(results_path),
                "baseline_summary": str(summary_path),
            },
        }

    def scaffold_atomic_understanding(
        self,
        *,
        topic_slug: str,
        run_id: str,
        method_title: str,
        updated_by: str = "aitp-cli",
        scope_note: str | None = None,
    ) -> dict[str, Any]:
        run_root = self._validation_run_root(topic_slug, run_id)
        run_root.mkdir(parents=True, exist_ok=True)
        method_id = f"method-understanding:{slugify(method_title)}"

        concept_map_path = run_root / "atomic_concept_map.json"
        dependency_graph_path = run_root / "derivation_dependency_graph.json"
        summary_path = run_root / "understanding_summary.md"

        write_json(
            concept_map_path,
            {
                "method_id": method_id,
                "title": method_title,
                "updated_at": now_iso(),
                "updated_by": updated_by,
                "concepts": [],
                "status": "planned",
            },
        )
        write_json(
            dependency_graph_path,
            {
                "method_id": method_id,
                "title": method_title,
                "updated_at": now_iso(),
                "updated_by": updated_by,
                "nodes": [],
                "edges": [],
                "status": "planned",
            },
        )
        write_text(
            summary_path,
            "\n".join(
                [
                    "# Understanding summary",
                    "",
                    f"- Method id: `{method_id}`",
                    f"- Method title: `{method_title}`",
                    "- Current status: `planned`",
                    "",
                    "## Scope note",
                    "",
                    f"- {scope_note or 'Pending atomic concept decomposition and dependency mapping.'}",
                    "",
                    "## Judgment",
                    "",
                    "- Do not treat this method as understood until the concept map and dependency graph are populated.",
                    "",
                ]
            ),
        )
        return {
            "method_id": method_id,
            "paths": {
                "atomic_concept_map": str(concept_map_path),
                "derivation_dependency_graph": str(dependency_graph_path),
                "understanding_summary": str(summary_path),
            },
        }

    def audit_theory_coverage(
        self,
        *,
        topic_slug: str,
        candidate_id: str,
        run_id: str | None = None,
        updated_by: str = "aitp-cli",
        source_sections: list[str] | None = None,
        covered_sections: list[str] | None = None,
        equation_labels: list[str] | None = None,
        notation_bindings: list[dict[str, str]] | None = None,
        derivation_nodes: list[str] | None = None,
        derivation_edges: list[dict[str, str]] | None = None,
        agent_votes: list[dict[str, str]] | None = None,
        consensus_status: str = "unanimous",
        critical_unit_recall: float = 1.0,
        missing_anchor_count: int = 0,
        skeptic_major_gap_count: int = 0,
        supporting_regression_question_ids: list[str] | None = None,
        supporting_oracle_ids: list[str] | None = None,
        supporting_regression_run_ids: list[str] | None = None,
        promotion_blockers: list[str] | None = None,
        split_required: bool | None = None,
        cited_recovery_required: bool | None = None,
        followup_gap_ids: list[str] | None = None,
        topic_completion_status: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        resolved_run_id = self._resolve_run_id(topic_slug, run_id)
        if not resolved_run_id:
            raise FileNotFoundError(f"Unable to resolve a validation run for topic {topic_slug}")
        if critical_unit_recall < 0.0 or critical_unit_recall > 1.0:
            raise ValueError("critical_unit_recall must be between 0.0 and 1.0")
        if missing_anchor_count < 0 or skeptic_major_gap_count < 0:
            raise ValueError("missing-anchor-count and skeptic-major-gap-count must be non-negative")

        candidate = self._load_candidate(topic_slug, resolved_run_id, candidate_id)
        source_rows = read_jsonl(self.kernel_root / "source-layer" / "topics" / topic_slug / "source_index.jsonl")
        source_row = choose_source_row(source_rows=source_rows, candidate=candidate)
        source_id = str((source_row or {}).get("source_id") or "") or f"source:{slugify(candidate_id)}"
        candidate_question_ids = self._dedupe_strings(
            supporting_regression_question_ids
            if supporting_regression_question_ids is not None
            else list(candidate.get("supporting_regression_question_ids") or [])
        )
        candidate_oracle_ids = self._dedupe_strings(
            supporting_oracle_ids
            if supporting_oracle_ids is not None
            else list(candidate.get("supporting_oracle_ids") or [])
        )
        candidate_regression_run_ids = self._dedupe_strings(
            supporting_regression_run_ids
            if supporting_regression_run_ids is not None
            else list(candidate.get("supporting_regression_run_ids") or [])
        )
        candidate_promotion_blockers = self._dedupe_strings(
            promotion_blockers
            if promotion_blockers is not None
            else list(candidate.get("promotion_blockers") or [])
        )
        candidate_split_required = (
            as_bool(split_required)
            if split_required is not None
            else as_bool(candidate.get("split_required"))
        )
        candidate_cited_recovery_required = (
            as_bool(cited_recovery_required)
            if cited_recovery_required is not None
            else as_bool(candidate.get("cited_recovery_required"))
        )
        candidate_followup_gap_ids = self._dedupe_strings(
            followup_gap_ids
            if followup_gap_ids is not None
            else list(candidate.get("followup_gap_ids") or [])
        )

        canonical_source_sections = self._dedupe_strings(source_sections or [])
        canonical_covered_sections = self._dedupe_strings(covered_sections or canonical_source_sections)
        if not canonical_source_sections and canonical_covered_sections:
            canonical_source_sections = list(canonical_covered_sections)
        if not canonical_source_sections:
            canonical_source_sections = [f"{slugify(candidate_id)}/overview"]
            canonical_covered_sections = list(canonical_source_sections)

        section_statuses = []
        covered_lookup = set(canonical_covered_sections)
        for section_id in canonical_source_sections:
            section_statuses.append(
                {
                    "section_id": section_id,
                    "status": "covered" if section_id in covered_lookup else "missing",
                }
            )
        extra_covered_sections = [section for section in canonical_covered_sections if section not in {row["section_id"] for row in section_statuses}]
        for section_id in extra_covered_sections:
            section_statuses.append({"section_id": section_id, "status": "covered"})

        notation_rows = []
        for binding in notation_bindings or []:
            symbol = str(binding.get("symbol") or "").strip()
            meaning = str(binding.get("meaning") or "").strip()
            if not symbol or not meaning:
                continue
            notation_rows.append({"symbol": symbol, "meaning": meaning})

        derivation_node_rows = []
        for node in self._dedupe_strings(derivation_nodes or []):
            derivation_node_rows.append({"id": node, "label": node})
        derivation_edge_rows = []
        for edge in derivation_edges or []:
            source = str(edge.get("source") or "").strip()
            target = str(edge.get("target") or "").strip()
            relation = str(edge.get("relation") or "").strip() or "depends_on"
            if not source or not target:
                continue
            derivation_edge_rows.append({"source": source, "target": target, "relation": relation})

        normalized_votes = []
        for row in agent_votes or []:
            role = str(row.get("role") or "").strip()
            verdict = str(row.get("verdict") or "").strip()
            if not role or not verdict:
                continue
            normalized_votes.append(
                {
                    "role": role,
                    "verdict": verdict,
                    "notes": str(row.get("notes") or "").strip(),
                }
            )
        if not normalized_votes:
            normalized_votes = [
                {"role": "structure", "verdict": "covered", "notes": ""},
                {"role": "skeptic", "verdict": "no_major_gap", "notes": ""},
                {"role": "adjudicator", "verdict": consensus_status, "notes": ""},
            ]

        coverage_status = (
            "pass"
            if canonical_source_sections
            and all(row["status"] == "covered" for row in section_statuses if row["section_id"] in canonical_source_sections)
            and missing_anchor_count == 0
            and skeptic_major_gap_count == 0
            and critical_unit_recall >= 0.95
            and consensus_status in {"unanimous", "majority"}
            else "needs_revision"
        )
        coverage_score = round(
            max(
                0.0,
                min(
                    1.0,
                    (
                        (len(canonical_covered_sections) / max(1, len(canonical_source_sections))) * 0.5
                        + critical_unit_recall * 0.35
                        + (0.15 if skeptic_major_gap_count == 0 else 0.0)
                    ),
                ),
            ),
            3,
        )

        packet_paths = self._theory_packet_paths(topic_slug, resolved_run_id, candidate_id)
        structure_map = {
            "candidate_id": candidate_id,
            "candidate_type": str(candidate.get("candidate_type") or ""),
            "source_id": source_id,
            "title": str(candidate.get("title") or candidate_id),
            "updated_at": now_iso(),
            "updated_by": updated_by,
            "sections": section_statuses,
            "equation_labels": self._dedupe_strings(equation_labels or []),
        }
        coverage_ledger = {
            "candidate_id": candidate_id,
            "candidate_type": str(candidate.get("candidate_type") or ""),
            "source_section_count": len(canonical_source_sections),
            "covered_section_count": len(canonical_covered_sections),
            "missing_section_count": len([row for row in section_statuses if row["status"] == "missing"]),
            "missing_anchor_count": missing_anchor_count,
            "critical_unit_recall": critical_unit_recall,
            "skeptic_major_gap_count": skeptic_major_gap_count,
            "consensus_status": consensus_status,
            "coverage_score": coverage_score,
            "status": coverage_status,
            "ready_for_auto_promotion": coverage_status == "pass",
            "updated_at": now_iso(),
            "updated_by": updated_by,
            "notes": notes or "",
        }
        notation_table = {
            "candidate_id": candidate_id,
            "source_id": source_id,
            "updated_at": now_iso(),
            "updated_by": updated_by,
            "status": "captured" if notation_rows else "pending",
            "bindings": notation_rows,
        }
        derivation_graph = {
            "candidate_id": candidate_id,
            "updated_at": now_iso(),
            "updated_by": updated_by,
            "status": "captured" if derivation_node_rows or derivation_edge_rows else "pending",
            "nodes": derivation_node_rows,
            "edges": derivation_edge_rows,
        }
        agent_consensus = {
            "candidate_id": candidate_id,
            "updated_at": now_iso(),
            "updated_by": updated_by,
            "consensus_status": consensus_status,
            "status": "ready" if consensus_status in {"unanimous", "majority"} else "blocked",
            "agents": normalized_votes,
            "skeptic_major_gap_count": skeptic_major_gap_count,
            "notes": notes or "",
        }
        resolved_topic_completion_status = self._derive_topic_completion_status(
            requested_status=topic_completion_status or str(candidate.get("topic_completion_status") or ""),
            coverage_status=coverage_status,
            supporting_regression_question_ids=candidate_question_ids,
            supporting_oracle_ids=candidate_oracle_ids,
            supporting_regression_run_ids=candidate_regression_run_ids,
            promotion_blockers=candidate_promotion_blockers,
            split_required=candidate_split_required,
            cited_recovery_required=candidate_cited_recovery_required,
        )
        regression_gate = self._build_regression_gate(
            topic_slug=topic_slug,
            run_id=resolved_run_id,
            candidate_id=candidate_id,
            updated_by=updated_by,
            coverage_status=coverage_status,
            consensus_status=str(agent_consensus.get("status") or "blocked"),
            topic_completion_status=resolved_topic_completion_status,
            supporting_regression_question_ids=candidate_question_ids,
            supporting_oracle_ids=candidate_oracle_ids,
            supporting_regression_run_ids=candidate_regression_run_ids,
            promotion_blockers=candidate_promotion_blockers,
            split_required=candidate_split_required,
            cited_recovery_required=candidate_cited_recovery_required,
            followup_gap_ids=candidate_followup_gap_ids,
            notes=notes or "",
        )

        write_json(packet_paths["structure_map"], structure_map)
        write_json(packet_paths["coverage_ledger"], coverage_ledger)
        write_json(packet_paths["notation_table"], notation_table)
        write_json(packet_paths["derivation_graph"], derivation_graph)
        write_json(packet_paths["agent_consensus"], agent_consensus)
        write_json(packet_paths["regression_gate"], regression_gate)

        updated_candidate = dict(candidate)
        updated_candidate["supporting_regression_question_ids"] = candidate_question_ids
        updated_candidate["supporting_oracle_ids"] = candidate_oracle_ids
        updated_candidate["supporting_regression_run_ids"] = candidate_regression_run_ids
        updated_candidate["promotion_blockers"] = candidate_promotion_blockers
        updated_candidate["split_required"] = candidate_split_required
        updated_candidate["cited_recovery_required"] = candidate_cited_recovery_required
        updated_candidate["followup_gap_ids"] = candidate_followup_gap_ids
        updated_candidate["topic_completion_status"] = resolved_topic_completion_status
        self._replace_candidate_row(topic_slug, resolved_run_id, candidate_id, updated_candidate)

        return {
            "topic_slug": topic_slug,
            "run_id": resolved_run_id,
            "candidate_id": candidate_id,
            "coverage_status": coverage_status,
            "coverage_score": coverage_score,
            "regression_gate_status": regression_gate["status"],
            "topic_completion_status": resolved_topic_completion_status,
            "ready_for_auto_promotion": coverage_ledger["ready_for_auto_promotion"],
            "paths": {key: str(value) for key, value in packet_paths.items() if key != "root"},
            "artifacts": {
                "structure_map": structure_map,
                "coverage_ledger": coverage_ledger,
                "notation_table": notation_table,
                "derivation_graph": derivation_graph,
                "agent_consensus": agent_consensus,
                "regression_gate": regression_gate,
            },
        }

    def scaffold_operation(
        self,
        *,
        topic_slug: str,
        run_id: str | None,
        title: str,
        kind: str,
        updated_by: str = "aitp-cli",
        summary: str | None = None,
        notes: str | None = None,
        baseline_required: bool | None = None,
        atomic_understanding_required: bool | None = None,
        references: list[str] | None = None,
        source_paths: list[str] | None = None,
    ) -> dict[str, Any]:
        resolved_run_id = self._resolve_run_id(topic_slug, run_id)
        if not resolved_run_id:
            raise FileNotFoundError(f"Unable to resolve a validation run for topic {topic_slug}")
        operation_id = self._operation_id(title)
        inferred_baseline_required, inferred_atomic_required = self._operation_requirement_defaults(kind)
        baseline_required = inferred_baseline_required if baseline_required is None else baseline_required
        atomic_understanding_required = (
            inferred_atomic_required if atomic_understanding_required is None else atomic_understanding_required
        )

        manifest = {
            "operation_id": operation_id,
            "topic_slug": topic_slug,
            "run_id": resolved_run_id,
            "title": title,
            "kind": kind,
            "summary": summary or "Pending trust-ready operation definition.",
            "notes": notes or "",
            "baseline_required": baseline_required,
            "baseline_status": "planned" if baseline_required else "not_required",
            "atomic_understanding_required": atomic_understanding_required,
            "atomic_understanding_status": "planned" if atomic_understanding_required else "not_required",
            "references": self._dedupe_strings(references),
            "source_paths": self._dedupe_strings(source_paths),
            "artifact_paths": [],
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "updated_by": updated_by,
        }
        manifest_path = self._operation_manifest_path(topic_slug, resolved_run_id, operation_id)
        summary_path = self._operation_summary_path(topic_slug, resolved_run_id, operation_id)
        write_json(manifest_path, manifest)
        write_text(summary_path, self._operation_summary_markdown(manifest))
        return {
            "operation_id": operation_id,
            "run_id": resolved_run_id,
            "manifest_path": str(manifest_path),
            "summary_path": str(summary_path),
            "manifest": manifest,
        }

    def update_operation(
        self,
        *,
        topic_slug: str,
        run_id: str | None,
        operation: str,
        updated_by: str = "aitp-cli",
        summary: str | None = None,
        notes: str | None = None,
        baseline_status: str | None = None,
        atomic_understanding_status: str | None = None,
        references: list[str] | None = None,
        source_paths: list[str] | None = None,
        artifact_paths: list[str] | None = None,
    ) -> dict[str, Any]:
        resolved_run_id = self._resolve_run_id(topic_slug, run_id)
        if not resolved_run_id:
            raise FileNotFoundError(f"Unable to resolve a validation run for topic {topic_slug}")
        operation_id = self._operation_id(operation)
        manifest = self._read_operation_manifest(topic_slug, resolved_run_id, operation_id)

        if summary is not None:
            manifest["summary"] = summary
        if notes is not None:
            manifest["notes"] = notes
        if baseline_status is not None:
            manifest["baseline_status"] = baseline_status
        if atomic_understanding_status is not None:
            manifest["atomic_understanding_status"] = atomic_understanding_status

        manifest["references"] = self._dedupe_strings(
            [*manifest.get("references", []), *(references or [])]
        )
        manifest["source_paths"] = self._dedupe_strings(
            [*manifest.get("source_paths", []), *(source_paths or [])]
        )
        manifest["artifact_paths"] = self._dedupe_strings(
            [*manifest.get("artifact_paths", []), *(artifact_paths or [])]
        )
        manifest["updated_at"] = now_iso()
        manifest["updated_by"] = updated_by

        manifest_path = self._operation_manifest_path(topic_slug, resolved_run_id, operation_id)
        summary_path = self._operation_summary_path(topic_slug, resolved_run_id, operation_id)
        write_json(manifest_path, manifest)
        write_text(summary_path, self._operation_summary_markdown(manifest))
        return {
            "operation_id": operation_id,
            "run_id": resolved_run_id,
            "manifest_path": str(manifest_path),
            "summary_path": str(summary_path),
            "manifest": manifest,
        }

    def audit_operation_trust(
        self,
        *,
        topic_slug: str,
        run_id: str | None = None,
        updated_by: str = "aitp-cli",
    ) -> dict[str, Any]:
        resolved_run_id = self._resolve_run_id(topic_slug, run_id)
        if not resolved_run_id:
            raise FileNotFoundError(f"Unable to resolve a validation run for topic {topic_slug}")

        operations_root = self._validation_run_root(topic_slug, resolved_run_id) / "operations"
        operations: list[dict[str, Any]] = []
        recommendations: list[str] = []
        for manifest_path in sorted(operations_root.glob("*/operation_manifest.json")):
            manifest = read_json(manifest_path)
            if manifest is None:
                continue
            baseline_ready = self._baseline_status_ready(str(manifest.get("baseline_status", "")))
            atomic_ready = self._atomic_status_ready(str(manifest.get("atomic_understanding_status", "")))
            trust_ready = baseline_ready and atomic_ready
            operation_payload = {
                "operation_id": manifest["operation_id"],
                "title": manifest["title"],
                "kind": manifest["kind"],
                "baseline_status": manifest["baseline_status"],
                "atomic_understanding_status": manifest["atomic_understanding_status"],
                "trust_ready": trust_ready,
                "manifest_path": str(manifest_path),
                "summary_path": str(manifest_path.parent / "operation_summary.md"),
            }
            operations.append(operation_payload)
            if not baseline_ready:
                recommendations.append(
                    f"{manifest['operation_id']} still needs a satisfied numerical baseline before reuse."
                )
            if not atomic_ready:
                recommendations.append(
                    f"{manifest['operation_id']} still needs an atomic-understanding judgment before reuse."
                )

        if not operations:
            overall_status = "missing"
            recommendations.append("No operation manifests were found for this validation run.")
        elif all(operation["trust_ready"] for operation in operations):
            overall_status = "pass"
        else:
            overall_status = "blocked"

        payload = {
            "topic_slug": topic_slug,
            "run_id": resolved_run_id,
            "updated_at": now_iso(),
            "updated_by": updated_by,
            "overall_status": overall_status,
            "operations": operations,
            "recommendations": recommendations,
        }
        trust_audit_path = self._trust_audit_path(topic_slug, resolved_run_id)
        trust_report_path = self._trust_report_path(topic_slug, resolved_run_id)
        write_json(trust_audit_path, payload)
        write_text(trust_report_path, self._trust_report_markdown(payload))
        return {
            **payload,
            "trust_audit_path": str(trust_audit_path),
            "trust_report_path": str(trust_report_path),
        }

    def capability_audit(
        self,
        *,
        topic_slug: str,
        updated_by: str = "aitp-cli",
    ) -> dict[str, Any]:
        runtime_root = self._ensure_runtime_root(topic_slug)
        topic_state = read_json(runtime_root / "topic_state.json")
        latest_run_id = self._resolve_run_id(topic_slug, None)

        runtime_section: dict[str, dict[str, str]] = {}
        for filename in (
            "topic_state.json",
            "resume.md",
            "action_queue.jsonl",
            "agent_brief.md",
            "interaction_state.json",
            "operator_console.md",
            "conformance_state.json",
            "conformance_report.md",
            "runtime_protocol.generated.json",
            "runtime_protocol.generated.md",
            "promotion_gate.json",
            "promotion_gate.md",
            "skill_discovery.json",
            "skill_recommendations.md",
            "loop_state.json",
            "loop_history.jsonl",
        ):
            path = runtime_root / filename
            runtime_section[filename] = {
                "status": "present" if path.exists() else "missing",
                "path": str(path),
            }

        layer_section = {
            "L0": {
                "status": "present" if (self.kernel_root / "source-layer" / "topics" / topic_slug).exists() else "missing",
                "path": str(self.kernel_root / "source-layer" / "topics" / topic_slug),
            },
            "L1": {
                "status": "present" if (self.kernel_root / "intake" / "topics" / topic_slug).exists() else "missing",
                "path": str(self.kernel_root / "intake" / "topics" / topic_slug),
            },
            "L2": {
                "status": "present" if (self.kernel_root / "canonical").exists() else "missing",
                "path": str(self.kernel_root / "canonical"),
            },
            "L3": {
                "status": "present" if (self.kernel_root / "feedback" / "topics" / topic_slug).exists() else "missing",
                "path": str(self.kernel_root / "feedback" / "topics" / topic_slug),
            },
            "L4": {
                "status": "present" if (self.kernel_root / "validation" / "topics" / topic_slug).exists() else "missing",
                "path": str(self.kernel_root / "validation" / "topics" / topic_slug),
            },
            "consultation": {
                "status": "present" if (self.kernel_root / "consultation" / "topics" / topic_slug).exists() else "missing",
                "path": str(self.kernel_root / "consultation" / "topics" / topic_slug),
            },
        }

        integration_section = {
            "aitp": {"status": "present" if shutil.which("aitp") else "missing", "path": shutil.which("aitp") or ""},
            "aitp-mcp": {
                "status": "present" if shutil.which("aitp-mcp") else "missing",
                "path": shutil.which("aitp-mcp") or "",
            },
            "codex": {"status": "present" if shutil.which("codex") else "missing", "path": shutil.which("codex") or ""},
            "mcporter": {
                "status": "present" if shutil.which("mcporter") else "missing",
                "path": shutil.which("mcporter") or "",
            },
            "opencode_config": {
                "status": "present" if (Path.home() / ".config" / "opencode" / "opencode.json").exists() else "missing",
                "path": str(Path.home() / ".config" / "opencode" / "opencode.json"),
            },
        }

        trust_audit_path = (
            self._trust_audit_path(topic_slug, latest_run_id) if latest_run_id else runtime_root / "missing-trust-audit.json"
        )
        capability_specific = {
            "latest_run": {
                "status": "present" if latest_run_id else "missing",
                "detail": latest_run_id or "No latest_run_id is currently recorded.",
            },
            "operation_trust": {
                "status": "present" if latest_run_id and trust_audit_path.exists() else "missing",
                "path": str(trust_audit_path),
            },
            "topic_state_resume_stage": {
                "status": "present" if topic_state else "missing",
                "detail": str(topic_state.get("resume_stage")) if topic_state else "topic_state.json missing",
            },
        }

        recommendations: list[str] = []
        if runtime_section["topic_state.json"]["status"] != "present":
            recommendations.append("Run `aitp bootstrap ...` or `aitp resume ...` to materialize runtime state.")
        if layer_section["L2"]["status"] != "present":
            recommendations.append("Restore `canonical/` so the formal Layer 2 surface exists in this kernel.")
        if runtime_section["conformance_report.md"]["status"] != "present":
            recommendations.append("Run `aitp audit --topic-slug <topic_slug> --phase entry` to restore conformance visibility.")
        if capability_specific["operation_trust"]["status"] != "present" and latest_run_id:
            recommendations.append(
                "Run `aitp trust-audit --topic-slug <topic_slug> --run-id <run_id>` after creating operation manifests."
            )
        if runtime_section["skill_discovery.json"]["status"] != "present":
            recommendations.append("If a capability gap exists, run `aitp loop ... --skill-query ...` to materialize skill discovery.")

        overall_status = "ready"
        if runtime_section["topic_state.json"]["status"] != "present":
            overall_status = "missing_runtime"
        elif layer_section["L2"]["status"] != "present":
            overall_status = "missing_layers"
        elif capability_specific["operation_trust"]["status"] != "present":
            overall_status = "missing_trust"

        payload = {
            "topic_slug": topic_slug,
            "updated_at": now_iso(),
            "updated_by": updated_by,
            "overall_status": overall_status,
            "sections": {
                "runtime": runtime_section,
                "layers": layer_section,
                "integrations": integration_section,
                "capabilities": capability_specific,
            },
            "recommendations": recommendations,
        }
        registry_path = self._capability_registry_path(topic_slug)
        report_path = self._capability_report_path(topic_slug)
        write_json(registry_path, payload)
        write_text(report_path, self._capability_report_markdown(payload))
        return {
            **payload,
            "capability_registry_path": str(registry_path),
            "capability_report_path": str(report_path),
        }

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
            "supporting_regression_question_ids": self._dedupe_strings(
                list(candidate.get("supporting_regression_question_ids") or [])
            ),
            "supporting_oracle_ids": self._dedupe_strings(list(candidate.get("supporting_oracle_ids") or [])),
            "supporting_regression_run_ids": self._dedupe_strings(
                list(candidate.get("supporting_regression_run_ids") or [])
            ),
            "promotion_blockers": self._dedupe_strings(list(candidate.get("promotion_blockers") or [])),
            "split_required": as_bool(candidate.get("split_required")),
            "cited_recovery_required": as_bool(candidate.get("cited_recovery_required")),
            "followup_gap_ids": self._dedupe_strings(list(candidate.get("followup_gap_ids") or [])),
            "merge_outcome": "pending",
            "requested_by": requested_by,
            "requested_at": now_iso(),
            "approved_by": None,
            "approved_at": None,
            "rejected_by": None,
            "rejected_at": None,
            "promoted_by": None,
            "promoted_at": None,
            "promoted_units": [],
            "notes": notes or "",
        }
        paths = self._write_promotion_gate(topic_slug, gate_payload)
        log_path = self._append_promotion_gate_log(
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
    ) -> dict[str, Any]:
        gate_payload = self._load_promotion_gate(topic_slug)
        if gate_payload is None:
            raise FileNotFoundError(f"Promotion gate missing for topic {topic_slug}")
        resolved_run_id = self._resolve_run_id(topic_slug, run_id or str(gate_payload.get("run_id") or ""))
        if not resolved_run_id:
            raise FileNotFoundError(f"Unable to resolve a validation run for topic {topic_slug}")
        if str(gate_payload.get("candidate_id") or "") != candidate_id:
            raise ValueError(f"Promotion gate candidate mismatch: expected {gate_payload.get('candidate_id')}, got {candidate_id}")
        gate_payload["status"] = "approved"
        gate_payload["approved_by"] = approved_by
        gate_payload["approved_at"] = now_iso()
        if notes is not None:
            gate_payload["notes"] = notes
        paths = self._write_promotion_gate(topic_slug, gate_payload)
        log_path = self._append_promotion_gate_log(
            topic_slug,
            resolved_run_id,
            {
                "event": "approved",
                "candidate_id": candidate_id,
                "status": gate_payload["status"],
                "updated_by": approved_by,
                "updated_at": gate_payload["approved_at"],
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
        gate_payload = self._load_promotion_gate(topic_slug)
        if gate_payload is None:
            raise FileNotFoundError(f"Promotion gate missing for topic {topic_slug}")
        resolved_run_id = self._resolve_run_id(topic_slug, run_id or str(gate_payload.get("run_id") or ""))
        if not resolved_run_id:
            raise FileNotFoundError(f"Unable to resolve a validation run for topic {topic_slug}")
        if str(gate_payload.get("candidate_id") or "") != candidate_id:
            raise ValueError(f"Promotion gate candidate mismatch: expected {gate_payload.get('candidate_id')}, got {candidate_id}")
        gate_payload["status"] = "rejected"
        gate_payload["rejected_by"] = rejected_by
        gate_payload["rejected_at"] = now_iso()
        if notes is not None:
            gate_payload["notes"] = notes
        paths = self._write_promotion_gate(topic_slug, gate_payload)
        log_path = self._append_promotion_gate_log(
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
        return {
            **gate_payload,
            **paths,
            "promotion_gate_log_path": log_path,
        }

    def promote_candidate(
        self,
        *,
        topic_slug: str,
        candidate_id: str,
        run_id: str | None = None,
        promoted_by: str = "aitp-cli",
        backend_id: str | None = None,
        target_backend_root: str | None = None,
        domain: str | None = None,
        subdomain: str | None = None,
        source_id: str | None = None,
        source_section: str | None = None,
        source_section_title: str | None = None,
        notes: str | None = None,
        review_mode: str | None = None,
        canonical_layer: str | None = None,
        review_artifact_paths: dict[str, str] | None = None,
        coverage_summary: dict[str, Any] | None = None,
        consensus_summary: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        gate_payload = self._load_promotion_gate(topic_slug)
        if gate_payload is None:
            raise FileNotFoundError(f"Promotion gate missing for topic {topic_slug}")
        if str(gate_payload.get("candidate_id") or "") != candidate_id:
            raise ValueError(f"Promotion gate candidate mismatch: expected {gate_payload.get('candidate_id')}, got {candidate_id}")
        if str(gate_payload.get("status") or "") != "approved":
            raise PermissionError("Layer 2 promotion requires an approved promotion_gate.json status.")

        resolved_run_id = self._resolve_run_id(topic_slug, run_id or str(gate_payload.get("run_id") or ""))
        if not resolved_run_id:
            raise FileNotFoundError(f"Unable to resolve a validation run for topic {topic_slug}")
        candidate = self._load_candidate(topic_slug, resolved_run_id, candidate_id)
        resolved_backend_id = backend_id or str(gate_payload.get("backend_id") or "") or "backend:theoretical-physics-knowledge-network"
        review_mode = review_mode or str(gate_payload.get("review_mode") or "human")
        canonical_layer = canonical_layer or str(gate_payload.get("canonical_layer") or ("L2_auto" if review_mode == "ai_auto" else "L2"))
        tpkn_root, card_path, card_payload = self._resolve_tpkn_root(
            backend_id=resolved_backend_id,
            target_backend_root=target_backend_root or str(gate_payload.get("target_backend_root") or ""),
        )
        if card_payload is None and resolved_backend_id:
            card_path, card_payload = self._load_backend_card(resolved_backend_id)
        mapped_type = map_aitp_candidate_type(str(candidate.get("candidate_type") or ""))
        if not self._backend_supports_candidate_type(card_payload, str(candidate.get("candidate_type") or "")):
            raise ValueError(
                f"Backend {resolved_backend_id} does not declare support for candidate type {candidate.get('candidate_type')}"
            )
        source_rows = read_jsonl(self.kernel_root / "source-layer" / "topics" / topic_slug / "source_index.jsonl")
        source_row = choose_source_row(source_rows=source_rows, candidate=candidate)
        resolved_source_id = source_id or str((source_row or {}).get("source_id") or "") or f"source:{slugify(candidate_id)}"
        resolved_source_section = source_section or "aitp/promoted-candidate"
        resolved_source_section_title = source_section_title or str(candidate.get("title") or candidate_id)

        default_domain = slugify(domain or topic_slug).replace("-", "-")
        default_subdomain = slugify(subdomain or mapped_type).replace("-", "-")
        collision_rows = find_collision_rows(
            tpkn_root=tpkn_root,
            candidate_title=str(candidate.get("title") or ""),
            candidate_summary=str(candidate.get("summary") or ""),
            candidate_tags=[
                str(candidate.get("candidate_type") or ""),
                str(candidate.get("topic_slug") or ""),
            ],
            candidate_aliases=[],
            domain=default_domain,
            target_type=mapped_type,
        )
        context_ref = {
            "id": candidate_id,
            "layer": "L3",
            "object_type": "candidate",
            "path": self._relativize(self._candidate_ledger_path(topic_slug, resolved_run_id)),
            "title": str(candidate.get("title") or candidate_id),
            "summary": str(candidate.get("summary") or ""),
        }
        retrieved_refs = [
            {
                "id": str(row.get("id") or ""),
                "layer": "L2",
                "object_type": f"tpkn_{row.get('type') or 'unit'}",
                "path": str(row.get("path") or ""),
                "title": str(row.get("title") or row.get("id") or ""),
                "summary": str(row.get("summary") or ""),
            }
            for row in collision_rows
        ]

        requested_unit_id = derive_tpkn_unit_id(candidate, mapped_type)
        existing_tpkn_ids = {str(row.get("id") or "") for row in load_unit_index_rows(tpkn_root)}
        merge_target = choose_merge_target(
            collision_rows=collision_rows,
            requested_unit_id=requested_unit_id,
            candidate_title=str(candidate.get("title") or ""),
            target_type=mapped_type,
        )
        equivalence_refs = [
            str(row.get("id") or "")
            for row in collision_rows
            if str(row.get("id") or "") and str(row.get("id") or "") != str((merge_target or {}).get("id") or "")
        ]
        target_unit_id = str((merge_target or {}).get("id") or requested_unit_id)
        merge_outcome = "merged_existing" if merge_target else ("created_with_neighbors" if equivalence_refs else "created_new")
        merge_lineage = {
            "strategy": merge_outcome,
            "candidate_id": candidate_id,
            "collision_scan_count": len(collision_rows),
            "selected_match_id": str((merge_target or {}).get("id") or ""),
        }
        packet_paths = self._theory_packet_paths(topic_slug, resolved_run_id, candidate_id)
        gate_path_json = self._promotion_gate_paths(topic_slug)["json"]
        review_artifacts_payload = dict(review_artifact_paths or {})
        review_artifacts_payload.setdefault("candidate_id", candidate_id)
        review_artifacts_payload.setdefault("promotion_gate_path", self._relativize(gate_path_json))
        if packet_paths["regression_gate"].exists():
            review_artifacts_payload.setdefault("regression_gate_path", self._relativize(packet_paths["regression_gate"]))
        if packet_paths["merge_report"].exists():
            review_artifacts_payload.setdefault("merge_report_path", self._relativize(packet_paths["merge_report"]))
        regression_summary = read_json(packet_paths["regression_gate"]) or {
            "status": str(gate_payload.get("regression_gate_status") or "not_audited"),
            "topic_completion_status": str(
                candidate.get("topic_completion_status") or gate_payload.get("topic_completion_status") or "not_assessed"
            ),
            "supporting_regression_question_ids": self._dedupe_strings(
                list(candidate.get("supporting_regression_question_ids") or gate_payload.get("supporting_regression_question_ids") or [])
            ),
            "supporting_oracle_ids": self._dedupe_strings(
                list(candidate.get("supporting_oracle_ids") or gate_payload.get("supporting_oracle_ids") or [])
            ),
            "supporting_regression_run_ids": self._dedupe_strings(
                list(candidate.get("supporting_regression_run_ids") or gate_payload.get("supporting_regression_run_ids") or [])
            ),
            "promotion_blockers": self._dedupe_strings(
                list(candidate.get("promotion_blockers") or gate_payload.get("promotion_blockers") or [])
            ),
            "split_clearance_status": "blocked" if as_bool(candidate.get("split_required")) else "clear",
            "promotion_blockers_cleared": not (
                list(candidate.get("promotion_blockers") or []) or as_bool(candidate.get("cited_recovery_required"))
            ),
        }

        incoming_unit_payload = build_tpkn_unit(
            candidate=candidate,
            unit_id=target_unit_id,
            target_type=mapped_type,
            domain=default_domain,
            subdomain=default_subdomain,
            source_id=resolved_source_id,
            source_section=resolved_source_section,
            source_anchor_notes=(
                f"AITP promoted candidate {candidate_id} from topic {topic_slug}; "
                + (
                    "keep upstream auto-adjudication artifacts for full provenance."
                    if review_mode == "ai_auto"
                    else "keep upstream validation and approval artifacts for full provenance."
                )
            ),
            existing_tpkn_ids=existing_tpkn_ids,
            canonical_layer=canonical_layer,
            review_mode=review_mode,
            promotion_route=str(gate_payload.get("route") or "L3->L4->L2"),
            review_artifacts=review_artifacts_payload,
            coverage=coverage_summary,
            consensus=consensus_summary,
            regression_gate=regression_summary,
            merge_lineage=merge_lineage,
            conflict_status="none",
            equivalence_refs=equivalence_refs,
        )
        unit_path = unit_path_for(tpkn_root, mapped_type, target_unit_id)
        if merge_target and unit_path.exists():
            existing_payload = read_json(unit_path)
            if existing_payload is None:
                raise FileNotFoundError(f"Existing merge target is missing on disk: {unit_path}")
            unit_payload = merge_tpkn_unit(existing_unit=existing_payload, incoming_unit=incoming_unit_payload)
        else:
            unit_payload = incoming_unit_payload

        manifest_path, created_manifest = ensure_source_manifest(
            tpkn_root=tpkn_root,
            source_row=source_row,
            source_id=resolved_source_id,
            source_section=resolved_source_section,
            source_section_title=resolved_source_section_title,
            source_section_summary=str(candidate.get("summary") or resolved_source_section_title),
        )
        merge_report = {
            "candidate_id": candidate_id,
            "target_unit_id": target_unit_id,
            "target_unit_type": mapped_type,
            "merge_outcome": merge_outcome,
            "requested_unit_id": requested_unit_id,
            "selected_collision": merge_target or {},
            "collision_rows": collision_rows,
            "equivalence_refs": equivalence_refs,
            "review_mode": review_mode,
            "canonical_layer": canonical_layer,
            "updated_at": now_iso(),
            "updated_by": promoted_by,
        }
        write_json(packet_paths["merge_report"], merge_report)
        write_external_json(unit_path, unit_payload)
        check_results = run_tpkn_checks(tpkn_root)

        consultation_paths = self._record_l2_consultation(
            topic_slug=topic_slug,
            stage="L4",
            run_id=resolved_run_id,
            consultation_slug=f"tpkn-promotion-{slugify(candidate_id)}",
            context_ref=context_ref,
            purpose="Consult the external formal-theory backend before L2 promotion to detect collisions and keep writeback explicit.",
            query_text=(
                f"Check TPKN collisions and source-anchor compatibility before promoting {candidate_id} "
                f"as {mapped_type}:{target_unit_id.split(':', 1)[-1]}."
            ),
            requested_unit_types=[str(candidate.get("candidate_type") or "")],
            retrieved_refs=retrieved_refs,
            result_summary=(
                f"Found {len(retrieved_refs)} nearby TPKN objects before unit promotion; merge outcome={merge_outcome}."
                if retrieved_refs
                else f"No obvious TPKN collision was found before unit promotion; merge outcome={merge_outcome}."
            ),
            effect_on_work=(
                f"Created or updated `{target_unit_id}` in the configured TPKN backend and recorded the collision scan."
            ),
            outcome="candidate_narrowed" if retrieved_refs else "no_change",
            projection_paths=[
                self._relativize(self._candidate_ledger_path(topic_slug, resolved_run_id)),
                self._relativize(self._promotion_gate_paths(topic_slug)["json"]),
                self._relativize(self._promotion_gate_paths(topic_slug)["note"]),
                self._relativize(packet_paths["merge_report"]),
            ],
            requested_by=promoted_by,
            produced_by=promoted_by,
            written_by=promoted_by,
            retrieval_profile="tpkn-unit-index-and-source-anchor-scan",
        )

        decision_id = f"decision:{slugify(candidate_id)}-tpkn-promotion"
        promoted_at = now_iso()
        decision_row = {
            "decision_id": decision_id,
            "candidate_id": candidate_id,
            "route": str(gate_payload.get("route") or "L3->L4->L2"),
            "verdict": "accepted",
            "promoted_units": [target_unit_id],
            "fallback_targets": [],
            "evidence_refs": self._dedupe_strings(
                [
                    self._relativize(self._candidate_ledger_path(topic_slug, resolved_run_id)),
                    self._relativize(self._promotion_gate_paths(topic_slug)["json"]),
                    self._relativize(Path(consultation_paths["consultation_result_path"])),
                    self._relativize(packet_paths["merge_report"]),
                    str(unit_path),
                    str(manifest_path),
                ]
            ),
            "decided_by": promoted_by,
            "decided_at": promoted_at,
            "review_mode": review_mode,
            "canonical_layer": canonical_layer,
            "coverage_status": str((coverage_summary or {}).get("status") or gate_payload.get("coverage_status") or "not_audited"),
            "consensus_status": str((consensus_summary or {}).get("status") or gate_payload.get("consensus_status") or "not_requested"),
            "regression_gate_status": str(
                regression_summary.get("status") or gate_payload.get("regression_gate_status") or "not_audited"
            ),
            "merge_outcome": merge_outcome,
            "merge_target_unit": str((merge_target or {}).get("id") or ""),
            "reason": notes
            or (
                "Promoted after theory auto-adjudication and an explicit TPKN backend collision scan."
                if review_mode == "ai_auto"
                else "Promoted after explicit human approval and an explicit TPKN backend collision scan."
            ),
        }
        decisions_path = self._validation_run_root(topic_slug, resolved_run_id) / "promotion_decisions.jsonl"
        decision_rows = read_jsonl(decisions_path)
        decision_rows = [row for row in decision_rows if row.get("decision_id") != decision_id]
        decision_rows.append(decision_row)
        write_jsonl(decisions_path, decision_rows)

        updated_candidate = dict(candidate)
        updated_candidate["status"] = "auto_promoted" if review_mode == "ai_auto" else "promoted"
        updated_candidate["promotion_mode"] = review_mode
        updated_candidate["promoted_units"] = [target_unit_id]
        self._replace_candidate_row(topic_slug, resolved_run_id, candidate_id, updated_candidate)

        gate_payload["status"] = "promoted"
        gate_payload["backend_id"] = resolved_backend_id
        gate_payload["target_backend_root"] = str(tpkn_root)
        gate_payload["review_mode"] = review_mode
        gate_payload["canonical_layer"] = canonical_layer
        gate_payload["coverage_status"] = str((coverage_summary or {}).get("status") or gate_payload.get("coverage_status") or "not_audited")
        gate_payload["consensus_status"] = str((consensus_summary or {}).get("status") or gate_payload.get("consensus_status") or "not_requested")
        gate_payload["regression_gate_status"] = str(
            regression_summary.get("status") or gate_payload.get("regression_gate_status") or "not_audited"
        )
        gate_payload["topic_completion_status"] = str(
            regression_summary.get("topic_completion_status") or gate_payload.get("topic_completion_status") or "not_assessed"
        )
        gate_payload["supporting_regression_question_ids"] = self._dedupe_strings(
            list(regression_summary.get("supporting_regression_question_ids") or gate_payload.get("supporting_regression_question_ids") or [])
        )
        gate_payload["supporting_oracle_ids"] = self._dedupe_strings(
            list(regression_summary.get("supporting_oracle_ids") or gate_payload.get("supporting_oracle_ids") or [])
        )
        gate_payload["supporting_regression_run_ids"] = self._dedupe_strings(
            list(regression_summary.get("supporting_regression_run_ids") or gate_payload.get("supporting_regression_run_ids") or [])
        )
        gate_payload["promotion_blockers"] = self._dedupe_strings(
            list(regression_summary.get("promotion_blockers") or gate_payload.get("promotion_blockers") or [])
        )
        gate_payload["split_required"] = bool(
            regression_summary.get("split_required")
            if "split_required" in regression_summary
            else gate_payload.get("split_required")
        )
        gate_payload["cited_recovery_required"] = bool(
            regression_summary.get("cited_recovery_required")
            if "cited_recovery_required" in regression_summary
            else gate_payload.get("cited_recovery_required")
        )
        gate_payload["merge_outcome"] = merge_outcome
        gate_payload["promoted_by"] = promoted_by
        gate_payload["promoted_at"] = promoted_at
        gate_payload["promoted_units"] = [target_unit_id]
        gate_payload["notes"] = notes or gate_payload.get("notes") or ""
        gate_paths = self._write_promotion_gate(topic_slug, gate_payload)
        log_path = self._append_promotion_gate_log(
            topic_slug,
            resolved_run_id,
            {
                "event": "promoted",
                "candidate_id": candidate_id,
                "status": gate_payload["status"],
                "updated_by": promoted_by,
                "updated_at": promoted_at,
                "promoted_units": [target_unit_id],
                "backend_id": resolved_backend_id,
                "target_backend_root": str(tpkn_root),
                "review_mode": review_mode,
                "canonical_layer": canonical_layer,
                "merge_outcome": merge_outcome,
                "notes": gate_payload.get("notes") or "",
            },
        )

        return {
            "topic_slug": topic_slug,
            "run_id": resolved_run_id,
            "candidate_id": candidate_id,
            "backend_id": resolved_backend_id,
            "backend_card_path": str(card_path) if card_path else None,
            "target_backend_root": str(tpkn_root),
            "target_unit_id": target_unit_id,
            "target_unit_path": str(unit_path),
            "source_manifest_path": str(manifest_path),
            "source_manifest_created": created_manifest,
            "promotion_decision_path": str(decisions_path),
            "promotion_gate_log_path": log_path,
            "merge_report_path": str(packet_paths["merge_report"]),
            "merge_outcome": merge_outcome,
            "tpkn_check": check_results["check"],
            "tpkn_build": check_results["build"],
            "consultation": consultation_paths,
            **gate_paths,
        }

    def auto_promote_candidate(
        self,
        *,
        topic_slug: str,
        candidate_id: str,
        run_id: str | None = None,
        promoted_by: str = "aitp-cli",
        backend_id: str | None = None,
        target_backend_root: str | None = None,
        domain: str | None = None,
        subdomain: str | None = None,
        source_id: str | None = None,
        source_section: str | None = None,
        source_section_title: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        resolved_run_id = self._resolve_run_id(topic_slug, run_id)
        if not resolved_run_id:
            raise FileNotFoundError(f"Unable to resolve a validation run for topic {topic_slug}")
        candidate = self._load_candidate(topic_slug, resolved_run_id, candidate_id)
        resolved_backend_id = backend_id or "backend:theoretical-physics-knowledge-network"
        card_path, card_payload = self._load_backend_card(resolved_backend_id)
        if not self._backend_allows_auto_promotion(card_payload):
            raise PermissionError(f"Backend {resolved_backend_id} does not allow auto canonical promotion.")
        if not self._backend_supports_candidate_type(card_payload, str(candidate.get("candidate_type") or "")):
            raise ValueError(
                f"Backend {resolved_backend_id} does not declare support for candidate type {candidate.get('candidate_type')}"
            )

        packet_paths = self._theory_packet_paths(topic_slug, resolved_run_id, candidate_id)
        runtime_policy = self._load_runtime_policy().get("auto_promotion_policy") or {}
        required_paths = tuple(
            str(value).strip()
            for value in (
                runtime_policy.get("required_theory_packet_artifacts")
                or [
                    "structure_map",
                    "coverage_ledger",
                    "notation_table",
                    "derivation_graph",
                    "agent_consensus",
                    "regression_gate",
                ]
            )
            if str(value).strip()
        )
        missing = [name for name in required_paths if not packet_paths[name].exists()]
        if missing:
            raise FileNotFoundError(
                "Missing theory packet artifacts for auto promotion: " + ", ".join(sorted(missing))
            )

        coverage_summary = read_json(packet_paths["coverage_ledger"]) or {}
        consensus_summary = read_json(packet_paths["agent_consensus"]) or {}
        regression_summary = read_json(packet_paths["regression_gate"]) or {}
        structure_map = read_json(packet_paths["structure_map"]) or {}
        notation_table = read_json(packet_paths["notation_table"]) or {}
        derivation_graph = read_json(packet_paths["derivation_graph"]) or {}

        source_policy = (card_payload or {}).get("source_policy") or {}
        if source_policy.get("auto_promotion_requires_coverage_audit") and str(coverage_summary.get("status") or "") != "pass":
            raise PermissionError("Auto promotion requires a passing coverage_ledger.json status.")
        if source_policy.get("auto_promotion_requires_multi_agent_consensus") and str(
            consensus_summary.get("status") or ""
        ) != "ready":
            raise PermissionError("Auto promotion requires a ready agent_consensus.json status.")
        if source_policy.get("auto_promotion_requires_split_clearance") and str(
            regression_summary.get("split_clearance_status") or ""
        ) not in {"clear", "not_applicable"}:
            raise PermissionError("Auto promotion is blocked until split clearance is explicit.")
        if source_policy.get("auto_promotion_requires_gap_honesty"):
            if list(regression_summary.get("promotion_blockers") or []):
                raise PermissionError("Auto promotion is blocked while promotion_blockers remain.")
            if as_bool(regression_summary.get("cited_recovery_required")):
                raise PermissionError("Auto promotion is blocked while cited recovery remains required.")
        if source_policy.get("auto_promotion_requires_regression_gate") and str(
            regression_summary.get("status") or ""
        ) != "pass":
            raise PermissionError("Auto promotion requires a passing regression_gate.json status.")

        gate_payload = {
            "topic_slug": topic_slug,
            "run_id": resolved_run_id,
            "candidate_id": candidate_id,
            "candidate_type": str(candidate.get("candidate_type") or ""),
            "title": str(candidate.get("title") or ""),
            "summary": str(candidate.get("summary") or ""),
            "route": "L3->L4_auto->L2_auto",
            "status": "approved",
            "intended_l2_targets": self._dedupe_strings(list(candidate.get("intended_l2_targets") or [])),
            "backend_id": resolved_backend_id,
            "target_backend_root": str(target_backend_root or ""),
            "review_mode": "ai_auto",
            "canonical_layer": "L2_auto",
            "coverage_status": str(coverage_summary.get("status") or "not_audited"),
            "consensus_status": str(consensus_summary.get("status") or "not_requested"),
            "regression_gate_status": str(regression_summary.get("status") or "not_audited"),
            "topic_completion_status": str(regression_summary.get("topic_completion_status") or "not_assessed"),
            "supporting_regression_question_ids": self._dedupe_strings(
                list(regression_summary.get("supporting_regression_question_ids") or candidate.get("supporting_regression_question_ids") or [])
            ),
            "supporting_oracle_ids": self._dedupe_strings(
                list(regression_summary.get("supporting_oracle_ids") or candidate.get("supporting_oracle_ids") or [])
            ),
            "supporting_regression_run_ids": self._dedupe_strings(
                list(regression_summary.get("supporting_regression_run_ids") or candidate.get("supporting_regression_run_ids") or [])
            ),
            "promotion_blockers": self._dedupe_strings(
                list(regression_summary.get("promotion_blockers") or candidate.get("promotion_blockers") or [])
            ),
            "split_required": as_bool(regression_summary.get("split_required")),
            "cited_recovery_required": as_bool(regression_summary.get("cited_recovery_required")),
            "followup_gap_ids": self._dedupe_strings(
                list(regression_summary.get("followup_gap_ids") or candidate.get("followup_gap_ids") or [])
            ),
            "merge_outcome": "pending",
            "requested_by": promoted_by,
            "requested_at": now_iso(),
            "approved_by": f"{promoted_by}:auto",
            "approved_at": now_iso(),
            "rejected_by": None,
            "rejected_at": None,
            "promoted_by": None,
            "promoted_at": None,
            "promoted_units": [],
            "notes": notes or "",
        }
        gate_paths = self._write_promotion_gate(topic_slug, gate_payload)
        log_path = self._append_promotion_gate_log(
            topic_slug,
            resolved_run_id,
            {
                "event": "auto_approved",
                "candidate_id": candidate_id,
                "status": gate_payload["status"],
                "updated_by": promoted_by,
                "updated_at": gate_payload["approved_at"],
                "backend_id": resolved_backend_id,
                "target_backend_root": gate_payload["target_backend_root"],
                "coverage_status": gate_payload["coverage_status"],
                "consensus_status": gate_payload["consensus_status"],
                "notes": gate_payload["notes"],
            },
        )

        review_artifacts = {
            "structure_map_path": self._relativize(packet_paths["structure_map"]),
            "coverage_ledger_path": self._relativize(packet_paths["coverage_ledger"]),
            "notation_table_path": self._relativize(packet_paths["notation_table"]),
            "derivation_graph_path": self._relativize(packet_paths["derivation_graph"]),
            "agent_consensus_path": self._relativize(packet_paths["agent_consensus"]),
            "regression_gate_path": self._relativize(packet_paths["regression_gate"]),
            "promotion_gate_path": self._relativize(Path(gate_paths["promotion_gate_path"])),
            "candidate_id": candidate_id,
        }
        promote_payload = self.promote_candidate(
            topic_slug=topic_slug,
            candidate_id=candidate_id,
            run_id=resolved_run_id,
            promoted_by=promoted_by,
            backend_id=resolved_backend_id,
            target_backend_root=target_backend_root,
            domain=domain,
            subdomain=subdomain,
            source_id=source_id,
            source_section=source_section,
            source_section_title=source_section_title,
            notes=notes,
            review_mode="ai_auto",
            canonical_layer="L2_auto",
            review_artifact_paths=review_artifacts,
            coverage_summary=coverage_summary,
            consensus_summary=consensus_summary,
        )

        auto_report = {
            "topic_slug": topic_slug,
            "run_id": resolved_run_id,
            "candidate_id": candidate_id,
            "candidate_type": str(candidate.get("candidate_type") or ""),
            "review_mode": "ai_auto",
            "canonical_layer": "L2_auto",
            "backend_id": resolved_backend_id,
            "backend_card_path": str(card_path) if card_path else None,
            "coverage_status": str(coverage_summary.get("status") or ""),
            "consensus_status": str(consensus_summary.get("status") or ""),
            "regression_gate_status": str(regression_summary.get("status") or ""),
            "topic_completion_status": str(regression_summary.get("topic_completion_status") or ""),
            "supporting_regression_question_ids": self._dedupe_strings(
                list(regression_summary.get("supporting_regression_question_ids") or [])
            ),
            "supporting_oracle_ids": self._dedupe_strings(list(regression_summary.get("supporting_oracle_ids") or [])),
            "supporting_regression_run_ids": self._dedupe_strings(
                list(regression_summary.get("supporting_regression_run_ids") or [])
            ),
            "promotion_blockers": self._dedupe_strings(list(regression_summary.get("promotion_blockers") or [])),
            "structure_section_count": len(structure_map.get("sections") or []),
            "notation_binding_count": len(notation_table.get("bindings") or []),
            "derivation_node_count": len(derivation_graph.get("nodes") or []),
            "derivation_edge_count": len(derivation_graph.get("edges") or []),
            "merge_outcome": str(promote_payload.get("merge_outcome") or ""),
            "target_unit_id": str(promote_payload.get("target_unit_id") or ""),
            "target_unit_path": str(promote_payload.get("target_unit_path") or ""),
            "updated_at": now_iso(),
            "updated_by": promoted_by,
            "notes": notes or "",
        }
        write_json(packet_paths["auto_promotion_report"], auto_report)

        return {
            **promote_payload,
            "auto_promotion_report_path": str(packet_paths["auto_promotion_report"]),
            "auto_promotion_report": auto_report,
            "auto_promotion_gate_log_path": log_path,
        }

    def run_topic_loop(
        self,
        *,
        topic_slug: str | None = None,
        topic: str | None = None,
        statement: str | None = None,
        run_id: str | None = None,
        control_note: str | None = None,
        updated_by: str = "aitp-cli",
        human_request: str | None = None,
        skill_queries: list[str] | None = None,
        max_auto_steps: int = 4,
        research_mode: str | None = None,
    ) -> dict[str, Any]:
        if not topic_slug and not topic:
            raise ValueError("Provide topic_slug or topic.")

        bootstrap = self.orchestrate(
            topic_slug=topic_slug,
            topic=topic,
            statement=statement,
            run_id=run_id,
            control_note=control_note,
            updated_by=updated_by,
            human_request=human_request,
            skill_queries=skill_queries or [],
            research_mode=research_mode,
        )
        resolved_topic_slug = bootstrap["topic_slug"]
        resolved_run_id = self._resolve_run_id(resolved_topic_slug, run_id)

        entry_audit = self.audit(topic_slug=resolved_topic_slug, phase="entry", updated_by=updated_by)
        executed_auto_actions: list[dict[str, Any]] = []
        auto_queue_path = str(self._runtime_root(resolved_topic_slug) / "action_queue.jsonl")
        remaining_pending = 0
        remaining_budget = max_auto_steps
        while remaining_budget > 0:
            auto_step = self._execute_auto_actions(
                topic_slug=resolved_topic_slug,
                updated_by=updated_by,
                max_auto_steps=1,
                default_skill_queries=skill_queries,
            )
            auto_queue_path = auto_step["queue_path"]
            remaining_pending = auto_step["remaining_pending"]
            if not auto_step["executed"]:
                break
            executed_auto_actions.extend(auto_step["executed"])
            remaining_budget -= 1
            if any(step.get("status") != "completed" for step in auto_step["executed"]):
                break
            if remaining_budget <= 0:
                break
            self.orchestrate(
                topic_slug=resolved_topic_slug,
                run_id=resolved_run_id,
                control_note=control_note,
                updated_by=updated_by,
                skill_queries=skill_queries or [],
                human_request=human_request,
                research_mode=research_mode,
            )
        auto_actions = {
            "queue_path": auto_queue_path,
            "executed": executed_auto_actions,
            "remaining_pending": remaining_pending,
        }
        capability = self.capability_audit(topic_slug=resolved_topic_slug, updated_by=updated_by)
        trust = None
        if resolved_run_id:
            try:
                trust = self.audit_operation_trust(
                    topic_slug=resolved_topic_slug,
                    run_id=resolved_run_id,
                    updated_by=updated_by,
                )
            except FileNotFoundError:
                trust = None
        exit_audit = self.audit(topic_slug=resolved_topic_slug, phase="exit", updated_by=updated_by)

        loop_state = {
            "topic_slug": resolved_topic_slug,
            "run_id": resolved_run_id,
            "updated_at": now_iso(),
            "updated_by": updated_by,
            "human_request": human_request or "",
            "max_auto_steps": max_auto_steps,
            "bootstrap_runtime_root": bootstrap["runtime_root"],
            "entry_conformance": (entry_audit.get("conformance_state") or {}).get("overall_status"),
            "exit_conformance": (exit_audit.get("conformance_state") or {}).get("overall_status"),
            "capability_status": capability.get("overall_status"),
            "trust_status": trust.get("overall_status") if trust else "missing",
            "promotion_gate_status": str((self._load_promotion_gate(resolved_topic_slug) or {}).get("status") or "not_requested"),
            "auto_actions_executed": auto_actions["executed"],
            "remaining_pending_actions": auto_actions["remaining_pending"],
        }
        loop_state_path = self._loop_state_path(resolved_topic_slug)
        loop_history_path = self._loop_history_path(resolved_topic_slug)
        write_json(loop_state_path, loop_state)
        history_rows = read_jsonl(loop_history_path)
        history_rows.append(loop_state)
        write_jsonl(loop_history_path, history_rows)
        protocol_paths = self._materialize_runtime_protocol_bundle(
            topic_slug=resolved_topic_slug,
            updated_by=updated_by,
            human_request=human_request,
        )
        return {
            "topic_slug": resolved_topic_slug,
            "run_id": resolved_run_id,
            "bootstrap": bootstrap,
            "entry_audit": entry_audit,
            "auto_actions": auto_actions,
            "capability_audit": capability,
            "trust_audit": trust,
            "exit_audit": exit_audit,
            "loop_state_path": str(loop_state_path),
            "loop_history_path": str(loop_history_path),
            "loop_state": loop_state,
            "runtime_protocol": protocol_paths,
        }

    def _codex_skill_template(self) -> str:
        return f"""---
name: aitp-runtime
description: Route research work through the AITP kernel using the installable `aitp` CLI. Use when the task should follow the AITP layer architecture instead of ad hoc browsing.
---

# AITP Runtime

## Required entry

1. In a bare `codex` research session, do not start with direct browsing or free-form synthesis; enter through `aitp loop ...`, `aitp resume ...`, or `aitp bootstrap ...` first.
2. For Codex-driven implementation or execution work inside an active topic, prefer `aitp-codex --topic-slug <topic_slug> "<task>"`.
3. Read `runtime_protocol.generated.md` first, then the files listed under `Must read now`.
4. Expand promotion, consultation, capability, or queue details only when the named trigger in the runtime bundle fires.
5. Register reusable operations with `aitp operation-init ...`.
6. For human-reviewed `L2`, use `aitp request-promotion ...` and wait for `aitp approve-promotion ...`.
7. For theory-formal `L2_auto`, materialize coverage/consensus artifacts with `aitp coverage-audit ...` and then use `aitp auto-promote ...`.
8. End with `aitp audit --topic-slug <topic_slug> --phase exit`.

## Hard rules

- If the conformance audit fails, the run does not count as AITP work.
- If the task is theoretical-physics research rather than plain coding, staying inside AITP is mandatory.
- Prefer durable control notes and contract files over Python heuristic defaults.
- Every reusable operation must pass through `aitp trust-audit ...` before AITP treats it as trusted.
- If a new numerical backend or diagnostic is being trusted, scaffold a baseline first with `aitp baseline ...`.
- If a derivation-heavy method is being claimed as understood, scaffold atomic understanding first with `aitp atomize ...`.
- If there is a capability gap, prefer `aitp loop ... --skill-query ...` so discovery becomes runtime state instead of ad hoc browsing.
- Human-reviewed Layer 2 promotion is blocked until `promotion_gate.json` says `approved` and `aitp promote ...` records the writeback.
- Theory-formal `L2_auto` promotion is blocked until `coverage_ledger.json` passes and `agent_consensus.json` is ready.

## Common commands

```bash
aitp-codex --topic-slug <topic_slug> "<task>"
aitp loop --topic-slug <topic_slug> --human-request "<task>" --skill-query "<capability gap>"
aitp resume --topic-slug <topic_slug> --human-request "<task>"
aitp coverage-audit --topic-slug <topic_slug> --candidate-id <candidate_id> --source-section <section> --covered-section <section>
aitp request-promotion --topic-slug <topic_slug> --candidate-id <candidate_id> --backend-id backend:theoretical-physics-knowledge-network
aitp approve-promotion --topic-slug <topic_slug> --candidate-id <candidate_id>
aitp promote --topic-slug <topic_slug> --candidate-id <candidate_id> --target-backend-root <tpkn_root>
aitp auto-promote --topic-slug <topic_slug> --candidate-id <candidate_id> --target-backend-root <tpkn_root>
aitp operation-init --topic-slug <topic_slug> --run-id <run_id> --title "<operation>" --kind numerical
aitp operation-update --topic-slug <topic_slug> --run-id <run_id> --operation "<operation>" --baseline-status passed
aitp trust-audit --topic-slug <topic_slug> --run-id <run_id>
aitp capability-audit --topic-slug <topic_slug>
aitp audit --topic-slug <topic_slug> --phase exit
aitp baseline --topic-slug <topic_slug> --run-id <run_id> --title "<baseline title>" --reference "<source>" --agreement-criterion "<criterion>"
aitp atomize --topic-slug <topic_slug> --run-id <run_id> --method-title "<method title>"
```

Kernel root default: `{self.kernel_root}`
"""

    def _claude_code_skill_template(self) -> str:
        return f"""---
name: aitp-runtime
description: Route Claude Code through the AITP runtime so substantial research work stays auditable, resumable, and conformance-checked.
---

# AITP Runtime For Claude Code

## Required entry

1. Start topic work with `aitp loop ...` when possible.
2. Use `aitp bootstrap ...` only to create a new topic, then return to `aitp loop ...`.
3. Read `runtime_protocol.generated.md` first, then follow its `Must read now` list before deeper work.
4. Expand deferred surfaces only when the named trigger fires.
5. Treat missing conformance as a hard failure for AITP work.
6. Close with `aitp audit --topic-slug <topic_slug> --phase exit`.

## Hard rules

- Charter first, adapter second.
- Contracts before hidden heuristics.
- Do not silently upgrade exploratory output into reusable knowledge.
- Use `aitp baseline ...`, `aitp atomize ...`, and `aitp trust-audit ...` before claiming method reuse.

Kernel root default: `{self.kernel_root}`
"""

    def _openclaw_skill_template(self) -> str:
        return f"""---
name: aitp-runtime
description: Enter the AITP kernel from OpenClaw using the `aitp` CLI and `mcporter` bridge so the run stays auditable, resumable, and conformance-checked.
---

# AITP Runtime For OpenClaw

Use this skill when the task belongs inside AITP rather than a free-form note workflow.

## Start here

```bash
aitp loop --topic-slug <topic_slug> --human-request "<task>"
```

Then read `runtime/topics/<topic_slug>/runtime_protocol.generated.md` and follow its `Must read now` and `Escalate only when triggered` sections before acting on the queue. Do not bypass the loop and jump straight into ad hoc browsing or execution.

If the topic does not exist yet:

```bash
aitp bootstrap --topic "<topic>" --statement "<statement>"
```

## Before finishing

```bash
aitp audit --topic-slug <topic_slug> --phase exit
```

## Structured tool path

If you need the structured AITP MCP tool surface from OpenClaw, use the `aitp`
server registered in `mcporter`.

## Trust gates

- Reusable operations require `aitp operation-init ...` and `aitp trust-audit ...`
- Numerical novelty requires `aitp baseline ...`
- Theory-method understanding requires `aitp atomize ...`
- Human-reviewed Layer 2 promotion requires `aitp request-promotion ...`, a human `aitp approve-promotion ...`, and only then `aitp promote ...`
- Theory-formal `L2_auto` promotion requires `aitp coverage-audit ...` and then `aitp auto-promote ...`

Kernel root default: `{self.kernel_root}`
"""

    def _opencode_harness_template(self) -> str:
        return """# AITP Command Harness

These OpenCode commands route work through the installed `aitp` CLI instead of
letting topic work drift into ad hoc file browsing.

Required pattern:

1. enter through `aitp loop` whenever the topic already exists
2. use `aitp bootstrap` only to create a new topic shell, then return to `aitp loop`
3. read `runtime_protocol.generated.md` first, then follow `Must read now`
4. expand deferred surfaces only when the named trigger in the runtime bundle fires
5. register reusable operations with `aitp operation-init`
6. do the actual work
7. request human approval before any human-reviewed `L2` promotion with `aitp request-promotion ...`
8. for theory-formal `L2_auto`, materialize `coverage-audit` artifacts before `aitp auto-promote ...`
9. close with `aitp audit --phase exit`

If method trust is missing:

- use `aitp baseline ...` for numerical backends
- use `aitp atomize ...` for theory-method understanding
- use `aitp trust-audit ...` before reusing an operation as if it were established
"""

    def _opencode_command_template(self, name: str) -> str:
        if name == "aitp":
            body = """---
description: Enter the AITP kernel for a new or existing research task
subtask: false
---
# aitp Command

Before doing substantial work, read `./AITP_COMMAND_HARNESS.md`.

User request: $ARGUMENTS

1. If the topic already exists, run `aitp loop --topic-slug <topic_slug> --human-request "$ARGUMENTS"`.
2. If the topic is new, run `aitp bootstrap --topic "<topic>" --statement "$ARGUMENTS"` and then `aitp loop --topic-slug <topic_slug> --human-request "$ARGUMENTS"`.
3. Read `runtime_protocol.generated.md` first, then follow `Must read now`.
4. Expand deferred surfaces only when the named trigger in `runtime_protocol.generated.md` fires.
5. If the work is heading toward human-reviewed `L2`, use `aitp request-promotion ...` and wait for a durable approval gate.
6. If the work is heading toward theory-formal `L2_auto`, use `aitp coverage-audit ...` before `aitp auto-promote ...`.
7. Continue the task only after the runtime artifacts exist and conformance passes.
"""
        elif name == "aitp-resume":
            body = """---
description: Resume an existing AITP topic from the installable aitp CLI
subtask: false
---
# aitp-resume Command

Before doing substantial work, read `./AITP_COMMAND_HARNESS.md`.

Arguments: $ARGUMENTS

Run:

```bash
aitp resume $ARGUMENTS
```

Then read `runtime_protocol.generated.md` first, follow `Must read now`, and only expand deferred surfaces when the named trigger fires.
"""
        elif name == "aitp-loop":
            body = """---
description: Run the safe AITP auto-continue loop for an active topic
subtask: false
---
# aitp-loop Command

Before doing substantial work, read `./AITP_COMMAND_HARNESS.md`.

Arguments: $ARGUMENTS

Run:

```bash
aitp loop $ARGUMENTS
```

Then read `runtime_protocol.generated.md` first, follow `Must read now`, and only expand deferred surfaces when the named trigger fires.
Inspect `loop_state.json` after the runtime contract if you need loop-exit status.
If the loop surfaces a promotion-ready candidate, use `aitp request-promotion ...` for human-reviewed `L2`, or `aitp coverage-audit ...` before `aitp auto-promote ...` for theory-formal `L2_auto`.
"""
        else:
            body = """---
description: Run the AITP conformance audit for the active topic
subtask: false
---
# aitp-audit Command

Before doing substantial work, read `./AITP_COMMAND_HARNESS.md`.

Arguments: $ARGUMENTS

Run:

```bash
aitp audit $ARGUMENTS
```
"""
        return body

    def _claude_code_command_template(self, name: str) -> str:
        if name == "aitp":
            body = """---
description: Enter the AITP runtime for a Claude Code research task
---
# aitp Command

Arguments: $ARGUMENTS

1. If the topic exists, run `aitp loop --topic-slug <topic_slug> --human-request "$ARGUMENTS"`.
2. If the topic is new, run `aitp bootstrap --topic "<topic>" --statement "$ARGUMENTS"` and then `aitp loop --topic-slug <topic_slug> --human-request "$ARGUMENTS"`.
3. Read `runtime_protocol.generated.md` first, then follow `Must read now`.
4. Expand deferred surfaces only when the named trigger fires.
5. Request human approval before any Layer 2 promotion.
"""
        elif name == "aitp-loop":
            body = """---
description: Run the bounded AITP loop inside Claude Code
---
# aitp-loop Command

Arguments: $ARGUMENTS

Run:

```bash
aitp loop $ARGUMENTS
```

Then read `runtime_protocol.generated.md` first, follow `Must read now`, and only expand deferred surfaces when the named trigger fires.
Inspect `loop_state.json` after the runtime contract if you need loop-exit status.
If the result should enter Layer 2, run `aitp request-promotion ...` first.
"""
        else:
            body = """---
description: Run the AITP conformance audit inside Claude Code
---
# aitp-audit Command

Arguments: $ARGUMENTS

Run:

```bash
aitp audit $ARGUMENTS
```
"""
        return body

    def install_agent(
        self,
        *,
        agent: str,
        scope: str = "user",
        target_root: str | None = None,
        force: bool = True,
        install_mcp: bool = True,
    ) -> dict[str, Any]:
        agent = agent.lower()
        installed: list[dict[str, str]] = []
        targets = [agent] if agent != "all" else ["codex", "openclaw", "opencode", "claude-code"]

        for target in targets:
            resolved_target_root = target_root
            if agent == "all" and target_root:
                resolved_target_root = str(Path(target_root) / target)
            installed.extend(
                self._install_one_agent(
                    target,
                    scope=scope,
                    target_root=resolved_target_root,
                    force=force,
                    install_mcp=install_mcp,
                )
            )

        return {
            "agent": agent,
            "scope": scope,
            "installed": installed,
        }

    def _install_one_agent(
        self,
        agent: str,
        *,
        scope: str,
        target_root: str | None,
        force: bool,
        install_mcp: bool,
    ) -> list[dict[str, str]]:
        home = Path.home()
        installed: list[dict[str, str]] = []

        if agent == "codex":
            for base in self._codex_skill_targets(scope=scope, target_root=target_root):
                base.mkdir(parents=True, exist_ok=True)
                skill_path = base / "SKILL.md"
                if skill_path.exists() and not force:
                    raise FileExistsError(f"Refusing to overwrite {skill_path}")
                write_text(skill_path, self._codex_skill_template())
                installed.append({"agent": agent, "path": str(skill_path), "kind": "skill"})

                if target_root or scope == "project":
                    setup_path = base / "AITP_MCP_SETUP.md"
                    write_text(setup_path, self._codex_mcp_setup_markdown())
                    installed.append({"agent": agent, "path": str(setup_path), "kind": "mcp-setup"})

            if install_mcp and not target_root and scope == "user":
                installed.extend(self._install_codex_mcp(force=force))
            return installed

        if agent == "openclaw":
            base = (
                Path(target_root)
                if target_root
                else (home / ".openclaw" / "skills" / "aitp-runtime" if scope == "user" else self.repo_root / "skills" / "aitp-runtime")
            )
            base.mkdir(parents=True, exist_ok=True)
            skill_path = base / "SKILL.md"
            if skill_path.exists() and not force:
                raise FileExistsError(f"Refusing to overwrite {skill_path}")
            write_text(skill_path, self._openclaw_skill_template())
            installed.append({"agent": agent, "path": str(skill_path), "kind": "skill"})

            if target_root or scope == "project":
                setup_path = base / "AITP_MCP_SETUP.md"
                write_text(setup_path, self._openclaw_mcp_setup_markdown(scope=scope))
                installed.append({"agent": agent, "path": str(setup_path), "kind": "mcp-setup"})

            if install_mcp and not target_root:
                installed.extend(self._install_openclaw_mcp(force=force, scope=scope))
            return installed

        if agent == "opencode":
            base = (
                Path(target_root)
                if target_root
                else (home / ".config" / "opencode" / "commands" if scope == "user" else self.repo_root / ".opencode" / "commands")
            )
            base.mkdir(parents=True, exist_ok=True)
            harness_path = base / "AITP_COMMAND_HARNESS.md"
            if harness_path.exists() and not force:
                raise FileExistsError(f"Refusing to overwrite {harness_path}")
            write_text(harness_path, self._opencode_harness_template())
            installed.append({"agent": agent, "path": str(harness_path), "kind": "command-harness"})
            for command_name in ("aitp", "aitp-resume", "aitp-loop", "aitp-audit"):
                command_path = base / f"{command_name}.md"
                if command_path.exists() and not force:
                    raise FileExistsError(f"Refusing to overwrite {command_path}")
                write_text(command_path, self._opencode_command_template(command_name))
                installed.append({"agent": agent, "path": str(command_path), "kind": "command"})

            if install_mcp:
                installed.extend(self._install_opencode_mcp(force=force, scope=scope, target_root=target_root))
            return installed

        if agent == "claude-code":
            if target_root:
                target_base = Path(target_root)
                skill_base = target_base / "skills" / "aitp-runtime"
                command_base = target_base / "commands"
            elif scope == "user":
                target_base = home / ".claude"
                skill_base = target_base / "skills" / "aitp-runtime"
                command_base = target_base / "commands"
            else:
                target_base = self.repo_root / ".claude"
                skill_base = target_base / "skills" / "aitp-runtime"
                command_base = target_base / "commands"

            skill_base.mkdir(parents=True, exist_ok=True)
            command_base.mkdir(parents=True, exist_ok=True)

            skill_path = skill_base / "SKILL.md"
            if skill_path.exists() and not force:
                raise FileExistsError(f"Refusing to overwrite {skill_path}")
            write_text(skill_path, self._claude_code_skill_template())
            installed.append({"agent": agent, "path": str(skill_path), "kind": "skill"})

            for command_name in ("aitp", "aitp-loop", "aitp-audit"):
                command_path = command_base / f"{command_name}.md"
                if command_path.exists() and not force:
                    raise FileExistsError(f"Refusing to overwrite {command_path}")
                write_text(command_path, self._claude_code_command_template(command_name))
                installed.append({"agent": agent, "path": str(command_path), "kind": "command"})

            setup_path = skill_base / "AITP_MCP_SETUP.md"
            if setup_path.exists() and not force:
                raise FileExistsError(f"Refusing to overwrite {setup_path}")
            write_text(
                setup_path,
                "Register an `aitp` MCP server pointing to `aitp-mcp` in your Claude Code config if you want structured tool access.\n",
            )
            installed.append({"agent": agent, "path": str(setup_path), "kind": "mcp-setup"})
            return installed

        raise ValueError(f"Unsupported agent: {agent}")

    def ensure_cli_installed(self) -> dict[str, Any]:
        command_path = shutil.which("aitp")
        mcp_path = shutil.which("aitp-mcp")
        codex_path = shutil.which("codex")
        mcporter_path = shutil.which("mcporter")
        opencode_config = Path.home() / ".config" / "opencode" / "opencode.json"
        opencode_has_aitp = False
        if opencode_config.exists():
            try:
                opencode_payload = json.loads(opencode_config.read_text(encoding="utf-8"))
                opencode_has_aitp = bool(opencode_payload.get("mcp", {}).get("aitp"))
            except json.JSONDecodeError:
                opencode_has_aitp = False
        layer_roots = {
            "L0": str(self.kernel_root / "source-layer"),
            "L1": str(self.kernel_root / "intake"),
            "L2": str(self.kernel_root / "canonical"),
            "L3": str(self.kernel_root / "feedback"),
            "L4": str(self.kernel_root / "validation"),
            "consultation": str(self.kernel_root / "consultation"),
            "runtime": str(self.kernel_root / "runtime"),
            "schemas": str(self.kernel_root / "schemas"),
        }
        layer_status = {
            name: {"path": path, "status": "present" if Path(path).exists() else "missing"}
            for name, path in layer_roots.items()
        }
        contract_paths = {
            "layer_map": self.kernel_root / "LAYER_MAP.md",
            "routing_policy": self.kernel_root / "ROUTING_POLICY.md",
            "communication_contract": self.kernel_root / "COMMUNICATION_CONTRACT.md",
            "autonomy_operator_model": self.kernel_root / "AUTONOMY_AND_OPERATOR_MODEL.md",
            "l2_consultation_protocol": self.kernel_root / "L2_CONSULTATION_PROTOCOL.md",
            "research_execution_guardrails": self.kernel_root / "RESEARCH_EXECUTION_GUARDRAILS.md",
            "proof_obligation_protocol": self.kernel_root / "PROOF_OBLIGATION_PROTOCOL.md",
            "gap_recovery_protocol": self.kernel_root / "GAP_RECOVERY_PROTOCOL.md",
            "family_fusion_protocol": self.kernel_root / "FAMILY_FUSION_PROTOCOL.md",
            "verification_bridge_protocol": self.kernel_root / "VERIFICATION_BRIDGE_PROTOCOL.md",
            "indexing_rules": self.kernel_root / "INDEXING_RULES.md",
            "l0_source_layer": self.kernel_root / "L0_SOURCE_LAYER.md",
        }
        return {
            "aitp": command_path,
            "aitp_mcp": mcp_path,
            "codex": codex_path,
            "mcporter": mcporter_path,
            "kernel_root": str(self.kernel_root),
            "repo_root": str(self.repo_root),
            "opencode_has_aitp_mcp": opencode_has_aitp,
            "layer_roots": layer_status,
            "protocol_contracts": {
                name: {"path": str(path), "status": "present" if path.exists() else "missing"}
                for name, path in contract_paths.items()
            },
        }
