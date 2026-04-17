from __future__ import annotations

from typing import Any

_NODE_SPECS: dict[str, dict[str, str]] = {
    "L0": {
        "macro_layer": "L0",
        "role": "source_recovery",
        "summary": "Recover cited definitions, derivations, and prior-work context before continuing.",
    },
    "L1": {
        "macro_layer": "L1",
        "role": "intake_and_assumption_tracking",
        "summary": "Record source-backed assumptions, regimes, notation, and ambiguity honestly.",
    },
    "L3-I": {
        "macro_layer": "L3",
        "role": "ideation",
        "summary": "Record, connect, and refine vague ideas before they become formal candidates.",
    },
    "L3-P": {
        "macro_layer": "L3",
        "role": "planning",
        "summary": "Translate ideas into executable research plans with steps, tools, and checkpoints.",
    },
    "L3-A": {
        "macro_layer": "L3",
        "role": "analysis",
        "summary": "Execute plans, form formal candidates with explicit claims and supporting derivation.",
    },
    "L3-R": {
        "macro_layer": "L3",
        "role": "result_integration",
        "summary": "Interpret L4 returns, explain validation outcomes, and decide what to do with failures.",
    },
    "L3-D": {
        "macro_layer": "L3",
        "role": "distillation_preparation",
        "summary": "Prepare reusable distillation after validation without bypassing the return law.",
    },
    "L4": {
        "macro_layer": "L4",
        "role": "validation",
        "summary": "Validate, adjudicate, and classify bounded claims against durable evidence.",
    },
    "L2": {
        "macro_layer": "L2",
        "role": "reusable_memory",
        "summary": "Consult or write reusable knowledge under explicit trust gates.",
    },
}

_EDGE_SPECS: list[dict[str, str]] = [
    {
        "from_node": "L0",
        "to_node": "L1",
        "edge_kind": "forward",
        "summary": "Move from gathered sources into provisional understanding.",
    },
    {
        "from_node": "L1",
        "to_node": "L0",
        "edge_kind": "backedge",
        "summary": "Recover missing sources or prior-work anchors before smoothing the narrative.",
    },
    {
        "from_node": "L1",
        "to_node": "L3-I",
        "edge_kind": "forward",
        "summary": "Record an idea from source-backed understanding.",
    },
    {
        "from_node": "L3-I",
        "to_node": "L3-P",
        "edge_kind": "forward",
        "summary": "Translate a refined idea into an executable research plan.",
    },
    {
        "from_node": "L3-I",
        "to_node": "L2",
        "edge_kind": "consultation",
        "summary": "Compare idea with L2 knowledge to assess novelty.",
    },
    {
        "from_node": "L3-P",
        "to_node": "L3-A",
        "edge_kind": "forward",
        "summary": "Begin executing the plan to form a formal candidate.",
    },
    {
        "from_node": "L3-P",
        "to_node": "L3-I",
        "edge_kind": "backedge",
        "summary": "Replan reveals the idea needs refinement.",
    },
    {
        "from_node": "L3-A",
        "to_node": "L4",
        "edge_kind": "forward",
        "summary": "Send a concrete candidate into bounded validation.",
    },
    {
        "from_node": "L3-A",
        "to_node": "L0",
        "edge_kind": "backedge",
        "summary": "Return for cited recovery when the candidate still hides source gaps.",
    },
    {
        "from_node": "L3-A",
        "to_node": "L2",
        "edge_kind": "consultation",
        "summary": "Consult compiled knowledge without treating consultation as promotion.",
    },
    {
        "from_node": "L3-A",
        "to_node": "L3-P",
        "edge_kind": "backedge",
        "summary": "Analysis reveals the plan needs adjustment.",
    },
    {
        "from_node": "L4",
        "to_node": "L3-R",
        "edge_kind": "mandatory_return",
        "summary": "Validation returns through result integration before reusable distillation.",
    },
    {
        "from_node": "L4",
        "to_node": "L0",
        "edge_kind": "backedge",
        "summary": "Recover missing sources or prior-work comparisons exposed by validation.",
    },
    {
        "from_node": "L4",
        "to_node": "L2",
        "edge_kind": "consultation",
        "summary": "Consult reusable knowledge during validation without making writeback claims.",
    },
    {
        "from_node": "L3-R",
        "to_node": "L3-D",
        "edge_kind": "forward",
        "summary": "Convert an integrated result into reusable distillation candidates.",
    },
    {
        "from_node": "L3-R",
        "to_node": "L4",
        "edge_kind": "iterate",
        "summary": "Re-enter bounded validation after interpreting the returned result honestly.",
    },
    {
        "from_node": "L3-R",
        "to_node": "L3-A",
        "edge_kind": "iterate",
        "summary": "Return to analysis to revise the candidate based on validation feedback.",
    },
    {
        "from_node": "L3-R",
        "to_node": "L0",
        "edge_kind": "backedge",
        "summary": "Return for source recovery if the returned result exposes missing inputs.",
    },
    {
        "from_node": "L3-R",
        "to_node": "L2",
        "edge_kind": "consultation",
        "summary": "Consult reusable knowledge while interpreting returned validation evidence.",
    },
    {
        "from_node": "L3-D",
        "to_node": "L2",
        "edge_kind": "distillation",
        "summary": "Cross the reusable-memory boundary only after result integration has happened.",
    },
    {
        "from_node": "L3-D",
        "to_node": "L4",
        "edge_kind": "iterate",
        "summary": "Return to validation if distillation uncovers unresolved proof or execution debt.",
    },
    {
        "from_node": "L3-D",
        "to_node": "L0",
        "edge_kind": "backedge",
        "summary": "Return for source recovery when distillation still hides cited gaps.",
    },
    {
        "from_node": "L2",
        "to_node": "L3-I",
        "edge_kind": "reuse_return",
        "summary": "Reusable knowledge can seed a new idea without becoming the whole topic.",
    },
    {
        "from_node": "L2",
        "to_node": "L3-A",
        "edge_kind": "reuse_return",
        "summary": "Reusable knowledge can seed a new bounded candidate without becoming the whole topic.",
    },
]

