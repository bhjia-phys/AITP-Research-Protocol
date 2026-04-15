from __future__ import annotations

import json
from pathlib import Path
from typing import Any


FULL_TOPIC_REFERENCE_ARTIFACTS = [
    "topics/<topic_slug>/runtime/topic_state.json",
    "topics/<topic_slug>/runtime/topic_synopsis.json",
    "topics/<topic_slug>/runtime/topic_dashboard.md",
    "topics/<topic_slug>/runtime/runtime_protocol.generated.json",
    "topics/<topic_slug>/runtime/runtime_protocol.generated.md",
    "topics/<topic_slug>/runtime/session_start.contract.json",
    "topics/<topic_slug>/runtime/session_start.generated.md",
    "topics/<topic_slug>/runtime/idea_packet.json",
    "topics/<topic_slug>/runtime/idea_packet.md",
    "topics/<topic_slug>/runtime/operator_checkpoint.active.json",
    "topics/<topic_slug>/runtime/operator_checkpoint.active.md",
]


def exploration_session_paths(*, kernel_root: Path, exploration_id: str) -> dict[str, Path]:
    root = kernel_root / "runtime" / "explorations" / exploration_id
    return {
        "root": root,
        "json": root / "explore_session.json",
        "note": root / "explore_session.md",
        "promotion_json": root / "promotion_request.json",
        "promotion_note": root / "promotion_request.md",
    }


def build_exploration_session_payload(
    *,
    exploration_id: str,
    task: str,
    updated_at: str,
    updated_by: str,
    current_topic_slug: str | None,
    current_topic_note_path: str | None,
    current_topic_summary: str | None,
) -> dict[str, Any]:
    uses_current_topic_context = bool(current_topic_slug)
    must_read_now = (
        [
            {
                "path": str(current_topic_note_path or "").strip(),
                "reason": "Current-topic context is available. Read it before promoting this quick exploration into a full topic loop.",
            }
        ]
        if str(current_topic_note_path or "").strip()
        else []
    )
    summary = (
        f"Quick exploration stays lightweight while reusing current-topic context from `{current_topic_slug}`."
        if uses_current_topic_context
        else "Quick exploration stays lightweight and does not bootstrap a full topic loop."
    )
    return {
        "session_kind": "quick_exploration",
        "exploration_id": exploration_id,
        "status": "lightweight_open",
        "task": task,
        "summary": summary,
        "updated_at": updated_at,
        "updated_by": updated_by,
        "current_topic_slug": current_topic_slug,
        "current_topic_summary": str(current_topic_summary or "").strip(),
        "topic_bootstrap_skipped": True,
        "artifact_count": 2,
        "runtime_mode": "explore",
        "load_profile": "light",
        "artifact_footprint": {
            "status": "lighter_than_full_topic",
            "quick_exploration_artifact_count": 2,
            "quick_exploration_artifacts": [],
            "reference_full_topic_artifact_count": len(FULL_TOPIC_REFERENCE_ARTIFACTS),
            "avoided_full_topic_artifacts": FULL_TOPIC_REFERENCE_ARTIFACTS,
            "reduction_vs_full_topic": len(FULL_TOPIC_REFERENCE_ARTIFACTS) - 2,
        },
        "must_read_now": must_read_now,
        "boundaries": [
            "This quick exploration does not bootstrap a full topic loop.",
            "This quick exploration does not claim L1, L3, or L4 completion.",
            "Promote it into `aitp session-start` when durable topic artifacts are actually needed.",
        ],
        "promotion_paths": {
            "stay_lightweight_command": f'aitp explore "{task}"',
            "promote_to_current_topic_command": f'aitp session-start --current-topic "{task}"' if uses_current_topic_context else None,
            "promote_to_new_topic_command": f'aitp session-start "{task}"',
        },
    }


