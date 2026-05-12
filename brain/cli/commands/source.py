"""L0 source management CLI commands."""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import urllib.request
import urllib.error


def _now_iso():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _slugify(text: str) -> str:
    import re
    return re.sub(r'[^a-z0-9-]', '-', (text or "untitled").lower().strip())[:60]


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


def _atomic_write(path: Path, content: str):
    import os, tempfile
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix="." + path.name + ".")
    try:
        os.write(fd, content.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, path)


def _append_research_md(root: Path, layer: str, entry: str):
    path = root / "research.md"
    line = f"- {_now_iso()} [{layer}] {entry}\n"
    if path.exists():
        _atomic_write(path, path.read_text(encoding="utf-8") + line)
    else:
        _atomic_write(path, f"# Research Trail\n\n{line}")


def _download_file(url: str, dest: Path) -> bool:
    """Download a file from URL to dest. Returns True on success."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AITP/1.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "wb") as f:
                f.write(resp.read())
        return True
    except Exception as e:
        print(f"  Download failed: {e}")
        return False


def cmd_source_add(args):
    if hasattr(args, 'topics_root') and args.topics_root:
        root = Path(args.topics_root)
    else:
        root = _resolve_topic_root(args.topic)
    source_id = _slugify(args.id or args.title or args.path or args.url or args.repo or "untitled")

    # Auto-detect type if not given
    stype = args.type or "paper"
    if not args.type:
        if args.repo:
            stype = "repo"
        elif args.path:
            ext = Path(args.path).suffix.lower()
            if ext in (".cpp", ".h", ".py", ".f90", ".c", ".cu"):
                stype = "code"
            elif ext in (".pdf", ".tex", ".md"):
                stype = "paper"

    # Per-source directory: L0/sources/<source_id>/
    source_dir = root / "L0" / "sources" / source_id
    original_dir = source_dir / "original"
    source_dir.mkdir(parents=True, exist_ok=True)
    original_dir.mkdir(parents=True, exist_ok=True)

    original_files: list[str] = []

    # ── git clone if --repo given ──────────────────────────────────────
    if args.repo:
        import subprocess
        repo_url = args.repo
        branch = getattr(args, "branch", None) or ""
        commit = getattr(args, "commit", "") or ""
        print(f"  Cloning {repo_url} ...")
        # Clone into source_dir directly (not into original/)
        clone_cmd = ["git", "clone"]
        if branch:
            clone_cmd += ["--branch", branch, "--single-branch"]
        clone_cmd += [repo_url, str(source_dir)]
        result = subprocess.run(clone_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            # Move source.md and notes.md if they already exist, then recreate
            # (clone would have created them from template, no — clone creates dir)
            # Clone creates source_dir; source.md/notes.md written after
            print(f"  Cloned: {repo_url}")
            original_files.append("(git repository)")
        else:
            print(f"  Clone failed: {result.stderr[:200]}")
            return 1

    # ── Copy local files if --path given ───────────────────────────────
    if args.path:
        p = Path(args.path)
        if p.exists() and p.is_file():
            dest = original_dir / p.name
            shutil.copy2(p, dest)
            original_files.append(p.name)
            print(f"  Copied: {p.name} → original/")
        elif p.exists() and p.is_dir():
            for f in p.rglob("*"):
                if f.is_file() and ".git" not in f.parts:
                    rel = f.relative_to(p)
                    dest = original_dir / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, dest)
            original_files.append(f"{p.name}/ (directory)")
            print(f"  Copied directory: {p.name}/ → original/")
        else:
            print(f"  Path not found: {args.path}")

    # ── Download from URL if --url given ───────────────────────────────
    if args.url:
        url_path = args.url.split("/")[-1].split("?")[0] or "downloaded"
        if args.url.endswith(".tar.gz") or args.url.endswith(".tgz"):
            # arXiv e-print: download + extract LaTeX source
            tarball = original_dir / url_path
            if _download_file(args.url, tarball):
                original_files.append(url_path)
                import tarfile
                try:
                    with tarfile.open(tarball) as tf:
                        tf.extractall(original_dir)
                    print(f"  Extracted LaTeX source to original/")
                except Exception as e:
                    print(f"  Extract failed: {e}")
        else:
            dest = original_dir / url_path
            if _download_file(args.url, dest):
                original_files.append(url_path)
                print(f"  Downloaded: {url_path} → original/")

    # ── Write source.md (pure metadata) ───────────────────────────────
    fm = {
        "source_id": source_id,
        "title": args.title or args.path or args.url or args.repo or "Untitled",
        "type": stype,
        "role": args.role or "direct_dependency",
        "created_at": _now_iso(),
        "original_files": original_files,
    }
    if args.repo:
        fm["repo"] = args.repo
        if branch:
            fm["branch"] = branch
        if commit:
            fm["commit"] = commit
    if args.url:
        fm["source_url"] = args.url

    metadata_lines = [
        f"# Source: {fm['title']}",
        "",
        f"**Type**: {fm['type']}",
        f"**Role**: {fm['role']}",
        f"**Registered**: {fm['created_at']}",
        "",
    ]
    if original_files:
        metadata_lines.append(f"**Original files**: {', '.join(original_files)}")
    if args.repo:
        metadata_lines.append(f"**Repo**: {args.repo}")
    if args.url:
        metadata_lines.append(f"**URL**: {args.url}")

    _write_md(source_dir / "source.md", fm, "\n".join(metadata_lines))

    # ── Write notes.md ─────────────────────────────────────────────
    notes_fm = {
        "kind": "source_notes",
        "source_id": source_id,
        "created_at": _now_iso(),
    }
    if args.notes and args.notes.strip():
        notes_body = args.notes.strip() + "\n"
    else:
        notes_body = (
            "# Reading Notes\n\n"
            "## Key Claims / Equations\n\n"
            "*(Extract the main physical claims, key equations, and argument structure.)*\n\n"
            "## Structure / Coverage\n\n"
            "*(Sections read, what each section contributes.)*\n\n"
            "## Observations\n\n"
            "*(Anything surprising, unclear, or worth following up.)*\n"
        )
    _write_md(source_dir / "notes.md", notes_fm, notes_body)

    _append_research_md(root, "L0", f"Registered source: {source_id} ({stype})")
    print(f"Source '{source_id}' ({stype}) registered → {source_dir}")
    print(f"  source.md  — metadata")
    print(f"  notes.md   — reading notes template")
    if original_files:
        print(f"  original/  — {len(original_files)} file(s)")
    return 0


def cmd_source_discover(args):
    """Search arXiv for papers matching a query. Returns results for manual review."""
    query = args.query or ""
    if not query:
        print("Provide --query for arXiv search.")
        return 1

    import urllib.parse
    import xml.etree.ElementTree as ET

    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode({
        "search_query": query,
        "max_results": str(args.max or 10),
        "sortBy": "relevance",
    })

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AITP/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read().decode("utf-8")
    except Exception as e:
        print(f"arXiv API error: {e}")
        return 1

    ns = {"atom": "http://www.w3.org/2005/Atom",
          "arxiv": "http://arxiv.org/schemas/atom"}
    root_el = ET.fromstring(data)

    entries = root_el.findall("atom:entry", ns)
    if not entries:
        print(f"No results for '{query}'")
        return 0

    print(f"arXiv results for '{query}': {len(entries)} found\n")
    for i, entry in enumerate(entries, 1):
        title = entry.findtext("atom:title", "", ns).strip().replace("\n", " ")
        arxiv_id = entry.findtext("atom:id", "", ns).strip()
        arxiv_short = arxiv_id.split("/abs/")[-1] if "/abs/" in arxiv_id else arxiv_id
        authors = [
            a.findtext("atom:name", "", ns).strip()
            for a in entry.findall("atom:author", ns)
        ]
        summary = entry.findtext("atom:summary", "", ns).strip()[:200].replace("\n", " ")
        published = entry.findtext("atom:published", "", ns)[:10]
        print(f"{i}. [{arxiv_short}] {title}")
        print(f"   Authors: {', '.join(authors[:3])}{'...' if len(authors) > 3 else ''}")
        print(f"   Published: {published}  |  {summary[:120]}...")
        print()

    register_n = getattr(args, "register", 0) or 0
    if register_n > 0:
        n = min(register_n, len(entries))
        print(f"\nAuto-registering top {n} result(s)...")
        registered = 0
        for i, entry in enumerate(entries[:n], 1):
            title = entry.findtext("atom:title", "", ns).strip().replace("\n", " ")
            arxiv_id_full = entry.findtext("atom:id", "", ns).strip()
            arxiv_short = arxiv_id_full.split("/abs/")[-1] if "/abs/" in arxiv_id_full else arxiv_id_full
            sid = _slugify(arxiv_short)
            try:
                cmd_source_add(argparse.Namespace(
                    topic=args.topic, id=sid, type="paper", role="direct_dependency",
                    title=title, url="", path="", repo="", branch="", commit="",
                    notes="",
                ))
                # Enrich with arxiv_id
                topic_root = _resolve_topic_root(args.topic)
                src_path = topic_root / "L0" / "sources" / sid / "source.md"
                if src_path.exists():
                    fm, body = _parse_md(src_path)
                    fm["arxiv_id"] = arxiv_short
                    fm["fidelity"] = "arxiv_preprint"
                    _write_md(src_path, fm, body)
                registered += 1
                print(f"  {i}. [{arxiv_short}] {title[:60]}...  REGISTERED")
            except Exception as e:
                print(f"  {i}. [{arxiv_short}] FAILED: {e}")
        print(f"\nRegistered {registered}/{n}. Use 'aitp source registry {args.topic}' to view.")
    else:
        print(f"Register with: aitp source add {args.topic} --id <arxiv_id> --title \"...\" --type paper")
    return 0


def cmd_source_registry(args):
    root = _resolve_topic_root(args.topic)
    sources_dir = root / "L0" / "sources"
    if not sources_dir.exists() or not list(sources_dir.iterdir()):
        print("No sources registered yet. Use 'aitp source add' first.")
        return 1

    # Scan for source directories (contain source.md) and legacy flat .md files
    sources: list[Path] = []
    for item in sorted(sources_dir.iterdir()):
        if item.is_dir() and (item / "source.md").exists():
            sources.append(item / "source.md")
        elif item.is_file() and item.suffix == ".md":
            sources.append(item)

    if not sources:
        print("No sources found.")
        return 1

    lines = ["# Source Registry\n", f"\n**Total sources**: {len(sources)}\n"]
    for s in sorted(sources):
        sf, _ = _parse_md(s)
        sid = sf.get("source_id", s.stem)
        title = sf.get("title", "?")
        stype = sf.get("type", "?")
        srole = sf.get("role", "?")
        orig = sf.get("original_files", [])
        orig_str = f" [orig: {', '.join(orig)}]" if orig else ""
        lines.append(f"- **{sid}**: {title} ({stype}, {srole}){orig_str}\n")

    registry_path = root / "L0" / "source_registry.md"
    fm = {"source_count": len(sources), "search_status": "complete"}
    _write_md(registry_path, fm, "".join(lines))
    _append_research_md(root, "L0", f"Registry synthesized: {len(sources)} sources")
    print(f"Registry written with {len(sources)} sources → {registry_path}")
    return 0


def cmd_source_read(args):
    root = _resolve_topic_root(args.topic)
    # Try new directory structure first
    source_dir = root / "L0" / "sources" / args.source
    path = source_dir / "source.md"
    if not path.exists():
        # Fall back to legacy flat .md
        path = root / "L0" / "sources" / f"{args.source}.md"
    if not path.exists():
        print(f"Source '{args.source}' not found in L0/sources/")
        # Show what's available
        candidates = sorted(
            [d.name for d in (root / "L0" / "sources").iterdir() if d.is_dir()]
            + [f.stem for f in (root / "L0" / "sources").glob("*.md")]
        )
        if candidates:
            print(f"  Available: {', '.join(candidates[:10])}")
        return 1
    _, body = _parse_md(path)
    print(body[:2000])
    return 0


def _resolve_topic_root(topic_slug: str) -> Path:
    import os
    base = Path(os.environ.get("AITP_TOPICS_ROOT",
        "D:/BaiduSyncdisk/Theoretical-Physics/research/aitp-topics"))
    for candidate in [base / topic_slug, base / "topics" / topic_slug]:
        if (candidate / "state.md").exists():
            return candidate
    return base / topic_slug
