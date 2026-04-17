#!/usr/bin/env python
"""Acceptance for the bounded LibRPA QSGW positive target contract."""

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


DEFAULT_CODE_ROOT = Path("D:/BaiduSyncdisk/Theoretical-Physics/LibRPA-develop")
DEFAULT_WRAPPER_ROOT = Path("D:/BaiduSyncdisk/repos/oh-my-LibRPA")
DEFAULT_VALIDATOR_PATH = Path("D:/BaiduSyncdisk/Theoretical-Physics/automation/validators/qsgw_validator.py")
DEFAULT_ENGINEERING_REPORT_PATH = Path(
    "D:/BaiduSyncdisk/Theoretical-Physics/obsidian-markdown/04 平时的记录/LibRPA/"
    "2026-02-27 LibRPA QSGW 单线程-多线程不一致定位与修复测试报告.md"
)
DEFAULT_CONSISTENCY_REPORT_PATH = Path(
    "D:/BaiduSyncdisk/Theoretical-Physics/obsidian-markdown/04 平时的记录/LibRPA/"
    "2026-02-27 QSGW OMP线程数一致性（LibRI确定性归约）.md"
)

REFERENCE_CASE = "H2O/really_tight iter=10"
TARGET_CANDIDATE_ID = "candidate:librpa-qsgw-deterministic-reduction-consistency-core"
TARGET_CANDIDATE_TYPE = "claim_card"
TARGET_TITLE = "LibRPA QSGW Deterministic-Reduction Thread-Consistency Core"
TARGET_SUMMARY = (
    "Bounded claim-card candidate: on the H2O/really_tight iter=10 reference case, "
    "the deterministic-reduction guard yields an identical homo_lumo_vs_iterations "
    "trajectory for OMP_NUM_THREADS=1 and OMP_NUM_THREADS=32. This is a bounded "
    "positive code-method consistency result, not a full QSGW convergence claim."
)
DEFAULT_HUMAN_REQUEST = (
    "Open a fresh first-principles topic around the bounded LibRPA QSGW "
    "deterministic-reduction consistency core. Keep the route tied to the "
    "real codebase, the H2O/really_tight iter=10 reference workflow, and the "
    "validator-backed OMP=1/32 consistency evidence."
)
DEFAULT_WORK_HUMAN_REQUEST = (
    "Treat the deterministic-reduction consistency result as the first bounded "
    "positive code-method gate for the LibRPA QSGW lane, and preserve the "
    "known non-claims about broader convergence."
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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def ensure_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Expected artifact is missing: {path}")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def excerpt_around(text: str, token: str, *, radius: int = 2) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if token in line:
            start = max(0, index - radius)
            end = min(len(lines), index + radius + 1)
            return "\n".join(lines[start:end]).strip()
    raise RuntimeError(f"Token {token!r} not found while building code anchor note.")


def render_codebase_anchor_note(
    *,
    code_root: Path,
    wrapper_root: Path,
    params_path: Path,
    task_qsgw_path: Path,
) -> str:
    params_text = params_path.read_text(encoding="utf-8")
    task_text = task_qsgw_path.read_text(encoding="utf-8")
    mixing_excerpt = excerpt_around(params_text, "qsgw_mixing_beta")
    homo_lumo_excerpt = excerpt_around(task_text, "homo_values.push_back")
    return "\n".join(
        [
            "# LibRPA QSGW Codebase Anchor",
            "",
            f"- Primary code root: `{code_root}`",
            f"- Workflow wrapper root: `{wrapper_root}`",
            f"- QSGW parameter anchor: `{params_path}`",
            f"- QSGW iteration anchor: `{task_qsgw_path}`",
            "",
            "## Why this note exists",
            "",
            "This bounded Phase 173 target is about one real LibRPA QSGW code-method "
            "surface, not a generic prose-only claim. The note fixes the exact local "
            "checkout and the key files that anchor the target contract.",
            "",
            "## Params anchor excerpt",
            "",
            "```text",
            mixing_excerpt,
            "```",
            "",
            "## Iteration / HOMO-LUMO anchor excerpt",
            "",
            "```text",
            homo_lumo_excerpt,
            "```",
            "",
            "## Bounded scope",
            "",
            "- The current target is restricted to the deterministic-reduction "
            "consistency core on the H2O/really_tight iter=10 reference case.",
            "- This note does not claim broad QSGW convergence or full-codebase closure.",
            "",
        ]
    )


def render_workflow_anchor_note(
    *,
    validator_path: Path,
    engineering_report_path: Path,
    consistency_report_path: Path,
) -> str:
    engineering_text = engineering_report_path.read_text(encoding="utf-8")
    consistency_text = consistency_report_path.read_text(encoding="utf-8")
    return "\n".join(
        [
            "# LibRPA QSGW Workflow Trust Anchor",
            "",
            f"- Validator path: `{validator_path}`",
            f"- Engineering report: `{engineering_report_path}`",
            f"- Consistency report: `{consistency_report_path}`",
            "",
            "## Positive evidence",
            "",
            "- The engineering report identifies the deterministic-reduction merge guard "
            "as the minimal fix for OMP thread inconsistency.",
            "- The consistency report records that the strict deterministic mode yields "
            "identical trajectories for OMP=1 and OMP=32 on the bounded reference case.",
            "",
            "## Required criterion",
            "",
            "- Treat the bounded target as positive only if the H2O/really_tight iter=10 "
            "trajectory is identical for OMP=1 and OMP=32 under deterministic reduction.",
            "",
            "## Explicit non-claims",
            "",
            "- Mixing-only scans do not yet prove full 1e-3 eV convergence.",
            "- This target does not close the whole QSGW workflow or every benchmark system.",
            "",
            "## Report excerpts",
            "",
            "```text",
            "ENGINEERING REPORT:",
            excerpt_around(engineering_text, "dGap = 0.0 eV", radius=3)
            if "dGap = 0.0 eV" in engineering_text
            else excerpt_around(engineering_text, "dGap_eV 0.0", radius=3),
            "```",
            "",
            "```text",
            "CONSISTENCY REPORT:",
            excerpt_around(consistency_text, "LIBRI_DETERMINISTIC_REDUCTION=1", radius=3),
            "```",
            "",
        ]
    )


def render_target_contract_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# LibRPA QSGW Positive Target Contract",
        "",
        f"- Topic slug: `{payload['topic_slug']}`",
        f"- Target candidate id: `{payload['target_candidate']['candidate_id']}`",
        f"- Target candidate type: `{payload['target_candidate']['candidate_type']}`",
        f"- Codebase root: `{payload['source_of_truth']['codebase_root']}`",
        f"- Validator path: `{payload['source_of_truth']['validator_path']}`",
        f"- Reference case: `{payload['workflow_anchor']['reference_case']}`",
        "",
        "## Positive target",
        "",
        payload["target_candidate"]["summary"],
        "",
        "## Trust contract",
        "",
    ]
    for item in payload["trust_contract"]["rules"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Explicit non-claims", ""])
    for item in payload["excluded_claims"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Source refs", ""])
    for item in payload["source_refs"]:
        lines.append(f"- `{item}`")
    lines.append("")
    return "\n".join(lines)


def build_origin_refs(source_rows: list[dict[str, Any]], source_index_path: Path) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for row in source_rows:
        source_id = str(row.get("source_id") or "").strip()
        if not source_id:
            continue
        refs.append(
            {
                "id": source_id,
                "layer": "L0",
                "object_type": "source",
                "path": str(source_index_path.relative_to(source_index_path.parents[3])).replace("\\", "/"),
                "title": str(row.get("title") or ""),
                "summary": str(row.get("summary") or "")[:240],
            }
        )
    return refs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", default=str(KERNEL_ROOT))
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--work-root")
    parser.add_argument("--topic", default="LibRPA QSGW deterministic-reduction consistency core")
    parser.add_argument(
        "--question",
        default=(
            "What is the smallest honest positive LibRPA QSGW code-method route "
            "that can be trusted before claiming broader convergence or whole-stack closure?"
        ),
    )
    parser.add_argument("--run-id", default=f"{now_stamp()}-bootstrap")
    parser.add_argument("--updated-by", default="librpa-qsgw-target-contract-acceptance")
    parser.add_argument("--code-root", default=str(DEFAULT_CODE_ROOT))
    parser.add_argument("--wrapper-root", default=str(DEFAULT_WRAPPER_ROOT))
    parser.add_argument("--validator-path", default=str(DEFAULT_VALIDATOR_PATH))
    parser.add_argument("--engineering-report-path", default=str(DEFAULT_ENGINEERING_REPORT_PATH))
    parser.add_argument("--consistency-report-path", default=str(DEFAULT_CONSISTENCY_REPORT_PATH))
    parser.add_argument("--human-request", default=DEFAULT_HUMAN_REQUEST)
    parser.add_argument("--work-human-request", default=DEFAULT_WORK_HUMAN_REQUEST)
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    package_root = Path(args.package_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    code_root = Path(args.code_root).expanduser().resolve()
    wrapper_root = Path(args.wrapper_root).expanduser().resolve()
    validator_path = Path(args.validator_path).expanduser().resolve()
    engineering_report_path = Path(args.engineering_report_path).expanduser().resolve()
    consistency_report_path = Path(args.consistency_report_path).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="lqtc-")).resolve()
    )
    kernel_root = work_root / "knowledge-hub"

    params_path = code_root / "src" / "params.h"
    task_qsgw_path = code_root / "driver" / "task_qsgw.cpp"
    for path in (
        code_root,
        wrapper_root,
        validator_path,
        engineering_report_path,
        consistency_report_path,
        params_path,
        task_qsgw_path,
    ):
        ensure_exists(path)

    engineering_text = engineering_report_path.read_text(encoding="utf-8")
    consistency_text = consistency_report_path.read_text(encoding="utf-8")
    check(
        "dGap = 0.0 eV" in engineering_text or "dGap_eV 0.0" in engineering_text,
        "Expected the LibRPA engineering report to contain the bounded positive dGap=0 evidence.",
    )
    check(
        "LIBRI_DETERMINISTIC_REDUCTION=1" in consistency_text,
        "Expected the consistency report to mention deterministic reduction explicitly.",
    )

    for relative in ("canonical", "knowledge_hub", "schemas"):
        shutil.copytree(package_root / relative, kernel_root / relative, dirs_exist_ok=True)
    (kernel_root / "runtime").mkdir(parents=True, exist_ok=True)
    (kernel_root / "source-layer" / "topics").mkdir(parents=True, exist_ok=True)
    (kernel_root / "source-layer" / "compiled").mkdir(parents=True, exist_ok=True)
    (kernel_root / "feedback" / "topics").mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        package_root / "source-layer" / "scripts",
        kernel_root / "source-layer" / "scripts",
        dirs_exist_ok=True,
    )
    for relative in ("source-layer/README.md", "source-layer/global_index.jsonl"):
        source_path = package_root / relative
        destination_path = kernel_root / relative
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        if source_path.exists():
            shutil.copy2(source_path, destination_path)
        elif not destination_path.exists():
            destination_path.write_text("", encoding="utf-8")
    for path in (package_root / "runtime").iterdir():
        if path.is_file():
            shutil.copy2(path, kernel_root / "runtime" / path.name)
    shutil.copytree(package_root / "runtime" / "scripts", kernel_root / "runtime" / "scripts", dirs_exist_ok=True)
    runtime_schemas_root = package_root / "runtime" / "schemas"
    if runtime_schemas_root.exists():
        shutil.copytree(runtime_schemas_root, kernel_root / "runtime" / "schemas", dirs_exist_ok=True)

    notes_root = work_root / "notes"
    codebase_note_path = notes_root / "librpa_qsgw_codebase_anchor.md"
    workflow_note_path = notes_root / "librpa_qsgw_workflow_anchor.md"
    write_text(
        codebase_note_path,
        render_codebase_anchor_note(
            code_root=code_root,
            wrapper_root=wrapper_root,
            params_path=params_path,
            task_qsgw_path=task_qsgw_path,
        ),
    )
    write_text(
        workflow_note_path,
        render_workflow_anchor_note(
            validator_path=validator_path,
            engineering_report_path=engineering_report_path,
            consistency_report_path=consistency_report_path,
        ),
    )

    service = AITPService(kernel_root=kernel_root, repo_root=repo_root)
    bootstrap_payload = service.new_topic(
        topic=args.topic,
        question=args.question,
        mode="first_principles",
        run_id=args.run_id,
        updated_by=args.updated_by,
        local_note_paths=[
            str(codebase_note_path),
            str(workflow_note_path),
            str(engineering_report_path),
            str(consistency_report_path),
        ],
        human_request=args.human_request,
    )
    topic_slug = str(bootstrap_payload.get("topic_slug") or "").strip()
    check(bool(topic_slug), "Expected new_topic to return a topic slug.")

    entry_audit = service.audit(topic_slug=topic_slug, phase="entry", updated_by=args.updated_by)
    work_payload = service.work_topic(
        topic_slug=topic_slug,
        question=(
            "Keep the LibRPA QSGW route bounded to the deterministic-reduction consistency core "
            "before any broader convergence or whole-stack claim."
        ),
        mode="first_principles",
        run_id=args.run_id,
        updated_by=args.updated_by,
        human_request=args.work_human_request,
        max_auto_steps=0,
        load_profile="light",
    )

    runtime_root = kernel_root / "topics" / topic_slug / "runtime"
    source_index_path = kernel_root / "topics" / topic_slug / "L0" / "source_index.jsonl"
    target_contract_path = runtime_root / "librpa_qsgw_target_contract.json"
    target_contract_note_path = runtime_root / "librpa_qsgw_target_contract.md"
    candidate_ledger_path = kernel_root / "topics" / topic_slug / "L3" / "runs" / args.run_id / "candidate_ledger.jsonl"
    source_rows = read_jsonl(source_index_path)
    check(bool(source_rows), "Expected local-note sources to be registered for the LibRPA QSGW topic.")
    origin_refs = build_origin_refs(source_rows, source_index_path)

    target_contract = {
        "contract_kind": "librpa_qsgw_positive_target",
        "status": "chosen",
        "topic_slug": topic_slug,
        "run_id": args.run_id,
        "research_mode": "first_principles",
        "source_of_truth": {
            "codebase_root": str(code_root),
            "wrapper_root": str(wrapper_root),
            "validator_path": str(validator_path),
        },
        "target_candidate": {
            "candidate_id": TARGET_CANDIDATE_ID,
            "candidate_type": TARGET_CANDIDATE_TYPE,
            "title": TARGET_TITLE,
            "summary": TARGET_SUMMARY,
        },
        "workflow_anchor": {
            "reference_case": REFERENCE_CASE,
            "positive_evidence": "deterministic reduction yields identical OMP=1 and OMP=32 trajectories",
            "engineering_report_path": str(engineering_report_path),
            "consistency_report_path": str(consistency_report_path),
        },
        "trust_contract": {
            "evidence_basis": [
                "LibRPA codebase anchor note",
                "QSGW deterministic-reduction engineering report",
                "OMP=1/32 consistency report for H2O/really_tight iter=10",
                "qsgw_validator reference criterion",
            ],
            "rules": [
                "Treat only the deterministic-reduction thread-consistency core as the positive target.",
                "Require real codebase anchors plus real workflow evidence from the H2O/really_tight iter=10 reference case.",
                "Do not reinterpret mixing-only scans as full QSGW convergence evidence.",
                "Do not claim broad multi-system or whole-stack LibRPA QSGW closure from this contract.",
            ],
            "consistency_criterion": (
                "Under deterministic reduction, the H2O/really_tight iter=10 "
                "homo_lumo_vs_iterations trajectory is identical for OMP=1 and OMP=32."
            ),
            "validator_command": (
                "python automation/validators/qsgw_validator.py --gap-delta-max 0.001 "
                "--gap-delta-window 10 --require-converged"
            ),
        },
        "known_open_gaps": [
            "mixing=0.05 at iter=60 fails the 1e-3 eV gap-delta convergence gate",
            "mixing=0.02 with history=2 at iter=120 also fails the 1e-3 eV gate",
            "hamiltonian-cut stabilizing knobs remain to be bounded separately before broader convergence claims",
        ],
        "excluded_claims": [
            "LibRPA QSGW is already fully converged in general",
            "mixing-only scans already prove 1e-3 eV convergence for the bounded reference case",
            "the whole LibRPA codebase is already ingested into authoritative L2 by this phase",
            "the bounded deterministic-reduction consistency core closes every first-principles lane",
        ],
        "source_refs": [str(row.get("source_id") or "").strip() for row in source_rows if str(row.get("source_id") or "").strip()],
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "updated_by": args.updated_by,
    }
    write_json(target_contract_path, target_contract)
    write_text(target_contract_note_path, render_target_contract_markdown(target_contract))

    candidate_row = {
        "candidate_id": TARGET_CANDIDATE_ID,
        "candidate_type": TARGET_CANDIDATE_TYPE,
        "title": TARGET_TITLE,
        "summary": TARGET_SUMMARY,
        "topic_slug": topic_slug,
        "run_id": args.run_id,
        "origin_refs": origin_refs,
        "question": args.question,
        "assumptions": [
            "The positive target is bounded to the deterministic-reduction consistency core on the H2O/really_tight iter=10 reference case.",
            "The target is code-method positive because it proves a real algorithmic/workflow consistency property before broader convergence claims.",
            "Known mixing-only convergence failures remain explicit non-claims rather than hidden debt.",
        ],
        "proposed_validation_route": "librpa-qsgw-deterministic-reduction-consistency-core-route",
        "intended_l2_targets": [
            "claim_card:librpa-qsgw-deterministic-reduction-consistency-core"
        ],
        "status": "ready_for_validation",
        "supporting_regression_question_ids": [],
        "supporting_oracle_ids": [],
        "supporting_regression_run_ids": [
            "run:QSGW_iter10_detred_guardtry_20260227_024539_t1",
            "run:QSGW_iter10_detred_guardtry_20260227_024539_t32",
        ],
        "promotion_blockers": [],
        "split_required": False,
        "cited_recovery_required": False,
        "followup_gap_ids": [],
        "topic_completion_status": "regression-stable",
    }
    write_jsonl(candidate_ledger_path, [candidate_row])

    baseline = service.scaffold_baseline(
        topic_slug=topic_slug,
        run_id=args.run_id,
        title="LibRPA QSGW deterministic-reduction thread-consistency benchmark",
        reference=str(consistency_report_path),
        agreement_criterion=(
            "Accept only if the bounded H2O/really_tight iter=10 reference case shows identical "
            "OMP=1 and OMP=32 trajectories under deterministic reduction."
        ),
        notes="Use the deterministic-reduction consistency result as the first bounded positive gate for the LibRPA QSGW lane.",
        updated_by=args.updated_by,
    )
    understanding = service.scaffold_atomic_understanding(
        topic_slug=topic_slug,
        run_id=args.run_id,
        method_title="LibRPA QSGW deterministic-reduction consistency core",
        scope_note=(
            "Treat the deterministic-reduction consistency result on the H2O/really_tight iter=10 reference "
            "workflow as the current reusable bounded code-method surface."
        ),
        updated_by=args.updated_by,
    )
    operation = service.scaffold_operation(
        topic_slug=topic_slug,
        run_id=args.run_id,
        title="LibRPA QSGW deterministic-reduction benchmark workflow",
        kind="coding",
        summary="Bounded code-method workflow for the LibRPA QSGW deterministic-reduction consistency core.",
        references=[
            str(params_path),
            str(task_qsgw_path),
            str(validator_path),
            str(consistency_report_path),
        ],
        source_paths=[
            str(codebase_note_path),
            str(workflow_note_path),
            str(engineering_report_path),
            str(consistency_report_path),
        ],
        notes="Broader first-principles claims stay blocked until the bounded deterministic-reduction consistency core is fixed as the trust gate.",
        updated_by=args.updated_by,
    )
    operation_update = service.update_operation(
        topic_slug=topic_slug,
        run_id=args.run_id,
        operation="LibRPA QSGW deterministic-reduction benchmark workflow",
        summary=(
            "The bounded LibRPA QSGW target now uses the deterministic-reduction thread-consistency result "
            "as the positive code-method gate before any broader convergence claim."
        ),
        notes=(
            "Mixing-only scans remain explicit failures; broader convergence and Hamiltonian-cut stabilization "
            "remain follow-up gaps."
        ),
        baseline_status="passed",
        artifact_paths=[str(target_contract_path), str(target_contract_note_path), str(candidate_ledger_path)],
        references=[str(target_contract_note_path), str(consistency_report_path)],
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
        summary="Use deterministic-reduction thread consistency as the first bounded LibRPA QSGW gate before broader convergence claims.",
        outcome="helpful",
        confidence=0.86,
        lane="code_method",
        evidence_refs=[
            str(target_contract_path),
            str(target_contract_note_path),
            str(consistency_report_path),
        ],
        reuse_conditions=[
            "bounded LibRPA QSGW code-method lane",
            "real codebase anchors plus validator-backed workflow evidence",
            "thread-consistency proof before broader convergence claims",
        ],
        do_not_apply_when=[
            "the route already has a stronger bounded convergence proof and no thread-consistency uncertainty remains",
        ],
        human_note="Use this before trying to promote broader first-principles or workflow-level claims.",
        updated_by=args.updated_by,
    )
    status_payload = service.topic_status(topic_slug=topic_slug, updated_by=args.updated_by)
    capability_payload = service.capability_audit(topic_slug=topic_slug, updated_by=args.updated_by)
    exit_audit = service.audit(topic_slug=topic_slug, phase="exit", updated_by=args.updated_by)

    baseline_summary_path = Path(baseline["paths"]["baseline_summary"])
    concept_map_path = Path(understanding["paths"]["atomic_concept_map"])
    operation_manifest_path = Path(operation["manifest_path"])
    operation_summary_path = Path(operation["summary_path"])
    trust_audit_path = Path(trust_audit["trust_audit_path"])
    strategy_memory_path = Path(strategy_memory["strategy_memory_path"])
    runtime_protocol_path = runtime_root / "runtime_protocol.generated.json"
    runtime_protocol_note_path = runtime_root / "runtime_protocol.generated.md"
    topic_synopsis_path = runtime_root / "topic_synopsis.json"
    pending_decisions_path = runtime_root / "pending_decisions.json"
    promotion_readiness_path = runtime_root / "promotion_readiness.json"

    for path in (
        codebase_note_path,
        workflow_note_path,
        source_index_path,
        target_contract_path,
        target_contract_note_path,
        candidate_ledger_path,
        baseline_summary_path,
        concept_map_path,
        operation_manifest_path,
        operation_summary_path,
        trust_audit_path,
        strategy_memory_path,
        runtime_protocol_path,
        runtime_protocol_note_path,
        topic_synopsis_path,
        pending_decisions_path,
        promotion_readiness_path,
    ):
        ensure_exists(path)

    runtime_protocol_note = runtime_protocol_note_path.read_text(encoding="utf-8")
    topic_state = bootstrap_payload.get("topic_state") or {}
    check(str(topic_state.get("research_mode") or "") == "first_principles", "Expected the fresh topic to stay in first_principles mode.")
    check(status_payload["load_profile"] == "light", "Expected the bounded first-principles acceptance topic to stay in light profile.")
    check(trust_audit["overall_status"] == "pass", "Expected operation trust to pass for the bounded LibRPA QSGW target contract.")
    check(any(str(row.get("source_type") or "").startswith("local_") for row in source_rows), "Expected local-note sources to be registered in the source index.")
    check("## Strategy memory" in runtime_protocol_note, "Expected runtime protocol note to surface strategy memory.")
    check(
        capability_payload["sections"]["capabilities"]["operation_trust"]["status"] == "present",
        "Expected capability audit to surface operation trust artifacts.",
    )
    check(
        str((exit_audit.get("conformance_state") or {}).get("overall_status") or "") == "pass",
        "Expected exit audit conformance to remain pass.",
    )
    payload = {
        "status": "success",
        "topic_slug": topic_slug,
        "run_id": args.run_id,
        "work_root": str(work_root),
        "kernel_root": str(kernel_root),
        "checks": {
            "research_mode": topic_state.get("research_mode"),
            "lane": status_payload["topic_synopsis"]["lane"],
            "load_profile": status_payload["load_profile"],
            "trust_status": trust_audit["overall_status"],
            "strategy_memory_status": status_payload["strategy_memory"]["status"],
            "operation_trust_status": capability_payload["sections"]["capabilities"]["operation_trust"]["status"],
            "exit_conformance": (exit_audit.get("conformance_state") or {}).get("overall_status"),
        },
        "target_contract": {
            "json_path": str(target_contract_path),
            "markdown_path": str(target_contract_note_path),
            "payload": target_contract,
        },
        "candidate": {
            "ledger_path": str(candidate_ledger_path),
            "candidate_id": TARGET_CANDIDATE_ID,
            "candidate_type": TARGET_CANDIDATE_TYPE,
            "intended_l2_targets": candidate_row["intended_l2_targets"],
        },
        "source_layer": {
            "source_index": str(source_index_path),
            "source_ids": [str(row.get("source_id") or "").strip() for row in source_rows if str(row.get("source_id") or "").strip()],
        },
        "trust_gate": {
            "baseline_summary": str(baseline_summary_path),
            "atomic_concept_map": str(concept_map_path),
            "operation_manifest": str(operation_manifest_path),
            "operation_summary": str(operation_summary_path),
            "trust_audit_path": str(trust_audit_path),
            "strategy_memory_path": str(strategy_memory_path),
        },
        "artifacts": {
            "runtime_protocol": str(runtime_protocol_path),
            "runtime_protocol_note": str(runtime_protocol_note_path),
            "topic_synopsis": str(topic_synopsis_path),
            "pending_decisions": str(pending_decisions_path),
            "promotion_readiness": str(promotion_readiness_path),
            "codebase_anchor_note": str(codebase_note_path),
            "workflow_anchor_note": str(workflow_note_path),
        },
        "evidence_inputs": {
            "code_root": str(code_root),
            "wrapper_root": str(wrapper_root),
            "validator_path": str(validator_path),
            "engineering_report_path": str(engineering_report_path),
            "consistency_report_path": str(consistency_report_path),
        },
        "entry_audit": entry_audit,
        "work_topic": work_payload,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
