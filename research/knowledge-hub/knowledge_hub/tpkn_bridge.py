from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


AITP_TO_TPKN_TYPE = {
    "concept": "concept",
    "physical_picture": "concept",
    "definition_card": "definition",
    "notation_card": "notation",
    "equation_card": "equation",
    "assumption_card": "assumption",
    "regime_card": "regime",
    "theorem_card": "theorem",
    "claim_card": "claim",
    "proof_fragment": "proof_fragment",
    "derivation_step": "derivation_step",
    "derivation_object": "derivation",
    "method": "method",
    "workflow": "method",
    "topic_skill_projection": "topic_skill_projection",
    "bridge": "bridge",
    "example_card": "example",
    "caveat_card": "caveat",
    "equivalence_map": "equivalence",
    "symbol_binding": "symbol_binding",
    "validation_pattern": "method",
    "warning_note": "warning",
}

AITP_ID_PREFIX_TO_TPKN_TYPE = {
    "concept": "concept",
    "physical_picture": "concept",
    "definition_card": "definition",
    "notation_card": "notation",
    "equation_card": "equation",
    "assumption_card": "assumption",
    "regime_card": "regime",
    "theorem_card": "theorem",
    "claim_card": "claim",
    "proof_fragment": "proof_fragment",
    "derivation_step": "derivation_step",
    "derivation_object": "derivation",
    "method": "method",
    "workflow": "method",
    "topic_skill_projection": "topic_skill_projection",
    "bridge": "bridge",
    "example_card": "example",
    "caveat_card": "caveat",
    "equivalence_map": "equivalence",
    "symbol_binding": "symbol_binding",
    "validation_pattern": "method",
    "warning_note": "warning",
}

TPKN_UNIT_DIRS = {
    "concept": "units/concepts",
    "definition": "units/definitions",
    "notation": "units/notations",
    "assumption": "units/assumptions",
    "regime": "units/regimes",
    "theorem": "units/theorems",
    "claim": "units/claims",
    "proof_fragment": "units/proof-fragments",
    "derivation_step": "units/derivation-steps",
    "derivation": "units/derivations",
    "method": "units/methods",
    "topic_skill_projection": "units/topic-skill-projections",
    "bridge": "units/bridges",
    "example": "units/examples",
    "caveat": "units/caveats",
    "equivalence": "units/equivalences",
    "symbol_binding": "units/symbol-bindings",
    "equation": "units/equations",
    "quantity": "units/quantities",
    "model": "units/models",
    "source_map": "units/source-maps",
    "warning": "units/warnings",
    "lemma": "units/lemmas",
    "conjecture": "units/conjectures",
    "theorem_family": "units/theorem-families",
    "definition_family": "units/definition-families",
    "notation_family": "units/notation-families",
    "feasibility_question": "units/feasibility-questions",
    "dependency_request": "units/dependency-requests",
    "proof_search_request": "units/proof-search-requests",
    "equation_context": "units/equation-contexts",
    "proof_obligation": "units/proof-obligations",
    "proof_state": "units/proof-states",
    "dependency_graph_snapshot": "units/dependency-graph-snapshots",
    "notation_map": "units/notation-maps",
    "source_fusion_record": "units/source-fusion-records",
    "conflict_record": "units/conflict-records",
    "open_gap": "units/open-gaps",
    "question_oracle": "units/question-oracles",
    "regression_question": "units/regression-questions",
    "followup_source_task": "units/followup-source-tasks",
}

SOURCE_MANIFEST_REQUIRED_URL_KEYS = ("abs", "pdf", "doi")


def slugify(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-+", "-", lowered).strip("-")
    return lowered or "aitp"


def today_iso() -> str:
    return datetime.now().date().isoformat()


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
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_or_replace_jsonl(path: Path, row: dict[str, Any], *, key: str) -> None:
    rows = [existing for existing in read_jsonl(path) if existing.get(key) != row.get(key)]
    rows.append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n" for item in rows),
        encoding="utf-8",
    )


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _dedupe_strings(values: list[str] | None) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        stripped = str(value).strip()
        if stripped and stripped not in seen:
            seen.add(stripped)
            deduped.append(stripped)
    return deduped


