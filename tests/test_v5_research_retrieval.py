from brain.v5.markdown import write_md
from brain.v5.models import ClaimRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.query_index import build_query_index
from brain.v5.query_index_contracts import validate_index_build_report
from brain.v5.research_retrieval import ResearchQuery, exact_expand, query_records
from brain.v5.retrieval_audit import build_retrieval_audit
from brain.v5.store import write_record


def _write_claim(ws, claim_id, topic_id, statement, lifecycle_status="active"):
    record = ClaimRecord(
        claim_id=claim_id,
        topic_id=topic_id,
        statement=statement,
        evidence_profile="numerical_validation",
        confidence_state="candidate",
        active_uncertainty="Validation remains open.",
        lifecycle_status=lifecycle_status,
    )
    write_record(ws.registry_dir("claims") / f"{claim_id}.md", record, body=f"# {claim_id}\n")


def test_retrieval_filters_ranks_and_paginates_deterministically(tmp_path):
    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    _write_claim(ws, "c1", "qsgw", "head wing convergence")
    _write_claim(ws, "c2", "qsgw", "head convergence")
    _write_claim(ws, "c3", "quantum-gravity", "wing observable", "superseded")
    report = build_query_index(ws)

    first = query_records(
        ws,
        ResearchQuery(
            text="head wing",
            topic_ids=("qsgw",),
            families=("claims",),
            statuses=("active",),
            limit=1,
        ),
    )
    second = query_records(
        ws,
        ResearchQuery(text="head wing", topic_ids=("qsgw",), offset=1, limit=1),
    )

    assert validate_index_build_report(report) == ()
    assert [item.record_ref for item in first.items] == ["claim:c1"]
    assert first.items[0].lexical_score == 2
    assert first.truncated is True
    assert first.next_offset == 1
    assert [item.record_ref for item in second.items] == ["claim:c2"]


def test_topic_query_only_includes_explicitly_allowlisted_unscoped_families(tmp_path):
    from brain.v5.models import ExecutionEnvironmentRecord
    from brain.v5.record_envelope import RecordActor
    from brain.v5.record_repository import RecordRepository

    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    _write_claim(ws, "c1", "qsgw", "solver execution is reproducible")
    environment = ExecutionEnvironmentRecord(
        environment_id="solver-env",
        host="cluster",
        operating_system="Linux",
        architecture="x86_64",
        executable_paths={"solver": "/opt/solver"},
        executable_hashes={"solver": "a" * 64},
    )
    RecordRepository(
        ws,
        actor=RecordActor(actor_type="tool", actor_id="retrieval-test", host="pytest"),
    ).write("execution_environments", environment)
    write_md(
        ws.registry_dir("execution_environments") / "other-program-env.md",
        {
            "kind": "execution_environment",
            "environment_id": "other-program-env",
            "program_id": "other-program",
            "host": "cluster",
            "operating_system": "Linux",
            "architecture": "x86_64",
            "executable_paths": {"solver": "/opt/solver"},
            "executable_hashes": {"solver": "b" * 64},
        },
        "# Other Program Execution Environment\n",
    )
    build_query_index(ws)

    excluded = query_records(
        ws,
        ResearchQuery(
            text="execution",
            topic_ids=("qsgw",),
            families=("claims", "execution_environments"),
        ),
    )
    included = query_records(
        ws,
        ResearchQuery(
            text="execution",
            topic_ids=("qsgw",),
            families=("claims", "execution_environments"),
            include_unscoped_families=("execution_environments",),
        ),
    )

    assert [item.record_ref for item in excluded.items] == ["claim:c1"]
    assert {item.record_ref for item in included.items} == {
        "claim:c1",
        "execution_environment:solver-env",
    }
    assert "execution_environment:other-program-env" not in {
        item.record_ref for item in included.items
    }


