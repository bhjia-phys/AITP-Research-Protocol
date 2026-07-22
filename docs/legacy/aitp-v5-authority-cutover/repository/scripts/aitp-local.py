from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILD_LIB = REPO_ROOT / "research" / "knowledge-hub" / "build" / "lib"


def main() -> int:
    try:
        from knowledge_hub import aitp_cli
    except ImportError:
        cli_path = BUILD_LIB / "knowledge_hub" / "aitp_cli.py"
        if not cli_path.exists():
            print(
                "[aitp-local] Missing AITP CLI entrypoint at "
                f"{cli_path}",
                file=sys.stderr,
            )
            print(
                "[aitp-local] Install `aitp-kernel` or regenerate the repo-local build/lib surface.",
                file=sys.stderr,
            )
            return 1
        sys.path.insert(0, str(BUILD_LIB))
        from knowledge_hub import aitp_cli

    sys.argv[0] = str(REPO_ROOT / "scripts" / "aitp-local.cmd")
    return int(aitp_cli.main())


if __name__ == "__main__":
    raise SystemExit(main())
