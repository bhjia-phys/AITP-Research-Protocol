"""LaTeX research notebook for L3 candidate workspace.

Maintains a compilable LaTeX file at ``topics/<slug>/L3/research_notebook.tex``
that accumulates every L3 operation as a dated, structured section.
Each append rewrites the full file so it always compiles cleanly.
"""
from __future__ import annotations

import json
import re
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

_LATEX_ESCAPE_MAP = str.maketrans({
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
})


def _esc(text: str) -> str:
    return text.translate(_LATEX_ESCAPE_MAP)


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _notebook_paths(l3_root: Path) -> dict[str, Path]:
    return {
        "tex": l3_root / "research_notebook.tex",
        "pdf": l3_root / "research_notebook.pdf",
        "aux": l3_root / "research_notebook.aux",
        "log": l3_root / "research_notebook.log",
        "out": l3_root / "research_notebook.synctex.gz",
        "entries": l3_root / "research_notebook_entries.jsonl",
    }


def _topic_paths(l3_root: Path) -> dict[str, Path]:
    topic_root = l3_root.parent
    runtime_root = topic_root / "runtime"
    return {
        "topic_root": topic_root,
        "runtime_root": runtime_root,
        "runs_root": l3_root / "runs",
        "research_contract": runtime_root / "research_question.contract.json",
        "idea_packet": runtime_root / "idea_packet.json",
        "unfinished_work": runtime_root / "unfinished_work.json",
    }


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _summarize_scalar(value: Any) -> str:
    if isinstance(value, (list, dict)):
        try:
            text = json.dumps(value, ensure_ascii=False, separators=(", ", ": "))
        except TypeError:
            text = str(value)
    else:
        text = str(value or "").strip()
    return text


def _render_plain_paragraph(text: str) -> list[str]:
    normalized = str(text or "").strip()
    if not normalized:
        return []
    return [_esc_latex_body(normalized), ""]


def _render_body_paragraphs(text: str) -> list[str]:
    normalized = str(text or "").strip()
    if not normalized:
        return []
    lines: list[str] = []
    for paragraph in normalized.split("\n\n"):
        chunk = paragraph.strip()
        if not chunk:
            continue
        lines.append(_esc_latex_body(chunk))
        lines.append("")
    return lines


def _status_badge(status: str) -> str:
    normalized = str(status or "").strip()
    if not normalized:
        return ""
    if normalized in ("success", "completed", "promoted", "approved"):
        return f"\\statusgood{{{_esc(normalized)}}}"
    if normalized in ("failed", "error", "rejected", "discarded", "blocked"):
        return f"\\statusfail{{{_esc(normalized)}}}"
    return f"\\statuswarn{{{_esc(normalized)}}}"


def _render_meta_badge_line(pairs: list[tuple[str, str]], *, status: str = "") -> list[str]:
    badges = [
        f"\\metaitem{{{_esc(label)}}}{{{_esc(value)}}}"
        for label, value in pairs
        if str(value or "").strip()
    ]
    status_badge = _status_badge(status)
    if status_badge:
        badges.append(status_badge)
    if not badges:
        return []
    return ["\\noindent " + " \\hspace{0.45em} ".join(badges) + r"\par", ""]


def _render_bullet_block(title: str, items: list[str]) -> list[str]:
    if not items:
        return []
    lines = [f"\\subsection*{{{_esc(title)}}}", "\\begin{itemize}"]
    for item in items:
        lines.append(f"  \\item {_esc_latex_body(item)}")
    lines.append("\\end{itemize}")
    lines.append("")
    return lines


def _render_kv_box(rows: list[tuple[str, str]]) -> list[str]:
    filtered_rows = [(label, value) for label, value in rows if str(value or "").strip()]
    if not filtered_rows:
        return []
    lines = [
        "\\begin{tcolorbox}[enhanced,breakable,colback=white,colframe=linecolor,boxrule=0.4pt,arc=1.0mm,left=1.1mm,right=1.1mm,top=0.9mm,bottom=0.9mm]",
        "\\begin{tabularx}{\\linewidth}{@{}>{\\raggedright\\arraybackslash\\ttfamily\\footnotesize\\color{muted}}p{0.28\\linewidth}>{\\raggedright\\arraybackslash}X@{}}",
        "\\toprule",
        "\\textnormal{Field} & \\textnormal{Value} \\\\",
        "\\midrule",
    ]
    for key, value in filtered_rows:
        cell = _esc_latex_body(value).replace(" \\\\\n", r"\newline ")
        lines.append(f"{_esc(key)} & {cell} \\\\")
    lines.extend(
        [
            "\\bottomrule",
            "\\end{tabularx}",
            "\\end{tcolorbox}",
            "",
        ]
    )
    return lines


