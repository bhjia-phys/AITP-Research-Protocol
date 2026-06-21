"""Lightweight record router — plan-only surface for short research events.

This surface reads typed records and a short event summary, then returns a
*typed write plan*. It never writes records and never applies trust updates.

Hard trust boundaries (enforced everywhere, including the contract):
- ``can_update_claim_trust`` is always False
- ``summary_inputs_trusted`` is always False
- ``orientation_only`` is always True
- the relation-map may be consulted for *locating* a claim, never as evidence
- runtime failure is recorded as runtime/environment failure, never auto-judged
  as an algorithm failure
- an old plot/old convention is never promoted to new-report evidence
- mentioning a claim in ``event_summary`` does not raise its confidence
- when one ``sensemaking_report`` is enough, the plan is minimal — do not split
  into five redundant records
"""

from __future__ import annotations

import re
from typing import Any

from brain.v5.models import ClaimRecord
from brain.v5.record_refs import lookup_record_refs
from brain.v5.store import list_valid_records
from brain.v5.workspace import WorkspacePaths


# --------------------------------------------------------------------------- #
# Trust-boundary constants (these never change for this surface)
# --------------------------------------------------------------------------- #

_TRUST_BOUNDARY = {
    "can_update_claim_trust": False,
    "trust_update_requested": False,
    "trust_preflight_required": False,
    "forbidden_interpretations": [
        "relation_map_is_not_evidence",
        "runtime_failure_is_not_algorithm_failure",
        "old_plot_is_not_new_report_evidence",
        "event_summary_does_not_raise_confidence",
    ],
}

_TOP_LEVEL_TRUTH = {
    "truth_source": "event_metadata_and_typed_records",
    "summary_inputs_trusted": False,
    "orientation_only": True,
    "can_update_kernel_state": False,
    "can_update_claim_trust": False,
}

# Decisions returned by the router.
DECISION_NO_WRITE = "no_write"
DECISION_PLAN_WRITE = "plan_write"
DECISION_NEEDS_HUMAN = "needs_human_target_claim"
DECISION_UNSUPPORTED = "unsupported"

_VALID_DECISIONS = {
    DECISION_NO_WRITE,
    DECISION_PLAN_WRITE,
    DECISION_NEEDS_HUMAN,
    DECISION_UNSUPPORTED,
}

# Canonical ref kinds accepted as input (verified via record_refs lookup).
_ACCEPTED_REF_KINDS = {
    "artifact",
    "tool_run",
    "evidence",
    "validation_result",
    "reference_location",
    "code_state",
}

# Tokens that are too generic to discriminate target claim choice.
_GENERIC_CLAIM_TOKENS = {
    "claim", "result", "figure", "plot", "evidence", "the", "a", "an",
    "of", "and", "or", "for", "to", "in", "on", "with", "is", "are",
    "not", "no", "that", "this", "we", "our", "be", "as", "at", "by",
}

# Keyword buckets that drive write/no_write + record-type selection.
_KW_BOUNDARY = [
    "边界", "scope", "limitation", "cannot mix", "non-claim", "口径",
    "图表口径", "diagnostic lane", "boundary",
    # NOTE: "final lane" removed — too ambiguous (appears in gap descriptions too).
    # The diagnostic-vs-final lane boundary is better caught via explicit
    # "cannot mix" / "口径" phrasing.
]
_KW_OLD_NEW_CONFLICT = [
    "不能混用", "old plot", "old figure", "stale", "outdated",
    "legacy result", "old convention", "new convention",
    "contaminated", "not final evidence",
]
_KW_GAP = [
    "open gap", "validation gap", "proof gap", "missing check",
    "未验证", "缺少证明", "缺少复现", "missing validation", "missing proof",
]
_KW_NEGATIVE = [
    "negative result", "inconclusive", "failed physics",
    "undefined object", "未定义对象", "object undefined", "no solution",
]
_KW_NEXT_ACTION = [
    "next action", "reproduce", "rerun", "proof obligation",
    "validation contract needed", "下一步", "复现实验", "证明义务",
]
_KW_DURABLE_OUTPUT = [
    "figure", "plot", "chart", "image", "json", "log", "report",
    "notebook", "dump", "table", "csv", "dat", "npy", "h5", "hdf5",
    "日志",  # multi-char only; single-char 图/表 are too ambiguous as substrings
]
_KW_RUNTIME_FAILURE = [
    "matplotlib", "importerror", "module not found", "path", "permission",
    "environment", "dependency", "runtime failure", "环境", "依赖",
    "远端环境", "timeout", "out of memory", "oom",
    # NOTE: bare "缺少" removed — too generic ("缺少证明" just means "lacks proof").
    # Runtime/dependency failures carry "matplotlib"/"environment"/"dependency"/"远端环境".
]
_KW_TRUST_REQUEST = [
    "trust update", "confidence promotion", "promote confidence",
    "l2 promotion", "promote to l2", "set confidence", "提升置信度",
    "提升可信度",
]


