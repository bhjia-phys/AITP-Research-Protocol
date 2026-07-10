"""Integrity checks for the canonical AITP record-family registry."""

from __future__ import annotations

from dataclasses import MISSING, fields, is_dataclass
from typing import Any, Mapping

from brain.v5.record_family_registry import RecordFamilySpec


_LIFECYCLE_POLICIES = {
    "append_only",
    "append_revision",
    "replace_idempotent",
    "runtime_binding",
}
_AUTO_WRITE_POLICIES = {
    "bounded_observation",
    "promotion_only",
    "reviewed",
    "unimplemented_layout",
}
_STORAGE_SCOPES = {"context", "memory", "registry", "runtime", "topic"}
_TRUST_EFFECTS = {"none", "candidate_only", "trust_path_input"}


def validate_record_family_registry(
    specs: Mapping[str, RecordFamilySpec],
) -> dict[str, Any]:
    """Return deterministic structural diagnostics without mutating the store."""

    errors: list[str] = []
    aliases: dict[str, str] = {}
    relative_dirs: dict[str, str] = {}
    for key, spec in sorted(specs.items()):
        prefix = f"families.{key}"
        if key != spec.family:
            errors.append(f"{prefix}.family must match registry key")
        if not spec.relative_dir:
            errors.append(f"{prefix}.relative_dir must be non-empty")
        elif spec.relative_dir in relative_dirs:
            errors.append(
                f"{prefix}.relative_dir duplicates {relative_dirs[spec.relative_dir]}"
            )
        else:
            relative_dirs[spec.relative_dir] = key
        if spec.is_registry_family and spec.relative_dir != f"registry/{key}":
            errors.append(f"{prefix}.relative_dir must be registry/{key}")
        if spec.storage_scope not in _STORAGE_SCOPES:
            errors.append(f"{prefix}.storage_scope is unsupported")
        if spec.lifecycle_policy not in _LIFECYCLE_POLICIES:
            errors.append(f"{prefix}.lifecycle_policy is unsupported")
        if spec.auto_write_policy not in _AUTO_WRITE_POLICIES:
            errors.append(f"{prefix}.auto_write_policy is unsupported")
        if not spec.schema_version:
            errors.append(f"{prefix}.schema_version must be non-empty")
        if spec.trust_effect not in _TRUST_EFFECTS:
            errors.append(f"{prefix}.trust_effect is unsupported")
        if not {"exact_ref", "inventory"} <= set(spec.participates_in):
            errors.append(f"{prefix}.participates_in must include exact_ref and inventory")
        if "exact_ref" in spec.participates_in and not spec.surface:
            errors.append(f"{prefix}.surface must be non-empty for exact_ref")
        if "query_index" in spec.participates_in and spec.id_field not in spec.index_fields:
            errors.append(f"{prefix}.index_fields must include id_field for query_index")
        if spec.record_kind not in spec.exact_ref_aliases:
            errors.append(f"{prefix}.exact_ref_aliases must include record_kind")
        if not spec.ref_kind or spec.ref_kind not in spec.exact_ref_aliases:
            errors.append(f"{prefix}.exact_ref_aliases must include ref_kind")
        _validate_record_class(spec, prefix, errors)
        for alias in spec.exact_ref_aliases:
            normalized = alias.replace("-", "_")
            previous = aliases.get(normalized)
            if previous is not None and previous != key:
                errors.append(f"{prefix}.exact_ref_aliases collides with {previous}: {alias}")
            else:
                aliases[normalized] = key
        if spec.id_field in spec.legacy_id_fields or len(set(spec.legacy_id_fields)) != len(
            spec.legacy_id_fields
        ):
            errors.append(f"{prefix}.legacy_id_fields must be unique aliases")

    registry_count = sum(1 for spec in specs.values() if spec.is_registry_family)
    return {
        "ok": not errors,
        "kind": "record_family_registry_validation",
        "family_count": len(specs),
        "registry_family_count": registry_count,
        "special_family_count": len(specs) - registry_count,
        "errors": errors,
        "truth_source": "record_family_specs",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _validate_record_class(
    spec: RecordFamilySpec,
    prefix: str,
    errors: list[str],
) -> None:
    cls = spec.record_class
    if cls is None:
        if spec.auto_write_policy != "unimplemented_layout":
            errors.append(f"{prefix}.record_class is absent but family is marked writable")
        return
    if not is_dataclass(cls):
        errors.append(f"{prefix}.record_class must be a dataclass")
        return
    declared = {field.name: field for field in fields(cls)}
    if spec.id_field not in declared:
        errors.append(f"{prefix}.id_field is not declared by record_class")
    kind_field = declared.get("kind")
    if kind_field is None:
        errors.append(f"{prefix}.record_class must declare kind")
    elif kind_field.default is not MISSING and kind_field.default != spec.record_kind:
        errors.append(
            f"{prefix}.record_kind {spec.record_kind!r} does not match class default "
            f"{kind_field.default!r}"
        )
