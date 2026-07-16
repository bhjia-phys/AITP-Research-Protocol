'Read-only compiler from research records to reusable-block candidates.'

from __future__ import annotations

from brain.v5.compat_module_loader import load_module_shards as _load_module_shards

_load_module_shards(
    globals(),
    __file__,
    (
    "_compat_shards/research_distillation/part_01.py",
    "_compat_shards/research_distillation/part_02.py",
    ),
)
del _load_module_shards

_build_legacy_research_distillation_candidates = build_research_distillation_candidates


def build_research_distillation_candidates(ws, session_id, *, limit=_DEFAULT_LIMIT):
    """Route semantic and mixed legacy candidates away from direct Skill drafting."""

    payload = dict(
        _build_legacy_research_distillation_candidates(ws, session_id, limit=limit)
    )
    candidates = []
    for raw in payload.get("candidates", []):
        candidate = dict(raw)
        kind = candidate.get("candidate_kind")
        if kind == "physics_semantic_fragment_candidate":
            candidate.update(
                {
                    "knowledge_route": "grounded_or_insight_review",
                    "distillation_state": "routes_to_knowledge_review",
                    "can_draft_reusable_block": False,
                    "target_surfaces": ["physics_assertion_candidate", "insight_candidate"],
                }
            )
        elif kind == "method_capsule_candidate":
            candidate.update(
                {
                    "knowledge_route": "mixed_split_required",
                    "distillation_state": "mixed_split_required",
                    "can_draft_reusable_block": False,
                    "target_surfaces": [
                        "physics_assertion_candidate",
                        "insight_candidate",
                        "tool_recipe_record",
                        "skill_distillation_candidate_record",
                    ],
                }
            )
        else:
            candidate.update(
                {
                    "knowledge_route": "procedural_review",
                    "can_draft_reusable_block": False,
                    "target_surfaces": _procedural_targets(candidate),
                }
            )
        candidates.append(candidate)
    payload["candidates"] = candidates
    payload["summary"] = _summary(candidates)
    routed_actions = [
        f"split and review candidate {item['candidate_id']} before knowledge review or procedural candidate recording"
        for item in candidates
        if item.get("knowledge_route") == "mixed_split_required"
    ]
    payload["next_valid_actions"] = _dedupe(
        [*routed_actions, *list(payload.get("next_valid_actions") or [])]
    )
    return payload


def _procedural_targets(candidate):
    targets = [
        value
        for value in candidate.get("target_surfaces", [])
        if value not in {"strategy_memory_record", "sensemaking_report_record"}
    ]
    return _dedupe([*targets, "skill_distillation_candidate_record"])
