#!/usr/bin/env python3
"""Regenerate the first compiled L2 workspace memory map."""

from __future__ import annotations

import json
import sys
from pathlib import Path

KERNEL_ROOT = Path(__file__).resolve().parents[2]
if str(KERNEL_ROOT) not in sys.path:
    sys.path.insert(0, str(KERNEL_ROOT))

from knowledge_hub.l2_compiler import materialize_workspace_memory_map


def main() -> int:
    result = materialize_workspace_memory_map(KERNEL_ROOT)
    payload = result["payload"]
    summary = payload.get("summary") or {}
    print(
        json.dumps(
            {
                "status": "success",
                "json_path": result["json_path"],
                "markdown_path": result["markdown_path"],
                "total_units": summary.get("total_units", 0),
                "edge_count": summary.get("edge_count", 0),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