def _render_named_box(title: str, rows: list[tuple[str, str]], body: list[str] | None = None) -> list[str]:
    lines = [
        "\\begin{tcolorbox}[enhanced,breakable,colback=softfill,colframe=linecolor,boxrule=0.45pt,arc=1.0mm,left=1.2mm,right=1.2mm,top=1.0mm,bottom=1.0mm]",
        f"{{\\small\\bfseries\\color{{ink}} {_esc(title)}}}\\par",
        "\\medskip",
    ]
    if body:
        for item in body:
            lines.append(item)
    kv_lines = _render_kv_box(rows)
    if kv_lines:
        lines.extend(kv_lines)
    lines.append("\\end{tcolorbox}")
    lines.append("")
    return lines


def _collect_run_records(l3_root: Path) -> list[dict[str, Any]]:
    runs_root = _topic_paths(l3_root)["runs_root"]
    if not runs_root.exists():
        return []

    records: list[dict[str, Any]] = []
    for run_root in sorted(path for path in runs_root.iterdir() if path.is_dir()):
        candidate_rows = _read_jsonl(run_root / "candidate_ledger.jsonl")
        derivation_rows = _read_jsonl(run_root / "derivation_records.jsonl")
        comparison_rows = _read_jsonl(run_root / "l2_comparison_receipts.jsonl")
        strategy_rows = _read_jsonl(run_root / "strategy_memory.jsonl")
        journal_payload = _read_json(run_root / "iteration_journal.json") or {}
        records.append(
            {
                "run_id": run_root.name,
                "candidate_rows": candidate_rows,
                "derivation_rows": derivation_rows,
                "comparison_rows": comparison_rows,
                "strategy_rows": strategy_rows,
                "iteration_journal": journal_payload,
            }
        )
    return records


def _render_research_framing_section(l3_root: Path) -> list[str]:
    topic_paths = _topic_paths(l3_root)
    research_contract = _read_json(topic_paths["research_contract"]) or {}
    idea_packet = _read_json(topic_paths["idea_packet"]) or {}
    if not research_contract and not idea_packet:
        return []

    lines = ["\\section{Research Framing}", ""]
    lines.extend(
        _render_kv_box(
            [
                ("Topic", _topic_slug_from_l3(l3_root)),
                ("Idea Status", _summarize_scalar(idea_packet.get("status"))),
                ("Initial Idea", _summarize_scalar(idea_packet.get("initial_idea"))),
                ("Novelty Target", _summarize_scalar(idea_packet.get("novelty_target"))),
                ("First Validation Route", _summarize_scalar(idea_packet.get("first_validation_route"))),
                ("Evidence Bar", _summarize_scalar(idea_packet.get("initial_evidence_bar"))),
            ]
        )
    )

    question = _summarize_scalar(research_contract.get("question") or research_contract.get("title"))
    if question:
        lines.append("\\subsection*{Active Question}")
        lines.extend(_render_plain_paragraph(question))

    lines.append("\\subsection*{How To Read This Notebook}")
    lines.extend(
        _render_plain_paragraph(
            "L1 appears only as a source-provenance map. All detailed derivation bodies, including source reconstructions, "
            "live in L3 so the topic keeps one derivation home. Machine-facing ids and event-level audit trails are pushed "
            "to later appendix-style sections."
        )
    )

    lines.extend(_render_bullet_block("Scope", _string_list(research_contract.get("scope"))))
    lines.extend(_render_bullet_block("Assumptions", _string_list(research_contract.get("assumptions"))))
    lines.extend(_render_bullet_block("Formalism And Notation", _string_list(research_contract.get("formalism_and_notation"))))
    lines.extend(_render_bullet_block("Deliverables", _string_list(research_contract.get("deliverables"))))
    return lines


