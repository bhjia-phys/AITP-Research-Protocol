# Compatibility shard 3 for process_graph.
from __future__ import annotations

def _provenance_gaps(
    *,
    claims: list[ClaimRecord],
    references: list[ReferenceLocationRecord],
    source_assets: list[SourceAssetRecord],
    evidence: list[EvidenceRecord],
    validation_contracts: list[ValidationContractRecord],
    validation_results: list[ValidationResultRecord],
    tool_runs: list[ToolRunRecord],
    code_states: list[CodeStateRecord],
) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for claim in claims:
        claim_id = claim.claim_id
        claim_refs = [record for record in references if record.claim_id == claim_id]
        claim_assets = [
            record
            for record in source_assets
            if record.claim_id == claim_id or _mapping_links_any(record.linked_records, {claim_id})
        ]
        claim_runs = [record for record in tool_runs if record.claim_id == claim_id]
        claim_contracts = [record for record in validation_contracts if record.claim_id == claim_id]
        claim_results = [record for record in validation_results if record.claim_id == claim_id]
        claim_code_state_ids = {
            code_id
            for run in claim_runs
            for code_id in run.code_state_ids
            if code_id
        }
        claim_code_state_ids.update(
            code_id
            for asset in claim_assets
            for code_id in asset.code_state_ids
            if code_id
        )
        claim_code_states = [
            record
            for record in code_states
            if record.code_state_id in claim_code_state_ids or _mapping_links_any(record.linked_records, {claim_id})
        ]
        if not claim_refs:
            gaps.append(
                _provenance_gap(
                    gap_type="reference_location_missing",
                    reason="claim has no typed source/reference pointer",
                    topic_id=claim.topic_id,
                    claim_id=claim_id,
                    target_type="claim",
                    target_id=claim_id,
                    recommended_actions=["aitp.record_reference_location"],
                    recommended_entrypoints=["aitp_v5_record_reference_location"],
                    severity="high",
                    provenance_kind="source",
                    target_record=claim,
                )
            )
        if not claim_assets:
            gaps.append(
                _provenance_gap(
                    gap_type="source_asset_missing",
                    reason="claim has no canonical source asset identity",
                    topic_id=claim.topic_id,
                    claim_id=claim_id,
                    target_type="claim",
                    target_id=claim_id,
                    recommended_actions=["aitp.capture_source_asset_auto", "aitp.register_source_asset"],
                    recommended_entrypoints=[
                        "aitp_v5_capture_source_asset_auto",
                        "aitp_v5_register_source_asset",
                    ],
                    severity="high",
                    provenance_kind="source",
                    target_record=claim,
                )
            )
        hashed_derivatives_by_parent = _hashed_source_asset_derivatives_by_parent(claim_assets)
        for asset in claim_assets:
            if not asset.content_hash and asset.asset_id not in hashed_derivatives_by_parent:
                gaps.append(
                    _provenance_gap(
                        gap_type="source_asset_hash_missing",
                        reason="source asset identity lacks a stable content hash",
                        topic_id=asset.topic_id,
                        claim_id=asset.claim_id or claim_id,
                        target_type="source_asset",
                        target_id=asset.asset_id,
                        recommended_actions=["aitp.capture_source_asset_auto", "aitp.register_source_asset"],
                        recommended_entrypoints=[
                            "aitp_v5_capture_source_asset_auto",
                            "aitp_v5_register_source_asset",
                        ],
                        severity="normal",
                        provenance_kind="source",
                        target_record=asset,
                    )
                )
            duplicate = asset.metadata.get("duplicate_hash_diagnostics", {})
            if isinstance(duplicate, dict) and duplicate.get("duplicate_hash"):
                gaps.append(
                    _provenance_gap(
                        gap_type="source_asset_duplicate_hash",
                        reason="source asset content hash matches another registered asset",
                        topic_id=asset.topic_id,
                        claim_id=asset.claim_id or claim_id,
                        target_type="source_asset",
                        target_id=asset.asset_id,
                        recommended_actions=["aitp.review_source_asset_duplicate"],
                        recommended_entrypoints=["aitp_v5_register_source_asset"],
                        severity="normal",
                        provenance_kind="source",
                        target_record=asset,
                    )
                )
        if _claim_needs_code_provenance(claim):
            if not claim_code_states:
                gaps.append(
                    _provenance_gap(
                        gap_type="code_state_missing",
                        reason="code-dependent claim has no captured git code state",
                        topic_id=claim.topic_id,
                        claim_id=claim_id,
                        target_type="claim",
                        target_id=claim_id,
                        recommended_actions=["aitp.capture_code_state_auto", "aitp.record_code_state"],
                        recommended_entrypoints=["aitp_v5_capture_code_state_auto", "aitp_v5_record_code_state"],
                        severity="high",
                        provenance_kind="code",
                        target_record=claim,
                    )
                )
            if not claim_runs:
                gaps.append(
                    _provenance_gap(
                        gap_type="tool_run_missing",
                        reason="code-dependent claim has no typed tool-run provenance",
                        topic_id=claim.topic_id,
                        claim_id=claim_id,
                        target_type="claim",
                        target_id=claim_id,
                        recommended_actions=["aitp.capture_tool_run_auto", "aitp.record_tool_run"],
                        recommended_entrypoints=["aitp_v5_capture_tool_run_auto", "aitp_v5_record_tool_run"],
                        severity="high",
                        provenance_kind="tool_run",
                        target_record=claim,
                    )
                )
            if not claim_contracts:
                gaps.append(
                    _provenance_gap(
                        gap_type="validation_contract_missing",
                        reason="code/benchmark-dependent claim has no validation contract",
                        topic_id=claim.topic_id,
                        claim_id=claim_id,
                        target_type="claim",
                        target_id=claim_id,
                        recommended_actions=["aitp.create_validation_contract"],
                        recommended_entrypoints=["aitp_v5_create_validation_contract"],
                        severity="normal",
                        provenance_kind="validation",
                        target_record=claim,
                    )
                )
        for run in claim_runs:
            if _tool_run_needs_code_state(run) and not run.code_state_ids:
                gaps.append(
                    _provenance_gap(
                        gap_type="tool_run_code_state_missing",
                        reason="tool run looks code-backed but is not linked to a code state",
                        topic_id=run.topic_id,
                        claim_id=run.claim_id,
                        target_type="tool_run",
                        target_id=run.run_id,
                        recommended_actions=["aitp.capture_code_state_auto", "aitp.record_tool_run"],
                        recommended_entrypoints=["aitp_v5_capture_code_state_auto", "aitp_v5_record_tool_run"],
                        severity="high",
                        provenance_kind="code",
                        target_record=run,
                    )
                )
            if _tool_run_needs_artifact(run) and not run.artifact_ids:
                gaps.append(
                    _provenance_gap(
                        gap_type="benchmark_artifact_missing",
                        reason="benchmark/result-like tool run has no artifact reference",
                        topic_id=run.topic_id,
                        claim_id=run.claim_id,
                        target_type="tool_run",
                        target_id=run.run_id,
                        recommended_actions=["aitp.attach_artifact_auto", "aitp.attach_artifact", "aitp.record_tool_run"],
                        recommended_entrypoints=[
                            "aitp_v5_attach_artifact_auto",
                            "aitp_v5_attach_artifact",
                            "aitp_v5_record_tool_run",
                        ],
                        severity="normal",
                        provenance_kind="artifact",
                        target_record=run,
                    )
                )
        for result in claim_results:
            if _validation_result_needs_artifact(result) and not result.artifact_ids:
                gaps.append(
                    _provenance_gap(
                        gap_type="validation_result_artifact_missing",
                        reason="validation result has no artifact reference for its checked output",
                        topic_id=result.topic_id,
                        claim_id=result.claim_id,
                        target_type="validation_result",
                        target_id=result.result_id,
                        recommended_actions=[
                            "aitp.attach_artifact_auto",
                            "aitp.attach_artifact",
                            "aitp.record_validation_result",
                        ],
                        recommended_entrypoints=[
                            "aitp_v5_attach_artifact_auto",
                            "aitp_v5_attach_artifact",
                            "aitp_v5_record_validation_result",
                        ],
                        severity="normal",
                        provenance_kind="artifact",
                        target_record=result,
                    )
                )
    return _dedupe_gaps(gaps)

