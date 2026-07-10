from dataclasses import replace
from pathlib import Path

from brain.v5.record_family_contracts import validate_record_family_registry as validate_specs
from brain.v5.record_family_registry import (
    record_family_specs,
    registry_family_specs,
    validate_record_family_registry,
)
from brain.v5.runtime_audit import build_runtime_capability_audit


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_every_writable_family_has_path_ref_and_inventory_contract():
    specs = record_family_specs()

    assert "claims" in specs
    assert "source_assets" in specs
    assert "monitor_snapshots" in specs
    for family, spec in specs.items():
        assert spec.family == family
        assert spec.relative_dir
        assert spec.id_field
        assert "exact_ref" in spec.participates_in
        assert "inventory" in spec.participates_in


def test_registry_contains_every_literal_registry_family():
    audit = build_runtime_capability_audit(REPO_ROOT)

    assert set(audit["record_families"]["literal_uses"]) <= set(record_family_specs())
    assert audit["record_families"]["used_not_layout"] == []


def test_record_family_registry_contract_is_self_consistent():
    payload = validate_record_family_registry()

    assert payload["ok"] is True
    assert payload["errors"] == []
    assert payload["registry_family_count"] == 42
    assert payload["special_family_count"] == 4
    assert payload["truth_source"] == "record_family_specs"
    assert payload["can_update_kernel_state"] is False
    assert payload["can_update_claim_trust"] is False

    assert "authoritie" not in record_family_specs()["authorities"].exact_ref_aliases
    assert "memory_entrie" not in record_family_specs()["memory_entries"].exact_ref_aliases
    assert "claim_statuse" not in record_family_specs()["claim_statuses"].exact_ref_aliases

    assert "id" in record_family_specs()["claims"].legacy_id_fields
    assert "reference_location_id" in record_family_specs()["reference_locations"].legacy_id_fields
    assert "validation_result_id" in record_family_specs()["validation_results"].legacy_id_fields


def test_record_family_contract_rejects_incomplete_query_and_surface_metadata():
    specs = record_family_specs()
    specs["claims"] = replace(
        specs["claims"],
        surface="",
        index_fields=("topic_id",),
        schema_version="",
        trust_effect="promotes_claim",
    )

    payload = validate_specs(specs)

    assert payload["ok"] is False
    assert any("surface" in error for error in payload["errors"])
    assert any("index_fields" in error for error in payload["errors"])
    assert any("schema_version" in error for error in payload["errors"])
    assert any("trust_effect" in error for error in payload["errors"])


def test_family_consumers_are_canonical_registry_projections():
    from brain.v5 import lifecycle_events, paths, record_refs, workspace_inventory

    expected = set(registry_family_specs())
    assert set(paths.registry_layout_families()) == expected
    assert set(record_refs.record_ref_registry_families()) == expected
    assert set(workspace_inventory.REGISTRY_FAMILIES) == expected

    lifecycle_expected = {
        spec.record_kind: spec.family
        for spec in registry_family_specs().values()
        if "lifecycle" in spec.participates_in
    }
    assert lifecycle_events.lifecycle_subject_families() == lifecycle_expected


def test_unimplemented_layout_family_is_readable_but_not_auto_writable(tmp_path):
    from brain.v5.markdown import write_md
    from brain.v5.record_refs import lookup_record_refs
    from brain.v5.workspace import init_workspace

    spec = record_family_specs()["outputs"]
    assert spec.record_class is None
    assert spec.auto_write_policy == "unimplemented_layout"

    ws = init_workspace(tmp_path)
    write_md(
        ws.registry_dir("outputs") / "output-1.md",
        {"output_id": "output-1", "kind": "output"},
        "# Historical output\n",
    )

    result = lookup_record_refs(ws, ["output:output-1"])["refs"][0]
    assert result["status"] == "found"
    assert result["record_kind"] == "output"
    assert result["can_update_record_claim_trust"] is False


def test_special_record_paths_are_exact_ref_addressable_without_registry_aliasing(tmp_path):
    from brain.v5.record_refs import lookup_record_refs
    from brain.v5.workspace import create_context, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_context(ws, "formal-theory", title="Formal Theory")
    create_topic(ws, "qg", context_id="formal-theory", title="Quantum Gravity")

    refs = lookup_record_refs(ws, ["context:formal-theory", "topic:qg"])

    assert [item["status"] for item in refs["refs"]] == ["found", "found"]
    assert record_family_specs()["contexts"].is_registry_family is False
    assert record_family_specs()["topics"].is_registry_family is False
    assert record_family_specs()["sessions"].surface == "session_binding"
