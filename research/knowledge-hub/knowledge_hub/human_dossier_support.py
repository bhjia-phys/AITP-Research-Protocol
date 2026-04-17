"""L3 Human Dossier — LaTeX research compilation for theoretical physics topics.

Generates a complete LaTeX dossier from a topic's L0-L4 artifacts,
structured for a theoretical physicist to read and review.

Each research cycle (L3-I → L3-P → L4 → L3-R) is rendered as a
self-contained derivation section with physics-grade formatting.
"""
from __future__ import annotations

import json
import re
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _tex_escape(text: str) -> str:
    for ch, rep in [
        ("\\", r"\textbackslash{}"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("$", r"\$"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ]:
        text = text.replace(ch, rep)
    return text


def _md_to_tex(md: str) -> str:
    """Best-effort Markdown → LaTeX conversion for physics content."""
    out: list[str] = []
    for line in md.splitlines():
        stripped = line.strip()
        if stripped.startswith("### "):
            out.append(r"\subsubsection{" + _tex_escape(stripped[4:]) + "}")
        elif stripped.startswith("## "):
            out.append(r"\subsection{" + _tex_escape(stripped[3:]) + "}")
        elif stripped.startswith("# "):
            out.append(r"\section{" + _tex_escape(stripped[2:]) + "}")
        elif stripped.startswith("- "):
            out.append(r"\item " + _tex_escape(stripped[2:]))
        elif stripped.startswith("$$"):
            out.append(stripped)
        elif stripped.startswith("`") and stripped.endswith("`") and len(stripped) > 2:
            out.append(r"\texttt{" + _tex_escape(stripped[1:-1]) + "}")
        elif stripped == "":
            out.append("")
        else:
            out.append(_tex_escape(stripped))
    return "\n".join(out)


def _wrap_itemize(lines: list[str]) -> list[str]:
    result: list[str] = []
    inside = False
    for line in lines:
        if r"\item" in line and not inside:
            result.append(r"\begin{itemize}")
            inside = True
        elif r"\item" not in line and inside and line.strip() == "":
            result.append(r"\end{itemize}")
            inside = False
        result.append(line)
    if inside:
        result.append(r"\end{itemize}")
    return result


@dataclass
class CycleData:
    cycle_id: str = ""
    idea: str = ""
    plan: str = ""
    derivation: str = ""
    validation_result: str = ""
    result_interpretation: str = ""
    assessment: str = ""
    timestamp: str = ""
    candidates: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class TopicDossier:
    topic_slug: str = ""
    research_question: str = ""
    background: str = ""
    sources: list[dict[str, str]] = field(default_factory=list)
    cycles: list[CycleData] = field(default_factory=list)
    conclusions: str = ""
    open_problems: list[str] = field(default_factory=list)
    numerical_data: str = ""
    generated_at: str = ""


def _collect_sources(topic_root: Path) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    source_index = topic_root / "source-layer" / "topics" / _slug_from(topic_root) / "source_index.jsonl"
    if not source_index.exists():
        source_index = topic_root / "L0" / "source_index.jsonl"
    for row in read_jsonl(source_index):
        sources.append({
            "title": str(row.get("title", "")),
            "summary": str(row.get("summary", "")),
            "id": str(row.get("id", row.get("source_id", ""))),
        })
    return sources


def _slug_from(topic_root: Path) -> str:
    return topic_root.name


def _collect_l1_notes(topic_root: Path, slug: str) -> str:
    parts: list[str] = []
    l1_dir = topic_root / "L1"
    if l1_dir.exists():
        for p in sorted(l1_dir.rglob("*.md")):
            content = read_text(p)
            if content:
                parts.append(f"## {p.stem}\n\n{content}")
    source_notes = topic_root / "source-layer" / "topics" / slug
    if source_notes.exists():
        for p in sorted(source_notes.rglob("*.md")):
            content = read_text(p)
            if content:
                parts.append(f"## {p.stem}\n\n{content}")
    return "\n\n".join(parts)


def _collect_candidates(run_dir: Path) -> list[dict[str, Any]]:
    ledger = run_dir / "candidate_ledger.jsonl"
    return read_jsonl(ledger)


def _collect_cycles(topic_root: Path, slug: str) -> list[CycleData]:
    cycles: list[CycleData] = []

    l3_runs = topic_root / "L3" / "runs"
    if not l3_runs.exists():
        l3_runs = topic_root / "topics" / slug / "L3" / "runs"

    if not l3_runs.exists():
        return cycles

    for run_dir in sorted(l3_runs.iterdir()):
        if not run_dir.is_dir():
            continue
        cycle = CycleData(
            cycle_id=run_dir.name,
            timestamp=run_dir.name.split("T")[0] if "T" in run_dir.name else run_dir.name[:10],
            idea=read_text(run_dir / "idea_packet.md"),
            plan=read_text(run_dir / "validation_plan.md"),
            derivation=read_text(run_dir / "result_summary.md"),
            candidates=_collect_candidates(run_dir),
        )

        val_base = topic_root / "validation" / "topics" / slug / "runs" / run_dir.name
        if val_base.exists():
            for vp in sorted(val_base.rglob("*.md")):
                cycle.validation_result += read_text(vp) + "\n\n"

        runtime_idea = topic_root / "runtime" / "topics" / slug / "runtime" / "idea_packet.md"
        if runtime_idea.exists() and not cycle.idea:
            cycle.idea = read_text(runtime_idea)

        cycles.append(cycle)

    return cycles


def _collect_validation_results(topic_root: Path, slug: str) -> str:
    parts: list[str] = []
    val_base = topic_root / "validation" / "topics" / slug
    if val_base.exists():
        for p in sorted(val_base.rglob("*.md")):
            content = read_text(p)
            if content:
                parts.append(f"## {p.relative_to(val_base)}\n\n{content}")
    return "\n\n".join(parts)


def _collect_conclusions(runtime_dir: Path) -> tuple[str, list[str]]:
    conclusions = ""
    open_problems: list[str] = []

    op_console = runtime_dir / "operator_console.md"
    if op_console.exists():
        conclusions += read_text(op_console)

    gap_map = runtime_dir / "gap_map.md"
    if gap_map.exists():
        text = read_text(gap_map)
        open_problems.extend(
            line.lstrip("- ").strip()
            for line in text.splitlines()
            if line.strip().startswith("- ")
        )

    return conclusions, open_problems


def collect_dossier(topic_root: Path) -> TopicDossier:
    """Collect all research data from a topic directory into a dossier."""
    slug = _slug_from(topic_root)
    runtime_dir = topic_root / "runtime"
    if not runtime_dir.exists():
        runtime_dir = topic_root / "runtime" / "topics" / slug / "runtime"

    rq_path = runtime_dir / "research_question.contract.md"
    research_question = read_text(rq_path)

    sources = _collect_sources(topic_root)
    background = _collect_l1_notes(topic_root, slug)
    cycles = _collect_cycles(topic_root, slug)
    conclusions, open_problems = _collect_conclusions(runtime_dir)
    numerical_data = _collect_validation_results(topic_root, slug)

    return TopicDossier(
        topic_slug=slug,
        research_question=research_question,
        background=background,
        sources=sources,
        cycles=cycles,
        conclusions=conclusions,
        open_problems=open_problems,
        numerical_data=numerical_data,
        generated_at=datetime.now().isoformat(),
    )


# ── LaTeX rendering ──────────────────────────────────────────────────

_PREAMBLE = r"""\documentclass[11pt,a4paper]{article}

% ── Packages ──────────────────────────────────────────────────────────
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{amsmath,amssymb,amsthm}
\usepackage{mathtools}
\usepackage{physics}
\usepackage{bm}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{enumitem}
\usepackage{hyperref}
\usepackage{xcolor}
\usepackage{tcolorbox}
\usepackage[margin=2.5cm]{geometry}
\usepackage{fancyhdr}
\usepackage{lastpage}
\usepackage{listings}
\usepackage{natbib}

% ── Theorem environments ─────────────────────────────────────────────
\newtheorem{theorem}{Theorem}[section]
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{proposition}[theorem]{Proposition}
\newtheorem{corollary}[theorem]{Corollary}
\newtheorem{conjecture}{Conjecture}[section]
\newtheorem{definition}{Definition}[section]
\newtheorem{remark}{Remark}[section]

% ── Custom commands for physics ───────────────────────────────────────
\newcommand{\ket}[1]{\left|#1\right\rangle}
\newcommand{\bra}[1]{\left\langle#1\right|}
\newcommand{\braket}[2]{\left\langle#1\middle|#2\right\rangle}
\newcommand{\expect}[1]{\left\langle#1\right\rangle}
\newcommand{\Tr}{\operatorname{Tr}}
\newcommand{\Hil}{\mathcal{H}}

% ── Status boxes ─────────────────────────────────────────────────────
\definecolor{ideacolor}{RGB}{0,100,180}
\definecolor{plancolor}{RGB}{0,130,60}
\definecolor{resultcolor}{RGB}{140,80,0}
\definecolor{assesscolor}{RGB}{120,0,120}

\newtcolorbox{ideabox}[1][]{colback=ideacolor!5,colframe=ideacolor!70,
  title={\textbf{Idea (L3-I)}},fonttitle=\color{white},#1}
\newtcolorbox{planbox}[1][]{colback=plancolor!5,colframe=plancolor!70,
  title={\textbf{Plan (L3-P)}},fonttitle=\color{white},#1}
\newtcolorbox{resultbox}[1][]{colback=resultcolor!5,colframe=resultcolor!70,
  title={\textbf{Result (L3-R / L4)}},fonttitle=\color{white},#1}
\newtcolorbox{assessbox}[1][]{colback=assesscolor!5,colframe=assesscolor!70,
  title={\textbf{Assessment}},fonttitle=\color{white},#1}

% ── Page style ────────────────────────────────────────────────────────
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\textit{AITP Research Dossier}}
\fancyhead[R]{\small\textit{\topicname}}
\fancyfoot[C]{\small\thepage\,/\,\pageref{LastPage}}

% ── Listings ──────────────────────────────────────────────────────────
\lstset{
  basicstyle=\ttfamily\small,
  breaklines=true,
  frame=single,
  backgroundcolor=\color{gray!5},
}

\newcommand{\topicname}{}

\begin{document}
"""

_CLOSE = r"""
\end{document}
"""


def _render_title(dossier: TopicDossier) -> str:
    slug_nice = dossier.topic_slug.replace("-", " ").replace("_", " ").title()
    return (
        f"\\newcommand{{\\topicname}}{{{_tex_escape(slug_nice)}}}\n"
        f"\\title{{\\textbf{{Research Dossier}} \\\\\n"
        f"  \\large {{{_tex_escape(slug_nice)}}}}}\n"
        f"\\author{{AITP Research Protocol}}\n"
        f"\\date{{Generated: {_tex_escape(dossier.generated_at[:19])}}}\n"
        f"\\maketitle\n"
        f"\\tableofcontents\n"
        f"\\newpage\n"
    )


def _render_abstract(dossier: TopicDossier) -> str:
    parts = [r"\section{Research Question}", ""]
    if dossier.research_question:
        parts.append(_md_to_tex(dossier.research_question))
    else:
        parts.append(r"\textit{No research question contract recorded.}")
    return "\n".join(parts) + "\n\n"


def _render_sources(dossier: TopicDossier) -> str:
    if not dossier.sources:
        return ""
    parts = [r"\section{Sources (L0)}", "", r"\begin{itemize}"]
    for s in dossier.sources:
        title = _tex_escape(s.get("title", "Untitled"))
        summary = _tex_escape(s.get("summary", ""))
        sid = _tex_escape(s.get("id", ""))
        entry = f"\\item \\textbf{{{title}}} \\cite{{{sid}}}"
        if summary:
            entry += f" --- {summary}"
        parts.append(entry)
    parts.append(r"\end{itemize}")
    return "\n".join(parts) + "\n\n"


def _render_background(dossier: TopicDossier) -> str:
    if not dossier.background:
        return ""
    return (
        "\\section{Background (L0/L1)}\n\n"
        + _md_to_tex(dossier.background)
        + "\n\n"
    )


def _render_cycle(cycle: CycleData, idx: int) -> str:
    parts = [
        f"\\section{{Cycle {idx:03d}: {_tex_escape(cycle.timestamp)}}}",
        "",
    ]

    if cycle.idea:
        parts += [r"\begin{ideabox}", _md_to_tex(cycle.idea), r"\end{ideabox}", ""]

    if cycle.plan:
        parts += [r"\begin{planbox}", _md_to_tex(cycle.plan), r"\end{planbox}", ""]

    if cycle.derivation:
        parts += [
            r"\subsection{Derivation (L3-A $\to$ L4)}",
            "",
            _md_to_tex(cycle.derivation),
            "",
        ]

    if cycle.validation_result:
        parts += [
            r"\begin{resultbox}",
            _md_to_tex(cycle.validation_result),
            r"\end{resultbox}",
            "",
        ]

    if cycle.candidates:
        parts += [r"\subsection{Candidates}", ""]
        for c in cycle.candidates:
            cid = _tex_escape(str(c.get("candidate_id", "unknown")))
            title = _tex_escape(str(c.get("title", "Untitled")))
            summary = _tex_escape(str(c.get("summary", "")))
            status = _tex_escape(str(c.get("status", "")))
            parts.append(f"\\subsubsection{{Candidate: {title}}}")
            parts.append("")
            parts.append(f"\\textbf{{ID:}} \\texttt{{{cid}}} \\\\")
            parts.append(f"\\textbf{{Status:}} {status} \\\\")
            if summary:
                parts.append(f"\\textbf{{Summary:}} {summary}")
            parts.append("")

            assumptions = c.get("assumptions", [])
            if assumptions:
                parts.append(r"\textbf{Assumptions:}")
                parts.append(r"\begin{itemize}")
                for a in assumptions:
                    parts.append(f"\\item {_tex_escape(str(a))}")
                parts.append(r"\end{itemize}")

            blockers = c.get("promotion_blockers", [])
            if blockers:
                parts.append(r"\textbf{Promotion blockers:}")
                parts.append(r"\begin{itemize}")
                for b in blockers:
                    parts.append(f"\\item {_tex_escape(str(b))}")
                parts.append(r"\end{itemize}")

    return "\n".join(parts) + "\n\n"


def _render_conclusions(dossier: TopicDossier) -> str:
    if not dossier.conclusions:
        return ""
    return (
        "\\section{Current State}\n\n"
        + _md_to_tex(dossier.conclusions)
        + "\n\n"
    )


def _render_open_problems(dossier: TopicDossier) -> str:
    if not dossier.open_problems:
        return ""
    parts = [r"\section{Open Problems}", "", r"\begin{itemize}"]
    for p in dossier.open_problems:
        parts.append(f"\\item {_tex_escape(p)}")
    parts.append(r"\end{itemize}")
    return "\n".join(parts) + "\n\n"


def _render_numerical_data(dossier: TopicDossier) -> str:
    if not dossier.numerical_data:
        return ""
    return (
        "\\section{Numerical Data (L4)}\n\n"
        + _md_to_tex(dossier.numerical_data)
        + "\n\n"
    )


def render_dossier_tex(dossier: TopicDossier) -> str:
    """Render the full dossier as a single LaTeX document."""
    parts = [_PREAMBLE, _render_title(dossier), _render_abstract(dossier)]

    parts.append(_render_sources(dossier))
    parts.append(_render_background(dossier))

    for i, cycle in enumerate(dossier.cycles, 1):
        parts.append(_render_cycle(cycle, i))

    parts.append(_render_conclusions(dossier))
    parts.append(_render_open_problems(dossier))
    parts.append(_render_numerical_data(dossier))
    parts.append(_CLOSE)

    return "\n".join(parts)


def write_dossier(topic_root: Path, output_dir: Path | None = None) -> Path:
    """Collect data from topic_root and write the dossier to disk.

    Returns the path to the generated main.tex.
    """
    dossier = collect_dossier(topic_root)
    slug = dossier.topic_slug

    if output_dir is None:
        output_dir = topic_root / "L3" / "human_dossier"

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "figures").mkdir(exist_ok=True)

    main_tex = render_dossier_tex(dossier)
    main_path = output_dir / "main.tex"
    main_path.write_text(main_tex, encoding="utf-8")

    _write_preamble(output_dir)

    cycles_dir = output_dir / "cycles"
    cycles_dir.mkdir(exist_ok=True)
    for i, cycle in enumerate(dossier.cycles, 1):
        cycle_tex = _render_cycle(cycle, i)
        cycle_path = cycles_dir / f"cycle_{i:03d}.tex"
        cycle_path.write_text(cycle_tex, encoding="utf-8")

    _write_bib(dossier, output_dir)

    meta = {
        "topic_slug": slug,
        "generated_at": dossier.generated_at,
        "num_cycles": len(dossier.cycles),
        "num_sources": len(dossier.sources),
        "output_dir": str(output_dir),
    }
    (output_dir / "dossier_meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return main_path


def _write_preamble(output_dir: Path) -> None:
    prelude_lines = [
        r"% This file contains reusable preamble commands.",
        r"% Included by main.tex. Edit to customize physics macros.",
        "",
        r"% Example custom command:",
        r"% \newcommand{\ham}{\hat{H}}",
    ]
    (output_dir / "preamble_custom.tex").write_text(
        "\n".join(prelude_lines) + "\n", encoding="utf-8"
    )


def _write_bib(dossier: TopicDossier, output_dir: Path) -> None:
    bib_path = output_dir / "references.bib"
    if not dossier.sources:
        bib_path.write_text("% No sources registered.\n", encoding="utf-8")
        return

    entries: list[str] = []
    for i, s in enumerate(dossier.sources):
        sid = re.sub(r"[^a-zA-Z0-9]", "_", s.get("id", f"source_{i}"))
        title = s.get("title", "Untitled")
        entries.append(
            f"@misc{{{sid},\n"
            f"  title = {{{_tex_escape(title)}}},\n"
            f"  note = {{AITP source}},\n"
            f"}}\n"
        )
    bib_path.write_text("\n".join(entries), encoding="utf-8")


def collect_all_dossiers(kernel_root: Path, topics_dir: Path | None = None) -> list[Path]:
    """Generate dossiers for all topics that have L3 data.

    Returns list of generated main.tex paths.
    """
    if topics_dir is None:
        topics_dir = kernel_root / "topics"

    generated: list[Path] = []
    if not topics_dir.exists():
        return generated

    for topic_dir in sorted(topics_dir.iterdir()):
        if not topic_dir.is_dir():
            continue
        l3 = topic_dir / "L3"
        if not l3.exists():
            l3 = topic_dir
        runs = l3 / "runs"
        if runs.exists() and any(runs.iterdir()):
            try:
                path = write_dossier(topic_dir)
                generated.append(path)
            except Exception as exc:
                print(f"[dossier] {topic_dir.name}: {exc}")

    return generated
