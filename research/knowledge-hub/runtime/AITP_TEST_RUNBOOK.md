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
aitp state --topic-slug <topic_slug>
aitp capability-audit --topic-slug <topic_slug>
```

Pass condition:
- CLI installed
- runtime state readable
- capability audit not obviously broken

## 3. Single-step loop smoke test

Run one bounded step only:

```bash
aitp loop \
  --topic-slug <topic_slug> \
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
- run the generic OpenClaw plugin smoke script:
  - `research/adapters/openclaw/scripts/run_openclaw_plugin_smoke.sh`

Pass condition:
- transport works
- runtime state is readable
- bounded OpenClaw/AITP handoff is truthful

## 6. L2 backend bridge test: note-library backend

Pick one real note from a backend that you have already registered under
`canonical/backends/`.

For the public formal-theory example route, you can run:

```bash
research/knowledge-hub/runtime/scripts/run_formal_theory_backend_smoke.sh
```

That script creates one temporary external formal-theory note backend, realizes
the public example backend card against it, registers one note into `L0`, and
runs one bounded `aitp loop`.

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
  --human-request "Use the registered human-note backend as a bounded knowledge bridge, but keep all conclusions operator-visible." \
  --max-auto-steps 1 \
  --json
```

Pass condition:
- note is registered in `L0`
- runtime artifacts remain operator-visible
- no direct folder-level canonicalization happens

## 7. L2 backend bridge test: software backend

Do not start with heavy execution.
Start with docs/tests/method context.

Use a registered software backend card from `canonical/backends/`.

Goal:
- seed one `method`, `workflow`, or `validation_pattern` candidate from software knowledge
- keep reproducibility paths explicit

Pass condition:
- AITP can reference the backend coherently
- no black-box code claims
- paths to code/tests/results remain durable

For the public toy-model numeric starter route, you can run:

```bash
research/knowledge-hub/runtime/scripts/run_toy_model_numeric_backend_smoke.sh
```

That script creates one temporary external toy-model backend, runs a tiny
public TFIM exact-diagonalization helper on a fixed config, registers the
generated run note into `L0`, and runs one bounded `aitp loop`.

## 8. Exit gate

Close with:

```bash
aitp audit --topic-slug <topic_slug> --phase exit
```

The run only counts if exit conformance is still honest.

## 9. Real-topic acceptance: scRPA thesis lane

Use this when you want a real formal-theory topic acceptance that starts from
the master's-thesis scRPA material instead of a synthetic smoke payload.

```bash
python research/knowledge-hub/runtime/scripts/run_scrpa_thesis_topic_acceptance.py --json
```

Pass condition:
- the topic lands in the `formal_theory` lane
- the runtime stays in the `light` profile
- `topic_synopsis.json`, `pending_decisions.json`, and `promotion_readiness.json` are materialized
- the topic remains honest about still needing thesis-grounded source/candidate tightening before any stronger closure claim
