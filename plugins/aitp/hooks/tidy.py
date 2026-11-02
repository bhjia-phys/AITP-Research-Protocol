#!/usr/bin/env python3
"""AITP end-of-reply check: did this reply's changes keep the topic's architecture?

Two hook entry points (stdin is the host's hook event JSON):
  python3 tidy.py --turn-start   UserPromptSubmit: remember when this reply began; if the previous
                                 reply asked the researcher for a decision, remind this reply
                                 to record the answer (the only output of this entry point)
  python3 tidy.py --reply-end    Stop: list the files this reply changed and, if any, ask once
                                 for the check in skills/aitp-memory/references/tidy.md

The same entry points watch a main note's size budget (BUDGET below, from aitp-writing's
research-note.md): the Stop check names a changed research.md that is over budget, and the first
prompt of a day in an over-budget topic carries one line asking to offer the consolidation pass.

"Asked for a decision" means the reply contains a request line "Decision needed:", the form
that aitp-human-brainstorming gives every request; it is read from the Stop event's
last_assistant_message (Claude Code and Codex) or from the Claude Code transcript.
Manual use:
  python3 tidy.py --status [DIR] [--hours H]   files changed in DIR's topic in the last H hours

"Changed in this reply" is the union of two sets:
- every file in the session's topic (the nearest folder above the working directory that holds
  research.md) whose modification time is after the reply began. This covers the main agent's
  edits, its shell commands and the work of its subagents;
- the files that the main transcript's Write, Edit, MultiEdit or NotebookEdit calls touched
  since the last user message, when they lie in a topic.

It skips hidden folders, environments, nested repositories, caches, build output and frozen
before/ and provenance/snapshots/ copies. It stays silent when:
- nothing changed;
- the session is outside a topic and edited none;
- the stop is the hook's own continuation (stop_hook_active);
- AITP_TIDY is "off" or "0".

The check itself is done by the agent, following the rules. Nothing is moved or applied by this
script, and it writes nothing inside a topic; its only state is the turn start and whether a
decision was asked, kept in ~/.cache/aitp/turns/. Standard library only.
"""
import hashlib, json, os, re, sys, time
from datetime import datetime

# A request line, not a quoted template ("Decision needed: <one question>").
DECISION = re.compile(r"(?m)^[\s>*_`#-]*(?:Decision needed|需要(?:你|您)?决定)\s*(?:\*\*)?\s*[:：](?!\s*(?:\*\*)?\s*<)")
DECISION_CUE = (
    "AITP: your previous reply asked the researcher for a decision ('Decision needed:'). If this "
    "message answers it, record the decision where the work it constrains will see it: the owning "
    "research.md's decisions format, with the date, the scope and the researcher's own words, and "
    "update the Current work entry that was waiting. If it does not answer it, that entry stays "
    "'waiting on the researcher'. Never record a decision the researcher did not make."
)

SKIP_DIRS = {"__pycache__", "node_modules", "build", "dist", "before", ".venv", "venv"}
EDIT_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
LIST_MAX = 20
SCAN_BUDGET_S = 3.0
STATE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "aitp", "turns")
TOPIC_STATE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "aitp", "topics")
# The main-note size budget of aitp-writing's research-note.md; past it, a consolidation pass is offered.
BUDGET = {"lines": 400, "opening": 30, "entries": 7}
OFFER_INTERVAL_S = 86400
HERE = os.path.dirname(os.path.abspath(__file__))
RULES = os.path.normpath(os.path.join(HERE, "..", "skills", "aitp-memory", "references", "tidy.md"))


