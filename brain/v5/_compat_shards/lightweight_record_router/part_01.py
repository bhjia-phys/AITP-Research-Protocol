# Compatibility shard 1 for lightweight_record_router.
from __future__ import annotations

import re

from typing import Any

from brain.v5.models import ClaimRecord

from brain.v5.record_refs import lookup_record_refs

from brain.v5.store import list_records

from brain.v5.workspace import WorkspacePaths

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

_ACCEPTED_REF_KINDS = {
    "artifact",
    "tool_run",
    "evidence",
    "validation_result",
    "reference_location",
    "code_state",
}

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

def _lower(summary: str) -> str:
    return (summary or "").lower()

def _contains_any(text_lower: str, keywords: list[str]) -> bool:
    """Substring match for multi-char / non-Latin keywords (safe — e.g. 日志, matplotlib, oom)."""

    return any(kw in text_lower for kw in keywords)

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

def _looks_like_windows_path(value: str) -> bool:
    return bool(re.match(r"^[a-zA-Z]:[\\/]", value or ""))

def _looks_like_local_file_reference(value: str) -> bool:
    lowered = (value or "").strip().lower()
    if lowered.startswith("file://"):
        return True
    for prefix in ("local:file:", "file:", "path:"):
        if lowered.startswith(prefix):
            rest = value[len(prefix) :].strip()
            return bool(rest.startswith(("/", "\\")) or _looks_like_windows_path(rest))
    return False

def _normalize_local_file_reference(value: str) -> str:
    text = (value or "").strip()
    lowered = text.lower()
    for prefix in ("local:file:", "file:", "path:"):
        if lowered.startswith(prefix) and not lowered.startswith("file://"):
            rest = text[len(prefix) :].strip()
            if _looks_like_windows_path(rest) or rest.startswith(("/", "\\")):
                return rest.replace("\\", "/")
    return text

def _looks_like_ref_like_token(value: str) -> bool:
    """Detect unsupported ``kind:id``-style refs without catching paths/URLs."""

    if not value or _looks_like_windows_path(value) or _looks_like_local_file_reference(value) or "://" in value:
        return False
    parsed = _split_ref(value)
    if parsed is None:
        return False
    kind, _ = parsed
    return bool(re.match(r"^[a-z_][a-z0-9_]*$", kind))

def _classify_touched(value: str) -> dict[str, str]:
    """Classify one ``touched_files_or_artifacts`` entry.

    Returns a dict with ``kind`` in {canonical_ref, ref_like, path, other} and
    the raw value. ``ref_like`` is for unsupported ``kind:id``-style tokens that
    should be diagnosed rather than silently treated as ordinary prose.
    """

    value = (value or "").strip()
    if not value:
        return {"kind": "other", "value": value}
    if _looks_like_local_file_reference(value):
        return {"kind": "path", "value": _normalize_local_file_reference(value)}
    if _looks_like_canonical_ref(value):
        return {"kind": "canonical_ref", "value": value}
    if _looks_like_ref_like_token(value):
        return {"kind": "ref_like", "value": value}
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

def _topic_claims(ws: WorkspacePaths, topic_id: str) -> list[ClaimRecord]:
    try:
        claims = list_records(ws.registry_dir("claims"), ClaimRecord)
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
