import ast
from pathlib import Path

import pytest


def test_m0_query_and_context_wrappers_live_in_focused_modules():
    from brain.v5 import mcp_context, mcp_query, mcp_tools

    query_names = (
        "aitp_v5_build_query_index",
        "aitp_v5_get_query_index_status",
        "aitp_v5_exact_expand_records",
    )
    context_names = (
        "aitp_v5_get_capability_registry",
        "aitp_v5_get_runtime_capability_audit",
        "aitp_v5_compile_research_context",
    )
    for name in query_names:
        assert getattr(mcp_tools, name) is getattr(mcp_query, name)
    for name in context_names:
        assert getattr(mcp_tools, name) is getattr(mcp_context, name)


def test_m0_query_and_context_cli_routes_parse():
    from brain.v5.cli import _build_parser

    parser = _build_parser()
    cases = (
        ["query", "index-build"],
        ["query", "index-status"],
        ["query", "exact", "--ref", "claim:c1"],
        ["context", "capability-audit"],
        ["context", "runtime-audit"],
        ["context", "compile", "session-1"],
    )

    for argv in cases:
        assert parser.parse_args(argv).command == argv[0]


def test_m0_cli_dispatches_query_and_context_without_private_shortcuts(tmp_path):
    from brain.v5.cli import _build_parser, _dispatch
    from brain.v5.workspace import bind_session, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "qg", context_id="theory", title="Quantum gravity")
    bind_session(ws, "session-qg", topic_id="qg", context_id="theory")
    parser = _build_parser()

    build = _dispatch(parser.parse_args(["--base", str(tmp_path), "query", "index-build"]))
    exact = _dispatch(
        parser.parse_args(
            ["--base", str(tmp_path), "query", "exact", "--ref", "topic:qg"]
        )
    )
    context = _dispatch(
        parser.parse_args(
            ["--base", str(tmp_path), "context", "compile", "session-qg"]
        )
    )

    assert build["kind"] == "query_index_build_report"
    assert exact["kind"] == "research_retrieval_result"
    assert context["kind"] == "research_context_bundle"


def test_m0_release_checks_all_python_modules_recursively():
    from tests.test_v5_architecture_boundaries import (
        INTENTIONAL_V5_AGGREGATOR_LIMITS,
        MAX_V5_SOURCE_MODULE_LINES,
    )

    repo_root = Path(__file__).resolve().parents[1]
    source_root = repo_root / "brain" / "v5"
    oversized = {}
    for path in source_root.rglob("*.py"):
        relative = path.relative_to(source_root)
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        limit = (
            INTENTIONAL_V5_AGGREGATOR_LIMITS.get(path.name, MAX_V5_SOURCE_MODULE_LINES)
            if len(relative.parts) == 1
            else MAX_V5_SOURCE_MODULE_LINES
        )
        if line_count > limit:
            oversized[relative.as_posix()] = line_count

    assert oversized == {}


def test_m0_compatibility_facades_reference_every_local_shard():
    repo_root = Path(__file__).resolve().parents[1]
    source_root = repo_root / "brain" / "v5"
    shard_root = source_root / "_compat_shards"
    referenced = set()

    for facade in source_root.glob("*.py"):
        tree = ast.parse(facade.read_text(encoding="utf-8"), filename=str(facade))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            if not node.value.startswith("_compat_shards/"):
                continue
            shard = source_root / node.value
            assert node.value.startswith(f"_compat_shards/{facade.stem}/")
            assert shard.is_file()
            referenced.add(shard.resolve())

    existing = {
        path.resolve()
        for path in shard_root.rglob("*.py")
        if path.name != "__init__.py"
    }
    assert len(referenced) >= 30
    assert referenced == existing


def test_m0_compatibility_loader_rejects_directory_traversal():
    from brain.v5.compat_module_loader import load_module_shards

    with pytest.raises(RuntimeError, match="invalid compatibility shard path"):
        load_module_shards({}, __file__, ("../outside.py",))
