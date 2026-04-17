#!/usr/bin/env python
"""Acceptance for the bounded HS toy-model positive target contract."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
KERNEL_ROOT = SCRIPT_PATH.parents[2]
REPO_ROOT = SCRIPT_PATH.parents[4]

if str(KERNEL_ROOT) not in sys.path:
    sys.path.insert(0, str(KERNEL_ROOT))

from knowledge_hub.aitp_service import AITPService  # noqa: E402


REFERENCE_TOPIC_SLUG = "haldane-shastry-chaos-transition"
REFERENCE_RUN_ID = "2026-03-27-030941-bootstrap"
REFERENCE_CANDIDATE_ID = "candidate:hs-chaos-window-finite-size-core"
NEGATIVE_COMPARATOR_ENTRY_ID = "staging:hs-model-otoc-lyapunov-exponent-regime-mismatch"
DEFAULT_HUMAN_REQUEST = (
    "Open a fresh toy-model topic for the HS-like finite-size chaos-window core, "
    "keep the target bounded to the benchmark-backed `0.4 <= alpha <= 1.0` core, "
    "and preserve the exact HS OTOC mismatch route as an explicit negative comparator."
)


def now_stamp() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d-%H%M%S")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def ensure_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Expected artifact is missing: {path}")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def rewrite_topic_relative_path(
    value: str,
    *,
    reference_topic_slug: str,
    target_topic_slug: str,
) -> str:
    return str(value).replace(
        f"topics/{reference_topic_slug}/L0/",
        f"topics/{target_topic_slug}/L0/",
    )


def clone_reference_sources(
    *,
    kernel_root: Path,
    reference_topic_slug: str,
    target_topic_slug: str,
) -> dict[str, Any]:
    reference_root = kernel_root / "topics" / reference_topic_slug / "L0"
    if not reference_root.exists():
        raise FileNotFoundError(f"Reference topic root is missing: {reference_root}")

    target_root = kernel_root / "topics" / target_topic_slug / "L0"
    target_root.mkdir(parents=True, exist_ok=True)

    reference_sources_root = reference_root / "sources"
    target_sources_root = target_root / "sources"
    if reference_sources_root.exists():
        shutil.copytree(reference_sources_root, target_sources_root, dirs_exist_ok=True)

    cloned_rows: list[dict[str, Any]] = []
    for row in read_jsonl(reference_root / "source_index.jsonl"):
        cloned = dict(row)
        cloned["topic_slug"] = target_topic_slug
        locator = dict(cloned.get("locator") or {})
        for key in ("local_path", "snapshot_path"):
            if key in locator:
                locator[key] = rewrite_topic_relative_path(
                    str(locator[key]),
                    reference_topic_slug=reference_topic_slug,
                    target_topic_slug=target_topic_slug,
                )
        cloned["locator"] = locator
        cloned_rows.append(cloned)
    write_text(
        target_root / "source_index.jsonl",
        "".join(json.dumps(row, ensure_ascii=True) + "\n" for row in cloned_rows),
    )

    topic_payload_path = reference_root / "topic.json"
    if topic_payload_path.exists():
        topic_payload = read_json(topic_payload_path)
        topic_payload["topic_slug"] = target_topic_slug
        if "slug" in topic_payload:
            topic_payload["slug"] = target_topic_slug
        write_json(target_root / "topic.json", topic_payload)

    return {
        "reference_topic_slug": reference_topic_slug,
        "target_topic_slug": target_topic_slug,
        "target_root": str(target_root),
        "source_count": len(cloned_rows),
    }


def load_reference_candidate(
    *,
    package_root: Path,
    topic_slug: str,
    run_id: str,
    candidate_id: str,
) -> dict[str, Any]:
    ledger_path = package_root / "topics" / topic_slug / "L3" / "runs" / run_id / "candidate_ledger.jsonl"
    for row in read_jsonl(ledger_path):
        if str(row.get("candidate_id") or "").strip() == candidate_id:
            return row
    raise FileNotFoundError(f"Candidate {candidate_id} was not found in {ledger_path}")


def render_target_contract_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# HS Toy-Model Positive Target Contract",
        "",
        f"- Topic slug: `{payload['topic_slug']}`",
        f"- Target candidate id: `{payload['target_candidate']['candidate_id']}`",
        f"- Target candidate type: `{payload['target_candidate']['candidate_type']}`",
        f"- Source topic slug: `{payload['source_topic_slug']}`",
        f"- Negative comparator: `{payload['negative_comparator']['entry_id']}`",
        "",
        "## Positive target",
        "",
        payload["target_candidate"]["summary"],
        "",
        "## Benchmark contract",
        "",
    ]
    for item in payload["benchmark_contract"]["rules"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Excluded claims", ""])
    for item in payload["excluded_claims"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Source refs", ""])
    for item in payload["source_refs"]:
        lines.append(f"- `{item}`")
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", default=str(KERNEL_ROOT))
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--work-root")
    parser.add_argument("--topic", default="HS-like finite-size chaos-window core")
    parser.add_argument(
        "--question",
        default=(
            "Can the benchmark-calibrated finite-size HS-like chaos-window core "
            "be made into one bounded positive toy-model target without "
            "collapsing the exact HS negative comparator?"
        ),
    )
    parser.add_argument("--human-request", default=DEFAULT_HUMAN_REQUEST)
    parser.add_argument("--reference-topic-slug", default=REFERENCE_TOPIC_SLUG)
    parser.add_argument("--reference-run-id", default=REFERENCE_RUN_ID)
    parser.add_argument("--reference-candidate-id", default=REFERENCE_CANDIDATE_ID)
    parser.add_argument("--run-id", default=f"{now_stamp()}-bootstrap")
    parser.add_argument("--updated-by", default="hs-toy-model-target-contract-acceptance")
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="hstc-")).resolve()
    )
    kernel_root = work_root / "knowledge-hub"

    for relative in ("canonical", "knowledge_hub", "schemas"):
        shutil.copytree(package_root / relative, kernel_root / relative, dirs_exist_ok=True)
    (kernel_root / "runtime").mkdir(parents=True, exist_ok=True)
    for path in (package_root / "runtime").iterdir():
        if path.is_file():
            shutil.copy2(path, kernel_root / "runtime" / path.name)
    shutil.copytree(package_root / "runtime" / "scripts", kernel_root / "runtime" / "scripts", dirs_exist_ok=True)
    runtime_schemas_root = package_root / "runtime" / "schemas"
    if runtime_schemas_root.exists():
        shutil.copytree(runtime_schemas_root, kernel_root / "runtime" / "schemas", dirs_exist_ok=True)
    reference_topic_root = package_root / "topics" / args.reference_topic_slug / "L0"
    shutil.copytree(
        reference_topic_root,
        kernel_root / "topics" / args.reference_topic_slug / "L0",
        dirs_exist_ok=True,
    )

    service = AITPService(kernel_root=kernel_root, repo_root=repo_root)
    bootstrap_payload = service.new_topic(
        topic=args.topic,
        question=args.question,
        mode="toy_model",
        run_id=args.run_id,
        updated_by=args.updated_by,
        human_request=args.human_request,
    )
    topic_slug = str(bootstrap_payload.get("topic_slug") or "").strip()
    check(bool(topic_slug), "Expected new_topic to return a topic slug.")

    entry_audit = service.audit(topic_slug=topic_slug, phase="entry", updated_by=args.updated_by)
    source_seed = clone_reference_sources(
        kernel_root=kernel_root,
        reference_topic_slug=args.reference_topic_slug,
        target_topic_slug=topic_slug,
    )
    candidate = load_reference_candidate(
        package_root=package_root,
        topic_slug=args.reference_topic_slug,
        run_id=args.reference_run_id,
        candidate_id=args.reference_candidate_id,
    )

    runtime_root = kernel_root / "topics" / topic_slug / "runtime"
    target_contract_path = runtime_root / "hs_positive_target_contract.json"
    target_contract_note_path = runtime_root / "hs_positive_target_contract.md"
    source_index_path = kernel_root / "topics" / topic_slug / "L0" / "source_index.jsonl"

    target_contract = {
        "contract_kind": "hs_toy_model_positive_target",
        "status": "chosen",
        "topic_slug": topic_slug,
        "run_id": args.run_id,
        "research_mode": "toy_model",
        "source_topic_slug": args.reference_topic_slug,
        "target_candidate": {
            "candidate_id": str(candidate["candidate_id"]),
            "candidate_type": str(candidate["candidate_type"]),
            "title": str(candidate["title"]),
            "summary": str(candidate["summary"]),
            "supporting_regression_question_ids": list(candidate.get("supporting_regression_question_ids") or []),
            "supporting_oracle_ids": list(candidate.get("supporting_oracle_ids") or []),
            "supporting_regression_run_ids": list(candidate.get("supporting_regression_run_ids") or []),
        },
        "benchmark_contract": {
            "evidence_basis": [
                "benchmark-calibrated finite-size Fisher ED protocol",
                "benchmark-calibrated OTOC observable",
                "paper-convention Krylov observable",
                "supporting gap-ratio evidence only as secondary support",
            ],
            "rules": [
                "Treat only the robust core window `0.4 <= alpha <= 1.0` as the positive target.",
                "Do not promote the weaker `1.2 <= alpha <= 1.4` shoulder as part of this bounded claim.",
                "Do not reinterpret the exact HS `alpha = 2` point as a positive chaos result.",
                "Do not claim thermodynamic closure, operator independence, or larger-system continuation from this contract.",
            ],
        },
        "negative_comparator": {
            "entry_id": NEGATIVE_COMPARATOR_ENTRY_ID,
            "title": "HS model OTOC Lyapunov exponent: regime mismatch",
            "reason": "Exact HS `alpha = 2` remains an explicit negative comparator, not part of the positive target.",
        },
        "excluded_claims": [
            "exact HS `alpha = 2` exhibits positive OTOC Lyapunov chaos",
            "the weak `1.2 <= alpha <= 1.4` shoulder is already robust enough for promotion",
            "the bounded finite-size core closes the whole topic in the thermodynamic limit",
            "operator robustness or larger-system continuation are already proved",
        ],
        "source_refs": [
            str(item.get("id") or "").strip()
            for item in (candidate.get("origin_refs") or [])
            if str(item.get("id") or "").strip()
        ],
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "updated_by": args.updated_by,
    }
    write_json(target_contract_path, target_contract)
    write_text(target_contract_note_path, render_target_contract_markdown(target_contract))

    baseline = service.scaffold_baseline(
        topic_slug=topic_slug,
        run_id=args.run_id,
        title="HS-like finite-size chaos-window benchmark gate",
        reference=str(target_contract_note_path),
        agreement_criterion=(
            "Accept only if the positive target stays restricted to the "
            "`0.4 <= alpha <= 1.0` core and keeps exact HS `alpha = 2` as the "
            "negative comparator."
        ),
        updated_by=args.updated_by,
        notes="Benchmark-calibrated finite-size ED evidence is the only trust basis for this bounded positive target.",
    )
    operation = service.scaffold_operation(
        topic_slug=topic_slug,
        run_id=args.run_id,
        title="HS-like finite-size chaos-window positive target contract",
        kind="numerical",
        summary="Bounded toy-model contract for the benchmark-backed HS-like finite-size chaos-window core.",
        references=[str(target_contract_path)],
        source_paths=[str(source_index_path)],
        notes="Promotion is blocked until the contract stays within the robust finite-size core and excludes the exact-HS negative comparator.",
        updated_by=args.updated_by,
    )
    operation_update = service.update_operation(
        topic_slug=topic_slug,
        run_id=args.run_id,
        operation="HS-like finite-size chaos-window positive target contract",
        summary="The fresh toy-model topic now carries one bounded HS-like positive target contract backed by the existing benchmark-calibrated finite-size evidence chain.",
        notes="Exact HS alpha=2 remains negative comparator; 1.2<=alpha<=1.4 shoulder remains excluded from the bounded positive target.",
        baseline_status="passed",
        artifact_paths=[str(target_contract_path), str(target_contract_note_path)],
        references=[str(target_contract_note_path)],
        updated_by=args.updated_by,
    )
    trust_audit = service.audit_operation_trust(
        topic_slug=topic_slug,
        run_id=args.run_id,
        updated_by=args.updated_by,
    )
    strategy_memory = service.record_strategy_memory(
        topic_slug=topic_slug,
        run_id=args.run_id,
        strategy_type="verification_guardrail",
        summary="Promote only the benchmark-backed HS-like finite-size core and keep the exact HS OTOC route explicit as a negative comparator.",
        outcome="helpful",
        confidence=0.84,
        lane="toy_model",
        evidence_refs=[str(target_contract_path), str(target_contract_note_path)],
        reuse_conditions=[
            "HS or HS-like toy-model widening after an already-proven exact-HS negative route",
            "bounded finite-size evidence chain with explicit excluded claims",
        ],
        do_not_apply_when=[
            "the target has already widened to larger-system continuation or thermodynamic claims",
        ],
        human_note="Use this before any toy-model promotion attempt in the HS family.",
        updated_by=args.updated_by,
    )
    status_payload = service.topic_status(topic_slug=topic_slug, updated_by=args.updated_by)
    exit_audit = service.audit(topic_slug=topic_slug, phase="exit", updated_by=args.updated_by)

    baseline_summary_path = Path(baseline["paths"]["baseline_summary"])
    operation_manifest_path = Path(operation["manifest_path"])
    operation_summary_path = Path(operation["summary_path"])
    trust_audit_path = Path(trust_audit["trust_audit_path"])
    strategy_memory_path = Path(strategy_memory["strategy_memory_path"])

    for path in (
        target_contract_path,
        target_contract_note_path,
        source_index_path,
        baseline_summary_path,
        operation_manifest_path,
        operation_summary_path,
        trust_audit_path,
        strategy_memory_path,
    ):
        ensure_exists(path)

    check(str(candidate.get("candidate_type") or "") == "claim_card", "Expected the chosen positive target to be a claim card.")
    check(str(candidate.get("status") or "") == "ready_for_validation", "Expected the reference candidate to be ready for validation.")
    check(not list(candidate.get("promotion_blockers") or []), "Expected the reference candidate to have no promotion blockers.")
    check(
        "0.4 <= alpha <= 1.0" in json.dumps(target_contract, ensure_ascii=False),
        "Expected the target contract to preserve the robust finite-size core window.",
    )
    check(
        "1.2 <= alpha <= 1.4" in json.dumps(target_contract, ensure_ascii=False),
        "Expected the target contract to keep the weak shoulder explicit as excluded.",
    )
    check(
        NEGATIVE_COMPARATOR_ENTRY_ID in json.dumps(target_contract, ensure_ascii=False),
        "Expected the exact-HS negative comparator to stay explicit.",
    )
    check(
        str((bootstrap_payload.get("topic_state") or {}).get("research_mode") or "") == "toy_model",
        "Expected the fresh topic to bootstrap in toy_model mode.",
    )
    check(
        str(trust_audit.get("overall_status") or "") == "pass",
        "Expected the benchmark contract operation trust audit to pass.",
    )
    check(
        str((exit_audit.get("conformance_state") or {}).get("overall_status") or "") == "pass",
        "Expected exit conformance to remain pass.",
    )
    check(source_seed["source_count"] > 0, "Expected cloned HS-like source rows on the fresh toy-model topic.")
    check(
        str(status_payload.get("research_mode") or "") == "toy_model",
        "Expected topic status to report toy_model mode.",
    )

    payload = {
        "status": "success",
        "topic_slug": topic_slug,
        "run_id": args.run_id,
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "source_seed": source_seed,
        "entry_audit": entry_audit,
        "target_contract": {
            "json_path": str(target_contract_path),
            "markdown_path": str(target_contract_note_path),
            "payload": target_contract,
        },
        "trust_gate": {
            "baseline_summary": str(baseline_summary_path),
            "operation_manifest": str(operation_manifest_path),
            "operation_summary": str(operation_summary_path),
            "operation_manifest_payload": operation_update["manifest"],
            "trust_audit_path": str(trust_audit_path),
            "overall_status": trust_audit["overall_status"],
        },
        "strategy_memory": {
            "path": str(strategy_memory_path),
            "status": (status_payload.get("strategy_memory") or {}).get("status"),
        },
        "checks": {
            "research_mode": str((bootstrap_payload.get("topic_state") or {}).get("research_mode") or ""),
            "candidate_id": str(candidate["candidate_id"]),
            "candidate_status": str(candidate.get("status") or ""),
            "candidate_type": str(candidate.get("candidate_type") or ""),
            "trust_status": str(trust_audit.get("overall_status") or ""),
            "exit_conformance": str((exit_audit.get("conformance_state") or {}).get("overall_status") or ""),
            "source_count": source_seed["source_count"],
        },
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
