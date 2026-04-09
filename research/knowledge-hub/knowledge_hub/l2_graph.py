from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


CANONICAL_DIR_BY_TYPE = {
    "atomic_note": "atomic-notes",
    "concept": "concepts",
    "claim_card": "claim-cards",
    "derivation_object": "derivation-objects",
    "method": "methods",
    "workflow": "workflows",
    "topic_skill_projection": "topic-skill-projections",
    "bridge": "bridges",
    "example_card": "examples",
    "validation_pattern": "validation-patterns",
    "warning_note": "warning-notes",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def _validator(path: Path) -> Draft202012Validator:
    return Draft202012Validator(json.loads(path.read_text(encoding="utf-8")))


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_]+", text.lower())


def _relative(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def _unit_path(kernel_root: Path, unit_id: str, unit_type: str) -> Path:
    slug = unit_id.split(":", 1)[1]
    return kernel_root / "canonical" / CANONICAL_DIR_BY_TYPE[unit_type] / f"{unit_type}--{slug}.json"


def _staging_root(kernel_root: Path) -> Path:
    return kernel_root / "canonical" / "staging"


def _staging_entry_path(kernel_root: Path, entry_id: str) -> Path:
    slug = entry_id.split(":", 1)[1]
    return _staging_root(kernel_root) / "entries" / f"staging--{slug}.json"


def _base_unit(
    *,
    unit_id: str,
    unit_type: str,
    title: str,
    summary: str,
    tags: list[str],
    assumptions: list[str],
    dependencies: list[str],
    related_units: list[str],
    payload: dict[str, Any],
    updated_by: str,
    timestamp: str,
) -> dict[str, Any]:
    return {
        "id": unit_id,
        "unit_type": unit_type,
        "title": title,
        "summary": summary,
        "maturity": "human_promoted",
        "created_at": timestamp,
        "updated_at": timestamp,
        "topic_completion_status": "regression-stable",
        "tags": tags,
        "assumptions": assumptions,
        "regime": {
            "domain": "tfim benchmark-first seed",
            "approximations": ["tiny exact benchmark"],
            "scale": "smoke-test",
            "boundary_conditions": ["bounded public route"],
            "exclusions": ["large-scale numerics", "broad portability claims"],
        },
        "scope": {
            "applies_to": ["bounded TFIM benchmark memory"],
            "out_of_scope": ["full many-body closure"],
        },
        "provenance": {
            "source_ids": [
                "source:tfim-exact-diagonalization-tool",
                "source:tfim-benchmark-code-method-acceptance",
                "source:aitp-test-runbook",
            ],
            "l1_artifacts": [
                "README.md#tfim-code-method-acceptance",
                "runtime/AITP_TEST_RUNBOOK.md#real-topic-acceptance-code-backed-benchmark-first-lane",
            ],
            "l3_runs": ["runtime/scripts/run_tfim_benchmark_code_method_acceptance.py"],
            "l4_checks": [
                "runtime/scripts/run_tfim_benchmark_code_method_acceptance.py",
                "validation/tools/tfim_exact_diagonalization.py",
            ],
            "citations": ["AITP public TFIM benchmark-first acceptance lane"],
        },
        "promotion": {
            "route": "L3->L4->L2",
            "review_mode": "human",
            "canonical_layer": "L2",
            "promoted_by": updated_by,
            "promoted_at": timestamp,
            "review_status": "accepted",
            "rationale": "Repo-seeded L2 MVP direction for the public TFIM benchmark-first lane.",
        },
        "dependencies": dependencies,
        "related_units": related_units,
        "payload": payload,
    }


def _tfim_units(updated_by: str, timestamp: str) -> list[dict[str, Any]]:
    return [
        _base_unit(
            unit_id="concept:tfim-transverse-field-ising-model",
            unit_type="concept",
            title="TFIM benchmark substrate",
            summary="Small finite-size TFIM substrate used for the first bounded exact benchmark.",
            tags=["tfim", "spin-chain", "toy-model"],
            assumptions=["Small-system TFIM is an honest first validation substrate."],
            dependencies=[],
            related_units=["method:tfim-exact-diagonalization-helper", "workflow:tfim-benchmark-workflow"],
            payload={"definition": "Bounded TFIM substrate for the public exact benchmark."},
            updated_by=updated_by,
            timestamp=timestamp,
        ),
        _base_unit(
            unit_id="concept:tfim-benchmark-first-validation",
            unit_type="concept",
            title="Benchmark-first validation",
            summary="Broader code-memory claims should wait until the tiny exact benchmark closes.",
            tags=["tfim", "benchmark-first", "code-method"],
            assumptions=["A bounded exact result is stronger than a first successful code run."],
            dependencies=[],
            related_units=["claim_card:tfim-benchmark-before-portability-claim"],
            payload={"definition": "Validation posture that promotes the exact benchmark before portability."},
            updated_by=updated_by,
            timestamp=timestamp,
        ),
        _base_unit(
            unit_id="method:tfim-exact-diagonalization-helper",
            unit_type="method",
            title="TFIM exact-diagonalization helper",
            summary="Dense exact diagonalization helper used for the public tiny TFIM benchmark.",
            tags=["tfim", "exact-diagonalization", "benchmark"],
            assumptions=["Dense exact diagonalization is affordable only for very small systems."],
            dependencies=["concept:tfim-transverse-field-ising-model"],
            related_units=["workflow:tfim-benchmark-workflow", "warning_note:tfim-dense-ed-finite-size-limit"],
            payload={"tool_path": "validation/tools/tfim_exact_diagonalization.py"},
            updated_by=updated_by,
            timestamp=timestamp,
        ),
        _base_unit(
            unit_id="workflow:tfim-benchmark-workflow",
            unit_type="workflow",
            title="TFIM benchmark workflow",
            summary="Benchmark-first workflow that runs the tiny TFIM exact result before reuse.",
            tags=["tfim", "workflow", "benchmark-first"],
            assumptions=["The first reusable workflow memory should stay tied to the bounded benchmark."],
            dependencies=[
                "concept:tfim-transverse-field-ising-model",
                "concept:tfim-benchmark-first-validation",
                "method:tfim-exact-diagonalization-helper",
            ],
            related_units=[
                "validation_pattern:tfim-small-system-gap-reproduction",
                "warning_note:tfim-dense-ed-finite-size-limit",
                "topic_skill_projection:tfim-benchmark-first-route",
            ],
            payload={"steps": ["prepare config", "run helper", "check gap", "attach warning"]},
            updated_by=updated_by,
            timestamp=timestamp,
        ),
        _base_unit(
            unit_id="validation_pattern:tfim-small-system-gap-reproduction",
            unit_type="validation_pattern",
            title="TFIM small-system gap reproduction",
            summary="Validation pattern that checks the bounded exact gap before broader method claims.",
            tags=["tfim", "validation", "gap"],
            assumptions=["The tiny exact gap is a meaningful first benchmark in this lane."],
            dependencies=["method:tfim-exact-diagonalization-helper"],
            related_units=["claim_card:tfim-benchmark-before-portability-claim"],
            payload={"validation_axes": ["exact-gap reproduction", "artifact persistence"]},
            updated_by=updated_by,
            timestamp=timestamp,
        ),
        _base_unit(
            unit_id="warning_note:tfim-dense-ed-finite-size-limit",
            unit_type="warning_note",
            title="Dense exact diagonalization finite-size limit",
            summary="The public TFIM helper is only a tiny-system benchmark gate and not a scalable solver claim.",
            tags=["tfim", "warning", "finite-size"],
            assumptions=["Dense exact diagonalization does not scale to larger systems in this route."],
            dependencies=["method:tfim-exact-diagonalization-helper"],
            related_units=["workflow:tfim-benchmark-workflow", "claim_card:tfim-benchmark-before-portability-claim"],
            payload={"warning_tags": ["finite-size", "benchmark-only", "non-scalable"]},
            updated_by=updated_by,
            timestamp=timestamp,
        ),
        _base_unit(
            unit_id="claim_card:tfim-benchmark-before-portability-claim",
            unit_type="claim_card",
            title="Benchmark before portability claim",
            summary="Promote the bounded exact benchmark memory before promoting broader code portability.",
            tags=["tfim", "claim", "benchmark-first"],
            assumptions=["The exact benchmark is the honest first closure target."],
            dependencies=[
                "concept:tfim-benchmark-first-validation",
                "validation_pattern:tfim-small-system-gap-reproduction",
            ],
            related_units=["warning_note:tfim-dense-ed-finite-size-limit", "topic_skill_projection:tfim-benchmark-first-route"],
            payload={"claim": "Benchmark-first promotion should precede portability claims."},
            updated_by=updated_by,
            timestamp=timestamp,
        ),
        _base_unit(
            unit_id="bridge:tfim-toy-model-code-method-bridge",
            unit_type="bridge",
            title="TFIM toy-model to code-method bridge",
            summary="The bounded TFIM benchmark bridges toy-model understanding and code-method route memory.",
            tags=["tfim", "bridge", "toy-model", "code-method"],
            assumptions=["One bounded benchmark can support both physics interpretation and workflow memory."],
            dependencies=["concept:tfim-transverse-field-ising-model", "workflow:tfim-benchmark-workflow"],
            related_units=["topic_skill_projection:tfim-benchmark-first-route"],
            payload={"bridge_statement": "Bounded benchmark links toy-model physics and code-method memory."},
            updated_by=updated_by,
            timestamp=timestamp,
        ),
        _base_unit(
            unit_id="topic_skill_projection:tfim-benchmark-first-route",
            unit_type="topic_skill_projection",
            title="TFIM benchmark-first route",
            summary="Reusable route capsule for the bounded TFIM exact benchmark workflow and its limitation note.",
            tags=["tfim", "topic-skill-projection", "benchmark-first"],
            assumptions=["The route stays bounded to the public exact benchmark."],
            dependencies=["workflow:tfim-benchmark-workflow", "method:tfim-exact-diagonalization-helper"],
            related_units=[
                "warning_note:tfim-dense-ed-finite-size-limit",
                "claim_card:tfim-benchmark-before-portability-claim",
                "bridge:tfim-toy-model-code-method-bridge",
            ],
            payload={"required_first_routes": ["Run the tiny exact benchmark before broader claims."]},
            updated_by=updated_by,
            timestamp=timestamp,
        ),
    ]


def _tfim_edges() -> list[dict[str, Any]]:
    return [
        {"edge_id": "benchmark-first-supports-claim", "from_id": "concept:tfim-benchmark-first-validation", "relation": "supports", "to_id": "claim_card:tfim-benchmark-before-portability-claim", "evidence_refs": ["README.md"], "notes": "Benchmark-first posture supports the bounded claim."},
        {"edge_id": "gap-pattern-uses-ed-helper", "from_id": "validation_pattern:tfim-small-system-gap-reproduction", "relation": "uses_method", "to_id": "method:tfim-exact-diagonalization-helper", "evidence_refs": ["validation/tools/tfim_exact_diagonalization.py"], "notes": "Gap reproduction uses the helper."},
        {"edge_id": "claim-validated-by-gap-pattern", "from_id": "claim_card:tfim-benchmark-before-portability-claim", "relation": "validated_by", "to_id": "validation_pattern:tfim-small-system-gap-reproduction", "evidence_refs": ["runtime/scripts/run_tfim_benchmark_code_method_acceptance.py"], "notes": "The bounded claim is validated by the gap benchmark."},
        {"edge_id": "workflow-uses-ed-helper", "from_id": "workflow:tfim-benchmark-workflow", "relation": "uses_method", "to_id": "method:tfim-exact-diagonalization-helper", "evidence_refs": ["validation/tools/tfim_exact_diagonalization.py"], "notes": "The workflow calls the helper."},
        {"edge_id": "workflow-depends-on-tfim", "from_id": "workflow:tfim-benchmark-workflow", "relation": "depends_on", "to_id": "concept:tfim-transverse-field-ising-model", "evidence_refs": ["runtime/scripts/run_tfim_benchmark_code_method_acceptance.py"], "notes": "The workflow is TFIM-specific."},
        {"edge_id": "workflow-depends-on-benchmark-first", "from_id": "workflow:tfim-benchmark-workflow", "relation": "depends_on", "to_id": "concept:tfim-benchmark-first-validation", "evidence_refs": ["README.md"], "notes": "The workflow uses the benchmark-first posture."},
        {"edge_id": "workflow-warned-by-finite-size-limit", "from_id": "workflow:tfim-benchmark-workflow", "relation": "warned_by", "to_id": "warning_note:tfim-dense-ed-finite-size-limit", "evidence_refs": ["validation/tools/tfim_exact_diagonalization.py"], "notes": "The workflow carries the finite-size warning."},
        {"edge_id": "projection-depends-on-workflow", "from_id": "topic_skill_projection:tfim-benchmark-first-route", "relation": "depends_on", "to_id": "workflow:tfim-benchmark-workflow", "evidence_refs": ["runtime/scripts/run_tfim_benchmark_code_method_acceptance.py"], "notes": "The route capsule depends on the workflow."},
        {"edge_id": "projection-uses-ed-helper", "from_id": "topic_skill_projection:tfim-benchmark-first-route", "relation": "uses_method", "to_id": "method:tfim-exact-diagonalization-helper", "evidence_refs": ["runtime/scripts/run_tfim_benchmark_code_method_acceptance.py"], "notes": "The route capsule reuses the helper."},
        {"edge_id": "projection-warned-by-finite-size-limit", "from_id": "topic_skill_projection:tfim-benchmark-first-route", "relation": "warned_by", "to_id": "warning_note:tfim-dense-ed-finite-size-limit", "evidence_refs": ["validation/tools/tfim_exact_diagonalization.py"], "notes": "The route capsule includes the finite-size warning."},
        {"edge_id": "claim-warned-by-finite-size-limit", "from_id": "claim_card:tfim-benchmark-before-portability-claim", "relation": "warned_by", "to_id": "warning_note:tfim-dense-ed-finite-size-limit", "evidence_refs": ["validation/tools/tfim_exact_diagonalization.py"], "notes": "The bounded claim stays under the same warning."},
        {"edge_id": "bridge-supports-projection", "from_id": "bridge:tfim-toy-model-code-method-bridge", "relation": "supports", "to_id": "topic_skill_projection:tfim-benchmark-first-route", "evidence_refs": ["README.md"], "notes": "The bridge explains the reusable route."},
    ]


def materialize_canonical_index(kernel_root: Path) -> dict[str, Any]:
    canonical_root = kernel_root / "canonical"
    rows: list[dict[str, Any]] = []
    for unit_type, directory in sorted(CANONICAL_DIR_BY_TYPE.items()):
        unit_dir = canonical_root / directory
        if not unit_dir.exists():
            continue
        for path in sorted(unit_dir.glob("*.json")):
            payload = read_json(path)
            if payload is None:
                continue
            rows.append(
                {
                    "unit_id": payload["id"],
                    "id": payload["id"],
                    "unit_type": payload["unit_type"],
                    "title": payload["title"],
                    "summary": payload["summary"],
                    "tags": list(payload.get("tags") or []),
                    "assumptions": list(payload.get("assumptions") or []),
                    "regime": payload.get("regime") or {},
                    "scope": payload.get("scope") or {},
                    "dependencies": list(payload.get("dependencies") or []),
                    "related_units": list(payload.get("related_units") or []),
                    "warning_tags": list((payload.get("payload") or {}).get("warning_tags") or []),
                    "validation_tags": list((payload.get("payload") or {}).get("validation_axes") or []),
                    "path": _relative(path, kernel_root),
                    "search_terms": " ".join(
                        [
                            payload.get("title") or "",
                            payload.get("summary") or "",
                            " ".join(payload.get("tags") or []),
                            " ".join(payload.get("assumptions") or []),
                        ]
                    ),
                }
            )
    rows.sort(key=lambda row: str(row["id"]))
    write_jsonl(canonical_root / "index.jsonl", rows)
    return {"index_path": str(canonical_root / "index.jsonl"), "row_count": len(rows)}


def seed_l2_demo_direction(kernel_root: Path, *, direction: str, updated_by: str) -> dict[str, Any]:
    if direction != "tfim-benchmark-first":
        raise ValueError(f"Unsupported L2 demo direction: {direction}")
    timestamp = now_iso()
    canonical_root = kernel_root / "canonical"
    unit_validator = _validator(canonical_root / "canonical-unit.schema.json")
    edge_validator = _validator(kernel_root / "schemas" / "edge.schema.json")
    units = _tfim_units(updated_by, timestamp)
    edges = _tfim_edges()
    for unit in units:
        unit_validator.validate(unit)
        write_json(_unit_path(kernel_root, unit["id"], unit["unit_type"]), unit)
    for edge in edges:
        edge_validator.validate(edge)
    write_jsonl(canonical_root / "edges.jsonl", edges)
    index_payload = materialize_canonical_index(kernel_root)
    return {
        "direction": direction,
        "unit_count": len(units),
        "edge_count": len(edges),
        "index_path": index_payload["index_path"],
        "index_row_count": index_payload["row_count"],
        "updated_by": updated_by,
    }


def stage_l2_insight(
    kernel_root: Path,
    *,
    title: str,
    summary: str,
    candidate_unit_type: str,
    tags: list[str],
    source_refs: list[str],
    created_by: str,
    assumptions: list[str] | None = None,
    linked_unit_ids: list[str] | None = None,
    contradicts_unit_ids: list[str] | None = None,
    integration_summary: str | None = None,
    failure_kind: str | None = None,
    failed_route: str | None = None,
    next_implication: str | None = None,
    scope_note: str | None = None,
    topic_slug: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    timestamp = now_iso()
    slug = re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", title.lower())).strip("-") or "l2-insight"
    entry_id = f"staging:{slug}"
    entry = {
        "entry_id": entry_id,
        "title": title,
        "summary": summary,
        "candidate_unit_type": candidate_unit_type,
        "trust_surface": "staging",
        "status": "staged",
        "tags": tags,
        "source_refs": source_refs,
        "assumptions": list(assumptions or []),
        "linked_unit_ids": list(linked_unit_ids or []),
        "contradicts_unit_ids": list(contradicts_unit_ids or []),
        "integration_summary": integration_summary or "",
        "failure_kind": failure_kind or "",
        "failed_route": failed_route or "",
        "next_implication": next_implication or "",
        "scope_note": scope_note or "",
        "topic_slug": topic_slug or "",
        "created_at": timestamp,
        "updated_at": timestamp,
        "created_by": created_by,
        "notes": notes or "",
    }
    _validator(kernel_root / "schemas" / "l2-staging-entry.schema.json").validate(entry)
    write_json(_staging_entry_path(kernel_root, entry_id), entry)
    index_path = _staging_root(kernel_root) / "staging_index.jsonl"
    rows = [row for row in read_jsonl(index_path) if row.get("entry_id") != entry_id]
    rows.append(
        {
            "entry_id": entry_id,
            "title": title,
            "summary": summary,
            "candidate_unit_type": candidate_unit_type,
            "trust_surface": "staging",
            "status": "staged",
            "tags": tags,
            "source_refs": source_refs,
            "linked_unit_ids": list(linked_unit_ids or []),
            "contradicts_unit_ids": list(contradicts_unit_ids or []),
            "integration_summary": integration_summary or "",
            "failure_kind": failure_kind or "",
            "failed_route": failed_route or "",
            "next_implication": next_implication or "",
            "path": _relative(_staging_entry_path(kernel_root, entry_id), kernel_root),
            "search_terms": " ".join(
                [
                    title,
                    summary,
                    " ".join(tags),
                    " ".join(assumptions or []),
                    integration_summary or "",
                    failure_kind or "",
                    failed_route or "",
                    next_implication or "",
                ]
            ),
            "created_at": timestamp,
            "updated_at": timestamp,
        }
    )
    rows.sort(key=lambda row: str(row["entry_id"]))
    write_jsonl(index_path, rows)
    return entry


def consult_canonical_l2(
    kernel_root: Path,
    *,
    query_text: str,
    retrieval_profile: str,
    max_primary_hits: int | None = None,
    include_staging: bool = False,
) -> dict[str, Any]:
    canonical_root = kernel_root / "canonical"
    index_path = canonical_root / "index.jsonl"
    if not index_path.exists() or not read_jsonl(index_path):
        materialize_canonical_index(kernel_root)
    profiles = (read_json(canonical_root / "retrieval_profiles.json") or {}).get("profiles") or {}
    if retrieval_profile not in profiles:
        raise ValueError(f"Unknown retrieval profile: {retrieval_profile}")
    profile = profiles[retrieval_profile]
    preferred_types = set(profile.get("preferred_unit_types") or [])
    edge_expansion = set(profile.get("edge_expansion") or [])
    limit = int(max_primary_hits or profile.get("max_primary_hits") or 8)
    index_rows = read_jsonl(index_path)
    edge_rows = read_jsonl(canonical_root / "edges.jsonl")
    row_by_id = {str(row["id"]): row for row in index_rows}
    query_terms = set(_tokenize(query_text))
    query_phrase = " ".join(query_text.lower().split())

    scored: list[dict[str, Any]] = []
    for row in index_rows:
        searchable = str(row.get("search_terms") or "")
        terms = set(_tokenize(searchable))
        overlap = query_terms & terms
        if not overlap and query_phrase not in searchable.lower():
            continue
        score = float(len(overlap))
        if query_phrase and query_phrase in searchable.lower():
            score += 2.0
        if str(row.get("unit_type") or "") in preferred_types:
            score += 0.5
        scored.append({**row, "score": round(score, 3), "matched_terms": sorted(overlap)})
    scored.sort(key=lambda row: (-float(row["score"]), str(row["id"])))
    primary_hits = scored[:limit]
    primary_ids = {str(row["id"]) for row in primary_hits}

    expanded_hits: list[dict[str, Any]] = []
    seen: set[str] = set()
    expanded_edge_types: list[str] = []
    for edge in edge_rows:
        relation = str(edge.get("relation") or "")
        if relation not in edge_expansion:
            continue
        from_id = str(edge.get("from_id") or "")
        to_id = str(edge.get("to_id") or "")
        if from_id in primary_ids and to_id not in primary_ids and to_id in row_by_id:
            if to_id not in seen:
                seen.add(to_id)
                expanded_hits.append({**row_by_id[to_id], "via_relation": relation, "via_id": from_id})
            if relation not in expanded_edge_types:
                expanded_edge_types.append(relation)
        if to_id in primary_ids and from_id not in primary_ids and from_id in row_by_id:
            if from_id not in seen:
                seen.add(from_id)
                expanded_hits.append({**row_by_id[from_id], "via_relation": relation, "via_id": to_id})
            if relation not in expanded_edge_types:
                expanded_edge_types.append(relation)

    staged_hits: list[dict[str, Any]] = []
    if include_staging:
        staging_rows = read_jsonl(_staging_root(kernel_root) / "staging_index.jsonl")
        for row in staging_rows:
            searchable = str(row.get("search_terms") or "")
            terms = set(_tokenize(searchable))
            overlap = query_terms & terms
            if not overlap and query_phrase not in searchable.lower():
                continue
            staged_hits.append({**row, "matched_terms": sorted(overlap)})

    return {
        "query_text": query_text,
        "retrieval_profile": retrieval_profile,
        "primary_hits": primary_hits,
        "expanded_hits": expanded_hits,
        "staged_hits": staged_hits,
        "expanded_edge_types": expanded_edge_types,
        "index_count": len(index_rows),
        "edge_count": len(edge_rows),
    }