def _provenance_gap(
    *,
    gap_type: str,
    reason: str,
    topic_id: str,
    claim_id: str,
    target_type: str,
    target_id: str,
    recommended_actions: list[str],
    recommended_entrypoints: list[str],
    severity: str,
    provenance_kind: str,
    target_record: Any | None = None,
) -> dict[str, Any]:
    target_payload = _record_payload(target_record) if target_record is not None else {}
    return {
        "gap_id": f"provenance-gap:{gap_type}:{target_type}:{target_id}",
        "gap_type": gap_type,
        "provenance_kind": provenance_kind,
        "reason": reason,
        "topic_id": topic_id,
        "claim_id": claim_id,
        "target_type": target_type,
        "target_id": target_id,
        "target_refs": [f"{target_type}:{target_id}"],
        "recommended_actions": list(recommended_actions),
        "recommended_entrypoints": list(recommended_entrypoints),
        "payload_hints": _provenance_payload_hints(
            recommended_entrypoints=recommended_entrypoints,
            gap_type=gap_type,
            provenance_kind=provenance_kind,
            reason=reason,
            topic_id=topic_id,
            claim_id=claim_id,
            target_type=target_type,
            target_id=target_id,
            target_record=target_payload,
        ),
        "severity": severity,
        "required_now": False,
        "required_before_trust_change": False,
        "strict_boundary": "before_using_as_evidence_validation_benchmark_memory_or_checked_conclusion",
        "blocking_when_used_as": [
            "evidence",
            "validation_input",
            "benchmark_basis",
            "memory_promotion_input",
            "human_facing_checked_conclusion",
        ],
        "orientation_only": True,
        "can_update_claim_trust": False,
    }

