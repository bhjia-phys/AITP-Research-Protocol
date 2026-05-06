"""Markdown body → LaTeX converter with staged regex pipeline.

Pipeline:
  0. Normalize Unicode, truncate if needed
  1. Protect fenced code blocks (may contain $ and |)
  2. Detect and convert markdown tables → LaTeX tabular (pipe rows still visible)
  3. Protect $...$ and $$...$$ math spans in remaining text
  4. Convert block elements: headings, lists
  5. Convert inline formatting: bold, italic, code, links
  6. Restore protected code/math tokens
"""
from __future__ import annotations

import re

from brain.flow_notebook.utils import _sanitize_unicode, _esc_tex_special

_TOKEN_ID = 0


def _next_token() -> str:
    global _TOKEN_ID
    _TOKEN_ID += 1
    return f"\x00MDTOK{_TOKEN_ID:04d}\x00"


def md_body_to_latex(md_text: str, max_chars: int = 8000) -> str:
    """Convert markdown body to LaTeX fragment.

    Handles: headings, bold, italic, inline code, fenced code blocks,
    markdown tables, bullet/enumerated lists, $...$ inline math,
    $$...$$ display math, links.
    """
    if not md_text or not md_text.strip():
        return ""

    text = _sanitize_unicode(md_text)
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n*(Content truncated — see source artifact.)*"

    tokens: dict[str, str] = {}

    text = _protect_code_blocks(text, tokens)
    text = _convert_tables(text)               # before math — pipe rows need visible |
    text = _protect_math_spans(text, tokens)
    text = _convert_headings(text)
    text = _convert_lists(text)
    text = _convert_inline_formatting(text)
    text = _restore_tokens(text, tokens)

    return text


# ── Code block protection ───────────────────────────────────────────────

def _protect_code_blocks(text: str, tokens: dict[str, str]) -> str:
    pattern = re.compile(r'```(\w*)\n(.*?)```', re.DOTALL)

    def _replace(m):
        lang = m.group(1) or "text"
        code = m.group(2)
        tok = _next_token()
        lang_opt = f"[language={lang.capitalize()}]" if lang != "text" else ""
        tokens[tok] = (
            r"\begin{lstlisting}" + lang_opt + "\n"
            + code + "\n"
            + r"\end{lstlisting}"
        )
        return tok

    return pattern.sub(_replace, text)


# ── Table detection & conversion ────────────────────────────────────────

def _convert_tables(text: str) -> str:
    """Detect pipe tables and convert to LaTeX tabular with booktabs."""
    lines = text.split('\n')
    result: list[str] = []
    i = 0
    while i < len(lines):
        if i + 1 < len(lines) and _is_table_row(lines[i]) and _is_table_sep(lines[i + 1]):
            header = lines[i]
            sep = lines[i + 1]
            body_rows: list[str] = []
            j = i + 2
            while j < len(lines) and _is_table_row(lines[j]):
                body_rows.append(lines[j])
                j += 1
            latex_table = _render_table(header, sep, body_rows)
            result.append(latex_table)
            i = j
        else:
            result.append(lines[i])
            i += 1
    return '\n'.join(result)


def _is_table_row(line: str) -> bool:
    s = line.strip()
    return s.startswith('|') and s.endswith('|')


def _is_table_sep(line: str) -> bool:
    """Match separator row like |---|:---:|---:| with 2+ columns."""
    s = line.strip()
    return bool(re.match(r'^\|[\s\-:]+(\|[\s\-:]+)+\|\s*$', s))


def _render_table(header: str, sep: str, body: list[str]) -> str:
    cells_h = [c.strip() for c in header.strip().strip('|').split('|')]
    cells_s = [c.strip() for c in sep.strip().strip('|').split('|')]
    ncols = len(cells_h)

    align = ""
    for c in cells_s:
        left = c.startswith(':')
        right = c.endswith(':')
        if left and right:
            align += 'c'
        elif right:
            align += 'r'
        else:
            align += 'l'

    out = [r"\begin{tabular}{" + align + "}"]
    out.append(r"\toprule")
    out.append(" & ".join(_esc_table_cell(c) for c in cells_h) + r" \\")
    out.append(r"\midrule")
    for row in body:
        cells = [c.strip() for c in row.strip().strip('|').split('|')]
        while len(cells) < ncols:
            cells.append("")
        out.append(" & ".join(_esc_table_cell(c) for c in cells[:ncols]) + r" \\")
    out.append(r"\bottomrule")
    out.append(r"\end{tabular}")
    return '\n'.join(out)


