from __future__ import annotations

from types import SimpleNamespace


def test_state_show_uses_live_gate_when_cached_gate_is_stale(tmp_path, capsys, monkeypatch):
    import brain.cli as cli

    topics_root = tmp_path / "aitp-topics"
    topic_root = topics_root / "hs-topic"
    monkeypatch.setattr(cli, "DEFAULT_TOPICS_ROOT", str(topics_root))

    cli._write_md(
        topic_root / "state.md",
        {
            "stage": "L3",
            "lane": "formal_theory",
            "l3_activity": "diagnose",
            "gate_status": "blocked_missing_artifact",
        },
        "# State\n",
    )
    cli._write_md(
        topic_root / "L3" / "diagnose" / "active_diagnosis.md",
        {
            "artifact_kind": "l3_active_diagnosis",
            "activity": "diagnose",
            "anomaly_description": "readiness fixture",
            "hypothesis_count": 1,
        },
        (
            "# Active Diagnosis\n\n"
            "## Anomaly Description\n"
            "The artifact is sufficiently populated for the live gate fixture.\n\n"
            "## Hypothesis Stack\n"
            "A single bounded hypothesis is present for this regression test.\n"
        ),
    )

    assert cli.cmd_state_show(SimpleNamespace(topic="hs-topic")) == 0
    out = capsys.readouterr().out

    assert "Gate: ready" in out
    assert "Stored gate: blocked_missing_artifact (stale; live evaluation used)" in out
