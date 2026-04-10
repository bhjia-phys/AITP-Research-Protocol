#!/usr/bin/env python3
"""Generate a human-readable replay bundle for one topic."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

KERNEL_ROOT = Path(__file__).resolve().parents[2]
if str(KERNEL_ROOT) not in sys.path:
    sys.path.insert(0, str(KERNEL_ROOT))

from knowledge_hub.topic_replay import materialize_topic_replay_bundle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a topic replay bundle from durable artifacts")
    parser.add_argument("--topic-slug", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = materialize_topic_replay_bundle(KERNEL_ROOT, args.topic_slug)
    payload = result["payload"]
    print(
        json.dumps(
            {
                "status": "success",
                "topic_slug": args.topic_slug,
                "json_path": result["json_path"],
                "markdown_path": result["markdown_path"],
                "missing_artifact_count": len(payload.get("missing_artifacts") or []),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
