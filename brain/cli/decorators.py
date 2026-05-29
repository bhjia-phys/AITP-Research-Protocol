"""Stage gate and preflight decorators for AITP MCP tools.

Provides:
  - @require_stage     — block tool calls if the topic is at the wrong stage
  - @with_preflight    — run preflight checks from command policy before execution

Both decorators are idempotent and can be stacked.
"""

from __future__ import annotations

import inspect
from functools import wraps
from pathlib import Path
from typing import Any


# ── Stage permissions ────────────────────────────────────────────────────

STAGE_PERMISSIONS: dict[str, dict[str, list[str]]] = {
    "L0": {
        "allow": [
            "aitp_register_source", "aitp_list_sources", "aitp_request_source_evidence",
            "aitp_get_execution_brief", "aitp_get_status", "aitp_list_topics",
            "aitp_bootstrap_topic", "aitp_bind_repo",
            "aitp_query_l2", "aitp_query_l2_index", "aitp_query_l2_graph",
            "aitp_query_entries", "aitp_get_l2_provenance",
            "aitp_visualize_knowledge_graph", "aitp_visualize_eft_tower",
            "aitp_visualize_derivation_chain",
            "aitp_session_resume", "aitp_health_check",
            "aitp_set_compute_target", "aitp_set_interaction_level",
            "aitp_load_domain_manifest",
        ],
        "deny": [
            "aitp_create_derivation_step", "aitp_submit_candidate", "aitp_submit_idea",
            "aitp_promote_idea_to_candidate", "aitp_list_candidates",
            "aitp_submit_l4_review", "aitp_l4_background_submit",
            "aitp_l4_check_results", "aitp_record_numerical_result",
            "aitp_l4_analyze_run",
            "aitp_promote_candidate", "aitp_request_promotion", "aitp_resolve_promotion_gate",
            "aitp_fast_track_claim",
            "aitp_create_l2_node", "aitp_create_l2_edge", "aitp_create_l2_tower",
            "aitp_create_entry", "aitp_update_l2_node", "aitp_merge_subgraph_delta",
            "aitp_quick_l2_concept",
        ],
    },
    "L1": {
        "allow": [
            # L0 tools +
            "aitp_parse_source_toc", "aitp_update_section_status",
            "aitp_write_section_intake", "aitp_batch_extract_section",
            "aitp_advance_to_l3", "aitp_retreat_to_l0",
        ],
        "deny": [
            "aitp_submit_candidate", "aitp_submit_idea",
            "aitp_promote_idea_to_candidate", "aitp_list_candidates",
            "aitp_submit_l4_review", "aitp_l4_background_submit",
            "aitp_l4_check_results",
            "aitp_promote_candidate", "aitp_request_promotion", "aitp_resolve_promotion_gate",
            "aitp_create_l2_node", "aitp_create_l2_edge", "aitp_create_l2_tower",
            "aitp_create_entry", "aitp_update_l2_node", "aitp_merge_subgraph_delta",
        ],
    },
    "L3": {
        "allow": [],
        "deny": [
            "aitp_promote_candidate", "aitp_request_promotion", "aitp_resolve_promotion_gate",
        ],
    },
    "L4": {
        "allow": [],
        "deny": [
            "aitp_create_derivation_step",
            "aitp_register_source",
        ],
    },
}


def _resolve_topic_root(topics_root: str, topic_slug: str | None) -> Path | None:
    """Resolve the topic root directory from topics_root and slug."""
    if not topic_slug:
        return None
    base = Path(topics_root)
    # Support both <topics_root>/<slug> and <topics_root>/topics/<slug>
    for candidate in [base / topic_slug, base / "topics" / topic_slug]:
        state_path = candidate / "state.md"
        if state_path.exists():
            return candidate
    return base / topic_slug


def _load_topic_stage(topic_root: Path) -> str:
    from brain.cli.state import load_state
    state_path = topic_root / "state.md"
    if not state_path.exists():
        return "L0"
    fm, _ = load_state(topic_root)
    return fm.get("stage", "L0")


