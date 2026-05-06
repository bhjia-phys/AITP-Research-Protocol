"""L1 reading CLI commands."""
from __future__ import annotations
from pathlib import Path
from brain.cli.commands.source import (_now_iso, _slugify, _parse_md, _write_md,
                                        _atomic_write, _append_research_md, _resolve_topic_root)


def cmd_source_parse_toc(args):
    root = _resolve_topic_root(args.topic)
    toc_path = root / "L1" / "source_toc_map.md"
    toc_path.parent.mkdir(parents=True, exist_ok=True)

    if toc_path.exists():
        fm, body = _parse_md(toc_path)
    else:
        fm = {"sources_with_toc": "", "total_sections": 0, "coverage_status": "incomplete"}
        body = "# Source TOC Map\n"

    sections = args.sections or "TBD"
    body += f"\n## {args.source}\nSections: {sections}\n"
    current_total = int(fm.get("total_sections", 0))
    fm["total_sections"] = current_total + len(sections.split(","))
    fm["coverage_status"] = "partial_with_deferrals"
    _write_md(toc_path, fm, body)
    print(f"TOC entry added for {args.source} ({sections})")
    return 0


def cmd_source_extract(args):
    root = _resolve_topic_root(args.topic)
    source_slug = _slugify(args.source)
    intake_dir = root / "L1" / "intake" / source_slug
    intake_dir.mkdir(parents=True, exist_ok=True)

    section_slug = _slugify(args.section)
    path = intake_dir / f"{section_slug}.md"
    fm = {
        "source_id": args.source,
        "section": args.section,
        "completeness_confidence": args.confidence or "medium",
        "extracted_at": _now_iso(),
    }
    if hasattr(args, 'source_file') and args.source_file:
        fm["source_file"] = args.source_file
    body = f"# {args.source} — {args.section}\n\n{args.content or ''}\n"
    _write_md(path, fm, body)
    _append_research_md(root, "L1", f"Extracted {args.source}/{args.section}")
    print(f"Section '{args.section}' extracted → {path}")
    return 0


def cmd_source_extract_all(args):
    """List all pending sections from source_toc_map.md for batch extraction.

    Reads the TOC map, finds sections with status=pending, and reports them.
    The agent should call 'aitp source extract' for each listed section.
    Does NOT auto-extract — the agent controls extraction granularity.
    """
    root = _resolve_topic_root(args.topic)
    toc_path = root / "L1" / "source_toc_map.md"
    if not toc_path.exists():
        print("No TOC map found. Run 'aitp source parse-toc' first.")
        return 1

    _, body = _parse_md(toc_path)
    import re

    # Parse per-source blocks: "## <source_id>" headings
    source_blocks = re.split(r'\n(?=## )', body)
    pending_all = []

    for block in source_blocks:
        # Extract source_id from heading
        src_match = re.match(r'^## (.+)', block)
        if not src_match:
            src_header = re.match(r'^# (.+)', block)
            if src_header:
                continue  # Top-level heading, skip
            continue
        src_id = src_match.group(1).strip()

        if args.source and src_id != args.source:
            continue

        # Parse section entries: "- [section_id] title -- status: pending"
        for line in block.split('\n'):
            sec_match = re.match(r'^(\s*)-\s*\[(.+?)\]\s*(.+?)\s*--\s*status:\s*(\w+)', line)
            if sec_match:
                indent = len(sec_match.group(1))
                sec_id = sec_match.group(2).strip()
                sec_title = sec_match.group(3).strip()
                sec_status = sec_match.group(4).strip()
                if sec_status == 'pending':
                    depth = indent // 2 + 1
                    pending_all.append({
                        'source': src_id, 'section_id': sec_id,
                        'title': sec_title, 'depth': depth,
                    })

    if not pending_all:
        src_msg = f" for {args.source}" if getattr(args, 'source', None) else ""
        print(f"No pending sections found{src_msg}.")
        return 0

    src_label = f" for {args.source}" if getattr(args, 'source', None) else ""
    print(f"Pending sections{src_label}: {len(pending_all)}")
    current_src = None
    for sec in pending_all:
        if sec['source'] != current_src:
            current_src = sec['source']
            print(f"\n  [{current_src}]")
        indent = "    " * sec['depth']
        print(f"{indent}  [{sec['section_id']}] {sec['title']}")

    print(f"\nRun 'aitp source extract {args.topic} --source <source> --section <section_id>' for each.")
    return 0
