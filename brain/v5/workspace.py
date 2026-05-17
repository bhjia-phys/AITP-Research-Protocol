"""Workspace and topic operations for the AITP v5 kernel."""

from __future__ import annotations

from pathlib import Path

from brain.v5.markdown import write_md
from brain.v5.ids import prefixed_id
from brain.v5.models import ClaimRecord, ContextRecord, SessionBinding, TopicRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import read_record, write_record


def init_workspace(base: str | Path) -> WorkspacePaths:
    """Create or open a v5 workspace."""

    ws = WorkspacePaths(Path(base))
    ws.ensure_layout()
    workspace_path = ws.root / "workspace.md"
    if not workspace_path.exists():
        write_md(
            workspace_path,
            {"kind": "aitp_v5_workspace", "version": "0.1"},
            "# AITP Workspace\n\nThis workspace stores AITP v5 research state.\n",
        )
    return ws


def create_context(ws: WorkspacePaths, context_id: str, *, title: str) -> ContextRecord:
    """Create or update a context record."""

    record = ContextRecord(context_id=context_id, title=title)
    path = ws.context_dir(context_id) / "context.md"
    write_record(path, record, body=f"# {title}\n\nContext id: `{context_id}`.\n")
    return record


def create_topic(
    ws: WorkspacePaths,
    topic_id: str,
    *,
    context_id: str,
    title: str,
) -> TopicRecord:
    """Create or update a topic workbench record."""

    record = TopicRecord(topic_id=topic_id, context_id=context_id, title=title)
    topic_dir = ws.topic_dir(topic_id)
    for rel in [
        "intent",
        "evidence/code_states",
        "claims/ledger",
        "routes/decisions",
        "attempts/code_patches",
        "attempts/upstream_comparisons",
        "runtime",
        "indexes",
    ]:
        (topic_dir / rel).mkdir(parents=True, exist_ok=True)
    write_record(topic_dir / "topic.md", record, body=f"# {title}\n\nTopic id: `{topic_id}`.\n")
    return record


def bind_session(
    ws: WorkspacePaths,
    session_id: str,
    *,
    topic_id: str,
    context_id: str,
    runtime: str = "unknown",
    interaction_profile: str = "collaborator",
    interaction_steering: str = "",
    active_cycle: str = "",
    active_claim: str = "",
    active_route: str = "",
    write_scope: list[str] | None = None,
    lock_level: str = "none",
) -> SessionBinding:
    """Bind one execution session to a topic/context focus."""

    binding = SessionBinding(
        session_id=session_id,
        topic_id=topic_id,
        context_id=context_id,
        runtime=runtime,
        interaction_profile=interaction_profile,
        interaction_steering=interaction_steering,
        active_cycle=active_cycle,
        active_claim=active_claim,
        active_route=active_route,
        write_scope=write_scope or [],
        lock_level=lock_level,
    )
    write_record(ws.session_path(session_id), binding, body=f"# Session {session_id}\n")
    return binding


def get_session_binding(ws: WorkspacePaths, session_id: str) -> SessionBinding:
    """Load a session binding."""

    return read_record(ws.session_path(session_id), SessionBinding)


def create_claim(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    statement: str,
    evidence_profile: str,
    confidence_state: str,
    active_uncertainty: str,
    recipe_id: str = "",
    scope: str = "",
    non_claims: str = "",
    strongest_failure_mode: str = "",
) -> ClaimRecord:
    """Create a claim record in the global registry and topic ledger."""

    claim_id = prefixed_id("claim", f"{topic_id}:{statement}")
    record = ClaimRecord(
        claim_id=claim_id,
        topic_id=topic_id,
        statement=statement,
        evidence_profile=evidence_profile,
        confidence_state=confidence_state,
        active_uncertainty=active_uncertainty,
        recipe_id=recipe_id,
        scope=scope,
        non_claims=non_claims,
        strongest_failure_mode=strongest_failure_mode,
    )
    body = f"# Claim\n\n{statement}\n"
    write_record(ws.registry_dir("claims") / f"{claim_id}.md", record, body=body)
    topic_claims = ws.topic_dir(topic_id) / "claims" / "ledger"
    write_record(topic_claims / f"{claim_id}.md", record, body=body)
    return record


def get_claim(ws: WorkspacePaths, claim_id: str) -> ClaimRecord:
    """Load a claim from the registry."""

    return read_record(ws.registry_dir("claims") / f"{claim_id}.md", ClaimRecord)
