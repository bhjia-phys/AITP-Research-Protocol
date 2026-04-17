#!/usr/bin/env python
"""Cross-platform real-topic acceptance for a benchmark-first code-method lane."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
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


def now_stamp() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d-%H%M%S")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def ensure_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Expected artifact is missing: {path}")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def create_minimal_tpkn_backend(target_root: Path) -> None:
    for relative in (
        "docs",
        "schema",
        "scripts",
        "sources",
        "units/concepts",
        "units/definitions",
        "units/notations",
        "units/assumptions",
        "units/regimes",
        "units/theorems",
        "units/claims",
        "units/proof-fragments",
        "units/derivation-steps",
        "units/derivations",
        "units/methods",
        "units/topic-skill-projections",
        "units/bridges",
        "units/examples",
        "units/caveats",
        "units/equivalences",
        "units/symbol-bindings",
        "units/equations",
        "units/quantities",
        "units/models",
        "units/source-maps",
        "units/warnings",
        "edges",
        "indexes",
        "portal",
        "human-mirror",
    ):
        (target_root / relative).mkdir(parents=True, exist_ok=True)
    for relative in (
        "docs/PROTOCOLS.md",
        "docs/L2_RETRIEVAL_PROTOCOL.md",
        "docs/OBJECT_MODEL.md",
        "docs/L2_BRIDGE_PROTOCOL.md",
    ):
        (target_root / relative).write_text("# Minimal TPKN backend seed\n", encoding="utf-8")
    (target_root / "edges" / "edges.jsonl").write_text("", encoding="utf-8")
    write_json(target_root / "schema" / "unit.schema.json", {"title": "minimal-unit-schema"})
    write_json(target_root / "schema" / "source-manifest.schema.json", {"title": "minimal-source-schema"})
    (target_root / "scripts" / "kb.py").write_text(
        """from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNIT_DIRS = {
    "concept": ROOT / "units" / "concepts",
    "definition": ROOT / "units" / "definitions",
    "notation": ROOT / "units" / "notations",
    "assumption": ROOT / "units" / "assumptions",
    "regime": ROOT / "units" / "regimes",
    "theorem": ROOT / "units" / "theorems",
    "claim": ROOT / "units" / "claims",
    "proof_fragment": ROOT / "units" / "proof-fragments",
    "derivation_step": ROOT / "units" / "derivation-steps",
    "derivation": ROOT / "units" / "derivations",
    "method": ROOT / "units" / "methods",
    "topic_skill_projection": ROOT / "units" / "topic-skill-projections",
    "bridge": ROOT / "units" / "bridges",
    "example": ROOT / "units" / "examples",
    "caveat": ROOT / "units" / "caveats",
    "equivalence": ROOT / "units" / "equivalences",
    "symbol_binding": ROOT / "units" / "symbol-bindings",
    "equation": ROOT / "units" / "equations",
    "quantity": ROOT / "units" / "quantities",
    "model": ROOT / "units" / "models",
    "source_map": ROOT / "units" / "source-maps",
    "warning": ROOT / "units" / "warnings",
}

def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def build() -> None:
    rows = []
    for unit_dir in UNIT_DIRS.values():
        unit_dir.mkdir(parents=True, exist_ok=True)
        for path in sorted(unit_dir.glob("*.json")):
            payload = read_json(path)
            rows.append(
                {
                    "id": payload["id"],
                    "type": payload["type"],
                    "title": payload["title"],
                    "summary": payload["summary"],
                    "path": str(path.relative_to(ROOT)),
                }
            )
    unit_index = ROOT / "indexes" / "unit_index.jsonl"
    unit_index.parent.mkdir(parents=True, exist_ok=True)
    unit_index.write_text(
        "".join(json.dumps(row, ensure_ascii=True) + "\\n" for row in rows),
        encoding="utf-8",
    )

