#!/usr/bin/env python3
"""Helpers for declarative AITP research-mode profiles."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

PROFILE_PATH = Path(__file__).resolve().parents[1] / "research_mode_profiles.json"
SIGNALS_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "lane_and_mode_signals.json"


def _slugify(text: str) -> str:
    lowered = text.lower().replace("/", " ").replace("-", "_")
    lowered = re.sub(r"[^a-z0-9_]+", "_", lowered)
    lowered = re.sub(r"_+", "_", lowered).strip("_")
    return lowered


@lru_cache(maxsize=1)
def load_registry() -> dict:
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_signals_config() -> dict:
    if not SIGNALS_CONFIG_PATH.exists():
        return {}
    return json.loads(SIGNALS_CONFIG_PATH.read_text(encoding="utf-8"))


def profile_path_ref() -> str:
    return "runtime/research_mode_profiles.json"


def default_research_mode() -> str:
    registry = load_registry()
    return str(registry.get("default_research_mode") or "exploratory_general")


def available_modes() -> set[str]:
    registry = load_registry()
    return set((registry.get("profiles") or {}).keys())


def normalize_research_mode(value: str | None) -> str | None:
    if not value:
        return None
    token = _slugify(str(value))
    aliases = _load_signals_config().get("mode_aliases") or {}
    token = aliases.get(token, token)
    return token if token in available_modes() else None


def profile_for_mode(research_mode: str | None) -> dict:
    registry = load_registry()
    profiles = registry.get("profiles") or {}
    normalized = normalize_research_mode(research_mode) or default_research_mode()
    profile = profiles.get(normalized) or profiles.get(default_research_mode()) or {}
    return {
        "research_mode": normalized,
        "profile_path": profile_path_ref(),
        **profile,
    }


def _signals_for_mode(mode: str) -> list[str]:
    cfg = _load_signals_config()
    mapping = {
        "first_principles": "first_principles",
        "toy_model": "toy_model",
        "formal_derivation": "formal_derivation",
    }
    key = mapping.get(mode)
    if not key:
        return []
    entry = (cfg.get("lane_signals") or {}).get(key)
    return list(entry.get("markers") or []) if entry else []


def _load_recorded_classification(
    classification_contract_path: Path | str | None,
) -> str | None:
    if not classification_contract_path:
        return None
    path = Path(classification_contract_path)
    if not path.exists():
        return None
    rows: list[dict] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    research_mode_rows = [r for r in rows if r.get("classification_type") == "research_mode"]
    if research_mode_rows:
        return research_mode_rows[-1].get("value")
    return None


def infer_research_mode(
    *,
    explicit_mode: str | None = None,
    task_payload: dict | None = None,
    route: dict | None = None,
    existing_topic_state: dict | None = None,
    classification_contract_path: str | None = None,
) -> str:
    for candidate in (
        explicit_mode,
        (task_payload or {}).get("research_mode"),
        (route or {}).get("research_mode"),
        (existing_topic_state or {}).get("research_mode"),
    ):
        normalized = normalize_research_mode(str(candidate) if candidate is not None else None)
        if normalized:
            return normalized

    recorded = _load_recorded_classification(classification_contract_path)
    if recorded:
        normalized = normalize_research_mode(recorded)
        if normalized:
            return normalized

    surface = str(
        (task_payload or {}).get("surface")
        or (route or {}).get("surface")
        or ""
    ).strip()
    if surface == "formal":
        return "formal_derivation"

    combined_text = " ".join(
        str(value or "")
        for value in (
            (task_payload or {}).get("summary"),
            (task_payload or {}).get("human_summary"),
            (route or {}).get("objective"),
            (route or {}).get("route_type"),
        )
    ).lower()

    for mode in ("first_principles", "toy_model", "formal_derivation"):
        if any(marker in combined_text for marker in _signals_for_mode(mode)):
            return mode

    if surface == "numerical":
        return "first_principles"
    if surface == "symbolic":
        return "formal_derivation"
    return default_research_mode()


def resolve_task_research_profile(
    *,
    explicit_mode: str | None = None,
    task_payload: dict | None = None,
    route: dict | None = None,
    existing_topic_state: dict | None = None,
    classification_contract_path: str | None = None,
) -> dict:
    research_mode = infer_research_mode(
        explicit_mode=explicit_mode,
        task_payload=task_payload,
        route=route,
        existing_topic_state=existing_topic_state,
        classification_contract_path=classification_contract_path,
    )
    profile = profile_for_mode(research_mode)

    executor_kind = str(
        (task_payload or {}).get("executor_kind")
        or (route or {}).get("executor_kind")
        or profile.get("default_executor_kind")
        or "codex_cli"
    ).strip()
    assigned_runtime = str(
        (task_payload or {}).get("assigned_runtime")
        or (route or {}).get("assigned_runtime")
        or profile.get("default_runtime_lane")
        or "codex"
    ).strip()
    reasoning_profile = str(
        (task_payload or {}).get("reasoning_profile")
        or (route or {}).get("reasoning_profile")
        or profile.get("reasoning_profile")
        or "medium"
    ).strip()

    return {
        "research_mode": research_mode,
        "profile": profile,
        "executor_kind": executor_kind,
        "assigned_runtime": assigned_runtime,
        "reasoning_profile": reasoning_profile,
        "reproducibility_expectations": list(profile.get("reproducibility_expectations") or []),
        "note_expectations": list(profile.get("note_expectations") or []),
    }
