"""L2 knowledge graph CLI commands."""
from __future__ import annotations
from pathlib import Path
import re

from brain.domains import topics_dir
from brain.state import L2_EDGE_TYPES, L2_NODE_TYPES


def _now_iso():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _parse_md(path: Path):
    import yaml
    if not path.exists():
        return {}, ""
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            try:
                fm = yaml.safe_load(parts[1]) or {}
            except Exception:
                fm = {}
            return fm, parts[2] if len(parts) > 2 else ""
    return {}, text


def _write_md(path: Path, fm: dict, body: str):
    import yaml
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["---", yaml.dump(dict(fm), default_flow_style=False, allow_unicode=True).rstrip(),
             "---", str(body).lstrip("\n")]
    path.write_text("\n".join(lines), encoding="utf-8")


def _slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value).strip()).strip("-")
    return slug or "node"


def _resolve_topic_root(topic_slug: str) -> Path:
    import os
    base = Path(os.environ.get("AITP_TOPICS_ROOT",
        "D:/BaiduSyncdisk/Theoretical-Physics/research/aitp-topics"))
    for candidate in [base / topic_slug, base / "topics" / topic_slug]:
        if (candidate / "state.md").exists():
            return candidate
    return base / topic_slug


def cmd_l2_node_create(args):
    """Create an L2 graph node."""
    topics_root = Path(args.topics_root) if getattr(args, 'topics_root') else Path(
        "D:/BaiduSyncdisk/Theoretical-Physics/research/aitp-topics")
    l2_dir = topics_dir(topics_root) / "L2" / "graph" / "nodes"
    l2_dir.mkdir(parents=True, exist_ok=True)

    node_type = args.node_type or "concept"
    if node_type not in L2_NODE_TYPES:
        print(f"Invalid node_type. Valid: {L2_NODE_TYPES}")
        return 1

    fm = {
        "node_id": args.node_id, "title": args.title or args.node_id,
        "type": node_type, "domain": args.domain or "abacus-librpa",
        "source_ref": args.source_ref or "", "created_at": _now_iso(),
    }
    body = f"# {fm['title']}\n\n{fm.get('source_ref', '')}\n"
    _write_md(l2_dir / f"{args.node_id}.md", fm, body)
    print(f"L2 node '{args.node_id}' created (type={node_type})")
    return 0


def cmd_l2_edge_create(args):
    """Create an L2 graph edge."""
    topics_root = Path(args.topics_root) if getattr(args, 'topics_root') else Path(
        "D:/BaiduSyncdisk/Theoretical-Physics/research/aitp-topics")
    l2_root = topics_dir(topics_root) / "L2"
    l2_dir = l2_root / "graph" / "edges"
    l2_dir.mkdir(parents=True, exist_ok=True)

    edge_type = args.edge_type or "uses"
    if edge_type not in L2_EDGE_TYPES:
        print(f"Invalid edge_type. Valid: {L2_EDGE_TYPES[:8]}...")
        return 1

    if not (args.source_ref or "").strip():
        print("source_ref is REQUIRED for L2 edges. Every relation must have provenance.")
        return 1

    nodes_dir = l2_root / "graph" / "nodes"
    missing = [
        node
        for node in [args.from_node, args.to_node]
        if not (nodes_dir / f"{_slugify(node)}.md").exists()
    ]
    if missing:
        print(f"L2 edge endpoint not found: {', '.join(missing)}")
        return 1

    fm = {
        "edge_id": args.edge_id, "from_node": args.from_node, "to_node": args.to_node,
        "type": edge_type, "source_ref": args.source_ref or "", "created_at": _now_iso(),
    }
    body = f"# {args.from_node} --[{edge_type}]--> {args.to_node}\n\n{fm.get('source_ref', '')}\n"
    _write_md(l2_dir / f"{args.edge_id}.md", fm, body)
    print(f"L2 edge '{args.edge_id}' created ({args.from_node} --[{edge_type}]--> {args.to_node})")
    return 0


def cmd_l2_merge(args):
    """Auto-merge topic subgraph to global L2."""
    root = _resolve_topic_root(args.topic)
    # Collect all derivation steps + edges from topic
    steps_dir = root / "L2" / "graph" / "steps"
    edges_dir = root / "L2" / "graph" / "edges"
    topics_root = topics_dir(Path("D:/BaiduSyncdisk/Theoretical-Physics/research/aitp-topics"))
    global_l2 = topics_root / "L2" / "graph"

    count = 0
    for src_dir, dst_dir in [(steps_dir, global_l2 / "steps"), (edges_dir, global_l2 / "edges")]:
        if not src_dir.exists():
            continue
        dst_dir.mkdir(parents=True, exist_ok=True)
        for f in src_dir.glob("*.md"):
            import shutil
            dst = dst_dir / f.name
            if not dst.exists():
                shutil.copy2(f, dst)
                count += 1
    print(f"Merged {count} items to global L2")
    return 0


def cmd_l2_query(args):
    """Query L2 knowledge graph."""
    topics_root = topics_dir(Path("D:/BaiduSyncdisk/Theoretical-Physics/research/aitp-topics"))
    query = " ".join(args.query) if hasattr(args.query, '__iter__') else str(args.query)
    nodes_dir = topics_root / "L2" / "graph" / "nodes"
    if not nodes_dir.exists():
        print("No L2 nodes found.")
        return 0
    matches = []
    for f in nodes_dir.glob("*.md"):
        fm, body = _parse_md(f)
        if query.lower() in body.lower() or query.lower() in fm.get("title", "").lower():
            matches.append(f"{fm.get('node_id', f.stem)}: {fm.get('title', '?')} ({fm.get('type', '?')})")
    print(f"Found {len(matches)} matching nodes for '{query}':")
    for m in matches[:20]:
        print(f"  {m}")
    return 0


def cmd_notebook_generate(args):
    """Generate flow notebook LaTeX from all topic artifacts.

    Uses the section-based template builder. Writes to topic root.
    """
    root = _resolve_topic_root(args.topic)
    from brain.flow_notebook import build_notebook
    force = getattr(args, "force", False)
    tex_content, regenerated = build_notebook(root, force_full=force)

    out_path = root / "flow_notebook.tex"
    # Atomic write
    from brain.cli.state import atomic_write
    atomic_write(out_path, tex_content)

    if regenerated:
        print(f"flow_notebook.tex written → {out_path}")
        print(f"  Sections regenerated: {', '.join(regenerated)}")
        print("  Compile with: pdflatex flow_notebook.tex")
    else:
        print("flow_notebook.tex is up to date (no sections changed).")
    return 0
