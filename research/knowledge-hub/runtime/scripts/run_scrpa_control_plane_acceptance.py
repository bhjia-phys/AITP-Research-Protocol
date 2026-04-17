#!/usr/bin/env python
"""Real-topic acceptance for control-plane and paired-backend governance."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
KERNEL_ROOT = SCRIPT_PATH.parents[2]
REPO_ROOT = SCRIPT_PATH.parents[4]
SCRPA_TOPIC_SCRIPT = SCRIPT_PATH.with_name("run_scrpa_thesis_topic_acceptance.py")

if str(KERNEL_ROOT) not in sys.path:
    sys.path.insert(0, str(KERNEL_ROOT))

from knowledge_hub.aitp_service import AITPService  # noqa: E402


def now_stamp() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d-%H%M%S")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel-root", default=str(KERNEL_ROOT))
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--theory-workspace-root")
    parser.add_argument("--thesis-root")
    parser.add_argument("--topic-slug", default=f"scrpa-control-plane-acceptance-{now_stamp()}")
    parser.add_argument("--updated-by", default="scrpa-control-plane-acceptance")
    parser.add_argument("--json", action="store_true")
    return parser


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def run_json_command(command: list[str], *, cwd: Path | None = None) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        raise RuntimeError(f"{' '.join(command)} failed: {detail}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Expected JSON output from {' '.join(command)}") from exc


def run_cli_json(*, kernel_root: Path, repo_root: Path, args: list[str]) -> dict[str, Any]:
    return run_json_command(
        [
            sys.executable,
            "-m",
            "knowledge_hub.aitp_cli",
            "--kernel-root",
            str(kernel_root),
            "--repo-root",
            str(repo_root),
            *args,
        ],
        cwd=kernel_root,
    )


def run_scrpa_topic_acceptance(args: argparse.Namespace) -> dict[str, Any]:
    acceptance_topic = f"scRPA variational closure from thesis control plane acceptance {args.topic_slug}"
    command = [
        sys.executable,
        str(SCRPA_TOPIC_SCRIPT),
        "--kernel-root",
        args.kernel_root,
        "--repo-root",
        args.repo_root,
        "--topic",
        acceptance_topic,
        "--topic-slug",
        args.topic_slug,
        "--updated-by",
        args.updated_by,
        "--json",
    ]
    if args.theory_workspace_root:
        command.extend(["--theory-workspace-root", args.theory_workspace_root])
    if args.thesis_root:
        command.extend(["--thesis-root", args.thesis_root])
    return run_json_command(command)


def build_backend_bridges(*, workspace_root: Path, repo_root: Path) -> list[dict[str, Any]]:
    tpkn_root = (repo_root.parent / "theoretical-physics-knowledge-network").resolve()
    return [
        {
            "backend_id": "backend:theoretical-physics-brain",
            "title": "Theoretical Physics Brain",
            "backend_type": "human_note_library",
            "status": "active",
            "card_status": "present",
            "card_path": "canonical/backends/theoretical-physics-brain.json",
            "backend_root": str(workspace_root),
            "artifact_kinds": ["formal_theory_note"],
            "canonical_targets": ["concept", "theorem_card"],
            "l0_registration_script": "source-layer/scripts/register_local_note_source.py",
            "source_count": 1,
        },
        {
            "backend_id": "backend:theoretical-physics-knowledge-network",
            "title": "Theoretical Physics Knowledge Network",
            "backend_type": "mixed_local_library",
            "status": "active",
            "card_status": "present",
            "card_path": "canonical/backends/theoretical-physics-knowledge-network.json",
            "backend_root": str(tpkn_root),
            "artifact_kinds": ["typed_unit"],
            "canonical_targets": ["concept", "theorem_card"],
            "l0_registration_script": "source-layer/scripts/register_local_note_source.py",
            "source_count": 1,
        },
    ]


def materialize_control_plane_runtime(
    *,
    service: AITPService,
    repo_root: Path,
    topic_slug: str,
    workspace_root: Path,
    updated_by: str,
) -> Path:
    runtime_root = service.kernel_root / "topics" / topic_slug / "runtime"
    ensure_exists(runtime_root / "topic_state.json")

    service.steer_topic(
        topic_slug=topic_slug,
        innovation_direction="Keep the thesis-backed variational-closure route explicit and do not pretend numerical closure already exists.",
        decision="redirect",
        updated_by=updated_by,
        human_request="Redirect the topic to an explicit variational-closure route and hold for review.",
    )
    service.pause_topic(
        topic_slug=topic_slug,
        updated_by=updated_by,
        human_request="Pause after the redirect so the operator can review the control-plane state.",
    )

    topic_state = read_json(runtime_root / "topic_state.json")
    topic_state["backend_bridges"] = build_backend_bridges(workspace_root=workspace_root, repo_root=repo_root)
    write_json(runtime_root / "topic_state.json", topic_state)

    checkpoint_note_path = runtime_root / "operator_checkpoint.active.md"
    write_json(
        runtime_root / "operator_checkpoint.active.json",
        {
            "status": "requested",
            "checkpoint_kind": "operator_review",
            "active": True,
            "note_path": str(checkpoint_note_path),
        },
    )
    write_text(
        checkpoint_note_path,
        "# Operator checkpoint\n\nReview the redirected scRPA control-plane route before continuing.\n",
    )
    write_json(
        runtime_root / "promotion_gate.json",
        {
            "status": "pending_human_approval",
            "candidate_id": "candidate:scrpa-control-plane-acceptance",
            "backend_id": "backend:theoretical-physics-knowledge-network",
            "approved_by": "",
        },
    )
    write_text(
        runtime_root / "promotion_gate.md",
        "# Promotion gate\n\nPending human approval for the bounded scRPA control-plane acceptance fixture.\n",
    )
    service.refresh_runtime_context(
        topic_slug=topic_slug,
        updated_by=updated_by,
        human_request="Refresh the runtime after control-plane and paired-backend acceptance seeding.",
        load_profile="full",
    )
    return runtime_root


def main() -> int:
    args = build_parser().parse_args()
    kernel_root = Path(args.kernel_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()

    scrpa_payload = run_scrpa_topic_acceptance(args)
    topic_slug = str(scrpa_payload["topic_slug"])
    workspace_root = Path(scrpa_payload["workspace_root"]).expanduser().resolve()
    service = AITPService(kernel_root=kernel_root, repo_root=repo_root)
    runtime_root = materialize_control_plane_runtime(
        service=service,
        repo_root=repo_root,
        topic_slug=topic_slug,
        workspace_root=workspace_root,
        updated_by=args.updated_by,
    )

    doctor_payload = run_cli_json(kernel_root=kernel_root, repo_root=repo_root, args=["doctor", "--json"])
    status_payload = run_cli_json(
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["status", "--topic-slug", topic_slug, "--json"],
    )
    paired_payload = run_cli_json(
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["paired-backend-audit", "--topic-slug", topic_slug, "--json"],
    )
    h_plane_payload = run_cli_json(
        kernel_root=kernel_root,
        repo_root=repo_root,
        args=["h-plane-audit", "--topic-slug", topic_slug, "--json"],
    )
    capability_payload = service.capability_audit(topic_slug=topic_slug, updated_by=args.updated_by)

    capability_registry_path = Path(capability_payload["capability_registry_path"])
    capability_report_path = Path(capability_payload["capability_report_path"])
    paired_audit_path = Path(paired_payload["audit_path"])
    paired_audit_note_path = Path(paired_payload["audit_note_path"])
    h_plane_audit_path = Path(h_plane_payload["audit_path"])
    h_plane_audit_note_path = Path(h_plane_payload["audit_note_path"])

    for path in (
        runtime_root / "runtime_protocol.generated.json",
        capability_registry_path,
        capability_report_path,
        paired_audit_path,
        paired_audit_note_path,
        h_plane_audit_path,
        h_plane_audit_note_path,
    ):
        ensure_exists(path)

    check(
        doctor_payload["control_plane_contracts"]["unified_architecture"]["status"] == "present",
        "Expected doctor to expose the unified architecture doc through control_plane_contracts.",
    )
    check(
        doctor_payload["control_plane_surfaces"]["paired_backend_audit"]["command"]
        == "aitp paired-backend-audit --topic-slug <topic_slug>",
        "Expected doctor to expose the paired-backend audit command.",
    )
    check("control_plane" in status_payload, "Expected status to expose control_plane.")
    check("h_plane" in status_payload, "Expected status to expose h_plane.")
    check(
        status_payload["h_plane"]["steering"]["status"] == "active_redirect",
        "Expected status to expose active redirect steering.",
    )
    check(
        status_payload["h_plane"]["registry"]["operator_status"] == "paused",
        "Expected status to expose paused operator status.",
    )
    check(
        status_payload["control_plane"]["h_plane"]["checkpoint_status"] == "requested",
        "Expected status to expose the requested checkpoint through control_plane.h_plane.",
    )
    check(
        paired_payload["pairing_status"] == "paired_active",
        "Expected paired-backend audit to detect the active theoretical-physics pair.",
    )
    check(
        paired_payload["drift_status"] == "audit_required",
        "Expected paired-backend audit to require a bounded drift audit.",
    )
    check(
        h_plane_payload["overall_status"] == "active_human_control",
        "Expected H-plane audit to report active human control.",
    )
    check(
        h_plane_payload["approval"]["status"] == "pending_human_approval",
        "Expected H-plane audit to expose pending human approval.",
    )
    check(
        capability_payload["sections"]["control_plane"]["status"]["status"] == "present",
        "Expected capability audit to expose the control-plane section.",
    )
    check(
        capability_payload["sections"]["h_plane"]["status"]["status"] == "present",
        "Expected capability audit to expose the H-plane section.",
    )
    check(
        capability_payload["sections"]["paired_backends"]["status"]["status"] == "present",
        "Expected capability audit to expose the paired-backend section.",
    )

    payload: dict[str, Any] = {
        "status": "success",
        "topic_slug": topic_slug,
        "workspace_root": str(workspace_root),
        "checks": {
            "doctor_contract_status": doctor_payload["control_plane_contracts"]["unified_architecture"]["status"],
            "status_h_plane": status_payload["h_plane"]["overall_status"],
            "status_operator_state": status_payload["h_plane"]["registry"]["operator_status"],
            "pairing_status": paired_payload["pairing_status"],
            "paired_backend_drift_status": paired_payload["drift_status"],
            "h_plane_overall_status": h_plane_payload["overall_status"],
            "capability_control_plane_status": capability_payload["sections"]["control_plane"]["status"]["status"],
        },
        "artifacts": {
            "runtime_root": str(runtime_root),
            "runtime_protocol": str(runtime_root / "runtime_protocol.generated.json"),
            "capability_registry": str(capability_registry_path),
            "capability_report": str(capability_report_path),
            "paired_backend_audit": str(paired_audit_path),
            "paired_backend_audit_note": str(paired_audit_note_path),
            "h_plane_audit": str(h_plane_audit_path),
            "h_plane_audit_note": str(h_plane_audit_note_path),
        },
        "doctor_payload": {
            "control_plane_contracts": doctor_payload["control_plane_contracts"],
            "control_plane_surfaces": doctor_payload["control_plane_surfaces"],
        },
        "status_payload": {
            "control_plane": status_payload["control_plane"],
            "h_plane": status_payload["h_plane"],
        },
        "paired_backend_payload": paired_payload,
        "h_plane_payload": h_plane_payload,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