def _esc_table_cell(cell: str) -> str:
    """Escape a table cell for LaTeX, preserving $...$ math spans."""
    # Protect math spans first
    math_tokens: dict[str, str] = {}

    def _protect(m):
        tok = _next_token()
        math_tokens[tok] = m.group(0)
        return tok

    cell = re.sub(r'\$[^$]+\$', _protect, cell)
    cell = _esc_tex_special(cell)
    for tok, val in math_tokens.items():
        cell = cell.replace(tok, val)
    return cell


# ── Math protection ─────────────────────────────────────────────────────

def _protect_math_spans(text: str, tokens: dict[str, str]) -> str:
    """Extract $$...$$ and $...$ spans, replace with tokens."""
    # $$...$$ (display math) → \[...\]
    pattern_display = re.compile(r'\$\$(.+?)\$\$', re.DOTALL)

    def _replace_display(m):
        tok = _next_token()
        tokens[tok] = r"\[" + m.group(1).strip() + r"\]"
        return tok

    text = pattern_display.sub(_replace_display, text)

    # $...$ (inline math) — not preceded by \
    pattern_inline = re.compile(r'(?<!\\)\$([^$]+?)\$')

    def _replace_inline(m):
        tok = _next_token()
        tokens[tok] = "$" + m.group(1) + "$"
        return tok

    text = pattern_inline.sub(_replace_inline, text)
    return text


# ── Headings ────────────────────────────────────────────────────────────

def _convert_headings(text: str) -> str:
    text = re.sub(r'^#### (.+)$', r'\\subparagraph*{\1}', text, flags=re.MULTILINE)
    text = re.sub(r'^### (.+)$', r'\\paragraph*{\1}', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'\\subsubsection*{\1}', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'\\subsection*{\1}', text, flags=re.MULTILINE)
    return text


# ── Lists ───────────────────────────────────────────────────────────────

def _convert_lists(text: str) -> str:
    lines = text.split('\n')
    result: list[str] = []
    i = 0
    while i < len(lines):
        stripped = lines[i].lstrip()
        if re.match(r'^[-*+]\s', stripped):
            items = []
            while i < len(lines) and re.match(r'^[-*+]\s', lines[i].lstrip()):
                items.append(re.sub(r'^[-*+]\s+', '', lines[i].lstrip()))
                i += 1
            result.append(r"\begin{itemize}")
            for item in items:
                result.append(r"\item " + item)
            result.append(r"\end{itemize}")
        elif re.match(r'^\d+[.)]\s', stripped):
            items = []
            while i < len(lines) and re.match(r'^\d+[.)]\s', lines[i].lstrip()):
                items.append(re.sub(r'^\d+[.)]\s+', '', lines[i].lstrip()))
                i += 1
            result.append(r"\begin{enumerate}")
            for item in items:
                result.append(r"\item " + item)
            result.append(r"\end{enumerate}")
        else:
            result.append(lines[i])
            i += 1
    return '\n'.join(result)


# ── Inline formatting ───────────────────────────────────────────────────

def _convert_inline_formatting(text: str) -> str:
    parts = re.split(r'(\x00MDTOK\d{4}\x00)', text)
    for idx in range(len(parts)):
        if parts[idx].startswith('\x00MDTOK'):
            continue
        p = parts[idx]
        p = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', p)
        p = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'\\textit{\1}', p)
        p = re.sub(
            r'`([^`]+)`',
            lambda m: r'\texttt{' + _esc_tex_special(m.group(1)) + '}',
            p,
        )
        p = re.sub(r'\[(.+?)\]\((.+?)\)', r'\\href{\2}{\1}', p)
        parts[idx] = p
    return ''.join(parts)


# ── Token restoration ───────────────────────────────────────────────────

def _restore_tokens(text: str, tokens: dict[str, str]) -> str:
    for tok, latex in tokens.items():
        text = text.replace(tok, latex)
    return text
