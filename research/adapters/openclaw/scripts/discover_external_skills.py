#!/usr/bin/env python3
"""Discover external skills and write an auditable recommendation bundle."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
CANDIDATE_RE = re.compile(
    r"^(?P<package>[A-Za-z0-9._-]+/[A-Za-z0-9._-]+@[^ ]+)(?:\s+(?P<installs>\d+)\s+installs)?$"
)


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_find_output(raw_output: str) -> list[dict]:
    clean_lines = [line.strip() for line in strip_ansi(raw_output).splitlines()]
    candidates: list[dict] = []
    current: dict | None = None

    for line in clean_lines:
        if not line:
            continue

        match = CANDIDATE_RE.match(line)
        if match:
            package = match.group("package")
            repo, skill_name = package.split("@", 1)
            installs = match.group("installs")
            current = {
                "package": package,
                "repo": repo,
                "skill_name": skill_name,
                "installs": int(installs) if installs else None,
            }
            candidates.append(current)
            continue

        if line.startswith("└ http") or line.startswith("http"):
            url = line.lstrip("└ ").strip()
            if current is not None:
                current["catalog_url"] = url

    return candidates


def failed_query_result(
    query: str,
    command: list[str],
    *,
    status: str,
    error_kind: str,
    message: str,
    stdout: str = "",
    stderr: str = "",
) -> dict:
    return {
        "query": query,
        "command": " ".join(command),
        "status": status,
        "error_kind": error_kind,
        "error_message": message,
        "raw_output": stdout,
        "raw_error": stderr,
        "candidates": [],
    }


def run_find_query(query: str) -> dict:
    command = ["npx", "--yes", "skills", "find", query]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
        )
    except FileNotFoundError as exc:
        return failed_query_result(
            query,
            command,
            status="unavailable",
            error_kind="command_not_found",
            message=str(exc),
        )

    stdout = strip_ansi(completed.stdout)
    stderr = strip_ansi(completed.stderr)

    if completed.returncode != 0:
        return failed_query_result(
            query,
            command,
            status="unavailable",
            error_kind="command_failed",
            message=stderr or stdout or f"exit={completed.returncode}",
            stdout=stdout,
            stderr=stderr,
        )

    return {
        "query": query,
        "command": " ".join(command),
        "status": "completed",
        "error_kind": None,
        "error_message": None,
        "raw_output": stdout,
        "raw_error": stderr,
        "candidates": parse_find_output(stdout),
    }


def enrich_candidate(candidate: dict, agent_target: str) -> dict:
    repo = candidate["repo"]
    skill_name = candidate["skill_name"]
    return {
        **candidate,
        "review_status": "discovered_unreviewed",
        "adoption_modes": [
            "discover_only",
            "vendor_local",
            "approved_local_install",
            "rejected",
        ],
        "auto_install_allowed": False,
        "policy_notes": [
            "Discovery is allowed; installation still requires review.",
            "Do not install into global user paths unless the user explicitly requests it.",
            "Do not silently install third-party skills into repository root in this workspace.",
            "Prefer read-only review or a rewritten local skill under skills-shared when long-term reuse matters.",
        ],
        "recommended_review_steps": [
            f"Read the repository metadata for {repo}.",
            f"Inspect the specific skill {skill_name} before adoption.",
            "Decide whether the skill should stay external, be rewritten locally, or be installed into an approved local agent path.",
        ],
        "proposed_local_install_command": (
            f"npx skills add {repo} --skill {skill_name} --agent {agent_target} --copy -y"
        ),
    }


def build_markdown_report(payload: dict) -> str:
    lines = [
        "# External skill recommendations",
        "",
        f"- Updated at: `{payload['updated_at']}`",
        f"- Updated by: `{payload['updated_by']}`",
        f"- Agent target: `{payload['agent_target']}`",
        f"- Topic slug: `{payload.get('topic_slug') or '(none)'}`",
        "",
        "## Policy",
        "",
        "- Discovery is allowed by default.",
        "- Installation remains review-gated.",
        "- This workspace should not silently install third-party skills into repo root or global user paths.",
        "",
    ]

    if payload.get("overall_status") != "ready":
        lines.extend(
            [
                "## Limitations",
                "",
                "- External skill discovery is running in degraded mode.",
                "- Missing or failing `npx skills find` no longer blocks AITP topic bootstrap.",
                "- Treat per-query status rows as authoritative before reusing any recommendation.",
                "",
            ]
        )

    for query_result in payload["queries"]:
        lines.extend(
            [
                f"## Query: `{query_result['query']}`",
                "",
                f"- Command: `{query_result['command']}`",
                f"- Status: `{query_result.get('status') or 'unknown'}`",
                f"- Candidate count: `{len(query_result['candidates'])}`",
                "",
            ]
        )

        if query_result.get("error_kind"):
            lines.extend(
                [
                    f"- Error kind: `{query_result['error_kind']}`",
                    f"- Error: `{query_result.get('error_message') or '(missing)'}`",
                    "",
                ]
            )

        if not query_result["candidates"]:
            lines.extend(
                [
                    "- No candidate skills were discovered.",
                    "",
                ]
            )
            continue

        for candidate in query_result["candidates"]:
            lines.extend(
                [
                    f"### `{candidate['package']}`",
                    "",
                    f"- Catalog: `{candidate.get('catalog_url', '(missing)')}`",
                    f"- Installs: `{candidate.get('installs') if candidate.get('installs') is not None else '(unknown)'}`",
                    f"- Review status: `{candidate['review_status']}`",
                    f"- Proposed install command: `{candidate['proposed_local_install_command']}`",
                    "- Policy notes:",
                ]
            )
            for note in candidate["policy_notes"]:
                lines.append(f"  - {note}")
            lines.append("- Recommended review steps:")
            for step in candidate["recommended_review_steps"]:
                lines.append(f"  - {step}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def default_output_dir(topic_slug: str | None) -> Path:
    research_root = Path(__file__).resolve().parents[3]
    if topic_slug:
        return research_root / "knowledge-hub" / "runtime" / "topics" / topic_slug
    return research_root / ".sisyphus" / "drafts" / "_scratch" / "aitp-skill-discovery"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", action="append", required=True)
    parser.add_argument("--topic-slug")
    parser.add_argument("--output-dir")
    parser.add_argument("--updated-by", default="codex")
    parser.add_argument("--agent-target", default="openclaw")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir) if args.output_dir else default_output_dir(args.topic_slug)

    query_results = []
    for query in args.query:
        query_result = run_find_query(query)
        query_result["candidates"] = [
            enrich_candidate(candidate, args.agent_target) for candidate in query_result["candidates"]
        ]
        query_results.append(query_result)

    payload = {
        "updated_at": now_iso(),
        "updated_by": args.updated_by,
        "topic_slug": args.topic_slug,
        "agent_target": args.agent_target,
        "protocol_path": "research/adapters/openclaw/SKILL_ADAPTATION_PROTOCOL.md",
        "queries": query_results,
    }
    payload["overall_status"] = (
        "ready" if all(result.get("status") == "completed" for result in query_results) else "degraded"
    )

    write_json(output_dir / "skill_discovery.json", payload)
    write_text(output_dir / "skill_recommendations.md", build_markdown_report(payload))

    print(f"Skill discovery written to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
