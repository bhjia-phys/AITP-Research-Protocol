#!/usr/bin/env python3
"""Advance the minimal AITP closed-loop runtime by one honest step."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from closed_loop_v1 import (
    compute_closed_loop_status,
    ingest_execution_result,
    materialize_execution_task,
    read_json,
    select_validation_route,
)


VALID_STEPS = {"auto", "select_route", "materialize_task", "ingest_result"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic-slug", required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--step", default="auto", choices=sorted(VALID_STEPS))
    parser.add_argument("--updated-by", default="codex")
    return parser


def load_topic_state(knowledge_root: Path, topic_slug: str) -> dict:
    topic_state_path = knowledge_root / "runtime" / "topics" / topic_slug / "topic_state.json"
    topic_state = read_json(topic_state_path)
    if topic_state is None:
        raise SystemExit(f"Runtime topic state missing: {topic_state_path}")
    return topic_state


def main() -> int:
    args = build_parser().parse_args()
    knowledge_root = Path(__file__).resolve().parents[2]
    topic_state = load_topic_state(knowledge_root, args.topic_slug)
    if args.run_id:
        topic_state["latest_run_id"] = args.run_id

    if args.step == "auto":
        closed_loop = compute_closed_loop_status(knowledge_root, args.topic_slug, topic_state.get("latest_run_id"))
        step = closed_loop.get("next_transition")
        if not step:
            print(
                json.dumps(
                    {
                        "topic_slug": args.topic_slug,
                        "step": None,
                        "status": "noop",
                        "reason": closed_loop.get("next_transition_reason"),
                    },
                    ensure_ascii=True,
                )
            )
            return 0
    else:
        step = args.step

    if step == "select_route":
        payload = select_validation_route(knowledge_root, topic_state, args.updated_by)
    elif step == "materialize_task":
        payload = materialize_execution_task(knowledge_root, topic_state, args.updated_by)
    elif step == "ingest_result":
        payload = ingest_execution_result(knowledge_root, topic_state, args.updated_by)
    else:
        raise SystemExit(f"Unsupported step: {step}")

    print(
        json.dumps(
            {
                "topic_slug": args.topic_slug,
                "step": step,
                "status": "applied",
                "payload": payload,
            },
            ensure_ascii=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