# --------------------------------------------------------------------------- #
# Small text helpers
# --------------------------------------------------------------------------- #

def _lower(summary: str) -> str:
    return (summary or "").lower()


def _contains_any(text_lower: str, keywords: list[str]) -> bool:
    return any(kw in text_lower for kw in keywords)


def _tokenize(text: str) -> set[str]:
    return {tok for tok in re.split(r"[^a-z0-9]+", _lower(text)) if len(tok) > 2}


def _discriminating_tokens(text: str) -> set[str]:
    return {t for t in _tokenize(text) if t not in _GENERIC_CLAIM_TOKENS}


# --------------------------------------------------------------------------- #
# Ref normalization
# --------------------------------------------------------------------------- #

def _split_ref(ref: str) -> tuple[str, str] | None:
    """Return (kind, id) for a canonical 'kind:id' ref, or None if malformed."""

    ref = (ref or "").strip()
    if not ref or ":" not in ref:
        return None
    kind, _, rid = ref.partition(":")
    kind = kind.removeprefix("aitp:").strip().lower()
    rid = rid.strip()
    if not kind or not rid:
        return None
    return kind, rid


def _looks_like_canonical_ref(value: str) -> bool:
    parsed = _split_ref(value)
    return parsed is not None and parsed[0] in _ACCEPTED_REF_KINDS


def _classify_touched(value: str) -> dict[str, str]:
    """Classify one ``touched_files_or_artifacts`` entry.

    Returns a dict with ``kind`` in {canonical_ref, path, other} and the raw value.
    """

    value = (value or "").strip()
    if not value:
        return {"kind": "other", "value": value}
    if _looks_like_canonical_ref(value):
        return {"kind": "canonical_ref", "value": value}
    # treat anything with a slash or a dot extension as a path
    if "/" in value or "\\" in value or re.search(r"\.[a-z0-9]{1,5}$", value.lower()):
        return {"kind": "path", "value": value}
    return {"kind": "other", "value": value}


def _infer_artifact_type(path_or_name: str) -> str:
    name = path_or_name.lower()
    if name.endswith((".png", ".jpg", ".jpeg", ".svg")):
        return "plot"
    if name.endswith(".pdf"):
        return "report"
    if name.endswith(".jsonl"):
        return "jsonl_log"
    if name.endswith(".json"):
        return "result_json"
    if name.endswith((".log", ".out", ".err")):
        return "log"
    if name.endswith(".ipynb"):
        return "notebook"
    if name.endswith((".csv", ".tsv", ".dat", ".npy", ".h5", ".hdf5")):
        return "data"
    return "other"


# --------------------------------------------------------------------------- #
# Target claim selection
# --------------------------------------------------------------------------- #

def _topic_claims(ws: WorkspacePaths, topic_id: str) -> list[ClaimRecord]:
    try:
        claims = list_valid_records(ws.registry_dir("claims"), ClaimRecord)
    except Exception:
        return []
    return [c for c in claims if getattr(c, "topic_id", "") == topic_id]


def _active_claims(claims: list[ClaimRecord]) -> list[ClaimRecord]:
    return [
        c for c in claims
        if getattr(c, "lifecycle_status", "active") == "active"
    ]


