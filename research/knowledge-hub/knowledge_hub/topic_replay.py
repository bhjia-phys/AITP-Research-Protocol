from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _runtime_root(kernel_root: Path, topic_slug: str) -> Path:
    return kernel_root / "runtime" / "topics" / topic_slug


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _existing_note(path: Path, *, kernel_root: Path) -> str | None:
    return _rel(path, kernel_root) if path.exists() else None


def _first_text(*values: object) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def build_topic_replay_bundle(kernel_root: Path, topic_slug: str) -> dict[str, Any]:
    kernel_root = kernel_root.resolve()
    topic_root = _runtime_root(kernel_root, topic_slug)
    if not topic_root.exists():
        raise FileNotFoundError(f"Missing runtime topic root: {topic_root}")

    synopsis = read_json(topic_root / "topic_synopsis.json") or {}
    topic_state = read_json(topic_root / "topic_state.json") or {}
    research_question = read_json(topic_root / "research_question.contract.json") or {}
    review_bundle = read_json(topic_root / "validation_review_bundle.active.json") or {}
    topic_completion = read_json(topic_root / "topic_completion.json") or {}
    projection = read_json(topic_root / "topic_skill_projection.active.json") or {}
    next_action = read_json(topic_root / "next_action_decision.json") or {}

    overview = {
        "topic_slug": topic_slug,
        "title": _first_text(synopsis.get("title"), research_question.get("title"), topic_slug),
        "question": _first_text(synopsis.get("question"), research_question.get("question")),
        "lane": _first_text(synopsis.get("lane"), topic_state.get("research_mode")),
        "human_request": _first_text(synopsis.get("human_request")),
    }

    current_position = {
        "resume_stage": _first_text(topic_state.get("resume_stage")),
        "last_materialized_stage": _first_text(topic_state.get("last_materialized_stage")),
        "latest_run_id": _first_text(topic_state.get("latest_run_id"), topic_completion.get("run_id")),
        "status_summary": _first_text(
            ((topic_state.get("status_explainability") or {}).get("current_status_summary")),
            topic_state.get("summary"),
        ),
        "next_action_summary": _first_text(
            synopsis.get("next_action_summary"),
            ((next_action.get("selected_action") or {}).get("summary")),
            ((topic_state.get("status_explainability") or {}).get("next_bounded_action") or {}).get("summary"),
        ),
        "open_gap_summary": _first_text(synopsis.get("open_gap_summary"), topic_completion.get("summary")),
    }

    conclusions = {
        "topic_completion_status": _first_text(topic_completion.get("status")),
        "topic_completion_summary": _first_text(topic_completion.get("summary")),
        "validation_review_status": _first_text(review_bundle.get("status")),
        "validation_review_summary": _first_text(review_bundle.get("summary")),
        "projection_status": _first_text(projection.get("status")),
        "projection_summary": _first_text(projection.get("summary")),
        "promoted_units": [str(item) for item in (((topic_state.get("promotion_gate") or {}).get("promoted_units")) or []) if str(item).strip()],
        "promotion_ready_candidate_ids": [str(item) for item in (topic_completion.get("promotion_ready_candidate_ids") or []) if str(item).strip()],
        "blocked_candidate_ids": [str(item) for item in (topic_completion.get("blocked_candidate_ids") or []) if str(item).strip()],
        "open_gap_ids": [str(item) for item in (topic_completion.get("open_gap_ids") or []) if str(item).strip()],
        "blockers": [str(item) for item in (topic_completion.get("blockers") or review_bundle.get("blockers") or []) if str(item).strip()],
    }

    reading_path = []

    def add_step(label: str, filename: str, reason: str, *, required: bool = False) -> None:
        path = topic_root / filename
        if path.exists():
            reading_path.append(
                {
                    "label": label,
                    "path": _rel(path, kernel_root),
                    "reason": reason,
                    "required": required,
                }
            )

    add_step("Current dashboard", "topic_dashboard.md", "Start here for the current human-facing topic state.", required=True)
    add_step("Question contract", "research_question.contract.md", "Read the bounded question, scope, deliverables, and forbidden proxies.", required=True)
    add_step("Validation review bundle", "validation_review_bundle.active.md", "Review the active L4 evidence and specialist artifacts when present.")
    add_step("Topic completion", "topic_completion.md", "Check what the topic currently claims to have completed or promoted.")
    add_step("Reusable projection", "topic_skill_projection.active.md", "Inspect reusable route memory when the topic already yielded a projection.")
    add_step("Runtime protocol", "runtime_protocol.generated.md", "Use the runtime read-order bundle for deeper protocol navigation.")
    add_step("Resume note", "resume.md", "See the compact resume context and additional pointers.")

    authoritative_artifacts = {
        "topic_synopsis_path": _existing_note(topic_root / "topic_synopsis.json", kernel_root=kernel_root),
        "topic_dashboard_path": _existing_note(topic_root / "topic_dashboard.md", kernel_root=kernel_root),
        "research_question_path": _existing_note(topic_root / "research_question.contract.md", kernel_root=kernel_root),
        "validation_review_bundle_path": _existing_note(topic_root / "validation_review_bundle.active.md", kernel_root=kernel_root),
        "topic_completion_path": _existing_note(topic_root / "topic_completion.md", kernel_root=kernel_root),
        "topic_skill_projection_path": _existing_note(topic_root / "topic_skill_projection.active.md", kernel_root=kernel_root),
        "runtime_protocol_path": _existing_note(topic_root / "runtime_protocol.generated.md", kernel_root=kernel_root),
        "resume_path": _existing_note(topic_root / "resume.md", kernel_root=kernel_root),
    }

    missing_artifacts = [name for name, path in authoritative_artifacts.items() if path is None]

    return {
        "kind": "topic_replay_bundle",
        "bundle_version": 1,
        "generated_at": now_iso(),
        "topic_slug": topic_slug,
        "source_contract_path": "TOPIC_REPLAY_PROTOCOL.md",
        "overview": overview,
        "current_position": current_position,
        "conclusions": conclusions,
        "reading_path": reading_path,
        "authoritative_artifacts": authoritative_artifacts,
        "missing_artifacts": missing_artifacts,
    }


