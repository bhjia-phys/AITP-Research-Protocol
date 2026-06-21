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

# Tokens that are too generic to discriminate target claim choice. These overlap
# tokens are ignored when scoring claim/event similarity so a high-overlap generic
# word like "validation"/"gap"/"report" cannot bias target selection toward whichever
# claim happens to share it.
_GENERIC_CLAIM_TOKENS = {
    "claim", "result", "figure", "plot", "evidence", "the", "a", "an",
    "of", "and", "or", "for", "to", "in", "on", "with", "is", "are",
    "not", "no", "that", "this", "we", "our", "be", "as", "at", "by",
    # domain-generic filler that inflates apparent overlap between any two physics
    # claims ("final report", "validation", "gap", ...). Downweighted so sibling
    # discrimination keys off the distinctive tokens instead.
    "gap", "validation", "final", "report", "result", "results", "open",
    "needs", "rerun", "has", "an", "the", "for", "that", "which",
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
    "matplotlib", "importerror", "module not found", "permission",
    "environment", "dependency", "runtime failure", "环境", "依赖",
    "远端环境", "timeout", "out of memory", "oom",
    # NOTE: bare "path" removed — too generic as a word ("go down this path").
    # NOTE: bare "缺少" removed — too generic ("缺少证明" just means "lacks proof").
    # Runtime/dependency failures carry matplotlib/environment/dependency/远端环境.
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
    """Substring match for multi-char / non-Latin keywords (safe — e.g. 日志, matplotlib, oom)."""

    return any(kw in text_lower for kw in keywords)


# Short English fragments that embed inside common words (log⊂logic, dat⊂update,
# table⊂acceptable, path⊂empathy, chart⊂chartreuse, dump⊂dumpling, report⊂reportedly,
# image⊂...). oom⊂room is a real false-positive caught in review. csv/npy/h5 etc. are
# fine as substrings in practice (rarely embedded in prose), but kept here defensively
# so future keyword additions are word-anchored by default for 3-letter tokens.
# These MUST be matched on word boundaries, never as substrings.
_WORD_BOUNDARY_KEYWORDS = {
    "log", "dat", "table", "path", "chart", "dump", "report", "image",
    "oom",
}


def _contains_any_word(text_lower: str, keywords: list[str]) -> bool:
    """Match short/ambiguous English keywords on word boundaries only.

    Multi-char / Chinese / distinctive keywords pass through to plain substring match.
    """

    for kw in keywords:
        if kw in _WORD_BOUNDARY_KEYWORDS:
            if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
                return True
        elif kw in text_lower:
            return True
    return False


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


def _claim_similarity(haystack_tokens: set[str], needle_tokens: set[str]) -> int:
    """Count overlapping discriminating tokens (generic words already filtered out)."""

    return len(haystack_tokens & needle_tokens)


def _choose_target_claim(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    event_summary: str,
    active_claim_id: str,
    target_claim_hint: str,
    artifact_claim_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Conservatively pick the target claim for the plan.

    Returns {"target_claim_id", "reason_for_target_claim", "confidence",
    "needs_human": bool}.
    Never mutates session binding.

    Selection is driven by unified scoring over discriminating tokens (generic
    words like gap/validation/final/report are downweighted), so an active claim is
    NOT preferred merely because it shares filler with the event. The best-scoring
    claim wins; near-ties between multiple claims return needs_human_target_claim.

    As a last resort, a confirmed artifact ref that already carries a claim_id can
    resolve the target (the artifact is durable provenance of which claim it belongs
    to), so an existing-artifact-only event does not lose provenance.
    """

    claims = _active_claims(_topic_claims(ws, topic_id))
    by_id = {c.claim_id: c for c in claims}

    # 1. explicit hint is an existing active claim id in this topic
    if target_claim_hint and target_claim_hint in by_id:
        return {
            "target_claim_id": target_claim_hint,
            "reason_for_target_claim": "target_claim_hint matched an active claim id in this topic",
            "confidence": "high",
            "needs_human": False,
        }

    # Build the needle token set: prefer an explicit hint fragment, else the event.
    if target_claim_hint:
        needle_tokens = _discriminating_tokens(target_claim_hint)
        needle_source = "target_claim_hint"
    else:
        needle_tokens = _discriminating_tokens(event_summary)
        needle_source = "event_summary"

    if not needle_tokens:
        # No distinctive text to match on. Fall back to a confirmed artifact ref's
        # own claim binding (durable provenance) before asking a human.
        if artifact_claim_map:
            for ref, claim_id in artifact_claim_map.items():
                if claim_id in by_id:
                    return {
                        "target_claim_id": claim_id,
                        "reason_for_target_claim": f"resolved from confirmed artifact ref {ref}",
                        "confidence": "high",
                        "needs_human": False,
                    }
        return {
            "target_claim_id": "",
            "reason_for_target_claim": f"no discriminating tokens in {needle_source}",
            "confidence": "low",
            "needs_human": True,
        }

    # 2. Score every active claim against the needle (uniformly — no active short-circuit).
    scored: list[tuple[int, ClaimRecord]] = []
    for c in claims:
        claim_tokens = (
            _discriminating_tokens(getattr(c, "statement", ""))
            | _discriminating_tokens(getattr(c, "active_uncertainty", ""))
        )
        overlap = _claim_similarity(claim_tokens, needle_tokens)
        if overlap:
            scored.append((overlap, c))

    if not scored:
        # No text overlap. Fall back to a confirmed artifact ref's claim binding.
        if artifact_claim_map:
            for ref, claim_id in artifact_claim_map.items():
                if claim_id in by_id:
                    return {
                        "target_claim_id": claim_id,
                        "reason_for_target_claim": f"resolved from confirmed artifact ref {ref}",
                        "confidence": "high",
                        "needs_human": False,
                    }
        return {
            "target_claim_id": "",
            "reason_for_target_claim": f"{needle_source} does not match any active claim",
            "confidence": "low",
            "needs_human": True,
        }

    scored.sort(key=lambda pair: pair[0], reverse=True)
    best_overlap, best = scored[0]
    # near-tie: any other claim within one token of the best -> ambiguous -> human
    near = [pair for pair in scored if pair[0] >= max(best_overlap - 1, 1)]
    if len(near) > 1:
        near_ids = ", ".join(pair[1].claim_id for pair in near)
        return {
            "target_claim_id": "",
            "reason_for_target_claim": f"multiple sibling claims match {needle_source} ambiguously: {near_ids}",
            "confidence": "low",
            "needs_human": True,
        }

    # Single clear winner.
    is_active = (best.claim_id == active_claim_id)
    if needle_source == "target_claim_hint":
        reason = "target_claim_hint matched a sibling claim statement"
    elif is_active:
        reason = "event_summary best matches the active claim statement/uncertainty"
    else:
        reason = "event_summary best matches a sibling claim, not the active claim"
    return {
        "target_claim_id": best.claim_id,
        "reason_for_target_claim": reason,
        "confidence": "high" if best_overlap >= 3 else "medium",
        "needs_human": False,
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
    return _contains_any_word(event_lower, _KW_DURABLE_OUTPUT)


def _wants_sensemaking(event_lower: str, touched: list[dict[str, str]]) -> bool:
    # _KW_RUNTIME_FAILURE contains the ambiguous "path" -> use word-boundary matching.
    # _KW_BOUNDARY / _KW_OLD_NEW_CONFLICT are safe substrings (multi-char or distinctive).
    return any(
        _contains_any(event_lower, bucket) for bucket in (_KW_BOUNDARY, _KW_OLD_NEW_CONFLICT)
    ) or _contains_any_word(event_lower, _KW_RUNTIME_FAILURE)


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
    return _contains_any_word(event_lower, _KW_RUNTIME_FAILURE)


def _has_tool_run_or_validation_ref(refs: list[str], confirmed_refs: set[str]) -> list[str]:
    """Return the subset of ``refs`` that are confirmed tool_run/validation_result records.

    Only refs that ``lookup_record_refs`` confirmed (status=found, record_confirmed=True)
    qualify. A bare ``tool_run:not-real`` is NOT verified evidence — it is dropped here,
    and the caller reports it via the unsupported path.
    """

    out = []
    for ref in refs:
        if ref not in confirmed_refs:
            continue
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
    extra_verification_refs: list[str] | None = None,
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
    extras = list(extra_verification_refs or [])
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
        "verification_refs": extras + ["sensemaking_report:<to-be-created>"],
        "recommended_mcp_tool": "aitp_v5_record_sensemaking_report",
        "execute_now": False,
    }


def _proof_obligation_plan(
    *,
    topic_id: str,
    target_claim_id: str,
    event_summary: str,
    extra_verification_refs: list[str] | None = None,
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
    extras = list(extra_verification_refs or [])
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
        "verification_refs": extras + ["proof_obligation:<to-be-created>"],
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
    extra_verification_refs: list[str] | None = None,
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
    extras = list(extra_verification_refs or [])
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
        # spec §4: preserve canonical input refs (tool_run:run-abc + existing artifact refs)
        # plus the to-be-created evidence ref
        "verification_refs": list(verified_refs) + extras + ["evidence:<to-be-created>"],
        "recommended_mcp_tool": "aitp_v5_record_evidence",
        "execute_now": False,
    }


def _trust_preflight_plan(
    *,
    topic_id: str,
    target_claim_id: str,
    current_session_id: str,
    event_summary: str,
    extra_verification_refs: list[str] | None = None,
) -> dict[str, Any]:
    extras = list(extra_verification_refs or [])
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
        "verification_refs": extras + ["trust_update_preflight:<to-be-created>"],
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
    confirmed_refs: set[str] = set()
    malformed_refs: list[str] = []
    unconfirmed_evidence_refs: list[str] = []  # tool_run/validation_result refs that don't confirm
    artifact_claim_map: dict[str, str] = {}  # artifact:<id> -> claim_id (from confirmed records)
    if ref_lookup is not None:
        for item in ref_lookup.get("refs", []):
            ref = item.get("ref", "")
            status = item.get("status")
            kind = item.get("ref_kind", "")
            if status == "found":
                confirmed_refs.add(ref)
                if kind == "artifact":
                    claim_from_record = str(item.get("claim_id", "") or "")
                    if claim_from_record:
                        artifact_claim_map[ref] = claim_from_record
            elif status == "malformed_ref":
                malformed_refs.append(ref)
            elif kind in {"tool_run", "validation_result"}:
                # not_found / unsupported_kind for an evidence-grade ref: cannot plan evidence
                unconfirmed_evidence_refs.append(ref)

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

    if unconfirmed_evidence_refs:
        return {
            "ok": True,
            "kind": "lightweight_record_write_plan",
            "decision": DECISION_UNSUPPORTED,
            "topic_id": topic_id,
            "current_session_id": current_session_id,
            "active_claim_id": active_claim_id,
            "target_claim": {
                "target_claim_id": "",
                "reason_for_target_claim": "unconfirmed evidence-grade ref",
                "confidence": "low",
            },
            "write_reasons": [],
            "no_write_reason": "",
            "selected_record_types": [],
            "typed_write_plan": [],
            "trust_boundary": dict(_TRUST_BOUNDARY),
            "final_human_readable_summary": (
                "Evidence-grade ref(s) did not resolve to a typed record, so no evidence "
                f"plan is produced and nothing is recorded: {unconfirmed_evidence_refs}. "
                "Create the tool_run/validation_result first, or supply a confirmed ref."
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

    verified_refs = _has_tool_run_or_validation_ref(touched_refs_raw + canonical_input_refs, confirmed_refs)
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
        artifact_claim_map=artifact_claim_map,
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

    # Existing canonical artifact refs are preserved as verification_refs on later
    # plan items (sensemaking/proof/evidence/trust) so provenance is not silently
    # dropped. They are NOT re-attached as a second artifact plan.
    existing_artifact_refs = [
        t["value"] for t in touched_files
        if t["kind"] == "canonical_ref" and t["value"] in confirmed_refs
        and _split_ref(t["value"])[0] == "artifact"
    ]
    path_entries = [t for t in touched_files if t["kind"] == "path"]

    if wants_artifact:
        # one artifact plan per path; canonical refs are preserved as verification
        # refs on later items, not re-attached as a second artifact plan.
        if path_entries:
            write_plan.append(_artifact_plan(
                topic_id=topic_id,
                target_claim_id=target_claim_id,
                event_summary=event_summary,
                touched_entry=path_entries[0],
            ))
            selected_types.append("artifact")

    if wants_sensemaking or is_runtime_failure or wants_negative:
        write_plan.append(_sensemaking_plan(
            topic_id=topic_id,
            target_claim_id=target_claim_id,
            event_summary=event_summary,
            is_runtime_failure=is_runtime_failure,
            is_boundary=_contains_any(event_lower, _KW_BOUNDARY) or _contains_any(event_lower, _KW_OLD_NEW_CONFLICT),
            extra_verification_refs=existing_artifact_refs,
        ))
        selected_types.append("sensemaking_report")

    if wants_gap:
        write_plan.append(_proof_obligation_plan(
            topic_id=topic_id,
            target_claim_id=target_claim_id,
            event_summary=event_summary,
            extra_verification_refs=existing_artifact_refs,
        ))
        selected_types.append("proof_obligation")

    if wants_evidence:
        write_plan.append(_evidence_plan(
            topic_id=topic_id,
            target_claim_id=target_claim_id,
            event_summary=event_summary,
            verified_refs=verified_refs,
            negative=wants_negative,
            extra_verification_refs=existing_artifact_refs,
        ))
        selected_types.append("evidence")

    if wants_trust:
        write_plan.append(_trust_preflight_plan(
            topic_id=topic_id,
            target_claim_id=target_claim_id,
            current_session_id=current_session_id,
            event_summary=event_summary,
            extra_verification_refs=existing_artifact_refs,
        ))
        selected_types.append("trust_preflight")

    # dedupe selected_types while preserving order
    seen: set[str] = set()
    selected_types = [t for t in selected_types if not (t in seen or seen.add(t))]

    if not write_plan:
        # No concrete write was selected. If the only durable signal was an existing
        # canonical artifact ref (no path to attach, no other trigger), do not drop its
        # provenance: return a minimal orientation plan that carries the ref forward.
        if existing_artifact_refs and not path_entries:
            orient = _sensemaking_plan(
                topic_id=topic_id,
                target_claim_id=target_claim_id,
                event_summary=event_summary,
                is_runtime_failure=False,
                is_boundary=False,
                extra_verification_refs=existing_artifact_refs,
            )
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
                "write_reasons": ["existing_artifact_ref_preserved"],
                "no_write_reason": "",
                "selected_record_types": ["sensemaking_report"],
                "typed_write_plan": [orient],
                "trust_boundary": dict(_TRUST_BOUNDARY),
                "final_human_readable_summary": (
                    "Only an existing artifact ref was provided (nothing new to attach); "
                    "preserving it on a minimal orientation sensemaking plan. "
                    "No claim trust changed."
                ),
                **_TOP_LEVEL_TRUTH,
            }
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
