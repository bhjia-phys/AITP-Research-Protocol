#!/usr/bin/env python3
"""Compatibility wrapper for the new Layer 0 arXiv registration helper."""

from __future__ import annotations

import runpy
from pathlib import Path


if __name__ == "__main__":
    target = (
        Path(__file__).resolve().parents[2]
        / "source-layer"
        / "scripts"
        / "register_arxiv_source.py"
    )
    runpy.run_path(str(target), run_name="__main__")