def render_topic_replay_bundle_markdown(payload: dict[str, Any]) -> str:
    overview = payload.get("overview") or {}
    current = payload.get("current_position") or {}
    conclusions = payload.get("conclusions") or {}
    lines = [
        "# Topic Replay Bundle",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Generated at: `{payload.get('generated_at') or '(missing)'}`",
        f"- Source contract: `{payload.get('source_contract_path') or '(missing)'}`",
        "",
        "## Overview",
        "",
        f"- Title: `{overview.get('title') or '(missing)'}`",
        f"- Question: {overview.get('question') or '(missing)' }",
        f"- Lane / mode: `{overview.get('lane') or '(missing)'}`",
        f"- Human request: {overview.get('human_request') or '(none recorded)' }",
        "",
        "## Current Position",
        "",
        f"- Resume stage: `{current.get('resume_stage') or '(missing)'}`",
        f"- Last materialized stage: `{current.get('last_materialized_stage') or '(missing)'}`",
        f"- Latest run id: `{current.get('latest_run_id') or '(missing)'}`",
        f"- Status summary: {current.get('status_summary') or '(missing)' }",
        f"- Next action summary: {current.get('next_action_summary') or '(missing)' }",
        f"- Open gap summary: {current.get('open_gap_summary') or '(none recorded)' }",
        "",
        "## What This Topic Currently Says",
        "",
        f"- Topic completion status: `{conclusions.get('topic_completion_status') or '(missing)'}`",
        f"- Topic completion summary: {conclusions.get('topic_completion_summary') or '(missing)' }",
        f"- Validation review status: `{conclusions.get('validation_review_status') or '(missing)'}`",
        f"- Validation review summary: {conclusions.get('validation_review_summary') or '(missing)' }",
        f"- Projection status: `{conclusions.get('projection_status') or '(missing)'}`",
        f"- Projection summary: {conclusions.get('projection_summary') or '(missing)' }",
        "",
        "## Reusable Outputs",
        "",
        f"- Promoted units: `{', '.join(conclusions.get('promoted_units') or []) or '(none)'}`",
        f"- Promotion-ready candidates: `{', '.join(conclusions.get('promotion_ready_candidate_ids') or []) or '(none)'}`",
        "",
        "## Reading Path",
        "",
    ]

    for idx, step in enumerate(payload.get("reading_path") or [], start=1):
        lines.append(
            f"{idx}. `{step.get('path') or '(missing)'}`"
        )
        lines.append(f"   - {step.get('reason') or '(missing reason)'}")

    if not (payload.get("reading_path") or []):
        lines.append("No reading-path steps could be materialized from the current topic artifacts.")

    lines.extend(["", "## Authoritative Artifacts", ""])
    for key, path in (payload.get("authoritative_artifacts") or {}).items():
        lines.append(f"- `{key}`: `{path or '(missing)'}`")

    lines.extend(["", "## Missing Artifacts", ""])
    missing = payload.get("missing_artifacts") or []
    if missing:
        for item in missing:
            lines.append(f"- `{item}`")
    else:
        lines.append("- `(none)`")

    lines.extend(
        [
            "",
            "## Replay Rule",
            "",
            "This bundle is derived for human study. When it conflicts with the underlying artifact files, the underlying artifacts win.",
            "",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def materialize_topic_replay_bundle(kernel_root: Path, topic_slug: str) -> dict[str, Any]:
    kernel_root = kernel_root.resolve()
    topic_root = _runtime_root(kernel_root, topic_slug)
    payload = build_topic_replay_bundle(kernel_root, topic_slug)
    json_path = topic_root / "topic_replay_bundle.json"
    md_path = topic_root / "topic_replay_bundle.md"
    write_json(json_path, payload)
    write_text(md_path, render_topic_replay_bundle_markdown(payload))
    return {
        "payload": payload,
        "json_path": str(json_path),
        "markdown_path": str(md_path),
    }
