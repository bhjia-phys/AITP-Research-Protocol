from pathlib import Path
import json

from brain.v5.claim_relation_map import build_claim_relation_map
from brain.v5.mcp_legacy import aitp_v5_build_legacy_semantic_review_queue
from brain.v5.mcp_tools import aitp_v5_bind_session, aitp_v5_build_workspace_recovery_audit, aitp_v5_init_workspace
from brain.v5.workspace import bind_session, create_claim, create_topic, get_session_binding, init_workspace


def _seed_workspace(topics_root: Path):
    ws = init_workspace(topics_root)
    create_topic(ws, "qsgw-ac-error-molecules", context_id="librpa", title="QSGW AC")
    claim = create_claim(
        ws,
        topic_id="qsgw-ac-error-molecules",
        statement="H2O ridge Padé diagnostics remain bounded by Si runtime blockers.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="Si baseline has not completed.",
    )
    bind_session(
        ws,
        "codex-qsgw-current",
        topic_id="qsgw-ac-error-molecules",
        context_id="librpa",
        active_claim=claim.claim_id,
    )
    return ws


def test_mcp_base_resolution_prefers_env_topics_root_over_workspace_root_aitp(tmp_path, monkeypatch):
    workspace_root = tmp_path / "Theoretical-Physics"
    topics_root = workspace_root / "research" / "aitp-topics"
    _seed_workspace(topics_root)
    root_aitp = workspace_root / ".aitp"

    # Simulate a previous accidental call that initialized the wrong root .aitp/.aitp store.
    aitp_v5_init_workspace(str(root_aitp))
    monkeypatch.setenv("AITP_TOPICS_ROOT", str(topics_root))

    payload = aitp_v5_build_workspace_recovery_audit(
        str(root_aitp),
        topics=["qsgw-ac-error-molecules"],
    )

    row = payload["topic_rows"][0]
    assert payload["canonical_topics_root"] == str(topics_root)
    assert row["recovery_status"] == "recovery_ready"
    assert row["session_id"] == "codex-qsgw-current"


def test_mcp_base_resolution_prefers_nested_topics_root_over_legacy_workspace_root(tmp_path, monkeypatch):
    workspace_root = tmp_path / "Theoretical-Physics"
    topics_root = workspace_root / "research" / "aitp-topics"
    _seed_workspace(topics_root)
    monkeypatch.delenv("AITP_TOPICS_ROOT", raising=False)

    # Simulate the old root control surface also looking like a v5 workspace.
    aitp_v5_init_workspace(str(workspace_root))

    payload = aitp_v5_build_workspace_recovery_audit(
        str(workspace_root),
        topics=["qsgw-ac-error-molecules"],
        compact=True,
    )
    root_store_payload = aitp_v5_build_workspace_recovery_audit(
        str(workspace_root / ".aitp"),
        topics=["qsgw-ac-error-molecules"],
        compact=True,
    )

    assert payload["canonical_topics_root"] == str(topics_root)
    assert payload["selected_topic"]["session_id"] == "codex-qsgw-current"
    assert root_store_payload["canonical_topics_root"] == str(topics_root)
    assert root_store_payload["selected_topic"]["session_id"] == "codex-qsgw-current"


