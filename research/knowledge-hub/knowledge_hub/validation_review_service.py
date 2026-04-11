from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


class ValidationReviewService:
    def __init__(
        self,
        service: Any,
        *,
        read_json: Callable[[Path], dict[str, Any] | None],
        now_iso: Callable[[], str],
    ) -> None:
        self._service = service
        self._read_json = read_json
        self._now_iso = now_iso

    def review_artifact_status(self, artifact_kind: str, payload: dict[str, Any]) -> str:
        if artifact_kind == "coverage_ledger":
            return str(payload.get("coverage_status") or payload.get("status") or "unknown")
        if artifact_kind == "analytical_review":
            return str(payload.get("overall_status") or payload.get("status") or "unknown")
        if artifact_kind == "formal_theory_review":
            return str(payload.get("overall_status") or payload.get("status") or "unknown")
        if artifact_kind == "merge_report":
            return str(payload.get("merge_outcome") or payload.get("status") or "unknown")
        return str(payload.get("status") or "unknown")

    def collect_validation_review_artifacts(
        self,
        *,
        topic_slug: str,
        latest_run_id: str,
        candidate_rows: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        if not latest_run_id:
            return []
        artifact_rows: list[dict[str, str]] = []
        for row in candidate_rows:
            candidate_id = str(row.get("candidate_id") or "").strip()
            if not candidate_id:
                continue
            packet_paths = self._service._theory_packet_paths(topic_slug, latest_run_id, candidate_id)
            for artifact_kind in (
                "coverage_ledger",
                "agent_consensus",
                "regression_gate",
                "analytical_review",
                "faithfulness_review",
                "provenance_review",
                "prerequisite_closure_review",
                "formal_theory_review",
                "merge_report",
            ):
                artifact_path = packet_paths[artifact_kind]
                if not artifact_path.exists():
                    continue
                payload = self._read_json(artifact_path) or {}
                artifact_rows.append(
                    {
                        "candidate_id": candidate_id,
                        "candidate_type": str(row.get("candidate_type") or ""),
                        "artifact_kind": artifact_kind,
                        "path": self._service._relativize(artifact_path),
                        "status": self.review_artifact_status(artifact_kind, payload),
                    }
                )
        deduped: list[dict[str, str]] = []
        seen: set[str] = set()
        for row in artifact_rows:
            key = f"{row['candidate_id']}::{row['artifact_kind']}::{row['path']}"
            if key in seen:
                continue
            seen.add(key)
            deduped.append(row)
        return deduped

    def derive_validation_review_bundle(
        self,
        *,
        topic_slug: str,
        latest_run_id: str,
        updated_by: str,
        validation_contract: dict[str, Any],
        promotion_readiness: dict[str, Any],
        open_gap_summary: dict[str, Any],
        topic_completion: dict[str, Any],
        candidate_rows: list[dict[str, Any]],
        promotion_gate: dict[str, Any],
    ) -> dict[str, Any]:
        artifact_rows = self.collect_validation_review_artifacts(
            topic_slug=topic_slug,
            latest_run_id=latest_run_id,
            candidate_rows=candidate_rows,
        )
        candidate_ids = self._service._dedupe_strings(
            [str(row.get("candidate_id") or "") for row in candidate_rows if str(row.get("candidate_id") or "").strip()]
        )
        artifact_kinds = {str(row.get("artifact_kind") or "") for row in artifact_rows}
        validation_mode = str(validation_contract.get("validation_mode") or "")
        if validation_mode == "analytical" and "analytical_review" in artifact_kinds:
            primary_review_kind = "analytical_review"
        elif "formal_theory_review" in artifact_kinds:
            primary_review_kind = "formal_theory_review"
        elif "analytical_review" in artifact_kinds:
            primary_review_kind = "analytical_review"
        elif artifact_kinds & {"regression_gate", "coverage_ledger", "agent_consensus"}:
            primary_review_kind = "promotion_readiness"
        else:
            primary_review_kind = "validation_contract"
        blockers = self._service._dedupe_strings(
            list(open_gap_summary.get("blockers") or [])
            + list(promotion_readiness.get("blockers") or [])
            + [
                f"{row['artifact_kind']}={row['status']}"
                for row in artifact_rows
                if str(row.get("status") or "").strip().lower()
                in {"blocked", "fail", "failed", "missing", "not_ready", "not_audited"}
            ]
        )
        if open_gap_summary.get("requires_l0_return"):
            status = "blocked"
        elif artifact_rows:
            status = "ready" if not blockers else "blocked"
        else:
            status = "not_materialized"
        summary = (
            f"Primary L4 review surface for topic `{topic_slug}` using `{primary_review_kind}` as the current review entry point."
        )
        if blockers:
            summary += f" Active blockers: {blockers[0]}"
        elif artifact_rows:
            summary += " Specialist review artifacts are available under this bundle."
        else:
            summary += " No specialist review artifacts are materialized for the active run yet."
        validation_paths = self._service._validation_contract_paths(topic_slug)
        topic_completion_paths = self._service._topic_completion_paths(topic_slug)
        promotion_gate_paths = self._service._promotion_gate_paths(topic_slug)
        entrypoints = {
            "validation_contract_path": self._service._relativize(validation_paths["json"]),
            "validation_contract_note_path": self._service._relativize(validation_paths["note"]),
            "promotion_readiness_path": self._service._relativize(self._service._runtime_root(topic_slug) / "promotion_readiness.json"),
            "promotion_readiness_note_path": self._service._relativize(self._service._promotion_readiness_path(topic_slug)),
            "topic_completion_path": self._service._relativize(topic_completion_paths["json"]),
            "topic_completion_note_path": self._service._relativize(topic_completion_paths["note"]),
            "gap_map_path": self._service._relativize(self._service._gap_map_path(topic_slug)),
            "promotion_gate_path": self._service._relativize(promotion_gate_paths["json"])
            if promotion_gate_paths["json"].exists()
            else None,
        }
        return {
            "bundle_kind": "validation_review_bundle",
            "topic_slug": topic_slug,
            "run_id": latest_run_id,
            "status": status,
            "primary_review_kind": primary_review_kind,
            "candidate_ids": candidate_ids,
            "validation_mode": str(validation_contract.get("validation_mode") or ""),
            "promotion_readiness_status": str(promotion_readiness.get("status") or "not_ready"),
            "topic_completion_status": str(topic_completion.get("status") or "not_assessed"),
            "promotion_gate_status": str(promotion_gate.get("status") or "not_requested"),
            "blockers": blockers,
            "entrypoints": entrypoints,
            "specialist_artifacts": artifact_rows,
            "summary": summary,
            "updated_at": self._now_iso(),
            "updated_by": updated_by,
        }

    def render_validation_review_bundle_markdown(self, payload: dict[str, Any]) -> str:
        lines = [
            "# Validation review bundle",
            "",
            f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
            f"- Run id: `{payload.get('run_id') or '(missing)'}`",
            f"- Status: `{payload.get('status') or '(missing)'}`",
            f"- Primary review kind: `{payload.get('primary_review_kind') or '(missing)'}`",
            f"- Validation mode: `{payload.get('validation_mode') or '(missing)'}`",
            f"- Promotion readiness: `{payload.get('promotion_readiness_status') or '(missing)'}`",
            f"- Topic completion: `{payload.get('topic_completion_status') or '(missing)'}`",
            f"- Promotion gate: `{payload.get('promotion_gate_status') or '(missing)'}`",
            "",
            "## Summary",
            "",
            payload.get("summary") or "(missing)",
            "",
            "## Entry points",
            "",
        ]
        for key in (
            "validation_contract_path",
            "validation_contract_note_path",
            "promotion_readiness_path",
            "promotion_readiness_note_path",
            "topic_completion_path",
            "topic_completion_note_path",
            "gap_map_path",
            "promotion_gate_path",
        ):
            lines.append(f"- {key}: `{((payload.get('entrypoints') or {}).get(key) or '(missing)')}`")
        lines.extend(["", "## Candidate scope", ""])
        for item in payload.get("candidate_ids") or ["(none)"]:
            lines.append(f"- `{item}`")
        lines.extend(["", "## Blockers", ""])
        for item in payload.get("blockers") or ["(none)"]:
            lines.append(f"- {item}")
        lines.extend(["", "## Specialist artifacts", ""])
        if payload.get("specialist_artifacts"):
            for row in payload.get("specialist_artifacts") or []:
                lines.append(
                    f"- `{row.get('artifact_kind') or '(missing)'}` "
                    f"candidate=`{row.get('candidate_id') or '(missing)'}` "
                    f"status=`{row.get('status') or '(missing)'}` "
                    f"path=`{row.get('path') or '(missing)'}`"
                )
        else:
            lines.append("- `(none)`")
        return "\n".join(lines) + "\n"
