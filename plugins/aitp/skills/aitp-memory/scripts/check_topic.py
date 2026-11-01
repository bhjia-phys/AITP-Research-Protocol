#!/usr/bin/env python3
"""Check a research topic's links, placement, Current work and note reachability.

Usage:
  python3 check_topic.py TOPIC [--workspace DIR ...] [--skip REL ...] [--frozen PATTERN ...]
                         [--include-repos] [--json OUT] [--strict]

TOPIC is a topic or family root (a folder whose research.md is the main note).
--workspace names folders outside TOPIC, such as the topics root or a shared
knowledge collection, whose Markdown links into TOPIC are checked as incoming links.
--skip excludes subtrees of TOPIC by relative path (for example a large archive).
--frozen adds folder-name patterns treated as frozen copies (for example '*-backup-*').
Nested source repositories (folders holding .git) are skipped unless --include-repos:
their documentation is not part of the topic's notes. Python and conda environments
(folders holding pyvenv.cfg or conda-meta) are always skipped.

The checker reports; it changes nothing and establishes no scientific claim.
Errors: broken relative links or #anchors in active notes, unresolved incoming links,
and files at a topic root that placement-rules.json does not admit. Warnings: links
leaving TOPIC that do not resolve, loose notes at a topic root, a main note without
Current work or with undated entries (pointer entries to an owning note are exempt), and notes/ files that no main note or README reaches.
Frozen copies (a path component "before", or provenance/snapshots) are reported only
as counts: they keep the link base of the revision they record.

Exit status is 1 when there are errors (or warnings with --strict), else 0.
Standard library only; Python 3.8 or later.
"""
import argparse, fnmatch, json, os, re, sys, unicodedata, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = os.path.normpath(os.path.join(HERE, "..", "..", "..", "assets", "placement-rules.json"))

LINK = re.compile(r"(!?)\[(?:[^\[\]]|\[[^\[\]]*\])*\]\((<[^>]*>|[^)\s]+)((?:\s+\"[^\"]*\"|\s+'[^']*')?)\)")
DEFN = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*(\S+)", re.M)
FENCE = re.compile(r"^(```|~~~)[^\n]*\n.*?^\1[^\n]*$", re.M | re.S)
INLINE_CODE = re.compile(r"`[^`\n]*`")
HEAD = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$", re.M)
IDS = re.compile(r"""<a\s[^>]*\b(?:id|name)\s*=\s*["']([^"']+)["']""", re.I)
MYST = re.compile(r"^\(([^)\s]+)\)=\s*$|\{#([^}\s]+)\}", re.M)
DATE = re.compile(r"20\d\d-[01]\d-[0-3]\d|unrecorded", re.I)
POINTER = re.compile(r"→\s*\[[^\]]*\]\([^)]*\)|\]\([^)]*research\.md#current-work\)")
SKIP_PREFIX = ("http://", "https://", "mailto:", "/", "file:", "#", "data:")


FROZEN_GLOBS = []


def is_frozen(rel):
    parts = rel.replace("\\", "/").split("/")
    if "before" in parts or ("provenance" in parts and "snapshots" in parts):
        return True
    return any(fnmatch.fnmatch(x, g) for x in parts[:-1] for g in FROZEN_GLOBS)


def code_ranges(text):
    rs = [m.span() for m in FENCE.finditer(text)]
    masked = FENCE.sub(lambda m: " " * len(m.group(0)), text)
    rs += [m.span() for m in INLINE_CODE.finditer(masked)]
    return sorted(rs)


def in_ranges(pos, rs):
    for a, b in rs:
        if a <= pos < b:
            return True
        if a > pos:
            break
    return False


def iter_links(text):
    """Yield (offset, raw_target, path, anchor) for relative links outside code."""
    rs = code_ranges(text)
    found = [(m.start(), m.group(2)) for m in LINK.finditer(text)]
    found += [(m.start(), m.group(1)) for m in DEFN.finditer(text)]
    for pos, tgt in found:
        if in_ranges(pos, rs):
            continue
        tgt = tgt.strip("<>").strip()
        if not tgt or tgt.startswith(SKIP_PREFIX) or re.match(r"^[a-z][a-z0-9+.-]*:", tgt, re.I):
            if tgt.startswith("#"):
                yield pos, tgt, "", tgt[1:]
            continue
        path, _, anchor = tgt.partition("#")
        if "\\" in path or ("." not in path and "/" not in path):  # LaTeX or bare notation
            continue
        yield pos, tgt, path, anchor


def slugify(h):
    h = re.sub(r"<[^>]+>", "", h)
    h = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", h)
    h = h.replace("`", "").strip().lower()
    out = []
    for ch in h:
        if ch == " ":
            out.append("-")
        elif ch in "-_" or ch.isalnum() or unicodedata.category(ch).startswith("M"):
            out.append(ch)
    return "".join(out)


