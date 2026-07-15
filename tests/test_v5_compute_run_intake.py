from __future__ import annotations

import json
from pathlib import Path

import pytest

from brain.v5.compute_run_intake import build_compute_run_intake
from brain.v5.compute_run_intake_contracts import (
    ComputeRunIntakeReport,
    ComputeRunIntakeRequest,
)


FIXTURE = Path(__file__).parent / "fixtures" / "v5_compute_run_intake" / "nio_manifest.json"


def _nio_manifest() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _local_manifest() -> dict:
    manifest = _nio_manifest()
    manifest["source"] = {
        "kind": "local",
        "uri": "file:///work/librpa/run-7",
        "accessible": True,
        "host": "workstation",
        "cluster": "",
    }
    manifest["run"]["scheduler"] = {}
    manifest["run"]["cwd"] = "/work/librpa/run-7"
    manifest["run"]["run_id"] = "local-run-7"
    return manifest


def test_completed_local_intake_builds_trust_neutral_prefill_candidates() -> None:
    report = build_compute_run_intake(ComputeRunIntakeRequest(manifest=_local_manifest()))

    assert report.status == "complete"
    assert report.coverage == "complete"
    assert report.missing_fields == ()
    assert report.writes_records is False
    assert report.orientation_only is True
    assert report.can_create_scientific_evidence is False
    assert report.can_update_claim_trust is False
    assert set(report.candidates) == {
        "tool_run",
        "artifacts",
        "monitor_snapshot",
        "execution_environment",
        "validation_checklist",
    }
    assert report.candidates["tool_run"]["lane"] == "final"
    assert report.candidates["tool_run"]["recorded_maturity"] == "diagnostic"
    assert report.candidates["artifacts"][0]["content_hash"] == "5" * 64
    assert report.candidates["execution_environment"]["executable_hashes"] == {
        "/opt/librpa/bin/librpa": "3" * 64
    }
    assert report.candidates["monitor_snapshot"]["snapshot_id"] == ""
    assert report.candidates["validation_checklist"]["status"] == "not_checked"


def test_slurm_remote_manifest_preserves_scheduler_and_collector_provenance() -> None:
    report = build_compute_run_intake(ComputeRunIntakeRequest(manifest=_nio_manifest()))

    assert report.status == "complete"
    assert report.candidates["tool_run"]["job_id"] == "4243"
    assert report.candidates["monitor_snapshot"]["remote_uri"].startswith("ssh://dongfang/")
    assert report.candidates["monitor_snapshot"]["collector_id"] == "slurm-run-manifest"
    assert report.candidates["monitor_snapshot"]["resource_usage"]["tasks"] == 64
    assert "run.scheduler.job_id" in report.checked_fields
    assert report.to_json() == build_compute_run_intake(
        ComputeRunIntakeRequest(manifest=_nio_manifest())
    ).to_json()


def test_running_manifest_is_partial_and_does_not_invent_completion() -> None:
    manifest = _nio_manifest()
    manifest["run"]["status"] = "running"
    manifest["run"]["output_manifest"] = []
    manifest["run"]["completed_at"] = ""
    manifest["run"]["exit_status"] = {}

    report = build_compute_run_intake(ComputeRunIntakeRequest(manifest=manifest))

    assert report.status == "partial"
    assert report.coverage == "partial"
    assert report.missing_fields == (
        "run.completed_at",
        "run.exit_status",
        "run.output_manifest",
    )
    assert report.candidates["tool_run"]["evidence_status"] == "running"
    assert report.candidates["validation_checklist"]["status"] == "not_checked"


def test_missing_executable_hash_is_reported_without_dropping_other_candidates() -> None:
    manifest = _nio_manifest()
    manifest["run"]["executable"]["sha256"] = ""

    report = build_compute_run_intake(ComputeRunIntakeRequest(manifest=manifest))

    assert report.status == "partial"
    assert report.missing_fields == ("run.executable.sha256",)
    assert report.candidates["execution_environment"]["executable_hashes"] == {}
    assert report.candidates["tool_run"]["output_manifest"]


def test_failed_job_remains_operational_failure_not_scientific_evidence() -> None:
    manifest = _nio_manifest()
    manifest["run"]["status"] = "failed"
    manifest["run"]["exit_status"] = {"code": 2, "state": "FAILED"}

    report = build_compute_run_intake(ComputeRunIntakeRequest(manifest=manifest))

    assert report.status == "failed"
    assert report.candidates["tool_run"]["evidence_status"] == "failed_runtime"
    assert report.candidates["tool_run"]["non_claims"] == [
        "collector status and scheduler metadata are process observations, not scientific evidence"
    ]
    assert report.can_create_scientific_evidence is False