def _render_source_provenance_section(l3_root: Path) -> list[str]:
    research_contract = _read_json(_topic_paths(l3_root)["research_contract"]) or {}
    l1_intake = research_contract.get("l1_source_intake") or {}
    l1_vault = research_contract.get("l1_vault") or {}
    if not l1_intake and not l1_vault:
        return []

    lines = ["\\section{Source Provenance Map}", ""]
    lines.extend(
        _render_kv_box(
            [
                ("Source Count", _summarize_scalar(l1_intake.get("source_count"))),
                ("Vault Status", _summarize_scalar(l1_vault.get("status"))),
                ("Vault Authority", _summarize_scalar(l1_vault.get("authority_level"))),
            ]
        )
    )

    reading_depth_rows = _dict_list(l1_intake.get("reading_depth_rows"))
    if reading_depth_rows:
        lines.append("\\subsection*{Reading Depth}")
        for row in reading_depth_rows:
            title = _summarize_scalar(row.get("source_title") or row.get("source_id") or "Source")
            lines.extend(
                _render_named_box(
                    title,
                    [
                        ("Reading Depth", _summarize_scalar(row.get("reading_depth"))),
                        ("Basis", _summarize_scalar(row.get("basis"))),
                    ],
                )
            )

    method_rows = _dict_list(l1_intake.get("method_specificity_rows"))
    if method_rows:
        lines.append("\\subsection*{Method Surfaces}")
        for row in method_rows:
            title = _summarize_scalar(row.get("source_title") or row.get("source_id") or "Method Record")
            lines.extend(
                _render_named_box(
                    title,
                    [
                        ("Method Family", _summarize_scalar(row.get("method_family"))),
                        ("Specificity Tier", _summarize_scalar(row.get("specificity_tier"))),
                        ("Reading Depth", _summarize_scalar(row.get("reading_depth"))),
                    ],
                    body=_render_plain_paragraph(_summarize_scalar(row.get("evidence_excerpt"))),
                )
            )

    notation_rows = _dict_list(l1_intake.get("notation_tension_candidates"))
    notation_items = [
        _summarize_scalar(row.get("summary") or row.get("description") or row)
        for row in notation_rows
    ]
    lines.extend(_render_bullet_block("Notation Tensions", notation_items))

    contradiction_rows = _dict_list(l1_intake.get("contradiction_candidates"))
    contradiction_items = [
        _summarize_scalar(row.get("summary") or row.get("description") or row)
        for row in contradiction_rows
    ]
    lines.extend(_render_bullet_block("Contradiction Watchlist", contradiction_items))

    vault_pages = _string_list(((l1_vault.get("wiki") or {}).get("page_paths")))
    lines.extend(_render_bullet_block("Persisted L1 Vault Pages", vault_pages))
    lines.append("\\subsection*{Role Of L1 In This Notebook}")
    lines.extend(
        _render_plain_paragraph(
            "L1 is compiled here as a source-provenance and intake-analysis layer: it records which sources were read, "
            "how deeply they were checked, and where notation or contradiction risks remain. The detailed derivation "
            "body for this topic belongs to L3."
        )
    )
    return lines


def _render_derivation_section(run_records: list[dict[str, Any]]) -> list[str]:
    derivation_rows = [
        (record["run_id"], row)
        for record in run_records
        for row in (record.get("derivation_rows") or [])
    ]
    if not derivation_rows:
        return []

    lines = ["\\section{Derivation Notebook}", ""]
    lines.extend(
        _render_plain_paragraph(
            "This section is the human-facing derivation body of the topic. Source provenance remains explicit, but the step-by-step "
            "reconstruction, candidate derivation, and failed derivation attempts all live here in L3."
        )
    )
    for run_id, row in derivation_rows:
        title = _summarize_scalar(row.get("title") or row.get("derivation_id") or "Derivation")
        lines.append(f"\\subsection*{{{_esc(title)}}}")
        lines.append("")
        lines.extend(
            _render_meta_badge_line(
                [
                    ("Run", run_id),
                    ("Kind", _summarize_scalar(row.get("derivation_kind"))),
                ],
                status=_summarize_scalar(row.get("status")),
            )
        )
        lines.extend(_render_body_paragraphs(_summarize_scalar(row.get("body"))))

        provenance_note = _summarize_scalar(row.get("provenance_note"))
        if provenance_note:
            lines.extend(
                _render_named_box(
                    "Provenance Note",
                    [],
                    body=_render_plain_paragraph(provenance_note),
                )
            )

        assumptions = _string_list(row.get("assumptions"))
        if assumptions:
            lines.extend(_render_bullet_block("Assumptions", assumptions))

        source_refs = _string_list(row.get("source_refs"))
        if source_refs:
            lines.extend(_render_bullet_block("Source Refs", source_refs))

        derivation_id = _summarize_scalar(row.get("derivation_id"))
        if derivation_id:
            lines.append("{\\footnotesize\\color{muted}\\texttt{derivation id: " + _esc(derivation_id) + "}}")
            lines.append("")
    return lines


def _render_comparison_section(run_records: list[dict[str, Any]]) -> list[str]:
    comparison_rows = [
        (record["run_id"], row)
        for record in run_records
        for row in (record.get("comparison_rows") or [])
    ]
    if not comparison_rows:
        return []

    lines = ["\\section{L2 Comparison Receipts}", ""]
    lines.extend(
        _render_plain_paragraph(
            "Every derivation-heavy candidate must carry an explicit comparison receipt against nearby L2 knowledge before it can be treated as promotion-ready. "
            "These receipts record what was compared, how far the comparison went, and which limitations still force a narrower L3 route or a return to source recovery."
        )
    )
    for run_id, row in comparison_rows:
        title = _summarize_scalar(row.get("title") or row.get("comparison_id") or "Comparison")
        body: list[str] = []
        summary = _summarize_scalar(row.get("comparison_summary"))
        if summary:
            body.extend(_render_plain_paragraph(summary))
        lines.extend(
            _render_named_box(
                title,
                [
                    ("Run", run_id),
                    ("Candidate Ref", _summarize_scalar(row.get("candidate_ref_id"))),
                    ("Comparison Scope", _summarize_scalar(row.get("comparison_scope"))),
                    ("Outcome", _summarize_scalar(row.get("outcome"))),
                ],
                body=body,
            )
        )

        compared_unit_ids = _string_list(row.get("compared_unit_ids"))
        if compared_unit_ids:
            lines.extend(_render_bullet_block("Compared L2 Units", compared_unit_ids))

        limitations = _string_list(row.get("limitations"))
        if limitations:
            lines.extend(_render_bullet_block("Limitations", limitations))

        comparison_id = _summarize_scalar(row.get("comparison_id"))
        if comparison_id:
            lines.append("{\\footnotesize\\color{muted}\\texttt{comparison id: " + _esc(comparison_id) + "}}")
            lines.append("")
    return lines


