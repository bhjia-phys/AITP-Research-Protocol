#!/usr/bin/env python
"""Real-topic acceptance for the scRPA thesis lane."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
KERNEL_ROOT = SCRIPT_PATH.parents[2]
REPO_ROOT = SCRIPT_PATH.parents[4]

if str(KERNEL_ROOT) not in sys.path:
    sys.path.insert(0, str(KERNEL_ROOT))

from knowledge_hub.aitp_service import AITPService  # noqa: E402


def now_stamp() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel-root", default=str(KERNEL_ROOT))
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--theory-workspace-root")
    parser.add_argument("--thesis-root")
    parser.add_argument("--topic", default="scRPA variational closure from thesis")
    parser.add_argument("--topic-slug", default=f"scrpa-thesis-acceptance-{now_stamp()}")
    parser.add_argument("--updated-by", default="scrpa-thesis-acceptance")
    parser.add_argument("--json", action="store_true")
    return parser


def discover_theory_workspace_root(repo_root: Path, override: str | None) -> Path:
    if override:
        candidate = Path(override).expanduser().resolve()
        if candidate.exists():
            return candidate
        raise FileNotFoundError(f"Invalid theory workspace root: {candidate}")

    candidates = [
        repo_root.parents[1] / "Theoretical-Physics",
        repo_root.parents[0] / "Theoretical-Physics",
    ]
    for candidate in candidates:
        if (candidate / "master-thesis" / "Thesis.tex").exists():
            return candidate.resolve()
    raise FileNotFoundError(
        "Unable to discover the Theoretical-Physics workspace automatically. "
        "Pass --theory-workspace-root."
    )


def discover_thesis_root(workspace_root: Path, override: str | None) -> Path:
    if override:
        candidate = Path(override).expanduser().resolve()
        if (candidate / "Thesis.tex").exists():
            return candidate
        raise FileNotFoundError(f"Invalid thesis root: {candidate}")

    candidate = workspace_root / "master-thesis"
    if (candidate / "Thesis.tex").exists():
        return candidate.resolve()
    raise FileNotFoundError(f"Unable to discover thesis root under {workspace_root}")


def thesis_paths(thesis_root: Path) -> list[Path]:
    required = [
        thesis_root / "Tex" / "Chap_4_scRPA.tex",
        thesis_root / "Tex" / "Chap_1_Introduction.tex",
        thesis_root / "Tex" / "Chap_5_Conclusion.tex",
        thesis_root / "Tex" / "Frontmatter.tex",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing thesis files: " + ", ".join(missing))
    return required


def ensure_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Expected artifact is missing: {path}")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    args = build_parser().parse_args()
    kernel_root = Path(args.kernel_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    workspace_root = discover_theory_workspace_root(repo_root, args.theory_workspace_root)
    thesis_root = discover_thesis_root(workspace_root, args.thesis_root)
    note_paths = thesis_paths(thesis_root)

    service = AITPService(kernel_root=kernel_root, repo_root=repo_root)

    human_request = (
        "Read my master's thesis and open a real scRPA AITP topic. "
        "Start from the variational closure route from generalized OEP to RDMFT, "
        "identify the first honest bounded question, and keep the route aligned "
        "with the thesis claim that scRPA is still at the theory-organization "
        "and closure stage rather than a completed numerical implementation."
    )
    question = (
        "Using the master's thesis scRPA route, what is the first honest bounded "
        "research question for constructing a self-consistent static nonlocal "
        "potential from generalized OEP to RDMFT without overclaiming numerical closure?"
    )

    opened = service.new_topic(
        topic=args.topic,
        question=question,
        mode="formal_theory",
        updated_by=args.updated_by,
        local_note_paths=[str(path) for path in note_paths],
        human_request=human_request,
    )
    topic_slug = str(opened["topic_slug"])

    status_payload = service.topic_status(topic_slug=topic_slug, updated_by=args.updated_by)
    next_payload = service.topic_next(topic_slug=topic_slug, updated_by=args.updated_by)
    work_payload = service.work_topic(
        topic_slug=topic_slug,
        question="From the thesis, tighten the first bounded validation route for the scRPA closure problem and keep the topic in a light profile.",
        mode="formal_theory",
        updated_by=args.updated_by,
        human_request="From the thesis, tighten the first bounded validation route for the scRPA closure problem and keep the topic in a light profile.",
        max_auto_steps=0,
        load_profile="light",
    )
    current_topic = service.get_current_topic_memory()

    runtime_root = kernel_root / "topics" / topic_slug / "runtime"
    research_question_note = runtime_root / "research_question.contract.md"
    validation_note = runtime_root / "validation_contract.active.md"
    idea_packet_note = runtime_root / "idea_packet.md"
    runtime_protocol = runtime_root / "runtime_protocol.generated.json"
    topic_synopsis = runtime_root / "topic_synopsis.json"
    pending_decisions = runtime_root / "pending_decisions.json"
    promotion_readiness = runtime_root / "promotion_readiness.json"

    for path in (
        research_question_note,
        validation_note,
        idea_packet_note,
        runtime_protocol,
        topic_synopsis,
        pending_decisions,
        promotion_readiness,
    ):
        ensure_exists(path)

    check(status_payload["load_profile"] == "light", "Expected the scRPA thesis topic to stay in light profile.")
    check(status_payload["topic_synopsis"]["lane"] == "formal_theory", "Expected the scRPA thesis topic to resolve to the formal_theory lane.")
    check(len(next_payload["must_read_now"]) == 2, "Expected light profile must_read_now to remain minimal.")
    check(
        next_payload["must_read_now"][0]["path"] == f"topics/{topic_slug}/runtime/topic_dashboard.md",
        "Expected the first light-profile read to be topic_dashboard.md.",
    )
    check(
        next_payload["must_read_now"][1]["path"] == f"topics/{topic_slug}/runtime/research_question.contract.md",
        "Expected the second light-profile read to be research_question.contract.md.",
    )
    check(
        any(
            row["path"] == f"topics/{topic_slug}/runtime/topic_synopsis.json"
            and row["trigger"] == "runtime_truth_audit"
            for row in next_payload["may_defer_until_trigger"]
        ),
        "Expected topic_synopsis.json to move behind the runtime_truth_audit trigger in light profile.",
    )
    check(
        status_payload["open_gap_summary"]["requires_l0_return"] is True,
        "Expected the initial scRPA thesis topic to remain honest about needing L0-style source recovery.",
    )
    check(
        str(current_topic.get("topic_slug") or "") == topic_slug,
        "Expected current-topic memory to update to the scRPA thesis topic.",
    )
    check(
        str((work_payload.get("runtime_context") or {}).get("load_profile") or "") == "light",
        "Expected explicit light-profile work refresh to preserve light runtime context.",
    )

    payload: dict[str, Any] = {
        "status": "success",
        "topic_slug": topic_slug,
        "workspace_root": str(workspace_root),
        "thesis_root": str(thesis_root),
        "thesis_sources": [str(path) for path in note_paths],
        "checks": {
            "formal_theory_lane": status_payload["topic_synopsis"]["lane"],
            "load_profile": status_payload["load_profile"],
            "requires_l0_return": status_payload["open_gap_summary"]["requires_l0_return"],
            "must_read_now_count": len(next_payload["must_read_now"]),
            "current_topic_slug": current_topic.get("topic_slug"),
        },
        "artifacts": {
            "research_question_note": str(research_question_note),
            "validation_note": str(validation_note),
            "idea_packet_note": str(idea_packet_note),
            "runtime_protocol": str(runtime_protocol),
            "topic_synopsis": str(topic_synopsis),
            "pending_decisions": str(pending_decisions),
            "promotion_readiness": str(promotion_readiness),
        },
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