def test_inaccessible_uri_returns_explicit_missing_report_without_candidates() -> None:
    manifest = _nio_manifest()
    manifest["source"]["accessible"] = False

    report = build_compute_run_intake(ComputeRunIntakeRequest(manifest=manifest))

    assert report.status == "inaccessible"
    assert report.coverage == "missing"
    assert report.candidates == {}
    assert report.missing_fields == ("source.content",)
    assert report.errors == ("collector source URI was not accessible",)


def test_invalid_manifest_shape_is_rejected() -> None:
    with pytest.raises(ValueError, match="manifest must be a mapping"):
        ComputeRunIntakeRequest(manifest=[])


def test_candidate_payload_redacts_credentials_and_sensitive_fields() -> None:
    manifest = _nio_manifest()
    manifest["source"]["uri"] = "ssh://alice:secret@dongfang/scratch/nio/run"
    manifest["run"]["environment"] = {"OMP_NUM_THREADS": "64", "api_token": "secret"}

    report = build_compute_run_intake(ComputeRunIntakeRequest(manifest=manifest))
    encoded = report.to_json()

    assert "secret" not in encoded
    assert "alice" not in encoded
    assert "[REDACTED]" in encoded
    assert report.redacted_fields == ("run.environment.api_token", "source.uri")


def test_request_detaches_mutable_manifest_from_caller() -> None:
    manifest = _nio_manifest()
    request = ComputeRunIntakeRequest(manifest=manifest)
    manifest["run"]["run_id"] = "mutated"

    report = build_compute_run_intake(request)

    assert report.candidates["tool_run"]["run_id"] == "nio-g0w0-4243"


@pytest.mark.parametrize(
    ("path", "value"),
    [
        ("schema_version", "compute-run-collector/v2"),
        ("source.kind", "ftp"),
        ("collector.captured_at", "2026-07-15T09:30:00"),
        ("run.status", "successful-ish"),
        ("run.lane", "accepted"),
        ("run.code.commit_sha", "deadbeef"),
        ("run.output_manifest.0.sha256", "not-a-hash"),
        ("run.output_manifest.0.size_bytes", "many"),
    ],
)
def test_malformed_exact_manifest_fields_are_explicitly_partial(path: str, value: str) -> None:
    manifest = _nio_manifest()
    target = manifest
    parts = path.split(".")
    for part in parts[:-1]:
        target = target[int(part)] if part.isdigit() else target[part]
    target[parts[-1]] = value

    report = build_compute_run_intake(ComputeRunIntakeRequest(manifest=manifest))

    normalized_path = path.replace(".0.", "[0].")
    assert report.coverage == "partial"
    assert normalized_path in report.invalid_fields
    assert f"invalid collector field: {normalized_path}" in report.errors


def test_malformed_container_shapes_do_not_crash_or_create_false_precision() -> None:
    manifest = _nio_manifest()
    manifest["run"]["resources"] = ["not", "a", "mapping"]
    manifest["run"]["argv"] = "librpa --unsafe-shape"
    manifest["run"]["output_manifest"][0]["sha256"] = "not-a-hash"
    manifest["run"]["output_manifest"][0]["size_bytes"] = "many"

    report = build_compute_run_intake(ComputeRunIntakeRequest(manifest=manifest))

    assert report.status == "partial"
    assert {
        "run.argv",
        "run.resources",
        "run.output_manifest[0].sha256",
        "run.output_manifest[0].size_bytes",
    }.issubset(report.invalid_fields)
    assert report.candidates["tool_run"]["argv"] == []
    assert report.candidates["artifacts"][0]["content_hash"] == ""
    assert report.candidates["artifacts"][0]["size_bytes"] == 0


def test_intake_contract_rejects_any_authoritative_capability() -> None:
    with pytest.raises(ValueError, match="trust-neutral"):
        ComputeRunIntakeReport(
            status="complete",
            coverage="complete",
            source_uri="file:///run",
            can_create_validation=True,
        )

    with pytest.raises(ValueError, match="forbidden candidates"):
        ComputeRunIntakeReport(
            status="complete",
            coverage="complete",
            source_uri="file:///run",
            candidates={"evidence": {}},
        )