def _choose_target_claim(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    event_summary: str,
    active_claim_id: str,
    target_claim_hint: str,
) -> dict[str, Any]:
    """Conservatively pick the target claim for the plan.

    Returns {"target_claim_id", "reason_for_target_claim", "confidence",
    "needs_human": bool}.
    Never mutates session binding.
    """

    claims = _active_claims(_topic_claims(ws, topic_id))
    by_id = {c.claim_id: c for c in claims}

    # 1. explicit hint is an existing claim id in this topic
    if target_claim_hint and target_claim_hint in by_id:
        return {
            "target_claim_id": target_claim_hint,
            "reason_for_target_claim": "target_claim_hint matched an active claim id in this topic",
            "confidence": "high",
            "needs_human": False,
        }

    # 2. hint is a statement fragment — scan siblings
    if target_claim_hint:
        hint_tokens = _discriminating_tokens(target_claim_hint)
        scored = []
        for c in claims:
            stmt_tokens = _discriminating_tokens(getattr(c, "statement", ""))
            overlap = len(hint_tokens & stmt_tokens)
            if overlap:
                scored.append((overlap, c))
        if scored:
            scored.sort(key=lambda pair: pair[0], reverse=True)
            best_overlap, best = scored[0]
            # multiple near-candidates -> ask human
            near = [pair for pair in scored if pair[0] >= max(best_overlap - 1, 1)]
            if len(near) > 1:
                return {
                    "target_claim_id": "",
                    "reason_for_target_claim": "multiple sibling claims match the hint ambiguously",
                    "confidence": "low",
                    "needs_human": True,
                }
            return {
                "target_claim_id": best.claim_id,
                "reason_for_target_claim": "target_claim_hint matched a sibling claim statement",
                "confidence": "high" if best_overlap >= 3 else "medium",
                "needs_human": False,
            }

    # 3. does event_summary match the active claim?
    summary_tokens = _discriminating_tokens(event_summary)
    if active_claim_id and active_claim_id in by_id:
        active = by_id[active_claim_id]
        active_tokens = (
            _discriminating_tokens(getattr(active, "statement", ""))
            | _discriminating_tokens(getattr(active, "active_uncertainty", ""))
        )
        overlap = summary_tokens & active_tokens
        if overlap:
            return {
                "target_claim_id": active.claim_id,
                "reason_for_target_claim": "event_summary matches the active claim statement/uncertainty",
                "confidence": "high" if len(overlap) >= 2 else "medium",
                "needs_human": False,
            }
        # 4. active claim does NOT match — suggest a sibling if one matches
        for c in claims:
            if c.claim_id == active_claim_id:
                continue
            sib_tokens = _discriminating_tokens(getattr(c, "statement", ""))
            if summary_tokens & sib_tokens:
                return {
                    "target_claim_id": c.claim_id,
                    "reason_for_target_claim": "event_summary matches a sibling claim, not the active claim",
                    "confidence": "medium",
                    "needs_human": False,
                }
        # no sibling matches either -> need human
        return {
            "target_claim_id": "",
            "reason_for_target_claim": "event_summary does not match the active claim or any sibling claim",
            "confidence": "low",
            "needs_human": True,
        }

    # 5. no hint and no active claim — need human
    return {
        "target_claim_id": "",
        "reason_for_target_claim": "no target_claim_hint and no usable active_claim_id",
        "confidence": "low",
        "needs_human": True,
    }


# --------------------------------------------------------------------------- #
# Record-type selection
# --------------------------------------------------------------------------- #

def _wants_artifact(
    event_lower: str,
    touched: list[dict[str, str]],
) -> bool:
    if any(t["kind"] in {"canonical_ref", "path"} for t in touched):
        return True
    return _contains_any(event_lower, _KW_DURABLE_OUTPUT)


def _wants_sensemaking(event_lower: str, touched: list[dict[str, str]]) -> bool:
    return any(
        _contains_any(event_lower, bucket)
        for bucket in (_KW_BOUNDARY, _KW_OLD_NEW_CONFLICT, _KW_RUNTIME_FAILURE)
    ) or any(t["kind"] == "path" and _contains_any(event_lower, _KW_OLD_NEW_CONFLICT) for t in touched)


def _wants_proof_obligation(event_lower: str) -> bool:
    return any(
        _contains_any(event_lower, bucket)
        for bucket in (_KW_GAP, _KW_NEXT_ACTION)
    )


def _wants_negative(event_lower: str) -> bool:
    return _contains_any(event_lower, _KW_NEGATIVE)


def _wants_trust(event_lower: str, risk_lower: str) -> bool:
    return _contains_any(event_lower, _KW_TRUST_REQUEST) or _contains_any(risk_lower, _KW_TRUST_REQUEST)


def _has_runtime_failure(event_lower: str) -> bool:
    return _contains_any(event_lower, _KW_RUNTIME_FAILURE)


