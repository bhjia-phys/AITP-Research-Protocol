"""Focused sample argv helpers for runtime entrypoint validation."""

from __future__ import annotations


def sample_args_for_template(template: str) -> list[str]:
    adapter_args = adapter_sample_args(template)
    if adapter_args is not None:
        return adapter_args
    if template.startswith("trust update-record"):
        return ["trust-update-sample"]
    if template.startswith("trust audit"):
        return ["--claim", "claim-fqhe"]
    if template.startswith("trust "):
        return ["change_claim_confidence", "--session", "s1", "--topic", "fqhe", "--claim", "claim-fqhe"]
    if template.startswith("policy pre-tool"):
        return ["validate_claim", "--session", "s1", "--claim", "claim-fqhe", "--source-kind", "typed_records"]
    if template.startswith("memory failure-mode-review-result"):
        return ["--claim", "claim-fqhe", "--checkpoint", "checkpoint-fqhe", "--status", "passed", "--reviewed-mode", "sector misassignment", "--basis-ref", "literature:fqhe", "--summary", "Review basis."]
    if template.startswith(("memory audit", "memory failure-modes", "memory failure-mode-review", "memory request-failure-mode-review")):
        return ["--claim", "claim-fqhe"]
    if template.startswith("source reconstruction-audit"):
        return ["--claim", "claim-fqhe"]
    if template.startswith("source reconstruction-review-result"):
        return ["--claim", "claim-fqhe", "--status", "inconclusive", "--reviewed-component", "definitions", "--basis-ref", "source:fqhe", "--summary", "Source reconstruction review sample."]
    if template.startswith("source reconstruction-review"):
        return ["--claim", "claim-fqhe"]
    if template.startswith("code state record"):
        return ["--repo-id", "librpa", "--upstream-remote", "origin", "--upstream-branch", "master", "--upstream-commit", "abc123", "--local-branch", "topic/gw", "--worktree-path", "D:/worktrees/librpa/gw"]
    if template.startswith("evidence record"):
        return ["--topic", "fqhe", "--claim", "claim-fqhe", "--type", "toy_numeric", "--status", "supports", "--summary", "Finite-size check."]
    if template.startswith("tool recipe register"):
        return ["recipe-ed", "--family", "numerical", "--name", "exact-diagonalization", "--purpose", "Run an ED check."]
    if template.startswith("tool run record"):
        return ["--recipe", "recipe-ed", "--family", "numerical", "--name", "exact-diagonalization", "--topic", "fqhe", "--claim", "claim-fqhe"]
    if template.startswith("tool execute"):
        return ["scalar_tolerance_check", "--recipe", "recipe-ed", "--topic", "fqhe", "--claim", "claim-fqhe", "--inputs-json", '{"observed":1,"expected":1,"tolerance":0}']
    if template.startswith("reference location record"):
        return ["--topic", "fqhe", "--connector", "local_pdf", "--type", "paper_pdf", "--uri", "file:///papers/fqhe.pdf", "--label", "FQHE paper PDF"]
    if template.startswith("trace hook-event persist"):
        return ["--payload-json", '{"kind":"hook_trace_event","hook_name":"post_tool","event":{"event_id":"event-1","session_id":"s1","topic_id":"fqhe","event_type":"tool_run_recorded","risk_level":"guided","payload":{},"kind":"trace_event"},"exit_code":0,"summary_inputs_trusted":false}']
    if template.startswith("legacy migrate"):
        return ["D:/aitp/legacy-topic", "--context", "legacy-context", "--session", "s1"]
    if template.startswith("legacy l2-graph-manifest"):
        return ["--legacy-l2-dir", "D:/aitp/research/aitp-topics/L2"]
    if template.startswith("legacy l2-typed-migration-packet"):
        return ["--legacy-l2-dir", "D:/aitp/research/aitp-topics/L2"]
    if template.startswith("legacy l2-obsidian-view"):
        return ["--legacy-l2-dir", "D:/aitp/research/aitp-topics/L2"]
    if template.startswith("legacy runtime-log-marker-audit"):
        return ["--topic", "fqhe", "--marker", "marker", "--raw-log-file", "D:/aitp/runtime/raw.log"]
    if template.startswith(("legacy migration-audit", "legacy semantic-review-queue")):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run"]
    if template.startswith("legacy semantic-review-manifest"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run"]
    if template.startswith("legacy semantic-review-worklist"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run"]
    if template.startswith("legacy semantic-review-packet"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run", "--topic", "fqhe"]
    if template.startswith("legacy semantic-repair-plan"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run", "--topic", "fqhe"]
    if template.startswith("legacy semantic-repair-apply"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run", "--topic", "fqhe", "--repair-type", "claim_statement_backfill", "--review-id", "legacy-semantic-review-sample"]
    if template.startswith("legacy source-reconstruction-plan"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run", "--topic", "fqhe"]
    if template.startswith("legacy source-reconstruction-review"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run", "--topic", "fqhe"]
    if template.startswith("legacy source-metadata-repair-packet"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run", "--topic", "fqhe"]
    if template.startswith("legacy executable-evidence-packet"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run", "--topic", "fqhe"]
    if template.startswith("legacy human-checkpoint-packet"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run", "--topic", "fqhe"]
    if template.startswith("legacy human-checkpoint-obsidian-view"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run", "--topic", "fqhe"]
    if template.startswith("legacy source-reconstruction-apply"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run", "--topic", "fqhe", "--repair-type", "reconstruction_path_evidence_backfill", "--review-id", "legacy-semantic-review-sample"]
    if template.startswith("legacy semantic-review-result"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run", "--topic", "fqhe", "--status", "inconclusive", "--legacy-ref", "legacy-topic:state.md", "--summary", "Semantic review sample."]
    if template.startswith("object record"):
        return ["--topic", "fqhe", "--type", "hilbert_sector", "--name", "N=8 sector", "--definition", "Finite-size Hilbert sector."]
    if template.startswith("relation record"):
        return ["--topic", "fqhe", "--type", "diagnoses", "--subject", "object-a", "--object", "object-b", "--statement", "A diagnoses B."]
    if template.startswith("sensemaking report"):
        return ["--topic", "fqhe", "--claim", "claim-fqhe", "--title", "Sanity check", "--summary", "Counting holds for N=8."]
    if template.startswith("subagent ingest-result"):
        return ["--topic", "fqhe", "--packet-json", '{"packet_id":"packet-critic","packet_type":"CriticPacket","claim_id":"claim-fqhe","claim_statement":"Claim"}', "--result-json", '{"summary":"Critique result."}']
    if template.startswith("validation contract create"):
        return ["--topic", "gw", "--claim", "claim-gw", "--required-check", "code_state_present", "--failure-mode", "dirty worktree", "--required-output", "evidence_or_provenance"]
    if template.startswith("validation result record"):
        return ["--topic", "gw", "--claim", "claim-gw", "--contract", "validation-contract-gw", "--tool-run", "tool-run-gw", "--status", "inconclusive", "--checked-output", "evidence_or_provenance", "--summary", "Validation result sample."]
    if template.startswith("checkpoint request"):
        return ["--topic", "fqhe", "--claim", "claim-fqhe", "--reason", "Promotion requires judgment", "--requested-by", "risk_policy", "--option", "approve"]
    if template.startswith("checkpoint decide"):
        return ["checkpoint-test", "--decision", "approve", "--rationale", "Looks good", "--decided-by", "human"]
    if template.startswith("promotion packet create"):
        return ["--topic", "fqhe", "--claim", "claim-fqhe", "--proposed-kind", "scoped_claim", "--scope", "N<=10 ED", "--evidence-ref", "evidence-1", "--validation-result-id", "validation-result-1", "--failure-mode", "misassignment"]
    if template.startswith("promotion packet apply"):
        return ["packet-fqhe", "--checkpoint", "checkpoint-fqhe"]
    return []


def adapter_sample_args(template: str) -> list[str] | None:
    if template.startswith("adapter final-readiness"):
        return []
    if template.startswith("adapter hook-bridge"):
        return ["--output", "AITP_V5_HOOK_BRIDGE.md"]
    if template.startswith("adapter hook-settings"):
        return ["--output", ".claude/settings.local.json"]
    if template.startswith("adapter install-hooks kimi-code"):
        return ["--settings", ".kimi/config.toml"]
    if template.startswith("adapter install-hooks codex"):
        return ["--output", ".codex/AITP_V5_HOOKS.json"]
    if template.startswith("adapter install-hooks opencode"):
        return ["--output", ".opencode/AITP_V5_PLUGIN_HOOKS.json"]
    if template.startswith("adapter install-hooks"):
        return ["--settings", ".claude/settings.local.json"]
    if template.startswith("adapter pre-tool-event"):
        return [
            "--bridge-json",
            '{"kind":"codex_hook_bridge","runtime":"codex","source_protocol_field":"runtime_hook_installation","installation_mode":"explicit_guard_calls","native_installer_available":false,"summary_inputs_trusted":false,"can_update_kernel_state":false,"pre_tool_policy_entrypoint":{"cli":"aitp-v5 policy pre-tool <args>","mcp":"aitp_v5_evaluate_pre_tool_policy","surface":"pre_tool_policy_decision","truth_source":"typed_records","summary_inputs_trusted":false,"can_update_kernel_state":false,"can_update_claim_trust":false},"gate_protocols":{"source_protocol_field":"runtime_gate_protocols","record_evidence":{"pre_tool_policy":"aitp_v5_evaluate_pre_tool_policy","preflight":"","sequence":["refresh_execution_brief","evaluate_pre_tool_policy","record_evidence","refresh_execution_brief","write_session_summary"],"required_typed_refs":["topic_id","claim_id"],"allowed_state_sources":["typed_records","typed_evidence_records"],"policy_reasons_field":"policy_reasons","human_checkpoint_required":false,"truth_source":"typed_records","summary_inputs_trusted":false}},"path":"AITP_V5_HOOK_BRIDGE.md","guard_calls":[{"hook_name":"pre_tool"}]}',
            "--event-json",
            '{"runtime":"codex","hook_name":"pre_tool","session_id":"s1","tool_name":"mcp__aitp__aitp_v5_record_evidence","tool_input":{"claim_id":"claim-fqhe","source_kind":"typed_records"}}',
        ]
    if template.startswith("adapter host-lifecycle"):
        return ["--command", "python", "--arg", "--version"]
    return None
