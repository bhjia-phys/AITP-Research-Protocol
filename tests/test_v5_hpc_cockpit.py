"""Tests for the AITP v5 HPC cockpit surface (tool_run-based, lane-contract-aware).

This replaces the earlier parallel-family design. HPC job state lives in
``tool_run`` records; these tests cover immutable forward attempt chains,
scientific_run_id inheritance, lane contracts, the orientation-only
cockpit aggregation, and the code_state / artifact back-link helpers.
"""

from __future__ import annotations

import json
import hashlib
from pathlib import Path


def _setup_workspace(tmp_path: Path):
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path / "ws")
    create_topic(ws, "si8-gw", context_id="librpa", title="Si8 G0W0 dataset")
    claim = create_claim(
        ws,
        topic_id="si8-gw",
        statement="Si8 G0W0 eigenvalues form a dataset entry per structure.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="Dataset generation not complete.",
    )
    return ws, claim


def test_tool_run_supersession_is_forward_only_and_hash_protected(tmp_path):
    from brain.v5.markdown import read_md
    from brain.v5.models import ToolRunRecord
    from brain.v5.store import read_record
    from brain.v5.tools import record_tool_run

    ws, claim = _setup_workspace(tmp_path)
    j1 = record_tool_run(
        ws, recipe_id="gw-submit-v1", tool_family="hpc_workflow", tool_name="sbatch",
        topic_id="si8-gw", claim_id=claim.claim_id,
        inputs={"remote_dir": "/scratch/r1"}, outputs={"slurm_job_id": "100"},
        evidence_status="submitted_pending", scientific_run_id="run-A", lane="diagnostic",
    )
    j2 = record_tool_run(
        ws, recipe_id="gw-submit-v2", tool_family="hpc_workflow", tool_name="sbatch",
        topic_id="si8-gw", claim_id=claim.claim_id,
        inputs={"remote_dir": "/scratch/r2"}, outputs={"slurm_job_id": "101"},
        evidence_status="running", supersedes=j1.run_id, lane="diagnostic",
    )
    reloaded = read_record(ws.registry_dir("tool_runs") / f"{j1.run_id}.md", ToolRunRecord)
    persisted_j2 = read_record(ws.registry_dir("tool_runs") / f"{j2.run_id}.md", ToolRunRecord)
    j1_frontmatter, _ = read_md(ws.registry_dir("tool_runs") / f"{j1.run_id}.md")
    j2_frontmatter, _ = read_md(ws.registry_dir("tool_runs") / f"{j2.run_id}.md")
    assert reloaded.superseded_by == ""
    assert "superseded_by" not in j1_frontmatter
    assert "superseded_by" not in j2_frontmatter
    assert j2.supersedes == j1.run_id
    assert persisted_j2.supersedes_run_id == j1.run_id
    assert persisted_j2.supersedes == j1.run_id
    assert j1_frontmatter["revision"] == 1
    assert j2_frontmatter["supersedes_run_id"] == j1.run_id
    assert j2_frontmatter["supersedes"] == []
    # scientific_run_id is inherited from the superseded attempt when not given
    assert j2.scientific_run_id == "run-A"
    # default lane is diagnostic so an unmarked run can never be mistaken for final
    assert j2.lane == "diagnostic"


