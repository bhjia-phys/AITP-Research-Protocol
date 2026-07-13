# Compatibility shard 2 for brief.
from __future__ import annotations

def _operating_note_payload(location) -> dict[str, Any]:
    metadata = location.metadata or {}
    linked_records = location.linked_records or {}
    return {
        "location_id": location.location_id,
        "label": location.label,
        "uri": location.uri,
        "summary": location.summary,
        "status": location.status,
        "location_type": location.location_type,
        "artifact_role": linked_records.get("artifact_role", ""),
        "lane_policy": metadata.get("lane_policy", ""),
        "final_lane_gate": metadata.get("final_lane_gate", ""),
        "diagnostic_lane_labels": metadata.get("diagnostic_lane_labels", []),
        "forbidden_root": metadata.get("forbidden_root", ""),
        "clean_root": metadata.get("clean_mgo_root", metadata.get("clean_root", "")),
        "orientation_only": True,
    }

def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result

def _flatten(groups) -> list[str]:
    values: list[str] = []
    for group in groups:
        values.extend(group)
    return values

def _default_risk_assessment_payload(action_budget) -> dict[str, Any]:
    return {
        "level": action_budget.level,
        "score": 0,
        "signals": [],
        "trust_reductions": [],
        "action_budget": asdict(action_budget),
        "human_checkpoint_needed": action_budget.requires_human_checkpoint,
        "summary": "guided protocol: no active claim",
    }
