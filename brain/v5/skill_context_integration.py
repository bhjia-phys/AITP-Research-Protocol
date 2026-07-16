"""Bounded Skill discovery cards for compiled research context."""

from __future__ import annotations

from dataclasses import replace
import re
from typing import Any

from brain.v5.paths import WorkspacePaths
from brain.v5.skill_applicability import SkillApplicabilityRequest, match_applicable_skills


_MAX_CARDS = 4
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
_CARD_KEYS = frozenset(
    {
        "skill_id",
        "name",
        "semantic_version",
        "package_hash",
        "proposal_ref",
        "install_receipt_ref",
        "match_source",
        "confidence",
        "expand_operation",
        "use_operation",
    }
)
_FORBIDDEN_CARD_KEYS = frozenset(
    {
        "body",
        "skill_body",
        "manifest",
        "files",
        "ordered_steps",
        "validation_commands",
        "patch_body",
        "selector_reasons",
    }
)


def compile_requested_skill_context(
    ws: WorkspacePaths,
    request: SkillApplicabilityRequest | None,
    *,
    topic_id: str,
    program_id: str,
    disclosure_level: str,
) -> dict[str, Any]:
    if request is None or disclosure_level not in {
        "startup_orientation",
        "normal_research",
    }:
        return {}
    if request.topic_ids and topic_id not in request.topic_ids:
        raise ValueError("Skill request topic conflicts with resolved session scope")
    topic_ids = tuple(dict.fromkeys((*request.topic_ids, topic_id)))
    program_ids = tuple(
        dict.fromkeys((*request.program_ids, *((program_id,) if program_id else ())))
    )
    result = match_applicable_skills(
        ws,
        replace(request, topic_ids=topic_ids, program_ids=program_ids),
    )
    cards = tuple(_card(item) for item in result.matches[:_MAX_CARDS])
    payload = {
        "cards": cards,
        "checked_count": result.checked_count,
        "matched_count": len(result.matches),
        "rejected_count": len(result.rejected),
        "truncated": len(result.matches) > len(cards),
        "can_claim_no_applicable_skill": False,
        "orientation_only": True,
        "can_update_claim_trust": False,
    }
    errors = skill_context_payload_errors(cards)
    if errors:
        raise ValueError("invalid Skill context projection: " + "; ".join(errors))
    return payload


def _card(item: Any) -> dict[str, Any]:
    return {
        "skill_id": item.skill_id,
        "name": item.name,
        "semantic_version": item.semantic_version,
        "package_hash": item.package_hash,
        "proposal_ref": dict(item.proposal_ref),
        "install_receipt_ref": dict(item.install_receipt_ref),
        "match_source": item.match_source,
        "confidence": item.confidence,
        "expand_operation": "skill_match_applicable",
        "use_operation": "skill_record_usage",
    }


def skill_context_coverage(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "skill_context_requested": bool(payload),
        "skill_context_checked_count": int(payload.get("checked_count") or 0),
        "skill_context_matched_count": int(payload.get("matched_count") or 0),
        "skill_context_rejected_count": int(payload.get("rejected_count") or 0),
        "skill_context_truncated": bool(payload.get("truncated")),
        "can_claim_no_applicable_skill": False,
    }


def skill_context_lines(payload: dict[str, Any]) -> list[str]:
    cards = payload.get("cards") or ()
    if not cards:
        return []
    lines = ["", "## Applicable reviewed Skills"]
    for card in cards:
        lines.append(
            f"- {card['name']} {card['semantic_version']} "
            f"[{card['match_source']}; confidence={card['confidence']:.3f}] "
            f"({card['install_receipt_ref']['record_ref']})"
        )
    lines.append("- Expand with `skill_match_applicable`; record exact use with `skill_record_usage`.")
    return lines


def skill_context_handles(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload:
        return {}
    return {
        "applicable_skill_count": len(payload.get("cards") or ()),
        "applicable_skills_truncated": bool(payload.get("truncated")),
        "skill_expand_operation": "skill_match_applicable",
        "skill_use_operation": "skill_record_usage",
        "skill_bodies_in_context": False,
    }


def skill_context_payload_errors(cards: tuple[dict[str, Any], ...]) -> tuple[str, ...]:
    errors: list[str] = []
    if not isinstance(cards, tuple):
        return ("applicable_skills must be a tuple",)
    if len(cards) > _MAX_CARDS:
        errors.append(f"applicable_skills must contain at most {_MAX_CARDS} cards")
    for index, card in enumerate(cards):
        path = f"applicable_skills[{index}]"
        if not isinstance(card, dict):
            errors.append(f"{path} must be a mapping")
            continue
        if set(card) != _CARD_KEYS:
            errors.append(f"{path} must contain only the compact Skill card fields")
        if _contains_forbidden_key(card):
            errors.append(f"{path} cannot contain Skill bodies, manifests, or patch content")
        if not card.get("skill_id") or not card.get("name"):
            errors.append(f"{path} must identify one Skill")
        if not isinstance(card.get("semantic_version"), str) or not _SEMVER.fullmatch(
            card["semantic_version"]
        ):
            errors.append(f"{path}.semantic_version must be x.y.z")
        if not isinstance(card.get("package_hash"), str) or not _SHA256.fullmatch(
            card["package_hash"]
        ):
            errors.append(f"{path}.package_hash must be lowercase sha256")
        for field in ("proposal_ref", "install_receipt_ref"):
            if not _valid_pin(card.get(field)):
                errors.append(f"{path}.{field} must be an exact typed-record pin")
        if card.get("expand_operation") != "skill_match_applicable":
            errors.append(f"{path}.expand_operation is invalid")
        if card.get("use_operation") != "skill_record_usage":
            errors.append(f"{path}.use_operation is invalid")
        confidence = card.get("confidence")
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            errors.append(f"{path}.confidence must be numeric")
        elif not 0.0 <= float(confidence) <= 1.0:
            errors.append(f"{path}.confidence must be between zero and one")
    return tuple(errors)


def _valid_pin(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    record_ref = value.get("record_ref")
    content_hash = value.get("content_hash")
    revision = value.get("revision")
    if not isinstance(record_ref, str) or not all(record_ref.partition(":")):
        return False
    if not isinstance(content_hash, str) or not _SHA256.fullmatch(content_hash):
        return False
    return isinstance(revision, int) and not isinstance(revision, bool) and revision >= 1


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, dict):
        return bool(_FORBIDDEN_CARD_KEYS & set(value)) or any(
            _contains_forbidden_key(item) for item in value.values()
        )
    if isinstance(value, (tuple, list)):
        return any(_contains_forbidden_key(item) for item in value)
    return False


__all__ = [
    "compile_requested_skill_context",
    "skill_context_handles",
    "skill_context_lines",
    "skill_context_payload_errors",
    "skill_context_coverage",
]
