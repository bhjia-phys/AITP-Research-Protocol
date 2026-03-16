from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


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

    def _runtime_protocol_markdown(self, payload: dict[str, Any]) -> str:
        lines = [
            "# AITP runtime protocol bundle",
            "",
            f"- Topic slug: `{payload['topic_slug']}`",
            f"- Updated at: `{payload['updated_at']}`",
            f"- Updated by: `{payload['updated_by']}`",
            f"- Human request: `{payload['human_request'] or '(missing)'}`",
            f"- Resume stage: `{payload['resume_stage'] or '(missing)'}`",
            f"- Last materialized stage: `{payload['last_materialized_stage'] or '(missing)'}`",
            f"- Research mode: `{payload['research_mode'] or '(missing)'}`",
            "",
            "## Why this file exists",
            "",
            "- Keep research behavior governed by durable protocol artifacts instead of hidden Python defaults.",
            "- Limit Python to state materialization, audits, and explicit handler execution.",
            "",
            "## What Python still does",
            "",
        ]
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
        lines.extend(
            [
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
        queue_rows = read_jsonl(runtime_root / "action_queue.jsonl")
        queue_surface = interaction_state.get("action_queue_surface") or {}
        decision_surface = interaction_state.get("decision_surface") or {}
        research_mode_profile = topic_state.get("research_mode_profile") or {}
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

        read_order: list[str] = [self._relativize(runtime_root / "runtime_protocol.generated.md")]
        for candidate in (
            "interaction_state.json",
            "agent_brief.md",
            "operator_console.md",
            "action_queue_contract.generated.md",
            "conformance_report.md",
        ):
            candidate_path = runtime_root / candidate
            if candidate_path.exists():
                read_order.append(self._relativize(candidate_path))
        if not read_order:
            read_order.append(self._relativize(runtime_root / "topic_state.json"))

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

        payload = {
            "protocol_version": 1,
            "topic_slug": topic_slug,
            "updated_at": now_iso(),
            "updated_by": updated_by,
            "human_request": human_request or str(interaction_state.get("human_request") or ""),
            "resume_stage": topic_state.get("resume_stage"),
            "last_materialized_stage": topic_state.get("last_materialized_stage"),
            "research_mode": topic_state.get("research_mode"),
            "python_runtime_scope": [
                "Materialize durable runtime state and protocol snapshots on disk.",
                "Run conformance, capability, and trust audits against persisted artifacts.",
                "Execute explicit auto-runnable handlers declared in runtime state.",
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
            return [Path(target_root)]
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
        )
        resolved_topic_slug = bootstrap["topic_slug"]
        resolved_run_id = self._resolve_run_id(resolved_topic_slug, run_id)

        entry_audit = self.audit(topic_slug=resolved_topic_slug, phase="entry", updated_by=updated_by)
        auto_actions = self._execute_auto_actions(
            topic_slug=resolved_topic_slug,
            updated_by=updated_by,
            max_auto_steps=max_auto_steps,
            default_skill_queries=skill_queries,
        )
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

1. For coding or implementation work, prefer `aitp-codex --topic-slug <topic_slug> "<task>"`.
2. Otherwise start substantial topic work with `aitp loop ...`, `aitp resume ...`, or `aitp bootstrap ...`.
3. Read the generated `runtime_protocol.generated.md`, `agent_brief.md`, `operator_console.md`, and `conformance_report.md`.
4. Register reusable operations with `aitp operation-init ...`.
5. End with `aitp audit --topic-slug <topic_slug> --phase exit`.

## Hard rules

- If the conformance audit fails, the run does not count as AITP work.
- Prefer durable control notes and contract files over Python heuristic defaults.
- Every reusable operation must pass through `aitp trust-audit ...` before AITP treats it as trusted.
- If a new numerical backend or diagnostic is being trusted, scaffold a baseline first with `aitp baseline ...`.
- If a derivation-heavy method is being claimed as understood, scaffold atomic understanding first with `aitp atomize ...`.
- If there is a capability gap, prefer `aitp loop ... --skill-query ...` so discovery becomes runtime state instead of ad hoc browsing.

## Common commands

```bash
aitp-codex --topic-slug <topic_slug> "<task>"
aitp loop --topic-slug <topic_slug> --human-request "<task>" --skill-query "<capability gap>"
aitp resume --topic-slug <topic_slug> --human-request "<task>"
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
3. Read `runtime_protocol.generated.md`, `agent_brief.md`, `operator_console.md`, and `conformance_report.md` before deeper work.
4. Treat missing conformance as a hard failure for AITP work.
5. Close with `aitp audit --topic-slug <topic_slug> --phase exit`.

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

Then read `runtime/topics/<topic_slug>/runtime_protocol.generated.md` before acting on the queue. Do not bypass the loop and jump straight into ad hoc browsing or execution.

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

Kernel root default: `{self.kernel_root}`
"""

    def _opencode_harness_template(self) -> str:
        return """# AITP Command Harness

These OpenCode commands route work through the installed `aitp` CLI instead of
letting topic work drift into ad hoc file browsing.

Required pattern:

1. enter through `aitp loop` whenever the topic already exists
2. use `aitp bootstrap` only to create a new topic shell, then return to `aitp loop`
3. inspect `runtime_protocol.generated.md` and the other generated runtime artifacts
4. register reusable operations with `aitp operation-init`
5. do the actual work
6. close with `aitp audit --phase exit`

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
3. Read the generated `runtime_protocol.generated.md`, `agent_brief.md`, `operator_console.md`, `capability_report.md`, and `conformance_report.md`.
4. Continue the task only after the runtime artifacts exist and conformance passes.
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

Then read the generated runtime artifacts before continuing.
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

Then inspect `runtime_protocol.generated.md`, `loop_state.json`, `capability_report.md`, and `conformance_report.md`.
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
3. Read the generated runtime protocol bundle before deeper work.
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

Then inspect `runtime_protocol.generated.md`, `loop_state.json`, and `conformance_report.md`.
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
