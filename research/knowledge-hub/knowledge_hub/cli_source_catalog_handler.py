from __future__ import annotations

import argparse
from typing import Any


SOURCE_CATALOG_COMMANDS = {
    "compile-source-catalog",
    "trace-source-citations",
    "compile-source-family",
    "export-source-bibtex",
    "import-bibtex-sources",
}


def register_source_catalog_commands(subparsers: argparse._SubParsersAction[Any]) -> None:
    compile_source_catalog = subparsers.add_parser(
        "compile-source-catalog",
        help="Compile a global deduplicated source catalog across topic-local Layer 0 indexes",
    )
    compile_source_catalog.add_argument("--json", action="store_true")

    trace_source_citations = subparsers.add_parser(
        "trace-source-citations",
        help="Materialize a bounded citation traversal for one canonical source",
    )
    trace_source_citations.add_argument("--canonical-source-id", required=True)
    trace_source_citations.add_argument("--json", action="store_true")

    compile_source_family = subparsers.add_parser(
        "compile-source-family",
        help="Compile a bounded source-family reuse report for one source type",
    )
    compile_source_family.add_argument("--source-type", required=True)
    compile_source_family.add_argument("--json", action="store_true")

    export_source_bibtex = subparsers.add_parser(
        "export-source-bibtex",
        help="Export one canonical Layer 0 source and its bounded neighborhood as BibTeX",
    )
    export_source_bibtex.add_argument("--canonical-source-id", required=True)
    export_source_bibtex.add_argument("--include-neighbors", action="store_true")
    export_source_bibtex.add_argument("--json", action="store_true")

    import_bibtex_sources = subparsers.add_parser(
        "import-bibtex-sources",
        help="Import a bounded BibTeX file into one topic Layer 0 source index",
    )
    import_bibtex_sources.add_argument("--topic-slug", required=True)
    import_bibtex_sources.add_argument("--bibtex-path", required=True)
    import_bibtex_sources.add_argument("--updated-by", default="aitp-cli")
    import_bibtex_sources.add_argument("--json", action="store_true")


def dispatch_source_catalog_command(args: argparse.Namespace, service: Any) -> dict[str, Any] | None:
    if args.command == "compile-source-catalog":
        return service.compile_source_catalog()
    if args.command == "trace-source-citations":
        return service.trace_source_citations(canonical_source_id=args.canonical_source_id)
    if args.command == "compile-source-family":
        return service.compile_source_family(source_type=args.source_type)
    if args.command == "export-source-bibtex":
        return service.export_source_bibtex(
            canonical_source_id=args.canonical_source_id,
            include_neighbors=args.include_neighbors,
        )
    if args.command == "import-bibtex-sources":
        return service.import_bibtex_sources(
            topic_slug=args.topic_slug,
            bibtex_path=args.bibtex_path,
            updated_by=args.updated_by,
        )
    return None
