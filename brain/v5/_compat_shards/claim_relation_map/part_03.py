# Compatibility shard 3 for claim_relation_map.
from __future__ import annotations

def _topic_claim_boundaries(records: list[ClaimRecord], *, active_claim_id: str) -> dict[str, Any]:
    siblings = [
        {
            "claim_id": record.claim_id,
            "confidence_state": record.confidence_state,
            "evidence_profile": record.evidence_profile,
            "statement_excerpt": _excerpt(record.statement, limit=180),
        }
        for record in sorted(records, key=lambda item: item.claim_id)
        if record.claim_id != active_claim_id
    ]
    has_siblings = bool(siblings)
    return {
        "kind": "topic_claim_boundaries",
        "active_claim_id": active_claim_id,
        "sibling_claim_count": len(siblings),
        "sibling_claims": siblings,
        "boundary_rule": (
            "Sibling claims are same-topic research lines for orientation only; their records cannot support, "
            "limit, or refute the active claim unless explicitly linked to this active claim."
        ),
        "current_conclusion": {
            "can_say": (
                ["same-topic sibling claims exist and may explain topic history"]
                if has_siblings
                else ["no same-topic sibling claims were found"]
            ),
            "cannot_say": (
                ["cannot use sibling-claim evidence or legacy reviews as active-claim support without an explicit claim link"]
                if has_siblings
                else []
            ),
        },
        "orientation_only": True,
        "can_update_claim_trust": False,
    }

def _empty_topic_claim_boundaries() -> dict[str, Any]:
    return _topic_claim_boundaries([], active_claim_id="")