def find_topic(start):
    d = os.path.abspath(start)
    if os.path.isfile(d):
        d = os.path.dirname(d)
    while True:
        if os.path.isfile(os.path.join(d, "research.md")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def state_file(session):
    return os.path.join(STATE_DIR, hashlib.sha1(str(session).encode("utf-8")).hexdigest()[:16] + ".json")


def skipped(rel):
    parts = rel.split("/")
    if any(p.startswith(".") or p in SKIP_DIRS for p in parts[:-1]) or parts[-1].startswith("."):
        return True
    if "provenance" in parts and "snapshots" in parts:
        return True
    return parts[-1].endswith((".pyc", ".swp", "~"))


def changed_in(topic, since):
    """Files under topic modified after since: (list of rel, complete)."""
    out, t0 = [], time.time()
    for dp, dns, fns in os.walk(topic):
        if dp != topic and any(os.path.exists(os.path.join(dp, x)) for x in (".git", "pyvenv.cfg", "conda-meta")):
            dns[:] = []
            continue
        rel_dir = os.path.relpath(dp, topic).replace(os.sep, "/")
        dns[:] = [d for d in dns if not d.startswith(".") and d not in SKIP_DIRS
                  and not (d == "snapshots" and rel_dir.split("/")[-1] == "provenance")]
        for fn in fns:
            rel = (fn if rel_dir == "." else rel_dir + "/" + fn)
            if skipped(rel):
                continue
            try:
                if os.stat(os.path.join(dp, fn)).st_mtime > since:
                    out.append(rel)
            except OSError:
                pass
        if time.time() - t0 > SCAN_BUDGET_S:
            return sorted(out), False
    return sorted(out), True


def parse_time(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def transcript_edits(path):
    """(time of the last user message, files edited after it, whether a reply after it asked for
    a decision) from a Claude Code transcript. Other formats yield (None, [], False)."""
    last_user, edits, asked = None, [], False
    try:
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        return None, [], False
    for line in lines:
        try:
            e = json.loads(line)
        except ValueError:
            continue
        msg = e.get("message") or {}
        content = msg.get("content")
        if e.get("type") == "user" and not e.get("isSidechain"):
            is_tool_result = isinstance(content, list) and any(
                isinstance(c, dict) and c.get("type") == "tool_result" for c in content)
            if not is_tool_result:
                last_user, edits, asked = parse_time(e.get("timestamp")), [], False
        elif e.get("type") == "assistant" and isinstance(content, list) and not e.get("isSidechain"):
            for c in content:
                if not isinstance(c, dict):
                    continue
                if c.get("type") == "tool_use" and c.get("name") in EDIT_TOOLS:
                    p = (c.get("input") or {}).get("file_path") or (c.get("input") or {}).get("notebook_path")
                    if p:
                        edits.append(p)
                elif c.get("type") == "text" and DECISION.search(c.get("text") or ""):
                    asked = True
    return last_user, edits, asked


def read_event():
    try:
        return json.load(sys.stdin)
    except ValueError:
        return {}


def load_state(event):
    try:
        return json.load(open(state_file(event.get("session_id", "default")), encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(event, state):
    os.makedirs(STATE_DIR, exist_ok=True)
    json.dump(state, open(state_file(event.get("session_id", "default")), "w", encoding="utf-8"))


def note_size(path):
    """(lines, opening lines, Current work entries) of a main note, or None if unreadable."""
    try:
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        return None
    heads = [i for i, line in enumerate(lines) if line.startswith("## ")]
    opening = heads[0] if heads else len(lines)
    entries = 0
    cw = next((i for i in heads if re.match(r"## +Current work", lines[i])), None)
    if cw is not None:
        end = next((h for h in heads if h > cw), len(lines))
        entries = sum(1 for line in lines[cw:end] if re.match(r"- +\*\*", line))
    return len(lines), opening, entries


def over_budget(path):
    """The parts of a main note that exceed the size budget, as short phrases."""
    size = note_size(path)
    if not size:
        return []
    n, opening, entries = size
    out = []
    if n > BUDGET["lines"]:
        out.append(f"{n} lines (budget {BUDGET['lines']})")
    if opening > BUDGET["opening"]:
        out.append(f"opening {opening} lines ({BUDGET['opening']})")
    if entries > BUDGET["entries"]:
        out.append(f"Current work {entries} entries ({BUDGET['entries']})")
    return out


def consolidation_offer(event):
    """Once a day per topic, when the session's topic note is over budget: a line asking to offer the pass."""
    topic = find_topic(event.get("cwd") or os.getcwd())
    if not topic:
        return None
    note = os.path.join(topic, "research.md")
    over = over_budget(note)
    if not over:
        return None
    f = os.path.join(TOPIC_STATE_DIR, hashlib.sha1(topic.encode("utf-8")).hexdigest()[:16] + ".json")
    try:
        last = json.load(open(f, encoding="utf-8"))["offered"]
    except (OSError, ValueError, KeyError):
        last = 0
    if time.time() - last < OFFER_INTERVAL_S:
        return None
    os.makedirs(TOPIC_STATE_DIR, exist_ok=True)
    json.dump({"offered": time.time(), "topic": topic}, open(f, "w", encoding="utf-8"))
    return (f"AITP: {note} is over its size budget: {', '.join(over)}. At a natural point in this "
            f"session, offer the researcher a consolidation pass ({RULES}, 'The consolidation pass'); "
            "do not start it without their agreement.")


def turn_start(event):
    previous = load_state(event)
    save_state(event, {"start": time.time(), "cwd": event.get("cwd") or os.getcwd()})
    if os.environ.get("AITP_TIDY", "").lower() not in ("off", "0", "false"):
        context = [DECISION_CUE] if previous.get("decision_asked") else []
        offer = consolidation_offer(event)
        if offer:
            context.append(offer)
        if context:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                                     "additionalContext": "\n\n".join(context)}}))
    now = time.time()
    for name in os.listdir(STATE_DIR):  # forget turns older than a week
        p = os.path.join(STATE_DIR, name)
        try:
            if now - os.stat(p).st_mtime > 7 * 86400:
                os.remove(p)
        except OSError:
            pass
    return 0


