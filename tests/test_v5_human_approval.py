from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest


pytestmark = pytest.mark.usefixtures("require_real_human_approval")


def _seed_checkpoint(tmp_path):
    from brain.v5.checkpoints import request_human_checkpoint
    from brain.v5.markdown import read_md
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="theory", title="Quantum gravity")
    claim = create_claim(
        ws,
        topic_id="qg",
        statement="A bounded derivation may be promoted only after human review.",
        evidence_profile="semi_formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="human review is pending",
    )
    checkpoint = request_human_checkpoint(
        ws,
        topic_id="qg",
        claim_id=claim.claim_id,
        reason="Review the exact bounded promotion request.",
        requested_by="human_approval_test",
        options=["approve", "reject"],
    )
    frontmatter, _ = read_md(ws.registry_dir("checkpoints") / f"{checkpoint.checkpoint_id}.md")
    return ws, checkpoint, frontmatter["record_content_hash"]


def _receipt(*, secret: bytes, checkpoint_id: str, checkpoint_hash: str, decision: str, rationale: str):
    now = datetime.now(UTC)
    payload = {
        "version": "v1",
        "checkpoint_id": checkpoint_id,
        "checkpoint_content_hash": checkpoint_hash,
        "decision": decision,
        "rationale_hash": hashlib.sha256(rationale.encode("utf-8")).hexdigest(),
        "decided_by": "samur",
        "issued_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=5)).isoformat(),
        "nonce": "human-approval-test-nonce",
    }
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {**payload, "signature": hmac.new(secret, encoded, hashlib.sha256).hexdigest()}


def test_checkpoint_decision_fails_closed_without_host_receipt(tmp_path, monkeypatch):
    from brain.v5.checkpoints import decide_human_checkpoint

    monkeypatch.delenv("AITP_TEST_ALLOW_UNVERIFIED_CHECKPOINT_DECISIONS", raising=False)
    monkeypatch.delenv("AITP_HUMAN_APPROVAL_HMAC_KEY_B64", raising=False)
    ws, checkpoint, _ = _seed_checkpoint(tmp_path)

    with pytest.raises(ValueError, match="host-verified human approval receipt"):
        decide_human_checkpoint(
            ws,
            checkpoint_id=checkpoint.checkpoint_id,
            decision="approve",
            rationale="Reviewed the exact request and approve it.",
            decided_by="samur",
        )


def test_checkpoint_test_bypass_rejects_spoofed_pytest_environment(tmp_path):
    env = os.environ.copy()
    env["AITP_TEST_ALLOW_UNVERIFIED_CHECKPOINT_DECISIONS"] = "1"
    env["PYTEST_CURRENT_TEST"] = "spoofed::outside-pytest"
    env["AITP_TEST_WORKSPACE"] = str(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import os, pytest; from pathlib import Path; "
            "from brain.v5.human_approval import verify_human_approval_receipt; "
            "from brain.v5.paths import WorkspacePaths; "
            "ws=WorkspacePaths(Path(os.environ['AITP_TEST_WORKSPACE'])); "
            "ok=False; "
            "\ntry: verify_human_approval_receipt(ws, checkpoint_id='checkpoint-spoof', "
            "checkpoint_content_hash='hash', decision='approve', rationale='r', decided_by='u')"
            "\nexcept ValueError as exc: ok='host-verified human approval receipt' in str(exc)"
            "\nraise SystemExit(0 if ok else 1)",
        ],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_checkpoint_decision_accepts_content_bound_host_receipt(tmp_path, monkeypatch):
    from brain.v5.checkpoints import decide_human_checkpoint
    from brain.v5.markdown import read_md

    monkeypatch.delenv("AITP_TEST_ALLOW_UNVERIFIED_CHECKPOINT_DECISIONS", raising=False)
    secret = b"test-only-host-secret-with-32-bytes"
    monkeypatch.setenv("AITP_HUMAN_APPROVAL_HMAC_KEY_B64", base64.b64encode(secret).decode("ascii"))
    ws, checkpoint, checkpoint_hash = _seed_checkpoint(tmp_path)
    rationale = "Reviewed the exact request and approve it."
    receipt = _receipt(
        secret=secret,
        checkpoint_id=checkpoint.checkpoint_id,
        checkpoint_hash=checkpoint_hash,
        decision="approve",
        rationale=rationale,
    )

    decided = decide_human_checkpoint(
        ws,
        checkpoint_id=checkpoint.checkpoint_id,
        decision="approve",
        rationale=rationale,
        decided_by="samur",
        approval_receipt=receipt,
    )

    frontmatter, _ = read_md(ws.registry_dir("checkpoints") / f"{checkpoint.checkpoint_id}.md")
    assert decided.decision_verified is True
    assert decided.can_authorize_trust is True
    assert decided.decision_verification == "hmac_sha256_v1"
    assert decided.decision_receipt_nonce == receipt["nonce"]
    assert frontmatter["created_by"]["actor_type"] == "tool"
    assert frontmatter["decision_receipt_hash"].startswith("sha256:")
    assert "signature" not in frontmatter


