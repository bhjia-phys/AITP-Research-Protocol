"""Section renderers for the flow notebook.

Each _render_<section>() reads L0-L4 markdown artifacts and produces
LaTeX fragments. The renderers now use md_body_to_latex() for true
Markdown→LaTeX conversion (no more verbatim dumps).

Key improvements over v1:
- Empty subplanes render informative placeholders, not ghost sections
- Derivation subplanes are deduplicated (content fingerprint)
- Numerical results elevated from runtime log to Validation
- Session metadata compacted (gate only shown when blocked)
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from brain.flow_notebook.converter import md_body_to_latex
from brain.flow_notebook.utils import _esc, _sanitize_unicode, _parse_md

# ── Empty content detection ─────────────────────────────────────────────

def _is_substantive(md_body: str, min_lines: int = 2) -> bool:
    """Check if markdown body has substantive content beyond headings."""
    lines = [l.strip() for l in md_body.split('\n') if l.strip()]
    content_lines = [
        l for l in lines
        if not l.startswith('#')
        and l not in ('---', '***', '___')
    ]
    return len(content_lines) >= min_lines


def _placeholder_for(subplane: str) -> str:
    placeholders = {
        "gap-audit": r"\textit{No formal gap audit has been recorded at this stage.}",
        "connect": r"\textit{No cross-topic connections have been recorded at this stage.}",
        "trace-derivation": r"\textit{No source derivation trace has been recorded.}",
        "ideate": r"\textit{No idea has been recorded yet.}",
        "plan": r"\textit{No plan has been recorded yet.}",
        "derive": r"\textit{No derivation steps have been recorded yet.}",
        "integrate": r"\textit{No integration has been recorded yet.}",
        "distill": r"\textit{No distillation has been recorded yet.}",
    }
    return placeholders.get(subplane, r"\textit{No content recorded for this subplane.}")


# ── Content deduplication ───────────────────────────────────────────────

def _content_fingerprint(md_body: str) -> str:
    """SHA-256 fingerprint of normalized body for dedup."""
    normalized = ' '.join(md_body.split())
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


# ── Numerical result parsing from runtime log ───────────────────────────

def _parse_numerical_results_from_log(log_body: str) -> list[dict]:
    """Extract successful numerical results from runtime/log.md."""
    results: list[dict] = []
    for line in log_body.split('\n'):
        if 'L4_numerical_result' not in line:
            continue
        # Parse key-value pairs after the timestamp
        match = re.search(r'L4_numerical_result:\s*(.+)', line)
        if not match:
            continue
        payload = match.group(1)
        result = {"raw": payload[:300]}
        # Try to extract common patterns
        for pat, key in [
            (r'GW\s+VBM.*?([-\d.]+)\s*eV', 'vbm_eV'),
            (r'gap.*?([-\d.]+)\s*eV', 'gap_eV'),
            (r'G0W0\s+correction.*?([-\d.]+)\s*eV', 'correction_eV'),
        ]:
            m = re.search(pat, payload, re.IGNORECASE)
            if m:
                result[key] = m.group(1)
        if len(result) > 1:  # Has at least one extracted value
            results.append(result)
    return results


# ── Section renderers ───────────────────────────────────────────────────

def _render_research_question(topic_root: Path) -> str:
    qc_path = topic_root / "L1" / "question_contract.md"
    if not qc_path.exists():
        return r"\section{Research Question}" "\n\n" \
               r"\textit{(No question\_contract.md — complete L1 framing first.)}"

    fm, body = _parse_md(qc_path)
    question = fm.get("bounded_question", "")
    scope = fm.get("scope_boundaries", "")
    targets = fm.get("target_quantities", "")

    non_success = ""
    body_parts = body.split("## Non-Success Conditions")
    if len(body_parts) > 1:
        non_success = body_parts[1].split("##")[0].strip()

    lines: list[str] = []
    lines.append(r"\section{Research Question}\label{sec:question}")
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
        lines.append(md_body_to_latex(non_success))
        lines.append(r"\end{warningbox}")
    return "\n".join(lines)


def _render_source_landscape(topic_root: Path) -> str:
    src_dir = topic_root / "L0" / "sources"
    sources: list[dict] = []
    seen: set[str] = set()
    if src_dir.is_dir():
        for d in sorted(src_dir.iterdir()):
            if d.is_dir():
                sf = d / "source.md"
                if sf.exists():
                    fm, _ = _parse_md(sf)
                    sid = fm.get("source_id", d.name)
                    seen.add(sid)
                    sources.append({
                        "id": sid, "title": fm.get("title", d.name),
                        "source_type": fm.get("type", ""),
                        "fidelity": fm.get("fidelity", ""),
                        "role": fm.get("role", ""),
                    })
        for sp in sorted(src_dir.glob("*.md")):
            fm, _ = _parse_md(sp)
            sid = fm.get("source_id", sp.stem)
            if sid not in seen:
                seen.add(sid)
                sources.append({
                    "id": sid, "title": fm.get("title", sp.stem),
                    "source_type": fm.get("type", ""),
                    "fidelity": fm.get("fidelity", ""),
                    "role": fm.get("role", ""),
                })

    lines: list[str] = []
    lines.append(r"\section{Source Landscape}\label{sec:sources}")
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
        return r"\section{Conventions \& Notation}\label{sec:conventions}" "\n\n" \
               r"\textit{(No convention snapshot — complete L1/convention\_snapshot.md.)}"

    fm, body = _parse_md(cs_path)
    lines: list[str] = []
    lines.append(r"\section{Conventions \& Notation}\label{sec:conventions}")
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
    if body.strip():
        lines.append(md_body_to_latex(body))
    return "\n".join(lines)


def _render_session_metadata(topic_root: Path) -> str:
    """Compact protocol metadata — physics readers don't need this prominent."""
    state_path = topic_root / "state.md"
    if not state_path.exists():
        return r"\section{Session Metadata}" "\n\n" \
               r"\textit{(No state.md — topic not bootstrapped.)}"

    fm, _ = _parse_md(state_path)
    slug = str(fm.get("topic_slug", topic_root.name))
    posture = str(fm.get("posture", "?"))
    lane = str(fm.get("lane", "?"))
    status = str(fm.get("status", "?"))
    gate = str(fm.get("gate_status", "?"))

    lines: list[str] = []
    lines.append(r"\section{Session Metadata}\label{sec:session}")
    lines.append("")
    lines.append(r"\begin{tabular}{ll}")
    lines.append(r"\toprule")
    lines.append(r"\textbf{Field} & \textbf{Value} \\")
    lines.append(r"\midrule")
    for label, val in [
        ("Topic", _esc(slug)),
        ("Posture", _esc(posture)),
        ("Lane", _esc(lane)),
        ("Status", _esc(status)),
    ]:
        lines.append(f"{label} & \\texttt{{{val}}} \\\\")
    if gate.startswith("blocked"):
        lines.append(f"Gate & \\textcolor{{failred}}{{\\texttt{{{_esc(gate)}}}}} \\\\")
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    return "\n".join(lines)


