#!/usr/bin/env python3
"""AITP 2.0 Repository Authority Guard.

Standalone standard-library script. Run from repo root or any subdirectory.
Anchors to repo root via `git rev-parse --show-toplevel`.
Fixed baseline: eec20f6faeb089ec2fcdc982ad65adce242a21a9

Output format:
  FAIL <check>: <path> — <reason>

Exit 0 on all-clear, 1 on any violation.
"""

import ast as _ast
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys

# ---------------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------------

BASELINE = "eec20f6faeb089ec2fcdc982ad65adce242a21a9"

DELETE_PATHS = [
    ".agents/plugins/marketplace.json",
    ".claude-plugin/plugin.json",
    "plugins/marketplace.kimi.json",
    "plugins/aitp-research-protocol/.codex-plugin/plugin.json",
    "plugins/aitp-research-protocol/.mcp.json",
    "plugins/aitp-research-protocol-kimi/kimi.plugin.json",
    "research/adapters/openclaw/OPENCLAW_PLUGIN_PROFILE.manifest.json",
    "research/adapters/openclaw/plugin/aitp-openclaw-runtime/openclaw.plugin.json",
    "research/adapters/openclaw/plugin/aitp-openclaw-runtime/package.json",
    "package.json",
    "aitp-manifest.json",
    "bin/aitp-v5.mjs",
    "scripts/aitp",
    "scripts/aitp.cmd",
    "scripts/aitp-local.py",
    "scripts/aitp-local.cmd",
    "scripts/aitp-pm.py",
]

REPLACE_PATHS = [
    ".codex/INSTALL.md",
    "docs/INSTALL.md",
    "docs/INSTALL_CLAUDE_CODE.md",
    "docs/INSTALL_CODEX.md",
    "docs/INSTALL_KIMI_CODE.md",
    "docs/INSTALL_OPENCLAW.md",
    "docs/QUICKSTART.md",
    "docs/PUBLISH_PYPI.md",
    "docs/MIGRATE_LOCAL_INSTALL.md",
    "docs/UNINSTALL.md",
    "plugins/aitp-research-protocol/README.md",
    "plugins/aitp-research-protocol-kimi/README.md",
    "brain/PROTOCOL.md",
    "docs/AUDIT_REPORT_ALIGNMENT.md",
    "docs/README.codex.md",
    "docs/PROJECT_INDEX.md",
    "docs/AITP_SPEC.md",
    "docs/AITP_POSITIONING.md",
    "docs/AITP_RESEARCH_BRAIN_ROADMAP.md",
    "docs/AITP_SKILL_LINKAGE.md",
    "docs/CODEX_APP_1_0_PLAN.md",
    "docs/AITP_V5_THEORY_RESEARCH_STATE.md",
    "docs/v5-quiet-research-workflow-architecture.md",
    "docs/v5-source-asset-pdf-acquisition.md",
    "adapters/README.md",
    "adapters/claude-code/SKILL.md",
    "adapters/codex/SKILL.md",
    "adapters/openclaw/SKILL.md",
    "adapters/opencode/SKILL.md",
    "research/knowledge-hub/README.md",
    "research/knowledge-hub/LAYER_MAP.md",
    "research/adapters/openclaw/PLUGIN_PROFILE_INSTALL.md",
    "research/adapters/openclaw/BOOTSTRAP.md",
    "research/adapters/openclaw/AITP_AGENT_ENTRYPOINT.md",
    "docs/architecture.md",
    "docs/AITP_TOPIC_FOLDER_ARCHITECTURE.md",
    "docs/MULTI_TOPIC_RUNTIME.md",
    "docs/AITP_GSD_WORKFLOW_CONTRACT.md",
    "docs/MIGRATE_MULTI_TOPIC.md",
    "docs/EXECUTION_PLAN.md",
    "docs/SESSION_COORDINATION_10WAY.md",
    "docs/protocols/TOPIC_NOTEBOOK_OBLIGATION_PROTOCOL.md",
    "research/knowledge-hub/runtime/TOPIC_TRUTH_ROOT_CONTRACT.md",
]

MODIFY_PATH = ".github/workflows/v5-test-lanes.yml"
AUTHORITY_GUARD_PATH = ".github/workflows/authority-guard.yml"

ROOT_FILES = ["PROJECT_MEMORY.md", "README.md"]

ALL_SOURCE_PATHS = ROOT_FILES + DELETE_PATHS + REPLACE_PATHS + [MODIFY_PATH]
# assert 63
assert len(ALL_SOURCE_PATHS) == 63, f"Expected 63 source paths, got {len(ALL_SOURCE_PATHS)}"

ARCHIVE_ROOT = "docs/legacy/aitp-v5-authority-cutover/repository"
MANIFEST_PATH = "docs/legacy/aitp-v5-authority-cutover/archive-manifest.json"


def archive_path_for(source_path):
    return f"{ARCHIVE_ROOT}/{source_path}"


# expected REPLACE template (byte-for-byte)
# 4 lines for standard, 5 lines for UNINSTALL
REPLACE_HEADING = "# AITP v5 entrypoint retired"
REPLACE_BODY = "AITP v5 is retired. `PROJECT_MEMORY.md` is the sole active authority."
UNINSTALL_EXTRA = "Local uninstall is a separate operation and requires explicit human approval."


def expected_replace_bytes(source_path):
    """Construct exact expected bytes for a REPLACE retirement notice."""
    archive = archive_path_for(source_path)
    lines = [
        REPLACE_HEADING,
        "",
        REPLACE_BODY,
        f"Historical content: `{archive}`.",
    ]
    if source_path == "docs/UNINSTALL.md":
        lines.append(UNINSTALL_EXTRA)
    return "\n".join(lines).encode("utf-8") + b"\n"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def repo_root():
    """Return absolute repo root or exit."""
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True
        )
        return r.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"FAIL git: cannot find repo root — {e}", file=sys.stderr)
        sys.exit(1)


def _run_git(args, capture_text=False, cwd=None):
    """Run a git command and return CompletedProcess. Raises on failure."""
    return subprocess.run(
        args, capture_output=True, text=capture_text, check=True, cwd=cwd
    )


def git_show_blob(ref, path):
    """Return bytes of `git show <ref>:<path>`, or None on error."""
    try:
        r = subprocess.run(
            ["git", "show", f"{ref}:{path}"],
            capture_output=True, check=True
        )
        return r.stdout
    except subprocess.CalledProcessError:
        return None


def git_diff_names(base, head, pathspec=None):
    """Return list of changed paths via direct baseline-to-HEAD diff (two-dot);
    raises on git error (fail-closed)."""
    cmd = ["git", "diff", "--name-only", base, head]
    if pathspec:
        cmd.append("--")
        if isinstance(pathspec, list):
            cmd.extend(pathspec)
        else:
            cmd.append(pathspec)
    r = _run_git(cmd, capture_text=True)
    return [p for p in r.stdout.strip().split("\n") if p]


def git_ls_files(patterns):
    """Return list of tracked files matching patterns; raises on git error."""
    cmd = ["git", "ls-files"] + list(patterns)
    r = _run_git(cmd, capture_text=True)
    return [p for p in r.stdout.strip().split("\n") if p]


def git_status_porcelain(pathspecs):
    """Run `git status --porcelain=v1 --untracked-files=all -- <pathspecs>`.
    Returns list of lines, raises on git error."""
    cmd = ["git", "status", "--porcelain=v1", "--untracked-files=all", "--"] + list(pathspecs)
    r = _run_git(cmd, capture_text=True)
    return [p for p in r.stdout.strip().split("\n") if p]


def git_ls_tree_mode(ref, path):
    """Return git mode string (e.g. '100644', '100755') for <ref>:<path>;
    raises on git error. Returns empty string if ref/path not found."""
    r = _run_git(["git", "ls-tree", ref, path], capture_text=True)
    if not r.stdout.strip():
        return ""
    return r.stdout.strip().split()[0]


