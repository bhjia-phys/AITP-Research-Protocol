"""Focused sample argv helpers for runtime entrypoint validation."""

from __future__ import annotations


def sample_args_for_template(template: str) -> list[str]:
    adapter_args = adapter_sample_args(template)
    if adapter_args is not None:
        return adapter_args
    if template.startswith("trust update-record"):
        return ["trust-update-sample"]
    if template.startswith("session bind"):
        return ["--topic", "fqhe", "--context", "topological-order", "--claim", "claim-fqhe"]
    if template.startswith("relation-map"):
        return ["s1"]
    if template.startswith("trust audit"):
        return ["--claim", "claim-fqhe"]
    if template.startswith("trust "):
        return ["change_claim_confidence", "--session", "s1", "--topic", "fqhe", "--claim", "claim-fqhe"]
    if template.startswith("policy pre-tool"):
        return ["validate_claim", "--session", "s1", "--claim", "claim-fqhe", "--source-kind", "typed_records"]
    if template.startswith("recording classify-candidate"):
        return ["--session", "s1", "--event-type", "tool_run_completed", "--summary", "ED diagnostic run completed.", "--topic", "fqhe", "--claim", "claim-fqhe", "--tool-call-id", "tool-call-1"]
    if template.startswith("recording plan-lightweight-write"):
        return ["--topic", "fqhe", "--session", "s1", "--summary", "old kconv plot uses diagnostic lane, cannot mix with new final report.", "--active-claim", "claim-fqhe", "--touched-file", "reports/old_kconv.png"]
    if template.startswith("recording navigation-state"):
        return ["s1", "--claim", "claim-fqhe"]
    if template.startswith("recording expand-slot"):
        return ["--slot", "evidence", "--claim", "claim-fqhe"]
    if template.startswith("recording verify-effect"):
        return ["--expected-ref", "evidence:evidence-sample", "--claim", "claim-fqhe"]
    if template.startswith("memory failure-mode-review-result"):
        return ["--claim", "claim-fqhe", "--checkpoint", "checkpoint-fqhe", "--status", "passed", "--reviewed-mode", "sector misassignment", "--basis-ref", "literature:fqhe", "--summary", "Review basis."]
    if template.startswith(("memory audit", "memory failure-modes", "memory failure-mode-review", "memory request-failure-mode-review")):
        return ["--claim", "claim-fqhe"]
    if template.startswith("source reconstruction-audit"):
        return ["--claim", "claim-fqhe"]
    if template.startswith("source reconstruction-review-result"):
        return ["--claim", "claim-fqhe", "--status", "inconclusive", "--reviewed-component", "definitions", "--basis-ref", "source:fqhe", "--summary", "Source reconstruction review sample."]
    if template.startswith("source reconstruction-obsidian-view"):
        return []
    if template.startswith("source reconstruction-review"):
        return ["--claim", "claim-fqhe"]
    if template.startswith("code state record"):
        return ["--repo-id", "librpa", "--upstream-remote", "origin", "--upstream-branch", "master", "--upstream-commit", "abc123", "--local-branch", "topic/gw", "--worktree-path", "D:/worktrees/librpa/gw"]
    if template.startswith("code state auto"):
        return ["--worktree-path", ".", "--repo-id", "librpa", "--topic", "gw", "--claim", "claim-gw"]
    if template.startswith("evidence record"):
        return ["--topic", "fqhe", "--claim", "claim-fqhe", "--type", "toy_numeric", "--status", "supports", "--summary", "Finite-size check."]
    if template.startswith("record rehome"):
        return ["--record-id", "claim-fqhe", "--kind", "claim", "--from-topic", "wrong-topic", "--to-topic", "right-topic", "--reason", "misrouted"]
    if template.startswith("record supersede"):
        return ["--record-id", "claim-fqhe", "--kind", "claim", "--status", "misrouted", "--reason", "replaced"]
    if template.startswith("record audit-routing"):
        return ["--topic", "wrong-topic"]
    if template.startswith("record lifecycle"):
        return ["--record-id", "claim-fqhe"]
    if template.startswith("research-state register-source"):
        return ["--topic", "fqhe", "--claim", "claim-fqhe", "--uri", "arxiv:2604.14695", "--label", "Close prior art"]
    if template.startswith("research-state attach-artifact-auto"):
        return ["--path", "results/check.json", "--topic", "fqhe", "--claim", "claim-fqhe", "--type", "result_json", "--summary", "Finite-size result file."]
    if template.startswith("research-state attach-artifact"):
        return ["--topic", "fqhe", "--claim", "claim-fqhe", "--type", "result_json", "--uri", "results/check.json", "--summary", "Finite-size result file."]
    if template.startswith("research-state update-claim-status"):
        return ["--topic", "fqhe", "--claim", "claim-fqhe", "--maturity-level", "finite-size evidence", "--claim-status", "bounded_check_recorded", "--scope", "N<=10", "--risk", "not a theorem", "--next-action", "human review"]
    if template.startswith("research-state create-proof-obligation"):
        return ["--topic", "fqhe", "--claim", "claim-fqhe", "--statement", "Prove the finite-size pattern for all N.", "--type", "theorem_gap", "--status", "open", "--maturity-level", "theorem-candidate", "--next-action", "derive symbolic proof"]
    if template.startswith("research-state update-proof-obligation"):
        return ["proof-obligation-fqhe", "--topic", "fqhe", "--claim", "claim-fqhe", "--status", "refined", "--next-action", "split proof into algebraic lemmas"]
    if template.startswith("research-state classify-event"):
        return ["--topic", "fqhe", "--claim", "claim-fqhe", "--event-kind", "result_json", "--summary", "JSON result with a finite-size check.", "--source-uri", "results/check.json"]
    if template.startswith("research-state bounded-evidence"):
        return ["--topic", "fqhe", "--claim", "claim-fqhe", "--artifact-uri", "results/check.json", "--artifact-summary", "Finite-size result file.", "--supports-output", "finite_size_check", "--scope", "N<=10 only"]
    if template.startswith("curated-rag ingest"):
        return ["--path", "notes/dmft-orientation.md", "--tag", "dmft", "--topic-hint", "gw-dmft"]
    if template.startswith("knowledge bind"):
        return [
            "--connector",
            "qft_literature",
            "--root",
            "file:///D:/aitp/qft-literature",
            "--corpus-id",
            "qft-local",
            "--glob",
            "**/*.pdf",
        ]
    if template.startswith("domain-pack suggest"):
        return [
            "--topic",
            "librpa-gw",
            "--statement",
            "The LibRPA GW benchmark table is reproduced after a QSGW self-energy change.",
            "--evidence-profile",
            "code_method",
        ]
    if template.startswith("literature comparison-draft"):
        return [
            "--session",
            "s1",
            "--question",
            "How do the source assumptions compare?",
            "--source-ref",
            "source_asset:source-a",
            "--source-ref",
            "reference_location:source-b",
            "--dimension",
            "method_assumptions",
        ]
    if template.startswith("adapter curated-rag-chunk"):
        return ["curated_rag_chunk:source_backtrace_orientation:0001"]
    if template.startswith("adapter curated-rag-promotion-draft"):
        return ["--topic", "fqhe", "--claim", "claim-fqhe"]
    if template.startswith("adapter record-ref-lookup"):
        return ["source_asset:source-asset-edge-counting", "reference_location:reference-location-edge-counting"]
    if template.startswith("tool recipe register"):
        return ["recipe-ed", "--family", "numerical", "--name", "exact-diagonalization", "--purpose", "Run an ED check."]
    if template.startswith("tool run capture-auto"):
        return ["--path", "results/ed-transcript.txt", "--recipe", "recipe-ed", "--family", "numerical", "--name", "exact-diagonalization", "--topic", "fqhe", "--claim", "claim-fqhe"]
    if template.startswith("tool run record"):
        return ["--recipe", "recipe-ed", "--family", "numerical", "--name", "exact-diagonalization", "--topic", "fqhe", "--claim", "claim-fqhe"]
    if template.startswith("tool execute"):
        return ["scalar_tolerance_check", "--recipe", "recipe-ed", "--topic", "fqhe", "--claim", "claim-fqhe", "--inputs-json", '{"observed":1,"expected":1,"tolerance":0}']
    if template.startswith("reference location record"):
        return ["--topic", "fqhe", "--connector", "local_pdf", "--type", "paper_pdf", "--uri", "file:///papers/fqhe.pdf", "--label", "FQHE paper PDF"]
    if template.startswith("exploration record"):
        return [
            "--topic",
            "fqhe",
            "--claim",
            "claim-fqhe",
            "--session",
            "s1",
            "--type",
            "relation_path_brainstorm",
            "--title",
            "Counting to CFT relation path",
            "--focal-question",
            "How can the counting sequence constrain the candidate edge CFT?",
            "--summary",
            "Exploratory relation path before validation.",
            "--original-question",
            "Does sector counting identify the edge theory?",
            "--local-question",
            "Which intermediate objects connect counting data to CFT labels?",
            "--candidate-path",
            "counting sequence -> sector matching -> edge CFT",
            "--unresolved-point",
            "finite-size aliasing",
            "--next-action",
            "trace source definitions",
        ]
    if template.startswith("route record"):
        return [
            "--topic",
            "fqhe",
            "--claim",
            "claim-fqhe",
            "--session",
            "s1",
            "--type",
            "relation_path",
            "--status",
            "live",
            "--title",
            "Counting to CFT route",
            "--rationale",
            "Try the sector-counting relation path before validation.",
            "--current-question",
            "Can sector counting be traced to a CFT label definition?",
            "--next-action",
            "open source backtrace",
        ]
    if template.startswith("asset capture-auto"):
        return [
            "--path",
            "D:/sources/edge-counting.pdf",
            "--topic",
            "fqhe",
            "--claim",
            "claim-fqhe",
            "--summary",
            "Auto-captured local source file identity.",
        ]
    if template.startswith("asset acquire-pdf"):
        return [
            "--topic",
            "fqhe",
            "--claim",
            "claim-fqhe",
            "--url",
            "file:///D:/sources/edge-counting.pdf",
            "--title",
            "Edge counting source PDF",
            "--summary",
            "Acquired local PDF copy for later text extraction.",
        ]
    if template.startswith("asset acquire-arxiv"):
        return [
            "--topic",
            "fqhe",
            "--claim",
            "claim-fqhe",
            "--arxiv-id",
            "2604.14695",
            "--title",
            "Long-range spin-chain level statistics",
            "--summary",
            "Acquired arXiv PDF source asset for source backtrace.",
        ]
    if template.startswith("asset register"):
        return [
            "--topic",
            "fqhe",
            "--claim",
            "claim-fqhe",
            "--type",
            "paper",
            "--uri",
            "arxiv:2601.00001",
            "--title",
            "Edge counting source",
            "--version-anchor-json",
            '{"arxiv_version":"v1"}',
            "--source-kind",
            "literature",
            "--summary",
            "Canonical source asset identity for the raw paper.",
        ]
    if (
        template.startswith("literature suggest-intake")
        or template.startswith("literature record-candidate")
        or template.startswith("literature source-review-handoff")
    ):
        return [
            "--session",
            "s1",
            "--uri",
            "https://arxiv.org/abs/2604.14695",
            "--label",
            "Long-range spin-chain level statistics",
            "--summary",
            "Close prior art.",
            "--detected-relevance",
            "close_prior_art",
            "--reviewed-ref",
            "source_asset:source-asset-edge-counting",
        ]
    if template.startswith("intent packet record"):
        return [
            "--topic",
            "fqhe",
            "--idea",
            "Test whether a scoped finite-size invariant is stable.",
            "--novelty-target",
            "Find a falsifiable scoped claim before deeper execution.",
            "--required-first-validation-route",
            "toy_numeric_or_literature_check",
            "--initial-evidence-bar",
            "At least one concrete source or executable sanity check.",
            "--clarification-question",
            "What output would count as a failure?",
        ]
    if template.startswith("intent steering materialize"):
        return [
            "--topic",
            "fqhe",
            "--steering",
            "Redirect toward a narrower falsifiable invariant.",
            "--novelty-target",
            "Avoid re-running known checks without a new scoped output.",
            "--scope",
            "finite-size diagnostic only",
            "--acceptance-posture",
            "diagnostic until independently validated",
            "--control-note",
            "Do not promote without a validation contract.",
            "--session",
            "s1",
        ]
    if template.startswith("output profile record"):
        return [
            "--topic",
            "fqhe",
            "--version",
            "fqhe-final-output-v1",
            "--audience",
            "future_agent",
            "--stable-section",
            "current_state",
            "--stable-section",
            "next_actions",
            "--flexible-section",
            "open_questions",
            "--change-policy",
            "Breaking changes require a new output version.",
        ]
    if template.startswith("operator checkpoint request"):
        return [
            "--topic",
            "fqhe",
            "--kind",
            "promotion_approval",
            "--question",
            "Can this scoped result be promoted?",
            "--option",
            "approve",
            "--option",
            "defer",
            "--requested-by",
            "promotion_preflight",
        ]
    if template.startswith("operator checkpoint answer"):
        return [
            "operator-checkpoint-sample",
            "--topic",
            "fqhe",
            "--selected-option",
            "defer",
            "--rationale",
            "Need one more validation result.",
            "--answered-by",
            "human",
        ]
    if template.startswith("strategy memory record"):
        return [
            "--topic",
            "fqhe",
            "--run",
            "run-fqhe-strategy",
            "--type",
            "verification_guardrail",
            "--outcome",
            "helped",
            "--lesson",
            "Keep finite-size diagnostics separate from promoted claims.",
            "--next-time-rule",
            "Do not promote without a validation result and checkpoint.",
            "--scope",
            "finite-size evidence review",
        ]
    if template.startswith("run iteration record"):
        return [
            "--topic",
            "fqhe",
            "--run",
            "run-fqhe-iteration",
            "--iteration",
            "iter-001",
            "--plan-summary",
            "Run a bounded diagnostic check.",
            "--deliverable",
            "diagnostic note",
            "--check",
            "do not promote diagnostic output",
            "--stop-rule",
            "stop before trust update",
            "--status",
            "planned",
        ]
    if template.startswith("run research start"):
        return [
            "--topic",
            "fqhe",
            "--objective",
            "Answer whether the scoped finite-size invariant survives source review.",
            "--question",
            "Does the diagnostic invariant have validated support or only finite evidence?",
            "--operator",
            "human",
            "--session",
            "s1",
            "--claim",
            "claim-fqhe",
        ]
    if template.startswith("run research update"):
        return [
            "--run",
            "research-run-fqhe",
            "--topic",
            "fqhe",
            "--operator",
            "hakimi",
            "--status",
            "paused",
            "--phase",
            "awaiting_approval",
            "--event-summary",
            "Paused before trust-changing work.",
        ]
    if template.startswith("run event record"):
        return [
            "--run",
            "research-run-fqhe",
            "--topic",
            "fqhe",
            "--operator",
            "hakimi",
            "--type",
            "context_refreshed",
            "--summary",
            "Read current AITP process graph slice.",
            "--phase",
            "context_refresh",
        ]
    if template.startswith("exemplar lane record"):
        return [
            "--topic",
            "fqhe",
            "--lane",
            "toy_numeric",
            "--title",
            "Finite-size diagnostic exemplar",
            "--summary",
            "Toy numeric exemplar with explicit trust boundary.",
            "--gate",
            "G3_verification",
            "--artifact-ref",
            "test:test_v5_lane_exemplars.py",
            "--trust-boundary",
            "Exemplar only; not evidence.",
            "--status",
            "accepted",
        ]
    if template.startswith("trace hook-event persist"):
        return ["--payload-json", '{"kind":"hook_trace_event","hook_name":"post_tool","event":{"event_id":"event-1","session_id":"s1","topic_id":"fqhe","event_type":"tool_run_recorded","risk_level":"guided","payload":{},"kind":"trace_event"},"exit_code":0,"summary_inputs_trusted":false}']
    if template.startswith("legacy migrate"):
        return ["D:/aitp/legacy-topic", "--context", "legacy-context", "--session", "s1"]
    if template.startswith("legacy l2-graph-manifest"):
        return ["--legacy-l2-dir", "D:/aitp/research/aitp-topics/L2"]
    if template.startswith("legacy l2-typed-migration-packet"):
        return ["--legacy-l2-dir", "D:/aitp/research/aitp-topics/L2"]
    if template.startswith("legacy l2-seed-audit"):
        return ["--sample-limit", "5"]
    if template.startswith("legacy l2-seed-review-worklist"):
        return ["--group-limit", "5", "--sample-limit", "2"]
    if template.startswith("legacy l2-seed-review-result"):
        return [
            "--group-id",
            "legacy-l2-seed-review:fqhe:fqhe:claim-fqhe:claim",
            "--status",
            "passed",
            "--decision",
            "archive",
            "--summary",
            "Seed group reviewed as archive-only sample.",
            "--seed-entry-id",
            "memory-legacy-l2-fqhe-claim",
        ]
    if template.startswith("legacy l2-obsidian-view"):
        return ["--legacy-l2-dir", "D:/aitp/research/aitp-topics/L2"]
    if template.startswith("legacy runtime-log-marker-audit"):
        return ["--topic", "fqhe", "--marker", "marker", "--raw-log-file", "D:/aitp/runtime/raw.log"]
    if template.startswith(("legacy migration-audit", "legacy semantic-review-queue")):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run"]
    if template.startswith("legacy migration-accounting-run"):
        return ["--legacy-root", "D:/aitp/research/aitp-topics", "--run-id", "legacy-v5-lossless-run"]
    if template.startswith("legacy semantic-review-manifest"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run"]
    if template.startswith("legacy semantic-review-worklist"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run"]
    if template.startswith("legacy semantic-needs-revision-basis"):
        args = ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run"]
        if template.startswith("legacy semantic-needs-revision-basis-packet"):
            args.extend(["--topic", "fqhe"])
        return args
    if template.startswith("legacy semantic-review-obsidian-view"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run"]
    if template.startswith("legacy semantic-review-packet"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run", "--topic", "fqhe"]
    if template.startswith("legacy semantic-repair-plan"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run", "--topic", "fqhe"]
    if template.startswith("legacy semantic-repair-manifest"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run"]
    if template.startswith("legacy semantic-repair-apply"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run", "--topic", "fqhe", "--repair-type", "claim_statement_backfill", "--review-id", "legacy-semantic-review-sample"]
    if template.startswith("legacy source-reconstruction-plan"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run", "--topic", "fqhe"]
    if template.startswith("legacy source-reconstruction-manifest"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run"]
    if template.startswith("legacy source-reconstruction-obsidian-view"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run"]
    if template.startswith("legacy source-reconstruction-review"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run", "--topic", "fqhe"]
    if template.startswith("legacy source-metadata-repair-packet"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run", "--topic", "fqhe"]
    if template.startswith("legacy executable-evidence-packet"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run", "--topic", "fqhe"]
    if template.startswith("legacy human-checkpoint-packet"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run", "--topic", "fqhe"]
    if template.startswith("legacy topic-question-backfill-packet"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run"]
    if template.startswith("legacy human-checkpoint-obsidian-view"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run", "--topic", "fqhe"]
    if template.startswith("legacy source-reconstruction-apply"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run", "--topic", "fqhe", "--repair-type", "reconstruction_path_evidence_backfill", "--review-id", "legacy-semantic-review-sample"]
    if template.startswith("legacy semantic-review-result"):
        return ["--migration-dir", "D:/aitp/.aitp/migrations/legacy-v5-lossless-run", "--topic", "fqhe", "--status", "inconclusive", "--legacy-ref", "legacy-topic:state.md", "--summary", "Semantic review sample."]
    if template.startswith("workspace file-migration-ledger"):
        return ["--workspace-root", "D:/aitp", "--compact"]
    if template.startswith("workspace migration-health"):
        return ["--sample-limit", "5"]
    if template.startswith("workspace old-store-import"):
        return ["--workspace-root", "D:/aitp", "--topic", "fqhe"]
    if template.startswith("workspace recovery-binding-repair"):
        return ["--topic", "fqhe"]
    if template.startswith("workspace recovery-audit"):
        return ["--compact"]
    if template.startswith("workspace recording-audit"):
        return ["--topic", "fqhe"]
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
    if template.startswith("adapter bridge-acceptance"):
        return []
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
    if template.startswith("adapter host-production-loop"):
        return ["--command", "python", "--arg", "--version", "--skip-install-audit"]
    if template.startswith("goal write"):
        return ["--objective", "Test objective"]
    if template.startswith("goal latest") or template.startswith("goal list"):
        return []
    return None
