"""Plan-only completeness audit for Codex closeout and quiet checkpoints."""

from __future__ import annotations

import re
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

    tool_run_need = _tool_run_need(
        inputs=inputs,
        outputs=outputs,
        validation_commands=validation_commands,
        tool_run_specs=tool_run_specs,
    )
    if tool_run_need["needed"] and "tool_recipe" not in recorded_slots:
        _add_missing(missing_slots, "tool_recipe")
        recommendations.append(
            {
                "slot": "tool_recipe",
                "recommended_tool": "aitp_v5_register_tool_recipe",
                "reason": "tool-run provenance is expected but no reusable recipe is recorded",
                "triggers": tool_run_need["triggers"],
                "plan_only": True,
                "requires_user_confirmation": True,
                "do_not_promote_trust": True,
            }
        )

    if tool_run_need["needed"] and "tool_run" not in recorded_slots:
        _add_missing(missing_slots, "tool_run")
        recommendations.append(
            {
                "slot": "tool_run",
                "recommended_tool": "aitp_v5_record_tool_run",
                "reason": tool_run_need["reason"],
                "triggers": tool_run_need["triggers"],
                "json_argument_policy": "prefer *_json_file CLI arguments on Windows for nested payloads",
                "plan_only": True,
                "requires_user_confirmation": True,
                "do_not_promote_trust": True,
            }
        )

    source_asset_need = _source_asset_need(
        source_specs=source_specs,
        artifact_candidates=artifact_candidates,
        tool_run_needed=bool(tool_run_need["needed"]),
    )
    if source_asset_need["needed"] and "source_asset" not in recorded_slots:
        _add_missing(missing_slots, "source_asset")
        recommendations.append(
            {
                "slot": "source_asset",
                "recommended_tool": "aitp_v5_register_source_asset",
                "reason": source_asset_need["reason"],
                "canonical_provenance": source_asset_need["canonical_provenance"],
                "asset_type_policy": {
                    "allowed_examples": ["paper", "dataset", "generated_artifact", "note"],
                    "common_aliases": {"derived_dataset": "dataset"},
                },
                "plan_only": True,
                "requires_user_confirmation": True,
                "do_not_promote_trust": True,
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

    sensemaking_need = _sensemaking_need(claim_boundary, next_blockers)
    if sensemaking_need["needed"] and "sensemaking_report" not in recorded_slots:
        _add_missing(missing_slots, "sensemaking_report")
        recommendations.append(
            {
                "slot": "sensemaking_report",
                "recommended_tool": "aitp_v5_record_sensemaking_report",
                "reason": sensemaking_need["reason"],
                "boundary_refs": sensemaking_need["boundary_refs"],
                "plan_only": True,
                "requires_user_confirmation": True,
                "do_not_promote_trust": True,
            }
        )

    compact_apply_plan = _compact_apply_plan(
        topic_id=topic_id,
        claim_id=claim_id,
        run_id=run_id,
        summary=summary,
        inputs=inputs,
        outputs=outputs,
        changed_files=changed_files,
        artifact_candidates=artifact_candidates,
        validation_commands=validation_commands,
        claim_boundary=claim_boundary,
        missing_slots=missing_slots,
        validation_needed=bool(validation_need["needed"]),
    )

    trust_boundary = {
        "quiet_checkpoint_orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
        "do_not_promote_trust": True,
        "unresolved_artifact_refs_are_not_evidence": bool(artifact_candidates and "artifact" not in recorded_slots),
        "requires_trust_preflight_for_promotion": True,
        "finite_numeric_outputs_do_not_prove_theorem": True,
        "sibling_claim_records_do_not_support_active_claim_by_default": True,
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
        "expected_record_slots": _expected_record_slots(
            artifact_candidates=artifact_candidates,
            tool_run_needed=bool(tool_run_need["needed"]),
            source_asset_needed=bool(source_asset_need["needed"]),
            code_state_needed=bool(code_state_reasons),
            validation_needed=bool(validation_need["needed"]),
            sensemaking_needed=bool(sensemaking_need["needed"]),
        ),
        "recorded_slots": recorded_slots,
        "planned_slots": planned_slots,
        "missing_recommended_slots": missing_slots,
        "recommended_next_records": recommendations,
        "compact_apply_plan": compact_apply_plan,
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
        normalized_uri = _normalize_local_file_reference(uri)
        artifact_type = _first_string(item, ("artifact_type", "type", "kind"))
        if not uri and not artifact_type:
            return None
        if normalized_uri and not (_looks_like_durable_artifact(normalized_uri) or artifact_type):
            return None
        candidate = {
            "uri": normalized_uri,
            "artifact_type": artifact_type or _artifact_type_from_uri(normalized_uri),
            "label": _first_string(item, ("label", "title", "name")),
            "summary": _first_string(item, ("summary", "description", "note")),
        }
        if normalized_uri != uri:
            candidate["original_uri"] = uri
        repo_path = _first_string(item, ("repo_path", "worktree_path", "repository", "repo"))
        if repo_path:
            candidate["repo_path"] = repo_path
        return {key: value for key, value in candidate.items() if value not in (None, "")}

    uri = _normalize_local_file_reference(str(item).strip())
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
    text = _normalize_local_file_reference(str(uri).strip()).split("?", 1)[0].split("#", 1)[0]
    win_suffix = PureWindowsPath(text).suffix.lower()
    posix_suffix = PurePosixPath(text).suffix.lower()
    return win_suffix or posix_suffix


def _normalize_local_file_reference(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    lowered = text.lower()
    for prefix in ("local:file:", "path:", "file:"):
        if lowered.startswith(prefix) and not lowered.startswith("file://"):
            rest = text[len(prefix) :].strip()
            if _looks_like_windows_drive_path(rest):
                return "file:///" + rest.replace("\\", "/")
            if rest.startswith(("/", "\\")):
                return "file://" + rest.replace("\\", "/")
            return rest or text
    return text


def _looks_like_windows_drive_path(value: str) -> bool:
    return bool(re.match(r"^[A-Za-z]:[\\/]", str(value or "")))


def _compact_apply_plan(
    *,
    topic_id: str,
    claim_id: str,
    run_id: str,
    summary: str,
    inputs: list[Any],
    outputs: list[Any],
    changed_files: list[Any],
    artifact_candidates: list[dict[str, Any]],
    validation_commands: list[Any],
    claim_boundary: dict[str, Any],
    missing_slots: list[str],
    validation_needed: bool,
) -> dict[str, Any]:
    actions: list[dict[str, Any]] = []
    recipe_id = _recipe_id_for_closeout(run_id, validation_commands)
    artifact_refs = ["artifact:<from prior artifact apply>"] if "artifact" in missing_slots else []
    code_state_refs = ["code_state:<from code_state apply>"] if "code_state" in missing_slots else []
    validation_semantics = _validation_semantics(
        artifact_candidates=artifact_candidates,
        validation_commands=validation_commands,
        claim_boundary=claim_boundary,
    )

    if "artifact" in missing_slots:
        for index, candidate in enumerate(artifact_candidates, start=1):
            actions.append(
                {
                    "step": len(actions) + 1,
                    "slot": "artifact",
                    "apply_tool": "aitp_v5_codex_record_apply",
                    "purpose": "Attach a durable generated file by reference.",
                    "payload_template": {
                        "artifact_type": candidate.get("artifact_type") or "generated_artifact",
                        "uri": candidate.get("uri") or "",
                        "summary": candidate.get("summary") or summary,
                        "metadata": {
                            "closeout_run_id": run_id,
                            "closeout_artifact_index": index,
                            "original_uri": candidate.get("original_uri", ""),
                            "can_update_claim_trust": False,
                        },
                    },
                }
            )

    if "code_state" in missing_slots:
        worktree_path = _infer_worktree_path(artifact_candidates)
        action = {
            "step": len(actions) + 1,
            "slot": "code_state",
            "apply_tool": "aitp_v5_codex_record_apply",
            "purpose": "Capture git/worktree provenance for the files used to produce the artifact.",
            "payload_template": {
                "worktree_path": worktree_path or "<workspace-root-containing-changed-files>",
                "changed_files": [str(path) for path in changed_files],
                "runtime_environment": {
                    "closeout_run_id": run_id,
                    "changed_files_relevant": [str(path) for path in changed_files],
                    "clean_reproducibility_anchor_required": False,
                },
                "known_divergence": (
                    "If the source tree is dirty, this code_state is not a clean reproducibility anchor."
                ),
                "write_patch_artifact": False,
            },
        }
        if not worktree_path:
            action["requires_agent_fill"] = ["payload.worktree_path"]
        actions.append(action)

    if "tool_recipe" in missing_slots:
        actions.append(
            {
                "step": len(actions) + 1,
                "slot": "tool_recipe",
                "apply_tool": "aitp_v5_codex_record_apply",
                "purpose": "Register the repeatable document build/check recipe before recording the tool run.",
                "payload_template": {
                    "recipe_id": recipe_id,
                    "tool_family": validation_semantics["tool_family"],
                    "tool_name": validation_semantics["tool_name"],
                    "purpose": validation_semantics["recipe_purpose"],
                    "required_inputs": [str(item) for item in inputs + changed_files],
                    "expected_outputs": [str(item.get("uri") or item) for item in artifact_candidates] + [str(item) for item in outputs],
                    "invariants": validation_semantics["invariants"],
                },
            }
        )

    if "tool_run" in missing_slots:
        actions.append(
            {
                "step": len(actions) + 1,
                "slot": "tool_run",
                "apply_tool": "aitp_v5_codex_record_apply",
                "purpose": "Record the Codex-side build/check execution as diagnostic provenance.",
                "depends_on_slots": ["tool_recipe", "artifact", "code_state"],
                "payload_template": {
                    "recipe_id": recipe_id,
                    "tool_family": validation_semantics["tool_family"],
                    "tool_name": validation_semantics["tool_name"],
                    "inputs": {
                        "reported_inputs": [str(item) for item in inputs],
                        "changed_files": [str(path) for path in changed_files],
                    },
                    "outputs": {
                        "generated_artifacts": artifact_candidates,
                        "reported_outputs": [str(item) for item in outputs],
                        "validation_commands": [str(command) for command in validation_commands],
                        "closeout_run_id": run_id,
                    },
                    "environment": {
                        "executor": "Codex app",
                        "validation_target": validation_semantics["target"],
                        "validation_boundary": validation_semantics["boundary"],
                        "can_update_claim_trust": False,
                    },
                    "evidence_status": "diagnostic",
                    "artifact_ids": artifact_refs,
                    "code_state_ids": code_state_refs,
                    "scientific_run_id": run_id,
                    "lane": "diagnostic",
                },
            }
        )

    if validation_needed and "validation_result" in missing_slots:
        actions.append(
            {
                "step": len(actions) + 1,
                "slot": "validation_contract",
                "apply_tool": "aitp_v5_codex_record_apply",
                "purpose": "Define exactly what the document validation checks cover.",
                "payload_template": {
                    "required_checks": validation_semantics["required_checks"],
                    "failure_modes": validation_semantics["failure_modes"],
                    "required_evidence_outputs": validation_semantics["required_evidence_outputs"],
                    "tool_recipe_ids": [recipe_id],
                    "executor_ids": ["codex-app"],
                    "validator_role": validation_semantics["validator_role"],
                },
            }
        )
        actions.append(
            {
                "step": len(actions) + 1,
                "slot": "validation_result",
                "apply_tool": "aitp_v5_codex_record_apply",
                "purpose": "Record document build/layout validation without treating it as physics-claim support.",
                "depends_on_slots": ["validation_contract", "tool_run"],
                "payload_template": {
                    "contract_id": "validation_contract:<from validation_contract apply>",
                    "tool_run_id": "tool_run:<from tool_run apply>",
                    "status": validation_semantics["status"],
                    "checked_outputs": validation_semantics["checked_outputs"],
                    "summary": validation_semantics["result_summary"],
                    "artifact_ids": artifact_refs,
                    "covered_failure_modes": validation_semantics["failure_modes"],
                    "failure_modes_observed": [],
                },
            }
        )

    return {
        "kind": "compact_record_apply_plan",
        "apply_tool": "aitp_v5_codex_record_apply",
        "session_id_required": True,
        "topic_id": topic_id,
        "claim_id": claim_id,
        "run_id": run_id,
        "actions": actions,
        "action_count": len(actions),
        "validation_semantics": validation_semantics,
        "trust_policy": {
            "can_update_claim_trust": False,
            "trust_promotion_allowed": False,
            "promotion_requires_trust_preflight_and_human_gate": True,
            "quiet_checkpoint_is_not_evidence": True,
            "validation_result_is_not_claim_support_by_itself": True,
        },
    }


def _validation_semantics(
    *,
    artifact_candidates: list[dict[str, Any]],
    validation_commands: list[Any],
    claim_boundary: dict[str, Any],
) -> dict[str, Any]:
    command_text = " ".join(str(command).lower() for command in validation_commands)
    artifact_text = " ".join(str(item.get("uri") or "") for item in artifact_candidates).lower()
    is_document_build = any(token in command_text for token in ("pdflatex", "xelatex", "lualatex", "tectonic")) or any(
        artifact_text.endswith(ext) or ext in artifact_text for ext in (".tex", ".pdf")
    )
    if is_document_build:
        return {
            "target": "generated note artifact",
            "tool_family": "codex_document_build",
            "tool_name": "latex_pdf_note_validation",
            "recipe_purpose": "Reproduce the LaTeX note build, log scan, and selected PDF visual spot-check.",
            "required_checks": [
                "latex_compile_succeeds",
                "log_scan_has_no_fatal_error_undefined_reference_or_overfull_issue",
                "selected_pdf_pages_render_and_are_visually_spot_checked",
            ],
            "failure_modes": [
                "latex_compile_failure",
                "log_error_or_undefined_reference",
                "pdf_render_or_layout_regression",
            ],
            "required_evidence_outputs": ["document_build_and_layout_validation"],
            "checked_outputs": ["document_build_and_layout_validation"],
            "status": "passed",
            "validator_role": "document_build_reviewer",
            "boundary": {
                "validates": "document build and selected-page layout only",
                "does_not_validate": "underlying physics claim",
                "does_not_promote_claim_trust": True,
                "claim_boundary": claim_boundary,
            },
            "result_summary": (
                "Document build/layout validation passed for the generated note artifact. "
                "This validates compilation, log hygiene, and selected rendered pages only; "
                "it does not validate the underlying physics claim or promote trust."
            ),
            "invariants": [
                "validation_result covers document build/layout only",
                "validation_result is not evidence for the physics claim by itself",
                "claim trust promotion requires separate trust preflight and human gate",
            ],
        }
    return {
        "target": "reported generated artifact or run output",
        "tool_family": "codex_validation",
        "tool_name": "reported_validation_commands",
        "recipe_purpose": "Reproduce the reported validation commands and preserve their boundary.",
        "required_checks": [str(command) for command in validation_commands] or ["explicit_validation_boundary_review"],
        "failure_modes": ["reported_validation_failure", "incomplete_validation_boundary"],
        "required_evidence_outputs": ["reported_validation_boundary"],
        "checked_outputs": ["reported_validation_boundary"],
        "status": "partial" if _has_open_gap(claim_boundary, []) else "passed",
        "validator_role": "validation_boundary_reviewer",
        "boundary": {
            "validates": "reported command outcomes only",
            "does_not_promote_claim_trust": True,
            "claim_boundary": claim_boundary,
        },
        "result_summary": (
            "Reported validation commands were recorded with their explicit boundary. "
            "This result does not promote claim trust by itself."
        ),
        "invariants": [
            "validation_result covers only the stated checks",
            "claim trust promotion requires separate trust preflight and human gate",
        ],
    }


def _recipe_id_for_closeout(run_id: str, validation_commands: list[Any]) -> str:
    kind = "document-build" if any("latex" in str(command).lower() for command in validation_commands) else "closeout"
    return f"codex-{kind}-{_safe_slug(run_id, 48)}"


def _safe_slug(value: str, limit: int) -> str:
    text = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value or "").strip()).strip(".-").lower()
    return (text or "run")[:limit]


def _infer_worktree_path(artifact_candidates: list[dict[str, Any]]) -> str:
    for candidate in artifact_candidates:
        repo_path = str(candidate.get("repo_path") or "").strip()
        if repo_path:
            return repo_path
    return ""


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


def _tool_run_need(
    *,
    inputs: list[Any],
    outputs: list[Any],
    validation_commands: list[Any],
    tool_run_specs: list[Any],
) -> dict[str, Any]:
    triggers: list[str] = []
    if tool_run_specs:
        triggers.append("tool_run_specs_present")
    if validation_commands:
        triggers.append("validation_commands_present")
    if inputs:
        triggers.append("inputs_reported")
    if outputs:
        triggers.append("outputs_reported")
    if not triggers:
        return {"needed": False, "reason": "", "triggers": []}
    return {
        "needed": True,
        "reason": "inputs, outputs, or validation commands imply a reproducible tool execution that should be captured as a typed tool_run",
        "triggers": _dedupe(triggers),
    }


def _source_asset_need(
    *,
    source_specs: list[Any],
    artifact_candidates: list[dict[str, Any]],
    tool_run_needed: bool,
) -> dict[str, Any]:
    if source_specs:
        return {
            "needed": True,
            "reason": "source asset specs are present but no source_asset record is written yet",
            "canonical_provenance": [item for item in source_specs if isinstance(item, dict)],
        }
    data_candidates = [
        candidate
        for candidate in artifact_candidates
        if candidate.get("artifact_type") in {"data_output", "dataset", "result_json"}
    ]
    if data_candidates and tool_run_needed:
        return {
            "needed": True,
            "reason": "data outputs from a tool-like run should have a canonical source_asset or dataset identity before evidence/trust use",
            "canonical_provenance": data_candidates,
        }
    return {"needed": False, "reason": "", "canonical_provenance": []}


def _sensemaking_need(claim_boundary: dict[str, Any], next_blockers: list[Any]) -> dict[str, Any]:
    boundary_refs = _matching_boundary_strings(claim_boundary, OPEN_GAP_TOKENS)
    boundary_refs.extend(str(blocker) for blocker in next_blockers)
    boundary_refs = _dedupe(boundary_refs)
    if not boundary_refs:
        return {"needed": False, "reason": "", "boundary_refs": []}
    return {
        "needed": True,
        "reason": "claim boundaries or blockers should be preserved as sensemaking before they are reused across sessions",
        "boundary_refs": boundary_refs,
    }


def _expected_record_slots(
    *,
    artifact_candidates: list[dict[str, Any]],
    tool_run_needed: bool,
    source_asset_needed: bool,
    code_state_needed: bool,
    validation_needed: bool,
    sensemaking_needed: bool,
) -> list[str]:
    slots: list[str] = []
    if artifact_candidates:
        slots.append("artifact")
    if tool_run_needed:
        slots.extend(["tool_recipe", "tool_run"])
    if source_asset_needed:
        slots.append("source_asset")
    if code_state_needed:
        slots.append("code_state")
    if validation_needed:
        slots.append("validation_result")
    if sensemaking_needed:
        slots.append("sensemaking_report")
    return _dedupe(slots)


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
    if slot == "tool_recipe":
        return "register tool_recipe"
    if slot == "tool_run":
        return "record tool_run"
    if slot == "source_asset":
        return "register source_asset"
    if slot == "code_state":
        return "capture code_state"
    if slot == "validation_result":
        return "record validation_result/gap"
    if slot == "sensemaking_report":
        return "record sensemaking_report"
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
