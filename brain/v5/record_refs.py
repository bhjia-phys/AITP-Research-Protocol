"""Read-only lookup helpers for canonical typed record references."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from brain.v5.markdown import read_md
from brain.v5.paths import WorkspacePaths
from brain.v5.record_family_registry import record_family_specs
from brain.v5.store import read_record


_RecordSpec = tuple[str, str, str, type[Any] | None, str, str, bool]


def _build_record_specs() -> dict[str, _RecordSpec]:
    specs: dict[str, _RecordSpec] = {}
    for family_spec in record_family_specs().values():
        if "exact_ref" not in family_spec.participates_in:
            continue
        specs[family_spec.ref_kind] = (
            family_spec.family,
            family_spec.id_field,
            family_spec.surface,
            family_spec.record_class,
            family_spec.record_role,
            family_spec.relative_dir,
            not family_spec.is_registry_family,
        )
    return dict(sorted(specs.items()))


def _build_aliases() -> dict[str, str]:
    aliases = {"aitp": ""}
    for spec in record_family_specs().values():
        if "exact_ref" not in spec.participates_in:
            continue
        aliases[spec.ref_kind] = spec.ref_kind
        for alias in spec.exact_ref_aliases:
            aliases[alias] = spec.ref_kind
    return aliases


_RECORD_SPECS = _build_record_specs()
_ALIASES = _build_aliases()

_MISSING_REF_SUGGESTIONS: dict[str, tuple[str, str, str, str]] = {
    "reference_location": (
        "recordReferenceLocation",
        "record_reference_location",
        "reference_location_record",
        "record a normal AITP reference location before using this ref as source context",
    ),
    "source_asset": (
        "registerSourceAsset",
        "register_source_asset",
        "source_asset_record",
        "register or auto-capture a normal AITP source asset before using this ref as source context",
    ),
}


def record_ref_registry_families() -> tuple[str, ...]:
    """Return normal registry families addressable through exact refs."""

    return tuple(
        sorted(
            {
                family
                for family, _id, _surface, _cls, _role, _scope, custom in _RECORD_SPECS.values()
                if not custom
            }
        )
    )


def lookup_record_refs(ws: WorkspacePaths, refs: list[str]) -> dict[str, Any]:
    """Return read-only typed-store existence checks for canonical record refs."""

    clean_refs = [str(ref).strip() for ref in refs if str(ref).strip()]
    results = [_lookup_record_ref(ws, ref) for ref in clean_refs]
    found_count = sum(1 for item in results if item["status"] == "found")
    return {
        "kind": "record_ref_lookup",
        "lookup_scope": "typed_record_existence_only",
        "lookup_count": len(results),
        "found_count": found_count,
        "missing_count": sum(1 for item in results if item["status"] == "not_found"),
        "unsupported_count": sum(1 for item in results if item["status"] == "unsupported_kind"),
        "malformed_count": sum(1 for item in results if item["status"] == "malformed_ref"),
        "refs": results,
        "supported_ref_kinds": sorted(_RECORD_SPECS),
        "read_surface_effect": "record_existence_check_only",
        "records_validation_result": False,
        "source_support_result": False,
        "evidence_created": False,
        "validation_created": False,
        "claim_trust_mutation": "none",
        "can_update_claim_trust": False,
        "summary_inputs_trusted": False,
        "orientation_only": True,
    }


def _lookup_record_ref(ws: WorkspacePaths, ref: str) -> dict[str, Any]:
    parsed = _parse_ref(ref)
    if parsed is None:
        return _base_result(
            ref,
            status="malformed_ref",
            diagnostic="expected '<kind>:<record_id>' or 'aitp:<kind>:<record_id>'",
        )

    ref_kind, record_id = parsed
    spec = _RECORD_SPECS.get(ref_kind)
    if spec is None:
        result = _base_result(
            ref,
            ref_kind=ref_kind,
            record_id=record_id,
            status="unsupported_kind",
        )
        result["diagnostic"] = "ref kind is not supported by this read-only lookup surface"
        return result

    family, id_field, surface, cls, record_role, store_scope, custom_path = spec
    path = _record_path(ws, family, record_id, custom_path=custom_path)
    result = _base_result(
        ref,
        ref_kind=ref_kind,
        record_id=record_id,
        status="not_found",
        id_field=id_field,
        surface=surface,
        record_role=record_role,
        store_scope=store_scope,
    )
    if not path.exists():
        _add_missing_ref_suggestion(result, ref_kind)
        return result

    try:
        record_payload, actual_id = _read_record_payload(path, cls, id_field)
    except (TypeError, ValueError):
        result["diagnostic"] = "record file exists but does not satisfy its typed record shape"
        return result
    if actual_id != record_id:
        result["diagnostic"] = "record file exists but record id field does not match requested ref"
        return result

    result.update(
        {
            "status": "found",
            "record_confirmed": True,
            "topic_id": str(record_payload.get("topic_id") or ""),
            "claim_id": str(record_payload.get("claim_id") or ""),
            "record_kind": str(record_payload.get("kind") or ""),
            "orientation_only_record": bool(record_payload.get("orientation_only", False)),
            "can_update_record_claim_trust": False,
            "diagnostic": "record exists in typed store",
        }
    )
    return result


def _read_record_payload(
    path: Path,
    cls: type[Any] | None,
    id_field: str,
) -> tuple[dict[str, Any], str]:
    if cls is None:
        frontmatter, _body = read_md(path)
        payload = dict(frontmatter)
        return payload, str(payload.get(id_field) or "")
    record = read_record(path, cls)
    payload = asdict(record) if is_dataclass(record) else dict(record)
    return payload, str(getattr(record, id_field, ""))


def _add_missing_ref_suggestion(result: dict[str, Any], ref_kind: str) -> None:
    suggestion = _MISSING_REF_SUGGESTIONS.get(ref_kind)
    if suggestion is None:
        return
    operation, entrypoint, surface, reason = suggestion
    result.update(
        {
            "suggested_next_operation": operation,
            "suggested_next_entrypoint": entrypoint,
            "suggested_next_surface": surface,
            "suggested_next_reason": reason,
        }
    )


def _parse_ref(ref: str) -> tuple[str, str] | None:
    parts = [part.strip() for part in ref.split(":")]
    if len(parts) == 3 and parts[0] == "aitp":
        _, raw_kind, record_id = parts
    elif len(parts) == 2:
        raw_kind, record_id = parts
    else:
        return None
    if not raw_kind or not record_id:
        return None
    kind = _ALIASES.get(raw_kind, raw_kind).replace("-", "_")
    return kind, record_id


def _record_path(
    ws: WorkspacePaths,
    family: str,
    record_id: str,
    *,
    custom_path: bool,
) -> Path:
    if not custom_path:
        return ws.registry_dir(family) / f"{record_id}.md"
    if family == "sessions":
        return ws.session_path(record_id)
    if family == "topics":
        return ws.topic_dir(record_id) / "topic.md"
    if family == "contexts":
        return ws.context_dir(record_id) / "context.md"
    if family == "memory_entries":
        return ws.root / "memory" / "l2" / "entries" / f"{record_id}.md"
    raise ValueError(f"unsupported special record family: {family}")


def _base_result(
    ref: str,
    *,
    status: str,
    ref_kind: str = "",
    record_id: str = "",
    id_field: str = "",
    surface: str = "",
    record_role: str = "",
    store_scope: str = "",
    diagnostic: str = "",
) -> dict[str, Any]:
    return {
        "ref": ref,
        "ref_kind": ref_kind,
        "record_id": record_id,
        "id_field": id_field,
        "surface": surface,
        "record_role": record_role,
        "store_scope": store_scope,
        "status": status,
        "record_confirmed": False,
        "topic_id": "",
        "claim_id": "",
        "record_kind": "",
        "orientation_only_record": False,
        "can_update_record_claim_trust": False,
        "read_surface_effect": "record_existence_check_only",
        "records_validation_result": False,
        "source_support_result": False,
        "claim_trust_mutation": "none",
        "can_update_claim_trust": False,
        "suggested_next_operation": "",
        "suggested_next_entrypoint": "",
        "suggested_next_surface": "",
        "suggested_next_reason": "",
        "diagnostic": diagnostic,
    }
