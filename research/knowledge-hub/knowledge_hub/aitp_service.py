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
from .aitp_mcp_profiles import normalize_mcp_profile, server_name_for_mcp_profile
from .agent_install_support import (
    agent_hidden_root as resolve_agent_hidden_root,
    install_agent as perform_install_agent,
    install_claude_mcp as perform_claude_mcp_install,
    install_claude_session_start_hook as perform_claude_session_start_hook_install,
    install_codex_mcp as perform_codex_mcp_install,
    install_one_agent as perform_install_one_agent,
    install_opencode_mcp as perform_opencode_mcp_install,
    install_opencode_plugin as perform_opencode_plugin_install,
    install_openclaw_mcp as perform_openclaw_mcp_install,
    openclaw_skill_target as resolve_openclaw_skill_target,
)
from .frontdoor_support import (
    claude_hook_status as compute_claude_hook_status,
    claude_legacy_command_paths as discover_claude_legacy_command_paths,
    claude_mcp_status as compute_claude_mcp_status,
    claude_settings_has_expected_session_start_command as check_claude_settings_session_start_command,
    codex_skill_status as compute_codex_skill_status,
    ensure_cli_installed as compute_cli_install_status,
    ensure_opencode_plugin_enabled as enable_opencode_plugin_entry,
    migrate_local_install as perform_local_install_migration,
    opencode_plugin_enabled as detect_opencode_plugin_enabled,
    opencode_plugin_status as compute_opencode_plugin_status,
    pip_show_package as query_pip_show_package,
    runtime_convergence_summary as compute_runtime_convergence_summary,
    workspace_legacy_entrypoints as discover_workspace_legacy_entrypoints,
)
from .kernel_templates import (
    claude_code_skill_template,
    codex_skill_template,
    openclaw_skill_template,
    opencode_skill_template,
    render_session_start_note,
    using_aitp_skill_template,
)
from .runtime_bundle_support import (
    materialize_runtime_protocol_bundle,
    materialize_session_start_contract,
    runtime_protocol_markdown,
)
from .collaborator_profile_support import load_collaborator_profile
from .exploration_session_support import build_exploration_promotion_request, build_exploration_session_payload, load_exploration_session, materialize_exploration_promotion_request, materialize_exploration_session
from .mode_learning_support import load_mode_learning
from .research_trajectory_support import load_research_trajectory
from .research_taste_support import (
    record_research_taste_payload,
    topic_research_taste_payload,
)
from .scratchpad_support import (
    record_negative_result_payload,
    record_scratch_note_payload,
    topic_scratchpad_payload,
)
from .l2_consultation_support import build_l2_consultation_record, consultation_projection_path
from .topic_shell_support import (
    compute_topic_completion_payload,
    derive_idea_packet,
    derive_open_gap_summary,
    derive_operator_checkpoint,
    ensure_topic_shell_surfaces,
    render_topic_dashboard_markdown,
)
from .topic_status_explainability_support import derive_topic_status_explainability
from .followup_support import (
    apply_candidate_split_contract,
    buffer_entry_ready_for_reactivation,
    deferred_buffer_markdown,
    followup_gap_writeback_markdown,
    followup_reintegration_markdown,
    followup_return_packet_markdown,
    followup_subtopics_markdown,
    load_deferred_buffer,
    load_followup_gap_writeback_rows,
    load_followup_reintegration_rows,
    load_followup_subtopic_rows,
    reactivate_deferred_candidates,
    reactivation_context,
    reintegrate_followup_subtopic,
    return_shape_for_status,
    spawn_followup_subtopics,
    update_followup_return_packet,
    write_deferred_buffer,
    write_followup_gap_writeback_rows,
    write_followup_reintegration_rows,
    write_followup_return_packet,
    write_followup_subtopic_rows,
)
from .kernel_markdown_renderers import (
    render_control_note_markdown,
    render_current_topic_note,
    render_gap_map_markdown,
    render_idea_packet_markdown,
    render_lean_bridge_index_markdown,
    render_lean_bridge_packet_markdown,
    render_operator_checkpoint_markdown,
    render_proof_repair_plan_markdown,
    render_proof_obligations_markdown,
    render_proof_state_markdown,
    render_promotion_readiness_markdown,
    render_research_question_contract_markdown,
    render_statement_compilation_index_markdown,
    render_statement_compilation_packet_markdown,
    render_topic_family_reuse_note,
    render_topic_skill_projection_markdown,
    render_validation_contract_markdown,
)
from .runtime_projection_handler import (
    build_knowledge_packets_from_candidates,
    write_pending_decisions_projection,
    write_promotion_readiness_projection,
    write_promotion_trace,
    write_topic_skill_projection,
    write_topic_synopsis,
)
from .compat_surface_cleanup_support import prune_compat_surfaces as perform_prune_compat_surfaces
from .runtime_path_support import resolve_runtime_reference_path
from .subprocess_error_support import format_subprocess_failure
from .topic_runtime_surface_support import (
    materialize_layer_graph_artifact,
    runtime_surface_roles,
    topic_layer_graph_payload,
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
from .runtime_truth_service import RuntimeTruthService
from .runtime_support_matrix import build_runtime_support_matrix
from .validation_review_service import ValidationReviewService
from .auto_action_support import execute_auto_actions
from .auto_promotion_support import auto_promote_candidate
from .analytical_review_support import audit_analytical_review as perform_analytical_review_audit
from .candidate_promotion_support import promote_candidate
from .formal_theory_audit_support import audit_formal_theory as perform_formal_theory_audit
from .lean_bridge_support import materialize_lean_bridge
from .statement_compilation_support import materialize_statement_compilation
from .h_plane_support import h_plane_audit as perform_h_plane_audit
from .paired_backend_support import paired_backend_audit as perform_paired_backend_audit
from .capability_audit_support import capability_audit as perform_capability_audit
from .chat_session_support import (
    route_codex_chat_request as route_chat_request,
    start_chat_session as start_codex_chat_session,
)
from .theory_metrics import (
    candidate_metric_context,
    analyze_theory_metrics as perform_theory_metrics_analysis,
    record_analytical_review_metric,
    record_candidate_promotion_metric,
    record_conformance_metric,
    record_coverage_metric,
    record_formal_theory_metric,
    record_promotion_gate_metric,
    record_theory_operation_metric as perform_record_theory_operation_metric,
    record_topic_completion_metric,
)
from .source_distillation_support import distill_from_sources
from .theory_coverage_audit_support import audit_theory_coverage as perform_theory_coverage_audit
from .topic_loop_support import run_topic_loop as execute_topic_loop
from .topic_skill_projection_support import derive_topic_skill_projection
from .promotion_gate_support import (
    append_promotion_gate_log,
    approve_promotion,
    load_promotion_gate,
    promotion_gate_markdown,
    reject_promotion,
    request_promotion,
    write_promotion_gate,
)
from .l2_graph import consult_canonical_l2, seed_l2_demo_direction
from .literature_intake_support import (
    derive_literature_stage_payload_from_runtime_payload,
    stage_literature_units,
)
from .l2_compiler import (
    materialize_workspace_graph_report,
    materialize_workspace_knowledge_report,
    materialize_workspace_memory_map,
)
from .l2_hygiene import materialize_workspace_hygiene_report
from .source_catalog import materialize_source_catalog, materialize_source_citation_traversal, materialize_source_family_report
from .source_bibtex_support import import_bibtex_sources as materialize_bibtex_source_import, materialize_source_bibtex_export
from .obsidian_graph_bridge_support import sync_concept_graph_export_to_theoretical_physics_brain
from .semantic_routing import canonical_validation_mode
from .bundle_support import (
    LEGACY_PACKAGE_DISTRIBUTION_NAMES,
    PACKAGE_DISTRIBUTION_NAME,
    default_user_kernel_root,
    ensure_materialized_kernel_root,
    package_bundle_available,
    package_distribution_names,
)


def _looks_like_repo_root(path: Path) -> bool:
    return (
        (path / "AGENTS.md").exists()
        and (path / "docs" / "CHARTER.md").exists()
        and (path / "research" / "knowledge-hub" / "setup.py").exists()
    )


def _looks_like_kernel_root(path: Path) -> bool:
    if (path / "runtime" / "scripts" / "orchestrate_topic.py").exists():
        return True
    return (
        (path / "runtime" / "schemas" / "progressive-disclosure-runtime-bundle.schema.json").exists()
        and (path / "schemas").exists()
    )


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

    if package_bundle_available():
        return default_user_kernel_root()

    return repo_candidate


DEFAULT_KERNEL_ROOT = _detect_default_kernel_root()


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def slugify(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-+", "-", lowered).strip("-")
    return lowered or "aitp-topic"


def bounded_slugify(text: str, *, max_length: int = 32) -> str:
    slug = slugify(text)
    if len(slug) <= max_length:
        return slug
    digest = hashlib.sha1(slug.encode("utf-8")).hexdigest()[:8]
    head = slug[: max(8, max_length - len(digest) - 1)].rstrip("-")
    return f"{head}-{digest}"


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
            detected_repo_root = _detect_repo_root().resolve()
            if _looks_like_repo_root(detected_repo_root):
                self.repo_root = detected_repo_root
        if not _looks_like_kernel_root(self.kernel_root) and package_bundle_available():
            self.kernel_root = ensure_materialized_kernel_root(self.kernel_root)
        if not _looks_like_kernel_root(self.kernel_root):
            repo_candidate = (self.repo_root / "research" / "knowledge-hub").resolve()
            if _looks_like_kernel_root(repo_candidate):
                self.kernel_root = repo_candidate
        self._runtime_truth_service = RuntimeTruthService(self)
        self._validation_review_service = ValidationReviewService(
            self,
            read_json=read_json,
            now_iso=now_iso,
        )

    def _kernel_script(self, relative_path: str) -> Path:
        script_path = self.kernel_root / relative_path
        if not script_path.exists():
            raise FileNotFoundError(f"Missing kernel script: {script_path}")
        return script_path

    def _run(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(argv, check=False, capture_output=True, text=True)
        if completed.returncode != 0:
            raise RuntimeError(
                format_subprocess_failure(
                    argv,
                    returncode=completed.returncode,
                    stdout=completed.stdout,
                    stderr=completed.stderr,
                    context="aitp-service command",
                )
            )
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

    def _mcp_environment(self, *, mcp_profile: str = "full") -> dict[str, str]:
        environment = dict(self._runtime_environment())
        resolved_profile = normalize_mcp_profile(mcp_profile)
        if resolved_profile != "full":
            environment["AITP_MCP_PROFILE"] = resolved_profile
        return environment

    def _mcp_server_name(self, mcp_profile: str = "full") -> str:
        return server_name_for_mcp_profile(mcp_profile)

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
            return self.repo_root if _looks_like_repo_root(self.repo_root) else Path.cwd().resolve()

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
        runtime_root = self.kernel_root / "runtime"
        return {
            "jsonl": runtime_root / "collaborator_memory.jsonl",
            "note": runtime_root / "collaborator_memory.md",
        }

    def _active_topics_registry_paths(self) -> dict[str, Path]:
        runtime_root = self.kernel_root / "runtime"
        return {
            "json": runtime_root / "active_topics.json",
            "note": runtime_root / "active_topics.md",
        }

    def _topic_family_reuse_paths(self) -> dict[str, Path]:
        runtime_root = self.kernel_root / "runtime"
        return {
            "json": runtime_root / "topic_family_reuse.json",
            "note": runtime_root / "topic_family_reuse.md",
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
        if _looks_like_repo_root(self.repo_root):
            return self.repo_root / "research" / "knowledge-hub"
        return Path(__file__).resolve().parents[1]

    def _package_distribution_names(self) -> tuple[str, ...]:
        return package_distribution_names()

    def _primary_package_distribution_name(self) -> str:
        return PACKAGE_DISTRIBUTION_NAME

    def _legacy_package_distribution_names(self) -> tuple[str, ...]:
        return LEGACY_PACKAGE_DISTRIBUTION_NAMES

    def _has_repo_checkout(self) -> bool:
        return _looks_like_repo_root(self.repo_root)

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
        return query_pip_show_package(package_name)

    def _text_matches_canonical(self, path: Path, canonical_relative_path: str) -> bool:
        canonical_path = self.repo_root / canonical_relative_path
        if not path.exists() or not canonical_path.exists():
            return False
        return path.read_text(encoding="utf-8") == canonical_path.read_text(encoding="utf-8")

    def _workspace_legacy_entrypoints(self, workspace_root: Path) -> list[Path]:
        return discover_workspace_legacy_entrypoints(workspace_root)

    def _claude_legacy_command_paths(self) -> list[Path]:
        return discover_claude_legacy_command_paths()

    def _ensure_opencode_plugin_enabled(self) -> dict[str, Any]:
        return enable_opencode_plugin_entry()

    def _opencode_plugin_enabled(self) -> tuple[bool, Path, list[str]]:
        return detect_opencode_plugin_enabled()

    def _opencode_plugin_status(self, workspace_root: Path | None = None) -> dict[str, Any]:
        return compute_opencode_plugin_status(repo_root=self.repo_root, workspace_root=workspace_root)

    def _claude_settings_has_expected_session_start_command(self, settings_path: Path, run_hook_path: Path) -> bool:
        return check_claude_settings_session_start_command(settings_path, run_hook_path)

    def _claude_hook_status(self) -> dict[str, Any]:
        return compute_claude_hook_status(repo_root=self.repo_root)

    def _claude_mcp_status(self, workspace_root: Path | None = None) -> dict[str, Any]:
        return compute_claude_mcp_status(self, workspace_root=workspace_root)

    def _codex_skill_status(self) -> dict[str, Any]:
        return compute_codex_skill_status(repo_root=self.repo_root)

    def _backup_and_move(self, path: Path, backup_root: Path, backup_subdir: str) -> dict[str, str]:
        destination = backup_root / backup_subdir / path.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(destination))
        return {"original_path": str(path), "backup_path": str(destination)}

    def _runtime_convergence_summary(self, doctor_payload: dict[str, Any]) -> dict[str, Any]:
        return compute_runtime_convergence_summary(doctor_payload)

    def _operation_id(self, value: str) -> str:
        if value.startswith("operation:"):
            return value
        return f"operation:{slugify(value)}"

    def _operation_slug(self, operation_id: str) -> str:
        return bounded_slugify(operation_id.split(":", 1)[-1])

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

    def _topic_synopsis_path(self, topic_slug: str) -> Path:
        return self._runtime_root(topic_slug) / "topic_synopsis.json"

    def _promotion_readiness_path(self, topic_slug: str) -> Path:
        return self._runtime_root(topic_slug) / "promotion_readiness.md"

    def _validation_review_bundle_paths(self, topic_slug: str) -> dict[str, Path]:
        runtime_root = self._runtime_root(topic_slug)
        return {
            "json": runtime_root / "validation_review_bundle.active.json",
            "note": runtime_root / "validation_review_bundle.active.md",
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

    def _statement_compilation_active_paths(self, topic_slug: str) -> dict[str, Path]:
        runtime_root = self._runtime_root(topic_slug)
        return {
            "json": runtime_root / "statement_compilation.active.json",
            "note": runtime_root / "statement_compilation.active.md",
        }

    def _statement_compilation_packet_paths(self, topic_slug: str, run_id: str, candidate_id: str) -> dict[str, Path]:
        root = self._validation_run_root(topic_slug, run_id) / "statement-compilation" / bounded_slugify(candidate_id)
        return {
            "root": root,
            "json": root / "statement_compilation.json",
            "note": root / "statement_compilation.md",
            "repair_plan": root / "proof_repair_plan.json",
            "repair_plan_note": root / "proof_repair_plan.md",
        }

    def _lean_bridge_packet_paths(self, topic_slug: str, run_id: str, candidate_id: str) -> dict[str, Path]:
        root = self._validation_run_root(topic_slug, run_id) / "lean-bridge" / bounded_slugify(candidate_id)
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

    def analyze_theory_metrics(
        self,
        *,
        topic_slug: str | None = None,
        updated_by: str = "aitp-cli",
    ) -> dict[str, Any]:
        return perform_theory_metrics_analysis(
            self,
            topic_slug=topic_slug,
            updated_by=updated_by,
        )

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
        return "formal" if normalized == "formal_theory" else "numerical" if normalized == "toy_numeric" else "hybrid"
    def _validation_mode_for_modes(self, *, template_mode: str | None, research_mode: str | None) -> str: return canonical_validation_mode(template_mode, research_mode)

    def _lane_for_modes(self, *, template_mode: str | None, research_mode: str | None) -> str:
        normalized_template = str(template_mode or "").strip().lower()
        normalized_research = str(research_mode or "").strip().lower()
        if normalized_template == "formal_theory" or normalized_research == "formal_derivation":
            return "formal_theory"
        if normalized_template == "toy_numeric" or normalized_research in {"toy_model", "first_principles"}:
            return "toy_numeric"
        return "code_method"

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

    def _load_collaborator_memory_rows(self) -> list[dict[str, Any]]:
        path = self._collaborator_memory_paths()["jsonl"]
        rows: list[dict[str, Any]] = []
        for raw_row in read_jsonl(path):
            if not isinstance(raw_row, dict):
                continue
            row = dict(raw_row)
            row["memory_id"] = str(row.get("memory_id") or "")
            row["recorded_at"] = str(row.get("recorded_at") or "")
            row["memory_kind"] = str(row.get("memory_kind") or "")
            row["summary"] = str(row.get("summary") or "")
            row["details"] = str(row.get("details") or "")
            row["topic_slug"] = str(row.get("topic_slug") or "")
            row["run_id"] = str(row.get("run_id") or "")
            row["tags"] = self._dedupe_strings([str(item) for item in (row.get("tags") or [])])
            row["related_topic_slugs"] = self._dedupe_strings(
                [str(item) for item in (row.get("related_topic_slugs") or [])]
            )
            row["updated_by"] = str(row.get("updated_by") or "")
            row["memory_domain"] = "collaborator"
            row["storage_layer"] = "runtime"
            row["canonical_status"] = "separate_from_scientific_memory"
            rows.append(row)
        rows.sort(
            key=lambda item: (
                str(item.get("recorded_at") or ""),
                str(item.get("memory_id") or ""),
            ),
            reverse=True,
        )
        return rows

    def _collaborator_memory_matches_topic(self, row: dict[str, Any], topic_slug: str | None) -> bool:
        normalized = str(topic_slug or "").strip()
        if not normalized:
            return True
        if str(row.get("topic_slug") or "").strip() == normalized:
            return True
        return normalized in {
            str(item).strip()
            for item in (row.get("related_topic_slugs") or [])
            if str(item).strip()
        }

    def _render_collaborator_memory_note(self, payload: dict[str, Any]) -> str:
        lines = [
            "# Collaborator memory",
            "",
            "This ledger stores runtime-side collaborator memory only.",
            "It is not canonical scientific memory, not Layer 2, and not a promotion surface.",
            "",
            f"- Status: `{payload.get('status') or '(missing)'}`",
            f"- Storage layer: `{payload.get('storage_layer') or '(missing)'}`",
            f"- Canonical status: `{payload.get('canonical_status') or '(missing)'}`",
            f"- Row count: `{payload.get('row_count') or 0}`",
            f"- Matching count: `{payload.get('matching_count') or 0}`",
            "",
            str(payload.get("summary") or "(missing)"),
        ]
        entries = payload.get("entries") or []
        if not entries:
            lines.extend(["", "No collaborator-memory rows are currently recorded."])
            return "\n".join(lines).strip() + "\n"
        lines.extend(["", "## Recent entries"])
        for index, row in enumerate(entries, start=1):
            topic_label = str(row.get("topic_slug") or "").strip() or "workspace"
            lines.extend(
                [
                    "",
                    f"### {index}. {row.get('memory_kind') or 'memory'}",
                    f"- Topic: `{topic_label}`",
                    f"- Run id: `{row.get('run_id') or '(none)'}`",
                    f"- Summary: {row.get('summary') or '(missing)'}",
                    f"- Tags: {', '.join(row.get('tags') or []) or '(none)'}",
                    f"- Related topics: {', '.join(row.get('related_topic_slugs') or []) or '(none)'}",
                    f"- Updated by: `{row.get('updated_by') or '(missing)'}`",
                ]
            )
            details = str(row.get("details") or "").strip()
            if details:
                lines.append(f"- Details: {details}")
        return "\n".join(lines).strip() + "\n"

    def _build_collaborator_memory_payload(
        self,
        *,
        topic_slug: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        paths = self._collaborator_memory_paths()
        rows = self._load_collaborator_memory_rows()
        matching_rows = [
            row
            for row in rows
            if self._collaborator_memory_matches_topic(row, topic_slug)
        ]
        normalized_topic_slug = str(topic_slug or "").strip() or None
        status = "available" if rows else "absent"
        if not rows:
            summary = "No collaborator memory is currently recorded in the runtime ledger."
        elif normalized_topic_slug:
            summary = (
                f"{len(matching_rows)} collaborator-memory row(s) match topic `{normalized_topic_slug}` "
                f"out of {len(rows)} total runtime-side rows."
            )
        else:
            summary = f"{len(rows)} collaborator-memory row(s) are recorded in the runtime ledger."
        return {
            "memory_domain": "collaborator",
            "storage_layer": "runtime",
            "canonical_status": "separate_from_scientific_memory",
            "status": status,
            "topic_slug": normalized_topic_slug,
            "row_count": len(rows),
            "matching_count": len(matching_rows),
            "memory_kinds": sorted(
                {
                    str(row.get("memory_kind") or "").strip()
                    for row in matching_rows
                    if str(row.get("memory_kind") or "").strip()
                }
            ),
            "collaborator_memory_path": str(paths["jsonl"]),
            "collaborator_memory_note_path": str(paths["note"]),
            "entries": matching_rows[: max(1, limit)],
            "summary": summary,
        }

    def get_collaborator_memory(
        self,
        *,
        topic_slug: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        return self._build_collaborator_memory_payload(topic_slug=topic_slug, limit=limit)

    def record_collaborator_memory(
        self,
        *,
        memory_kind: str,
        summary: str,
        updated_by: str = "aitp-cli",
        details: str | None = None,
        topic_slug: str | None = None,
        run_id: str | None = None,
        tags: list[str] | None = None,
        related_topic_slugs: list[str] | None = None,
    ) -> dict[str, Any]:
        valid_memory_kinds = {
            "preference",
            "trajectory",
            "working_style",
            "stuckness",
            "surprise",
            "coordination",
        }
        normalized_kind = str(memory_kind or "").strip()
        if normalized_kind not in valid_memory_kinds:
            raise ValueError(f"memory_kind must be one of {sorted(valid_memory_kinds)}")
        normalized_summary = str(summary or "").strip()
        if not normalized_summary:
            raise ValueError("summary must not be empty")

        normalized_topic_slug = str(topic_slug or "").strip()
        normalized_run_id = str(run_id or "").strip()
        recorded_at = now_iso()
        normalized_related_topics = self._dedupe_strings(
            [str(item) for item in (related_topic_slugs or [])]
            + ([normalized_topic_slug] if normalized_topic_slug else [])
        )
        row = {
            "memory_id": f"collab-{slugify(normalized_kind)}-{slugify(recorded_at)}",
            "recorded_at": recorded_at,
            "memory_domain": "collaborator",
            "storage_layer": "runtime",
            "canonical_status": "separate_from_scientific_memory",
            "memory_kind": normalized_kind,
            "summary": normalized_summary,
            "details": str(details or "").strip(),
            "topic_slug": normalized_topic_slug,
            "run_id": normalized_run_id,
            "tags": self._dedupe_strings([str(item) for item in (tags or [])]),
            "related_topic_slugs": normalized_related_topics,
            "updated_by": updated_by,
        }
        path = self._collaborator_memory_paths()["jsonl"]
        rows = read_jsonl(path)
        rows.append(row)
        write_jsonl(path, rows)
        note_payload = self._build_collaborator_memory_payload(limit=20)
        write_text(
            self._collaborator_memory_paths()["note"],
            self._render_collaborator_memory_note(note_payload),
        )
        return {
            "memory_domain": "collaborator",
            "storage_layer": "runtime",
            "canonical_status": "separate_from_scientific_memory",
            "collaborator_memory_path": str(path),
            "collaborator_memory_note_path": str(self._collaborator_memory_paths()["note"]),
            "collaborator_memory_entry": row,
        }

    def record_research_taste(self, **kwargs: Any) -> dict[str, Any]: return record_research_taste_payload(self, **kwargs)

    def topic_research_taste(self, *, topic_slug: str, updated_by: str = "aitp-cli") -> dict[str, Any]: return topic_research_taste_payload(self, topic_slug=topic_slug, updated_by=updated_by)

    def record_scratch_note(self, **kwargs: Any) -> dict[str, Any]: return record_scratch_note_payload(self, **kwargs)

    def record_negative_result(self, **kwargs: Any) -> dict[str, Any]: return record_negative_result_payload(self, **kwargs)

    def topic_scratchpad(self, *, topic_slug: str, updated_by: str = "aitp-cli") -> dict[str, Any]: return topic_scratchpad_payload(self, topic_slug=topic_slug, updated_by=updated_by)

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
        return derive_topic_skill_projection(
            self,
            topic_slug=topic_slug,
            updated_by=updated_by,
            topic_state=topic_state,
            research_contract=research_contract,
            validation_contract=validation_contract,
            selected_pending_action=selected_pending_action,
            strategy_memory=strategy_memory,
            topic_completion=topic_completion,
            open_gap_summary=open_gap_summary,
            candidate_rows=candidate_rows,
        )

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
        runtime_mode: str | None = None,
    ) -> dict[str, Any]:
        resolved_runtime_mode = str(runtime_mode or "").strip().lower()
        if not resolved_runtime_mode:
            protocol_payload = read_json(self._runtime_protocol_paths(topic_slug)["json"]) or {}
            resolved_runtime_mode = str(protocol_payload.get("runtime_mode") or "").strip().lower()
        return distill_from_sources(
            kernel_root=self.kernel_root,
            source_rows=source_rows,
            topic_slug=topic_slug,
            runtime_mode=resolved_runtime_mode or None,
        )

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
        return derive_open_gap_summary(
            self,
            topic_slug=topic_slug,
            candidate_rows=candidate_rows,
            pending_actions=pending_actions,
            selected_pending_action=selected_pending_action,
        )

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
        return derive_idea_packet(
            self,
            topic_slug=topic_slug,
            updated_by=updated_by,
            human_request=human_request,
            topic_state=topic_state,
            interaction_state=interaction_state,
            existing_idea_packet=existing_idea_packet,
            existing_research=existing_research,
            existing_validation=existing_validation,
            research_contract=research_contract,
            validation_contract=validation_contract,
            selected_pending_action=selected_pending_action,
        )

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
        decision_surface: dict[str, Any],
        dashboard_path: Path,
        idea_packet_paths: dict[str, Path],
        research_paths: dict[str, Path],
        validation_paths: dict[str, Path],
        execution_task: dict[str, Any] | None,
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        return derive_operator_checkpoint(
            self,
            topic_slug=topic_slug,
            updated_by=updated_by,
            existing_checkpoint=existing_checkpoint,
            idea_packet=idea_packet,
            research_contract=research_contract,
            validation_contract=validation_contract,
            promotion_gate=promotion_gate,
            selected_pending_action=selected_pending_action,
            decision_surface=decision_surface,
            dashboard_path=dashboard_path,
            idea_packet_paths=idea_packet_paths,
            research_paths=research_paths,
            validation_paths=validation_paths,
            execution_task=execution_task,
        )

    def _render_operator_checkpoint_markdown(self, payload: dict[str, Any]) -> str:
        return render_operator_checkpoint_markdown(payload)

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
            research_judgment = explainability.get("research_judgment") or {}
            lines.extend(
                [
                    "",
                    "## Topic explainability",
                    "",
                    f"- Why here: {explainability.get('why_this_topic_is_here') or '(missing)'}",
                    f"- Current route: {current_route_choice.get('selected_action_summary') or '(none)'}",
                    f"- Last evidence: {last_evidence_return.get('summary') or '(none)'}",
                    f"- Human need: {active_human_need.get('summary') or '(none)'}",
                    f"- Research judgment: {research_judgment.get('summary') or '(none)'}",
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
    ) -> dict[str, Any]:
        return derive_topic_status_explainability(
            self,
            topic_slug=topic_slug,
            topic_state=topic_state,
            interaction_state=interaction_state,
            selected_pending_action=selected_pending_action,
            idea_packet=idea_packet,
            operator_checkpoint=operator_checkpoint,
            open_gap_summary=open_gap_summary,
            validation_contract=validation_contract,
        )

    def _next_action_truth_surface_path(
        self,
        *,
        topic_slug: str,
        topic_state: dict[str, Any],
        interaction_state: dict[str, Any],
    ) -> str:
        pointers = topic_state.get("pointers") or {}
        decision_surface = interaction_state.get("decision_surface") or {}
        queue_surface = interaction_state.get("action_queue_surface") or {}
        return (
            self._normalize_artifact_path(
                pointers.get("next_action_decision_path")
                or pointers.get("next_action_decision_note_path")
                or decision_surface.get("next_action_decision_path")
                or decision_surface.get("next_action_decision_note_path")
                or queue_surface.get("generated_contract_path")
                or queue_surface.get("declared_contract_path")
            )
            or self._relativize(self._runtime_root(topic_slug) / "action_queue.jsonl")
        )

    def _human_need_truth_surface_path(
        self,
        *,
        idea_packet: dict[str, Any],
        operator_checkpoint: dict[str, Any],
    ) -> str | None:
        if str(operator_checkpoint.get("status") or "").strip() == "requested":
            return self._normalize_artifact_path(
                operator_checkpoint.get("path") or operator_checkpoint.get("note_path")
            )
        if str(idea_packet.get("status") or "").strip() == "needs_clarification":
            return self._normalize_artifact_path(idea_packet.get("path") or idea_packet.get("note_path"))
        return None

    def _topic_synopsis_runtime_focus(
        self,
        *,
        topic_state: dict[str, Any],
        topic_status_explainability: dict[str, Any],
        dependency_state: dict[str, Any],
        promotion_readiness: dict[str, Any],
    ) -> dict[str, Any]:
        return self._runtime_truth_service.topic_synopsis_runtime_focus(
            topic_state=topic_state,
            topic_status_explainability=topic_status_explainability,
            dependency_state=dependency_state,
            promotion_readiness=promotion_readiness,
        )

    def _topic_synopsis_truth_sources(
        self,
        *,
        topic_slug: str,
        topic_state: dict[str, Any],
        interaction_state: dict[str, Any],
        idea_packet: dict[str, Any],
        operator_checkpoint: dict[str, Any],
        research_question_contract_path: Path,
        promotion_readiness_path: str | Path,
        promotion_gate_path: str | Path | None,
    ) -> dict[str, Any]:
        return self._runtime_truth_service.topic_synopsis_truth_sources(
            topic_slug=topic_slug,
            topic_state=topic_state,
            interaction_state=interaction_state,
            idea_packet=idea_packet,
            operator_checkpoint=operator_checkpoint,
            research_question_contract_path=research_question_contract_path,
            promotion_readiness_path=promotion_readiness_path,
            promotion_gate_path=promotion_gate_path,
        )

    def _research_source_basis_refs(
        self,
        *,
        topic_slug: str,
        source_rows: list[dict[str, Any]],
    ) -> list[str]:
        refs: list[str] = []
        source_index_path = self.kernel_root / "source-layer" / "topics" / topic_slug / "source_index.jsonl"
        refs.append(self._relativize(source_index_path))
        for row in source_rows[:5]:
            source_id = str(row.get("source_id") or "").strip()
            title = str(row.get("title") or "").strip()
            if source_id or title:
                refs.append(f"{source_id or '(missing)'} :: {title or '(untitled source)'}")
        return self._dedupe_strings(refs)

    def _research_interpretation_focus_defaults(
        self,
        *,
        active_question: str,
        first_validation_route: str,
        research_mode: str,
        selected_action_summary: str,
    ) -> list[str]:
        defaults = [
            f"Interpret the current L0 source set toward the bounded question: {active_question}",
            "Record topic-local meaning, ambiguity, and terminology choices here instead of copying raw source metadata.",
            f"Research mode `{research_mode}` sets the default interpretation granularity for this topic.",
        ]
        if first_validation_route:
            defaults.append(f"Use `{first_validation_route}` as the first validation lens for interpreting the source set.")
        if selected_action_summary:
            defaults.append(f"Keep the current interpretation aligned with the bounded next action: {selected_action_summary}")
        return self._dedupe_strings(defaults)

    def _research_open_ambiguities_defaults(
        self,
        *,
        existing_idea_packet: dict[str, Any],
        open_gap_summary: dict[str, Any],
    ) -> list[str]:
        if str(existing_idea_packet.get("status") or "").strip() == "needs_clarification":
            missing_fields = self._dedupe_strings(list(existing_idea_packet.get("missing_fields") or []))
            questions = self._dedupe_strings(list(existing_idea_packet.get("clarification_questions") or []))
            if questions:
                return questions
            if missing_fields:
                return [f"Clarify missing idea-packet fields: {', '.join(missing_fields)}"]
        blockers = self._dedupe_strings(list(open_gap_summary.get("blockers") or []))
        if blockers:
            return blockers
        return ["No active intake ambiguity is currently recorded; follow explicit L0/L4 gap signals if that changes."]

    def _review_artifact_status(self, artifact_kind: str, payload: dict[str, Any]) -> str:
        return self._validation_review_service.review_artifact_status(artifact_kind, payload)

    def _collect_validation_review_artifacts(
        self,
        *,
        topic_slug: str,
        latest_run_id: str,
        candidate_rows: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        return self._validation_review_service.collect_validation_review_artifacts(
            topic_slug=topic_slug,
            latest_run_id=latest_run_id,
            candidate_rows=candidate_rows,
        )

    def _derive_validation_review_bundle(
        self,
        *,
        topic_slug: str,
        latest_run_id: str,
        updated_by: str,
        validation_contract: dict[str, Any],
        promotion_readiness: dict[str, Any],
        open_gap_summary: dict[str, Any],
        topic_completion: dict[str, Any],
        candidate_rows: list[dict[str, Any]],
        promotion_gate: dict[str, Any],
    ) -> dict[str, Any]:
        return self._validation_review_service.derive_validation_review_bundle(
            topic_slug=topic_slug,
            latest_run_id=latest_run_id,
            updated_by=updated_by,
            validation_contract=validation_contract,
            promotion_readiness=promotion_readiness,
            open_gap_summary=open_gap_summary,
            topic_completion=topic_completion,
            candidate_rows=candidate_rows,
            promotion_gate=promotion_gate,
        )

    def _render_research_question_contract_markdown(self, payload: dict[str, Any]) -> str:
        return render_research_question_contract_markdown(payload)

    def _render_validation_contract_markdown(self, payload: dict[str, Any]) -> str:
        return render_validation_contract_markdown(payload)

    def _render_validation_review_bundle_markdown(self, payload: dict[str, Any]) -> str:
        return self._validation_review_service.render_validation_review_bundle_markdown(payload)

    def _render_idea_packet_markdown(self, payload: dict[str, Any]) -> str:
        return render_idea_packet_markdown(payload)

    def _render_topic_skill_projection_markdown(self, payload: dict[str, Any]) -> str:
        return render_topic_skill_projection_markdown(payload)

    def _render_topic_dashboard_markdown(
        self,
        *,
        topic_slug: str,
        topic_state: dict[str, Any],
        source_intelligence: dict[str, Any],
        graph_analysis: dict[str, Any],
        runtime_focus: dict[str, Any],
        selected_pending_action: dict[str, Any] | None,
        pending_actions: list[dict[str, Any]],
        idea_packet: dict[str, Any],
        operator_checkpoint: dict[str, Any],
        topic_status_explainability: dict[str, Any],
        research_contract: dict[str, Any],
        validation_contract: dict[str, Any],
        validation_review_bundle: dict[str, Any],
        promotion_readiness: dict[str, Any],
        open_gap_summary: dict[str, Any],
        strategy_memory: dict[str, Any],
        statement_compilation: dict[str, Any],
        topic_skill_projection: dict[str, Any],
        topic_completion: dict[str, Any],
        lean_bridge: dict[str, Any],
        dependency_state: dict[str, Any],
    ) -> str:
        return render_topic_dashboard_markdown(
            self,
            topic_slug=topic_slug,
            topic_state=topic_state,
            source_intelligence=source_intelligence,
            graph_analysis=graph_analysis,
            runtime_focus=runtime_focus,
            selected_pending_action=selected_pending_action,
            pending_actions=pending_actions,
            idea_packet=idea_packet,
            operator_checkpoint=operator_checkpoint,
            topic_status_explainability=topic_status_explainability,
            research_contract=research_contract,
            validation_contract=validation_contract,
            validation_review_bundle=validation_review_bundle,
            promotion_readiness=promotion_readiness,
            open_gap_summary=open_gap_summary,
            strategy_memory=strategy_memory,
            statement_compilation=statement_compilation,
            topic_skill_projection=topic_skill_projection,
            topic_completion=topic_completion,
            lean_bridge=lean_bridge,
            dependency_state=dependency_state,
        )

    def _render_promotion_readiness_markdown(self, payload: dict[str, Any]) -> str:
        return render_promotion_readiness_markdown(payload)

    def _render_gap_map_markdown(self, payload: dict[str, Any]) -> str:
        return render_gap_map_markdown(payload)

    def _return_shape_for_status(
        self,
        return_status: str,
        unresolved_statuses: set[str] | None = None,
    ) -> str:
        return return_shape_for_status(
            self,
            return_status,
            unresolved_statuses=unresolved_statuses,
        )

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
        return followup_return_packet_markdown(self, payload)

    def _compute_topic_completion_payload(
        self,
        *,
        topic_slug: str,
        run_id: str | None,
        candidate_rows: list[dict[str, Any]],
        updated_by: str,
    ) -> dict[str, Any]:
        return compute_topic_completion_payload(
            self,
            topic_slug=topic_slug,
            run_id=run_id,
            candidate_rows=candidate_rows,
            updated_by=updated_by,
        )

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
        return render_proof_obligations_markdown(rows)

    def _render_proof_state_markdown(self, payload: dict[str, Any]) -> str:
        return render_proof_state_markdown(payload)

    def _render_statement_compilation_packet_markdown(self, payload: dict[str, Any]) -> str:
        return render_statement_compilation_packet_markdown(payload)

    def _render_proof_repair_plan_markdown(self, payload: dict[str, Any]) -> str:
        return render_proof_repair_plan_markdown(payload)

    def _render_statement_compilation_index_markdown(self, payload: dict[str, Any]) -> str:
        return render_statement_compilation_index_markdown(payload)

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
        return render_lean_bridge_packet_markdown(payload)

    def _render_lean_bridge_index_markdown(self, payload: dict[str, Any]) -> str:
        return render_lean_bridge_index_markdown(payload)

    def _materialize_statement_compilation(
        self,
        *,
        topic_slug: str,
        run_id: str,
        candidate_rows: list[dict[str, Any]],
        updated_by: str,
        candidate_id: str | None = None,
    ) -> dict[str, Any]:
        return materialize_statement_compilation(
            self,
            topic_slug=topic_slug,
            run_id=run_id,
            candidate_rows=candidate_rows,
            updated_by=updated_by,
            candidate_id=candidate_id,
        )

    def _materialize_lean_bridge(
        self,
        *,
        topic_slug: str,
        run_id: str | None,
        candidate_rows: list[dict[str, Any]],
        updated_by: str,
        candidate_id: str | None = None,
    ) -> dict[str, Any]:
        return materialize_lean_bridge(
            self,
            topic_slug=topic_slug,
            run_id=run_id,
            candidate_rows=candidate_rows,
            updated_by=updated_by,
            candidate_id=candidate_id,
        )

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
        return ensure_topic_shell_surfaces(
            self,
            topic_slug=topic_slug,
            updated_by=updated_by,
            human_request=human_request,
            topic_state=topic_state,
            interaction_state=interaction_state,
            promotion_gate=promotion_gate,
            queue_rows=queue_rows,
        )

    def _deferred_buffer_markdown(self, payload: dict[str, Any]) -> str:
        return deferred_buffer_markdown(self, payload)

    def _followup_subtopics_markdown(self, rows: list[dict[str, Any]]) -> str:
        return followup_subtopics_markdown(self, rows)

    def _followup_reintegration_markdown(self, rows: list[dict[str, Any]]) -> str:
        return followup_reintegration_markdown(self, rows)

    def _followup_gap_writeback_markdown(self, rows: list[dict[str, Any]]) -> str:
        return followup_gap_writeback_markdown(self, rows)

    def _load_deferred_buffer(self, topic_slug: str) -> dict[str, Any]:
        return load_deferred_buffer(self, topic_slug)

    def _write_deferred_buffer(self, topic_slug: str, payload: dict[str, Any]) -> dict[str, str]:
        return write_deferred_buffer(self, topic_slug, payload)

    def _load_followup_subtopic_rows(self, topic_slug: str) -> list[dict[str, Any]]:
        return load_followup_subtopic_rows(self, topic_slug)

    def _write_followup_subtopic_rows(self, topic_slug: str, rows: list[dict[str, Any]]) -> dict[str, str]:
        return write_followup_subtopic_rows(self, topic_slug, rows)

    def _write_followup_return_packet(self, topic_slug: str, payload: dict[str, Any]) -> str:
        return write_followup_return_packet(self, topic_slug, payload)

    def _load_followup_reintegration_rows(self, topic_slug: str) -> list[dict[str, Any]]:
        return load_followup_reintegration_rows(self, topic_slug)

    def _write_followup_reintegration_rows(self, topic_slug: str, rows: list[dict[str, Any]]) -> dict[str, str]:
        return write_followup_reintegration_rows(self, topic_slug, rows)

    def _load_followup_gap_writeback_rows(self, topic_slug: str) -> list[dict[str, Any]]:
        return load_followup_gap_writeback_rows(self, topic_slug)

    def _write_followup_gap_writeback_rows(self, topic_slug: str, rows: list[dict[str, Any]]) -> dict[str, str]:
        return write_followup_gap_writeback_rows(self, topic_slug, rows)

    def _reactivation_context(self, topic_slug: str) -> tuple[set[str], str, set[str]]:
        return reactivation_context(self, topic_slug)

    def _buffer_entry_ready_for_reactivation(
        self,
        entry: dict[str, Any],
        *,
        source_ids: set[str],
        source_text: str,
        child_topics: set[str],
    ) -> bool:
        return buffer_entry_ready_for_reactivation(
            self,
            entry,
            source_ids=source_ids,
            source_text=source_text,
            child_topics=child_topics,
        )

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
        raw_value = str(value or "").strip()
        quote_pairs = {'"': '"', "'": "'", "“": "”", "‘": "’", "`": "`"}
        if raw_value[:1] in quote_pairs:
            closing_quote = quote_pairs[raw_value[0]]
            closing_index = raw_value.find(closing_quote, 1)
            if closing_index > 0:
                return raw_value[1:closing_index].strip(" \t\r\n.,;:!?\"'`，。；：！？“”‘’")

        cleaned = raw_value
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
            r"(?:start|open|create|begin|launch)\s+(?:a\s+)?(?:brand[-\s]+new|new)\s+(?:research\s+)?topic(?:\s+named)?\s*[:：]?\s*(?P<title>.+)",
        )
        for pattern in patterns:
            match = re.search(pattern, raw_request, flags=re.IGNORECASE)
            if not match:
                continue
            title = self._trim_topic_title_fragment(match.group("title"))
            if title:
                return title
        return None

    def _topic_slug_exists(self, topic_slug: str) -> bool:
        resolved_slug = str(topic_slug or "").strip()
        if not resolved_slug:
            return False
        if (self._runtime_root(resolved_slug) / "topic_state.json").exists():
            return True
        if (self.kernel_root / "source-layer" / "topics" / resolved_slug / "topic.json").exists():
            return True
        if (self.kernel_root / "intake" / "topics" / resolved_slug / "topic.json").exists():
            return True
        return any(
            str(row.get("topic_slug") or "").strip() == resolved_slug
            for row in self.recent_topics(limit=500)
        )

    def _allocate_new_topic_slug(self, topic_title: str) -> str:
        base_slug = slugify(topic_title)
        if not self._topic_slug_exists(base_slug):
            return base_slug
        for index in range(2, 1000):
            candidate_slug = f"{base_slug}-{index}"
            if not self._topic_slug_exists(candidate_slug):
                return candidate_slug
        raise RuntimeError(f"Unable to allocate a fresh topic slug for {topic_title!r}")

    def _resolve_new_topic_routing(self, routing: dict[str, Any]) -> dict[str, Any]:
        if str(routing.get("route") or "").strip() != "request_new_topic":
            return routing

        topic_title = str(routing.get("topic") or "").strip()
        if not topic_title:
            return routing

        requested_slug = slugify(topic_title)
        allocated_slug = self._allocate_new_topic_slug(topic_title)
        payload = dict(routing)
        payload["topic_slug"] = allocated_slug
        payload["new_topic_allocation"] = {
            "requested_title": topic_title,
            "requested_slug": requested_slug,
            "allocated_topic_slug": allocated_slug,
            "collision": allocated_slug != requested_slug,
        }
        if allocated_slug != requested_slug:
            payload["reason"] = (
                f"{str(routing.get('reason') or '').strip()} "
                f"Existing topic slug `{requested_slug}` already exists, so AITP allocated fresh slug "
                f"`{allocated_slug}` to honor the explicit new-topic request."
            ).strip()
        return payload

    def _resolve_requested_topic_slug(
        self,
        *,
        topic_slug: str | None,
        topic: str | None,
        human_request: str | None,
    ) -> str:
        explicit_topic_slug = str(topic_slug or "").strip()
        if explicit_topic_slug:
            return explicit_topic_slug
        resolved_topic = str(topic or "").strip()
        if not resolved_topic:
            raise ValueError("Provide topic_slug or topic.")
        if self._extract_new_topic_title(human_request):
            return self._allocate_new_topic_slug(resolved_topic)
        return slugify(resolved_topic)

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

    def _resolve_topic_reference_for_management(self, task: str) -> str | None:
        named = self._find_known_topic_slug_in_request(task)
        if named:
            return named
        if re.search(r"(?:这个\s*topic|当前\s*topic|这个\s*课题|当前\s*课题|this topic|current topic|active topic)", task, flags=re.IGNORECASE):
            try:
                return self.current_topic_slug(fallback_to_latest=True)
            except FileNotFoundError:
                return None
        return None

    def _projection_routing_tokens(self, text: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[\u4e00-\u9fff]+|[a-z0-9_]+", str(text or "").lower())
            if len(token) > 1
        }

    def _projection_routing_match_score(
        self,
        *,
        task: str,
        row: dict[str, Any],
        projection: dict[str, Any],
    ) -> int:
        task_tokens = self._projection_routing_tokens(task)
        if not task_tokens:
            return 0

        projection_text = " ".join(
            [
                str(projection.get("summary") or ""),
                str(row.get("summary") or ""),
                str(projection.get("lane") or row.get("lane") or ""),
                *[str(item) for item in (projection.get("entry_signals") or [])],
                *[str(item) for item in (projection.get("required_first_routes") or [])],
            ]
        )
        projection_tokens = self._projection_routing_tokens(projection_text)
        overlap = task_tokens & projection_tokens
        score = min(len(overlap), 4)

        task_lower = str(task or "").lower()
        lane = str(projection.get("lane") or row.get("lane") or "").strip()
        if lane == "formal_theory" and re.search(
            r"(formal|theorem|proof|lean|derivation|operator algebra|证明|定理|推导|形式)",
            task_lower,
            flags=re.IGNORECASE,
        ):
            score += 2
        if lane == "code_method" and re.search(
            r"(benchmark|workflow|implementation|code|algorithm|benchmark-first|基准|实现|算法|数值)",
            task_lower,
            flags=re.IGNORECASE,
        ):
            score += 2
        if str(projection.get("status") or "").strip() == "available":
            score += 1
        return score

    def _projection_routing_hint(
        self,
        *,
        task: str,
        registry: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if registry is None or not str(task or "").strip():
            return None

        best_match: dict[str, Any] | None = None
        for row in registry.get("topics") or []:
            if not isinstance(row, dict):
                continue
            topic_slug = str(row.get("topic_slug") or "").strip()
            if not topic_slug:
                continue
            if self._scheduler_skip_reason(row) is not None:
                continue
            if str(row.get("projection_status") or "").strip() != "available":
                continue

            projection_paths = self._topic_skill_projection_paths(topic_slug)
            projection = read_json(projection_paths["json"]) or {}
            if str(projection.get("status") or "").strip() != "available":
                continue
            projection_note_path = str(
                row.get("projection_note_path")
                or (self._relativize(projection_paths["note"]) if projection_paths["note"].exists() else "")
            ).strip()
            if not projection_note_path:
                continue

            score = self._projection_routing_match_score(
                task=task,
                row=row,
                projection=projection,
            )
            if score < 3:
                continue

            candidate = {
                "matched_topic_slug": topic_slug,
                "match_score": score,
                "lane": str(projection.get("lane") or row.get("lane") or "").strip(),
                "projection_status": str(projection.get("status") or "missing").strip(),
                "projection_note_path": projection_note_path,
                "projection_summary": str(projection.get("summary") or row.get("summary") or "").strip(),
                "focus_state": str(row.get("focus_state") or "background"),
            }
            if best_match is None or (
                candidate["match_score"],
                candidate["focus_state"] == "focused",
                candidate["matched_topic_slug"],
            ) > (
                best_match["match_score"],
                best_match["focus_state"] == "focused",
                best_match["matched_topic_slug"],
            ):
                best_match = candidate
        return best_match

    def route_codex_chat_request(
        self,
        *,
        task: str,
        explicit_topic_slug: str | None = None,
        explicit_topic: str | None = None,
        explicit_current_topic: bool = False,
        explicit_latest_topic: bool = False,
    ) -> dict[str, Any]:
        return route_chat_request(
            self,
            task=task,
            explicit_topic_slug=explicit_topic_slug,
            explicit_topic=explicit_topic,
            explicit_current_topic=explicit_current_topic,
            explicit_latest_topic=explicit_latest_topic,
        )

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
        return start_codex_chat_session(
            self,
            task=task,
            explicit_topic_slug=explicit_topic_slug,
            explicit_topic=explicit_topic,
            explicit_current_topic=explicit_current_topic,
            explicit_latest_topic=explicit_latest_topic,
            statement=statement,
            run_id=run_id,
            control_note=control_note,
            updated_by=updated_by,
            skill_queries=skill_queries,
            max_auto_steps=max_auto_steps,
            research_mode=research_mode,
            load_profile=load_profile,
        )

    def _exploration_current_topic_context(self) -> dict[str, str] | None:
        payload = read_json(self._current_topic_memory_paths()["json"]) or {}
        topic_slug = str(payload.get("topic_slug") or "").strip()
        if not topic_slug or not (self._runtime_root(topic_slug) / "topic_state.json").exists():
            return None
        return {
            "topic_slug": topic_slug,
            "note_path": str(payload.get("current_topic_note_path") or self._relativize(self._current_topic_memory_paths()["note"])),
            "summary": str(payload.get("summary") or "").strip(),
        }

    def explore(self, *, task: str, updated_by: str = "aitp-explore") -> dict[str, Any]:
        normalized_task = str(task or "").strip()
        if not normalized_task:
            raise ValueError("task must not be empty")
        current_topic = self._exploration_current_topic_context() or {}
        payload = build_exploration_session_payload(
            exploration_id=f"explore-{bounded_slugify(normalized_task, max_length=24)}-{bounded_slugify(now_iso(), max_length=24)}",
            task=normalized_task,
            updated_at=now_iso(),
            updated_by=updated_by,
            current_topic_slug=str(current_topic.get("topic_slug") or "").strip() or None,
            current_topic_note_path=str(current_topic.get("note_path") or "").strip() or None,
            current_topic_summary=str(current_topic.get("summary") or "").strip() or None,
        )
        return materialize_exploration_session(kernel_root=self.kernel_root, payload=payload)

    def promote_exploration(self, *, exploration_id: str, explicit_current_topic: bool = False, explicit_topic_slug: str | None = None, explicit_topic: str | None = None, updated_by: str = "aitp-explore") -> dict[str, Any]:
        exploration = load_exploration_session(kernel_root=self.kernel_root, exploration_id=exploration_id)
        target_mode = "current_topic" if explicit_current_topic or (not explicit_topic_slug and not explicit_topic and exploration.get("current_topic_slug")) else ("topic_slug" if explicit_topic_slug else ("topic" if explicit_topic else "new_topic"))
        promoted_session = self.start_chat_session(task=str(exploration.get("task") or ""), explicit_topic_slug=explicit_topic_slug, explicit_topic=explicit_topic, explicit_current_topic=target_mode == "current_topic", updated_by=updated_by, max_auto_steps=0)
        payload = build_exploration_promotion_request(exploration_payload=exploration, updated_at=now_iso(), updated_by=updated_by, target_mode=target_mode, promoted_session=promoted_session)
        return materialize_exploration_promotion_request(kernel_root=self.kernel_root, exploration_id=exploration_id, payload=payload)

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
        return render_control_note_markdown(
            topic_slug=topic_slug,
            run_id=run_id,
            updated_by=updated_by,
            updated_at=now_iso(),
            steering=steering,
            innovation_direction_path=innovation_direction_path,
            innovation_decisions_path=innovation_decisions_path,
            steering_contract=steering_contract,
        )

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

    def steer_topic_from_text(
        self,
        *,
        topic_slug: str,
        text: str,
        run_id: str | None = None,
        updated_by: str = "aitp-cli",
        topic_state: dict[str, Any] | None = None,
        control_note: str | None = None,
    ) -> dict[str, Any]:
        raw_text = str(text or "").strip()
        if not raw_text:
            raise ValueError("text must not be empty")

        steering = self._parse_human_steering_request(raw_text)
        if not steering.get("detected"):
            raise ValueError("text did not contain a recognizable steering directive")

        return self._materialize_steering_payload(
            topic_slug=topic_slug,
            run_id=run_id,
            steering=steering,
            raw_request=raw_text,
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
        return promotion_gate_markdown(payload)

    def _write_promotion_gate(self, topic_slug: str, payload: dict[str, Any]) -> dict[str, str]:
        return write_promotion_gate(self, topic_slug, payload)

    def _load_promotion_gate(self, topic_slug: str) -> dict[str, Any] | None:
        return load_promotion_gate(self, topic_slug)

    def _append_promotion_gate_log(self, topic_slug: str, run_id: str, row: dict[str, Any]) -> str:
        return append_promotion_gate_log(self, topic_slug, run_id, row)

    def _theory_packet_root(self, topic_slug: str, run_id: str, candidate_id: str) -> Path:
        return self._validation_run_root(topic_slug, run_id) / "theory-packets" / bounded_slugify(candidate_id)

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
            "analytical_review": packet_root / "analytical_review.json",
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

        projection_path = consultation_projection_path(
            self.kernel_root,
            topic_slug=topic_slug,
            stage=stage,
            run_id=run_id,
        )
        if projection_path is not None:
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
        return runtime_protocol_markdown(payload)

    def _materialize_runtime_protocol_bundle(
        self,
        *,
        topic_slug: str,
        updated_by: str,
        human_request: str | None = None,
        load_profile: str | None = None,
        requested_max_auto_steps: int | None = None,
        applied_max_auto_steps: int | None = None,
        auto_step_budget_reason: str | None = None,
    ) -> dict[str, str]:
        return materialize_runtime_protocol_bundle(
            self,
            topic_slug=topic_slug,
            updated_by=updated_by,
            human_request=human_request,
            load_profile=load_profile,
            requested_max_auto_steps=requested_max_auto_steps,
            applied_max_auto_steps=applied_max_auto_steps,
            auto_step_budget_reason=auto_step_budget_reason,
        )

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

    def _maybe_append_literature_intake_stage_action(
        self,
        *,
        topic_slug: str,
        queue_rows: list[dict[str, Any]],
        runtime_payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if str(runtime_payload.get("runtime_mode") or "").strip() != "explore":
            return queue_rows
        if str(runtime_payload.get("active_submode") or "").strip() != "literature":
            return queue_rows
        if any(str(row.get("action_type") or "").strip() == "literature_intake_stage" for row in queue_rows):
            return queue_rows

        stage_payload = derive_literature_stage_payload_from_runtime_payload(
            topic_slug=topic_slug,
            runtime_payload=runtime_payload,
        )
        candidate_units = list(stage_payload.get("candidate_units") or [])
        if not candidate_units:
            return queue_rows

        queue_rows.insert(
            0,
            {
                "action_id": f"action:{topic_slug}:literature-intake-stage:01",
                "topic_slug": topic_slug,
                "resume_stage": "L1",
                "status": "pending",
                "action_type": "literature_intake_stage",
                "summary": "Stage bounded literature-intake units from the current L1 vault into L2 staging.",
                "auto_runnable": True,
                "handler_args": {
                    "source_slug": stage_payload.get("source_slug") or topic_slug,
                    "candidate_units": candidate_units,
                },
                "queue_source": "runtime_appended",
                "declared_contract_path": None,
            },
        )
        return queue_rows

    def _run_literature_intake_stage(
        self,
        *,
        topic_slug: str,
        row: dict[str, Any],
        updated_by: str,
    ) -> dict[str, Any]:
        handler_args = row.get("handler_args") or {}
        source_slug = str(handler_args.get("source_slug") or "").strip()
        candidate_units = handler_args.get("candidate_units") or []
        if not isinstance(candidate_units, list):
            candidate_units = []
        if not candidate_units:
            protocol_payload = read_json(self._runtime_protocol_paths(topic_slug)["json"]) or {}
            derived_stage_payload = derive_literature_stage_payload_from_runtime_payload(
                topic_slug=topic_slug,
                runtime_payload=protocol_payload,
            )
            source_slug = source_slug or str(derived_stage_payload.get("source_slug") or "").strip()
            candidate_units = list(derived_stage_payload.get("candidate_units") or [])
        if not candidate_units:
            raise RuntimeError("No candidate_units provided or derivable for literature_intake_stage.")
        source_slug = source_slug or topic_slug

        staging = stage_literature_units(
            self.kernel_root,
            topic_slug=topic_slug,
            source_slug=source_slug,
            candidate_units=[dict(item) for item in candidate_units if isinstance(item, dict)],
            created_by=updated_by,
        )
        return {
            "source_slug": source_slug,
            "staging": staging,
        }

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
        return apply_candidate_split_contract(
            self,
            topic_slug=topic_slug,
            run_id=run_id,
            updated_by=updated_by,
        )

    def reactivate_deferred_candidates(
        self,
        *,
        topic_slug: str,
        run_id: str | None = None,
        entry_id: str | None = None,
        updated_by: str = "aitp-cli",
    ) -> dict[str, Any]:
        return reactivate_deferred_candidates(
            self,
            topic_slug=topic_slug,
            run_id=run_id,
            entry_id=entry_id,
            updated_by=updated_by,
        )

    def spawn_followup_subtopics(
        self,
        *,
        topic_slug: str,
        run_id: str | None = None,
        query: str | None = None,
        receipt_id: str | None = None,
        updated_by: str = "aitp-cli",
    ) -> dict[str, Any]:
        return spawn_followup_subtopics(
            self,
            topic_slug=topic_slug,
            run_id=run_id,
            query=query,
            receipt_id=receipt_id,
            updated_by=updated_by,
        )

    def _execute_auto_actions(
        self,
        *,
        topic_slug: str,
        updated_by: str,
        max_auto_steps: int,
        default_skill_queries: list[str] | None,
    ) -> dict[str, Any]:
        return execute_auto_actions(
            self,
            topic_slug=topic_slug,
            updated_by=updated_by,
            max_auto_steps=max_auto_steps,
            default_skill_queries=default_skill_queries,
        )

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

    def _codex_mcp_setup_markdown(self, *, mcp_profile: str = "full") -> str:
        server_name = self._mcp_server_name(mcp_profile)
        command = ["codex", "mcp", "add", server_name]
        for key, value in self._mcp_environment(mcp_profile=mcp_profile).items():
            command.extend(["--env", f"{key}={value}"])
        command.extend(["--", *self._resolve_aitp_mcp_command()])
        return "\n".join(
            [
                "# Codex MCP setup",
                "",
                f"Run this once to register the installable `{server_name}` MCP server with Codex:",
                "",
                "```bash",
                self._format_command(command),
                "```",
                "",
                "Verify with:",
                "",
                "```bash",
                f"codex mcp get {server_name}",
                "```",
                "",
            ]
        )

    def _openclaw_mcp_setup_markdown(self, *, scope: str, mcp_profile: str = "full") -> str:
        server_name = self._mcp_server_name(mcp_profile)
        command = ["mcporter", "config", "add", server_name]
        command.extend(["--command", self._resolve_aitp_mcp_command()[0]])
        for arg in self._resolve_aitp_mcp_command()[1:]:
            command.extend(["--arg", arg])
        for key, value in self._mcp_environment(mcp_profile=mcp_profile).items():
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
                f"mcporter config get {server_name} --json",
                "```",
                "",
            ]
        )

    def _opencode_mcp_setup_markdown(
        self,
        *,
        scope: str,
        target_root: str | None,
        mcp_profile: str = "full",
    ) -> str:
        server_name = self._mcp_server_name(mcp_profile)
        if target_root:
            config_path = resolve_agent_hidden_root(
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
                f"OpenCode should expose an `{server_name}` local MCP server entry.",
                "",
                "Expected config path:",
                "",
                f"- `{config_path}`",
                "",
                "If config mutation is disabled, copy the generated MCP block into your active OpenCode config manually.",
                "",
            ]
        )

    def _claude_mcp_setup_markdown(
        self,
        *,
        scope: str,
        target_root: str | None,
        mcp_profile: str = "full",
    ) -> str:
        server_name = self._mcp_server_name(mcp_profile)
        if target_root:
            target_path = Path(target_root)
            fake_home = target_path.parent if target_path.name == ".claude" else target_path
            config_path = fake_home / (".mcp.json" if scope == "project" else ".claude.json")
        elif scope == "project":
            config_path = self.repo_root / ".mcp.json"
        else:
            config_path = Path.home() / ".claude.json"

        command = [
            "claude",
            "mcp",
            "add-json",
            "-s",
            "project" if scope == "project" else "user",
            server_name,
            json.dumps(self._claude_mcp_entry(mcp_profile=mcp_profile), ensure_ascii=True, separators=(",", ":")),
        ]

        return "\n".join(
            [
                "# Claude Code MCP setup",
                "",
                f"Claude Code should expose an `{server_name}` MCP server so AITP runtime actions are available as native structured tools.",
                "",
                "Expected config path:",
                "",
                f"- `{config_path}`",
                "",
                "Equivalent Claude CLI command:",
                "",
                "```bash",
                self._format_command(command),
                "```",
                "",
                "Verify with:",
                "",
                "```bash",
                "claude mcp list",
                "```",
                "",
            ]
        )

    def _opencode_mcp_entry(self, *, mcp_profile: str = "full") -> dict[str, Any]:
        return {
            "type": "local",
            "command": self._resolve_aitp_mcp_command(),
            "enabled": True,
            "timeout": 120000,
            "environment": self._mcp_environment(mcp_profile=mcp_profile),
        }

    def _claude_mcp_entry(self, *, mcp_profile: str = "full") -> dict[str, Any]:
        command = self._resolve_aitp_mcp_command()
        return {
            "command": command[0],
            "args": command[1:],
            "env": self._mcp_environment(mcp_profile=mcp_profile),
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
        return resolve_openclaw_skill_target(self, scope=scope, target_root=target_root)

    def _agent_hidden_root(
        self,
        *,
        target_root: str | None,
        scope: str,
        hidden_dir: str,
        user_root: Path,
        project_root: Path,
    ) -> Path:
        return resolve_agent_hidden_root(
            target_root=target_root,
            scope=scope,
            hidden_dir=hidden_dir,
            user_root=user_root,
            project_root=project_root,
        )

    def _install_codex_mcp(self, *, force: bool) -> list[dict[str, str]]:
        return perform_codex_mcp_install(self, force=force)

    def _install_openclaw_mcp(self, *, force: bool, scope: str) -> list[dict[str, str]]:
        return perform_openclaw_mcp_install(self, force=force, scope=scope)

    def _install_claude_mcp(
        self,
        *,
        force: bool,
        scope: str,
        target_root: str | None,
    ) -> list[dict[str, str]]:
        return perform_claude_mcp_install(
            self,
            force=force,
            scope=scope,
            target_root=target_root,
        )

    def _install_opencode_mcp(
        self,
        *,
        force: bool,
        scope: str,
        target_root: str | None,
    ) -> list[dict[str, str]]:
        return perform_opencode_mcp_install(
            self,
            force=force,
            scope=scope,
            target_root=target_root,
        )

    def _install_opencode_plugin(
        self,
        *,
        scope: str,
        target_root: str | None,
        force: bool,
    ) -> list[dict[str, str]]:
        return perform_opencode_plugin_install(
            self,
            scope=scope,
            target_root=target_root,
            force=force,
        )

    def _install_claude_session_start_hook(
        self,
        *,
        scope: str,
        target_root: str | None,
        force: bool,
    ) -> list[dict[str, str]]:
        return perform_claude_session_start_hook_install(
            self,
            scope=scope,
            target_root=target_root,
            force=force,
        )

    def get_runtime_state(self, topic_slug: str) -> dict[str, Any]:
        topic_state = read_json(self._runtime_root(topic_slug) / "topic_state.json")
        if topic_state is None:
            raise FileNotFoundError(f"Runtime state missing for topic {topic_slug}")
        return topic_state

    def _known_topic_slugs(self) -> list[str]:
        slugs: set[str] = set()
        for row in read_jsonl(self._runtime_topic_index_path()):
            topic_slug = str(row.get("topic_slug") or "").strip()
            if topic_slug:
                slugs.add(topic_slug)
        topics_root = self.kernel_root / "runtime" / "topics"
        if topics_root.exists():
            for path in topics_root.iterdir():
                if not path.is_dir():
                    continue
                topic_slug = path.name.strip()
                if not topic_slug or topic_slug.startswith("."):
                    continue
                if (path / "topic_state.json").exists():
                    slugs.add(topic_slug)
        return sorted(slugs)

    def _coerce_priority(self, value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _build_active_topic_record(
        self,
        *,
        topic_slug: str,
        previous: dict[str, Any] | None = None,
        human_request: str | None = None,
    ) -> dict[str, Any] | None:
        topic_slug = str(topic_slug or "").strip()
        if not topic_slug:
            return None
        topic_state = read_json(self._runtime_root(topic_slug) / "topic_state.json")
        if topic_state is None:
            return None
        previous = previous or {}
        synopsis = read_json(self._runtime_root(topic_slug) / "topic_synopsis.json") or {}
        runtime_focus = synopsis.get("runtime_focus") or {}
        projection_paths = self._topic_skill_projection_paths(topic_slug)
        projection = read_json(projection_paths["json"]) or {}
        explainability = topic_state.get("status_explainability") or {}
        updated_at = (
            str(synopsis.get("updated_at") or "").strip()
            or str(topic_state.get("updated_at") or "").strip()
            or now_iso()
        )
        status = (
            str(synopsis.get("status") or "").strip()
            or str((((topic_state.get("layer_status") or {}).get(str(topic_state.get("resume_stage") or "")) or {}).get("status")) or "").strip()
            or str(topic_state.get("resume_stage") or "").strip()
            or "unknown"
        )
        projection_note_path = self._relativize(projection_paths["note"]) if projection_paths["note"].exists() else None
        details = self._normalize_blocked_by_details(previous.get("blocked_by_details") or [])
        blocked_by = self._blocked_by_slugs_from_details(details) or [item for item in (previous.get("blocked_by") or []) if str(item).strip()]
        return {
            "topic_slug": topic_slug,
            "status": status,
            "operator_status": str(previous.get("operator_status") or "").strip(),
            "priority": self._coerce_priority(previous.get("priority")),
            "last_activity": updated_at,
            "runtime_root": self._relativize(self._runtime_root(topic_slug)),
            "lane": str(synopsis.get("lane") or topic_state.get("research_mode") or "").strip(),
            "resume_stage": str(topic_state.get("resume_stage") or "").strip(),
            "run_id": str(topic_state.get("latest_run_id") or "").strip(),
            "projection_status": str(projection.get("status") or "missing").strip(),
            "projection_note_path": projection_note_path,
            "blocked_by": blocked_by,
            "blocked_by_details": details,
            "focus_state": "background",
            "summary": str(
                runtime_focus.get("summary")
                or synopsis.get("next_action_summary")
                or explainability.get("current_status_summary")
                or topic_state.get("summary")
                or ""
            ).strip(),
            "human_request": str(human_request or previous.get("human_request") or "").strip(),
        }

    def _render_active_topics_registry_note(self, payload: dict[str, Any]) -> str:
        focused = str(payload.get("focused_topic_slug") or "").strip()
        rows = payload.get("topics") or []
        lines = [
            "# Active topics registry",
            "",
            f"- Registry version: `{payload.get('registry_version') or '(missing)'}`",
            f"- Focused topic: `{focused or '(none)'}`",
            f"- Updated at: `{payload.get('updated_at') or '(missing)'}`",
            f"- Updated by: `{payload.get('updated_by') or '(missing)'}`",
            f"- Topic count: `{len(rows)}`",
            "",
            "## Topics",
            "",
        ]
        for row in rows:
            lines.extend(
                [
                    f"- `{row.get('topic_slug') or '(missing)'}`"
                    f" status=`{self._effective_topic_status(row)}`"
                    f" lane=`{row.get('lane') or '(missing)'}`"
                    f" priority=`{row.get('priority')}`"
                    f" focus=`{row.get('focus_state') or 'background'}`"
                    f" projection=`{row.get('projection_status') or 'missing'}`",
                    f"  - Last activity: `{row.get('last_activity') or '(missing)'}`",
                    f"  - Runtime root: `{row.get('runtime_root') or '(missing)'}`",
                ]
            )
            blocked_by = [item for item in (row.get("blocked_by") or []) if str(item).strip()]
            if blocked_by:
                lines.append(f"  - Blocked by: `{', '.join(blocked_by)}`")
            if str(row.get("summary") or "").strip():
                lines.append(f"  - Summary: {row.get('summary')}")
        if not rows:
            lines.append("- `(none)`")
        lines.extend(
            [
                "",
                "This registry is the authoritative multi-topic runtime index.",
                "`current_topic.json` is treated as the focused-topic compatibility projection.",
                "",
            ]
        )
        return "\n".join(lines)

    def _topic_family_id(self, lane: str) -> str:
        return f"topic_family:{slugify(lane or 'generic')}"

    def _build_topic_family_reuse_surface(self, registry: dict[str, Any]) -> dict[str, Any]:
        families_by_id: dict[str, dict[str, Any]] = {}
        for row in registry.get("topics") or []:
            if not isinstance(row, dict):
                continue
            topic_slug = str(row.get("topic_slug") or "").strip()
            if not topic_slug:
                continue
            if str(row.get("projection_status") or "").strip() != "available":
                continue

            projection_paths = self._topic_skill_projection_paths(topic_slug)
            projection = read_json(projection_paths["json"]) or {}
            if str(projection.get("status") or "").strip() != "available":
                continue

            lane = str(projection.get("lane") or row.get("lane") or "generic").strip() or "generic"
            family_id = self._topic_family_id(lane)
            family = families_by_id.setdefault(
                family_id,
                {
                    "family_id": family_id,
                    "lane": lane,
                    "status": "available",
                    "reuse_mode": "protocol_native_route_capsule",
                    "topic_count": 0,
                    "topic_slugs": [],
                    "capsules": [],
                    "family_rules": [],
                    "forbidden_proxies": [],
                },
            )

            capsule = {
                "topic_slug": topic_slug,
                "projection_id": str(projection.get("id") or "").strip() or None,
                "candidate_id": str(projection.get("candidate_id") or "").strip() or None,
                "summary": str(projection.get("summary") or row.get("summary") or "").strip(),
                "note_path": str(
                    row.get("projection_note_path")
                    or (self._relativize(projection_paths["note"]) if projection_paths["note"].exists() else "")
                ).strip()
                or None,
                "required_first_routes": self._dedupe_strings(
                    [str(item) for item in (projection.get("required_first_routes") or [])]
                ),
                "operator_checkpoint_rules": self._dedupe_strings(
                    [str(item) for item in (projection.get("operator_checkpoint_rules") or [])]
                ),
                "benchmark_first_rules": self._dedupe_strings(
                    [str(item) for item in (projection.get("benchmark_first_rules") or [])]
                ),
                "status_reason": str(projection.get("status_reason") or "").strip(),
            }
            family["capsules"].append(capsule)
            family["topic_slugs"].append(topic_slug)
            family["family_rules"] = self._dedupe_strings(
                list(family.get("family_rules") or [])
                + capsule["required_first_routes"]
                + capsule["operator_checkpoint_rules"]
                + capsule["benchmark_first_rules"]
            )
            family["forbidden_proxies"] = self._dedupe_strings(
                list(family.get("forbidden_proxies") or [])
                + [str(item) for item in (projection.get("forbidden_proxies") or [])]
            )

        families: list[dict[str, Any]] = []
        for family in families_by_id.values():
            family["topic_slugs"] = self._dedupe_strings(list(family.get("topic_slugs") or []))
            family["capsules"] = sorted(
                list(family.get("capsules") or []),
                key=lambda item: (str(item.get("topic_slug") or ""), str(item.get("projection_id") or "")),
            )
            family["topic_count"] = len(family["topic_slugs"])
            family["summary"] = (
                f"{family['topic_count']} mature projection capsule(s) are available for lane `{family['lane']}`."
            )
            families.append(family)

        families.sort(key=lambda item: (str(item.get("lane") or ""), str(item.get("family_id") or "")))
        return {
            "surface_kind": "topic_family_reuse",
            "protocol_version": 1,
            "updated_at": now_iso(),
            "updated_by": str(registry.get("updated_by") or "aitp-cli"),
            "family_count": len(families),
            "families": families,
        }

    def _render_topic_family_reuse_note(self, payload: dict[str, Any]) -> str:
        return render_topic_family_reuse_note(payload)

    def _write_topic_family_reuse_surface(self, payload: dict[str, Any]) -> dict[str, Any]:
        paths = self._topic_family_reuse_paths()
        write_json(paths["json"], payload)
        write_text(paths["note"], self._render_topic_family_reuse_note(payload))
        return {
            **payload,
            "topic_family_reuse_path": str(paths["json"]),
            "topic_family_reuse_note_path": str(paths["note"]),
        }

    def _write_active_topics_registry(self, payload: dict[str, Any]) -> dict[str, Any]:
        paths = self._active_topics_registry_paths()
        write_json(paths["json"], payload)
        write_text(paths["note"], self._render_active_topics_registry_note(payload))
        topic_family_reuse = self._write_topic_family_reuse_surface(
            self._build_topic_family_reuse_surface(payload)
        )
        return {
            **payload,
            "active_topics_path": str(paths["json"]),
            "active_topics_note_path": str(paths["note"]),
            "topic_family_reuse": topic_family_reuse,
        }

    def _build_active_topics_registry(
        self,
        *,
        focused_topic_slug: str | None = None,
        updated_by: str,
        source: str,
        human_request: str | None = None,
    ) -> dict[str, Any]:
        current_payload = read_json(self._current_topic_memory_paths()["json"]) or {}
        current_topic_slug = str(current_payload.get("topic_slug") or "").strip()
        known_slugs = self._known_topic_slugs()
        if focused_topic_slug and focused_topic_slug not in known_slugs:
            if (self._runtime_root(focused_topic_slug) / "topic_state.json").exists():
                known_slugs.append(focused_topic_slug)
        rows = []
        for topic_slug in known_slugs:
            row = self._build_active_topic_record(
                topic_slug=topic_slug,
                human_request=human_request if topic_slug == focused_topic_slug else None,
            )
            if row is not None:
                rows.append(row)
        if not focused_topic_slug:
            focused_topic_slug = current_topic_slug
        if not focused_topic_slug and rows:
            rows_sorted = sorted(rows, key=lambda row: str(row.get("last_activity") or ""), reverse=True)
            focused_topic_slug = str(rows_sorted[0].get("topic_slug") or "").strip()
        for row in rows:
            row["focus_state"] = "focused" if str(row.get("topic_slug") or "") == focused_topic_slug else "background"
        rows = self._sort_registry_rows(rows, focused_topic_slug)
        return {
            "registry_version": 1,
            "focused_topic_slug": focused_topic_slug or "",
            "updated_at": now_iso(),
            "updated_by": updated_by,
            "source": source,
            "topics": rows,
        }

    def _load_active_topics_registry(self) -> dict[str, Any] | None:
        payload = read_json(self._active_topics_registry_paths()["json"])
        if not isinstance(payload, dict):
            return None
        rows = []
        for row in payload.get("topics") or []:
            if not isinstance(row, dict):
                continue
            topic_slug = str(row.get("topic_slug") or "").strip()
            if not topic_slug:
                continue
            rows.append(
                {
                    **row,
                    "topic_slug": topic_slug,
                    "runtime_root": self._relativize(resolved_runtime_root) if (resolved_runtime_root := resolve_runtime_reference_path(row.get("runtime_root"), kernel_root=self.kernel_root, repo_root=self.repo_root)) else "",
                    "priority": self._coerce_priority(row.get("priority")),
                    "blocked_by": [item for item in (row.get("blocked_by") or []) if str(item).strip()],
                    "blocked_by_details": self._normalize_blocked_by_details(row.get("blocked_by_details") or []),
                }
            )
        return {
            "registry_version": int(payload.get("registry_version") or 1),
            "focused_topic_slug": str(payload.get("focused_topic_slug") or "").strip(),
            "updated_at": str(payload.get("updated_at") or "").strip(),
            "updated_by": str(payload.get("updated_by") or "").strip(),
            "source": str(payload.get("source") or "").strip(),
            "topics": rows,
        }

    def _sync_active_topics_registry(
        self,
        *,
        topic_slug: str,
        updated_by: str,
        source: str,
        human_request: str | None = None,
        focus: bool = False,
    ) -> dict[str, Any]:
        registry = self._load_active_topics_registry()
        if registry is None:
            registry = self._build_active_topics_registry(
                focused_topic_slug=topic_slug if focus else None,
                updated_by=updated_by,
                source=source,
                human_request=human_request,
            )
            return self._write_active_topics_registry(registry)

        rows_by_slug = {
            str(row.get("topic_slug") or "").strip(): row
            for row in (registry.get("topics") or [])
            if str(row.get("topic_slug") or "").strip()
        }
        row = self._build_active_topic_record(
            topic_slug=topic_slug,
            previous=rows_by_slug.get(topic_slug),
            human_request=human_request,
        )
        if row is not None:
            rows_by_slug[topic_slug] = row
        focused_topic_slug = str(registry.get("focused_topic_slug") or "").strip()
        if focus or not focused_topic_slug:
            focused_topic_slug = topic_slug
        registry_rows = list(rows_by_slug.values())
        for item in registry_rows:
            item["focus_state"] = "focused" if str(item.get("topic_slug") or "") == focused_topic_slug else "background"
        registry["focused_topic_slug"] = focused_topic_slug
        registry["updated_at"] = now_iso()
        registry["updated_by"] = updated_by
        registry["source"] = source
        registry["topics"] = self._sort_registry_rows(registry_rows, focused_topic_slug)
        return self._write_active_topics_registry(registry)

    def _build_current_topic_memory_payload(
        self,
        *,
        topic_slug: str,
        updated_by: str,
        source: str,
        human_request: str | None = None,
        updated_at: str | None = None,
        summary_override: str | None = None,
    ) -> dict[str, Any]:
        topic_state = self.get_runtime_state(topic_slug)
        runtime_root = self._runtime_root(topic_slug)
        synopsis = read_json(runtime_root / "topic_synopsis.json") or {}
        runtime_focus = synopsis.get("runtime_focus") or {}
        collaborator_profile = load_collaborator_profile(
            runtime_root,
            topic_slug=topic_slug,
            updated_by=updated_by,
        ) or {
            "status": "absent",
            "summary": "No collaborator profile is currently recorded for this topic.",
            "path": self._relativize(runtime_root / "collaborator_profile.active.json"),
            "note_path": self._relativize(runtime_root / "collaborator_profile.active.md"),
        }
        research_trajectory = load_research_trajectory(runtime_root, topic_slug=topic_slug, updated_by=updated_by) or {
            "status": "absent",
            "summary": "No research trajectory is currently recorded for this topic.",
            "path": self._relativize(runtime_root / "research_trajectory.active.json"),
            "note_path": self._relativize(runtime_root / "research_trajectory.active.md"),
        }
        mode_learning = load_mode_learning(runtime_root, topic_slug=topic_slug, updated_by=updated_by) or {
            "status": "absent",
            "summary": "No mode learning is currently recorded for this topic.",
            "path": self._relativize(runtime_root / "mode_learning.active.json"),
            "note_path": self._relativize(runtime_root / "mode_learning.active.md"),
        }
        return {
            "topic_slug": topic_slug,
            "updated_at": updated_at or now_iso(),
            "updated_by": updated_by,
            "source": source,
            "run_id": str(topic_state.get("latest_run_id") or ""),
            "resume_stage": str(topic_state.get("resume_stage") or ""),
            "runtime_root": self._relativize(runtime_root),
            "human_request": str(human_request or "").strip(),
            "summary": str(
                summary_override
                or runtime_focus.get("summary")
                or ((topic_state.get("status_explainability") or {}).get("current_status_summary"))
                or topic_state.get("summary")
                or topic_state.get("resume_reason")
                or ""
            ),
            "collaborator_profile_status": str(collaborator_profile.get("status") or "absent"),
            "collaborator_profile_summary": str(collaborator_profile.get("summary") or ""),
            "collaborator_profile_path": str(
                collaborator_profile.get("path")
                or self._relativize(runtime_root / "collaborator_profile.active.json")
            ),
            "collaborator_profile_note_path": str(
                collaborator_profile.get("note_path")
                or self._relativize(runtime_root / "collaborator_profile.active.md")
            ),
            "research_trajectory_status": str(research_trajectory.get("status") or "absent"),
            "research_trajectory_summary": str(research_trajectory.get("summary") or ""),
            "research_trajectory_path": str(research_trajectory.get("path") or self._relativize(runtime_root / "research_trajectory.active.json")),
            "research_trajectory_note_path": str(research_trajectory.get("note_path") or self._relativize(runtime_root / "research_trajectory.active.md")),
            "mode_learning_status": str(mode_learning.get("status") or "absent"),
            "mode_learning_summary": str(mode_learning.get("summary") or ""),
            "mode_learning_path": str(mode_learning.get("path") or self._relativize(runtime_root / "mode_learning.active.json")),
            "mode_learning_note_path": str(mode_learning.get("note_path") or self._relativize(runtime_root / "mode_learning.active.md")),
        }

    def _write_current_topic_memory(self, payload: dict[str, Any]) -> dict[str, Any]:
        paths = self._current_topic_memory_paths()
        write_json(paths["json"], payload)
        write_text(paths["note"], self._render_current_topic_note(payload))
        return {
            **payload,
            "current_topic_path": str(paths["json"]),
            "current_topic_note_path": str(paths["note"]),
        }

    def _project_current_topic_from_registry(self, registry: dict[str, Any]) -> dict[str, Any] | None:
        payload = self._derive_current_topic_memory_from_registry(registry)
        if payload is None:
            return None
        return self._write_current_topic_memory(payload)

    def list_active_topics(self, *, updated_by: str = "aitp-cli") -> dict[str, Any]:
        registry = self._load_active_topics_registry()
        if registry is None:
            registry = self._build_active_topics_registry(
                updated_by=updated_by,
                source="list-active-topics",
            )
            registry = self._write_active_topics_registry(registry)
        else:
            registry = self._write_active_topics_registry(registry)
        topics = []
        for row in registry.get("topics") or []:
            topics.append(
                {
                    **row,
                    "effective_status": self._effective_topic_status(row),
                    "dependency_state": self._topic_dependency_state(str(row.get("topic_slug") or "")),
                }
            )
        return {
            "focused_topic_slug": str(registry.get("focused_topic_slug") or "").strip(),
            "updated_at": str(registry.get("updated_at") or "").strip(),
            "updated_by": str(registry.get("updated_by") or "").strip(),
            "topic_count": len(topics),
            "topics": topics,
            "active_topics_path": str(self._active_topics_registry_paths()["json"]),
            "active_topics_note_path": str(self._active_topics_registry_paths()["note"]),
            "topic_family_reuse": registry.get("topic_family_reuse") or {},
            "topic_family_reuse_path": str(self._topic_family_reuse_paths()["json"]),
            "topic_family_reuse_note_path": str(self._topic_family_reuse_paths()["note"]),
        }

    def focus_topic(
        self,
        *,
        topic_slug: str,
        updated_by: str = "aitp-cli",
        human_request: str | None = None,
    ) -> dict[str, Any]:
        registry = self._sync_active_topics_registry(
            topic_slug=topic_slug,
            updated_by=updated_by,
            source="focus-topic",
            human_request=human_request,
            focus=True,
        )
        current_projection = self._project_current_topic_from_registry(registry)
        return {
            "topic_slug": topic_slug,
            "status": "focused",
            "focused_topic_slug": str(registry.get("focused_topic_slug") or "").strip(),
            "active_topics_path": str(self._active_topics_registry_paths()["json"]),
            "current_topic_memory": current_projection,
        }

    def _update_registry_operator_status(
        self,
        *,
        topic_slug: str,
        operator_status: str,
        updated_by: str,
        source: str,
        human_request: str | None = None,
    ) -> dict[str, Any]:
        registry = self._load_active_topics_registry()
        if registry is None:
            registry = self._build_active_topics_registry(
                focused_topic_slug=topic_slug,
                updated_by=updated_by,
                source=source,
                human_request=human_request,
            )
        rows_by_slug = {
            str(row.get("topic_slug") or "").strip(): row
            for row in (registry.get("topics") or [])
            if str(row.get("topic_slug") or "").strip()
        }
        row = self._build_active_topic_record(
            topic_slug=topic_slug,
            previous=rows_by_slug.get(topic_slug),
            human_request=human_request,
        )
        if row is None:
            raise FileNotFoundError(f"Active topic {topic_slug} is missing a runtime state.")
        row["operator_status"] = operator_status
        rows_by_slug[topic_slug] = row
        focused_topic_slug = str(registry.get("focused_topic_slug") or "").strip()
        if not focused_topic_slug:
            focused_topic_slug = topic_slug
        if operator_status == "paused" and focused_topic_slug == topic_slug:
            alternative = None
            for candidate in self._sort_registry_rows(list(rows_by_slug.values()), focused_topic_slug):
                candidate_slug = str(candidate.get("topic_slug") or "").strip()
                if candidate_slug == topic_slug:
                    continue
                if self._scheduler_skip_reason(candidate) is None:
                    alternative = candidate_slug
                    break
            if alternative:
                focused_topic_slug = alternative
        if operator_status == "ready":
            focused_topic_slug = topic_slug
        rows = list(rows_by_slug.values())
        for item in rows:
            item["focus_state"] = "focused" if str(item.get("topic_slug") or "").strip() == focused_topic_slug else "background"
        registry["focused_topic_slug"] = focused_topic_slug
        registry["updated_at"] = now_iso()
        registry["updated_by"] = updated_by
        registry["source"] = source
        registry["topics"] = self._sort_registry_rows(rows, focused_topic_slug)
        return self._write_active_topics_registry(registry)

    def pause_topic(
        self,
        *,
        topic_slug: str,
        updated_by: str = "aitp-cli",
        human_request: str | None = None,
    ) -> dict[str, Any]:
        registry = self._update_registry_operator_status(
            topic_slug=topic_slug,
            operator_status="paused",
            updated_by=updated_by,
            source="pause-topic",
            human_request=human_request,
        )
        current_projection = self._project_current_topic_from_registry(registry)
        return {
            "topic_slug": topic_slug,
            "status": "paused",
            "focused_topic_slug": str(registry.get("focused_topic_slug") or "").strip(),
            "active_topics_path": str(self._active_topics_registry_paths()["json"]),
            "current_topic_memory": current_projection,
        }

    def resume_topic(
        self,
        *,
        topic_slug: str,
        updated_by: str = "aitp-cli",
        human_request: str | None = None,
    ) -> dict[str, Any]:
        registry = self._update_registry_operator_status(
            topic_slug=topic_slug,
            operator_status="ready",
            updated_by=updated_by,
            source="resume-topic",
            human_request=human_request,
        )
        current_projection = self._project_current_topic_from_registry(registry)
        return {
            "topic_slug": topic_slug,
            "status": "ready",
            "focused_topic_slug": str(registry.get("focused_topic_slug") or "").strip(),
            "active_topics_path": str(self._active_topics_registry_paths()["json"]),
            "current_topic_memory": current_projection,
        }

    def set_topic_dependency(
        self,
        *,
        topic_slug: str,
        blocked_by_topic_slug: str,
        reason: str,
        updated_by: str = "aitp-cli",
        human_request: str | None = None,
    ) -> dict[str, Any]:
        registry = self._load_active_topics_registry()
        if registry is None:
            registry = self._build_active_topics_registry(
                focused_topic_slug=topic_slug,
                updated_by=updated_by,
                source="set-topic-dependency",
                human_request=human_request,
            )
        rows_by_slug = {
            str(row.get("topic_slug") or "").strip(): row
            for row in (registry.get("topics") or [])
            if str(row.get("topic_slug") or "").strip()
        }
        row = self._build_active_topic_record(
            topic_slug=topic_slug,
            previous=rows_by_slug.get(topic_slug),
            human_request=human_request,
        )
        if row is None:
            raise FileNotFoundError(f"Active topic {topic_slug} is missing a runtime state.")
        details = self._normalize_blocked_by_details(row.get("blocked_by_details") or [])
        details = [item for item in details if item["topic_slug"] != blocked_by_topic_slug]
        details.append({"topic_slug": blocked_by_topic_slug, "reason": str(reason or "").strip()})
        row["blocked_by_details"] = details
        row["blocked_by"] = self._blocked_by_slugs_from_details(details)
        rows_by_slug[topic_slug] = row
        focused_topic_slug = str(registry.get("focused_topic_slug") or "").strip() or topic_slug
        if focused_topic_slug == topic_slug:
            alternative = None
            for candidate in self._sort_registry_rows(list(rows_by_slug.values()), focused_topic_slug):
                candidate_slug = str(candidate.get("topic_slug") or "").strip()
                if candidate_slug == topic_slug:
                    continue
                if self._scheduler_skip_reason(candidate) is None:
                    alternative = candidate_slug
                    break
            if alternative:
                focused_topic_slug = alternative
        rows = list(rows_by_slug.values())
        for item in rows:
            item["focus_state"] = "focused" if str(item.get("topic_slug") or "").strip() == focused_topic_slug else "background"
        registry["focused_topic_slug"] = focused_topic_slug
        registry["updated_at"] = now_iso()
        registry["updated_by"] = updated_by
        registry["source"] = "set-topic-dependency"
        registry["topics"] = self._sort_registry_rows(rows, focused_topic_slug)
        registry = self._write_active_topics_registry(registry)
        current_projection = self._project_current_topic_from_registry(registry)
        return {
            "topic_slug": topic_slug,
            "status": "dependency_blocked",
            "blocked_by": row["blocked_by"],
            "blocked_by_details": details,
            "focused_topic_slug": str(registry.get("focused_topic_slug") or "").strip(),
            "active_topics_path": str(self._active_topics_registry_paths()["json"]),
            "current_topic_memory": current_projection,
        }

    def clear_topic_dependency(self, *, topic_slug: str, blocked_by_topic_slug: str, updated_by: str = "aitp-cli", human_request: str | None = None) -> dict[str, Any]:
        registry = self._load_active_topics_registry()
        if registry is None:
            raise FileNotFoundError("Active topics registry has not been materialized yet.")
        rows_by_slug = {
            str(row.get("topic_slug") or "").strip(): row
            for row in (registry.get("topics") or [])
            if str(row.get("topic_slug") or "").strip()
        }
        row = rows_by_slug.get(topic_slug)
        if row is None:
            raise FileNotFoundError(f"Active topic {topic_slug} is missing from the registry.")
        details = [item for item in self._normalize_blocked_by_details(row.get("blocked_by_details") or []) if item["topic_slug"] != blocked_by_topic_slug]
        row["blocked_by_details"] = details
        row["blocked_by"] = self._blocked_by_slugs_from_details(details)
        rows_by_slug[topic_slug] = row
        focused_topic_slug = str(registry.get("focused_topic_slug") or "").strip() or topic_slug
        rows = list(rows_by_slug.values())
        for item in rows:
            item["focus_state"] = "focused" if str(item.get("topic_slug") or "").strip() == focused_topic_slug else "background"
        registry["focused_topic_slug"] = focused_topic_slug
        registry["updated_at"] = now_iso()
        registry["updated_by"] = updated_by
        registry["source"] = "clear-topic-dependency"
        registry["topics"] = self._sort_registry_rows(rows, focused_topic_slug)
        registry = self._write_active_topics_registry(registry)
        current_projection = self._project_current_topic_from_registry(registry)
        return {
            "topic_slug": topic_slug,
            "status": "dependency_cleared",
            "blocked_by": row["blocked_by"],
            "blocked_by_details": details,
            "focused_topic_slug": str(registry.get("focused_topic_slug") or "").strip(),
            "active_topics_path": str(self._active_topics_registry_paths()["json"]),
            "current_topic_memory": current_projection,
        }

    def clear_all_topic_dependencies(self, *, topic_slug: str, updated_by: str = "aitp-cli", human_request: str | None = None) -> dict[str, Any]:
        registry = self._load_active_topics_registry()
        if registry is None:
            raise FileNotFoundError("Active topics registry has not been materialized yet.")
        rows_by_slug = {
            str(row.get("topic_slug") or "").strip(): row
            for row in (registry.get("topics") or [])
            if str(row.get("topic_slug") or "").strip()
        }
        row = rows_by_slug.get(topic_slug)
        if row is None:
            raise FileNotFoundError(f"Active topic {topic_slug} is missing from the registry.")
        row["blocked_by_details"] = []
        row["blocked_by"] = []
        rows_by_slug[topic_slug] = row
        focused_topic_slug = str(registry.get("focused_topic_slug") or "").strip() or topic_slug
        rows = list(rows_by_slug.values())
        for item in rows:
            item["focus_state"] = "focused" if str(item.get("topic_slug") or "").strip() == focused_topic_slug else "background"
        registry["focused_topic_slug"] = focused_topic_slug
        registry["updated_at"] = now_iso()
        registry["updated_by"] = updated_by
        registry["source"] = "clear-all-topic-dependencies"
        registry["topics"] = self._sort_registry_rows(rows, focused_topic_slug)
        registry = self._write_active_topics_registry(registry)
        current_projection = self._project_current_topic_from_registry(registry)
        return {
            "topic_slug": topic_slug,
            "status": "dependencies_cleared",
            "blocked_by": [],
            "blocked_by_details": [],
            "focused_topic_slug": str(registry.get("focused_topic_slug") or "").strip(),
            "active_topics_path": str(self._active_topics_registry_paths()["json"]),
            "current_topic_memory": current_projection,
        }

    def prune_compat_surfaces(self, *, topic_slug: str, updated_by: str = "aitp-cli") -> dict[str, Any]:
        return perform_prune_compat_surfaces(self, topic_slug=topic_slug, updated_by=updated_by)

    def _derive_current_topic_memory_from_registry(self, registry: dict[str, Any]) -> dict[str, Any] | None:
        focused_topic_slug = str(registry.get("focused_topic_slug") or "").strip()
        if not focused_topic_slug:
            return None
        focused_row = next(
            (row for row in (registry.get("topics") or []) if str(row.get("topic_slug") or "").strip() == focused_topic_slug),
            None,
        )
        if focused_row is None:
            return None
        try:
            return self._build_current_topic_memory_payload(
                topic_slug=focused_topic_slug,
                updated_by=str(registry.get("updated_by") or "active-topics-registry"),
                source="active-topics-registry",
                human_request=str(focused_row.get("human_request") or ""),
                updated_at=str(registry.get("updated_at") or focused_row.get("last_activity") or now_iso()),
                summary_override=str(focused_row.get("summary") or "").strip() or None,
            )
        except FileNotFoundError:
            return None

    def get_current_topic_memory(self) -> dict[str, Any]:
        registry = self._load_active_topics_registry()
        if registry is not None:
            payload = self._derive_current_topic_memory_from_registry(registry)
            if payload is not None:
                self._write_current_topic_memory(payload)
                return payload
        payload = read_json(self._current_topic_memory_paths()["json"])
        if payload is None:
            raise FileNotFoundError("Current topic memory has not been materialized yet.")
        topic_slug = str(payload.get("topic_slug") or "").strip()
        if topic_slug and (self._runtime_root(topic_slug) / "topic_state.json").exists():
            self._sync_active_topics_registry(
                topic_slug=topic_slug,
                updated_by=str(payload.get("updated_by") or "aitp-service"),
                source="current-topic-compatibility",
                human_request=str(payload.get("human_request") or ""),
                focus=True,
            )
        return payload

    def _render_current_topic_note(self, payload: dict[str, Any]) -> str:
        return render_current_topic_note(payload)

    def remember_current_topic(
        self,
        *,
        topic_slug: str,
        updated_by: str,
        source: str,
        human_request: str | None = None,
    ) -> dict[str, Any]:
        payload = self._build_current_topic_memory_payload(
            topic_slug=topic_slug,
            updated_by=updated_by,
            source=source,
            human_request=human_request,
        )
        result = self._write_current_topic_memory(payload)
        self._sync_active_topics_registry(
            topic_slug=topic_slug,
            updated_by=updated_by,
            source=source,
            human_request=human_request,
            focus=True,
        )
        return result

    def _materialize_session_start_contract(
        self,
        *,
        task: str,
        routing: dict[str, Any],
        loop_payload: dict[str, Any],
        updated_by: str,
        pre_route_current_topic: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return materialize_session_start_contract(
            self,
            task=task,
            routing=routing,
            loop_payload=loop_payload,
            updated_by=updated_by,
            pre_route_current_topic=pre_route_current_topic,
        )

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

    def _scheduler_skip_reason(self, row: dict[str, Any]) -> str | None:
        blocked_by = (
            self._blocked_by_slugs_from_details(self._normalize_blocked_by_details(row.get("blocked_by_details") or []))
            or [str(item).strip() for item in (row.get("blocked_by") or []) if str(item).strip()]
        )
        if blocked_by:
            return "dependency_blocked"
        status = self._effective_topic_status(row).lower()
        if status in {
            "paused",
            "pause",
            "stopped",
            "stopped_by_operator",
            "archived",
            "completed",
            "done",
            "dependency_blocked",
            "blocked_by_dependency",
        }:
            return status or "ineligible"
        runtime_root = resolve_runtime_reference_path(
            row.get("runtime_root"),
            kernel_root=self.kernel_root,
            repo_root=self.repo_root,
        )
        if runtime_root is None or not (runtime_root / "topic_state.json").exists():
            return "missing_runtime_state"
        return None

    def _scheduler_sort_key(self, row: dict[str, Any]) -> tuple[int, int, str, str]:
        return (
            self._coerce_priority(row.get("priority")),
            1 if str(row.get("focus_state") or "") == "focused" else 0,
            str(row.get("last_activity") or ""),
            str(row.get("topic_slug") or ""),
        )

    def _effective_topic_status(self, row: dict[str, Any]) -> str:
        return str(row.get("operator_status") or row.get("status") or "unknown").strip() or "unknown"

    def _sort_registry_rows(self, rows: list[dict[str, Any]], focused_topic_slug: str) -> list[dict[str, Any]]:
        return sorted(
            rows,
            key=lambda row: (str(row.get("topic_slug") or "") != focused_topic_slug, str(row.get("last_activity") or "")),
            reverse=False,
        )

    def _normalize_blocked_by_details(self, value: Any) -> list[dict[str, str]]:
        details: list[dict[str, str]] = []
        seen: set[str] = set()
        if isinstance(value, list):
            for row in value:
                if isinstance(row, dict):
                    topic_slug = str(row.get("topic_slug") or row.get("blocked_by") or "").strip()
                    reason = str(row.get("reason") or "").strip()
                else:
                    topic_slug = str(row).strip()
                    reason = ""
                if not topic_slug or topic_slug in seen:
                    continue
                seen.add(topic_slug)
                details.append({"topic_slug": topic_slug, "reason": reason})
        return details

    def _blocked_by_slugs_from_details(self, details: list[dict[str, str]]) -> list[str]:
        return [str(row.get("topic_slug") or "").strip() for row in details if str(row.get("topic_slug") or "").strip()]

    def _topic_dependency_state(self, topic_slug: str) -> dict[str, Any]:
        registry = self._load_active_topics_registry()
        if registry is None:
            return {"status": "none", "blocked_by": [], "blocked_by_details": [], "summary": "No dependency state recorded."}
        row = next(
            (item for item in (registry.get("topics") or []) if str(item.get("topic_slug") or "").strip() == topic_slug),
            None,
        )
        if row is None:
            return {"status": "none", "blocked_by": [], "blocked_by_details": [], "summary": "No dependency state recorded."}
        details = self._normalize_blocked_by_details(row.get("blocked_by_details") or [])
        blocked_by = self._blocked_by_slugs_from_details(details) or [item for item in (row.get("blocked_by") or []) if str(item).strip()]
        if blocked_by:
            summary = "; ".join(
                f"{item['topic_slug']}: {item['reason']}" if str(item.get("reason") or "").strip() else item["topic_slug"]
                for item in details
            ) or ", ".join(blocked_by)
            return {
                "status": "dependency_blocked",
                "blocked_by": blocked_by,
                "blocked_by_details": details,
                "summary": summary,
            }
        return {"status": "clear", "blocked_by": [], "blocked_by_details": [], "summary": "No active topic dependencies."}

    def select_next_topic(self, *, updated_by: str = "aitp-cli") -> dict[str, Any]:
        registry = self._load_active_topics_registry()
        if registry is None:
            registry = self._build_active_topics_registry(
                updated_by=updated_by,
                source="scheduler-bootstrap",
            )
            self._write_active_topics_registry(registry)
        rows = list(registry.get("topics") or [])
        if not rows:
            raise FileNotFoundError("No active topics are available for scheduler selection.")

        eligible: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        for row in rows:
            reason = self._scheduler_skip_reason(row)
            if reason:
                skipped.append(
                    {
                        "topic_slug": str(row.get("topic_slug") or "").strip(),
                        "reason": reason,
                        "status": str(row.get("status") or "").strip(),
                    }
                )
                continue
            eligible.append(row)

        if not eligible:
            raise FileNotFoundError("No scheduler-eligible topics are available in the active-topics registry.")

        ordered = sorted(eligible, key=self._scheduler_sort_key, reverse=True)
        selected = ordered[0]
        focused_topic_slug = str(registry.get("focused_topic_slug") or "").strip()
        selection_reasons: list[str] = []
        if self._coerce_priority(selected.get("priority")) > 0:
            selection_reasons.append(f"highest_priority={self._coerce_priority(selected.get('priority'))}")
        if str(selected.get("topic_slug") or "") == focused_topic_slug:
            selection_reasons.append("focused_topic_bonus")
        selection_reasons.append(f"last_activity={selected.get('last_activity') or '(missing)'}")
        return {
            "selected_topic_slug": str(selected.get("topic_slug") or "").strip(),
            "selection_reason": ", ".join(selection_reasons),
            "selected_topic": selected,
            "eligible_topics": [
                {
                    "topic_slug": str(row.get("topic_slug") or "").strip(),
                    "priority": self._coerce_priority(row.get("priority")),
                    "focus_state": str(row.get("focus_state") or "background"),
                    "last_activity": str(row.get("last_activity") or ""),
                    "status": str(row.get("status") or ""),
                }
                for row in ordered
            ],
            "skipped_topics": skipped,
            "focused_topic_slug": focused_topic_slug,
            "registry_path": str(self._active_topics_registry_paths()["json"]),
        }

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

    def hello_topic(
        self,
        *,
        topic: str = "Demo topic",
        question: str = "What is the first bounded question?",
        mode: str = "formal_theory",
        updated_by: str = "aitp-cli",
        arxiv_ids: list[str] | None = None,
        local_note_paths: list[str] | None = None,
    ) -> dict[str, Any]:
        install_payload = self.ensure_cli_installed()
        try:
            current_topic = self.get_current_topic_memory()
        except FileNotFoundError:
            current_topic = {}
        current_topic_slug = str(current_topic.get("topic_slug") or "").strip()
        if current_topic_slug:
            status_payload = self.topic_status(
                topic_slug=current_topic_slug,
                updated_by=updated_by,
            )
            return {
                "mode": "current_topic",
                "topic_slug": current_topic_slug,
                "topic_title": str(current_topic.get("title") or current_topic_slug),
                "install": install_payload,
                "current_topic_memory": current_topic,
                "status": status_payload,
                "docs_hint": "research/knowledge-hub/README.md",
            }
        return {
            "mode": "welcome",
            "topic_slug": "",
            "requested_topic": topic,
            "requested_question": question,
            "install": install_payload,
            "suggested_command": f'aitp bootstrap --topic "{topic}" --statement "{question}"',
            "docs_hint": "research/knowledge-hub/README.md",
        }

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
        layer_graph = materialize_layer_graph_artifact(self, topic_slug=topic_slug, topic_state=topic_state, bundle=bundle, updated_by=updated_by)
        return {
            "topic_slug": topic_slug,
            "load_profile": str(bundle.get("load_profile") or topic_state.get("load_profile") or "light"),
            "runtime_protocol_path": protocol_paths["runtime_protocol_path"],
            "runtime_protocol_note_path": protocol_paths["runtime_protocol_note_path"],
            "primary_runtime_surfaces": runtime_surface_roles(self, topic_slug),
            "topic_state": topic_state,
            "layer_graph": layer_graph,
            "control_plane": bundle.get("control_plane") or {},
            "h_plane": bundle.get("h_plane") or {},
            "human_interaction_posture": bundle.get("human_interaction_posture") or {},
            "autonomy_posture": bundle.get("autonomy_posture") or {},
            "topic_synopsis": bundle.get("topic_synopsis") or {},
            "source_intelligence": bundle.get("source_intelligence") or {},
            "graph_analysis": bundle.get("graph_analysis") or {},
            "pending_decisions": bundle.get("pending_decisions") or {},
            "promotion_readiness": bundle.get("promotion_readiness") or {},
            "protocol_manifest": bundle.get("protocol_manifest") or {},
            "collaborator_profile": bundle.get("collaborator_profile") or {},
            "research_trajectory": bundle.get("research_trajectory") or {},
            "mode_learning": bundle.get("mode_learning") or {},
            "research_judgment": bundle.get("research_judgment") or {},
            "research_taste": bundle.get("research_taste") or {},
            "scratchpad": bundle.get("scratchpad") or {},
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
        layer_graph = materialize_layer_graph_artifact(self, topic_slug=topic_slug, topic_state=topic_state, bundle=bundle, updated_by=updated_by)
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
            "next_action_hint": str(topic_state.get("next_action_hint") or ""),
            "runtime_protocol_path": protocol_paths["runtime_protocol_path"],
            "runtime_protocol_note_path": protocol_paths["runtime_protocol_note_path"],
            "primary_runtime_surfaces": runtime_surface_roles(self, topic_slug),
            "topic_state": topic_state,
            "topic_state_explainability": (topic_state.get("status_explainability") or {}),
            "layer_graph": layer_graph,
            "control_plane": bundle.get("control_plane") or {},
            "h_plane": bundle.get("h_plane") or {},
            "human_interaction_posture": bundle.get("human_interaction_posture") or {},
            "autonomy_posture": bundle.get("autonomy_posture") or {},
            "dependency_state": bundle.get("dependency_state") or self._topic_dependency_state(topic_slug),
            "topic_synopsis": bundle.get("topic_synopsis") or {},
            "source_intelligence": bundle.get("source_intelligence") or {},
            "graph_analysis": bundle.get("graph_analysis") or {},
            "pending_decisions": bundle.get("pending_decisions") or {},
            "active_research_contract": bundle.get("active_research_contract") or {},
            "idea_packet": bundle.get("idea_packet") or {},
            "operator_checkpoint": bundle.get("operator_checkpoint") or {},
            "validation_review_bundle": bundle.get("validation_review_bundle") or {},
            "promotion_readiness": bundle.get("promotion_readiness") or {},
            "protocol_manifest": bundle.get("protocol_manifest") or {},
            "open_gap_summary": bundle.get("open_gap_summary") or {},
            "strategy_memory": bundle.get("strategy_memory") or {},
            "collaborator_profile": bundle.get("collaborator_profile") or {},
            "research_trajectory": bundle.get("research_trajectory") or {},
            "mode_learning": bundle.get("mode_learning") or {},
            "research_judgment": bundle.get("research_judgment") or {},
            "research_taste": bundle.get("research_taste") or {},
            "scratchpad": bundle.get("scratchpad") or {},
            "topic_skill_projection": bundle.get("topic_skill_projection") or {},
            "topic_completion": bundle.get("topic_completion") or {},
            "statement_compilation": bundle.get("statement_compilation") or {},
            "lean_bridge": bundle.get("lean_bridge") or {},
            "must_read_now": bundle.get("must_read_now") or [],
        }

    def topic_layer_graph(
        self,
        *,
        topic_slug: str,
        updated_by: str = "aitp-cli",
    ) -> dict[str, Any]:
        return topic_layer_graph_payload(self, topic_slug=topic_slug, updated_by=updated_by)

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
            "may_defer_until_trigger": bundle.get("may_defer_until_trigger") or [],
            "escalation_triggers": bundle.get("escalation_triggers") or [],
            "control_plane": bundle.get("control_plane") or {},
            "h_plane": bundle.get("h_plane") or {},
            "primary_runtime_surfaces": runtime_surface_roles(self, topic_slug),
            "topic_synopsis": bundle.get("topic_synopsis") or {},
            "source_intelligence": bundle.get("source_intelligence") or {},
            "graph_analysis": bundle.get("graph_analysis") or {},
            "validation_review_bundle": bundle.get("validation_review_bundle") or {},
            "pending_decisions": bundle.get("pending_decisions") or {},
            "protocol_manifest": bundle.get("protocol_manifest") or {},
            "open_gap_summary": bundle.get("open_gap_summary") or {},
            "strategy_memory": bundle.get("strategy_memory") or {},
            "collaborator_profile": bundle.get("collaborator_profile") or {},
            "research_trajectory": bundle.get("research_trajectory") or {},
            "mode_learning": bundle.get("mode_learning") or {},
            "research_judgment": bundle.get("research_judgment") or {},
            "research_taste": bundle.get("research_taste") or {},
            "scratchpad": bundle.get("scratchpad") or {},
            "topic_skill_projection": bundle.get("topic_skill_projection") or {},
            "topic_completion": bundle.get("topic_completion") or {},
            "statement_compilation": bundle.get("statement_compilation") or {},
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
            "numeric": {
                "validation_mode": "numerical",
                "verification_focus": "Validate the active topic against executed numeric or benchmark evidence.",
                "required_checks": [
                    "Require executed evidence artifacts, not only planned benchmarks.",
                    "Require declared tolerances or qualitative agreement criteria.",
                    "Reject narrative-only claims that lack result artifacts or route receipts.",
                ],
            },
            "analytical": {
                "validation_mode": "analytical",
                "verification_focus": "Validate the active topic against analytical checks such as limiting cases, dimensional consistency, symmetry, source-backed self-consistency, and source-cross-reference agreement.",
                "required_checks": ["Record at least one explicit limiting-case, dimensional, symmetry, self-consistency, or source-cross-reference check as a durable artifact.", "Tie each analytical check to a source-backed assumption, regime, or prior result instead of free-floating prose.", "Reject analytical claims that do not leave a durable artifact naming the exact check and outcome."],
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
        record_topic_completion_metric(
            self,
            topic_slug=topic_slug,
            run_id=resolved_run_id,
            updated_by=updated_by,
            payload=payload,
            json_path=paths["json"],
            note_path=paths["note"],
        )
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
        return update_followup_return_packet(
            self,
            topic_slug=topic_slug,
            run_id=run_id,
            return_status=return_status,
            accepted_return_shape=accepted_return_shape,
            return_summary=return_summary,
            child_topic_summary=child_topic_summary,
            return_artifact_paths=return_artifact_paths,
            updated_by=updated_by,
            refresh_runtime_bundle=refresh_runtime_bundle,
        )

    def reintegrate_followup_subtopic(
        self,
        *,
        topic_slug: str,
        child_topic_slug: str,
        run_id: str | None = None,
        updated_by: str = "aitp-cli",
    ) -> dict[str, Any]:
        return reintegrate_followup_subtopic(
            self,
            topic_slug=topic_slug,
            child_topic_slug=child_topic_slug,
            run_id=run_id,
            updated_by=updated_by,
        )

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
        self._materialize_statement_compilation(
            topic_slug=topic_slug,
            run_id=resolved_run_id,
            candidate_rows=candidate_rows,
            updated_by=updated_by,
            candidate_id=candidate_id,
        )
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

    def prepare_statement_compilation(
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
        payload = self._materialize_statement_compilation(
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

        resolved_topic_slug = self._resolve_requested_topic_slug(
            topic_slug=topic_slug,
            topic=topic,
            human_request=human_request,
        )
        command = [
            *self._resolve_runtime_python_command(),
            str(self._kernel_script("runtime/scripts/orchestrate_topic.py")),
            "--updated-by",
            updated_by,
        ]
        command.extend(["--topic-slug", resolved_topic_slug])
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
        topic_state = self.get_runtime_state(resolved_topic_slug)
        next_action_hint = (
            f"Run 'aitp status --topic-slug {resolved_topic_slug}' to inspect the topic, "
            f"or 'aitp loop --topic-slug {resolved_topic_slug}' to continue the bounded loop."
        )
        topic_state["next_action_hint"] = next_action_hint
        write_json(runtime_root / "topic_state.json", topic_state)
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
                "topic_synopsis": str(self._topic_synopsis_path(resolved_topic_slug)),
                "topic_dashboard": str(self._topic_dashboard_path(resolved_topic_slug)),
                "validation_review_bundle": str(self._validation_review_bundle_paths(resolved_topic_slug)["json"]),
                "validation_review_bundle_note": str(self._validation_review_bundle_paths(resolved_topic_slug)["note"]),
                "promotion_readiness": str(self._promotion_readiness_path(resolved_topic_slug)),
                "gap_map": str(self._gap_map_path(resolved_topic_slug)),
            },
            "topic_state": topic_state,
            "next_action_hint": next_action_hint,
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
        result = {
            "topic_slug": topic_slug,
            "phase": phase,
            "command": command,
            "stdout": completed.stdout.strip(),
            "conformance_state": state,
            "conformance_report_path": str(report_path),
        }
        record_conformance_metric(
            self,
            topic_slug=topic_slug,
            phase=phase,
            updated_by=updated_by,
            state=state,
            report_path=report_path,
        )
        return result

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

    def audit_theory_coverage(self, **kwargs: Any) -> dict[str, Any]:
        topic_slug = str(kwargs.get("topic_slug") or "").strip()
        candidate_id = str(kwargs.get("candidate_id") or "").strip()
        resolved_run_id, candidate_type = candidate_metric_context(
            self,
            topic_slug=topic_slug,
            run_id=kwargs.get("run_id"),
            candidate_id=candidate_id,
        )
        try:
            result = perform_theory_coverage_audit(self, **kwargs)
        except Exception as exc:
            if topic_slug:
                perform_record_theory_operation_metric(
                    self,
                    topic_slug=topic_slug,
                    run_id=resolved_run_id,
                    operation_kind="theory_coverage_audit",
                    status="error",
                    updated_by=str(kwargs.get("updated_by") or "aitp-cli"),
                    candidate_id=candidate_id or None,
                    candidate_type=candidate_type or None,
                    blocker_tags=["coverage_audit_error"],
                    summary=str(exc),
                )
            raise
        record_coverage_metric(
            self,
            topic_slug=topic_slug,
            run_id=resolved_run_id,
            updated_by=str(kwargs.get("updated_by") or "aitp-cli"),
            candidate_id=candidate_id,
            candidate_type=candidate_type,
            result=result,
        )
        return result

    def audit_formal_theory(self, **kwargs: Any) -> dict[str, Any]:
        topic_slug = str(kwargs.get("topic_slug") or "").strip()
        candidate_id = str(kwargs.get("candidate_id") or "").strip()
        resolved_run_id, candidate_type = candidate_metric_context(
            self,
            topic_slug=topic_slug,
            run_id=kwargs.get("run_id"),
            candidate_id=candidate_id,
        )
        try:
            result = perform_formal_theory_audit(self, **kwargs)
        except Exception as exc:
            if topic_slug:
                perform_record_theory_operation_metric(
                    self,
                    topic_slug=topic_slug,
                    run_id=resolved_run_id,
                    operation_kind="formal_theory_audit",
                    status="error",
                    updated_by=str(kwargs.get("updated_by") or "aitp-cli"),
                    candidate_id=candidate_id or None,
                    candidate_type=candidate_type or None,
                    blocker_tags=["formal_theory_audit_error"],
                    summary=str(exc),
                )
            raise
        record_formal_theory_metric(
            self,
            topic_slug=topic_slug,
            run_id=resolved_run_id,
            updated_by=str(kwargs.get("updated_by") or "aitp-cli"),
            candidate_id=candidate_id,
            candidate_type=candidate_type,
            result=result,
        )
        return result

    def audit_analytical_review(self, **kwargs: Any) -> dict[str, Any]:
        result = perform_analytical_review_audit(self, **kwargs)
        topic_slug = str(kwargs.get("topic_slug") or "").strip()
        resolved_run_id = self._resolve_run_id(topic_slug, kwargs.get("run_id")) if topic_slug else None
        if topic_slug:
            record_analytical_review_metric(
                self,
                topic_slug=topic_slug,
                run_id=resolved_run_id,
                updated_by=str(kwargs.get("updated_by") or "aitp-cli"),
                candidate_id=str(kwargs.get("candidate_id") or "").strip() or None,
                result=result,
            )
        return result

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
        return perform_capability_audit(
            self,
            topic_slug=topic_slug,
            updated_by=updated_by,
        )

    def paired_backend_audit(
        self,
        *,
        topic_slug: str,
        backend_id: str | None = None,
        updated_by: str = "aitp-cli",
    ) -> dict[str, Any]:
        return perform_paired_backend_audit(
            self,
            topic_slug=topic_slug,
            backend_id=backend_id,
            updated_by=updated_by,
        )

    def h_plane_audit(
        self,
        *,
        topic_slug: str,
        updated_by: str = "aitp-cli",
    ) -> dict[str, Any]:
        return perform_h_plane_audit(
            self,
            topic_slug=topic_slug,
            updated_by=updated_by,
        )

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
        result = request_promotion(
            self,
            topic_slug=topic_slug,
            candidate_id=candidate_id,
            run_id=run_id,
            route=route,
            backend_id=backend_id,
            target_backend_root=target_backend_root,
            requested_by=requested_by,
            notes=notes,
        )
        record_promotion_gate_metric(
            self,
            topic_slug=topic_slug,
            run_id=str(result.get("run_id") or self._resolve_run_id(topic_slug, run_id) or "").strip() or None,
            candidate_id=candidate_id,
            candidate_type=str(result.get("candidate_type") or "").strip() or None,
            updated_by=requested_by,
            operation_kind="promotion_request",
            status=str(result.get("status") or "unknown"),
            summary=f"Promotion request {str(result.get('status') or 'unknown')} for {candidate_id}.",
            metric_values={"route": route},
        )
        return result

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
        result = approve_promotion(
            self,
            topic_slug=topic_slug,
            candidate_id=candidate_id,
            run_id=run_id,
            approved_by=approved_by,
            notes=notes,
            human_modifications=human_modifications,
        )
        record_promotion_gate_metric(
            self,
            topic_slug=topic_slug,
            run_id=str(result.get("run_id") or self._resolve_run_id(topic_slug, run_id) or "").strip() or None,
            candidate_id=candidate_id,
            candidate_type=str(result.get("candidate_type") or "").strip() or None,
            updated_by=approved_by,
            operation_kind="promotion_approve",
            status=str(result.get("status") or "unknown"),
            summary=f"Promotion approval {str(result.get('status') or 'unknown')} for {candidate_id}.",
            metric_values={"human_modification_count": len(human_modifications or [])},
        )
        return result

    def reject_promotion(
        self,
        *,
        topic_slug: str,
        candidate_id: str,
        run_id: str | None = None,
        rejected_by: str = "aitp-cli",
        notes: str | None = None,
    ) -> dict[str, Any]:
        result = reject_promotion(
            self,
            topic_slug=topic_slug,
            candidate_id=candidate_id,
            run_id=run_id,
            rejected_by=rejected_by,
            notes=notes,
        )
        record_promotion_gate_metric(
            self,
            topic_slug=topic_slug,
            run_id=str(result.get("run_id") or self._resolve_run_id(topic_slug, run_id) or "").strip() or None,
            candidate_id=candidate_id,
            candidate_type=str(result.get("candidate_type") or "").strip() or None,
            updated_by=rejected_by,
            operation_kind="promotion_reject",
            status=str(result.get("status") or "unknown"),
            blocker_tags=["promotion_rejected"],
            summary=f"Promotion rejected for {candidate_id}.",
        )
        return result

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
        resolved_run_id, candidate_type = candidate_metric_context(
            self,
            topic_slug=topic_slug,
            run_id=run_id,
            candidate_id=candidate_id,
        )
        try:
            result = promote_candidate(
                self,
                topic_slug=topic_slug,
                candidate_id=candidate_id,
                run_id=run_id,
                promoted_by=promoted_by,
                backend_id=backend_id,
                target_backend_root=target_backend_root,
                domain=domain,
                subdomain=subdomain,
                source_id=source_id,
                source_section=source_section,
                source_section_title=source_section_title,
                notes=notes,
                review_mode=review_mode,
                canonical_layer=canonical_layer,
                review_artifact_paths=review_artifact_paths,
                coverage_summary=coverage_summary,
                consensus_summary=consensus_summary,
            )
        except Exception as exc:
            record_candidate_promotion_metric(
                self,
                topic_slug=topic_slug,
                run_id=resolved_run_id,
                updated_by=promoted_by,
                candidate_id=candidate_id,
                candidate_type=candidate_type or None,
                operation_kind="candidate_promotion",
                status="error",
                summary=str(exc),
                blocker_tags=["promotion_execution_failed"],
            )
            raise
        record_candidate_promotion_metric(
            self,
            topic_slug=topic_slug,
            run_id=resolved_run_id,
            updated_by=promoted_by,
            candidate_id=candidate_id,
            candidate_type=candidate_type or None,
            operation_kind="candidate_promotion",
            status="promoted",
            result=result,
            summary=f"Candidate promotion completed for {candidate_id}.",
        )
        return result

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
        resolved_run_id, candidate_type = candidate_metric_context(
            self,
            topic_slug=topic_slug,
            run_id=run_id,
            candidate_id=candidate_id,
        )
        try:
            result = auto_promote_candidate(
                self,
                topic_slug=topic_slug,
                candidate_id=candidate_id,
                run_id=run_id,
                promoted_by=promoted_by,
                backend_id=backend_id,
                target_backend_root=target_backend_root,
                domain=domain,
                subdomain=subdomain,
                source_id=source_id,
                source_section=source_section,
                source_section_title=source_section_title,
                notes=notes,
            )
        except Exception as exc:
            record_candidate_promotion_metric(
                self,
                topic_slug=topic_slug,
                run_id=resolved_run_id,
                updated_by=promoted_by,
                candidate_id=candidate_id,
                candidate_type=candidate_type or None,
                operation_kind="candidate_auto_promotion",
                status="error",
                summary=str(exc),
                blocker_tags=["auto_promotion_failed"],
            )
            raise
        record_candidate_promotion_metric(
            self,
            topic_slug=topic_slug,
            run_id=resolved_run_id,
            updated_by=promoted_by,
            candidate_id=candidate_id,
            candidate_type=candidate_type or None,
            operation_kind="candidate_auto_promotion",
            status="promoted",
            result=result,
            summary=f"Auto promotion completed for {candidate_id}.",
        )
        return result

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
        return execute_topic_loop(
            self,
            topic_slug=topic_slug,
            topic=topic,
            statement=statement,
            run_id=run_id,
            control_note=control_note,
            updated_by=updated_by,
            human_request=human_request,
            skill_queries=skill_queries,
            max_auto_steps=max_auto_steps,
            research_mode=research_mode,
            load_profile=load_profile,
        )

    def _codex_skill_template(self) -> str:
        return codex_skill_template(
            kernel_root=self.kernel_root,
        )

    def _using_aitp_skill_template(self, platform: str) -> str:
        return using_aitp_skill_template(platform=platform)

    def _claude_code_skill_template(self) -> str:
        return claude_code_skill_template(
            kernel_root=self.kernel_root,
        )

    def _opencode_skill_template(self) -> str:
        return opencode_skill_template(
            kernel_root=self.kernel_root,
        )

    def _openclaw_skill_template(self) -> str:
        return openclaw_skill_template(
            kernel_root=self.kernel_root,
        )

    def install_agent(
        self,
        *,
        agent: str,
        scope: str = "user",
        target_root: str | None = None,
        force: bool = True,
        install_mcp: bool = True,
        mcp_profile: str = "full",
    ) -> dict[str, Any]:
        return perform_install_agent(
            self,
            agent=agent,
            scope=scope,
            target_root=target_root,
            force=force,
            install_mcp=install_mcp,
            mcp_profile=mcp_profile,
        )

    def _install_one_agent(
        self,
        agent: str,
        *,
        scope: str,
        target_root: str | None,
        force: bool,
        install_mcp: bool,
        mcp_profile: str = "full",
    ) -> list[dict[str, str]]:
        return perform_install_one_agent(
            self,
            agent,
            scope=scope,
            target_root=target_root,
            force=force,
            install_mcp=install_mcp,
            mcp_profile=mcp_profile,
        )

    def ensure_cli_installed(self, *, workspace_root: str | None = None) -> dict[str, Any]:
        return compute_cli_install_status(self, workspace_root=workspace_root)

    def migrate_local_install(
        self,
        *,
        workspace_root: str,
        backup_root: str | None = None,
        agents: list[str] | None = None,
        with_mcp: bool = False,
    ) -> dict[str, Any]:
        return perform_local_install_migration(
            self,
            workspace_root=workspace_root,
            backup_root=backup_root,
            agents=agents,
            with_mcp=with_mcp,
        )

    def seed_l2_direction(
        self,
        *,
        direction: str,
        updated_by: str = "aitp-cli",
    ) -> dict[str, Any]:
        return seed_l2_demo_direction(
            self.kernel_root,
            direction=direction,
            updated_by=updated_by,
        )

    def consult_l2(self, *, query_text: str, retrieval_profile: str, max_primary_hits: int | None = None, include_staging: bool = False, topic_slug: str | None = None, stage: str = "L3", run_id: str | None = None, updated_by: str = "aitp-cli", record_consultation: bool = False) -> dict[str, Any]:
        resolved_max_primary_hits = 1 if record_consultation and max_primary_hits is None else max_primary_hits
        payload = consult_canonical_l2(self.kernel_root, query_text=query_text, retrieval_profile=retrieval_profile, max_primary_hits=resolved_max_primary_hits, include_staging=include_staging)
        if not record_consultation:
            return payload

        resolved_topic_slug = str(topic_slug or "").strip()
        if not resolved_topic_slug:
            raise ValueError("topic_slug is required when record_consultation=True")
        if stage not in {"L1", "L3", "L4"}:
            raise ValueError(f"Unsupported consultation stage: {stage}")
        resolved_run_id = self._resolve_run_id(resolved_topic_slug, run_id) if stage in {"L3", "L4"} else run_id
        if stage in {"L3", "L4"} and not resolved_run_id:
            raise ValueError(f"run_id is required to record {stage} consultations for {resolved_topic_slug}")
        consultation_slug = bounded_slugify(f"l2-{resolved_topic_slug}-{stage}-{resolved_run_id or 'standalone'}-{query_text}-{now_iso()}", max_length=48)
        record_payload = build_l2_consultation_record(
            kernel_root=self.kernel_root,
            topic_slug=resolved_topic_slug,
            stage=stage,
            run_id=resolved_run_id,
            query_text=query_text,
            retrieval_profile=retrieval_profile,
            dashboard_path=self._topic_dashboard_path(resolved_topic_slug),
            context_id=f"context:l2-consult-{bounded_slugify(resolved_topic_slug, max_length=24)}",
            payload=payload,
            relativize=self._relativize,
        )
        consultation_paths = self._record_l2_consultation(
            topic_slug=resolved_topic_slug,
            stage=stage,
            run_id=resolved_run_id,
            consultation_slug=consultation_slug,
            purpose=f"Consult canonical L2 memory during {stage} work and preserve the retrieval context as a durable artifact.",
            query_text=query_text,
            requested_by=updated_by,
            produced_by=updated_by,
            written_by=updated_by,
            retrieval_profile=retrieval_profile,
            **record_payload["record_args"],
        )
        result_path = Path(consultation_paths["consultation_result_path"])
        result_payload = {**(read_json(result_path) or {}), "traversal_paths": record_payload["traversal_paths"], "retrieval_summary": record_payload["retrieval_summary"]}
        write_json(result_path, result_payload)
        return {**payload, "consultation": consultation_paths}

    def compile_l2_workspace_map(self) -> dict[str, Any]:
        return materialize_workspace_memory_map(self.kernel_root)

    def compile_source_catalog(self) -> dict[str, Any]: return materialize_source_catalog(self.kernel_root)
    def trace_source_citations(self, *, canonical_source_id: str) -> dict[str, Any]: return materialize_source_citation_traversal(self.kernel_root, canonical_source_id=canonical_source_id)
    def compile_source_family(self, *, source_type: str) -> dict[str, Any]: return materialize_source_family_report(self.kernel_root, source_type=source_type)
    def export_source_bibtex(self, *, canonical_source_id: str, include_neighbors: bool = False) -> dict[str, Any]: return materialize_source_bibtex_export(self.kernel_root, canonical_source_id=canonical_source_id, include_neighbors=include_neighbors)
    def import_bibtex_sources(self, *, topic_slug: str, bibtex_path: str, updated_by: str) -> dict[str, Any]: return materialize_bibtex_source_import(self.kernel_root, topic_slug=topic_slug, bibtex_path=bibtex_path, updated_by=updated_by)
    def sync_l1_graph_export_to_theoretical_physics_brain(self, *, topic_slug: str, updated_by: str = "aitp-cli", target_root: str | None = None) -> dict[str, Any]:
        return sync_concept_graph_export_to_theoretical_physics_brain(
            kernel_root=self.kernel_root,
            repo_root=self.repo_root,
            topic_slug=topic_slug,
            updated_by=updated_by,
            target_root=target_root,
        )

    def compile_l2_graph_report(self) -> dict[str, Any]:
        return materialize_workspace_graph_report(self.kernel_root)

    def compile_l2_knowledge_report(self) -> dict[str, Any]:
        return materialize_workspace_knowledge_report(self.kernel_root)

    def audit_l2_hygiene(self) -> dict[str, Any]:
        return materialize_workspace_hygiene_report(self.kernel_root)