def _render_run_iteration_section(l3_root: Path, run_records: list[dict[str, Any]]) -> list[str]:
    if not run_records:
        return []

    lines = ["\\section{Run And Iteration Record}", ""]
    for record in run_records:
        journal = record.get("iteration_journal") or {}
        lines.extend(
            _render_named_box(
                f"Run {record['run_id']}",
                [
                    ("Candidates", str(len(record.get("candidate_rows") or []))),
                    ("Derivations", str(len(record.get("derivation_rows") or []))),
                    ("Strategy Rows", str(len(record.get("strategy_rows") or []))),
                    ("Run Status", _summarize_scalar(journal.get("status"))),
                    ("Current Iteration", _summarize_scalar(journal.get("current_iteration_id"))),
                    ("Latest Conclusion", _summarize_scalar(journal.get("latest_conclusion_status"))),
                    ("Staging Decision", _summarize_scalar(journal.get("latest_staging_decision"))),
                ],
            )
        )
    return lines


def _render_candidate_catalog_section(run_records: list[dict[str, Any]]) -> list[str]:
    candidate_rows = [
        (record["run_id"], row)
        for record in run_records
        for row in (record.get("candidate_rows") or [])
    ]
    if not candidate_rows:
        return []

    lines = ["\\section{Candidate Catalog}", ""]
    for run_id, row in candidate_rows:
        title = _summarize_scalar(row.get("title") or row.get("candidate_id") or "Candidate")
        body: list[str] = []
        body.extend(_render_plain_paragraph(_summarize_scalar(row.get("summary"))))
        question = _summarize_scalar(row.get("question"))
        if question:
            body.append("{\\small\\bfseries\\color{ink} Adjudication Question}\\par")
            body.extend(_render_plain_paragraph(question))
        assumptions = _string_list(row.get("assumptions"))
        if assumptions:
            body.append("{\\small\\bfseries\\color{ink} Working Assumptions}\\par")
            body.append("\\begin{itemize}")
            for item in assumptions:
                body.append(f"  \\item {_esc_latex_body(item)}")
            body.append("\\end{itemize}")
            body.append("")
        lines.extend(
            _render_named_box(
                title,
                [
                    ("Run", run_id),
                    ("Candidate Type", _summarize_scalar(row.get("candidate_type") or row.get("claim_type"))),
                    ("Status", _summarize_scalar(row.get("status"))),
                    ("Validation Route", _summarize_scalar(row.get("proposed_validation_route"))),
                    ("Intended L2 Targets", _summarize_scalar(row.get("intended_l2_targets"))),
                ],
                body=body,
            )
        )
        candidate_id = _summarize_scalar(row.get("candidate_id"))
        if candidate_id:
            lines.append("{\\footnotesize\\color{muted}\\texttt{candidate id: " + _esc(candidate_id) + "}}")
            lines.append("")
    return lines


def _render_strategy_section(run_records: list[dict[str, Any]]) -> list[str]:
    strategy_rows = [
        (record["run_id"], row)
        for record in run_records
        for row in (record.get("strategy_rows") or [])
    ]
    if not strategy_rows:
        return []

    lines = ["\\section{Strategy And Failure Memory}", ""]
    for run_id, row in strategy_rows:
        summary = _summarize_scalar(row.get("summary") or row.get("strategy_id") or "Strategy")
        body: list[str] = []
        notes = _string_list(row.get("reuse_conditions"))
        if notes:
            body.append("{\\small\\bfseries\\color{ink} Reuse Conditions}\\par")
            body.append("\\begin{itemize}")
            for item in notes:
                body.append(f"  \\item {_esc_latex_body(item)}")
            body.append("\\end{itemize}")
            body.append("")
        exclusions = _string_list(row.get("do_not_apply_when"))
        if exclusions:
            body.append("{\\small\\bfseries\\color{ink} Do Not Apply When}\\par")
            body.append("\\begin{itemize}")
            for item in exclusions:
                body.append(f"  \\item {_esc_latex_body(item)}")
            body.append("\\end{itemize}")
            body.append("")
        lines.extend(
            _render_named_box(
                summary,
                [
                    ("Run", run_id),
                    ("Strategy Type", _summarize_scalar(row.get("strategy_type"))),
                    ("Outcome", _summarize_scalar(row.get("outcome"))),
                    ("Confidence", _summarize_scalar(row.get("confidence"))),
                ],
                body=body,
            )
        )
    return lines


