# Compatibility shard 6 for process_graph.
from __future__ import annotations

def _obligation_severity(record: ProofObligationRecord) -> str:
    text = " ".join(
        [
            record.obligation_type,
            record.maturity_level,
            record.statement,
            record.next_action,
            " ".join(record.required_evidence),
        ]
    ).lower()
    if record.human_gate_required and any(
        token in text
        for token in ("validation", "human", "final", "promotion", "publish", "trust", "theorem", "proof_gap")
    ):
        return "blocking"
    if any(token in text for token in ("source", "proof", "derive", "definition", "failure", "limit")):
        return "recommended"
    return "advisory"

def _suggested_moments_for_obligation(record: ProofObligationRecord) -> list[str]:
    text = " ".join(
        [
            record.obligation_type,
            record.statement,
            record.next_action,
            " ".join(record.required_evidence),
            " ".join(record.source_refs),
        ]
    ).lower()
    result = ["aitp.create_open_obligation"]
    if any(token in text for token in ("source", "citation", "reference", "provenance")):
        result.append("trace.follow_source_dependency")
    if any(token in text for token in ("definition", "define", "term", "notation")):
        result.append("trace.reconstruct_definition")
    if any(token in text for token in ("relation", "bridge", "connect", "path")):
        result.append("physics.brainstorm_relation_path")
    return result

def _dedupe_moments(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for item in items:
        key = (item.get("moment"), item.get("target_type"), item.get("target_id"))
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result
