from __future__ import annotations

from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys


def _seed_workspace(tmp_path: Path):
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "codex-facade-topic", context_id="codex-context", title="Codex facade topic")
    claim = create_claim(
        ws,
        topic_id="codex-facade-topic",
        statement="Compact Codex context should expand only when the research step needs it.",
        evidence_profile="protocol_engineering",
        confidence_state="hypothesis",
        active_uncertainty="facade must not expose trust apply as a default action",
    )
    bind_session(
        ws,
        "codex-session",
        topic_id="codex-facade-topic",
        context_id="codex-context",
        active_claim=claim.claim_id,
    )
    return ws, claim


def _read_content_length_message(stream: BytesIO) -> dict:
    header = b""
    while not (header.endswith(b"\r\n\r\n") or header.endswith(b"\n\n")):
        chunk = stream.read(1)
        assert chunk, f"unexpected EOF while reading MCP header: {header!r}"
        header += chunk
    length = None
    for line in header.decode("utf-8").replace("\r\n", "\n").split("\n"):
        if line.lower().startswith("content-length:"):
            length = int(line.split(":", 1)[1].strip())
            break
    assert length is not None
    return json.loads(stream.read(length).decode("utf-8"))


def test_codex_facade_tools_are_compact_progressive_and_trust_safe(tmp_path):
    from brain.v5.mcp_tools import (
        aitp_v5_codex_autoroute,
        aitp_v5_codex_closeout,
        aitp_v5_codex_enter,
        aitp_v5_codex_expand,
        aitp_v5_codex_literature_step,
        aitp_v5_codex_record_apply,
        aitp_v5_codex_recording_step,
        aitp_v5_codex_tool_catalog,
    )
    from brain.v5.models import ReferenceLocationRecord, SourceAssetRecord, TrustUpdateRecord
    from brain.v5.store import list_records

    ws, claim = _seed_workspace(tmp_path)

    catalog = aitp_v5_codex_tool_catalog(profile="entry")
    assert catalog["kind"] == "codex_mcp_surface_catalog"
    assert catalog["default_mcp_surface"] == "codex"
    assert "aitp_v5_apply_trust_update" in catalog["hidden_in_codex_surface"]
    assert catalog["progressive_policy"]["start_with"] == "aitp_v5_codex_autoroute"
    assert catalog["progressive_policy"]["enter_payload_profile"] == "minimal"
    assert "needs_prior_research_state" in catalog["autoroute_semantic_contract"]["assessment_fields"]

    route = aitp_v5_codex_autoroute(
        str(ws.base),
        session_id="codex-session",
        request_summary="继续这个理论物理课题，检查最新结果并补研究记录",
    )
    assert route["kind"] == "codex_auto_route_decision"
    assert route["decision"] == "enter_existing_session"
    assert route["aitp_required_before_answer"] is True
    assert route["recommended_next_tool"] == "aitp_v5_codex_enter"
    assert route["recommended_args"]["payload_profile"] == "minimal"
    assert route["recommended_sequence"][1]["arguments"]["expansion"] == "timeline"
    assert route["can_update_kernel_state"] is False
    assert route["can_update_claim_trust"] is False

    generic_route = aitp_v5_codex_autoroute(
        str(ws.base),
        request_summary="What is a Green function in physics?",
    )
    assert generic_route["decision"] == "answer_without_aitp"
    assert generic_route["safe_to_answer_without_aitp"] is True
    assert "generic_knowledge_question_without_project_context" in generic_route["reason_codes"]

    semantic_route = aitp_v5_codex_autoroute(
        str(ws.base),
        session_id="codex-session",
        request_summary="Please handle the next step from yesterday.",
        semantic_assessment={
            "task_kind": "topic_continuation",
            "needs_prior_research_state": True,
            "needs_latest_topic_state": True,
            "should_use_aitp": "required",
            "confidence": "medium",
            "rationale": "The request depends on prior project state even though the words are generic.",
        },
    )
    assert semantic_route["semantic_assessment_used"] is True
    assert semantic_route["decision"] == "enter_existing_session"
    assert "semantic_needs_prior_research_state" in semantic_route["reason_codes"]
    assert semantic_route["truth_source"] == "codex_autoroute_semantic_guarded"

    semantic_generic = aitp_v5_codex_autoroute(
        str(ws.base),
        request_summary="Please explain the basic idea.",
        semantic_assessment={
            "task_kind": "generic_qna",
            "is_generic_textbook_question": True,
            "should_use_aitp": "not_required",
            "confidence": "high",
            "rationale": "No project state, record, validation, or claim boundary is needed.",
        },
    )
    assert semantic_generic["decision"] == "answer_without_aitp"
    assert semantic_generic["semantic_assessment"]["is_generic_textbook_question"] is True

    entered = aitp_v5_codex_enter(
        str(ws.base),
        session_id="codex-session",
        request_summary="continue the topic and maybe draft a note",
    )
    assert entered["kind"] == "codex_entry_context"
    assert entered["payload_profile"] == "minimal"
    assert entered["active_session_ready"] is True
    assert entered["process_mode"] == "writing"
    assert entered["entry_card"]["kind"] == "codex_entry_card"
    assert "context_pack" not in entered
    assert entered["entry_card"]["model_policy"]["do_not_record_from_entry_card"] is True
    assert entered["expand_context_pack_when_needed"]["arguments"]["expansion"] == "context_pack"
    assert entered["can_update_claim_trust"] is False

    context_entered = aitp_v5_codex_enter(
        str(ws.base),
        session_id="codex-session",
        request_summary="continue the topic and maybe draft a note",
        payload_profile="context_pack",
    )
    assert context_entered["payload_profile"] == "context_pack"
    assert context_entered["context_pack"]["kind"] == "aitp_context_pack"
    assert "entry_card" not in context_entered

    outline = aitp_v5_codex_expand(str(ws.base), session_id="codex-session", expansion="note_outline")
    assert outline["kind"] == "codex_context_expansion"
    assert outline["surface"]["kind"] == "note_outline"
    assert outline["can_update_kernel_state"] is False

    recording = aitp_v5_codex_recording_step(
        str(ws.base),
        session_id="codex-session",
        event_type="source_touched",
        summary="Found a paper section that may be reused in the note.",
        claim_id=claim.claim_id,
        slot="reference_location",
    )
    assert recording["kind"] == "codex_recording_step"
    assert recording["classification"]["decision"] in {"navigate", "defer", "checkpoint"}
    assert recording["slot_expansion"]["recommended_write_tool"] == "aitp_v5_record_reference_location"
    assert recording["write_executed"] is False
    assert recording["can_update_claim_trust"] is False

    applied = aitp_v5_codex_record_apply(
        str(ws.base),
        session_id="codex-session",
        slot="source_asset",
        event_type="source_touched",
        summary="Register source identity through compact Codex facade.",
        payload={
            "asset_type": "paper",
            "uri": "https://arxiv.org/abs/2604.00001",
            "title": "Compact facade source identity paper",
            "summary": "Source identity only; no evidence.",
        },
    )
    assert applied["kind"] == "codex_record_apply"
    assert applied["write_executed"] is True
    assert applied["record_ref"].startswith("source_asset:")
    assert applied["can_update_claim_trust"] is False

    suggested = aitp_v5_codex_literature_step(
        str(ws.base),
        session_id="codex-session",
        uri="https://arxiv.org/abs/2604.14695",
        label="Related long-range spin-chain paper",
        external_id="arXiv:2604.14695",
        short_summary="Potential related work; claim relation still needs review.",
        detected_relevance="related work",
    )
    assert suggested["action"] == "suggest"
    assert suggested["surface"]["kind"] == "literature_intake_suggestion"
    assert suggested["can_update_kernel_state"] is False

    recorded = aitp_v5_codex_literature_step(
        str(ws.base),
        session_id="codex-session",
        action="record_reference",
        uri="https://arxiv.org/abs/2604.14695",
        label="Related long-range spin-chain paper",
        external_id="arXiv:2604.14695",
        short_summary="Reference only; no evidence yet.",
        detected_relevance="related work",
    )
    references = list_records(ws.registry_dir("reference_locations"), ReferenceLocationRecord)
    source_assets = list_records(ws.registry_dir("source_assets"), SourceAssetRecord)
    trust_updates = list_records(ws.registry_dir("trust_updates"), TrustUpdateRecord)
    assert recorded["kernel_state_change"] == "source_asset_and_reference_location_records"
    assert recorded["recorded_source_asset"]["orientation_only"] is True
    assert recorded["recorded_reference_location"]["source_ref"].startswith("source_asset:")
    assert recorded["can_update_claim_trust"] is False
    assert len(references) == 1
    assert len(source_assets) == 2
    assert trust_updates == []

    closeout = aitp_v5_codex_closeout(
        str(ws.base),
        session_id="codex-session",
        summary="Session ended after planning compact Codex facade behavior.",
    )
    assert closeout["kind"] == "codex_closeout"
    assert closeout["mode"] == "preview"
    assert closeout["write_executed"] is False
    assert closeout["can_update_claim_trust"] is False