def _topic_claim_boundaries_markdown(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        return "- None\n"
    siblings = payload.get("sibling_claims") or []
    lines = [
        f"- Active claim: `{payload.get('active_claim_id', '')}`\n",
        f"- Sibling claim count: `{payload.get('sibling_claim_count', 0)}`\n",
        f"- Boundary rule: {payload.get('boundary_rule', '')}\n",
    ]
    for item in siblings[:8]:
        lines.append(
            f"- Sibling `{item.get('claim_id', '')}` "
            f"({item.get('confidence_state', '')}, {item.get('evidence_profile', '')}): "
            f"{item.get('statement_excerpt', '')}\n"
        )
    return "".join(lines)

def _legacy_semantic_review_context_ref(context: dict[str, Any]) -> str:
    run_id = str(context.get("migration_run_id") or "")
    topic = str(context.get("topic_id") or "")
    if run_id and topic:
        return f"legacy-migration-coverage:{run_id}:{topic}"
    return f"legacy-semantic-review:{topic or 'pending'}"

def _legacy_semantic_review_source_refs(context: dict[str, Any]) -> list[str]:
    if context.get("review_id"):
        return [f"legacy_semantic_review:{context.get('review_id')}"]
    ref = _legacy_semantic_review_context_ref(context)
    return [ref] if ref else []

def _key_object_relation_summaries(object_relations: list[dict[str, Any]]) -> list[str]:
    summaries: list[str] = []
    for relation in object_relations:
        relation_type = str(relation.get("relation_type") or "").strip()
        statement = str(relation.get("statement") or "").strip()
        subject_id = str(relation.get("subject_id") or "").strip()
        object_id = str(relation.get("object_id") or "").strip()
        status = str(relation.get("status") or "").strip()
        failure_modes = [
            str(item).strip()
            for item in relation.get("failure_modes", [])
            if str(item).strip()
        ]
        if statement:
            summary = f"{relation_type}: {statement}" if relation_type else statement
        else:
            summary = f"{subject_id} --{relation_type or 'relates_to'}-> {object_id}"
        if status:
            summary = f"{summary} (status={status})"
        if failure_modes:
            summary = f"{summary}; failure modes: {', '.join(failure_modes[:3])}"
        summaries.append(summary)
    return _dedupe_clean(summaries)

def _bucket_for_status(status: str, *, text: str) -> str:
    normalized = status.strip().lower().replace(" ", "_")
    lower = text.lower()
    if normalized in _SUPPORT_STATUSES:
        return "supported_by"
    if normalized in _LIMIT_STATUSES:
        return "limited_by"
    if _is_pre_domain_failure_text(lower) and (
        normalized in _RUNTIME_FAILURE_STATUSES or _has_explicit_pre_domain_failure_context(lower)
    ):
        return "not_tested_by"
    if normalized in _CONTRADICT_STATUSES:
        return "contradicted_by"
    return "limited_by"

def _is_pre_domain_failure_text(lower_text: str) -> bool:
    if not any(marker in lower_text for marker in _PRE_DOMAIN_FAILURE_MARKERS):
        return False
    return _has_explicit_pre_domain_failure_context(lower_text)

def _has_explicit_pre_domain_failure_context(lower_text: str) -> bool:
    return any(marker in lower_text for marker in _EXPLICIT_PRE_DOMAIN_FAILURE_CONTEXT_MARKERS)

def _evidence_entry(record) -> dict[str, Any]:
    text = _evidence_text(record)
    return {
        "record_kind": "evidence",
        "record_id": record.evidence_id,
        "relation_to_claim": _relation_label(record.status, text=text),
        "status": record.status,
        "summary": record.summary,
        "reason": _relation_reason(record.status, text=text),
        "source_refs": list(record.source_refs),
        "evidence_refs": [record.evidence_id],
        "tool_run_ids": list(record.tool_run_ids),
        "artifact_ids": list(record.artifact_ids),
    }

def _tool_run_entry(record: ToolRunRecord) -> dict[str, Any]:
    text = _tool_run_text(record)
    return {
        "record_kind": "tool_run",
        "record_id": record.run_id,
        "relation_to_claim": _relation_label(record.evidence_status, text=text),
        "status": record.evidence_status,
        "summary": _excerpt(text, limit=360),
        "reason": _relation_reason(record.evidence_status, text=text),
        "source_refs": list(record.source_refs),
        "evidence_refs": [],
        "tool_run_ids": [record.run_id],
        "artifact_ids": list(record.artifact_ids),
    }

def _claim_status_gap_entry(record: ClaimStatusRecord, gap: str) -> dict[str, Any]:
    return {
        "record_kind": "claim_status",
        "record_id": record.status_id,
        "relation_to_claim": "limits_claim_scope",
        "status": record.claim_status,
        "summary": gap,
        "reason": f"recorded open gap under scope: {record.scope}",
        "source_refs": list(record.source_refs),
        "evidence_refs": list(record.evidence_refs),
        "tool_run_ids": [],
        "artifact_ids": list(record.artifact_ids),
    }

def _proof_obligation_entry(record: ProofObligationRecord) -> dict[str, Any]:
    return {
        "record_kind": "proof_obligation",
        "record_id": record.obligation_id,
        "relation_to_claim": "open_proof_or_validation_gap",
        "status": record.status,
        "summary": record.statement,
        "reason": record.next_action,
        "source_refs": list(record.source_refs),
        "evidence_refs": list(record.evidence_refs),
        "tool_run_ids": [],
        "artifact_ids": list(record.artifact_ids),
    }

def _relation_label(status: str, *, text: str) -> str:
    bucket = _bucket_for_status(status, text=text)
    if bucket == "not_tested_by":
        return "does_not_test_core_claim"
    if bucket == "supported_by":
        return "supports_claim_within_scope"
    if bucket == "contradicted_by":
        return "challenges_or_refutes_claim"
    return "limits_or_does_not_close_claim"

def _relation_reason(status: str, *, text: str) -> str:
    if _bucket_for_status(status, text=text) == "not_tested_by":
        return "classified as application/runtime/pre-domain failure, so it cannot support or refute the core claim"
    if status.strip().lower() in _SUPPORT_STATUSES:
        return "record status is supporting"
    if status.strip().lower() in _CONTRADICT_STATUSES:
        return "record status is challenging and no pre-domain failure marker was found"
    return "record is mixed, inconclusive, diagnostic, or scope-limiting"

def _evidence_text(record) -> str:
    return " ".join(
        [
            str(record.evidence_type),
            str(record.status),
            str(record.summary),
            " ".join(record.supports_outputs),
            " ".join(record.source_refs),
            " ".join(record.tool_run_ids),
            " ".join(record.artifact_ids),
        ]
    )

def _tool_run_text(record: ToolRunRecord) -> str:
    return " ".join(
        [
            str(record.tool_family),
            str(record.tool_name),
            str(record.evidence_status),
            _json_text(record.inputs),
            _json_text(record.outputs),
            _json_text(record.environment),
            " ".join(record.source_refs),
        ]
    )

def _json_text(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=True, sort_keys=True)
    except TypeError:
        return str(value)

def _blocker_hints(text: str) -> list[str]:
    lower = text.lower()
    hints: list[str] = []
    if "scalapack" in lower:
        hints.append("ScaLAPACK/runtime dependency failure")
    if "executable" in lower or "path error" in lower or "path not found" in lower:
        hints.append("executable path or executable selection blocker")
    if "slurm" in lower:
        hints.append("Slurm/runtime job failure")
    if "before analytic continuation" in lower or "pre_ac" in lower or "pre-ac" in lower or "before ac" in lower:
        hints.append("failure occurred before analytic continuation")
    if "modulenotfounderror" in lower or "no module named" in lower or "importerror" in lower or "import error" in lower:
        hints.append("missing Python module / import error (setup failure)")
    if "no such file" in lower or "file not found" in lower or "missing file" in lower:
        hints.append("missing input/output file (setup/path failure)")
    if "out of memory" in lower or "oom" in lower or "exceeded memory" in lower:
        hints.append("out-of-memory runtime failure")
    if "dependency never satisfied" in lower or "dependency unresolved" in lower or "dependency not met" in lower:
        hints.append("Slurm dependency never satisfied (scheduler failure)")
    if "cancelled before start" in lower or "cancelled_before_start" in lower:
        hints.append("job cancelled before it started (scheduler failure)")
    if "setup failure" in lower or "setup failed" in lower or "failed_setup" in lower:
        hints.append("setup failure before the physics was produced")
    if not hints and any(marker in lower for marker in _PRE_DOMAIN_FAILURE_MARKERS):
        hints.append("application/runtime/setup failure before the core claim was tested")
    return hints

def _can_say(claim, supported_by: list[dict[str, Any]], limited_by: list[dict[str, Any]], not_tested_by: list[dict[str, Any]], blockers: list[str]) -> list[str]:
    statements: list[str] = [f"active claim remains {claim.confidence_state}"]
    if supported_by:
        statements.append("recorded support exists for the claim within the explicit recorded scope")
    if limited_by:
        statements.append("recorded limitations or open gaps bound how far the claim can be used")
    if not_tested_by:
        statements.append("some failed attempts are application/runtime failures and do not test the core claim")
    if blockers:
        statements.append(f"current blocker: {blockers[0]}")
    return _dedupe_clean(statements)

def _cannot_say(supported_by: list[dict[str, Any]], limited_by: list[dict[str, Any]], contradicted_by: list[dict[str, Any]], not_tested_by: list[dict[str, Any]]) -> list[str]:
    statements = ["cannot update or promote claim trust from this relation map alone"]
    if not supported_by:
        statements.append("cannot say the claim is supported until supporting evidence records exist")
    if limited_by:
        statements.append("cannot ignore scope limits, gap audits, or open proof obligations")
    if not_tested_by:
        statements.append("cannot say runtime/application failures prove the core algorithm works or fails")
    if contradicted_by:
        statements.append("cannot treat the claim as settled while challenging evidence remains unresolved")
    return _dedupe_clean(statements)

def _fallback_next_actions(not_tested_by: list[dict[str, Any]], blockers: list[str]) -> list[str]:
    if not_tested_by and blockers:
        text = " ".join(str(entry.get("summary") or "") for entry in not_tested_by).lower()
        if "thiele" in text and "ridge" in text:
            return [
                "resolve the runtime/application blocker, then rerun the same-executable Thiele baseline before interpreting ridge evidence"
            ]
        return [
            "resolve the runtime/application blocker, then rerun the same-executable baseline/control before interpreting algorithm evidence"
        ]
    if blockers:
        return ["resolve the recorded blocker before trust-changing interpretation"]
    return ["record explicit evidence, claim status, or proof obligation before drawing conclusions"]

def _prioritized_next_actions(
    recorded_actions: list[str],
    not_tested_by: list[dict[str, Any]],
    blockers: list[str],
) -> list[str]:
    fallback = _fallback_next_actions(not_tested_by, blockers)
    if not not_tested_by or not blockers:
        return recorded_actions or fallback
    if any(_is_specific_runtime_resolution_action(action) for action in recorded_actions):
        return recorded_actions
    return _dedupe_clean(fallback + recorded_actions)

def _is_specific_runtime_resolution_action(action: str) -> bool:
    lower = action.lower()
    if "baseline" in lower and ("same executable" in lower or "same-executable" in lower):
        return True
    if "thiele" in lower and "ridge" in lower and ("rerun" in lower or "reproduce" in lower or "run" in lower):
        return True
    if "control" in lower and ("runtime" in lower or "application" in lower):
        return True
    return False

def _entry_bullets(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return "- None\n"
    lines = []
    for entry in entries:
        lines.append(
            f"- `{entry.get('record_id', '')}` ({entry.get('relation_to_claim', '')}, "
            f"status={entry.get('status', '')}): {entry.get('summary', '')}\n"
        )
    return "".join(lines)

def _bullets(values: list[str]) -> str:
    return "".join(f"- {value}\n" for value in values) if values else "- None\n"

def _dedupe_clean(values: list[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        clean = str(value or "").strip()
        if clean and clean not in out:
            out.append(clean)
    return out

def _excerpt(value: Any, *, limit: int = 260) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
