"""Shared panel rendering for AITP status displays.

Provides clean box-drawing dashboard panels for both HUD statusline
(compact panel) and context injection (full dashboard).
"""
import os
import re
import sys
import json as _json
from pathlib import Path

# ── ANSI color helpers ──────────────────────────────────────────
C = "\033[36m"; G = "\033[32m"; Y = "\033[33m"
R = "\033[31m"; M = "\033[35m"; B = "\033[34m"
W = "\033[37m"; D = "\033[90m"; Z = "\033[0m"

# ── Unicode / ASCII mode ────────────────────────────────────────
_UNI = os.environ.get("AITP_PANEL_UNICODE", "").lower() in {"1", "true", "yes"}

if _UNI:
    _TL="┌"; _TR="┐"; _BL="└"; _BR="┘"; _HZ="─"; _VT="│"
    _DL="═"; _DV="║"; _D_tl="╔"; _D_tr="╗"; _D_bl="╚"; _D_br="╝"; _D_xl="╠"
    _CHK="✓"; _X="✗"; _TRI="△"; _ARR="→"; _UP="⬆"; _DOT="·"
else:
    _TL="+"; _TR="+"; _BL="+"; _BR="+"; _HZ="-"; _VT="|"
    _DL="="; _DV="|"; _D_tl="+"; _D_tr="+"; _D_bl="+"; _D_br="+"; _D_xl="+"
    _CHK="v"; _X="x"; _TRI="~"; _ARR=">"; _UP="^"; _DOT="."

# ── Path resolution ─────────────────────────────────────────────
_TOPICS_ROOT = None

def _resolve_topics_root():
    global _TOPICS_ROOT
    if _TOPICS_ROOT is not None:
        return _TOPICS_ROOT
    env = os.environ.get("AITP_TOPICS_ROOT", "")
    if env and Path(env).is_dir():
        _TOPICS_ROOT = Path(env)
    else:
        configured = Path("{{TOPICS_ROOT}}")
        _TOPICS_ROOT = configured if configured.is_dir() else Path.cwd() / "research" / "aitp-topics"
    return _TOPICS_ROOT


