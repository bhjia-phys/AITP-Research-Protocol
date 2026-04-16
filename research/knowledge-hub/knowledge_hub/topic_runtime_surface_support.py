from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .layer_graph_support import build_layer_graph_payload, render_layer_graph_markdown


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def layer_graph_paths(service: Any, topic_slug: str) -> dict[str, Path]:
    runtime_root = service._runtime_root(topic_slug)
    return {
        "json": runtime_root / "layer_graph.generated.json",
        "note": runtime_root / "layer_graph.generated.md",
    }


def runtime_surface_roles(service: Any, topic_slug: str) -> dict[str, Any]:
    runtime_root = service._runtime_root(topic_slug)
    validation_review_bundle_paths = service._validation_review_bundle_paths(topic_slug)
    topic_completion_paths = service._topic_completion_paths(topic_slug)
    graph_paths = layer_graph_paths(service, topic_slug)
    return {
        "primary": {
            "runtime_machine": service._relativize(service._topic_synopsis_path(topic_slug)),
            "runtime_human": service._relativize(service._topic_dashboard_path(topic_slug)),
            "review_machine": service._relativize(validation_review_bundle_paths["json"]),
            "review_human": service._relativize(validation_review_bundle_paths["note"]),
            "registry_machine": service._relativize(service._active_topics_registry_paths()["json"]),
            "registry_human": service._relativize(service._active_topics_registry_paths()["note"]),
        },
        "derived": {
            "startup_bundle_machine": service._relativize(runtime_root / "runtime_protocol.generated.json"),
            "startup_bundle_human": service._relativize(runtime_root / "runtime_protocol.generated.md"),
            "layer_graph_machine": service._relativize(graph_paths["json"]),
            "layer_graph_human": service._relativize(graph_paths["note"]),
        },
        "compatibility": {
            "current_topic_machine": service._relativize(service._current_topic_memory_paths()["json"]),
            "current_topic_human": service._relativize(service._current_topic_memory_paths()["note"]),
            "operator_console": service._relativize(runtime_root / "operator_console.md"),
            "agent_brief": service._relativize(runtime_root / "agent_brief.md"),
        },
        "supporting": {
            "research_question_human": service._relativize(service._research_question_contract_paths(topic_slug)["note"]),
            "validation_contract_human": service._relativize(service._validation_contract_paths(topic_slug)["note"]),
            "promotion_readiness_human": service._relativize(service._promotion_readiness_path(topic_slug)),
            "gap_map_human": service._relativize(service._gap_map_path(topic_slug)),
            "iteration_journal_human": service._relativize(
                service._feedback_run_root(
                    topic_slug,
                    str((service.get_runtime_state(topic_slug)).get("latest_run_id") or ""),
                )
                / "iteration_journal.md"
            )
            if str((service.get_runtime_state(topic_slug)).get("latest_run_id") or "").strip()
            else "",
            "collaborator_profile_machine": service._relativize(runtime_root / "collaborator_profile.active.json"),
            "collaborator_profile_human": service._relativize(runtime_root / "collaborator_profile.active.md"),
            "topic_completion_human": service._relativize(topic_completion_paths["note"]),
        },
    }


def materialize_layer_graph_artifact(
    service: Any,
    *,
    topic_slug: str,
    topic_state: dict[str, Any],
    bundle: dict[str, Any],
    updated_by: str,
) -> dict[str, Any]:
    topic_synopsis = bundle.get("topic_synopsis") or {}
    runtime_focus = topic_synopsis.get("runtime_focus") or {}
    layer_graph_payload = build_layer_graph_payload(
        topic_slug=topic_slug,
        topic_state=topic_state,
        runtime_focus=runtime_focus,
        runtime_mode_payload={
            "runtime_mode": bundle.get("runtime_mode"),
            "active_submode": bundle.get("active_submode"),
            "transition_posture": bundle.get("transition_posture") or {},
        },
        promotion_readiness=bundle.get("promotion_readiness") or {},
        validation_review_bundle=bundle.get("validation_review_bundle") or {},
    )
    paths = layer_graph_paths(service, topic_slug)
    payload = {
        **layer_graph_payload,
        "updated_at": _now_iso(),
        "updated_by": updated_by,
        "path": service._relativize(paths["json"]),
        "note_path": service._relativize(paths["note"]),
    }
    _write_json(paths["json"], payload)
    _write_text(paths["note"], render_layer_graph_markdown(payload))
    return payload


def topic_layer_graph_payload(
    service: Any,
    *,
    topic_slug: str,
    updated_by: str,
) -> dict[str, Any]:
    protocol_paths = service._materialize_runtime_protocol_bundle(
        topic_slug=topic_slug,
        updated_by=updated_by,
        load_profile=None,
    )
    bundle = _read_json(Path(protocol_paths["runtime_protocol_path"])) or {}
    topic_state = _read_json(service._runtime_root(topic_slug) / "topic_state.json") or {}
    layer_graph = materialize_layer_graph_artifact(
        service,
        topic_slug=topic_slug,
        topic_state=topic_state,
        bundle=bundle,
        updated_by=updated_by,
    )
    paths = layer_graph_paths(service, topic_slug)
    return {
        "topic_slug": topic_slug,
        "current_stage": bundle.get("resume_stage") or topic_state.get("resume_stage"),
        "runtime_protocol_path": protocol_paths["runtime_protocol_path"],
        "runtime_protocol_note_path": protocol_paths["runtime_protocol_note_path"],
        "layer_graph": layer_graph,
        "layer_graph_path": str(paths["json"]),
        "layer_graph_note_path": str(paths["note"]),
        "primary_runtime_surfaces": runtime_surface_roles(service, topic_slug),
        "control_plane": bundle.get("control_plane") or {},
    }
