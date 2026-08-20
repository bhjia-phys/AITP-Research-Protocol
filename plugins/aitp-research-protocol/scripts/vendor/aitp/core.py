"""Stable public API for the AITP Evidence Ledger."""

from __future__ import annotations

from .backfill import backfill_workspace
from .md import AITPError, atomic_write, parse_markdown, render_markdown
from .notes import prepare_note, save_note
from .diagnostics import check_workspace
from .query import list_workspace, show_entry
from .records import prepare_entry, save_entry
from .state import enter_workspace
from .workspace import (
    adopt_workspace, build_inventory, init_workspace, resolve_root,
)

__all__ = [
    "AITPError",
    "adopt_workspace",
    "atomic_write",
    "backfill_workspace",
    "build_inventory",
    "check_workspace",
    "enter_workspace",
    "init_workspace",
    "list_workspace",
    "parse_markdown",
    "prepare_entry",
    "prepare_note",
    "render_markdown",
    "save_entry",
    "save_note",
    "show_entry",
]
