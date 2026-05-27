"""MCP wrappers for run-local iteration continuity."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.run_iterations import record_run_iteration
from brain.v5.workspace import init_workspace


def _ws(base: str):
    return init_workspace(Path(base))


def aitp_v5_record_run_iteration(
    base: str, *, topic_id: str, run_id: str, iteration_id: str, plan_summary: str,
    deliverables: list[str] | None = None, checks: list[str] | None = None,
    stop_rules: list[str] | None = None, l4_return_summary: str = "",
    l4_artifact_refs: list[str] | None = None, l3_synthesis_summary: str = "",
    decision: str = "", status: str = "planned", claim_id: str = "",
    source_refs: list[str] | None = None,
) -> dict:
    record = record_run_iteration(
        _ws(base),
        topic_id=topic_id,
        run_id=run_id,
        iteration_id=iteration_id,
        plan_summary=plan_summary,
        deliverables=deliverables,
        checks=checks,
        stop_rules=stop_rules,
        l4_return_summary=l4_return_summary,
        l4_artifact_refs=l4_artifact_refs,
        l3_synthesis_summary=l3_synthesis_summary,
        decision=decision,
        status=status,
        claim_id=claim_id,
        source_refs=source_refs,
    )
    return require_valid_public_surface("run_iteration_record", {"ok": True, **asdict(record)})
