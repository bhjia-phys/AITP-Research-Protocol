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
    text = _protect_math_spans(text, tokens)   # before tables — tokens absorb | inside math
    text = _convert_tables(text, tokens)        # tables → LaTeX tabular, tokenized
    text = _convert_headings(text)
    text = _convert_lists(text)
    text = _convert_inline_formatting(text)
    text = _escape_stray_specials(text)
    text = _restore_tokens(text, tokens)

    return text


# ── Code block protection ───────────────────────────────────────────────

_LISTINGS_LANG_MAP = {
    "cpp": "C++", "c++": "C++", "c": "C", "python": "Python", "py": "Python",
    "bash": "bash", "sh": "bash", "shell": "bash",
    "java": "Java", "javascript": "JavaScript", "js": "JavaScript",
    "rust": "Rust", "go": "Go", "fortran": "Fortran",
    "latex": "TeX", "tex": "TeX", "makefile": "make",
}


def _normalize_listings_lang(lang: str) -> str:
    """Normalize language tag for listings package."""
    if not lang:
        return ""
    lang_lower = lang.lower().strip()
    return _LISTINGS_LANG_MAP.get(lang_lower, lang_lower)


def _protect_code_blocks(text: str, tokens: dict[str, str]) -> str:
    pattern = re.compile(r'```(\w*)\n(.*?)```', re.DOTALL)

    def _replace(m):
        lang = _normalize_listings_lang(m.group(1) or "")
        code = m.group(2)
        tok = _next_token()
        lang_opt = f"[language={lang}]" if lang else ""
        tokens[tok] = (
            r"\begin{lstlisting}" + lang_opt + "\n"
            + code + "\n"
            + r"\end{lstlisting}"
        )
        return tok

    return pattern.sub(_replace, text)


# ── Table detection & conversion ────────────────────────────────────────

def _convert_tables(text: str, tokens: dict[str, str]) -> str:
    """Detect pipe tables and convert to LaTeX tabular with booktabs.

    Table output is tokenized to prevent later stages from escaping
    the & column separators inside tabular environments.
    """
    lines = text.split('\n')
    result: list[str] = []
    i = 0
    while i < len(lines):
        if i + 1 < len(lines) and _is_table_row(lines[i]) and _is_table_sep(lines[i + 1]):
            header = _protect_stray_pipes(lines[i])
            sep = lines[i + 1]
            body_rows: list[str] = []
            j = i + 2
            while j < len(lines) and _is_table_row(lines[j]):
                body_rows.append(_protect_stray_pipes(lines[j]))
                j += 1
            latex_table = _render_table(header, sep, body_rows)
            tok = _next_token()
            tokens[tok] = latex_table
            result.append(tok)
            i = j
        else:
            result.append(lines[i])
            i += 1
    return '\n'.join(result)


def _protect_stray_pipes(row: str) -> str:
    """Protect | between word chars (cell content) from splitting.

    $...$ math is already tokenized by this point, so only bare | between
    content characters needs protection.
    """
    row = re.sub(r'(?<=[a-zA-Z0-9\)\]>])\|(?=[a-zA-Z0-9\$\(\[<\-])', '\x00PIPE\x00', row)
    return row


def _is_table_row(line: str) -> bool:
    s = line.strip()
    return s.startswith('|') and s.endswith('|')


def _is_table_sep(line: str) -> bool:
    """Match separator row like |---|:---:|---:| with 2+ columns."""
    s = line.strip()
    return bool(re.match(r'^\|[\s\-:]+(\|[\s\-:]+)+\|\s*$', s))


def _render_table(header: str, sep: str, body: list[str]) -> str:
    cells_h = _split_table_row(header)
    cells_s = _split_table_row(sep)
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
        cells = _split_table_row(row)
        while len(cells) < ncols:
            cells.append("")
        out.append(" & ".join(_esc_table_cell(c) for c in cells[:ncols]) + r" \\")
    out.append(r"\bottomrule")
    out.append(r"\end{tabular}")
    return '\n'.join(out)


def _split_table_row(row: str) -> list[str]:
    """Split a markdown table row by | into cells.

    Stray | inside content has already been protected by _protect_stray_pipes
    (replaced with \\x00PIPE\\x00). We split on remaining | and restore.
    """
    s = row.strip()
    if s.startswith('|'):
        s = s[1:]
    if s.endswith('|'):
        s = s[:-1]

    cells = [c.strip() for c in s.split('|')]
    # Restore protected pipes (both from _protect_stray_pipes)
    cells = [c.replace('\x00PIPE\x00', '|') for c in cells]
    return cells


