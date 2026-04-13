from __future__ import annotations

from pathlib import Path
from typing import Any


def _build_l0_source_handoff(
    *,
    next_bounded_action: dict[str, Any],
    blocker_summary: list[str],
) -> dict[str, Any] | None:
    next_action_type = str(next_bounded_action.get("action_type") or "").strip()
    next_action_summary = str(next_bounded_action.get("summary") or "").strip().lower()
    blocker_text = " ".join(str(item or "").strip().lower() for item in blocker_summary)
    requires_handoff = next_action_type == "l0_source_expansion"
    requires_handoff = requires_handoff or any(
        needle in next_action_summary
        for needle in ("source", "citation", "prior-work", "reference", "literature")
    )
    requires_handoff = requires_handoff or "return to l0" in blocker_text
    if not requires_handoff:
        return None

    return {
        "status": "needs_sources",
        "summary": (
            "Start with discovery when you have a topic query, then fall back to direct arXiv "
            "registration when the paper id is already known."
        ),
        "primary_path": "source-layer/scripts/discover_and_register.py",
        "primary_when": "Use when you have a topic query rather than a fixed arXiv id.",
        "alternate_entries": [
            {
                "path": "source-layer/scripts/register_arxiv_source.py",
                "when": "Use when the arXiv id is already known.",
            },
            {
                "path": "intake/ARXIV_FIRST_SOURCE_INTAKE.md",
                "when": "Use for the exact command forms and intake workflow.",
            },
        ],
    }


class RuntimeTruthService:
    def __init__(self, service: Any) -> None:
        self._service = service

    def topic_synopsis_runtime_focus(
        self,
        *,
        topic_state: dict[str, Any],
        topic_status_explainability: dict[str, Any],
        dependency_state: dict[str, Any],
        promotion_readiness: dict[str, Any],
    ) -> dict[str, Any]:
        next_bounded_action = topic_status_explainability.get("next_bounded_action") or {}
        active_human_need = topic_status_explainability.get("active_human_need") or {}
        last_evidence_return = topic_status_explainability.get("last_evidence_return") or {}
        research_judgment = topic_status_explainability.get("research_judgment") or {}
        next_action_summary = (
            str(next_bounded_action.get("summary") or "").strip()
            or "No bounded action is currently selected."
        )
        summary = str(topic_status_explainability.get("current_status_summary") or "").strip()
        if not summary:
            summary = (
                f"Stage `{topic_state.get('resume_stage') or '(missing)'}`; "
                f"next `{next_action_summary}`; "
                f"human need `{active_human_need.get('kind') or 'none'}`; "
                f"last evidence `{last_evidence_return.get('kind') or 'none'}`."
            )
        why_this_topic_is_here = str(topic_status_explainability.get("why_this_topic_is_here") or "").strip()
        if not why_this_topic_is_here:
            why_this_topic_is_here = "AITP is holding the current bounded route defined by the runtime state."
        human_need_summary = str(active_human_need.get("summary") or "").strip()
        if not human_need_summary:
            human_need_summary = "No active human checkpoint is currently blocking the bounded loop."
        last_evidence_summary = str(last_evidence_return.get("summary") or "").strip()
        if not last_evidence_summary:
            last_evidence_summary = "No durable evidence-return artifact is currently recorded for this topic."
        dependency_summary = str(dependency_state.get("summary") or "").strip()
        if not dependency_summary:
            dependency_summary = "No dependency state recorded."
        blocker_summary = self._service._dedupe_strings(list(topic_status_explainability.get("blocker_summary") or []))
        l0_source_handoff = _build_l0_source_handoff(
            next_bounded_action=next_bounded_action,
            blocker_summary=blocker_summary,
        )
        default_momentum_status = "unknown"
        if str(active_human_need.get("status") or "").strip() == "requested":
            default_momentum_status = "held"
        elif str(last_evidence_return.get("kind") or "").strip() not in {"", "none"}:
            default_momentum_status = "advancing"
        elif str(next_bounded_action.get("action_id") or "").strip():
            default_momentum_status = "queued"
        default_judgment_summary = (
            f"Momentum `{default_momentum_status}`; stuckness `none`; surprise `none`."
        )
        payload = {
            "summary": summary,
            "why_this_topic_is_here": why_this_topic_is_here,
            "resume_stage": str(topic_state.get("resume_stage") or ""),
            "last_materialized_stage": str(topic_state.get("last_materialized_stage") or ""),
            "next_action_id": str(next_bounded_action.get("action_id") or "").strip() or None,
            "next_action_type": str(next_bounded_action.get("action_type") or "").strip() or None,
            "next_action_summary": next_action_summary,
            "human_need_status": str(active_human_need.get("status") or "none"),
            "human_need_kind": str(active_human_need.get("kind") or "none"),
            "human_need_summary": human_need_summary,
            "blocker_summary": blocker_summary,
            "last_evidence_kind": str(last_evidence_return.get("kind") or "none"),
            "last_evidence_summary": last_evidence_summary,
            "dependency_status": str(dependency_state.get("status") or "none"),
            "dependency_summary": dependency_summary,
            "promotion_status": str(promotion_readiness.get("status") or "not_ready"),
            "momentum_status": str((research_judgment.get("momentum") or {}).get("status") or default_momentum_status),
            "stuckness_status": str((research_judgment.get("stuckness") or {}).get("status") or "none"),
            "surprise_status": str((research_judgment.get("surprise") or {}).get("status") or "none"),
            "judgment_summary": str(research_judgment.get("summary") or default_judgment_summary),
        }
        if l0_source_handoff is not None:
            payload["l0_source_handoff"] = l0_source_handoff
        return payload

    def topic_synopsis_truth_sources(
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
        resolved_promotion_gate_path = self._service._normalize_artifact_path(promotion_gate_path)
        return {
            "topic_state_path": self._service._relativize(self._service._runtime_root(topic_slug) / "topic_state.json"),
            "research_question_contract_path": self._service._relativize(research_question_contract_path),
            "next_action_surface_path": self._service._next_action_truth_surface_path(
                topic_slug=topic_slug,
                topic_state=topic_state,
                interaction_state=interaction_state,
            ),
            "human_need_surface_path": self._service._human_need_truth_surface_path(
                idea_packet=idea_packet,
                operator_checkpoint=operator_checkpoint,
            ),
            "dependency_registry_path": self._service._relativize(self._service._active_topics_registry_paths()["json"]),
            "promotion_readiness_path": self._service._normalize_artifact_path(promotion_readiness_path)
            or self._service._relativize(self._service._runtime_root(topic_slug) / "promotion_readiness.json"),
            "promotion_gate_path": resolved_promotion_gate_path,
        }
