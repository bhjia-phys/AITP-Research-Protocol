from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest


@pytest.fixture
def require_real_human_approval():
    """Opt a test module out of the historical checkpoint compatibility stub."""


@pytest.fixture(autouse=True)
def _install_checkpoint_approval_test_fixture(request, monkeypatch):
    """Keep legacy tests working without adding any production authorization bypass."""

    if "require_real_human_approval" in request.fixturenames:
        return

    from brain.v5.human_approval import (
        load_human_approval_receipt,
        persist_human_approval_receipt,
        verify_human_approval_receipt,
    )

    temp_root = Path(tempfile.gettempdir()).resolve()
    default_secret = b"pytest-only-human-approval-secret-32-bytes"
    monkeypatch.setenv(
        "AITP_HUMAN_APPROVAL_HMAC_KEY_B64",
        base64.b64encode(default_secret).decode("ascii"),
    )

    def verify_test_checkpoint(ws, **kwargs):
        workspace = ws.base.resolve()
        if not workspace.is_relative_to(temp_root):
            raise ValueError("pytest checkpoint fixture is restricted to system Temp workspaces")
        supplied = kwargs.get("approval_receipt")
        existing = load_human_approval_receipt(ws, kwargs["checkpoint_id"])
        if supplied is not None or existing is not None:
            return verify_human_approval_receipt(ws, **kwargs)

        now = datetime.now(UTC)
        key = base64.b64decode(
            os.environ["AITP_HUMAN_APPROVAL_HMAC_KEY_B64"],
            validate=True,
        )
        payload = {
            "version": "v1",
            "checkpoint_id": kwargs["checkpoint_id"],
            "checkpoint_content_hash": kwargs["checkpoint_content_hash"],
            "decision": kwargs["decision"],
            "rationale_hash": hashlib.sha256(
                kwargs["rationale"].encode("utf-8")
            ).hexdigest(),
            "decided_by": kwargs["decided_by"],
            "issued_at": now.isoformat(),
            "expires_at": (now + timedelta(minutes=30)).isoformat(),
            "nonce": f"pytest-{kwargs['checkpoint_id']}",
        }
        encoded = json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        receipt = {
            **payload,
            "signature": hmac.new(key, encoded, hashlib.sha256).hexdigest(),
        }
        verification = verify_human_approval_receipt(
            ws,
            **{**kwargs, "approval_receipt": receipt},
        )
        persist_human_approval_receipt(ws, kwargs["checkpoint_id"], receipt)
        return verification

    monkeypatch.setattr(
        "brain.v5.checkpoints.verify_human_approval_receipt",
        verify_test_checkpoint,
    )
