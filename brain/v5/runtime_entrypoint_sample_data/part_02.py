"""Runtime CLI sample resolver part 2."""

from __future__ import annotations


def sample_args_part_02(template: str) -> list[str] | None:
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
    if template.startswith("exemplar lane record-librpa-code"):
            return [
                "--topic",
                "librpa-gw",
                "--claim",
                "claim-librpa-gw",
                "--run",
                "run-librpa-gw",
                "--status",
                "accepted",
            ]
    if template.startswith("exemplar lane record-qft-qg-source"):
            return [
                "--topic",
                "qft-qg-source-reconstruction",
                "--claim",
                "claim-qft-qg",
                "--run",
                "run-qft-qg-source",
                "--status",
                "accepted",
            ]
    if template.startswith("exemplar lane record-toy-numeric"):
            return [
                "--topic",
                "toy-finite-size",
                "--claim",
                "claim-toy",
                "--run",
                "run-toy-finite-size",
                "--status",
                "accepted",
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
    if template.startswith("promotion-checkpoint request"):
            return ["--packet", "packet-fqhe", "--reason", "Review exact packet", "--requested-by", "risk_policy", "--expires-at", "2099-01-01T00:00:00+00:00", "--option", "approve"]
    if template.startswith("checkpoint decide"):
            return ["checkpoint-test", "--decision", "approve", "--rationale", "Looks good", "--decided-by", "human"]
    if template.startswith("promotion packet create"):
            return ["--topic", "fqhe", "--claim", "claim-fqhe", "--proposed-kind", "scoped_claim", "--scope", "N<=10 ED", "--evidence-ref", "evidence-1", "--validation-result-id", "validation-result-1", "--failure-mode", "misassignment"]
    if template.startswith("promotion packet apply"):
            return ["packet-fqhe", "--checkpoint", "checkpoint-fqhe"]
    return None
