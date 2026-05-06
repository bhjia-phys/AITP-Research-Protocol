"""Flow notebook builder — section-based, template-driven, incremental.

Architecture:
  Template (templates/flow_notebook.tex) defines the canonical section
  structure with ``% --- BEGIN <name> ---`` / ``% --- END <name> ---``
  markers.  Each section maps to specific L0–L4 artifacts.

  Python extracts structured data and renders clean LaTeX sections.
  AI (guided by the AITP skill) then polishes for narrative flow and
  human readability — the Python output is correct, not necessarily
  beautiful.

  Incremental: section source hashes are stored in
  ``runtime/.notebook_section_hashes.json``.  Only sections whose
  source artifacts changed are regenerated.

  Output: ``<topic_root>/flow_notebook.tex``
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

# ── Template marker regex ────────────────────────────────────────────────
_BEGIN_RE = re.compile(r"^%\s*---\s*BEGIN\s+(\w+)\s*---\s*$")
_END_RE   = re.compile(r"^%\s*---\s*END\s+(\w+)\s*---\s*$")

# ── Section → source artifact globs ──────────────────────────────────────
SECTION_SOURCES: dict[str, list[str]] = {
    "research_question":    ["L1/question_contract.md"],
    "source_landscape":     ["L0/source_registry.md", "L0/sources/*.md",
                             "L1/source_basis.md", "L1/source_cross_map.md"],
    "conventions":          ["L1/convention_snapshot.md"],
    "session_history":      ["state.md", "runtime/sessions.md"],
    "derivation":           ["L3/ideate/active_idea.md", "L3/plan/active_plan.md",
                             "L3/derive/active_derivation.md",
                             "L3/trace-derivation/active_trace.md",
                             "L3/gap-audit/active_gaps.md",
                             "L3/integrate/active_integration.md",
                             "L3/ideas/*.md"],
    "synthesis":            ["L3/distill/active_distillation.md",
                             "L3/candidates/*.md"],
    "validation":           ["L4/reviews/*.md", "L4/outputs/*.md",
                             "L4/validation_contract.md", "state.md"],
    "l2_knowledge":         [],   # global L2 — checked via parent dir
    "domain_context":       ["contracts/domain-manifest.md"],
    "open_questions":       ["L3/deferred.md", "L3/ideas/*.md",
                             "L1/contradiction_register.md"],
    "execution_provenance": ["runtime/log.md"],
}

SECTION_ORDER: list[str] = [
    "research_question", "source_landscape", "conventions",
    "session_history", "derivation", "synthesis", "validation",
    "l2_knowledge", "domain_context", "open_questions",
    "execution_provenance",
]


# ── Markdown / YAML parsing ──────────────────────────────────────────────

_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


def _parse_md(path: Path) -> tuple[dict[str, Any], str]:
    if not path.exists():
        return {}, ""
    text = path.read_text(encoding="utf-8")
    m = _FM_RE.match(text)
    if not m:
        return {}, text
    import yaml
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, m.group(2)


# ── LaTeX escaping ───────────────────────────────────────────────────────

def _esc(text: str) -> str:
    """Escape plain text for LaTeX and convert Unicode math chars.

    Escapes TeX special chars first, then converts Unicode math chars
    to $...$ wrappers (after escaping, so $ are not double-escaped).
    """
    if not text:
        return text
    # Step 1: escape TeX special chars (on raw text, before $ are added)
    # We skip $ itself — sanitize_unicode will add proper $...$ wrappers later
    text = _esc_tex_special(text)
    # Step 2: convert Unicode to LaTeX math (adds $...$)
    text = _sanitize_unicode(text)
    return text


def _esc_tex_special(text: str) -> str:
    """Escape TeX special characters (except $, which sanitize_unicode adds)."""
    if not text:
        return text
    result: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == '\\':
            if i + 1 < len(text) and text[i + 1].isalpha():
                result.append(ch)
            else:
                result.append(r"\textbackslash{}")
        elif ch == '&':
            result.append(r"\&")
        elif ch == '%':
            result.append(r"\%")
        elif ch == '$':
            # Do NOT escape $ — _sanitize_unicode adds proper $...$ wrappers
            result.append(ch)
        elif ch == '#':
            result.append(r"\#")
        elif ch == '_':
            result.append(r"\_")
        elif ch == '^':
            result.append(r"\^{}")
        elif ch == '~':
            result.append(r"\textasciitilde{}")
        elif ch == '{':
            result.append(r"\{")
        elif ch == '}':
            result.append(r"\}")
        elif ch == '<':
            result.append(r"\textless{}")
        elif ch == '>':
            result.append(r"\textgreater{}")
        elif ch == '\n':
            result.append(ch)
        else:
            result.append(ch)
        i += 1
    return "".join(result)


# ── Unicode to LaTeX converter ───────────────────────────────────────────

# Map of Unicode math/special chars to LaTeX commands
# Two versions: with $ wrapper (for outside math mode) and without (for inside)
_UNICODE_TO_LATEX_OUTSIDE: dict[str, str] = {}
_UNICODE_TO_LATEX_INSIDE: dict[str, str] = {}

for _k, _v in [
    # Greek lowercase
    ("α", "\\alpha"), ("β", "\\beta"), ("γ", "\\gamma"),
    ("δ", "\\delta"), ("ε", "\\varepsilon"), ("ζ", "\\zeta"),
    ("η", "\\eta"), ("θ", "\\theta"), ("ι", "\\iota"),
    ("κ", "\\kappa"), ("λ", "\\lambda"), ("μ", "\\mu"),
    ("ν", "\\nu"), ("ξ", "\\xi"), ("π", "\\pi"),
    ("ρ", "\\rho"), ("σ", "\\sigma"), ("τ", "\\tau"),
    ("υ", "\\upsilon"), ("φ", "\\phi"), ("χ", "\\chi"),
    ("ψ", "\\psi"), ("ω", "\\omega"),
    # Greek uppercase
    ("Γ", "\\Gamma"), ("Δ", "\\Delta"), ("Θ", "\\Theta"),
    ("Λ", "\\Lambda"), ("Ξ", "\\Xi"), ("Π", "\\Pi"),
    ("Σ", "\\Sigma"), ("Φ", "\\Phi"), ("Ψ", "\\Psi"),
    ("Ω", "\\Omega"),
    # Math operators and symbols
    ("∂", "\\partial"), ("∇", "\\nabla"), ("∫", "\\int"),
    ("∑", "\\sum"), ("∏", "\\prod"),
    ("∞", "\\infty"), ("≈", "\\approx"), ("≡", "\\equiv"),
    ("≠", "\\neq"), ("≤", "\\leq"), ("≥", "\\geq"),
    ("±", "\\pm"), ("×", "\\times"), ("·", "\\cdot"),
    ("→", "\\to"), ("←", "\\leftarrow"), ("↔", "\\leftrightarrow"),
    ("⇒", "\\Rightarrow"), ("⇐", "\\Leftarrow"),
    ("∈", "\\in"), ("∉", "\\notin"), ("⊂", "\\subset"),
    ("⊃", "\\supset"), ("∪", "\\cup"), ("∩", "\\cap"),
    ("∧", "\\land"), ("∨", "\\lor"), ("∀", "\\forall"),
    ("∃", "\\exists"), ("∄", "\\nexists"),
    ("⟨", "\\langle"), ("⟩", "\\rangle"),
    ("ħ", "\\hbar"), ("ℏ", "\\hbar"),
    # Subscripts
    ("₀", "_0"), ("₁", "_1"), ("₂", "_2"),
    ("₃", "_3"), ("₄", "_4"), ("₅", "_5"),
    # Superscripts
    ("⁰", "^0"), ("¹", "^1"), ("²", "^2"),
    ("³", "^3"), ("⁴", "^4"), ("⁵", "^5"),
    ("⁻", "^-"), ("⁺", "^+"),
    ("ᵀ", "^T"),
    # Special
    ("−", "-"),  # Unicode minus → ASCII minus
    ("†", "\\dagger"), ("…", "\\dots"),
    ("√", "\\sqrt{}"),
    # Combining chars (accent-like)
    ("̂", "^"),  # combining circumflex
]:
    _UNICODE_TO_LATEX_OUTSIDE[_k] = "$" + _v + "$"
    _UNICODE_TO_LATEX_INSIDE[_k] = _v


def _sanitize_unicode(text: str) -> str:
    """Replace Unicode math/special chars with LaTeX commands.

    Handles chars both inside and outside $...$ math spans.
    Unmapped non-ASCII chars (emoji, etc.) are stripped.
    """
    result: list[str] = []
    in_math = False
    for ch in text:
        if ch == '$':
            in_math = not in_math
            result.append(ch)
        elif in_math and ch in _UNICODE_TO_LATEX_INSIDE:
            result.append(_UNICODE_TO_LATEX_INSIDE[ch])
        elif not in_math and ch in _UNICODE_TO_LATEX_OUTSIDE:
            result.append(_UNICODE_TO_LATEX_OUTSIDE[ch])
        elif ord(ch) < 128:
            # ASCII — pass through
            result.append(ch)
        elif ord(ch) in (0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D):
            # Smart quotes and dashes — keep (handled by inputenc)
            result.append(ch)
        else:
            # Non-ASCII, unmapped (emoji, CJK, etc.) — strip silently
            pass
    return "".join(result)


# ── Markdown body to LaTeX (pandoc fallback) ─────────────────────────────

def _md_body_to_latex(body_text: str, max_chars: int = 6000) -> str:
    """Render Markdown body as verbatim LaTeX.

    Uses verbatim to guarantee correct compilation.  AI polishes
    the verbatim blocks into proper LaTeX tables/lists/equations
    as part of the notebook readability step.

    Truncates input to max_chars to prevent notebook bloat.
    """
    if not body_text.strip():
        return ""
    # Sanitize Unicode
    cleaned = _sanitize_unicode(body_text)
    # Truncate
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars] + "\n\n*(Content truncated — see source artifact for full text.)*"
    # Use verbatim for reliable compilation
    return (
        r"\begin{verbatim}" + "\n"
        + cleaned + "\n"
        + r"\end{verbatim}"
    )


# ── Section hash tracking ────────────────────────────────────────────────

def _hash_files(topic_root: Path, patterns: list[str]) -> str:
    """Combined SHA256 of all files matching the given patterns."""
    h = hashlib.sha256()
    for pat in patterns:
        if "*" in pat:
            for f in sorted(topic_root.glob(pat)):
                h.update(f.read_bytes())
        else:
            f = topic_root / pat
            if f.exists():
                h.update(f.read_bytes())
    return h.hexdigest()


def _hash_state_path(topic_root: Path) -> Path:
    return topic_root / "runtime" / ".notebook_section_hashes.json"


def _load_hash_state(topic_root: Path) -> dict[str, str]:
    p = _hash_state_path(topic_root)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_hash_state(topic_root: Path, hashes: dict[str, str]) -> None:
    p = _hash_state_path(topic_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(hashes, indent=2), encoding="utf-8")


# ── parse template into sections ─────────────────────────────────────────

def _parse_template(template_text: str) -> dict[str, tuple[int, int, int, int]]:
    """Return {section_name: (begin_line, begin_end, end_line, end_end)}
    where begin_line/end_line are 0-based line indices into template lines,
    and begin_end/end_end are character positions of the marker lines.

    Content between markers is at lines[begin_line+1 : end_line].
    """
    lines = template_text.split("\n")
    markers: dict[str, tuple[int, int, int, int]] = {}
    open_markers: dict[str, tuple[int, int]] = {}

    for i, line in enumerate(lines):
        m_begin = _BEGIN_RE.match(line)
        m_end   = _END_RE.match(line)
        if m_begin:
            name = m_begin.group(1)
            open_markers[name] = (i, len(line) + 1)
        elif m_end:
            name = m_end.group(1)
            if name in open_markers:
                begin_lineno, begin_endpos = open_markers.pop(name)
                markers[name] = (begin_lineno, begin_endpos, i, 0)
    return markers


# ── Section renderers ────────────────────────────────────────────────────

def _render_research_question(topic_root: Path) -> str:
    qc_path = topic_root / "L1" / "question_contract.md"
    if not qc_path.exists():
        return (
            r"\textit{(No question\_contract.md — complete L1 framing first.)}"
        )
    fm, body = _parse_md(qc_path)
    question = fm.get("bounded_question", "") or fm.get("bounded_question", "")
    scope = fm.get("scope_boundaries", "")
    targets = fm.get("target_quantities", "")
    competing = fm.get("competing_hypotheses", "")
    non_success = ""

    # Extract non-success conditions from body
    body_parts = body.split("## Non-Success Conditions")
    if len(body_parts) > 1:
        non_success = body_parts[1].split("##")[0].strip()

    lines: list[str] = []
    lines.append(r"\section{Research Question}")
    lines.append("")
    lines.append(r"\begin{resultbox}[Bounded Question]")
    lines.append(_esc(question) if question else r"\textit{(No bounded question recorded.)}")
    lines.append(r"\end{resultbox}")
    lines.append("")
    if scope or targets:
        lines.append(r"\noindent\textbf{Scope:} " + _esc(scope))
        lines.append(r"\quad\textbf{Target quantities:} " + _esc(targets))
        lines.append("")
    if non_success:
        lines.append(r"\begin{warningbox}[Non-Success Conditions]")
        lines.append(_md_body_to_latex(non_success))
        lines.append(r"\end{warningbox}")
    return "\n".join(lines)


def _render_source_landscape(topic_root: Path) -> str:
    src_dir = topic_root / "L0" / "sources"
    sources: list[dict] = []
    seen: set[str] = set()
    if src_dir.is_dir():
        # New directory structure: L0/sources/<slug>/source.md
        for d in sorted(src_dir.iterdir()):
            if d.is_dir():
                sf = d / "source.md"
                if sf.exists():
                    fm, _ = _parse_md(sf)
                    sid = fm.get("source_id", d.name)
                    seen.add(sid)
                    sources.append({
                        "id": sid,
                        "title": fm.get("title", d.name),
                        "source_type": fm.get("type", ""),
                        "fidelity": fm.get("fidelity", ""),
                        "role": fm.get("role", ""),
                        "original_files": fm.get("original_files", []),
                    })
        # Legacy flat .md files (for topics not yet migrated)
        for sp in sorted(src_dir.glob("*.md")):
            fm, _ = _parse_md(sp)
            sid = fm.get("source_id", sp.stem)
            if sid not in seen:
                seen.add(sid)
                sources.append({
                    "id": sid,
                    "title": fm.get("title", sp.stem),
                    "source_type": fm.get("type", ""),
                    "fidelity": fm.get("fidelity", ""),
                    "role": fm.get("role", ""),
                    "original_files": [],
                })

    lines: list[str] = []
    lines.append(r"\section{Source Landscape}")
    lines.append("")
    if not sources:
        lines.append(r"\textit{(No sources registered.)}")
        return "\n".join(lines)

    lines.append(r"\begin{longtable}{>{\raggedright}p{3cm} p{5cm} p{1.5cm} p{2.5cm}}")
    lines.append(r"\toprule")
    lines.append(r"\textbf{Source} & \textbf{Title} & \textbf{Type} & \textbf{Role/Fidelity} \\")
    lines.append(r"\midrule")
    lines.append(r"\endhead")
    for s in sources[:50]:
        sid = _esc(s["id"][:40])
        title = _esc((s["title"] or s["id"])[:80])
        stype = _esc(s.get("source_type", "")[:20])
        role_fid = _esc((s.get("role", "") + "/" + s.get("fidelity", ""))[:25])
        lines.append(f"{sid} & {title} & {stype} & {role_fid} \\\\")
    lines.append(r"\bottomrule")
    lines.append(r"\end{longtable}")
    return "\n".join(lines)


def _render_conventions(topic_root: Path) -> str:
    cs_path = topic_root / "L1" / "convention_snapshot.md"
    if not cs_path.exists():
        return (
            r"\section{Conventions \& Notation}" "\n\n"
            r"\textit{(No convention snapshot — complete L1/convention\_snapshot.md.)}"
        )
    fm, body = _parse_md(cs_path)

    lines: list[str] = []
    lines.append(r"\section{Conventions \& Notation}")
    lines.append("")

    notation = fm.get("notation_choices", "")
    units = fm.get("unit_conventions", "")

    if notation:
        lines.append(r"\subsection*{Notation}")
        lines.append(_esc(notation))
        lines.append("")
    if units:
        lines.append(r"\noindent\textbf{Units:} " + _esc(units))
        lines.append("")

    # Render body content (tables, sign conventions, etc.) via pandoc
    if body.strip():
        lines.append(_md_body_to_latex(body))
    return "\n".join(lines)


def _render_session_history(topic_root: Path) -> str:
    state_path = topic_root / "state.md"
    if not state_path.exists():
        return (
            r"\section{Mode \& Session History}" "\n\n"
            r"\textit{(No state.md — topic not bootstrapped.)}"
        )
    fm, _ = _parse_md(state_path)

    slug = str(fm.get("topic_slug", topic_root.name))
    stage = str(fm.get("stage", "?"))
    posture = str(fm.get("posture", "?"))
    lane = str(fm.get("lane", "?"))
    l3_activity = str(fm.get("l3_activity", fm.get("l3_subplane", "")))
    status = str(fm.get("status", "?"))
    gate = str(fm.get("gate_status", "?"))
    created = str(fm.get("created_at", "?"))
    updated = str(fm.get("updated_at", "?"))

    lines: list[str] = []
    lines.append(r"\section{Mode \& Session History}")
    lines.append("")
    lines.append(r"\begin{tabular}{ll}")
    lines.append(r"\toprule")
    lines.append(r"\textbf{Field} & \textbf{Value} \\")
    lines.append(r"\midrule")
    for label, val in [
        ("Topic slug", _esc(slug)),
        ("Stage", _esc(stage)),
        ("Posture", _esc(posture)),
        ("Lane", _esc(lane)),
        ("L3 activity", _esc(l3_activity)),
        ("Status", _esc(status)),
        ("Gate", _esc(gate)),
        ("Created", _esc(created)),
        ("Updated", _esc(updated)),
    ]:
        lines.append(f"{label} & \\texttt{{{val}}} \\\\")
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    return "\n".join(lines)


def _render_derivation(topic_root: Path) -> str:
    """Collect L3 subplane artifacts.  Each active_*.md → subsection."""
    from brain.state_model import L3_ACTIVITIES, L3_ACTIVITY_ARTIFACT_NAMES

    lines: list[str] = []
    lines.append(r"\section{Derivation Journey}")
    lines.append("")

    # Ideas first
    ideas_dir = topic_root / "L3" / "ideas"
    idea_files: list[Path] = []
    if ideas_dir.is_dir():
        idea_files = sorted(
            [p for p in ideas_dir.glob("*.md") if not p.stem.startswith("_")],
            key=lambda p: p.stat().st_mtime, reverse=True,
        )

    if idea_files:
        lines.append(r"\subsection{Ideas Explored}")
        for ip in idea_files:
            fm, body = _parse_md(ip)
            title = fm.get("title", ip.stem)
            status = fm.get("status", "active")
            approach = fm.get("approach", "")

            status_cmd = {
                "active": r"\statusactive",
                "failed": r"\statusfail",
                "succeeded": r"\statuspass",
                "abandoned": r"\statusdeferred",
                "superseded": r"\statusdeferred",
            }.get(status, r"\statusactive")

            lines.append(
                r"\begin{resultbox}[" + _esc(title) + r" \quad " + status_cmd + "]"
            )
            if approach:
                lines.append(_esc(approach[:800]))
            lines.append(r"\end{resultbox}")
            lines.append("")

    # Subplane artifacts
    has_any = False
    for sp in L3_ACTIVITIES:
        art_name = L3_ACTIVITY_ARTIFACT_NAMES.get(sp, f"active_{sp}.md")
        art_path = topic_root / "L3" / sp / art_name
        if not art_path.exists():
            continue
        has_any = True
        fm, body = _parse_md(art_path)
        label = sp.replace("-", " ").replace("_", " ").title()

        lines.append(r"\subsection*{" + label + "}")
        if body.strip():
            lines.append(_md_body_to_latex(body))
        else:
            lines.append(r"\textit{(No content recorded.)}")
        lines.append("")

    if not has_any and not idea_files:
        lines.append(r"\textit{(No derivation content yet — advance to L3.)}")
    return "\n".join(lines)


def _render_synthesis(topic_root: Path) -> str:
    lines: list[str] = []
    lines.append(r"\section{Synthesis \& Claims}")
    lines.append("")

    # Distillation
    dist_path = topic_root / "L3" / "distill" / "active_distillation.md"
    if dist_path.exists():
        fm, body = _parse_md(dist_path)
        claim = fm.get("distilled_claim", "")
        evidence = fm.get("evidence_summary", "")
        confidence = fm.get("confidence", "")

        lines.append(r"\begin{resultbox}[Distilled Claim]")
        lines.append(_esc(claim) if claim else r"\textit{(No distilled claim.)}")
        lines.append(r"\end{resultbox}")
        if evidence:
            lines.append(r"\noindent\textbf{Evidence:} " + _esc(evidence))
        if confidence:
            lines.append(r"\noindent\textbf{Confidence:} " + _esc(confidence))
        lines.append("")

    # Candidates
    cand_dir = topic_root / "L3" / "candidates"
    if cand_dir.is_dir():
        for cp in sorted(cand_dir.glob("*.md")):
            fm, _ = _parse_md(cp)
            ctitle = fm.get("title", cp.stem)
            claim = fm.get("claim", "")
            status = fm.get("status", "submitted")
            evidence = fm.get("evidence", "")

            lines.append(r"\begin{resultbox}[" + _esc(ctitle) + "]")
            if claim:
                lines.append(r"\textbf{Claim:} " + _esc(claim[:1200]))
            lines.append(r"\textit{Status:} " + _esc(status))
            if evidence:
                lines.append("")
                lines.append(r"\textbf{Evidence:} " + _esc(evidence[:800]))
            lines.append(r"\end{resultbox}")
            lines.append("")

    if not dist_path.exists() and not (cand_dir and list(cand_dir.glob("*.md"))):
        lines.append(r"\textit{(No candidates submitted yet.)}")
    return "\n".join(lines)


def _render_validation(topic_root: Path) -> str:
    lines: list[str] = []
    lines.append(r"\section{Validation}")
    lines.append("")

    # Reviews
    review_dir = topic_root / "L4" / "reviews"
    has_any = False
    if review_dir.is_dir():
        for rp in sorted(review_dir.glob("*.md")):
            has_any = True
            fm, body = _parse_md(rp)
            outcome = fm.get("outcome", "unknown")
            notes = fm.get("notes", "")

            badge = r"\statuspass" if outcome == "pass" else (
                r"\statusfail" if outcome in ("fail", "contradiction") else r"\statusactive"
            )
            lines.append(r"\begin{warningbox}[" + _esc(rp.stem) + r" \quad " + badge + "]")
            if notes:
                lines.append(_esc(notes[:1000]))
            if body.strip():
                lines.append("")
                lines.append(_md_body_to_latex(body[:2000]))
            lines.append(r"\end{warningbox}")
            lines.append("")

    # Numerical results
    outputs_dir = topic_root / "L4" / "outputs"
    if outputs_dir.is_dir():
        for op in sorted(outputs_dir.glob("*.md")):
            fm, _ = _parse_md(op)
            if fm.get("artifact_kind") != "numerical_result":
                continue
            has_any = True
            observable = fm.get("observable", op.stem)
            value = fm.get("computed_value", "")
            uncertainty = fm.get("uncertainty", "")
            units = fm.get("units", "")
            lit_val = fm.get("literature_value", "")
            agreement = fm.get("agreement_status", "")

            lines.append(r"\begin{valbox}[" + _esc(observable) + "]")
            lines.append(f"Computed: {_esc(str(value))} $\\pm$ {_esc(str(uncertainty))} {_esc(str(units))}")
            if lit_val:
                lines.append(f"\\quad Literature: {_esc(str(lit_val))} {_esc(str(units))}")
            if agreement:
                lines.append(f"\\quad Agreement: {_esc(agreement)}")
            lines.append(r"\end{valbox}")
            lines.append("")

    if not has_any:
        lines.append(r"\textit{(No validation reviews or numerical results yet.)}")
    return "\n".join(lines)


def _render_l2_knowledge(topic_root: Path) -> str:
    """Read global L2 nodes if accessible via parent topics root."""
    lines: list[str] = []
    lines.append(r"\section{Canonical Knowledge (L2)}")
    lines.append("")

    # Try to locate global L2 relative to topic root
    # topics_root is parent of topic directory
    global_l2 = topic_root.parent / "L2" / "graph" / "nodes"
    if not global_l2.is_dir():
        global_l2 = topic_root.parent.parent / "L2" / "graph" / "nodes"

    nodes: list[dict] = []
    if global_l2.is_dir():
        for np in sorted(global_l2.glob("*.md"))[:30]:
            fm, _ = _parse_md(np)
            nodes.append({
                "id": np.stem,
                "title": fm.get("title", np.stem),
                "node_type": fm.get("node_type", ""),
            })

    if nodes:
        lines.append(r"\begin{longtable}{>{\raggedright}p{3cm} p{2cm} p{6cm}}")
        lines.append(r"\toprule")
        lines.append(r"\textbf{Node} & \textbf{Type} & \textbf{Title} \\")
        lines.append(r"\midrule")
        lines.append(r"\endhead")
        for n in nodes:
            lines.append(f"{_esc(n['id'][:40])} & {_esc(n['node_type'][:20])} & {_esc(n['title'][:90])} \\\\")
        lines.append(r"\bottomrule")
        lines.append(r"\end{longtable}")
    else:
        lines.append(r"\textit{(No L2 nodes promoted from this topic yet.)}")
    return "\n".join(lines)


def _render_domain_context(topic_root: Path) -> str:
    dm_path = topic_root / "contracts" / "domain-manifest.md"
    if not dm_path.exists():
        return (
            r"\section{Domain Context}" "\n\n"
            r"\textit{(No domain manifest — create contracts/domain-manifest.md.)}"
        )
    fm, body = _parse_md(dm_path)
    domain_id = fm.get("domain_id", "")

    lines: list[str] = []
    lines.append(r"\section{Domain Context}")
    lines.append("")
    if domain_id:
        lines.append(r"\noindent\textbf{Domain:} \texttt{" + _esc(domain_id) + r"} \\")
    if body.strip():
        lines.append(_md_body_to_latex(body[:2000]))
    return "\n".join(lines)


def _render_open_questions(topic_root: Path) -> str:
    lines: list[str] = []
    lines.append(r"\section{Negative Results \& Open Questions}")
    lines.append("")

    # Deferred items
    deferred_path = topic_root / "L3" / "deferred.md"
    has_content = False
    if deferred_path.exists():
        _, body = _parse_md(deferred_path)
        if body.strip():
            has_content = True
            lines.append(r"\subsection*{Deferred Items}")
            lines.append(_md_body_to_latex(body[:3000]))

    # Failed ideas
    ideas_dir = topic_root / "L3" / "ideas"
    failed_ideas: list[dict] = []
    if ideas_dir.is_dir():
        for ip in sorted(ideas_dir.glob("*.md")):
            if ip.stem.startswith("_"):
                continue
            fm, _ = _parse_md(ip)
            if fm.get("status") in ("failed", "abandoned"):
                failed_ideas.append({
                    "title": fm.get("title", ip.stem),
                    "lessons": fm.get("lessons_learned", ""),
                })

    if failed_ideas:
        has_content = True
        lines.append(r"\subsection*{Failed Approaches}")
        for fi in failed_ideas:
            lines.append(r"\begin{warningbox}[" + _esc(fi["title"]) + "]")
            if fi["lessons"]:
                lines.append(_esc(fi["lessons"][:800]))
            lines.append(r"\end{warningbox}")
            lines.append("")

    if not has_content:
        lines.append(r"\textit{(No deferred items or failed approaches recorded.)}")
    return "\n".join(lines)


def _render_execution_provenance(topic_root: Path) -> str:
    log_path = topic_root / "runtime" / "log.md"
    if not log_path.exists():
        return (
            r"\section{Execution Provenance}" "\n\n"
            r"\textit{(No execution log yet.)}"
        )

    _, body = _parse_md(log_path)
    # Only take last ~30 event lines to avoid notebook bloat
    log_lines = [l for l in body.strip().split("\n") if l.strip()]
    recent = "\n".join(log_lines[-40:]) if len(log_lines) > 40 else body.strip()

    # Use verbatim for log content
    lines: list[str] = []
    lines.append(r"\section{Execution Provenance}")
    lines.append("")
    lines.append(r"{\footnotesize")
    lines.append(r"\begin{verbatim}")
    lines.append(_sanitize_unicode(recent[:8000]))
    lines.append(r"\end{verbatim}")
    lines.append(r"}")
    return "\n".join(lines)


# ── Section renderer dispatch ────────────────────────────────────────────

_SECTION_RENDERERS = {
    "research_question":    _render_research_question,
    "source_landscape":     _render_source_landscape,
    "conventions":          _render_conventions,
    "session_history":      _render_session_history,
    "derivation":           _render_derivation,
    "synthesis":            _render_synthesis,
    "validation":           _render_validation,
    "l2_knowledge":         _render_l2_knowledge,
    "domain_context":       _render_domain_context,
    "open_questions":       _render_open_questions,
    "execution_provenance": _render_execution_provenance,
}


# ── Template-based full document assembly ──────────────────────────────

def _resolve_template(topic_root: Path, template_path: Path | None) -> Path:
    if template_path is not None:
        return template_path
    repo_root = Path(__file__).resolve().parent.parent
    p = repo_root / "templates" / "flow_notebook.tex"
    if p.exists():
        return p
    return topic_root.parent.parent / "templates" / "flow_notebook.tex"


def _fill_template_placeholders(template_text: str, topic_root: Path) -> str:
    """Replace {{PLACEHOLDER}} in template with values from topic state."""
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

    Always assembles the document from the clean template — never uses
    existing notebook as base (avoids corruption propagation).

    Args:
        topic_root: Path to the topic directory.
        template_path: Path to the LaTeX template.  Auto-detected if None.
        changed_sections: Explicit sections to regenerate.  If None, hashes
            determine what changed.
        force_full: If True, regenerate every section.

    Returns:
        (notebook_text, list_of_regenerated_sections)
    """
    template_path = _resolve_template(topic_root, template_path)
    template_text = template_path.read_text(encoding="utf-8")

    # Split template into: preamble + sections + postamble
    # Each section lives between % --- BEGIN <name> --- and % --- END <name> ---
    tlines = template_text.split("\n")
    preamble_end = 0
    postamble_start = len(tlines)

    # Find the range of section markers
    first_begin = len(tlines)
    last_end = 0
    for i, line in enumerate(tlines):
        if _BEGIN_RE.match(line):
            if i < first_begin:
                first_begin = i
        if _END_RE.match(line) and i > last_end:
            last_end = i

    if first_begin < len(tlines) and last_end > 0:
        preamble_end = first_begin
        postamble_start = last_end + 1

    preamble = "\n".join(tlines[:preamble_end])
    postamble = "\n".join(tlines[postamble_start:])

    # Fill template-level placeholders
    preamble = _fill_template_placeholders(preamble, topic_root)

    # Determine which sections changed
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
        # Nothing changed — return existing notebook if available
        nb_path = topic_root / "flow_notebook.tex"
        if nb_path.exists():
            for name in SECTION_ORDER:
                if name not in new_hashes:
                    new_hashes[name] = _hash_files(topic_root, SECTION_SOURCES.get(name, []))
            _save_hash_state(topic_root, new_hashes)
            return nb_path.read_text(encoding="utf-8"), []
        # No existing notebook, must do full build
        to_regenerate = set(SECTION_ORDER)

    # Render sections and assemble document
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
            # Use cached section from existing notebook
            # We don't have per-section cache, so re-render silently
            # (hash check already passed, should be identical)
            renderer = _SECTION_RENDERERS.get(name)
            if renderer:
                rendered_sections.append(renderer(topic_root))
            else:
                rendered_sections.append("")
            if name not in new_hashes:
                new_hashes[name] = _hash_files(topic_root, SECTION_SOURCES.get(name, []))

    # Assemble: preamble + all sections + postamble
    body = "\n".join(rendered_sections)
    document = preamble + "\n" + body + "\n" + postamble

    _save_hash_state(topic_root, new_hashes)
    return document, regenerated


def render_all_sections(topic_root: Path) -> dict[str, str]:
    """Render every section and return {name: latex_content}.  Useful for
    manual inspection or AI-assisted polishing of individual sections."""
    result: dict[str, str] = {}
    for name in SECTION_ORDER:
        renderer = _SECTION_RENDERERS.get(name)
        if renderer:
            result[name] = renderer(topic_root)
    return result
