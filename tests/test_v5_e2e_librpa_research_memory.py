from __future__ import annotations

import os
from pathlib import Path

import pytest


def test_real_librpa_hpc_probe_is_hash_pinned_and_trust_neutral():
    if os.environ.get("AITP_RUN_REAL_VERTICAL_PROBES") != "1":
        pytest.skip("set AITP_RUN_REAL_VERTICAL_PROBES=1 on the authorized research machine")

    from brain.v5.real_vertical_probes import run_librpa_real_probe

    repo_root = Path(__file__).resolve().parents[1]
    receipt = run_librpa_real_probe(
        topics_root=Path(r"F:\AI_Workspace\Theoretical-Physics\research\aitp-topics"),
        manifest_path=(
            repo_root / "tests" / "fixtures" / "v5_e2e" / "librpa" / "real_probe_manifest.json"
        ),
    )

    assert receipt["status"] == "passed"
    assert receipt["final_row_count"] >= 10
    assert {"Si", "MgO", "BN"}.issubset(receipt["materials"])
    assert {
        "artifacts",
        "code_states",
        "tool_runs",
        "validation_results",
    }.issubset(receipt["selected_context_families"])
    assert len(receipt["input_fingerprint"]) == 64
    assert receipt["can_update_claim_trust"] is False
