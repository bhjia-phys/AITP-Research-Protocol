#!/usr/bin/env python3
"""Synthetic controls for check_topic.py and move_notes.py.

Builds a small generic topic with known defects in a temporary folder, then checks
that each defect is reported, that moves rewrite exactly the expected links, and that
unsafe moves are refused. Run: python3 test_topic_tools.py   (no arguments, no network)
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHECK = os.path.join(HERE, "check_topic.py")
MOVE = os.path.join(HERE, "move_notes.py")

FILES = {
    "knowledge/index.md": "# Index\n\n- [Gate](../topics/fam/branch/gate.md#the-gate) and [family](../topics/fam/research.md)\n",
    "topics/fam/README.md": "# Map\n\n[Main](research.md), [branch](branch/research.md), [shared](notes/shared.md),\n[long](notes/long%20name.md), [anchors](notes/anchors.md).\n",
    "topics/fam/research.md": (
        "# Family question\n\nOpening.\n\n## Current work\n\n- **Shared thread** — active · 2026-03-01. Next: a check.\n"
        "- **Branch → [branch](branch/research.md#current-work)** — contributes a bound under its stated limit.\n"
        "- **Glued date** — waiting on run · updated2026-03-02.\n\n"
        "## Account\n\nSee [knowledge](../../knowledge/index.md), [section](notes/shared.md#section-one) and [gate](branch/gate.md).\n"),
    "topics/fam/notes/shared.md": "# Shared\n\n## Section one\n\nUses [the gate](../branch/gate.md).\n",
    "topics/fam/notes/long name.md": "# Long name\n\nBack to [main](../research.md).\n",
    "topics/fam/notes/orphan.md": "# Orphan\n\nNobody links here.\n",
    "topics/fam/branch/research.md": (
        "# Branch question\r\n\r\n[Parent](../research.md).\r\n\r\n## Current work\r\n\r\n- **Bound** — active. No date given.\r\n\r\n"
        "## Account\r\n\r\nThe [gate](gate.md#the-gate), a [missing anchor](../notes/shared.md#no-such-section),\r\n"
        "a [missing file](missing.md), the [long note](../notes/long%20name.md) and `[x](nowhere.md)` in code.\r\n"
        "Math like [t^{M-m}](1-t) is not a link.\r\n\r\n```\r\n[quoted](elsewhere.md)\r\n```\r\n"),
    "topics/fam/branch/gate.md": "# Gate note\n\n## The gate\n\nParent [main](../research.md); data in [run](data/run.json).\n",
    "topics/fam/branch/data/run.json": "{}\n",
    "topics/fam/branch/tool.py": "print('at a topic root')\n",
    "topics/fam/branch/code/emit.py": "REF = 'branch/gate.md#the-gate'\n",
    "topics/fam/reports/r1/before/research.md": "# Frozen\n\n[stale](../../../nowhere.md)\n\n## Current work\n",
    "topics/fam/calculations/run1/research.md": "# Run study\n\n## Current work\n\n- **Done** — concluded · 2026-02-02.\n",
    "topics/fam/calculations/run1/run.py": "pass\n",
    "topics/fam/code/vendor/.git": "gitdir: elsewhere\n",
    "topics/fam/code/vendor/docs/guide.md": "# Guide\n\n(usage)=\n[broken](nope.md) and [ok](#usage)\n",
    "topics/fam/notes/results-backup-20260101/old.md": "# Old copy\n\n[stale](gone.md)\n",
    "topics/fam/notes/anchors.md": "# Anchors\n\n(myst-target)=\n## Mixed Case Heading\n\nSee [myst](#myst-target), [case](#Mixed-Case-Heading) and [main](../research.md).\n",
}


def build(base):
    for rel, text in FILES.items():
        p = os.path.join(base, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(text)
    return os.path.join(base, "topics", "fam")


def run(*args):
    r = subprocess.run([sys.executable, "-I", *args], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def check(topic, ws, *extra):
    out = os.path.join(os.path.dirname(topic), "check.json")
    code, text = run(CHECK, topic, "--workspace", ws, "--json", out, *extra)
    rep = json.load(open(out, encoding="utf-8"))
    kinds = sorted((f["kind"], f["where"].split(":")[0].replace(os.sep, "/")) for f in rep["findings"])
    return code, kinds, rep, text


failures = []


def expect(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        failures.append(msg)


with tempfile.TemporaryDirectory() as tmp:
    # 1. The checker finds each planted defect and nothing else.
    t1 = build(os.path.join(tmp, "a"))
    ws = os.path.join(tmp, "a", "knowledge")
    code, kinds, rep, text = check(t1, ws, "--frozen", "*-backup-*")
    want = {("broken-link", "branch/research.md"), ("broken-anchor", "branch/research.md"),
            ("root-file", "branch/tool.py"), ("loose-note", "branch/gate.md"),
            ("undated-entry", "branch/research.md"), ("unreached-note", "notes/orphan.md"),
            ("study-note", "calculations/run1/research.md")}
    expect(set(kinds) == want, f"checker reports exactly the planted defects (got {kinds})")
    expect(code == 1, "checker exits 1 when errors exist")
    expect(rep["stats"]["frozen_unresolved"] == 2, "frozen stale links (before/ and the --frozen backup) are counted, not reported")
    expect(rep["stats"]["incoming_links"] == 2, "two incoming links from the knowledge folder are seen")
    expect(rep["stats"]["external_links"] == 1, "one link leaves the topic and resolves")
    expect(rep["stats"]["nested_repositories_skipped"] == 1, "the nested source repository is skipped")
    expect(not any("results-backup" in w for _, w in kinds),
           "a --frozen backup folder is treated as frozen")

    moves = os.path.join(tmp, "moves.tsv")
    with open(moves, "w", encoding="utf-8") as f:
        f.write("branch/gate.md\tbranch/notes/gate.md\tloose note\nnotes/long name.md\tnotes/archive/long name.md\ttest encoding\n")

    # 2. Dry run changes nothing and reports incoming links and code mentions.
    man = os.path.join(tmp, "a-moves.json")
    before = {p: open(os.path.join(t1, p), "rb").read() for p in ("research.md", "branch/gate.md")}
    code, text = run(MOVE, t1, moves, "--manifest", man, "--incoming", ws)
    m = json.load(open(man, encoding="utf-8"))
    expect(code == 0 and not m["applied"], "dry run succeeds without applying")
    expect(all(open(os.path.join(t1, p), "rb").read() == b for p, b in before.items()), "dry run leaves files unchanged")
    expect(len(m["incoming"]) == 1 and len(m["incoming"][0]["changes"]) == 1, "the incoming knowledge link is reported")
    expect([x["file"].replace(os.sep, "/") for x in m["non_markdown_mentions"]] == ["branch/code/emit.py"],
           "the code string naming the old path is reported")

    # 3. Applying without --rewrite-incoming: internal links fixed, incoming break is detected.
    code, text = run(MOVE, t1, moves, "--manifest", man, "--incoming", ws, "--apply")
    m = json.load(open(man, encoding="utf-8"))
    expect(code == 0 and m["verification"]["passed"], "apply verifies identical moves and link-only edits")
    expect(os.path.isdir(m["backup"]), "backup folder was written")
    g = open(os.path.join(t1, "branch/notes/gate.md"), encoding="utf-8").read()
    expect("](../../research.md)" in g and "](../data/run.json)" in g, "moved note's outgoing links follow its new depth")
    b = open(os.path.join(t1, "branch/research.md"), encoding="utf-8", newline="").read()
    expect("](notes/gate.md#the-gate)" in b and "\r\n" in b and "](../notes/archive/long%20name.md)" in b,
           "inbound link keeps its anchor, %20 style and CRLF line endings")
    expect("`[x](nowhere.md)`" in b and "[quoted](elsewhere.md)" in b, "code spans and fences are untouched")
    expect(open(os.path.join(t1, "branch/code/emit.py")).read() == FILES["topics/fam/branch/code/emit.py"],
           "code file is not edited")
    code, kinds, rep, text = check(t1, ws)
    expect(("incoming-broken", os.path.join(tmp, "a", "knowledge", "index.md").replace(os.sep, "/")) in
           [(k, w) for k, w in kinds], "checker reports the unrewritten incoming link as broken")
    expect(("loose-note", "branch/gate.md") not in kinds, "the loose-note warning is gone after the move")

    # 3b. A manifest and backup kept inside the topic are not mistaken for live material.
    t3 = build(os.path.join(tmp, "c"))
    ws3 = os.path.join(tmp, "c", "knowledge")
    org = os.path.join(t3, "calculations", "organization-test")
    os.makedirs(org)
    man3 = os.path.join(org, "moves.json")
    run(MOVE, t3, moves, "--manifest", man3, "--incoming", ws3)                      # dry run first
    code, text = run(MOVE, t3, moves, "--manifest", man3, "--incoming", ws3, "--apply")
    m3 = json.load(open(man3, encoding="utf-8"))
    expect(code == 0 and m3["verification"]["passed"] and "/before" in m3["backup"].replace(os.sep, "/"),
           "apply with the manifest inside the topic passes and backs up under before/")
    expect(not any(x["file"].startswith("calculations") for x in m3["non_markdown_mentions"]),
           "the earlier dry-run manifest is not reported as a mention of the old path")
    code, kinds, rep, text = check(t3, ws3, "--frozen", "*-backup-*")
    expect(not any("organization-test" in w for _, w in kinds), "the in-topic backup is treated as frozen by the checker")
    expect("rewrite: research.md: branch/gate.md -> branch/notes/gate.md" in run(MOVE, build(os.path.join(tmp, "d")), moves,
           "--manifest", os.path.join(tmp, "d.json"))[1], "the dry run prints each link rewrite")

    # 4. With --rewrite-incoming the outside link is repaired too.
    t2 = build(os.path.join(tmp, "b"))
    ws2 = os.path.join(tmp, "b", "knowledge")
    man2 = os.path.join(tmp, "b-moves.json")
    code, text = run(MOVE, t2, moves, "--manifest", man2, "--incoming", ws2, "--rewrite-incoming", "--apply")
    k = open(os.path.join(ws2, "index.md"), encoding="utf-8").read()
    expect(code == 0 and "../topics/fam/branch/notes/gate.md#the-gate" in k, "incoming link rewritten on request")
    code, kinds, rep, text = check(t2, ws2)
    expect(not any(x[0].startswith("incoming") for x in kinds), "no incoming problems after the rewrite")

    # 5. Unsafe moves are refused.
    for line, why in [("reports/r1/before/research.md\tnotes/x.md\t", "a frozen source"),
                      ("notes/shared.md\tresearch.md\t", "an existing destination"),
                      ("notes/none.md\tnotes/y.md\t", "a missing source"),
                      ("notes/shared.md\t../escape.md\t", "a destination outside the topic")]:
        bad = os.path.join(tmp, "bad.tsv")
        open(bad, "w", encoding="utf-8").write(line + "\n")
        code, text = run(MOVE, t2, bad, "--manifest", os.path.join(tmp, "bad.json"))
        expect(code != 0 and "refused" in text, f"refuses a move with {why}")

print(f"{len(failures)} failure(s)")
sys.exit(1 if failures else 0)