def _load_topic_lane(topic_root: Path) -> str:
    from brain.cli.state import load_state
    state_path = topic_root / "state.md"
    if not state_path.exists():
        return "unspecified"
    fm, _ = load_state(topic_root)
    return fm.get("lane", "unspecified")


# ── Lane-aware permission overrides ─────────────────────────────────────

# Bash is split: Bash:local (everyone — file ops, local scripts),
# Bash:remote (code_method/toy_numeric — SSH/HPC).
# The base STAGE_PERMISSIONS lists canonical tool names; LANE_OVERRIDES
# adjusts allow/deny lists per lane at runtime.

LANE_OVERRIDES: dict[str, dict[str, dict[str, list[str]]]] = {
    "code_method": {
        "L3": {"allow_extra": ["Bash"]},  # includes Bash:remote (SSH/HPC)
        "L4": {"require_invariant_checks": True},
    },
    "formal_theory": {
        "L3": {"allow_extra": []},
        "L4": {"require_invariant_checks": False},
    },
    "unspecified": {
        "L3": {"allow_extra": []},
        "L4": {"require_invariant_checks": False},
    },
}


def require_stage(func):
    """Block MCP tool calls if the topic is not at an allowed stage.

    Uses the STAGE_PERMISSIONS table to check allow/deny lists.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            bound = inspect.signature(func).bind_partial(*args, **kwargs)
            topics_root = bound.arguments.get("topics_root")
            topic_slug = bound.arguments.get("topic_slug")
        except TypeError:
            topics_root = kwargs.get("topics_root")
            topic_slug = kwargs.get("topic_slug")

        if topic_slug:
            topic_root = _resolve_topic_root(topics_root, topic_slug)
            if topic_root and topic_root.exists():
                stage = _load_topic_stage(topic_root)
                lane = _load_topic_lane(topic_root)
                perms = STAGE_PERMISSIONS.get(stage, {"allow": [], "deny": []})
                tool_name = func.__name__

                # Apply lane overrides
                lane_overrides = LANE_OVERRIDES.get(lane, {}).get(stage, {})
                allow_extra = lane_overrides.get("allow_extra", [])
                deny_extra = lane_overrides.get("deny_extra", [])

                # Check deny list first (base + lane overrides)
                deny_list = perms.get("deny", []) + deny_extra
                if tool_name in deny_list:
                    return {
                        "error": (
                            f"Stage gate: {tool_name} is BLOCKED in stage {stage} "
                            f"(lane={lane}). "
                            f"Use 'aitp gate override' to bypass if intentional."
                        ),
                        "stage_gate_blocked": True,
                        "current_stage": stage,
                    }

                # Check allow list (if allow is non-empty, with lane extras)
                allow_list = perms.get("allow", []) + allow_extra
                if allow_list and "*" not in allow_list:
                    if tool_name not in allow_list:
                        return {
                            "error": (
                                f"Stage gate: {tool_name} is not in the allowed list "
                                f"for stage {stage} (lane={lane})."
                            ),
                            "stage_gate_blocked": True,
                            "current_stage": stage,
                        }

        return func(*args, **kwargs)
    return wrapper


def with_preflight(command_name: str):
    """Decorator: run preflight checks from the named command policy.

    The command_name must match a file in brain/commands/<command_name>.md.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                bound = inspect.signature(func).bind_partial(*args, **kwargs)
                topics_root = bound.arguments.get("topics_root")
                topic_slug = bound.arguments.get("topic_slug")
            except TypeError:
                topics_root = kwargs.get("topics_root")
                topic_slug = kwargs.get("topic_slug")

            if topic_slug:
                topic_root = _resolve_topic_root(topics_root, topic_slug)
                if topic_root and topic_root.exists():
                    from brain.cli.preflight import run_preflight
                    failures = run_preflight(command_name, topic_root, **kwargs)
                    if failures:
                        return {
                            "error": (
                                f"Preflight blocked {command_name}:\n" +
                                "\n".join(f"  • {f}" for f in failures)
                            ),
                            "preflight_status": "blocked",
                            "preflight_failures": failures,
                            "command": command_name,
                        }
            return func(*args, **kwargs)
        return wrapper
    return decorator
