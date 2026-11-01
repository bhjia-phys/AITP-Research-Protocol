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
    expect("architecture check: ok" in reason and "never delete" in reason, "the request states the check and its limits")

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

print(f"{len(failures)} failure(s)")
sys.exit(1 if failures else 0)