def _has_tool_run_or_validation_ref(refs: list[str]) -> list[str]:
    out = []
    for ref in refs:
        parsed = _split_ref(ref)
        if parsed and parsed[0] in {"tool_run", "validation_result"}:
            out.append(ref)
    return out


# --------------------------------------------------------------------------- #
# Plan-item builders
# --------------------------------------------------------------------------- #

def _artifact_plan(
    *,
    topic_id: str,
    target_claim_id: str,
    event_summary: str,
    touched_entry: dict[str, str],
) -> dict[str, Any]:
    value = touched_entry["value"]
    if touched_entry["kind"] == "canonical_ref":
        kind, rid = _split_ref(value)  # type: ignore[assignment]
        return {
            "record_type": "artifact",
            "target_claim_id": target_claim_id,
            "summary": _compress(event_summary),
            "required_fields": {
                "topic_id": topic_id,
                "claim_id": target_claim_id,
                "artifact_type": _infer_artifact_type(rid),
                "uri": rid,
                "summary": _compress(event_summary),
            },
            "optional_fields": {
                "metadata": {
                    "status": "orientation_only_not_claim_trust",
                    "event_summary": event_summary,
                    "source": "lightweight_record_router",
                }
            },
            "verification_refs": [value],  # already canonical
            "recommended_mcp_tool": "aitp_v5_attach_artifact_auto",
            "execute_now": False,
        }
    # path entry -> plan a new artifact
    return {
        "record_type": "artifact",
        "target_claim_id": target_claim_id,
        "summary": _compress(event_summary),
        "required_fields": {
            "topic_id": topic_id,
            "claim_id": target_claim_id,
            "path": value,
            "artifact_type": _infer_artifact_type(value),
            "summary": _compress(event_summary),
        },
        "optional_fields": {
            "metadata": {
                "status": "orientation_only_not_claim_trust",
                "event_summary": event_summary,
                "router_reason": "durable_artifact_located",
            }
        },
        "verification_refs": ["artifact:<to-be-created>"],
        "recommended_mcp_tool": "aitp_v5_attach_artifact_auto",
        "execute_now": False,
    }


def _sensemaking_plan(
    *,
    topic_id: str,
    target_claim_id: str,
    event_summary: str,
    is_runtime_failure: bool,
    is_boundary: bool,
) -> dict[str, Any]:
    if is_runtime_failure:
        title = "Runtime/environment failure boundary (not algorithm failure)"
        summary = (
            f"{event_summary}\n\nThis is a runtime/environment failure, NOT an "
            "algorithm failure. It does not refute any claim."
        )
    elif is_boundary:
        title = "Lane/convention boundary note"
        summary = (
            f"{event_summary}\n\nThis is an orientation-only boundary/convention "
            "note. It is not evidence and does not change claim trust."
        )
    else:
        title = "Orientation-only sensemaking note"
        summary = event_summary
    return {
        "record_type": "sensemaking_report",
        "target_claim_id": target_claim_id,
        "summary": _compress(summary),
        "required_fields": {
            "topic_id": topic_id,
            "claim_id": target_claim_id,
            "title": title,
            "summary": summary,
        },
        "optional_fields": {
            "evidence_refs": [],
            "open_questions": [],
            "next_actions": [],
            "metadata": {"status": "orientation_only_not_claim_trust"},
        },
        "verification_refs": ["sensemaking_report:<to-be-created>"],
        "recommended_mcp_tool": "aitp_v5_record_sensemaking_report",
        "execute_now": False,
    }


def _proof_obligation_plan(
    *,
    topic_id: str,
    target_claim_id: str,
    event_summary: str,
) -> dict[str, Any]:
    event_lower = _lower(event_summary)
    if _contains_any(event_lower, _KW_GAP):
        obligation_type = "validation_gap"
    elif _contains_any(event_lower, ["reproduce", "rerun", "复现"]):
        obligation_type = "reproducibility_gap"
    elif _contains_any(event_lower, ["undefined", "未定义"]):
        obligation_type = "undefined_object_gap"
    else:
        obligation_type = "proof_gap"
    return {
        "record_type": "proof_obligation",
        "target_claim_id": target_claim_id,
        "summary": _compress(event_summary),
        "required_fields": {
            "topic_id": topic_id,
            "claim_id": target_claim_id,
            "statement": _compress(event_summary),
            "obligation_type": obligation_type,
            "status": "open",
            "maturity_level": "exploratory",
            "next_action": _compress(event_summary),
        },
        "optional_fields": {
            "required_evidence": [],
            "proof_strategy": [],
            "failure_modes": [],
            "source_refs": [],
            "evidence_refs": [],
            "artifact_ids": [],
            "metadata": {"status": "orientation_only_not_claim_trust"},
        },
        "verification_refs": ["proof_obligation:<to-be-created>"],
        "recommended_mcp_tool": "aitp_v5_create_proof_obligation",
        "execute_now": False,
    }


