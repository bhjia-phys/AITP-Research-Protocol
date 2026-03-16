from __future__ import annotations

import sys

from .aitp_codex import main as aitp_codex_main


def main() -> int:
    return aitp_codex_main(["--preset", "hs", *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
