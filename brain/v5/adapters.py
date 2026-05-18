"""Runtime adapter packets for AITP v5 agents."""

from __future__ import annotations

from typing import Any

from brain.v5.adapter_protocols import build_adapter_protocols, supported_runtimes
from brain.v5.brief import build_execution_brief
from brain.v5.contracts import require_valid_adapter_packet, require_valid_execution_brief
from brain.v5.paths import WorkspacePaths
from brain.v5.public_surfaces import describe_public_surfaces
from brain.v5.runtime_entrypoints import runtime_entrypoints
from brain.v5.summaries import read_summary_orientation, write_session_summary


def build_adapter_packet(ws: WorkspacePaths, session_id: str, *, runtime: str = "codex") -> dict[str, Any]:
    """Build the compact packet an external agent should read on entry.

    The packet deliberately separates orientation surfaces from trusted kernel
    state so weaker models get useful context without being invited to trust a
    hand-edited Markdown summary.
    """

    normalized_runtime = _normalize_runtime(runtime)
    summary = write_session_summary(ws, session_id)
    orientation = read_summary_orientation(ws, session_id)
    brief = require_valid_execution_brief(build_execution_brief(ws, session_id))
    focus = brief["current_focus"]

    packet = {
        "kind": "adapter_packet",
        "runtime": normalized_runtime,
        "session_id": session_id,
        "topic_id": brief["session"]["topic_id"],
        "truth_sources": ["typed_records", "execution_brief"],
        "orientation_surfaces": summary.files,
        "summary_orientation": orientation,
        "execution_brief": brief,
        "trusted_focus": {
            "active_claim": focus["active_claim"],
            "claim_statement": focus["claim_statement"],
            "confidence_state": focus["confidence_state"],
            "evidence_profile": focus["evidence_profile"],
            "main_uncertainty": focus["main_uncertainty"],
            "flow_profile": brief["flow_profile"]["profile"],
            "risk_level": brief["risk_assessment"]["level"],
        },
        "adapter_contract": {
            "summary_files_are_truth_source": False,
            "summary_files_can_update_kernel_state": False,
            "kernel_must_be_called_before_trust_updates": True,
            "regenerated_from": "kernel_state",
        },
        "public_surface_audit": describe_public_surfaces(),
        "runtime_entrypoints": runtime_entrypoints(),
        **build_adapter_protocols(),
        "runtime_rules": _runtime_rules(normalized_runtime),
    }
    return require_valid_adapter_packet(packet)


def _normalize_runtime(runtime: str) -> str:
    value = runtime.strip().lower().replace("-", "_")
    if value in supported_runtimes():
        return value
    return "codex"


def _runtime_rules(runtime: str) -> list[str]:
    common_first = "read_for_orientation_only: task_plan/findings/progress are compact views, not truth sources"
    if runtime == "claude_code":
        return [
            common_first,
            "Use MCP wrappers for execution brief, evidence, tool-run, risk, and summary updates.",
            "Before validation or promotion, re-query the kernel and attach typed evidence references.",
        ]
    if runtime == "opencode":
        return [
            common_first,
            "Use CLI entrypoints for execution brief, summaries, evidence, tool runs, and risk checks.",
            "Do not infer confidence changes from local planning files alone.",
        ]
    return [
        common_first,
        "Use CLI or MCP entrypoints for execution brief, summaries, evidence, tool runs, and risk checks.",
        "Keep worktree/code provenance attached before trusting code-method results.",
    ]