def _evidence_plan(
    *,
    topic_id: str,
    target_claim_id: str,
    event_summary: str,
    verified_refs: list[str],
    negative: bool,
) -> dict[str, Any]:
    tool_run_ids: list[str] = []
    validation_result_ids: list[str] = []
    for ref in verified_refs:
        kind, rid = _split_ref(ref)  # type: ignore[assignment]
        if kind == "tool_run":
            tool_run_ids.append(rid)
        elif kind == "validation_result":
            validation_result_ids.append(rid)
    if negative:
        evidence_type = "negative_result"
        status = "inconclusive"
    else:
        evidence_type = "tool_run" if tool_run_ids and not validation_result_ids else "validation_result"
        status = "supports"
    return {
        "record_type": "evidence",
        "target_claim_id": target_claim_id,
        "summary": _compress(event_summary),
        "required_fields": {
            "topic_id": topic_id,
            "claim_id": target_claim_id,
            "evidence_type": evidence_type,
            "status": status,
            "summary": _compress(event_summary),
        },
        "optional_fields": {
            "supports_outputs": [],
            "source_refs": [],
            "tool_run_ids": tool_run_ids,
            "validation_result_ids": validation_result_ids,
            "artifact_ids": [],
            "metadata": {
                "status": "orientation_only_not_claim_trust unless verified evidence is explicit"
            },
        },
        # spec §4: preserve canonical input refs (tool_run:run-abc) plus the to-be-created evidence ref
        "verification_refs": list(verified_refs) + ["evidence:<to-be-created>"],
        "recommended_mcp_tool": "aitp_v5_record_evidence",
        "execute_now": False,
    }


def _trust_preflight_plan(
    *,
    topic_id: str,
    target_claim_id: str,
    current_session_id: str,
    event_summary: str,
) -> dict[str, Any]:
    return {
        "record_type": "trust_preflight",
        "target_claim_id": target_claim_id,
        "summary": _compress(event_summary),
        "required_fields": {
            "action": "set_confidence",
            "session_id": current_session_id,
            "topic_id": topic_id,
            "claim_id": target_claim_id,
            "requested_state": "",
        },
        "optional_fields": {
            "source_kind": "typed_records",
            "source_ref": "",
            "evidence_refs": [],
            "code_state_ids": [],
            "rationale": "requested by event_summary; preflight only, not an approval",
        },
        "verification_refs": ["trust_update_preflight:<to-be-created>"],
        "recommended_mcp_tool": "aitp_v5_preflight_trust_update",
        "execute_now": False,
    }


# --------------------------------------------------------------------------- #
# Misc
# --------------------------------------------------------------------------- #

