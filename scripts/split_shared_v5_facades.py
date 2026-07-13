"""Prepare clean bounded facades for shared files with unstaged extensions."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from split_v5_compat_modules import split_module


FILES = ("brain/v5/mcp_tools.py", "brain/v5/public_surfaces.py")


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    temp = repo / "tmp" / "gate0-shared-clean-20260710"
    if temp.exists():
        raise RuntimeError(f"temporary split root already exists: {temp}")
    temp.mkdir(parents=True)
    overlap = _git(repo, "diff", "--", *FILES)
    (temp / "user-overlap.patch").write_text(overlap, encoding="utf-8")

    for relative in FILES:
        source = _git(repo, "show", f"HEAD:{relative}")
        if relative.endswith("mcp_tools.py"):
            source = source.replace(
                "from brain.v5.mcp_capabilities import (\n"
                "    aitp_v5_build_query_index,\n"
                "    aitp_v5_compile_research_context,\n"
                "    aitp_v5_exact_expand_records,\n"
                "    aitp_v5_get_capability_registry,\n"
                "    aitp_v5_get_query_index_status,\n"
                "    aitp_v5_get_runtime_capability_audit,\n"
                ")\n",
                "from brain.v5.mcp_context import (\n"
                "    aitp_v5_compile_research_context,\n"
                "    aitp_v5_get_capability_registry,\n"
                "    aitp_v5_get_runtime_capability_audit,\n"
                ")\n"
                "from brain.v5.mcp_query import (\n"
                "    aitp_v5_build_query_index,\n"
                "    aitp_v5_exact_expand_records,\n"
                "    aitp_v5_get_query_index_status,\n"
                ")\n",
            )
            if "from brain.v5.mcp_context import" not in source:
                raise RuntimeError("failed to apply focused MCP import migration")
        target = temp / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")
        split_module(temp, relative)

        real_target = repo / relative
        real_shards = real_target.parent / "_compat_shards" / real_target.stem
        if real_shards.exists():
            raise RuntimeError(f"real shard directory already exists: {real_shards}")
        shutil.copy2(target, real_target)
        shutil.copytree(
            target.parent / "_compat_shards" / target.stem,
            real_shards,
        )
    print(f"saved overlap patch to {temp / 'user-overlap.patch'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
