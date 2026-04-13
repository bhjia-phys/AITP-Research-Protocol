from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


RUNTIME_SCHEMA_FILES = {
    "lean-ready-packet": "lean-ready-packet.schema.json",
    "proof-repair-plan": "proof-repair-plan.schema.json",
    "statement-compilation-packet": "statement-compilation-packet.schema.json",
}


def _schema_root(schema_root: Path | None = None) -> Path:
    return schema_root or Path(__file__).resolve().parents[1] / "schemas"


def load_runtime_schema_registry(schema_root: Path | None = None) -> dict[str, Path]:
    """Return the package-local runtime proof schema paths keyed by artifact type."""
    root = _schema_root(schema_root)
    return {
        artifact_type: root / file_name
        for artifact_type, file_name in RUNTIME_SCHEMA_FILES.items()
    }


def validate_runtime_artifact(
    artifact_type: str,
    artifact: dict[str, Any],
    *,
    schema_root: Path | None = None,
) -> tuple[bool, str]:
    """Validate one runtime proof artifact against its package-local schema."""
    registry = load_runtime_schema_registry(schema_root)
    schema_path = registry.get(artifact_type)
    if schema_path is None:
        raise ValueError(f"Unknown runtime artifact type: {artifact_type}")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    try:
        Draft202012Validator(schema).validate(artifact)
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
    return True, ""


def _statement_unit_type(primary_kind: str) -> str:
    lowered = str(primary_kind or "").strip().lower()
    if lowered == "definition":
        return "definition_card"
    if lowered in {"theorem", "lemma", "conjecture"}:
        return "theorem_card"
    return "claim_card"


def translate_to_canonical_surface(artifact_type: str, artifact: dict[str, Any]) -> dict[str, Any]:
    """Project a runtime proof artifact onto the canonical L2 surface."""
    if artifact_type == "lean-ready-packet":
        declaration_name = str(artifact.get("declaration_name") or artifact.get("candidate_id") or "lean-ready-packet")
        return {
            "unit_type": "proof_fragment",
            "title": f"Lean-ready fragment: {declaration_name}",
            "summary": str(artifact.get("statement_text") or "Lean-ready proof fragment prepared for bounded promotion."),
            "payload": {
                "declaration_kind": str(artifact.get("declaration_kind") or ""),
                "namespace": str(artifact.get("namespace") or ""),
                "proof_obligation_count": int(artifact.get("proof_obligation_count") or 0),
                "statement_compilation_path": str(artifact.get("statement_compilation_path") or ""),
                "proof_repair_plan_path": str(artifact.get("proof_repair_plan_path") or ""),
            },
        }
    if artifact_type == "proof-repair-plan":
        proof_holes = list(artifact.get("proof_holes") or [])
        return {
            "unit_type": "negative_result",
            "title": f"Proof repair debt: {artifact.get('candidate_id') or 'candidate'}",
            "summary": (
                f"{len(proof_holes)} bounded proof hole(s) remain before proof-grade promotion can continue."
                if proof_holes
                else "Proof repair planning remains attached even though no explicit proof holes are currently open."
            ),
            "payload": {
                "status": str(artifact.get("status") or ""),
                "proof_hole_count": len(proof_holes),
                "compilation_path": str(artifact.get("compilation_path") or ""),
            },
        }
    if artifact_type == "statement-compilation-packet":
        primary_kind = str(artifact.get("primary_statement_kind") or "")
        return {
            "unit_type": _statement_unit_type(primary_kind),
            "title": str(artifact.get("title") or artifact.get("primary_identifier") or "Statement compilation packet"),
            "summary": (
                f"Bounded {primary_kind or 'statement'} compilation packet with "
                f"{int(artifact.get('declaration_count') or 0)} declaration(s) and "
                f"{int(artifact.get('proof_hole_count') or 0)} proof hole(s)."
            ),
            "payload": {
                "primary_statement_kind": primary_kind,
                "primary_identifier": str(artifact.get("primary_identifier") or ""),
                "declaration_count": int(artifact.get("declaration_count") or 0),
                "proof_hole_count": int(artifact.get("proof_hole_count") or 0),
            },
        }
    raise ValueError(f"Unknown runtime artifact type: {artifact_type}")


def load_runtime_schema_context(
    artifact_paths: dict[str, Path | str],
    *,
    schema_root: Path | None = None,
) -> dict[str, Any]:
    """Load, validate, and translate the runtime proof artifacts that currently exist."""
    registry = load_runtime_schema_registry(schema_root)
    artifacts: list[dict[str, Any]] = []
    for artifact_type, raw_path in artifact_paths.items():
        path = Path(raw_path)
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        is_valid, validation_error = validate_runtime_artifact(
            artifact_type,
            payload,
            schema_root=schema_root,
        )
        artifacts.append(
            {
                "artifact_type": artifact_type,
                "artifact_path": str(path),
                "schema_path": str(registry[artifact_type]),
                "is_valid": is_valid,
                "validation_error": validation_error,
                "translated_unit": translate_to_canonical_surface(artifact_type, payload) if is_valid else {},
            }
        )
    return {
        "all_valid": all(bool(row.get("is_valid")) for row in artifacts) if artifacts else True,
        "artifact_types": [str(row["artifact_type"]) for row in artifacts],
        "schema_paths": {str(row["artifact_type"]): str(row["schema_path"]) for row in artifacts},
        "artifact_paths": {str(row["artifact_type"]): str(row["artifact_path"]) for row in artifacts},
        "artifacts": artifacts,
    }


def collect_runtime_schema_context(
    service: Any,
    *,
    topic_slug: str,
    run_id: str,
    candidate_id: str,
) -> dict[str, Any]:
    """Collect runtime proof packet context for one candidate using service path helpers."""
    artifact_paths = {
        "statement-compilation-packet": service._statement_compilation_packet_paths(topic_slug, run_id, candidate_id)["json"],
        "proof-repair-plan": service._statement_compilation_packet_paths(topic_slug, run_id, candidate_id)["repair_plan"],
        "lean-ready-packet": service._lean_bridge_packet_paths(topic_slug, run_id, candidate_id)["json"],
    }
    context = load_runtime_schema_context(artifact_paths)
    context["schema_paths"] = {
        artifact_type: service._relativize(Path(path))
        for artifact_type, path in context.get("schema_paths", {}).items()
    }
    context["artifact_paths"] = {
        artifact_type: service._relativize(Path(path))
        for artifact_type, path in context.get("artifact_paths", {}).items()
    }
    for row in context.get("artifacts", []):
        row["schema_path"] = service._relativize(Path(str(row.get("schema_path") or "")))
        row["artifact_path"] = service._relativize(Path(str(row.get("artifact_path") or "")))
    return context
