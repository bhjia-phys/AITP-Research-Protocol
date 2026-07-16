"""Typed edge projection helpers for knowledge snapshots."""

from __future__ import annotations

from typing import Any, Mapping, Sequence


def record_links(frontmatter: Mapping[str, Any]) -> tuple[str, ...]:
    keys = (
        "object_ref",
        "subject_ref",
        "source_refs",
        "source_asset_refs",
        "source_location_refs",
        "contradiction_refs",
        "grounding_refs",
        "inferred_from_refs",
        "proof_obligation_refs",
        "dependency_step_refs",
        "invoked_knowledge_refs",
        "source_anchor_refs",
        "ordered_step_refs",
        "chain_ref",
        "step_refs",
        "validation_check_refs",
        "tool_run_check_refs",
        "checkpoint_ref",
    )
    refs: list[str] = []
    for key in keys:
        refs.extend(_refs(frontmatter.get(key)))
    metadata = _metadata(frontmatter)
    for key in (
        "formula_ref",
        "code_state_ref",
        "source_refs",
        "test_refs",
        "accepted_baseline_ref",
    ):
        refs.extend(_refs(metadata.get(key)))
    if metadata.get("schema_version") != "formula-code-relation/v1":
        subject_id = str(frontmatter.get("subject_id") or "")
        object_id = str(frontmatter.get("object_id") or "")
        if subject_id:
            refs.append(f"physics_object:{subject_id}")
        if object_id:
            refs.append(f"physics_object:{object_id}")
    return tuple(dict.fromkeys(refs))


def record_link_types(
    frontmatter: Mapping[str, Any],
) -> dict[str, tuple[str, ...]]:
    relation_keys = {
        "object_ref": "assertion_object",
        "subject_ref": "relation_subject",
        "source_refs": "source",
        "source_asset_refs": "source_asset",
        "source_location_refs": "source_location",
        "contradiction_refs": "contradiction",
        "grounding_refs": "grounding",
        "inferred_from_refs": "inferred_from",
        "proof_obligation_refs": "proof_obligation",
        "dependency_step_refs": "derivation_dependency",
        "invoked_knowledge_refs": "invoked_knowledge",
        "source_anchor_refs": "source_anchor",
        "ordered_step_refs": "ordered_step",
        "chain_ref": "derivation_chain",
        "step_refs": "reviewed_step",
        "validation_check_refs": "validation_check",
        "tool_run_check_refs": "tool_run_check",
        "checkpoint_ref": "checkpoint",
    }
    collected: dict[str, list[str]] = {}
    for key, relation_type in relation_keys.items():
        for record_ref in _refs(frontmatter.get(key)):
            collected.setdefault(record_ref, []).append(relation_type)
    metadata = _metadata(frontmatter)
    if metadata.get("schema_version") == "formula-code-relation/v1":
        for key, relation_type in (
            ("formula_ref", "formula_code_formula"),
            ("code_state_ref", "formula_code_code_state"),
            ("source_refs", "formula_code_source"),
            ("test_refs", "formula_code_test"),
            ("accepted_baseline_ref", "execution_baseline"),
        ):
            for record_ref in _refs(metadata.get(key)):
                collected.setdefault(record_ref, []).append(relation_type)
    else:
        for key, relation_type in (
            ("subject_id", "relation_subject"),
            ("object_id", "relation_object"),
        ):
            record_id = str(frontmatter.get(key) or "")
            if record_id:
                collected.setdefault(f"physics_object:{record_id}", []).append(
                    relation_type
                )
    return {
        record_ref: tuple(sorted(set(relation_types)))
        for record_ref, relation_types in sorted(collected.items())
    }


def link_types(
    value: Any,
    links: tuple[str, ...],
) -> dict[str, tuple[str, ...]]:
    result: dict[str, tuple[str, ...]] = {}
    if value not in (None, {}) and not isinstance(value, Mapping):
        raise ValueError("knowledge snapshot link_types must be a mapping")
    if isinstance(value, Mapping):
        for record_ref, relation_types in value.items():
            ref = str(record_ref)
            if ref not in links:
                raise ValueError("knowledge snapshot link_types must target a link")
            normalized = _strings(relation_types)
            if not normalized:
                raise ValueError("knowledge snapshot link_types must be non-empty")
            result[ref] = tuple(sorted(set(normalized)))
    for record_ref in links:
        result.setdefault(record_ref, ("related",))
    return result


def _metadata(frontmatter: Mapping[str, Any]) -> Mapping[str, Any]:
    value = frontmatter.get("metadata")
    return value if isinstance(value, Mapping) else {}


def _refs(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if ":" in value else []
    if isinstance(value, Mapping):
        ref = str(value.get("record_ref") or "")
        return [ref] if ref else []
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        refs: list[str] = []
        for item in value:
            refs.extend(_refs(item))
        return refs
    return []


def _strings(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,) if value.strip() else ()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(
            str(item)
            for item in value
            if isinstance(item, (str, int, float)) and str(item).strip()
        )
    if value not in (None, ""):
        return (str(value),)
    return ()


__all__ = ["link_types", "record_link_types", "record_links"]
