#!/usr/bin/env python3
"""Move files inside a research topic and rewrite the relative links that use them.

Usage:
  python3 move_notes.py TOPIC MOVES.tsv --manifest OUT.json [--incoming DIR ...]
                        [--rewrite-incoming] [--frozen PATTERN ...] [--apply]

MOVES.tsv has one move per line: old_path<TAB>new_path<TAB>reason, paths relative to TOPIC
('#' lines are comments). Without --apply this is a dry run: it writes the manifest and
prints what would change. With --apply it backs up every file it will touch, moves the
files, rewrites links and verifies the result.

Rules:
* Only the target of a parsed Markdown link changes; link text, titles, #anchors, <...>
  wrappers and %-encoding style are kept. Links in fenced or inline code are never touched.
* Frozen copies (a path component "before", provenance/snapshots, or a folder matching
  --frozen) are never edited, and a move of a frozen file is refused. Nested source
  repositories (folders holding .git) are never edited.
* For each active Markdown file F and each relative link, the old target is resolved from
  F's old folder, mapped through the moves, and rewritten relative to F's new folder when
  F or the target moved. Links leaving TOPIC keep their meaning when F moves.
* --incoming DIR scans Markdown outside TOPIC (a knowledge collection, other topics) for
  links into moved files. They are always reported; they are rewritten only with
  --rewrite-incoming, because such folders may lie outside the authorized scope.
* Non-Markdown text files inside TOPIC that mention a moved file's old path (code strings,
  JSON receipts) are reported, never edited.

The manifest records each move with sha256 before, right after the move and final, every
link rewrite, incoming links, non-Markdown mentions, the backup location and verification.
The backup is written to <manifest>-backup/before/, which both scripts treat as frozen.
Standard library only; Python 3.8 or later.
"""
import argparse, fnmatch, hashlib, json, os, re, shutil, sys, urllib.parse

LINK = re.compile(r"(!?)\[(?:[^\[\]]|\[[^\[\]]*\])*\]\((<[^>]*>|[^)\s]+)((?:\s+\"[^\"]*\"|\s+'[^']*')?)\)")
FENCE = re.compile(r"^(```|~~~)[^\n]*\n.*?^\1[^\n]*$", re.M | re.S)
INLINE_CODE = re.compile(r"`[^`\n]*`")
SKIP_PREFIX = ("http://", "https://", "mailto:", "/", "file:", "#", "data:")
TEXT_EXT = {".py", ".sh", ".json", ".yaml", ".yml", ".toml", ".txt", ".tex", ".jl", ".m", ".csv",
            ".sbatch", ".slurm", ".cfg", ".ini", ".js", ".ts", ".r", ".ipynb"}


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
    return rs


def links(text):
    """Yield (start, end, target) for the target substring of each relative link."""
    rs = code_ranges(text)
    for m in LINK.finditer(text):
        if any(a <= m.start() < b for a, b in rs):
            continue
        tgt = m.group(2)
        s, e = m.span(2)
        if tgt.startswith("<") and tgt.endswith(">"):
            tgt, s, e = tgt[1:-1], s + 1, e - 1
        if not tgt or tgt.startswith(SKIP_PREFIX) or re.match(r"^[a-z][a-z0-9+.-]*:", tgt, re.I):
            continue
        path = tgt.split("#", 1)[0]
        if not path or "\\" in path or ("." not in path and "/" not in path):
            continue
        yield s, e, tgt


def encode_like(original, new):
    return urllib.parse.quote(new, safe="/._-~()+,;=!*'@$&") if "%" in original else new


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read(p):
    return open(p, encoding="utf-8", newline="").read()


def md_files(root, skip_hidden=True):
    for dp, dns, fns in os.walk(root):
        if dp != root and any(os.path.exists(os.path.join(dp, x)) for x in (".git", "pyvenv.cfg", "conda-meta")):
            dns[:] = []  # a nested source repository or environment is not edited
            continue
        dns[:] = [d for d in dns if not (skip_hidden and d.startswith("."))]
        for fn in fns:
            if fn.endswith(".md"):
                yield os.path.join(dp, fn)