_NEXT_NODE_SEQUENCE: dict[str, list[str]] = {
    "L0": ["L1"],
    "L1": ["L3-I", "L0"],
    "L3-I": ["L3-P", "L2"],
    "L3-P": ["L3-A", "L3-I"],
    "L3-A": ["L4", "L0", "L2", "L3-P"],
    "L3-R": ["L3-D", "L4", "L3-A", "L0", "L2"],
    "L3-D": ["L2", "L4", "L0"],
    "L4": ["L3-R", "L0", "L2"],
    "L2": ["L3-I", "L3-A"],
}

_PROMOTION_STATUSES = {"ready", "promotion_ready", "ready_for_promotion", "promoted"}
_RETURN_EVIDENCE_KINDS = {"result_manifest", "validation_review_bundle", "returned_execution_result"}


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped


def _joined_signal_text(*values: Any) -> str:
    return " ".join(str(value or "").strip().lower() for value in values if str(value or "").strip())


def _current_macro_layer(topic_state: dict[str, Any], runtime_focus: dict[str, Any]) -> str:
    layer = str(
        topic_state.get("resume_stage")
        or runtime_focus.get("resume_stage")
        or topic_state.get("last_materialized_stage")
        or runtime_focus.get("last_materialized_stage")
        or "L1"
    ).strip()
    return layer if layer in {"L0", "L1", "L2", "L3", "L4"} else "L1"