def _render_open_problems_section(l3_root: Path, run_records: list[dict[str, Any]]) -> list[str]:
    topic_paths = _topic_paths(l3_root)
    research_contract = _read_json(topic_paths["research_contract"]) or {}
    unfinished_work = _read_json(topic_paths["unfinished_work"]) or {}
    items: list[str] = []

    items.extend(_string_list(research_contract.get("open_ambiguities")))

    unfinished_rows = _dict_list(
        unfinished_work.get("items")
        or unfinished_work.get("entries")
        or unfinished_work.get("work_items")
    )
    for row in unfinished_rows:
        summary = _summarize_scalar(row.get("summary") or row.get("title") or row.get("question"))
        status = _summarize_scalar(row.get("status"))
        if summary:
            items.append(f"{summary} [{status or 'status unspecified'}]")

    for record in run_records:
        for row in record.get("candidate_rows") or []:
            blockers = _string_list(row.get("promotion_blockers"))
            for blocker in blockers:
                items.append(f"{row.get('candidate_id') or 'candidate'} blocker: {blocker}")

    if not items:
        return []

    lines = ["\\section{Open Problems And Deferred Fragments}", ""]
    lines.extend(_render_bullet_block("Active Open Items", items))
    return lines


def _render_topic_archive_sections(l3_root: Path) -> list[str]:
    run_records = _collect_run_records(l3_root)
    lines: list[str] = []
    for block in (
        _render_research_framing_section(l3_root),
        _render_source_provenance_section(l3_root),
        _render_derivation_section(run_records),
        _render_comparison_section(run_records),
        _render_run_iteration_section(l3_root, run_records),
        _render_open_problems_section(l3_root, run_records),
    ):
        if block:
            lines.extend(block)
    return lines