def test_retrieval_propagates_malformed_coverage_and_excluded_exact_refs(tmp_path):
    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    _write_claim(ws, "c1", "qsgw", "head wing convergence")
    write_md(
        ws.registry_dir("claims") / "bad.md",
        {"topic_id": "qsgw", "kind": "claim"},
        "# Missing id\n",
    )
    report = build_query_index(ws)

    result = query_records(
        ws,
        ResearchQuery(text="absent", exact_refs=("claim:missing",)),
    )
    audit = build_retrieval_audit(ResearchQuery(text="absent"), result)

    assert report.malformed_count == 1
    assert result.coverage.malformed_count == 1
    assert result.coverage.exhaustive is False
    assert result.coverage.can_claim_no_result is False
    assert result.excluded_candidates == ("claim:missing",)
    assert audit["orientation_only"] is True
    assert audit["can_update_kernel_state"] is False
    assert audit["can_update_claim_trust"] is False
    assert audit["coverage"]["can_claim_no_result"] is False


def test_exact_retrieval_falls_back_to_document_for_unmaterializable_record(tmp_path):
    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    write_md(
        ws.registry_dir("claims") / "legacy-claim.md",
        {
            "claim_id": "legacy-claim",
            "topic_id": "qsgw",
            "kind": "claim",
            "statement": "Incomplete historical claim shape",
        },
        "# Incomplete historical claim\n",
    )
    build_query_index(ws)

    result = query_records(
        ws,
        ResearchQuery(exact_refs=("claim:legacy-claim",)),
    )

    assert result.excluded_candidates == ()
    assert result.items[0].record_ref == "claim:legacy-claim"
    assert result.items[0].exact_score == 100
    assert result.items[0].record["typed_materialization_status"] == "unavailable"


def test_retrieval_indexes_unicode_theory_terms_without_returning_unrelated_records(tmp_path):
    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    _write_claim(ws, "c-a", "qg", "unrelated lattice convergence note")
    _write_claim(ws, "c-z", "qg", "量子引力中的黑洞微观态需要保持来源边界")
    build_query_index(ws)

    result = query_records(ws, ResearchQuery(text="量子引力", topic_ids=("qg",)))

    assert [item.record_ref for item in result.items] == ["claim:c-z"]
    assert result.items[0].lexical_score >= 1


def test_retrieval_can_claim_scoped_no_result_when_unchecked_family_has_errors(tmp_path):
    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    _write_claim(ws, "c1", "qsgw", "head wing convergence")
    write_md(
        ws.registry_dir("tool_runs") / "bad.md",
        {"topic_id": "qsgw", "kind": "tool_run"},
        "# Missing run id\n",
    )
    build_query_index(ws)

    scoped = query_records(
        ws,
        ResearchQuery(text="absent", families=("claims",), topic_ids=("qsgw",)),
    )
    global_query = query_records(ws, ResearchQuery(text="absent"))

    assert scoped.items == ()
    assert scoped.coverage.exhaustive is True
    assert scoped.coverage.can_claim_no_result is True
    assert "tool_runs" in scoped.coverage.unchecked_families
    assert global_query.coverage.exhaustive is False
    assert global_query.coverage.can_claim_no_result is False


def test_orientation_query_is_state_fresh_but_never_exhaustive(tmp_path):
    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    _write_claim(ws, "c1", "qsgw", "orientation fixture")
    build_query_index(ws)

    result = query_records(
        ws,
        ResearchQuery(
            text="absent",
            families=("claims",),
            verification_mode="orientation",
        ),
    )

    assert result.index_status == "fresh"
    assert result.coverage.scope_state_fresh is True
    assert result.coverage.scope_content_verified is False
    assert result.coverage.scope_fresh is True
    assert result.coverage.exhaustive is False
    assert result.coverage.can_claim_no_result is False


def test_exact_expand_does_not_verify_the_global_query_index(tmp_path, monkeypatch):
    import brain.v5.research_retrieval as research_retrieval

    ws = WorkspacePaths(tmp_path)
    ws.ensure_layout()
    _write_claim(ws, "c1", "qsgw", "exact expansion fixture")
    build_query_index(ws)

    def reject_global_freshness(*_args, **_kwargs):
        raise AssertionError("exact canonical expansion must not verify the global index")

    monkeypatch.setattr(
        research_retrieval,
        "query_index_is_fresh",
        reject_global_freshness,
    )

    result = exact_expand(ws, ["claim:c1"], limit=10)

    assert [item.record_ref for item in result.items] == ["claim:c1"]
    assert result.index_status == "fresh"