def test_checkpoint_authority_requires_complete_verified_receipt_metadata():
    from brain.v5.human_approval import checkpoint_can_authorize_trust
    from brain.v5.models import HumanCheckpointRecord

    checkpoint = HumanCheckpointRecord(
        checkpoint_id="checkpoint-authority-shape",
        topic_id="qg",
        claim_id="claim-qg",
        reason="Trust-sensitive review.",
        requested_by="test",
        options=["approve"],
        status="decided",
        decision="approve",
        rationale="Reviewed.",
        decided_by="samur",
        decision_verified=True,
        decision_verification="forged_boolean_only",
        decision_receipt_hash="not-a-receipt-hash",
        decision_receipt_nonce="nonce",
        can_authorize_trust=True,
    )

    assert checkpoint_can_authorize_trust(checkpoint) is False
    checkpoint.decision_verification = "hmac_sha256_v1"
    checkpoint.decision_receipt_hash = f"sha256:{'a' * 64}"
    assert checkpoint_can_authorize_trust(checkpoint) is True


def test_new_human_checkpoints_use_schema_v2(tmp_path):
    from brain.v5.markdown import read_md
    from brain.v5.record_family_registry import spec_for_family

    ws, checkpoint, _ = _seed_checkpoint(tmp_path)
    frontmatter, _ = read_md(
        ws.registry_dir("checkpoints") / f"{checkpoint.checkpoint_id}.md"
    )

    assert spec_for_family("checkpoints").schema_version == "v2"
    assert frontmatter["schema_version"] == "v2"


def test_checkpoint_decision_rejects_tampered_receipt(tmp_path, monkeypatch):
    from brain.v5.checkpoints import decide_human_checkpoint

    monkeypatch.delenv("AITP_TEST_ALLOW_UNVERIFIED_CHECKPOINT_DECISIONS", raising=False)
    secret = b"test-only-host-secret-with-32-bytes"
    monkeypatch.setenv("AITP_HUMAN_APPROVAL_HMAC_KEY_B64", base64.b64encode(secret).decode("ascii"))
    ws, checkpoint, checkpoint_hash = _seed_checkpoint(tmp_path)
    receipt = _receipt(
        secret=secret,
        checkpoint_id=checkpoint.checkpoint_id,
        checkpoint_hash=checkpoint_hash,
        decision="approve",
        rationale="Original rationale.",
    )

    with pytest.raises(ValueError, match="rationale_hash"):
        decide_human_checkpoint(
            ws,
            checkpoint_id=checkpoint.checkpoint_id,
            decision="approve",
            rationale="Tampered rationale.",
            decided_by="samur",
            approval_receipt=receipt,
        )


def test_mcp_checkpoint_decision_loads_host_runtime_receipt(tmp_path, monkeypatch):
    from brain.v5.mcp_tools import aitp_v5_decide_human_checkpoint

    monkeypatch.delenv("AITP_TEST_ALLOW_UNVERIFIED_CHECKPOINT_DECISIONS", raising=False)
    secret = b"test-only-host-secret-with-32-bytes"
    monkeypatch.setenv("AITP_HUMAN_APPROVAL_HMAC_KEY_B64", base64.b64encode(secret).decode("ascii"))
    ws, checkpoint, checkpoint_hash = _seed_checkpoint(tmp_path)
    rationale = "Reviewed through the host confirmation surface."
    receipt = _receipt(
        secret=secret,
        checkpoint_id=checkpoint.checkpoint_id,
        checkpoint_hash=checkpoint_hash,
        decision="approve",
        rationale=rationale,
    )
    receipt_dir = ws.root / "runtime" / "human_approval_receipts"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    (receipt_dir / f"{checkpoint.checkpoint_id}.json").write_text(
        json.dumps(receipt, ensure_ascii=True, sort_keys=True),
        encoding="utf-8",
    )

    payload = aitp_v5_decide_human_checkpoint(
        str(ws.base),
        checkpoint_id=checkpoint.checkpoint_id,
        decision="approve",
        rationale=rationale,
        decided_by="samur",
    )

    assert payload["decision_verified"] is True
    assert payload["decision_verification"] == "hmac_sha256_v1"
    assert payload["can_authorize_trust"] is True
    assert payload["decision_receipt_nonce"] == receipt["nonce"]