def _claim_needs_code_provenance(claim: ClaimRecord) -> bool:
    text = " ".join(
        [
            claim.evidence_profile,
            claim.statement,
            claim.active_uncertainty,
            claim.recipe_id,
            claim.scope,
        ]
    ).lower()
    return any(token in text for token in ("code", "benchmark", "git", "repo", "tool", "run", "numerical"))

def _tool_run_needs_code_state(record: ToolRunRecord) -> bool:
    text = " ".join([record.recipe_id, record.tool_family, record.tool_name]).lower()
    return any(token in text for token in ("code", "python", "git", "benchmark", "runner", "numeric"))

def _tool_run_needs_artifact(record: ToolRunRecord) -> bool:
    text = " ".join(
        [
            record.recipe_id,
            record.tool_family,
            record.tool_name,
            str(record.outputs),
            record.evidence_status,
        ]
    ).lower()
    return any(token in text for token in ("benchmark", "result", "stdout", "log", "artifact", "plot", "json"))

def _validation_result_needs_artifact(record: ValidationResultRecord) -> bool:
    text = " ".join([record.summary, " ".join(record.checked_outputs)]).lower()
    return any(token in text for token in ("benchmark", "result", "log", "plot", "artifact", "json"))

def _dedupe_gaps(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result: list[dict[str, Any]] = []
    for item in items:
        key = (item.get("gap_type"), item.get("target_type"), item.get("target_id"))
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result

def _provenance_payload_hints(
    *,
    recommended_entrypoints: list[str],
    gap_type: str,
    provenance_kind: str,
    reason: str,
    topic_id: str,
    claim_id: str,
    target_type: str,
    target_id: str,
    target_record: dict[str, Any],
) -> list[dict[str, Any]]:
    hints: list[dict[str, Any]] = []
    for entrypoint in recommended_entrypoints:
        hint = _provenance_payload_hint(
            entrypoint=entrypoint,
            gap_type=gap_type,
            provenance_kind=provenance_kind,
            reason=reason,
            topic_id=topic_id,
            claim_id=claim_id,
            target_type=target_type,
            target_id=target_id,
            target_record=target_record,
        )
        if hint is not None:
            hints.append(with_draft_schema(hint))
    return hints