def _infer_current_node_id(
    *,
    current_macro_layer: str,
    topic_state: dict[str, Any],
    runtime_focus: dict[str, Any],
    runtime_mode_payload: dict[str, Any],
    promotion_readiness: dict[str, Any],
    validation_review_bundle: dict[str, Any],
) -> str:
    if current_macro_layer != "L3":
        return current_macro_layer

    runtime_mode = str(runtime_mode_payload.get("runtime_mode") or "").strip()
    transition = runtime_mode_payload.get("transition_posture") or {}
    last_materialized_stage = str(
        topic_state.get("last_materialized_stage")
        or runtime_focus.get("last_materialized_stage")
        or ""
    ).strip()
    promotion_status = str(promotion_readiness.get("status") or "").strip().lower().replace("-", "_")
    validation_status = str(validation_review_bundle.get("status") or "").strip().lower().replace("-", "_")
    last_evidence_kind = str(runtime_focus.get("last_evidence_kind") or "").strip()
    next_action_summary = str(runtime_focus.get("next_action_summary") or "").strip()
    transition_reason = str(transition.get("transition_reason") or "").strip()

    signal_text = _joined_signal_text(
        next_action_summary,
        transition_reason,
        promotion_status,
        validation_status,
        last_evidence_kind,
    )

    if (
        runtime_mode == "promote"
        or promotion_status in _PROMOTION_STATUSES
        or "writeback" in signal_text
        or "promot" in signal_text
        or "prepare the candidate for bounded layer 2" in signal_text
        or "promotion boundary" in signal_text
    ):
        return "L3-D"

    if (
        last_materialized_stage == "L4"
        or last_evidence_kind in _RETURN_EVIDENCE_KINDS
        or "returned result" in signal_text
        or "integrat" in signal_text
        or "proof review" in signal_text
        or validation_status in {"revise", "returned", "needs_revision", "ready_for_promotion"}
    ):
        return "L3-R"

    return "L3-A"


def _node_status(
    *,
    node_id: str,
    current_node_id: str,
    last_materialized_stage: str,
    semantic_next_nodes: list[str],
) -> str:
    if node_id == current_node_id:
        return "current"
    if node_id in semantic_next_nodes:
        return "reachable"
    if node_id == last_materialized_stage:
        return "recent"
    return "inactive"


def _edge_status(
    *,
    edge: dict[str, str],
    current_node_id: str,
    last_materialized_stage: str,
    semantic_next_nodes: list[str],
    available_macro_targets: list[str],
) -> str:
    if edge["edge_kind"] == "mandatory_return" and last_materialized_stage == "L4":
        if current_node_id in {"L4", "L3-R"}:
            return "required"
    if edge["from_node"] != current_node_id:
        return "inactive"
    if edge["to_node"] in semantic_next_nodes:
        return "available"
    target_macro = _NODE_SPECS[edge["to_node"]]["macro_layer"]
    if target_macro in available_macro_targets:
        return "available"
    return "inactive"


def build_layer_graph_payload(
    *,
    topic_slug: str,
    topic_state: dict[str, Any] | None,
    runtime_focus: dict[str, Any] | None,
    runtime_mode_payload: dict[str, Any] | None,
    promotion_readiness: dict[str, Any] | None,
    validation_review_bundle: dict[str, Any] | None,
) -> dict[str, Any]:
    topic_state = topic_state or {}
    runtime_focus = runtime_focus or {}
    runtime_mode_payload = runtime_mode_payload or {}
    promotion_readiness = promotion_readiness or {}
    validation_review_bundle = validation_review_bundle or {}

    current_macro_layer = _current_macro_layer(topic_state, runtime_focus)
    current_node_id = _infer_current_node_id(
        current_macro_layer=current_macro_layer,
        topic_state=topic_state,
        runtime_focus=runtime_focus,
        runtime_mode_payload=runtime_mode_payload,
        promotion_readiness=promotion_readiness,
        validation_review_bundle=validation_review_bundle,
    )
    current_node = {"node_id": current_node_id, **_NODE_SPECS[current_node_id]}
    semantic_next_nodes = list(_NEXT_NODE_SEQUENCE.get(current_node_id, []))
    transition = runtime_mode_payload.get("transition_posture") or {}
    available_macro_targets = _dedupe_preserve_order(
        [_NODE_SPECS[node_id]["macro_layer"] for node_id in semantic_next_nodes]
        + [str(item).strip() for item in (transition.get("allowed_targets") or []) if str(item).strip()]
    )
    last_materialized_stage = str(
        topic_state.get("last_materialized_stage")
        or runtime_focus.get("last_materialized_stage")
        or ""
    ).strip()

    nodes = [
        {
            "node_id": node_id,
            **node_spec,
            "status": _node_status(
                node_id=node_id,
                current_node_id=current_node_id,
                last_materialized_stage=last_materialized_stage,
                semantic_next_nodes=semantic_next_nodes,
            ),
        }
        for node_id, node_spec in _NODE_SPECS.items()
    ]
    edges = [
        {
            **edge,
            "from_macro_layer": _NODE_SPECS[edge["from_node"]]["macro_layer"],
            "to_macro_layer": _NODE_SPECS[edge["to_node"]]["macro_layer"],
            "status": _edge_status(
                edge=edge,
                current_node_id=current_node_id,
                last_materialized_stage=last_materialized_stage,
                semantic_next_nodes=semantic_next_nodes,
                available_macro_targets=available_macro_targets,
            ),
        }
        for edge in _EDGE_SPECS
    ]

    current_summary = {
        "L3-A": "The topic is actively comparing or refining bounded candidate routes before validation.",
        "L3-R": "The topic has returned from validation and is integrating the result before another pass or distillation.",
        "L3-D": "The topic is preparing reusable distillation at the L3/L2 boundary without skipping result integration.",
    }.get(current_node_id, current_node["summary"])

    return {
        "layer_graph_kind": "iterative_layer_graph",
        "topic_slug": topic_slug,
        "current_macro_layer": current_macro_layer,
        "last_materialized_stage": last_materialized_stage,
        "current_node_id": current_node_id,
        "current_node": current_node,
        "available_macro_targets": available_macro_targets,
        "available_next_nodes": semantic_next_nodes,
        "transition": {
            "transition_kind": str(transition.get("transition_kind") or "unspecified"),
            "transition_reason": str(transition.get("transition_reason") or ""),
            "allowed_targets": [str(item).strip() for item in (transition.get("allowed_targets") or []) if str(item).strip()],
        },
        "return_law": {
            "required_return_edge": "L4 -> L3-R",
            "required_return_node": "L3-R",
            "direct_l4_to_l2_promotion_allowed": False,
            "summary": "Validation does not write directly into reusable memory; results return through L3-R first.",
        },
        "current_summary": current_summary,
        "nodes": nodes,
        "edges": edges,
    }


