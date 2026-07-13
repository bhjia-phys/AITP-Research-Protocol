# Compatibility shard 2 for research_distillation.
from __future__ import annotations

def _summary(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    state_counts: dict[str, int] = {}
    kind_counts: dict[str, int] = {}
    draftable = 0
    for candidate in candidates:
        state = str(candidate.get("distillation_state") or "")
        kind = str(candidate.get("candidate_kind") or "")
        state_counts[state] = state_counts.get(state, 0) + 1
        kind_counts[kind] = kind_counts.get(kind, 0) + 1
        if candidate.get("can_draft_reusable_block"):
            draftable += 1
    return {
        "candidate_count": len(candidates),
        "draftable_count": draftable,
        "needs_more_records_count": state_counts.get("needs_more_records", 0),
        "state_counts": state_counts,
        "kind_counts": kind_counts,
    }

def _read_iteration_items(ws: WorkspacePaths, topic_id: str) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    run_root = ws.topic_dir(topic_id) / "L3" / "runs"
    if not run_root.exists():
        return [], []
    items: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for path in sorted(run_root.glob("*/iteration_journal.json")):
        try:
            journal = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append({"path": str(path), "error_type": type(exc).__name__, "message": _excerpt(str(exc), limit=240)})
            continue
        for item in journal.get("iterations", []):
            if not isinstance(item, dict):
                continue
            item = dict(item)
            item.setdefault("run_id", str(journal.get("run_id") or path.parent.name))
            item.setdefault("topic_id", str(journal.get("topic_id") or topic_id))
            items.append(item)
    return items, errors

def _claim_boundary(claim: dict[str, Any], relation_map: dict[str, Any]) -> list[str]:
    conclusion = relation_map.get("current_conclusion") if isinstance(relation_map.get("current_conclusion"), dict) else {}
    return _dedupe(
        _as_list(claim.get("non_claims"))
        + [str(claim.get("strongest_failure_mode") or "")]
        + list(conclusion.get("cannot_say") or [])[:4]
    )

def _relation_boundaries(relation_map: dict[str, Any]) -> list[str]:
    conclusion = relation_map.get("current_conclusion") if isinstance(relation_map.get("current_conclusion"), dict) else {}
    return _dedupe(list(relation_map.get("current_blockers") or [])[:4] + list(conclusion.get("cannot_say") or [])[:4])

def _validation_refs(relation_map: dict[str, Any]) -> list[str]:
    source_records = relation_map.get("source_records") if isinstance(relation_map.get("source_records"), dict) else {}
    refs = []
    for key in ("validation_results", "validation_contracts"):
        refs.extend(str(value) for value in source_records.get(key, []) if value)
    return _dedupe(refs)

def _candidate_text(item: dict[str, Any], claim: dict[str, Any]) -> str:
    groups = [
        [item.get("plan_summary"), item.get("l3_synthesis_summary"), item.get("l4_return_summary"), item.get("decision")],
        item.get("checks") or [],
        item.get("deliverables") or [],
        item.get("stop_rules") or [],
        [claim.get("statement"), claim.get("scope"), claim.get("strongest_failure_mode")],
    ]
    return " ".join(str(value or "") for group in groups for value in group).lower()

def _infer_candidate_kind(text: str) -> str:
    workflow = _contains_any(text, ("workflow", "script", "pipeline", "sbatch", "plot", "parse", "compiled", "job", "run", "recipe", "audit", "reproduce", "refresh"))
    physics = _contains_any(text, ("proof", "theorem", "lemma", "derive", "formula", "operator", "schur", "yangian", "symmetry", "kernel", "rank", "green", "self-energy", "pade", "qsgw", "rational"))
    failure = _contains_any(text, ("failure", "failed", "bias", "warning", "contradict", "deprecated", "blocked", "does not prove", "do not", "not prove"))
    if failure and not workflow and not physics:
        return "failure_playbook_candidate"
    if workflow and physics:
        return "method_capsule_candidate"
    if physics:
        return "physics_semantic_fragment_candidate"
    if workflow:
        return "workflow_recipe_candidate"
    return "workflow_recipe_candidate"

def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)

def _typed_refs(item: dict[str, Any], *, prefixes: tuple[str, ...]) -> list[str]:
    refs: list[str] = []
    groups = [
        item.get("source_refs") or [],
        item.get("l4_artifact_refs") or [],
        (item.get("source_records") or {}).get("source_refs") or [],
    ]
    for value in [ref for group in groups for ref in group]:
        text = str(value or "")
        if any(text.startswith(prefix) for prefix in prefixes):
            refs.append(text.removeprefix("evidence:"))
    return _dedupe(refs)

def _title_from_iteration(item: dict[str, Any]) -> str:
    iteration_id = str(item.get("iteration_id") or "iteration")
    summary = str(item.get("plan_summary") or item.get("l3_synthesis_summary") or "")
    return f"{iteration_id}: {_excerpt(summary, limit=96)}" if summary else iteration_id

def _candidate_source_records(candidates: list[dict[str, Any]]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"claims": [], "run_iterations": [], "artifacts": [], "source_refs": []}
    for candidate in candidates:
        source_records = candidate.get("source_records") if isinstance(candidate.get("source_records"), dict) else {}
        for key in out:
            out[key].extend(str(value) for value in source_records.get(key, []) if value)
    return {key: _dedupe(values) for key, values in out.items()}

def _candidate_id(prefix: str, *parts: Any) -> str:
    raw = "-".join(str(part or "") for part in parts if str(part or ""))
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", raw).strip(".-").lower()
    slug = slug[:120] or "candidate"
    return f"{prefix}-{slug}"

def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if isinstance(value, str) and value.strip():
        return [value]
    return []

def _dedupe(values: list[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in out:
            out.append(text)
    return out

def _excerpt(value: Any, *, limit: int = 180) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."

def list_topic_claim_records(ws: WorkspacePaths, topic_id: str) -> list[ClaimRecord]:
    """Expose a small helper for tests and downstream read-only integrations."""

    return [claim for claim in list_records(ws.registry_dir("claims"), ClaimRecord) if claim.topic_id == topic_id]
