from __future__ import annotations

import json
import os
from pathlib import Path
from statistics import quantiles
from time import perf_counter

import pytest


_RUN_PERFORMANCE = os.environ.get("AITP_RUN_PERFORMANCE") == "1"


@pytest.mark.skipif(not _RUN_PERFORMANCE, reason="set AITP_RUN_PERFORMANCE=1")
def test_versioned_10000_record_context_latency(tmp_path):
    from brain.v5.context_pack import build_aitp_context_pack
    from brain.v5.models import ClaimRecord
    from brain.v5.query_index import build_query_index
    from brain.v5.record_envelope import RecordActor
    from brain.v5.record_repository import RecordRepository
    from brain.v5.research_retrieval import exact_expand
    from brain.v5.research_timeline import build_research_timeline
    from brain.v5.store import write_record
    from brain.v5.workspace import bind_session, create_topic, init_workspace

    config_path = Path(__file__).parent / "fixtures" / "v5_context_10000_fixture.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    ws = init_workspace(tmp_path / "fixture")
    for topic_index in range(config["topic_count"]):
        topic_id = f"topic-{topic_index:03d}"
        session_id = f"session-{topic_index:03d}"
        create_topic(ws, topic_id, context_id="perf-context", title=f"Performance topic {topic_index}")
        for claim_index in range(config["claims_per_topic"]):
            claim_id = f"claim-{topic_id}-{claim_index:03d}"
            write_record(
                ws.registry_dir("claims") / f"{claim_id}.md",
                ClaimRecord(
                    claim_id=claim_id,
                    topic_id=topic_id,
                    statement=(
                        f"Versioned fixture claim {claim_index} for {topic_id} tests bounded indexed recall."
                    ),
                    evidence_profile="performance_fixture",
                    confidence_state="candidate",
                    active_uncertainty="Synthetic fixture records do not support scientific conclusions.",
                ),
            )
        bind_session(
            ws,
            session_id,
            topic_id=topic_id,
            context_id="perf-context",
            active_claim=f"claim-{topic_id}-000",
        )

    build_start = perf_counter()
    report = build_query_index(ws)
    build_seconds = perf_counter() - build_start
    assert report.indexed_count == config["expected_record_count"]

    session_id = config["active_session_id"]
    claim_ref = f"claim:{config['active_claim_id']}"
    minimal_values, pack = _measure(
        lambda: build_aitp_context_pack(ws, session_id, max_lines=45),
        repetitions=7,
    )
    timeline_values, _timeline = _measure(
        lambda: build_research_timeline(ws, session_id, limit=80),
        repetitions=6,
    )
    exact_values, _exact = _measure(
        lambda: exact_expand(ws, [claim_ref], limit=10),
        repetitions=10,
    )
    repository = RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="model",
            actor_id="performance-fixture",
            host="pytest",
        ),
    )
    write_values = []
    write_results = []
    for write_index in range(5):
        started = perf_counter()
        write_results.append(
            repository.write(
                "claims",
                ClaimRecord(
                    claim_id=f"claim-performance-write-{write_index:03d}",
                    topic_id=config["active_topic_id"],
                    statement="Versioned fixture write-through latency probe.",
                    evidence_profile="performance_fixture",
                    confidence_state="candidate",
                    active_uncertainty=(
                        "Synthetic fixture records do not support scientific conclusions."
                    ),
                ),
                body="# Write-through latency probe\n",
            )
        )
        write_values.append(perf_counter() - started)

    metrics = {
        "fixture_version": config["fixture_version"],
        "record_count": report.indexed_count,
        "index_build_seconds": build_seconds,
        "cold_minimal_seconds": minimal_values[0],
        "warm_minimal_p95_seconds": _p95(minimal_values[1:]),
        "warm_timeline_p95_seconds": _p95(timeline_values[1:]),
        "exact_ref_p95_seconds": _p95(exact_values),
        "write_through_p95_seconds": _p95(write_values),
        "context_bytes": pack["byte_count"],
        "context_tokens": pack["estimated_tokens"],
    }
    print(json.dumps(metrics, sort_keys=True))

    assert metrics["cold_minimal_seconds"] < 3.0
    assert metrics["warm_minimal_p95_seconds"] < 1.0
    assert metrics["warm_timeline_p95_seconds"] < 2.0
    assert metrics["exact_ref_p95_seconds"] < 0.25
    assert metrics["write_through_p95_seconds"] < 0.1
    assert all(result.status == "created" for result in write_results)
    assert all(result.index_projection.status == "projected" for result in write_results)
    assert pack["byte_count"] <= pack["context_budget"]["max_bytes"]
    assert pack["estimated_tokens"] <= pack["context_budget"]["max_tokens"]


def _measure(call, *, repetitions: int):
    values = []
    payload = None
    for _ in range(repetitions):
        started = perf_counter()
        payload = call()
        values.append(perf_counter() - started)
    return values, payload


def _p95(values):
    return quantiles(values, n=20, method="inclusive")[18]
