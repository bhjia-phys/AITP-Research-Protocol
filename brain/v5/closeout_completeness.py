"""Plan-only completeness audit for Codex closeout and quiet checkpoints."""

from __future__ import annotations

from pathlib import PurePosixPath, PureWindowsPath
from typing import Any


DURABLE_ARTIFACT_EXTENSIONS = {
    ".csv",
    ".dat",
    ".ipynb",
    ".json",
    ".jsonl",
    ".log",
    ".md",
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".svg",
    ".tex",
    ".tsv",
    ".txt",
    ".yaml",
    ".yml",
}

CODE_STATE_EXTENSIONS = {
    ".bat",
    ".c",
    ".cc",
    ".cpp",
    ".cu",
    ".f",
    ".f90",
    ".ipynb",
    ".jl",
    ".m",
    ".py",
    ".ps1",
    ".R",
    ".rs",
    ".sh",
    ".toml",
    ".yaml",
    ".yml",
}

VALIDATION_COMMAND_TOKENS = (
    "pytest",
    "pdflatex",
    "xelatex",
    "lualatex",
    "tectonic",
    "python",
    "python3",
    "julia",
    "bash",
    "pwsh",
    "powershell",
    "select-string",
    "grep",
    "diff",
    "make",
    "ninja",
)

VALIDATION_SUCCESS_TOKENS = (
    "compile",
    "compiled",
    "passed",
    "pass",
    "success",
    "zero",
    "control",
    "validated",
    "verification",
    "verified",
)

OPEN_GAP_TOKENS = (
    "cannot say",
    "do not claim",
    "gap",
    "incomplete",
    "not checked",
    "not claim",
    "not established",
    "not validated",
    "not verified",
    "open",
    "open-gap",
    "unchecked",
    "unresolved",
    "unvalidated",
    "unverified",
)