_PREAMBLE = r"""\documentclass[11pt,a4paper]{article}
\usepackage[UTF8]{ctex}
\usepackage{amsmath,amssymb,amsthm}
\usepackage{booktabs}
\usepackage{enumitem}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage[margin=2.3cm,headheight=16pt,headsep=0.75cm,footskip=1.1cm]{geometry}
\usepackage[most]{tcolorbox}
\usepackage{tabularx}
\usepackage{array}
\usepackage{xcolor}
\usepackage{fancyhdr}
\usepackage{lastpage}
\usepackage{longtable}
\usepackage{titlesec}
\usepackage{needspace}

\hypersetup{
  colorlinks=true,
  linkcolor=black,
  urlcolor=black,
  pdftitle={AITP Research Notebook - TOPIC_SLUG_PLACEHOLDER}
}

\setlength{\parindent}{0pt}
\setlength{\parskip}{0.55em}
\renewcommand{\arraystretch}{1.15}
\setlist[itemize]{leftmargin=1.8em}
\setlist[description]{style=nextline,leftmargin=1.8em,labelsep=0.6em}

\definecolor{ink}{RGB}{32,38,46}
\definecolor{muted}{RGB}{93,103,118}
\definecolor{linecolor}{RGB}{216,222,230}
\definecolor{softfill}{RGB}{247,249,252}

\definecolor{candidateframe}{RGB}{32,88,146}
\definecolor{candidateback}{RGB}{242,247,253}
\definecolor{strategyframe}{RGB}{120,82,38}
\definecolor{strategyback}{RGB}{250,246,239}
\definecolor{autoframe}{RGB}{86,93,113}
\definecolor{autoback}{RGB}{244,246,249}
\definecolor{journalframe}{RGB}{60,115,88}
\definecolor{journalback}{RGB}{242,248,244}
\definecolor{loopframe}{RGB}{140,54,104}
\definecolor{loopback}{RGB}{250,242,248}

\definecolor{resultcolor}{RGB}{28,115,76}
\definecolor{resultback}{RGB}{236,247,241}
\definecolor{warncolor}{RGB}{176,105,24}
\definecolor{warnback}{RGB}{252,244,233}
\definecolor{failcolor}{RGB}{176,54,54}
\definecolor{failback}{RGB}{252,238,238}

\newcommand{\result}[1]{\textcolor{resultcolor}{#1}}
\newcommand{\warn}[1]{\textcolor{warncolor}{#1}}
\newcommand{\fail}[1]{\textcolor{failcolor}{#1}}

\newtcbox{\entrytag}{on line,boxsep=0.45mm,left=1.1mm,right=1.1mm,top=0.3mm,bottom=0.3mm,
  colback=white,colframe=linecolor,boxrule=0.4pt,arc=0.9mm,
  fontupper=\ttfamily\scriptsize\color{muted}}

\newtcbox{\metabox}{on line,boxsep=0.55mm,left=1.2mm,right=1.2mm,top=0.45mm,bottom=0.45mm,
  colback=white,colframe=linecolor,boxrule=0.4pt,arc=1.0mm}

\newcommand{\metaitem}[2]{\metabox{\textcolor{muted}{\scriptsize\textsf{#1}}\hspace{0.45em}\texttt{\scriptsize #2}}}

\newcommand{\kindpill}[2]{\tcbox[on line,boxsep=0.6mm,left=1.4mm,right=1.4mm,top=0.45mm,bottom=0.45mm,
  colback=#1,colframe=#1,boxrule=0pt,arc=1.2mm]{\textcolor{white}{\textsf{\scriptsize\bfseries #2}}}}

\newcommand{\statusgood}[1]{\tcbox[on line,boxsep=0.6mm,left=1.4mm,right=1.4mm,top=0.45mm,bottom=0.45mm,
  colback=resultback,colframe=resultcolor,boxrule=0.45pt,arc=1.2mm]{\textcolor{resultcolor}{\textsf{\scriptsize\bfseries Status: #1}}}}

\newcommand{\statuswarn}[1]{\tcbox[on line,boxsep=0.6mm,left=1.4mm,right=1.4mm,top=0.45mm,bottom=0.45mm,
  colback=warnback,colframe=warncolor,boxrule=0.45pt,arc=1.2mm]{\textcolor{warncolor}{\textsf{\scriptsize\bfseries Status: #1}}}}

\newcommand{\statusfail}[1]{\tcbox[on line,boxsep=0.6mm,left=1.4mm,right=1.4mm,top=0.45mm,bottom=0.45mm,
  colback=failback,colframe=failcolor,boxrule=0.45pt,arc=1.2mm]{\textcolor{failcolor}{\textsf{\scriptsize\bfseries Status: #1}}}}

\titleformat{\section}
  {\Large\bfseries\color{ink}}
  {}
  {0pt}
  {}

\titlespacing*{\section}{0pt}{2.0em}{0.75em}

\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\textsf{AITP Research Notebook}}
\fancyhead[R]{\small\nouppercase{\leftmark}}
\fancyfoot[L]{\small\textsf{TOPIC_SLUG_PLACEHOLDER}}
\fancyfoot[R]{\small\textsf{Page \thepage\ of \pageref*{LastPage}}}
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\footrulewidth}{0pt}

\title{AITP Research Notebook\\[0.5em]
\large Topic: TOPIC_SLUG_PLACEHOLDER}
\author{AITP Kernel}
\date{Generated: DATE_PLACEHOLDER}

\begin{document}
\begin{titlepage}
\thispagestyle{empty}
\vspace*{0.12\textheight}

{\Huge\bfseries\color{ink} AITP Research Notebook\par}
\vspace{0.8em}
{\Large\color{muted} Topic: TOPIC_SLUG_PLACEHOLDER\par}
\vspace{1.8em}

\begin{tcolorbox}[
  enhanced,
  width=0.92\textwidth,
  colback=softfill,
  colframe=linecolor,
  boxrule=0.6pt,
  arc=1.5mm,
  left=2.5mm,
  right=2.5mm,
  top=2mm,
  bottom=2mm
]
\small\color{ink}
This notebook is rebuilt from the topic's durable research surfaces,
including runtime contracts, L1 provenance surfaces, L3 derivation and run
records, and the append-only event log used for audit replay.
\end{tcolorbox}

\vfill
{\large\color{ink} AITP Kernel\par}
\vspace{0.4em}
{\normalsize\color{muted} Generated: DATE_PLACEHOLDER\par}
\end{titlepage}

\tableofcontents
\clearpage
"""

_CLOSING = r"""
\end{document}
"""


def _topic_slug_from_l3(l3_root: Path) -> str:
    return l3_root.parent.name.replace("-", " ").title()


