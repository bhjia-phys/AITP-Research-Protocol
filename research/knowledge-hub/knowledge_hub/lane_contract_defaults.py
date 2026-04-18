"""Lane-aware defaults for the active research contract.

When a topic has no human-curated values for observables, target_claims, or
deliverables, the runtime falls back to generic template text that carries zero
physics content.  This module replaces those generic defaults with lane-specific
alternatives derived from ``template_mode``, ``research_mode``, and the topic's
existing content.

All functions are pure — they only read their inputs and return lists of strings.

Classification signals and contract defaults are loaded from
``config/lane_and_mode_signals.json``.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "lane_and_mode_signals.json"


@lru_cache(maxsize=1)
def _load_config() -> dict:
    return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))


def _lane_signals(lane_key: str) -> set[str]:
    cfg = _load_config()
    entry = (cfg.get("lane_signals") or {}).get(lane_key)
    if not entry:
        return set()
    return set(entry.get("markers") or [])


def detect_lane(
    *,
    template_mode: str,
    research_mode: str,
    topic_content_hints: dict[str, Any] | None = None,
) -> str:
    hints = topic_content_hints or {}
    tm = str(template_mode or "").strip().lower()
    cfg = _load_config()

    if tm == "formal_theory":
        return "formal_derivation"

    rm = str(research_mode or "").strip().lower()
    if tm == "code_method":
        text = _hint_text(hints)
        if _text_matches_signals(text, _lane_signals("toy_model")):
            return "toy_model"
        if _text_matches_signals(text, _lane_signals("first_principles")):
            return "first_principles"

    return "generic"


def lane_observables(lane: str, topic_context: dict[str, Any]) -> list[str]:
    question = str((topic_context or {}).get("question") or "").strip()
    cfg = _load_config()
    defaults = (cfg.get("lane_contract_defaults") or {}).get(lane)
    if defaults:
        base = list(defaults.get("observables") or [])
    else:
        base = [
            "Declared candidate ids, bounded claims, and validation outcomes.",
            "Promotion readiness, gap honesty, and whether the topic must return to L0.",
        ]
    if question:
        template = (defaults or {}).get("target_claims_template") or "Bounded question: {question}"
        base.insert(0, template.format(question=question))
    return base


def lane_target_claims(
    lane: str,
    topic_context: dict[str, Any],
    candidate_rows: list[dict[str, Any]] | None = None,
    selected_action: dict[str, Any] | None = None,
) -> list[str]:
    question = str((topic_context or {}).get("question") or "").strip()
    claims: list[str] = []

    if candidate_rows:
        for row in candidate_rows:
            cid = str(row.get("candidate_id") or "").strip()
            if cid and not _is_runtime_action_id(cid):
                claims.append(cid)

    if claims:
        return claims

    if question:
        short = question[:120] + ("..." if len(question) > 120 else "")
        claims.append(f"Bounded claim: {short}")
        return claims

    if selected_action:
        aid = str(selected_action.get("action_id") or "").strip()
        if aid:
            claims.append(aid)
            return claims

    return ["(no bounded claim registered yet)"]


def lane_deliverables(lane: str, topic_context: dict[str, Any]) -> list[str]:
    cfg = _load_config()
    defaults = (cfg.get("lane_contract_defaults") or {}).get(lane)
    if defaults:
        return list(defaults.get("deliverables") or [])

    return [
        "Persist the active research question, validation route, and bounded next action as durable runtime artifacts.",
        "Write derivation/proof or execution evidence into the appropriate AITP layer before claiming completion.",
        "Produce Layer-appropriate outputs that can later be promoted into durable L2 knowledge when justified.",
    ]


def lane_signals_config() -> dict:
    return _load_config().get("lane_signals") or {}


def full_lane_config() -> dict:
    return _load_config()


def known_research_modes() -> set[str]:
    return set(_load_config().get("known_research_modes") or [])


def mode_aliases() -> dict[str, str]:
    return dict(_load_config().get("mode_aliases") or {})


def template_mode_to_research_mode_map() -> dict[str, str]:
    return dict(_load_config().get("template_mode_to_research_mode") or {})


def research_mode_to_template_mode_map() -> dict[str, str]:
    return dict(_load_config().get("research_mode_to_template_mode") or {})


def return_to_l0_outcomes() -> set[str]:
    return set(_load_config().get("return_to_l0_outcomes") or [])


def valid_strategy_types() -> set[str]:
    return set(_load_config().get("valid_strategy_types") or [])


def _is_runtime_action_id(value: str) -> bool:
    import re
    return bool(re.match(r"^action:[^:]+:\d+$", value))


def _hint_text(hints: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("question", "scope", "source_basis_refs"):
        val = hints.get(key)
        if isinstance(val, str) and val.strip():
            parts.append(val.strip())
        elif isinstance(val, list):
            parts.extend(str(v).strip() for v in val if str(v).strip())
    l1 = hints.get("l1_source_intake") or {}
    for sub_key in ("assumption_rows", "interpretation_rows"):
        for row in l1.get(sub_key) or []:
            for field in ("assumption", "interpretation", "text"):
                v = str(row.get(field) or "").strip()
                if v:
                    parts.append(v)
    return " ".join(parts).lower()


def _text_matches_signals(text: str, signals: set[str]) -> bool:
    return any(s in text for s in signals)