def build_record_completeness_audit(
    *,
    topic_id: str,
    claim_id: str,
    run_id: str,
    summary: str = "",
    inputs: list[Any] | None = None,
    outputs: list[Any] | None = None,
    changed_files: list[Any] | None = None,
    generated_artifacts: list[Any] | None = None,
    validation_commands: list[Any] | None = None,
    claim_boundary: dict[str, Any] | None = None,
    next_blockers: list[Any] | None = None,
    artifact_specs: list[Any] | None = None,
    source_specs: list[Any] | None = None,
    tool_run_specs: list[Any] | None = None,
    written_refs: list[str] | None = None,
    planned_typed_writes: list[Any] | None = None,
    closeout_surface: str = "quiet_checkpoint",
    write_executed: bool = False,
) -> dict[str, Any]:
    """Return a structured, non-writing audit for closeout record completeness.

    The audit is intentionally advisory. It can identify missing typed records,
    but it must not create evidence, validation, code-state, or trust records.
    """

    inputs = list(inputs or [])
    outputs = list(outputs or [])
    changed_files = list(changed_files or [])
    generated_artifacts = list(generated_artifacts or [])
    validation_commands = list(validation_commands or [])
    claim_boundary = dict(claim_boundary or {})
    next_blockers = list(next_blockers or [])
    artifact_specs = list(artifact_specs or [])
    source_specs = list(source_specs or [])
    tool_run_specs = list(tool_run_specs or [])
    written_refs = [str(ref) for ref in written_refs or []]
    planned_typed_writes = list(planned_typed_writes or [])

    recorded_slots = _slots_from_written_refs(written_refs)
    planned_slots = _slots_from_planned_writes(planned_typed_writes, artifact_specs, source_specs, tool_run_specs)
    artifact_candidates = _artifact_candidates(generated_artifacts, outputs)

    missing_slots: list[str] = []
    recommendations: list[dict[str, Any]] = []

    if artifact_candidates and "artifact" not in recorded_slots:
        _add_missing(missing_slots, "artifact")
        recommendations.append(
            {
                "slot": "artifact",
                "recommended_tool": "aitp_v5_attach_artifact",
                "reason": "durable closeout files are referenced but not attached as typed artifacts",
                "canonical_provenance": artifact_candidates,
                "plan_only": True,
                "requires_user_confirmation": True,
            }
        )

    code_state_reasons = _code_state_reasons(changed_files, generated_artifacts, validation_commands)
    if code_state_reasons and "code_state" not in recorded_slots:
        _add_missing(missing_slots, "code_state")
        recommendations.append(
            {
                "slot": "code_state",
                "recommended_tool": "aitp_v5_capture_code_state_auto",
                "reason": "repo-dependent numerical or code work should be tied to a code_state record",
                "triggers": code_state_reasons,
                "changed_files": [str(path) for path in changed_files],
                "plan_only": True,
                "requires_user_confirmation": True,
            }
        )

    validation_need = _validation_need(validation_commands, claim_boundary)
    if validation_need["needed"] and "validation_result" not in recorded_slots:
        _add_missing(missing_slots, "validation_result")
        recommendations.append(
            {
                "slot": "validation_result",
                "recommended_tool": "aitp_v5_record_validation_result",
                "record_kind": "validation_result_or_validation_gap",
                "reason": validation_need["reason"],
                "validation_commands": [str(command) for command in validation_commands],
                "status_hint": validation_need["status_hint"],
                "claim_boundary_refs": validation_need["boundary_refs"],
                "prerequisites": ["validation_contract", "tool_run"],
                "plan_only": True,
                "requires_user_confirmation": True,
                "do_not_promote_trust": True,
            }
        )

    trust_boundary = {
        "quiet_checkpoint_orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
        "do_not_promote_trust": True,
        "unresolved_artifact_refs_are_not_evidence": bool(artifact_candidates and "artifact" not in recorded_slots),
        "requires_trust_preflight_for_promotion": True,
    }

    checkpoint_strength = "weak_checkpoint"
    action = "recorded" if write_executed else "previewed"
    if missing_slots:
        completeness_summary = (
            f"{closeout_surface} {action}, but durable package incomplete: "
            + ", ".join(_missing_phrase(slot) for slot in missing_slots)
            + "."
        )
    else:
        completeness_summary = (
            f"{closeout_surface} has no missing recommended typed records for the supplied closeout payload."
        )

    if _has_open_gap(claim_boundary, next_blockers):
        completeness_summary += " Explicit open gaps remain; do not promote trust."

    return {
        "kind": "record_completeness_audit",
        "topic_id": topic_id,
        "claim_id": claim_id,
        "run_id": run_id,
        "closeout_surface": closeout_surface,
        "write_executed": bool(write_executed),
        "recording_complete": not missing_slots,
        "checkpoint_strength": checkpoint_strength,
        "recorded_slots": recorded_slots,
        "planned_slots": planned_slots,
        "missing_recommended_slots": missing_slots,
        "recommended_next_records": recommendations,
        "trust_boundary": trust_boundary,
        "requires_user_confirmation": bool(missing_slots),
        "summary": completeness_summary,
        "unresolved_artifact_refs": artifact_candidates if "artifact" in missing_slots else [],
        "inputs_considered": {
            "has_summary": bool(str(summary or "").strip()),
            "input_count": len(inputs),
            "output_count": len(outputs),
            "generated_artifact_count": len(generated_artifacts),
            "durable_artifact_candidate_count": len(artifact_candidates),
            "changed_file_count": len(changed_files),
            "validation_command_count": len(validation_commands),
            "claim_boundary_keys": sorted(str(key) for key in claim_boundary.keys()),
        },
        "plan_only": True,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }


def _slots_from_written_refs(written_refs: list[str]) -> list[str]:
    slots: set[str] = set()
    for ref in written_refs:
        prefix = ref.split(":", 1)[0].strip()
        if prefix:
            slots.add(prefix)
    return sorted(slots)


