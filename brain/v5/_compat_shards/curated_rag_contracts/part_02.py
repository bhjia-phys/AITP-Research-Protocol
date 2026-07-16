# Compatibility shard 2 for curated_rag_contracts.
from __future__ import annotations

def _contains_reserved_source_shelf_structure(payload: dict[str, Any]) -> bool:
    reserved_pin_keys = {
        "acquisition_decision_ref",
        "acquisition_receipt_ref",
        "source_asset_ref",
        "source_content_hash",
        "source_location_pins",
        "source_location_refs",
        "source_record_content_hash",
        "source_record_revision",
    }
    stack: list[Any] = [payload]
    seen: set[int] = set()
    while stack:
        value = stack.pop()
        if isinstance(value, dict):
            identity = id(value)
            if identity in seen:
                continue
            seen.add(identity)
            for key, item in value.items():
                normalized = key.lower().replace("-", "_")
                if (
                    "source_shelf" in normalized
                    or "source_passage" in normalized
                    or normalized in reserved_pin_keys
                ):
                    return True
                if isinstance(item, (dict, list)):
                    stack.append(item)
        elif isinstance(value, list):
            identity = id(value)
            if identity in seen:
                continue
            seen.add(identity)
            stack.extend(value)
    return False

def _validate_json_compatible(value: Any, path: str, result: ContractResult) -> bool:
    stack: list[tuple[Any, bool]] = [(value, False)]
    active: set[int] = set()
    while stack:
        item, leaving = stack.pop()
        if leaving:
            active.remove(id(item))
            continue
        if item is None or type(item) in {str, int, bool}:
            continue
        if type(item) is float:
            if item != item or item in {float("inf"), float("-inf")}:
                result.add(path, "must contain only finite JSON values")
                return False
            continue
        if type(item) not in {dict, list}:
            result.add(path, "must contain only JSON-compatible values")
            return False
        identity = id(item)
        if identity in active:
            result.add(path, "must not contain circular JSON containers")
            return False
        active.add(identity)
        stack.append((item, True))
        if type(item) is dict:
            if any(type(key) is not str for key in item):
                result.add(path, "must use string JSON object keys")
                return False
            stack.extend((child, False) for child in item.values())
        else:
            stack.extend((child, False) for child in item)
    return True

def _require_string_list(value: Any, path: str, result: ContractResult) -> None:
    _require_list(value, path, result)
    if isinstance(value, list) and any(type(item) is not str for item in value):
        result.add(path, "must contain only strings")

def _validate_curated_rag_authority_mode(
    payload: dict[str, Any], path: str, result: ContractResult, *, base=None,
) -> None:
    kind = payload.get("kind")
    policy = payload.get("index_policy")
    mode = policy.get("active_index_mode") if isinstance(policy, dict) else None
    if kind != "curated_rag_corpus":
        mode = payload.get("index_mode")
    if mode == "lexical_source_shelf":
        if kind == "curated_rag_corpus":
            _validate_source_shelf_catalog(payload, path, result, base=base)
        else:
            _validate_source_shelf_retrieval(payload, path, result, base=base)
    elif _contains_reserved_source_shelf_structure(payload):
        result.add(path, "non-shelf mode must not carry reserved source-shelf structure")

def _validate_search_result_item(item: Any, path: str, result: ContractResult) -> None:
    _require_mapping(item, path, result)
    if not isinstance(item, dict):
        return
    for key in ("chunk_id", "document_id", "summary", "text", "content_hash"):
        if not isinstance(item.get(key), str) or not item.get(key):
            result.add(f"{path}.{key}", "must be a non-empty string")
    if not isinstance(item.get("score"), int) or item["score"] <= 0:
        result.add(f"{path}.score", "must be a positive integer")
    if item.get("retrieval_role") != "heuristic_context":
        result.add(f"{path}.retrieval_role", "must be 'heuristic_context'")
    if item.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    if item.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
    _require_mapping(item.get("anchor"), f"{path}.anchor", result)
    _require_string_list(item.get("tags"), f"{path}.tags", result)

