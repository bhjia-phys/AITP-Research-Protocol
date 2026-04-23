"""AITP Stop hook — save progress summary at session end.

Only updates the active topic (via .current_topic marker or most-recent),
not every topic in the tree. Records session end in runtime/log.md and
updates state.md updated_at timestamp atomically.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path


def _parse_frontmatter(path: str) -> dict:
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm


def _parse_md(path: Path) -> tuple[dict, str]:
    if not path.exists():
        return {}, ""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not m:
        return {}, text
    import yaml
    fm = yaml.safe_load(m.group(1)) or {}
    return fm, m.group(2)


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _render_md(fm: dict, body: str) -> str:
    import yaml
    frontmatter = yaml.dump(fm, default_flow_style=False, allow_unicode=True).strip()
    return f"---\n{frontmatter}\n---\n{body}\n"


def _find_workspace_root() -> str:
    cwd = os.getcwd()
    for _ in range(8):
        if (os.path.isfile(os.path.join(cwd, ".aitp_config.json"))
                or os.path.isfile(os.path.join(cwd, "CLAUDE.md"))
                or os.path.isdir(os.path.join(cwd, ".git"))):
            return cwd
        parent = os.path.dirname(cwd)
        if parent == cwd:
            break
        cwd = parent
    return os.getcwd()


def _read_aitp_config(workspace: str) -> dict:
    config_path = os.path.join(workspace, ".aitp_config.json")
    if not os.path.isfile(config_path):
        return {}
    try:
        with open(config_path, encoding="utf-8") as f:
            return json.loads(f.read())
    except (json.JSONDecodeError, OSError):
        return {}


def _find_topics_root() -> str | None:
    env = os.environ.get("AITP_TOPICS_ROOT")
    if env:
        return env
    workspace = _find_workspace_root()
    config = _read_aitp_config(workspace)
    cfg_root = config.get("topics_root")
    if cfg_root:
        if os.path.isabs(cfg_root):
            return cfg_root
        return os.path.normpath(os.path.join(workspace, cfg_root))
    cwd = os.getcwd()
    for _ in range(5):
        candidate = os.path.join(cwd, "topics")
        if os.path.isdir(candidate):
            return os.path.dirname(candidate)
        parent = os.path.dirname(cwd)
        if parent == cwd:
            break
        cwd = parent
    return None


def _find_active_topic(topics_root: str) -> str | None:
    from brain.state_model import topics_dir
    td = topics_dir(topics_root)

    marker = Path(td) / ".current_topic"
    if marker.exists():
        slug = marker.read_text(encoding="utf-8").strip()
        if slug and (Path(td) / slug / "state.md").exists():
            return slug

    best_slug = None
    best_time = ""
    if not os.path.isdir(td):
        return None
    for entry in os.listdir(td):
        state_path = os.path.join(td, entry, "state.md")
        if os.path.isfile(state_path):
            fm = _parse_frontmatter(state_path)
            updated = fm.get("updated_at", "")
            if updated > best_time:
                best_time = updated
                best_slug = entry
    return best_slug


def stop_for_topic(topics_root: str) -> None:
    from brain.state_model import topics_dir
    td = topics_dir(topics_root)
    slug = _find_active_topic(topics_root)
    if not slug:
        return

    now = datetime.now().astimezone().isoformat(timespec="seconds")
    root = Path(td) / slug

    # Update state.md updated_at atomically
    state_path = root / "state.md"
    if state_path.exists():
        fm, body = _parse_md(state_path)
        fm["updated_at"] = now
        fm["last_session_ended"] = now
        _atomic_write_text(state_path, _render_md(fm, body))

    # Append session-end event to runtime log
    log_path = root / "runtime" / "log.md"
    log_text = log_path.read_text(encoding="utf-8") if log_path.exists() else "# Topic Log\n\n## Events\n"
    if not log_text.endswith("\n"):
        log_text += "\n"
    _atomic_write_text(log_path, log_text + f"- {now} session ended\n")


def _hooks_disabled(workspace: str) -> bool:
    """Check if hooks are explicitly disabled via env var or config."""
    if os.environ.get("AITP_HOOKS", "").lower() in ("off", "0", "false", "no"):
        return True
    config = _read_aitp_config(workspace)
    return not config.get("hooks_enabled", True)


def main():
    workspace = _find_workspace_root()
    if _hooks_disabled(workspace):
        return
    topics_root = _find_topics_root()
    if not topics_root:
        return
    stop_for_topic(topics_root)


if __name__ == "__main__":
    main()