def _render_entry_at_level(entry: dict[str, Any], heading_level: str = "section") -> str:
    """Render one notebook entry as LaTeX."""
    kind_styles = {
        "candidate_update": {
            "label": "Candidate Update",
            "frame": "candidateframe",
            "back": "candidateback",
        },
        "strategy": {
            "label": "Strategy Record",
            "frame": "strategyframe",
            "back": "strategyback",
        },
        "auto_action": {
            "label": "Automated Action",
            "frame": "autoframe",
            "back": "autoback",
        },
        "iteration_journal": {
            "label": "Iteration Journal",
            "frame": "journalframe",
            "back": "journalback",
        },
        "derivation_note": {
            "label": "Derivation Note",
            "frame": "loopframe",
            "back": "loopback",
        },
        "comparison_note": {
            "label": "L2 Comparison",
            "frame": "candidateframe",
            "back": "candidateback",
        },
        "closed_loop_result": {
            "label": "Closed-Loop Result",
            "frame": "loopframe",
            "back": "loopback",
        },
    }
    kind = str(entry.get("kind") or "note").strip()
    timestamp = str(entry.get("timestamp") or "").strip()
    run_id = str(entry.get("run_id") or "").strip()
    style = kind_styles.get(
        kind,
        {
            "label": kind.replace("_", " ").title() or "Notebook Entry",
            "frame": "autoframe",
            "back": "softfill",
        },
    )
    kind_label = str(style["label"])
    raw_title = str(entry.get("title") or "").strip()
    section_title = raw_title or kind_label
    if section_title != kind_label:
        section_title = f"{kind_label}: {section_title}"
    title = _esc(section_title)
    body = str(entry.get("body") or "").strip()
    status = str(entry.get("status") or "").strip()
    details = entry.get("details") or {}

    lines: list[str] = []
    lines.append("\\needspace{12\\baselineskip}")
    lines.append(f"\\{heading_level}{{{title}}}")
    lines.append("")
    lines.append(
        "\\begin{tcolorbox}["
        "enhanced,"
        "breakable,"
        f"colback={style['back']},"
        f"colframe={style['frame']},"
        "boxrule=0.7pt,"
        "arc=1.5mm,"
        "left=1.6mm,"
        "right=1.6mm,"
        "top=1.4mm,"
        "bottom=1.4mm,"
        "before skip=0.25em,"
        "after skip=1.1em,"
        f"borderline west={{2.5mm}}{{0pt}}{{{style['frame']}}}"
        "]"
    )
    header_parts = [
        f"\\kindpill{{{style['frame']}}}{{{_esc(kind_label)}}}",
        f"\\entrytag{{{_esc(kind)}}}",
    ]

    if timestamp:
        header_parts.append(f"\\metaitem{{Time}}{{{_esc(timestamp)}}}")
    if run_id:
        header_parts.append(f"\\metaitem{{Run}}{{{_esc(run_id)}}}")
    if status:
        if status in ("success", "completed", "promoted", "approved"):
            header_parts.append(f"\\statusgood{{{_esc(status)}}}")
        elif status in ("failed", "error", "rejected", "discarded"):
            header_parts.append(f"\\statusfail{{{_esc(status)}}}")
        else:
            header_parts.append(f"\\statuswarn{{{_esc(status)}}}")

    lines.append("\\noindent " + " \\hspace{0.45em} ".join(header_parts) + r"\par")
    lines.append("")

    if body:
        for paragraph in body.split("\n\n"):
            paragraph = paragraph.strip()
            if not paragraph:
                lines.append("")
                continue
            lines.append(_esc_latex_body(paragraph))
            lines.append("")

    if details:
        lines.append("\\begin{tcolorbox}[enhanced,breakable,colback=white,colframe=linecolor,boxrule=0.4pt,arc=1.0mm,left=1.1mm,right=1.1mm,top=0.9mm,bottom=0.9mm]")
        lines.append("{\\small\\bfseries\\color{ink} Structured Details}\\par\\medskip")
        lines.append(
            "\\begin{tabularx}{\\linewidth}{@{}>{\\raggedright\\arraybackslash\\ttfamily\\footnotesize\\color{muted}}p{0.28\\linewidth}>{\\raggedright\\arraybackslash}X@{}}"
        )
        lines.append("\\toprule")
        lines.append("\\textnormal{Field} & \\textnormal{Value} \\\\")
        lines.append("\\midrule")
        for key, val in details.items():
            if isinstance(val, (list, dict)):
                try:
                    val_str = json.dumps(val, ensure_ascii=False, separators=(", ", ": "))
                except TypeError:
                    val_str = str(val)
            else:
                val_str = str(val)
            if len(val_str) > 400:
                val_str = val_str[:400].rstrip() + "..."
            val_tex = _esc_latex_body(val_str).replace(" \\\\\n", r"\newline ")
            lines.append(f"{_esc(key)} & {val_tex} \\\\")
        lines.append("\\bottomrule")
        lines.append("\\end{tabularx}")
        lines.append("\\end{tcolorbox}")
        lines.append("")

    lines.append("\\end{tcolorbox}")
    lines.append("")
    return "\n".join(lines)


def _render_entry(entry: dict[str, Any]) -> str:
    return _render_entry_at_level(entry, "section")


def _esc_latex_body(text: str) -> str:
    """Escape plain text for LaTeX body, but preserve $$...$$ and $...$ math."""
    parts = re.split(r"(\$\$.*?\$\$|\$[^$\n]+?\$)", text, flags=re.DOTALL)
    result = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            result.append(part)
        else:
            escaped = _esc(part)
            escaped = escaped.replace("\n", " \\\\\n")
            result.append(escaped)
    return "".join(result)