def _validate_promotion_chunk(item: Any, path: str, result: ContractResult) -> None:
    _require_mapping(item, path, result)
    if not isinstance(item, dict):
        return
    for key in ("chunk_id", "document_id", "summary", "text", "content_hash"):
        if not isinstance(item.get(key), str) or not item.get(key):
            result.add(f"{path}.{key}", "must be a non-empty string")
    if item.get("retrieval_role") != "heuristic_context":
        result.add(f"{path}.retrieval_role", "must be 'heuristic_context'")
    if item.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    if item.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
    _require_mapping(item.get("anchor"), f"{path}.anchor", result)
    _require_string_list(item.get("tags"), f"{path}.tags", result)

def _validate_promotion_document(item: Any, path: str, result: ContractResult) -> None:
    _require_mapping(item, path, result)
    if not isinstance(item, dict):
        return
    for key in ("document_id", "title", "asset_type", "source_uri", "content_hash", "language", "priority"):
        if not isinstance(item.get(key), str) or not item.get(key):
            result.add(f"{path}.{key}", "must be a non-empty string")
    for key in ("tags", "domain_hints", "topic_hints"):
        _require_string_list(item.get(key), f"{path}.{key}", result)
    _require_mapping(item.get("version_anchor"), f"{path}.version_anchor", result)
    if item.get("trust_status") != "heuristic_context":
        result.add(f"{path}.trust_status", "must be 'heuristic_context'")
    if item.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    if item.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")

def _validate_draft_operations(items: list[Any], path: str, result: ContractResult) -> None:
    expected_stages = [
        "source_asset",
        "reference_location",
        "evidence",
        "validation",
        "trust_preflight",
    ]
    stages: list[str] = []
    for index, item in enumerate(items):
        item_path = f"{path}[{index}]"
        _require_mapping(item, item_path, result)
        if not isinstance(item, dict):
            continue
        stage = item.get("stage")
        if isinstance(stage, str):
            stages.append(stage)
        for key in ("stage", "operation", "mcp_tool", "cli_template", "surface"):
            if not isinstance(item.get(key), str) or not item.get(key):
                result.add(f"{item_path}.{key}", "must be a non-empty string")
        if item.get("draft_only") is not True:
            result.add(f"{item_path}.draft_only", "must be true")
        if item.get("creates_record_now") is not False:
            result.add(f"{item_path}.creates_record_now", "must be false")
        if item.get("claim_support_created") is not False:
            result.add(f"{item_path}.claim_support_created", "must be false")
        if "payload_draft" in item:
            _require_mapping(item.get("payload_draft"), f"{item_path}.payload_draft", result)
        if "payload_template" in item:
            _require_mapping(item.get("payload_template"), f"{item_path}.payload_template", result)
        if "requires_existing_records" in item:
            _require_list(item.get("requires_existing_records"), f"{item_path}.requires_existing_records", result)
    if stages != expected_stages:
        result.add(path, "must list source, reference, evidence, validation, and trust-preflight stages in order")