def _compress(text: str, limit: int = 240) -> str:
    text = (text or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text[:limit] + ("…" if len(text) > limit else "")


def _no_write_payload(
    *,
    topic_id: str,
    current_session_id: str,
    active_claim_id: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "ok": True,
        "kind": "lightweight_record_write_plan",
        "decision": DECISION_NO_WRITE,
        "topic_id": topic_id,
        "current_session_id": current_session_id,
        "active_claim_id": active_claim_id,
        "target_claim": {
            "target_claim_id": "",
            "reason_for_target_claim": "no target claim needed for no_write",
            "confidence": "low",
        },
        "write_reasons": [],
        "no_write_reason": reason,
        "selected_record_types": [],
        "typed_write_plan": [],
        "trust_boundary": dict(_TRUST_BOUNDARY),
        "final_human_readable_summary": (
            "No durable research event detected; nothing recorded, no claim changed."
        ),
        **_TOP_LEVEL_TRUTH,
    }


# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #

def plan_lightweight_record_write(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    current_session_id: str,
    event_summary: str,
    active_claim_id: str = "",
    target_claim_hint: str = "",
    touched_files_or_artifacts: list[str] | None = None,
    touched_tool_runs_or_evidence_refs: list[str] | None = None,
    risk_hint: str = "",
) -> dict[str, Any]:
    """Return a plan-only payload describing what records *would* be written.

    Reads typed records + the event summary; never writes anything; never
    applies trust. See module docstring for the hard trust boundaries.
    """

    if not topic_id or not current_session_id or not (event_summary or "").strip():
        return _no_write_payload(
            topic_id=topic_id,
            current_session_id=current_session_id,
            active_claim_id=active_claim_id,
            reason="missing_required_input_topic_session_or_event_summary",
        )

    event_lower = _lower(event_summary)
    risk_lower = _lower(risk_hint)

    touched_files = [
        _classify_touched(v) for v in (touched_files_or_artifacts or []) if (v or "").strip()
    ]
    touched_refs_raw = [v for v in (touched_tool_runs_or_evidence_refs or []) if (v or "").strip()]

    # validate canonical input refs via the existing read-only lookup
    canonical_input_refs = [t["value"] for t in touched_files if t["kind"] == "canonical_ref"]
    all_input_refs = canonical_input_refs + touched_refs_raw
    ref_lookup = lookup_record_refs(ws, all_input_refs) if all_input_refs else None
    malformed_refs = []
    if ref_lookup is not None:
        for item in ref_lookup.get("refs", []):
            if item.get("status") == "malformed_ref":
                malformed_refs.append(item.get("ref", ""))

    if malformed_refs:
        return {
            "ok": True,
            "kind": "lightweight_record_write_plan",
            "decision": DECISION_UNSUPPORTED,
            "topic_id": topic_id,
            "current_session_id": current_session_id,
            "active_claim_id": active_claim_id,
            "target_claim": {
                "target_claim_id": "",
                "reason_for_target_claim": "malformed input ref",
                "confidence": "low",
            },
            "write_reasons": [],
            "no_write_reason": "",
            "selected_record_types": [],
            "typed_write_plan": [],
            "trust_boundary": dict(_TRUST_BOUNDARY),
            "final_human_readable_summary": (
                f"Malformed input ref(s) rejected: {malformed_refs}. Nothing recorded."
            ),
            **_TOP_LEVEL_TRUTH,
        }

    # ---- decide write vs no_write -----------------------------------------
    wants_artifact = _wants_artifact(event_lower, touched_files)
    wants_sensemaking = _wants_sensemaking(event_lower, touched_files)
    wants_gap = _wants_proof_obligation(event_lower)
    wants_negative = _wants_negative(event_lower)
    wants_trust = _wants_trust(event_lower, risk_lower)
    is_runtime_failure = _has_runtime_failure(event_lower)

    verified_refs = _has_tool_run_or_validation_ref(touched_refs_raw + canonical_input_refs)
    wants_evidence = bool(verified_refs)

    any_trigger = any(
        [wants_artifact, wants_sensemaking, wants_gap, wants_negative, wants_evidence, wants_trust]
    )

    if not any_trigger:
        return _no_write_payload(
            topic_id=topic_id,
            current_session_id=current_session_id,
            active_claim_id=active_claim_id,
            reason="ordinary_chat_or_repeat_summary_without_durable_research_event",
        )

    # ---- target claim selection -------------------------------------------
    target = _choose_target_claim(
        ws,
        topic_id=topic_id,
        event_summary=event_summary,
        active_claim_id=active_claim_id,
        target_claim_hint=target_claim_hint,
    )
    target_claim_id = target["target_claim_id"]

    if not target_claim_id:
        # artifact-only without a claim still needs a claim binding (ArtifactRecord requires claim_id)
        reason = (
            "target claim unclear; artifact/sensemaking records require claim binding"
            if target.get("needs_human")
            else "target claim unclear"
        )
        return {
            "ok": True,
            "kind": "lightweight_record_write_plan",
            "decision": DECISION_NEEDS_HUMAN,
            "topic_id": topic_id,
            "current_session_id": current_session_id,
            "active_claim_id": active_claim_id,
            "target_claim": {
                "target_claim_id": "",
                "reason_for_target_claim": target["reason_for_target_claim"],
                "confidence": target["confidence"],
            },
            "write_reasons": [],
            "no_write_reason": "",
            "selected_record_types": [],
            "typed_write_plan": [],
            "trust_boundary": dict(_TRUST_BOUNDARY),
            "final_human_readable_summary": (
                f"Needs human target-claim decision: {target['reason_for_target_claim']}. "
                "Nothing recorded."
            ),
            **_TOP_LEVEL_TRUTH,
        }

    # ---- build the typed write plan ---------------------------------------
    write_plan: list[dict[str, Any]] = []
    selected_types: list[str] = []

    if wants_artifact:
        # one artifact plan per path; canonical refs are folded in as verification refs, not re-attached
        path_entries = [t for t in touched_files if t["kind"] == "path"]
        if path_entries:
            write_plan.append(_artifact_plan(
                topic_id=topic_id,
                target_claim_id=target_claim_id,
                event_summary=event_summary,
                touched_entry=path_entries[0],
            ))
            selected_types.append("artifact")
        # canonical artifact refs are recorded as verification refs on later items, not re-attached

    if wants_sensemaking or is_runtime_failure or wants_negative:
        write_plan.append(_sensemaking_plan(
            topic_id=topic_id,
            target_claim_id=target_claim_id,
            event_summary=event_summary,
            is_runtime_failure=is_runtime_failure,
            is_boundary=_contains_any(event_lower, _KW_BOUNDARY) or _contains_any(event_lower, _KW_OLD_NEW_CONFLICT),
        ))
        selected_types.append("sensemaking_report")

    if wants_gap:
        write_plan.append(_proof_obligation_plan(
            topic_id=topic_id,
            target_claim_id=target_claim_id,
            event_summary=event_summary,
        ))
        selected_types.append("proof_obligation")

    if wants_evidence:
        write_plan.append(_evidence_plan(
            topic_id=topic_id,
            target_claim_id=target_claim_id,
            event_summary=event_summary,
            verified_refs=verified_refs,
            negative=wants_negative,
        ))
        selected_types.append("evidence")

    if wants_trust:
        write_plan.append(_trust_preflight_plan(
            topic_id=topic_id,
            target_claim_id=target_claim_id,
            current_session_id=current_session_id,
            event_summary=event_summary,
        ))
        selected_types.append("trust_preflight")

    # dedupe selected_types while preserving order
    seen: set[str] = set()
    selected_types = [t for t in selected_types if not (t in seen or seen.add(t))]

    if not write_plan:
        return _no_write_payload(
            topic_id=topic_id,
            current_session_id=current_session_id,
            active_claim_id=active_claim_id,
            reason="no_concrete_record_type_selected_after_routing",
        )

    write_reasons: list[str] = []
    if wants_artifact:
        write_reasons.append("durable_artifact_located")
    if wants_sensemaking:
        write_reasons.append("boundary_or_convention_clarification")
    if is_runtime_failure:
        write_reasons.append("runtime_failure_boundary_recorded_not_algorithm_failure")
    if wants_gap:
        write_reasons.append("open_gap_or_proof_obligation")
    if wants_evidence:
        write_reasons.append("verified_tool_run_or_validation_result_ref")
    if wants_negative:
        write_reasons.append("negative_result")
    if wants_trust:
        write_reasons.append("trust_preflight_requested_only")

    final_summary_parts = [
        f"Planned {len(write_plan)} record(s): {', '.join(selected_types)}.",
    ]
    if is_runtime_failure:
        final_summary_parts.append(
            "Runtime failure boundary recorded; NOT an algorithm failure, no claim refuted."
        )
    if wants_trust:
        final_summary_parts.append(
            "Trust preflight only; confidence NOT raised (requires passed validation)."
        )
    final_summary_parts.append("No claim trust changed; this is orientation-only.")

    return {
        "ok": True,
        "kind": "lightweight_record_write_plan",
        "decision": DECISION_PLAN_WRITE,
        "topic_id": topic_id,
        "current_session_id": current_session_id,
        "active_claim_id": active_claim_id,
        "target_claim": {
            "target_claim_id": target_claim_id,
            "reason_for_target_claim": target["reason_for_target_claim"],
            "confidence": target["confidence"],
        },
        "write_reasons": write_reasons,
        "no_write_reason": "",
        "selected_record_types": selected_types,
        "typed_write_plan": write_plan,
        "trust_boundary": dict(_TRUST_BOUNDARY),
        "final_human_readable_summary": " ".join(final_summary_parts),
        **_TOP_LEVEL_TRUTH,
    }
