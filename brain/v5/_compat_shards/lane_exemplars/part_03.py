# Compatibility shard 3 for lane_exemplars.
from __future__ import annotations

def _lane_exemplar_body(record: LaneExemplarRecord) -> str:
    return (
        "# Lane Exemplar\n\n"
        f"Lane: {record.lane}\n\n"
        f"Title: {record.title}\n\n"
        f"Summary: {record.summary}\n\n"
        f"Trust boundary: {record.trust_boundary or 'Workflow exemplar only; not claim evidence.'}\n\n"
        "Gates demonstrated:\n"
        f"{_bullets(record.gates_demonstrated)}\n\n"
        "Artifacts:\n"
        f"{_bullets(record.artifact_refs)}\n\n"
        "Domain packs:\n"
        f"{_bullets(record.domain_pack_refs)}\n\n"
        "Context profiles:\n"
        f"{_bullets(record.context_profile_refs)}\n\n"
        "Skill refs:\n"
        f"{_bullets(record.skill_refs)}\n\n"
        "Workflow steps:\n"
        f"{_mapping_bullets(record.workflow_steps, label_key='step_id')}\n\n"
        "Failure modes:\n"
        f"{_mapping_bullets(record.failure_modes, label_key='failure_id')}\n\n"
        "Forbidden uses:\n"
        f"{_bullets(record.forbidden_uses)}\n"
    )

def _bullets(values: list[str]) -> str:
    return "\n".join(f"- {value}" for value in values) if values else "- None"

def _mapping_bullets(values: list[dict[str, Any]], *, label_key: str) -> str:
    if not values:
        return "- None"
    lines = []
    for value in values:
        if not isinstance(value, dict):
            lines.append(f"- {value}")
            continue
        label = str(value.get(label_key) or value.get("entrypoint") or value.get("purpose") or "item")
        detail = str(value.get("purpose") or value.get("signals") or value.get("required_basis") or "")
        lines.append(f"- {label}: {detail}" if detail else f"- {label}")
    return "\n".join(lines)

def _list_values(item: dict[str, Any], key: str) -> list[Any]:
    value = item.get(key)
    return list(value) if isinstance(value, list) else []

def _runtime_dir(ws: WorkspacePaths, topic_id: str) -> Path:
    return ws.topic_dir(topic_id) / "runtime"

def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