def _validate_promotion_write_sequence(items: list[Any], path: str, result: ContractResult) -> None:
    expected = [
        {
            "order": 1,
            "stage": "source_asset",
            "operation": "registerSourceAsset",
            "surface": "source_asset_record",
            "output_ref": "source_asset:<asset_id>",
            "requires_prior_refs": [],
            "feeds_next_stages": ["reference_location", "evidence"],
        },
        {
            "order": 2,
            "stage": "reference_location",
            "operation": "recordReferenceLocation",
            "surface": "reference_location_record",
            "output_ref": "reference_location:<location_id>",
            "requires_prior_refs": ["source_asset:<asset_id>"],
            "feeds_next_stages": ["evidence"],
        },
        {
            "order": 3,
            "stage": "evidence",
            "operation": "recordEvidence",
            "surface": "evidence_record",
            "output_ref": "evidence:<evidence_id>",
            "requires_prior_refs": [
                "source_asset:<asset_id>",
                "reference_location:<location_id>",
            ],
            "feeds_next_stages": ["validation", "trust_preflight"],
        },
        {
            "order": 4,
            "stage": "validation",
            "operation": "createValidationContract",
            "surface": "validation_contract_record",
            "output_ref": "validation_contract:<contract_id>",
            "requires_prior_refs": ["evidence:<evidence_id>"],
            "feeds_next_stages": ["trust_preflight"],
        },
        {
            "order": 5,
            "stage": "trust_preflight",
            "operation": "preflightTrustUpdate",
            "surface": "trust_update_preflight",
            "output_ref": "trust_preflight:<preflight_token>",
            "requires_prior_refs": [
                "evidence:<evidence_id>",
                "validation_result:<result_id>",
            ],
            "feeds_next_stages": [],
        },
    ]
    if len(items) != len(expected):
        result.add(path, "must describe exactly five promotion write steps")
    for index, item in enumerate(items):
        item_path = f"{path}[{index}]"
        _require_mapping(item, item_path, result)
        if not isinstance(item, dict):
            continue
        expected_item = expected[index] if index < len(expected) else None
        if expected_item is not None:
            for key in ("order", "stage", "operation", "surface", "output_ref"):
                if item.get(key) != expected_item[key]:
                    result.add(f"{item_path}.{key}", f"must be {expected_item[key]!r}")
            for key in ("requires_prior_refs", "feeds_next_stages"):
                if item.get(key) != expected_item[key]:
                    result.add(f"{item_path}.{key}", "must follow the AITP promotion dependency sequence")
        if item.get("requires_explicit_execute_call") is not True:
            result.add(f"{item_path}.requires_explicit_execute_call", "must be true")
        if item.get("executes_write_now") is not False:
            result.add(f"{item_path}.executes_write_now", "must be false")
        if item.get("records_validation_result") is not False:
            result.add(f"{item_path}.records_validation_result", "must be false")
        if item.get("claim_trust_mutation") != "none":
            result.add(f"{item_path}.claim_trust_mutation", "must be 'none'")

def _validate_promotion_boundary(item: Any, path: str, result: ContractResult) -> None:
    _require_mapping(item, path, result)
    if not isinstance(item, dict):
        return
    false_keys = [
        "retrieval_is_claim_support",
        "draft_is_evidence",
        "draft_records_validation_result",
        "draft_satisfies_final_gate",
        "draft_can_update_claim_trust",
    ]
    for key in false_keys:
        if item.get(key) is not False:
            result.add(f"{path}.{key}", "must be false")
    if item.get("requires_user_or_model_decision_before_write") is not True:
        result.add(f"{path}.requires_user_or_model_decision_before_write", "must be true")

def _validate_lookup_promotion_boundary(item: Any, path: str, result: ContractResult) -> None:
    _require_mapping(item, path, result)
    if not isinstance(item, dict):
        return
    false_keys = [
        "retrieval_is_claim_support",
        "lookup_is_evidence",
        "lookup_records_validation_result",
        "lookup_satisfies_final_gate",
        "lookup_can_update_claim_trust",
    ]
    for key in false_keys:
        if item.get(key) is not False:
            result.add(f"{path}.{key}", "must be false")
    if item.get("requires_user_or_model_decision_before_write") is not True:
        result.add(f"{path}.requires_user_or_model_decision_before_write", "must be true")

def _validate_source_shelf_catalog(payload: dict[str, Any], path: str, result: ContractResult, *, base=None) -> None:
    from brain.v5.curated_rag_source_shelf_contracts import validate_source_shelf_catalog

    validate_source_shelf_catalog(payload, path, result, base=base)

def _validate_source_shelf_retrieval(payload: dict[str, Any], path: str, result: ContractResult, *, base=None) -> None:
    from brain.v5.curated_rag_source_shelf_contracts import validate_source_shelf_retrieval

    validate_source_shelf_retrieval(payload, path, result, base=base)