def _dedupe_object_list(values: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for value in values or []:
        key = json.dumps(value, ensure_ascii=True, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(value)
    return deduped


def _normalize_metadata_entries(value: Any) -> list[str]:
    entries: list[str] = []
    if value is None:
        return entries
    if isinstance(value, dict):
        for key in sorted(value):
            item = value[key]
            if item is None:
                continue
            if isinstance(item, str):
                stripped = item.strip()
                if stripped:
                    entries.append(f"{key}={stripped}")
                continue
            entries.append(f"{key}={json.dumps(item, ensure_ascii=True, sort_keys=True)}")
        return _dedupe_strings(entries)
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                stripped = item.strip()
                if stripped:
                    entries.append(stripped)
                continue
            if isinstance(item, dict):
                entries.extend(_normalize_metadata_entries(item))
                continue
            stripped = str(item).strip()
            if stripped:
                entries.append(stripped)
        return _dedupe_strings(entries)
    stripped = str(value).strip()
    return [stripped] if stripped else []


def _extract_review_candidate_id(review_artifacts: list[str] | None) -> str:
    for entry in review_artifacts or []:
        if entry.startswith("candidate_id="):
            return entry.split("=", 1)[1].strip()
    return ""


def load_unit_index_rows(tpkn_root: Path) -> list[dict[str, Any]]:
    unit_index_path = tpkn_root / "indexes" / "unit_index.jsonl"
    if unit_index_path.exists():
        return read_jsonl(unit_index_path)

    rows: list[dict[str, Any]] = []
    for unit_type, relative_dir in TPKN_UNIT_DIRS.items():
        unit_dir = tpkn_root / relative_dir
        if not unit_dir.exists():
            continue
        for unit_path in sorted(unit_dir.glob("*.json")):
            payload = read_json(unit_path)
            if payload is None:
                continue
            rows.append(
                {
                    "id": payload["id"],
                    "type": payload["type"],
                    "title": payload["title"],
                    "summary": payload["summary"],
                    "path": str(unit_path.relative_to(tpkn_root)),
                    "domain": payload.get("domain"),
                    "subdomain": payload.get("subdomain"),
                    "tags": payload.get("tags") or [],
                    "aliases": payload.get("aliases") or [],
                    "dependencies": payload.get("dependencies") or [],
                    "related_units": payload.get("related_units") or [],
                    "formalization_status": payload.get("formalization_status"),
                    "validation_status": payload.get("validation_status"),
                    "maturity": payload.get("maturity"),
                    "source_anchor_count": len(payload.get("source_anchors") or []),
                }
            )
    return rows


def find_collision_rows(
    *,
    tpkn_root: Path,
    candidate_title: str,
    candidate_summary: str,
    candidate_tags: list[str],
    candidate_aliases: list[str],
    domain: str | None,
    target_type: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    title_norm = normalize_text(candidate_title)
    alias_norms = {normalize_text(value) for value in candidate_aliases if value.strip()}
    tag_set = {tag.strip().lower() for tag in candidate_tags if tag.strip()}

    scored: list[tuple[int, dict[str, Any]]] = []
    for row in load_unit_index_rows(tpkn_root):
        score = 0
        row_title = normalize_text(str(row.get("title") or ""))
        row_aliases = {normalize_text(value) for value in row.get("aliases") or [] if str(value).strip()}
        row_tags = {str(value).strip().lower() for value in row.get("tags") or [] if str(value).strip()}
        row_type = str(row.get("type") or "")
        row_domain = str(row.get("domain") or "")

        if row_type == target_type:
            score += 2
        if row_title == title_norm:
            score += 10
        if title_norm in row_aliases or row_title in alias_norms:
            score += 6
        if alias_norms & row_aliases:
            score += 4
        if tag_set and row_tags:
            score += min(3, len(tag_set & row_tags))
        if domain and row_domain and domain == row_domain:
            score += 1
        if candidate_summary and row.get("summary") and normalize_text(candidate_summary) == normalize_text(str(row["summary"])):
            score += 5
        if score <= 0:
            continue
        scored.append((score, row))

    scored.sort(
        key=lambda item: (
            -item[0],
            str(item[1].get("type") or ""),
            str(item[1].get("title") or ""),
        )
    )
    return [row for _, row in scored[:limit]]


def map_aitp_candidate_type(candidate_type: str) -> str:
    mapped = AITP_TO_TPKN_TYPE.get(candidate_type)
    if mapped is None:
        raise ValueError(f"Unsupported AITP candidate_type for TPKN promotion: {candidate_type}")
    return mapped


def _map_aitp_id_to_tpkn_id(identifier: str) -> str | None:
    if ":" not in identifier:
        return None
    prefix, slug = identifier.split(":", 1)
    mapped_prefix = AITP_ID_PREFIX_TO_TPKN_TYPE.get(prefix)
    if mapped_prefix is None:
        return None
    return f"{mapped_prefix}:{slug}"


def derive_tpkn_unit_id(candidate: dict[str, Any], target_type: str) -> str:
    for identifier in candidate.get("intended_l2_targets") or []:
        mapped = _map_aitp_id_to_tpkn_id(str(identifier))
        if mapped and mapped.startswith(f"{target_type}:"):
            return mapped
    slug = str(candidate.get("candidate_id") or "").split(":", 1)[-1]
    return f"{target_type}:{slugify(slug)}"


def choose_merge_target(
    *,
    collision_rows: list[dict[str, Any]],
    requested_unit_id: str,
    candidate_title: str,
    target_type: str,
) -> dict[str, Any] | None:
    for row in collision_rows:
        if str(row.get("id") or "") == requested_unit_id:
            return row

    title_norm = normalize_text(candidate_title)
    for row in collision_rows:
        if str(row.get("type") or "") != target_type:
            continue
        if normalize_text(str(row.get("title") or "")) == title_norm:
            return row
    return None


def choose_source_row(
    *,
    source_rows: list[dict[str, Any]],
    candidate: dict[str, Any],
) -> dict[str, Any] | None:
    origin_ids = {str(ref.get("id") or "").strip() for ref in candidate.get("origin_refs") or [] if str(ref.get("id") or "").strip()}
    for row in source_rows:
        source_id = str(row.get("source_id") or "").strip()
        if source_id and source_id in origin_ids:
            return row
    for row in source_rows:
        if str(row.get("source_type") or "").strip() == "paper":
            return row
    return source_rows[0] if source_rows else None


def _find_source_manifest_paths_by_id(tpkn_root: Path, source_id: str) -> list[Path]:
    sources_root = tpkn_root / "sources"
    if not sources_root.exists():
        return []
    matches: list[Path] = []
    for manifest_path in sorted(sources_root.glob("*/manifest.json")):
        payload = read_json(manifest_path)
        if payload is None:
            continue
        if str(payload.get("source_id") or "").strip() == source_id:
            matches.append(manifest_path)
    return matches


def ensure_source_manifest(
    *,
    tpkn_root: Path,
    source_row: dict[str, Any] | None,
    source_id: str,
    source_section: str,
    source_section_title: str,
    source_section_summary: str,
) -> tuple[Path, bool]:
    source_slug = source_id.split(":", 1)[-1]
    expected_manifest_path = tpkn_root / "sources" / source_slug / "manifest.json"
    matching_manifest_paths = _find_source_manifest_paths_by_id(tpkn_root, source_id)
    if len(matching_manifest_paths) > 1:
        relative_paths = ", ".join(str(path.relative_to(tpkn_root)) for path in matching_manifest_paths)
        raise RuntimeError(
            f"Multiple source manifests already declare source_id {source_id}; "
            f"clean up duplicates before promotion: {relative_paths}"
        )
    manifest_path = matching_manifest_paths[0] if matching_manifest_paths else expected_manifest_path
    existing = read_json(manifest_path)
    created = existing is None
    provenance = (source_row or {}).get("provenance") or {}
    acquired_at = str((source_row or {}).get("acquired_at") or today_iso())
    published = str(provenance.get("published") or "")[:10] or acquired_at[:10]
    updated = str(provenance.get("updated") or "")[:10] or published
    title = str((source_row or {}).get("title") or source_id)
    authors = [str(value) for value in provenance.get("authors") or [] if str(value).strip()]
    urls = {
        "abs": str(provenance.get("abs_url") or ""),
        "pdf": str(provenance.get("pdf_url") or ""),
        "doi": str(provenance.get("doi") or ""),
    }
    optional_urls = {
        "source_archive": str(provenance.get("source_url") or ""),
        "journal": str(provenance.get("journal_url") or ""),
    }

    if existing is None:
        manifest = {
            "source_id": source_id,
            "title": title,
            "authors": authors,
            "version": str(provenance.get("arxiv_id") or provenance.get("versioned_id") or "unknown"),
            "submitted_date": published,
            "updated_date": updated,
            "canonical_scope": f"AITP source-onboarding bridge for {source_id}.",
            "urls": urls,
            "section_map": [],
            "equation_map": [],
            "figure_map": [],
        }
        for key, value in optional_urls.items():
            if value:
                manifest["urls"][key] = value
    else:
        manifest = existing
        manifest.setdefault("section_map", [])
        manifest.setdefault("equation_map", [])
        manifest.setdefault("figure_map", [])

    section_ids = {str(entry.get("id") or "") for entry in manifest.get("section_map") or []}
    if source_section not in section_ids:
        manifest["section_map"].append(
            {
                "id": source_section,
                "title": source_section_title,
                "summary": source_section_summary,
            }
        )

    for key in SOURCE_MANIFEST_REQUIRED_URL_KEYS:
        manifest.setdefault("urls", {})
        manifest["urls"].setdefault(key, "")

    write_json(manifest_path, manifest)
    return manifest_path, created


def _title_from_identifier(identifier: str) -> str:
    slug = identifier.split(":", 1)[-1]
    words = [part for part in slug.replace("_", "-").split("-") if part]
    if not words:
        return identifier
    return " ".join(word.capitalize() for word in words)


def build_supporting_regression_question_unit(
    *,
    unit_id: str,
    domain: str,
    source_id: str,
    source_section: str,
    source_anchor_notes: str,
    promoted_unit_id: str,
    promoted_unit_title: str,
    topic_slug: str,
    oracle_id: str | None = None,
) -> dict[str, Any]:
    title = _title_from_identifier(unit_id)
    return {
        "id": unit_id,
        "type": "regression_question",
        "title": title,
        "summary": (
            f"AITP-generated supporting regression question for {promoted_unit_title}; "
            "used to keep the promoted topic-completion surface explicit."
        ),
        "domain": domain,
        "subdomain": "regression",
        "tags": _dedupe_strings(["regression-question", topic_slug, promoted_unit_id.split(":", 1)[0]]),
        "aliases": [],
        "assumptions": [
            "This supporting regression surface is auto-generated during AITP promotion.",
        ],
        "regime": f"Scoped regression surface for promoted unit {promoted_unit_id}.",
        "scope": f"Supporting regression question attached to {promoted_unit_id}.",
        "dependencies": [promoted_unit_id],
        "related_units": [oracle_id] if oracle_id else [],
        "source_anchors": [
            {
                "source_id": source_id,
                "section": source_section,
                "notes": source_anchor_notes,
            }
        ],
        "formalization_status": "candidate",
        "validation_status": "generated-support",
        "maturity": "seed",
        "representation": "AITP-generated supporting regression question.",
        "prompt": (
            f"State and explain {promoted_unit_title} while preserving the current bounded assumptions "
            "and proof-status boundary."
        ),
        "question_family": "bridge",
        "primary_retrieval_paths": [promoted_unit_id],
        "pass_conditions": [
            "The answer preserves the promoted theorem or concept boundary.",
            "The answer does not overclaim proof completion beyond the current bounded surface.",
        ],
        "retrieval_hints": [
            f"Use when checking whether {promoted_unit_id} remains stable under topic regression.",
        ],
        "created_at": today_iso(),
        "updated_at": today_iso(),
    }


def build_supporting_question_oracle_unit(
    *,
    unit_id: str,
    domain: str,
    source_id: str,
    source_section: str,
    source_anchor_notes: str,
    promoted_unit_id: str,
    promoted_unit_title: str,
    regression_question_id: str,
    topic_slug: str,
) -> dict[str, Any]:
    title = _title_from_identifier(unit_id)
    return {
        "id": unit_id,
        "type": "question_oracle",
        "title": title,
        "summary": (
            f"AITP-generated supporting oracle for {promoted_unit_title}; "
            "used to keep promotion-ready regression grading explicit."
        ),
        "domain": domain,
        "subdomain": "regression",
        "tags": _dedupe_strings(["question-oracle", topic_slug, promoted_unit_id.split(":", 1)[0]]),
        "aliases": [],
        "assumptions": [
            "This supporting oracle is auto-generated during AITP promotion.",
        ],
        "regime": f"Scoped regression oracle for promoted unit {promoted_unit_id}.",
        "scope": f"Supporting oracle attached to {promoted_unit_id}.",
        "dependencies": [regression_question_id],
        "related_units": [promoted_unit_id],
        "source_anchors": [
            {
                "source_id": source_id,
                "section": source_section,
                "notes": source_anchor_notes,
            }
        ],
        "formalization_status": "candidate",
        "validation_status": "generated-support",
        "maturity": "seed",
        "representation": "AITP-generated supporting regression oracle.",
        "prompt": f"Detailed oracle for {regression_question_id}.",
        "mandatory_unit_ids": [promoted_unit_id],
        "pass_conditions": [
            "The answer preserves the promoted unit boundary.",
            "The answer keeps the current proof-status caveat explicit.",
        ],
        "derivation_spine": [
            f"recover-statement:{promoted_unit_id}",
            "preserve-bounded-scope",
            "preserve-proof-status-boundary",
        ],
        "failure_triggers": [
            "Fail if the answer overclaims proof or formalization closure.",
            "Fail if the answer drops the promoted unit's central statement.",
        ],
        "grading_rubric": [
            "Pass when the promoted unit can be reconstructed faithfully at the current bounded scope.",
            "Fail when the answer invents extra claims or drops the core statement.",
        ],
        "common_failure_patterns": [
            "Overclaiming full formal proof closure.",
            "Answering only vaguely without restating the promoted unit.",
        ],
        "retrieval_hints": [
            f"Use when grading answers about {promoted_unit_id}.",
        ],
        "created_at": today_iso(),
        "updated_at": today_iso(),
    }


def build_tpkn_unit(
    *,
    candidate: dict[str, Any],
    unit_id: str,
    target_type: str,
    domain: str,
    subdomain: str,
    source_id: str,
    source_section: str,
    source_anchor_notes: str,
    existing_tpkn_ids: set[str],
    canonical_layer: str = "L2",
    review_mode: str = "human",
    promotion_route: str | None = None,
    review_artifacts: Any | None = None,
    coverage: dict[str, Any] | None = None,
    consensus: dict[str, Any] | None = None,
    regression_gate: dict[str, Any] | None = None,
    merge_lineage: Any | None = None,
    conflict_status: str = "none",
    conflict_refs: list[str] | None = None,
    equivalence_refs: list[str] | None = None,
) -> dict[str, Any]:
    assumptions = [str(value) for value in candidate.get("assumptions") or [] if str(value).strip()]
    if not assumptions:
        assumptions = ["Promoted from an AITP candidate; refine assumptions in later review."]
    supporting_regression_question_ids = _dedupe_strings(
        list((regression_gate or {}).get("supporting_regression_question_ids") or candidate.get("supporting_regression_question_ids") or [])
    )
    supporting_oracle_ids = _dedupe_strings(
        list((regression_gate or {}).get("supporting_oracle_ids") or candidate.get("supporting_oracle_ids") or [])
    )
    supporting_regression_run_ids = _dedupe_strings(
        list((regression_gate or {}).get("supporting_regression_run_ids") or candidate.get("supporting_regression_run_ids") or [])
    )
    promotion_blockers = _dedupe_strings(
        list((regression_gate or {}).get("promotion_blockers") or candidate.get("promotion_blockers") or [])
    )
    followup_gap_ids = _dedupe_strings(
        list((regression_gate or {}).get("followup_gap_ids") or candidate.get("followup_gap_ids") or [])
    )
    split_required = bool((regression_gate or {}).get("split_required", candidate.get("split_required", False)))
    cited_recovery_required = bool(
        (regression_gate or {}).get("cited_recovery_required", candidate.get("cited_recovery_required", False))
    )
    review_phrase = {
        "human": "after explicit human approval.",
        "ai_auto": "after passing the documented AI coverage and consensus gate.",
        "hybrid": "after hybrid human and AI review.",
    }.get(review_mode, "after explicit review.")

    dependencies: list[str] = []
    related_units: list[str] = []
    for identifier in candidate.get("intended_l2_targets") or []:
        mapped = _map_aitp_id_to_tpkn_id(str(identifier))
        if not mapped or mapped == unit_id or mapped not in existing_tpkn_ids:
            continue
        if mapped not in dependencies:
            dependencies.append(mapped)
    for ref in candidate.get("origin_refs") or []:
        mapped = _map_aitp_id_to_tpkn_id(str(ref.get("id") or ""))
        if not mapped or mapped == unit_id or mapped not in existing_tpkn_ids:
            continue
        if mapped not in related_units and mapped not in dependencies:
            related_units.append(mapped)

    unit = {
        "id": unit_id,
        "type": target_type,
        "title": str(candidate["title"]),
        "summary": str(candidate["summary"]),
        "domain": domain,
        "subdomain": subdomain,
        "tags": sorted(
            {
                str(candidate.get("candidate_type") or "").strip(),
                str(candidate.get("topic_slug") or "").strip(),
                target_type,
            }
            - {""}
        ),
        "aliases": [],
        "assumptions": assumptions,
        "regime": (
            f"Promoted from AITP topic {candidate['topic_slug']} via candidate {candidate['candidate_id']} "
            + review_phrase
        ),
        "scope": str(candidate.get("question") or candidate["summary"]),
        "dependencies": dependencies,
        "related_units": related_units,
        "source_anchors": [
            {
                "source_id": source_id,
                "section": source_section,
                "notes": source_anchor_notes,
            }
        ],
        "formalization_status": "candidate",
        "validation_status": "validated",
        "maturity": "seed",
        "topic_completion_status": str(
            (regression_gate or {}).get("topic_completion_status")
            or candidate.get("topic_completion_status")
            or "not_assessed"
        ),
        "supporting_regression_question_ids": supporting_regression_question_ids,
        "supporting_oracle_ids": supporting_oracle_ids,
        "supporting_regression_run_ids": supporting_regression_run_ids,
        "promotion_blockers": promotion_blockers,
        "split_required": split_required,
        "cited_recovery_required": cited_recovery_required,
        "followup_gap_ids": followup_gap_ids,
        "canonical_layer": canonical_layer,
        "review_mode": review_mode,
        "promotion_route": promotion_route or "",
        "conflict_status": conflict_status,
        "conflict_refs": _dedupe_strings(conflict_refs),
        "equivalence_refs": _dedupe_strings(equivalence_refs),
        "failure_modes": [
            "Review the regime and assumptions before treating this promoted unit as stable."
        ],
        "formal_targets": ["aitp-l2-auto" if canonical_layer == "L2_auto" else "aitp-l2"],
        "retrieval_hints": [
            f"Promoted from AITP candidate {candidate['candidate_id']}.",
        ],
        "trust_boundary": (
            "This is a semi-formal AITP Layer 2 unit: source-grounded and auditable, "
            "but not itself a proof-assistant-certified artifact."
        ),
        "translation_readiness": (
            "candidate"
            if target_type in {
                "concept",
                "definition",
                "notation",
                "equation",
                "assumption",
                "regime",
                "theorem",
                "claim",
                "proof_fragment",
                "derivation_step",
                "derivation",
                "bridge",
                "example",
                "caveat",
                "equivalence",
                "symbol_binding",
                "quantity",
                "model",
                "source_map",
            }
            else "future"
        ),
        "semi_formal_contract": [
            "Keep the statement, assumptions, and regime explicit.",
            "Keep source anchors and review artifacts explicit.",
            "Do not treat Layer 2 promotion as proof-assistant closure.",
            "Use later Lean export only after the bounded family is stable enough to translate cleanly.",
        ],
        "created_at": today_iso(),
        "updated_at": today_iso(),
        "promotion": {
            "route": promotion_route or (canonical_layer == "L2_auto" and "L3->L4_auto->L2_auto" or "L3->L4->L2"),
            "review_mode": review_mode,
            "canonical_layer": canonical_layer,
            "coverage_status": str((coverage or {}).get("status") or "not_audited"),
            "consensus_status": str((consensus or {}).get("status") or "not_requested"),
            "regression_gate_status": str((regression_gate or {}).get("status") or "not_audited"),
            "supporting_regression_question_ids": supporting_regression_question_ids,
            "supporting_oracle_ids": supporting_oracle_ids,
            "supporting_regression_run_ids": supporting_regression_run_ids,
            "promotion_blockers": promotion_blockers,
            "blocking_reasons": _dedupe_strings(list((regression_gate or {}).get("blocking_reasons") or [])),
            "cited_recovery_required": cited_recovery_required,
            "followup_gap_ids": followup_gap_ids,
            "split_clearance_status": str((regression_gate or {}).get("split_clearance_status") or "not_applicable"),
            "promotion_blockers_cleared": bool((regression_gate or {}).get("promotion_blockers_cleared", True)),
            "promoted_by": "",
            "promoted_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "review_status": "accepted",
            "rationale": (
                "Promoted after AI auto-review gates passed."
                if review_mode == "ai_auto"
                else "Promoted after explicit promotion review."
            ),
        },
    }
    normalized_review_artifacts = _normalize_metadata_entries(review_artifacts)
    if normalized_review_artifacts:
        unit["review_artifacts"] = normalized_review_artifacts
    if coverage:
        unit["coverage"] = coverage
    if consensus:
        unit["consensus"] = consensus
    if regression_gate:
        unit["regression_gate"] = regression_gate
    normalized_merge_lineage = _normalize_metadata_entries(merge_lineage)
    if normalized_merge_lineage:
        unit["merge_lineage"] = normalized_merge_lineage
    return unit


def merge_tpkn_unit(
    *,
    existing_unit: dict[str, Any],
    incoming_unit: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(existing_unit)
    merged["tags"] = sorted(set(existing_unit.get("tags") or []) | set(incoming_unit.get("tags") or []))
    aliases = list(existing_unit.get("aliases") or [])
    incoming_title = str(incoming_unit.get("title") or "").strip()
    if incoming_title and normalize_text(incoming_title) != normalize_text(str(existing_unit.get("title") or "")):
        aliases.append(incoming_title)
    aliases.extend(incoming_unit.get("aliases") or [])
    merged["aliases"] = _dedupe_strings(aliases)
    merged["assumptions"] = _dedupe_strings(list(existing_unit.get("assumptions") or []) + list(incoming_unit.get("assumptions") or []))
    merged["dependencies"] = _dedupe_strings(list(existing_unit.get("dependencies") or []) + list(incoming_unit.get("dependencies") or []))
    merged["related_units"] = _dedupe_strings(list(existing_unit.get("related_units") or []) + list(incoming_unit.get("related_units") or []))
    merged["source_anchors"] = _dedupe_object_list(list(existing_unit.get("source_anchors") or []) + list(incoming_unit.get("source_anchors") or []))
    merged["failure_modes"] = _dedupe_strings(list(existing_unit.get("failure_modes") or []) + list(incoming_unit.get("failure_modes") or []))
    merged["formal_targets"] = _dedupe_strings(list(existing_unit.get("formal_targets") or []) + list(incoming_unit.get("formal_targets") or []))
    merged["retrieval_hints"] = _dedupe_strings(list(existing_unit.get("retrieval_hints") or []) + list(incoming_unit.get("retrieval_hints") or []))
    merged["equivalence_refs"] = _dedupe_strings(list(existing_unit.get("equivalence_refs") or []) + list(incoming_unit.get("equivalence_refs") or []))
    merged["conflict_refs"] = _dedupe_strings(list(existing_unit.get("conflict_refs") or []) + list(incoming_unit.get("conflict_refs") or []))
    merged["semi_formal_contract"] = _dedupe_strings(
        list(existing_unit.get("semi_formal_contract") or []) + list(incoming_unit.get("semi_formal_contract") or [])
    )
    merged["updated_at"] = today_iso()

    existing_layer = str(existing_unit.get("canonical_layer") or "")
    incoming_layer = str(incoming_unit.get("canonical_layer") or "")
    merged["canonical_layer"] = "L2" if "L2" in {existing_layer, incoming_layer} else incoming_layer or existing_layer
    merged["review_mode"] = str(existing_unit.get("review_mode") or incoming_unit.get("review_mode") or "human")
    merged["promotion_route"] = str(existing_unit.get("promotion_route") or incoming_unit.get("promotion_route") or "")
    merged["conflict_status"] = str(incoming_unit.get("conflict_status") or existing_unit.get("conflict_status") or "none")
    merged["trust_boundary"] = str(
        incoming_unit.get("trust_boundary")
        or existing_unit.get("trust_boundary")
        or "This is a semi-formal AITP Layer 2 unit."
    )
    merged["translation_readiness"] = str(
        incoming_unit.get("translation_readiness")
        or existing_unit.get("translation_readiness")
        or "future"
    )

    review_artifacts = _dedupe_strings(
        _normalize_metadata_entries(existing_unit.get("review_artifacts"))
        + _normalize_metadata_entries(incoming_unit.get("review_artifacts"))
    )
    if review_artifacts:
        merged["review_artifacts"] = review_artifacts

    coverage = incoming_unit.get("coverage") or existing_unit.get("coverage")
    if coverage:
        merged["coverage"] = coverage
    consensus = incoming_unit.get("consensus") or existing_unit.get("consensus")
    if consensus:
        merged["consensus"] = consensus
    regression_gate = incoming_unit.get("regression_gate") or existing_unit.get("regression_gate")
    if regression_gate:
        merged["regression_gate"] = regression_gate
    merged["supporting_regression_question_ids"] = _dedupe_strings(
        list(existing_unit.get("supporting_regression_question_ids") or [])
        + list(incoming_unit.get("supporting_regression_question_ids") or [])
    )
    merged["supporting_oracle_ids"] = _dedupe_strings(
        list(existing_unit.get("supporting_oracle_ids") or [])
        + list(incoming_unit.get("supporting_oracle_ids") or [])
    )
    merged["supporting_regression_run_ids"] = _dedupe_strings(
        list(existing_unit.get("supporting_regression_run_ids") or [])
        + list(incoming_unit.get("supporting_regression_run_ids") or [])
    )
    merged["promotion_blockers"] = _dedupe_strings(
        list(existing_unit.get("promotion_blockers") or [])
        + list(incoming_unit.get("promotion_blockers") or [])
    )
    merged["followup_gap_ids"] = _dedupe_strings(
        list(existing_unit.get("followup_gap_ids") or [])
        + list(incoming_unit.get("followup_gap_ids") or [])
    )
    merged["split_required"] = bool(incoming_unit.get("split_required", existing_unit.get("split_required", False)))
    merged["cited_recovery_required"] = bool(
        incoming_unit.get("cited_recovery_required", existing_unit.get("cited_recovery_required", False))
    )
    merged["topic_completion_status"] = str(
        incoming_unit.get("topic_completion_status")
        or existing_unit.get("topic_completion_status")
        or "not_assessed"
    )
    promotion = dict(existing_unit.get("promotion") or {})
    promotion.update(incoming_unit.get("promotion") or {})
    if promotion:
        merged["promotion"] = promotion

    lineage = _dedupe_strings(
        _normalize_metadata_entries(existing_unit.get("merge_lineage"))
        + _normalize_metadata_entries(incoming_unit.get("merge_lineage"))
    )
    incoming_candidate_id = _extract_review_candidate_id(
        _normalize_metadata_entries(incoming_unit.get("review_artifacts"))
    )
    if incoming_candidate_id:
        lineage.append(f"merged_candidate_id={incoming_candidate_id}")
    lineage.append(f"last_merge_at={today_iso()}")
    lineage = _dedupe_strings(lineage)
    if lineage:
        merged["merge_lineage"] = lineage

    return merged


def unit_path_for(tpkn_root: Path, unit_type: str, unit_id: str) -> Path:
    relative_dir = TPKN_UNIT_DIRS.get(unit_type)
    if relative_dir is None:
        raise ValueError(f"Unsupported TPKN unit type: {unit_type}")
    slug = unit_id.split(":", 1)[-1]
    return tpkn_root / relative_dir / f"{slug}.json"


def run_tpkn_checks(tpkn_root: Path, *, scoped_paths: list[Path] | None = None) -> dict[str, Any]:
    python_command = [sys.executable] if sys.executable else [shutil.which("python") or shutil.which("python3") or "python3"]
    normalized_scope: list[str] = []
    for path in scoped_paths or []:
        try:
            relative = path.resolve().relative_to(tpkn_root.resolve())
        except ValueError:
            continue
        normalized_scope.append(str(relative))
    if (tpkn_root / "scripts" / "check_protocol.py").exists() and (tpkn_root / "scripts" / "build.py").exists():
        check_command = [*python_command, "scripts/check_protocol.py"]
        build_command = [*python_command, "scripts/build.py"]
        if normalized_scope:
            check_command.extend(["--allow-unrelated-errors"])
            build_command.extend(["--allow-unrelated-errors"])
            for path in normalized_scope:
                check_command.extend(["--scope", path])
                build_command.extend(["--scope", path])
    else:
        check_command = [*python_command, "scripts/kb.py", "check"]
        build_command = [*python_command, "scripts/kb.py", "build"]
    commands = {
        "check": check_command,
        "build": build_command,
    }
    results: dict[str, Any] = {}
    for key, command in commands.items():
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            cwd=tpkn_root,
            stdin=subprocess.DEVNULL,
        )
        if completed.returncode != 0:
            message = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
            raise RuntimeError(f"TPKN {key} failed: {message}")
        results[key] = {
            "command": command,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
            "scoped_paths": normalized_scope,
        }
    return results