def _slots_from_planned_writes(
    planned_typed_writes: list[Any],
    artifact_specs: list[Any],
    source_specs: list[Any],
    tool_run_specs: list[Any],
) -> list[str]:
    slots: set[str] = set()
    for item in planned_typed_writes:
        slot = ""
        if isinstance(item, dict):
            slot = _slot_from_record_type(str(item.get("record_type") or item.get("slot") or ""))
        else:
            slot = _slot_from_record_type(str(item))
        if slot:
            slots.add(slot)
    if artifact_specs:
        slots.add("artifact")
    if source_specs:
        slots.add("source_asset")
    if tool_run_specs:
        slots.add("tool_run")
    return sorted(slots)


def _slot_from_record_type(record_type: str) -> str:
    text = record_type.strip()
    for suffix in ("_record", "_batch"):
        if text.endswith(suffix):
            text = text[: -len(suffix)]
    if text == "artifact":
        return "artifact"
    if text == "source_asset":
        return "source_asset"
    if text == "tool_run":
        return "tool_run"
    if text == "sensemaking_report":
        return "sensemaking_report"
    if text == "quiet_checkpoint":
        return "quiet_checkpoint"
    if text == "run_iteration":
        return "run_iteration"
    return text


def _artifact_candidates(generated_artifacts: list[Any], outputs: list[Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in [*generated_artifacts, *outputs]:
        candidate = _normalize_artifact_candidate(item)
        if not candidate:
            continue
        key = candidate.get("uri") or candidate.get("path") or repr(candidate)
        if key in seen:
            continue
        seen.add(key)
        candidates.append(candidate)
    return candidates


def _normalize_artifact_candidate(item: Any) -> dict[str, Any] | None:
    if isinstance(item, dict):
        uri = _first_string(item, ("uri", "path", "file", "local_path", "target_path", "href"))
        artifact_type = _first_string(item, ("artifact_type", "type", "kind"))
        if not uri and not artifact_type:
            return None
        if uri and not (_looks_like_durable_artifact(uri) or artifact_type):
            return None
        candidate = {
            "uri": uri,
            "artifact_type": artifact_type or _artifact_type_from_uri(uri),
            "label": _first_string(item, ("label", "title", "name")),
            "summary": _first_string(item, ("summary", "description", "note")),
        }
        repo_path = _first_string(item, ("repo_path", "worktree_path", "repository", "repo"))
        if repo_path:
            candidate["repo_path"] = repo_path
        return {key: value for key, value in candidate.items() if value not in (None, "")}

    uri = str(item).strip()
    if not uri or not _looks_like_durable_artifact(uri):
        return None
    return {
        "uri": uri,
        "artifact_type": _artifact_type_from_uri(uri),
    }


def _first_string(item: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = item.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _artifact_type_from_uri(uri: str) -> str:
    suffix = _suffix(uri)
    if suffix == ".pdf":
        return "pdf_report"
    if suffix in {".png", ".jpg", ".jpeg", ".svg"}:
        return "figure"
    if suffix in {".json", ".jsonl", ".csv", ".tsv", ".dat"}:
        return "data_output"
    if suffix in {".tex", ".md", ".txt"}:
        return "note_or_source"
    if suffix in {".log", ".yaml", ".yml"}:
        return "diagnostic_output"
    if suffix == ".ipynb":
        return "notebook"
    return "durable_file"


def _looks_like_durable_artifact(uri: str) -> bool:
    return _suffix(uri) in DURABLE_ARTIFACT_EXTENSIONS


def _suffix(uri: str) -> str:
    text = str(uri).strip().split("?", 1)[0].split("#", 1)[0]
    win_suffix = PureWindowsPath(text).suffix.lower()
    posix_suffix = PurePosixPath(text).suffix.lower()
    return win_suffix or posix_suffix


def _code_state_reasons(
    changed_files: list[Any],
    generated_artifacts: list[Any],
    validation_commands: list[Any],
) -> list[str]:
    reasons: list[str] = []
    if changed_files:
        reasons.append("changed_files_present")

    for item in generated_artifacts:
        if isinstance(item, dict) and _first_string(item, ("repo_path", "worktree_path", "repository", "repo")):
            reasons.append("repo_path_present")
            break

    if any(_suffix(str(path)) in CODE_STATE_EXTENSIONS for path in changed_files):
        reasons.append("code_or_script_changes_present")

    lowered_commands = " ".join(str(command).lower() for command in validation_commands)
    if lowered_commands and any(token in lowered_commands for token in VALIDATION_COMMAND_TOKENS):
        reasons.append("validation_commands_depend_on_tools_or_scripts")

    return _dedupe(reasons)


def _validation_need(validation_commands: list[Any], claim_boundary: dict[str, Any]) -> dict[str, Any]:
    boundary_refs = _matching_boundary_strings(claim_boundary, VALIDATION_SUCCESS_TOKENS + OPEN_GAP_TOKENS)
    open_gap = any(_contains_token(ref, OPEN_GAP_TOKENS) for ref in boundary_refs)
    success_boundary = any(_contains_token(ref, VALIDATION_SUCCESS_TOKENS) for ref in boundary_refs)

    if validation_commands and open_gap:
        return {
            "needed": True,
            "reason": "validation commands and explicit open validation gaps require a validation_result or validation-gap record",
            "status_hint": "inconclusive_or_partial",
            "boundary_refs": boundary_refs,
        }
    if validation_commands:
        return {
            "needed": True,
            "reason": "validation commands are reported but no typed validation_result is recorded",
            "status_hint": "passed_failed_or_inconclusive_from_command_outcome",
            "boundary_refs": boundary_refs,
        }
    if open_gap:
        return {
            "needed": True,
            "reason": "explicit validation boundary or open gap should be recorded as validation_result or validation-gap",
            "status_hint": "inconclusive_or_open_gap",
            "boundary_refs": boundary_refs,
        }
    if success_boundary:
        return {
            "needed": True,
            "reason": "explicit validation boundary should be represented by a typed validation_result",
            "status_hint": "passed_failed_or_inconclusive_from_boundary",
            "boundary_refs": boundary_refs,
        }
    return {
        "needed": False,
        "reason": "",
        "status_hint": "",
        "boundary_refs": boundary_refs,
    }


def _has_open_gap(claim_boundary: dict[str, Any], next_blockers: list[Any]) -> bool:
    refs = _matching_boundary_strings(claim_boundary, OPEN_GAP_TOKENS)
    refs.extend(str(blocker) for blocker in next_blockers)
    return any(_contains_token(ref, OPEN_GAP_TOKENS) for ref in refs)


def _matching_boundary_strings(value: Any, tokens: tuple[str, ...]) -> list[str]:
    matches: list[str] = []
    for text in _flatten_strings(value):
        if _contains_token(text, tokens):
            matches.append(text)
    return _dedupe(matches)


def _flatten_strings(value: Any) -> list[str]:
    if isinstance(value, dict):
        strings: list[str] = []
        for key, item in value.items():
            strings.append(str(key))
            strings.extend(_flatten_strings(item))
        return strings
    if isinstance(value, (list, tuple, set)):
        strings = []
        for item in value:
            strings.extend(_flatten_strings(item))
        return strings
    if value is None:
        return []
    return [str(value)]


def _contains_token(text: str, tokens: tuple[str, ...]) -> bool:
    lowered = str(text).lower()
    return any(token in lowered for token in tokens)


def _add_missing(missing_slots: list[str], slot: str) -> None:
    if slot not in missing_slots:
        missing_slots.append(slot)


def _missing_phrase(slot: str) -> str:
    if slot == "artifact":
        return "attach artifact"
    if slot == "code_state":
        return "capture code_state"
    if slot == "validation_result":
        return "record validation_result/gap"
    return f"record {slot}"


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result