def _render_derivation_journey(topic_root: Path) -> str:
    """Collect L3 subplane artifacts with empty detection and dedup."""
    from brain.state_model import L3_ACTIVITIES, L3_ACTIVITY_ARTIFACT_NAMES

    lines: list[str] = []
    lines.append(r"\section{Derivation Journey}\label{sec:derivation}")
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
                "active": r"\statusactive", "failed": r"\statusfail",
                "succeeded": r"\statuspass", "abandoned": r"\statusdeferred",
                "superseded": r"\statusdeferred",
            }.get(status, r"\statusactive")
            lines.append(r"\begin{resultbox}[" + _esc(title) + r" \quad " + status_cmd + "]")
            if approach:
                lines.append(_esc(approach[:800]))
            lines.append(r"\end{resultbox}")
            lines.append("")

    # Subplane artifacts with dedup
    seen_fingerprints: dict[str, str] = {}  # fp → first subplane name
    has_any = False
    for sp in L3_ACTIVITIES:
        art_name = L3_ACTIVITY_ARTIFACT_NAMES.get(sp, f"active_{sp}.md")
        art_path = topic_root / "L3" / sp / art_name
        if not art_path.exists():
            continue
        fm, body = _parse_md(art_path)
        label = sp.replace("-", " ").replace("_", " ").title()

        if not body.strip():
            lines.append(r"\subsection*{" + label + "}")
            lines.append(_placeholder_for(sp))
            lines.append("")
            continue

        # Dedup check
        fp = _content_fingerprint(body)
        if fp in seen_fingerprints:
            primary = seen_fingerprints[fp]
            lines.append(r"\subsection*{" + label + "}")
            lines.append(
                r"\textit{Content identical to \textbf{" + primary
                + r"} — see preceding subsection.}"
            )
            lines.append("")
            continue

        seen_fingerprints[fp] = label
        has_any = True
        lines.append(r"\subsection*{" + label + "}")
        if _is_substantive(body):
            lines.append(md_body_to_latex(body))
        else:
            lines.append(_placeholder_for(sp))
        lines.append("")

    if not has_any and not idea_files:
        lines.append(r"\textit{(No derivation content yet — advance to L3.)}")
    return "\n".join(lines)


