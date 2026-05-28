"""Claude Code hook bridge for AITP v5."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from brain.v5.brief import build_execution_brief
from brain.v5.hook_adapters import hook_decision_payload, hook_trace_event_payload
from brain.v5.hooks import decide_pre_tool_use, post_tool_use_trace_event
from brain.v5.policy import PolicyDecision, PolicyReason
from brain.v5.pretool_policy import context_policy_decision
from brain.v5.trace import persist_hook_trace_event
from brain.v5.workspace import get_session_binding, init_workspace
from brain.v5.workspace_refresh import refresh_workspace_startup_views


_AITP_MCP_ACTIONS = {
    "aitp_v5_record_code_state": "record_code_state",
    "aitp_v5_record_evidence": "record_evidence",
    "aitp_v5_record_tool_run": "record_tool_run",
    "aitp_v5_execute_tool": "execute_tool",
    "aitp_v5_register_tool_recipe": "register_tool_recipe",
    "aitp_v5_record_reference_location": "record_reference_location",
    "aitp_v5_record_physics_object": "record_physics_object",
    "aitp_v5_record_object_relation": "record_object_relation",
    "aitp_v5_record_sensemaking_report": "record_sensemaking_report",
    "aitp_v5_ingest_subagent_result": "ingest_subagent_result",
    "aitp_v5_apply_trust_update": "change_claim_confidence",
    "aitp_v5_create_promotion_packet": "create_promotion_packet",
    "aitp_v5_apply_promotion_packet": "apply_promotion_packet",
    "aitp_v5_request_human_checkpoint": "request_human_checkpoint",
    "aitp_v5_decide_human_checkpoint": "decide_human_checkpoint",
    "aitp_v5_create_validation_contract": "validate_claim",
    "aitp_v5_record_validation_result": "record_validation_result",
}
_TRUSTED_APPLY_SOURCE_KINDS = {
    "execution_brief",
    "typed_record",
    "typed_records",
    "evidence_record",
    "validation_record",
    "human_checkpoint",
}


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    claude_payload = _read_stdin_payload()
    payload = _dispatch(args, claude_payload)
    json.dump(payload, sys.stdout, ensure_ascii=True, sort_keys=True)
    sys.stdout.write("\n")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aitp-v5-claude-hook")
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--base", required=True)
    parent.add_argument("--session-id", required=True)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("session-start", parents=[parent])
    subparsers.add_parser("pre-tool", parents=[parent])
    subparsers.add_parser("post-tool", parents=[parent])
    return parser


def _dispatch(args: argparse.Namespace, claude_payload: dict) -> dict:
    if args.command == "session-start":
        ws = init_workspace(args.base)
        return _claude_continue({"aitp": refresh_workspace_startup_views(ws, session_id=args.session_id)})
    if args.command == "pre-tool":
        action = _action_from_claude_tool(claude_payload)
        policy_decision = _policy_from_claude_tool(
            action,
            claude_payload,
            base=args.base,
            session_id=args.session_id,
        )
        decision = decide_pre_tool_use(
            action=action,
            risk_level="guided",
            policy_decision=policy_decision,
        )
        return _claude_pre_tool_output(decision, action=action, policy_decision=policy_decision)
    if args.command == "post-tool":
        ws = init_workspace(args.base)
        binding = get_session_binding(ws, args.session_id)
        risk_level = _risk_level(ws, args.session_id)
        event = post_tool_use_trace_event(
            session_id=args.session_id,
            topic_id=binding.topic_id,
            risk_level=risk_level,
            claim_id=binding.active_claim,
            tool_name=str(claude_payload.get("tool_name") or "unknown"),
            evidence_status=_evidence_status(claude_payload),
        )
        hook_payload = hook_trace_event_payload(event, hook_name="post_tool")
        record = persist_hook_trace_event(ws, hook_payload)
        return _claude_continue({"aitp": record})
    raise SystemExit(f"unsupported Claude hook command: {args.command}")


def _read_stdin_payload() -> dict:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    payload = json.loads(raw)
    return payload if isinstance(payload, dict) else {}


def _action_from_claude_tool(payload: dict) -> str:
    tool_name = str(payload.get("tool_name") or "").lower()
    action = _action_from_aitp_mcp_tool(tool_name)
    if action:
        return action
    if tool_name == "bash":
        command = str((payload.get("tool_input") or {}).get("command") or "").lower()
        if any(token in command for token in ("rm -rf", "git reset --hard")):
            return "destructive_action"
        if any(token in command for token in ("ssh ", "scp ")):
            return "remote_execution"
        if any(token in command for token in ("sbatch", "qsub", "srun ")):
            return "expensive_compute"
    if tool_name in {"webfetch", "websearch"}:
        return "literature_or_web_tool_use"
    return "claude_tool_use"


def _action_from_aitp_mcp_tool(tool_name: str) -> str:
    for entrypoint, action in _AITP_MCP_ACTIONS.items():
        if entrypoint in tool_name:
            return action
    return ""


def _policy_from_claude_tool(
    action: str,
    payload: dict,
    *,
    base: str,
    session_id: str,
) -> PolicyDecision:
    if action == "change_claim_confidence" and not _has_trusted_apply_source(payload):
        return PolicyDecision(
            allowed=False,
            action=action,
            reasons=[
                PolicyReason(
                    policy_id="claude_pre_tool_requires_trust_preflight",
                    message="Direct trust application requires a typed preflight/source, not an unqualified tool call.",
                    severity="hard_block",
                )
            ],
            required_actions=["aitp_v5_preflight_trust_update"],
        )
    context_policy = _context_policy_from_workspace(action, payload, base=base, session_id=session_id)
    if context_policy is not None:
        return context_policy
    if action in {"destructive_action", "remote_execution", "expensive_compute"}:
        return PolicyDecision(
            allowed=False,
            action=action,
            reasons=[
                PolicyReason(
                    policy_id="claude_pre_tool_requires_human_checkpoint",
                    message="High-risk Claude tool use requires an explicit human checkpoint before execution.",
                    severity="block",
                )
            ],
            required_actions=["request_human_checkpoint"],
        )
    return PolicyDecision(allowed=True, action=action)


def _context_policy_from_workspace(
    action: str,
    payload: dict,
    *,
    base: str,
    session_id: str,
) -> PolicyDecision | None:
    if action not in {
        "record_code_state",
        "record_evidence",
        "record_tool_run",
        "execute_tool",
        "register_tool_recipe",
        "record_reference_location",
        "record_physics_object",
        "record_object_relation",
        "record_sensemaking_report",
        "ingest_subagent_result",
        "create_promotion_packet",
        "apply_promotion_packet",
        "request_human_checkpoint",
        "decide_human_checkpoint",
        "record_validation_result",
        "validate_claim",
        "promote_to_l2",
    }:
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_input = {}
    try:
        ws = init_workspace(base)
        claim_id = str(tool_input.get("claim_id") or tool_input.get("claim") or "").strip()
        return context_policy_decision(
            ws,
            session_id=session_id,
            action=action,
            claim_id=claim_id,
            code_state_ids=_input_list(tool_input, "code_state_ids"),
            evidence_refs=_input_list(tool_input, "evidence_refs"),
            validation_contract_ids=_input_list(tool_input, "validation_contract_ids"),
            tool_run_ids=_input_list(tool_input, "tool_run_ids"),
            validation_result_ids=_input_list(tool_input, "validation_result_ids"),
            known_failure_modes=_input_list(tool_input, "known_failure_modes"),
            recipe_id=str(tool_input.get("recipe_id") or tool_input.get("recipe") or ""),
            executor_id=str(tool_input.get("executor_id") or tool_input.get("executor") or ""),
            source_kind=str(tool_input.get("source_kind") or ""),
            source_ref=str(tool_input.get("source_ref") or ""),
            orientation_only=bool(tool_input.get("orientation_only") is True),
            risk_level=str(tool_input.get("risk_level") or "guided"),
            human_checkpoint_id=str(tool_input.get("human_checkpoint_id") or tool_input.get("checkpoint_id") or ""),
            failure_mode_review_checkpoint_id=str(
                tool_input.get("failure_mode_review_checkpoint_id")
                or tool_input.get("failure_mode_review_checkpoint")
                or ""
            ),
        )
    except Exception:
        return None


def _has_trusted_apply_source(payload: dict) -> bool:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return False
    source_kind = str(tool_input.get("source_kind") or "").strip().lower()
    preflight_token = str(tool_input.get("preflight_token") or "").strip()
    return source_kind in _TRUSTED_APPLY_SOURCE_KINDS and preflight_token.startswith("trust-preflight-")


def _input_list(payload: dict, key: str) -> list[str]:
    value = payload.get(key)
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    singular = payload.get(key.removesuffix("s"))
    if singular:
        return [str(singular)]
    return []


def _claude_pre_tool_output(decision, *, action: str, policy_decision: PolicyDecision) -> dict:
    aitp_payload = hook_decision_payload(decision, hook_name="pre_tool")
    aitp_payload["action"] = action
    aitp_payload["policy_reasons"] = [
        {
            "policy_id": reason.policy_id,
            "severity": reason.severity,
            "message": reason.message,
        }
        for reason in policy_decision.reasons
    ]
    aitp_payload["can_update_kernel_state"] = False
    aitp_payload["can_update_claim_trust"] = False
    permission = "deny" if decision.block else "allow"
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": permission,
            "permissionDecisionReason": decision.message,
        },
        "aitp": aitp_payload,
    }


def _evidence_status(payload: dict) -> str:
    response = payload.get("tool_response")
    if isinstance(response, dict) and response.get("exit_code") == 0:
        return "completed"
    return "process_trace"


def _risk_level(ws, session_id: str) -> str:
    try:
        return str(build_execution_brief(ws, session_id)["risk_assessment"]["level"])
    except Exception:
        return "guided"


def _claude_continue(extra: dict) -> dict:
    return {
        "continue": True,
        "suppressOutput": True,
        **extra,
    }


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