def append_notebook_entry(
    l3_root: Path,
    *,
    kind: str,
    title: str,
    body: str = "",
    status: str = "",
    run_id: str = "",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append one entry and rebuild the LaTeX file."""
    paths = _notebook_paths(l3_root)
    paths["entries"].parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": _now_iso(),
        "kind": str(kind or "note").strip(),
        "title": str(title or "").strip(),
        "body": str(body or "").strip(),
        "status": str(status or "").strip(),
        "run_id": str(run_id or "").strip(),
        "details": details or {},
    }

    # Persist entry to JSONL (source of truth for rebuilds)
    entries_file = paths["entries"]
    with open(entries_file, "a", encoding="utf-8") as f:
        f.write(_json_one_line(entry) + "\n")

    _rebuild_latex(l3_root, paths)

    return {
        "notebook_tex": str(paths["tex"]),
        "entry_count": _count_entries(entries_file),
    }


def _json_one_line(obj: dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def _count_entries(entries_file: Path) -> int:
    if not entries_file.exists():
        return 0
    return sum(1 for line in entries_file.read_text(encoding="utf-8").strip().split("\n") if line.strip())


def _rebuild_latex(l3_root: Path, paths: dict[str, Path]) -> None:
    """Rebuild the full .tex from all entries."""
    entries_file = paths["entries"]

    entries: list[dict[str, Any]] = []
    if entries_file.exists():
        for line in entries_file.read_text(encoding="utf-8").strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    slug_display = _topic_slug_from_l3(l3_root)
    preamble = _PREAMBLE.replace("TOPIC_SLUG_PLACEHOLDER", _esc(slug_display))
    preamble = preamble.replace("DATE_PLACEHOLDER", _esc(_now_iso()))

    run_records = _collect_run_records(l3_root)
    body_parts = []
    for block in (
        _render_research_framing_section(l3_root),
        _render_source_provenance_section(l3_root),
        _render_derivation_section(run_records),
        _render_comparison_section(run_records),
        _render_run_iteration_section(l3_root, run_records),
        _render_open_problems_section(l3_root, run_records),
    ):
        if block:
            body_parts.extend(block)
    appendix_sections: list[str] = []
    for block in (
        _render_candidate_catalog_section(run_records),
        _render_strategy_section(run_records),
    ):
        if block:
            appendix_sections.extend(block)

    body_parts.append("\\appendix")
    body_parts.append("")
    body_parts.extend(appendix_sections)
    body_parts.append("\\section{Chronological Entry Log}")
    body_parts.append("")
    for entry in entries:
        body_parts.append(_render_entry_at_level(entry, "subsection*"))
    if not entries:
        body_parts.extend(_render_plain_paragraph("No notebook events have been recorded for this topic yet."))

    full_tex = preamble + "\n".join(body_parts) + _CLOSING
    paths["tex"].write_text(full_tex, encoding="utf-8")


def compile_notebook(l3_root: Path) -> dict[str, Any]:
    """Compile the LaTeX file to PDF."""
    paths = _notebook_paths(l3_root)
    _rebuild_latex(l3_root, paths)
    tex_path = paths["tex"]

    if not tex_path.exists():
        return {"compiled": False, "reason": "no .tex file"}

    xelatex = shutil.which("xelatex")
    if xelatex is None:
        return {"compiled": False, "reason": "xelatex not found on PATH"}

    work_dir = l3_root
    result: subprocess.CompletedProcess[str] | None = None
    for _ in range(2):
        result = subprocess.run(
            [xelatex, "-interaction=nonstopmode",
             "-output-directory", str(work_dir), tex_path.name],
            capture_output=True,
            text=True,
            cwd=str(work_dir),
            timeout=120,
        )

    pdf_exists = paths["pdf"].exists()
    # Clean auxiliary files
    for key in ("aux", "log", "out"):
        p = paths.get(key)
        if p and p.exists():
            try:
                p.unlink()
            except OSError:
                pass

    return {
        "compiled": pdf_exists,
        "returncode": result.returncode if result is not None else 1,
        "pdf_path": str(paths["pdf"]) if pdf_exists else None,
    }


def append_and_compile(
    l3_root: Path,
    *,
    kind: str,
    title: str,
    body: str = "",
    status: str = "",
    run_id: str = "",
    details: dict[str, Any] | None = None,
    compile: bool = True,
) -> dict[str, Any]:
    """Append an entry and optionally compile to PDF."""
    append_result = append_notebook_entry(
        l3_root,
        kind=kind,
        title=title,
        body=body,
        status=status,
        run_id=run_id,
        details=details,
    )
    compile_result: dict[str, Any] = {"compiled": False, "skipped": True}
    if compile:
        compile_result = compile_notebook(l3_root)

    return {
        **append_result,
        "compile": compile_result,
    }