def test_tool_run_supersession_allows_only_one_concurrent_successor(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from brain.v5.models import ToolRunRecord
    from brain.v5.store import list_records
    from brain.v5.tools import record_tool_run

    ws, claim = _setup_workspace(tmp_path)
    first = record_tool_run(
        ws,
        recipe_id="gw-submit-v1",
        tool_family="hpc_workflow",
        tool_name="sbatch",
        topic_id="si8-gw",
        claim_id=claim.claim_id,
        outputs={"slurm_job_id": "100"},
        scientific_run_id="run-A",
    )
    barrier = Barrier(2)

    def supersede(job_id: str):
        barrier.wait()
        return record_tool_run(
            ws,
            recipe_id=f"gw-submit-{job_id}",
            tool_family="hpc_workflow",
            tool_name="sbatch",
            topic_id="si8-gw",
            claim_id=claim.claim_id,
            outputs={"slurm_job_id": job_id},
            supersedes=first.run_id,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(supersede, "101"), pool.submit(supersede, "102")]
        results = []
        errors = []
        for future in futures:
            try:
                results.append(future.result())
            except ValueError as exc:
                errors.append(str(exc))

    records = list_records(ws.registry_dir("tool_runs"), ToolRunRecord)
    successors = [run for run in records if run.supersedes_run_id == first.run_id]
    assert len(results) == 1
    assert len(errors) == 1
    assert "already has successor" in errors[0]
    assert [run.run_id for run in successors] == [results[0].run_id]


def test_tool_run_environment_participates_in_immutable_identity(tmp_path):
    from brain.v5.tools import record_tool_run

    ws, claim = _setup_workspace(tmp_path)
    local = record_tool_run(
        ws,
        recipe_id="gw-submit",
        tool_family="hpc_workflow",
        tool_name="sbatch",
        topic_id="si8-gw",
        claim_id=claim.claim_id,
        inputs={"command": "sbatch run.slurm"},
        outputs={"status": "completed"},
        environment={"cluster": "dongfang"},
    )
    remote = record_tool_run(
        ws,
        recipe_id="gw-submit",
        tool_family="hpc_workflow",
        tool_name="sbatch",
        topic_id="si8-gw",
        claim_id=claim.claim_id,
        inputs={"command": "sbatch run.slurm"},
        outputs={"status": "completed"},
        environment={"cluster": "huairou"},
    )

    assert remote.run_id != local.run_id


def test_tool_run_rejects_unknown_lane(tmp_path):
    import pytest

    from brain.v5.tools import record_tool_run

    ws, claim = _setup_workspace(tmp_path)
    with pytest.raises(ValueError, match="lane"):
        record_tool_run(
            ws,
            recipe_id="gw-submit",
            tool_family="hpc_workflow",
            tool_name="sbatch",
            topic_id="si8-gw",
            claim_id=claim.claim_id,
            lane="accepted_final_without_review",
        )


def test_tool_run_identity_is_unambiguous_across_delimited_fields(tmp_path):
    from brain.v5.tools import record_tool_run

    ws, claim = _setup_workspace(tmp_path)
    first = record_tool_run(
        ws,
        recipe_id="recipe:a",
        tool_family="family",
        tool_name="sbatch",
        topic_id="si8-gw",
        claim_id=claim.claim_id,
    )
    second = record_tool_run(
        ws,
        recipe_id="recipe",
        tool_family="a:family",
        tool_name="sbatch",
        topic_id="si8-gw",
        claim_id=claim.claim_id,
    )

    assert second.run_id != first.run_id


def test_ambiguous_tool_run_ids_are_insertion_order_independent(tmp_path):
    from brain.v5.tools import record_tool_run

    identities = [
        {"recipe_id": "recipe:a", "tool_family": "family"},
        {"recipe_id": "recipe", "tool_family": "a:family"},
    ]

    def record_in_order(base, order):
        ws, claim = _setup_workspace(base)
        result = {}
        for index in order:
            identity = identities[index]
            run = record_tool_run(
                ws,
                recipe_id=identity["recipe_id"],
                tool_family=identity["tool_family"],
                tool_name="sbatch",
                topic_id="si8-gw",
                claim_id=claim.claim_id,
            )
            result[index] = run.run_id
        return result

    forward = record_in_order(tmp_path / "forward", [0, 1])
    reverse = record_in_order(tmp_path / "reverse", [1, 0])

    assert forward == reverse
    assert forward[0] != forward[1]


def test_ambiguous_tool_run_ids_are_concurrency_safe(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from brain.v5.tools import record_tool_run

    ws, claim = _setup_workspace(tmp_path)
    barrier = Barrier(2)

    def create(recipe_id, tool_family):
        barrier.wait()
        return record_tool_run(
            ws,
            recipe_id=recipe_id,
            tool_family=tool_family,
            tool_name="sbatch",
            topic_id="si8-gw",
            claim_id=claim.claim_id,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(create, "recipe:a", "family"),
            pool.submit(create, "recipe", "a:family"),
        ]
        runs = [future.result() for future in futures]

    assert len({run.run_id for run in runs}) == 2


def test_tool_run_replay_accepts_explicit_inherited_scientific_run_id(tmp_path):
    from brain.v5.tools import record_tool_run

    ws, claim = _setup_workspace(tmp_path)
    first = record_tool_run(
        ws,
        recipe_id="gw-submit-v1",
        tool_family="hpc_workflow",
        tool_name="sbatch",
        topic_id="si8-gw",
        claim_id=claim.claim_id,
        outputs={"slurm_job_id": "100"},
        scientific_run_id="run-A",
    )
    successor_args = {
        "recipe_id": "gw-submit-v2",
        "tool_family": "hpc_workflow",
        "tool_name": "sbatch",
        "topic_id": "si8-gw",
        "claim_id": claim.claim_id,
        "outputs": {"slurm_job_id": "101"},
        "supersedes": first.run_id,
    }
    inherited = record_tool_run(ws, **successor_args)
    replayed = record_tool_run(
        ws,
        **successor_args,
        scientific_run_id="run-A",
    )

    assert inherited.run_id == replayed.run_id
    assert replayed.scientific_run_id == "run-A"


def test_tool_run_supersession_rejects_cross_scope_and_run_mismatch(tmp_path):
    import pytest

    from brain.v5.tools import record_tool_run
    from brain.v5.workspace import create_claim, create_topic

    ws, claim = _setup_workspace(tmp_path)
    first = record_tool_run(
        ws,
        recipe_id="gw-submit-v1",
        tool_family="hpc_workflow",
        tool_name="sbatch",
        topic_id="si8-gw",
        claim_id=claim.claim_id,
        scientific_run_id="run-A",
    )
    create_topic(ws, "other-topic", context_id="librpa", title="Other topic")
    other_claim = create_claim(
        ws,
        topic_id="other-topic",
        statement="Independent topic-local claim.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="No cross-topic supersession is allowed.",
    )

    with pytest.raises(ValueError, match="same topic and claim"):
        record_tool_run(
            ws,
            recipe_id="gw-submit-v2",
            tool_family="hpc_workflow",
            tool_name="sbatch",
            topic_id="other-topic",
            claim_id=other_claim.claim_id,
            supersedes=first.run_id,
        )
    with pytest.raises(ValueError, match="scientific_run_id"):
        record_tool_run(
            ws,
            recipe_id="gw-submit-v2",
            tool_family="hpc_workflow",
            tool_name="sbatch",
            topic_id="si8-gw",
            claim_id=claim.claim_id,
            scientific_run_id="run-B",
            supersedes=first.run_id,
        )


def test_uncontested_tool_run_keeps_v1_deterministic_id(tmp_path):
    from brain.v5.ids import prefixed_id
    from brain.v5.tools import record_tool_run

    ws, claim = _setup_workspace(tmp_path)
    run = record_tool_run(
        ws,
        recipe_id="gw-submit",
        tool_family="hpc_workflow",
        tool_name="sbatch",
        topic_id="si8-gw",
        claim_id=claim.claim_id,
    )

    def stable_hash(value):
        encoded = json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()[:12]

    v1_basis = ":".join(
        [
            "gw-submit",
            "hpc_workflow",
            "sbatch",
            "si8-gw",
            claim.claim_id,
            stable_hash({}),
            stable_hash({}),
            stable_hash({}),
            "unreviewed",
            stable_hash([]),
            "",
            "",
            "diagnostic",
        ]
    )
    assert run.run_id == prefixed_id("tool-run", v1_basis, max_slug=72)


def test_tool_run_mcp_surface_exposes_attempt_chain_and_deprecated_alias(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_record_tool_run
    from brain.v5.tools import record_tool_run

    ws, claim = _setup_workspace(tmp_path)
    first = record_tool_run(
        ws,
        recipe_id="gw-submit-v1",
        tool_family="hpc_workflow",
        tool_name="sbatch",
        topic_id="si8-gw",
        claim_id=claim.claim_id,
        outputs={"slurm_job_id": "100"},
        scientific_run_id="run-A",
    )

    payload = aitp_v5_record_tool_run(
        str(ws.base),
        recipe_id="gw-submit-v2",
        tool_family="hpc_workflow",
        tool_name="sbatch",
        topic_id="si8-gw",
        claim_id=claim.claim_id,
        outputs={"slurm_job_id": "101"},
        evidence_status="running",
        supersedes=first.run_id,
        lane="final",
    )

    assert payload["supersedes_run_id"] == first.run_id
    assert payload["supersedes"] == first.run_id
    assert payload["scientific_run_id"] == "run-A"
    assert payload["lane"] == "final"


def test_tool_run_public_contract_requires_attempt_fields_and_alias_consistency(tmp_path):
    import pytest

    from brain.v5.contracts import ContractError
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.tools import record_tool_run, tool_run_payload

    ws, claim = _setup_workspace(tmp_path)
    run = record_tool_run(
        ws,
        recipe_id="gw-submit",
        tool_family="hpc_workflow",
        tool_name="sbatch",
        topic_id="si8-gw",
        claim_id=claim.claim_id,
    )
    payload = tool_run_payload(run)
    assert require_valid_public_surface("tool_run_record", payload) == payload

    for missing in ("scientific_run_id", "supersedes_run_id", "supersedes", "lane"):
        invalid = dict(payload)
        invalid.pop(missing)
        with pytest.raises(ContractError, match=missing):
            require_valid_public_surface("tool_run_record", invalid)

    mismatched = {**payload, "supersedes": "different-run"}
    with pytest.raises(ContractError, match="supersedes"):
        require_valid_public_surface("tool_run_record", mismatched)

    invalid_lane = {**payload, "lane": "unreviewed_final"}
    with pytest.raises(ContractError, match="lane"):
        require_valid_public_surface("tool_run_record", invalid_lane)


def test_tool_run_cli_surface_exposes_attempt_chain_and_deprecated_alias(
    tmp_path,
    capsys,
):
    from brain.v5.cli import main
    from brain.v5.tools import record_tool_run

    ws, claim = _setup_workspace(tmp_path)
    first = record_tool_run(
        ws,
        recipe_id="gw-submit-v1",
        tool_family="hpc_workflow",
        tool_name="sbatch",
        topic_id="si8-gw",
        claim_id=claim.claim_id,
        outputs={"slurm_job_id": "100"},
        scientific_run_id="run-A",
    )

    assert main(
        [
            "--base",
            str(ws.base),
            "tool",
            "run",
            "record",
            "--recipe",
            "gw-submit-v2",
            "--family",
            "hpc_workflow",
            "--name",
            "sbatch",
            "--topic",
            "si8-gw",
            "--claim",
            claim.claim_id,
            "--outputs-json",
            '{"slurm_job_id":"101"}',
            "--scientific-run-id",
            "run-A",
            "--supersedes",
            first.run_id,
            "--lane",
            "final",
        ]
    ) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["supersedes_run_id"] == first.run_id
    assert payload["supersedes"] == first.run_id
    assert payload["scientific_run_id"] == "run-A"
    assert payload["lane"] == "final"


def test_lane_contract_record_and_effective(tmp_path):
    from brain.v5.lane_contracts import (
        get_effective_lane_contract,
        lane_contract_payload,
        record_lane_contract,
    )
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim = _setup_workspace(tmp_path)
    contract = record_lane_contract(
        ws, topic_id="si8-gw", campaign="archivefaithful", claim_id=claim.claim_id,
        forbidden_roots=["/data/home/bad/mgo-1135"],
        preferred_clean_roots=["/data/home/good/mgo-1210"],
        final_rules=["No noiter/unfinished/nonconverged as final."],
        trust_update_forbidden=True,
    )
    require_valid_public_surface("lane_contract_record", lane_contract_payload(contract))
    assert contract.forbidden_roots == ["/data/home/bad/mgo-1135"]
    assert contract.trust_update_forbidden is True
    assert get_effective_lane_contract(ws, "si8-gw").contract_id == contract.contract_id


def test_hpc_cockpit_aggregates_runs(tmp_path):
    from brain.v5.hpc_cockpit import build_hpc_cockpit
    from brain.v5.lane_contracts import record_lane_contract
    from brain.v5.public_surfaces import require_valid_public_surface
    from brain.v5.tools import record_tool_run

    ws, claim = _setup_workspace(tmp_path)
    j1 = record_tool_run(
        ws, recipe_id="gw-submit-v1", tool_family="hpc_workflow", tool_name="sbatch",
        topic_id="si8-gw", claim_id=claim.claim_id, inputs={"remote_dir": "/r1"},
        outputs={"slurm_job_id": "200"}, evidence_status="submitted_pending",
        scientific_run_id="run-A", lane="diagnostic",
    )
    record_tool_run(
        ws, recipe_id="gw-submit-v2", tool_family="hpc_workflow", tool_name="sbatch",
        topic_id="si8-gw", claim_id=claim.claim_id, inputs={"remote_dir": "/r2"},
        outputs={"slurm_job_id": "201"}, evidence_status="running",
        scientific_run_id="run-A", supersedes=j1.run_id, lane="diagnostic",
    )
    record_tool_run(
        ws, recipe_id="gw-fail", tool_family="hpc_workflow", tool_name="sbatch",
        topic_id="si8-gw", claim_id=claim.claim_id, inputs={"remote_dir": "/r3"},
        outputs={"slurm_job_id": "202"}, evidence_status="failed_setup",
        scientific_run_id="run-B", lane="diagnostic",
    )
    record_lane_contract(
        ws, topic_id="si8-gw", campaign="archivefaithful",
        forbidden_roots=["/bad"], trust_update_forbidden=True,
    )

    cockpit = build_hpc_cockpit(ws, "si8-gw")
    require_valid_public_surface("hpc_cockpit", cockpit)
    active = [job["scheduler_job_id"] for job in cockpit["active_jobs"]]
    # j1 was superseded -> not current; j2 running -> active; j3 failed -> failure history
    assert "201" in active and "200" not in active
    assert any(fail["scheduler_job_id"] == "202" for fail in cockpit["failure_history"])
    assert cockpit["lane_counts"]["diagnostic"] == 2
    assert cockpit["lane_contract"]["forbidden_roots"] == ["/bad"]
    assert cockpit["conclusions_not_allowed"]  # active job + failure + diagnostic-only + trust forbidden
    assert cockpit["next_valid_actions"]
    assert "# HPC Cockpit" in cockpit["markdown"]


def test_hpc_cockpit_preserves_superseded_failure_history(tmp_path):
    from brain.v5.hpc_cockpit import build_hpc_cockpit
    from brain.v5.tools import record_tool_run

    ws, claim = _setup_workspace(tmp_path)
    failed = record_tool_run(
        ws,
        recipe_id="gw-submit-v1",
        tool_family="hpc_workflow",
        tool_name="sbatch",
        topic_id="si8-gw",
        claim_id=claim.claim_id,
        outputs={"slurm_job_id": "500"},
        evidence_status="failed_runtime",
        scientific_run_id="run-A",
    )
    record_tool_run(
        ws,
        recipe_id="gw-submit-v2",
        tool_family="hpc_workflow",
        tool_name="sbatch",
        topic_id="si8-gw",
        claim_id=claim.claim_id,
        outputs={"slurm_job_id": "501"},
        evidence_status="completed",
        supersedes=failed.run_id,
    )

    cockpit = build_hpc_cockpit(ws, "si8-gw")

    assert [item["scheduler_job_id"] for item in cockpit["failure_history"]] == ["500"]
    assert [item["scheduler_job_id"] for item in cockpit["effective_attempts"]] == ["501"]


def test_link_helpers_fill_provenance(tmp_path):
    from brain.v5.hpc_cockpit import build_hpc_cockpit
    from brain.v5.tools import (
        link_artifact_to_run,
        link_code_state_to_run,
        record_tool_run,
    )

    ws, claim = _setup_workspace(tmp_path)
    j = record_tool_run(
        ws, recipe_id="r", tool_family="hpc_workflow", tool_name="sbatch",
        topic_id="si8-gw", claim_id=claim.claim_id, outputs={"slurm_job_id": "300"},
        evidence_status="completed", lane="diagnostic",
    )
    before = build_hpc_cockpit(ws, "si8-gw")
    assert before["provenance_gaps"]["missing_code_state_run_ids"] == [j.run_id]

    link_code_state_to_run(ws, run_id=j.run_id, code_state_id="code-state-librpa-abc")
    link_code_state_to_run(ws, run_id=j.run_id, code_state_id="code-state-librpa-abc")  # idempotent
    link_artifact_to_run(ws, run_id=j.run_id, artifact_id="source-asset-gw-xyz")

    after = build_hpc_cockpit(ws, "si8-gw")
    assert after["provenance_gaps"]["missing_code_state_run_ids"] == []
    assert after["provenance_gaps"]["missing_artifact_run_ids"] == []


def test_tool_run_replay_and_concurrent_links_merge_provenance(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier, local

    from brain.v5 import tool_run_transitions as transitions_module
    from brain.v5.models import ToolRunRecord
    from brain.v5.store import read_record
    from brain.v5.tools import link_artifact_to_run, link_code_state_to_run, record_tool_run

    ws, claim = _setup_workspace(tmp_path)
    run_args = {
        "recipe_id": "gw-submit",
        "tool_family": "hpc_workflow",
        "tool_name": "sbatch",
        "topic_id": "si8-gw",
        "claim_id": claim.claim_id,
        "outputs": {"slurm_job_id": "600"},
    }
    run = record_tool_run(ws, **run_args)
    link_code_state_to_run(ws, run_id=run.run_id, code_state_id="code-state-existing")
    replayed = record_tool_run(ws, **run_args)
    assert replayed.code_state_ids == ["code-state-existing"]

    original_basis = transitions_module.tool_run_revision_basis
    barrier = Barrier(2)
    thread_state = local()

    def synchronized_basis(repository, run_id):
        result = original_basis(repository, run_id)
        if not getattr(thread_state, "synchronized", False):
            thread_state.synchronized = True
            barrier.wait()
        return result

    monkeypatch.setattr(
        transitions_module,
        "tool_run_revision_basis",
        synchronized_basis,
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(
                link_code_state_to_run,
                ws,
                run_id=run.run_id,
                code_state_id="code-state-concurrent",
            ),
            pool.submit(
                link_artifact_to_run,
                ws,
                run_id=run.run_id,
                artifact_id="artifact-concurrent",
            ),
        ]
        for future in futures:
            future.result()

    persisted = read_record(
        ws.registry_dir("tool_runs") / f"{run.run_id}.md",
        ToolRunRecord,
    )
    assert persisted.code_state_ids == ["code-state-existing", "code-state-concurrent"]
    assert persisted.artifact_ids == ["artifact-concurrent"]


def test_hpc_cockpit_mcp_surface(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_hpc_cockpit, aitp_v5_record_lane_contract
    from brain.v5.tools import record_tool_run

    ws, claim = _setup_workspace(tmp_path)
    record_tool_run(
        ws, recipe_id="r", tool_family="hpc_workflow", tool_name="sbatch",
        topic_id="si8-gw", claim_id=claim.claim_id, outputs={"slurm_job_id": "400"},
        evidence_status="running", lane="diagnostic",
    )
    aitp_v5_record_lane_contract(
        str(ws.root), topic_id="si8-gw", campaign="bench", final_allowlist=["c", "bp"],
    )
    cockpit = aitp_v5_hpc_cockpit(str(ws.root), topic_id="si8-gw")
    assert cockpit["kind"] == "hpc_cockpit"
    assert cockpit["active_jobs"]
    assert cockpit["lane_contract"]["final_allowlist"] == ["c", "bp"]