def main() -> int:
    if len(sys.argv) < 2:
        return 1
    command = sys.argv[1]
    if command == "check":
        for unit_dir in UNIT_DIRS.values():
            unit_dir.mkdir(parents=True, exist_ok=True)
        return 0
    if command == "build":
        build()
        return 0
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
""",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel-root", default=str(KERNEL_ROOT))
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--work-root")
    parser.add_argument("--topic", default="TFIM benchmark-first code-method acceptance")
    parser.add_argument("--topic-slug", default=f"tfim-code-method-acceptance-{now_stamp()}")
    parser.add_argument("--run-id", default=f"{now_stamp()}-tfim-code-method")
    parser.add_argument("--updated-by", default="tfim-code-method-acceptance")
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    kernel_root = Path(args.kernel_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    work_root = (
        Path(args.work_root).expanduser().resolve()
        if args.work_root
        else Path(tempfile.mkdtemp(prefix="aitp-code-method-acceptance-")).resolve()
    )
    work_root.mkdir(parents=True, exist_ok=True)

    tool_path = kernel_root / "validation" / "tools" / "tfim_exact_diagonalization.py"
    config_template = kernel_root / "validation" / "templates" / "toy-model-numeric" / "tfim-gap.config.template.json"
    config_path = work_root / "configs" / "tfim-gap-config.json"
    result_path = work_root / "results" / "tfim-gap-result.json"
    note_path = work_root / "notes" / "tfim-gap-benchmark.md"
    tpkn_work_root = work_root / "topic-skill-projection-backend"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.parent.mkdir(parents=True, exist_ok=True)
    create_minimal_tpkn_backend(tpkn_work_root)

    shutil.copyfile(config_template, config_path)
    config_payload = read_json(config_path)
    config_payload["summary_title"] = "TFIM benchmark-first code-method acceptance"
    config_payload["notes"] = (
        "This bounded acceptance note is used to test a code-backed benchmark-first AITP lane. "
        "It is not a full-theory or larger-system claim."
    )
    config_path.write_text(json.dumps(config_payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    subprocess.run(
        [
            sys.executable,
            str(tool_path),
            "--config",
            str(config_path),
            "--output",
            str(result_path),
            "--summary-note",
            str(note_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    service = AITPService(kernel_root=kernel_root, repo_root=repo_root)
    human_request = (
        "Open a real code-backed AITP topic around the TFIM exact-diagonalization helper. "
        "Treat the smallest exact benchmark as the gate before any broader workflow or method claims, "
        "and keep the route honest about bounded code-method scope."
    )
    question = (
        "What is the smallest honest benchmark-first code-method route for the TFIM exact-diagonalization helper "
        "before claiming broader workflow confidence?"
    )

    opened = service.new_topic(
        topic=args.topic,
        question=question,
        mode="code_method",
        run_id=args.run_id,
        updated_by=args.updated_by,
        local_note_paths=[str(note_path)],
        human_request=human_request,
    )
    topic_slug = str(opened["topic_slug"])
    runtime_root = kernel_root / "topics" / topic_slug / "runtime"

    work_payload = service.work_topic(
        topic_slug=topic_slug,
        question=(
            "Keep the TFIM helper on a benchmark-first route and use the bounded exact result before making "
            "broader code-path claims."
        ),
        mode="code_method",
        run_id=args.run_id,
        updated_by=args.updated_by,
        human_request=(
            "Keep the benchmark-first route bounded, prefer the small exact TFIM result, and treat broader "
            "workflow changes as downstream of the benchmark gate."
        ),
        max_auto_steps=0,
        load_profile="light",
    )

    baseline = service.scaffold_baseline(
        topic_slug=topic_slug,
        run_id=args.run_id,
        title="TFIM exact-diagonalization small-system benchmark",
        reference=str(tool_path),
        agreement_criterion="The configured exact-diagonalization run produces a persisted result JSON and summary note.",
        notes="Use the tiny public TFIM helper as the benchmark-first gate for this bounded code-method lane.",
        updated_by=args.updated_by,
    )
    understanding = service.scaffold_atomic_understanding(
        topic_slug=topic_slug,
        run_id=args.run_id,
        method_title="TFIM exact-diagonalization helper",
        scope_note="Treat the helper and its finite-size output as the current reusable code-backed method surface.",
        updated_by=args.updated_by,
    )
    operation = service.scaffold_operation(
        topic_slug=topic_slug,
        run_id=args.run_id,
        title="TFIM exact-diagonalization benchmark workflow",
        kind="coding",
        summary="Benchmark-first code-backed workflow for the TFIM exact-diagonalization helper.",
        references=[str(tool_path), str(config_template)],
        source_paths=[str(tool_path), str(config_path), str(note_path)],
        notes="Coding claims stay blocked until the exact benchmark result is persisted and reviewed.",
        updated_by=args.updated_by,
    )
    operation_update = service.update_operation(
        topic_slug=topic_slug,
        run_id=args.run_id,
        operation="TFIM exact-diagonalization benchmark workflow",
        summary="The bounded exact benchmark was reproduced for the TFIM helper before any broader code-path claim.",
        notes="Benchmark-first gate satisfied for the current code-backed acceptance lane.",
        baseline_status="passed",
        artifact_paths=[str(result_path), str(note_path)],
        references=[str(result_path)],
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
        summary="Close the exact benchmark before claiming broader code-method confidence.",
        outcome="helpful",
        confidence=0.82,
        lane="code_method",
        evidence_refs=[str(result_path), str(note_path)],
        reuse_conditions=[
            "code-backed benchmark-first lane",
            "small-system exact route",
            "workflow changes gated by a persisted benchmark artifact",
        ],
        do_not_apply_when=[
            "the route already has a stronger executed benchmark and no code-path uncertainty remains",
        ],
        human_note="Use this before larger refactors or larger-system inference.",
        updated_by=args.updated_by,
    )
    projection_payload = service.project_topic_skill(
        topic_slug=topic_slug,
        updated_by=args.updated_by,
    )
    projection = projection_payload["topic_skill_projection"]
    projection_candidate = projection_payload["topic_skill_projection_candidate"]
    check(str(projection.get("status") or "") == "available", "Expected the TFIM projection to be available.")
    check(projection_candidate is not None, "Expected the TFIM projection to materialize an L3 candidate.")
    request_payload = service.request_promotion(
        topic_slug=topic_slug,
        candidate_id=projection_candidate["candidate_id"],
        run_id=args.run_id,
        backend_id="backend:theoretical-physics-knowledge-network",
        target_backend_root=str(tpkn_work_root),
        requested_by=args.updated_by,
    )
    approve_payload = service.approve_promotion(
        topic_slug=topic_slug,
        candidate_id=projection_candidate["candidate_id"],
        run_id=args.run_id,
        approved_by=args.updated_by,
    )
    promote_payload = service.promote_candidate(
        topic_slug=topic_slug,
        candidate_id=projection_candidate["candidate_id"],
        run_id=args.run_id,
        promoted_by=args.updated_by,
        target_backend_root=str(tpkn_work_root),
        domain="toy-models",
        subdomain="tfim-code-method",
    )
    status_payload = service.topic_status(topic_slug=topic_slug, updated_by=args.updated_by)
    next_payload = service.topic_next(topic_slug=topic_slug, updated_by=args.updated_by)
    capability_payload = service.capability_audit(topic_slug=topic_slug, updated_by=args.updated_by)
    current_topic = service.get_current_topic_memory()
    exit_audit = service.audit(topic_slug=topic_slug, phase="exit", updated_by=args.updated_by)

    source_index_path = kernel_root / "topics" / topic_slug / "L0" / "source_index.jsonl"
    runtime_protocol_path = runtime_root / "runtime_protocol.generated.json"
    runtime_protocol_note_path = runtime_root / "runtime_protocol.generated.md"
    topic_synopsis_path = runtime_root / "topic_synopsis.json"
    pending_decisions_path = runtime_root / "pending_decisions.json"
    promotion_readiness_path = runtime_root / "promotion_readiness.json"
    strategy_memory_path = Path(strategy_memory["strategy_memory_path"])
    projection_path = Path(projection_payload["topic_skill_projection_path"])
    projection_note_path = Path(projection_payload["topic_skill_projection_note_path"])
    operation_manifest_path = Path(operation["manifest_path"])
    operation_summary_path = Path(operation["summary_path"])
    baseline_summary_path = Path(baseline["paths"]["baseline_summary"])
    concept_map_path = Path(understanding["paths"]["atomic_concept_map"])
    trust_audit_path = Path(trust_audit["trust_audit_path"])
    promotion_gate_path = runtime_root / "promotion_gate.json"
    promoted_unit_path = Path(promote_payload["target_unit_path"])

    for path in (
        config_path,
        result_path,
        note_path,
        source_index_path,
        runtime_protocol_path,
        runtime_protocol_note_path,
        topic_synopsis_path,
        pending_decisions_path,
        promotion_readiness_path,
        strategy_memory_path,
        projection_path,
        projection_note_path,
        operation_manifest_path,
        operation_summary_path,
        baseline_summary_path,
        concept_map_path,
        trust_audit_path,
        promotion_gate_path,
        promoted_unit_path,
    ):
        ensure_exists(path)

    source_rows = read_jsonl(source_index_path)
    manifest_payload = read_json(operation_manifest_path)
    protocol_note = runtime_protocol_note_path.read_text(encoding="utf-8")

    check(status_payload["topic_synopsis"]["lane"] == "code_method", "Expected the acceptance topic to land in the code_method lane.")
    check(status_payload["load_profile"] == "light", "Expected the code-method acceptance topic to stay in light profile.")
    check(trust_audit["overall_status"] == "pass", "Expected operation trust to pass after the exact benchmark gate closed.")
    check(manifest_payload["baseline_required"] is True, "Expected the coding operation to require a baseline gate.")
    check(str(manifest_payload["baseline_status"]) == "passed", "Expected the coding operation baseline to be marked passed.")
    check(status_payload["strategy_memory"]["status"] == "available", "Expected strategy memory to be available after recording a row.")
    check(status_payload["topic_skill_projection"]["status"] == "available", "Expected topic status to surface the available projection.")
    check(capability_payload["sections"]["capabilities"]["operation_trust"]["status"] == "present", "Expected capability audit to surface operation trust artifacts.")
    check(str(current_topic.get("topic_slug") or "") == topic_slug, "Expected current-topic memory to point at the code-method acceptance topic.")
    check(str((exit_audit.get("conformance_state") or {}).get("overall_status") or "") == "pass", "Expected exit audit conformance to remain pass.")
    check(any(str(row.get("source_type") or "") == "local_note" for row in source_rows), "Expected the generated benchmark note to be registered as a local-note source.")
    check("## Strategy memory" in protocol_note, "Expected runtime protocol note to surface strategy memory.")
    check("## Topic skill projection" in protocol_note, "Expected runtime protocol note to surface the topic-skill projection.")
    check(
        any(str(row.get("path") or "").endswith("topic_skill_projection.active.md") for row in status_payload["must_read_now"]),
        "Expected runtime read-path exposure for the available topic-skill projection.",
    )
    check(
        "code-backed benchmark-first lane" in json.dumps(read_jsonl(strategy_memory_path), ensure_ascii=False),
        "Expected the persisted strategy-memory row to preserve reuse conditions for the code-backed lane.",
    )
    check("topic-skill-projections" in str(promoted_unit_path).replace("\\", "/"), "Expected promoted projection to land in units/topic-skill-projections/.")
    check(read_json(promoted_unit_path).get("type") == "topic_skill_projection", "Expected promoted unit type to be topic_skill_projection.")

    payload: dict[str, Any] = {
        "status": "success",
        "topic_slug": topic_slug,
        "run_id": args.run_id,
        "work_root": str(work_root),
        "tpkn_work_root": str(tpkn_work_root),
        "checks": {
            "lane": status_payload["topic_synopsis"]["lane"],
            "load_profile": status_payload["load_profile"],
            "trust_status": trust_audit["overall_status"],
            "strategy_memory_status": status_payload["strategy_memory"]["status"],
            "topic_skill_projection_status": status_payload["topic_skill_projection"]["status"],
            "current_topic_slug": current_topic.get("topic_slug"),
            "must_read_now_count": len(status_payload["must_read_now"]),
            "next_action_summary": next_payload.get("selected_action_summary"),
            "exit_conformance": (exit_audit.get("conformance_state") or {}).get("overall_status"),
        },
        "artifacts": {
            "config_path": str(config_path),
            "result_path": str(result_path),
            "summary_note": str(note_path),
            "source_index": str(source_index_path),
            "runtime_protocol": str(runtime_protocol_path),
            "runtime_protocol_note": str(runtime_protocol_note_path),
            "topic_synopsis": str(topic_synopsis_path),
            "pending_decisions": str(pending_decisions_path),
            "promotion_readiness": str(promotion_readiness_path),
            "topic_skill_projection": str(projection_path),
            "topic_skill_projection_note": str(projection_note_path),
            "baseline_summary": str(baseline_summary_path),
            "atomic_concept_map": str(concept_map_path),
            "operation_manifest": str(operation_manifest_path),
            "operation_summary": str(operation_summary_path),
            "trust_audit": str(trust_audit_path),
            "strategy_memory": str(strategy_memory_path),
            "promotion_gate": str(promotion_gate_path),
            "promoted_unit": str(promoted_unit_path),
        },
        "status_payload": {
            "strategy_memory": status_payload["strategy_memory"],
            "topic_skill_projection": status_payload["topic_skill_projection"],
            "promotion_readiness": status_payload["promotion_readiness"],
            "open_gap_summary": status_payload["open_gap_summary"],
        },
        "operation_manifest": operation_update["manifest"],
        "projection_candidate": projection_candidate,
        "promotion": {
            "request": request_payload,
            "approve": approve_payload,
            "promote": promote_payload,
        },
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
