"""Protocol v1.0 → v1.1 migration: L3 completion_status, retreat fields, connect cleanup.

Idempotent — safe to run on already-migrated topics.
"""
from __future__ import annotations
from pathlib import Path
import os
import shutil
import yaml
import sys

DEFAULT_TOPICS_ROOT = os.environ.get(
    "AITP_TOPICS_ROOT",
    str(Path.cwd() / "research" / "aitp-topics"),
)

# New retreat fields with defaults
_RETREAT_DEFAULTS = {
    "retreated_from": None,
    "retreated_to": None,
    "retreat_reason": None,
    "retreated_at": None,
    "retreat_count": 0,
}

# Old boolean retreat fields to remove
_DEPRECATED_RETREAT_KEYS = ["retreated_from_l3", "returned_from_l4"]

# L3 activities (post-connect-removal)
L3_ACTIVITIES = [
    "ideate", "plan", "derive", "trace-derivation",
    "gap-audit", "integrate", "distill",
]

L3_ARTIFACT_NAMES = {
    "ideate": "active_idea.md",
    "plan": "active_plan.md",
    "derive": "active_derivation.md",
    "trace-derivation": "active_trace.md",
    "gap-audit": "active_gaps.md",
    "integrate": "active_integration.md",
    "distill": "active_distillation.md",
}


def _parse_md(path: Path):
    if not path.exists():
        return {}, ""
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            try:
                fm = yaml.safe_load(parts[1]) or {}
            except Exception:
                fm = {}
            return fm, parts[2] if len(parts) > 2 else ""
    return {}, text


def _write_md(path: Path, fm: dict, body: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        yaml.dump(dict(fm), default_flow_style=False, allow_unicode=True).rstrip(),
        "---",
        str(body).lstrip("\n"),
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def migrate_topic(topic_path: Path, dry_run: bool = False) -> list[str]:
    """Migrate a single topic. Returns list of actions taken."""
    actions = []
    slug = topic_path.name
    state_path = topic_path / "state.md"

    if not state_path.exists():
        return actions

    # --- 1. Update state.md retreat fields ---
    fm, body = _parse_md(state_path)
    changed = False

    # Add missing retreat fields
    for key, default in _RETREAT_DEFAULTS.items():
        if key not in fm:
            fm[key] = default
            changed = True
            actions.append(f"  state.md: +{key} = {default}")

    # Preserve old retreat reason if present
    if "l4_return_reason" in fm and not fm.get("retreat_reason"):
        fm["retreat_reason"] = fm["l4_return_reason"]
        actions.append("  state.md: retreat_reason ← l4_return_reason")

    # Remove deprecated boolean retreat keys
    for key in _DEPRECATED_RETREAT_KEYS:
        if key in fm:
            old_val = fm.pop(key)
            actions.append(f"  state.md: -{key} (was {old_val})")
            changed = True

    # Migrate old retreaded_from_l3
    if fm.get("retreated_from_l3"):
        if not fm.get("retreated_from"):
            fm["retreated_from"] = "L3"
            fm["retreated_to"] = "L1"
            actions.append("  state.md: retreated_from/to ← retreated_from_l3=True")
        del fm["retreated_from_l3"]
        changed = True

    # Update protocol version
    if fm.get("protocol_version") == "v1.0":
        fm["protocol_version"] = "v1.1"
        changed = True
        actions.append("  state.md: protocol_version v1.0 → v1.1")

    if changed and not dry_run:
        _write_md(state_path, fm, body)

    # --- 2. Add completion_status to L3 artifacts ---
    for activity in L3_ACTIVITIES:
        artifact_name = L3_ARTIFACT_NAMES[activity]
        artifact_path = topic_path / "L3" / activity / artifact_name
        if not artifact_path.exists():
            continue
        afm, abody = _parse_md(artifact_path)
        if "completion_status" not in afm:
            # If artifact has real content (body > 200 chars), mark complete
            content_len = len(abody.strip())
            status = "complete" if content_len > 200 else "draft"
            afm["completion_status"] = status
            if not dry_run:
                _write_md(artifact_path, afm, abody)
            actions.append(f"  L3/{activity}/{artifact_name}: completion_status={status} ({content_len} chars)")

    # --- 3. Remove L3/connect/ directory ---
    connect_dir = topic_path / "L3" / "connect"
    if connect_dir.exists():
        if not dry_run:
            shutil.rmtree(connect_dir)
        actions.append("  L3/connect/: removed")

    return actions


def migrate_all(topics_root: str = "", dry_run: bool = False):
    root = Path(topics_root or DEFAULT_TOPICS_ROOT)
    if not root.exists():
        print(f"Topics root not found: {root}")
        return

    for topic_dir in sorted(root.iterdir()):
        if not topic_dir.is_dir():
            continue
        state_path = topic_dir / "state.md"
        if not state_path.exists():
            continue
        fm, _ = _parse_md(state_path)
        stage = fm.get("stage", "L0")
        if stage not in ("L3", "L4"):
            continue

        print(f"\n{topic_dir.name} (stage={stage}):")
        actions = migrate_topic(topic_dir, dry_run=dry_run)
        if actions:
            for a in actions:
                print(a)
        else:
            print("  (already up to date)")

    if dry_run:
        print("\n[Dry run — no changes made. Run without --dry-run to apply.]")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    migrate_all(dry_run=dry_run)