def render_layer_graph_markdown(payload: dict[str, Any]) -> str:
    transition = payload.get("transition") or {}
    current_node = payload.get("current_node") or {}
    return_law = payload.get("return_law") or {}
    lines = [
        "# Layer graph",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Current macro layer: `{payload.get('current_macro_layer') or '(missing)'}`",
        f"- Current node: `{payload.get('current_node_id') or '(missing)'}`",
        f"- Current role: `{current_node.get('role') or '(missing)'}`",
        f"- Last materialized stage: `{payload.get('last_materialized_stage') or '(missing)'}`",
        "",
        payload.get("current_summary") or "(missing)",
        "",
        "## Return law",
        "",
        f"- Required return edge: `{return_law.get('required_return_edge') or '(missing)'}`",
        f"- Required return node: `{return_law.get('required_return_node') or '(missing)'}`",
        f"- Direct L4 to L2 promotion allowed: `{str(bool(return_law.get('direct_l4_to_l2_promotion_allowed'))).lower()}`",
        f"- Summary: {return_law.get('summary') or '(missing)'}",
        "",
        "## Available macro targets",
        "",
    ]
    for item in payload.get("available_macro_targets") or ["(none)"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Active transition",
            "",
            f"- Kind: `{transition.get('transition_kind') or '(missing)'}`",
            f"- Allowed targets: `{', '.join(transition.get('allowed_targets') or []) or '(none)'}`",
            f"- Reason: `{transition.get('transition_reason') or '(missing)'}`",
            "",
            "## Nodes",
            "",
        ]
    )
    for node in payload.get("nodes") or []:
        lines.append(
            f"- `{node.get('node_id') or '(missing)'}` macro=`{node.get('macro_layer') or '(missing)'}` "
            f"role=`{node.get('role') or '(missing)'}` status=`{node.get('status') or '(missing)'}`"
        )
        lines.append(f"  - {node.get('summary') or '(missing)'}")
    lines.extend(["", "## Edges", ""])
    for edge in payload.get("edges") or []:
        lines.append(
            f"- `{edge.get('from_node') or '(missing)'} -> {edge.get('to_node') or '(missing)'}` "
            f"kind=`{edge.get('edge_kind') or '(missing)'}` status=`{edge.get('status') or '(missing)'}`"
        )
        lines.append(f"  - {edge.get('summary') or '(missing)'}")
    return "\n".join(lines) + "\n"