def _render_synthesis_claims(topic_root: Path) -> str:
    lines: list[str] = []
    lines.append(r"\section{Synthesis \& Claims}\label{sec:synthesis}")
    lines.append("")

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
    lines.append(r"\section{Validation}\label{sec:validation}")
    lines.append("")

    has_any = False

    # Numerical results from L4/outputs
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
            lines.append(
                f"Computed: {_esc(str(value))} $\\pm$ {_esc(str(uncertainty))}"
                f" {_esc(str(units))}"
            )
            if lit_val:
                lines.append(f"\\quad Literature: {_esc(str(lit_val))} {_esc(str(units))}")
            if agreement:
                lines.append(f"\\quad Agreement: {_esc(agreement)}")
            lines.append(r"\end{valbox}")
            lines.append("")

    # Numerical results elevated from runtime log
    log_path = topic_root / "runtime" / "log.md"
    if log_path.exists():
        _, log_body = _parse_md(log_path)
        log_results = _parse_numerical_results_from_log(log_body)
        for lr in log_results:
            has_any = True
            lines.append(r"\begin{valbox}[Numerical Result]")
            lines.append(r"{\footnotesize " + _esc(lr.get("raw", "")[:400]) + "}")
            lines.append(r"\end{valbox}")
            lines.append("")

    # Reviews
    review_dir = topic_root / "L4" / "reviews"
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
                lines.append(md_body_to_latex(body[:2000]))
            lines.append(r"\end{warningbox}")
            lines.append("")

    if not has_any:
        lines.append(r"\textit{(No validation reviews or numerical results yet.)}")
    return "\n".join(lines)


def _render_negative_results(topic_root: Path) -> str:
    lines: list[str] = []
    lines.append(r"\section{Negative Results \& Open Questions}\label{sec:negative}")
    lines.append("")

    has_content = False

    deferred_path = topic_root / "L3" / "deferred.md"
    if deferred_path.exists():
        _, body = _parse_md(deferred_path)
        if body.strip():
            has_content = True
            lines.append(r"\subsection*{Deferred Items}")
            lines.append(md_body_to_latex(body[:3000]))

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


def _render_canonical_knowledge(topic_root: Path) -> str:
    lines: list[str] = []
    lines.append(r"\section{Canonical Knowledge (L2)}\label{sec:l2}")
    lines.append("")

    global_l2 = topic_root.parent / "L2" / "graph" / "nodes"
    if not global_l2.is_dir():
        global_l2 = topic_root.parent.parent / "L2" / "graph" / "nodes"

    nodes: list[dict] = []
    if global_l2.is_dir():
        for np in sorted(global_l2.glob("*.md"))[:30]:
            fm, _ = _parse_md(np)
            nodes.append({
                "id": np.stem, "title": fm.get("title", np.stem),
                "node_type": fm.get("node_type", ""),
            })

    if nodes:
        lines.append(r"\begin{longtable}{>{\raggedright}p{3cm} p{2cm} p{6cm}}")
        lines.append(r"\toprule")
        lines.append(r"\textbf{Node} & \textbf{Type} & \textbf{Title} \\")
        lines.append(r"\midrule")
        lines.append(r"\endhead")
        for n in nodes:
            lines.append(
                f"{_esc(n['id'][:40])} & {_esc(n['node_type'][:20])} & "
                f"{_esc(n['title'][:90])} \\\\"
            )
        lines.append(r"\bottomrule")
        lines.append(r"\end{longtable}")
    else:
        lines.append(r"\textit{(No L2 nodes promoted from this topic yet.)}")
    return "\n".join(lines)


def _render_domain_context(topic_root: Path) -> str:
    dm_path = topic_root / "contracts" / "domain-manifest.md"
    if not dm_path.exists():
        return r"\section{Domain Context}\label{sec:domain}" "\n\n" \
               r"\textit{(No domain manifest — create contracts/domain-manifest.md.)}"

    fm, body = _parse_md(dm_path)
    domain_id = fm.get("domain_id", "")
    lines: list[str] = []
    lines.append(r"\section{Domain Context}\label{sec:domain}")
    lines.append("")
    if domain_id:
        lines.append(r"\noindent\textbf{Domain:} \texttt{" + _esc(domain_id) + r"} \\")
    if body.strip():
        lines.append(md_body_to_latex(body[:2000]))
    return "\n".join(lines)


def _render_execution_provenance(topic_root: Path) -> str:
    log_path = topic_root / "runtime" / "log.md"
    if not log_path.exists():
        return r"\section{Execution Provenance}\label{sec:provenance}" "\n\n" \
               r"\textit{(No execution log yet.)}"

    _, body = _parse_md(log_path)
    log_lines = [l for l in body.strip().split("\n") if l.strip()]
    recent = "\n".join(log_lines[-40:]) if len(log_lines) > 40 else body.strip()

    lines: list[str] = []
    lines.append(r"\section{Execution Provenance}\label{sec:provenance}")
    lines.append("")
    lines.append(r"{\footnotesize")
    lines.append(r"\begin{verbatim}")
    lines.append(_sanitize_unicode(recent[:8000]))
    lines.append(r"\end{verbatim}")
    lines.append(r"}")
    return "\n".join(lines)


# ── Renderer dispatch ───────────────────────────────────────────────────

_SECTION_RENDERERS = {
    "research_question":    _render_research_question,
    "source_landscape":     _render_source_landscape,
    "conventions":          _render_conventions,
    "derivation_journey":   _render_derivation_journey,
    "synthesis_claims":     _render_synthesis_claims,
    "validation":           _render_validation,
    "negative_results":     _render_negative_results,
    "canonical_knowledge":  _render_canonical_knowledge,
    "domain_context":       _render_domain_context,
    "session_metadata":     _render_session_metadata,
    "execution_provenance": _render_execution_provenance,
}