def test_codex_recording_step_includes_lightweight_sibling_claim_plan(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_codex_recording_step
    from brain.v5.workspace import create_claim

    ws, active_claim = _seed_workspace(tmp_path)
    sibling = create_claim(
        ws,
        topic_id="codex-facade-topic",
        statement="Hidden symmetry matrix-unit workflow controls level-spacing statistics.",
        evidence_profile="mixed_theory_numeric",
        confidence_state="hypothesis",
        active_uncertainty="finite-size diagnostics do not prove the hidden symmetry theorem",
    )

    step = aitp_v5_codex_recording_step(
        str(ws.base),
        session_id="codex-session",
        event_type="numerical_diagnostic",
        summary="Hidden symmetry matrix-unit workflow has an open gap in level-spacing statistics validation.",
        produced_artifacts=["results/level_spacing_L13.json"],
    )

    plan = step["lightweight_record_write_plan"]
    assert plan["kind"] == "lightweight_record_write_plan"
    assert plan["decision"] == "plan_write"
    assert plan["target_claim"]["target_claim_id"] == sibling.claim_id
    assert plan["target_claim"]["target_claim_id"] != active_claim.claim_id
    assert step["write_executed"] is False
    assert step["can_update_claim_trust"] is False


def test_codex_recording_step_accepts_windows_local_file_artifact_refs(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_codex_recording_step

    ws, _claim = _seed_workspace(tmp_path)
    report = tmp_path / "report.pdf"
    report.write_bytes(b"%PDF-1.4\n% test\n")
    windows_like_ref = f"local:file:{report.as_posix()}"

    step = aitp_v5_codex_recording_step(
        str(ws.base),
        session_id="codex-session",
        event_type="artifact_created",
        summary="Saved compact Codex facade report PDF artifact.",
        produced_artifacts=[windows_like_ref],
    )

    plan = step["lightweight_record_write_plan"]
    assert plan["decision"] != "unsupported"
    assert "Malformed input ref" not in plan["final_human_readable_summary"]
    assert "artifact" in plan["selected_record_types"]
    artifact_plan = next(item for item in plan["typed_write_plan"] if item["record_type"] == "artifact")
    assert "report.pdf" in artifact_plan["required_fields"]["path"]


def test_codex_pdf_note_closeout_can_backfill_typed_validation_package(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_codex_closeout, aitp_v5_codex_record_apply
    from brain.v5.workspace import get_claim

    ws, claim = _seed_workspace(tmp_path)
    repo = tmp_path / "report-repo"
    figures = repo / "figures"
    figures.mkdir(parents=True)
    _git(repo, "init")
    _git(repo, "config", "user.email", "aitp@example.invalid")
    _git(repo, "config", "user.name", "AITP Test")
    old_note = repo / "old_note.md"
    tex = repo / "report.tex"
    style = repo / "aitpnote.sty"
    pdf = repo / "report.pdf"
    figure = figures / "diagram.pdf"
    old_note.write_text("# Old note\n", encoding="utf-8")
    tex.write_text("\\documentclass{article}\\begin{document}seed\\end{document}\n", encoding="utf-8")
    style.write_text("% seed style\n", encoding="utf-8")
    _git(repo, "add", "old_note.md", "report.tex", "aitpnote.sty")
    _git(repo, "commit", "-m", "seed report")
    tex.write_text("\\documentclass{article}\\begin{document}updated\\end{document}\n", encoding="utf-8")
    style.write_text("% updated style\n", encoding="utf-8")
    pdf.write_bytes(b"%PDF-1.4\n% generated report\n")
    figure.write_bytes(b"%PDF-1.4\n% generated figure\n")

    closeout_kwargs = {
        "session_id": "codex-session",
        "claim_id": claim.claim_id,
        "summary": "Completed compact facade PDF note build and layout validation.",
        "inputs": [str(old_note)],
        "generated_artifacts": [
            {
                "uri": f"local:file:{tex.as_posix()}",
                "artifact_type": "tex_source",
                "summary": "Generated LaTeX source.",
                "repo_path": str(repo),
            },
            {
                "uri": f"local:file:{pdf.as_posix()}",
                "artifact_type": "pdf_report",
                "summary": "Compiled PDF report.",
                "repo_path": str(repo),
            },
        ],
        "validation_commands": [
            "pdflatex report.tex",
            "Select-String -Path report.log -Pattern 'Fatal|Error|undefined|Overfull'",
            "render selected PDF pages and visually spot-check layout",
        ],
        "changed_files": ["report.tex", "report.pdf", "aitpnote.sty", "figures/diagram.pdf"],
        "claim_boundary": {
            "validated": ["PDF compile, log hygiene, and selected rendered-page layout were checked."],
            "cannot_say": ["This does not validate the underlying physics claim."],
        },
        "sensemaking_summary": (
            "Document build closeout boundary: validates PDF artifact build/layout only; no claim trust change."
        ),
    }

    before_claim = get_claim(ws, claim.claim_id)
    closeout = aitp_v5_codex_closeout(str(ws.base), apply=True, **closeout_kwargs)
    surface = closeout["surface"]
    assert any(ref.startswith("quiet_checkpoint:") for ref in surface["written_refs"])
    assert any(ref.startswith("sensemaking_report:") for ref in surface["written_refs"])
    initial_missing = set(closeout["record_completeness_audit"]["missing_recommended_slots"])
    assert {"artifact", "tool_recipe", "tool_run", "code_state", "validation_result"} <= initial_missing
    apply_plan = closeout["record_completeness_audit"]["compact_apply_plan"]
    planned_slots = [action["slot"] for action in apply_plan["actions"]]
    assert {"artifact", "tool_recipe", "tool_run", "code_state", "validation_contract", "validation_result"} <= set(planned_slots)
    assert apply_plan["validation_semantics"]["boundary"]["does_not_validate"] == "underlying physics claim"

    artifact_ids = []
    for path, artifact_type, summary in [
        (tex, "tex_source", "Generated LaTeX source."),
        (pdf, "pdf_report", "Compiled PDF report."),
    ]:
        applied = aitp_v5_codex_record_apply(
            str(ws.base),
            session_id="codex-session",
            slot="artifact",
            summary=summary,
            payload={
                "artifact_type": artifact_type,
                "uri": f"local:file:{path.as_posix()}",
                "summary": summary,
                "metadata": {"closeout_run_id": surface["run_id"]},
            },
        )
        assert applied["ok"] is True
        artifact_ids.append(applied["record"]["artifact_id"])

    code_state = aitp_v5_codex_record_apply(
        str(ws.base),
        session_id="codex-session",
        slot="code_state",
        payload={
            "worktree_path": str(repo),
            "changed_files": closeout_kwargs["changed_files"],
            "runtime_environment": {"closeout_run_id": surface["run_id"]},
            "known_divergence": "dirty report tree after note generation",
        },
    )
    assert code_state["ok"] is True
    assert code_state["record"]["dirty"] is True
    tracking = code_state["record"]["runtime_environment"]["changed_files_tracking"]
    assert any(item["path"] == "report.pdf" and item["untracked"] is True for item in tracking)
    assert code_state["record"]["runtime_environment"]["clean_reproducibility_anchor"] is False

    recipe = aitp_v5_codex_record_apply(
        str(ws.base),
        session_id="codex-session",
        slot="tool_recipe",
        payload={
            "recipe_id": "codex-document-build-regression",
            "tool_family": "codex_document_build",
            "tool_name": "latex_pdf_note_validation",
            "purpose": "Build the LaTeX note and inspect PDF/log outputs.",
            "required_inputs": ["old_note.md", "report.tex", "aitpnote.sty"],
            "expected_outputs": ["report.pdf", "report.log", "rendered page images"],
            "invariants": [
                "validates document build/layout only",
                "does not validate physics claim",
                "does not promote claim trust",
            ],
        },
    )
    assert recipe["ok"] is True

    run = aitp_v5_codex_record_apply(
        str(ws.base),
        session_id="codex-session",
        slot="tool_run",
        payload={
            "recipe_id": recipe["record"]["recipe_id"],
            "tool_family": "codex_document_build",
            "tool_name": "latex_pdf_note_validation",
            "inputs": {"old_note_path": str(old_note), "source_paths": [str(tex), str(style)]},
            "outputs": {
                "generated_artifacts": [str(tex), str(pdf)],
                "validation_commands": closeout_kwargs["validation_commands"],
                "closeout_run_id": surface["run_id"],
            },
            "environment": {"executor": "Codex app", "validation_target": "generated note artifact"},
            "evidence_status": "diagnostic",
            "code_state_ids": [code_state["record"]["code_state_id"]],
            "artifact_ids": artifact_ids,
            "scientific_run_id": surface["run_id"],
            "lane": "diagnostic",
        },
    )
    assert run["ok"] is True

    contract = aitp_v5_codex_record_apply(
        str(ws.base),
        session_id="codex-session",
        slot="validation_contract",
        payload={
            "required_checks": [
                "latex_compile_succeeds",
                "log_scan_has_no_fatal_error_undefined_reference_or_overfull_issue",
                "selected_pdf_pages_render_and_are_visually_spot_checked",
            ],
            "failure_modes": [
                "latex_compile_failure",
                "log_error_or_undefined_reference",
                "pdf_render_or_layout_regression",
            ],
            "required_evidence_outputs": ["document_build_and_layout_validation"],
            "tool_recipe_ids": [recipe["record"]["recipe_id"]],
            "executor_ids": ["codex-app"],
            "validator_role": "document_build_reviewer",
        },
    )
    assert contract["ok"] is True

    validation = aitp_v5_codex_record_apply(
        str(ws.base),
        session_id="codex-session",
        slot="validation_result",
        payload={
            "contract_id": contract["record"]["contract_id"],
            "tool_run_id": run["record"]["run_id"],
            "status": "passed",
            "checked_outputs": ["document_build_and_layout_validation"],
            "summary": (
                "PDF note validation passed for compile/log/render spot-checks only; "
                "no physics claim trust promotion."
            ),
            "artifact_ids": artifact_ids,
            "covered_failure_modes": [
                "latex_compile_failure",
                "log_error_or_undefined_reference",
                "pdf_render_or_layout_regression",
            ],
        },
    )
    assert validation["ok"] is True

    refreshed = aitp_v5_codex_closeout(
        str(ws.base),
        apply=False,
        run_id=surface["run_id"],
        **closeout_kwargs,
    )
    refreshed_missing = set(refreshed["record_completeness_audit"]["missing_recommended_slots"])
    assert not {"artifact", "tool_recipe", "tool_run", "code_state", "validation_result"} & refreshed_missing
    after_claim = get_claim(ws, claim.claim_id)
    assert after_claim.confidence_state == before_claim.confidence_state
    assert refreshed["can_update_claim_trust"] is False


def test_native_mcp_codex_surface_exposes_facade_not_full_kernel(tmp_path):
    script = Path(__file__).resolve().parents[1] / "brain" / "v5" / "native_mcp.py"
    env = {
        **os.environ,
        "AITP_MCP_SURFACE": "codex",
        "AITP_V5_MCP_LOG": str(tmp_path / "mcp.log"),
    }
    input_bytes = b""
    for message in [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    ]:
        body = json.dumps(message).encode("utf-8")
        input_bytes += f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8") + body

    process = subprocess.run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        input=input_bytes,
        capture_output=True,
        env=env,
        timeout=10,
    )
    assert process.returncode == 0, process.stderr.decode("utf-8", "replace")
    stdout = BytesIO(process.stdout)
    initialized = _read_content_length_message(stdout)
    tools = _read_content_length_message(stdout)["result"]["tools"]
    tool_names = {tool["name"] for tool in tools}

    assert initialized["result"]["serverInfo"]["version"] == "1.0.0"
    assert "aitp_v5_codex_autoroute" in tool_names
    assert "aitp_v5_codex_enter" in tool_names
    assert "aitp_v5_codex_expand" in tool_names
    assert "aitp_v5_codex_record_apply" in tool_names
    assert "aitp_v5_codex_literature_step" in tool_names
    assert "aitp_v5_preflight_trust_update" in tool_names
    assert "aitp_v5_apply_trust_update" not in tool_names
    assert "aitp_v5_register_source_asset" not in tool_names
    assert "aitp_v5_get_execution_brief" not in tool_names
    assert "aitp_v5_get_context_pack" not in tool_names
    assert len(tool_names) < 20


def test_native_mcp_unknown_surface_fails_closed_to_codex_allowlist(tmp_path):
    script = Path(__file__).resolve().parents[1] / "brain" / "v5" / "native_mcp.py"
    env = {
        **os.environ,
        "AITP_MCP_SURFACE": "codx",
        "AITP_V5_MCP_LOG": str(tmp_path / "mcp.log"),
    }
    message = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    body = json.dumps(message).encode("utf-8")
    process = subprocess.run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        input=f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8") + body,
        capture_output=True,
        env=env,
        timeout=10,
    )
    assert process.returncode == 0, process.stderr.decode("utf-8", "replace")
    tools = _read_content_length_message(BytesIO(process.stdout))["result"]["tools"]
    tool_names = {tool["name"] for tool in tools}

    assert "aitp_v5_codex_autoroute" in tool_names
    assert "aitp_v5_codex_enter" in tool_names
    assert "aitp_v5_codex_record_apply" in tool_names
    assert "aitp_v5_apply_trust_update" not in tool_names
    assert "aitp_v5_register_source_asset" not in tool_names
    assert len(tool_names) < 20


def _git(repo: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    )
    return process.stdout.strip()


def test_codex_plugin_skills_and_launcher_route_through_facade():
    repo = Path(__file__).resolve().parents[1]
    using = (repo / "plugins" / "aitp-research-protocol" / "skills" / "using-aitp" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    runtime = (repo / "plugins" / "aitp-research-protocol" / "skills" / "aitp-runtime" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    launcher = (repo / "plugins" / "aitp-research-protocol" / "scripts" / "launch_aitp_mcp.py").read_text(
        encoding="utf-8"
    )
    plugin_readme = (repo / "plugins" / "aitp-research-protocol" / "README.md").read_text(encoding="utf-8")

    assert 'os.environ.setdefault("AITP_MCP_SURFACE", "codex")' in launcher
    assert "full `aitp_v5_*` tool surface loads" not in using
    assert "aitp_v5_codex_tool_catalog" in using
    assert "aitp_v5_codex_autoroute" in using
    assert "aitp_v5_codex_enter" in using
    assert "AITP_MCP_SURFACE=full" in using
    assert "aitp_v5_codex_autoroute" in runtime
    assert "aitp_v5_codex_expand" in runtime
    assert "aitp_v5_codex_recording_step" in runtime
    assert "aitp_v5_codex_record_apply" in runtime
    assert "aitp_v5_codex_literature_step" in runtime
    assert "aitp_v5_codex_closeout" in runtime
    assert "A paper, web page, local note, or RAG chunk is not evidence" in runtime
    assert "AITP_MCP_SURFACE=codex" in plugin_readme
    assert "AITP_MCP_SURFACE=full" in plugin_readme
