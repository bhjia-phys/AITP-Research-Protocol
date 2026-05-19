# AITP v5 CLI/MCP Interface Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep CLI, MCP, runtime entrypoints, and adapter metadata as thin, contract-checked surfaces over the v5 kernel.

**Architecture:** Kernel functions in `brain/v5/` remain authoritative. CLI/MCP functions may parse arguments and serialize JSON, but must not duplicate policy, promotion, validation, or evidence rules. Runtime and adapter registries are the parity layer that prevents hidden capabilities.

**Tech Stack:** Python standard library, pytest, Markdown+YAML store, PowerShell verification commands.

---

## File Responsibility Map

- `brain/v5/cli.py`: command parsing and JSON output only.
- `brain/v5/mcp_tools.py`: thin MCP-callable wrappers only.
- `brain/v5/runtime_entrypoints.py`: public runtime inventory and sample argv.
- `brain/v5/adapter_protocols.py`: Codex/Claude/OpenCode-readable entrypoint metadata.
- `brain/v5/public_surfaces.py`: surface names and validators.
- `tests/test_v5_cli.py`: CLI behavior.
- `tests/test_v5_mcp_tools.py`: MCP wrapper behavior.
- `tests/test_v5_runtime_entrypoints.py`: CLI/MCP/runtime parity.
- `tests/test_v5_adapters.py`: adapter metadata parity.

## Task 1: Enforce Runtime Surface Parity

**Files:**
- Modify: `tests/test_v5_runtime_entrypoints.py`
- Modify: `brain/v5/runtime_entrypoints.py`

- [ ] **Step 1: Write the failing test**

Add a test that every entrypoint with a user-facing kernel action declares `surface`, `cli`, `mcp`, and `sample_argv`.

```python
def test_runtime_entrypoints_have_cli_mcp_and_sample_argv():
    from brain.v5.runtime_entrypoints import runtime_entrypoints

    for name, entry in runtime_entrypoints().items():
        assert entry["surface"]
        assert entry["cli"]
        assert entry["mcp"]
        assert entry["sample_argv"]
```

- [ ] **Step 2: Run red**

```powershell
pytest tests\test_v5_runtime_entrypoints.py::test_runtime_entrypoints_have_cli_mcp_and_sample_argv -q
```

Expected: fail if any entrypoint has missing interface metadata.

- [ ] **Step 3: Implement minimal registry completion**

Add missing metadata in `brain/v5/runtime_entrypoints.py`; do not add kernel behavior here.

- [ ] **Step 4: Verify**

```powershell
pytest tests\test_v5_runtime_entrypoints.py tests\test_v5_adapters.py -q
```

Expected: all pass.

## Task 2: Keep CLI/MCP Wrappers Contract-Checked

**Files:**
- Modify: `tests/test_v5_cli.py`
- Modify: `tests/test_v5_mcp_tools.py`
- Modify: `brain/v5/cli.py`
- Modify: `brain/v5/mcp_tools.py`

- [ ] **Step 1: Write the failing tests**

For each newly added kernel capability, add one CLI test and one MCP test asserting `ok is True` and validating the declared public surface.

```python
def test_mcp_new_capability_returns_valid_surface(tmp_path):
    from brain.v5.mcp_tools import aitp_v5_new_capability
    from brain.v5.public_surfaces import require_valid_public_surface

    payload = aitp_v5_new_capability(str(tmp_path), required_arg="value")

    assert payload["ok"] is True
    assert require_valid_public_surface("new_surface", payload) == payload
```

- [ ] **Step 2: Run red**

```powershell
pytest tests\test_v5_cli.py tests\test_v5_mcp_tools.py -q
```

Expected: fail until wrapper and surface validation are connected.

- [ ] **Step 3: Implement thin wrappers**

Wrappers should call one kernel function and return `{"ok": True, **asdict(record)}` or an existing dict payload. Do not inspect or rewrite records manually.

- [ ] **Step 4: Verify**

```powershell
pytest tests\test_v5_cli.py tests\test_v5_mcp_tools.py tests\test_v5_public_surfaces.py -q
```

Expected: all pass.

## Task 3: Full Interface Regression

**Files:**
- Modify only the files touched by Tasks 1-2.

- [ ] **Step 1: Run v5 regression**

```powershell
$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }
pytest $files -q
python -m compileall -q brain\v5
git diff --check -- .
```

Expected: all v5 tests pass, compileall passes, diff check has no errors.

- [ ] **Step 2: Commit and push**

```powershell
git add brain/v5/cli.py brain/v5/mcp_tools.py brain/v5/runtime_entrypoints.py brain/v5/adapter_protocols.py tests/test_v5_cli.py tests/test_v5_mcp_tools.py tests/test_v5_runtime_entrypoints.py tests/test_v5_adapters.py
git commit -m "test(v5): enforce cli mcp runtime parity"
git push origin codex/aitp-v5-kernel-mvp
git push origin HEAD:main
```