def rewrite(text, old_dir, new_dir, M, self_moved):
    """Return (new_text, changes) with link targets remapped."""
    out, last, changes = [], 0, []
    for s, e, tgt in links(text):
        path, h, anchor = tgt.partition("#")
        t_old = os.path.normpath(os.path.join(old_dir, urllib.parse.unquote(path)))
        t_new = M.get(t_old, t_old)
        if not self_moved and t_new == t_old:
            continue
        relp = os.path.relpath(t_new, new_dir).replace("\\", "/")
        if path.endswith("/") and not relp.endswith("/"):
            relp += "/"
        new = encode_like(path, relp) + (h + anchor if h else "")
        if new != tgt:
            out += [text[last:s], new]
            last = e
            changes.append({"old": tgt, "new": new})
    out.append(text[last:])
    return "".join(out), changes


def strip_targets(text):
    parts, last, tg = [], 0, []
    for s, e, t in links(text):
        parts.append(text[last:s]); last = e; tg.append(t)
    parts.append(text[last:])
    return "\x00".join(parts), tg


def verify(old_text, new_text, old_dir, new_dir, M):
    """Only link targets may differ, and each new target must equal the mapped old one."""
    ra, ta = strip_targets(old_text)
    rb, tb = strip_targets(new_text)
    if ra != rb or len(ta) != len(tb):
        return ["text outside link targets changed"]
    bad = []
    for x, y in zip(ta, tb):
        px, _, ax = x.partition("#"); py, _, ay = y.partition("#")
        tx = os.path.normpath(os.path.join(old_dir, urllib.parse.unquote(px)))
        ty = os.path.normpath(os.path.join(new_dir, urllib.parse.unquote(py)))
        if ax != ay or M.get(tx, tx) != ty:
            bad.append(f"{x} -> {y}")
    return bad


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("topic"); ap.add_argument("moves")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--incoming", action="append", default=[], help="folder outside TOPIC to scan for links into moved files")
    ap.add_argument("--rewrite-incoming", action="store_true", help="also rewrite those incoming links")
    ap.add_argument("--frozen", action="append", default=[], help="folder-name pattern treated as a frozen copy")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    FROZEN_GLOBS.extend(a.frozen)
    root = os.path.abspath(a.topic)

    moves = []
    for n, line in enumerate(open(a.moves, encoding="utf-8"), 1):
        line = line.rstrip("\r\n")
        if not line.strip() or line.startswith("#"):
            continue
        f = line.split("\t")
        if len(f) < 2:
            sys.exit(f"{a.moves}:{n}: expected old<TAB>new<TAB>reason")
        moves.append((f[0].strip(), f[1].strip(), f[2].strip() if len(f) > 2 else ""))
    M = {}
    for o, n, _ in moves:
        po, pn = os.path.normpath(os.path.join(root, o)), os.path.normpath(os.path.join(root, n))
        for p in (po, pn):
            if not p.startswith(root + os.sep):
                sys.exit(f"refused: {p} is outside the topic")
        if is_frozen(o) or is_frozen(n):
            sys.exit(f"refused: {o} -> {n} touches a frozen copy")
        if not os.path.isfile(po):
            sys.exit(f"refused: missing source {o}")
        if os.path.exists(pn) or pn in M.values():
            sys.exit(f"refused: destination exists or repeats {n}")
        M[po] = pn

    # Plan rewrites inside TOPIC.
    plan = {}  # path -> (new_text, changes, old_dir, new_dir)
    for p in md_files(root):
        rel = os.path.relpath(p, root)
        if is_frozen(rel):
            continue
        text = read(p)
        nt, ch = rewrite(text, os.path.dirname(p), os.path.dirname(M.get(p, p)), M, p in M)
        if ch:
            plan[p] = (nt, ch, os.path.dirname(p), os.path.dirname(M.get(p, p)))
    # Incoming links from outside TOPIC.
    incoming = []
    for w in a.incoming:
        w = os.path.abspath(w)
        for p in md_files(w):
            if p.startswith(root + os.sep) or is_frozen(os.path.relpath(p, w)):
                continue
            text = read(p)
            nt, ch = rewrite(text, os.path.dirname(p), os.path.dirname(p), M, False)
            if ch:
                incoming.append({"file": p, "changes": ch})
                if a.rewrite_incoming:
                    plan[p] = (nt, ch, os.path.dirname(p), os.path.dirname(p))
    # Non-Markdown mentions of old paths inside TOPIC (reported only).
    olds = {o: [o.replace("\\", "/"), os.path.basename(root) + "/" + o.replace("\\", "/")] for o, _, _ in moves}
    mentions = []
    manifest_abs = os.path.abspath(a.manifest)
    backup_root = os.path.splitext(manifest_abs)[0] + "-backup"
    for dp, dns, fns in os.walk(root):
        if dp == backup_root or dp.startswith(backup_root + os.sep):
            dns[:] = []
            continue
        dns[:] = [d for d in dns if not d.startswith(".")]
        for fn in fns:
            if os.path.splitext(fn)[1].lower() not in TEXT_EXT:
                continue
            fp = os.path.join(dp, fn)
            if os.path.abspath(fp) == manifest_abs:
                continue
            try:
                if os.path.getsize(fp) > 5_000_000:
                    continue
                t = open(fp, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            if fn.endswith(".json") and '"topic"' in t and ('"sha256_before"' in t or '"findings"' in t):
                continue  # an earlier move manifest or checker report, not evidence naming the path
            for o, keys in olds.items():
                if any(k in t for k in keys):
                    mentions.append({"file": os.path.relpath(fp, root), "old_path": o})

    man = {"topic": root, "applied": a.apply, "moves": [], "link_rewrites": {},
           "incoming": incoming, "incoming_rewritten": a.rewrite_incoming,
           "non_markdown_mentions": mentions}
    for o, n, r in moves:
        man["moves"].append({"old_path": o, "new_path": n, "reason": r, "sha256_before": sha(os.path.join(root, o))})
    for p, (_, ch, _, _) in plan.items():
        man["link_rewrites"][os.path.relpath(p, root) if p.startswith(root + os.sep) else p] = ch
    nlinks = sum(len(v) for v in man["link_rewrites"].values())
    print(f"moves {len(moves)}; files with rewritten links {len(plan)}; links rewritten {nlinks}")
    shown = 0
    for f, ch in man["link_rewrites"].items():
        for c in ch:
            if shown < 60:
                print(f"  rewrite: {f}: {c['old']} -> {c['new']}")
            shown += 1
    if shown > 60:
        print(f"  ... {shown - 60} more in the manifest")
    print(f"incoming files linking moved paths {len(incoming)} ({sum(len(x['changes']) for x in incoming)} links) "
          f"-> {'rewritten' if a.rewrite_incoming else 'reported only'}")
    for x in incoming:
        print(f"  incoming: {x['file']} ({len(x['changes'])})")
    for x in mentions:
        print(f"  non-Markdown mention (not edited): {x['file']} names {x['old_path']}")

    if not a.apply:
        json.dump(man, open(a.manifest, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print("dry run; nothing changed; manifest written")
        return

    # Back up everything that will be moved or rewritten.
    bdir = os.path.join(os.path.splitext(os.path.abspath(a.manifest))[0] + "-backup", "before")
    if os.path.exists(bdir):
        sys.exit(f"refused: backup folder exists {bdir}")
    touched = set(M) | set(plan)
    for p in touched:
        key = os.path.relpath(p, root) if p.startswith(root + os.sep) else "_outside/" + p.lstrip("/")
        dst = os.path.join(bdir, key)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(p, dst)
    man["backup"] = bdir
    originals = {p: read(p) for p in plan}
    for entry in man["moves"]:
        po, pn = os.path.join(root, entry["old_path"]), os.path.join(root, entry["new_path"])
        os.makedirs(os.path.dirname(pn), exist_ok=True)
        os.replace(po, pn)
        entry["sha256_after_move"] = sha(pn)
        entry["identical_after_move"] = entry["sha256_after_move"] == entry["sha256_before"]
    problems = {}
    for p, (nt, _, od, nd) in plan.items():
        dest = M.get(p, p)
        with open(dest, "w", encoding="utf-8", newline="") as h:
            h.write(nt)
        bad = verify(originals[p], read(dest), od, nd, M)
        if bad:
            problems[dest] = bad
    for entry in man["moves"]:
        entry["sha256_final"] = sha(os.path.join(root, entry["new_path"]))
    man["verification"] = {"problems": problems, "passed": not problems and all(e["identical_after_move"] for e in man["moves"])}
    json.dump(man, open(a.manifest, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"applied; backup {bdir}; verification {'passed' if man['verification']['passed'] else 'FAILED'}")
    for k, v in problems.items():
        print(f"  PROBLEM {k}: {v[:3]}")
    sys.exit(0 if man["verification"]["passed"] else 1)


if __name__ == "__main__":
    main()
