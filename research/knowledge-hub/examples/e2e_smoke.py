from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _bootstrap_path() -> None:
    current = Path(__file__).resolve()
    package_root = current.parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


def _safe_console_text(text: str) -> str:
    encoding = sys.stdout.encoding or "utf-8"
    return text.encode(encoding, errors="replace").decode(encoding, errors="replace")


def main() -> None:
    _bootstrap_path()
    from knowledge_hub import KnowledgeHub

    parser = argparse.ArgumentParser(description="Knowledge Hub end-to-end smoke test")
    parser.add_argument(
        "--source",
        default=str(Path(__file__).resolve().parents[3] / "1510.07698v2.txt"),
        help="Local source file path to ingest",
    )
    parser.add_argument(
        "--question",
        default="What is the main argument flow of this paper?",
        help="Question to run against the hub",
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Also export result to Obsidian",
    )
    args = parser.parse_args()

    hub = KnowledgeHub()

    ingest = hub.ingest_sources([args.source], source_kind="auto")
    print("[1] Ingest:", ingest)

    result = hub.query(args.question, top_k=6, include_zotero=True)
    print("[2] Query ID:", result["query_id"])
    print("[3] Citations:", len(result.get("citations", [])))
    print("[4] Answer preview:")
    print(_safe_console_text(result["answer"][:600]))

    if args.export:
        exported = hub.export_obsidian(
            query_id=result["query_id"],
            note_title="Knowledge Hub Smoke Test",
        )
        print("[5] Exported:", exported["note_path"])


if __name__ == "__main__":
    main()
