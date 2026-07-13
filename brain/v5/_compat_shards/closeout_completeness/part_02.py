# Compatibility shard 2 for closeout_completeness.
from __future__ import annotations

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
