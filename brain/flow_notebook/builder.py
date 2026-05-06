"""Flow notebook builder — template-based assembly with incremental rebuild."""
from __future__ import annotations

import re
from pathlib import Path

from brain.flow_notebook.hashing import _hash_files, _load_hash_state, _save_hash_state
from brain.flow_notebook.renderers import _SECTION_RENDERERS
from brain.flow_notebook.section_map import SECTION_ORDER, SECTION_SOURCES
from brain.flow_notebook.utils import _parse_md, _esc

_BEGIN_RE = re.compile(r"^%\s*---\s*BEGIN\s+(\w+)\s*---\s*$")
_END_RE   = re.compile(r"^%\s*---\s*END\s+(\w+)\s*---\s*$")


def _resolve_template(topic_root: Path, template_path: Path | None) -> Path:
    if template_path is not None:
        return template_path
    # builder.py is at brain/flow_notebook/builder.py → 3 levels up = repo root
    repo_root = Path(__file__).resolve().parent.parent.parent
    candidates = [
        repo_root / "templates" / "flow_notebook.tex",
        topic_root.parent.parent / "templates" / "flow_notebook.tex",
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]  # Best effort, will fail with clear error


def _fill_template_placeholders(template_text: str, topic_root: Path) -> str:
    state_path = topic_root / "state.md"
    fm, _ = _parse_md(state_path)
    title = fm.get("title", topic_root.name)
    lane = fm.get("lane", "unspecified")
    mode = fm.get("posture", fm.get("stage", "?"))
    return (template_text
            .replace("{{TOPIC_TITLE}}", _esc(str(title)))
            .replace("{{MODE}}", _esc(str(mode)))
            .replace("{{LANE}}", _esc(str(lane))))


def build_notebook(
    topic_root: Path,
    template_path: Path | None = None,
    changed_sections: list[str] | None = None,
    force_full: bool = False,
) -> tuple[str, list[str]]:
    """Build (or rebuild) the flow notebook.

    Always assembles from the clean template — never uses existing notebook
    as base (avoids corruption propagation).

    Args:
        topic_root: Path to the topic directory.
        template_path: Path to the LaTeX template. Auto-detected if None.
        changed_sections: Explicit sections to regenerate.
        force_full: If True, regenerate every section.

    Returns:
        (notebook_text, list_of_regenerated_sections)
    """
    template_path = _resolve_template(topic_root, template_path)
    template_text = template_path.read_text(encoding="utf-8")
    tlines = template_text.split("\n")

    # Find section marker boundaries
    first_begin = len(tlines)
    last_end = 0
    for i, line in enumerate(tlines):
        if _BEGIN_RE.match(line):
            first_begin = min(first_begin, i)
        if _END_RE.match(line):
            last_end = max(last_end, i)

    preamble_end = first_begin if first_begin < len(tlines) else 0
    postamble_start = last_end + 1 if last_end > 0 else len(tlines)

    preamble = "\n".join(tlines[:preamble_end])
    postamble = "\n".join(tlines[postamble_start:])
    preamble = _fill_template_placeholders(preamble, topic_root)

    # Determine which sections to regenerate
    old_hashes = _load_hash_state(topic_root)
    new_hashes: dict[str, str] = {}

    if force_full:
        to_regenerate = set(SECTION_ORDER)
    elif changed_sections is not None:
        to_regenerate = set(changed_sections)
    else:
        to_regenerate = set()
        for name in SECTION_ORDER:
            sources = SECTION_SOURCES.get(name, [])
            new_hash = _hash_files(topic_root, sources)
            new_hashes[name] = new_hash
            if name not in old_hashes or old_hashes[name] != new_hash:
                to_regenerate.add(name)

    if not to_regenerate:
        nb_path = topic_root / "flow_notebook.tex"
        if nb_path.exists():
            for name in SECTION_ORDER:
                if name not in new_hashes:
                    new_hashes[name] = _hash_files(topic_root, SECTION_SOURCES.get(name, []))
            _save_hash_state(topic_root, new_hashes)
            return nb_path.read_text(encoding="utf-8"), []

        to_regenerate = set(SECTION_ORDER)

    # Render sections and assemble
    rendered_sections: list[str] = []
    regenerated: list[str] = []

    for name in SECTION_ORDER:
        if name in to_regenerate:
            renderer = _SECTION_RENDERERS.get(name)
            if renderer:
                rendered_sections.append(renderer(topic_root))
            else:
                rendered_sections.append(
                    f"\\section{{{name.replace('_', ' ').title()}}}\n\n"
                    r"\textit{(Section not yet implemented.)}"
                )
            regenerated.append(name)
            new_hashes[name] = _hash_files(topic_root, SECTION_SOURCES.get(name, []))
        else:
            renderer = _SECTION_RENDERERS.get(name)
            if renderer:
                rendered_sections.append(renderer(topic_root))
            else:
                rendered_sections.append("")
            if name not in new_hashes:
                new_hashes[name] = _hash_files(topic_root, SECTION_SOURCES.get(name, []))

    body = "\n".join(rendered_sections)
    document = preamble + "\n" + body + "\n" + postamble

    _save_hash_state(topic_root, new_hashes)
    return document, regenerated


def render_all_sections(topic_root: Path) -> dict[str, str]:
    """Render every section and return {name: latex_content}."""
    result: dict[str, str] = {}
    for name in SECTION_ORDER:
        renderer = _SECTION_RENDERERS.get(name)
        if renderer:
            result[name] = renderer(topic_root)
    return result