def render_exploration_session_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Quick exploration session",
        "",
        f"- Exploration id: `{payload.get('exploration_id') or '(missing)'}`",
        f"- Status: `{payload.get('status') or '(missing)'}`",
        f"- Runtime mode: `{payload.get('runtime_mode') or '(missing)'}`",
        f"- Load profile: `{payload.get('load_profile') or '(missing)'}`",
        f"- Updated at: `{payload.get('updated_at') or '(missing)'}`",
        f"- Updated by: `{payload.get('updated_by') or '(missing)'}`",
        f"- Current topic: `{payload.get('current_topic_slug') or '(none)'}`",
        "",
        f"{payload.get('summary') or '(missing)'}",
        "",
        "## Task",
        "",
        payload.get("task") or "(missing)",
        "",
        "## Boundaries",
        "",
    ]
    for item in payload.get("boundaries") or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Must read now", ""])
    for item in payload.get("must_read_now") or [{"path": "(none)", "reason": "No current-topic context is pinned yet."}]:
        lines.append(f"- `{item['path']}` - {item['reason']}")
    footprint = payload.get("artifact_footprint") or {}
    lines.extend(
        [
            "",
            "## Artifact footprint",
            "",
            f"- Status: `{footprint.get('status') or '(missing)'}`",
            f"- Quick exploration artifact count: `{footprint.get('quick_exploration_artifact_count') or 0}`",
            f"- Full-topic reference artifact count: `{footprint.get('reference_full_topic_artifact_count') or 0}`",
            f"- Reduction vs full topic: `{footprint.get('reduction_vs_full_topic') or 0}`",
            "",
        ]
    )
    for item in footprint.get("quick_exploration_artifacts") or ["(missing)"]:
        lines.append(f"- produced: `{item}`")
    for item in footprint.get("avoided_full_topic_artifacts") or ["(none)"]:
        lines.append(f"- avoided: `{item}`")
    lines.extend(["", "## Promotion paths", ""])
    promotion_paths = payload.get("promotion_paths") or {}
    for key in ("stay_lightweight_command", "promote_to_current_topic_command", "promote_to_new_topic_command"):
        value = promotion_paths.get(key)
        lines.append(f"- {key}: `{value or '(none)'}`")
    return "\n".join(lines) + "\n"


def materialize_exploration_session(*, kernel_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    paths = exploration_session_paths(kernel_root=kernel_root, exploration_id=str(payload.get("exploration_id") or "explore"))
    paths["root"].mkdir(parents=True, exist_ok=True)
    payload = dict(payload)
    footprint = dict(payload.get("artifact_footprint") or {})
    footprint["quick_exploration_artifacts"] = [
        str(paths["json"].relative_to(kernel_root)),
        str(paths["note"].relative_to(kernel_root)),
    ]
    payload["artifact_footprint"] = footprint
    paths["json"].write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    paths["note"].write_text(render_exploration_session_markdown(payload), encoding="utf-8")
    return {
        **payload,
        "exploration_session_path": str(paths["json"]),
        "exploration_session_note_path": str(paths["note"]),
    }


def load_exploration_session(*, kernel_root: Path, exploration_id: str) -> dict[str, Any]:
    path = exploration_session_paths(kernel_root=kernel_root, exploration_id=exploration_id)["json"]
    return json.loads(path.read_text(encoding="utf-8"))


def build_exploration_promotion_request(
    *,
    exploration_payload: dict[str, Any],
    updated_at: str,
    updated_by: str,
    target_mode: str,
    promoted_session: dict[str, Any],
) -> dict[str, Any]:
    return {
        "request_kind": "exploration_promotion",
        "exploration_id": str(exploration_payload.get("exploration_id") or ""),
        "status": "promoted",
        "task": str(exploration_payload.get("task") or ""),
        "target_mode": target_mode,
        "current_topic_slug": exploration_payload.get("current_topic_slug"),
        "updated_at": updated_at,
        "updated_by": updated_by,
        "promoted_session": {
            "topic_slug": promoted_session.get("topic_slug"),
            "routing": promoted_session.get("routing") or {},
            "session_start_contract_path": promoted_session.get("session_start_contract_path"),
            "session_start_note_path": promoted_session.get("session_start_note_path"),
        },
    }


def render_exploration_promotion_markdown(payload: dict[str, Any]) -> str:
    session = payload.get("promoted_session") or {}
    return "\n".join(
        [
            "# Exploration promotion request",
            "",
            f"- Exploration id: `{payload.get('exploration_id') or '(missing)'}`",
            f"- Status: `{payload.get('status') or '(missing)'}`",
            f"- Target mode: `{payload.get('target_mode') or '(missing)'}`",
            f"- Updated at: `{payload.get('updated_at') or '(missing)'}`",
            f"- Updated by: `{payload.get('updated_by') or '(missing)'}`",
            f"- Promoted topic slug: `{session.get('topic_slug') or '(missing)'}`",
            f"- Session-start contract: `{session.get('session_start_contract_path') or '(missing)'}`",
            "",
            payload.get("task") or "(missing)",
            "",
        ]
    ) + "\n"


def materialize_exploration_promotion_request(*, kernel_root: Path, exploration_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    paths = exploration_session_paths(kernel_root=kernel_root, exploration_id=exploration_id)
    paths["root"].mkdir(parents=True, exist_ok=True)
    paths["promotion_json"].write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    paths["promotion_note"].write_text(render_exploration_promotion_markdown(payload), encoding="utf-8")
    return {
        **payload,
        "promotion_request_path": str(paths["promotion_json"]),
        "promotion_request_note_path": str(paths["promotion_note"]),
    }
