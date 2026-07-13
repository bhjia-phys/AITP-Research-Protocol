"""Hash-pinned read-only probes for real research vertical acceptance."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from brain.v5.context_compiler import ContextRequest, compile_research_context
from brain.v5.paths import WorkspacePaths
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository


def run_librpa_real_probe(
    *,
    topics_root: Path,
    manifest_path: Path,
) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("kind") != "librpa_real_probe_manifest":
        raise ValueError("unexpected LibRPA real-probe manifest kind")
    if manifest.get("review_status") != "authorized_for_read_only_probe":
        raise ValueError("LibRPA real-probe manifest is not authorized")

    inputs = {}
    for name in ("final_table", "status_table", "collector_script"):
        spec = manifest["inputs"][name]
        path = Path(spec["path"])
        if not path.is_file():
            raise FileNotFoundError(f"real-probe input is unavailable: {path}")
        actual_hash = _sha256(path)
        if actual_hash != spec["sha256"]:
            raise ValueError(f"real-probe input hash changed for {name}: {path}")
        inputs[name] = {
            "path": str(path),
            "sha256": actual_hash,
            "size_bytes": path.stat().st_size,
        }

    final_rows = _read_tsv(Path(inputs["final_table"]["path"]))
    accepted_rows = [
        row
        for row in final_rows
        if _true(row.get("finished"))
        and _true(row.get("converged"))
        and _true(row.get("usable_for_final"))
        and float(row.get("gap_eV") or 0.0) > 0.0
    ]
    minimum = int(manifest["acceptance"]["minimum_final_rows"])
    if len(accepted_rows) < minimum or len(accepted_rows) != len(final_rows):
        raise ValueError(
            "final table contains rows outside the approved finished/converged/positive contract"
        )
    materials = sorted({row["material"] for row in accepted_rows})
    required_materials = sorted(manifest["acceptance"]["required_materials"])
    if not set(required_materials).issubset(materials):
        raise ValueError("final table does not cover every required material")

    status_rows = _read_tsv(Path(inputs["status_table"]["path"]))
    if not status_rows:
        raise ValueError("status collector table is empty")
    script_text = Path(inputs["collector_script"]["path"]).read_text(encoding="utf-8")
    required_policy_markers = manifest["acceptance"]["collector_policy_markers"]
    missing_markers = [marker for marker in required_policy_markers if marker not in script_text]
    if missing_markers:
        raise ValueError(f"collector policy markers are missing: {missing_markers}")

    ws = WorkspacePaths(topics_root)
    bundle = compile_research_context(
        ws,
        ContextRequest(
            session_id=manifest["session_id"],
            objective_text=manifest["objective"],
            max_tokens=1200,
            max_bytes=6000,
            candidate_limit=12,
        ),
    )
    selected_families = {item["family"] for item in bundle.candidate_summaries}
    required_context_families = set(manifest["acceptance"]["required_context_families"])
    if not required_context_families.issubset(selected_families):
        missing = sorted(required_context_families - selected_families)
        raise ValueError(f"real LibRPA context is missing required families: {missing}")
    if bundle.index_status != "fresh" or bundle.read_errors:
        raise ValueError("real LibRPA context is stale or contains read errors")

    fingerprint_basis = {
        "manifest_sha256": _sha256(manifest_path),
        "inputs": inputs,
        "index_generation": bundle.source_index_generation,
        "topic_id": bundle.topic_id,
    }
    return {
        "ok": True,
        "kind": "real_vertical_probe_receipt",
        "vertical": "librpa_hpc",
        "status": "passed",
        "topic_id": bundle.topic_id,
        "index_generation": bundle.source_index_generation,
        "input_fingerprint": hashlib.sha256(
            json.dumps(fingerprint_basis, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "inputs": inputs,
        "final_row_count": len(accepted_rows),
        "materials": materials,
        "selected_context_families": sorted(selected_families),
        "not_shown_count": bundle.not_shown_count,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def run_qft_qg_real_probe(
    *,
    topics_root: Path,
    manifest_path: Path,
) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("kind") != "qft_qg_real_probe_manifest":
        raise ValueError("unexpected QFT/QG real-probe manifest kind")
    ws = WorkspacePaths(topics_root)
    repository = RecordRepository(
        ws,
        actor=RecordActor(actor_type="tool", actor_id="qft_qg_real_probe", host="aitp-v5"),
    )
    source_receipts = []
    source_refs = []
    anchor_expectations: dict[str, dict[str, Any]] = {}
    arxiv_ids = set()
    for source in manifest["sources"]:
        ref = source["record_ref"]
        result = repository.read(ref)
        if result.status != "found" or result.record is None:
            raise ValueError(f"QFT/QG source record is unavailable: {ref}")
        record = result.record
        if record.content_hash != source["sha256"] or record.hash_algorithm != "sha256":
            raise ValueError(f"QFT/QG source record hash mismatch: {ref}")
        local_path = Path(record.metadata["local_path"])
        if _sha256(local_path) != source["sha256"]:
            raise ValueError(f"QFT/QG source PDF bytes changed: {local_path}")
        arxiv_id = str(record.metadata.get("arxiv_id") or "")
        paired_with = str(record.metadata.get("paired_with") or "")
        if paired_with != source["paired_with"]:
            raise ValueError(f"QFT/QG paired-source metadata changed: {ref}")
        arxiv_ids.add(arxiv_id)
        source_refs.append(ref)
        exact_anchor = source.get("exact_anchor")
        if not isinstance(exact_anchor, dict) or not exact_anchor:
            raise ValueError(f"QFT/QG source lacks an exact-anchor contract: {ref}")
        anchor_expectations[ref] = {
            **exact_anchor,
            "source_sha256": source["sha256"],
        }
        source_receipts.append(
            {
                "record_ref": ref,
                "title": record.title,
                "arxiv_id": arxiv_id,
                "paired_with": paired_with,
                "sha256": source["sha256"],
                "size_bytes": local_path.stat().st_size,
            }
        )
    if arxiv_ids != {source["arxiv_id"] for source in manifest["sources"]}:
        raise ValueError("QFT/QG source set does not match the manifest")

    bundle = compile_research_context(
        ws,
        ContextRequest(
            session_id=manifest["session_id"],
            objective_text=manifest["objective"],
            exact_refs=tuple(source_refs),
            max_tokens=1200,
            max_bytes=6000,
            candidate_limit=12,
        ),
    )
    selected_refs = {item["record_ref"] for item in bundle.candidate_summaries}
    if not set(source_refs).issubset(selected_refs):
        raise ValueError("bounded QFT/QG context did not retain both paired sources")
    topic_id = manifest["topic_id"]
    proof_obligations = [
        record
        for record in _records(repository, "proof_obligations")
        if record.topic_id == topic_id
    ]
    relations = [
        record for record in _records(repository, "object_relations") if record.topic_id == topic_id
    ]
    objects = [
        record for record in _records(repository, "physics_objects") if record.topic_id == topic_id
    ]
    locations = [
        record
        for record in _records(repository, "reference_locations")
        if record.topic_id == topic_id
    ]
    exploratory_records = [
        record
        for record in _records(repository, "exploratory_records")
        if record.topic_id == topic_id
    ]
    claim_id = str(manifest.get("claim_id") or "")
    if not claim_id:
        raise ValueError("QFT/QG real-probe manifest must pin the active claim")
    coverage = _assess_qft_qg_derivation_coverage(
        source_refs=source_refs,
        claim_id=claim_id,
        anchor_expectations=anchor_expectations,
        required_proof_strategy=list(manifest.get("required_proof_strategy") or []),
        proof_obligations=proof_obligations,
        relations=relations,
        objects=objects,
        locations=locations,
        exploratory_records=exploratory_records,
    )
    blockers = []
    if not coverage["source_grounded_proof_obligation_count"]:
        blockers.append("missing_real_canonical_proof_obligation_or_derivation_chain")
    if (
        not coverage["source_grounded_object_relation_count"]
        or coverage["source_grounded_physics_object_count"] < len(source_refs)
    ):
        blockers.append("missing_real_grounded_object_relation_graph")
    if coverage["exact_reference_source_count"] < len(source_refs):
        blockers.append("missing_real_exact_reference_locations")
    if not coverage["source_linked_speculative_insight_count"]:
        blockers.append("missing_real_separated_speculative_insight")
    status = "passed" if not blockers else "blocked"
    fingerprint_basis = {
        "manifest_sha256": _sha256(manifest_path),
        "sources": source_receipts,
        "index_generation": bundle.source_index_generation,
        "counts": {
            "proof_obligations": len(proof_obligations),
            "object_relations": len(relations),
            "physics_objects": len(objects),
            "reference_locations": len(locations),
            "source_grounded_proof_obligations": coverage[
                "source_grounded_proof_obligation_count"
            ],
            "source_grounded_object_relations": coverage[
                "source_grounded_object_relation_count"
            ],
            "source_grounded_physics_objects": coverage[
                "source_grounded_physics_object_count"
            ],
            "exact_reference_locations": coverage["exact_reference_location_count"],
            "exact_reference_sources": coverage["exact_reference_source_count"],
            "source_linked_speculative_insights": coverage[
                "source_linked_speculative_insight_count"
            ],
        },
    }
    return {
        "ok": status == "passed",
        "kind": "real_vertical_probe_receipt",
        "vertical": "qft_qg_knowledge",
        "status": status,
        "topic_id": topic_id,
        "index_generation": bundle.source_index_generation,
        "input_fingerprint": hashlib.sha256(
            json.dumps(fingerprint_basis, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "sources": source_receipts,
        "proof_obligation_count": len(proof_obligations),
        "object_relation_count": len(relations),
        "physics_object_count": len(objects),
        "reference_location_count": len(locations),
        "exploratory_record_count": len(exploratory_records),
        "source_grounded_proof_obligation_count": coverage[
            "source_grounded_proof_obligation_count"
        ],
        "source_grounded_object_relation_count": coverage[
            "source_grounded_object_relation_count"
        ],
        "source_grounded_physics_object_count": coverage[
            "source_grounded_physics_object_count"
        ],
        "exact_reference_location_count": coverage["exact_reference_location_count"],
        "exact_reference_source_count": coverage["exact_reference_source_count"],
        "source_linked_speculative_insight_count": coverage[
            "source_linked_speculative_insight_count"
        ],
        "covered_source_refs": coverage["covered_source_refs"],
        "blockers": blockers,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _assess_qft_qg_derivation_coverage(
    *,
    source_refs: list[str],
    claim_id: str,
    anchor_expectations: dict[str, dict[str, Any]] | None = None,
    required_proof_strategy: list[str] | None = None,
    proof_obligations: list[Any],
    relations: list[Any],
    objects: list[Any],
    locations: list[Any],
    exploratory_records: list[Any] | None = None,
) -> dict[str, Any]:
    expected_sources = list(dict.fromkeys(source_refs))
    anchor_expectations = anchor_expectations or {}
    required_proof_strategy = required_proof_strategy or []
    exploratory_records = exploratory_records or []
    location_refs_by_source = {
        source_ref: {
            f"reference_location:{location.location_id}"
            for location in locations
            if getattr(location, "source_ref", "") == source_ref
            and _matches_exact_anchor(location, anchor_expectations.get(source_ref))
        }
        for source_ref in expected_sources
    }
    exact_location_count = sum(len(refs) for refs in location_refs_by_source.values())
    exact_source_count = sum(bool(refs) for refs in location_refs_by_source.values())

    source_grounded_objects = [
        record
        for record in objects
        if set(getattr(record, "source_refs", [])) & set(expected_sources)
    ]
    object_source_coverage = {
        source_ref
        for source_ref in expected_sources
        if any(
            source_ref in set(getattr(record, "source_refs", []))
            for record in source_grounded_objects
        )
    }
    object_ids_by_source = {
        source_ref: {
            str(getattr(record, "object_id", ""))
            for record in source_grounded_objects
            if source_ref in set(getattr(record, "source_refs", []))
            and str(getattr(record, "object_id", ""))
        }
        for source_ref in expected_sources
    }
    source_grounded_relations = [
        record
        for record in relations
        if getattr(record, "claim_id", "") == claim_id
        and set(expected_sources).issubset(set(getattr(record, "source_refs", [])))
        and getattr(record, "status", "") == "hypothesis"
        and not list(getattr(record, "evidence_refs", []))
        and getattr(record, "metadata", {}).get("can_be_used_as_evidence") is False
        and _connects_distinct_source_objects(
            record,
            expected_sources=expected_sources,
            object_ids_by_source=object_ids_by_source,
        )
    ]
    source_grounded_obligations = [
        record
        for record in proof_obligations
        if getattr(record, "claim_id", "") == claim_id
        and all(
            location_refs_by_source[source_ref]
            & set(getattr(record, "source_refs", []))
            for source_ref in expected_sources
        )
        and getattr(record, "status", "") == "open"
        and getattr(record, "maturity_level", "")
        in {"formula-identified", "theorem-candidate", "publishable"}
        and bool(list(getattr(record, "required_evidence", [])))
        and bool(list(getattr(record, "failure_modes", [])))
        and _has_required_strategy(record, required_proof_strategy)
        and getattr(record, "human_gate_required", False) is True
        and getattr(record, "can_update_claim_trust", True) is False
    ]
    valid_relation_ids = {
        str(getattr(record, "relation_id", ""))
        for record in source_grounded_relations
        if str(getattr(record, "relation_id", ""))
    }
    valid_relation_object_ids = {
        str(value)
        for record in source_grounded_relations
        for value in (getattr(record, "subject_id", ""), getattr(record, "object_id", ""))
        if str(value)
    }
    source_linked_speculative_insights = [
        record
        for record in exploratory_records
        if getattr(record, "claim_id", "") == claim_id
        and getattr(record, "exploration_type", "") == "relation_path_brainstorm"
        and getattr(record, "status", "") == "open"
        and set(expected_sources).issubset(set(getattr(record, "source_refs", [])))
        and valid_relation_ids & set(getattr(record, "relation_ids", []))
        and valid_relation_object_ids.issubset(set(getattr(record, "object_ids", [])))
        and getattr(record, "metadata", {}).get("epistemic_role") == "speculative_insight"
        and getattr(record, "metadata", {}).get("can_be_used_as_evidence") is False
        and getattr(record, "metadata", {}).get("can_update_claim_trust") is False
        and getattr(record, "orientation_only", False) is True
        and getattr(record, "can_update_claim_trust", True) is False
    ]
    covered_source_refs = [
        source_ref
        for source_ref in expected_sources
        if location_refs_by_source[source_ref] and source_ref in object_source_coverage
    ]
    ready = bool(
        len(covered_source_refs) == len(expected_sources)
        and source_grounded_relations
        and source_grounded_obligations
        and source_linked_speculative_insights
    )
    return {
        "ready": ready,
        "covered_source_refs": covered_source_refs,
        "source_grounded_proof_obligation_count": len(source_grounded_obligations),
        "source_grounded_object_relation_count": len(source_grounded_relations),
        "source_grounded_physics_object_count": len(source_grounded_objects),
        "exact_reference_location_count": exact_location_count,
        "exact_reference_source_count": exact_source_count,
        "source_linked_speculative_insight_count": len(
            source_linked_speculative_insights
        ),
    }


def _matches_exact_anchor(location: Any, expectation: dict[str, Any] | None) -> bool:
    if not expectation:
        return True
    if getattr(location, "location_type", "") != "paper_equation_range":
        return False
    if getattr(location, "status", "") != "located":
        return False
    if str(getattr(location, "uri", "")) != str(expectation.get("uri") or ""):
        return False
    metadata = getattr(location, "metadata", {})
    if not isinstance(metadata, dict):
        return False
    for field in ("arxiv_version", "section_number", "source_sha256"):
        if str(metadata.get(field) or "") != str(expectation.get(field) or ""):
            return False
    return list(metadata.get("equation_labels") or []) == list(
        expectation.get("equation_labels") or []
    )


def _connects_distinct_source_objects(
    relation: Any,
    *,
    expected_sources: list[str],
    object_ids_by_source: dict[str, set[str]],
) -> bool:
    subject_id = str(getattr(relation, "subject_id", ""))
    object_id = str(getattr(relation, "object_id", ""))
    if not subject_id or not object_id or subject_id == object_id:
        return False
    return any(
        subject_id in object_ids_by_source[left]
        and object_id in object_ids_by_source[right]
        for left in expected_sources
        for right in expected_sources
        if left != right
    )


def _has_required_strategy(record: Any, required: list[str]) -> bool:
    strategy = list(getattr(record, "proof_strategy", []))
    if not strategy:
        return False
    return not required or strategy[: len(required)] == required


def _read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _records(repository: RecordRepository, family: str) -> list[Any]:
    report = repository.list(family)
    if report.malformed:
        raise ValueError(f"real probe cannot read malformed {family} records")
    return list(report.records)


def _true(value: Any) -> bool:
    return str(value or "").strip().lower() == "true"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