def _esc_table_cell(cell: str) -> str:
    """Escape a table cell for LaTeX.

    $...$ math spans are already tokenized by _protect_math_spans (runs
    before table conversion), so we just escape remaining TeX specials.
    """
    # Use placeholder tokens to avoid ordering issues between replacements
    cell = cell.replace('\\', '\x00BSLASH\x00')
    cell = cell.replace('{', '\x00LBRACE\x00')
    cell = cell.replace('}', '\x00RBRACE\x00')
    cell = cell.replace('&', '\x00AMP\x00')
    cell = cell.replace('%', '\x00PCNT\x00')
    cell = cell.replace('#', '\x00HASH\x00')
    cell = cell.replace('_', '\x00USCORE\x00')
    cell = cell.replace('^', '\x00CARET\x00')
    cell = cell.replace('~', '\x00TILDE\x00')
    cell = cell.replace('|', '\x00PIPE\x00')
    cell = cell.replace('\x00BSLASH\x00', r'\textbackslash{}')
    cell = cell.replace('\x00LBRACE\x00', r'\{')
    cell = cell.replace('\x00RBRACE\x00', r'\}')
    cell = cell.replace('\x00AMP\x00', r'\&')
    cell = cell.replace('\x00PCNT\x00', r'\%')
    cell = cell.replace('\x00HASH\x00', r'\#')
    cell = cell.replace('\x00USCORE\x00', r'\_')
    cell = cell.replace('\x00CARET\x00', r'\^{}')
    cell = cell.replace('\x00TILDE\x00', r'\textasciitilde{}')
    cell = cell.replace('\x00PIPE\x00', r'\textbar{}')
    return cell


# ── Math protection ─────────────────────────────────────────────────────

def _protect_math_spans(text: str, tokens: dict[str, str]) -> str:
    """Extract $$...$$ and $...$ spans, replace with tokens."""
    # $$...$$ (display math) → \[...\]
    # Only match $$ at line start or after whitespace to avoid conflating
    # consecutive inline spans like $x$$y$ (from _sanitize_unicode).
    pattern_display = re.compile(r'(?:^|(?<=\s))\$\$(.+?)\$\$', re.DOTALL | re.MULTILINE)

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
    """Convert # headings to LaTeX section commands (demoted by one level).

    H3/H4 use \\textbf{} with spacing instead of \\paragraph*/\\subparagraph*
    to avoid LaTeX errors when headings appear inside list environments.
    """
    text = re.sub(r'^#### (.+)$', r'\\medskip\\noindent\\textbf{\1}\\par', text, flags=re.MULTILINE)
    text = re.sub(r'^### (.+)$', r'\\medskip\\noindent\\textbf{\1}\\par', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'\\subsubsection{\1}', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'\\subsection{\1}', text, flags=re.MULTILINE)
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
    """Apply markdown inline formatting → LaTeX.

    Per-part processing (split by tokens). Bold/italic are matched within
    each part — Unicode math chars in the source add \$...\$ tokens that
    can split **...** across parts. For the common case of Greek letters
    inside bold (e.g., **C^{mn}_μ**), the _sanitize_unicode step uses
    \\textmu instead of \$\\mu\$ to avoid creating math tokens mid-bold.
    """
    parts = re.split(r'(\x00MDTOK\d{4}\x00)', text)
    for idx in range(len(parts)):
        if parts[idx].startswith('\x00MDTOK'):
            continue
        p = parts[idx]
        # Bold: **text** (DOTALL for multi-line)
        p = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', p, flags=re.DOTALL)
        # Italic: *text* (not **)
        p = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'\\textit{\1}', p, flags=re.DOTALL)
        # Inline code: `text`
        p = re.sub(
            r'`([^`]+)`',
            lambda m: r'\texttt{' + _esc_tex_special(m.group(1)) + '}',
            p,
        )
        # Links: [text](url)
        p = re.sub(
            r'\[(.+?)\]\((.+?)\)',
            lambda m: r'\href{' + m.group(2).replace('#', r'\#') + '}{' + m.group(1) + '}',
            p,
        )
        parts[idx] = p
    return ''.join(parts)


def _escape_stray_specials(text: str) -> str:
    """Escape remaining TeX specials in plain text after all formatting.

    Only escapes characters that are NOT already part of valid LaTeX commands
    (e.g., \# from \\texttt{} is already escaped by _esc_tex_special).
    Math spans and code blocks are already tokenized.
    """
    parts = re.split(r'(\x00MDTOK\d{4}\x00)', text)
    for idx in range(len(parts)):
        if parts[idx].startswith('\x00MDTOK'):
            continue
        p = parts[idx]
        # Escape ONLY if not preceded by \ (already part of \\_, \\^, \\#, etc.)
        p = re.sub(r'(?<!\\)_', r'\\_', p)
        p = re.sub(r'(?<!\\)\^', r'\\^{}', p)
        p = re.sub(r'(?<!\\)#', r'\\#', p)
        p = re.sub(r'(?<!\\)&', r'\\&', p)
        p = re.sub(r'(?<!\\)%', r'\\%', p)
        parts[idx] = p
    return ''.join(parts)


# ── Token restoration ───────────────────────────────────────────────────

def _restore_tokens(text: str, tokens: dict[str, str]) -> str:
    """Replace all tokens with their LaTeX content.

    Loops until all tokens are resolved (handles nested tokens where
    a table token wraps a math token).
    """
    for _ in range(len(tokens) + 1):
        changed = False
        for tok, latex in tokens.items():
            if tok in text:
                text = text.replace(tok, latex)
                changed = True
        if not changed:
            break
    return text
