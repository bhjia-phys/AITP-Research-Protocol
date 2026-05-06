"""AITP Flow Notebook — section-based, template-driven, incremental LaTeX builder."""
from brain.flow_notebook.builder import build_notebook, render_all_sections, generate_l1_index
from brain.flow_notebook.converter import md_body_to_latex
from brain.flow_notebook.section_map import SECTION_ORDER, SECTION_SOURCES
from brain.flow_notebook.utils import _esc, _sanitize_unicode, _parse_md
from brain.flow_notebook.hashing import compute_section_hash

__all__ = [
    "build_notebook", "render_all_sections", "md_body_to_latex",
    "SECTION_ORDER", "SECTION_SOURCES",
    "_esc", "_sanitize_unicode", "_parse_md", "compute_section_hash",
]