def reply_end(event):
    if os.environ.get("AITP_TIDY", "").lower() in ("off", "0", "false"):
        return 0
    cwd = event.get("cwd") or os.getcwd()
    state = load_state(event)
    start = state.get("start")
    t_user, edited, asked = (transcript_edits(event["transcript_path"]) if event.get("transcript_path")
                             else (None, [], False))
    asked = asked or bool(DECISION.search(str(event.get("last_assistant_message") or "")))
    if asked and not state.get("decision_asked"):  # recorded on every stop, continuations included
        state["decision_asked"] = True
        save_state(event, state)
    if event.get("stop_hook_active"):
        return 0
    if start is None:
        start = t_user
    if start is None:
        return 0
    by_topic, complete = {}, True
    topic = find_topic(cwd)
    if topic:
        files, complete = changed_in(topic, start)
        if files:
            by_topic[topic] = set(files)
    for p in edited:
        p = os.path.abspath(p)
        t = find_topic(p)
        if t and os.path.exists(p):
            rel = os.path.relpath(p, t).replace(os.sep, "/")
            if not skipped(rel):
                by_topic.setdefault(t, set()).add(rel)
    if not by_topic:
        return 0
    lines, n = [], 0
    for t in sorted(by_topic):
        for rel in sorted(by_topic[t]):
            n += 1
            if n <= LIST_MAX:
                lines.append(f"  - {os.path.join(t, rel)}")
    if n > LIST_MAX:
        lines.append(f"  - … and {n - LIST_MAX} more")
    sizes = []
    for t in sorted(by_topic):
        for rel in sorted(by_topic[t]):
            if os.path.basename(rel) == "research.md":
                over = over_budget(os.path.join(t, rel))
                if over:
                    sizes.append(f"  - {os.path.join(t, rel)}: {', '.join(over)}")
    size_note = ("Size: these changed main notes are over their budget:\n" + "\n".join(sizes) + "\nDid this "
                 "reply replace passages rather than only add to them? Do not consolidate now; offer the "
                 "consolidation pass to the researcher.\n\n") if sizes else ""
    note = "" if complete else " (the scan stopped at its time budget; the list may be incomplete)"
    reason = (
        f"AITP reply check: this reply changed {n} file(s) in research topics{note}:\n" + "\n".join(lines) + "\n\n"
        + size_note +
        f"Before ending, check these changes against the topic architecture ({RULES}). For each file: is it in "
        "the home its kind and question use (the topic's README map and placement rules), and is it linked "
        "from the research.md passage, or the note, that uses its result? If a thread's state changed, does "
        "its Current work entry say so? If a result's strength changed, do the parent passage and story.md "
        "that use it still agree? " + ("This reply asks the researcher for a decision: does the owning "
        "Current work entry say 'waiting on the researcher'? " if asked else "") +
        "Fix clear misplacements of files this reply created or changed, "
        "within the task's scope. List anything else for the researcher in at most five lines. Never change a "
        "number or conclusion, never delete, and leave frozen copies and other people's files to the "
        "researcher. If everything fits, say in one line: 'architecture check: ok'."
    )
    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


def status(argv):
    hours = 24.0
    if "--hours" in argv:
        i = argv.index("--hours")
        hours = float(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    topic = find_topic(argv[0] if argv else os.getcwd())
    if not topic:
        print("not inside a research topic (no research.md above this folder)")
        return 1
    files, complete = changed_in(topic, time.time() - hours * 3600)
    print(f"{topic}: {len(files)} file(s) changed in the last {hours:g} h" + ("" if complete else " (incomplete scan)"))
    size = note_size(os.path.join(topic, "research.md"))
    if size:
        over = over_budget(os.path.join(topic, "research.md"))
        print(f"research.md: {size[0]} lines, opening {size[1]} lines, {size[2]} Current work entries"
              + (f"; over budget: {', '.join(over)}" if over else "; within budget"))
    for rel in files:
        print(f"  {rel}")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--turn-start"]:
        sys.exit(turn_start(read_event()))
    if args[:1] == ["--status"]:
        sys.exit(status(args[1:]))
    sys.exit(reply_end(read_event()))