def sha256_bytes(data):
    """Return hex SHA-256 of bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(filepath):
    """Return hex SHA-256 of file on disk, or None."""
    try:
        with open(filepath, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except FileNotFoundError:
        return None


def report_fail(check, path, reason):
    print(f"FAIL {check}: {path} — {reason}")


# ---------------------------------------------------------------------------
# checks
# ---------------------------------------------------------------------------

def check_delete(repo):
    """Check 1: DELETE paths must not exist at original locations (lexists catches broken symlinks)."""
    failures = 0
    for p in DELETE_PATHS:
        full = os.path.join(repo, p)
        if os.path.lexists(full):
            report_fail("DELETE", p, "path still exists after cutover")
            failures += 1
    return failures


def check_replace(repo):
    """Check 2: REPLACE paths must match expected retirement notice byte-for-byte."""
    failures = 0
    for p in REPLACE_PATHS:
        full = os.path.join(repo, p)
        if not os.path.isfile(full):
            report_fail("REPLACE", p, "file does not exist")
            failures += 1
            continue
        if os.path.islink(full):
            report_fail("REPLACE", p, "is a symlink — rejected")
            failures += 1
            continue
        try:
            with open(full, "rb") as f:
                actual = f.read()
        except OSError as e:
            report_fail("REPLACE", p, f"cannot read file: {e}")
            failures += 1
            continue

        expected = expected_replace_bytes(p)
        if actual != expected:
            # Provide diagnostic info
            if len(actual) != len(expected):
                report_fail("REPLACE", p, f"byte length mismatch: got {len(actual)}, expected {len(expected)}")
            else:
                # Find first differing byte
                for i in range(len(actual)):
                    if actual[i] != expected[i]:
                        report_fail("REPLACE", p, f"byte mismatch at offset {i}: got 0x{actual[i]:02x}, expected 0x{expected[i]:02x}")
                        break
            failures += 1
    return failures


def check_v5_workflow(repo):
    """Check 3: v5 CI workflow must only have workflow_dispatch with per-job manual if."""
    failures = 0
    wf_path = os.path.join(repo, MODIFY_PATH)
    if not os.path.isfile(wf_path):
        report_fail("WORKFLOW", MODIFY_PATH, "workflow file does not exist")
        return 1
    if os.path.islink(wf_path):
        report_fail("WORKFLOW", MODIFY_PATH, "is a symlink — rejected")
        return 1

    try:
        with open(wf_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError) as e:
        report_fail("WORKFLOW", MODIFY_PATH, f"cannot read file: {e}")
        return 1

    # Parse column-0 keys (top-level YAML keys)
    col0_keys = []
    for i, raw in enumerate(lines):
        if raw and raw[0] not in (" ", "\t", "\n", "\r", "#"):
            col0_keys.append((i, raw.rstrip("\n").rstrip("\r")))

    # Find 'on:' block and collect event keys
    on_idx = None
    for idx, (li, key) in enumerate(col0_keys):
        stripped_key = key.strip().rstrip(":") if key.strip().endswith(":") else key.strip()
        if stripped_key == "on":
            on_idx = idx
            break

    if on_idx is None:
        report_fail("WORKFLOW", MODIFY_PATH, "cannot find 'on:' block")
        return 1

    on_line = col0_keys[on_idx][0]
    next_key_line = col0_keys[on_idx + 1][0] if on_idx + 1 < len(col0_keys) else len(lines)

    event_keys = set()
    for li in range(on_line + 1, next_key_line):
        raw = lines[li]
        # Lines starting with exactly two spaces then a word then ':'
        if raw.startswith("  ") and not raw.startswith("   "):
            stripped = raw.strip()
            if stripped.endswith(":"):
                key = stripped.rstrip(":")
                event_keys.add(key)

    expected_events = {"workflow_dispatch"}
    if event_keys != expected_events:
        report_fail("WORKFLOW", MODIFY_PATH,
                     f"event keys: {sorted(event_keys)}, expected {sorted(expected_events)}")
        failures += 1

    # Parse jobs block: build map of job_name -> set of if: conditions at job level
    in_jobs = False
    current_job = None
    jobs_parsed = {}  # job_name -> {"line": int, "if_conditions": list of (lineno, condition)}
    line_no = 0
    for raw in lines:
        line_no += 1
        # Column-0 detection
        is_col0 = raw and raw[0] not in (" ", "\t", "\n", "\r", "#")
        if is_col0:
            if raw.strip() == "jobs:":
                in_jobs = True
                continue
            elif in_jobs:
                # Next column-0 key ends jobs section
                in_jobs = False
                current_job = None
                continue

        if not in_jobs:
            continue

        # Inside jobs: detect job names (2-space indent, not 4-space)
        if raw.startswith("  ") and not raw.startswith("    ") and raw.rstrip().endswith(":"):
            candidate = raw.strip().rstrip(":")
            # Skip known YAML sub-keys that are not job names
            skip_keys = {
                "steps", "strategy", "concurrency", "permissions",
                "env", "runs-on", "timeout-minutes", "with",
                "matrix", "fail-fast", "lane", "name", "uses", "run",
                "contents", "group", "cancel-in-progress",
                "needs", "container", "services", "outputs",
            }
            if candidate not in skip_keys:
                current_job = candidate
                if current_job not in jobs_parsed:
                    jobs_parsed[current_job] = {"line": line_no, "if_conditions": []}

        # Job-level if: (4-space indent under a job)
        if raw.startswith("    if:") and current_job:
            cond = raw.strip()[len("if:"):].strip()
            jobs_parsed[current_job]["if_conditions"].append((line_no, cond))

    expected_jobs = {"m0-fast", "slow-adapter", "scheduled-full-suite"}
    found_jobs = set(jobs_parsed.keys())

    if found_jobs != expected_jobs:
        report_fail("WORKFLOW", MODIFY_PATH,
                     f"job names: {sorted(found_jobs)}, expected {sorted(expected_jobs)}")
        failures += 1

    # Each expected job must have exactly one job-level if: with exact value
    expected_if_value = "github.event_name == 'workflow_dispatch'"
    for job_name in expected_jobs:
        if job_name not in jobs_parsed:
            report_fail("WORKFLOW", MODIFY_PATH, f"job '{job_name}' not found in parsed jobs")
            failures += 1
            continue
        info = jobs_parsed[job_name]
        if_conds = info["if_conditions"]
        if len(if_conds) == 0:
            report_fail("WORKFLOW", MODIFY_PATH,
                         f"job '{job_name}' missing job-level 'if:' condition")
            failures += 1
        elif len(if_conds) > 1:
            report_fail("WORKFLOW", MODIFY_PATH,
                         f"job '{job_name}' has {len(if_conds)} job-level 'if:' conditions (expected exactly 1)")
            failures += 1
        else:
            cond = if_conds[0][1]
            if cond != expected_if_value:
                report_fail("WORKFLOW", MODIFY_PATH,
                             f"job '{job_name}' if: is '{cond}', expected '{expected_if_value}'")
                failures += 1

    return failures


def check_root_authority(repo):
    """Check 4: Root authority files must reflect 2.0 sole-active status."""
    failures = 0

    # README first 40 lines + full file scan
    readme_path = os.path.join(repo, "README.md")
    if not os.path.isfile(readme_path):
        report_fail("ROOT", "README.md", "file does not exist")
        failures += 1
    elif os.path.islink(readme_path):
        report_fail("ROOT", "README.md", "is a symlink — rejected")
        failures += 1
    else:
        try:
            with open(readme_path, "r", encoding="utf-8") as f:
                first40 = "".join(f.readline() for _ in range(40))
        except OSError:
            report_fail("ROOT", "README.md", "cannot read file")
            failures += 1
            first40 = ""

        if first40:
            has_sole = "sole active" in first40.lower()
            has_retired = "retired" in first40.lower()
            has_no_runtime = ("no" in first40.lower() and "released" in first40.lower()) or \
                             "does not yet contain" in first40 or \
                             "no installable" in first40.lower()

            if not (has_sole and has_retired and has_no_runtime):
                report_fail("ROOT", "README.md",
                             "missing 2.0 sole-active/retired/no-released-runtime boundary in first 40 lines")
                failures += 1

            install_patterns = [
                r"pip\s+install", r"npm\s+install", r"mcp\s+install",
                r"hook\s+install", r"npx\s+aitp", r"python\s+-m\s+aitp",
            ]
            for pat in install_patterns:
                if re.search(pat, first40, re.IGNORECASE):
                    report_fail("ROOT", "README.md",
                                 f"v5 install/run command pattern found in first 40 lines: '{pat}'")
                    failures += 1
                    break

            if re.search(r'```\w*\s*\n', first40):
                report_fail("ROOT", "README.md", "fenced command block found in first 40 lines")
                failures += 1

        # Full README scan: forbid v5 operational/install/run command-form patterns
        # Uses command/path tokens to avoid false positives on retired prose
        try:
            with open(readme_path, "r", encoding="utf-8") as f:
                full_readme = f.read()
        except (OSError, UnicodeDecodeError):
            full_readme = ""

        if full_readme:
            # Strip legacy archive path references before scanning for commands
            scan_text = full_readme
            # Remove `docs/legacy/aitp-v5-authority-cutover/` references (legitimate archive pointers)
            scan_text = re.sub(r'`?docs/legacy/aitp-v5-authority-cutover/[^\s`]*`?', '', scan_text)
            # Remove markdown link targets containing docs/legacy/
            scan_text = re.sub(r'\]\(docs/legacy/[^)]+\)', ']()', scan_text)

            full_forbidden = [
                (re.compile(r'\bpip\s+install\b', re.IGNORECASE), "pip install"),
                (re.compile(r'\bnpm\s+(install|i)\b', re.IGNORECASE), "npm install"),
                (re.compile(r'\bnpx\s+aitp\b', re.IGNORECASE), "npx aitp"),
                (re.compile(r'\bmcp\s+install\b', re.IGNORECASE), "mcp install"),
                (re.compile(r'\bmcp\s+register\b', re.IGNORECASE), "mcp register"),
                (re.compile(r'\bmcp\s+server\b', re.IGNORECASE), "mcp server"),
                (re.compile(r'\bhook\s+install\b', re.IGNORECASE), "hook install"),
                (re.compile(r'\bhook\s+register\b', re.IGNORECASE), "hook register"),
                (re.compile(r'\bplugin\s+marketplace\b', re.IGNORECASE), "plugin marketplace"),
                (re.compile(r'\bplugin\s+add\b', re.IGNORECASE), "plugin add"),
                (re.compile(r'\baitp-v5\b', re.IGNORECASE), "aitp-v5"),
                (re.compile(r'brain/v5/native_mcp\.py'), "brain/v5/native_mcp.py"),
                (re.compile(r'python\s+-m\s+brain\.'), "python -m brain"),
                (re.compile(r'\bscripts/aitp\.(cmd|py|mjs)\b'), "scripts/aitp.{cmd,py,mjs} CLI"),
                (re.compile(r'\bscripts/aitp-local\.'), "scripts/aitp-local CLI"),
                (re.compile(r'\bscripts/aitp-pm\.'), "scripts/aitp-pm CLI"),
                (re.compile(r'\baitp\s+install\b', re.IGNORECASE), "aitp install"),
                (re.compile(r'\baitp\s+run\b', re.IGNORECASE), "aitp run"),
            ]
            for pattern, desc in full_forbidden:
                if pattern.search(scan_text):
                    report_fail("ROOT", "README.md",
                                 f"v5 operational pattern in full README: '{desc}'")
                    failures += 1

    # PROJECT_MEMORY.md
    pm_path = os.path.join(repo, "PROJECT_MEMORY.md")
    if not os.path.isfile(pm_path):
        report_fail("ROOT", "PROJECT_MEMORY.md", "file does not exist")
        failures += 1
    elif os.path.islink(pm_path):
        report_fail("ROOT", "PROJECT_MEMORY.md", "is a symlink — rejected")
        failures += 1
    else:
        try:
            with open(pm_path, "r", encoding="utf-8") as f:
                pm_text = f.read()
        except OSError:
            report_fail("ROOT", "PROJECT_MEMORY.md", "cannot read file")
            failures += 1
            pm_text = ""

        if pm_text:
            if "sole active" not in pm_text.lower():
                report_fail("ROOT", "PROJECT_MEMORY.md", "does not state 2.0 as sole active target")
                failures += 1

            v5_active_patterns = [
                (r"v5\s+is\s+(the\s+)?active", "v5 as active"),
                (r"active\s+v5", "v5 as active"),
            ]
            for pat, desc in v5_active_patterns:
                if re.search(pat, pm_text, re.IGNORECASE):
                    report_fail("ROOT", "PROJECT_MEMORY.md", f"references {desc}")
                    failures += 1

            install_patterns = [
                r"pip\s+install\s+aitp", r"npm\s+install\s+aitp",
                r"npx\s+aitp", r"aitp\s+install",
            ]
            for pat in install_patterns:
                if re.search(pat, pm_text, re.IGNORECASE):
                    report_fail("ROOT", "PROJECT_MEMORY.md", f"v5 install command found: '{pat}'")
                    failures += 1
                    break

    return failures


def check_shims(repo):
    """Check 5: AGENTS.md and CLAUDE.md must be regular non-symlink files,
    mode 100644 in baseline and non-exec on disk, byte-identical content."""
    failures = 0
    for shim in ["AGENTS.md", "CLAUDE.md"]:
        worktree_path = os.path.join(repo, shim)

        # Must lexists, be a regular file, and not a symlink
        if not os.path.lexists(worktree_path):
            report_fail("SHIM", shim, "path does not exist (lexists)")
            failures += 1
            continue
        if os.path.islink(worktree_path):
            report_fail("SHIM", shim, "is a symlink — rejected")
            failures += 1
            continue
        if not os.path.isfile(worktree_path):
            report_fail("SHIM", shim, "is not a regular file")
            failures += 1
            continue

        # --- Baseline git ls-tree mode must be 100644 ---
        try:
            bl_mode = git_ls_tree_mode(BASELINE, shim)
        except subprocess.CalledProcessError as e:
            report_fail("SHIM", shim, f"git ls-tree baseline mode failed: {e}")
            failures += 1
            bl_mode = ""
        if bl_mode and bl_mode != "100644":
            report_fail("SHIM", shim,
                         f"baseline git mode is '{bl_mode}', expected '100644'")
            failures += 1

        # --- Current worktree mode: non-executable ---
        try:
            st = os.stat(worktree_path, follow_symlinks=False)
            if (st.st_mode & 0o111) != 0:
                report_fail("SHIM", shim,
                             "file has executable bit set on disk")
                failures += 1
        except OSError as e:
            report_fail("SHIM", shim, f"cannot stat file: {e}")
            failures += 1
            continue

        # --- Current index mode if possible ---
        try:
            idx_mode = git_ls_tree_mode("HEAD", shim)
        except subprocess.CalledProcessError:
            idx_mode = ""
        if idx_mode and idx_mode != "100644":
            report_fail("SHIM", shim,
                         f"current index git mode is '{idx_mode}', expected '100644'")
            failures += 1

        # --- Baseline content byte-for-byte comparison ---
        baseline_bytes = git_show_blob(BASELINE, shim)
        if baseline_bytes is None:
            report_fail("SHIM", shim, "cannot read baseline blob")
            failures += 1
            continue

        try:
            with open(worktree_path, "rb") as f:
                worktree_bytes = f.read()
        except OSError:
            report_fail("SHIM", shim, "cannot read worktree file")
            failures += 1
            continue

        if worktree_bytes != baseline_bytes:
            report_fail("SHIM", shim, "differs from baseline bytes")
            failures += 1

    return failures


def check_legacy_imports(repo):
    """Check 6: No .py file under src/aitp/ may import from brain/ (AST-based detection)."""
    src_aitp = os.path.join(repo, "src", "aitp")
    if os.path.islink(src_aitp):
        report_fail("LEGACY", "src/aitp", "is a symlink — refusing to traverse")
        return 1
    if not os.path.isdir(src_aitp):
        # Directory does not exist — pass
        return 0

    failures = 0
    for dirpath, dirnames, filenames in os.walk(src_aitp, followlinks=False):
        # Check directory symlinks — reject and prune from traversal
        for d in list(dirnames):
            dpath = os.path.join(dirpath, d)
            if os.path.islink(dpath):
                rel = os.path.relpath(dpath, repo)
                report_fail("LEGACY", rel,
                             "symlink directory under src/aitp/ — refusing to follow")
                failures += 1
                dirnames.remove(d)

        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            fpath = os.path.join(dirpath, fn)
            rel = os.path.relpath(fpath, repo)

            # Check for symlink — fail if encountered
            if os.path.islink(fpath):
                report_fail("LEGACY", rel, "symlink under src/aitp/ — refusing to follow")
                failures += 1
                continue

            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
            except OSError as e:
                report_fail("LEGACY", rel, f"cannot read file: {e}")
                failures += 1
                continue

            # Parse AST — syntax errors are failures
            try:
                tree = _ast.parse(content, filename=fpath)
            except SyntaxError as e:
                report_fail("LEGACY", rel, f"Python syntax error: {e}")
                failures += 1
                continue

            # Walk AST for import statements referencing brain
            for node in _ast.walk(tree):
                if isinstance(node, _ast.Import):
                    for alias in node.names:
                        name = alias.name
                        # Check "import brain" or "import brain.v5" etc.
                        if name == "brain" or name.startswith("brain."):
                            report_fail("LEGACY", rel,
                                         f"imports 'brain' module (import {name})")
                            failures += 1
                elif isinstance(node, _ast.ImportFrom):
                    if node.module and (node.module == "brain" or node.module.startswith("brain.")):
                        imported = ", ".join(a.name for a in node.names)
                        report_fail("LEGACY", rel,
                                     f"imports from 'brain' module (from {node.module} import {imported})")
                        failures += 1

    return failures


def check_archive_ledger(repo):
    """Check 7: Archive ledger must exist and all entries must validate — complete byte contract."""
    failures = 0
    manifest_full = os.path.join(repo, MANIFEST_PATH)

    # --- Raw byte validation of manifest file ---
    if not os.path.isfile(manifest_full):
        report_fail("LEDGER", MANIFEST_PATH, "archive-manifest.json does not exist (missing)")
        return 1
    if os.path.islink(manifest_full):
        report_fail("LEDGER", MANIFEST_PATH, "is a symlink — rejected")
        return 1

    try:
        with open(manifest_full, "rb") as f:
            manifest_raw = f.read()
    except OSError as e:
        report_fail("LEDGER", MANIFEST_PATH, f"cannot read manifest: {e}")
        return 1

    # Must be valid UTF-8 with no BOM
    if manifest_raw[:3] == b"\xef\xbb\xbf":
        report_fail("LEDGER", MANIFEST_PATH, "manifest contains UTF-8 BOM")
        failures += 1

    # No CR (LF only)
    if b"\r" in manifest_raw:
        report_fail("LEDGER", MANIFEST_PATH, "manifest contains CR (must be LF-only)")
        failures += 1

    # Must end with exactly one final LF
    if not manifest_raw.endswith(b"\n"):
        report_fail("LEDGER", MANIFEST_PATH, "manifest does not end with final LF")
        failures += 1
    elif manifest_raw.endswith(b"\n\n"):
        report_fail("LEDGER", MANIFEST_PATH, "manifest ends with multiple final LFs")
        failures += 1

    try:
        manifest_str = manifest_raw.decode("utf-8")
    except UnicodeDecodeError as e:
        report_fail("LEDGER", MANIFEST_PATH, f"manifest is not valid UTF-8: {e}")
        return failures + 1

    # --- JSON parse ---
    try:
        manifest = json.loads(manifest_str)
    except json.JSONDecodeError as e:
        report_fail("LEDGER", MANIFEST_PATH, f"cannot parse manifest JSON: {e}")
        return failures + 1

    # --- Top-level must be a dict ---
    if not isinstance(manifest, dict):
        report_fail("LEDGER", MANIFEST_PATH,
                     f"top-level JSON must be a dict, got {type(manifest).__name__}")
        return failures + 1

    # --- Required top-level keys ---
    required_top_keys = {"schema_version", "source_baseline", "archived_at", "entries"}
    actual_top_keys = set(manifest.keys())
    missing_top = required_top_keys - actual_top_keys
    extra_top = actual_top_keys - required_top_keys
    if missing_top:
        report_fail("LEDGER", MANIFEST_PATH,
                     f"missing required top-level keys: {sorted(missing_top)}")
        failures += 1
    if extra_top:
        report_fail("LEDGER", MANIFEST_PATH,
                     f"unexpected top-level keys: {sorted(extra_top)}")
        failures += 1

    # --- schema_version ---
    if manifest.get("schema_version") != 1:
        report_fail("LEDGER", MANIFEST_PATH,
                     f"schema_version is {manifest.get('schema_version')}, expected 1")
        failures += 1

    # --- source_baseline ---
    if manifest.get("source_baseline") != BASELINE:
        report_fail("LEDGER", MANIFEST_PATH,
                     f"source_baseline is '{manifest.get('source_baseline')}', expected '{BASELINE}'")
        failures += 1

    # --- archived_at strict UTC ISO-8601 Z ---
    archived_at_str = manifest.get("archived_at")
    if not isinstance(archived_at_str, str) or not archived_at_str:
        report_fail("LEDGER", MANIFEST_PATH,
                     f"archived_at is missing or not a non-empty string (got {type(archived_at_str).__name__})")
        failures += 1
    elif not archived_at_str.endswith("Z"):
        report_fail("LEDGER", MANIFEST_PATH,
                     f"archived_at must end with 'Z' for UTC, got '{archived_at_str}'")
        failures += 1
    else:
        try:
            # Replace Z with +00:00 for Python < 3.11 compatibility
            parsed_str = archived_at_str.replace("Z", "+00:00")
            dt = datetime.datetime.fromisoformat(parsed_str)
        except (ValueError, TypeError) as e:
            report_fail("LEDGER", MANIFEST_PATH,
                         f"archived_at '{archived_at_str}' cannot be parsed as ISO-8601: {e}")
            failures += 1
        else:
            if dt.tzinfo is None:
                report_fail("LEDGER", MANIFEST_PATH,
                             "archived_at is naive (missing timezone) after parse")
                failures += 1
            elif dt.utcoffset() != datetime.timedelta(0):
                report_fail("LEDGER", MANIFEST_PATH,
                             f"archived_at is not UTC: offset={dt.utcoffset()}")
                failures += 1

    # --- entries list ---
    entries = manifest.get("entries", [])
    if not isinstance(entries, list):
        report_fail("LEDGER", MANIFEST_PATH, "entries is not a list")
        return failures + 1

    if len(entries) != 63:
        report_fail("LEDGER", MANIFEST_PATH, f"entries count is {len(entries)}, expected 63")
        failures += 1

    # --- Validate entries before processing (dict + non-empty string source_path) ---
    seen_paths = set()
    valid_source_paths = []
    for i, e in enumerate(entries):
        if not isinstance(e, dict):
            report_fail("LEDGER", f"entries[{i}]",
                         f"entry is not a dict (got {type(e).__name__})")
            failures += 1
            continue
        sp = e.get("source_path")
        if not isinstance(sp, str) or not sp:
            report_fail("LEDGER", f"entries[{i}]",
                         f"source_path missing or not a non-empty string (got {type(sp).__name__})")
            failures += 1
            continue
        valid_source_paths.append(sp)
        if sp in seen_paths:
            report_fail("LEDGER", sp, "duplicate source_path in ledger")
            failures += 1
        seen_paths.add(sp)

    # --- Set equality check ---
    manifest_paths_set = set(valid_source_paths)
    expected_paths_set = set(ALL_SOURCE_PATHS)
    extra = manifest_paths_set - expected_paths_set
    missing = expected_paths_set - manifest_paths_set
    if extra:
        for ep in sorted(extra):
            report_fail("LEDGER", ep, "extra entry not in expected source_path set")
        failures += len(extra)
    if missing:
        for mp in sorted(missing):
            report_fail("LEDGER", mp, "missing from manifest source_path set")
        failures += len(missing)

    if extra or missing:
        return failures

    # --- Validate each entry ---
    required_keys = [
        "source_path", "source_commit", "original_sha256", "archive_path",
        "archive_sha256", "git_mode", "byte_count", "line_count",
        "byte_interval", "line_interval",
    ]

    for entry in entries:
        # Must be dict before any .get() access
        if not isinstance(entry, dict):
            report_fail("LEDGER", "entries", f"entry is not a dict (got {type(entry).__name__})")
            failures += 1
            continue

        sp = entry.get("source_path", "")

        missing_keys = [k for k in required_keys if k not in entry]
        if missing_keys:
            report_fail("LEDGER", sp, f"entry missing required keys: {missing_keys}")
            failures += 1
            continue

        # --- Strict type validation for all required fields ---
        type_fail = False

        # string fields: source_path, source_commit, archive_path
        for sf in ["source_path", "source_commit", "archive_path"]:
            v = entry[sf]
            if not isinstance(v, str):
                report_fail("LEDGER", sp,
                             f"{sf} must be str, got {type(v).__name__}")
                type_fail = True

        # hash fields: original_sha256, archive_sha256 (64 lowercase hex)
        for hf in ["original_sha256", "archive_sha256"]:
            v = entry[hf]
            if not isinstance(v, str) or not re.fullmatch(r'[0-9a-f]{64}', v):
                report_fail("LEDGER", sp,
                             f"{hf} must be 64-char lowercase hex string, got {type(v).__name__}")
                type_fail = True

        # git_mode: only "100644" or "100755"
        v = entry["git_mode"]
        if v not in ("100644", "100755"):
            report_fail("LEDGER", sp,
                         f"git_mode must be '100644' or '100755', got {v!r}")
            type_fail = True

        # counts: nonnegative int, not bool
        for cf in ["byte_count", "line_count"]:
            v = entry[cf]
            if not isinstance(v, int) or isinstance(v, bool) or v < 0:
                report_fail("LEDGER", sp,
                             f"{cf} must be nonnegative int (not bool), got {type(v).__name__} = {v!r}")
                type_fail = True

        # interval fields: must be string
        for inf in ["byte_interval", "line_interval"]:
            v = entry[inf]
            if not isinstance(v, str):
                report_fail("LEDGER", sp,
                             f"{inf} must be str, got {type(v).__name__}")
                type_fail = True

        if type_fail:
            failures += 1
            # Continue to value checks even with type failures
            # (comparisons will naturally fail/mismatch, no crash risk)

        sc = entry["source_commit"]
        ap = entry["archive_path"]
        orig_sha = entry["original_sha256"]
        arch_sha = entry["archive_sha256"]
        mode = entry["git_mode"]
        byte_count = entry["byte_count"]
        line_count = entry["line_count"]
        byte_int = entry["byte_interval"]
        line_int = entry["line_interval"]

        # --- source_commit must equal BASELINE ---
        if sc != BASELINE:
            report_fail("LEDGER", sp, f"source_commit '{sc}' != baseline '{BASELINE}'")
            failures += 1

        # --- archive_path mapping ---
        expected_ap = archive_path_for(sp)
        if ap != expected_ap:
            report_fail("LEDGER", sp, f"archive_path '{ap}' != expected '{expected_ap}'")
            failures += 1
            continue

        # --- archive exists on disk (regular file, not symlink) ---
        arch_full = os.path.join(repo, ap)
        if not os.path.isfile(arch_full):
            report_fail("LEDGER", sp, f"archive file not found: {ap}")
            failures += 1
            continue
        if os.path.islink(arch_full):
            report_fail("LEDGER", sp, f"archive path is a symlink: {ap}")
            failures += 1
            continue

        # --- source bytes via git show ---
        source_bytes = git_show_blob(sc, sp)
        if source_bytes is None:
            report_fail("LEDGER", sp, f"cannot read '{sc}:{sp}' from git")
            failures += 1
            continue

        # --- archive bytes from disk ---
        try:
            with open(arch_full, "rb") as f:
                archive_bytes = f.read()
        except OSError as e:
            report_fail("LEDGER", sp, f"cannot read archive file: {e}")
            failures += 1
            continue

        # --- archive_bytes == source_bytes (all 63, not just root2) ---
        if archive_bytes != source_bytes:
            report_fail("LEDGER", sp, "archive_bytes != source_bytes (byte-for-byte mismatch)")
            failures += 1

        # --- SHA-256 triple match ---
        computed_orig_sha = sha256_bytes(source_bytes)
        computed_arch_sha = sha256_bytes(archive_bytes)

        if computed_orig_sha != orig_sha:
            report_fail("LEDGER", sp,
                         f"original_sha256 mismatch: ledger={orig_sha}, computed={computed_orig_sha}")
            failures += 1
        if computed_arch_sha != arch_sha:
            report_fail("LEDGER", sp,
                         f"archive_sha256 mismatch: ledger={arch_sha}, computed={computed_arch_sha}")
            failures += 1
        if orig_sha != arch_sha:
            report_fail("LEDGER", sp,
                         f"original_sha256 != archive_sha256 in ledger ({orig_sha} vs {arch_sha})")
            failures += 1

        # --- byte_count ---
        actual_byte_count = len(source_bytes)
        if not isinstance(byte_count, int):
            report_fail("LEDGER", sp, f"byte_count is not an integer: {type(byte_count).__name__}")
            failures += 1
        elif actual_byte_count != byte_count:
            report_fail("LEDGER", sp,
                         f"byte_count mismatch: ledger={byte_count}, actual={actual_byte_count}")
            failures += 1

        # --- line_count ---
        if not isinstance(line_count, int):
            report_fail("LEDGER", sp, f"line_count is not an integer: {type(line_count).__name__}")
            failures += 1
        else:
            actual_line_count = source_bytes.count(b"\n")
            if source_bytes and not source_bytes.endswith(b"\n"):
                actual_line_count += 1
            if source_bytes == b"":
                actual_line_count = 0
            if actual_line_count != line_count:
                report_fail("LEDGER", sp,
                             f"line_count mismatch: ledger={line_count}, actual={actual_line_count}")
                failures += 1

        # --- byte_interval ---
        expected_byte_int = f"[0,{len(source_bytes)})"
        if byte_int != expected_byte_int:
            report_fail("LEDGER", sp,
                         f"byte_interval mismatch: ledger='{byte_int}', expected='{expected_byte_int}'")
            failures += 1

        # --- line_interval ---
        n_lines = source_bytes.count(b"\n")
        if source_bytes and not source_bytes.endswith(b"\n"):
            n_lines += 1
        if source_bytes == b"":
            n_lines = 0
        if n_lines == 0:
            expected_line_int = "0..0"
        else:
            expected_line_int = f"1..{n_lines}"
        if line_int != expected_line_int:
            report_fail("LEDGER", sp,
                         f"line_interval mismatch: ledger='{line_int}', expected='{expected_line_int}'")
            failures += 1

        # --- git_mode via ls-tree ---
        try:
            expected_mode = git_ls_tree_mode(sc, sp)
            if not expected_mode:
                report_fail("LEDGER", sp, "git ls-tree returned empty output for source")
                failures += 1
            elif mode != expected_mode:
                report_fail("LEDGER", sp,
                             f"git_mode mismatch: ledger={mode}, git={expected_mode}")
                failures += 1
        except subprocess.CalledProcessError as e:
            report_fail("LEDGER", sp, f"git ls-tree failed: {e}")
            failures += 1

        # --- archive actual mode executable bit ---
        try:
            st = os.stat(arch_full, follow_symlinks=True)
            actual_exec = (st.st_mode & 0o111) != 0
            ledger_exec = (mode == "100755")
            if actual_exec != ledger_exec:
                report_fail("LEDGER", sp,
                             f"executable bit mismatch: disk={'exec' if actual_exec else 'noexec'}, "
                             f"ledger git_mode={mode}")
                failures += 1
        except OSError as e:
            report_fail("LEDGER", sp, f"cannot stat archive file: {e}")
            failures += 1

    # --- Retirement notice archive mapping consistency ---
    for sp in REPLACE_PATHS:
        expected_ap = archive_path_for(sp)
        disk_path = os.path.join(repo, sp)
        if os.path.isfile(disk_path):
            try:
                with open(disk_path, "r", encoding="utf-8") as f:
                    content = f.read()
                if f"`{expected_ap}`" not in content:
                    report_fail("LEDGER", sp,
                                 f"retirement notice does not reference expected archive path '{expected_ap}'")
                    failures += 1
            except (OSError, UnicodeDecodeError) as e:
                report_fail("LEDGER", sp, f"cannot read retirement notice for archive mapping check: {e}")
                failures += 1

    return failures


def check_authority_markers(repo):
    """Check 8: Strong authority markers must not appear in non-retirement, non-historical Markdown."""
    failures = 0

    # Get all tracked Markdown files — fail on git error
    try:
        md_files = git_ls_files(["*.md"])
    except subprocess.CalledProcessError as e:
        report_fail("MARKER", "git", f"git ls-files failed: {e}")
        return 1

    # Authority marker patterns (anchored)
    patterns = [
        (re.compile(r'\bStatus\s*:\s*active\b', re.IGNORECASE),
         "Status: active"),
        (re.compile(r'\bStatus\s*:\s*canonical\b', re.IGNORECASE),
         "Status: canonical"),
        (re.compile(r'\bstatus\s*:\s*active\b'),
         "status: active (lowercase)"),
        (re.compile(r'\bstatus\s*:\s*canonical\b'),
         "status: canonical (lowercase)"),
        (re.compile(r'highest\s+public\s+authority', re.IGNORECASE),
         "highest public authority"),
        (re.compile(r'active\s+local\s+workflow\s+rule', re.IGNORECASE),
         "active local workflow rule"),
        (re.compile(r'active\s+runtime\s+contract', re.IGNORECASE),
         "active runtime contract"),
        (re.compile(r'single[\s-]*source[\s-]*of[\s-]*truth', re.IGNORECASE),
         "single source of truth"),
        (re.compile(r'authoritative\s+active[\s-]*topic', re.IGNORECASE),
         "authoritative active-topic"),
    ]

    # Exclusion sets
    excluded_dirs = [
        "archive/", "docs/archive/", "docs/legacy/", "docs/superpowers/",
        "docs/session_reports/", ".planning/", "tests/", "output/", "tmp/",
        "build/", "generated/", ".git/",
    ]
    keep_historical_prefixes = [
        "brain/v5/",
        "hooks/",
        "deploy/",
        "plugins/aitp-research-protocol/scripts/",
        "plugins/aitp-research-protocol/skills/",
        "plugins/aitp-research-protocol-kimi/scripts/",
        "plugins/aitp-research-protocol-kimi/skills/",
        "research/adapters/openclaw/scripts/",
        "research/adapters/openclaw/plugin/",
        "contracts/",
        "schemas/",
        "research/knowledge-hub/canonical/",
        "docs/superpowers/plans/",
        "docs/superpowers/progress/",
    ]
    keep_historical_exact = [
        "scripts/split_topics.py",
        "scripts/run_v5_test_lanes.py",
        "tests/",
        "bin/convert_legacy_to_v2.py",
        "bin/migrate_legacy_topics.py",
        "docs/CHARTER.md",
    ]

    replace_exact = set(REPLACE_PATHS)

    def is_excluded(filepath):
        # Directory exclusion prefix
        for ed in excluded_dirs:
            if filepath == ed.rstrip("/") or filepath.startswith(ed):
                return True

        # KEEP-HISTORICAL prefix
        for khp in keep_historical_prefixes:
            if filepath.startswith(khp):
                return True

        # KEEP-HISTORICAL exact
        for khe in keep_historical_exact:
            if khe.endswith("/"):
                if filepath.startswith(khe):
                    return True
            elif filepath == khe:
                return True

        # docs/protocols/** except TOPIC_NOTEBOOK_OBLIGATION_PROTOCOL.md
        if filepath.startswith("docs/protocols/") and filepath != "docs/protocols/TOPIC_NOTEBOOK_OBLIGATION_PROTOCOL.md":
            return True

        # research/knowledge-hub/** non-entry payload except REPLACEd entry notices
        if filepath.startswith("research/knowledge-hub/") and filepath not in replace_exact:
            return True

        # REPLACE paths (retirement notices)
        if filepath in replace_exact:
            return True

        return False

    for filepath in md_files:
        if is_excluded(filepath):
            continue

        fullpath = os.path.join(repo, filepath)
        if not os.path.isfile(fullpath):
            continue

        try:
            with open(fullpath, "r", encoding="utf-8") as f:
                content = f.read()
        except (OSError, UnicodeDecodeError) as e:
            report_fail("MARKER", filepath, f"cannot read/decode file: {e}")
            failures += 1
            continue

        for pattern, desc in patterns:
            if pattern.search(content):
                report_fail("MARKER", filepath, f"contains old authority marker: '{desc}'")
                failures += 1
                break  # One failure per file is enough

    return failures


def check_frozen_paths(repo):
    """Check 9: frozen paths must not be modified against baseline or locally (staged/untracked)."""
    failures = 0
    frozen = ["research/knowledge-hub/canonical", "contracts", "schemas"]

    # baseline->HEAD diff — fails on git error
    try:
        changed = git_diff_names(BASELINE, "HEAD", frozen)
    except subprocess.CalledProcessError as e:
        report_fail("FROZEN", "git", f"git diff baseline..HEAD failed: {e}")
        return 1

    for p in changed:
        report_fail("FROZEN", p, "modified in baseline->HEAD diff")
        failures += 1

    # Local tracked + index diff against HEAD — fail on git error
    try:
        r = _run_git(
            ["git", "diff", "--name-only", "HEAD", "--"] + frozen,
            capture_text=True
        )
        local_changed = [p for p in r.stdout.strip().split("\n") if p]
    except subprocess.CalledProcessError as e:
        report_fail("FROZEN", "git", f"git diff HEAD failed: {e}")
        return failures + 1

    for p in local_changed:
        report_fail("FROZEN", p, "modified in local working-tree or index diff")
        failures += 1

    # git status --porcelain for tracked + staged + untracked
    try:
        status_lines = git_status_porcelain(frozen)
    except subprocess.CalledProcessError as e:
        report_fail("FROZEN", "git", f"git status --porcelain failed: {e}")
        return failures + 1

    for line in status_lines:
        # Parse: "XY path" or "XY path -> newpath" for renames
        # Extract the path(s) after the status flags
        parts = line.strip().split()
        if len(parts) < 2:
            continue
        # First field is the status (XY), rest are path(s)
        status_flag = parts[0]
        if "->" in line:
            # Rename: "R  old -> new"
            # Extract the new path
            arrow_idx = line.index("->")
            new_path = line[arrow_idx + 2:].strip()
            report_fail("FROZEN", new_path,
                         f"local status '{status_flag}' in porcelain output")
        else:
            path = " ".join(parts[1:])
            report_fail("FROZEN", path,
                         f"local status '{status_flag}' in porcelain output")
        failures += 1

    return failures


def check_aitp_boundary(repo):
    """Check 10: repo-root .aitp/ must not be modified (includes untracked/staged)."""
    failures = 0
    aitp_dir = os.path.join(repo, ".aitp")

    # Check baseline->HEAD — fail on git error
    try:
        changed = git_diff_names(BASELINE, "HEAD", ".aitp")
    except subprocess.CalledProcessError as e:
        report_fail("AITP", "git", f"git diff baseline..HEAD .aitp failed: {e}")
        return 1

    for p in changed:
        report_fail("AITP", p, "modified in baseline->HEAD diff")
        failures += 1

    # Check local diff HEAD — fail on git error
    try:
        r = _run_git(
            ["git", "diff", "--name-only", "HEAD", "--", ".aitp"],
            capture_text=True
        )
        local_changed = [p for p in r.stdout.strip().split("\n") if p]
    except subprocess.CalledProcessError as e:
        report_fail("AITP", "git", f"git diff HEAD .aitp failed: {e}")
        return failures + 1

    for p in local_changed:
        report_fail("AITP", p, "modified in local working-tree or index diff")
        failures += 1

    # Check staged changes — fail on git error
    try:
        r = _run_git(
            ["git", "diff", "--cached", "--name-only", "--", ".aitp"],
            capture_text=True
        )
        staged_changed = [p for p in r.stdout.strip().split("\n") if p]
    except subprocess.CalledProcessError as e:
        report_fail("AITP", "git", f"git diff --cached .aitp failed: {e}")
        return failures + 1

    for p in staged_changed:
        report_fail("AITP", p, "staged modification under .aitp/")
        failures += 1

    # git status --porcelain for tracked + staged + untracked under .aitp/
    try:
        status_lines = git_status_porcelain([".aitp"])
    except subprocess.CalledProcessError as e:
        report_fail("AITP", "git", f"git status --porcelain .aitp failed: {e}")
        return failures + 1

    for line in status_lines:
        parts = line.strip().split()
        if len(parts) < 2:
            continue
        status_flag = parts[0]
        if "->" in line:
            arrow_idx = line.index("->")
            new_path = line[arrow_idx + 2:].strip()
            report_fail("AITP", new_path,
                         f"local status '{status_flag}' in porcelain output")
        else:
            path = " ".join(parts[1:])
            report_fail("AITP", path,
                         f"local status '{status_flag}' in porcelain output")
        failures += 1

    return failures


def check_authority_guard_workflow(repo):
    """Check 11: Validate the authority-guard workflow with structural exactness."""
    failures = 0
    wf_path = os.path.join(repo, AUTHORITY_GUARD_PATH)

    if not os.path.isfile(wf_path):
        report_fail("GUARD", AUTHORITY_GUARD_PATH, "workflow file does not exist (missing)")
        return 1
    if os.path.islink(wf_path):
        report_fail("GUARD", AUTHORITY_GUARD_PATH, "is a symlink — rejected")
        return 1

    try:
        with open(wf_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError) as e:
        report_fail("GUARD", AUTHORITY_GUARD_PATH, f"cannot read file: {e}")
        return 1

    content = "".join(lines)

    # =========================================================================
    # 1. Parse col-0 keys (top-level YAML keys)
    # =========================================================================
    col0_keys = []  # list of (line_index, stripped_key)
    for i, raw in enumerate(lines):
        if raw and raw[0] not in (" ", "\t", "\n", "\r", "#"):
            col0_keys.append((i, raw.rstrip("\n").rstrip("\r")))

    # Find 'on:' block window: [on_line+1, next_col0_line)
    on_idx = None
    for idx, (li, key) in enumerate(col0_keys):
        clean = key.strip().rstrip(":") if key.strip().endswith(":") else key.strip()
        if clean == "on":
            on_idx = idx
            break
    if on_idx is None:
        report_fail("GUARD", AUTHORITY_GUARD_PATH, "cannot find 'on:' block")
        return failures + 1

    on_line = col0_keys[on_idx][0]
    next_on_line = col0_keys[on_idx + 1][0] if on_idx + 1 < len(col0_keys) else len(lines)

    # =========================================================================
    # 2. Parse on: block — event keys and push branches
    # =========================================================================
    event_keys = set()
    push_branches = []
    in_push = False

    for li in range(on_line + 1, next_on_line):
        raw = lines[li]
        if raw.startswith("  ") and not raw.startswith("   "):
            stripped = raw.strip()
            if stripped.endswith(":"):
                key = stripped.rstrip(":")
                event_keys.add(key)
                in_push = (key == "push")
        elif in_push and raw.startswith("    ") and raw.strip().startswith("branches:"):
            branch_content = raw.strip()[len("branches:"):].strip()
            if branch_content.startswith("["):
                inner = branch_content.strip("[]")
                for part in inner.split(","):
                    part = part.strip().strip("'").strip('"')
                    if part:
                        push_branches.append(part)
            elif branch_content:
                push_branches.append(branch_content.strip().strip("'").strip('"'))
            # Multi-line branches list
            for li2 in range(li + 1, next_on_line):
                raw2 = lines[li2]
                stripped2 = raw2.strip()
                if stripped2.startswith("- "):
                    branch = stripped2[2:].strip().strip("[]").strip("'").strip('"')
                    if branch:
                        push_branches.append(branch)
                elif raw2 and raw2[0] not in (" ", "\t", "\n"):
                    break

    # Event keys must be exactly {pull_request, push}
    expected_events = {"pull_request", "push"}
    if event_keys != expected_events:
        report_fail("GUARD", AUTHORITY_GUARD_PATH,
                     f"event keys: {sorted(event_keys)}, expected {sorted(expected_events)}")
        failures += 1

    # Forbidden events
    forbidden_events = {"schedule", "workflow_dispatch"}
    if event_keys & forbidden_events:
        report_fail("GUARD", AUTHORITY_GUARD_PATH,
                     f"forbidden event keys found: {sorted(event_keys & forbidden_events)}")
        failures += 1

    # Push branches must be exactly {main}
    if set(push_branches) != {"main"}:
        report_fail("GUARD", AUTHORITY_GUARD_PATH,
                     f"push.branches set must be exactly {{main}}, got {sorted(set(push_branches))}")
        failures += 1

    # =========================================================================
    # 3. Parse permissions block (top-level, between col-0 keys)
    # =========================================================================
    perm_idx = None
    for idx, (li, key) in enumerate(col0_keys):
        clean = key.strip().rstrip(":") if key.strip().endswith(":") else key.strip()
        if clean == "permissions":
            perm_idx = idx
            break

    permissions_ok = True
    if perm_idx is None:
        report_fail("GUARD", AUTHORITY_GUARD_PATH, "missing top-level 'permissions:' block")
        failures += 1
        permissions_ok = False
    else:
        perm_line = col0_keys[perm_idx][0]
        next_perm_line = col0_keys[perm_idx + 1][0] if perm_idx + 1 < len(col0_keys) else len(lines)

        perm_keys = {}  # key -> value
        for li in range(perm_line + 1, next_perm_line):
            raw = lines[li]
            if raw.startswith("  ") and not raw.startswith("   "):
                stripped = raw.strip()
                if ":" in stripped:
                    k, _, v = stripped.partition(":")
                    k = k.strip()
                    v = v.strip()
                    perm_keys[k] = v

        # Must have exactly 'contents: read' and no other keys
        if set(perm_keys.keys()) != {"contents"}:
            report_fail("GUARD", AUTHORITY_GUARD_PATH,
                         f"permissions keys must be exactly {{contents}}, got {sorted(perm_keys.keys())}")
            failures += 1
            permissions_ok = False
        elif perm_keys.get("contents", "").strip() != "read":
            report_fail("GUARD", AUTHORITY_GUARD_PATH,
                         f"permissions contents must be exactly 'read', got '{perm_keys.get('contents', '')}'")
            failures += 1
            permissions_ok = False

    # =========================================================================
    # 4. Parse jobs section — extract guard job properties
    # =========================================================================
    jobs_found = set()
    guard_runs_on = None
    guard_timeout = None
    guard_steps = []  # list of step block strings

    in_jobs = False
    current_job = None
    in_steps = False
    in_step = False
    current_step_lines = []

    for li, raw in enumerate(lines):
        is_col0 = raw and raw[0] not in (" ", "\t", "\n", "\r", "#")
        if is_col0:
            stripped = raw.strip()
            if stripped == "jobs:":
                in_jobs = True
                current_job = None
                in_steps = False
                in_step = False
                continue
            elif in_jobs:
                in_jobs = False
                current_job = None
                in_steps = False
                in_step = False
                continue

        if not in_jobs:
            continue

        # Job names: 2-space indent, not 4-space
        if raw.startswith("  ") and not raw.startswith("    ") and raw.rstrip().endswith(":"):
            candidate = raw.strip().rstrip(":")
            skip_keys = {
                "steps", "strategy", "concurrency", "permissions",
                "env", "runs-on", "timeout-minutes", "with",
                "matrix", "fail-fast", "lane", "name", "uses", "run",
                "contents", "group", "cancel-in-progress",
                "needs", "container", "services", "outputs",
                "if",
            }
            if candidate not in skip_keys:
                current_job = candidate
                jobs_found.add(candidate)
                in_steps = False
                in_step = False
                continue

        # Job-level keys within guard job
        if current_job == "guard" and raw.startswith("    ") and not raw.startswith("      "):
            stripped = raw.strip()
            if stripped.startswith("runs-on:"):
                guard_runs_on = stripped[len("runs-on:"):].strip().strip("'").strip('"')
            elif stripped.startswith("timeout-minutes:"):
                val = stripped[len("timeout-minutes:"):].strip()
                guard_timeout = val

        # Steps block
        if current_job and raw.startswith("    ") and not raw.startswith("      "):
            stripped = raw.strip()
            if stripped == "steps:":
                in_steps = True
                in_step = False
                continue

        if not in_steps or current_job != "guard":
            continue

        # Step items: "      - " at 6-space indent
        if raw.startswith("      - "):
            if in_step and current_step_lines:
                guard_steps.append("".join(current_step_lines))
            current_step_lines = [raw]
            in_step = True
        elif in_step and raw.startswith("        "):
            current_step_lines.append(raw)
        elif in_step and raw.startswith("      - "):
            pass  # next step (handled above)

    # Flush last step
    if in_step and current_step_lines:
        guard_steps.append("".join(current_step_lines))

    # =========================================================================
    # 5. Validate jobs set: exactly {guard}
    # =========================================================================
    if jobs_found != {"guard"}:
        report_fail("GUARD", AUTHORITY_GUARD_PATH,
                     f"jobs set must be exactly {{guard}}, got {sorted(jobs_found)}")
        failures += 1

    # =========================================================================
    # 6. Validate guard job properties: runs-on, timeout-minutes
    # =========================================================================
    if guard_runs_on is None:
        report_fail("GUARD", AUTHORITY_GUARD_PATH, "guard job missing 'runs-on:'")
        failures += 1
    elif guard_runs_on != "ubuntu-latest":
        report_fail("GUARD", AUTHORITY_GUARD_PATH,
                     f"guard job runs-on must be 'ubuntu-latest', got '{guard_runs_on}'")
        failures += 1

    if guard_timeout is None:
        report_fail("GUARD", AUTHORITY_GUARD_PATH, "guard job missing 'timeout-minutes:'")
        failures += 1
    elif guard_timeout != "5":
        report_fail("GUARD", AUTHORITY_GUARD_PATH,
                     f"guard job timeout-minutes must be '5', got '{guard_timeout}'")
        failures += 1

    # =========================================================================
    # 7. Validate guard job steps — must be exactly 3
    # =========================================================================
    if len(guard_steps) != 3:
        report_fail("GUARD", AUTHORITY_GUARD_PATH,
                     f"guard job must have exactly 3 steps, got {len(guard_steps)}")
        failures += 1

    # =========================================================================
    # 8. Per-step structural validation
    # =========================================================================
    forbidden_guard_patterns = [
        "pip install",
        "pip3 install",
        "npm install",
        "requirements",
        "run_v5_test_lanes",
        "aitp-v5",
        "brain.v5",
    ]

    step_has_uses = []
    step_has_run = []
    step_combined = []

    for si, step in enumerate(guard_steps):
        step_num = si + 1

        # Extract uses: and run: values (may be on "- uses:" or "- run:" lines)
        uses_val = None
        run_val = None
        for line in step.split("\n"):
            stripped = line.strip()
            # Strip leading "- " if present (step item prefix)
            if stripped.startswith("- "):
                content = stripped[2:]
            else:
                content = stripped

            if content.startswith("uses:"):
                uval = content[len("uses:"):].strip().strip("'").strip('"')
                if uses_val is None:
                    uses_val = uval
                else:
                    report_fail("GUARD", AUTHORITY_GUARD_PATH,
                                 f"step {step_num}: multiple 'uses:' directives")
                    failures += 1
            if content.startswith("run:"):
                rval_raw = content[len("run:"):].strip()
                if run_val is None:
                    run_val = rval_raw
                else:
                    report_fail("GUARD", AUTHORITY_GUARD_PATH,
                                 f"step {step_num}: multiple 'run:' directives")
                    failures += 1

            # Forbidden patterns (check against full stripped line)
            for pat in forbidden_guard_patterns:
                if pat in stripped:
                    report_fail("GUARD", AUTHORITY_GUARD_PATH,
                                 f"step {step_num}: forbidden content '{pat}'")
                    failures += 1

        # Step must have exactly one of uses: or run:, not both, not neither
        has_uses = uses_val is not None
        has_run = run_val is not None
        if has_uses and has_run:
            report_fail("GUARD", AUTHORITY_GUARD_PATH,
                         f"step {step_num}: has both 'uses:' and 'run:' — must be one or the other")
            failures += 1
        elif not has_uses and not has_run:
            report_fail("GUARD", AUTHORITY_GUARD_PATH,
                         f"step {step_num}: missing 'uses:' or 'run:' directive")
            failures += 1

        step_has_uses.append(has_uses)
        step_has_run.append(has_run)
        step_combined.append((uses_val, run_val))

    # Step 1 must be checkout
    if len(guard_steps) >= 1:
        u1, r1 = step_combined[0]
        if u1 != "actions/checkout@v6":
            report_fail("GUARD", AUTHORITY_GUARD_PATH,
                         f"step 1 uses: must be 'actions/checkout@v6', got '{u1}'")
            failures += 1
        if r1 is not None:
            report_fail("GUARD", AUTHORITY_GUARD_PATH,
                         "step 1 (checkout) must not have 'run:'")
            failures += 1
        # Must have fetch-depth: 0 within the same step
        if "fetch-depth:" not in guard_steps[0] or "fetch-depth: 0" not in guard_steps[0]:
            report_fail("GUARD", AUTHORITY_GUARD_PATH,
                         "step 1 (checkout) missing 'fetch-depth: 0' within the same step")
            failures += 1

    # Step 2 must be setup-python
    if len(guard_steps) >= 2:
        u2, r2 = step_combined[1]
        if u2 != "actions/setup-python@v5":
            report_fail("GUARD", AUTHORITY_GUARD_PATH,
                         f"step 2 uses: must be 'actions/setup-python@v5', got '{u2}'")
            failures += 1
        if r2 is not None:
            report_fail("GUARD", AUTHORITY_GUARD_PATH,
                         "step 2 (setup-python) must not have 'run:'")
            failures += 1
        # Must have python-version in the same step
        step2_content = guard_steps[1]
        if "python-version:" not in step2_content:
            report_fail("GUARD", AUTHORITY_GUARD_PATH,
                         "step 2 (setup-python) missing 'python-version:'")
            failures += 1
        else:
            # Extract python-version value
            for line in step2_content.split("\n"):
                stripped = line.strip()
                if stripped.startswith("python-version:"):
                    pv = stripped[len("python-version:"):].strip().strip("'").strip('"')
                    if pv != "3.12":
                        report_fail("GUARD", AUTHORITY_GUARD_PATH,
                                     f"step 2 python-version must be '3.12', got '{pv}'")
                        failures += 1
                    break

    # Step 3 must be the run step
    if len(guard_steps) >= 3:
        u3, r3 = step_combined[2]
        if u3 is not None:
            report_fail("GUARD", AUTHORITY_GUARD_PATH,
                         f"step 3 must not have 'uses:' (got '{u3}')")
            failures += 1
        expected_run = "python scripts/check_repository_authority.py"
        if r3 != expected_run:
            report_fail("GUARD", AUTHORITY_GUARD_PATH,
                         f"step 3 run: must be exactly '{expected_run}', got '{r3}'")
            failures += 1
        # No && in run
        if r3 and "&&" in r3:
            report_fail("GUARD", AUTHORITY_GUARD_PATH,
                         "step 3 run: must not contain '&&'")
            failures += 1

    # Exactly 2 uses steps (step 1, 2) and 1 run step (step 3)
    total_uses = sum(1 for u, _ in step_combined if u is not None)
    total_runs = sum(1 for _, r in step_combined if r is not None)
    if total_uses != 2:
        report_fail("GUARD", AUTHORITY_GUARD_PATH,
                     f"expected exactly 2 'uses:' steps, got {total_uses}")
        failures += 1
    if total_runs != 1:
        report_fail("GUARD", AUTHORITY_GUARD_PATH,
                     f"expected exactly 1 'run:' step, got {total_runs}")
        failures += 1

    return failures


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    repo = repo_root()
    os.chdir(repo)

    total_failures = 0

    total_failures += check_delete(repo)
    total_failures += check_replace(repo)
    total_failures += check_v5_workflow(repo)
    total_failures += check_root_authority(repo)
    total_failures += check_shims(repo)
    total_failures += check_legacy_imports(repo)
    total_failures += check_archive_ledger(repo)
    total_failures += check_authority_markers(repo)
    total_failures += check_frozen_paths(repo)
    total_failures += check_aitp_boundary(repo)
    total_failures += check_authority_guard_workflow(repo)

    if total_failures > 0:
        print(f"\n{total_failures} failure(s) detected.", file=sys.stderr)
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
