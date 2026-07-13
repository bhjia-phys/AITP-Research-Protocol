# Compatibility shard 2 for quiet_checkpoint.
from __future__ import annotations

def _existing_closeout_record_refs(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    claim_id: str,
    run_id: str,
    generated_artifacts: list[dict[str, Any]],
    changed_files: list[str],
) -> list[str]:
    refs: list[str] = []
    artifact_uris = {
        _normalize_uri(str(item.get("uri") or item.get("path") or item.get("file") or ""))
        for item in _dict_list(generated_artifacts)
    }
    artifact_ids: set[str] = set()
    for artifact in list_records(ws.registry_dir("artifacts"), ArtifactRecord):
        if artifact.topic_id != topic_id or artifact.claim_id != claim_id:
            continue
        metadata = _dict(artifact.metadata)
        uri = _normalize_uri(artifact.uri)
        if metadata.get("closeout_run_id") == run_id or (uri and uri in artifact_uris):
            artifact_ids.add(artifact.artifact_id)
            refs.append(f"artifact:{artifact.artifact_id}")

    code_state_ids: set[str] = set()
    for state in list_records(ws.registry_dir("code_states"), CodeStateRecord):
        links = _dict(state.linked_records)
        runtime = _dict(state.runtime_environment)
        if links.get("topic_id") != topic_id or links.get("claim_id") != claim_id:
            continue
        if runtime.get("closeout_run_id") == run_id or _changed_files_overlap(runtime, changed_files):
            code_state_ids.add(state.code_state_id)
            refs.append(f"code_state:{state.code_state_id}")

    matching_run_ids: set[str] = set()
    matching_recipe_ids: set[str] = set()
    for run in list_records(ws.registry_dir("tool_runs"), ToolRunRecord):
        if run.topic_id != topic_id or run.claim_id != claim_id:
            continue
        outputs = _dict(run.outputs)
        if run.scientific_run_id == run_id or outputs.get("closeout_run_id") == run_id:
            matching_run_ids.add(run.run_id)
            matching_recipe_ids.add(run.recipe_id)
            refs.append(f"tool_run:{run.run_id}")

    for recipe in list_records(ws.registry_dir("tool_recipes"), ToolRecipeRecord):
        if recipe.recipe_id in matching_recipe_ids:
            refs.append(f"tool_recipe:{recipe.recipe_id}")

    for result in list_records(ws.registry_dir("validation_results"), ValidationResultRecord):
        if result.topic_id != topic_id or result.claim_id != claim_id:
            continue
        if result.tool_run_id in matching_run_ids or artifact_ids.intersection(set(result.artifact_ids)):
            refs.append(f"validation_result:{result.result_id}")

    for asset in list_records(ws.registry_dir("source_assets"), SourceAssetRecord):
        if asset.topic_id == topic_id and asset.claim_id == claim_id and _dict(asset.metadata).get("closeout_run_id") == run_id:
            refs.append(f"source_asset:{asset.asset_id}")

    for report in list_records(ws.registry_dir("sensemaking_reports"), SensemakingReportRecord):
        if report.topic_id == topic_id and report.claim_id == claim_id and (
            run_id in report.summary or run_id in report.title
        ):
            refs.append(f"sensemaking_report:{report.report_id}")

    return _dedupe(refs)

def _changed_files_overlap(runtime: dict[str, Any], changed_files: list[str]) -> bool:
    if not changed_files:
        return False
    wanted = {_normalize_uri(path) for path in changed_files}
    recorded = {
        _normalize_uri(str(item))
        for item in runtime.get("changed_files_relevant", [])
        if str(item).strip()
    }
    for item in runtime.get("changed_files_tracking", []):
        if isinstance(item, dict):
            recorded.add(_normalize_uri(str(item.get("path") or "")))
            recorded.add(_normalize_uri(str(item.get("git_path") or "")))
    return bool(wanted.intersection(recorded))

def _normalize_uri(value: str) -> str:
    text = str(value or "").strip().replace("\\", "/")
    lowered = text.lower()
    for prefix in ("local:file:", "path:", "file:"):
        if lowered.startswith(prefix) and not lowered.startswith("file://"):
            text = text[len(prefix) :].strip().replace("\\", "/")
            lowered = text.lower()
            break
    if lowered.startswith("file:///"):
        text = text[len("file:///") :]
    elif lowered.startswith("file://"):
        text = text[len("file://") :]
    return text

def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result
