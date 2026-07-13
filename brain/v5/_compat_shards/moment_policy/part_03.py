# Compatibility shard 3 for moment_policy.
from __future__ import annotations

def _derivation_backtrace_questions(action_kind: str, record: dict[str, Any]) -> list[str]:
    values = _string_list(record.get("derivation_backtrace_questions"))
    if values:
        return values
    if "source" in action_kind or "backtrace" in action_kind:
        return ["Which derivation step should be traced back to first principles or assumptions?"]
    return []

def _source_dependency_questions(action_kind: str, record: dict[str, Any]) -> list[str]:
    values = _string_list(record.get("source_dependency_questions"))
    if values:
        return values
    if "source" in action_kind or "backtrace" in action_kind:
        return ["Which paper, lecture note, theorem, or technique must be followed before this concept is clear?"]
    return []

def _original_question_guard(record: dict[str, Any]) -> list[str]:
    values = _string_list(record.get("original_question_guard"))
    if values:
        return values
    original = str(record.get("original_question") or "")
    local = str(record.get("local_question") or "")
    if original and local:
        return [f"Keep local question '{local}' tied to original question '{original}'."]
    return []

def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return []

def _placeholder(label: str) -> str:
    return f"<{label}>"

def _clean_mapping(value: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in value.items():
        if item == "" or item == [] or item == {}:
            continue
        result[key] = item
    return result

def _entrypoints(
    record_entrypoints: list[str],
    exploration_entrypoints: list[str],
    required_before_trust_change: list[str],
) -> list[str]:
    result: list[str] = []
    for value in [*record_entrypoints, *exploration_entrypoints]:
        if value and value not in result:
            result.append(value)
    if any("aitp_v5_preflight_trust_update" in value for value in required_before_trust_change):
        result.append("aitp_v5_preflight_trust_update")
    return result
