from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .research_judgment_runtime_support import materialize_research_judgment_surface
from .research_taste_support import materialize_research_taste_surface
from .topic_truth_root_support import compatibility_projection_path


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, ensure_ascii=True, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    compatibility_path = compatibility_projection_path(path)
    if compatibility_path is not None and compatibility_path != path:
        compatibility_path.parent.mkdir(parents=True, exist_ok=True)
        compatibility_path.write_text(rendered, encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    compatibility_path = compatibility_projection_path(path)
    if compatibility_path is not None and compatibility_path != path:
        compatibility_path.parent.mkdir(parents=True, exist_ok=True)
        compatibility_path.write_text(text, encoding="utf-8")


def materialize_research_state_surfaces(
    service: Any,
    *,
    runtime_root: Path,
    topic_slug: str,
    latest_run_id: str,
    updated_by: str,
    topic_status_explainability: dict[str, Any],
    selected_pending_action: dict[str, Any] | None,
    open_gap_summary: dict[str, Any],
    strategy_memory: dict[str, Any],
    dependency_state: dict[str, Any],
    gap_map_path: Path,
) -> tuple[dict[str, Path], dict[str, Any], dict[str, Path], dict[str, Any]]:
    research_judgment_paths, research_judgment = materialize_research_judgment_surface(
        service,
        runtime_root=runtime_root,
        topic_slug=topic_slug,
        latest_run_id=latest_run_id,
        updated_by=updated_by,
        topic_status_explainability=topic_status_explainability,
        selected_pending_action=selected_pending_action,
        open_gap_summary=open_gap_summary,
        strategy_memory=strategy_memory,
        dependency_state=dependency_state,
        gap_map_path=service._relativize(gap_map_path),
        write_json=_write_json,
        write_text=_write_text,
    )
    topic_status_explainability["research_judgment"] = research_judgment
    research_taste_paths, research_taste = materialize_research_taste_surface(
        service,
        runtime_root=runtime_root,
        topic_slug=topic_slug,
        updated_by=updated_by,
        research_judgment=research_judgment,
    )
    topic_status_explainability["research_taste"] = research_taste
    return research_judgment_paths, research_judgment, research_taste_paths, research_taste


def write_topic_dashboard_surface(
    service: Any,
    *,
    dashboard_path: Path,
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
) -> None:
    _write_text(
        dashboard_path,
        service._render_topic_dashboard_markdown(
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
        ),
    )


def finalize_topic_shell_outputs(
    service: Any,
    *,
    dashboard_path: Path,
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
    readiness_path: Path,
    open_gap_summary: dict[str, Any],
    gap_map_path: Path,
    strategy_memory: dict[str, Any],
    statement_compilation: dict[str, Any],
    topic_skill_projection: dict[str, Any],
    topic_completion: dict[str, Any],
    lean_bridge: dict[str, Any],
    dependency_state: dict[str, Any],
) -> None:
    write_topic_dashboard_surface(
        service,
        dashboard_path=dashboard_path,
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
    _write_text(readiness_path, service._render_promotion_readiness_markdown(promotion_readiness))
    _write_text(gap_map_path, service._render_gap_map_markdown(open_gap_summary))
    service._refresh_operator_console_checkpoint_section(
        topic_slug=topic_slug,
        operator_checkpoint=operator_checkpoint,
        topic_status_explainability=topic_status_explainability,
    )
