#!/usr/bin/env python3
"""Generate the workspace-level L2 hygiene report."""

from __future__ import annotations

import json
import sys
from pathlib import Path

KERNEL_ROOT = Path(__file__).resolve().parents[2]
if str(KERNEL_ROOT) not in sys.path:
    sys.path.insert(0, str(KERNEL_ROOT))

from knowledge_hub.l2_hygiene import materialize_workspace_hygiene_report


def main() -> int:
    result = materialize_workspace_hygiene_report(KERNEL_ROOT)
    summary = result["payload"].get("summary") or {}
    print(
        json.dumps(
            {
                "status": "success",
                "json_path": result["json_path"],
                "markdown_path": result["markdown_path"],
                "total_units": summary.get("total_units", 0),
                "total_findings": summary.get("total_findings", 0),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
