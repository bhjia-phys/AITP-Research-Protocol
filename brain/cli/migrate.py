"""Protocol version migration: v0.6 → v1.0.

Idempotent — safe to run on already-migrated topics.
Updates state.md, creates missing directories, scaffolds missing files,
removes deprecated fields, fixes renamed activity names.
"""
from __future__ import annotations
from pathlib import Path
import os

DEFAULT_TOPICS_ROOT = os.environ.get(
    "AITP_TOPICS_ROOT",
    str(Path.cwd() / "research" / "aitp-topics"),
)

_POSTURE_MAP = {"L0": "discover", "L1": "read", "L3": "derive", "L4": "verify"}

_V10_DIRS = [
    "L0/sources", "L1/intake", "L2/graph/steps", "L2/graph/edges",
    "L3/candidates", "L3/ideate", "L4/reviews", "L4/reports",
    "L4/scripts", "L4/outputs", "compute", "runtime", "notebook/sections",
    "notebook/figures", "contracts",
]

_ACTIVITY_RENAMES = {
    "planning": "plan", "ideation": "ideate", "analysis": "derive",
    "synthesis": "integrate",
}

_DEPRECATED_KEYS = ["mode", "migrated_from"]


def migrate_topic(topic_root: Path) -> dict[str, str]:
    """Full v1.0 migration: state.md + directories + scaffold files + cleanup."""
    from brain.cli.state import _parse_md_local, _write_md_local

    state_path = topic_root / "state.md"
    if not state_path.exists():
        return {"error": "state.md not found"}

    fm, body = _parse_md_local(state_path)
    result = {}

    # ── Phase 1: Directories ──────────────────────────────────────────
    dirs_created = 0
    for d in _V10_DIRS:
        p = topic_root / d
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            dirs_created += 1
    if dirs_created:
        result["directories_created"] = str(dirs_created)

    # ── Phase 2: Scaffold files ───────────────────────────────────────
    now = _now_iso()
    scaffolds = {
        "research.md": f"# Research Trail\n\n- {now} [L0] Topic initialized\n",
        "MEMORY.md": "# Memory\n\n## Steering\n\n## Decisions\n\n## Dead Ends\n\n## Pitfalls\n",
        "compute/targets.yaml": (
            "targets:\n"
            "  local:\n"
            "    type: local\n"
            "    python: python\n"
            "    sympy: available\n"
        ),
        "runtime/log.md": f"# Topic Log\n\n## Events\n\n- {now} log initialized\n",
        "L0/source_registry.md": (
            "---\nkind: source_registry\ncoverage: initial\n---\n"
            "# Source Registry\n\n## Sources by Role\n\n## Coverage Assessment\n"
        ),
        "L1/source_toc_map.md": (
            "---\nsources_with_toc: ''\ntotal_sections: 0\ncoverage_status: incomplete\n---\n"
            "# Source TOC Map\n"
        ),
    }
    files_created = 0
    for fname, content in scaffolds.items():
        fp = topic_root / fname
        if not fp.exists():
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(content, encoding="utf-8")
            files_created += 1
    if files_created:
        result["scaffold_files_created"] = str(files_created)

    # ── Phase 3: State.md frontmatter ─────────────────────────────────
    state_changes = {}

    # Always set protocol_version
    fm["protocol_version"] = "v1.0"

    # Add missing v1.0 fields
    defaults = {
        "research_intensity": "standard",
        "memory_gate_enabled": False,
        "research_loop_active": False,
        "l4_cycle_count": 0,
    }
    for key, default in defaults.items():
        if key not in fm:
            fm[key] = default
            state_changes[key] = str(default)

    # Posture
    if "posture" not in fm:
        stage = fm.get("stage", "L0")
        fm["posture"] = _POSTURE_MAP.get(stage, "discover")
        state_changes["posture"] = fm["posture"]

    # l3_activity
    if "l3_activity" not in fm and fm.get("stage") == "L3":
        fm["l3_activity"] = "derive"
        state_changes["l3_activity"] = "derive"

    # ── Phase 4: Cleanup deprecated ───────────────────────────────────
    cleanup_done = []
    for key in _DEPRECATED_KEYS:
        if key in fm:
            del fm[key]
            cleanup_done.append(key)

    # Fix renamed activities
    for key in ("l3_activity", "l3_subplane"):
        old_val = fm.get(key, "")
        if old_val in _ACTIVITY_RENAMES:
            fm[key] = _ACTIVITY_RENAMES[old_val]
            cleanup_done.append(f"{key}:{old_val}→{fm[key]}")

    # Fix deprecated lane
    if fm.get("lane") == "toy_numeric":
        fm["lane"] = "code_method"
        cleanup_done.append("lane:toy_numeric→code_method")

    fm["updated_at"] = now

    if state_changes or cleanup_done:
        _write_md_local(state_path, fm, body)
        if state_changes:
            for k, v in state_changes.items():
                result[k] = v
        if cleanup_done:
            result["cleanup"] = ", ".join(cleanup_done)

    total = dirs_created + files_created + len(state_changes) + len(cleanup_done)
    if total == 0:
        result["status"] = "already v1.0 — nothing to migrate"
    else:
        result["status"] = f"migrated v0.6 → v1.0 ({total} changes)"
    return result


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def cmd_migrate(args):
    """Migrate a topic from v0.6 to v1.0 protocol (idempotent)."""
    base = Path(DEFAULT_TOPICS_ROOT)
    slug = args.topic
    for candidate in [base / slug, base / "topics" / slug]:
        if (candidate / "state.md").exists():
            result = migrate_topic(candidate)
            for k, v in result.items():
                print(f"  {k}: {v}")
            return 0 if "error" not in result else 1

    print(f"Topic '{slug}' not found")
    return 1
