from dataclasses import replace
import hashlib
from pathlib import Path


_COMPACT_MAINTENANCE_NAMES = {
    "aitp_v5_get_runtime_bridge_target_manifest",
    "aitp_v5_get_runtime_payload_profiles",
    "aitp_v5_audit_runtime_mcp_bridge_acceptance",
    "aitp_v5_audit_hook_installation",
    "aitp_v5_discover_hook_install_paths",
    "aitp_v5_report_hook_smoke_coverage",
}


def _mcp_wrapper_names():
    from brain.v5 import mcp_tools

    return {
        name
        for name, value in vars(mcp_tools).items()
        if name.startswith("aitp_v5_") and callable(value)
    }


def test_capability_registry_covers_catalog_and_full_mcp_surface():
    from brain.v5.capability_registry import capability_specs
    from brain.v5.runtime_entrypoint_catalog import capability_registry_ref
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    specs = capability_specs()
    entrypoints = runtime_entrypoints()

    assert set(entrypoints).issubset(specs)
    assert capability_registry_ref() == "brain.v5.capability_registry:capability_specs"
    assert {spec.mcp_name for spec in specs.values()} == _mcp_wrapper_names()
    for operation, entrypoint in entrypoints.items():
        spec = specs[operation]
        assert spec.mcp_name == entrypoint["mcp"]
        assert spec.cli_route == entrypoint["cli"]
        assert spec.public_surface == entrypoint["surface"]


def test_capability_registry_declares_gate0_and_compact_capabilities():
    from brain.v5.capability_registry import capability_specs

    specs = capability_specs()
    expected = {
        "capability_registry": (
            "aitp_v5_get_capability_registry",
            "read_only",
            "full",
        ),
        "runtime_capability_audit": (
            "aitp_v5_get_runtime_capability_audit",
            "read_only",
            "full",
        ),
        "query_index_build": (
            "aitp_v5_build_query_index",
            "runtime_write",
            "full",
        ),
        "query_index_status": (
            "aitp_v5_get_query_index_status",
            "read_only",
            "full",
        ),
        "exact_record_expansion": (
            "aitp_v5_exact_expand_records",
            "read_only",
            "full",
        ),
        "research_context_compile": (
            "aitp_v5_compile_research_context",
            "read_only",
            "full",
        ),
        "codex_expand": (
            "aitp_v5_codex_expand",
            "read_only",
            "compact",
        ),
    }

    for operation, (mcp_name, state_effect, visibility) in expected.items():
        spec = specs[operation]
        assert spec.mcp_name == mcp_name
        assert spec.state_effect == state_effect
        assert spec.compact_visibility == visibility


def test_compact_maintenance_capabilities_use_one_release_soft_deprecation():
    from brain.v5.capability_registry import capability_specs, compact_mcp_tools
    from brain.v5.capability_registry_data import COMPACT_SOFT_DEPRECATION_BY_MCP

    specs_by_name = {spec.mcp_name: spec for spec in capability_specs().values()}

    assert len(compact_mcp_tools()) == 10
    assert _COMPACT_MAINTENANCE_NAMES.isdisjoint(compact_mcp_tools())
    for name in _COMPACT_MAINTENANCE_NAMES:
        spec = specs_by_name[name]
        assert spec.compact_visibility == "full"
        assert spec.lifecycle_status == "soft_deprecated_from_compact"
        assert spec.compatibility_window == "one_release"
        assert spec.cli_route
        assert COMPACT_SOFT_DEPRECATION_BY_MCP[name]["cli_route"] == spec.cli_route
        assert "full MCP or CLI" in spec.compatibility_warning


def test_capability_registry_matches_public_compact_and_bridge_surfaces():
    from brain.v5.capability_registry import (
        capability_specs,
        normalize_bridge_state_effect,
    )
    from brain.v5.codex_facade import CODEX_SURFACE_TOOL_ALLOWLIST
    from brain.v5.public_surfaces import public_surface_names
    from brain.v5.runtime_bridge_targets import runtime_bridge_target_manifest

    specs = capability_specs()
    public = set(public_surface_names())
    compact = {
        spec.mcp_name
        for spec in specs.values()
        if spec.compact_visibility == "compact"
    }

    assert all(spec.public_surface in public for spec in specs.values())
    assert compact == set(CODEX_SURFACE_TOOL_ALLOWLIST)
    assert all(spec.state_effect in {"read_only", "runtime_write", "kernel_write"} for spec in specs.values())
    assert all(spec.compact_visibility in {"compact", "full", "hidden"} for spec in specs.values())

    for target in runtime_bridge_target_manifest()["targets"]:
        spec = specs[target["entrypoint_key"]]
        assert spec.bridge_target == target["operation"]
        assert spec.state_effect == normalize_bridge_state_effect(target["state_effect"])


