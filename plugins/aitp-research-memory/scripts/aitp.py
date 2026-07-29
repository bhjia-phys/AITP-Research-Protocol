#!/usr/bin/env python3
"""Run the AITP Lite CLI bundled with the Codex plugin."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    if sys.version_info < (3, 11):
        print("AITP requires Python 3.11 or newer.", file=sys.stderr)
        return 2
    vendor = Path(__file__).resolve().parent / "vendor"
    sys.path.insert(0, str(vendor))
    from aitp.cli import main as cli_main

    return cli_main()


if __name__ == "__main__":
    raise SystemExit(main())
