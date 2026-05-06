"""Tests for md_body_to_latex() — Markdown to LaTeX staged pipeline converter."""
import pytest
from brain.flow_notebook.converter import md_body_to_latex


class TestMathPreservation:
    def test_inline_math_passthrough(self):
        result = md_body_to_latex("Energy $E_g = 1.12$ eV")
        assert "$E_g = 1.12$" in result

    def test_display_math_to_bracket(self):
        result = md_body_to_latex("$$\nE = mc^2\n$$")
        assert r"\[" in result
        assert r"\]" in result
        assert "E = mc^2" in result

    def test_math_underscores_not_escaped(self):
        result = md_body_to_latex(r"$v_{mn}^{\alpha}$")
        assert "$" in result

    def test_math_inside_table_cell(self):
        md = "| Formula | Value |\n|---------|-------|\n| $E=mc^2$ | 1 |\n"
        result = md_body_to_latex(md)
        assert "$E=mc^2$" in result


class TestCodeBlocks:
    def test_fenced_to_lstlisting(self):
        md = "```cpp\nint main() { return 0; }\n```"
        result = md_body_to_latex(md)
        assert r"\begin{lstlisting}" in result
        assert "int main()" in result
        assert r"\end{lstlisting}" in result

    def test_code_block_with_language(self):
        md = "```python\nprint('hello')\n```"
        result = md_body_to_latex(md)
        assert "language=Python" in result or "Python" in result

    def test_code_block_contains_dollars(self):
        md = "```c\nint x = $foo;\n```"
        result = md_body_to_latex(md)
        assert r"\begin{lstlisting}" in result


class TestTables:
    def test_simple_table(self):
        md = "| A | B | C |\n|---|---|---|\n| 1 | 2 | 3 |\n"
        result = md_body_to_latex(md)
        assert r"\begin{tabular}" in result
        assert r"\toprule" in result
        assert "A & B & C" in result
        assert "1 & 2 & 3" in result
        assert r"\bottomrule" in result

    def test_table_alignment(self):
        md = "| L | C | R |\n|:---|---:|:---:|\n| a | b | c |\n"
        result = md_body_to_latex(md)
        assert "{" in result  # alignment spec present

    def test_table_in_body_with_other_text(self):
        md = "Some text\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\nMore text"
        result = md_body_to_latex(md)
        assert r"\begin{tabular}" in result
        assert "Some text" in result
        assert "More text" in result


class TestHeadings:
    def test_h1_to_subsection(self):
        assert r"\subsection*{Title}" in md_body_to_latex("# Title")

    def test_h2_to_subsubsection(self):
        assert r"\subsubsection*{Title}" in md_body_to_latex("## Title")

    def test_h3_to_paragraph(self):
        assert r"\paragraph*{Title}" in md_body_to_latex("### Title")

    def test_h4_to_subparagraph(self):
        assert r"\subparagraph*{Title}" in md_body_to_latex("#### Title")


class TestLists:
    def test_bullet_list(self):
        result = md_body_to_latex("- a\n- b\n- c\n")
        assert r"\begin{itemize}" in result
        assert r"\item a" in result
        assert r"\end{itemize}" in result

    def test_enumerated_list(self):
        result = md_body_to_latex("1. first\n2. second\n")
        assert r"\begin{enumerate}" in result
        assert r"\item first" in result
        assert r"\end{enumerate}" in result

    def test_asterisk_bullet_list(self):
        result = md_body_to_latex("* item1\n* item2\n")
        assert r"\begin{itemize}" in result
        assert r"\item item1" in result


class TestInlineFormatting:
    def test_bold(self):
        assert r"\textbf{bold}" in md_body_to_latex("**bold**")

    def test_italic(self):
        result = md_body_to_latex("*italic* and **bold**")
        assert r"\textit{italic}" in result
        assert r"\textbf{bold}" in result

    def test_link(self):
        result = md_body_to_latex("[text](https://x.com)")
        assert r"\href{https://x.com}{text}" in result


class TestEdgeCases:
    def test_empty_input(self):
        assert md_body_to_latex("") == ""
        assert md_body_to_latex("   ") == ""

    def test_plain_text_passthrough(self):
        result = md_body_to_latex("Just some plain text.")
        assert "Just some plain text." in result
        assert r"\begin{verbatim}" not in result

    def test_no_verbatim_wrapping(self):
        result = md_body_to_latex("## Hello\n\nSome **bold** text.")
        assert r"\begin{verbatim}" not in result
        assert r"\end{verbatim}" not in result
        assert r"\subsubsection*{Hello}" in result

    def test_unicode_greek(self):
        result = md_body_to_latex("α particle = 5.0")
        assert r"$\alpha$" in result

    def test_mixed_complex(self):
        md = (
            "## Results\n\n"
            "The gap $E_g$:\n\n"
            "| k-grid | $E_g$ (eV) |\n"
            "|--------|------------|\n"
            "| 4x4x4  | 1.12       |\n\n"
            "- **Finding**: head-wing *improves* convergence.\n"
            "- `option=3` is sufficient.\n"
        )
        result = md_body_to_latex(md)
        assert r"\subsubsection*{Results}" in result
        assert r"\begin{tabular}" in result
        assert r"\begin{itemize}" in result
