# Compatibility shard 2 for literature_extraction_report.
from __future__ import annotations

def _missing_record_kinds_for_sections(missing_section_ids: list[str]) -> list[str]:
    result: list[str] = []
    for section_id in missing_section_ids:
        if "source_identity" == section_id:
            result.append("source_asset")
        elif "anchor" in section_id:
            result.append("reference_location")
        elif any(token in section_id for token in ("object", "definition", "operator", "field", "method", "parameter")):
            result.append("physics_object")
        elif any(token in section_id for token in ("relation", "workflow", "map", "scheme", "limit")):
            result.append("object_relation")
        elif "gap" in section_id:
            result.append("proof_obligation")
        elif "report" in section_id or "orientation" in section_id:
            result.append("sensemaking_report")
    return _nonempty_unique(result)

_ENTRYPOINT_BY_RECORD_KIND = {
    "source_asset": (
        "register_source_asset",
        "source_asset_record",
        "record canonical source identity",
    ),
    "reference_location": (
        "record_reference_location",
        "reference_location_record",
        "record exact source anchors",
    ),
    "physics_object": (
        "record_physics_object",
        "physics_object_record",
        "write source-backed definitions, objects, notation, or conventions",
    ),
    "object_relation": (
        "record_object_relation",
        "object_relation_record",
        "write source-backed relations after object endpoints exist",
    ),
    "proof_obligation": (
        "create_proof_obligation",
        "proof_obligation_record",
        "preserve source, derivation, or validation gaps",
    ),
    "sensemaking_report": (
        "record_sensemaking_report",
        "sensemaking_report_record",
        "summarize extraction status as orientation only",
    ),
}

def _next_entrypoint_for_missing(missing_record_kinds: list[str]) -> str:
    if not missing_record_kinds:
        return ""
    record_kind = missing_record_kinds[0]
    return _ENTRYPOINT_BY_RECORD_KIND.get(record_kind, ("", "", ""))[0]

def _source_asset_for_ref(
    source_ref: str,
    parsed: tuple[str, str] | None,
    source_assets: list[SourceAssetRecord],
    reference_locations: list[ReferenceLocationRecord],
) -> SourceAssetRecord | None:
    by_id = {asset.asset_id: asset for asset in source_assets}
    if parsed and parsed[0] == "source_asset":
        return by_id.get(parsed[1])
    if parsed and parsed[0] == "reference_location":
        location = next((item for item in reference_locations if item.location_id == parsed[1]), None)
        if location and location.source_ref.startswith("source_asset:"):
            return by_id.get(location.source_ref.split(":", 1)[1])
    for asset in source_assets:
        candidate_values = {f"source_asset:{asset.asset_id}", asset.uri}
        if source_ref in candidate_values:
            return asset
    return None

def _reference_locations_for_ref(
    source_ref: str,
    parsed: tuple[str, str] | None,
    source_asset: SourceAssetRecord | None,
    reference_locations: list[ReferenceLocationRecord],
) -> list[ReferenceLocationRecord]:
    matches: list[ReferenceLocationRecord] = []
    if parsed and parsed[0] == "reference_location":
        matches.extend(item for item in reference_locations if item.location_id == parsed[1])
    if source_asset is not None:
        asset_ref = f"source_asset:{source_asset.asset_id}"
        matches.extend(item for item in reference_locations if item.source_ref == asset_ref)
        matches.extend(item for item in reference_locations if item.location_id in source_asset.reference_location_ids)
    matches.extend(item for item in reference_locations if item.source_ref == source_ref)
    return _unique_by(matches, "location_id")

def _candidate_source_refs(
    source_ref: str,
    source_asset: SourceAssetRecord | None,
    reference_locations: list[ReferenceLocationRecord],
) -> list[str]:
    refs = [source_ref]
    if source_asset is not None:
        refs.append(f"source_asset:{source_asset.asset_id}")
        refs.append(source_asset.uri)
    refs.extend(f"reference_location:{location.location_id}" for location in reference_locations)
    refs.extend(location.source_ref for location in reference_locations if location.source_ref)
    return _nonempty_unique(refs)

def _normalize_profile(value: str) -> str:
    normalized = str(value or "paper_learning").strip().lower().replace("-", "_")
    return _PROFILE_ALIASES.get(normalized, "generic_literature_report")

def _parse_ref(ref: str) -> tuple[str, str] | None:
    parts = [part.strip() for part in ref.split(":")]
    if len(parts) == 3 and parts[0] == "aitp":
        _, kind, record_id = parts
    elif len(parts) == 2:
        kind, record_id = parts
    else:
        return None
    if not kind or not record_id:
        return None
    return kind.replace("-", "_"), record_id

def _intersects(values: list[str], candidates: list[str]) -> bool:
    return bool(set(values).intersection(candidates))

def _unique_by(values: list[Any], attr: str) -> list[Any]:
    seen: set[str] = set()
    result: list[Any] = []
    for value in values:
        key = str(getattr(value, attr))
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result

def _nonempty_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = str(value).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result
