# Compatibility shard 3 for closeout_completeness.
from __future__ import annotations

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