def test_legacy_mcp_base_resolution_prefers_nested_topics_root(tmp_path, monkeypatch):
    workspace_root = tmp_path / "Theoretical-Physics"
    topics_root = workspace_root / "research" / "aitp-topics"
    _seed_workspace(topics_root)
    migration_dir = topics_root / ".aitp" / "migrations" / "legacy-v5-lossless-test"
    migration_dir.mkdir(parents=True)
    summary = {
        "run_id": "legacy-v5-lossless-test",
        "workspace": str(topics_root),
        "legacy_root": str(workspace_root / "legacy"),
        "v5_root": str(topics_root / ".aitp"),
        "totals": {
            "topic_count": 1,
            "legacy_file_count": 1,
            "post_legacy_file_count": 1,
            "legacy_manifest_hash_stable": True,
            "legacy_manifest_change_count": 0,
            "structured_file_count": 1,
            "archive_reference_count": 0,
            "accounted_file_count": 1,
            "topics_with_errors": 0,
            "missing_archive_record_files": 0,
        },
        "topics": [
            {
                "topic": "qsgw-ac-error-molecules",
                "status": "ok",
                "file_count": 1,
                "accounted_file_count": 1,
                "structured_file_count": 1,
                "archive_reference_count": 0,
                "missing_expected_paths": [],
                "can_write_v5_records": True,
                "active_claim_id": "",
                "written_records": {},
                "preserved_source_refs": 0,
            }
        ],
    }
    verification = {
        "run_id": "legacy-v5-lossless-test",
        "file_accounting_ok": True,
        "manifest_check": {"pre_count": 1, "post_count": 1, "missing": 0, "extra": 0, "changed": 0},
        "archive_reference_check": {
            "archive_records_checked": 0,
            "archive_records_expected": 0,
            "registry_archive_reference_count": 0,
            "problem_count": 0,
        },
        "markdown_readability_check": {"markdown_files_checked": 1, "problem_count": 0},
    }
    (migration_dir / "migration_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (migration_dir / "verification_report.json").write_text(json.dumps(verification), encoding="utf-8")
    stale_root_run = workspace_root / ".aitp" / "migrations" / "legacy-v5-lossless-stale-root-run"
    stale_root_run.mkdir(parents=True)
    (stale_root_run / "migration_summary.json").write_text(
        json.dumps({**summary, "run_id": "legacy-v5-lossless-stale-root-run", "workspace": str(workspace_root)}),
        encoding="utf-8",
    )
    (stale_root_run / "verification_report.json").write_text(
        json.dumps({**verification, "run_id": "legacy-v5-lossless-stale-root-run"}),
        encoding="utf-8",
    )
    monkeypatch.delenv("AITP_TOPICS_ROOT", raising=False)

    relative_payload = aitp_v5_build_legacy_semantic_review_queue(
        str(workspace_root),
        migration_dir=".aitp/migrations/legacy-v5-lossless-stale-root-run",
    )
    bare_payload = aitp_v5_build_legacy_semantic_review_queue(
        str(workspace_root),
        migration_dir="legacy-v5-lossless-stale-root-run",
    )
    existing_root_payload = aitp_v5_build_legacy_semantic_review_queue(
        str(workspace_root),
        migration_dir=str(stale_root_run),
    )

    for payload in (relative_payload, bare_payload, existing_root_payload):
        assert payload["workspace"] == str(topics_root)
        assert payload["migration_dir"] == str(migration_dir)
        assert payload["review_item_count"] == 1


def test_mcp_base_resolution_accepts_canonical_store_path(tmp_path, monkeypatch):
    topics_root = tmp_path / "Theoretical-Physics" / "research" / "aitp-topics"
    _seed_workspace(topics_root)
    monkeypatch.setenv("AITP_TOPICS_ROOT", str(topics_root))

    payload = aitp_v5_build_workspace_recovery_audit(
        str(topics_root / ".aitp"),
        topics=["qsgw-ac-error-molecules"],
        compact=True,
    )

    assert payload["canonical_topics_root"] == str(topics_root)
    assert payload["recovery_ready_count"] == 1


def test_bind_session_preserves_existing_active_claim_when_recovery_call_omits_claim(tmp_path):
    topics_root = tmp_path / "Theoretical-Physics" / "research" / "aitp-topics"
    ws = _seed_workspace(topics_root)

    aitp_v5_bind_session(
        str(topics_root),
        session_id="codex-qsgw-current",
        topic_id="qsgw-ac-error-molecules",
        context_id="librpa",
    )

    session = get_session_binding(ws, "codex-qsgw-current")
    relation = build_claim_relation_map(ws, "codex-qsgw-current")
    assert session.active_claim
    assert relation["claim_id"] == session.active_claim
