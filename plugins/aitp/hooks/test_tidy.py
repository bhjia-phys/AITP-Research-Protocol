#!/usr/bin/env python3
"""Synthetic controls for tidy.py, the end-of-reply architecture check. Run: python3 test_tidy.py"""
import json, os, subprocess, sys, tempfile, time
from datetime import datetime, timezone

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tidy.py")
failures = []


def expect(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        failures.append(msg)


def run(home, args, event, env_extra=None):
    env = dict(os.environ, HOME=home)
    env.pop("AITP_TIDY", None)
    env.update(env_extra or {})
    r = subprocess.run([sys.executable, "-I", HOOK, *args], input=json.dumps(event), capture_output=True, text=True, env=env)
    return r.returncode, r.stdout.strip()


def write(p, text="x\n", mtime=None):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(text)
    if mtime is not None:
        os.utime(p, (mtime, mtime))


def iso(t):
    return datetime.fromtimestamp(t, timezone.utc).isoformat().replace("+00:00", "Z")


with tempfile.TemporaryDirectory() as tmp:
    home = os.path.join(tmp, "home"); os.makedirs(home)
    topic = os.path.join(tmp, "topics", "demo")
    other = os.path.join(tmp, "topics", "other")
    old = time.time() - 86400
    write(os.path.join(topic, "research.md"), "# Demo\n", old)
    write(os.path.join(topic, "notes", "old.md"), mtime=old)
    write(os.path.join(other, "research.md"), "# Other\n", old)
    outside = os.path.join(tmp, "elsewhere"); os.makedirs(outside)
    ev = {"session_id": "s1", "cwd": os.path.join(topic, "notes")}

    code, out = run(home, ["--turn-start"], ev)
    expect(code == 0 and out == "", "turn start prints nothing")
    code, out = run(home, ["--reply-end"], ev)
    expect(code == 0 and out == "", "a reply that changed nothing ends silently")

    time.sleep(0.05)
    after = None  # real modification times, later than the recorded turn start
    write(os.path.join(topic, "stray_script.py"), mtime=after)                 # main agent's shell command
    write(os.path.join(topic, "notes", "subagent-derivation.md"), mtime=after)  # a subagent's file
    for skipped in ("__pycache__/x.pyc", ".venv/lib/x.py", "reports/r1/before/research.md",
                    "manuscripts/p/provenance/snapshots/main.tex", ".scratch/t.txt"):
        write(os.path.join(topic, skipped), mtime=after)
    write(os.path.join(topic, "code", "vendor", ".git", "HEAD"), mtime=after)
    write(os.path.join(topic, "code", "vendor", "README.md"), mtime=after)     # inside a nested repository
    code, out = run(home, ["--reply-end"], ev)
    d = json.loads(out) if out else {}
    reason = d.get("reason", "")
    expect(d.get("decision") == "block", "a reply that changed topic files asks once for the check")
    expect("stray_script.py" in reason and "subagent-derivation.md" in reason,
           "files changed during the reply are listed, including shell and subagent changes")
    expect(not any(s in reason for s in ("__pycache__", ".venv", "/before/", "snapshots", "vendor", ".scratch")),
           "caches, environments, frozen copies and nested repositories are not listed")
    expect("end without further comment" in reason and "never delete" in reason, "the request states the check and its limits")

    code, out = run(home, ["--reply-end"], dict(ev, stop_hook_active=True))
    expect(out == "", "the hook is silent during its own continuation (stop_hook_active)")
    code, out = run(home, ["--reply-end"], ev, {"AITP_TIDY": "off"})
    expect(out == "", "AITP_TIDY=off disables the check")

    time.sleep(0.05)
    run(home, ["--turn-start"], ev)
    code, out = run(home, ["--reply-end"], ev)
    expect(out == "", "the next reply does not report the previous reply's changes")

    # Edits in another topic, known only from the transcript, while the session sits outside any topic.
    t0 = time.time() + 5
    other_note = os.path.join(other, "notes", "new.md")
    write(other_note, mtime=t0 + 1)
    tr = os.path.join(tmp, "transcript.jsonl")
    rows = [
        {"type": "user", "timestamp": iso(t0), "message": {"role": "user", "content": "please write the note"}},
        {"type": "assistant", "timestamp": iso(t0 + 1), "message": {"role": "assistant", "content": [
            {"type": "tool_use", "name": "Write", "input": {"file_path": other_note, "content": "x"}}]}},
        {"type": "user", "timestamp": iso(t0 + 2), "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "1", "content": "ok"}]}},
    ]
    open(tr, "w").write("\n".join(json.dumps(r) for r in rows) + "\n")
    ev2 = {"session_id": "s2", "cwd": outside, "transcript_path": tr}
    code, out = run(home, ["--reply-end"], ev2)
    expect("other/notes/new.md" in out,
           "an edit in another topic, seen in the transcript, is listed; without a recorded turn start the last user message is used")
    expect(not os.path.exists(os.path.join(topic, ".aitp")) and not any(f.endswith(".json") for f in os.listdir(topic)),
           "the hook writes nothing inside a topic")

    code, out = run(home, ["--reply-end"], {"session_id": "s3", "cwd": outside})
    expect(out == "", "outside a topic with no transcript edits the hook is silent")

    # A reply that asks the researcher for a decision: the next prompt is reminded to record the answer.
    def cue_after(session, stop_event, env=None):
        run(home, ["--turn-start"], {"session_id": session, "cwd": outside})
        run(home, ["--reply-end"], dict({"session_id": session, "cwd": outside}, **stop_event), env)
        return run(home, ["--turn-start"], {"session_id": session, "cwd": outside}, env)[1]

    ask = ("Two options remain.\n\n**Decision needed:** use unfolding-free ratios as the primary statistic?\n"
           "Options: A — ratios · B — unfolded spacings\nI recommend: A\nMeanwhile: the L ≤ 20 tables continue.")
    out = cue_after("d1", {"last_assistant_message": ask})
    d = json.loads(out) if out else {}
    ctx = (d.get("hookSpecificOutput") or {}).get("additionalContext", "")
    expect(d.get("hookSpecificOutput", {}).get("hookEventName") == "UserPromptSubmit" and "researcher's own words" in ctx
           and "Never record a decision" in ctx,
           "after a reply with 'Decision needed:', the next prompt gets one reminder to record the answer")
    code, out = run(home, ["--turn-start"], {"session_id": "d1", "cwd": outside})
    expect(out == "", "the reminder is given once, not on every later prompt")

    out = cue_after("d2", {"last_assistant_message": "需要你决定：先做 L=22 还是先写文章？\n选项：A · B"})
    expect("additionalContext" in out, "a request written in Chinese is recognized")

    out = cue_after("d3", {"last_assistant_message": "Give each request this form:\n\n```text\nDecision needed: <one question>\n```"})
    expect(out == "", "a quoted template line with a placeholder is not a request")

    out = cue_after("d4", {"last_assistant_message": "We decided to use ratios; the decision needed no input."})
    expect(out == "", "ordinary prose about decisions is not a request")

    out = cue_after("d5", {"last_assistant_message": ask, "stop_hook_active": True})
    expect("additionalContext" in out, "a request in the reply that follows the architecture check is still seen")

    out = cue_after("d6", {"last_assistant_message": ask}, {"AITP_TIDY": "off"})
    expect(out == "", "AITP_TIDY=off disables the reminder too")

    tr2 = os.path.join(tmp, "transcript-ask.jsonl")
    t1 = time.time()
    rows = [
        {"type": "user", "timestamp": iso(t1), "message": {"role": "user", "content": "which statistic?"}},
        {"type": "assistant", "timestamp": iso(t1 + 1), "message": {"role": "assistant", "content": [
            {"type": "text", "text": ask}]}},
    ]
    open(tr2, "w").write("\n".join(json.dumps(r) for r in rows) + "\n")
    out = cue_after("d7", {"transcript_path": tr2})
    expect("additionalContext" in out, "without last_assistant_message, the Claude Code transcript is read")

    sub = [dict(rows[0]), {"type": "assistant", "isSidechain": True, "timestamp": iso(t1 + 1),
                           "message": {"role": "assistant", "content": [{"type": "text", "text": ask}]}}]
    tr3 = os.path.join(tmp, "transcript-sub.jsonl")
    open(tr3, "w").write("\n".join(json.dumps(r) for r in sub) + "\n")
    out = cue_after("d8", {"transcript_path": tr3})
    expect(out == "", "a subagent's text is not the main reply's request")

    # The reply check mentions the pending question when the asking reply also changed files.
    run(home, ["--turn-start"], ev)
    time.sleep(0.05)  # file times use a coarse clock: write clearly after the recorded start
    write(os.path.join(topic, "notes", "choice.md"))
    code, out = run(home, ["--reply-end"], dict(ev, last_assistant_message=ask))
    expect("waiting on the researcher" in out, "a reply that asks and changes files is checked for its waiting entry")
    code, out = run(home, ["--reply-end"], dict(ev, last_assistant_message="Done."))
    expect("block" in out and "waiting on the researcher" not in out, "a reply that does not ask is not asked about it")

    # The size budget: a big main note.
    big = os.path.join(tmp, "topics", "big")
    entries = "".join(f"- **Thread {i}** — active · 2026-11-01. Next: step {i}.\n" for i in range(9))
    body = "# Big\n\n" + "Opening line.\n" * 35 + "## Current work\n\n" + entries + "\n## Account\n\n" + "Account line.\n" * 500
    write(os.path.join(big, "research.md"), body, old)
    evb = {"session_id": "b1", "cwd": big}
    code, out = run(home, ["--turn-start"], evb)
    ctx = (json.loads(out).get("hookSpecificOutput") or {}).get("additionalContext", "") if out else ""
    expect("over its size budget" in ctx and "lines (budget 400)" in ctx and "opening 37 lines" in ctx
           and "do not start it without their agreement" in ctx and "entries" not in ctx,
           "the first prompt in an over-budget topic asks to offer the pass, naming length and opening only")
    code, out = run(home, ["--turn-start"], {"session_id": "b2", "cwd": big})
    expect(out == "", "the offer is not repeated within a day, across sessions")
    code, out = run(home, ["--turn-start"], {"session_id": "b3", "cwd": topic})
    expect(out == "", "a topic within its budget gets no offer")

    import hashlib
    sf = os.path.join(home, ".cache", "aitp", "topics", hashlib.sha1(big.encode("utf-8")).hexdigest()[:16] + ".json")
    n_big = len(body.splitlines())
    json.dump({"offered": time.time() - 2 * 86400, "lines": n_big, "topic": big}, open(sf, "w"))
    code, out = run(home, ["--turn-start"], {"session_id": "b4", "cwd": big})
    expect(out == "", "after a day, an unchanged long note (an accepted length) gets no new offer")
    json.dump({"offered": time.time() - 2 * 86400, "lines": int(n_big / 1.2), "topic": big}, open(sf, "w"))
    code, out = run(home, ["--turn-start"], {"session_id": "b5", "cwd": big})
    expect("over its size budget" in out, "after a day and 10% growth since the last offer, the offer returns")

    run(home, ["--turn-start"], evb)
    time.sleep(0.05)
    with open(os.path.join(big, "research.md"), "a") as fh:
        fh.write("Another account line.\n" * 3)
    code, out = run(home, ["--reply-end"], evb)
    expect("grew from" in out and "budget 400" in out and "only add" in out and "offer" not in out.split("Size:")[1].split("\n\n")[0],
           "a reply that grew an over-budget main note asks whether it replaced or only added, without asking for an offer")
    run(home, ["--turn-start"], evb)
    time.sleep(0.05)
    txt = open(os.path.join(big, "research.md")).read().replace("Another account line.", "Rewritten account line.", 1)
    open(os.path.join(big, "research.md"), "w").write(txt)
    code, out = run(home, ["--reply-end"], evb)
    expect("block" in out and "grew from" not in out, "a reply that rewrote the note without growing it gets no size line")
    run(home, ["--turn-start"], ev)
    time.sleep(0.05)
    write(os.path.join(topic, "research.md"), "# Demo\n\nSmall.\n")
    code, out = run(home, ["--reply-end"], ev)
    expect("block" in out and "grew from" not in out, "a changed main note within budget gets no size line")

    r = subprocess.run([sys.executable, "-I", HOOK, "--status", big, "--hours", "1"], capture_output=True, text=True,
                       env=dict(os.environ, HOME=home))
    expect("over budget" in r.stdout and "opening 37 lines" in r.stdout, "--status reports the note's size against the budget")

    # An unanswered question must not be lost: the reminder says to leave it waiting on record.
    out = cue_after("d9", {"last_assistant_message": ask})
    expect("names the question" in out, "the reminder asks to keep an unanswered question on record")

print(f"{len(failures)} failure(s)")
sys.exit(1 if failures else 0)