def _read_session_map(root):
    smap_file = root / ".session_map.json"
    if smap_file.exists():
        try:
            return _json.loads(smap_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _write_session_map(root, smap):
    smap_file = root / ".session_map.json"
    try:
        smap_file.write_text(_json.dumps(smap, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


_SESSION_ID = None

def set_session_id(sid):
    global _SESSION_ID
    _SESSION_ID = sid


def get_session_id():
    global _SESSION_ID
    if _SESSION_ID:
        return _SESSION_ID
    env = os.environ.get("AITP_SESSION_ID", "")
    if env:
        _SESSION_ID = env
        return env
    return None


def get_active_topic():
    """Resolve the active topic for the current session.

    ONLY uses per-session mapping (.session_map.json).
    No global fallback — sessions not explicitly bound to an AITP
    topic will return None, keeping non-AITP conversations clean.
    """
    root = _resolve_topics_root()
    sid = get_session_id()
    if sid:
        smap = _read_session_map(root)
        slug = smap.get(sid, "")
        if slug and (root / slug / "state.md").exists():
            return slug
    return None


def parse_frontmatter(text):
    fm = {}
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].splitlines():
                s = line.strip()
                if ":" in s:
                    k, _, v = s.partition(":")
                    fm[k.strip()] = v.strip().strip("\"'")
    return fm


def _parse_md_yaml(path):
    """Parse markdown with YAML frontmatter (for state model)."""
    import yaml
    if not path.exists():
        return {}, ""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not m:
        return {}, text
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


_GATE_CACHE = {}

def evaluate_topic_gate(topic_slug):
    """Run state model evaluation for real-time gate status.

    Cached by state.md mtime — only re-evaluates when state changes.
    """
    root = _resolve_topics_root()
    state_file = root / topic_slug / "state.md"
    if not state_file.exists():
        return None

    try:
        mtime = state_file.stat().st_mtime
    except OSError:
        return None

    if topic_slug in _GATE_CACHE:
        cached_mtime, cached_result = _GATE_CACHE[topic_slug]
        if cached_mtime == mtime:
            return cached_result

    _aitp_repo = os.environ.get("AITP_REPO_ROOT", "{{REPO_ROOT}}")
    if _aitp_repo not in sys.path:
        sys.path.insert(0, _aitp_repo)

    try:
        from brain.state_model import evaluate_l3_stage, evaluate_l4_stage
    except ImportError:
        return None

    fm = parse_frontmatter(state_file.read_text(encoding="utf-8"))
    stage = fm.get("stage", "L1")
    lane = fm.get("lane", "unspecified")
    topic_dir = root / topic_slug

    try:
        if stage == "L3":
            snapshot = evaluate_l3_stage(_parse_md_yaml, topic_dir, lane=lane)
        elif stage == "L4":
            snapshot = evaluate_l4_stage(_parse_md_yaml, topic_dir, lane=lane)
        else:
            from brain.state_model import evaluate_l0_stage, evaluate_l1_stage
            if stage == "L0":
                snapshot = evaluate_l0_stage(_parse_md_yaml, topic_dir, lane=lane)
            else:
                snapshot = evaluate_l1_stage(_parse_md_yaml, topic_dir, lane=lane)
    except Exception:
        return None

    result = {
        "stage": getattr(snapshot, "stage", stage),
        "posture": getattr(snapshot, "posture", ""),
        "gate_status": getattr(snapshot, "gate_status", ""),
        "l3_subplane": getattr(snapshot, "l3_subplane", ""),
        "required_artifact": getattr(snapshot, "required_artifact_path", ""),
        "domain_constraints": getattr(snapshot, "domain_constraints", {}),
    }

    if result["gate_status"].startswith("blocked"):
        missing = result["gate_status"].replace("blocked_", "").replace("_", " ")
        result["gate_detail"] = missing
        if result["required_artifact"]:
            result["gate_detail"] = f"{missing} — fill {result['required_artifact']}"
    else:
        result["gate_detail"] = ""

    _GATE_CACHE[topic_slug] = (mtime, result)
    return result


def record_session_topic(sid, topic_slug):
    """Record that a session is working on a specific topic."""
    if not sid or not topic_slug:
        return
    root = _resolve_topics_root()
    smap = _read_session_map(root)
    smap[sid] = topic_slug
    _write_session_map(root, smap)
    # Also update global marker for backwards compatibility
    marker = root / ".current_topic"
    try:
        marker.write_text(topic_slug, encoding="utf-8")
    except Exception:
        pass


def read_topic_state(topic_slug):
    root = _resolve_topics_root()
    sf = root / topic_slug / "state.md"
    if not sf.exists():
        return None
    return parse_frontmatter(sf.read_text(encoding="utf-8"))


# ── Status helpers ──────────────────────────────────────────────

def _gate_icon(gate_status):
    if gate_status in ("passed", "clean"):
        return f"{G}{_CHK}{Z}", "passed"
    elif gate_status.startswith("blocked"):
        return f"{R}{_X}{Z}", gate_status.replace("blocked_", "").replace("_", " ")
    elif gate_status in ("not_evaluated", ""):
        return f"{Y}{_TRI}{Z}", "pending"
    else:
        return f"{Y}{_TRI}{Z}", gate_status


def _l4_display(l4_status):
    if l4_status == "submitted":
        return f"{Y}{_UP}{Z} submitted"
    elif l4_status == "running":
        return f"{Y}...{Z} running"
    elif l4_status == "complete":
        return f"{G}{_CHK}{Z} done"
    elif l4_status == "failed":
        return f"{R}{_X}{Z} failed"
    return l4_status


def _lane_short(lane):
    return {"code_method": "code", "formal_theory": "formal", "toy_numeric": "toy"}.get(lane, lane)


def _stage_str(fm):
    stage = fm.get("stage", "?")
    posture = fm.get("posture", "") or fm.get("l3_activity", "")
    return f"{stage}/{posture}" if posture else stage


def _vislen(s):
    return len(re.sub(r"\033\[[0-9;]*m", "", s))


def _pad(s, width):
    need = width - _vislen(s)
    return s + " " * max(0, need)


def _width():
    try:
        return os.get_terminal_size().columns
    except Exception:
        pass
    try:
        return int(os.environ.get("COLUMNS", 0)) or 80
    except Exception:
        return 80


# ── HUD panel (5-line detailed dashboard) ───────────────────────

def render_hud_panel(fm, topic_slug, gate_info=None):
    w = min(_width(), 100)
    inner = w - 2
    rpad = inner // 2 + 3

    stage = _stage_str(fm)
    if gate_info:
        gate_status = gate_info.get("gate_status", fm.get("gate_status", ""))
        gate_detail = gate_info.get("gate_detail", "")
    else:
        gate_status = fm.get("gate_status", "")
        gate_detail = ""
    gate_icon, gate_label = _gate_icon(gate_status)
    lane = _lane_short(fm.get("lane", ""))
    status = fm.get("status", "")
    sources = fm.get("sources_count", "")
    compute = fm.get("compute", "")
    l4s = fm.get("l4_background_status", "")
    l4_job = fm.get("l4_job_id", "")
    l4_eta = fm.get("l4_job_estimated_time", "")
    l4_host = fm.get("l4_job_host", compute)

    def _row(left, right=""):
        if right:
            return _pad(f"{left}{' ' * max(2, rpad - _vislen(left))}{right}", inner)
        return _pad(left, inner)

    title = f"AITP {_DOT} {topic_slug}"
    if _vislen(title) > inner - 4:
        title = title[:inner - 7] + ".."

    lines = []
    lines.append(f"{C}{_TL}{_HZ}{Z} {W}{title}{Z} {C}{_HZ * max(1, inner - _vislen(title) - 2)}{_TR}{Z}")

    # Row 1: Stage + Gate
    gate_right = f"Gate {D}......{Z} {gate_icon} {D}{gate_label}{Z}"
    if gate_detail:
        gate_right += f" {D}— {gate_detail}{Z}"
    lines.append(f"{C}{_VT}{Z} {_row(f'Stage {D}.....{Z} {W}{stage}{Z}', gate_right)} {C}{_VT}{Z}")

    # Row 2: Lane + Info
    meta_parts = []
    if status:
        meta_parts.append(f"{status}")
    if sources:
        meta_parts.append(f"{sources} sources")
    if compute:
        meta_parts.append(f"@{compute}")
    meta = f" {D}{_DOT}{Z} ".join(meta_parts) if meta_parts else "--"
    lines.append(f"{C}{_VT}{Z} {_row(f'Lane {D}......{Z} {B}{lane}{Z}',
                                     f'Info {D}......{Z} {meta}')} {C}{_VT}{Z}")

    # Row 3: L4 job
    if l4s and l4s != "idle":
        j = l4_job if l4_job and len(l4_job) <= 10 else (l4_job[-8:] if l4_job else "?")
        l4_str = f"{M}#{j}{Z}  {_l4_display(l4s)}"
        if l4_eta:
            l4_str += f"  {D}~{l4_eta}{Z}"
        if l4_host:
            l4_str += f"  {D}on{Z} {l4_host}"
        lines.append(f"{C}{_VT}{Z} {_row(f'L4 {D}.......{Z} {l4_str}')} {C}{_VT}{Z}")

    # Row last: Next
    next_action = gate_detail if gate_detail else _get_next_action(fm, gate_info)
    lines.append(f"{C}{_VT}{Z} {_row(f'{Y}{_ARR} Next{Z}  {D}...{Z} {next_action}')} {C}{_VT}{Z}")

    lines.append(f"{C}{_BL}{_HZ * inner}{_BR}{Z}")
    return "\n".join(lines)


# ── Dashboard panel (context injection) ─────────────────────────

def render_dashboard(fm, topic_slug, gate_info=None):
    w = 64; inner = w - 2; S = " "
    stage = _stage_str(fm)
    if gate_info:
        gate_status = gate_info.get("gate_status", fm.get("gate_status", ""))
        gate_detail = gate_info.get("gate_detail", "")
        required = gate_info.get("required_artifact", "")
    else:
        gate_status = fm.get("gate_status", "")
        gate_detail = ""; required = ""
    gate_icon, gate_label = _gate_icon(gate_status)
    lane = _lane_short(fm.get("lane", ""))
    title = fm.get("title", topic_slug)
    l4s = fm.get("l4_background_status", "")
    l4_job = fm.get("l4_job_id", "")
    l4_eta = fm.get("l4_job_estimated_time", "")
    l4_host = fm.get("l4_job_host", fm.get("compute", ""))
    compute = fm.get("compute", "")
    status = fm.get("status", "")
    sources = fm.get("sources_count", "")
    rpad = inner // 2 + 5

    def row(text=""):
        return f"{C}{_DV}{Z}{S}{text}" + " " * max(0, inner - _vislen(text) - 1) + f"{C}{_DV}{Z}"

    def section(label):
        rem = inner - _vislen(label) - 5
        return row(f"{D}{_HZ}{_HZ}{Z} {W}{label}{Z} {D}{_HZ * max(1, rem)}{Z}")

    lines = []
    lines.append(f"{C}{_D_tl}{_DL * inner}{_D_tr}{Z}")
    lines.append(row(f"{W}AITP ACTIVE TOPIC{Z}"))
    lines.append(f"{C}{_D_xl}{_DL * inner}{_DV}{Z}")
    lines.append(row())

    lines.append(row(f"Topic {D}:{Z} {W}{topic_slug}{Z}"))
    if title:
        t_max = inner - 17
        lines.append(row(f"Title {D}:{Z} {title[:t_max] + '..' if len(title) > t_max else title}"))
    lines.append(row())

    lines.append(section("Status"))
    sc = f"Stage {D}....{Z} {stage} {gate_icon}"
    gc = f"Gate {D}......{Z} {gate_label}"
    if gate_detail:
        gc += f" {D}({gate_detail}){Z}"
    lines.append(row(_pad(f"{sc}{' ' * max(2, rpad - _vislen(sc))}{gc}", inner)))
    lc = f"Lane {D}......{Z} {lane}"
    cc = f"Compute {D}...{Z} {compute or '--'}"
    lines.append(row(_pad(f"{lc}{' ' * max(2, rpad - _vislen(lc))}{cc}", inner)))
    if status:
        sc2 = f"Status {D}....{Z} {status}"
        src = f"Sources {D}...{Z} {sources or '--'}"
        lines.append(row(_pad(f"{sc2}{' ' * max(2, rpad - _vislen(sc2))}{src}", inner)))
    lines.append(row())

    if l4s and l4s != "idle":
        lines.append(section("L4 Background Job"))
        jc = f"Job {D}.......{Z} {M}#{l4_job}{Z}" if l4_job else f"Job {D}.......{Z} --"
        lc = f"Status {D}....{Z} {_l4_display(l4s)}"
        lines.append(row(_pad(f"{jc}{' ' * max(2, rpad - _vislen(jc))}{lc}", inner)))
        hc = f"Host {D}......{Z} {l4_host or compute or '--'}"
        ec = f"ETA {D}.......{Z} {l4_eta or '--'}"
        lines.append(row(_pad(f"{hc}{' ' * max(2, rpad - _vislen(hc))}{ec}", inner)))
        lines.append(row())

    if gate_detail:
        next_action = gate_detail
    elif required:
        next_action = f"Fill required: {required}"
    else:
        next_action = _get_next_action(fm, gate_info)
    lines.append(row(f"{Y}{_ARR}{Z} Next: {next_action}"))
    lines.append(row())
    lines.append(f"{C}{_D_bl}{_DL * inner}{_D_br}{Z}")

    return "\n".join(lines)


def _get_next_action(fm, gate_info=None):
    stage = fm.get("stage", "")
    activity = fm.get("l3_activity", fm.get("posture", ""))
    gate = gate_info.get("gate_status", fm.get("gate_status", "")) if gate_info else fm.get("gate_status", "")
    if gate.startswith("blocked"):
        if gate_info and gate_info.get("gate_detail"):
            return gate_info["gate_detail"]
        field = gate.replace("blocked_", "").replace("_", " ")
        return f"Complete required: {field}"
    hints = {
        "L0": "Discover and register sources; evaluate quality",
        "L1": "Complete reading notes, frame research question, advance to L3",
        "L3:ideate": "Generate and refine research ideas; promote candidate",
        "L3:derive": "Execute derivation steps with source anchoring (file:line)",
        "L3:integrate": "Combine results into findings; synthesize claims",
        "L3:distill": "Extract final claims from integrated results",
        "L3:gap-audit": "Find hidden assumptions and missing correspondence checks",
        "L3:plan": "Design derivation route; map steps and dependencies",
        "L4": "Submit adversarial review; verify against evidence and known limits",
        "promote": "Request promotion gate; human approval for L2 merge",
    }
    key = f"{stage}:{activity}" if activity else stage
    return hints.get(key, "Use aitp_v5_get_execution_brief for current v5 guidance")
