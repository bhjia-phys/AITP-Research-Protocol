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


def generate_l1_index(topic_root: Path) -> str:
    """Generate L1/INDEX.md — one-page L3 entry point.

    Reads state.md, source_registry, derivation_anchor_map, source_cross_map,
    convention_snapshot, and contradiction_register dynamically. No hardcoded
    topic-specific content.
    """
    state_fm, _ = _parse_md(topic_root / "state.md")
    title = state_fm.get("title", topic_root.name)

    lines: list[str] = []
    lines.append(f"# L1 Index — {title}")
    lines.append("")
    lines.append("> Auto-generated from L1 artifacts. Read this first before L3 derivation.")
    lines.append("")

    # ── §1 Research Question ──────────────────────────────────────────
    qc_path = topic_root / "L1" / "question_contract.md"
    if qc_path.exists():
        qfm, _ = _parse_md(qc_path)
        question = qfm.get("bounded_question", "(not set)")
        scope = qfm.get("scope_boundaries", "")
        hypotheses = qfm.get("competing_hypotheses", "")
        targets = qfm.get("target_quantities", "")
        lines.append("## 1. Research Question")
        lines.append("")
        lines.append(f"**{question}**")
        lines.append("")
        if scope:
            lines.append(f"**Scope**: {_esc(str(scope))[:400]}")
            lines.append("")
        if targets:
            lines.append(f"**Targets**: {_esc(str(targets))}")
            lines.append("")
        if hypotheses:
            lines.append(f"**Hypotheses**: {_esc(str(hypotheses))[:300]}")
            lines.append("")

    # ── §2 Source Summary ─────────────────────────────────────────────
    lines.append("## 2. Source Summary")
    lines.append("")
    lines.append("| Source | Type | Role | Intake Notes |")
    lines.append("|--------|------|------|-------------|")
    src_dir = topic_root / "L0" / "sources"
    intake_dir = topic_root / "L1" / "intake"
    if src_dir.is_dir():
        for d in sorted(src_dir.iterdir()):
            if not d.is_dir():
                continue
            sf = d / "source.md"
            if not sf.exists():
                continue
            fm, _ = _parse_md(sf)
            sid = fm.get("source_id", d.name)
            stype = fm.get("type", "?")
            srole = fm.get("role", "?")
            src_intake = intake_dir / sid
            intake_count = len(list(src_intake.glob("*.md"))) if src_intake.is_dir() else 0
            lines.append(f"| {sid} | {stype} | {srole} | {intake_count} |")
    lines.append("")

    # ── §3 Derivation Anchors ─────────────────────────────────────────
    dam_path = topic_root / "L1" / "derivation_anchor_map.md"
    if dam_path.exists():
        dfm, _ = _parse_md(dam_path)
        lines.append("## 3. Derivation Anchors")
        lines.append("")
        anchors_text = str(dfm.get("starting_anchors", ""))
        if anchors_text:
            lines.append("| Anchor | Source:File:Line | Description |")
            lines.append("|--------|-----------------|-------------|")
            for a_line in anchors_text.split("\n"):
                a_line = a_line.strip().rstrip(",")
                if not a_line or not a_line.startswith("A"):
                    continue
                # Format: A1: source:file:line — description
                parts = a_line.split(":", 1)
                aid = parts[0].strip()
                rest = parts[1].strip() if len(parts) > 1 else ""
                # Split on first em-dash or double-hyphen
                for sep in [" — ", " -- ", ": "]:
                    if sep in rest:
                        loc, desc = rest.split(sep, 1)
                        break
                else:
                    loc, desc = rest, ""
                lines.append(
                    f"| {aid} | {loc.strip()[:60]} | {desc.strip()[:80]} |"
                )
            lines.append("")
        else:
            lines.append("*No anchors registered yet.*")
            lines.append("")

    # ── §4 Key Equations ──────────────────────────────────────────────
    scm_path = topic_root / "L1" / "source_cross_map.md"
    if scm_path.exists():
        sfm, sbody = _parse_md(scm_path)
        lines.append("## 4. Key Equations (from source_cross_map.md)")
        lines.append("")
        # Extract equation lineage table if present
        if "| Equation | Origin | Appears In |" in sbody:
            in_table = False
            for bline in sbody.split("\n"):
                if "| Equation | Origin" in bline:
                    in_table = True
                    lines.append(bline)
                    continue
                if in_table and bline.startswith("|") and "---" not in bline:
                    lines.append(bline)
                elif in_table and not bline.startswith("|"):
                    in_table = False
                    break
            lines.append("")

    # ── §5 Notation ───────────────────────────────────────────────────
    cs_path = topic_root / "L1" / "convention_snapshot.md"
    if cs_path.exists():
        lines.append("## 5. Notation Quick Reference")
        lines.append("")
        lines.append("See `L1/convention_snapshot.md` for full mapping.")
        lines.append("Key tables are in: ## Notation Choices, ## Code notation")
        lines.append("")

    # ── §6 Contradictions ─────────────────────────────────────────────
    cr_path = topic_root / "L1" / "contradiction_register.md"
    if cr_path.exists():
        cfm, _ = _parse_md(cr_path)
        blocking = str(cfm.get("blocking_contradictions", ""))
        lines.append("## 6. Contradictions")
        lines.append("")
        lines.append(f"**Blocking?** {blocking[:200]}")
        lines.append("")
        lines.append("See `L1/contradiction_register.md` for details.")
        lines.append("")

    # ── §7 Reading Order ──────────────────────────────────────────────
    lines.append("## 7. Suggested Reading Order for L3")
    lines.append("")
    lines.append("1. **This INDEX** (you are here)")
    lines.append("2. `L1/derivation_anchor_map.md` — choose a starting anchor")
    lines.append("3. `L1/intake/<source>/<section>.md` — read relevant intake notes")
    lines.append("4. `L1/convention_snapshot.md` — check notation for unfamiliar symbols")
    lines.append("5. `L1/contradiction_register.md` — verify no blocking issues")
    lines.append("6. `L0/sources/<id>/original/` — go to original source if needed")
    lines.append("")

    return "\n".join(lines)
