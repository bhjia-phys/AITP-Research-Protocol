# AITP test runbook

Use this runbook for the next honest AITP tests.

## 1. Platform gate

Check the host and chat surfaces first:

```bash
openclaw status
openclaw channels status --probe --json
systemctl --user status openclaw-gateway.service --no-pager
```

Pass condition:
- gateway running
- Feishu probe healthy
- intended agent/session visible

## 2. Kernel gate

Check that the kernel itself is healthy:

```bash
aitp doctor
aitp state --topic-slug haldane-shastry-chaos-transition
aitp capability-audit --topic-slug haldane-shastry-chaos-transition
```

Pass condition:
- CLI installed
- runtime state readable
- capability audit not obviously broken

## 3. Single-step loop smoke test

Run one bounded step only:

```bash
aitp loop \
  --topic-slug haldane-shastry-chaos-transition \
  --updated-by manual-smoke \
  --max-auto-steps 1 \
  --json
```

Pass condition:
- `runtime/topics/<topic_slug>/loop_state.json` updates
- conformance remains truthful
- no fake scientific success is claimed

## 4. Heartbeat semantic test

The heartbeat policy should now prefer:

```bash
aitp loop --updated-by openclaw-heartbeat --max-auto-steps 1 --json
```

Test either by:
- waiting for the scheduled heartbeat,
- or manually sending the configured heartbeat prompt through the bound chat surface.

Pass condition:
- heartbeat follows `HEARTBEAT.md`
- if AITP is selected, it follows `HEARTBEAT_AITP.md`
- ack stays short and truthful

## 5. Feishu end-to-end test

From Feishu DM, ask for:
- a small runtime read
- one bounded execution step

Suggested checks:
- read `loop_state`
- run the existing bounded HS smoke test

Pass condition:
- transport works
- runtime state is readable
- bounded Codex/AITP handoff is truthful

## 6. L2 backend bridge test: Obsidian 01

Pick one real note from:

- `/home/bhj/projects/repos/Theoretical-Physics/obsidian-markdown/01 Theoretical Physics/`

Register it into `L0`:

```bash
python3 research/knowledge-hub/source-layer/scripts/register_local_note_source.py \
  --topic-slug <topic_slug> \
  --path "<absolute-note-path>" \
  --registered-by backend-bridge-smoke
```

Then run one bounded loop step that explicitly mentions the backend:

```bash
aitp loop \
  --topic-slug <topic_slug> \
  --human-request "Use backend:obsidian-01-theoretical-physics as a human knowledge bridge, but keep all conclusions operator-visible." \
  --max-auto-steps 1 \
  --json
```

Pass condition:
- note is registered in `L0`
- runtime artifacts remain operator-visible
- no direct folder-level canonicalization happens

## 7. L2 backend bridge test: LibRPA

Do not start with heavy execution.
Start with docs/tests/method context.

Use backend card:
- `backend:librpa-local-workspace`

Goal:
- seed one `method`, `workflow`, or `validation_pattern` candidate from software knowledge
- keep reproducibility paths explicit

Pass condition:
- AITP can reference the backend coherently
- no black-box code claims
- paths to code/tests/results remain durable

## 8. Exit gate

Close with:

```bash
aitp audit --topic-slug <topic_slug> --phase exit
```

The run only counts if exit conformance is still honest.