_anchor_cache = {}


def anchors_of(path):
    if path not in _anchor_cache:
        try:
            text = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            _anchor_cache[path] = None
            return None
        seen, out = {}, set()
        for m in HEAD.finditer(FENCE.sub("", text)):
            s = slugify(m.group(2))
            if s in seen:
                seen[s] += 1
                out.add(f"{s}-{seen[s]}")
            else:
                seen[s] = 0
                out.add(s)
        out.update(IDS.findall(text))
        out.update(x or y for x, y in MYST.findall(text))
        _anchor_cache[path] = {x.lower() for x in out}
    return _anchor_cache[path]


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


SKIP_REPOS = True
SKIPPED_REPOS = []


def walk_md(root, skips, hidden=True):
    for dp, dns, fns in os.walk(root):
        rd = os.path.relpath(dp, root).replace("\\", "/")
        rd = "" if rd == "." else rd
        if rd and any(os.path.exists(os.path.join(dp, x)) for x in ("pyvenv.cfg", "conda-meta")):
            dns[:] = []  # a Python or conda environment is a tool, not research material
            continue
        if SKIP_REPOS and rd and os.path.exists(os.path.join(dp, ".git")):
            if dp not in SKIPPED_REPOS:
                SKIPPED_REPOS.append(dp)
            dns[:] = []
            continue
        dns[:] = sorted(d for d in dns if not (hidden and d.startswith(".")) and not any(
            (rd + "/" + d).lstrip("/") == s or (rd + "/" + d).lstrip("/").startswith(s + "/") for s in skips))
        for fn in sorted(fns):
            if fn.endswith(".md"):
                yield os.path.join(dp, fn)