def test_capability_registry_audit_and_contract_report_drift():
    from brain.v5.capability_registry import audit_capability_registry, capability_specs
    from brain.v5.capability_registry_contracts import (
        validate_capability_registry_audit,
    )

    audit = audit_capability_registry()

    assert audit["ok"] is True
    assert audit["capability_count"] == len(capability_specs())
    assert audit["issues"] == []
    assert validate_capability_registry_audit(audit).ok

    specs = capability_specs()
    first = next(iter(specs))
    broken = dict(specs)
    broken[first] = replace(specs[first], state_effect="ambiguous")
    invalid = audit_capability_registry(specs=broken)

    assert invalid["ok"] is False
    assert any("state_effect" in issue for issue in invalid["issues"])
    assert not validate_capability_registry_audit(invalid).ok


def test_gate0_mcp_capabilities_build_derived_state_and_compile_context(tmp_path):
    from brain.v5 import mcp_tools
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="theory", title="Quantum gravity")
    claim = create_claim(
        ws,
        topic_id="qg",
        statement="The checked saddle has a controlled semiclassical boundary.",
        evidence_profile="formal_derivation",
        confidence_state="conditional",
        active_uncertainty="The one-loop determinant remains open.",
    )
    bind_session(
        ws,
        "session-qg",
        topic_id="qg",
        context_id="theory",
        active_claim=claim.claim_id,
    )
    before = _markdown_hashes(ws.root)

    missing = mcp_tools.aitp_v5_get_query_index_status(str(tmp_path))
    assert missing["exists"] is False
    build = mcp_tools.aitp_v5_build_query_index(str(tmp_path))
    status = mcp_tools.aitp_v5_get_query_index_status(str(tmp_path))

    assert build["kind"] == "query_index_build_report"
    assert build["indexed_count"] >= 3
    assert status["exists"] is True
    assert status["fresh"] is True
    assert _markdown_hashes(ws.root) == before

    exact = mcp_tools.aitp_v5_exact_expand_records(
        str(tmp_path),
        refs=[f"claim:{claim.claim_id}"],
    )
    context = mcp_tools.aitp_v5_compile_research_context(
        str(tmp_path),
        session_id="session-qg",
        objective_text="continue the one-loop boundary check",
        max_tokens=300,
        max_bytes=1800,
    )

    assert exact["items"][0]["record_ref"] == f"claim:{claim.claim_id}"
    assert exact["can_update_kernel_state"] is False
    assert context["topic_id"] == "qg"
    assert context["byte_count"] <= 1800
    assert context["estimated_tokens"] <= 300
    assert context["requires_exact_expansion_before_trust_conclusions"] is True
    assert require_valid_public_surface("research_retrieval_result", exact) == exact
    assert require_valid_public_surface("research_context_bundle", context) == context


def test_read_only_context_wrapper_requires_prebuilt_index(tmp_path):
    import pytest

    from brain.v5 import mcp_tools
    from brain.v5.workspace import bind_session, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qft", context_id="theory", title="QFT")
    bind_session(ws, "session-qft", topic_id="qft", context_id="theory")

    with pytest.raises(FileNotFoundError, match="build_query_index"):
        mcp_tools.aitp_v5_compile_research_context(
            str(tmp_path),
            session_id="session-qft",
        )


def test_registry_and_runtime_audit_mcp_surfaces_are_contracted():
    from brain.v5 import mcp_tools
    from brain.v5.capability_registry import capability_specs
    from brain.v5.public_surfaces import require_valid_public_surface

    registry = mcp_tools.aitp_v5_get_capability_registry()
    runtime = mcp_tools.aitp_v5_get_runtime_capability_audit(
        repo_root=str(Path(__file__).resolve().parents[1])
    )
    catalog = mcp_tools.aitp_v5_codex_tool_catalog()

    assert registry["capability_count"] == len(capability_specs())
    assert require_valid_public_surface("capability_registry_audit", registry) == registry
    assert require_valid_public_surface("runtime_capability_audit", runtime) == runtime
    assert require_valid_public_surface("codex_mcp_surface_catalog", catalog) == catalog


def test_optional_runtime_extension_does_not_make_core_registry_incomplete(monkeypatch):
    from brain.v5 import mcp_tools
    from brain.v5.capability_registry import audit_capability_registry, capability_specs

    optional_name = "aitp_v5_build_harness_feedback_problem_dossier"
    monkeypatch.delattr(mcp_tools, optional_name, raising=False)

    specs = capability_specs()
    audit = audit_capability_registry(specs=specs)

    assert "harness_feedback_problem_dossier" not in specs
    assert optional_name not in {spec.mcp_name for spec in specs.values()}
    assert audit["ok"] is True


def _markdown_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*.md"))
    }
