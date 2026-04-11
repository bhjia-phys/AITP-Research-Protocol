from __future__ import annotations

from pathlib import Path
from typing import Any

from .research_judgment_support import (
    derive_research_judgment,
    empty_research_judgment,
    render_research_judgment_markdown,
)


def research_judgment_paths(runtime_root: Path) -> dict[str, Path]:
    return {
        "json": runtime_root / "research_judgment.active.json",
        "note": runtime_root / "research_judgment.active.md",
    }


def dashboard_research_judgment_lines(research_judgment: dict[str, Any]) -> list[str]:
    return [
        "## Research judgment",
        "",
        f"- Status: `{research_judgment.get('status') or '(missing)'}`",
        f"- Momentum: `{((research_judgment.get('momentum') or {}).get('status') or '(missing)')}`",
        f"- Stuckness: `{((research_judgment.get('stuckness') or {}).get('status') or '(missing)')}`",
        f"- Surprise: `{((research_judgment.get('surprise') or {}).get('status') or '(missing)')}`",
        f"- Note path: `{research_judgment.get('note_path') or '(missing)'}`",
        "",
        f"{research_judgment.get('summary') or '(missing)'}",
        "",
    ]


def append_research_judgment_markdown(lines: list[str], research_judgment: dict[str, Any]) -> None:
    lines.extend(
        [
            "## Research judgment",
            "",
            f"- Status: `{research_judgment.get('status') or '(missing)'}`",
            f"- Momentum: `{((research_judgment.get('momentum') or {}).get('status') or '(missing)')}`",
            f"- Stuckness: `{((research_judgment.get('stuckness') or {}).get('status') or '(missing)')}`",
            f"- Surprise: `{((research_judgment.get('surprise') or {}).get('status') or '(missing)')}`",
            f"- Note path: `{research_judgment.get('note_path') or '(missing)'}`",
            "",
            f"{research_judgment.get('summary') or '(missing)'}",
            "",
        ]
    )


def normalize_research_judgment_for_bundle(
    self,
    *,
    shell_surfaces: dict[str, Any],
    topic_slug: str,
    runtime_root: Path,
    latest_run_id: str,
    updated_by: str,
) -> dict[str, Any]:
    research_judgment = dict(
        shell_surfaces.get("research_judgment")
        or empty_research_judgment(
            topic_slug=topic_slug,
            run_id=latest_run_id,
            updated_by=updated_by,
        )
    )
    paths = research_judgment_paths(runtime_root)
    if not str(research_judgment.get("path") or "").strip():
        research_judgment["path"] = self._relativize(paths["json"])
    if not str(research_judgment.get("note_path") or "").strip():
        research_judgment["note_path"] = self._relativize(paths["note"])
    return research_judgment


def research_judgment_must_read_entry(research_judgment: dict[str, Any]) -> dict[str, str] | None:
    if str(research_judgment.get("status") or "") != "signals_active":
        return None
    note_path = str(research_judgment.get("note_path") or "").strip()
    if not note_path:
        return None
    return {
        "path": note_path,
        "reason": "Active research-judgment signals are recorded for this topic. Read them before trusting the bounded route at face value.",
    }


def decision_surface_snapshot(
    decision_surface: dict[str, Any],
    runtime_focus: dict[str, Any],
    research_judgment: dict[str, Any],
) -> dict[str, Any]:
    return {
        "decision_mode": decision_surface.get("decision_mode"),
        "decision_source": decision_surface.get("decision_source"),
        "decision_contract_status": decision_surface.get("decision_contract_status"),
        "control_note_path": decision_surface.get("control_note_path"),
        "selected_action_id": decision_surface.get("selected_action_id"),
        "momentum_status": runtime_focus.get("momentum_status"),
        "stuckness_status": runtime_focus.get("stuckness_status"),
        "surprise_status": runtime_focus.get("surprise_status"),
        "judgment_summary": runtime_focus.get("judgment_summary"),
        "research_judgment_note_path": research_judgment.get("note_path"),
    }


def materialize_research_judgment_surface(
    self,
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
    gap_map_path: str,
    write_json: Any,
    write_text: Any,
) -> tuple[dict[str, Path], dict[str, Any]]:
    paths = research_judgment_paths(runtime_root)
    payload = derive_research_judgment(
        self,
        topic_slug=topic_slug,
        latest_run_id=latest_run_id,
        updated_by=updated_by,
        topic_status_explainability=topic_status_explainability,
        selected_pending_action=selected_pending_action,
        open_gap_summary=open_gap_summary,
        strategy_memory=strategy_memory,
        dependency_state=dependency_state,
        gap_map_path=gap_map_path,
    )
    payload = {
        **payload,
        "path": self._relativize(paths["json"]),
        "note_path": self._relativize(paths["note"]),
    }
    write_json(paths["json"], payload)
    write_text(paths["note"], render_research_judgment_markdown(payload))
    return paths, payload
