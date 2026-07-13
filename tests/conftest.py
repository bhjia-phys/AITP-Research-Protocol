from __future__ import annotations

import tempfile
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

    from brain.v5.human_approval import HumanApprovalVerification

    temp_root = Path(tempfile.gettempdir()).resolve()

    def verify_test_checkpoint(ws, **_kwargs):
        workspace = ws.base.resolve()
        if not workspace.is_relative_to(temp_root):
            raise ValueError("pytest checkpoint fixture is restricted to system Temp workspaces")
        return HumanApprovalVerification(
            decision_verified=True,
            method="hmac_sha256_v1",
            receipt_hash=f"sha256:{'f' * 64}",
            nonce="pytest-temp-host-receipt",
            can_authorize_trust=True,
        )

    monkeypatch.setattr(
        "brain.v5.checkpoints.verify_human_approval_receipt",
        verify_test_checkpoint,
    )