class Report:
    def __init__(self):
        self.rows = []

    def add(self, level, kind, where, msg):
        self.rows.append({"level": level, "kind": kind, "where": where, "message": msg})

    def count(self, level):
        return sum(r["level"] == level for r in self.rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("topic")
    ap.add_argument("--workspace", action="append", default=[], help="folder scanned for incoming links")
    ap.add_argument("--skip", action="append", default=[], help="relative subtree of TOPIC to ignore")
    ap.add_argument("--frozen", action="append", default=[], help="folder-name pattern treated as a frozen copy")
    ap.add_argument("--include-repos", action="store_true", help="also check nested source repositories")
    ap.add_argument("--rules", default=RULES, help="placement-rules.json (default: AITP's copy)")
    ap.add_argument("--json", help="write the full report as JSON")
    ap.add_argument("--strict", action="store_true", help="exit 1 on warnings too")
    a = ap.parse_args()

    global SKIP_REPOS
    root = os.path.abspath(a.topic)
    skips = [s.strip("/") for s in a.skip]
    FROZEN_GLOBS.extend(a.frozen)
    SKIP_REPOS = not a.include_repos
    rules = json.load(open(a.rules, encoding="utf-8"))
    allow_names = set(rules["root"]["allowNames"])
    allow_ext = set(rules["root"]["allowExtensions"])
    study_dirs = set(rules.get("freeDirs", [])) | set(rules["topLevel"].get("legacy", []))
    rep = Report()
    stats = {"active_markdown": 0, "frozen_markdown": 0, "links": 0, "external_links": 0,
             "frozen_unresolved": 0, "incoming_links": 0}
    graph = {}

    # 1. Links and anchors inside TOPIC.
    for p in walk_md(root, skips):
        rel = os.path.relpath(p, root).replace("\\", "/")
        frozen = is_frozen(rel)
        stats["frozen_markdown" if frozen else "active_markdown"] += 1
        text = open(p, encoding="utf-8", errors="replace").read()
        d = os.path.dirname(p)
        for pos, raw, path, anchor in iter_links(text):
            stats["links"] += 1
            tgt = os.path.normpath(os.path.join(d, urllib.parse.unquote(path))) if path else p
            where = f"{rel}:{line_of(text, pos)}"
            inside = tgt == root or tgt.startswith(root + os.sep)
            if not frozen and inside:
                graph.setdefault(p, set()).add(tgt)
            if not os.path.exists(tgt):
                if frozen:
                    stats["frozen_unresolved"] += 1
                elif inside:
                    rep.add("error", "broken-link", where, raw)
                else:
                    stats["external_links"] += 1
                    rep.add("warning", "external-unresolved", where, raw)
                continue
            if not inside and not frozen:
                stats["external_links"] += 1
            if anchor and not frozen and tgt.endswith(".md") and os.path.isfile(tgt):
                an = anchors_of(tgt)
                if an is not None and urllib.parse.unquote(anchor).lower() not in an:
                    rep.add("error", "broken-anchor", where, raw)

    # 2. Incoming links from the named workspaces.
    for w in a.workspace:
        w = os.path.abspath(w)
        for p in walk_md(w, []):
            if p == root or p.startswith(root + os.sep):
                continue
            rel = os.path.relpath(p, w)
            if is_frozen(rel):
                continue
            text = open(p, encoding="utf-8", errors="replace").read()
            d = os.path.dirname(p)
            for pos, raw, path, anchor in iter_links(text):
                if not path:
                    continue
                tgt = os.path.normpath(os.path.join(d, urllib.parse.unquote(path)))
                if not (tgt == root or tgt.startswith(root + os.sep)):
                    continue
                stats["incoming_links"] += 1
                where = f"{p}:{line_of(text, pos)}"
                if not os.path.exists(tgt):
                    rep.add("error", "incoming-broken", where, raw)
                elif anchor and tgt.endswith(".md") and os.path.isfile(tgt):
                    an = anchors_of(tgt)
                    if an is not None and urllib.parse.unquote(anchor).lower() not in an:
                        rep.add("error", "incoming-broken-anchor", where, raw)

    # 3. Topic roots: placement, Current work, notes reachability.
    mains = []
    for p in walk_md(root, skips):
        rel = os.path.relpath(p, root).replace("\\", "/")
        if os.path.basename(p) == "research.md" and not is_frozen(rel):
            mains.append(p)
    for m in mains:
        troot = os.path.dirname(m)
        trel = os.path.relpath(troot, root).replace("\\", "/")
        parts = [] if trel == "." else trel.split("/")
        if any(x in study_dirs for x in parts):
            rep.add("info", "study-note", trel + "/research.md",
                    "main note inside a run or legacy folder; root placement rules not applied")
        else:
            for f in sorted(os.listdir(troot)):
                fp = os.path.join(troot, f)
                if not os.path.isfile(fp) or f in allow_names:
                    continue
                ext = os.path.splitext(f)[1].lower()
                if ext not in allow_ext:
                    rep.add("error", "root-file", os.path.join(trel, f), "file type not admitted at a topic root")
                elif ext == ".md":
                    rep.add("warning", "loose-note", os.path.join(trel, f),
                            "note at a topic root; notes/ is its usual home")
        text = open(m, encoding="utf-8", errors="replace").read()
        sec = re.search(r"^## Current work[^\n]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
        mrel = os.path.relpath(m, root).replace("\\", "/")
        if not sec:
            rep.add("warning", "no-current-work", mrel, "no '## Current work' section (fine only if no thread continues)")
        else:
            body = sec.group(1)
            start = sec.start(1)
            for e in re.finditer(r"^- (.*?)(?=^- |^\S|\Z)", body, re.M | re.S):
                first_line = e.group(1).split("\n")[0]
                if POINTER.search(first_line):  # a pointer entry names its owner and needs no date
                    continue
                if not DATE.search(e.group(1)):
                    first = e.group(1).strip().split("\n")[0][:70]
                    rep.add("warning", "undated-entry", f"{mrel}:{line_of(text, start + e.start())}",
                            f"Current work entry without a date or 'change date unrecorded': {first}")
        ndir = os.path.join(troot, "notes")
        if os.path.isdir(ndir):
            starts = [x for x in (m, os.path.join(troot, "README.md")) if os.path.exists(x)]
            seen, q = set(), list(starts)
            while q:
                x = q.pop()
                if x in seen:
                    continue
                seen.add(x)
                for t in graph.get(x, ()):
                    if os.path.isdir(t) and os.path.exists(os.path.join(t, "README.md")):
                        t = os.path.join(t, "README.md")
                    if t.endswith(".md") and t not in seen:
                        q.append(t)
            for f in sorted(os.listdir(ndir)):
                fp = os.path.join(ndir, f)
                if f.endswith(".md") and fp not in seen:
                    rep.add("warning", "unreached-note", os.path.relpath(fp, root),
                            "not reached from this topic's research.md or README.md")

    stats["main_notes"] = len(mains)
    stats["nested_repositories_skipped"] = sum(1 for x in SKIPPED_REPOS if x.startswith(root + os.sep))
    errors, warnings = rep.count("error"), rep.count("warning")
    print(f"topic: {root}")
    print("main notes {main_notes}; active Markdown {active_markdown}; frozen {frozen_markdown}; "
          "links {links}; leaving the topic {external_links}; incoming {incoming_links}; "
          "frozen unresolved (not repaired) {frozen_unresolved}; nested repositories skipped "
          "{nested_repositories_skipped}".format(**stats))
    for r in rep.rows:
        print(f"{r['level'].upper():7s} {r['kind']:22s} {r['where']}  {r['message']}")
    print(f"{errors} error(s), {warnings} warning(s)")
    if a.json:
        json.dump({"topic": root, "stats": stats, "findings": rep.rows}, open(a.json, "w", encoding="utf-8"),
                  indent=1, ensure_ascii=False)
    sys.exit(1 if errors or (a.strict and warnings) else 0)


if __name__ == "__main__":
    main()
