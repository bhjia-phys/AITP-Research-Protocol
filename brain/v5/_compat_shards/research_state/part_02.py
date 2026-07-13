# Compatibility shard 2 for research_state.
from __future__ import annotations

def record_bounded_numerical_evidence(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    claim_id: str,
    artifact_uri: str,
    artifact_summary: str,
    supports_outputs: list[str],
    scope: str,
    status: str = "supports",
    artifact_type: str = "result_json",
    evidence_type: str = "bounded_numerical_evidence",
    recipe_id: str = "fisherd-bounded-numerical-audit",
    tool_family: str = "remote_numerics",
    tool_name: str = "fisherd",
    command: str = "",
    machine: str = "",
    remote_root: str = "",
    inputs: dict[str, Any] | None = None,
    outputs: dict[str, Any] | None = None,
    environment: dict[str, Any] | None = None,
    source_refs: list[str] | None = None,
    assumptions: list[str] | None = None,
    open_gaps: list[str] | None = None,
    next_action: str = "human_review_before_trust_update",
) -> dict[str, Any]:
    """Record a finite/run-bounded numerical result without trust promotion."""

    _require_known_claim(ws, claim_id, topic_id=topic_id)
    if status not in EVIDENCE_STATUSES:
        raise ValueError(f"unsupported evidence status: {status}")
    if not supports_outputs:
        raise ValueError("bounded numerical evidence requires at least one scoped output")
    metadata = {
        "scope": scope,
        "bounded_evidence": True,
        "machine": machine,
        "remote_root": remote_root,
        "command": command,
    }
    artifact = attach_artifact(
        ws,
        topic_id=topic_id,
        claim_id=claim_id,
        artifact_type=artifact_type,
        uri=artifact_uri,
        summary=artifact_summary,
        metadata=metadata,
    )
    run_inputs = dict(inputs or {})
    run_outputs = dict(outputs or {})
    run_env = dict(environment or {})
    if command:
        run_inputs.setdefault("command", command)
    if machine:
        run_env.setdefault("machine", machine)
    if remote_root:
        run_env.setdefault("remote_root", remote_root)
    run_outputs.setdefault("artifact_uri", artifact_uri)
    run_outputs.setdefault("artifact_id", artifact.artifact_id)
    run_outputs.setdefault("bounded_scope", scope)
    run = record_tool_run(
        ws,
        recipe_id=recipe_id,
        tool_family=tool_family,
        tool_name=tool_name,
        topic_id=topic_id,
        claim_id=claim_id,
        inputs=run_inputs,
        outputs=run_outputs,
        environment=run_env,
        evidence_status=status,
        artifact_ids=[artifact.artifact_id],
        source_refs=source_refs or [],
    )
    evidence_summary = f"{artifact_summary} Scope: {scope}"
    evidence = record_evidence(
        ws,
        topic_id=topic_id,
        claim_id=claim_id,
        evidence_type=evidence_type,
        status=status,
        summary=evidence_summary,
        supports_outputs=supports_outputs,
        source_refs=source_refs or [artifact_uri],
        tool_run_ids=[run.run_id],
        artifact_ids=[artifact.artifact_id],
    )
    claim_status = update_claim_status(
        ws,
        topic_id=topic_id,
        claim_id=claim_id,
        maturity_level="finite-size evidence",
        claim_status="bounded_numerical_evidence_recorded",
        scope=scope,
        risk="finite-size evidence only; no theorem or trust promotion",
        next_action=next_action,
        assumptions=assumptions or [],
        open_gaps=open_gaps or ["human gate required before trust update or L2 promotion"],
        source_refs=source_refs or [artifact_uri],
        evidence_refs=[evidence.evidence_id],
        artifact_ids=[artifact.artifact_id],
        human_gate_required=True,
    )
    classification = classify_research_event(
        topic_id=topic_id,
        claim_id=claim_id,
        event_kind="bounded_numerical_result",
        event_summary=artifact_summary,
        source_uri=artifact_uri,
    )
    return {
        "ok": True,
        "kind": "bounded_numerical_evidence_bundle",
        "topic_id": topic_id,
        "claim_id": claim_id,
        "artifact": asdict(artifact),
        "tool_run": tool_run_payload(run, include_ok=False),
        "evidence": asdict(evidence),
        "claim_status": asdict(claim_status),
        "classification": classification,
        "component_ids": {
            "artifact_id": artifact.artifact_id,
            "tool_run_id": run.run_id,
            "evidence_id": evidence.evidence_id,
            "claim_status_id": claim_status.status_id,
        },
        "supports_outputs": list(supports_outputs),
        "human_gate_required": True,
        "trust_update_forbidden": True,
        "can_update_claim_trust": False,
        "summary_inputs_trusted": False,
    }

def _require_known_claim(ws: WorkspacePaths, claim_id: str, *, topic_id: str) -> None:
    claim = get_claim(ws, claim_id)
    if claim.topic_id != topic_id:
        raise ValueError(f"claim {claim_id} belongs to topic {claim.topic_id}, not {topic_id}")

def _require_maturity(maturity_level: str) -> None:
    if maturity_level not in MATURITY_LEVELS:
        raise ValueError(f"maturity_level must be one of {sorted(MATURITY_LEVELS)}")

def _normalize_size_bytes(value: Any) -> int:
    if value in (None, ""):
        return 0
    try:
        size = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"size_bytes must be a non-negative integer, got {value!r}") from exc
    if size < 0:
        raise ValueError(f"size_bytes must be non-negative, got {size}")
    return size

def _merge_list(current: list[str], updates: list[str] | None, *, replace: bool) -> list[str]:
    if updates is None:
        return list(current)
    if replace:
        return _unique([str(item) for item in updates if str(item)])
    return _unique(list(current) + [str(item) for item in updates if str(item)])

def _local_path_from_uri(uri: str) -> Path | None:
    if uri.startswith("file://"):
        return Path(uri[7:])
    path = Path(uri)
    if path.exists():
        return path
    return None

def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = str(item)
        if key and key not in seen:
            out.append(key)
            seen.add(key)
    return out
