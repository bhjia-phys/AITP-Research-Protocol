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
from urllib.parse import urlparse

from .decision_point_handler import get_all_decision_points, list_pending_decision_points
from .decision_trace_handler import get_decision_traces
from .runtime_projection_handler import (
    build_knowledge_packets_from_candidates,
    write_l0_sources_projection,
    write_l1_understanding_projection,
    write_l2_memory_projection,
    write_l3_analysis_projection,
    write_l3_distillation_projection,
    write_l3_result_integration_projection,
    write_l4_validation_projection,
    write_pending_decisions_projection,
    write_promotion_readiness_projection,
    write_promotion_trace,
    write_topic_skill_projection,
    write_topic_synopsis,
)
from .l2_graph import (
    consult_canonical_l2 as consult_canonical_l2_graph,
    materialize_canonical_index as materialize_canonical_l2_index,
    seed_l2_demo_direction as seed_l2_demo_graph_direction,
    stage_l2_insight as stage_l2_graph_insight,
)
from .tpkn_bridge import (
    build_supporting_question_oracle_unit,
    build_supporting_regression_question_unit,
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
from .semantic_routing import (
    canonical_lane,
    canonical_template_mode,
    canonical_validation_mode,
)


def _looks_like_repo_root(path: Path) -> bool:
    return (
        (path / "AGENTS.md").exists()
        and (path / "docs" / "CHARTER.md").exists()
        and (path / "research" / "knowledge-hub" / "setup.py").exists()
    )


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


def write_executable_text(path: Path, text: str) -> None:
    write_text(path, text)
    try:
        path.chmod(path.stat().st_mode | 0o111)
    except OSError:
        pass


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

    def _runtime_pythonpath(self) -> str:
        entries = [str(self.kernel_root)]
        existing = os.environ.get("PYTHONPATH", "")
        if existing:
            entries.extend(part for part in existing.split(os.pathsep) if part)

        deduped: list[str] = []
        seen: set[str] = set()
        for entry in entries:
            if entry and entry not in seen:
                seen.add(entry)
                deduped.append(entry)
        return os.pathsep.join(deduped)

    def _runtime_environment(self) -> dict[str, str]:
        return {
            "AITP_KERNEL_ROOT": str(self.kernel_root),
            "AITP_REPO_ROOT": str(self.repo_root),
            "PYTHONPATH": self._runtime_pythonpath(),
        }

    def _mcp_environment(self) -> dict[str, str]:
        return self._runtime_environment()

    def _resolve_aitp_mcp_command(self) -> list[str]:
        installed = shutil.which("aitp-mcp")
        if installed:
            return [installed]

        repo_venv_candidates = [
            self.repo_root / "research" / "knowledge-hub" / ".venv" / "bin" / "aitp-mcp",
            self.repo_root / "research" / "knowledge-hub" / ".venv" / "Scripts" / "aitp-mcp.exe",
            self.repo_root / "research" / "knowledge-hub" / ".venv" / "Scripts" / "aitp-mcp.cmd",
        ]
        for candidate in repo_venv_candidates:
            if candidate.exists():
                return [str(candidate)]

        fallback_python = shutil.which("python") or shutil.which("python3") or sys.executable
        return [fallback_python, "-m", "knowledge_hub.aitp_mcp_server"]

        raise FileNotFoundError("Unable to resolve the aitp-mcp server command.")

    def _resolve_runtime_python_command(self) -> list[str]:
        override = os.environ.get("AITP_PYTHON", "").strip()
        if override:
            return [override]
        if sys.executable:
            return [sys.executable]
        discovered = shutil.which("python") or shutil.which("python3")
        if discovered:
            return [discovered]
        py_launcher = shutil.which("py")
        if py_launcher:
            return [py_launcher, "-3"]
        return ["python3"]

    def _workspace_root_from_target_root(self, target_root: str | None) -> Path:
        if not target_root:
            return self.repo_root

        target_path = Path(target_root)
        if target_path.name == "aitp-runtime" and target_path.parent.name == "skills":
            parent = target_path.parent.parent
            if parent.name == ".agents":
                return parent.parent
        return target_path

    def _runtime_root(self, topic_slug: str) -> Path:
        return self.kernel_root / "runtime" / "topics" / topic_slug

    def _runtime_topic_index_path(self) -> Path:
        return self.kernel_root / "runtime" / "topic_index.jsonl"

    def _current_topic_memory_paths(self) -> dict[str, Path]:
        runtime_root = self.kernel_root / "runtime"
        return {
            "json": runtime_root / "current_topic.json",
            "note": runtime_root / "current_topic.md",
        }

    def _collaborator_memory_paths(self) -> dict[str, Path]:
        root = self.kernel_root / "collaborator-memory"
        return {
            "json": root / "profile.json",
            "note": root / "profile.md",
        }

    def _session_start_paths(self, topic_slug: str) -> dict[str, Path]:
        runtime_root = self._runtime_root(topic_slug)
        return {
            "json": runtime_root / "session_start.contract.json",
            "note": runtime_root / "session_start.generated.md",
        }

    def _control_note_path(self, topic_slug: str) -> Path:
        return self._runtime_root(topic_slug) / "control_note.md"

    def _innovation_direction_path(self, topic_slug: str) -> Path:
        return self._runtime_root(topic_slug) / "innovation_direction.md"

    def _innovation_decisions_path(self, topic_slug: str) -> Path:
        return self._runtime_root(topic_slug) / "innovation_decisions.jsonl"

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

    def _normalize_artifact_path(self, value: str | Path | None) -> str | None:
        raw = str(value or "").strip()
        if not raw:
            return None
        path = Path(raw)
        if path.is_absolute():
            return self._relativize(path)
        return path.as_posix()

    def _artifact_path_on_disk(self, value: str | Path | None) -> Path | None:
        raw = str(value or "").strip()
        if not raw:
            return None
        path = Path(raw).expanduser()
        if path.is_absolute():
            return path
        for root in (self.kernel_root, self.repo_root):
            candidate = (root / path).resolve()
            if candidate.exists():
                return candidate
        kernel_prefixes = (
            "runtime/",
            "source-layer/",
            "intake/",
            "feedback/",
            "validation/",
            "canonical/",
            "consultation/",
        )
        if raw.startswith(kernel_prefixes):
            return (self.kernel_root / path).resolve()
        return (self.repo_root / path).resolve()

    def _research_root(self) -> Path:
        return self.kernel_root.parent

    def _canonical_package_root(self) -> Path:
        return self.repo_root / "research" / "knowledge-hub"

    def _canonical_repo_asset_text(self, relative_path: str, *, fallback_text: str | None = None) -> str:
        candidate = self.repo_root / relative_path
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")
        if fallback_text is not None:
            return fallback_text
        raise FileNotFoundError(f"Canonical repo asset missing: {candidate}")

    def _canonical_skill_text(self, skill_name: str, *, fallback_text: str | None = None) -> str:
        return self._canonical_repo_asset_text(
            f"skills/{skill_name}/SKILL.md",
            fallback_text=fallback_text,
        )

    def _pip_show_package(self, package_name: str) -> dict[str, str]:
        completed = subprocess.run(
            [sys.executable, "-m", "pip", "show", package_name],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            return {}
        payload: dict[str, str] = {}
        for raw_line in completed.stdout.splitlines():
            if ":" not in raw_line:
                continue
            key, value = raw_line.split(":", 1)
            payload[key.strip().lower()] = value.strip()
        return payload

    def _text_matches_canonical(self, path: Path, canonical_relative_path: str) -> bool:
        canonical_path = self.repo_root / canonical_relative_path
        if not path.exists() or not canonical_path.exists():
            return False
        return path.read_text(encoding="utf-8") == canonical_path.read_text(encoding="utf-8")

    def _workspace_legacy_entrypoints(self, workspace_root: Path) -> list[Path]:
        return [
            path
            for path in (
                workspace_root / "AITP_COMMAND_HARNESS.md",
                workspace_root / "AITP_MCP_CONFIG.json",
                workspace_root / "aitp.md",
                workspace_root / "aitp-loop.md",
                workspace_root / "aitp-resume.md",
                workspace_root / "aitp-audit.md",
            )
            if path.exists()
        ]

    def _claude_legacy_command_paths(self) -> list[Path]:
        command_root = Path.home() / ".claude" / "commands"
        if not command_root.exists():
            return []
        return sorted(command_root.glob("aitp*.md"))

    def _ensure_opencode_plugin_enabled(self) -> dict[str, Any]:
        config_path = Path.home() / ".config" / "opencode" / "opencode.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        if config_path.exists():
            payload = json.loads(config_path.read_text(encoding="utf-8"))
        else:
            payload = {"$schema": "https://opencode.ai/config.json"}
        plugin_rows = payload.setdefault("plugin", [])
        if not isinstance(plugin_rows, list):
            plugin_rows = []
            payload["plugin"] = plugin_rows
        canonical_plugin = "aitp@git+https://github.com/bhjia-phys/AITP-Research-Protocol.git"
        if canonical_plugin not in plugin_rows:
            plugin_rows.append(canonical_plugin)
        write_json(config_path, payload)
        return {"config_path": str(config_path), "plugin_entry": canonical_plugin}

    def _opencode_plugin_enabled(self) -> tuple[bool, Path, list[str]]:
        config_path = Path.home() / ".config" / "opencode" / "opencode.json"
        if not config_path.exists():
            return False, config_path, []
        try:
            payload = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return False, config_path, []
        plugin_rows = payload.get("plugin")
        if not isinstance(plugin_rows, list):
            return False, config_path, []
        normalized_rows = [str(item) for item in plugin_rows]
        enabled = any("aitp@" in item for item in normalized_rows)
        return enabled, config_path, normalized_rows

    def _claude_hook_status(self) -> dict[str, Any]:
        base = Path.home() / ".claude"
        return {
            "using_skill": (base / "skills" / "using-aitp" / "SKILL.md").exists(),
            "runtime_skill": (base / "skills" / "aitp-runtime" / "SKILL.md").exists(),
            "session_start_hook": (base / "hooks" / "session-start").exists(),
            "hook_wrapper": (base / "hooks" / "run-hook.cmd").exists(),
            "hooks_manifest": (base / "hooks" / "hooks.json").exists(),
            "settings": (base / "settings.json").exists(),
        }

    def _codex_skill_status(self) -> dict[str, Any]:
        using_path = Path.home() / ".agents" / "skills" / "using-aitp" / "SKILL.md"
        runtime_path = Path.home() / ".agents" / "skills" / "aitp-runtime" / "SKILL.md"
        return {
            "using_skill_path": str(using_path),
            "runtime_skill_path": str(runtime_path),
            "using_skill_present": using_path.exists(),
            "runtime_skill_present": runtime_path.exists(),
            "using_skill_matches_canonical": self._text_matches_canonical(using_path, "skills/using-aitp/SKILL.md"),
            "runtime_skill_matches_canonical": self._text_matches_canonical(runtime_path, "skills/aitp-runtime/SKILL.md"),
        }

    def _backup_and_move(self, path: Path, backup_root: Path, backup_subdir: str) -> dict[str, str]:
        destination = backup_root / backup_subdir / path.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(destination))
        return {"original_path": str(path), "backup_path": str(destination)}

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

    def _idea_packet_paths(self, topic_slug: str) -> dict[str, Path]:
        runtime_root = self._runtime_root(topic_slug)
        return {
            "json": runtime_root / "idea_packet.json",
            "note": runtime_root / "idea_packet.md",
        }

    def _operator_checkpoint_paths(self, topic_slug: str) -> dict[str, Path]:
        runtime_root = self._runtime_root(topic_slug)
        return {
            "json": runtime_root / "operator_checkpoint.active.json",
            "note": runtime_root / "operator_checkpoint.active.md",
            "ledger": runtime_root / "operator_checkpoints.jsonl",
        }

    def _strategy_memory_path(self, topic_slug: str, run_id: str) -> Path:
        return self._feedback_run_root(topic_slug, run_id) / "strategy_memory.jsonl"

    def _topic_skill_projection_paths(self, topic_slug: str) -> dict[str, Path]:
        runtime_root = self._runtime_root(topic_slug)
        return {
            "json": runtime_root / "topic_skill_projection.active.json",
            "note": runtime_root / "topic_skill_projection.active.md",
        }

    def _topic_skill_projection_read_reason(self, payload: dict[str, Any]) -> str:
        lane = str(payload.get("lane") or "").strip()
        if lane == "formal_theory":
            return "Validated topic-skill projection for this formal-theory lane. Read it before reusing the theorem-facing route."
        if lane == "code_method":
            return "Validated topic-skill projection for this code-method lane. Read it before reusing the benchmark-first route."
        return "Validated topic-skill projection for this lane. Read it before reusing the bounded route."

    def _topic_skill_projection_deferred_reason(self, payload: dict[str, Any]) -> str:
        lane = str(payload.get("lane") or "").strip()
        if lane == "formal_theory":
            return "The projection becomes mandatory once this topic's theorem-facing route is stable enough to reuse or promote."
        if lane == "code_method":
            return "The projection becomes mandatory once this topic's code-method route is stable enough to reuse or promote."
        return "The projection becomes mandatory once this topic's bounded route is stable enough to reuse or promote."

    def _topic_dashboard_path(self, topic_slug: str) -> Path:
        return self._runtime_root(topic_slug) / "topic_dashboard.md"

    def _result_brief_paths(self, topic_slug: str) -> dict[str, Path]:
        runtime_root = self._runtime_root(topic_slug)
        return {
            "json": runtime_root / "result_brief.latest.json",
            "note": runtime_root / "result_brief.latest.md",
        }

    def _promotion_readiness_path(self, topic_slug: str) -> Path:
        return self._runtime_root(topic_slug) / "promotion_readiness.md"

    def _layer_projection_paths(self, topic_slug: str, layer: str) -> dict[str, Path]:
        runtime_root = self._runtime_root(topic_slug)
        stem_by_layer = {
            "L0": "l0_sources",
            "L1": "l1_understanding",
            "L2": "l2_memory",
            "L4": "l4_validation",
        }
        if layer not in stem_by_layer:
            raise ValueError(f"Unsupported layer projection: {layer}")
        stem = stem_by_layer[layer]
        return {
            "json": runtime_root / f"{stem}.json",
            "note": runtime_root / f"{stem}.md",
        }

    def _l3_subplane_paths(self, topic_slug: str, subplane: str) -> dict[str, Path]:
        runtime_root = self._runtime_root(topic_slug)
        stem_by_subplane = {
            "analysis": "l3_analysis",
            "result_integration": "l3_result_integration",
            "distillation": "l3_distillation",
        }
        if subplane not in stem_by_subplane:
            raise ValueError(f"Unsupported L3 subplane: {subplane}")
        stem = stem_by_subplane[subplane]
        return {
            "json": runtime_root / f"{stem}.json",
            "note": runtime_root / f"{stem}.md",
        }

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

    def _theory_formal_candidate_types(self) -> set[str]:
        runtime_policy = self._load_runtime_policy().get("auto_promotion_policy") or {}
        configured = {
            str(value).strip()
            for value in (runtime_policy.get("theory_formal_candidate_types") or [])
            if str(value).strip()
        }
        if configured:
            return configured
        return {
            "definition_card",
            "notation_card",
            "equation_card",
            "assumption_card",
            "regime_card",
            "theorem_card",
            "proof_fragment",
            "derivation_step",
            "example_card",
            "caveat_card",
            "equivalence_map",
            "symbol_binding",
        }

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
        return canonical_template_mode(research_mode)

    def _validation_mode_for_template(self, template_mode: str | None, research_mode: str | None = None) -> str:
        return canonical_validation_mode(template_mode, research_mode)

    def _lane_for_modes(self, *, template_mode: str | None, research_mode: str | None) -> str:
        return canonical_lane(template_mode=template_mode, research_mode=research_mode)

    def _load_strategy_memory_rows(self, topic_slug: str) -> list[dict[str, Any]]:
        runs_root = self.kernel_root / "feedback" / "topics" / topic_slug / "runs"
        if not runs_root.exists():
            return []
        rows: list[dict[str, Any]] = []
        for path in sorted(runs_root.glob("*/strategy_memory.jsonl")):
            for raw_row in read_jsonl(path):
                if not isinstance(raw_row, dict):
                    continue
                row = dict(raw_row)
                row["path"] = self._relativize(path)
                row["run_id"] = str(row.get("run_id") or path.parent.name)
                row["timestamp"] = str(row.get("timestamp") or "")
                row["strategy_id"] = str(row.get("strategy_id") or "")
                row["strategy_type"] = str(row.get("strategy_type") or "")
                row["summary"] = str(row.get("summary") or "")
                row["lane"] = str(row.get("lane") or "")
                row["outcome"] = str(row.get("outcome") or "")
                try:
                    row["confidence"] = float(row.get("confidence") or 0.0)
                except (TypeError, ValueError):
                    row["confidence"] = 0.0
                row["reuse_conditions"] = self._dedupe_strings(
                    [str(item) for item in (row.get("reuse_conditions") or [])]
                )
                row["do_not_apply_when"] = self._dedupe_strings(
                    [str(item) for item in (row.get("do_not_apply_when") or [])]
                )
                input_context = row.get("input_context")
                row["input_context"] = input_context if isinstance(input_context, dict) else {}
                row["evidence_refs"] = self._dedupe_strings(
                    [str(item) for item in (row.get("evidence_refs") or [])]
                )
                rows.append(row)
        rows.sort(
            key=lambda item: (
                str(item.get("timestamp") or ""),
                str(item.get("run_id") or ""),
                str(item.get("strategy_id") or ""),
            ),
            reverse=True,
        )
        return rows

    def _strategy_memory_match_score(
        self,
        row: dict[str, Any],
        *,
        lane: str,
        current_context_text: str,
    ) -> int:
        score = 0
        if lane and str(row.get("lane") or "").strip() == lane:
            score += 2
        if str(row.get("outcome") or "").strip() in {"helpful", "harmful"}:
            score += 1
        row_text_parts = [
            str(row.get("summary") or ""),
            str(row.get("strategy_type") or ""),
            str(row.get("human_note") or ""),
            *[str(item) for item in (row.get("reuse_conditions") or [])],
            *[str(item) for item in (row.get("do_not_apply_when") or [])],
            *[
                str(value)
                for value in ((row.get("input_context") or {}) if isinstance(row.get("input_context"), dict) else {}).values()
            ],
        ]
        current_tokens = set(re.findall(r"[a-z0-9_]+", current_context_text.lower()))
        row_tokens = set(re.findall(r"[a-z0-9_]+", " ".join(row_text_parts).lower()))
        overlap = current_tokens & row_tokens
        if overlap:
            score += min(len(overlap), 4)
        return score

    def _derive_strategy_memory_summary(
        self,
        *,
        topic_slug: str,
        latest_run_id: str | None,
        selected_pending_action: dict[str, Any] | None,
        research_contract: dict[str, Any],
        validation_contract: dict[str, Any],
    ) -> dict[str, Any]:
        rows = self._load_strategy_memory_rows(topic_slug)
        lane = self._lane_for_modes(
            template_mode=research_contract.get("template_mode"),
            research_mode=research_contract.get("research_mode"),
        )
        if not rows:
            return {
                "topic_slug": topic_slug,
                "latest_run_id": latest_run_id or "",
                "status": "absent",
                "lane": lane,
                "row_count": 0,
                "relevant_count": 0,
                "helpful_count": 0,
                "harmful_count": 0,
                "latest_path": None,
                "relevant_paths": [],
                "guidance": [],
                "summary": "No run-local strategy memory is currently recorded for this topic.",
            }

        current_context_text = " ".join(
            [
                str((selected_pending_action or {}).get("summary") or ""),
                str(research_contract.get("question") or ""),
                str(validation_contract.get("verification_focus") or ""),
            ]
        )
        scored_rows = [
            {
                **row,
                "match_score": self._strategy_memory_match_score(
                    row,
                    lane=lane,
                    current_context_text=current_context_text,
                ),
            }
            for row in rows
        ]
        relevant_rows = [
            row for row in scored_rows if int(row.get("match_score") or 0) > 0
        ][:3]
        guidance: list[str] = []
        for row in relevant_rows:
            outcome = str(row.get("outcome") or "").strip()
            if outcome == "helpful":
                prefix = "Reuse"
            elif outcome == "harmful":
                prefix = "Avoid"
            else:
                prefix = "Review"
            guidance.append(f"{prefix}: {row.get('summary') or '(missing)'}")
        helpful_count = sum(1 for row in rows if str(row.get("outcome") or "").strip() == "helpful")
        harmful_count = sum(1 for row in rows if str(row.get("outcome") or "").strip() == "harmful")
        latest_path = str(rows[0].get("path") or "") or None
        summary = (
            f"{len(rows)} strategy-memory row(s) recorded for lane `{lane}`; "
            f"{len(relevant_rows)} relevant to the current bounded route."
        )
        if guidance:
            summary += " " + guidance[0]
        return {
            "topic_slug": topic_slug,
            "latest_run_id": latest_run_id or "",
            "status": "available",
            "lane": lane,
            "row_count": len(rows),
            "relevant_count": len(relevant_rows),
            "helpful_count": helpful_count,
            "harmful_count": harmful_count,
            "latest_path": latest_path,
            "relevant_paths": self._dedupe_strings(
                [str(row.get("path") or "") for row in relevant_rows if str(row.get("path") or "").strip()]
            ),
            "guidance": guidance,
            "summary": summary,
        }

    def record_strategy_memory(
        self,
        *,
        topic_slug: str,
        run_id: str,
        strategy_type: str,
        summary: str,
        outcome: str,
        updated_by: str = "aitp-cli",
        lane: str | None = None,
        strategy_id: str | None = None,
        input_context: dict[str, Any] | None = None,
        confidence: float | int | None = None,
        evidence_refs: list[str] | None = None,
        reuse_conditions: list[str] | None = None,
        do_not_apply_when: list[str] | None = None,
        human_note: str | None = None,
    ) -> dict[str, Any]:
        valid_strategy_types = {
            "search_route",
            "verification_guardrail",
            "debug_pattern",
            "resource_plan",
            "scope_control",
        }
        valid_outcomes = {"helpful", "neutral", "harmful", "inconclusive"}
        normalized_strategy_type = str(strategy_type or "").strip()
        normalized_outcome = str(outcome or "").strip()
        if normalized_strategy_type not in valid_strategy_types:
            raise ValueError(f"strategy_type must be one of {sorted(valid_strategy_types)}")
        if normalized_outcome not in valid_outcomes:
            raise ValueError(f"outcome must be one of {sorted(valid_outcomes)}")
        normalized_summary = str(summary or "").strip()
        if not normalized_summary:
            raise ValueError("summary must not be empty")
        normalized_confidence = float(confidence if confidence is not None else 0.5)
        if not 0.0 <= normalized_confidence <= 1.0:
            raise ValueError("confidence must be within [0, 1]")

        topic_state = read_json(self._runtime_root(topic_slug) / "topic_state.json") or {}
        research_contract = read_json(self._research_question_contract_paths(topic_slug)["json"]) or {}
        resolved_lane = str(lane or "").strip() or self._lane_for_modes(
            template_mode=research_contract.get("template_mode"),
            research_mode=research_contract.get("research_mode") or topic_state.get("research_mode"),
        )
        timestamp = now_iso()
        resolved_strategy_id = str(strategy_id or "").strip() or (
            f"strat-{normalized_strategy_type}-{slugify(timestamp)}"
        )
        row = {
            "timestamp": timestamp,
            "topic_slug": topic_slug,
            "run_id": run_id,
            "lane": resolved_lane,
            "strategy_id": resolved_strategy_id,
            "strategy_type": normalized_strategy_type,
            "summary": normalized_summary,
            "input_context": input_context if isinstance(input_context, dict) else {},
            "outcome": normalized_outcome,
            "confidence": normalized_confidence,
            "evidence_refs": self._dedupe_strings([str(item) for item in (evidence_refs or [])]),
            "reuse_conditions": self._dedupe_strings([str(item) for item in (reuse_conditions or [])]),
            "do_not_apply_when": self._dedupe_strings([str(item) for item in (do_not_apply_when or [])]),
            "human_note": str(human_note or "").strip(),
            "updated_by": updated_by,
        }
        path = self._strategy_memory_path(topic_slug, run_id)
        rows = read_jsonl(path)
        rows.append(row)
        write_jsonl(path, rows)
        return {
            "topic_slug": topic_slug,
            "run_id": run_id,
            "strategy_memory_path": str(path),
            "strategy_memory_entry": row,
        }

    def _load_operation_manifests(self, topic_slug: str, run_id: str | None) -> list[dict[str, Any]]:
        resolved_run_id = str(run_id or "").strip()
        if not resolved_run_id:
            return []
        operations_root = self._validation_run_root(topic_slug, resolved_run_id) / "operations"
        if not operations_root.exists():
            return []
        rows: list[dict[str, Any]] = []
        for manifest_path in sorted(operations_root.glob("*/operation_manifest.json")):
            manifest = read_json(manifest_path)
            if not isinstance(manifest, dict):
                continue
            row = dict(manifest)
            row["path"] = self._relativize(manifest_path)
            row["summary_path"] = self._relativize(manifest_path.parent / "operation_summary.md")
            rows.append(row)
        return rows

    def _derive_topic_skill_projection(
        self,
        *,
        topic_slug: str,
        updated_by: str,
        topic_state: dict[str, Any],
        research_contract: dict[str, Any],
        validation_contract: dict[str, Any],
        selected_pending_action: dict[str, Any] | None,
        strategy_memory: dict[str, Any],
        topic_completion: dict[str, Any],
        open_gap_summary: dict[str, Any],
        candidate_rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        latest_run_id = str(topic_state.get("latest_run_id") or "").strip()
        lane = self._lane_for_modes(
            template_mode=research_contract.get("template_mode"),
            research_mode=research_contract.get("research_mode"),
        )
        formal_theory_context = self._formal_theory_projection_candidate_context(
            topic_slug=topic_slug,
            run_id=latest_run_id or None,
            candidate_rows=candidate_rows,
        )
        formal_theory_candidate_id = str((formal_theory_context or {}).get("candidate_id") or "").strip()
        formal_theory_review_path = (formal_theory_context or {}).get("review_path")
        formal_theory_review_status = str((formal_theory_context or {}).get("review_status") or "missing").strip()
        formal_theory_completion_status = str(
            (formal_theory_context or {}).get("completion_status")
            or topic_completion.get("status")
            or "not_assessed"
        ).strip()
        trust_audit_path = (
            self._trust_audit_path(topic_slug, latest_run_id)
            if latest_run_id
            else self._runtime_root(topic_slug) / "missing-trust-audit.json"
        )
        trust_audit = read_json(trust_audit_path) if trust_audit_path.exists() else None
        operation_manifests = self._load_operation_manifests(topic_slug, latest_run_id or None)
        title = f"{str(research_contract.get('title') or self._topic_display_title(topic_slug))} Topic Skill Projection"
        projection_id = f"topic_skill_projection:{slugify(topic_slug)}"
        candidate_hash = hashlib.sha1(topic_slug.encode("utf-8")).hexdigest()[:8]
        candidate_slug = slugify(topic_slug)[:24].rstrip("-")
        candidate_id = f"candidate:topic-skill-proj-{candidate_slug}-{candidate_hash}"
        intended_l2_target = projection_id
        derived_from_artifacts = self._dedupe_strings(
            [
                self._relativize(self._research_question_contract_paths(topic_slug)["json"]),
                self._relativize(self._validation_contract_paths(topic_slug)["json"]),
                self._relativize(self._runtime_root(topic_slug) / "topic_state.json"),
                self._normalize_artifact_path(strategy_memory.get("latest_path")),
                self._relativize(trust_audit_path) if trust_audit_path.exists() else "",
                self._relativize(self._topic_completion_paths(topic_slug)["json"]),
                self._relativize(formal_theory_review_path) if isinstance(formal_theory_review_path, Path) and formal_theory_review_path.exists() else "",
                self._relativize(self._gap_map_path(topic_slug)),
                *[str(row.get("path") or "") for row in operation_manifests],
            ]
        )
        entry_signals = self._dedupe_strings(
            [
                f"lane={lane}",
                f"selected_action={str((selected_pending_action or {}).get('summary') or '').strip() or '(none)'}",
                f"strategy_memory_status={strategy_memory.get('status') or 'absent'}",
                (
                    f"theorem_candidate={formal_theory_candidate_id or '(none)'}"
                    if lane == "formal_theory"
                    else f"operation_count={len(operation_manifests)}"
                ),
                (
                    f"formal_theory_review={formal_theory_review_status}"
                    if lane == "formal_theory"
                    else f"operation_trust={str((trust_audit or {}).get('overall_status') or 'missing')}"
                ),
                (
                    f"topic_completion={formal_theory_completion_status}"
                    if lane == "formal_theory"
                    else ""
                ),
            ]
        )
        required_first_reads = self._dedupe_strings(
            [
                self._relativize(self._research_question_contract_paths(topic_slug)["note"]),
                self._relativize(self._validation_contract_paths(topic_slug)["note"]),
                self._normalize_artifact_path(strategy_memory.get("latest_path")),
                (
                    self._relativize(formal_theory_review_path)
                    if lane == "formal_theory" and isinstance(formal_theory_review_path, Path) and formal_theory_review_path.exists()
                    else self._relativize(trust_audit_path) if trust_audit_path.exists() else ""
                ),
                (
                    self._relativize(self._topic_completion_paths(topic_slug)["note"])
                    if lane == "formal_theory"
                    else ""
                ),
                *[
                    str(row.get("summary_path") or row.get("path") or "")
                    for row in operation_manifests
                ],
            ]
        )
        required_first_routes: list[str] = []
        benchmark_first_rules: list[str] = []
        operation_trust_requirements: list[str] = []
        if lane == "formal_theory":
            candidate_label = formal_theory_candidate_id or "the active theorem-facing candidate"
            required_first_routes.extend(
                [
                    f"Read `formal_theory_review.json` for `{candidate_label}` before reusing the theorem-facing route.",
                    "Check that `topic_completion.json` still reports `promotion-ready` or `promoted` before treating the route as reusable.",
                ]
            )
            benchmark_first_rules.append(
                f"`{candidate_label}` requires `formal_theory_review.json` overall_status `ready` and topic completion `promotion-ready` or `promoted` before route reuse is trusted."
            )
            operation_trust_requirements.append(
                f"`{candidate_label}`: formal_theory_review_status={formal_theory_review_status}, topic_completion_status={formal_theory_completion_status}, strategy_memory_rows={int(strategy_memory.get('row_count') or 0)}."
            )
        else:
            for manifest in operation_manifests:
                title_hint = str(manifest.get("title") or manifest.get("operation_id") or "(missing)")
                baseline_required = bool(manifest.get("baseline_required"))
                atomic_required = bool(manifest.get("atomic_understanding_required"))
                baseline_status = str(manifest.get("baseline_status") or "missing")
                atomic_status = str(manifest.get("atomic_understanding_status") or "missing")
                if baseline_required:
                    required_first_routes.append(
                        f"Close the declared benchmark/baseline for `{title_hint}` before broader workflow claims."
                    )
                    benchmark_first_rules.append(
                        f"`{title_hint}` requires baseline status `{baseline_status}` before route reuse is trusted."
                    )
                if atomic_required:
                    required_first_routes.append(
                        f"Complete atomic understanding for `{title_hint}` before claiming reusable method understanding."
                    )
                operation_trust_requirements.append(
                    f"`{title_hint}`: baseline_required={str(baseline_required).lower()}, "
                    f"baseline_status={baseline_status}, atomic_understanding_required={str(atomic_required).lower()}, "
                    f"atomic_understanding_status={atomic_status}."
                )
            if not benchmark_first_rules:
                benchmark_first_rules.append(
                    "Do not claim reusable code-method confidence without a persisted benchmark or trust-ready operation artifact."
                )
        operator_checkpoint_rules = [
            "Raise an operator checkpoint when benchmark mismatch or validation-route ambiguity changes the bounded route.",
            "Require explicit human approval before any L2 promotion of a topic-skill projection.",
            "Translate continue/branch/redirect answers into durable steering artifacts before deeper execution continues.",
        ]
        forbidden_proxies = self._dedupe_strings(
            list(research_contract.get("forbidden_proxies") or [])
            + [
                "Do not treat raw code changes, unreviewed configs, or prose-only workflow descriptions as a reusable topic-skill projection.",
                (
                    "Do not treat the projection itself as a theorem certificate, proof closure, or completed formal result."
                    if lane == "formal_theory"
                    else "Do not claim broader workflow portability before the benchmark-first gate and operation-trust audit are both satisfied."
                ),
            ]
        )
        strategy_guidance = self._dedupe_strings(list(strategy_memory.get("guidance") or []))

        if lane == "formal_theory":
            if not latest_run_id:
                status = "blocked"
                status_reason = "Projection is blocked because the topic has no active run id yet."
            elif not formal_theory_context:
                status = "not_applicable"
                status_reason = "Topic-skill projection is not applicable because the active run has no theorem-facing candidate rows."
            elif not isinstance(formal_theory_review_path, Path) or not formal_theory_review_path.exists():
                status = "blocked"
                status_reason = (
                    f"Projection is blocked until `{formal_theory_candidate_id or 'the active theorem-facing candidate'}` "
                    "has a durable formal_theory_review.json artifact."
                )
            elif formal_theory_review_status != "ready":
                status = "blocked"
                status_reason = (
                    f"Projection is blocked until `{formal_theory_candidate_id or 'the active theorem-facing candidate'}` "
                    "has formal_theory_review overall_status `ready`."
                )
            elif formal_theory_completion_status not in {"promotion-ready", "promoted"}:
                status = "blocked"
                status_reason = "Projection is blocked until topic completion reaches `promotion-ready` or `promoted`."
            elif int(strategy_memory.get("row_count") or 0) <= 0:
                status = "blocked"
                status_reason = "Projection is blocked until at least one run-local strategy-memory row exists."
            else:
                status = "available"
                status_reason = (
                    "Projection is available because the topic is formal_theory, the active theorem-facing review is ready, "
                    "topic completion is promotion-ready, and route-level strategy memory exists."
                )
        elif lane != "code_method":
            status = "not_applicable"
            status_reason = "Topic-skill projection v1 only applies to the code_method lane."
        elif not latest_run_id:
            status = "blocked"
            status_reason = "Projection is blocked because the topic has no active run id yet."
        elif not operation_manifests:
            status = "blocked"
            status_reason = "Projection is blocked because no operation manifests exist for the active run."
        elif not trust_audit or str(trust_audit.get("overall_status") or "") != "pass":
            status = "blocked"
            status_reason = "Projection is blocked until operation trust passes for the active run."
        elif int(strategy_memory.get("row_count") or 0) <= 0:
            status = "blocked"
            status_reason = "Projection is blocked until at least one run-local strategy-memory row exists."
        else:
            status = "available"
            status_reason = (
                "Projection is available because the topic is code_method, has trust-ready operation manifests, "
                "and carries route-level strategy memory."
            )

        summary = (
            (
                "Validated reusable execution projection for the topic's theorem-facing formal-theory route."
                if lane == "formal_theory"
                else "Validated reusable execution projection for the topic's benchmark-first code-method route."
            )
            if status == "available"
            else "Topic-skill projection is not yet reusable enough to treat as an L2-ready execution projection."
        )
        return {
            "id": projection_id,
            "topic_slug": topic_slug,
            "source_topic_slug": topic_slug,
            "run_id": latest_run_id,
            "title": title,
            "summary": summary,
            "lane": lane,
            "status": status,
            "status_reason": status_reason,
            "candidate_id": candidate_id if status == "available" else None,
            "intended_l2_target": intended_l2_target if status == "available" else None,
            "entry_signals": entry_signals,
            "required_first_reads": required_first_reads,
            "required_first_routes": self._dedupe_strings(required_first_routes),
            "benchmark_first_rules": self._dedupe_strings(benchmark_first_rules),
            "operator_checkpoint_rules": operator_checkpoint_rules,
            "operation_trust_requirements": self._dedupe_strings(operation_trust_requirements),
            "strategy_guidance": strategy_guidance,
            "forbidden_proxies": forbidden_proxies,
            "derived_from_artifacts": derived_from_artifacts,
            "updated_at": now_iso(),
            "updated_by": updated_by,
        }

    def _sync_topic_skill_projection_candidate(
        self,
        *,
        topic_slug: str,
        run_id: str | None,
        projection: dict[str, Any],
        updated_by: str,
    ) -> dict[str, Any] | None:
        resolved_run_id = str(run_id or "").strip()
        candidate_id = str(
            projection.get("candidate_id") or f"candidate:topic-skill-projection-{slugify(topic_slug)}"
        ).strip()
        if resolved_run_id and str(projection.get("status") or "") != "available":
            self._remove_candidate_row(topic_slug, resolved_run_id, candidate_id)
            return None
        if not resolved_run_id:
            return None
        if not candidate_id:
            return None
        lane = str(projection.get("lane") or "").strip()
        trust_ref_path = str(
            next(
                (
                    item
                    for item in projection.get("derived_from_artifacts") or []
                    if str(item).endswith("formal_theory_review.json")
                ),
                "",
            )
            if lane == "formal_theory"
            else next(
                (
                    item
                    for item in projection.get("derived_from_artifacts") or []
                    if str(item).endswith("trust_audit.json")
                ),
                "",
            )
        )
        candidate_row = {
            "candidate_id": candidate_id,
            "candidate_type": "topic_skill_projection",
            "title": str(projection.get("title") or candidate_id),
            "summary": str(projection.get("summary") or ""),
            "topic_slug": topic_slug,
            "run_id": resolved_run_id,
            "origin_refs": [
                {
                    "id": f"strategy_memory:{resolved_run_id}",
                    "layer": "L3",
                    "object_type": "strategy_memory",
                    "path": str(next((item for item in projection.get("derived_from_artifacts") or [] if str(item).endswith("strategy_memory.jsonl")), "")),
                    "title": "Strategy memory",
                    "summary": "Run-local route memory contributing to the projection.",
                },
                {
                    "id": (
                        f"formal_theory_review:{resolved_run_id}"
                        if lane == "formal_theory"
                        else f"trust_audit:{resolved_run_id}"
                    ),
                    "layer": "L4",
                    "object_type": (
                        "formal_theory_review"
                        if lane == "formal_theory"
                        else "operation_trust_audit"
                    ),
                    "path": trust_ref_path,
                    "title": (
                        "Formal theory review"
                        if lane == "formal_theory"
                        else "Operation trust audit"
                    ),
                    "summary": (
                        "Ready theorem-facing review evidence used to validate the formal-theory projection."
                        if lane == "formal_theory"
                        else "Passing operation-trust evidence used to validate the code-method projection."
                    ),
                },
            ],
            "question": (
                (
                    f"How should the topic `{topic_slug}` be entered and advanced as a reusable theorem-facing formal-theory route?"
                    if lane == "formal_theory"
                    else f"How should the topic `{topic_slug}` be entered and advanced as a reusable benchmark-first code-method route?"
                )
            ),
            "assumptions": self._dedupe_strings(list(projection.get("benchmark_first_rules") or [])),
            "proposed_validation_route": (
                "human-reviewed formal-theory topic-skill projection promotion"
                if lane == "formal_theory"
                else "human-reviewed topic-skill projection promotion"
            ),
            "intended_l2_targets": [str(projection.get("intended_l2_target") or "")],
            "status": "ready_for_validation",
            "promotion_mode": "human",
            "topic_completion_status": "promotion-ready" if lane == "formal_theory" else "regression-stable",
        }
        self._replace_candidate_row(topic_slug, resolved_run_id, candidate_id, candidate_row)
        return candidate_row

    def _resolve_load_profile(
        self,
        *,
        explicit_load_profile: str | None,
        human_request: str | None = None,
        topic_state: dict[str, Any] | None = None,
    ) -> tuple[str, str]:
        normalized_explicit = str(explicit_load_profile or "").strip().lower()
        if normalized_explicit in {"light", "full"}:
            return normalized_explicit, "explicit_request"

        normalized_request = str(human_request or "").strip().lower()
        if normalized_request:
            full_patterns = (
                r"\bmismatch\b",
                r"\bpromotion\b",
                r"\baudit\b",
                r"\bscope\b",
                r"\bcontradiction\b",
                r"\bdisagree(?:ment)?\b",
                r"不一致",
                r"矛盾",
                r"全面检查",
                r"全量",
                r"晋升",
                r"升级到l2",
                r"改范围",
                r"改 scope",
            )
            for pattern in full_patterns:
                if re.search(pattern, normalized_request, flags=re.IGNORECASE):
                    return "full", "auto_escalation_from_request"
            return "light", "auto_light_for_ordinary_topic_work"

        remembered = str((topic_state or {}).get("load_profile") or "").strip().lower()
        if remembered in {"light", "full"}:
            return remembered, "persisted_topic_state"
        return "light", "default_light_profile"

    def _persist_load_profile_state(
        self,
        *,
        topic_slug: str,
        load_profile: str,
        reason: str,
        updated_by: str,
    ) -> dict[str, Any]:
        topic_state_path = self._runtime_root(topic_slug) / "topic_state.json"
        topic_state = read_json(topic_state_path) or {"topic_slug": topic_slug}
        previous_profile = str(topic_state.get("load_profile") or "").strip()
        topic_state["load_profile"] = load_profile
        topic_state["load_profile_reason"] = reason
        topic_state["load_profile_updated_at"] = now_iso()
        topic_state["load_profile_updated_by"] = updated_by
        if previous_profile and previous_profile != load_profile:
            topic_state["load_profile_last_transition"] = {
                "from": previous_profile,
                "to": load_profile,
                "reason": reason,
                "updated_at": topic_state["load_profile_updated_at"],
                "updated_by": updated_by,
            }
        write_json(topic_state_path, topic_state)
        return topic_state

    def _coalesce_list(self, existing: Any, defaults: list[str]) -> list[str]:
        if isinstance(existing, list):
            values = self._dedupe_strings([str(item) for item in existing])
            if values:
                return values
        return self._dedupe_strings(defaults)

    def _distill_from_sources(
        self,
        source_rows: list[dict[str, Any]],
        topic_slug: str,
    ) -> dict[str, Any]:
        """从已注册的 source 中提取 initial_idea, novelty_target. first_validation_route.

        这是 source-to-question 蒸馏的核心逻辑。
        改进版本：过滤 REV 注释、从原始文件读取、智能提取 novelty。
        """
        if not source_rows:
            return {
                "distilled_initial_idea": "",
                "distilled_novelty_target": "",
                "distilled_first_validation_route": "",
                "distilled_lane": "",
            }

        all_previews: list[dict[str, str]] = []
        all_claims: list[dict[str, str]] = []
        all_titles: list[str] = []

        for row in source_rows:
            source_id = str(row.get("source_id") or "")
            source_type = str(row.get("source_type") or "")
            title = str(row.get("title") or "")
            provenance = row.get("provenance") or {}
            absolute_path = str(provenance.get("absolute_path") or "") if isinstance(provenance, dict) else ""

            if title:
                all_titles.append(title)

            # 构建 snapshot 路径
            safe_source_id = source_id.replace(":", "-")
            snapshot_path = (
                self.kernel_root
                / "source-layer"
                / "topics"
                / topic_slug
                / "sources"
                / safe_source_id
                / "snapshot.md"
            )

            snapshot_text = ""
            if snapshot_path.exists():
                snapshot_text = snapshot_path.read_text(encoding="utf-8")

            # 从 summary 中提取（通常是更好的内容）
            summary = str(row.get("summary") or "")

            # 从 snapshot 中提取 Preview 部分
            preview_content = ""
            if snapshot_text:
                preview_match = re.search(
                    r"## Preview\s*\n(.*?)(?=\n##|\Z)",
                    snapshot_text,
                    re.DOTALL,
                )
                if preview_match:
                    preview_content = preview_match.group(1).strip()

            # 过滤掉 REV 注释，只保留实际内容
            if preview_content:
                # 移除 LaTeX 注释行（以 % 开头的行）
                lines = preview_content.split("\n")
                content_lines = [
                    line for line in lines
                    if not line.strip().startswith("%")
                ]
                filtered_content = "\n".join(content_lines).strip()
                if filtered_content:
                    preview_content = filtered_content

            # 如果 Preview 只有注释，尝试从原始文件读取
            if (not preview_content or preview_content.startswith("%")) and absolute_path:
                original_path = Path(absolute_path)
                if original_path.exists() and original_path.suffix.lower() in [".tex", ".md", ".txt"]:
                    try:
                        original_text = original_path.read_text(encoding="utf-8")
                        # 提取前 500 字符作为 preview
                        # 跳过 LaTeX 导言
                        if original_path.suffix.lower() == ".tex":
                            # 跳过注释和导言，找第一个 \section 或 \chapter
                            section_match = re.search(
                                r"\\(?:section|chapter|subsection)\*?\{[^}]+\}[^}]*",
                                original_text,
                                re.IGNORECASE | re.DOTALL,
                            )
                            if section_match:
                                start_pos = section_match.start()
                                # 取 section 之后的 500 字符
                                preview_content = original_text[start_pos:start_pos + 500].strip()
                            else:
                                # 没找到 section，取前 500 字符（过滤注释）
                                lines = original_text.split("\n")
                                content_lines = [line for line in lines if not line.strip().startswith("%")]
                                preview_content = "\n".join(content_lines[:30])[:500].strip()
                        else:
                            preview_content = original_text[:500].strip()
                    except Exception:
                        pass

            # 如果还是没有，用 summary
            if not preview_content and summary:
                # 过滤 summary 中的注释
                lines = summary.split("\n")
                content_lines = [line for line in lines if not line.strip().startswith("%")]
                preview_content = "\n".join(content_lines)[:300].strip()

            if preview_content:
                all_previews.append({
                    "source_id": source_id,
                    "source_type": source_type,
                    "title": title,
                    "preview": preview_content,
                })

            # 从多个来源提取 novelty claims
            # 1. 从 REV 注释
            if snapshot_text:
                rev_matches = re.findall(
                    r"%\s*\[REV\]\s*\[([^\]]+)\]",
                    snapshot_text,
                )
                for match in rev_matches:
                    tag = match.strip()
                    lower_tag = tag.lower()
                    if any(kw in lower_tag for kw in ["novel", "new", "change", "add", "improve", "extend", "mainline", "introduce"]):
                        all_claims.append({
                            "source_id": source_id,
                            "claim": tag,
                            "priority": 1 if "novel" in lower_tag else 2,
                        })

            # 2. 从 title 中提取（包含关键词的）
            title_lower = title.lower()
            if any(kw in title_lower for kw in ["novel", "new", "first", "closure", "variational", "derivation"]):
                all_claims.append({
                    "source_id": source_id,
                    "claim": f"Title indicates: {title}",
                    "priority": 3,
                })

            # 3. 从 summary 中提取关键词
            summary_lower = summary.lower()
            novelty_keywords = ["novel", "new contribution", "we show", "we prove", "we derive", "closure", "variational"]
            for kw in novelty_keywords:
                if kw in summary_lower:
                    # 提取包含关键词的句子
                    sentences = re.split(r"[.!?]", summary)
                    for sent in sentences:
                        if kw in sent.lower():
                            all_claims.append({
                                "source_id": source_id,
                                "claim": sent.strip()[:100],
                                "priority": 2,
                            })
                            break

        # 蒸馏结果
        distilled_initial_idea = ""
        distilled_novelty_target = ""
        distilled_first_validation_route = ""
        distilled_lane = ""

        # 合并 previews 作为 initial_idea
        if all_previews:
            preview_parts = []
            for p in all_previews[:3]:  # 只取前 3 个 source
                preview_text = p.get("preview", "")
                title = p.get("title", "")
                # 取第一段有效内容
                first_para = preview_text.split("\n\n")[0] if preview_text else ""
                if first_para and len(first_para) > 20:  # 过滤太短的内容
                    preview_parts.append(f"[{title}] {first_para[:200]}")
            if preview_parts:
                distilled_initial_idea = " ".join(preview_parts)

        # 如果没有 preview，用 titles
        if not distilled_initial_idea and all_titles:
            distilled_initial_idea = f"Research topic: {', '.join(all_titles[:3])}"

        # 提取最相关的 novelty claim（按优先级排序）
        if all_claims:
            # 按优先级排序
            sorted_claims = sorted(all_claims, key=lambda x: x.get("priority", 3))
            if sorted_claims:
                distilled_novelty_target = sorted_claims[0].get("claim", "")

        # 根据 source 类型推断 lane 和 first_validation_route
        source_types = set(
            str(row.get("source_type") or "").lower() for row in source_rows
        )

        # 扩展类型映射
        formal_types = ["paper", "thesis", "article", "local_note", "book", "lecture", "derivation"]
        numerical_types = ["benchmark", "code", "implementation", "numerical", "experiment"]

        if any(t in source_types for t in formal_types):
            distilled_lane = "formal_theory"
            # 根据 source 特性生成更具体的 first_validation_route
            if "thesis" in source_types:
                distilled_first_validation_route = (
                    f"Extract the core thesis claim from {', '.join(all_titles[:2])}, "
                    "then identify the key definitions and first bounded proof obligation."
                )
            else:
                distilled_first_validation_route = (
                    "Derive the first bounded question from the source material, "
                    "then identify the key definitions and proof obligations."
                )
        elif any(t in source_types for t in numerical_types):
            distilled_lane = "toy_numeric"
            distilled_first_validation_route = (
                "Reproduce the baseline benchmark before trusting new results. "
                "then validate the observable definitions and normalization."
            )
        else:
            distilled_lane = "code_method"
            distilled_first_validation_route = (
                "Define the scope boundaries and first validation artifact."
            )

        return {
            "distilled_initial_idea": distilled_initial_idea,
            "distilled_novelty_target": distilled_novelty_target,
            "distilled_first_validation_route": distilled_first_validation_route,
            "distilled_lane": distilled_lane,
        }

    def _coalesce_string(self, existing: Any, *defaults: str) -> str:
        """Coalesce existing value with multiple fallback defaults.

        Args:
            existing: The existing value to check first
            *defaults: One or more fallback values, tried in order

        Returns:
            The first non-empty string among existing and defaults
        """
        resolved = str(existing or "").strip()
        if resolved:
            return resolved
        for default in defaults:
            candidate = str(default or "").strip()
            if candidate:
                return candidate
        return ""

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

    def _formal_theory_projection_candidate_context(
        self,
        *,
        topic_slug: str,
        run_id: str | None,
        candidate_rows: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        if not run_id:
            return None
        fallback: dict[str, Any] | None = None
        for row in candidate_rows:
            candidate_id = str(row.get("candidate_id") or "").strip()
            candidate_type = str(row.get("candidate_type") or "").strip()
            if not candidate_id or candidate_type not in self._theory_formal_candidate_types():
                continue
            packet_paths = self._theory_packet_paths(topic_slug, run_id, candidate_id)
            review_path = packet_paths["formal_theory_review"]
            review_payload = read_json(review_path) if review_path.exists() else None
            review_status = str(
                (review_payload or {}).get("overall_status")
                or row.get("formal_theory_review_overall_status")
                or "missing"
            ).strip()
            completion_status = str(row.get("topic_completion_status") or "not_assessed").strip()
            context = {
                "candidate_row": row,
                "candidate_id": candidate_id,
                "candidate_type": candidate_type,
                "review_path": review_path,
                "review_payload": review_payload or {},
                "review_status": review_status,
                "completion_status": completion_status,
            }
            if fallback is None:
                fallback = context
            if review_path.exists() and review_status == "ready" and completion_status in {"promotion-ready", "promoted"}:
                return context
        return fallback

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

    def _derive_collaborator_memory_summary(self) -> dict[str, Any]:
        paths = self._collaborator_memory_paths()
        payload = read_json(paths["json"]) or {}
        preferences = self._dedupe_strings(list(payload.get("preferences") or []))
        preferred_lanes = self._dedupe_strings(list(payload.get("preferred_lanes") or []))
        avoided_patterns = self._dedupe_strings(list(payload.get("avoided_patterns") or []))
        concerns = self._dedupe_strings(list(payload.get("long_horizon_concerns") or []))
        collaboration_style = self._dedupe_strings(list(payload.get("collaboration_style") or []))
        if payload:
            status = "available"
            summary = (
                "Collaborator-specific preferences and long-horizon concerns are available. "
                "Use them as steering context, not as canonical scientific memory."
            )
        else:
            status = "absent"
            summary = "No collaborator-specific memory is currently recorded."
        return {
            "memory_kind": "collaborator_memory",
            "status": status,
            "preference_count": len(preferences),
            "preferences": preferences,
            "preferred_lanes": preferred_lanes,
            "avoided_pattern_count": len(avoided_patterns),
            "avoided_patterns": avoided_patterns,
            "long_horizon_concern_count": len(concerns),
            "long_horizon_concerns": concerns,
            "collaboration_style": collaboration_style,
            "path": self._relativize(paths["json"]) if paths["json"].exists() else None,
            "note_path": self._relativize(paths["note"]) if paths["note"].exists() else None,
            "summary": summary,
        }

    def _topic_staging_entries(self, topic_slug: str) -> list[dict[str, Any]]:
        entry_root = self.kernel_root / "canonical" / "staging" / "entries"
        if not entry_root.exists():
            return []
        rows: list[dict[str, Any]] = []
        for path in sorted(entry_root.glob("staging--*.json")):
            payload = read_json(path) or {}
            if str(payload.get("topic_slug") or "").strip() != topic_slug:
                continue
            rows.append(
                {
                    **payload,
                    "path": self._relativize(path),
                }
            )
        return rows

    def _origin_ref_strings(self, origin_refs: list[Any]) -> list[str]:
        refs: list[str] = []
        for row in origin_refs:
            if isinstance(row, str):
                value = row.strip()
                if value:
                    refs.append(value)
                continue
            if not isinstance(row, dict):
                continue
            for key in ("path", "id", "title"):
                value = str(row.get(key) or "").strip()
                if value:
                    refs.append(value)
                    break
        return self._dedupe_strings(refs)

    def _source_fidelity_class(self, row: dict[str, Any]) -> str:
        source_type = str(row.get("source_type") or "").strip().lower()
        if source_type in {"journal", "peer_reviewed_paper", "peer_reviewed_article", "published_paper"}:
            return "peer_reviewed"
        if source_type in {"paper", "arxiv", "preprint"}:
            return "preprint"
        if source_type in {"thesis", "dissertation"}:
            return "thesis"
        if source_type in {"book", "monograph", "lecture_notes", "review_article"}:
            return "formal_reference"
        if source_type in {"blog", "informal_note", "note", "webpage", "forum", "video", "talk", "verbal_claim"}:
            return "informal"
        if source_type in {"code", "repository", "numerical", "dataset", "software_doc", "local"}:
            return "code_artifact"
        return "unknown"

    def _source_fidelity_summary(self, fidelity_counts: dict[str, int]) -> str:
        nonzero = {key: value for key, value in fidelity_counts.items() if value > 0}
        if not nonzero:
            return "No registered source fidelity signal is currently available."
        ordered = sorted(nonzero.items(), key=lambda item: (-item[1], item[0]))
        parts = [f"{value} {key.replace('_', ' ')}" for key, value in ordered]
        if len(nonzero) == 1:
            return f"Current source basis is dominated by {parts[0]} evidence."
        return f"Current source basis mixes {'; '.join(parts)} evidence."

    def _infer_reading_depth(
        self,
        *,
        intake_stage: str,
        notation_table_path: Path,
        assumption_table_path: Path,
        regime_table_path: Path,
        claim_extraction_path: Path,
        explicit_value: str,
    ) -> str:
        if explicit_value:
            return explicit_value
        if all(path.exists() for path in (notation_table_path, assumption_table_path, regime_table_path, claim_extraction_path)):
            return "structured_reconstruction"
        if intake_stage == "technical_understanding" and notation_table_path.exists() and assumption_table_path.exists():
            return "technical_reconstruction"
        if notation_table_path.exists() or assumption_table_path.exists():
            return "partial_reconstruction"
        if intake_stage and intake_stage != "missing":
            return "source_preview"
        return "missing"

    def _infer_assumption_quality(
        self,
        *,
        assumption_table_path: Path,
        claim_extraction_path: Path,
        explicit_value: str,
    ) -> str:
        if explicit_value:
            return explicit_value
        if assumption_table_path.exists() and claim_extraction_path.exists():
            return "structured"
        if assumption_table_path.exists():
            return "partial"
        return "missing"

    def _citation_graph_signals(self, source_rows: list[dict[str, Any]]) -> dict[str, Any]:
        arxiv_id_count = 0
        bibtex_signal_count = 0
        citation_signal_count = 0
        for row in source_rows:
            provenance = row.get("provenance") or {}
            if str(row.get("arxiv_id") or provenance.get("arxiv_id") or provenance.get("versioned_id") or "").strip():
                arxiv_id_count += 1
            if str(row.get("bibtex_key") or provenance.get("bibtex_key") or provenance.get("doi") or "").strip():
                bibtex_signal_count += 1
            references = row.get("references") or provenance.get("references") or row.get("citations") or []
            if isinstance(references, list) and references:
                citation_signal_count += 1
        status = "present" if any((arxiv_id_count, bibtex_signal_count, citation_signal_count)) else "missing"
        if status == "present":
            summary = (
                f"Source graph signals: arXiv-backed={arxiv_id_count}, "
                f"BibTeX/DOI-backed={bibtex_signal_count}, cited-reference rows={citation_signal_count}."
            )
        else:
            summary = "No citation-graph or BibTeX-style source signals are currently registered."
        return {
            "arxiv_id_count": arxiv_id_count,
            "bibtex_signal_count": bibtex_signal_count,
            "citation_signal_count": citation_signal_count,
            "citation_graph_status": status,
            "citation_graph_summary": summary,
        }

    def _derive_l0_sources_projection(
        self,
        *,
        topic_slug: str,
        backend_bridges: list[dict[str, Any]],
    ) -> dict[str, Any]:
        source_index_path = self.kernel_root / "source-layer" / "topics" / topic_slug / "source_index.jsonl"
        source_rows = read_jsonl(source_index_path)
        source_ids = self._dedupe_strings(
            [str(row.get("source_id") or "").strip() for row in source_rows if str(row.get("source_id") or "").strip()]
        )
        source_titles = self._dedupe_strings(
            [str(row.get("title") or "").strip() for row in source_rows if str(row.get("title") or "").strip()]
        )
        source_types = self._dedupe_strings(
            [str(row.get("source_type") or "").strip() for row in source_rows if str(row.get("source_type") or "").strip()]
        )
        fidelity_counts = {
            "peer_reviewed": 0,
            "preprint": 0,
            "thesis": 0,
            "formal_reference": 0,
            "informal": 0,
            "code_artifact": 0,
            "unknown": 0,
        }
        for row in source_rows:
            fidelity_counts[self._source_fidelity_class(row)] += 1
        highest_fidelity_class = next(
            (
                key
                for key in (
                    "peer_reviewed",
                    "preprint",
                    "thesis",
                    "formal_reference",
                    "code_artifact",
                    "informal",
                    "unknown",
                )
                if fidelity_counts[key] > 0
            ),
            "unknown",
        )
        fidelity_summary = self._source_fidelity_summary(fidelity_counts)
        citation_signals = self._citation_graph_signals(source_rows)
        if source_rows:
            status = "present"
            summary = (
                f"{len(source_rows)} registered source(s) are available for fresh reading and source recovery. "
                f"{fidelity_summary} {citation_signals['citation_graph_summary']}"
            )
        else:
            status = "missing"
            summary = "No registered L0 source packet is currently available for this topic."
        return {
            "subplane": "L0",
            "status": status,
            "summary": summary,
            "primary_output_path": self._relativize(source_index_path),
            "source_count": len(source_rows),
            "source_ids": source_ids,
            "source_titles": source_titles,
            "source_types": source_types,
            "source_fidelity_counts": fidelity_counts,
            "highest_fidelity_class": highest_fidelity_class,
            "source_fidelity_summary": fidelity_summary,
            "arxiv_id_count": citation_signals["arxiv_id_count"],
            "bibtex_signal_count": citation_signals["bibtex_signal_count"],
            "citation_signal_count": citation_signals["citation_signal_count"],
            "citation_graph_status": citation_signals["citation_graph_status"],
            "citation_graph_summary": citation_signals["citation_graph_summary"],
            "backend_bridge_count": len(backend_bridges),
            "next_allowed_transitions": ["L1", "L3-A", "L4"],
            "consumed_by": ["L1", "L3-A", "L4", "H-plane"],
        }

    def _derive_l1_understanding_projection(self, *, topic_slug: str) -> dict[str, Any]:
        intake_root = self.kernel_root / "intake" / "topics" / topic_slug
        intake_status_path = intake_root / "status.json"
        intake_status = read_json(intake_status_path) or {}
        notation_table_path = intake_root / "notation_table.md"
        assumption_table_path = intake_root / "assumption_table.md"
        regime_table_path = intake_root / "regime_table.md"
        claim_extraction_path = intake_root / "claim_extraction.md"
        artifact_paths = []
        if intake_root.exists():
            for path in sorted(intake_root.glob("*")):
                if path.name == "status.json":
                    continue
                artifact_paths.append(self._relativize(path))
        intake_stage = str(intake_status.get("stage") or ("present" if intake_root.exists() else "missing")).strip()
        next_stage = str(intake_status.get("next_stage") or "").strip()
        reading_depth = self._infer_reading_depth(
            intake_stage=intake_stage or "missing",
            notation_table_path=notation_table_path,
            assumption_table_path=assumption_table_path,
            regime_table_path=regime_table_path,
            claim_extraction_path=claim_extraction_path,
            explicit_value=str(intake_status.get("reading_depth") or "").strip(),
        )
        assumption_quality = self._infer_assumption_quality(
            assumption_table_path=assumption_table_path,
            claim_extraction_path=claim_extraction_path,
            explicit_value=str(intake_status.get("assumption_quality") or "").strip(),
        )
        if intake_root.exists() or intake_status:
            status = "present"
            summary = str(intake_status.get("summary") or "").strip() or (
                "Layer 1 understanding artifacts are present and can feed topic analysis or validation."
            )
        else:
            status = "missing"
            summary = "No durable L1 understanding packet is currently available for this topic."
        return {
            "subplane": "L1",
            "status": status,
            "summary": summary,
            "primary_output_path": self._relativize(intake_status_path),
            "intake_stage": intake_stage or "missing",
            "next_stage": next_stage or None,
            "reading_depth": reading_depth,
            "assumption_quality": assumption_quality,
            "notation_table_path": self._relativize(notation_table_path) if notation_table_path.exists() else None,
            "assumption_table_path": self._relativize(assumption_table_path) if assumption_table_path.exists() else None,
            "regime_table_path": self._relativize(regime_table_path) if regime_table_path.exists() else None,
            "claim_extraction_path": self._relativize(claim_extraction_path) if claim_extraction_path.exists() else None,
            "available_artifact_paths": artifact_paths,
            "next_allowed_transitions": ["L3-A", "L4", "L3-D"],
            "consumed_by": ["L3-A", "L4", "L3-D", "H-plane"],
        }

    def _derive_l4_validation_projection(
        self,
        *,
        topic_slug: str,
        topic_state: dict[str, Any],
        validation_contract: dict[str, Any],
        topic_status_explainability: dict[str, Any],
    ) -> dict[str, Any]:
        last_evidence_return = topic_status_explainability.get("last_evidence_return") or self._derive_last_evidence_return(
            topic_state=topic_state,
            validation_contract=validation_contract,
        )
        evidence_status = str(last_evidence_return.get("status") or "missing").strip()
        evidence_path = str(last_evidence_return.get("path") or "").strip()
        if evidence_status == "present":
            status = "active"
            summary = str(last_evidence_return.get("summary") or "").strip() or (
                "A durable validation-return artifact is present for this topic."
            )
            primary_output_path = evidence_path or self._relativize(self._validation_contract_paths(topic_slug)["json"])
        elif str(validation_contract.get("status") or "").strip():
            status = "planned"
            summary = "Validation is contract-defined, but no durable return artifact is recorded yet."
            primary_output_path = (
                str(validation_contract.get("path") or "").strip()
                or self._relativize(self._validation_contract_paths(topic_slug)["json"])
            )
        else:
            status = "missing"
            summary = "No explicit Layer 4 validation projection is currently available for this topic."
            primary_output_path = self._relativize(self._validation_contract_paths(topic_slug)["json"])
        return {
            "subplane": "L4",
            "status": status,
            "summary": summary,
            "primary_output_path": primary_output_path,
            "validation_mode": str(validation_contract.get("validation_mode") or ""),
            "verification_focus": str(validation_contract.get("verification_focus") or ""),
            "analytic_check_families": self._dedupe_strings(list(validation_contract.get("analytic_check_families") or [])),
            "evidence_status": evidence_status,
            "evidence_kind": str(last_evidence_return.get("kind") or "none"),
            "evidence_path": evidence_path,
            "record_id": str(last_evidence_return.get("record_id") or ""),
            "next_allowed_transitions": ["L3-R", "H-plane"],
            "consumed_by": ["L3-R", "H-plane"],
        }

    def _canonical_l2_graph_surface(self) -> dict[str, Any]:
        canonical_index_path = self.kernel_root / "canonical" / "index.jsonl"
        canonical_edges_path = self.kernel_root / "canonical" / "edges.jsonl"
        canonical_index_rows = read_jsonl(canonical_index_path)
        canonical_edge_rows = read_jsonl(canonical_edges_path)
        canonical_unit_types = sorted(
            {
                str(row.get("unit_type") or "").strip()
                for row in canonical_index_rows
                if str(row.get("unit_type") or "").strip()
            }
        )
        if canonical_index_rows or canonical_edge_rows:
            status = "seeded"
            summary = (
                f"Canonical L2 graph is seeded with {len(canonical_index_rows)} units and "
                f"{len(canonical_edge_rows)} edges across {len(canonical_unit_types)} unit types."
            )
        else:
            status = "empty"
            summary = (
                "Canonical L2 graph is currently empty, so consultation may expose only "
                "local topic traces or staging instead of substantive reusable graph memory."
            )
        return {
            "index_path": self._relativize(canonical_index_path),
            "edges_path": self._relativize(canonical_edges_path),
            "unit_count": len(canonical_index_rows),
            "edge_count": len(canonical_edge_rows),
            "unit_types": canonical_unit_types,
            "status": status,
            "summary": summary,
        }

    def _derive_l2_memory_projection(
        self,
        *,
        topic_slug: str,
        topic_state: dict[str, Any],
        promotion_readiness: dict[str, Any],
        promotion_gate: dict[str, Any],
        topic_skill_projection: dict[str, Any],
        candidate_rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        graph_surface = self._canonical_l2_graph_surface()
        consultation_index_path = self._normalize_artifact_path(
            (topic_state.get("pointers") or {}).get("consultation_index_path")
        ) or self._relativize(self._consultation_root(topic_slug) / "consultation_index.jsonl")
        consultation_rows = read_jsonl(self._consultation_root(topic_slug) / "consultation_index.jsonl")
        staging_entries = self._topic_staging_entries(topic_slug)
        intended_l2_targets = self._dedupe_strings(
            [
                str(topic_skill_projection.get("intended_l2_target") or "").strip(),
                *[
                    str(target).strip()
                    for row in candidate_rows
                    for target in (row.get("intended_l2_targets") or [])
                    if str(target).strip()
                ],
                *[
                    str(value).strip()
                    for value in (promotion_readiness.get("ready_candidate_ids") or [])
                    if str(value).strip()
                ],
            ]
        )
        promoted_units = self._dedupe_strings(list(promotion_gate.get("promoted_units") or []))
        if consultation_rows or staging_entries or intended_l2_targets or promoted_units:
            status = "active"
            summary = "Layer 2 memory surfaces are active through consultation, staging, or writeback readiness."
        elif str(graph_surface.get("status") or "") == "seeded":
            status = "quiet"
            summary = "Canonical Layer 2 graph memory is seeded, but no strong topic-local consultation or writeback signal is currently active."
        else:
            status = "quiet"
            summary = "No strong Layer 2 consultation or writeback signal is currently active for this topic."
        latest_consultation = consultation_rows[-1] if consultation_rows else {}
        latest_consultation_id = str((latest_consultation or {}).get("consultation_id") or "").strip()
        consultation_surface = {
            "consultation_index_path": consultation_index_path,
            "consultation_count": len(consultation_rows),
            "latest_consultation_id": latest_consultation_id,
            "latest_query_text": str((latest_consultation or {}).get("query_text") or "").strip(),
            "latest_summary": str((latest_consultation or {}).get("summary") or "").strip(),
            "latest_application_path": str((latest_consultation or {}).get("application_path") or "").strip(),
            "latest_summary_note_path": str((latest_consultation or {}).get("summary_note_path") or "").strip(),
            "latest_memory_map_path": str((latest_consultation or {}).get("memory_map_path") or "").strip(),
            "latest_memory_map_note_path": str((latest_consultation or {}).get("memory_map_note_path") or "").strip(),
        }
        writeback_surface = {
            "promotion_gate_status": str(promotion_gate.get("status") or "not_requested"),
            "staging_entry_count": len(staging_entries),
            "staging_entry_ids": self._dedupe_strings(
                [str(row.get("entry_id") or "").strip() for row in staging_entries if str(row.get("entry_id") or "").strip()]
            ),
            "intended_l2_targets": intended_l2_targets,
            "promoted_unit_count": len(promoted_units),
            "promoted_units": promoted_units,
        }
        return {
            "subplane": "L2",
            "status": status,
            "summary": summary,
            "primary_output_path": consultation_index_path,
            "consultation_count": len(consultation_rows),
            "staging_entry_count": len(staging_entries),
            "staging_entry_ids": writeback_surface["staging_entry_ids"],
            "intended_l2_targets": intended_l2_targets,
            "promotion_gate_status": str(promotion_gate.get("status") or "not_requested"),
            "promoted_unit_count": len(promoted_units),
            "promoted_units": promoted_units,
            "consultation_surface": consultation_surface,
            "writeback_surface": writeback_surface,
            "graph_surface": graph_surface,
            "next_allowed_transitions": ["L3-A", "L3-D", "H-plane"],
            "consumed_by": ["L3-A", "L3-D", "H-plane"],
        }

    def _derive_l3_subplanes(
        self,
        *,
        topic_slug: str,
        latest_run_id: str,
        candidate_rows: list[dict[str, Any]],
        selected_pending_action: dict[str, Any] | None,
        result_brief: dict[str, Any],
        topic_status_explainability: dict[str, Any],
        promotion_readiness_path: str,
        promotion_readiness: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        candidate_ids = self._dedupe_strings(
            [str(row.get("candidate_id") or "").strip() for row in candidate_rows if str(row.get("candidate_id") or "").strip()]
        )
        selected_action_summary = str((selected_pending_action or {}).get("summary") or "").strip()
        if latest_run_id:
            analysis_primary_output_path = self._relativize(self._candidate_ledger_path(topic_slug, latest_run_id))
        else:
            analysis_primary_output_path = self._relativize(self.kernel_root / "feedback" / "topics" / topic_slug)
        if candidate_ids:
            analysis_status = "active"
            analysis_summary = (
                f"{len(candidate_ids)} candidate ledger item(s) are shaping the current topic analysis."
            )
        elif selected_action_summary:
            analysis_status = "route_selected_without_candidates"
            analysis_summary = (
                "A bounded next action is selected, but no candidate-ledger artifact has been recorded yet."
            )
        else:
            analysis_status = "idle"
            analysis_summary = "No durable topic-analysis packet is currently recorded."
        analysis = {
            "subplane": "L3-A",
            "status": analysis_status,
            "summary": analysis_summary,
            "primary_output_path": analysis_primary_output_path,
            "supporting_output_paths": [],
            "candidate_count": len(candidate_ids),
            "candidate_ids": candidate_ids,
            "selected_action_summary": selected_action_summary,
            "mandatory_inputs": ["L0", "L1", "L2 consult"],
            "next_allowed_transitions": ["L4", "L0", "L1"],
            "consumed_by": ["L4", "L0", "L1", "H-plane"],
        }

        last_evidence_return = topic_status_explainability.get("last_evidence_return") or {}
        evidence_status = str(last_evidence_return.get("status") or "missing").strip()
        if evidence_status == "present":
            result_integration_status = "active"
            result_integration_summary = str(last_evidence_return.get("summary") or "").strip() or (
                "A durable L4 return is present and awaits interpretation routing."
            )
        elif candidate_rows or selected_action_summary:
            result_integration_status = "awaiting_l4_return"
            result_integration_summary = "No durable L4 return is currently recorded for this topic."
        else:
            result_integration_status = "idle"
            result_integration_summary = "Result integration is idle because no bounded validation return is present."
        result_integration = {
            "subplane": "L3-R",
            "status": result_integration_status,
            "summary": result_integration_summary,
            "primary_output_path": str(result_brief.get("path") or ""),
            "supporting_output_paths": self._dedupe_strings(
                [
                    str(result_brief.get("note_path") or ""),
                    str(last_evidence_return.get("path") or ""),
                ]
            ),
            "evidence_status": evidence_status,
            "evidence_kind": str(last_evidence_return.get("kind") or "none"),
            "record_id": str(last_evidence_return.get("record_id") or ""),
            "mandatory_inputs": ["L4"],
            "next_allowed_transitions": ["L3-A", "L3-D", "L0", "L1"],
            "consumed_by": ["L3-A", "L3-D", "H-plane"],
        }

        staging_entries = self._topic_staging_entries(topic_slug)
        staging_entry_ids = self._dedupe_strings(
            [str(row.get("entry_id") or "").strip() for row in staging_entries if str(row.get("entry_id") or "").strip()]
        )
        staging_entry_paths = self._dedupe_strings(
            [str(row.get("path") or "").strip() for row in staging_entries if str(row.get("path") or "").strip()]
        )
        intended_l2_targets = self._dedupe_strings(
            [
                str(target).strip()
                for row in candidate_rows
                for target in (row.get("intended_l2_targets") or [])
                if str(target).strip()
            ]
        )
        ready_candidate_ids = self._dedupe_strings(list(promotion_readiness.get("ready_candidate_ids") or []))
        writeback_blockers = self._dedupe_strings(list(promotion_readiness.get("blockers") or []))
        if ready_candidate_ids or staging_entry_ids or intended_l2_targets:
            distillation_status = "active"
            distillation_summary = (
                "Distillation outputs are present and can route toward staging or canonical L2 under the current gate rules."
            )
        elif candidate_rows:
            distillation_status = "pending"
            distillation_summary = "Candidate shaping exists, but no staging or promotion-ready distillation output is recorded yet."
        else:
            distillation_status = "idle"
            distillation_summary = "No durable distillation output is currently recorded."
        distillation = {
            "subplane": "L3-D",
            "status": distillation_status,
            "summary": distillation_summary,
            "primary_output_path": promotion_readiness_path,
            "supporting_output_paths": staging_entry_paths,
            "ready_candidate_ids": ready_candidate_ids,
            "staging_entry_ids": staging_entry_ids,
            "staging_entry_paths": staging_entry_paths,
            "intended_l2_targets": intended_l2_targets,
            "writeback_blockers": writeback_blockers,
            "mandatory_inputs": ["L3-R"],
            "next_allowed_transitions": ["staging", "L2", "L3-A", "L1"],
            "consumed_by": ["canonical/staging/", "L2", "H-plane"],
            "forbidden_direct_transitions": ["L4->L2"],
            "mandatory_routing_rule": "L4 outputs must return to L3-R before any L2 writeback decision.",
        }

        return {
            "analysis": analysis,
            "result_integration": result_integration,
            "distillation": distillation,
        }

    def _derive_interaction_contract(
        self,
        *,
        topic_slug: str | None = None,
        human_request: str | None = None,
        idea_packet: dict[str, Any],
        operator_checkpoint: dict[str, Any],
        pending_decisions: dict[str, Any],
        promotion_readiness: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        checkpoint_status = str(operator_checkpoint.get("status") or "").strip()
        idea_status = str(idea_packet.get("status") or "").strip()
        blocking_count = int(pending_decisions.get("blocking_count") or 0)
        blocking_ids = [
            str(item).strip()
            for item in (pending_decisions.get("blocking_ids") or [])
            if str(item).strip()
        ]
        if checkpoint_status == "requested":
            stop_reason = str(operator_checkpoint.get("question") or "").strip()
            if not stop_reason:
                stop_reason = "; ".join(
                    str(item).strip()
                    for item in (operator_checkpoint.get("blocker_summary") or [])
                    if str(item).strip()
                )
            if not stop_reason:
                stop_reason = "Resolve the active operator checkpoint before deeper execution."
            return {
                "interaction_class": "checkpoint_question",
                "stop_status": "checkpoint_required",
                "stop_reason": stop_reason,
                "primary_result_shape": "checkpoint_card",
            }
        if blocking_count > 0:
            if blocking_ids:
                stop_reason = f"Blocking pending decisions require resolution: {', '.join(blocking_ids)}."
            else:
                stop_reason = "Blocking pending decisions require resolution before deeper execution."
            return {
                "interaction_class": "checkpoint_question",
                "stop_status": "checkpoint_required",
                "stop_reason": stop_reason,
                "primary_result_shape": "checkpoint_card",
            }
        if idea_status == "needs_clarification":
            stop_reason = str(idea_packet.get("status_reason") or "").strip()
            if not stop_reason:
                stop_reason = "; ".join(
                    str(item).strip()
                    for item in (idea_packet.get("clarification_questions") or [])
                    if str(item).strip()
                )
            if not stop_reason:
                stop_reason = "Clarify the idea packet before deeper execution."
            return {
                "interaction_class": "checkpoint_question",
                "stop_status": "checkpoint_required",
                "stop_reason": stop_reason,
                "primary_result_shape": "checkpoint_card",
            }
        update_reasons: list[str] = []
        if topic_slug:
            consultation_rows = read_jsonl(self._consultation_root(topic_slug) / "consultation_index.jsonl")
            latest_consultation = consultation_rows[-1] if consultation_rows else {}
            if str((latest_consultation or {}).get("summary_note_path") or "").strip():
                update_reasons.append("A new consultation summary is available for operator review.")
            staged_entry_count = len(self._topic_staging_entries(topic_slug))
            if staged_entry_count > 0:
                noun = "entry" if staged_entry_count == 1 else "entries"
                update_reasons.append(f"{staged_entry_count} staged memory {noun} are now available.")
        promotion_status = str((promotion_readiness or {}).get("status") or "").strip()
        if promotion_status in {"approved", "promoted", "blocked"}:
            update_reasons.append(f"Promotion readiness changed to `{promotion_status}`.")
        if update_reasons:
            return {
                "interaction_class": "non_blocking_update",
                "stop_status": "continue",
                "stop_reason": " ".join(update_reasons),
                "primary_result_shape": "result_brief",
            }
        task_type = str(idea_packet.get("task_type") or "").strip()
        if task_type == "open_exploration":
            return {
                "interaction_class": "free_explore",
                "stop_status": "continue",
                "stop_reason": "Open exploration is active, so bounded speculative analysis may continue before a harder route commitment is required.",
                "primary_result_shape": "status_update",
            }
        if task_type == "conjecture_attempt" and self._request_prefers_exploration(human_request):
            return {
                "interaction_class": "free_explore",
                "stop_status": "continue",
                "stop_reason": "Conjecture-shaping work is still exploratory, so bounded route comparison may continue before a harder commitment is required.",
                "primary_result_shape": "status_update",
            }
        if self._request_prefers_exploration(human_request):
            return {
                "interaction_class": "free_explore",
                "stop_status": "continue",
                "stop_reason": "Bounded exploratory analysis may continue before a harder route or writeback commitment is required.",
                "primary_result_shape": "status_update",
            }
        return {
            "interaction_class": "silent_continue",
            "stop_status": "continue",
            "stop_reason": "Ready to continue bounded execution.",
            "primary_result_shape": "status_update",
        }

    def _request_looks_actionable(self, request: str | None) -> bool:
        raw_request = str(request or "").strip()
        if not raw_request:
            return False
        normalized = raw_request.lower()
        actionable_cues = (
            "define",
            "scope",
            "benchmark",
            "validate",
            "validation",
            "derive",
            "derivation",
            "prove",
            "proof",
            "explore",
            "analyze",
            "analysis",
            "survey",
            "plan",
            "compare",
            "check",
            "build",
            "implement",
            "establish",
            "建立",
            "定义",
            "范围",
            "验证",
            "推导",
            "证明",
            "探索",
            "分析",
            "调研",
            "计划",
            "比较",
            "检查",
            "实现",
        )
        if any(cue in normalized for cue in actionable_cues):
            return True
        token_count = len(re.findall(r"[A-Za-z0-9_]+", raw_request))
        return token_count > 8 or len(raw_request) > 80

    def _request_prefers_exploration(self, request: str | None) -> bool:
        raw_request = str(request or "").strip()
        if not raw_request:
            return False
        normalized = raw_request.lower()
        exploratory_cues = (
            "explore",
            "speculate",
            "brainstorm",
            "possible bridge",
            "possible bridges",
            "what if",
            "idea",
            "intuition",
            "open question",
            "探索",
            "想法",
            "直觉",
            "猜想",
            "关联",
            "联系",
            "可能",
        )
        hard_commit_cues = (
            "implement",
            "build",
            "benchmark",
            "validate",
            "validation",
            "promote",
            "writeback",
            "prove",
            "proof",
            "formalize",
            "run ",
            "execute",
            "实现",
            "验证",
            "写回",
            "提升",
            "证明",
        )
        return any(cue in normalized for cue in exploratory_cues) and not any(
            cue in normalized for cue in hard_commit_cues
        )

    def _infer_task_type(self, request: str | None) -> str:
        normalized = str(request or "").strip().lower()
        if not normalized:
            return "open_exploration"
        target_driven_cues = (
            "implement",
            "implementation",
            "build",
            "finite-temperature",
            "finite temperature",
            "librpa",
            "librpa",
            "run ",
            "execute",
            "derive the",
            "prove the",
            "实现",
            "跑",
            "执行",
            "基准",
            "有限温",
        )
        exploration_cues = (
            "explore",
            "discussion",
            "discuss",
            "brainstorm",
            "possible",
            "maybe",
            "idea",
            "ideas",
            "open question",
            "可能",
            "想法",
            "讨论",
            "探索",
        )
        conjecture_cues = (
            "plausible bridge",
            "whether there is",
            "connection",
            "link between",
            "structural link",
            "conjecture",
            "hypothesis",
            "bridge between",
            "关联",
            "联系",
            "桥接",
            "猜想",
        )
        if any(cue in normalized for cue in exploration_cues):
            return "open_exploration"
        if any(cue in normalized for cue in conjecture_cues):
            return "conjecture_attempt"
        if any(cue in normalized for cue in target_driven_cues):
            return "target_driven_execution"
        return "target_driven_execution" if self._request_looks_actionable(request) else "open_exploration"

    def _derive_idea_packet(
        self,
        *,
        topic_slug: str,
        updated_by: str,
        human_request: str | None,
        topic_state: dict[str, Any],
        interaction_state: dict[str, Any],
        existing_idea_packet: dict[str, Any],
        existing_research: dict[str, Any],
        existing_validation: dict[str, Any],
        research_contract: dict[str, Any],
        validation_contract: dict[str, Any],
        selected_pending_action: dict[str, Any] | None,
    ) -> dict[str, Any]:
        source_rows = read_jsonl(self.kernel_root / "source-layer" / "topics" / topic_slug / "source_index.jsonl")
        request_text = (
            str(human_request or "").strip()
            or str(interaction_state.get("human_request") or "").strip()
        )
        actionable_request = self._request_looks_actionable(request_text)
        task_type = self._coalesce_string(
            existing_idea_packet.get("task_type"),
            existing_research.get("task_type"),
            self._infer_task_type(request_text),
        )

        # 从 source 中蒸馏信息（新增功能）
        distilled = self._distill_from_sources(source_rows or [], topic_slug)

        distilled_initial_idea = str(distilled.get("distilled_initial_idea") or "").strip()
        distilled_novelty_target = str(distilled.get("distilled_novelty_target") or "").strip()
        distilled_first_validation_route = str(
            distilled.get("distilled_first_validation_route") or ""
        ).strip()
        initial_idea = self._coalesce_string(
            existing_idea_packet.get("initial_idea"),
            str(existing_research.get("question") or "").strip(),
            distilled_initial_idea,
            request_text,
        )
        novelty_target = self._coalesce_string(
            existing_idea_packet.get("novelty_target"),
            distilled_novelty_target,
        )
        non_goals = self._coalesce_list(
            existing_idea_packet.get("non_goals"),
            list(existing_research.get("non_goals") or []),
        )
        first_validation_route = self._coalesce_string(
            existing_idea_packet.get("first_validation_route"),
            str(existing_validation.get("verification_focus") or "").strip()
            or str(validation_contract.get("verification_focus") or "").strip()
            or distilled_first_validation_route
            or str((selected_pending_action or {}).get("summary") or "").strip()
            or "Define the first bounded validation route before deeper execution.",
        )
        initial_evidence_bar = self._coalesce_string(
            existing_idea_packet.get("initial_evidence_bar"),
            str(existing_validation.get("acceptance_rule") or "").strip()
            or str(validation_contract.get("acceptance_rule") or "").strip()
            or "Require a durable first validation artifact before advancing the topic.",
        )

        missing_fields: list[str] = []
        if not initial_idea:
            missing_fields.append("initial_idea")
        if not novelty_target:
            missing_fields.append("novelty_target")
        if not non_goals:
            missing_fields.append("non_goals")
        if not first_validation_route:
            missing_fields.append("first_validation_route")
        if not initial_evidence_bar:
            missing_fields.append("initial_evidence_bar")

        execution_context_signals: list[str] = []
        if str(topic_state.get("latest_run_id") or "").strip():
            execution_context_signals.append("latest_run_id")
        if source_rows and (
            distilled_initial_idea
            or distilled_novelty_target
            or distilled_first_validation_route
        ):
            execution_context_signals.append("l0_sources")
        if str((selected_pending_action or {}).get("action_id") or "").strip():
            execution_context_signals.append("selected_action")
        explicit_shell_context = bool(
            str(existing_research.get("question") or "").strip()
            or list(existing_research.get("scope") or [])
            or list(existing_research.get("deliverables") or [])
            or str(existing_validation.get("verification_focus") or "").strip()
            or list(existing_validation.get("required_checks") or [])
        )
        if explicit_shell_context:
            execution_context_signals.append("existing_shell_contracts")

        existing_status = str(existing_idea_packet.get("status") or "").strip()
        fully_clarified_packet = bool(
            initial_idea
            and novelty_target
            and non_goals
            and first_validation_route
            and initial_evidence_bar
        )
        if existing_status == "deferred":
            status = existing_status
        elif execution_context_signals:
            status = "approved_for_execution"
        elif fully_clarified_packet:
            status = "approved_for_execution"
        elif initial_idea and first_validation_route and initial_evidence_bar and actionable_request:
            status = "approved_for_execution"
        else:
            status = "needs_clarification"

        status_reason = (
            "Approved for execution because durable topic context already exists."
            if status == "approved_for_execution" and execution_context_signals
            else (
                "Approved for execution because the idea packet now specifies a novelty target, first validation route, and evidence bar."
                if status == "approved_for_execution" and fully_clarified_packet
                else (
                    "Approved for execution because the request already specifies a concrete initial lane and evidence bar."
                    if status == "approved_for_execution"
                    else "Needs clarification because the topic is not yet specific enough to justify substantive execution."
                )
            )
        )

        clarification_questions: list[str] = []
        if status == "needs_clarification":
            if not actionable_request:
                clarification_questions.append(
                    "Should AITP first do scoped problem definition, literature scoping, benchmark reproduction, or derivation planning?"
                )
            if "initial_idea" in missing_fields:
                clarification_questions.append(
                    "What is the idea in one sentence, including the physical object, regime, and intended question?"
                )
            if "novelty_target" in missing_fields:
                clarification_questions.append(
                    "What exact novelty target should count as success beyond routine reproduction or literature summary?"
                )
            if "non_goals" in missing_fields:
                clarification_questions.append(
                    "What should this topic explicitly not try to solve in the first lane?"
                )
            if "first_validation_route" in missing_fields:
                clarification_questions.append(
                    "What is the first validation lane: literature scoping, analytic derivation, benchmark reproduction, or numerical pilot?"
                )
            if "initial_evidence_bar" in missing_fields:
                clarification_questions.append(
                    "What minimum evidence bar should justify continuing beyond the first bounded step?"
                )

        return {
            "topic_slug": topic_slug,
            "status": status,
            "task_type": task_type,
            "status_reason": status_reason,
            "initial_idea": initial_idea,
            "novelty_target": novelty_target,
            "non_goals": non_goals,
            "first_validation_route": first_validation_route,
            "initial_evidence_bar": initial_evidence_bar,
            "missing_fields": self._dedupe_strings(missing_fields),
            "clarification_questions": self._dedupe_strings(clarification_questions),
            "execution_context_signals": self._dedupe_strings(execution_context_signals),
            "updated_at": now_iso(),
            "updated_by": updated_by,
        }

    def _operator_checkpoint_signature(self, payload: dict[str, Any]) -> str:
        signature_payload = {
            "checkpoint_id": payload.get("checkpoint_id"),
            "checkpoint_kind": payload.get("checkpoint_kind"),
            "status": payload.get("status"),
            "trigger_fingerprint": payload.get("trigger_fingerprint"),
            "question": payload.get("question"),
            "required_response": payload.get("required_response"),
            "selected_action_id": payload.get("selected_action_id"),
            "answer": payload.get("answer"),
        }
        return json.dumps(signature_payload, ensure_ascii=True, sort_keys=True)

    def _derive_operator_checkpoint(
        self,
        *,
        topic_slug: str,
        updated_by: str,
        existing_checkpoint: dict[str, Any],
        idea_packet: dict[str, Any],
        research_contract: dict[str, Any],
        validation_contract: dict[str, Any],
        promotion_gate: dict[str, Any],
        selected_pending_action: dict[str, Any] | None,
        pending_decisions: dict[str, Any] | None,
        decision_surface: dict[str, Any],
        dashboard_path: Path,
        idea_packet_paths: dict[str, Path],
        research_paths: dict[str, Path],
        validation_paths: dict[str, Path],
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        selected_action_id = str((selected_pending_action or {}).get("action_id") or "").strip()
        selected_action_type = str((selected_pending_action or {}).get("action_type") or "").strip()
        selected_action_summary = str((selected_pending_action or {}).get("summary") or "").strip()
        selected_action_summary_lower = selected_action_summary.lower()
        promotion_status = str(promotion_gate.get("status") or "not_requested").strip()
        control_note_path = str(decision_surface.get("control_note_path") or "").strip()
        checkpoint_kind: str | None = None
        question = ""
        required_response = ""
        blocker_summary: list[str] = []
        evidence_refs: list[str] = []
        response_channels: list[str] = []

        if str(idea_packet.get("status") or "").strip() == "needs_clarification":
            checkpoint_kind = "scope_ambiguity"
            question = "AITP needs the initial topic intent clarified before substantive execution can continue."
            required_response = (
                "Fill the idea packet with a novelty target, non-goals, first validation route, and initial evidence bar."
            )
            blocker_summary = list(idea_packet.get("clarification_questions") or []) or [
                "Complete the missing intent fields in the idea packet."
            ]
            evidence_refs = [
                self._relativize(idea_packet_paths["note"]),
                self._relativize(research_paths["note"]),
                self._relativize(validation_paths["note"]),
            ]
            response_channels = [
                self._relativize(idea_packet_paths["note"]),
                self._relativize(research_paths["note"]),
                self._relativize(validation_paths["note"]),
            ]
        elif int((pending_decisions or {}).get("blocking_count") or 0) > 0:
            blocking_ids = [
                str(item).strip()
                for item in (pending_decisions or {}).get("blocking_ids") or []
                if str(item).strip()
            ]
            checkpoint_kind = "pending_decisions"
            if blocking_ids:
                question = f"Resolve blocking pending decisions before continuing: {', '.join(blocking_ids)}."
            else:
                question = "Resolve blocking pending decisions before continuing execution."
            required_response = "Close the blocking pending decisions and sync their durable traces."
            blocker_summary = [question]
            evidence_refs = [self._relativize(dashboard_path)]
            response_channels = [self._relativize(dashboard_path)]
        elif promotion_status in {"requested", "pending_human_approval"}:
            checkpoint_kind = "promotion_approval"
            candidate_id = str(promotion_gate.get("candidate_id") or "").strip() or "(missing)"
            backend_id = str(promotion_gate.get("backend_id") or "").strip() or "(missing)"
            question = f"Should AITP approve promotion for `{candidate_id}` into `{backend_id}`?"
            required_response = "Approve, reject, or narrow the current promotion request before writeback continues."
            blocker_summary = self._dedupe_strings(
                list(promotion_gate.get("promotion_blockers") or [])
                or ["Promotion is waiting for an explicit human decision."]
            )
            evidence_refs = self._dedupe_strings(
                [
                    self._relativize(self._promotion_gate_paths(topic_slug)["json"]),
                    self._relativize(self._promotion_gate_paths(topic_slug)["note"]),
                    self._relativize(dashboard_path),
                ]
            )
            response_channels = [
                self._relativize(self._promotion_gate_paths(topic_slug)["note"]),
                self._relativize(dashboard_path),
            ]
        elif any(needle in selected_action_summary_lower for needle in ("contradiction", "conflict", "regime mismatch")):
            checkpoint_kind = "contradiction_adjudication"
            question = "AITP found a contradiction-style blocker and needs the operator to choose the adjudication route."
            required_response = "Choose whether to split regimes, downgrade the claim, or return to L0 for source recovery."
            blocker_summary = [
                selected_action_summary or "An unresolved contradiction/regime conflict is active.",
                "Do not let the queue guess the adjudication route without an explicit operator choice.",
            ]
            evidence_refs = [
                self._relativize(self._gap_map_path(topic_slug)),
                self._relativize(validation_paths["note"]),
                self._relativize(dashboard_path),
            ]
            response_channels = [
                self._relativize(self._gap_map_path(topic_slug)),
                self._relativize(validation_paths["note"]),
            ]
        elif (
            selected_action_type in {"select_validation_route", "materialize_execution_task", "dispatch_execution_task"}
            or any(
                needle in selected_action_summary_lower
                for needle in ("validation route", "verification route", "benchmark", "selected route")
            )
        ):
            checkpoint_kind = "benchmark_or_validation_route_choice"
            question = "AITP needs an operator decision on the next benchmark or validation lane."
            required_response = "Choose the initial benchmark/validation route that should govern the next bounded step."
            blocker_summary = [
                selected_action_summary or "Validation-route choice remains unresolved.",
                "The active validation contract needs an explicit route choice before deeper execution.",
            ]
            evidence_refs = [
                self._relativize(validation_paths["note"]),
                self._relativize(dashboard_path),
            ]
            response_channels = [self._relativize(validation_paths["note"])]
        elif any(
            needle in selected_action_summary_lower
            for needle in ("resource limit", "risk limit", "compute budget", "system size", "larger-system", "budget")
        ):
            checkpoint_kind = "resource_risk_limit_choice"
            question = "AITP needs an operator decision on the acceptable resource or risk limit for the next lane."
            required_response = "State the permitted budget, system-size ceiling, or risk boundary before the next step expands."
            blocker_summary = [
                selected_action_summary or "The next lane requires an explicit resource/risk limit.",
            ]
            evidence_refs = [
                self._relativize(dashboard_path),
                self._relativize(validation_paths["note"]),
            ]
            response_channels = [self._relativize(dashboard_path)]
        elif any(
            needle in selected_action_summary_lower
            for needle in ("innovation direction", "novelty direction", "direction choice", "focus direction")
        ):
            checkpoint_kind = "novelty_direction_choice"
            question = "AITP needs an operator decision on the novelty direction before continuing."
            required_response = "Clarify which innovation target should dominate the current topic branch."
            blocker_summary = [
                selected_action_summary or "The current novelty direction remains ambiguous.",
            ]
            evidence_refs = [
                self._relativize(research_paths["note"]),
                self._relativize(dashboard_path),
            ]
            if control_note_path:
                evidence_refs.append(self._normalize_artifact_path(control_note_path) or control_note_path)
            response_channels = self._dedupe_strings(
                [self._normalize_artifact_path(control_note_path) or "", self._relativize(research_paths["note"])]
            )
        elif any(
            needle in selected_action_summary_lower
            for needle in ("continue or branch", "branch or redirect", "redirect decision", "stop or continue")
        ):
            checkpoint_kind = "stop_continue_branch_redirect_decision"
            question = "AITP needs an explicit stop/continue/branch/redirect decision from the operator."
            required_response = "Record whether the topic should continue, pause, branch, stop, or redirect."
            blocker_summary = [selected_action_summary or "The loop is waiting for an explicit operator steering decision."]
            evidence_refs = self._dedupe_strings(
                [self._normalize_artifact_path(control_note_path) or "", self._relativize(dashboard_path)]
            )
            response_channels = self._dedupe_strings([self._normalize_artifact_path(control_note_path) or ""])

        now = now_iso()
        existing_status = str(existing_checkpoint.get("status") or "").strip()
        existing_id = str(existing_checkpoint.get("checkpoint_id") or "").strip()
        existing_fingerprint = str(existing_checkpoint.get("trigger_fingerprint") or "").strip()

        if checkpoint_kind is None:
            payload = dict(existing_checkpoint or {})
            payload.setdefault("checkpoint_id", f"checkpoint:{topic_slug}:none")
            payload["topic_slug"] = topic_slug
            payload["run_id"] = str(existing_checkpoint.get("run_id") or "")
            payload["checkpoint_kind"] = None
            payload["status"] = "cancelled"
            payload["active"] = False
            payload["trigger_fingerprint"] = ""
            payload["question"] = "No active operator checkpoint is currently blocking execution."
            payload["required_response"] = "No operator response is currently required."
            payload["response_channels"] = []
            payload["blocker_summary"] = []
            payload["evidence_refs"] = []
            payload["selected_action_id"] = selected_action_id or None
            payload["selected_action_summary"] = selected_action_summary or None
            payload["answer"] = payload.get("answer")
            payload["requested_at"] = payload.get("requested_at")
            payload["requested_by"] = payload.get("requested_by")
            payload["answered_at"] = payload.get("answered_at")
            payload["answered_by"] = payload.get("answered_by")
            payload["updated_at"] = now if existing_status in {"requested", "answered"} else payload.get("updated_at") or now
            payload["updated_by"] = updated_by
            return payload, None

        checkpoint_id = f"checkpoint:{topic_slug}:{slugify(checkpoint_kind)}"
        trigger_fingerprint = "|".join(
            [
                checkpoint_kind,
                selected_action_id,
                promotion_status,
                ",".join(self._dedupe_strings(list(idea_packet.get("missing_fields") or []))),
                selected_action_summary,
            ]
        )
        payload = {
            "checkpoint_id": checkpoint_id,
            "topic_slug": topic_slug,
            "run_id": str(research_contract.get("run_id") or ""),
            "checkpoint_kind": checkpoint_kind,
            "status": "requested",
            "active": True,
            "trigger_fingerprint": trigger_fingerprint,
            "question": question,
            "required_response": required_response,
            "response_channels": self._dedupe_strings(response_channels),
            "blocker_summary": self._dedupe_strings(blocker_summary),
            "evidence_refs": self._dedupe_strings(evidence_refs),
            "selected_action_id": selected_action_id or None,
            "selected_action_summary": selected_action_summary or None,
            "answer": None,
            "requested_at": now,
            "requested_by": updated_by,
            "answered_at": None,
            "answered_by": None,
            "updated_at": now,
            "updated_by": updated_by,
        }
        superseded_payload: dict[str, Any] | None = None
        if existing_id == checkpoint_id and existing_fingerprint == trigger_fingerprint:
            if existing_status in {"requested", "answered"}:
                payload["status"] = existing_status
                payload["active"] = existing_status == "requested"
                payload["answer"] = existing_checkpoint.get("answer")
                payload["requested_at"] = existing_checkpoint.get("requested_at") or now
                payload["requested_by"] = existing_checkpoint.get("requested_by") or updated_by
                payload["answered_at"] = existing_checkpoint.get("answered_at")
                payload["answered_by"] = existing_checkpoint.get("answered_by")
                payload["updated_at"] = existing_checkpoint.get("updated_at") or now
                payload["updated_by"] = existing_checkpoint.get("updated_by") or updated_by
        elif existing_status in {"requested", "answered"} and existing_id and existing_id != checkpoint_id:
            superseded_payload = dict(existing_checkpoint)
            superseded_payload["status"] = "superseded"
            superseded_payload["active"] = False
            superseded_payload["updated_at"] = now
            superseded_payload["updated_by"] = updated_by
        return payload, superseded_payload

    def _render_operator_checkpoint_markdown(self, payload: dict[str, Any]) -> str:
        lines = [
            "# Operator checkpoint",
            "",
            f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
            f"- Checkpoint id: `{payload.get('checkpoint_id') or '(missing)'}`",
            f"- Kind: `{payload.get('checkpoint_kind') or '(none)'}`",
            f"- Status: `{payload.get('status') or '(missing)'}`",
            f"- Active: `{str(bool(payload.get('active'))).lower()}`",
            f"- Requested at: `{payload.get('requested_at') or '(missing)'}`",
            f"- Requested by: `{payload.get('requested_by') or '(missing)'}`",
            f"- Answered at: `{payload.get('answered_at') or '(none)'}`",
            f"- Answered by: `{payload.get('answered_by') or '(none)'}`",
            "",
            "## Question",
            "",
            payload.get("question") or "(missing)",
            "",
            "## Required response",
            "",
            payload.get("required_response") or "(missing)",
            "",
            "## Blocker summary",
            "",
        ]
        for item in payload.get("blocker_summary") or ["(none)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Response channels", ""])
        for item in payload.get("response_channels") or ["(none)"]:
            lines.append(f"- `{item}`")
        lines.extend(["", "## Evidence refs", ""])
        for item in payload.get("evidence_refs") or ["(none)"]:
            lines.append(f"- `{item}`")
        lines.extend(["", "## Current answer", ""])
        lines.append(payload.get("answer") or "(none yet)")
        return "\n".join(lines) + "\n"

    def _write_operator_checkpoint(
        self,
        *,
        topic_slug: str,
        payload: dict[str, Any],
        superseded_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        paths = self._operator_checkpoint_paths(topic_slug)
        ledger_rows = read_jsonl(paths["ledger"])
        if superseded_payload is not None:
            if not ledger_rows or self._operator_checkpoint_signature(ledger_rows[-1]) != self._operator_checkpoint_signature(
                superseded_payload
            ):
                ledger_rows.append(superseded_payload)
        if not ledger_rows or self._operator_checkpoint_signature(ledger_rows[-1]) != self._operator_checkpoint_signature(payload):
            ledger_rows.append(payload)
        write_json(paths["json"], payload)
        write_text(paths["note"], self._render_operator_checkpoint_markdown(payload))
        write_jsonl(paths["ledger"], ledger_rows)
        return {
            "operator_checkpoint_path": str(paths["json"]),
            "operator_checkpoint_note_path": str(paths["note"]),
            "operator_checkpoint_ledger_path": str(paths["ledger"]),
            "operator_checkpoint": payload,
        }

    def _refresh_operator_console_checkpoint_section(
        self,
        *,
        topic_slug: str,
        operator_checkpoint: dict[str, Any],
        topic_status_explainability: dict[str, Any] | None = None,
    ) -> None:
        operator_console_path = self._runtime_root(topic_slug) / "operator_console.md"
        if not operator_console_path.exists():
            return
        text = operator_console_path.read_text(encoding="utf-8")
        marker = "\n## Active operator checkpoint\n"
        if marker in text:
            text = text.split(marker, 1)[0].rstrip() + "\n"
        lines = [text.rstrip(), "", "## Active operator checkpoint", ""]
        lines.append(f"- Status: `{operator_checkpoint.get('status') or '(missing)'}`")
        lines.append(f"- Kind: `{operator_checkpoint.get('checkpoint_kind') or '(none)'}`")
        lines.append(f"- Question: {operator_checkpoint.get('question') or '(missing)'}")
        lines.append(
            f"- Open next: `{self._relativize(self._operator_checkpoint_paths(topic_slug)['note'])}`"
        )
        blocker_summary = operator_checkpoint.get("blocker_summary") or []
        if blocker_summary:
            lines.extend(["", "### Why it is blocked", ""])
            for item in blocker_summary:
                lines.append(f"- {item}")
        explainability = topic_status_explainability or {}
        if explainability:
            current_route_choice = explainability.get("current_route_choice") or {}
            last_evidence_return = explainability.get("last_evidence_return") or {}
            active_human_need = explainability.get("active_human_need") or {}
            lines.extend(
                [
                    "",
                    "## Topic explainability",
                    "",
                    f"- Why here: {explainability.get('why_this_topic_is_here') or '(missing)'}",
                    f"- Current route: {current_route_choice.get('selected_action_summary') or '(none)'}",
                    f"- Last evidence: {last_evidence_return.get('summary') or '(none)'}",
                    f"- Human need: {active_human_need.get('summary') or '(none)'}",
                ]
            )
        write_text(operator_console_path, "\n".join(lines).rstrip() + "\n")

    def answer_operator_checkpoint(
        self,
        *,
        topic_slug: str,
        answer: str,
        updated_by: str = "aitp-cli",
    ) -> dict[str, Any]:
        paths = self._operator_checkpoint_paths(topic_slug)
        payload = read_json(paths["json"])
        if payload is None:
            raise FileNotFoundError(f"No active operator checkpoint surface exists for topic {topic_slug}.")
        if str(payload.get("status") or "").strip() != "requested":
            raise ValueError("Operator checkpoint is not currently in requested status.")
        answer_text = str(answer or "").strip()
        if not answer_text:
            raise ValueError("answer must not be empty")
        answered_at = now_iso()
        payload["status"] = "answered"
        payload["active"] = False
        payload["answer"] = answer_text
        payload["answered_at"] = answered_at
        payload["answered_by"] = updated_by
        payload["updated_at"] = answered_at
        payload["updated_by"] = updated_by
        result = self._write_operator_checkpoint(topic_slug=topic_slug, payload=payload)
        runtime_root = self._runtime_root(topic_slug)
        topic_state = read_json(runtime_root / "topic_state.json") or {}
        interaction_state = read_json(runtime_root / "interaction_state.json") or {}
        queue_rows = read_jsonl(runtime_root / "action_queue.jsonl")
        decision_surface = interaction_state.get("decision_surface") or {}
        _, selected_pending_action = self._pending_action_context(queue_rows, decision_surface)
        validation_contract = read_json(self._validation_contract_paths(topic_slug)["json"]) or {}
        topic_status_explainability = {
            "topic_slug": topic_slug,
            "current_status_summary": "The latest operator checkpoint was answered and now awaits the next bounded runtime step.",
            "why_this_topic_is_here": "The latest operator checkpoint was answered and recorded. AITP should sync the answer into the next bounded step instead of silently reopening the checkpoint.",
            "current_route_choice": {
                "resume_stage": str(topic_state.get("resume_stage") or ""),
                "decision_source": str((interaction_state.get("decision_surface") or {}).get("decision_source") or ""),
                "queue_source": str((interaction_state.get("action_queue_surface") or {}).get("queue_source") or ""),
                "selected_action_id": str((selected_pending_action or {}).get("action_id") or "") or None,
                "selected_action_type": str((selected_pending_action or {}).get("action_type") or "") or None,
                "selected_action_summary": str((selected_pending_action or {}).get("summary") or "") or None,
                "selected_action_auto_runnable": bool((selected_pending_action or {}).get("auto_runnable")),
                "selected_validation_route_path": self._normalize_artifact_path(
                    (topic_state.get("pointers") or {}).get("selected_validation_route_path")
                ),
                "next_action_decision_note_path": self._normalize_artifact_path(
                    (topic_state.get("pointers") or {}).get("next_action_decision_note_path")
                    or (interaction_state.get("decision_surface") or {}).get("next_action_decision_note_path")
                ),
            },
            "last_evidence_return": self._derive_last_evidence_return(
                topic_state=topic_state,
                validation_contract=validation_contract,
            ),
            "active_human_need": {
                "status": "none",
                "kind": "none",
                "path": None,
                "summary": "No active human checkpoint is currently blocking the bounded loop.",
            },
            "blocker_summary": [],
            "next_bounded_action": {
                "status": "selected" if selected_pending_action else "missing",
                "action_id": str((selected_pending_action or {}).get("action_id") or "") or None,
                "action_type": str((selected_pending_action or {}).get("action_type") or "") or None,
                "summary": str((selected_pending_action or {}).get("summary") or "") or "No bounded action is currently selected.",
                "auto_runnable": bool((selected_pending_action or {}).get("auto_runnable")),
            },
            "updated_at": answered_at,
        }
        topic_state_path = runtime_root / "topic_state.json"
        if topic_state_path.exists() and topic_state:
            updated_topic_state = dict(topic_state)
            updated_topic_state["status_explainability"] = topic_status_explainability
            write_json(topic_state_path, updated_topic_state)
        self._refresh_operator_console_checkpoint_section(
            topic_slug=topic_slug,
            operator_checkpoint=payload,
            topic_status_explainability=topic_status_explainability,
        )
        steering_artifacts: dict[str, Any] = {
            "detected": False,
            "materialized": False,
            "requires_reorchestrate": False,
        }
        if str(payload.get("checkpoint_kind") or "").strip() in {
            "novelty_direction_choice",
            "stop_continue_branch_redirect_decision",
        }:
            steering_artifacts = self.materialize_steering_from_human_request(
                topic_slug=topic_slug,
                run_id=str(topic_state.get("latest_run_id") or payload.get("run_id") or "").strip() or None,
                human_request=answer_text,
                updated_by=updated_by,
                topic_state=topic_state,
            )
            if steering_artifacts.get("requires_reorchestrate"):
                self.orchestrate(
                    topic_slug=topic_slug,
                    run_id=str(topic_state.get("latest_run_id") or payload.get("run_id") or "").strip() or None,
                    control_note=str(steering_artifacts.get("control_note_path") or "").strip() or None,
                    updated_by=updated_by,
                    human_request=answer_text,
                )
                refreshed = self.ensure_topic_shell_surfaces(
                    topic_slug=topic_slug,
                    updated_by=updated_by,
                    human_request=answer_text,
                )
                return {
                    **result,
                    "operator_checkpoint": refreshed.get("operator_checkpoint") or payload,
                    "topic_state_explainability": refreshed.get("topic_state_explainability") or topic_status_explainability,
                    "steering_artifacts": steering_artifacts,
                }
        return {
            **result,
            "operator_checkpoint": payload,
            "topic_state_explainability": topic_status_explainability,
            "steering_artifacts": steering_artifacts,
        }

    def _derive_last_evidence_return(
        self,
        *,
        topic_state: dict[str, Any],
        validation_contract: dict[str, Any],
    ) -> dict[str, Any]:
        pointers = topic_state.get("pointers") or {}
        returned_result_path = self._artifact_path_on_disk(pointers.get("returned_execution_result_path"))
        if returned_result_path and returned_result_path.exists():
            returned_result = read_json(returned_result_path) or {}
            recorded_at = str(
                returned_result.get("updated_at")
                or returned_result.get("returned_at")
                or returned_result.get("completed_at")
                or ""
            ).strip()
            summary = str(
                returned_result.get("summary")
                or returned_result.get("what_actually_ran")
                or returned_result.get("what_was_attempted")
                or "A returned execution result is present but did not include a richer summary."
            ).strip()
            return {
                "status": "present",
                "kind": "returned_execution_result",
                "path": self._relativize(returned_result_path),
                "record_id": str(returned_result.get("result_id") or ""),
                "recorded_at": recorded_at,
                "summary": summary,
            }

        feedback_status_path = self._artifact_path_on_disk(pointers.get("feedback_status_path"))
        if feedback_status_path and feedback_status_path.exists():
            feedback_status = read_json(feedback_status_path) or {}
            return {
                "status": "present",
                "kind": "feedback_status",
                "path": self._relativize(feedback_status_path),
                "record_id": str(
                    feedback_status.get("last_result_id") or feedback_status.get("last_closed_loop_decision_id") or ""
                ),
                "recorded_at": self._coalesce_string(feedback_status.get("last_updated"), ""),
                "summary": str(feedback_status.get("summary") or "").strip()
                or (
                    f"Feedback stage `{feedback_status.get('stage') or '(missing)'}` "
                    f"with candidate status `{feedback_status.get('candidate_status') or '(missing)'}`."
                ),
            }

        executed_evidence = self._dedupe_strings(list(validation_contract.get("executed_evidence") or []))
        if executed_evidence:
            return {
                "status": "present",
                "kind": "validation_evidence",
                "path": executed_evidence[0],
                "record_id": "",
                "recorded_at": "",
                "summary": "Validation evidence artifacts are present, but no returned execution result was recorded as the latest evidence surface.",
            }

        return {
            "status": "missing",
            "kind": "none",
            "path": None,
            "record_id": "",
            "recorded_at": "",
            "summary": "No durable evidence-return artifact is currently recorded for this topic.",
        }

    def _derive_topic_status_explainability(
        self,
        *,
        topic_slug: str,
        topic_state: dict[str, Any],
        interaction_state: dict[str, Any],
        selected_pending_action: dict[str, Any] | None,
        idea_packet: dict[str, Any],
        operator_checkpoint: dict[str, Any],
        open_gap_summary: dict[str, Any],
        validation_contract: dict[str, Any],
        pending_decisions: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        decision_surface = interaction_state.get("decision_surface") or {}
        queue_surface = interaction_state.get("action_queue_surface") or {}
        pointers = topic_state.get("pointers") or {}
        selected_action_summary = str((selected_pending_action or {}).get("summary") or "").strip()
        selected_action_type = str((selected_pending_action or {}).get("action_type") or "").strip()
        selected_action_id = str((selected_pending_action or {}).get("action_id") or "").strip()
        selected_action_auto_runnable = bool((selected_pending_action or {}).get("auto_runnable"))
        current_route_choice = {
            "resume_stage": str(topic_state.get("resume_stage") or ""),
            "decision_source": str(decision_surface.get("decision_source") or ""),
            "queue_source": str(queue_surface.get("queue_source") or ""),
            "selected_action_id": selected_action_id or None,
            "selected_action_type": selected_action_type or None,
            "selected_action_summary": selected_action_summary or None,
            "selected_action_auto_runnable": selected_action_auto_runnable,
            "selected_validation_route_path": self._normalize_artifact_path(
                pointers.get("selected_validation_route_path")
            ),
            "next_action_decision_note_path": self._normalize_artifact_path(
                pointers.get("next_action_decision_note_path")
                or decision_surface.get("next_action_decision_note_path")
            ),
        }
        last_evidence_return = self._derive_last_evidence_return(
            topic_state=topic_state,
            validation_contract=validation_contract,
        )

        active_human_need: dict[str, Any]
        blocker_summary: list[str]
        if str(operator_checkpoint.get("status") or "").strip() == "requested":
            blocker_summary = self._dedupe_strings(list(operator_checkpoint.get("blocker_summary") or []))
            active_human_need = {
                "status": "requested",
                "kind": str(operator_checkpoint.get("checkpoint_kind") or ""),
                "path": self._normalize_artifact_path(operator_checkpoint.get("note_path")),
                "summary": str(operator_checkpoint.get("question") or ""),
            }
            why_this_topic_is_here = (
                (blocker_summary[0] if blocker_summary else "")
                or str(operator_checkpoint.get("question") or "").strip()
                or "AITP paused at an active operator checkpoint."
            )
        elif int((pending_decisions or {}).get("blocking_count") or 0) > 0:
            blocking_ids = [
                str(item).strip()
                for item in (pending_decisions or {}).get("blocking_ids") or []
                if str(item).strip()
            ]
            if blocking_ids:
                stop_reason = f"Blocking pending decisions require resolution: {', '.join(blocking_ids)}."
            else:
                stop_reason = "Blocking pending decisions require resolution before deeper execution."
            blocker_summary = [stop_reason]
            active_human_need = {
                "status": "requested",
                "kind": "pending_decisions",
                "path": None,
                "summary": stop_reason,
            }
            why_this_topic_is_here = stop_reason
        elif str(idea_packet.get("status") or "").strip() == "needs_clarification":
            blocker_summary = self._dedupe_strings(
                list(idea_packet.get("clarification_questions") or [])
                or [f"Missing idea-packet fields: {', '.join(idea_packet.get('missing_fields') or []) or '(none)'}"]
            )
            active_human_need = {
                "status": "requested",
                "kind": "idea_packet_clarification",
                "path": self._normalize_artifact_path(idea_packet.get("note_path")),
                "summary": str(idea_packet.get("status_reason") or ""),
            }
            why_this_topic_is_here = (
                (blocker_summary[0] if blocker_summary else "")
                or str(idea_packet.get("status_reason") or "").strip()
                or "AITP is holding at the research-intent gate."
            )
        else:
            blocker_summary = self._dedupe_strings(list(open_gap_summary.get("blockers") or []))
            active_human_need = {
                "status": "none",
                "kind": "none",
                "path": None,
                "summary": "No active human checkpoint is currently blocking the bounded loop.",
            }
            why_this_topic_is_here = (
                (blocker_summary[0] if blocker_summary else "")
                or (
                    f"The topic is currently following `{selected_action_summary}` at stage "
                    f"`{topic_state.get('resume_stage') or '(missing)'}`."
                    if selected_action_summary
                    else ""
                )
                or str(topic_state.get("resume_reason") or "").strip()
                or "AITP is holding the current bounded route defined by the runtime state."
            )

        next_bounded_action = {
            "status": "selected" if selected_action_summary else "missing",
            "action_id": selected_action_id or None,
            "action_type": selected_action_type or None,
            "summary": selected_action_summary or "No bounded action is currently selected.",
            "auto_runnable": selected_action_auto_runnable,
        }
        return {
            "topic_slug": topic_slug,
            "current_status_summary": (
                f"Stage `{topic_state.get('resume_stage') or '(missing)'}`; "
                f"next `{next_bounded_action['summary']}`; "
                f"human need `{active_human_need['kind']}`; "
                f"last evidence `{last_evidence_return['kind']}`."
            ),
            "why_this_topic_is_here": why_this_topic_is_here,
            "current_route_choice": current_route_choice,
            "last_evidence_return": last_evidence_return,
            "active_human_need": active_human_need,
            "blocker_summary": blocker_summary,
            "next_bounded_action": next_bounded_action,
            "updated_at": now_iso(),
        }

    def _render_research_question_contract_markdown(self, payload: dict[str, Any]) -> str:
        lines = [
            "# Active research question contract",
            "",
            f"- Topic slug: `{payload['topic_slug']}`",
            f"- Question id: `{payload['question_id']}`",
            f"- Title: `{payload['title']}`",
            f"- Status: `{payload['status']}`",
            f"- Task type: `{payload.get('task_type') or '(missing)'}`",
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
        analytic_check_families = payload.get("analytic_check_families") or []
        if analytic_check_families:
            lines.extend(["", "## Analytic check families", ""])
            for item in analytic_check_families:
                lines.append(f"- `{item}`")
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

    def _render_idea_packet_markdown(self, payload: dict[str, Any]) -> str:
        lines = [
            "# Idea packet",
            "",
            f"- Topic slug: `{payload['topic_slug']}`",
            f"- Status: `{payload.get('status') or '(missing)'}`",
            f"- Task type: `{payload.get('task_type') or '(missing)'}`",
            f"- Updated at: `{payload.get('updated_at') or '(missing)'}`",
            f"- Updated by: `{payload.get('updated_by') or '(missing)'}`",
            "",
            "## Gate summary",
            "",
            payload.get("status_reason") or "(missing)",
            "",
            "## Initial idea",
            "",
            payload.get("initial_idea") or "(missing)",
            "",
            "## Novelty target",
            "",
            payload.get("novelty_target") or "(missing)",
            "",
            "## Non-goals",
            "",
        ]
        for item in payload.get("non_goals") or ["(missing)"]:
            lines.append(f"- {item}")
        lines.extend(
            [
                "",
                "## First validation route",
                "",
                payload.get("first_validation_route") or "(missing)",
                "",
                "## Initial evidence bar",
                "",
                payload.get("initial_evidence_bar") or "(missing)",
                "",
                "## Missing fields",
                "",
            ]
        )
        for item in payload.get("missing_fields") or ["(none)"]:
            lines.append(f"- `{item}`")
        lines.extend(["", "## Clarification questions", ""])
        for item in payload.get("clarification_questions") or ["(none)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Execution context signals", ""])
        for item in payload.get("execution_context_signals") or ["(none)"]:
            lines.append(f"- `{item}`")
        return "\n".join(lines) + "\n"

    def _render_result_brief_markdown(self, payload: dict[str, Any]) -> str:
        lines = [
            "# Result brief",
            "",
            f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
            f"- Interaction class: `{payload.get('interaction_class') or '(missing)'}`",
            "",
            "## What Changed",
            "",
            payload.get("what_changed") or "(missing)",
            "",
            "## Evidence",
            "",
            payload.get("evidence_summary") or "(missing)",
            "",
            "## Scope",
            "",
            payload.get("scope_summary") or "(missing)",
            "",
            "## What This Does Not Yet Justify",
            "",
        ]
        for item in payload.get("non_claims") or ["(missing)"]:
            lines.append(f"- {item}")
        return "\n".join(lines) + "\n"

    def _render_layer_projection_markdown(self, payload: dict[str, Any]) -> str:
        lines = [
            f"# {payload.get('subplane') or 'Layer'} projection",
            "",
            f"- Status: `{payload.get('status') or '(missing)'}`",
            f"- Primary output path: `{payload.get('primary_output_path') or '(missing)'}`",
            f"- Next allowed transitions: `{', '.join(payload.get('next_allowed_transitions') or []) or '(missing)'}`",
            f"- Consumed by: `{', '.join(payload.get('consumed_by') or []) or '(missing)'}`",
            "",
            payload.get("summary") or "(missing)",
            "",
        ]
        source_ids = payload.get("source_ids") or []
        if source_ids:
            lines.extend(["## Source ids", ""])
            for item in source_ids:
                lines.append(f"- `{item}`")
            lines.append("")
        source_titles = payload.get("source_titles") or []
        if source_titles:
            lines.extend(["## Source titles", ""])
            for item in source_titles:
                lines.append(f"- {item}")
            lines.append("")
        if "source_count" in payload:
            lines.extend(
                [
                    "## Source count",
                    "",
                    f"- `{payload.get('source_count')}` registered source(s)",
                    "",
                ]
            )
        source_types = payload.get("source_types") or []
        if source_types:
            lines.extend(["## Source types", ""])
            for item in source_types:
                lines.append(f"- `{item}`")
            lines.append("")
        fidelity_counts = payload.get("source_fidelity_counts") or {}
        if fidelity_counts:
            lines.extend(
                [
                    "## Source fidelity",
                    "",
                    f"- Highest fidelity class: `{payload.get('highest_fidelity_class') or '(missing)'}`",
                    f"- Summary: {payload.get('source_fidelity_summary') or '(missing)'}",
                    "",
                ]
            )
            for key in sorted(fidelity_counts):
                lines.append(f"- `{key}`: `{fidelity_counts.get(key)}`")
            lines.append("")
        if "citation_graph_status" in payload:
            lines.extend(
                [
                    "## Citation graph signals",
                    "",
                    f"- Status: `{payload.get('citation_graph_status') or '(missing)'}`",
                    f"- Summary: {payload.get('citation_graph_summary') or '(missing)'}",
                    f"- arXiv ids: `{payload.get('arxiv_id_count') or 0}`",
                    f"- BibTeX/DOI signals: `{payload.get('bibtex_signal_count') or 0}`",
                    f"- Reference-bearing rows: `{payload.get('citation_signal_count') or 0}`",
                    "",
                ]
            )
        if "intake_stage" in payload:
            lines.extend(
                [
                    "## Intake status",
                    "",
                    f"- Stage: `{payload.get('intake_stage') or '(missing)'}`",
                    f"- Next stage: `{payload.get('next_stage') or '(none)'}`",
                    f"- Reading depth: `{payload.get('reading_depth') or '(missing)'}`",
                    f"- Assumption quality: `{payload.get('assumption_quality') or '(missing)'}`",
                    f"- Notation table: `{payload.get('notation_table_path') or '(missing)'}`",
                    f"- Assumption table: `{payload.get('assumption_table_path') or '(missing)'}`",
                    f"- Regime table: `{payload.get('regime_table_path') or '(missing)'}`",
                    f"- Claim extraction: `{payload.get('claim_extraction_path') or '(missing)'}`",
                    "",
                ]
            )
        if "validation_mode" in payload:
            lines.extend(
                [
                    "## Validation status",
                    "",
                    f"- Validation mode: `{payload.get('validation_mode') or '(missing)'}`",
                    f"- Verification focus: `{payload.get('verification_focus') or '(missing)'}`",
                    f"- Evidence status: `{payload.get('evidence_status') or '(missing)'}`",
                    f"- Evidence kind: `{payload.get('evidence_kind') or '(missing)'}`",
                    f"- Evidence path: `{payload.get('evidence_path') or '(missing)'}`",
                    "",
                ]
            )
            analytic_check_families = payload.get("analytic_check_families") or []
            if analytic_check_families:
                lines.extend(["## Analytic check families", ""])
                for item in analytic_check_families:
                    lines.append(f"- `{item}`")
                lines.append("")
        if "consultation_count" in payload:
            lines.extend(
                [
                    "## L2 activity",
                    "",
                    f"- Consultation count: `{payload.get('consultation_count') or 0}`",
                    f"- Staging entry count: `{payload.get('staging_entry_count') or 0}`",
                    f"- Promotion gate status: `{payload.get('promotion_gate_status') or '(missing)'}`",
                    f"- Promoted unit count: `{payload.get('promoted_unit_count') or 0}`",
                    "",
                ]
            )
        consultation_surface = payload.get("consultation_surface") or {}
        if consultation_surface:
            lines.extend(
                [
                    "## Consultation surface",
                    "",
                    f"- Consultation index: `{consultation_surface.get('consultation_index_path') or '(missing)'}`",
                    f"- Consultation count: `{consultation_surface.get('consultation_count') or 0}`",
                    f"- Latest consultation id: `{consultation_surface.get('latest_consultation_id') or '(none)'}`",
                    f"- Latest query: `{consultation_surface.get('latest_query_text') or '(none)'}`",
                    f"- Latest application: `{consultation_surface.get('latest_application_path') or '(none)'}`",
                    f"- Latest note: `{consultation_surface.get('latest_summary_note_path') or '(none)'}`",
                    f"- Latest memory map: `{consultation_surface.get('latest_memory_map_note_path') or '(none)'}`",
                    "",
                    f"{consultation_surface.get('latest_summary') or '(no consultation summary yet)' }",
                    "",
                ]
            )
        writeback_surface = payload.get("writeback_surface") or {}
        if writeback_surface:
            lines.extend(
                [
                    "## Writeback surface",
                    "",
                    f"- Promotion gate status: `{writeback_surface.get('promotion_gate_status') or '(missing)'}`",
                    f"- Staging entry count: `{writeback_surface.get('staging_entry_count') or 0}`",
                    f"- Promoted unit count: `{writeback_surface.get('promoted_unit_count') or 0}`",
                    "",
                ]
            )
        graph_surface = payload.get("graph_surface") or {}
        if graph_surface:
            lines.extend(
                [
                    "## Canonical graph surface",
                    "",
                    f"- Status: `{graph_surface.get('status') or '(missing)'}`",
                    f"- Index path: `{graph_surface.get('index_path') or '(missing)'}`",
                    f"- Edge path: `{graph_surface.get('edges_path') or '(missing)'}`",
                    f"- Unit count: `{graph_surface.get('unit_count') or 0}`",
                    f"- Edge count: `{graph_surface.get('edge_count') or 0}`",
                    f"- Unit types: `{', '.join(graph_surface.get('unit_types') or []) or '(none)'}`",
                    "",
                    f"{graph_surface.get('summary') or '(no canonical graph summary yet)' }",
                    "",
                ]
            )
        available_artifact_paths = payload.get("available_artifact_paths") or []
        if available_artifact_paths:
            lines.extend(["## Available artifact paths", ""])
            for item in available_artifact_paths:
                lines.append(f"- `{item}`")
            lines.append("")
        staging_entry_ids = payload.get("staging_entry_ids") or []
        if staging_entry_ids:
            lines.extend(["## Staging entry ids", ""])
            for item in staging_entry_ids:
                lines.append(f"- `{item}`")
            lines.append("")
        intended_l2_targets = payload.get("intended_l2_targets") or []
        if intended_l2_targets:
            lines.extend(["## Intended L2 targets", ""])
            for item in intended_l2_targets:
                lines.append(f"- `{item}`")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def _render_l3_subplane_markdown(self, payload: dict[str, Any]) -> str:
        lines = [
            f"# {payload.get('subplane') or 'L3'} projection",
            "",
            f"- Status: `{payload.get('status') or '(missing)'}`",
            f"- Primary output path: `{payload.get('primary_output_path') or '(missing)'}`",
            f"- Next allowed transitions: `{', '.join(payload.get('next_allowed_transitions') or []) or '(missing)'}`",
            f"- Consumed by: `{', '.join(payload.get('consumed_by') or []) or '(missing)'}`",
            "",
            payload.get("summary") or "(missing)",
            "",
        ]
        supporting_output_paths = payload.get("supporting_output_paths") or []
        if supporting_output_paths:
            lines.extend(["## Supporting output paths", ""])
            for item in supporting_output_paths:
                lines.append(f"- `{item}`")
            lines.append("")
        candidate_ids = payload.get("candidate_ids") or []
        if candidate_ids:
            lines.extend(["## Candidate ids", ""])
            for item in candidate_ids:
                lines.append(f"- `{item}`")
            lines.append("")
        ready_candidate_ids = payload.get("ready_candidate_ids") or []
        if ready_candidate_ids:
            lines.extend(["## Ready candidate ids", ""])
            for item in ready_candidate_ids:
                lines.append(f"- `{item}`")
            lines.append("")
        staging_entry_ids = payload.get("staging_entry_ids") or []
        if staging_entry_ids:
            lines.extend(["## Staging entry ids", ""])
            for item in staging_entry_ids:
                lines.append(f"- `{item}`")
            lines.append("")
        intended_l2_targets = payload.get("intended_l2_targets") or []
        if intended_l2_targets:
            lines.extend(["## Intended L2 targets", ""])
            for item in intended_l2_targets:
                lines.append(f"- `{item}`")
            lines.append("")
        writeback_blockers = payload.get("writeback_blockers") or []
        if writeback_blockers:
            lines.extend(["## Writeback blockers", ""])
            for item in writeback_blockers:
                lines.append(f"- {item}")
            lines.append("")
        forbidden_direct_transitions = payload.get("forbidden_direct_transitions") or []
        if forbidden_direct_transitions:
            lines.extend(["## Forbidden direct transitions", ""])
            for item in forbidden_direct_transitions:
                lines.append(f"- `{item}`")
            lines.append("")
        mandatory_routing_rule = str(payload.get("mandatory_routing_rule") or "").strip()
        if mandatory_routing_rule:
            lines.extend(["## Mandatory routing rule", "", mandatory_routing_rule, ""])
        return "\n".join(lines).rstrip() + "\n"

    def _render_topic_skill_projection_markdown(self, payload: dict[str, Any]) -> str:
        lines = [
            "# Topic skill projection",
            "",
            f"- Projection id: `{payload.get('id') or '(missing)'}`",
            f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
            f"- Source topic slug: `{payload.get('source_topic_slug') or '(missing)'}`",
            f"- Run id: `{payload.get('run_id') or '(missing)'}`",
            f"- Lane: `{payload.get('lane') or '(missing)'}`",
            f"- Status: `{payload.get('status') or '(missing)'}`",
            f"- Candidate id: `{payload.get('candidate_id') or '(none)'}`",
            f"- Intended L2 target: `{payload.get('intended_l2_target') or '(none)'}`",
            "",
            "## Summary",
            "",
            payload.get("summary") or "(missing)",
            "",
            "## Status reason",
            "",
            payload.get("status_reason") or "(missing)",
            "",
            "## Entry signals",
            "",
        ]
        for item in payload.get("entry_signals") or ["(none)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Required first reads", ""])
        for item in payload.get("required_first_reads") or ["(none)"]:
            lines.append(f"- `{item}`")
        lines.extend(["", "## Required first routes", ""])
        for item in payload.get("required_first_routes") or ["(none)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Benchmark-first rules", ""])
        for item in payload.get("benchmark_first_rules") or ["(none)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Operator checkpoint rules", ""])
        for item in payload.get("operator_checkpoint_rules") or ["(none)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Operation trust requirements", ""])
        for item in payload.get("operation_trust_requirements") or ["(none)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Strategy guidance", ""])
        for item in payload.get("strategy_guidance") or ["(none)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Forbidden proxies", ""])
        for item in payload.get("forbidden_proxies") or ["(none)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Derived from artifacts", ""])
        for item in payload.get("derived_from_artifacts") or ["(none)"]:
            lines.append(f"- `{item}`")
        return "\n".join(lines) + "\n"

    def _render_topic_dashboard_markdown(
        self,
        *,
        topic_slug: str,
        topic_state: dict[str, Any],
        selected_pending_action: dict[str, Any] | None,
        pending_actions: list[dict[str, Any]],
        idea_packet: dict[str, Any],
        operator_checkpoint: dict[str, Any],
        topic_status_explainability: dict[str, Any],
        research_contract: dict[str, Any],
        validation_contract: dict[str, Any],
        promotion_readiness: dict[str, Any],
        open_gap_summary: dict[str, Any],
        strategy_memory: dict[str, Any],
        topic_skill_projection: dict[str, Any],
        topic_completion: dict[str, Any],
        lean_bridge: dict[str, Any],
    ) -> str:
        selected_action_summary = str((selected_pending_action or {}).get("summary") or "").strip() or "(none)"
        current_route_choice = topic_status_explainability.get("current_route_choice") or {}
        last_evidence_return = topic_status_explainability.get("last_evidence_return") or {}
        active_human_need = topic_status_explainability.get("active_human_need") or {}
        blocker_summary = topic_status_explainability.get("blocker_summary") or []
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
            "## Why this topic is here",
            "",
            topic_status_explainability.get("why_this_topic_is_here") or "(missing)",
            "",
            "## Current status",
            "",
            f"- Idea packet: `{idea_packet.get('status') or '(missing)'}`",
            f"- Operator checkpoint: `{operator_checkpoint.get('status') or '(missing)'}`",
            f"- Research contract: `{research_contract.get('status') or '(missing)'}`",
            f"- Validation contract: `{validation_contract.get('status') or '(missing)'}`",
            f"- Promotion readiness: `{promotion_readiness.get('status') or '(missing)'}`",
            f"- Gap status: `{open_gap_summary.get('status') or '(missing)'}`",
            f"- Topic completion: `{topic_completion.get('status') or '(missing)'}`",
            f"- Lean bridge: `{lean_bridge.get('status') or '(missing)'}`",
            "",
            "## Idea packet summary",
            "",
            f"- Gate status: `{idea_packet.get('status') or '(missing)'}`",
            f"- First validation route: {idea_packet.get('first_validation_route') or '(missing)'}",
            f"- Initial evidence bar: {idea_packet.get('initial_evidence_bar') or '(missing)'}",
            f"- Missing fields: `{', '.join(idea_packet.get('missing_fields') or []) or '(none)'}`",
            "",
            idea_packet.get("status_reason") or "(missing)",
            "",
            "## Active operator checkpoint",
            "",
            f"- Status: `{operator_checkpoint.get('status') or '(missing)'}`",
            f"- Kind: `{operator_checkpoint.get('checkpoint_kind') or '(none)'}`",
            f"- Open next: `{operator_checkpoint.get('note_path') or '(missing)'}`",
            "",
            operator_checkpoint.get("question") or "(none)",
            "",
            "## Current route choice",
            "",
            f"- Decision source: `{current_route_choice.get('decision_source') or '(missing)'}`",
            f"- Queue source: `{current_route_choice.get('queue_source') or '(missing)'}`",
            f"- Selected action id: `{current_route_choice.get('selected_action_id') or '(none)'}`",
            f"- Selected action type: `{current_route_choice.get('selected_action_type') or '(none)'}`",
            f"- Selected action auto-runnable: `{str(bool(current_route_choice.get('selected_action_auto_runnable'))).lower()}`",
            f"- Next-action decision note: `{current_route_choice.get('next_action_decision_note_path') or '(missing)'}`",
            f"- Selected validation route: `{current_route_choice.get('selected_validation_route_path') or '(missing)'}`",
            "",
            f"{current_route_choice.get('selected_action_summary') or '(none)'}",
            "",
            "## Last evidence return",
            "",
            f"- Status: `{last_evidence_return.get('status') or '(missing)'}`",
            f"- Kind: `{last_evidence_return.get('kind') or '(missing)'}`",
            f"- Record id: `{last_evidence_return.get('record_id') or '(none)'}`",
            f"- Recorded at: `{last_evidence_return.get('recorded_at') or '(unknown)'}`",
            f"- Path: `{last_evidence_return.get('path') or '(missing)'}`",
            "",
            f"{last_evidence_return.get('summary') or '(none)'}",
            "",
            "## Active human need",
            "",
            f"- Status: `{active_human_need.get('status') or '(missing)'}`",
            f"- Kind: `{active_human_need.get('kind') or '(missing)'}`",
            f"- Path: `{active_human_need.get('path') or '(missing)'}`",
            "",
            f"{active_human_need.get('summary') or '(none)'}",
            "",
            "## Blocker summary",
            "",
        ]
        for item in blocker_summary or ["(none)"]:
            lines.append(f"- {item}")
        lines.extend([
            "",
            "## Promotion readiness summary",
            "",
            promotion_readiness.get("summary") or "(missing)",
            "",
            "## Open gap summary",
            "",
            open_gap_summary.get("summary") or "(missing)",
            "",
            "## Strategy memory",
            "",
            f"- Status: `{strategy_memory.get('status') or '(missing)'}`",
            f"- Lane: `{strategy_memory.get('lane') or '(missing)'}`",
            f"- Row count: `{strategy_memory.get('row_count') or 0}`",
            f"- Relevant count: `{strategy_memory.get('relevant_count') or 0}`",
            f"- Latest path: `{strategy_memory.get('latest_path') or '(none)'}`",
            "",
            strategy_memory.get("summary") or "(missing)",
            "",
            "## Topic skill projection",
            "",
            f"- Status: `{topic_skill_projection.get('status') or '(missing)'}`",
            f"- Projection id: `{topic_skill_projection.get('id') or '(missing)'}`",
            f"- Projection note: `{topic_skill_projection.get('note_path') or '(missing)'}`",
            f"- Intended L2 target: `{topic_skill_projection.get('intended_l2_target') or '(none)'}`",
            "",
            topic_skill_projection.get("summary") or "(missing)",
            "",
            "## Topic completion summary",
            "",
            topic_completion.get("summary") or "(missing)",
            "",
            "## Lean bridge summary",
            "",
            lean_bridge.get("summary") or "(missing)",
            "",
        ])
        for item in strategy_memory.get("guidance") or []:
            if item == (strategy_memory.get("guidance") or [None])[0]:
                lines.extend(["## Strategy guidance", ""])
            lines.append(f"- {item}")
        for item in topic_skill_projection.get("required_first_routes") or []:
            if item == (topic_skill_projection.get("required_first_routes") or [None])[0]:
                lines.extend(["", "## Projection route guidance", ""])
            lines.append(f"- {item}")
        lines.extend([
            "",
            "## Immediate next actions",
            "",
        ])
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
        promotion_gate = self._load_promotion_gate(topic_slug) or {}
        gate_status = str(promotion_gate.get("status") or "").strip()
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
        elif gate_status == "promoted" and candidate_rows:
            status = "promoted"
            summary = "At least one regression-backed candidate has already been promoted through the active gate."
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
            if str(row.get("candidate_type") or "").strip() == "topic_skill_projection":
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
        idea_packet_paths = self._idea_packet_paths(topic_slug)
        operator_checkpoint_paths = self._operator_checkpoint_paths(topic_slug)
        topic_skill_projection_paths = self._topic_skill_projection_paths(topic_slug)
        dashboard_path = self._topic_dashboard_path(topic_slug)
        result_brief_paths = self._result_brief_paths(topic_slug)
        readiness_path = self._promotion_readiness_path(topic_slug)
        gap_map_path = self._gap_map_path(topic_slug)

        existing_research = read_json(research_paths["json"]) or {}
        existing_validation = read_json(validation_paths["json"]) or {}
        existing_idea_packet = read_json(idea_packet_paths["json"]) or {}
        existing_operator_checkpoint = read_json(operator_checkpoint_paths["json"]) or {}
        source_rows = read_jsonl(self.kernel_root / "source-layer" / "topics" / topic_slug / "source_index.jsonl")
        distilled = self._distill_from_sources(source_rows or [], topic_slug)
        distilled_initial_idea = str(distilled.get("distilled_initial_idea") or "").strip()
        distilled_first_validation_route = str(
            distilled.get("distilled_first_validation_route") or ""
        ).strip()

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
            or self._validation_mode_for_template(template_mode, research_mode)
        ).strip()
        title = self._coalesce_string(
            existing_research.get("title"),
            self._topic_display_title(topic_slug),
        )
        selected_action_summary = str((selected_pending_action or {}).get("summary") or "").strip()
        active_question = self._coalesce_string(
            existing_research.get("question"),
            distilled_initial_idea,
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
        task_type = self._coalesce_string(
            existing_research.get("task_type"),
            existing_idea_packet.get("task_type"),
            self._infer_task_type(human_request or resolved_interaction_state.get("human_request")),
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
            "task_type": task_type,
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
                distilled_first_validation_route,
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
        strategy_memory = self._derive_strategy_memory_summary(
            topic_slug=topic_slug,
            latest_run_id=latest_run_id or None,
            selected_pending_action=selected_pending_action,
            research_contract=research_contract,
            validation_contract=validation_contract,
        )
        topic_skill_projection = self._derive_topic_skill_projection(
            topic_slug=topic_slug,
            updated_by=updated_by,
            topic_state=resolved_topic_state,
            research_contract=research_contract,
            validation_contract=validation_contract,
            selected_pending_action=selected_pending_action,
            strategy_memory=strategy_memory,
            topic_completion=topic_completion,
            open_gap_summary=open_gap_summary,
            candidate_rows=candidate_rows,
        )
        topic_skill_projection_written = write_topic_skill_projection(
            topic_slug,
            topic_skill_projection,
            kernel_root=self.kernel_root,
        )
        write_text(
            topic_skill_projection_paths["note"],
            self._render_topic_skill_projection_markdown(topic_skill_projection),
        )
        topic_skill_projection_surface = {
            **topic_skill_projection_written["topic_skill_projection"],
            "path": self._relativize(Path(topic_skill_projection_written["path"])),
            "note_path": self._relativize(topic_skill_projection_paths["note"]),
        }
        topic_skill_projection_candidate = self._sync_topic_skill_projection_candidate(
            topic_slug=topic_slug,
            run_id=latest_run_id or None,
            projection=topic_skill_projection_surface,
            updated_by=updated_by,
        )
        idea_packet = self._derive_idea_packet(
            topic_slug=topic_slug,
            updated_by=updated_by,
            human_request=human_request,
            topic_state=resolved_topic_state,
            interaction_state=resolved_interaction_state,
            existing_idea_packet=existing_idea_packet,
            existing_research=existing_research,
            existing_validation=existing_validation,
            research_contract=research_contract,
            validation_contract=validation_contract,
            selected_pending_action=selected_pending_action,
        )
        pending_decisions = list_pending_decision_points(topic_slug, kernel_root=self.kernel_root)
        pending_decisions_payload = {
            "blocking_count": sum(1 for row in pending_decisions if row.get("blocking")),
            "unresolved_ids": [
                str(row.get("id") or "").strip()
                for row in pending_decisions
                if str(row.get("id") or "").strip()
            ],
        }
        pending_decisions_internal = {
            **pending_decisions_payload,
            "blocking_ids": [
                str(row.get("id") or "").strip()
                for row in pending_decisions
                if row.get("blocking") and str(row.get("id") or "").strip()
            ],
        }
        operator_checkpoint, superseded_checkpoint = self._derive_operator_checkpoint(
            topic_slug=topic_slug,
            updated_by=updated_by,
            existing_checkpoint=existing_operator_checkpoint,
            idea_packet=idea_packet,
            research_contract=research_contract,
            validation_contract=validation_contract,
            promotion_gate=resolved_promotion_gate,
            selected_pending_action=selected_pending_action,
            pending_decisions=pending_decisions_internal,
            decision_surface=decision_surface,
            dashboard_path=dashboard_path,
            idea_packet_paths=idea_packet_paths,
            research_paths=research_paths,
            validation_paths=validation_paths,
        )

        write_json(research_paths["json"], research_contract)
        write_text(research_paths["note"], self._render_research_question_contract_markdown(research_contract))
        write_json(validation_paths["json"], validation_contract)
        write_text(validation_paths["note"], self._render_validation_contract_markdown(validation_contract))
        write_json(idea_packet_paths["json"], idea_packet)
        write_text(idea_packet_paths["note"], self._render_idea_packet_markdown(idea_packet))
        operator_checkpoint_paths_written = self._write_operator_checkpoint(
            topic_slug=topic_slug,
            payload=operator_checkpoint,
            superseded_payload=superseded_checkpoint,
        )
        operator_checkpoint_surface = {
            **operator_checkpoint,
            "path": self._relativize(Path(operator_checkpoint_paths_written["operator_checkpoint_path"])),
            "note_path": self._relativize(Path(operator_checkpoint_paths_written["operator_checkpoint_note_path"])),
            "ledger_path": self._relativize(Path(operator_checkpoint_paths_written["operator_checkpoint_ledger_path"])),
        }
        topic_status_explainability = self._derive_topic_status_explainability(
            topic_slug=topic_slug,
            topic_state=resolved_topic_state,
            interaction_state=resolved_interaction_state,
            selected_pending_action=selected_pending_action,
            idea_packet=idea_packet,
            operator_checkpoint=operator_checkpoint_surface,
            open_gap_summary=open_gap_summary,
            validation_contract=validation_contract,
            pending_decisions=pending_decisions_internal,
        )
        interaction_contract = self._derive_interaction_contract(
            topic_slug=topic_slug,
            idea_packet=idea_packet,
            operator_checkpoint=operator_checkpoint_surface,
            pending_decisions=pending_decisions_internal,
            promotion_readiness=promotion_readiness,
        )
        last_evidence_return = topic_status_explainability.get("last_evidence_return") or {}
        scope_parts = self._dedupe_strings(
            [
                str(research_contract.get("question") or "").strip(),
                str((research_contract.get("scope") or [None])[0] or "").strip(),
                f"Bounded action: {selected_action_summary}" if selected_action_summary else "",
            ]
        )
        non_claims = self._dedupe_strings(list(idea_packet.get("non_goals") or []))
        if not non_claims:
            non_claims = self._dedupe_strings(list(research_contract.get("non_goals") or []))
        if not non_claims:
            non_claims = ["(missing)"]
        result_brief = {
            "$schema": "https://aitp.local/schemas/result-brief.schema.json",
            "kind": "result_brief",
            "topic_slug": topic_slug,
            "interaction_class": interaction_contract["interaction_class"],
            "what_changed": self._coalesce_string(
                str(topic_status_explainability.get("why_this_topic_is_here") or "").strip(),
                str(topic_status_explainability.get("current_status_summary") or "").strip(),
                "(missing)",
            ),
            "evidence_summary": str(last_evidence_return.get("summary") or "").strip() or "(missing)",
            "scope_summary": " ".join(scope_parts).strip() or "(missing)",
            "non_claims": non_claims,
            "updated_at": now_iso(),
            "updated_by": updated_by,
        }
        write_json(result_brief_paths["json"], result_brief)
        write_text(result_brief_paths["note"], self._render_result_brief_markdown(result_brief))
        topic_state_path = runtime_root / "topic_state.json"
        if topic_state_path.exists() and resolved_topic_state:
            resolved_topic_state = dict(resolved_topic_state)
            resolved_topic_state["status_explainability"] = topic_status_explainability
            write_json(topic_state_path, resolved_topic_state)
        write_text(
            dashboard_path,
            self._render_topic_dashboard_markdown(
                topic_slug=topic_slug,
                topic_state=resolved_topic_state,
                selected_pending_action=selected_pending_action,
                pending_actions=pending_actions,
                idea_packet=idea_packet,
                operator_checkpoint=operator_checkpoint_surface,
                topic_status_explainability=topic_status_explainability,
                research_contract=research_contract,
                validation_contract=validation_contract,
                promotion_readiness=promotion_readiness,
                open_gap_summary=open_gap_summary,
                strategy_memory=strategy_memory,
                topic_skill_projection=topic_skill_projection_surface,
                topic_completion=topic_completion,
                lean_bridge=lean_bridge,
            ),
        )
        write_text(readiness_path, self._render_promotion_readiness_markdown(promotion_readiness))
        write_text(gap_map_path, self._render_gap_map_markdown(open_gap_summary))
        self._refresh_operator_console_checkpoint_section(
            topic_slug=topic_slug,
            operator_checkpoint=operator_checkpoint_surface,
            topic_status_explainability=topic_status_explainability,
        )
        return {
            "research_question_contract_path": str(research_paths["json"]),
            "research_question_contract_note_path": str(research_paths["note"]),
            "validation_contract_path": str(validation_paths["json"]),
            "validation_contract_note_path": str(validation_paths["note"]),
            "idea_packet_path": str(idea_packet_paths["json"]),
            "idea_packet_note_path": str(idea_packet_paths["note"]),
            "operator_checkpoint_path": operator_checkpoint_paths_written["operator_checkpoint_path"],
            "operator_checkpoint_note_path": operator_checkpoint_paths_written["operator_checkpoint_note_path"],
            "operator_checkpoint_ledger_path": operator_checkpoint_paths_written["operator_checkpoint_ledger_path"],
            "topic_dashboard_path": str(dashboard_path),
            "topic_skill_projection_path": str(topic_skill_projection_paths["json"]),
            "topic_skill_projection_note_path": str(topic_skill_projection_paths["note"]),
            "result_brief_path": str(result_brief_paths["json"]),
            "result_brief_note_path": str(result_brief_paths["note"]),
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
            "idea_packet": idea_packet,
            "operator_checkpoint": operator_checkpoint_surface,
            "topic_state_explainability": topic_status_explainability,
            "promotion_readiness": promotion_readiness,
            "open_gap_summary": open_gap_summary,
            "strategy_memory": strategy_memory,
            "topic_skill_projection": topic_skill_projection_surface,
            "topic_skill_projection_candidate": topic_skill_projection_candidate,
            "result_brief": result_brief,
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

    def _trim_steering_fragment(self, value: str) -> str:
        cleaned = str(value or "").strip()
        cleaned = re.sub(r"^[\s\"'“”‘’`]+", "", cleaned)
        cleaned = re.split(
            r"(?:\n|[，,;；]\s*(?:并且|并|然后|同时)|[，,;；]\s*(?:and then|and|then)\b)",
            cleaned,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]
        return cleaned.strip(" \t\r\n.,;:!?\"'`，。；：！？“”‘’")

    def _trim_topic_title_fragment(self, value: str) -> str:
        cleaned = str(value or "").strip()
        cleaned = re.sub(r"^[\s\"'“”‘’`]+", "", cleaned)
        cleaned = re.split(
            r"(?:\n|[，,;；]\s*(?:先做|先从|先|然后|并且|并|first|then|and)\s*)",
            cleaned,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]
        return cleaned.strip(" \t\r\n.,;:!?\"'`，。；：！？“”‘’")

    def _extract_direction_from_request(self, human_request: str) -> str | None:
        if not human_request.strip():
            return None

        patterns = (
            r"方向(?:改成|改为|变成|换成|换为|转成|转为)\s*[:：]?\s*(?P<direction>.+)",
            r"(?:转向|聚焦到|聚焦于|重点放到|重点放在)\s*[:：]?\s*(?P<direction>.+)",
            r"(?:focus on|redirect to|shift to|move to|change direction to)\s+(?P<direction>.+)",
        )
        for pattern in patterns:
            match = re.search(pattern, human_request, flags=re.IGNORECASE)
            if not match:
                continue
            direction = self._trim_steering_fragment(match.group("direction"))
            if direction:
                return direction
        return None

    def _extract_new_topic_title(self, human_request: str | None) -> str | None:
        raw_request = str(human_request or "").strip()
        if not raw_request:
            return None

        patterns = (
            r"(?:帮我|请)?(?:开|建|创建|新建|开始|启动)(?:一个)?(?:新的?)?\s*(?:topic|课题|主题)\s*[:：]?\s*(?P<title>.+)",
            r"(?:new topic|start a new topic|open a new topic|create a new topic)\s*[:：]?\s*(?P<title>.+)",
        )
        for pattern in patterns:
            match = re.search(pattern, raw_request, flags=re.IGNORECASE)
            if not match:
                continue
            title = self._trim_topic_title_fragment(match.group("title"))
            if title:
                return title
        return None

    def _find_known_topic_slug_in_request(self, human_request: str | None) -> str | None:
        raw_request = str(human_request or "").strip().lower()
        if not raw_request:
            return None

        candidate_slugs = [
            str(row.get("topic_slug") or "").strip()
            for row in self.recent_topics(limit=100)
            if str(row.get("topic_slug") or "").strip()
        ]
        candidate_slugs.sort(key=len, reverse=True)
        for slug in candidate_slugs:
            pattern = r"(?<![a-z0-9-])" + re.escape(slug.lower()) + r"(?![a-z0-9-])"
            if re.search(pattern, raw_request):
                return slug
        return None

    def route_codex_chat_request(
        self,
        *,
        task: str,
        explicit_topic_slug: str | None = None,
        explicit_topic: str | None = None,
        explicit_current_topic: bool = False,
        explicit_latest_topic: bool = False,
    ) -> dict[str, Any]:
        if explicit_topic_slug:
            return {
                "route": "explicit_topic_slug",
                "topic_slug": explicit_topic_slug,
                "topic": None,
                "reason": "Caller supplied an explicit topic slug.",
            }
        if explicit_topic:
            return {
                "route": "explicit_topic_title",
                "topic_slug": None,
                "topic": explicit_topic,
                "reason": "Caller supplied an explicit topic title.",
            }
        if explicit_current_topic:
            resolved_topic_slug = self.current_topic_slug(fallback_to_latest=True)
            return {
                "route": "explicit_current_topic",
                "topic_slug": resolved_topic_slug,
                "topic": None,
                "reason": "Caller explicitly requested the current topic route.",
            }
        if explicit_latest_topic:
            resolved_topic_slug = self.latest_topic_slug()
            return {
                "route": "explicit_latest_topic",
                "topic_slug": resolved_topic_slug,
                "topic": None,
                "reason": "Caller explicitly requested the latest topic route.",
            }

        resolved_slug = self._find_known_topic_slug_in_request(task)
        if resolved_slug:
            return {
                "route": "request_named_existing_topic",
                "topic_slug": resolved_slug,
                "topic": None,
                "reason": "The human request already names a known topic slug.",
            }

        new_topic_title = self._extract_new_topic_title(task)
        if new_topic_title:
            return {
                "route": "request_new_topic",
                "topic_slug": None,
                "topic": new_topic_title,
                "reason": "The human request clearly opens a new topic.",
            }

        if re.search(r"(?:这个\s*topic|当前\s*topic|这个\s*课题|当前\s*课题|this topic|current topic|active topic)", task, flags=re.IGNORECASE):
            resolved_topic_slug = self.current_topic_slug(fallback_to_latest=True)
            return {
                "route": "request_current_topic_reference",
                "topic_slug": resolved_topic_slug,
                "topic": None,
                "reason": "The human request refers to the current topic without naming a slug.",
            }

        try:
            resolved_topic_slug = self.current_topic_slug(fallback_to_latest=True)
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                "Unable to infer an AITP topic from this request. Say `开一个新 topic：...` or pass an explicit topic flag."
            ) from exc

        return {
            "route": "implicit_current_topic",
            "topic_slug": resolved_topic_slug,
            "topic": None,
            "reason": "No explicit topic was provided, so the request falls back to current-topic memory.",
        }

    def start_chat_session(
        self,
        *,
        task: str,
        explicit_topic_slug: str | None = None,
        explicit_topic: str | None = None,
        explicit_current_topic: bool = False,
        explicit_latest_topic: bool = False,
        statement: str | None = None,
        run_id: str | None = None,
        control_note: str | None = None,
        updated_by: str = "aitp-session-start",
        skill_queries: list[str] | None = None,
        max_auto_steps: int = 4,
        research_mode: str | None = None,
        load_profile: str | None = None,
    ) -> dict[str, Any]:
        pre_route_current_topic = read_json(self._current_topic_memory_paths()["json"]) or {}
        routing = self.route_codex_chat_request(
            task=task,
            explicit_topic_slug=explicit_topic_slug,
            explicit_topic=explicit_topic,
            explicit_current_topic=explicit_current_topic,
            explicit_latest_topic=explicit_latest_topic,
        )
        payload = self.run_topic_loop(
            topic_slug=routing.get("topic_slug"),
            topic=routing.get("topic"),
            statement=statement,
            run_id=run_id,
            control_note=control_note,
            updated_by=updated_by,
            human_request=task,
            skill_queries=skill_queries,
            max_auto_steps=max_auto_steps,
            research_mode=research_mode,
            load_profile=load_profile,
        )
        session_start = self._materialize_session_start_contract(
            task=task,
            routing=routing,
            loop_payload=payload,
            updated_by=updated_by,
            pre_route_current_topic=pre_route_current_topic,
        )
        payload["session_start"] = session_start
        memory_paths = self._current_topic_memory_paths()
        return {
            "task": task,
            "routing": routing,
            "topic_slug": payload["topic_slug"],
            "run_id": payload.get("run_id"),
            "loop_state_path": payload["loop_state_path"],
            "runtime_protocol_path": payload["runtime_protocol"]["runtime_protocol_path"],
            "load_profile": payload.get("load_profile"),
            "capability_report_path": payload["capability_audit"]["capability_report_path"],
            "trust_report_path": payload["trust_audit"]["trust_report_path"] if payload.get("trust_audit") else None,
            "current_topic_memory": payload["current_topic_memory"],
            "current_topic_memory_path": str(memory_paths["json"]),
            "current_topic_note_path": str(memory_paths["note"]),
            "session_start": session_start,
            "session_start_contract_path": session_start["session_start_contract_path"],
            "session_start_note_path": session_start["session_start_note_path"],
            "bootstrap": payload["bootstrap"],
            "entry_audit": payload["entry_audit"],
            "auto_actions": payload["auto_actions"],
            "exit_audit": payload["exit_audit"],
            "loop_payload": payload,
        }

    def _parse_human_steering_request(self, human_request: str | None) -> dict[str, Any]:
        raw_request = str(human_request or "").strip()
        if not raw_request:
            return {
                "detected": False,
                "decision": None,
                "direction": None,
                "directive": None,
                "summary": None,
            }

        direction = self._extract_direction_from_request(raw_request)
        decision: str | None = None
        if re.search(r"(?:停止|先停|停下|stop\b|halt\b)", raw_request, flags=re.IGNORECASE):
            decision = "stop"
        elif re.search(r"(?:暂停|pause\b)", raw_request, flags=re.IGNORECASE):
            decision = "pause"
        elif re.search(r"(?:分支|分叉|branch\b)", raw_request, flags=re.IGNORECASE):
            decision = "branch"
        elif direction or re.search(r"(?:转向|redirect\b|focus on|shift to|move to)", raw_request, flags=re.IGNORECASE):
            decision = "redirect"
        elif re.search(r"(?:继续这个\s*topic|继续这个\s*课题|继续这个\s*主题|继续\b|接着做|continue\b|resume\b)", raw_request, flags=re.IGNORECASE):
            decision = "continue"

        if decision is None:
            return {
                "detected": False,
                "decision": None,
                "direction": direction,
                "directive": None,
                "summary": None,
            }

        directive: str | None = None
        if decision in {"redirect", "branch"}:
            directive = "human_redirect"
        elif decision in {"pause", "stop"}:
            directive = decision

        if decision == "redirect":
            summary = (
                f"Redirect the active topic toward `{direction}`."
                if direction
                else "Redirect the active topic according to the latest persisted operator request."
            )
        elif decision == "branch":
            summary = (
                f"Open a bounded branch toward `{direction}` while keeping this topic auditable."
                if direction
                else "Open a bounded branch from the current topic while keeping the current evidence trail auditable."
            )
        elif decision == "pause":
            summary = "Pause automatic continuation until the updated operator steering is cleared."
        elif decision == "stop":
            summary = "Stop automatic continuation until the operator explicitly reopens the topic."
        else:
            summary = "Continue the active topic under the current operator steering."

        return {
            "detected": True,
            "decision": decision,
            "direction": direction,
            "directive": directive,
            "summary": summary,
        }

    def _replace_marked_block(
        self,
        existing_text: str,
        *,
        start_marker: str,
        end_marker: str,
        replacement_block: str,
        before_marker: str | None = None,
    ) -> str:
        pattern = re.compile(
            re.escape(start_marker) + r".*?" + re.escape(end_marker),
            flags=re.DOTALL,
        )
        if pattern.search(existing_text):
            return pattern.sub(replacement_block, existing_text)

        base = existing_text.rstrip()
        if before_marker and before_marker in base:
            return base.replace(before_marker, replacement_block + "\n\n" + before_marker, 1) + "\n"
        if base:
            return base + "\n\n" + replacement_block + "\n"
        return replacement_block + "\n"

    def _render_innovation_direction_auto_block(
        self,
        *,
        topic_slug: str,
        steering: dict[str, Any],
        raw_request: str,
        topic_state: dict[str, Any],
    ) -> str:
        decision = str(steering.get("decision") or "continue").strip() or "continue"
        direction = str(steering.get("direction") or "").strip()
        topic_title = self._topic_display_title(topic_slug)
        resume_stage = str(topic_state.get("resume_stage") or topic_state.get("last_materialized_stage") or "L1")
        research_contract_rel = self._relativize(self._research_question_contract_paths(topic_slug)["note"])
        validation_contract_rel = self._relativize(self._validation_contract_paths(topic_slug)["note"])

        if decision == "branch":
            idea_statement = (
                f"Open a bounded branch from `{topic_title}` toward `{direction}` while preserving the current evidence trail."
                if direction
                else f"Open a bounded branch from `{topic_title}` under the latest operator steering."
            )
        elif decision == "redirect":
            idea_statement = (
                f"Redirect the active topic `{topic_title}` toward `{direction}` and treat that lane as the current novelty target."
                if direction
                else f"Redirect the active topic `{topic_title}` according to the latest persisted operator steering."
            )
        elif decision == "pause":
            idea_statement = f"Pause the active topic `{topic_title}` until the operator records the next bounded direction."
        elif decision == "stop":
            idea_statement = f"Stop the active topic `{topic_title}` until the operator explicitly reopens it."
        else:
            idea_statement = (
                f"Continue the active topic `{topic_title}` under innovation direction `{direction}`."
                if direction
                else f"Continue the active topic `{topic_title}` under the latest persisted steering."
            )

        if direction:
            novelty_reason = (
                f"This lane may require different scope, observables, or validation logic than the previous framing. "
                f"Novelty is still unproven until the contracts and evidence are updated around `{direction}`."
            )
            meaningful_novelty = (
                f"A meaningful result must produce a direction-specific question and validation route for `{direction}` "
                "that differs from the previous topic framing in more than wording."
            )
        else:
            novelty_reason = (
                "The latest steering changes operator intent, but the novelty lane is not specific enough yet to count as a new result."
            )
            meaningful_novelty = (
                "A meaningful result must tighten the active question, deliverables, and validation route beyond the prior generic topic shell."
            )
        not_new_enough = "Renaming the direction while reusing the old question, deliverables, and checks unchanged."

        supporting_artifacts = (
            f"`{research_contract_rel}` and `{validation_contract_rel}` exist as the active contract surfaces, "
            "but they may still reflect the previous direction."
        )
        unresolved_gap = (
            f"The redirected direction has not yet been fully absorbed into `{research_contract_rel}` and `{validation_contract_rel}`."
            if direction
            else f"The latest steering has not yet been fully absorbed into `{research_contract_rel}` and `{validation_contract_rel}`."
        )

        if direction:
            next_question = (
                f"What exact problem statement, scope boundary, deliverables, and initial validation route should govern "
                f"`{direction}` inside `{topic_title}`?"
            )
        else:
            next_question = f"What exact bounded question should the next AITP step answer for `{topic_title}`?"

        if decision in {"redirect", "branch"}:
            stop_condition = (
                f"Stop once `{research_contract_rel}` and `{validation_contract_rel}` explicitly reflect `{direction or 'the updated steering'}`."
            )
        elif decision == "pause":
            stop_condition = "Stay paused until a new continue, branch, or redirect decision is written."
        elif decision == "stop":
            stop_condition = "Stay stopped until the operator explicitly reopens the topic."
        else:
            stop_condition = "Stop this loop step once the current contracts and next bounded action are synchronized."

        return "\n".join(
            [
                "<!-- AITP:auto-direction:start -->",
                "> Auto-filled from the latest steering request. Tighten any bullet manually if you need stricter bounds.",
                "",
                "## 1) Initial idea and novelty target",
                "",
                f"- Idea statement: {idea_statement}",
                f"- Why this direction is potentially new: {novelty_reason}",
                f"- What would count as meaningful novelty: {meaningful_novelty}",
                f"- What would count as `not new enough`: {not_new_enough}",
                "",
                "## 2) Current evidence boundary",
                "",
                f"- Highest reliable layer currently reached: `{resume_stage}`",
                f"- Strongest supporting evidence artifacts: {supporting_artifacts}",
                "- Strongest contradictory evidence artifacts: No explicit contradiction artifact is recorded yet.",
                f"- Main unresolved gap: {unresolved_gap}",
                "",
                "## 3) Human steering decision (required)",
                "",
                f"- Decision: `{decision}`",
                f"- Why this decision was chosen: Derived directly from the latest operator request: `{raw_request or '(missing)'}`.",
                "- Resource/risk limit for next loop step: Keep the next step bounded to contract synchronization and initial route selection. Do not claim novelty, proof closure, or execution evidence yet.",
                f"- Deadline or stop condition: {stop_condition}",
                "",
                "## 4) Next bounded question for AI",
                "",
                f"- Next question: {next_question}",
                f"- Required deliverables: Update `{research_contract_rel}`, `{validation_contract_rel}`, and the next-action surface if the steering changes queue selection.",
                "- Required checks: Conformance stays `pass`; control note and contracts agree on the active direction; no old-direction acceptance check remains active.",
                "- Forbidden proxies: Do not treat renamed headings, unchanged old contracts, or narrative confidence as evidence that the topic has actually changed direction.",
                "",
                "## 5) Promotion posture",
                "",
                "- Promotion allowed this step: `no`",
                "- If yes, which candidate IDs are eligible: _(none yet)_",
                "- If no, what must be true first: Direction-specific contracts, at least one bounded evidence artifact, and a candidate that survives the declared checks.",
                "<!-- AITP:auto-direction:end -->",
            ]
        )

    def _innovation_direction_looks_placeholder_heavy(self, text: str) -> bool:
        placeholder_markers = [
            "_(fill manually if missing)_",
            "_(fill manually if needed)_",
            "Decision: _(latest auto-updated snapshot appears below)_",
        ]
        return sum(text.count(marker) for marker in placeholder_markers) >= 4

    def _default_innovation_direction_text(
        self,
        *,
        topic_slug: str,
        run_id: str | None,
        updated_by: str,
        steering: dict[str, Any],
        raw_request: str,
        topic_state: dict[str, Any],
    ) -> str:
        return "\n".join(
            [
                "# Innovation direction",
                "",
                f"topic_slug: `{topic_slug}`",
                f"updated_by: `{updated_by}`",
                f"updated_at: `{now_iso()}`",
                f"run_id: `{run_id or '(none)'}`",
                "",
                self._render_innovation_direction_auto_block(
                    topic_slug=topic_slug,
                    steering=steering,
                    raw_request=raw_request,
                    topic_state=topic_state,
                ),
            ]
        )

    def _materialize_steering_action_contract(
        self,
        *,
        topic_slug: str,
        topic_state: dict[str, Any],
        steering: dict[str, Any],
        updated_by: str,
    ) -> dict[str, Any]:
        next_actions_rel = str(((topic_state.get("pointers") or {}).get("next_actions_path") or "")).strip()
        if not next_actions_rel:
            return {
                "path": None,
                "action_id": None,
                "summary": None,
                "materialized": False,
            }

        next_actions_path = Path(next_actions_rel)
        if not next_actions_path.is_absolute():
            next_actions_path = self.kernel_root / next_actions_path
        contract_path = next_actions_path.parent / "next_actions.contract.json"
        direction = str(steering.get("direction") or "").strip()
        decision = str(steering.get("decision") or "")

        if decision == "branch":
            summary = (
                f"Open a bounded branch toward `{direction}` and refresh the matching research/validation contracts before execution."
                if direction
                else "Open a bounded branch from the current topic and refresh the matching research/validation contracts before execution."
            )
        else:
            summary = (
                f"Redirect the current bounded work toward `{direction}` and refresh the matching research/validation contracts before execution."
                if direction
                else "Redirect the current bounded work according to the persisted operator request and refresh the matching research/validation contracts before execution."
            )

        steering_action_id = f"action:{topic_slug}:steering:operator-redirect"
        existing_payload = read_json(contract_path) or {}
        existing_actions = []
        for row in existing_payload.get("actions") or []:
            if not isinstance(row, dict):
                continue
            action_id = str(row.get("action_id") or "").strip()
            if action_id.startswith(f"action:{topic_slug}:steering:"):
                continue
            existing_actions.append(row)

        steering_row = {
            "action_id": steering_action_id,
            "resume_stage": str(topic_state.get("resume_stage") or "L3"),
            "action_type": "manual_followup",
            "summary": summary,
            "auto_runnable": False,
            "enabled": True,
            "handler_args": {
                "source": "human_request_steering",
                "decision": decision,
                "direction": direction,
            },
        }
        payload = dict(existing_payload)
        payload["contract_version"] = 1
        payload["updated_at"] = now_iso()
        payload["updated_by"] = updated_by
        payload["policy_note"] = (
            "Top action auto-materialized from persisted operator steering so the redirected topic has a durable next step."
        )
        payload["append_runtime_actions"] = True
        payload["append_skill_action_if_needed"] = True
        payload["actions"] = [steering_row, *existing_actions]
        write_json(contract_path, payload)
        return {
            "path": self._relativize(contract_path),
            "action_id": steering_action_id,
            "summary": summary,
            "materialized": True,
        }

    def _render_control_note_markdown(
        self,
        *,
        topic_slug: str,
        run_id: str | None,
        updated_by: str,
        steering: dict[str, Any],
        innovation_direction_path: str,
        innovation_decisions_path: str,
        steering_contract: dict[str, Any] | None,
    ) -> str:
        summary = str(steering.get("summary") or "Persist the latest operator steering for this topic.")
        direction = str(steering.get("direction") or "").strip()
        directive = str(steering.get("directive") or "").strip()
        decision = str(steering.get("decision") or "").strip()
        target_action_id = str((steering_contract or {}).get("action_id") or "").strip()
        target_action_summary = str((steering_contract or {}).get("summary") or "").strip()
        target_artifacts = [
            innovation_direction_path,
            innovation_decisions_path,
        ]
        contract_path = str((steering_contract or {}).get("path") or "").strip()
        if contract_path:
            target_artifacts.append(contract_path)

        lines = [
            "---",
            f"topic_slug: {topic_slug}",
            f"updated_by: {updated_by}",
            f"updated_at: {now_iso()}",
            f"run_id: {run_id or '(none)'}",
            f"summary: {summary}",
        ]
        if directive:
            lines.append(f"directive: {directive}")
        if decision in {"redirect", "branch"}:
            lines.append("allow_override_unfinished: true")
            lines.append("allow_override_decision_contract: true")
        if target_action_id:
            lines.append(f"target_action_id: {target_action_id}")
        if target_action_summary:
            lines.append(f"target_action_summary: {target_action_summary}")
        if target_artifacts:
            lines.extend(["target_artifacts:"] + [f"  - {artifact}" for artifact in target_artifacts])
        stop_conditions = []
        if decision in {"pause", "stop"}:
            stop_conditions.append("Resume only after the operator records a new continue or redirect decision.")
        elif decision in {"redirect", "branch"}:
            stop_conditions.append("Replace this steering redirect once the ordinary queue and contracts absorb the new direction.")
        if stop_conditions:
            lines.extend(["stop_conditions:"] + [f"  - {condition}" for condition in stop_conditions])
        lines.extend(
            [
                "---",
                "",
                "# Control note",
                "",
                f"- Decision: `{decision or '(missing)'}`",
                f"- Direction: `{direction or '(unchanged)'}`",
                f"- Innovation direction note: `{innovation_direction_path}`",
                f"- Innovation decisions log: `{innovation_decisions_path}`",
                f"- Raw operator request: {steering.get('raw_request') or '(missing)'}",
                "",
                "If this steering changes scope, observables, deliverables, or acceptance checks, update the matching research-question or validation contract in the same step.",
            ]
        )
        if contract_path:
            lines.extend(["", f"- Declared next-actions contract: `{contract_path}`"])
        return "\n".join(lines) + "\n"

    def _materialize_steering_payload(
        self,
        *,
        topic_slug: str,
        run_id: str | None,
        steering: dict[str, Any],
        raw_request: str,
        updated_by: str,
        topic_state: dict[str, Any] | None = None,
        control_note: str | None = None,
    ) -> dict[str, Any]:
        runtime_root = self._ensure_runtime_root(topic_slug)
        resolved_topic_state = dict(topic_state or read_json(runtime_root / "topic_state.json") or {})
        innovation_direction_path = self._innovation_direction_path(topic_slug)
        innovation_decisions_path = self._innovation_decisions_path(topic_slug)
        innovation_direction_rel = self._relativize(innovation_direction_path)
        innovation_decisions_rel = self._relativize(innovation_decisions_path)

        existing_innovation_text = (
            innovation_direction_path.read_text(encoding="utf-8")
            if innovation_direction_path.exists()
            else self._default_innovation_direction_text(
                topic_slug=topic_slug,
                run_id=run_id,
                updated_by=updated_by,
                steering=steering,
                raw_request=raw_request,
                topic_state=resolved_topic_state,
            )
        )
        auto_direction_block = self._render_innovation_direction_auto_block(
            topic_slug=topic_slug,
            steering=steering,
            raw_request=raw_request,
            topic_state=resolved_topic_state,
        )
        auto_block = "\n".join(
            [
                "<!-- AITP:auto-steering:start -->",
                "## Auto steering snapshot",
                "",
                f"- Updated at: `{now_iso()}`",
                f"- Updated by: `{updated_by}`",
                f"- Parsed decision: `{steering.get('decision') or '(missing)'}`",
                f"- Parsed direction: `{steering.get('direction') or '(unchanged)'}`",
                f"- Raw operator request: {raw_request or '(missing)'}",
                f"- Innovation decision log: `{innovation_decisions_rel}`",
                "- Rule: if this steering changes scope, observables, deliverables, or acceptance tests, update the matching research-question or validation contract in the same step.",
                "<!-- AITP:auto-steering:end -->",
            ]
        )
        if self._innovation_direction_looks_placeholder_heavy(existing_innovation_text):
            updated_innovation_text = self._default_innovation_direction_text(
                topic_slug=topic_slug,
                run_id=run_id,
                updated_by=updated_by,
                steering=steering,
                raw_request=raw_request,
                topic_state=resolved_topic_state,
            )
        else:
            updated_innovation_text = self._replace_marked_block(
                existing_innovation_text,
                start_marker="<!-- AITP:auto-direction:start -->",
                end_marker="<!-- AITP:auto-direction:end -->",
                replacement_block=auto_direction_block,
                before_marker="<!-- AITP:auto-steering:start -->",
            )
        updated_innovation_text = self._replace_marked_block(
            updated_innovation_text,
            start_marker="<!-- AITP:auto-steering:start -->",
            end_marker="<!-- AITP:auto-steering:end -->",
            replacement_block=auto_block,
        )
        write_text(innovation_direction_path, updated_innovation_text)

        steering_contract = {
            "path": None,
            "action_id": None,
            "summary": None,
            "materialized": False,
        }
        if steering.get("decision") in {"redirect", "branch"}:
            steering_contract = self._materialize_steering_action_contract(
                topic_slug=topic_slug,
                topic_state=resolved_topic_state,
                steering=steering,
                updated_by=updated_by,
            )

        control_note_rel = str(control_note or "").strip() or self._relativize(self._control_note_path(topic_slug))
        if not control_note:
            control_note_path = self._control_note_path(topic_slug)
            control_note_text = self._render_control_note_markdown(
                topic_slug=topic_slug,
                run_id=run_id,
                updated_by=updated_by,
                steering={**steering, "raw_request": raw_request},
                innovation_direction_path=innovation_direction_rel,
                innovation_decisions_path=innovation_decisions_rel,
                steering_contract=steering_contract,
            )
            write_text(control_note_path, control_note_text)
            control_note_rel = self._relativize(control_note_path)

        decision_row = {
            "decision_id": f"innovation-decision:{topic_slug}:{slugify(now_iso())}",
            "topic_slug": topic_slug,
            "run_id": run_id,
            "updated_at": now_iso(),
            "updated_by": updated_by,
            "decision": steering.get("decision"),
            "direction": steering.get("direction"),
            "summary": steering.get("summary"),
            "raw_request": raw_request,
            "innovation_direction_path": innovation_direction_rel,
            "innovation_decisions_path": innovation_decisions_rel,
            "control_note_path": control_note_rel,
            "next_actions_contract_path": steering_contract.get("path"),
            "target_action_id": steering_contract.get("action_id"),
            "target_action_summary": steering_contract.get("summary"),
        }
        decision_rows = read_jsonl(innovation_decisions_path)
        decision_rows.append(decision_row)
        write_jsonl(innovation_decisions_path, decision_rows)

        return {
            "detected": True,
            "materialized": True,
            "requires_reorchestrate": True,
            "decision": steering.get("decision"),
            "direction": steering.get("direction"),
            "summary": steering.get("summary"),
            "control_note_path": control_note_rel,
            "innovation_direction_path": innovation_direction_rel,
            "innovation_decisions_path": innovation_decisions_rel,
            "next_actions_contract_path": steering_contract.get("path"),
            "target_action_id": steering_contract.get("action_id"),
            "target_action_summary": steering_contract.get("summary"),
        }

    def materialize_steering_from_human_request(
        self,
        *,
        topic_slug: str,
        run_id: str | None,
        human_request: str | None,
        updated_by: str,
        topic_state: dict[str, Any] | None = None,
        control_note: str | None = None,
    ) -> dict[str, Any]:
        steering = self._parse_human_steering_request(human_request)
        if not steering.get("detected"):
            return {
                "detected": False,
                "materialized": False,
                "requires_reorchestrate": False,
            }

        return self._materialize_steering_payload(
            topic_slug=topic_slug,
            run_id=run_id,
            steering=steering,
            raw_request=str(human_request or "").strip(),
            updated_by=updated_by,
            topic_state=topic_state,
            control_note=control_note,
        )

    def steer_topic(
        self,
        *,
        topic_slug: str,
        innovation_direction: str,
        decision: str = "continue",
        run_id: str | None = None,
        updated_by: str = "aitp-cli",
        summary: str | None = None,
        next_question: str | None = None,
        target_action_id: str | None = None,
        target_action_summary: str | None = None,
        human_request: str | None = None,
        topic_state: dict[str, Any] | None = None,
        control_note: str | None = None,
    ) -> dict[str, Any]:
        resolved_direction = self._trim_steering_fragment(innovation_direction)
        if not resolved_direction:
            raise ValueError("innovation_direction must not be empty")

        normalized_decision = str(decision or "continue").strip().lower()
        directive: str | None = None
        if normalized_decision in {"redirect", "branch"}:
            directive = "human_redirect"
        elif normalized_decision in {"pause", "stop"}:
            directive = normalized_decision

        if summary:
            resolved_summary = summary
        elif normalized_decision == "branch":
            resolved_summary = f"Open a bounded branch toward `{resolved_direction}` while keeping the current topic auditable."
        elif normalized_decision == "redirect":
            resolved_summary = f"Redirect the active topic toward `{resolved_direction}`."
        elif normalized_decision == "pause":
            resolved_summary = "Pause automatic continuation until the updated operator steering is cleared."
        elif normalized_decision == "stop":
            resolved_summary = "Stop automatic continuation until the operator explicitly reopens the topic."
        else:
            resolved_summary = f"Continue the active topic under updated innovation direction `{resolved_direction}`."

        steering = {
            "detected": True,
            "decision": normalized_decision,
            "direction": resolved_direction,
            "directive": directive,
            "summary": resolved_summary,
            "next_question": str(next_question or "").strip() or None,
            "target_action_id": str(target_action_id or "").strip() or None,
            "target_action_summary": str(target_action_summary or "").strip() or None,
        }
        return self._materialize_steering_payload(
            topic_slug=topic_slug,
            run_id=run_id,
            steering=steering,
            raw_request=str(human_request or "").strip(),
            updated_by=updated_by,
            topic_state=topic_state,
            control_note=control_note,
        )

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

    def _remove_candidate_row(
        self,
        topic_slug: str,
        run_id: str,
        candidate_id: str,
    ) -> None:
        ledger_path = self._candidate_ledger_path(topic_slug, run_id)
        rows = [
            row
            for row in read_jsonl(ledger_path)
            if str(row.get("candidate_id") or "").strip() != candidate_id
        ]
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
            "faithfulness_review": packet_root / "faithfulness_review.json",
            "comparator_audit_record": packet_root / "comparator_audit_record.json",
            "provenance_review": packet_root / "provenance_review.json",
            "prerequisite_closure_review": packet_root / "prerequisite_closure_review.json",
            "formal_theory_review": packet_root / "formal_theory_review.json",
            "merge_report": packet_root / "merge_report.json",
            "auto_promotion_report": packet_root / "auto_promotion_report.json",
        }

    def _consultation_paths(self, topic_slug: str, consultation_slug: str) -> dict[str, Path]:
        call_root = self._consultation_root(topic_slug) / "calls" / f"consult-{consultation_slug}"
        return {
            "request": call_root / "request.json",
            "result": call_root / "result.json",
            "application": call_root / "application.json",
            "summary_note": call_root / "summary.md",
            "memory_map": call_root / "memory_map.json",
            "memory_map_note": call_root / "memory_map.md",
            "index": self._consultation_root(topic_slug) / "consultation_index.jsonl",
        }

    def _exploration_window_paths(self, topic_slug: str) -> dict[str, Path]:
        runtime_root = self._runtime_root(topic_slug)
        return {
            "json": runtime_root / "exploration_window.json",
            "note": runtime_root / "exploration_window.md",
        }

    def _task_type_lane_guidance_paths(self, topic_slug: str) -> dict[str, Path]:
        runtime_root = self._runtime_root(topic_slug)
        return {
            "json": runtime_root / "task_type_lane_guidance.json",
            "note": runtime_root / "task_type_lane_guidance.md",
        }

    def _collaborator_routing_guidance_paths(self, topic_slug: str) -> dict[str, Path]:
        runtime_root = self._runtime_root(topic_slug)
        return {
            "json": runtime_root / "collaborator_routing_guidance.json",
            "note": runtime_root / "collaborator_routing_guidance.md",
        }

    def _render_l2_consultation_summary_markdown(
        self,
        *,
        consultation_id: str,
        topic_slug: str,
        stage: str,
        retrieval_profile: str,
        query_text: str,
        result_summary: str,
        retrieved_refs: list[dict[str, Any]],
        effect_on_work: str,
        projection_paths: list[str],
    ) -> str:
        lines = [
            "# L2 consultation summary",
            "",
            f"- Consultation id: `{consultation_id}`",
            f"- Topic: `{topic_slug}`",
            f"- Stage: `{stage}`",
            f"- Retrieval profile: `{retrieval_profile}`",
            f"- Query: `{query_text}`",
            "",
            result_summary or "(missing summary)",
            "",
        ]
        if retrieved_refs:
            lines.extend(["## Retrieved references", ""])
            for row in retrieved_refs:
                lines.append(
                    f"- `{row.get('trust_surface') or 'unknown'}` :: `{row.get('id') or '(missing-id)'}` :: "
                    f"{row.get('title') or '(untitled)'}"
                )
                lines.append(f"  - Reason: {row.get('selection_reason') or '(missing)'}")
                lines.append(f"  - Path: `{row.get('path') or '(missing)'}`")
                lines.append(f"  - Summary: {row.get('summary') or '(missing)'}")
            lines.append("")
        warning_refs = [
            row
            for row in retrieved_refs
            if str(row.get("unit_type") or "").strip() == "warning_note"
        ]
        if warning_refs:
            lines.extend(["## Warning notes", ""])
            for row in warning_refs:
                lines.append(f"- `{row.get('id') or '(missing-id)'}` :: {row.get('summary') or '(missing)'}")
            lines.append("")
        if effect_on_work:
            lines.extend(["## Effect on work", "", effect_on_work, ""])
        if projection_paths:
            lines.extend(["## Follow-up paths", ""])
            for path in projection_paths:
                lines.append(f"- `{path}`")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def _render_l2_consultation_memory_map_markdown(
        self,
        *,
        consultation_id: str,
        topic_slug: str,
        retrieval_profile: str,
        query_text: str,
        graph_surface: dict[str, Any],
        primary_refs: list[dict[str, Any]],
        expanded_refs: list[dict[str, Any]],
        warning_refs: list[dict[str, Any]],
        staged_refs: list[dict[str, Any]],
    ) -> str:
        lines = [
            "# L2 consultation memory map",
            "",
            f"- Consultation id: `{consultation_id}`",
            f"- Topic: `{topic_slug}`",
            f"- Retrieval profile: `{retrieval_profile}`",
            f"- Query: `{query_text}`",
            "",
            "## Canonical graph status",
            "",
            f"- Status: `{graph_surface.get('status') or '(missing)'}`",
            f"- Unit count: `{graph_surface.get('unit_count') or 0}`",
            f"- Edge count: `{graph_surface.get('edge_count') or 0}`",
            f"- Unit types: `{', '.join(graph_surface.get('unit_types') or []) or '(none)'}`",
            "",
            f"{graph_surface.get('summary') or '(missing graph summary)'}",
            "",
            "## Primary canonical hits",
            "",
        ]
        if primary_refs:
            for row in primary_refs:
                lines.append(f"- `{row.get('id') or '(missing-id)'}` :: {row.get('title') or '(untitled)'}")
                lines.append(f"  - Reason: {row.get('selection_reason') or '(missing)'}")
                lines.append(f"  - Path: `{row.get('path') or '(missing)'}`")
        else:
            lines.append("- `(none)`")
        lines.extend(["", "## Expanded canonical hits", ""])
        if expanded_refs:
            for row in expanded_refs:
                lines.append(f"- `{row.get('id') or '(missing-id)'}` :: {row.get('title') or '(untitled)'}")
                lines.append(f"  - Reason: {row.get('selection_reason') or '(missing)'}")
                lines.append(f"  - Path: `{row.get('path') or '(missing)'}`")
        else:
            lines.append("- `(none)`")
        lines.extend(["", "## Warning notes", ""])
        if warning_refs:
            for row in warning_refs:
                lines.append(f"- `{row.get('id') or '(missing-id)'}` :: {row.get('summary') or '(missing)'}")
        else:
            lines.append("- `(none)`")
        lines.extend(["", "## Staged hits", ""])
        if staged_refs:
            for row in staged_refs:
                lines.append(f"- `{row.get('id') or '(missing-id)'}` :: {row.get('title') or '(untitled)'}")
                lines.append(f"  - Reason: {row.get('selection_reason') or '(missing)'}")
                lines.append(f"  - Path: `{row.get('path') or '(missing)'}`")
        else:
            lines.append("- `(none)`")
        lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def _render_exploration_window_markdown(self, payload: dict[str, Any]) -> str:
        lines = [
            "# Exploration window",
            "",
            f"- Status: `{payload.get('status') or '(missing)'}`",
            f"- Window open: `{str(bool(payload.get('window_open'))).lower()}`",
            f"- Closure required: `{str(bool(payload.get('closure_required'))).lower()}`",
            f"- Likely next target layer: `{payload.get('likely_next_target_layer') or '(missing)'}`",
            "",
            "## Current question",
            "",
            f"{payload.get('current_question') or '(none)'}",
            "",
            "## Candidate intuitions",
            "",
        ]
        candidate_intuitions = payload.get("candidate_intuitions") or []
        if candidate_intuitions:
            for item in candidate_intuitions:
                lines.append(f"- {item}")
        else:
            lines.append("- `(none)`")
        lines.extend(["", "## Local blockers", ""])
        local_blockers = payload.get("local_blockers") or []
        if local_blockers:
            for item in local_blockers:
                lines.append(f"- {item}")
        else:
            lines.append("- `(none)`")
        lines.extend(["", "## Summary", "", f"{payload.get('summary') or '(missing)' }", ""])
        return "\n".join(lines).rstrip() + "\n"

    def _lane_family(self, lane: str | None) -> str:
        normalized = str(lane or "").strip()
        if normalized == "formal_theory":
            return "formal_theory"
        if normalized in {"toy_numeric", "theory_synthesis"}:
            return "model_numeric"
        if normalized in {"code_method", "first_principles"}:
            return "code_and_materials"
        return "formal_theory"

    def _derive_task_type_lane_guidance(self, *, topic_slug: str, task_type: str, lane: str) -> dict[str, Any]:
        lane_family = self._lane_family(lane)
        templates: dict[tuple[str, str], dict[str, Any]] = {
            (
                "open_exploration",
                "formal_theory",
            ): {
                "summary": "Open formal-theory exploration should widen the source basis first, compare multiple structural routes in L3-A, and treat L4 as a partial or blocking check rather than a closure demand.",
                "l0_expectation": "Broaden the formal source basis before locking one route.",
                "l1_expectation": "Read comparatively for assumptions, notation, and tension across nearby sources.",
                "l3_expectation": "Keep route comparison active in L3-A instead of hardening one line too early.",
                "l4_expectation": "Allow partial or blocking analytical checks without forcing fake closure.",
                "l2_writeback_expectation": "Only distill scoped reusable insights after L3-D decides they survived the exploratory loop.",
                "recommended_first_moves": [
                    "Expand the nearby formal source basis before narrowing notation or claims.",
                    "Compare at least two candidate bridge or structure routes in L3-A.",
                    "Use L4 only for bounded sanity checks, not full closure pressure.",
                ],
                "human_interaction_bias": "Prefer non-blocking updates unless a contradiction or route boundary becomes consequential.",
            },
            (
                "conjecture_attempt",
                "model_numeric",
            ): {
                "summary": "Conjectural model-numeric work should tighten the benchmark model, compare candidate bridges explicitly, and demand a meaningful first check rather than staying at survey level.",
                "l0_expectation": "Gather the specific benchmark-model and nearby comparison sources needed to sharpen the conjecture.",
                "l1_expectation": "Extract assumptions and regime limits tightly enough to turn the conjecture into candidate checks.",
                "l3_expectation": "Use L3-A to compare bridge candidates and isolate the one most worth testing.",
                "l4_expectation": "Run a meaningful first benchmark or consistency check, not only descriptive survey work.",
                "l2_writeback_expectation": "Write back only the checked bridge candidate, warning, or negative result that survives the first test.",
                "recommended_first_moves": [
                    "Choose the smallest honest benchmark model for the conjecture.",
                    "Write the candidate bridge and its expected failure modes explicitly before checking.",
                    "Use the first bounded L4 check to eliminate or sharpen the conjecture.",
                ],
                "human_interaction_bias": "Allow exploratory comparison early, but checkpoint when the conjecture hardens into a main route.",
            },
            (
                "target_driven_execution",
                "code_and_materials",
            ): {
                "summary": "Target-driven code-and-materials work should narrow L0 to implementation-relevant sources, keep L1 highly technical, harden one route in L3, and carry a heavy L4 burden.",
                "l0_expectation": "Restrict the source basis to implementation, algorithm, and benchmark-critical material.",
                "l1_expectation": "Read at high technical detail for interfaces, assumptions, and exact benchmark obligations.",
                "l3_expectation": "Harden one route and track concrete blockers rather than keeping many speculative branches open.",
                "l4_expectation": "Require an explicit benchmark, execution artifact, or bounded numerical check before claiming progress.",
                "l2_writeback_expectation": "Write back only reusable workflow, validation, warning, or method memory that survived the execution check.",
                "recommended_first_moves": [
                    "Narrow the relevant implementation and benchmark sources first.",
                    "Choose one bounded execution route and define the first hard benchmark.",
                    "Do not widen scope until the first benchmark or validation artifact exists.",
                ],
                "human_interaction_bias": "Prefer ordinary continuation; raise checkpoints at route-choice, benchmark-mismatch, or resource-risk boundaries.",
            },
        }
        fallback_by_task_type: dict[str, dict[str, Any]] = {
            "open_exploration": {
                "summary": "Open exploration should keep source intake broad, route comparison live, and closure pressure low until one route earns harder validation.",
                "l0_expectation": "Broaden sources before narrowing.",
                "l1_expectation": "Read comparatively rather than monolithically.",
                "l3_expectation": "Compare routes before hardening one.",
                "l4_expectation": "Use bounded partial checks.",
                "l2_writeback_expectation": "Write back only scoped reusable insights after distillation.",
                "recommended_first_moves": [
                    "Broaden the nearby source basis.",
                    "Compare candidate routes before hardening one.",
                ],
                "human_interaction_bias": "Prefer free exploration unless a harder boundary is reached.",
            },
            "conjecture_attempt": {
                "summary": "Conjecture attempts should sharpen one plausible bridge into a bounded candidate and ask for a real first check.",
                "l0_expectation": "Gather the minimum source basis that can sharpen the conjecture honestly.",
                "l1_expectation": "Extract assumptions and regime limits tightly enough to define a check.",
                "l3_expectation": "Compare bridge candidates and pick one to test.",
                "l4_expectation": "Run a meaningful bounded check early.",
                "l2_writeback_expectation": "Write back only checked bridge or failure memory.",
                "recommended_first_moves": [
                    "State the bridge candidate explicitly.",
                    "Choose the first bounded check before widening scope.",
                ],
                "human_interaction_bias": "Stay flexible early, then checkpoint when one route hardens.",
            },
            "target_driven_execution": {
                "summary": "Target-driven execution should narrow scope early, harden one route, and insist on concrete validation artifacts.",
                "l0_expectation": "Gather only route-critical sources.",
                "l1_expectation": "Read technically and concretely.",
                "l3_expectation": "Harden one route and surface blockers explicitly.",
                "l4_expectation": "Demand a hard benchmark or validation artifact.",
                "l2_writeback_expectation": "Write back only reusable checked workflow or method memory.",
                "recommended_first_moves": [
                    "Choose one bounded execution route.",
                    "Define the first benchmark or validation artifact.",
                ],
                "human_interaction_bias": "Prefer ordinary continuation unless a true checkpoint boundary appears.",
            },
        }
        template = templates.get((task_type, lane_family), fallback_by_task_type.get(task_type, fallback_by_task_type["open_exploration"]))
        return {
            "topic_slug": topic_slug,
            "task_type": task_type,
            "lane": lane,
            "lane_family": lane_family,
            **template,
        }

    def _render_task_type_lane_guidance_markdown(self, payload: dict[str, Any]) -> str:
        lines = [
            "# Task-Type By Lane Guidance",
            "",
            f"- Task type: `{payload.get('task_type') or '(missing)'}`",
            f"- Lane: `{payload.get('lane') or '(missing)'}`",
            f"- Lane family: `{payload.get('lane_family') or '(missing)'}`",
            "",
            "## Summary",
            "",
            f"{payload.get('summary') or '(missing)'}",
            "",
            "## Layer expectations",
            "",
            f"- L0: {payload.get('l0_expectation') or '(missing)'}",
            f"- L1: {payload.get('l1_expectation') or '(missing)'}",
            f"- L3: {payload.get('l3_expectation') or '(missing)'}",
            f"- L4: {payload.get('l4_expectation') or '(missing)'}",
            f"- L2 writeback: {payload.get('l2_writeback_expectation') or '(missing)'}",
            "",
            "## Recommended first moves",
            "",
        ]
        for item in payload.get("recommended_first_moves") or ["(none)"]:
            lines.append(f"- {item}")
        lines.extend(
            [
                "",
                "## Human interaction bias",
                "",
                f"{payload.get('human_interaction_bias') or '(missing)'}",
                "",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    def _derive_collaborator_routing_guidance(
        self,
        *,
        topic_slug: str,
        task_type: str,
        lane: str,
        task_type_lane_guidance: dict[str, Any],
        collaborator_memory: dict[str, Any],
        override_surfaces: list[dict[str, str]],
    ) -> dict[str, Any]:
        preferred_lanes = self._dedupe_strings(list(collaborator_memory.get("preferred_lanes") or []))
        lane_family = self._lane_family(lane)
        if not preferred_lanes:
            alignment_status = "no_preference"
            summary = "No collaborator lane preference is currently recorded, so routing can follow the active task-type guidance without a preference conflict."
            recommended_steering_action = "Use the current task-type-by-lane guidance and only override it if the operator wants a different route."
        elif lane in preferred_lanes or lane_family in preferred_lanes:
            alignment_status = "aligned"
            summary = "The current route is aligned with recorded collaborator lane preferences."
            recommended_steering_action = "Continue with the current route unless the operator explicitly redirects scope or validation style."
        else:
            alignment_status = "preference_mismatch"
            summary = (
                f"The current route (`{lane}` / `{lane_family}`) does not match the recorded collaborator lane preferences "
                f"({', '.join(preferred_lanes)})."
            )
            recommended_steering_action = (
                "Review the override surfaces and decide whether to keep the current route or redirect the topic toward a preferred lane."
            )
        return {
            "topic_slug": topic_slug,
            "task_type": task_type,
            "lane": lane,
            "lane_family": lane_family,
            "preferred_lanes": preferred_lanes,
            "alignment_status": alignment_status,
            "summary": summary,
            "recommended_steering_action": recommended_steering_action,
            "override_surfaces": override_surfaces,
            "guidance_ref": task_type_lane_guidance.get("note_path") or "",
        }

    def _render_collaborator_routing_guidance_markdown(self, payload: dict[str, Any]) -> str:
        lines = [
            "# Collaborator Routing Guidance",
            "",
            f"- Task type: `{payload.get('task_type') or '(missing)'}`",
            f"- Lane: `{payload.get('lane') or '(missing)'}`",
            f"- Lane family: `{payload.get('lane_family') or '(missing)'}`",
            f"- Alignment status: `{payload.get('alignment_status') or '(missing)'}`",
            f"- Preferred lanes: `{', '.join(payload.get('preferred_lanes') or []) or '(none)'}`",
            f"- Guidance reference: `{payload.get('guidance_ref') or '(missing)'}`",
            "",
            "## Summary",
            "",
            f"{payload.get('summary') or '(missing)'}",
            "",
            "## Recommended steering action",
            "",
            f"{payload.get('recommended_steering_action') or '(missing)'}",
            "",
            "## Override surfaces",
            "",
        ]
        for row in payload.get("override_surfaces") or []:
            lines.append(f"- `{row.get('surface') or '(missing)'}` :: `{row.get('path') or '(missing)'}` :: {row.get('role') or '(missing)'}")
        if not payload.get("override_surfaces"):
            lines.append("- `(none)`")
        lines.append("")
        return "\n".join(lines).rstrip() + "\n"

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
        primary_refs: list[dict[str, Any]] | None = None,
        expanded_refs: list[dict[str, Any]] | None = None,
        staged_refs: list[dict[str, Any]] | None = None,
        warning_refs: list[dict[str, Any]] | None = None,
        graph_surface: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        consultation_id = f"consult:{consultation_slug}"
        timestamp = now_iso()
        paths = self._consultation_paths(topic_slug, consultation_slug)
        resolved_primary_refs = list(primary_refs or [])
        resolved_expanded_refs = list(expanded_refs or [])
        resolved_staged_refs = list(staged_refs or [])
        resolved_warning_refs = list(warning_refs or [])
        resolved_graph_surface = dict(graph_surface or self._canonical_l2_graph_surface())

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
        memory_map_payload: dict[str, Any] = {
            "consultation_id": consultation_id,
            "topic_slug": topic_slug,
            "stage": stage,
            "retrieval_profile": retrieval_profile,
            "query_text": query_text,
            "graph_surface": resolved_graph_surface,
            "primary_refs": resolved_primary_refs,
            "expanded_refs": resolved_expanded_refs,
            "warning_refs": resolved_warning_refs,
            "staged_refs": resolved_staged_refs,
            "result_summary": result_summary,
            "updated_at": timestamp,
        }
        index_entry: dict[str, Any] = {
            "consultation_id": consultation_id,
            "topic_slug": topic_slug,
            "stage": stage,
            "status": "applied",
            "context_ref": context_ref,
            "query_text": query_text,
            "retrieval_profile": retrieval_profile,
            "request_path": self._relativize(paths["request"]),
            "result_path": self._relativize(paths["result"]),
            "application_path": self._relativize(paths["application"]),
            "summary_note_path": self._relativize(paths["summary_note"]),
            "memory_map_path": self._relativize(paths["memory_map"]),
            "memory_map_note_path": self._relativize(paths["memory_map_note"]),
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
        write_json(paths["memory_map"], memory_map_payload)
        write_text(
            paths["summary_note"],
            self._render_l2_consultation_summary_markdown(
                consultation_id=consultation_id,
                topic_slug=topic_slug,
                stage=stage,
                retrieval_profile=retrieval_profile,
                query_text=query_text,
                result_summary=result_summary,
                retrieved_refs=retrieved_refs,
                effect_on_work=effect_on_work,
                projection_paths=projection_paths,
            ),
        )
        write_text(
            paths["memory_map_note"],
            self._render_l2_consultation_memory_map_markdown(
                consultation_id=consultation_id,
                topic_slug=topic_slug,
                retrieval_profile=retrieval_profile,
                query_text=query_text,
                graph_surface=resolved_graph_surface,
                primary_refs=resolved_primary_refs,
                expanded_refs=resolved_expanded_refs,
                warning_refs=resolved_warning_refs,
                staged_refs=resolved_staged_refs,
            ),
        )
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
            "consultation_summary_path": str(paths["summary_note"]),
            "consultation_memory_map_path": str(paths["memory_map"]),
            "consultation_memory_map_note_path": str(paths["memory_map_note"]),
            "consultation_index_path": str(paths["index"]),
        }

    def _runtime_protocol_markdown(self, payload: dict[str, Any]) -> str:
        load_profile = str(payload.get("load_profile") or "light")
        l0_sources = payload.get("l0_sources") or {}
        l1_understanding = payload.get("l1_understanding") or {}
        l4_validation = payload.get("l4_validation") or {}
        l2_memory = payload.get("l2_memory") or {}
        topic_synopsis = payload.get("topic_synopsis") or {}
        l3_subplanes = payload.get("l3_subplanes") or {}
        l3_analysis = l3_subplanes.get("analysis") or {}
        l3_result_integration = l3_subplanes.get("result_integration") or {}
        l3_distillation = l3_subplanes.get("distillation") or {}
        pending_decisions = payload.get("pending_decisions") or {}
        minimal = payload.get("minimal_execution_brief") or {}
        active_research_contract = payload.get("active_research_contract") or {}
        idea_packet = payload.get("idea_packet") or {}
        operator_checkpoint = payload.get("operator_checkpoint") or {}
        promotion_readiness = payload.get("promotion_readiness") or {}
        open_gap_summary = payload.get("open_gap_summary") or {}
        strategy_memory = payload.get("strategy_memory") or {}
        collaborator_memory = payload.get("collaborator_memory") or {}
        exploration_window = payload.get("exploration_window") or {}
        task_type_lane_guidance = payload.get("task_type_lane_guidance") or {}
        collaborator_routing_guidance = payload.get("collaborator_routing_guidance") or {}
        topic_skill_projection = payload.get("topic_skill_projection") or {}
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
            f"- Load profile: `{load_profile}`",
            "",
            "## L0 source basis",
            "",
            f"- Status: `{l0_sources.get('status') or '(missing)'}`",
            f"- Projection path: `{l0_sources.get('path') or '(missing)'}`",
            f"- Source index: `{l0_sources.get('primary_output_path') or '(missing)'}`",
            f"- Source count: `{l0_sources.get('source_count') or 0}`",
            "",
            f"{l0_sources.get('summary') or '(missing)'}",
            "",
            "## L1 understanding basis",
            "",
            f"- Status: `{l1_understanding.get('status') or '(missing)'}`",
            f"- Projection path: `{l1_understanding.get('path') or '(missing)'}`",
            f"- Intake status path: `{l1_understanding.get('primary_output_path') or '(missing)'}`",
            f"- Intake stage: `{l1_understanding.get('intake_stage') or '(missing)'}`",
            "",
            f"{l1_understanding.get('summary') or '(missing)'}",
            "",
            "## L4 validation surface",
            "",
            f"- Status: `{l4_validation.get('status') or '(missing)'}`",
            f"- Projection path: `{l4_validation.get('path') or '(missing)'}`",
            f"- Primary validation output: `{l4_validation.get('primary_output_path') or '(missing)'}`",
            f"- Validation mode: `{l4_validation.get('validation_mode') or '(missing)'}`",
            f"- Evidence status: `{l4_validation.get('evidence_status') or '(missing)'}`",
            "",
            f"{l4_validation.get('summary') or '(missing)'}",
            "",
            "## L2 memory surface",
            "",
            f"- Status: `{l2_memory.get('status') or '(missing)'}`",
            f"- Projection path: `{l2_memory.get('path') or '(missing)'}`",
            f"- Primary memory output: `{l2_memory.get('primary_output_path') or '(missing)'}`",
            f"- Consultation count: `{l2_memory.get('consultation_count') or 0}`",
            f"- Staging entry count: `{l2_memory.get('staging_entry_count') or 0}`",
            "",
            f"{l2_memory.get('summary') or '(missing)'}",
            "",
            "## Topic synopsis",
            "",
            f"- Synopsis path: `{topic_synopsis.get('path') or '(missing)'}`",
            f"- Lane: `{topic_synopsis.get('lane') or '(missing)'}`",
            f"- Pending decisions: `{topic_synopsis.get('pending_decision_count') or 0}`",
            f"- Knowledge packets: `{len(topic_synopsis.get('knowledge_packet_paths') or [])}`",
            "",
            f"{topic_synopsis.get('next_action_summary') or '(missing)'}",
            "",
            "## L3 subplanes",
            "",
            f"- `L3-A` status: `{l3_analysis.get('status') or '(missing)'}`",
            f"- `L3-A` note: `{l3_analysis.get('note_path') or '(missing)'}`",
            f"- `L3-A` next: `{', '.join(l3_analysis.get('next_allowed_transitions') or []) or '(missing)'}`",
            "",
            f"{l3_analysis.get('summary') or '(missing)'}",
            "",
            f"- `L3-R` status: `{l3_result_integration.get('status') or '(missing)'}`",
            f"- `L3-R` note: `{l3_result_integration.get('note_path') or '(missing)'}`",
            f"- `L3-R` next: `{', '.join(l3_result_integration.get('next_allowed_transitions') or []) or '(missing)'}`",
            "",
            f"{l3_result_integration.get('summary') or '(missing)'}",
            "",
            f"- `L3-D` status: `{l3_distillation.get('status') or '(missing)'}`",
            f"- `L3-D` note: `{l3_distillation.get('note_path') or '(missing)'}`",
            f"- `L3-D` next: `{', '.join(l3_distillation.get('next_allowed_transitions') or []) or '(missing)'}`",
            f"- Forbidden direct transitions: `{', '.join(l3_distillation.get('forbidden_direct_transitions') or []) or '(none)'}`",
            "",
            f"{l3_distillation.get('summary') or '(missing)'}",
            "",
            "## Pending decisions",
            "",
            f"- Projection path: `{pending_decisions.get('path') or '(missing)'}`",
            f"- Pending count: `{pending_decisions.get('pending_count') or 0}`",
            f"- Blocking count: `{pending_decisions.get('blocking_count') or 0}`",
            f"- Latest resolved trace: `{pending_decisions.get('latest_resolved_trace_ref') or '(none)'}`",
            "",
            f"{pending_decisions.get('latest_resolved_summary') or '(no resolved decision trace recorded)'}",
            "",
            "## Active research contract",
            "",
            f"- Question id: `{active_research_contract.get('question_id') or '(missing)'}`",
            f"- Title: `{active_research_contract.get('title') or '(missing)'}`",
            f"- Status: `{active_research_contract.get('status') or '(missing)'}`",
            f"- Task type: `{active_research_contract.get('task_type') or '(missing)'}`",
            f"- Template mode: `{active_research_contract.get('template_mode') or '(missing)'}`",
            f"- Validation mode: `{active_research_contract.get('validation_mode') or '(missing)'}`",
            f"- Contract JSON: `{active_research_contract.get('path') or '(missing)'}`",
            f"- Contract note: `{active_research_contract.get('note_path') or '(missing)'}`",
            "",
            f"{active_research_contract.get('question') or '(missing)'}",
            "",
            "## Idea packet",
            "",
            f"- Status: `{idea_packet.get('status') or '(missing)'}`",
            f"- Idea note: `{idea_packet.get('note_path') or '(missing)'}`",
            f"- First validation route: `{idea_packet.get('first_validation_route') or '(missing)'}`",
            f"- Initial evidence bar: `{idea_packet.get('initial_evidence_bar') or '(missing)'}`",
            f"- Missing fields: `{', '.join(idea_packet.get('missing_fields') or []) or '(none)'}`",
            "",
            f"{idea_packet.get('status_reason') or '(missing)'}",
            "",
            "## Operator checkpoint",
            "",
            f"- Status: `{operator_checkpoint.get('status') or '(missing)'}`",
            f"- Kind: `{operator_checkpoint.get('checkpoint_kind') or '(none)'}`",
            f"- Checkpoint note: `{operator_checkpoint.get('note_path') or '(missing)'}`",
            "",
            f"{operator_checkpoint.get('question') or '(none)'}",
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
            "## Strategy memory",
            "",
            f"- Status: `{strategy_memory.get('status') or '(missing)'}`",
            f"- Lane: `{strategy_memory.get('lane') or '(missing)'}`",
            f"- Row count: `{strategy_memory.get('row_count') or 0}`",
            f"- Relevant count: `{strategy_memory.get('relevant_count') or 0}`",
            f"- Helpful count: `{strategy_memory.get('helpful_count') or 0}`",
            f"- Harmful count: `{strategy_memory.get('harmful_count') or 0}`",
            f"- Latest path: `{strategy_memory.get('latest_path') or '(none)'}`",
            "",
            f"{strategy_memory.get('summary') or '(missing)'}",
            "",
            "## Collaborator memory",
            "",
            f"- Status: `{collaborator_memory.get('status') or '(missing)'}`",
            f"- Preference count: `{collaborator_memory.get('preference_count') or 0}`",
            f"- Preferred lanes: `{', '.join(collaborator_memory.get('preferred_lanes') or []) or '(none)'}`",
            f"- Note path: `{collaborator_memory.get('note_path') or '(none)'}`",
            "",
            f"{collaborator_memory.get('summary') or '(missing)'}",
            "",
            "## Exploration window",
            "",
            f"- Status: `{exploration_window.get('status') or '(missing)'}`",
            f"- Window note: `{exploration_window.get('note_path') or '(missing)'}`",
            f"- Window open: `{str(bool(exploration_window.get('window_open'))).lower()}`",
            f"- Closure required: `{str(bool(exploration_window.get('closure_required'))).lower()}`",
            f"- Likely next target layer: `{exploration_window.get('likely_next_target_layer') or '(missing)'}`",
            "",
            f"{exploration_window.get('summary') or '(missing)'}",
            "",
            "## Task-Type By Lane Guidance",
            "",
            f"- Task type: `{task_type_lane_guidance.get('task_type') or '(missing)'}`",
            f"- Lane: `{task_type_lane_guidance.get('lane') or '(missing)'}`",
            f"- Lane family: `{task_type_lane_guidance.get('lane_family') or '(missing)'}`",
            f"- Guidance note: `{task_type_lane_guidance.get('note_path') or '(missing)'}`",
            "",
            f"{task_type_lane_guidance.get('summary') or '(missing)'}",
            "",
            "## Collaborator Routing Guidance",
            "",
            f"- Alignment status: `{collaborator_routing_guidance.get('alignment_status') or '(missing)'}`",
            f"- Preferred lanes: `{', '.join(collaborator_routing_guidance.get('preferred_lanes') or []) or '(none)'}`",
            f"- Routing note: `{collaborator_routing_guidance.get('note_path') or '(missing)'}`",
            "",
            f"{collaborator_routing_guidance.get('summary') or '(missing)'}",
            "",
            "## Topic skill projection",
            "",
            f"- Status: `{topic_skill_projection.get('status') or '(missing)'}`",
            f"- Projection id: `{topic_skill_projection.get('id') or '(missing)'}`",
            f"- Candidate id: `{topic_skill_projection.get('candidate_id') or '(none)'}`",
            f"- Note path: `{topic_skill_projection.get('note_path') or '(missing)'}`",
            f"- Intended L2 target: `{topic_skill_projection.get('intended_l2_target') or '(none)'}`",
            "",
            f"{topic_skill_projection.get('summary') or '(missing)'}",
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
        if strategy_memory.get("guidance"):
            lines.extend(["", "## Strategy guidance", ""])
            for item in strategy_memory.get("guidance") or []:
                lines.append(f"- {item}")
        if topic_skill_projection.get("required_first_routes"):
            lines.extend(["", "## Projection route guidance", ""])
            for item in topic_skill_projection.get("required_first_routes") or []:
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
                f"- Keep ordinary topic work in the `{load_profile}` profile unless a real trigger forces escalation.",
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
        load_profile: str | None = None,
    ) -> dict[str, str]:
        runtime_root = self._ensure_runtime_root(topic_slug)
        topic_state = read_json(runtime_root / "topic_state.json") or {}
        resolved_load_profile, load_profile_reason = self._resolve_load_profile(
            explicit_load_profile=load_profile,
            human_request=human_request,
            topic_state=topic_state,
        )
        topic_state = self._persist_load_profile_state(
            topic_slug=topic_slug,
            load_profile=resolved_load_profile,
            reason=load_profile_reason,
            updated_by=updated_by,
        )
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
        idea_packet = dict(shell_surfaces["idea_packet"])
        runtime_task_type = self._coalesce_string(
            research_contract.get("task_type"),
            idea_packet.get("task_type"),
            self._infer_task_type(human_request or str(interaction_state.get("human_request") or "")),
        )
        research_contract = {**research_contract, "task_type": runtime_task_type}
        idea_packet["task_type"] = runtime_task_type
        idea_packet["path"] = self._relativize(Path(shell_surfaces["idea_packet_path"]))
        idea_packet["note_path"] = self._relativize(Path(shell_surfaces["idea_packet_note_path"]))
        operator_checkpoint = dict(shell_surfaces["operator_checkpoint"])
        operator_checkpoint["path"] = self._relativize(Path(shell_surfaces["operator_checkpoint_path"]))
        operator_checkpoint["note_path"] = self._relativize(Path(shell_surfaces["operator_checkpoint_note_path"]))
        operator_checkpoint["ledger_path"] = self._relativize(Path(shell_surfaces["operator_checkpoint_ledger_path"]))
        promotion_readiness = dict(shell_surfaces["promotion_readiness"])
        promotion_readiness["path"] = self._relativize(Path(shell_surfaces["promotion_readiness_path"]))
        open_gap_summary = dict(shell_surfaces["open_gap_summary"])
        open_gap_summary["path"] = self._relativize(Path(shell_surfaces["gap_map_path"]))
        strategy_memory = dict(
            shell_surfaces.get("strategy_memory")
            or {
                "topic_slug": topic_slug,
                "latest_run_id": str(topic_state.get("latest_run_id") or ""),
                "status": "absent",
                "lane": self._lane_for_modes(
                    template_mode=research_contract.get("template_mode"),
                    research_mode=research_contract.get("research_mode"),
                ),
                "row_count": 0,
                "relevant_count": 0,
                "helpful_count": 0,
                "harmful_count": 0,
                "latest_path": None,
                "relevant_paths": [],
                "guidance": [],
                "summary": "No run-local strategy memory is currently recorded for this topic.",
            }
        )
        collaborator_memory = self._derive_collaborator_memory_summary()
        topic_skill_projection = dict(
            shell_surfaces.get("topic_skill_projection")
            or {
                "id": f"topic_skill_projection:{slugify(topic_slug)}",
                "topic_slug": topic_slug,
                "source_topic_slug": topic_slug,
                "run_id": str(topic_state.get("latest_run_id") or ""),
                "title": f"{self._topic_display_title(topic_slug)} Topic Skill Projection",
                "summary": "No validated topic-skill projection is currently available for this topic.",
                "lane": self._lane_for_modes(
                    template_mode=research_contract.get("template_mode"),
                    research_mode=research_contract.get("research_mode"),
                ),
                "status": "not_applicable",
                "status_reason": "No topic-skill projection was materialized for this topic.",
                "candidate_id": None,
                "intended_l2_target": None,
                "entry_signals": [],
                "required_first_reads": [],
                "required_first_routes": [],
                "benchmark_first_rules": [],
                "operator_checkpoint_rules": [],
                "operation_trust_requirements": [],
                "strategy_guidance": [],
                "forbidden_proxies": [],
                "derived_from_artifacts": [],
                "path": None,
                "note_path": None,
                "updated_at": now_iso(),
                "updated_by": updated_by,
            }
        )
        topic_completion = dict(shell_surfaces["topic_completion"])
        topic_completion["path"] = self._relativize(Path(shell_surfaces["topic_completion_note_path"]))
        lean_bridge = dict(shell_surfaces["lean_bridge"])
        lean_bridge["path"] = self._relativize(Path(shell_surfaces["lean_bridge_note_path"]))
        active_research_contract = {
            "question_id": str(research_contract.get("question_id") or ""),
            "title": str(research_contract.get("title") or ""),
            "status": str(research_contract.get("status") or ""),
            "task_type": str(research_contract.get("task_type") or ""),
            "template_mode": str(research_contract.get("template_mode") or ""),
            "research_mode": str(research_contract.get("research_mode") or ""),
            "validation_mode": str(validation_contract.get("validation_mode") or ""),
            "target_layers": self._dedupe_strings(list(research_contract.get("target_layers") or [])),
            "question": str(research_contract.get("question") or ""),
            "path": self._relativize(Path(shell_surfaces["research_question_contract_path"])),
            "note_path": self._relativize(Path(shell_surfaces["research_question_contract_note_path"])),
        }
        latest_run_id = str(topic_state.get("latest_run_id") or "").strip()
        lane = self._lane_for_modes(
            template_mode=active_research_contract.get("template_mode"),
            research_mode=active_research_contract.get("research_mode"),
        )
        candidate_rows = self._candidate_rows_for_run(topic_slug, latest_run_id)
        knowledge_packets = build_knowledge_packets_from_candidates(
            topic_slug,
            candidate_rows,
            lane=lane,
            updated_at=now_iso(),
            updated_by=updated_by,
            kernel_root=self.kernel_root,
        )
        knowledge_packet_paths = [
            self._relativize(Path(item["path"]))
            for item in knowledge_packets
        ]
        all_decisions = get_all_decision_points(topic_slug, kernel_root=self.kernel_root)
        pending_decisions = list_pending_decision_points(topic_slug, kernel_root=self.kernel_root)
        decision_traces = get_decision_traces(topic_slug, kernel_root=self.kernel_root)
        latest_resolved_trace = decision_traces[-1] if decision_traces else None
        pending_decisions_payload = {
            "topic_slug": topic_slug,
            "pending_count": len(pending_decisions),
            "blocking_count": sum(1 for row in pending_decisions if row.get("blocking")),
            "unresolved_ids": [str(row.get("id") or "") for row in pending_decisions if str(row.get("id") or "").strip()],
            "latest_resolved_trace_ref": str((latest_resolved_trace or {}).get("id") or ""),
            "latest_resolved_summary": str((latest_resolved_trace or {}).get("decision_summary") or ""),
            "updated_at": now_iso(),
            "updated_by": updated_by,
        }
        pending_decisions_internal = {
            **pending_decisions_payload,
            "blocking_ids": [
                str(row.get("id") or "").strip()
                for row in pending_decisions
                if row.get("blocking") and str(row.get("id") or "").strip()
            ],
        }
        pending_decisions_written = write_pending_decisions_projection(
            topic_slug,
            pending_decisions_payload,
            kernel_root=self.kernel_root,
        )
        promotion_readiness_written = write_promotion_readiness_projection(
            topic_slug,
            promotion_readiness,
            kernel_root=self.kernel_root,
        )
        interaction_contract = self._derive_interaction_contract(
            topic_slug=topic_slug,
            human_request=human_request or str(interaction_state.get("human_request") or ""),
            idea_packet=idea_packet,
            operator_checkpoint=operator_checkpoint,
            pending_decisions=pending_decisions_internal,
            promotion_readiness=promotion_readiness,
        )
        exploration_paths = self._exploration_window_paths(topic_slug)
        exploration_question = (
            str(human_request or "").strip()
            or str(interaction_state.get("human_request") or "").strip()
            or str(active_research_contract.get("question") or "").strip()
        )
        exploration_window = {
            "status": "open" if interaction_contract["interaction_class"] == "free_explore" else "inactive",
            "current_question": exploration_question,
            "candidate_intuitions": self._dedupe_strings(
                [
                    str(idea_packet.get("novelty_target") or "").strip(),
                    str(idea_packet.get("initial_idea") or "").strip(),
                ]
            ),
            "local_blockers": self._dedupe_strings(list(open_gap_summary.get("blockers") or [])),
            "likely_next_target_layer": "L3-A" if interaction_contract["interaction_class"] == "free_explore" else str(topic_state.get("resume_stage") or "L3-A"),
            "window_open": interaction_contract["interaction_class"] == "free_explore",
            "closure_required": False,
            "summary": (
                "Bounded exploratory analysis is currently allowed before a harder validation, writeback, or checkpoint commitment is required."
                if interaction_contract["interaction_class"] == "free_explore"
                else "No active exploration window is currently open."
            ),
        }
        write_json(exploration_paths["json"], exploration_window)
        write_text(exploration_paths["note"], self._render_exploration_window_markdown(exploration_window))
        exploration_window = {
            **exploration_window,
            "path": self._relativize(exploration_paths["json"]),
            "note_path": self._relativize(exploration_paths["note"]),
        }
        task_type_lane_guidance_paths = self._task_type_lane_guidance_paths(topic_slug)
        task_type_lane_guidance = self._derive_task_type_lane_guidance(
            topic_slug=topic_slug,
            task_type=runtime_task_type,
            lane=lane,
        )
        write_json(task_type_lane_guidance_paths["json"], task_type_lane_guidance)
        write_text(
            task_type_lane_guidance_paths["note"],
            self._render_task_type_lane_guidance_markdown(task_type_lane_guidance),
        )
        task_type_lane_guidance = {
            **task_type_lane_guidance,
            "path": self._relativize(task_type_lane_guidance_paths["json"]),
            "note_path": self._relativize(task_type_lane_guidance_paths["note"]),
        }
        collaborator_routing_guidance_paths = self._collaborator_routing_guidance_paths(topic_slug)
        collaborator_routing_guidance = self._derive_collaborator_routing_guidance(
            topic_slug=topic_slug,
            task_type=runtime_task_type,
            lane=lane,
            task_type_lane_guidance=task_type_lane_guidance,
            collaborator_memory=collaborator_memory,
            override_surfaces=[
                {
                    "surface": "research_question_contract",
                    "path": self._relativize(Path(shell_surfaces["research_question_contract_note_path"])),
                    "role": "Adjust the active research question, scope, and declared route.",
                },
                {
                    "surface": "idea_packet",
                    "path": self._relativize(Path(shell_surfaces["idea_packet_note_path"])),
                    "role": "Adjust the initial idea framing, novelty target, and first validation route.",
                },
                {
                    "surface": "control_note",
                    "path": str((topic_state.get("pointers") or {}).get("control_note_path") or self._relativize(runtime_root / "control_note.md")),
                    "role": "Apply a bounded operator redirect without silently changing the route.",
                },
            ],
        )
        write_json(collaborator_routing_guidance_paths["json"], collaborator_routing_guidance)
        write_text(
            collaborator_routing_guidance_paths["note"],
            self._render_collaborator_routing_guidance_markdown(collaborator_routing_guidance),
        )
        collaborator_routing_guidance = {
            **collaborator_routing_guidance,
            "path": self._relativize(collaborator_routing_guidance_paths["json"]),
            "note_path": self._relativize(collaborator_routing_guidance_paths["note"]),
        }
        result_brief_payload = dict(shell_surfaces.get("result_brief") or {})
        if not result_brief_payload:
            topic_status_explainability = shell_surfaces.get("topic_state_explainability") or {}
            last_evidence_return = topic_status_explainability.get("last_evidence_return") or {}
            result_brief_payload = {
                "kind": "result_brief",
                "topic_slug": topic_slug,
                "interaction_class": interaction_contract["interaction_class"],
                "what_changed": str(topic_status_explainability.get("current_status_summary") or "").strip(),
                "evidence_summary": str(last_evidence_return.get("summary") or "").strip(),
                "scope_summary": str(active_research_contract.get("question") or "").strip(),
                "non_claims": self._dedupe_strings(list(idea_packet.get("non_goals") or [])),
            }
        result_brief_payload["interaction_class"] = interaction_contract["interaction_class"]
        result_brief_path = self._relativize(
            Path(shell_surfaces.get("result_brief_path") or self._result_brief_paths(topic_slug)["json"])
        )
        result_brief_note_path = self._relativize(
            Path(shell_surfaces.get("result_brief_note_path") or self._result_brief_paths(topic_slug)["note"])
        )
        result_brief = {
            "path": result_brief_path,
            "note_path": result_brief_note_path,
            "kind": result_brief_payload.get("kind") or "result_brief",
            "topic_slug": result_brief_payload.get("topic_slug") or topic_slug,
            "interaction_class": result_brief_payload.get("interaction_class") or interaction_contract["interaction_class"],
            "what_changed": result_brief_payload.get("what_changed") or "",
            "evidence_summary": result_brief_payload.get("evidence_summary") or "",
            "scope_summary": result_brief_payload.get("scope_summary") or "",
            "non_claims": self._dedupe_strings(list(result_brief_payload.get("non_claims") or [])),
        }
        l0_sources_payload = self._derive_l0_sources_projection(
            topic_slug=topic_slug,
            backend_bridges=backend_bridges,
        )
        l1_understanding_payload = self._derive_l1_understanding_projection(topic_slug=topic_slug)
        l4_validation_payload = self._derive_l4_validation_projection(
            topic_slug=topic_slug,
            topic_state=topic_state,
            validation_contract=validation_contract,
            topic_status_explainability=shell_surfaces.get("topic_state_explainability") or {},
        )
        l2_memory_payload = self._derive_l2_memory_projection(
            topic_slug=topic_slug,
            topic_state=topic_state,
            promotion_readiness=promotion_readiness,
            promotion_gate=promotion_gate,
            topic_skill_projection=topic_skill_projection,
            candidate_rows=candidate_rows,
        )
        l0_paths = self._layer_projection_paths(topic_slug, "L0")
        l1_paths = self._layer_projection_paths(topic_slug, "L1")
        l4_paths = self._layer_projection_paths(topic_slug, "L4")
        l2_paths = self._layer_projection_paths(topic_slug, "L2")
        l0_written = write_l0_sources_projection(
            topic_slug,
            l0_sources_payload,
            kernel_root=self.kernel_root,
        )
        l1_written = write_l1_understanding_projection(
            topic_slug,
            l1_understanding_payload,
            kernel_root=self.kernel_root,
        )
        l4_written = write_l4_validation_projection(
            topic_slug,
            l4_validation_payload,
            kernel_root=self.kernel_root,
        )
        l2_written = write_l2_memory_projection(
            topic_slug,
            l2_memory_payload,
            kernel_root=self.kernel_root,
        )
        write_text(l0_paths["note"], self._render_layer_projection_markdown(l0_sources_payload))
        write_text(l1_paths["note"], self._render_layer_projection_markdown(l1_understanding_payload))
        write_text(l4_paths["note"], self._render_layer_projection_markdown(l4_validation_payload))
        write_text(l2_paths["note"], self._render_layer_projection_markdown(l2_memory_payload))
        l0_sources = {
            **l0_written["l0_sources"],
            "path": self._relativize(Path(l0_written["path"])),
            "note_path": self._relativize(l0_paths["note"]),
        }
        l1_understanding = {
            **l1_written["l1_understanding"],
            "path": self._relativize(Path(l1_written["path"])),
            "note_path": self._relativize(l1_paths["note"]),
        }
        l4_validation = {
            **l4_written["l4_validation"],
            "path": self._relativize(Path(l4_written["path"])),
            "note_path": self._relativize(l4_paths["note"]),
        }
        l2_memory = {
            **l2_written["l2_memory"],
            "path": self._relativize(Path(l2_written["path"])),
            "note_path": self._relativize(l2_paths["note"]),
        }
        l3_subplanes_payload = self._derive_l3_subplanes(
            topic_slug=topic_slug,
            latest_run_id=latest_run_id,
            candidate_rows=candidate_rows,
            selected_pending_action=selected_pending_action,
            result_brief=result_brief,
            topic_status_explainability=shell_surfaces.get("topic_state_explainability") or {},
            promotion_readiness_path=self._relativize(Path(promotion_readiness_written["path"])),
            promotion_readiness=promotion_readiness,
        )
        l3_analysis_paths = self._l3_subplane_paths(topic_slug, "analysis")
        l3_result_integration_paths = self._l3_subplane_paths(topic_slug, "result_integration")
        l3_distillation_paths = self._l3_subplane_paths(topic_slug, "distillation")
        l3_analysis_written = write_l3_analysis_projection(
            topic_slug,
            l3_subplanes_payload["analysis"],
            kernel_root=self.kernel_root,
        )
        l3_result_integration_written = write_l3_result_integration_projection(
            topic_slug,
            l3_subplanes_payload["result_integration"],
            kernel_root=self.kernel_root,
        )
        l3_distillation_written = write_l3_distillation_projection(
            topic_slug,
            l3_subplanes_payload["distillation"],
            kernel_root=self.kernel_root,
        )
        write_text(
            l3_analysis_paths["note"],
            self._render_l3_subplane_markdown(l3_subplanes_payload["analysis"]),
        )
        write_text(
            l3_result_integration_paths["note"],
            self._render_l3_subplane_markdown(l3_subplanes_payload["result_integration"]),
        )
        write_text(
            l3_distillation_paths["note"],
            self._render_l3_subplane_markdown(l3_subplanes_payload["distillation"]),
        )
        l3_subplanes = {
            "analysis": {
                **l3_analysis_written["l3_analysis"],
                "path": self._relativize(Path(l3_analysis_written["path"])),
                "note_path": self._relativize(l3_analysis_paths["note"]),
            },
            "result_integration": {
                **l3_result_integration_written["l3_result_integration"],
                "path": self._relativize(Path(l3_result_integration_written["path"])),
                "note_path": self._relativize(l3_result_integration_paths["note"]),
            },
            "distillation": {
                **l3_distillation_written["l3_distillation"],
                "path": self._relativize(Path(l3_distillation_written["path"])),
                "note_path": self._relativize(l3_distillation_paths["note"]),
            },
        }
        topic_synopsis_payload = {
            "id": f"topic_synopsis:{topic_slug}",
            "topic_slug": topic_slug,
            "title": str(active_research_contract.get("title") or self._topic_display_title(topic_slug)),
            "question": str(active_research_contract.get("question") or ""),
            "lane": lane,
            "task_type": str(research_contract.get("task_type") or ""),
            "load_profile": resolved_load_profile,
            "status": str(active_research_contract.get("status") or "active"),
            "human_request": human_request or str(interaction_state.get("human_request") or ""),
            "assumptions": self._dedupe_strings(list(research_contract.get("assumptions") or [])),
            "next_action_summary": str((selected_pending_action or {}).get("summary") or "No bounded action is currently selected."),
            "open_gap_summary": str(open_gap_summary.get("summary") or ""),
            "pending_decision_count": len(pending_decisions),
            "knowledge_packet_paths": knowledge_packet_paths,
            "interaction_class": interaction_contract["interaction_class"],
            "stop_status": interaction_contract["stop_status"],
            "stop_reason": interaction_contract["stop_reason"],
            "primary_result_shape": interaction_contract["primary_result_shape"],
            "updated_at": now_iso(),
            "updated_by": updated_by,
        }
        topic_synopsis_written = write_topic_synopsis(
            topic_slug,
            topic_synopsis_payload,
            kernel_root=self.kernel_root,
        )
        promotion_trace_payload = {
            "id": f"promotion_trace:{slugify(topic_slug)}",
            "topic_slug": topic_slug,
            "trace_scope": "topic_latest",
            "status": str(promotion_readiness.get("status") or "not_ready"),
            "gate_status": str(promotion_readiness.get("gate_status") or ""),
            "human_gate_status": str(promotion_gate.get("status") or "not_requested"),
            "summary": str(promotion_readiness.get("summary") or ""),
            "candidate_refs": self._dedupe_strings(
                list(promotion_readiness.get("ready_candidate_ids") or [])
                + [str(row.get("candidate_id") or "") for row in candidate_rows if str(row.get("candidate_id") or "").strip()]
            ),
            "packet_refs": knowledge_packet_paths,
            "decision_trace_refs": [str(row.get("id") or "") for row in decision_traces[-5:] if str(row.get("id") or "").strip()],
            "audit_refs": self._dedupe_strings(
                [
                    self._relativize(Path(shell_surfaces["topic_completion_note_path"])),
                    self._relativize(Path(shell_surfaces["gap_map_path"])),
                    self._relativize(Path(shell_surfaces["validation_contract_note_path"])),
                ]
            ),
            "backend_target": {
                "backend_id": str(promotion_gate.get("backend_id") or ""),
                "target_backend_root": str(promotion_gate.get("target_backend_root") or ""),
                "canonical_layer": str(promotion_gate.get("canonical_layer") or "L2"),
            },
            "updated_at": now_iso(),
            "updated_by": updated_by,
        }
        promotion_trace_written = write_promotion_trace(
            topic_slug,
            promotion_trace_payload,
            kernel_root=self.kernel_root,
        )

        runtime_protocol_note = self._relativize(runtime_root / "runtime_protocol.generated.md")
        research_guardrails_note = self._relativize(self.kernel_root / "RESEARCH_EXECUTION_GUARDRAILS.md")
        formal_theory_upstream_note = self._relativize(
            self.kernel_root / "FORMAL_THEORY_UPSTREAM_REFERENCE_PROTOCOL.md"
        )
        section_formalization_note = self._relativize(
            self.kernel_root / "SECTION_FORMALIZATION_PROTOCOL.md"
        )
        formal_theory_active = (
            str(active_research_contract.get("research_mode") or "").strip() == "formal_derivation"
            or str(active_research_contract.get("template_mode") or "").strip() == "formal_theory"
        )
        must_read_now: list[dict[str, str]] = []
        if resolved_load_profile == "light":
            must_read_now.extend(
                [
                    {
                        "path": self._relativize(runtime_root / "topic_state.json"),
                        "reason": "Minimal runtime state for the current topic, including the active load profile.",
                    },
                    {
                        "path": self._relativize(Path(shell_surfaces["research_question_contract_note_path"])),
                        "reason": "Active research question, scope, and deliverables for ordinary topic work.",
                    },
                    {
                        "path": str((topic_state.get("pointers") or {}).get("control_note_path") or self._relativize(runtime_root / "control_note.md")),
                        "reason": "Current human steering note for this topic.",
                    },
                    {
                        "path": self._relativize(runtime_root / "operator_console.md"),
                        "reason": "Operator-facing topic state, pending actions, and unresolved checkpoints.",
                    },
                ]
            )
            if pending_decisions_payload.get("blocking_count", 0) > 0:
                must_read_now.insert(
                    1,
                    {
                        "path": self._relativize(Path(pending_decisions_written["path"])),
                        "reason": "Blocking pending decisions are active; resolve them before deeper execution.",
                    },
                )
            if strategy_memory.get("relevant_count") and strategy_memory.get("latest_path"):
                must_read_now.append(
                    {
                        "path": str(strategy_memory.get("latest_path")),
                        "reason": "Recent strategy memory overlaps with the current route. Consult it before trusting heuristic route selection.",
                    }
                )
            if collaborator_memory.get("status") == "available" and collaborator_memory.get("note_path"):
                must_read_now.append(
                    {
                        "path": str(collaborator_memory.get("note_path")),
                        "reason": "Collaborator-specific preferences are available here. Read them as steering context, not as canonical L2 truth.",
                    }
                )
            if str(collaborator_routing_guidance.get("alignment_status") or "") == "preference_mismatch":
                must_read_now.append(
                    {
                        "path": collaborator_routing_guidance["note_path"],
                        "reason": "Current route and collaborator lane preference disagree. Review the routing guidance before continuing.",
                    }
                )
            if str(topic_skill_projection.get("status") or "") == "available" and topic_skill_projection.get("note_path"):
                must_read_now.append(
                    {
                        "path": str(topic_skill_projection.get("note_path")),
                        "reason": self._topic_skill_projection_read_reason(topic_skill_projection),
                    }
                )
            if str(idea_packet.get("status") or "").strip() == "needs_clarification":
                must_read_now.insert(
                    1,
                    {
                        "path": str(idea_packet.get("note_path") or ""),
                        "reason": "Clarify the current idea packet before deeper execution.",
                    },
                )
            if str(operator_checkpoint.get("status") or "").strip() == "requested":
                must_read_now.insert(
                    1,
                    {
                        "path": str(operator_checkpoint.get("note_path") or ""),
                        "reason": "Resolve the active operator checkpoint before deeper execution.",
                    },
                )
        else:
            if str(operator_checkpoint.get("status") or "").strip() == "requested":
                must_read_now.append(
                    {
                        "path": str(operator_checkpoint.get("note_path") or ""),
                        "reason": "Active operator checkpoint. Resolve this human-decision surface before deeper execution.",
                    }
                )
            if str(idea_packet.get("status") or "").strip() == "needs_clarification":
                must_read_now.append(
                    {
                        "path": str(idea_packet.get("note_path") or ""),
                        "reason": "Clarify the idea packet before substantive execution. This is the active intent gate for the topic.",
                    }
                )
            if pending_decisions_payload.get("blocking_count", 0) > 0:
                must_read_now.append(
                    {
                        "path": self._relativize(Path(pending_decisions_written["path"])),
                        "reason": "Blocking pending decisions are active; resolve them before deeper execution.",
                    }
                )
            must_read_now.extend(
                [
                    {
                        "path": self._relativize(Path(shell_surfaces["research_question_contract_note_path"])),
                        "reason": "Active research question, scope, deliverables, and anti-proxy rules for this topic.",
                    },
                    {
                        "path": self._relativize(Path(shell_surfaces["topic_dashboard_path"])),
                        "reason": "Operator-facing topic snapshot that condenses the active question, next action, readiness, and gaps.",
                    },
                    {
                        "path": self._relativize(Path(shell_surfaces["topic_completion_note_path"])),
                        "reason": "Topic-completion gate over regression support, follow-up return debt, and blocker honesty.",
                    },
                    {
                        "path": self._relativize(Path(shell_surfaces["validation_contract_note_path"])),
                        "reason": "Current validation route, required checks, and failure modes for this topic.",
                    },
                ]
            )
            innovation_direction_path = str((topic_state.get("pointers") or {}).get("innovation_direction_path") or "")
            if innovation_direction_path:
                must_read_now.append(
                    {
                        "path": innovation_direction_path,
                        "reason": "Current human innovation target, steering decision, and novelty boundary for this topic.",
                    }
                )
            if strategy_memory.get("relevant_count") and strategy_memory.get("latest_path"):
                must_read_now.append(
                    {
                        "path": str(strategy_memory.get("latest_path")),
                        "reason": "Recent strategy memory overlaps with the current route. Consult it before trusting heuristic route selection.",
                    }
                )
            if collaborator_memory.get("status") == "available" and collaborator_memory.get("note_path"):
                must_read_now.append(
                    {
                        "path": str(collaborator_memory.get("note_path")),
                        "reason": "Collaborator-specific preferences are available here. Read them as steering context, not as canonical L2 truth.",
                    }
                )
            if str(topic_skill_projection.get("status") or "") == "available" and topic_skill_projection.get("note_path"):
                must_read_now.append(
                    {
                        "path": str(topic_skill_projection.get("note_path")),
                        "reason": self._topic_skill_projection_read_reason(topic_skill_projection),
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

        if exploration_window["window_open"]:
            must_read_now.insert(
                1,
                {
                    "path": exploration_window["note_path"],
                    "reason": "Bounded exploration is currently open. Use this carrier to preserve tentative route ideas without treating them as durable closure.",
                },
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
        innovation_decisions_path = str((topic_state.get("pointers") or {}).get("innovation_decisions_path") or "")
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
        if innovation_decisions_path:
            may_defer_until_trigger.append(
                {
                    "path": innovation_decisions_path,
                    "trigger": "decision_override_present",
                    "reason": "Open the steering decision log when you need the durable history behind a control-note redirect.",
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
        if strategy_memory.get("row_count") and strategy_memory.get("latest_path") and not strategy_memory.get("relevant_count"):
            may_defer_until_trigger.append(
                {
                    "path": str(strategy_memory.get("latest_path")),
                    "trigger": "verification_route_selection",
                    "reason": "Consult prior strategy memory when a later route choice starts resembling an earlier lane or guardrail pattern.",
                }
            )
        if str(topic_skill_projection.get("status") or "") != "available" and topic_skill_projection.get("note_path"):
            may_defer_until_trigger.append(
                {
                    "path": str(topic_skill_projection.get("note_path")),
                    "trigger": "verification_route_selection",
                    "reason": self._topic_skill_projection_deferred_reason(topic_skill_projection),
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
        if str(operator_checkpoint.get("status") or "").strip() == "requested":
            immediate_allowed_work = [
                f"Resolve `{operator_checkpoint.get('note_path') or '(missing)'}` before deeper execution.",
                "Limit the next step to answering the active operator checkpoint and syncing the affected durable artifacts.",
            ]
        if str(idea_packet.get("status") or "").strip() == "needs_clarification":
            immediate_allowed_work = [
                f"Clarify `{idea_packet.get('note_path') or '(missing)'}` and then synchronize the research and validation contracts.",
                "Limit the next step to intent clarification, scope tightening, and first-lane selection.",
            ]
        if pending_decisions_payload.get("blocking_count", 0) > 0:
            immediate_allowed_work = [
                f"Resolve blocking decisions in `{pending_decisions_written['path']}` before deeper execution.",
                "Limit the next step to closing the blocking decision points and syncing their durable traces.",
            ]

        immediate_blocked_work = [
            "Do not promote or auto-promote material into Layer 2 unless the promotion trigger fires and the gate artifacts allow it.",
            "Do not bypass conformance, declared control notes, or decision contracts with heuristic queue guesses.",
            "Do not treat consultation as promotion or claim heavy execution happened without the corresponding returned result artifacts.",
            "Do not substitute polished prose, memory agreement, or missing execution evidence for the declared acceptance checks.",
        ]
        if str(idea_packet.get("status") or "").strip() == "needs_clarification":
            immediate_blocked_work.append(
                "Do not treat literature intake, benchmark execution, derivation work, or queue advancement as started until the idea packet is clarified."
            )
        if str(operator_checkpoint.get("status") or "").strip() == "requested":
            immediate_blocked_work.append(
                "Do not continue deeper research execution until the active operator checkpoint is answered or cancelled."
            )
        if pending_decisions_payload.get("blocking_count", 0) > 0:
            immediate_blocked_work.append(
                "Do not continue bounded execution until blocking pending decisions are resolved."
            )

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
            {
                "trigger": "formal_theory_upstream_scan",
                "active": formal_theory_active,
                "condition": "Formal-theory topics should periodically consult the living Lean discussion/code upstreams before claiming novelty, choosing Lean target shapes, or exporting bridge packets.",
                "required_reads": [formal_theory_upstream_note],
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
            {
                "slice": "formal_theory_living_upstreams",
                "trigger": "formal_theory_upstream_scan",
                "paths": [formal_theory_upstream_note],
            },
            {
                "slice": "formal_theory_section_packets",
                "trigger": "formal_theory_upstream_scan",
                "paths": [section_formalization_note],
            },
        ]

        active_hard_constraints = [
            "Do not let progressive disclosure hide layer semantics, consultation obligations, trust gates, promotion gates, or conformance failures.",
            "Do not let the active research contract drift silently in scope, observables, deliverables, or acceptance tests.",
            "Do not treat heuristic queue rows as higher priority than declared control notes or decision contracts.",
            "Do not perform Layer 2 or Layer 2_auto writeback unless the corresponding gate artifacts say it is allowed.",
            "Do not route L4 outputs directly into L2. They must return through L3-R and then L3-D before any writeback decision.",
            "Do not treat proxy-success signals as validation when the declared execution or proof evidence is still missing.",
            "If definitions, cited derivations, or prior-work comparisons are missing, return to L0 and persist the recovery artifacts before continuing.",
            "When a named trigger becomes active, read its mandatory deeper surfaces before continuing execution.",
            "Do not collapse one compiled section packet into a whole-topic Lean completion claim.",
            "Do not treat live Lean community discussion as theorem truth, and do not cite physlib without recording the consulted commit, path, or declaration surface.",
        ]
        if str(idea_packet.get("status") or "").strip() == "needs_clarification":
            active_hard_constraints.append(
                f"Do not continue substantive execution until `{idea_packet.get('note_path') or '(missing)'}` resolves the missing intent fields."
            )
        if str(operator_checkpoint.get("status") or "").strip() == "requested":
            active_hard_constraints.append(
                f"Do not continue deeper execution until `{operator_checkpoint.get('note_path') or '(missing)'}` is answered or cancelled."
            )
        if pending_decisions_payload.get("blocking_count", 0) > 0:
            active_hard_constraints.append(
                f"Do not continue deeper execution until blocking decisions in `{pending_decisions_written['path']}` are resolved."
            )

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
                    "surface": "exploration_window",
                    "path": exploration_window["note_path"],
                    "role": "Review or refine the current bounded exploration carrier before harder validation, writeback, or checkpoint closure.",
                },
                {
                    "surface": "operator_checkpoint",
                    "path": self._relativize(Path(shell_surfaces["operator_checkpoint_note_path"])),
                    "role": "Answer the current human-checkpoint question or mark how the checkpoint was resolved.",
                },
                {
                    "surface": "idea_packet",
                    "path": self._relativize(Path(shell_surfaces["idea_packet_note_path"])),
                    "role": "Edit the initial idea, novelty target, first validation route, and evidence bar before deeper execution.",
                },
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
                    "surface": "l0_sources",
                    "path": self._relativize(l0_paths["note"]),
                    "role": "Review the current registered source basis before deeper reading or source recovery.",
                },
                {
                    "surface": "l1_understanding",
                    "path": self._relativize(l1_paths["note"]),
                    "role": "Review the current provisional-understanding packet before topic analysis or validation.",
                },
                {
                    "surface": "l4_validation",
                    "path": self._relativize(l4_paths["note"]),
                    "role": "Review the current validation return surface before interpreting or rerouting it.",
                },
                {
                    "surface": "l2_memory",
                    "path": self._relativize(l2_paths["note"]),
                    "role": "Review consultation, staging, and writeback state before treating L2 as active memory.",
                },
                {
                    "surface": "l3_analysis",
                    "path": self._relativize(l3_analysis_paths["note"]),
                    "role": "Review the current topic-analysis packet, active candidates, and legal next transitions.",
                },
                {
                    "surface": "l3_result_integration",
                    "path": self._relativize(l3_result_integration_paths["note"]),
                    "role": "Review how the latest L4 return was interpreted before rerouting or writeback.",
                },
                {
                    "surface": "l3_distillation",
                    "path": self._relativize(l3_distillation_paths["note"]),
                    "role": "Review staging/writeback readiness and the forbidden direct L4-to-L2 path.",
                },
                {
                    "surface": "topic_skill_projection",
                    "path": str(
                        topic_skill_projection.get("note_path")
                        or self._relativize(
                            Path(
                                shell_surfaces.get("topic_skill_projection_note_path")
                                or self._topic_skill_projection_paths(topic_slug)["note"]
                            )
                        )
                    ),
                    "role": "Review the reusable execution projection derived from this mature topic.",
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
            "load_profile": resolved_load_profile,
            "l0_sources": l0_sources,
            "l1_understanding": l1_understanding,
            "l4_validation": l4_validation,
            "l2_memory": l2_memory,
            "topic_synopsis": {
                **topic_synopsis_written["topic_synopsis"],
                "path": self._relativize(Path(topic_synopsis_written["path"])),
            },
            "l3_subplanes": l3_subplanes,
            "interaction_contract": interaction_contract,
            "pending_decisions": {
                **pending_decisions_written["pending_decisions"],
                "path": self._relativize(Path(pending_decisions_written["path"])),
            },
            "result_brief": result_brief,
            "active_research_contract": active_research_contract,
            "idea_packet": idea_packet,
            "operator_checkpoint": operator_checkpoint,
            "promotion_readiness": promotion_readiness,
            "open_gap_summary": open_gap_summary,
            "strategy_memory": strategy_memory,
            "collaborator_memory": collaborator_memory,
            "exploration_window": exploration_window,
            "task_type_lane_guidance": task_type_lane_guidance,
            "collaborator_routing_guidance": collaborator_routing_guidance,
            "topic_skill_projection": topic_skill_projection,
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
                "open_next": must_read_now[0]["path"] if must_read_now else runtime_protocol_note,
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
                    "source": "strategy_memory",
                    "rule": "When a route resembles a previously recorded helpful or harmful pattern, consult strategy memory before trusting heuristic route selection.",
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
            *self._resolve_runtime_python_command(),
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
            *self._resolve_runtime_python_command(),
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
        command = [*self._resolve_runtime_python_command(), str(handler_path)]
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
                child_row = dict(existing_child)
                child_row.update(
                    {
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
                )
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
        expected_return_route = str(policy.get("expected_return_route") or "L0->L1->L3-A->L4->L3-R->L3-D->L2")
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

    def _opencode_mcp_setup_markdown(self, *, scope: str, target_root: str | None) -> str:
        if target_root:
            config_path = self._agent_hidden_root(
                target_root=target_root,
                scope=scope,
                hidden_dir=".opencode",
                user_root=Path.home() / ".config" / "opencode",
                project_root=self.repo_root / ".opencode",
            ) / "AITP_MCP_CONFIG.json"
        elif scope == "project":
            config_path = self.repo_root / ".opencode" / "opencode.json"
        else:
            config_path = Path.home() / ".config" / "opencode" / "opencode.json"

        return "\n".join(
            [
                "# OpenCode MCP setup",
                "",
                "OpenCode should expose an `aitp` local MCP server entry.",
                "",
                "Expected config path:",
                "",
                f"- `{config_path}`",
                "",
                "If config mutation is disabled, copy the generated MCP block into your active OpenCode config manually.",
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
        candidates = [home / ".agents" / "skills" / "aitp-runtime"]
        if (home / ".codex").exists() or (home / ".codex" / "config.toml").exists():
            candidates.append(home / ".codex" / "skills" / "aitp-runtime")
        if (home / ".codex-home").exists():
            candidates.append(home / ".codex-home" / "skills" / "aitp-runtime")
        candidates.append(home / ".codex" / "skills" / "aitp-runtime")

        deduped: list[Path] = []
        seen: set[str] = set()
        for candidate in candidates:
            key = str(candidate)
            if key not in seen:
                seen.add(key)
                deduped.append(candidate)
        return deduped

    def _openclaw_skill_target(self, *, scope: str, target_root: str | None) -> Path:
        if target_root:
            target_path = Path(target_root)
            if target_path.name == "aitp-runtime" or target_path.parent.name == "skills":
                return target_path
            return target_path / "skills" / "aitp-runtime"
        if scope == "project":
            return self.repo_root / "skills" / "aitp-runtime"
        return Path.home() / ".openclaw" / "skills" / "aitp-runtime"

    def _agent_hidden_root(
        self,
        *,
        target_root: str | None,
        scope: str,
        hidden_dir: str,
        user_root: Path,
        project_root: Path,
    ) -> Path:
        if target_root:
            target_path = Path(target_root)
            if target_path.name == hidden_dir:
                return target_path
            return target_path / hidden_dir
        if scope == "project":
            return project_root
        return user_root

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
            base = self._agent_hidden_root(
                target_root=target_root,
                scope=scope,
                hidden_dir=".opencode",
                user_root=Path.home() / ".config" / "opencode",
                project_root=self.repo_root / ".opencode",
            )
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

    def _opencode_plugin_template(self) -> str:
        return r"""/**
 * AITP plugin for OpenCode
 *
 * Injects the using-aitp bootstrap and registers the local AITP skills path.
 */

import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const extractAndStripFrontmatter = (content) => {
  const match = content.match(/^---\\n([\\s\\S]*?)\\n---\\n([\\s\\S]*)$/);
  if (!match) return { frontmatter: {}, content };

  const frontmatterStr = match[1];
  const body = match[2];
  const frontmatter = {};

  for (const line of frontmatterStr.split('\\n')) {
    const colonIdx = line.indexOf(':');
    if (colonIdx > 0) {
      const key = line.slice(0, colonIdx).trim();
      const value = line.slice(colonIdx + 1).trim().replace(/^[\"']|[\"']$/g, '');
      frontmatter[key] = value;
    }
  }

  return { frontmatter, content: body };
};

const resolveSkillsDir = () => {
  const candidates = [
    path.resolve(__dirname, '../../skills'),
    path.resolve(__dirname, '../skills'),
  ];

  for (const candidate of candidates) {
    if (fs.existsSync(path.join(candidate, 'using-aitp', 'SKILL.md'))) {
      return candidate;
    }
  }
  return candidates[0];
};

const getBootstrapContent = () => {
  const skillsDir = resolveSkillsDir();
  const skillPath = path.join(skillsDir, 'using-aitp', 'SKILL.md');
  if (!fs.existsSync(skillPath)) return null;

  const fullContent = fs.readFileSync(skillPath, 'utf8');
  const { content } = extractAndStripFrontmatter(fullContent);
  const toolMapping = `**Tool Mapping for OpenCode:**\\n- \`TodoWrite\` -> \`todowrite\`\\n- \`Skill\` tool -> OpenCode's native \`skill\` tool\\n- File operations and shell calls -> native OpenCode tools\\n\\n**AITP skills location:**\\n\`${skillsDir}\``;

  return `<EXTREMELY_IMPORTANT>\\nYou are in an AITP-enabled OpenCode session.\\n\\n**IMPORTANT: The using-aitp skill content is included below and is already loaded. Do not load using-aitp again.**\\n\\n${content}\\n\\n${toolMapping}\\n</EXTREMELY_IMPORTANT>`;
};

export const AITPPlugin = async () => {
  const skillsDir = resolveSkillsDir();

  return {
    config: async (config) => {
      config.skills = config.skills || {};
      config.skills.paths = config.skills.paths || [];
      if (!config.skills.paths.includes(skillsDir)) {
        config.skills.paths.push(skillsDir);
      }
    },

    'experimental.chat.system.transform': async (_input, output) => {
      const bootstrap = getBootstrapContent();
      if (bootstrap) {
        (output.system ||= []).push(bootstrap);
      }
    }
  };
};

export default AITPPlugin;
"""

    def _install_opencode_plugin(
        self,
        *,
        scope: str,
        target_root: str | None,
        force: bool,
    ) -> list[dict[str, str]]:
        base = self._agent_hidden_root(
            target_root=target_root,
            scope=scope,
            hidden_dir=".opencode",
            user_root=Path.home() / ".config" / "opencode",
            project_root=self.repo_root / ".opencode",
        )
        plugin_root = base / "plugins"
        plugin_root.mkdir(parents=True, exist_ok=True)
        plugin_path = plugin_root / "aitp.js"
        if plugin_path.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite {plugin_path}")
        write_text(
            plugin_path,
            self._canonical_repo_asset_text(
                ".opencode/plugins/aitp.js",
                fallback_text=self._opencode_plugin_template(),
            ),
        )
        return [{"agent": "opencode", "path": str(plugin_path), "kind": "plugin"}]

    def _claude_session_start_hook_template(self) -> str:
        return """#!/usr/bin/env bash
# SessionStart hook for AITP

set -euo pipefail

SCRIPT_DIR=\"$(cd \"$(dirname \"$0\")\" && pwd)\"
PLUGIN_ROOT=\"$(cd \"${SCRIPT_DIR}/..\" && pwd)\"
SKILL_PATH=\"${PLUGIN_ROOT}/skills/using-aitp/SKILL.md\"

if [ -f \"$SKILL_PATH\" ]; then
    using_aitp_content=$(cat \"$SKILL_PATH\")
else
    using_aitp_content=\"Error reading using-aitp skill from ${SKILL_PATH}\"
fi

escape_for_json() {
    local s=\"$1\"
    s=\"${s//\\\\/\\\\\\\\}\"
    s=\"${s//\\\"/\\\\\\\"}\"
    s=\"${s//$'\\n'/\\\\n}\"
    s=\"${s//$'\\r'/\\\\r}\"
    s=\"${s//$'\\t'/\\\\t}\"
    printf '%s' \"$s\"
}

using_aitp_escaped=$(escape_for_json \"$using_aitp_content\")
session_context=\"<EXTREMELY_IMPORTANT>\\nYou are in an AITP-enabled Claude Code session.\\n\\n**Below is the full content of the using-aitp skill. It is already loaded. Do not load using-aitp again.**\\n\\n${using_aitp_escaped}\\n</EXTREMELY_IMPORTANT>\"

if [ -n \"${CLAUDE_PLUGIN_ROOT:-}\" ]; then
  printf '{\\n  \"hookSpecificOutput\": {\\n    \"hookEventName\": \"SessionStart\",\\n    \"additionalContext\": \"%s\"\\n  }\\n}\\n' \"$session_context\"
else
  printf '{\\n  \"additional_context\": \"%s\"\\n}\\n' \"$session_context\"
fi

exit 0
"""

    def _claude_hook_wrapper_template(self) -> str:
        return """: << 'CMDBLOCK'
@echo off
if \"%~1\"==\"\" (
    echo run-hook.cmd: missing script name >&2
    exit /b 1
)

set \"HOOK_DIR=%~dp0\"

if exist \"C:\\Program Files\\Git\\bin\\bash.exe\" (
    \"C:\\Program Files\\Git\\bin\\bash.exe\" \"%HOOK_DIR%%~1\" %2 %3 %4 %5 %6 %7 %8 %9
    exit /b %ERRORLEVEL%
)
if exist \"C:\\Program Files (x86)\\Git\\bin\\bash.exe\" (
    \"C:\\Program Files (x86)\\Git\\bin\\bash.exe\" \"%HOOK_DIR%%~1\" %2 %3 %4 %5 %6 %7 %8 %9
    exit /b %ERRORLEVEL%
)

where bash >nul 2>nul
if %ERRORLEVEL% equ 0 (
    bash \"%HOOK_DIR%%~1\" %2 %3 %4 %5 %6 %7 %8 %9
    exit /b %ERRORLEVEL%
)

exit /b 0
CMDBLOCK

SCRIPT_DIR=\"$(cd \"$(dirname \"$0\")\" && pwd)\"
SCRIPT_NAME=\"$1\"
shift
exec bash \"${SCRIPT_DIR}/${SCRIPT_NAME}\" \"$@\"
"""

    def _claude_hooks_manifest_template(self) -> str:
        payload = {
            "hooks": {
                "SessionStart": [
                    {
                        "matcher": "startup|clear|compact",
                        "hooks": [
                            {
                                "type": "command",
                                "command": '"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd" session-start',
                                "async": False,
                            }
                        ],
                    }
                ]
            }
        }
        return json.dumps(payload, ensure_ascii=True, indent=2) + "\n"

    def _install_claude_session_start_hook(
        self,
        *,
        scope: str,
        target_root: str | None,
        force: bool,
    ) -> list[dict[str, str]]:
        base = self._agent_hidden_root(
            target_root=target_root,
            scope=scope,
            hidden_dir=".claude",
            user_root=Path.home() / ".claude",
            project_root=self.repo_root / ".claude",
        )
        hook_root = base / "hooks"
        hook_root.mkdir(parents=True, exist_ok=True)

        session_start_path = hook_root / "session-start"
        if session_start_path.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite {session_start_path}")
        write_executable_text(
            session_start_path,
            self._canonical_repo_asset_text(
                "hooks/session-start",
                fallback_text=self._claude_session_start_hook_template(),
            ),
        )

        run_hook_path = hook_root / "run-hook.cmd"
        if run_hook_path.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite {run_hook_path}")
        write_text(
            run_hook_path,
            self._canonical_repo_asset_text(
                "hooks/run-hook.cmd",
                fallback_text=self._claude_hook_wrapper_template(),
            ),
        )

        hooks_json_path = hook_root / "hooks.json"
        if hooks_json_path.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite {hooks_json_path}")
        write_text(
            hooks_json_path,
            self._canonical_repo_asset_text(
                "hooks/hooks.json",
                fallback_text=self._claude_hooks_manifest_template(),
            ),
        )

        settings_path = base / "settings.json"
        if settings_path.exists():
            payload = json.loads(settings_path.read_text(encoding="utf-8"))
        else:
            payload = {}

        command_entry = f'"{run_hook_path}" session-start'
        desired_block = {
            "matcher": "startup|clear|compact",
            "hooks": [{"type": "command", "command": command_entry, "async": False}],
        }
        hooks_payload = payload.setdefault("hooks", {})
        session_blocks = hooks_payload.setdefault("SessionStart", [])
        filtered_blocks = []
        for block in session_blocks:
            block_hooks = block.get("hooks") or []
            commands = {
                str(entry.get("command") or "")
                for entry in block_hooks
                if isinstance(entry, dict)
            }
            if command_entry in commands:
                continue
            filtered_blocks.append(block)
        filtered_blocks.append(desired_block)
        hooks_payload["SessionStart"] = filtered_blocks
        self._write_json_file(settings_path, payload)

        return [
            {"agent": "claude-code", "path": str(session_start_path), "kind": "hook"},
            {"agent": "claude-code", "path": str(run_hook_path), "kind": "hook-wrapper"},
            {"agent": "claude-code", "path": str(hooks_json_path), "kind": "hook-manifest"},
            {"agent": "claude-code", "path": str(settings_path), "kind": "hook-config"},
        ]

    def get_runtime_state(self, topic_slug: str) -> dict[str, Any]:
        topic_state = read_json(self._runtime_root(topic_slug) / "topic_state.json")
        if topic_state is None:
            raise FileNotFoundError(f"Runtime state missing for topic {topic_slug}")
        return topic_state

    def get_current_topic_memory(self) -> dict[str, Any]:
        payload = read_json(self._current_topic_memory_paths()["json"])
        if payload is None:
            raise FileNotFoundError("Current topic memory has not been materialized yet.")
        return payload

    def get_collaborator_memory(self) -> dict[str, Any]:
        payload = read_json(self._collaborator_memory_paths()["json"])
        if payload is None:
            raise FileNotFoundError("Collaborator memory has not been materialized yet.")
        return payload

    def _render_collaborator_memory_note(self, payload: dict[str, Any]) -> str:
        lines = [
            "# Collaborator memory",
            "",
            f"- Updated at: `{payload.get('updated_at') or '(missing)'}`",
            f"- Updated by: `{payload.get('updated_by') or '(missing)'}`",
            "",
            "This file stores collaborator-specific preferences and long-horizon concerns.",
            "It is separate from canonical scientific memory and must not be treated as Layer 2 truth.",
            "",
            "## Preferences",
            "",
        ]
        for item in payload.get("preferences") or ["(none)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Preferred lanes", ""])
        for item in payload.get("preferred_lanes") or ["(none)"]:
            lines.append(f"- `{item}`")
        lines.extend(["", "## Avoided patterns", ""])
        for item in payload.get("avoided_patterns") or ["(none)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Long-horizon concerns", ""])
        for item in payload.get("long_horizon_concerns") or ["(none)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Collaboration style", ""])
        for item in payload.get("collaboration_style") or ["(none)"]:
            lines.append(f"- {item}")
        lines.append("")
        return "\n".join(lines)

    def record_collaborator_memory(
        self,
        *,
        preferences: list[str] | None = None,
        preferred_lanes: list[str] | None = None,
        avoided_patterns: list[str] | None = None,
        long_horizon_concerns: list[str] | None = None,
        collaboration_style: list[str] | None = None,
        updated_by: str = "aitp-cli",
    ) -> dict[str, Any]:
        existing = read_json(self._collaborator_memory_paths()["json"]) or {}
        payload = {
            "memory_kind": "collaborator_memory",
            "updated_at": now_iso(),
            "updated_by": updated_by,
            "preferences": self._dedupe_strings([*(existing.get("preferences") or []), *(preferences or [])]),
            "preferred_lanes": self._dedupe_strings([*(existing.get("preferred_lanes") or []), *(preferred_lanes or [])]),
            "avoided_patterns": self._dedupe_strings([*(existing.get("avoided_patterns") or []), *(avoided_patterns or [])]),
            "long_horizon_concerns": self._dedupe_strings(
                [*(existing.get("long_horizon_concerns") or []), *(long_horizon_concerns or [])]
            ),
            "collaboration_style": self._dedupe_strings([*(existing.get("collaboration_style") or []), *(collaboration_style or [])]),
        }
        paths = self._collaborator_memory_paths()
        write_json(paths["json"], payload)
        write_text(paths["note"], self._render_collaborator_memory_note(payload))
        return {
            **payload,
            "collaborator_memory_path": str(paths["json"]),
            "collaborator_memory_note_path": str(paths["note"]),
        }

    def _render_current_topic_note(self, payload: dict[str, Any]) -> str:
        return "\n".join(
            [
                "# Current topic memory",
                "",
                f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
                f"- Updated at: `{payload.get('updated_at') or '(missing)'}`",
                f"- Updated by: `{payload.get('updated_by') or '(missing)'}`",
                f"- Source: `{payload.get('source') or '(missing)'}`",
                f"- Resume stage: `{payload.get('resume_stage') or '(missing)'}`",
                f"- Latest run id: `{payload.get('run_id') or '(none)'}`",
                f"- Runtime root: `{payload.get('runtime_root') or '(missing)'}`",
                f"- Human request: {payload.get('human_request') or '(missing)'}",
                f"- Summary: {payload.get('summary') or '(missing)'}",
                "",
                "This is the workspace-facing memory used to resolve natural-language requests such as `继续这个 topic` before falling back to the latest topic index.",
                "",
            ]
        )

    def remember_current_topic(
        self,
        *,
        topic_slug: str,
        updated_by: str,
        source: str,
        human_request: str | None = None,
    ) -> dict[str, Any]:
        topic_state = self.get_runtime_state(topic_slug)
        payload = {
            "topic_slug": topic_slug,
            "updated_at": now_iso(),
            "updated_by": updated_by,
            "source": source,
            "run_id": str(topic_state.get("latest_run_id") or ""),
            "resume_stage": str(topic_state.get("resume_stage") or ""),
            "runtime_root": str(self._runtime_root(topic_slug)),
            "human_request": str(human_request or "").strip(),
            "summary": str(
                ((topic_state.get("status_explainability") or {}).get("current_status_summary"))
                or topic_state.get("summary")
                or topic_state.get("resume_reason")
                or ""
            ),
        }
        paths = self._current_topic_memory_paths()
        write_json(paths["json"], payload)
        write_text(paths["note"], self._render_current_topic_note(payload))
        return {
            **payload,
            "current_topic_path": str(paths["json"]),
            "current_topic_note_path": str(paths["note"]),
        }

    def _render_session_start_note(self, payload: dict[str, Any]) -> str:
        routing = payload.get("routing") or {}
        memory_resolution = payload.get("memory_resolution") or {}
        selected_action = payload.get("selected_action") or {}
        must_read_now = payload.get("must_read_now") or []
        linear_flow = payload.get("linear_flow") or []
        hard_stops = payload.get("hard_stops") or []

        memory_summary = str(memory_resolution.get("summary") or "(missing)")
        lines = [
            "# Session start contract",
            "",
            "This file is the durable session-start translation of the latest natural-language request.",
            "Read it before `runtime_protocol.generated.md`, then follow the linear startup order below.",
            "",
            f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
            f"- Updated at: `{payload.get('updated_at') or '(missing)'}`",
            f"- Updated by: `{payload.get('updated_by') or '(missing)'}`",
            f"- Original request: {payload.get('task') or '(missing)'}",
            f"- Route: `{routing.get('route') or '(missing)'}`",
            f"- Routing reason: {routing.get('reason') or '(missing)'}",
            f"- Memory resolution: {memory_summary}",
            f"- Canonical entry: `{payload.get('canonical_entry') or '(missing)'}`",
            "",
            "## Read Next",
            "",
        ]
        for index, item in enumerate(must_read_now, start=1):
            lines.append(
                f"{index}. `{item.get('path') or '(missing)'}`"
                + (
                    f" - {item.get('reason')}"
                    if str(item.get("reason") or "").strip()
                    else ""
                )
            )
        if not must_read_now:
            lines.append("1. `(missing)`")
        lines.extend(["", "## Linear Flow", ""])
        for index, item in enumerate(linear_flow, start=1):
            lines.append(
                f"{index}. {item.get('step') or '(missing)'}"
                + (
                    f" Result: {item.get('result')}."
                    if str(item.get("result") or "").strip()
                    else ""
                )
            )
        if not linear_flow:
            lines.append("1. Read the runtime protocol and continue with the bounded action.")
        lines.extend(["", "## Selected Action", ""])
        lines.append(f"- Action id: `{selected_action.get('action_id') or '(none)'}`")
        lines.append(f"- Action type: `{selected_action.get('action_type') or '(none)'}`")
        lines.append(f"- Summary: {selected_action.get('summary') or '(none)'}")
        lines.extend(["", "## Hard Stops", ""])
        for item in hard_stops:
            lines.append(f"- {item}")
        if not hard_stops:
            lines.append("- Do not continue if required runtime artifacts are missing.")
        lines.append("")
        return "\n".join(lines)

    def _materialize_session_start_contract(
        self,
        *,
        task: str,
        routing: dict[str, Any],
        loop_payload: dict[str, Any],
        updated_by: str,
        pre_route_current_topic: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        topic_slug = str(loop_payload.get("topic_slug") or routing.get("topic_slug") or "").strip()
        if not topic_slug:
            raise ValueError("Session-start contract requires a resolved topic slug.")

        runtime_root = self._ensure_runtime_root(topic_slug)
        session_paths = self._session_start_paths(topic_slug)
        runtime_protocol_paths = loop_payload.get("runtime_protocol") or {}
        runtime_protocol_path = self._normalize_artifact_path(runtime_protocol_paths.get("runtime_protocol_path"))
        runtime_protocol_note_path = self._normalize_artifact_path(runtime_protocol_paths.get("runtime_protocol_note_path"))
        runtime_bundle = read_json(Path(runtime_protocol_paths.get("runtime_protocol_path") or "")) or {}
        loop_state = loop_payload.get("loop_state") or {}
        steering_artifacts = loop_payload.get("steering_artifacts") or {}
        bootstrap = loop_payload.get("bootstrap") or {}
        pointers = (bootstrap.get("topic_state") or {}).get("pointers") or {}

        pre_route_payload = pre_route_current_topic or {}
        pre_route_topic_slug = str(pre_route_payload.get("topic_slug") or "").strip()
        pre_route_current_valid = bool(
            pre_route_topic_slug and (self._runtime_root(pre_route_topic_slug) / "topic_state.json").exists()
        )
        route_name = str(routing.get("route") or "")
        current_topic_first_route = route_name in {
            "explicit_current_topic",
            "request_current_topic_reference",
            "implicit_current_topic",
        }
        latest_only_route = route_name == "explicit_latest_topic"
        explicit_route = route_name in {
            "explicit_topic_slug",
            "explicit_topic_title",
            "request_named_existing_topic",
            "request_new_topic",
        }
        used_current_topic_memory = (
            current_topic_first_route and pre_route_current_valid and pre_route_topic_slug == topic_slug
        )
        used_latest_topic_fallback = (current_topic_first_route and not used_current_topic_memory) or latest_only_route

        if used_current_topic_memory:
            memory_summary = f"Resolved through durable current-topic memory: `{topic_slug}`."
        elif used_latest_topic_fallback:
            memory_summary = (
                f"Current-topic memory was missing or stale, so session-start fell back to the latest topic: `{topic_slug}`."
            )
        elif explicit_route:
            memory_summary = "Resolved from an explicit topic reference in the request or caller flags."
        else:
            memory_summary = "Resolved from the session-start routing layer."

        must_read_now: list[dict[str, str]] = []
        seen_paths: set[str] = set()

        def _append_read(path_value: str | Path | None, reason: str) -> None:
            normalized = self._normalize_artifact_path(path_value)
            if not normalized or normalized in seen_paths:
                return
            seen_paths.add(normalized)
            must_read_now.append({"path": normalized, "reason": reason})

        _append_read(
            runtime_protocol_note_path,
            "Primary AITP runtime contract for this topic. Open this immediately after the session-start contract.",
        )
        for item in runtime_bundle.get("must_read_now") or []:
            _append_read(item.get("path"), str(item.get("reason") or "").strip())

        control_note_path = self._normalize_artifact_path(
            steering_artifacts.get("control_note_path") or pointers.get("control_note_path")
        )
        operator_checkpoint_path = self._normalize_artifact_path(
            (runtime_bundle.get("operator_checkpoint") or {}).get("path")
        )
        operator_checkpoint_note_path = self._normalize_artifact_path(
            (runtime_bundle.get("operator_checkpoint") or {}).get("note_path")
        )
        idea_packet_path = self._normalize_artifact_path((runtime_bundle.get("idea_packet") or {}).get("path"))
        idea_packet_note_path = self._normalize_artifact_path((runtime_bundle.get("idea_packet") or {}).get("note_path"))
        innovation_direction_path = self._normalize_artifact_path(
            steering_artifacts.get("innovation_direction_path") or pointers.get("innovation_direction_path")
        )
        innovation_decisions_path = self._normalize_artifact_path(
            steering_artifacts.get("innovation_decisions_path") or pointers.get("innovation_decisions_path")
        )
        operator_checkpoint_status = str(((runtime_bundle.get("operator_checkpoint") or {}).get("status") or "")).strip()
        idea_packet_status = str(((runtime_bundle.get("idea_packet") or {}).get("status") or "")).strip()

        if steering_artifacts.get("detected"):
            _append_read(
                innovation_direction_path,
                "Authoritative translation of the latest human steering into a durable innovation target.",
            )
            _append_read(
                control_note_path,
                "Authoritative translation of the latest human steering into an executable control note.",
            )
            _append_read(
                innovation_decisions_path,
                "Durable steering history for this topic. Open when the redirect history matters.",
            )
        if idea_packet_status == "needs_clarification":
            _append_read(
                idea_packet_note_path,
                "Resolve the active idea-packet clarification gate before substantive execution continues.",
            )
        if operator_checkpoint_status == "requested":
            _append_read(
                operator_checkpoint_note_path,
                "Resolve the active operator checkpoint before deeper execution continues.",
            )
        pending_decisions = runtime_bundle.get("pending_decisions") or {}
        pending_decision_blockers = int(pending_decisions.get("blocking_count") or 0)
        pending_decisions_path = self._normalize_artifact_path(pending_decisions.get("path"))
        if pending_decision_blockers > 0:
            _append_read(
                pending_decisions_path,
                "Resolve blocking pending decisions before deeper execution continues.",
            )

        selected_action = (runtime_bundle.get("minimal_execution_brief") or {})
        selected_action_payload = {
            "action_id": str(selected_action.get("selected_action_id") or ""),
            "action_type": str(selected_action.get("selected_action_type") or ""),
            "summary": str(selected_action.get("selected_action_summary") or ""),
        }

        linear_flow = [
            {
                "step": "Treat the original chat request as already routed; do not ask for a topic again unless durable memory is still ambiguous.",
                "result": memory_summary,
            },
            {
                "step": "Read `session_start.generated.md` first, then `runtime_protocol.generated.md`.",
                "result": "Session-start defines the immediate startup order; the runtime bundle defines the topic contract.",
            },
            {
                "step": "If steering artifacts were auto-updated from the human request, treat `innovation_direction.md` and `control_note.md` as authoritative before continuing.",
                "result": "Natural-language steering becomes durable protocol state before execution.",
            },
            {
                "step": "Only then continue the currently selected bounded action and close with an exit audit when the step is done.",
                "result": selected_action_payload["summary"] or "Continue the bounded topic lane declared in the runtime bundle.",
            },
        ]
        if idea_packet_status == "needs_clarification":
            linear_flow.insert(
                2,
                {
                    "step": "Open `idea_packet.md` and answer its clarification questions before touching the queue or claiming substantive execution.",
                    "result": "AITP blocks deeper execution until the initial intent, validation route, and evidence bar are explicit.",
                },
            )
        if operator_checkpoint_status == "requested":
            linear_flow.insert(
                2,
                {
                    "step": "Open `operator_checkpoint.active.md` and resolve the active human-checkpoint question before the bounded loop continues.",
                    "result": "AITP stops at a durable operator checkpoint instead of silently guessing the human decision.",
                },
            )
        if pending_decision_blockers > 0:
            linear_flow.insert(
                2,
                {
                    "step": "Resolve the blocking pending decision(s) before touching the queue or continuing bounded execution.",
                    "result": "AITP pauses execution until blocking decisions are closed in durable decision traces.",
                },
            )
        linear_flow.insert(
            2
            + int(operator_checkpoint_status == "requested")
            + int(idea_packet_status == "needs_clarification")
            + int(pending_decision_blockers > 0),
            {
                "step": "Finish the files listed under `Must read now` before touching the queue or giving a substantial research answer.",
                "result": "Current topic state, question scope, validation route, and guardrails are loaded in a fixed order.",
            },
        )

        hard_stops = [
            "Do not skip session-start and jump straight into free-form explanation, browsing, or file editing for AITP-governed research work.",
            "Do not continue if `runtime_protocol.generated.md` is missing.",
            "Do not continue if conformance is not `pass`.",
            "Do not replace durable current-topic routing with a fresh topic guess when session-start already resolved the topic.",
            "Do not ignore `innovation_direction.md` or `control_note.md` after a steering request changed direction, paused work, or opened a branch.",
        ]
        if idea_packet_status == "needs_clarification":
            hard_stops.append(
                "Do not continue substantive execution until `idea_packet.md` resolves the missing intent fields and clarification questions."
            )
        if operator_checkpoint_status == "requested":
            hard_stops.append(
                "Do not continue deeper execution until `operator_checkpoint.active.md` is answered or cancelled."
            )
        if pending_decision_blockers > 0:
            hard_stops.append(
                "Do not continue deeper execution until blocking pending decisions are resolved."
            )
        if steering_artifacts.get("detected"):
            hard_stops.append(
                "This request carried human steering. `innovation_direction.md` and `control_note.md` must be read before deeper execution."
            )

        payload = {
            "contract_kind": "session_start_contract",
            "protocol_version": 1,
            "topic_slug": topic_slug,
            "updated_at": now_iso(),
            "updated_by": updated_by,
            "task": task,
            "canonical_entry": f'aitp session-start "{task}"',
            "routing": {
                "route": route_name,
                "reason": routing.get("reason"),
                "topic_slug": topic_slug,
                "topic_title": routing.get("topic"),
            },
            "memory_resolution": {
                "current_topic_first": True,
                "pre_route_current_topic_slug": pre_route_topic_slug or None,
                "pre_route_current_topic_valid": pre_route_current_valid,
                "used_current_topic_memory": used_current_topic_memory,
                "used_latest_topic_fallback": used_latest_topic_fallback,
                "summary": memory_summary,
            },
            "artifacts": {
                "session_start_contract_path": self._normalize_artifact_path(session_paths["json"]),
                "session_start_note_path": self._normalize_artifact_path(session_paths["note"]),
                "runtime_protocol_path": runtime_protocol_path,
                "runtime_protocol_note_path": runtime_protocol_note_path,
                "loop_state_path": self._normalize_artifact_path(loop_payload.get("loop_state_path")),
                "current_topic_memory_path": self._normalize_artifact_path(
                    (loop_payload.get("current_topic_memory") or {}).get("current_topic_path")
                ),
                "current_topic_note_path": self._normalize_artifact_path(
                    (loop_payload.get("current_topic_memory") or {}).get("current_topic_note_path")
                ),
                "operator_checkpoint_path": operator_checkpoint_path,
                "operator_checkpoint_note_path": operator_checkpoint_note_path,
                "idea_packet_path": idea_packet_path,
                "idea_packet_note_path": idea_packet_note_path,
                "innovation_direction_path": innovation_direction_path,
                "innovation_decisions_path": innovation_decisions_path,
                "control_note_path": control_note_path,
            },
            "must_read_now": must_read_now,
            "linear_flow": linear_flow,
            "selected_action": selected_action_payload,
            "hard_stops": hard_stops,
            "loop_state_summary": {
                "entry_conformance": loop_state.get("entry_conformance"),
                "exit_conformance": loop_state.get("exit_conformance"),
                "capability_status": loop_state.get("capability_status"),
                "trust_status": loop_state.get("trust_status"),
                "promotion_gate_status": loop_state.get("promotion_gate_status"),
            },
            "steering": {
                "detected": bool(steering_artifacts.get("detected")),
                "decision": steering_artifacts.get("decision"),
                "direction": steering_artifacts.get("direction"),
                "summary": steering_artifacts.get("summary"),
            },
        }
        write_json(session_paths["json"], payload)
        write_text(session_paths["note"], self._render_session_start_note(payload))
        return {
            **payload,
            "session_start_contract_path": str(session_paths["json"]),
            "session_start_note_path": str(session_paths["note"]),
            "runtime_root": str(runtime_root),
        }

    def recent_topics(self, *, limit: int = 10) -> list[dict[str, Any]]:
        rows = read_jsonl(self._runtime_topic_index_path())
        if not rows:
            return []
        ordered = sorted(
            rows,
            key=lambda row: str(row.get("updated_at") or ""),
        )
        ordered.reverse()
        return ordered[: max(1, limit)]

    def latest_topic_slug(self) -> str:
        rows = self.recent_topics(limit=1)
        if not rows:
            raise FileNotFoundError("No runtime topics have been materialized yet.")
        topic_slug = str(rows[0].get("topic_slug") or "").strip()
        if not topic_slug:
            raise FileNotFoundError("Runtime topic index is present but missing a valid topic slug.")
        return topic_slug

    def current_topic_slug(self, *, fallback_to_latest: bool = True) -> str:
        try:
            payload = self.get_current_topic_memory()
        except FileNotFoundError:
            payload = None

        topic_slug = str((payload or {}).get("topic_slug") or "").strip()
        if topic_slug:
            topic_state_path = self._runtime_root(topic_slug) / "topic_state.json"
            if topic_state_path.exists():
                return topic_slug

        if fallback_to_latest:
            return self.latest_topic_slug()
        raise FileNotFoundError("Current topic memory is missing or stale, and latest-topic fallback is disabled.")

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
        self.remember_current_topic(
            topic_slug=payload["topic_slug"],
            updated_by=updated_by,
            source="new-topic",
            human_request=human_request or question,
        )
        payload["template_mode"] = mode or self._research_mode_to_template_mode(
            str((payload.get("topic_state") or {}).get("research_mode") or research_mode or "")
        )
        return payload

    def refresh_runtime_context(
        self,
        *,
        topic_slug: str,
        updated_by: str = "aitp-cli",
        human_request: str | None = None,
        load_profile: str | None = None,
    ) -> dict[str, Any]:
        protocol_paths = self._materialize_runtime_protocol_bundle(
            topic_slug=topic_slug,
            updated_by=updated_by,
            human_request=human_request,
            load_profile=load_profile,
        )
        bundle = read_json(Path(protocol_paths["runtime_protocol_path"])) or {}
        topic_state = read_json(self._runtime_root(topic_slug) / "topic_state.json") or {}
        return {
            "topic_slug": topic_slug,
            "load_profile": str(bundle.get("load_profile") or topic_state.get("load_profile") or "light"),
            "runtime_protocol_path": protocol_paths["runtime_protocol_path"],
            "runtime_protocol_note_path": protocol_paths["runtime_protocol_note_path"],
            "topic_state": topic_state,
            "topic_synopsis": bundle.get("topic_synopsis") or {},
            "pending_decisions": bundle.get("pending_decisions") or {},
            "promotion_readiness": bundle.get("promotion_readiness") or {},
            "topic_skill_projection": bundle.get("topic_skill_projection") or {},
        }

    def topic_status(
        self,
        *,
        topic_slug: str,
        updated_by: str = "aitp-cli",
    ) -> dict[str, Any]:
        protocol_paths = self._materialize_runtime_protocol_bundle(
            topic_slug=topic_slug,
            updated_by=updated_by,
            load_profile=None,
        )
        bundle = read_json(Path(protocol_paths["runtime_protocol_path"])) or {}
        topic_state = read_json(self._runtime_root(topic_slug) / "topic_state.json") or {}
        minimal = bundle.get("minimal_execution_brief") or {}
        return {
            "topic_slug": topic_slug,
            "title": str(((bundle.get("active_research_contract") or {}).get("title") or self._topic_display_title(topic_slug))),
            "current_stage": bundle.get("resume_stage"),
            "research_mode": bundle.get("research_mode"),
            "load_profile": bundle.get("load_profile") or topic_state.get("load_profile"),
            "selected_action_id": minimal.get("selected_action_id"),
            "selected_action_type": minimal.get("selected_action_type"),
            "selected_action_summary": minimal.get("selected_action_summary"),
            "runtime_protocol_path": protocol_paths["runtime_protocol_path"],
            "runtime_protocol_note_path": protocol_paths["runtime_protocol_note_path"],
            "topic_state": topic_state,
            "topic_state_explainability": (topic_state.get("status_explainability") or {}),
            "topic_synopsis": bundle.get("topic_synopsis") or {},
            "pending_decisions": bundle.get("pending_decisions") or {},
            "active_research_contract": bundle.get("active_research_contract") or {},
            "idea_packet": bundle.get("idea_packet") or {},
            "operator_checkpoint": bundle.get("operator_checkpoint") or {},
            "promotion_readiness": bundle.get("promotion_readiness") or {},
            "open_gap_summary": bundle.get("open_gap_summary") or {},
            "strategy_memory": bundle.get("strategy_memory") or {},
            "topic_skill_projection": bundle.get("topic_skill_projection") or {},
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
            "load_profile": bundle.get("load_profile"),
            "selected_action_id": minimal.get("selected_action_id"),
            "selected_action_type": minimal.get("selected_action_type"),
            "selected_action_summary": minimal.get("selected_action_summary"),
            "current_stage": minimal.get("current_stage"),
            "open_next": minimal.get("open_next"),
            "must_read_now": bundle.get("must_read_now") or [],
            "escalation_triggers": bundle.get("escalation_triggers") or [],
            "topic_synopsis": bundle.get("topic_synopsis") or {},
            "pending_decisions": bundle.get("pending_decisions") or {},
            "open_gap_summary": bundle.get("open_gap_summary") or {},
            "strategy_memory": bundle.get("strategy_memory") or {},
            "topic_skill_projection": bundle.get("topic_skill_projection") or {},
            "topic_completion": bundle.get("topic_completion") or {},
            "runtime_protocol_note_path": protocol_paths["runtime_protocol_note_path"],
        }

    def project_topic_skill(
        self,
        *,
        topic_slug: str,
        updated_by: str = "aitp-cli",
        human_request: str | None = None,
        refresh_runtime_bundle: bool = True,
    ) -> dict[str, Any]:
        shell_surfaces = self.ensure_topic_shell_surfaces(
            topic_slug=topic_slug,
            updated_by=updated_by,
            human_request=human_request,
        )
        result = {
            "topic_slug": topic_slug,
            "topic_skill_projection": shell_surfaces.get("topic_skill_projection") or {},
            "topic_skill_projection_candidate": shell_surfaces.get("topic_skill_projection_candidate"),
            "topic_skill_projection_path": shell_surfaces.get("topic_skill_projection_path"),
            "topic_skill_projection_note_path": shell_surfaces.get("topic_skill_projection_note_path"),
        }
        if refresh_runtime_bundle:
            result["runtime_protocol"] = self._materialize_runtime_protocol_bundle(
                topic_slug=topic_slug,
                updated_by=updated_by,
                human_request=human_request,
            )
        return result

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
        load_profile: str | None = None,
    ) -> dict[str, Any]:
        research_mode = self._template_mode_to_research_mode(mode) if mode else None
        if max_auto_steps <= 0:
            payload = self.orchestrate(
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
            self.remember_current_topic(
                topic_slug=payload["topic_slug"],
                updated_by=updated_by,
                source="work",
                human_request=human_request or question,
            )
            payload["runtime_context"] = self.refresh_runtime_context(
                topic_slug=payload["topic_slug"],
                updated_by=updated_by,
                human_request=human_request or question,
                load_profile=load_profile,
            )
            return payload
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
            load_profile=load_profile,
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
            "analytic": {
                "validation_mode": "analytic",
                "verification_focus": "Check limiting cases, dimensional consistency, symmetry constraints, and self-consistency before trusting the active derivation or claim.",
                "analytic_check_families": [
                    "limiting_case",
                    "dimensional_consistency",
                    "symmetry_constraint",
                    "self_consistency",
                ],
                "required_checks": [
                    "State at least one limiting case or asymptotic regime the current claim should satisfy.",
                    "Check dimensional or units consistency where the claim carries physical scales.",
                    "Record any symmetry, conservation, or invariance expectation that the result must respect.",
                    "Return to L0 or L1 if the analytic check depends on an unstated definition, regime, or prior-work comparison.",
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
        validation_contract["analytic_check_families"] = defaults.get("analytic_check_families") or []
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
            *self._resolve_runtime_python_command(),
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
                "idea_packet": str(self._idea_packet_paths(resolved_topic_slug)["json"]),
                "idea_packet_note": str(self._idea_packet_paths(resolved_topic_slug)["note"]),
                "operator_checkpoint": str(self._operator_checkpoint_paths(resolved_topic_slug)["json"]),
                "operator_checkpoint_note": str(self._operator_checkpoint_paths(resolved_topic_slug)["note"]),
                "operator_checkpoint_ledger": str(self._operator_checkpoint_paths(resolved_topic_slug)["ledger"]),
                "topic_dashboard": str(self._topic_dashboard_path(resolved_topic_slug)),
                "promotion_readiness": str(self._promotion_readiness_path(resolved_topic_slug)),
                "gap_map": str(self._gap_map_path(resolved_topic_slug)),
            },
            "topic_state": self.get_runtime_state(resolved_topic_slug),
            "conformance_state": read_json(runtime_root / "conformance_state.json"),
        }

    def audit(self, *, topic_slug: str, phase: str = "entry", updated_by: str = "aitp-cli") -> dict[str, Any]:
        command = [
            *self._resolve_runtime_python_command(),
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

    def audit_formal_theory(
        self,
        *,
        topic_slug: str,
        candidate_id: str,
        run_id: str | None = None,
        updated_by: str = "aitp-cli",
        formal_theory_role: str = "trusted_target",
        statement_graph_role: str = "target_statement",
        definition_trust_tier: str | None = None,
        target_statement_id: str | None = None,
        statement_graph_parents: list[str] | None = None,
        statement_graph_children: list[str] | None = None,
        informal_statement: str | None = None,
        formal_target: str | None = None,
        faithfulness_status: str = "pending",
        faithfulness_strategy: str | None = None,
        faithfulness_notes: str | None = None,
        comparator_audit_status: str = "pending",
        comparator_risks: list[str] | None = None,
        nearby_variants: list[dict[str, str]] | None = None,
        comparator_notes: str | None = None,
        provenance_kind: str = "generated_from_scratch",
        attribution_requirements: list[str] | None = None,
        provenance_sources: list[str] | None = None,
        provenance_notes: str | None = None,
        prerequisite_closure_status: str = "pending",
        lean_prerequisite_ids: list[str] | None = None,
        supporting_obligation_ids: list[str] | None = None,
        formalization_blockers: list[str] | None = None,
        prerequisite_notes: str | None = None,
    ) -> dict[str, Any]:
        resolved_run_id = self._resolve_run_id(topic_slug, run_id)
        if not resolved_run_id:
            raise FileNotFoundError(f"Unable to resolve a validation run for topic {topic_slug}")

        candidate = self._load_candidate(topic_slug, resolved_run_id, candidate_id)
        candidate_type = str(candidate.get("candidate_type") or "")
        runtime_policy = self._load_runtime_policy()
        trust_policy = runtime_policy.get("formal_theory_trust_boundary_policy") or {}
        faithfulness_policy = runtime_policy.get("faithfulness_policy") or {}
        comparator_policy = runtime_policy.get("comparator_audit_policy") or {}
        provenance_policy = runtime_policy.get("provenance_review_policy") or {}
        prerequisite_policy = runtime_policy.get("prerequisite_closure_policy") or {}

        normalized_role = str(formal_theory_role or "").strip() or "trusted_target"
        normalized_statement_graph_role = str(statement_graph_role or "").strip()
        if not normalized_statement_graph_role:
            raise ValueError("statement_graph_role is required")

        trusted_roles = {
            str(value).strip()
            for value in (trust_policy.get("trusted_roles") or [])
            if str(value).strip()
        }
        intermediate_roles = {
            str(value).strip()
            for value in (trust_policy.get("intermediate_roles") or [])
            if str(value).strip()
        }
        supporting_roles = {
            str(value).strip()
            for value in (trust_policy.get("supporting_roles") or [])
            if str(value).strip()
        }
        known_roles = trusted_roles | intermediate_roles | supporting_roles
        if as_bool(trust_policy.get("enabled")) and known_roles and normalized_role not in known_roles:
            raise ValueError(
                "formal_theory_role must match the configured trust-boundary policy roles."
            )

        allowed_faithfulness_statuses = {
            str(value).strip()
            for value in (faithfulness_policy.get("allowed_statuses") or [])
            if str(value).strip()
        }
        normalized_faithfulness_status = str(faithfulness_status or "").strip() or "pending"
        if (
            as_bool(faithfulness_policy.get("enabled"))
            and allowed_faithfulness_statuses
            and normalized_faithfulness_status not in allowed_faithfulness_statuses
        ):
            raise ValueError("faithfulness_status is not allowed by faithfulness_policy")

        allowed_comparator_statuses = {
            str(value).strip()
            for value in (comparator_policy.get("allowed_statuses") or [])
            if str(value).strip()
        }
        normalized_comparator_status = str(comparator_audit_status or "").strip() or "pending"
        if (
            as_bool(comparator_policy.get("enabled"))
            and allowed_comparator_statuses
            and normalized_comparator_status not in allowed_comparator_statuses
        ):
            raise ValueError("comparator_audit_status is not allowed by comparator_audit_policy")

        allowed_provenance_kinds = {
            str(value).strip()
            for value in (provenance_policy.get("allowed_provenance_kinds") or [])
            if str(value).strip()
        }
        normalized_provenance_kind = str(provenance_kind or "").strip() or "generated_from_scratch"
        if (
            as_bool(provenance_policy.get("enabled"))
            and allowed_provenance_kinds
            and normalized_provenance_kind not in allowed_provenance_kinds
        ):
            raise ValueError("provenance_kind is not allowed by provenance_review_policy")

        allowed_prerequisite_statuses = {
            str(value).strip()
            for value in (prerequisite_policy.get("allowed_statuses") or [])
            if str(value).strip()
        }
        normalized_prerequisite_status = str(prerequisite_closure_status or "").strip() or "pending"
        if (
            as_bool(prerequisite_policy.get("enabled"))
            and allowed_prerequisite_statuses
            and normalized_prerequisite_status not in allowed_prerequisite_statuses
        ):
            raise ValueError("prerequisite_closure_status is not allowed by prerequisite_closure_policy")

        normalized_definition_trust_tier = str(definition_trust_tier or "").strip()
        normalized_target_statement_id = (
            str(target_statement_id or "").strip()
            or str(formal_target or "").strip()
            or str((candidate.get("intended_l2_targets") or [""])[0] or "").strip()
            or candidate_id
        )
        normalized_parents = self._dedupe_strings(statement_graph_parents)
        normalized_children = self._dedupe_strings(statement_graph_children)
        normalized_attribution_requirements = self._dedupe_strings(attribution_requirements)
        normalized_provenance_sources = self._dedupe_strings(provenance_sources)
        normalized_lean_prerequisite_ids = self._dedupe_strings(lean_prerequisite_ids)
        normalized_supporting_obligation_ids = self._dedupe_strings(supporting_obligation_ids)
        normalized_formalization_blockers = self._dedupe_strings(formalization_blockers)
        normalized_comparator_risks = self._dedupe_strings(comparator_risks)

        normalized_nearby_variants: list[dict[str, str]] = []
        for row in nearby_variants or []:
            label = str(row.get("label") or "").strip()
            relation = str(row.get("relation") or "").strip()
            verdict = str(row.get("verdict") or "").strip()
            notes = str(row.get("notes") or "").strip()
            if not label or not relation or not verdict:
                continue
            normalized_nearby_variants.append(
                {
                    "label": label,
                    "relation": relation,
                    "verdict": verdict,
                    "notes": notes,
                }
            )

        comparator_goal = str(comparator_policy.get("comparator_goal") or "").strip()
        normalized_faithfulness_strategy = str(faithfulness_strategy or "").strip()
        normalized_faithfulness_notes = str(faithfulness_notes or "").strip()
        normalized_informal_statement = str(informal_statement or "").strip() or str(candidate.get("summary") or "").strip()
        normalized_formal_target = str(formal_target or "").strip()
        normalized_comparator_notes = str(comparator_notes or "").strip()
        normalized_provenance_notes = str(provenance_notes or "").strip()
        normalized_prerequisite_notes = str(prerequisite_notes or "").strip()

        blocking_reasons: list[str] = []
        if as_bool(trust_policy.get("enabled")):
            if trusted_roles and normalized_role not in trusted_roles:
                if normalized_role in intermediate_roles:
                    blocking_reasons.append("formal_theory_role_is_intermediate_theory")
                elif normalized_role in supporting_roles:
                    blocking_reasons.append("formal_theory_role_is_supporting_context")
                else:
                    blocking_reasons.append("formal_theory_role_not_trusted_target")

        required_faithfulness_roles = {
            str(value).strip()
            for value in (faithfulness_policy.get("default_required_for_roles") or [])
            if str(value).strip()
        }
        blocking_faithfulness_statuses = {
            str(value).strip()
            for value in (faithfulness_policy.get("blocking_statuses") or [])
            if str(value).strip()
        }
        if normalized_role in required_faithfulness_roles:
            if not normalized_faithfulness_strategy:
                blocking_reasons.append("missing_faithfulness_strategy")
            if normalized_faithfulness_status in blocking_faithfulness_statuses:
                blocking_reasons.append("faithfulness_review_pending")

        required_comparator_roles = {
            str(value).strip()
            for value in (comparator_policy.get("required_for_roles") or [])
            if str(value).strip()
        }
        if normalized_role in required_comparator_roles:
            if normalized_comparator_status == "failed":
                blocking_reasons.append("comparator_audit_failed")
            elif normalized_comparator_status != "passed":
                blocking_reasons.append("comparator_audit_not_passed")

        if as_bool(provenance_policy.get("enabled")):
            if not normalized_attribution_requirements:
                blocking_reasons.append("missing_attribution_requirements")
            if (
                normalized_provenance_kind
                in {"retrieved_existing_formalization", "adapted_existing_formalization", "mixed"}
                and not normalized_provenance_sources
            ):
                blocking_reasons.append("missing_provenance_sources")

        required_prerequisite_roles = {
            str(value).strip()
            for value in (prerequisite_policy.get("default_required_for_roles") or [])
            if str(value).strip()
        }
        blocking_prerequisite_statuses = {
            str(value).strip()
            for value in (prerequisite_policy.get("blocking_statuses") or [])
            if str(value).strip()
        }
        if normalized_role in required_prerequisite_roles:
            if normalized_prerequisite_status in blocking_prerequisite_statuses:
                blocking_reasons.append("prerequisite_closure_incomplete")
        if normalized_formalization_blockers:
            blocking_reasons.append("formalization_blockers_present")

        overall_status = "ready" if not blocking_reasons else "blocked"
        updated_at = now_iso()
        packet_paths = self._theory_packet_paths(topic_slug, resolved_run_id, candidate_id)

        faithfulness_review = {
            "schema_version": 1,
            "topic_slug": topic_slug,
            "run_id": resolved_run_id,
            "candidate_id": candidate_id,
            "candidate_type": candidate_type,
            "formal_theory_role": normalized_role,
            "statement_graph_role": normalized_statement_graph_role,
            "target_statement_id": normalized_target_statement_id,
            "statement_graph_parents": normalized_parents,
            "statement_graph_children": normalized_children,
            "informal_statement": normalized_informal_statement,
            "formal_target": normalized_formal_target,
            "status": normalized_faithfulness_status,
            "strategy": normalized_faithfulness_strategy,
            "notes": normalized_faithfulness_notes,
            "updated_at": updated_at,
            "updated_by": updated_by,
        }
        comparator_audit_record = {
            "schema_version": 1,
            "topic_slug": topic_slug,
            "run_id": resolved_run_id,
            "candidate_id": candidate_id,
            "candidate_type": candidate_type,
            "formal_theory_role": normalized_role,
            "status": normalized_comparator_status,
            "goal": comparator_goal,
            "nearby_variants": normalized_nearby_variants,
            "risks": normalized_comparator_risks,
            "notes": normalized_comparator_notes,
            "updated_at": updated_at,
            "updated_by": updated_by,
        }
        provenance_review = {
            "schema_version": 1,
            "topic_slug": topic_slug,
            "run_id": resolved_run_id,
            "candidate_id": candidate_id,
            "candidate_type": candidate_type,
            "provenance_kind": normalized_provenance_kind,
            "attribution_requirements": normalized_attribution_requirements,
            "provenance_sources": normalized_provenance_sources,
            "notes": normalized_provenance_notes,
            "updated_at": updated_at,
            "updated_by": updated_by,
        }
        prerequisite_closure_review = {
            "schema_version": 1,
            "topic_slug": topic_slug,
            "run_id": resolved_run_id,
            "candidate_id": candidate_id,
            "candidate_type": candidate_type,
            "formal_theory_role": normalized_role,
            "status": normalized_prerequisite_status,
            "lean_prerequisite_ids": normalized_lean_prerequisite_ids,
            "supporting_obligation_ids": normalized_supporting_obligation_ids,
            "formalization_blockers": normalized_formalization_blockers,
            "notes": normalized_prerequisite_notes,
            "updated_at": updated_at,
            "updated_by": updated_by,
        }

        write_json(packet_paths["faithfulness_review"], faithfulness_review)
        write_json(packet_paths["comparator_audit_record"], comparator_audit_record)
        write_json(packet_paths["provenance_review"], provenance_review)
        write_json(packet_paths["prerequisite_closure_review"], prerequisite_closure_review)

        formal_theory_review = {
            "schema_version": 1,
            "topic_slug": topic_slug,
            "run_id": resolved_run_id,
            "candidate_id": candidate_id,
            "candidate_type": candidate_type,
            "formal_theory_role": normalized_role,
            "statement_graph_role": normalized_statement_graph_role,
            "target_statement_id": normalized_target_statement_id,
            "statement_graph_parents": normalized_parents,
            "statement_graph_children": normalized_children,
            "faithfulness_status": normalized_faithfulness_status,
            "comparator_audit_status": normalized_comparator_status,
            "comparator_risks": normalized_comparator_risks,
            "nearby_variants": normalized_nearby_variants,
            "provenance_kind": normalized_provenance_kind,
            "prerequisite_closure_status": normalized_prerequisite_status,
            "overall_status": overall_status,
            "blocking_reasons": blocking_reasons,
            "attribution_requirements": normalized_attribution_requirements,
            "provenance_sources": normalized_provenance_sources,
            "lean_prerequisite_ids": normalized_lean_prerequisite_ids,
            "supporting_obligation_ids": normalized_supporting_obligation_ids,
            "formalization_blockers": normalized_formalization_blockers,
            "faithfulness_review_path": self._relativize(packet_paths["faithfulness_review"]),
            "comparator_audit_record_path": self._relativize(packet_paths["comparator_audit_record"]),
            "provenance_review_path": self._relativize(packet_paths["provenance_review"]),
            "prerequisite_closure_review_path": self._relativize(packet_paths["prerequisite_closure_review"]),
            "formal_theory_review_path": self._relativize(packet_paths["formal_theory_review"]),
            "updated_at": updated_at,
            "updated_by": updated_by,
        }
        if normalized_definition_trust_tier:
            formal_theory_review["definition_trust_tier"] = normalized_definition_trust_tier
        if normalized_faithfulness_strategy:
            formal_theory_review["faithfulness_strategy"] = normalized_faithfulness_strategy
        if normalized_faithfulness_notes:
            formal_theory_review["faithfulness_notes"] = normalized_faithfulness_notes
        if normalized_informal_statement:
            formal_theory_review["informal_statement"] = normalized_informal_statement
        if normalized_formal_target:
            formal_theory_review["formal_target"] = normalized_formal_target
        if comparator_goal:
            formal_theory_review["comparator_goal"] = comparator_goal
        if normalized_comparator_notes:
            formal_theory_review["comparator_notes"] = normalized_comparator_notes
        if normalized_provenance_notes:
            formal_theory_review["provenance_notes"] = normalized_provenance_notes
        if normalized_prerequisite_notes:
            formal_theory_review["prerequisite_notes"] = normalized_prerequisite_notes

        write_json(packet_paths["formal_theory_review"], formal_theory_review)

        updated_candidate = dict(candidate)
        updated_candidate["formal_theory_role"] = normalized_role
        updated_candidate["statement_graph_role"] = normalized_statement_graph_role
        updated_candidate["target_statement_id"] = normalized_target_statement_id
        if normalized_definition_trust_tier:
            updated_candidate["definition_trust_tier"] = normalized_definition_trust_tier
        updated_candidate["faithfulness_status"] = normalized_faithfulness_status
        updated_candidate["comparator_audit_status"] = normalized_comparator_status
        updated_candidate["provenance_kind"] = normalized_provenance_kind
        updated_candidate["prerequisite_closure_status"] = normalized_prerequisite_status
        updated_candidate["formalization_blockers"] = normalized_formalization_blockers
        updated_candidate["formal_theory_review_overall_status"] = overall_status
        updated_candidate["formal_theory_blocking_reasons"] = blocking_reasons
        theory_packet_refs = dict(updated_candidate.get("theory_packet_refs") or {})
        theory_packet_refs.update(
            {
                "faithfulness_review": self._relativize(packet_paths["faithfulness_review"]),
                "comparator_audit_record": self._relativize(packet_paths["comparator_audit_record"]),
                "provenance_review": self._relativize(packet_paths["provenance_review"]),
                "prerequisite_closure_review": self._relativize(packet_paths["prerequisite_closure_review"]),
                "formal_theory_review": self._relativize(packet_paths["formal_theory_review"]),
            }
        )
        updated_candidate["theory_packet_refs"] = theory_packet_refs
        self._replace_candidate_row(topic_slug, resolved_run_id, candidate_id, updated_candidate)

        return {
            "topic_slug": topic_slug,
            "run_id": resolved_run_id,
            "candidate_id": candidate_id,
            "candidate_type": candidate_type,
            "target_statement_id": normalized_target_statement_id,
            "overall_status": overall_status,
            "blocking_reasons": blocking_reasons,
            "paths": {
                "faithfulness_review": str(packet_paths["faithfulness_review"]),
                "comparator_audit_record": str(packet_paths["comparator_audit_record"]),
                "provenance_review": str(packet_paths["provenance_review"]),
                "prerequisite_closure_review": str(packet_paths["prerequisite_closure_review"]),
                "formal_theory_review": str(packet_paths["formal_theory_review"]),
            },
            "artifacts": {
                "faithfulness_review": faithfulness_review,
                "comparator_audit_record": comparator_audit_record,
                "provenance_review": provenance_review,
                "prerequisite_closure_review": prerequisite_closure_review,
                "formal_theory_review": formal_theory_review,
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
            "research_question.contract.json",
            "research_question.contract.md",
            "validation_contract.active.json",
            "validation_contract.active.md",
            "idea_packet.json",
            "idea_packet.md",
            "operator_checkpoint.active.json",
            "operator_checkpoint.active.md",
            "operator_checkpoints.jsonl",
            "topic_dashboard.md",
            "promotion_readiness.md",
            "gap_map.md",
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
        supporting_unit_paths: list[Path] = []
        question_ids = list(unit_payload.get("supporting_regression_question_ids") or [])
        oracle_ids = list(unit_payload.get("supporting_oracle_ids") or [])
        for question_id in question_ids:
            question_path = unit_path_for(tpkn_root, "regression_question", question_id)
            matching_oracle_id = next(
                (
                    oracle_id
                    for oracle_id in oracle_ids
                    if oracle_id.split(":", 1)[-1] == question_id.split(":", 1)[-1]
                ),
                oracle_ids[0] if oracle_ids else None,
            )
            question_payload = build_supporting_regression_question_unit(
                unit_id=question_id,
                domain=default_domain,
                source_id=resolved_source_id,
                source_section=resolved_source_section,
                source_anchor_notes=(
                    f"AITP generated this supporting regression surface while promoting {candidate_id} "
                    f"for topic {topic_slug}."
                ),
                promoted_unit_id=target_unit_id,
                promoted_unit_title=str(unit_payload.get("title") or candidate.get("title") or target_unit_id),
                topic_slug=topic_slug,
                oracle_id=matching_oracle_id,
            )
            existing_question_payload = read_json(question_path)
            if existing_question_payload is None or str(existing_question_payload.get("validation_status") or "") == "generated-support":
                write_external_json(question_path, question_payload)
            supporting_unit_paths.append(question_path)
        for oracle_id in oracle_ids:
            oracle_path = unit_path_for(tpkn_root, "question_oracle", oracle_id)
            matching_question_id = next(
                (
                    question_id
                    for question_id in question_ids
                    if question_id.split(":", 1)[-1] == oracle_id.split(":", 1)[-1]
                ),
                question_ids[0] if question_ids else "",
            )
            oracle_payload = build_supporting_question_oracle_unit(
                unit_id=oracle_id,
                domain=default_domain,
                source_id=resolved_source_id,
                source_section=resolved_source_section,
                source_anchor_notes=(
                    f"AITP generated this supporting oracle while promoting {candidate_id} "
                    f"for topic {topic_slug}."
                ),
                promoted_unit_id=target_unit_id,
                promoted_unit_title=str(unit_payload.get("title") or candidate.get("title") or target_unit_id),
                regression_question_id=matching_question_id,
                topic_slug=topic_slug,
            )
            existing_oracle_payload = read_json(oracle_path)
            if existing_oracle_payload is None or str(existing_oracle_payload.get("validation_status") or "") == "generated-support":
                write_external_json(oracle_path, oracle_payload)
            supporting_unit_paths.append(oracle_path)
        check_results = run_tpkn_checks(
            tpkn_root,
            scoped_paths=[unit_path, manifest_path, *supporting_unit_paths],
        )

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
        if str(candidate.get("candidate_type") or "") == "topic_skill_projection":
            raise PermissionError("topic_skill_projection is human-reviewed only in v1 and may not enter L2_auto.")
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
        formal_theory_review = read_json(packet_paths["formal_theory_review"]) or {}
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
        if str(candidate.get("candidate_type") or "") in self._theory_formal_candidate_types():
            if not packet_paths["formal_theory_review"].exists():
                raise FileNotFoundError(
                    "Missing theory packet artifacts for auto promotion: formal_theory_review"
                )
            if str(formal_theory_review.get("overall_status") or "") != "ready":
                raise PermissionError("Auto promotion requires a ready formal_theory_review.json status.")

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
            "formal_theory_review_status": str(formal_theory_review.get("overall_status") or "not_required"),
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
        if packet_paths["faithfulness_review"].exists():
            review_artifacts["faithfulness_review_path"] = self._relativize(packet_paths["faithfulness_review"])
        if packet_paths["comparator_audit_record"].exists():
            review_artifacts["comparator_audit_record_path"] = self._relativize(packet_paths["comparator_audit_record"])
        if packet_paths["provenance_review"].exists():
            review_artifacts["provenance_review_path"] = self._relativize(packet_paths["provenance_review"])
        if packet_paths["prerequisite_closure_review"].exists():
            review_artifacts["prerequisite_closure_review_path"] = self._relativize(packet_paths["prerequisite_closure_review"])
        if packet_paths["formal_theory_review"].exists():
            review_artifacts["formal_theory_review_path"] = self._relativize(packet_paths["formal_theory_review"])
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
            "formal_theory_review_status": str(formal_theory_review.get("overall_status") or "not_required"),
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
        load_profile: str | None = None,
    ) -> dict[str, Any]:
        if not topic_slug and not topic:
            raise ValueError("Provide topic_slug or topic.")

        active_control_note = control_note
        bootstrap = self.orchestrate(
            topic_slug=topic_slug,
            topic=topic,
            statement=statement,
            run_id=run_id,
            control_note=active_control_note,
            updated_by=updated_by,
            human_request=human_request,
            skill_queries=skill_queries or [],
            research_mode=research_mode,
        )
        resolved_topic_slug = bootstrap["topic_slug"]
        resolved_run_id = self._resolve_run_id(resolved_topic_slug, run_id)
        steering_artifacts = self.materialize_steering_from_human_request(
            topic_slug=resolved_topic_slug,
            run_id=resolved_run_id,
            human_request=human_request,
            updated_by=updated_by,
            topic_state=bootstrap.get("topic_state"),
            control_note=active_control_note,
        )
        if steering_artifacts.get("requires_reorchestrate"):
            active_control_note = str(
                steering_artifacts.get("control_note_path") or active_control_note or ""
            ).strip() or active_control_note
            bootstrap = self.orchestrate(
                topic_slug=resolved_topic_slug,
                run_id=resolved_run_id,
                control_note=active_control_note,
                updated_by=updated_by,
                skill_queries=skill_queries or [],
                human_request=human_request,
                research_mode=research_mode,
            )
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
                control_note=active_control_note,
                updated_by=updated_by,
                skill_queries=skill_queries or [],
                human_request=human_request,
                research_mode=research_mode,
            )
        if executed_auto_actions:
            self.orchestrate(
                topic_slug=resolved_topic_slug,
                run_id=resolved_run_id,
                control_note=active_control_note,
                updated_by=updated_by,
                skill_queries=skill_queries or [],
                human_request=human_request,
                research_mode=research_mode,
            )
            auto_queue_path = str(self._runtime_root(resolved_topic_slug) / "action_queue.jsonl")
            remaining_pending = sum(
                1
                for row in read_jsonl(Path(auto_queue_path))
                if str(row.get("status") or "").strip() == "pending"
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
        current_topic_memory = self.remember_current_topic(
            topic_slug=resolved_topic_slug,
            updated_by=updated_by,
            source="run_topic_loop",
            human_request=human_request,
        )

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
            "steering": steering_artifacts,
            "current_topic_memory": current_topic_memory,
        }
        resolved_load_profile, load_profile_reason = self._resolve_load_profile(
            explicit_load_profile=load_profile,
            human_request=human_request,
            topic_state=bootstrap.get("topic_state"),
        )
        self._persist_load_profile_state(
            topic_slug=resolved_topic_slug,
            load_profile=resolved_load_profile,
            reason=load_profile_reason,
            updated_by=updated_by,
        )
        loop_state["load_profile"] = resolved_load_profile
        loop_state["load_profile_reason"] = load_profile_reason
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
            load_profile=resolved_load_profile,
        )
        return {
            "topic_slug": resolved_topic_slug,
            "run_id": resolved_run_id,
            "load_profile": resolved_load_profile,
            "bootstrap": bootstrap,
            "entry_audit": entry_audit,
            "auto_actions": auto_actions,
            "capability_audit": capability,
            "trust_audit": trust,
            "exit_audit": exit_audit,
            "loop_state_path": str(loop_state_path),
            "loop_history_path": str(loop_history_path),
            "loop_state": loop_state,
            "steering_artifacts": steering_artifacts,
            "current_topic_memory": current_topic_memory,
            "runtime_protocol": protocol_paths,
        }

    def _session_start_routing_block(self, *, hidden_entry: str) -> str:
        return f"""## Session-start routing invariant

Before any substantial response in an AITP-governed workspace:

1. materialize session state through {hidden_entry}
2. check durable current-topic memory first with `aitp current-topic` or `runtime/current_topic.json`
3. if the user says `继续这个 topic`, `continue this topic`, `this topic`, or `current topic`, resolve that to current-topic memory immediately
4. only fall back to latest-topic memory if current-topic memory is missing
5. translate steering requests like `方向改成 X`, `continue this topic but focus on X`, or `先补验证` into durable steering state before substantial execution continues
6. once AITP materializes the runtime bundle, follow `runtime_protocol.generated.md` and its `Must read now` list
7. only ask for a topic slug when both the request and durable memory remain genuinely ambiguous

This rule applies at session start, not later as a soft reminder.
"""

    def _codex_skill_template(self) -> str:
        session_start = self._session_start_routing_block(
            hidden_entry="platform bootstrap plus fallback `aitp session-start \"<original request>\"` when you need to materialize routing explicitly"
        )
        return f"""---
name: aitp-runtime
description: Route Codex research work through the AITP kernel. Use when the request is a theory topic, current-topic continuation, idea steering, derivation or validation planning, paper-learning task, or other AITP-governed execution instead of plain coding.
---

# AITP Runtime

{session_start}

## Required entry

1. In a bare `codex` research session, do not start with direct browsing or free-form synthesis.
2. Let the installed bootstrap route natural-language research work into AITP first. Use `aitp session-start "<task>"` only as the manual fallback.
3. Once the runtime bundle exists, read `runtime_protocol.generated.md`, then the files listed under `Must read now`.
4. Treat `session_start.generated.md` as a runtime audit artifact when it exists, not as a separate user ritual.
5. Ordinary topic work should stay in the light runtime profile unless a benchmark mismatch, scope change, promotion step, or explicit deep check forces the full profile.
6. Keep `innovation_direction.md` and `control_note.md` current before touching the queue.
7. Expand promotion, consultation, capability, or queue details only when the named trigger in the runtime bundle fires.
8. Register reusable operations with `aitp operation-init ...`.
9. For human-reviewed `L2`, use `aitp request-promotion ...` and wait for `aitp approve-promotion ...`.
10. For theory-formal `L2_auto`, materialize coverage/consensus artifacts with `aitp coverage-audit ...` and then use `aitp auto-promote ...`.
11. End with `aitp audit --topic-slug <topic_slug> --phase exit`.

## Hard rules

- If the conformance audit fails, the run does not count as AITP work.
- If the task is theoretical-physics research rather than plain coding, staying inside AITP is mandatory.
- Prefer durable control notes and contract files over Python heuristic defaults.
- Keep `innovation_direction.md` and `control_note.md` current before substantial execution continues.
- Every reusable operation must pass through `aitp trust-audit ...` before AITP treats it as trusted.
- If a new numerical backend or diagnostic is being trusted, scaffold a baseline first with `aitp baseline ...`.
- If a derivation-heavy method is being claimed as understood, scaffold atomic understanding first with `aitp atomize ...`.
- If there is a capability gap, prefer `aitp loop ... --skill-query ...` so discovery becomes runtime state instead of ad hoc browsing.
- Human-reviewed Layer 2 promotion is blocked until `promotion_gate.json` says `approved` and `aitp promote ...` records the writeback.
- Theory-formal `L2_auto` promotion is blocked until `coverage_ledger.json` passes and `agent_consensus.json` is ready.
- Do not expose protocol jargon in ordinary user-facing dialogue.

## Common commands

```bash
aitp session-start "<task>"
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

    def _using_aitp_skill_template(self, platform: str) -> str:
        if platform == "codex":
            runtime_reference = "the installed `aitp-runtime` skill plus Codex native skill discovery"
            entry_commands = "`aitp session-start \"<task>\"`, `aitp new-topic ...`, `aitp resume ...`, `aitp loop ...`, or `aitp bootstrap ...`"
            hidden_entry = "platform bootstrap with fallback `aitp session-start \"<original request>\"`"
        elif platform == "claude-code":
            runtime_reference = "the installed `aitp-runtime` skill, the `using-aitp` gatekeeper, and the Claude SessionStart bootstrap"
            entry_commands = "`aitp session-start \"<task>\"`, `aitp loop ...`, `aitp resume ...`, or `aitp bootstrap ...`"
            hidden_entry = "the Claude bootstrap with fallback `aitp session-start \"<original request>\"`"
        elif platform == "opencode":
            runtime_reference = "the installed `aitp-runtime` skill, the `using-aitp` gatekeeper, and the OpenCode plugin bootstrap"
            entry_commands = "`aitp session-start \"<task>\"`, `aitp loop ...`, `aitp resume ...`, or `aitp bootstrap ...`"
            hidden_entry = "the OpenCode bootstrap with fallback `aitp session-start \"<original request>\"`"
        else:
            runtime_reference = "the installed `aitp-runtime` skill"
            entry_commands = "`aitp session-start \"<task>\"`, `aitp loop ...`, `aitp resume ...`, or `aitp bootstrap ...`"
            hidden_entry = "plain `aitp session-start \"<original request>\"`"

        session_start = self._session_start_routing_block(hidden_entry=hidden_entry)

        return f"""---
name: using-aitp
description: Use when starting any conversation in a workspace where AITP is installed, or when the user says things like `继续这个 topic`, `continue this topic`, `current topic`, `开一个新 topic`, `方向改成 X`, asks to study a paper, evaluate an idea, plan a derivation, or set a validation route. Establishes whether work must first enter AITP before ANY substantial response.
---

# Using AITP

Use this skill to decide whether the current task must be governed by AITP
before you do substantial work.

<EXTREMELY-IMPORTANT>
If there is even a small chance the task is non-trivial theoretical-physics
research, theory-to-code validation, idea evaluation, literature-grounded
scientific synthesis, or protocol-governed topic work, you MUST enter AITP
first through {entry_commands}.

Do not start with free-form browsing, free-form explanation, or ad hoc file
editing if the task should actually be inside AITP.
</EXTREMELY-IMPORTANT>

{session_start}

## Mandatory triage

Before doing substantial work, classify the task into one of these buckets:

1. `AITP research execution`
   - a real research topic, idea, paper set, validation target, derivation,
     benchmark, or theory-side execution loop
2. `AITP protocol / tooling maintenance`
   - editing the AITP repo itself, its docs, adapters, tests, or installer
3. `plain coding outside AITP`
   - normal software work that does not claim to be AITP-governed research

## Hard gate

If the task is bucket `1`, you MUST:

1. enter through {runtime_reference}
2. materialize or resume runtime state
3. make sure `innovation_direction.md` and `control_note.md` are current before substantial execution continues
4. if the operator speaks in natural steering language such as `继续这个 topic，方向改成 X`, translate that request into durable steering artifacts before continuing
5. read `runtime_protocol.generated.md`
6. read the files named under `Must read now`
7. treat `session_start.generated.md` as a backend routing artifact when it exists, not as a user-facing entry ritual
8. only then continue with the task

If conformance fails, the work does not count as AITP work.

## Conversation style rules

- Do not expose protocol jargon to the user. Avoid phrases like `decision_point`, `L2 consultation`, or `load profile`.
- Ask in plain research language.
- By default ask one question at a time.
- If the user already gave enough direction, do not ask just to satisfy a workflow ritual.
- If the user says `you decide`, `just go`, or `直接做`, treat that as authorization to proceed and record the durable trace in the background.

## Natural-language routing

Do not make the user translate a clear research request into AITP shell syntax
when the intent is already recoverable from durable routing memory.

Preferred hidden routing:

- If the user is clearly opening a new research topic, for example `开一个新 topic：Topological phases from modular data`, extract the topic title and route through `aitp session-start "<original request>"` or the platform bootstrap.
- If the user says `继续这个 topic`, `continue this topic`, `current topic`, or otherwise refers to the active topic without naming a slug, route through `aitp session-start "<original request>"` or the platform bootstrap, letting current-topic memory win first.
- If the user says `方向改成 X`, `continue this topic but focus on X`, `先补验证`, or another steering phrase, translate it into durable steering artifacts before continuing.
- Resolve current-topic memory first and only fall back to the latest topic if that memory is missing.
- If the user names a known topic slug, preserve that slug and continue without asking for it again.
- Only ask the user to specify a topic manually when the topic reference is genuinely ambiguous.

The user experience target is: natural language first, AITP commands hidden in
the implementation path.

## Allowed exception

If the task is bucket `2`, you may work on the AITP codebase directly without
opening a topic shell, but you must preserve:

- the `L0 -> L1 -> L3-A -> L4 -> L3-R -> L3-D -> L2` ontology
- research-execution guardrails
- promotion and audit semantics
- adapter/runtime install consistency

## Red flags

These thoughts mean you are about to drift out of AITP discipline:

- "I'll just answer the research question directly first."
- "I only need a quick literature summary."
- "I can inspect files before deciding whether AITP applies."
- "This is probably too small to need runtime state."
- "I'll come back and register the topic later."

If one of those is true and the task is research-governed, stop and enter AITP
first.

## Practical rule

- Research task: route through AITP first.
- AITP repo maintenance task: edit code/docs/tests directly, but keep AITP
  contracts strict.
- When uncertain: bias toward entering AITP, not away from it.
"""

    def _claude_code_skill_template(self) -> str:
        session_start = self._session_start_routing_block(
            hidden_entry="the Claude SessionStart bootstrap, with fallback `aitp session-start \"<original request>\"` when you need to materialize routing explicitly"
        )
        return f"""---
name: aitp-runtime
description: Route Claude Code through the AITP runtime so natural-language research requests like `继续这个 topic`, new-topic creation, idea steering, and theory validation work become durable AITP state before execution.
---

# AITP Runtime For Claude Code

{session_start}

## Required entry

1. Let the Claude SessionStart bootstrap route natural-language research work into AITP before any substantial response. Use `aitp session-start "<task>"` only as the manual fallback.
2. Use `aitp loop ...` or `aitp resume ...` after AITP has materialized the topic shell.
3. Use `aitp bootstrap ...` only to create a new topic, then return to `aitp loop ...`.
4. Read `runtime_protocol.generated.md`, then follow its `Must read now` list before deeper work.
5. Treat `session_start.generated.md` as a routing audit artifact when it exists.
6. Ordinary topic work should stay in the light runtime profile unless a benchmark mismatch, scope change, promotion step, or explicit deep check forces the full profile.
7. Expand deferred surfaces only when the named trigger fires.
8. Treat missing conformance as a hard failure for AITP work.
9. Close with `aitp audit --topic-slug <topic_slug> --phase exit`.

## Hard rules

- Charter first, adapter second.
- Contracts before hidden heuristics.
- Do not silently upgrade exploratory output into reusable knowledge.
- Keep `innovation_direction.md` and `control_note.md` current before substantial execution continues.
- Use `aitp baseline ...`, `aitp atomize ...`, and `aitp trust-audit ...` before claiming method reuse.
- Do not expose protocol jargon in ordinary user-facing dialogue.

Kernel root default: `{self.kernel_root}`
"""

    def _opencode_skill_template(self) -> str:
        session_start = self._session_start_routing_block(
            hidden_entry="the OpenCode plugin bootstrap, with fallback `aitp session-start \"<original request>\"` when you need to materialize routing explicitly"
        )
        return f"""---
name: aitp-runtime
description: Route OpenCode through the AITP runtime so natural-language research requests like `继续这个 topic`, new-topic creation, idea steering, and theory validation work become durable AITP state before execution.
---

# AITP Runtime For OpenCode

{session_start}

## Required entry

1. Let the OpenCode plugin bootstrap route natural-language research work into AITP before any substantial response. Use `aitp session-start "<task>"` only as the manual fallback.
2. Use `aitp loop ...` or `aitp resume ...` after AITP has materialized the topic shell.
3. Use `aitp bootstrap ...` only to create a new topic, then return to `aitp loop ...`.
4. Read `runtime_protocol.generated.md`, then follow its `Must read now` list before deeper work.
5. Treat `session_start.generated.md` as a routing audit artifact when it exists.
6. Ordinary topic work should stay in the light runtime profile unless a benchmark mismatch, scope change, promotion step, or explicit deep check forces the full profile.
7. Expand deferred surfaces only when the named trigger fires.
8. Treat missing conformance as a hard failure for AITP work.
9. Close with `aitp audit --topic-slug <topic_slug> --phase exit`.

## Hard rules

- OpenCode should feel natural-language first, but routing must still become durable AITP state immediately.
- Keep `innovation_direction.md` and `control_note.md` current before substantial execution continues.
- Use `aitp baseline ...`, `aitp atomize ...`, and `aitp trust-audit ...` before claiming reusable method progress.
- Do not expose protocol jargon in ordinary user-facing dialogue.

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
                using_skill_base = base.parent / "using-aitp"
                using_skill_base.mkdir(parents=True, exist_ok=True)
                using_skill_path = using_skill_base / "SKILL.md"
                if using_skill_path.exists() and not force:
                    raise FileExistsError(f"Refusing to overwrite {using_skill_path}")
                write_text(
                    using_skill_path,
                    self._canonical_skill_text(
                        "using-aitp",
                        fallback_text=self._using_aitp_skill_template("codex"),
                    ),
                )
                installed.append({"agent": agent, "path": str(using_skill_path), "kind": "skill"})

                skill_path = base / "SKILL.md"
                if skill_path.exists() and not force:
                    raise FileExistsError(f"Refusing to overwrite {skill_path}")
                write_text(
                    skill_path,
                    self._canonical_skill_text(
                        "aitp-runtime",
                        fallback_text=self._codex_skill_template(),
                    ),
                )
                installed.append({"agent": agent, "path": str(skill_path), "kind": "skill"})

                if target_root or scope == "project":
                    setup_path = base / "AITP_MCP_SETUP.md"
                    write_text(setup_path, self._codex_mcp_setup_markdown())
                    installed.append({"agent": agent, "path": str(setup_path), "kind": "mcp-setup"})

            if install_mcp and not target_root and scope == "user":
                installed.extend(self._install_codex_mcp(force=force))
            return installed

        if agent == "openclaw":
            base = self._openclaw_skill_target(scope=scope, target_root=target_root)
            base.mkdir(parents=True, exist_ok=True)
            using_skill_base = base.parent / "using-aitp"
            using_skill_base.mkdir(parents=True, exist_ok=True)
            using_skill_path = using_skill_base / "SKILL.md"
            if using_skill_path.exists() and not force:
                raise FileExistsError(f"Refusing to overwrite {using_skill_path}")
            write_text(using_skill_path, self._using_aitp_skill_template("openclaw"))
            installed.append({"agent": agent, "path": str(using_skill_path), "kind": "skill"})

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
            target_base = self._agent_hidden_root(
                target_root=target_root,
                scope=scope,
                hidden_dir=".opencode",
                user_root=home / ".config" / "opencode",
                project_root=self.repo_root / ".opencode",
            )
            skill_base = target_base / "skills" / "aitp-runtime"
            using_skill_base = target_base / "skills" / "using-aitp"
            skill_base.mkdir(parents=True, exist_ok=True)
            using_skill_base.mkdir(parents=True, exist_ok=True)

            using_skill_path = using_skill_base / "SKILL.md"
            if using_skill_path.exists() and not force:
                raise FileExistsError(f"Refusing to overwrite {using_skill_path}")
            write_text(
                using_skill_path,
                self._canonical_skill_text(
                    "using-aitp",
                    fallback_text=self._using_aitp_skill_template("opencode"),
                ),
            )
            installed.append({"agent": agent, "path": str(using_skill_path), "kind": "skill"})

            skill_path = skill_base / "SKILL.md"
            if skill_path.exists() and not force:
                raise FileExistsError(f"Refusing to overwrite {skill_path}")
            write_text(
                skill_path,
                self._canonical_skill_text(
                    "aitp-runtime",
                    fallback_text=self._opencode_skill_template(),
                ),
            )
            installed.append({"agent": agent, "path": str(skill_path), "kind": "skill"})

            setup_path = skill_base / "AITP_MCP_SETUP.md"
            if setup_path.exists() and not force:
                raise FileExistsError(f"Refusing to overwrite {setup_path}")
            write_text(setup_path, self._opencode_mcp_setup_markdown(scope=scope, target_root=target_root))
            installed.append({"agent": agent, "path": str(setup_path), "kind": "mcp-setup"})

            installed.extend(self._install_opencode_plugin(scope=scope, target_root=target_root, force=force))

            if install_mcp:
                installed.extend(self._install_opencode_mcp(force=force, scope=scope, target_root=target_root))
            return installed

        if agent == "claude-code":
            target_base = self._agent_hidden_root(
                target_root=target_root,
                scope=scope,
                hidden_dir=".claude",
                user_root=home / ".claude",
                project_root=self.repo_root / ".claude",
            )
            skill_base = target_base / "skills" / "aitp-runtime"

            skill_base.mkdir(parents=True, exist_ok=True)
            using_skill_base = skill_base.parent / "using-aitp"
            using_skill_base.mkdir(parents=True, exist_ok=True)

            using_skill_path = using_skill_base / "SKILL.md"
            if using_skill_path.exists() and not force:
                raise FileExistsError(f"Refusing to overwrite {using_skill_path}")
            write_text(
                using_skill_path,
                self._canonical_skill_text(
                    "using-aitp",
                    fallback_text=self._using_aitp_skill_template("claude-code"),
                ),
            )
            installed.append({"agent": agent, "path": str(using_skill_path), "kind": "skill"})

            skill_path = skill_base / "SKILL.md"
            if skill_path.exists() and not force:
                raise FileExistsError(f"Refusing to overwrite {skill_path}")
            write_text(
                skill_path,
                self._canonical_skill_text(
                    "aitp-runtime",
                    fallback_text=self._claude_code_skill_template(),
                ),
            )
            installed.append({"agent": agent, "path": str(skill_path), "kind": "skill"})

            setup_path = skill_base / "AITP_MCP_SETUP.md"
            if setup_path.exists() and not force:
                raise FileExistsError(f"Refusing to overwrite {setup_path}")
            write_text(
                setup_path,
                "Register an `aitp` MCP server pointing to `aitp-mcp` in your Claude Code config if you want structured tool access.\n",
            )
            installed.append({"agent": agent, "path": str(setup_path), "kind": "mcp-setup"})
            installed.extend(self._install_claude_session_start_hook(scope=scope, target_root=target_root, force=force))
            return installed

        raise ValueError(f"Unsupported agent: {agent}")

    def ensure_cli_installed(self, *, workspace_root: str | None = None) -> dict[str, Any]:
        command_path = shutil.which("aitp")
        mcp_path = shutil.which("aitp-mcp")
        codex_path = shutil.which("codex")
        mcporter_path = shutil.which("mcporter")
        workspace_path = (
            Path(workspace_root).expanduser().resolve()
            if workspace_root
            else (self.repo_root.parents[1] / "Theoretical-Physics" if (self.repo_root.parents[1] / "Theoretical-Physics").exists() else Path.cwd().resolve())
        )
        pip_payload = self._pip_show_package("aitp-kernel")
        editable_location = str(pip_payload.get("editable project location") or "").strip()
        version = str(pip_payload.get("version") or "").strip()
        canonical_package_root = str(self._canonical_package_root().resolve())
        stale_cli = bool(editable_location) and Path(editable_location).resolve() != self._canonical_package_root().resolve()
        codex_skill_status = self._codex_skill_status()
        claude_hook_status = self._claude_hook_status()
        opencode_plugin_enabled, opencode_config_path, opencode_plugins = self._opencode_plugin_enabled()
        legacy_entrypoints = self._workspace_legacy_entrypoints(workspace_path)
        legacy_claude_commands = self._claude_legacy_command_paths()
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
            "formal_theory_automation_workflow": self.kernel_root / "FORMAL_THEORY_AUTOMATION_WORKFLOW.md",
            "section_formalization_protocol": self.kernel_root / "SECTION_FORMALIZATION_PROTOCOL.md",
            "formal_theory_upstream_reference_protocol": self.kernel_root / "FORMAL_THEORY_UPSTREAM_REFERENCE_PROTOCOL.md",
            "indexing_rules": self.kernel_root / "INDEXING_RULES.md",
            "l0_source_layer": self.kernel_root / "L0_SOURCE_LAYER.md",
        }
        issues: list[str] = []
        if stale_cli:
            issues.append("stale_cli")
        if legacy_entrypoints:
            issues.append("legacy_workspace_entrypoints_present")
        if not codex_skill_status["using_skill_present"] or not codex_skill_status["runtime_skill_present"]:
            issues.append("codex_skill_surface_missing")
        elif not codex_skill_status["using_skill_matches_canonical"] or not codex_skill_status["runtime_skill_matches_canonical"]:
            issues.append("codex_skill_surface_stale")
        if not all(claude_hook_status.values()):
            issues.append("claude_hook_surface_incomplete")
        if legacy_claude_commands:
            issues.append("claude_legacy_commands_present")
        if not opencode_plugin_enabled:
            issues.append("opencode_plugin_not_enabled")
        overall_status = "clean" if not issues else "mixed_install"
        return {
            "overall_status": overall_status,
            "issues": issues,
            "aitp": command_path,
            "aitp_mcp": mcp_path,
            "codex": codex_path,
            "mcporter": mcporter_path,
            "kernel_root": str(self.kernel_root),
            "repo_root": str(self.repo_root),
            "workspace_root": str(workspace_path),
            "package": {
                "name": "aitp-kernel",
                "version": version,
                "editable_project_location": editable_location,
                "canonical_package_root": canonical_package_root,
                "matches_canonical": not stale_cli and bool(editable_location),
            },
            "command_paths": {
                "aitp": command_path or "",
                "aitp_mcp": mcp_path or "",
            },
            "codex_skill_surface": codex_skill_status,
            "claude_hook_surface": {
                **claude_hook_status,
                "legacy_command_paths": [str(path) for path in legacy_claude_commands],
            },
            "opencode_plugin_surface": {
                "enabled": opencode_plugin_enabled,
                "config_path": str(opencode_config_path),
                "plugins": opencode_plugins,
            },
            "legacy_workspace_entrypoints": [str(path) for path in legacy_entrypoints],
            "layer_roots": layer_status,
            "protocol_contracts": {
                name: {"path": str(path), "status": "present" if path.exists() else "missing"}
                for name, path in contract_paths.items()
            },
        }

    def seed_l2_demo_direction(
        self,
        *,
        direction: str = "tfim-benchmark-first",
        updated_by: str = "aitp-cli",
    ) -> dict[str, Any]:
        return seed_l2_demo_graph_direction(self.kernel_root, direction=direction, updated_by=updated_by)

    def materialize_l2_index(self, *, updated_by: str = "aitp-cli") -> dict[str, Any]:
        payload = materialize_canonical_l2_index(self.kernel_root)
        payload["updated_by"] = updated_by
        return payload

    def consult_l2(
        self,
        *,
        query_text: str,
        retrieval_profile: str = "l3_candidate_formation",
        max_primary_hits: int | None = None,
        include_staging: bool = False,
        updated_by: str = "aitp-cli",
    ) -> dict[str, Any]:
        payload = consult_canonical_l2_graph(
            self.kernel_root,
            query_text=query_text,
            retrieval_profile=retrieval_profile,
            max_primary_hits=max_primary_hits,
            include_staging=include_staging,
        )
        payload["updated_by"] = updated_by
        return payload

    def consult_topic_l2(
        self,
        *,
        topic_slug: str,
        query_text: str,
        run_id: str | None = None,
        stage: str = "L3",
        retrieval_profile: str = "l3_candidate_formation",
        max_primary_hits: int | None = None,
        include_staging: bool = True,
        purpose: str | None = None,
        requested_unit_types: list[str] | None = None,
        updated_by: str = "aitp-cli",
    ) -> dict[str, Any]:
        resolved_run_id = self._resolve_run_id(topic_slug, run_id)
        retrieval_payload = consult_canonical_l2_graph(
            self.kernel_root,
            query_text=query_text,
            retrieval_profile=retrieval_profile,
            max_primary_hits=max_primary_hits,
            include_staging=include_staging,
        )
        profile_payload = (
            (read_json(self.kernel_root / "canonical" / "retrieval_profiles.json") or {}).get("profiles") or {}
        ).get(retrieval_profile) or {}
        preferred_types = set(profile_payload.get("preferred_unit_types") or [])

        def _canonical_reason(row: dict[str, Any]) -> str:
            matched_terms = [str(item).strip() for item in (row.get("matched_terms") or []) if str(item).strip()]
            parts: list[str] = []
            if matched_terms:
                parts.append(f"matched terms: {', '.join(matched_terms)}")
            if str(row.get("unit_type") or "") in preferred_types:
                parts.append("preferred by retrieval profile")
            return "; ".join(parts) or "selected by bounded lexical-plus-profile retrieval"

        def _expanded_reason(row: dict[str, Any]) -> str:
            via_relation = str(row.get("via_relation") or "").strip()
            via_id = str(row.get("via_id") or "").strip()
            if via_relation and via_id:
                return f"expanded via `{via_relation}` from `{via_id}`"
            return "expanded from a primary canonical hit"

        def _stage_reason(row: dict[str, Any]) -> str:
            matched_terms = [str(item).strip() for item in (row.get("matched_terms") or []) if str(item).strip()]
            if matched_terms:
                return f"matched staged distillation terms: {', '.join(matched_terms)}"
            return "matched a staged distillation entry"

        retrieved_refs: list[dict[str, Any]] = []
        primary_refs: list[dict[str, Any]] = []
        expanded_refs: list[dict[str, Any]] = []
        staged_refs: list[dict[str, Any]] = []
        warning_refs: list[dict[str, Any]] = []
        followup_paths: list[str] = []
        graph_surface = self._canonical_l2_graph_surface()

        for row in retrieval_payload.get("primary_hits") or []:
            ref = {
                "id": str(row.get("id") or ""),
                "unit_type": str(row.get("unit_type") or ""),
                "title": str(row.get("title") or ""),
                "summary": str(row.get("summary") or ""),
                "path": str(row.get("path") or ""),
                "trust_surface": "canonical",
                "selection_reason": _canonical_reason(row),
            }
            retrieved_refs.append(ref)
            primary_refs.append(ref)
            if ref["path"]:
                followup_paths.append(ref["path"])
            if ref["unit_type"] == "warning_note":
                warning_refs.append(ref)

        for row in retrieval_payload.get("expanded_hits") or []:
            ref = {
                "id": str(row.get("id") or ""),
                "unit_type": str(row.get("unit_type") or ""),
                "title": str(row.get("title") or ""),
                "summary": str(row.get("summary") or ""),
                "path": str(row.get("path") or ""),
                "trust_surface": "canonical",
                "selection_reason": _expanded_reason(row),
            }
            retrieved_refs.append(ref)
            expanded_refs.append(ref)
            if ref["path"]:
                followup_paths.append(ref["path"])
            if ref["unit_type"] == "warning_note":
                warning_refs.append(ref)

        for row in retrieval_payload.get("staged_hits") or []:
            ref = {
                "id": str(row.get("entry_id") or ""),
                "unit_type": str(row.get("candidate_unit_type") or ""),
                "title": str(row.get("title") or ""),
                "summary": str(row.get("summary") or ""),
                "path": str(row.get("path") or ""),
                "trust_surface": str(row.get("trust_surface") or "staging"),
                "selection_reason": _stage_reason(row),
            }
            retrieved_refs.append(ref)
            staged_refs.append(ref)
            if ref["path"]:
                followup_paths.append(ref["path"])

        canonical_hit_count = len(retrieval_payload.get("primary_hits") or []) + len(retrieval_payload.get("expanded_hits") or [])
        staged_hit_count = len(retrieval_payload.get("staged_hits") or [])
        result_summary = (
            f"Retrieved {len(retrieval_payload.get('primary_hits') or [])} primary canonical hits, "
            f"{len(retrieval_payload.get('expanded_hits') or [])} expanded canonical hits, and "
            f"{staged_hit_count} staged hits."
        )
        context_ref = {
            "topic_slug": topic_slug,
            "run_id": resolved_run_id or "",
            "surface": "topic_l2_consultation",
            "stage": stage,
        }
        consultation_slug = f"{stage.lower()}-{slugify(query_text)[:32]}-{slugify(now_iso())[-12:]}"
        projection_paths = [
            self._relativize(self._runtime_root(topic_slug) / "l2_memory.md"),
            self._relativize(self._l3_subplane_paths(topic_slug, "analysis")["note"]),
            self._relativize(self._l3_subplane_paths(topic_slug, "distillation")["note"]),
        ]
        if resolved_run_id:
            projection_paths.append(self._relativize(self._candidate_ledger_path(topic_slug, resolved_run_id)))
        consultation = self._record_l2_consultation(
            topic_slug=topic_slug,
            stage=stage,
            run_id=resolved_run_id,
            consultation_slug=consultation_slug,
            context_ref=context_ref,
            purpose=purpose or "Consult Layer 2 memory to shape the next bounded topic move without blurring canonical and staged trust.",
            query_text=query_text,
            requested_unit_types=list(requested_unit_types or []),
            retrieved_refs=retrieved_refs,
            primary_refs=primary_refs,
            expanded_refs=expanded_refs,
            staged_refs=staged_refs,
            warning_refs=warning_refs,
            graph_surface=graph_surface,
            result_summary=result_summary,
            effect_on_work=(
                "Consultation prepared reusable canonical and staged memory pointers for the active topic."
                if retrieved_refs
                else "No bounded reusable memory was retrieved for the active topic query."
            ),
            outcome="candidate_narrowed" if retrieved_refs else "no_change",
            projection_paths=self._dedupe_strings(projection_paths),
            requested_by=updated_by,
            produced_by=updated_by,
            written_by=updated_by,
            retrieval_profile=retrieval_profile,
        )
        return {
            **retrieval_payload,
            "topic_slug": topic_slug,
            "run_id": resolved_run_id or "",
            "stage": stage,
            "consultation": consultation,
            "trust_summary": {
                "canonical_hit_count": canonical_hit_count,
                "staged_hit_count": staged_hit_count,
            },
            "warning_refs": warning_refs,
            "followup_paths": self._dedupe_strings(followup_paths),
            "result_summary": result_summary,
            "updated_by": updated_by,
        }

    def stage_l2_insight(
        self,
        *,
        title: str,
        summary: str,
        candidate_unit_type: str = "concept",
        tags: list[str] | None = None,
        source_refs: list[str] | None = None,
        assumptions: list[str] | None = None,
        linked_unit_ids: list[str] | None = None,
        contradicts_unit_ids: list[str] | None = None,
        integration_summary: str | None = None,
        failure_kind: str | None = None,
        failed_route: str | None = None,
        next_implication: str | None = None,
        scope_note: str | None = None,
        topic_slug: str | None = None,
        notes: str | None = None,
        updated_by: str = "aitp-cli",
    ) -> dict[str, Any]:
        return stage_l2_graph_insight(
            self.kernel_root,
            title=title,
            summary=summary,
            candidate_unit_type=candidate_unit_type,
            tags=list(tags or []),
            source_refs=list(source_refs or []),
            created_by=updated_by,
            assumptions=list(assumptions or []),
            linked_unit_ids=list(linked_unit_ids or []),
            contradicts_unit_ids=list(contradicts_unit_ids or []),
            integration_summary=integration_summary,
            failure_kind=failure_kind,
            failed_route=failed_route,
            next_implication=next_implication,
            scope_note=scope_note,
            topic_slug=topic_slug,
            notes=notes,
        )

    def stage_negative_result(
        self,
        *,
        title: str,
        summary: str,
        failure_kind: str,
        failed_route: str | None = None,
        next_implication: str | None = None,
        tags: list[str] | None = None,
        source_refs: list[str] | None = None,
        assumptions: list[str] | None = None,
        contradicts_unit_ids: list[str] | None = None,
        scope_note: str | None = None,
        topic_slug: str | None = None,
        notes: str | None = None,
        updated_by: str = "aitp-cli",
    ) -> dict[str, Any]:
        return stage_l2_graph_insight(
            self.kernel_root,
            title=title,
            summary=summary,
            candidate_unit_type="negative_result",
            tags=self._dedupe_strings(["negative-result", *(tags or [])]),
            source_refs=list(source_refs or []),
            created_by=updated_by,
            assumptions=list(assumptions or []),
            linked_unit_ids=[],
            contradicts_unit_ids=list(contradicts_unit_ids or []),
            integration_summary=f"Recorded a negative-result memory candidate for `{failure_kind}`.",
            failure_kind=failure_kind,
            failed_route=failed_route,
            next_implication=next_implication,
            scope_note=scope_note,
            topic_slug=topic_slug,
            notes=notes,
        )

    def stage_topic_distillation(
        self,
        *,
        topic_slug: str,
        run_id: str | None = None,
        candidate_ids: list[str] | None = None,
        tags: list[str] | None = None,
        contradicts_unit_ids: list[str] | None = None,
        scope_note: str | None = None,
        notes: str | None = None,
        updated_by: str = "aitp-cli",
    ) -> dict[str, Any]:
        resolved_run_id = self._resolve_run_id(topic_slug, run_id)
        if not resolved_run_id:
            raise FileNotFoundError(f"Unable to resolve a feedback run for topic {topic_slug}")

        candidate_rows = self._candidate_rows_for_run(topic_slug, resolved_run_id)
        if not candidate_rows:
            return {
                "topic_slug": topic_slug,
                "run_id": resolved_run_id,
                "status": "no_candidates",
                "selection_basis": "none",
                "staged_entry_ids": [],
                "staged_entries": [],
            }

        promotion_gate = self._load_promotion_gate(topic_slug) or {}
        promotion_readiness = self._derive_promotion_readiness(
            topic_slug=topic_slug,
            latest_run_id=resolved_run_id,
            promotion_gate=promotion_gate,
            candidate_rows=candidate_rows,
        )
        requested_ids = {str(item).strip() for item in (candidate_ids or []) if str(item).strip()}
        selected_rows: list[dict[str, Any]] = []
        selection_basis = "candidate_ledger_distillation"

        if requested_ids:
            selected_rows = [
                row
                for row in candidate_rows
                if str(row.get("candidate_id") or "").strip() in requested_ids
            ]
            missing_ids = sorted(requested_ids - {str(row.get("candidate_id") or "").strip() for row in selected_rows})
            if missing_ids:
                raise FileNotFoundError(
                    f"Topic distillation staging could not find candidate ids: {', '.join(missing_ids)}"
                )
            selection_basis = "explicit_candidate_ids"
        else:
            ready_ids = set(promotion_readiness.get("ready_candidate_ids") or [])
            if ready_ids:
                selected_rows = [
                    row for row in candidate_rows if str(row.get("candidate_id") or "").strip() in ready_ids
                ]
                selection_basis = "promotion_ready_candidates"
            else:
                selected_rows = [
                    row
                    for row in candidate_rows
                    if (row.get("intended_l2_targets") or [])
                    or str(row.get("status") or "").strip() in {"ready_for_validation", "promotion-ready", "validated"}
                ]
                if not selected_rows:
                    selected_rows = [candidate_rows[0]]

        result_brief = read_json(self._result_brief_paths(topic_slug)["json"]) or {}
        topic_state = read_json(self._runtime_root(topic_slug) / "topic_state.json") or {"topic_slug": topic_slug}
        validation_contract = read_json(self._validation_contract_paths(topic_slug)["json"]) or {}
        last_evidence_return = self._derive_last_evidence_return(
            topic_state=topic_state,
            validation_contract=validation_contract,
        )
        if not str(last_evidence_return.get("path") or "").strip():
            fallback_return_path = self._validation_run_root(topic_slug, resolved_run_id) / "returned_execution_result.json"
            if fallback_return_path.exists():
                fallback_payload = read_json(fallback_return_path) or {}
                last_evidence_return = {
                    "status": "present",
                    "kind": "returned_execution_result",
                    "record_id": str(fallback_payload.get("result_id") or "").strip(),
                    "recorded_at": str(fallback_payload.get("updated_at") or fallback_payload.get("returned_at") or "").strip(),
                    "path": self._relativize(fallback_return_path),
                    "summary": str(fallback_payload.get("summary") or "").strip(),
                }
        ledger_ref = self._relativize(self._candidate_ledger_path(topic_slug, resolved_run_id))
        result_brief_ref = ""
        if self._result_brief_paths(topic_slug)["json"].exists():
            result_brief_ref = self._relativize(self._result_brief_paths(topic_slug)["json"])
        evidence_ref = str(last_evidence_return.get("path") or "").strip()

        staged_entries: list[dict[str, Any]] = []
        for row in selected_rows:
            candidate_id = str(row.get("candidate_id") or "").strip()
            candidate_type = str(row.get("candidate_type") or "concept").strip() or "concept"
            source_refs = self._dedupe_strings(
                [
                    ledger_ref,
                    *self._origin_ref_strings(list(row.get("origin_refs") or [])),
                    result_brief_ref,
                    evidence_ref,
                ]
            )
            integration_parts = [
                str(result_brief.get("what_changed") or "").strip(),
                str(last_evidence_return.get("summary") or "").strip(),
                str(promotion_readiness.get("summary") or "").strip(),
            ]
            integration_summary = " ".join(part for part in integration_parts if part).strip()
            entry = stage_l2_graph_insight(
                self.kernel_root,
                title=str(row.get("title") or candidate_id or f"{topic_slug} distillation"),
                summary=str(row.get("summary") or "Topic-side distillation candidate."),
                candidate_unit_type=candidate_type,
                tags=self._dedupe_strings([topic_slug, candidate_type, *list(tags or [])]),
                source_refs=source_refs,
                created_by=updated_by,
                assumptions=self._dedupe_strings(list(row.get("assumptions") or [])),
                linked_unit_ids=self._dedupe_strings(list(row.get("intended_l2_targets") or [])),
                contradicts_unit_ids=self._dedupe_strings(list(contradicts_unit_ids or [])),
                integration_summary=integration_summary,
                scope_note=scope_note or str(row.get("question") or row.get("proposed_validation_route") or ""),
                topic_slug=topic_slug,
                notes=notes or f"Created from topic distillation for {candidate_id or topic_slug}.",
            )
            staged_entries.append(entry)

        return {
            "topic_slug": topic_slug,
            "run_id": resolved_run_id,
            "status": "staged",
            "selection_basis": selection_basis,
            "promotion_readiness_status": str(promotion_readiness.get("status") or ""),
            "staged_entry_ids": [str(row.get("entry_id") or "") for row in staged_entries],
            "staged_entries": staged_entries,
            "result_brief_path": result_brief_ref,
            "evidence_path": evidence_ref,
        }

    def migrate_local_install(
        self,
        *,
        workspace_root: str,
        backup_root: str | None = None,
        agents: list[str] | None = None,
        with_mcp: bool = False,
    ) -> dict[str, Any]:
        workspace_path = Path(workspace_root).expanduser().resolve()
        timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
        resolved_backup_root = (
            Path(backup_root).expanduser().resolve()
            if backup_root
            else (workspace_path / "archive" / "aitp-local-migration" / timestamp).resolve()
        )
        resolved_backup_root.mkdir(parents=True, exist_ok=True)

        before = self.ensure_cli_installed(workspace_root=str(workspace_path))
        backup_log: list[dict[str, str]] = []
        for path in self._workspace_legacy_entrypoints(workspace_path):
            backup_log.append(self._backup_and_move(path, resolved_backup_root, "workspace-root-legacy"))
        for path in self._claude_legacy_command_paths():
            backup_log.append(self._backup_and_move(path, resolved_backup_root, "claude-legacy-commands"))

        pip_before = self._pip_show_package("aitp-kernel")
        editable_location = str(pip_before.get("editable project location") or "").strip()
        canonical_package_root = self._canonical_package_root().resolve()
        pip_actions: list[dict[str, Any]] = []
        if not editable_location or Path(editable_location).resolve() != canonical_package_root:
            uninstall_cmd = [sys.executable, "-m", "pip", "uninstall", "-y", "aitp-kernel"]
            uninstall_run = subprocess.run(uninstall_cmd, check=False, capture_output=True, text=True)
            pip_actions.append(
                {
                    "step": "uninstall_old_aitp_kernel",
                    "command": uninstall_cmd,
                    "returncode": uninstall_run.returncode,
                    "stdout": uninstall_run.stdout.strip(),
                    "stderr": uninstall_run.stderr.strip(),
                }
            )
            install_cmd = [sys.executable, "-m", "pip", "install", "-e", str(canonical_package_root)]
            install_run = subprocess.run(install_cmd, check=False, capture_output=True, text=True)
            if install_run.returncode != 0:
                raise RuntimeError(install_run.stderr.strip() or install_run.stdout.strip() or "pip install failed")
            pip_actions.append(
                {
                    "step": "install_canonical_aitp_kernel",
                    "command": install_cmd,
                    "returncode": install_run.returncode,
                    "stdout": install_run.stdout.strip(),
                    "stderr": install_run.stderr.strip(),
                }
            )

        refreshed_agents = agents or ["codex", "claude-code", "opencode"]
        installed_assets: list[dict[str, str]] = []
        for agent in refreshed_agents:
            installed_assets.extend(
                self.install_agent(
                    agent=agent,
                    scope="user",
                    force=True,
                    install_mcp=with_mcp,
                )["installed"]
            )
        opencode_plugin_update = self._ensure_opencode_plugin_enabled()
        after = self.ensure_cli_installed(workspace_root=str(workspace_path))
        return {
            "status": "success",
            "workspace_root": str(workspace_path),
            "backup_root": str(resolved_backup_root),
            "backup_log": backup_log,
            "pip_before": pip_before,
            "pip_actions": pip_actions,
            "installed_assets": installed_assets,
            "opencode_plugin_update": opencode_plugin_update,
            "doctor_before": before,
            "doctor_after": after,
        }
