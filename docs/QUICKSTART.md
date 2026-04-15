# 5-Minute Quickstart

This is the shortest audited path from "AITP is installed" to "AITP handled a
real topic once."

It is intentionally runtime-neutral:

- Codex, Claude Code, and OpenCode each have a different native front door.
- Once AITP is active, the first-run proof should still reduce to the same
  kernel path: `bootstrap -> loop -> status`.
- This guide uses the direct CLI path because it is the easiest way to verify
  that the shared runtime actually works.

If you have not installed AITP yet, start with [`docs/INSTALL.md`](INSTALL.md).

## 1. Verify the install

From a clean shell:

```bash
python -m pip install aitp-kernel
aitp --version
aitp doctor
aitp doctor --json
```

If you are on Windows-native and are still using the repo-local launcher from a
local checkout, run:

```cmd
scripts\aitp-local.cmd doctor
```

Contributor/local-dev note:

```bash
python -m pip install -e research/knowledge-hub
```

That editable install remains the right path when you are changing this
repository itself.

Your target runtime row should be `ready` in:

- `runtime_support_matrix.runtimes.codex.status`
- `runtime_support_matrix.runtimes.claude_code.status`
- `runtime_support_matrix.runtimes.opencode.status`

If your runtime is not `ready`, run that row's
`runtime_support_matrix.runtimes.<runtime>.remediation.command`, then rerun
`aitp doctor --json`.

## 2. Start one real topic

Use a real topic statement rather than a synthetic demo shell:

```bash
aitp bootstrap \
  --topic "Jones Chapter 4 finite-dimensional backbone" \
  --statement "Start from the finite-dimensional backbone and record the first honest closure target."
```

Windows-native one-line equivalent:

```cmd
scripts\aitp-local.cmd bootstrap --topic "Jones Chapter 4 finite-dimensional backbone" --statement "Start from the finite-dimensional backbone and record the first honest closure target."
```

What this should do:

- create `topics/jones-chapter-4-finite-dimensional-backbone/runtime/`
- materialize the first bounded research contract
- write `runtime_protocol.generated.json|md`

## 3. Take one bounded step

```bash
aitp loop \
  --topic-slug jones-chapter-4-finite-dimensional-backbone \
  --human-request "Continue with the first bounded route and stop before expensive execution." \
  --max-auto-steps 1
```

Windows-native one-line equivalent:

```cmd
scripts\aitp-local.cmd loop --topic-slug jones-chapter-4-finite-dimensional-backbone --human-request "Continue with the first bounded route and stop before expensive execution." --max-auto-steps 1
```

What this should do:

- keep the topic in the normal AITP loop instead of a one-shot shell
- write `loop_state.json`
- refresh the runtime protocol after the bounded action

## 4. Inspect what happened

```bash
aitp status --topic-slug jones-chapter-4-finite-dimensional-backbone
```

Windows-native one-line equivalent:

```cmd
scripts\aitp-local.cmd status --topic-slug jones-chapter-4-finite-dimensional-backbone
```

You should now be able to see:

- the current stage
- the selected next action
- the primary runtime surfaces for the topic

If you want the next bounded action without the larger status packet, run:

```bash
aitp next --topic-slug jones-chapter-4-finite-dimensional-backbone
```

## Runtime Notes

- Codex: the preferred UX is native `using-aitp` skill discovery. Use the CLI
  quickstart above as the fallback and verification path.
- Claude Code: the preferred UX is SessionStart bootstrap. The CLI quickstart
  above is still the shared first-run proof, and Windows-native SessionStart
  now prefers a Python hook sidecar instead of assuming bash.
- OpenCode: the preferred UX is plugin bootstrap. The CLI quickstart above is
  still the shared first-run proof.
- All three front doors should expose the same plain-language human-control
  posture and autonomous-continuation posture through
  `session_start.generated.md` and `runtime_protocol.generated.md`.
- If no real checkpoint is active, continue bounded work without ritual
  reconfirmation. In `verify + iterative_verify`, let the bounded L3-L4 loop
  keep cycling until success, a real blocker, or a real human checkpoint
  appears.

Windows note:

- If a runtime-specific bootstrap is not ready yet, `scripts\aitp-local.cmd`
  is the zero-WSL fallback for the shared quickstart path.
- For Codex on Windows, if you want to avoid creating a junction under
  `~/.agents/skills`, use `scripts\aitp-local.cmd install-agent --agent codex --scope user`
  and refresh those copied assets when the repo updates.

If a native front door does not claim the session yet, use:

```bash
aitp session-start "<task>"
```

and then return to the normal topic commands once the topic exists.
