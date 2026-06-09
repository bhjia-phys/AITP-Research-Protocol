"""Contracts for host-facing runtime bridge target manifests."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_list, _require_mapping
from brain.v5.runtime_bridge_targets import runtime_bridge_target_manifest
from brain.v5.runtime_entrypoints import runtime_entrypoints


def validate_runtime_bridge_target_manifest(
    payload: dict[str, Any],
    *,
    path: str = "runtime_bridge_target_manifest",
) -> ContractResult:
    """Validate that bridge targets match canonical runtime entrypoints."""

    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result

    if payload.get("kind") != "runtime_bridge_target_manifest":
        result.add(f"{path}.kind", "must be 'runtime_bridge_target_manifest'")
    if payload.get("preferred_transport") != "mcp":
        result.add(f"{path}.preferred_transport", "must be 'mcp'")
    if payload.get("fallback_transport") != "cli":
        result.add(f"{path}.fallback_transport", "must be 'cli'")
    if payload.get("mcp_argument_style") != "json_object":
        result.add(f"{path}.mcp_argument_style", "must be 'json_object'")
    if payload.get("mcp_base_argument") != "base":
        result.add(f"{path}.mcp_base_argument", "must be 'base'")
    if payload.get("mcp_payload_key_case") != "snake_case":
        result.add(f"{path}.mcp_payload_key_case", "must be 'snake_case'")
    if payload.get("mcp_result_content_type") != "json_object":
        result.add(f"{path}.mcp_result_content_type", "must be 'json_object'")
    if payload.get("fallback_policy") != "use_cli_when_mcp_transport_unavailable_or_call_fails":
        result.add(
            f"{path}.fallback_policy",
            "must use CLI when MCP transport is unavailable or call fails",
        )
    if payload.get("truth_source") != "runtime_entrypoint_catalog":
        result.add(f"{path}.truth_source", "must be 'runtime_entrypoint_catalog'")
    if payload.get("summary_inputs_trusted") is not False:
        result.add(f"{path}.summary_inputs_trusted", "must be false")
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")

    targets = payload.get("targets")
    _require_list(targets, f"{path}.targets", result)
    if isinstance(targets, list):
        if payload.get("target_count") != len(targets):
            result.add(f"{path}.target_count", "must match targets length")
        _validate_targets(targets, f"{path}.targets", result)

    expected = runtime_bridge_target_manifest()
    if payload != expected:
        result.add(path, "must match runtime_bridge_target_manifest()")
    return result


def require_valid_runtime_bridge_target_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a runtime bridge target manifest or raise a contract error."""

    result = validate_runtime_bridge_target_manifest(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_targets(targets: list[Any], path: str, result: ContractResult) -> None:
    entrypoints = runtime_entrypoints()
    seen_operations: set[str] = set()
    for index, target in enumerate(targets):
        item_path = f"{path}.{index}"
        _require_mapping(target, item_path, result)
        if not isinstance(target, dict):
            continue

        operation = target.get("operation")
        if not isinstance(operation, str) or not operation:
            result.add(f"{item_path}.operation", "must be a non-empty string")
        elif operation in seen_operations:
            result.add(f"{item_path}.operation", "must be unique")
        else:
            seen_operations.add(operation)

        entrypoint_key = target.get("entrypoint_key")
        if not isinstance(entrypoint_key, str) or entrypoint_key not in entrypoints:
            result.add(f"{item_path}.entrypoint_key", "must name a runtime entrypoint")
            continue
        entrypoint = entrypoints[entrypoint_key]
        if target.get("mcp_tool") != entrypoint["mcp"]:
            result.add(f"{item_path}.mcp_tool", "must match runtime entrypoint MCP tool")
        if target.get("cli_fallback") != entrypoint["cli"]:
            result.add(f"{item_path}.cli_fallback", "must match runtime entrypoint CLI template")
        if target.get("surface") != entrypoint["surface"]:
            result.add(f"{item_path}.surface", "must match runtime entrypoint surface")
        if target.get("preferred_transport") != "mcp":
            result.add(f"{item_path}.preferred_transport", "must be 'mcp'")
        if target.get("fallback_transport") != "cli":
            result.add(f"{item_path}.fallback_transport", "must be 'cli'")
        invocation = target.get("mcp_invocation")
        _require_mapping(invocation, f"{item_path}.mcp_invocation", result)
        if isinstance(invocation, dict):
            if invocation.get("tool") != entrypoint["mcp"]:
                result.add(f"{item_path}.mcp_invocation.tool", "must match MCP tool")
            if invocation.get("argument_style") != "json_object":
                result.add(f"{item_path}.mcp_invocation.argument_style", "must be 'json_object'")
            if invocation.get("base_argument") != "base":
                result.add(f"{item_path}.mcp_invocation.base_argument", "must be 'base'")
            if invocation.get("payload_key_case") != "snake_case":
                result.add(f"{item_path}.mcp_invocation.payload_key_case", "must be 'snake_case'")
            if invocation.get("result_surface") != entrypoint["surface"]:
                result.add(f"{item_path}.mcp_invocation.result_surface", "must match surface")
            if invocation.get("result_content_type") != "json_object":
                result.add(
                    f"{item_path}.mcp_invocation.result_content_type",
                    "must be 'json_object'",
                )
            if (
                invocation.get("fallback_policy")
                != "use_cli_when_mcp_transport_unavailable_or_call_fails"
            ):
                result.add(
                    f"{item_path}.mcp_invocation.fallback_policy",
                    "must use CLI when MCP transport is unavailable or call fails",
                )
        if target.get("claim_trust_mutation") != "none":
            result.add(f"{item_path}.claim_trust_mutation", "must be 'none'")
        if target.get("can_update_claim_trust") is not False:
            result.add(f"{item_path}.can_update_claim_trust", "must be false")
        if entrypoint_key == "ingest_curated_rag_corpus":
            if target.get("execution_role") != "write":
                result.add(f"{item_path}.execution_role", "must be 'write'")
            if target.get("state_effect") != "curated_rag_manifest_write":
                result.add(f"{item_path}.state_effect", "must be 'curated_rag_manifest_write'")
        _validate_mcp_arguments(target, item_path, result)


def _validate_mcp_arguments(target: dict[str, Any], path: str, result: ContractResult) -> None:
    entrypoint_key = target.get("entrypoint_key")
    arguments = target.get("mcp_arguments")
    if entrypoint_key in {
        "process_graph_slice",
        "host_agnostic_moment_policy",
        "runtime_payload_profiles",
        "record_ref_lookup",
        "curated_rag_corpus",
        "curated_rag_search",
        "curated_rag_chunk",
        "curated_rag_promotion_draft",
    }:
        _require_mapping(arguments, f"{path}.mcp_arguments", result)
        if not isinstance(arguments, dict):
            return
        _require_list(arguments.get("required"), f"{path}.mcp_arguments.required", result)
        _require_list(arguments.get("optional"), f"{path}.mcp_arguments.optional", result)
        if not isinstance(arguments.get("source"), str) or not arguments["source"]:
            result.add(f"{path}.mcp_arguments.source", "must be a non-empty string")
        if entrypoint_key in {"process_graph_slice", "host_agnostic_moment_policy"}:
            if arguments.get("required") != ["base", "session_id"]:
                result.add(
                    f"{path}.mcp_arguments.required",
                    "must require base and session_id",
                )
            if arguments.get("optional") != ["claim_id", "limit"]:
                result.add(
                    f"{path}.mcp_arguments.optional",
                    "must allow claim_id and limit",
                )
        if entrypoint_key == "runtime_payload_profiles":
            if arguments.get("required") != []:
                result.add(f"{path}.mcp_arguments.required", "must be empty")
            if arguments.get("optional") != []:
                result.add(f"{path}.mcp_arguments.optional", "must be empty")
        if entrypoint_key == "record_ref_lookup":
            if arguments.get("required") != ["base", "refs"]:
                result.add(f"{path}.mcp_arguments.required", "must require base and refs")
            if arguments.get("optional") != []:
                result.add(f"{path}.mcp_arguments.optional", "must be empty")
        if entrypoint_key == "curated_rag_corpus":
            if arguments.get("required") != []:
                result.add(f"{path}.mcp_arguments.required", "must be empty")
            if arguments.get("optional") != ["base"]:
                result.add(f"{path}.mcp_arguments.optional", "must allow base")
        if entrypoint_key == "curated_rag_search":
            if arguments.get("required") != ["query"]:
                result.add(f"{path}.mcp_arguments.required", "must require query")
            if arguments.get("optional") != ["base", "limit"]:
                result.add(f"{path}.mcp_arguments.optional", "must allow base and limit")
        if entrypoint_key == "curated_rag_chunk":
            if arguments.get("required") != ["chunk_id"]:
                result.add(f"{path}.mcp_arguments.required", "must require chunk_id")
            if arguments.get("optional") != ["base"]:
                result.add(f"{path}.mcp_arguments.optional", "must allow base")
        if entrypoint_key == "curated_rag_promotion_draft":
            if arguments.get("required") != ["chunk_id"]:
                result.add(f"{path}.mcp_arguments.required", "must require chunk_id")
            if arguments.get("optional") != ["base", "topic_id", "claim_id", "connector_id", "promotion_intent"]:
                result.add(
                    f"{path}.mcp_arguments.optional",
                    "must allow base, topic_id, claim_id, connector_id, and promotion_intent",
                )
    elif arguments is not None:
        result.add(f"{path}.mcp_arguments", "must be omitted for non-read target metadata")
