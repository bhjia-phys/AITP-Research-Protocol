"""Runtime CLI sample resolver part 1."""

from __future__ import annotations


def sample_args_part_01(template: str) -> list[str] | None:
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
    if template.startswith("domain-pack skill-shims"):
            return ["--pack", "gw_librpa", "--output-root", "D:/aitp/.agents/skills"]
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
    if template.startswith("literature reading-route"):
            return [
                "--session",
                "s1",
                "--question",
                "How should these two sources be read before synthesis?",
                "--source-ref",
                "source_asset:source-a",
                "--source-ref",
                "reference_location:source-b",
                "--route-type",
                "paired",
                "--focus",
                "source assumptions",
            ]
    if template.startswith("literature source-extraction"):
            return [
                "--session",
                "s1",
                "--source-ref",
                "source_asset:source-asset-edge-counting",
                "--source-ref",
                "reference_location:reference-location-edge-counting",
                "--focus",
                "edge CFT",
                "--mode",
                "concept",
                "--mode",
                "relation",
            ]
    if template.startswith("literature extraction-report"):
            return [
                "--session",
                "s1",
                "--source-ref",
                "source_asset:source-asset-edge-counting",
                "--source-ref",
                "reference_location:reference-location-edge-counting",
                "--profile",
                "paired_paper_learning",
                "--focus",
                "edge CFT",
            ]
    if template.startswith("literature corpus-extraction-artifact"):
            return [
                "--session",
                "s1",
                "--chunk-id",
                "curated_rag_chunk:source_backtrace_orientation:0001",
                "--reference-location-id",
                "reference-location-source-backtrace",
                "--profile",
                "paper_learning",
                "--focus",
                "source backtrace",
            ]
    if template.startswith("literature source-set-readiness"):
            return [
                "--session",
                "s1",
                "--source-ref",
                "source_asset:source-a",
                "--source-ref",
                "reference_location:source-b",
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
    return None
