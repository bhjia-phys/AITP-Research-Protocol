---
name: skill-continuous
description: Resume mode — restore workflow after session break or context compaction.
trigger: any status after session break
---

# Resume Mode

Your session was interrupted (context compaction, new session, or break).
This skill helps you pick up where you left off.

## What to Do

1. **Read the current execution brief** by calling:
   ```
   aitp_get_execution_brief(topics_root, topic_slug)
   ```

2. **Inspect the brief fields:**
   - `stage` — which research stage (L1, L3, L4, L2, L5)
   - `posture` — current operating stance (read, frame, derive, verify, distill, write)
   - `gate_status` — ready or blocked, and why
   - `required_artifact_path` — what file needs work
   - `missing_requirements` — specific fields or sections to fill

3. **Read the posture skill** named by the brief's `skill` field.

4. **Do not advance** if the brief says the topic is blocked. Fix the missing requirements first.

5. **If you need the full topic picture**, also read:
   - `state.md` — current status and research question
   - `L3/derivations.md` — what derivations have been done
   - `L3/candidates/*.md` — what candidates exist

## Rules

- Do NOT start from scratch. Read what already exists.
- Do NOT assume the status is correct. The brief is the authority.
- Do NOT bypass a blocked gate. Fix the missing artifact first.
- If you find work that was in progress but not recorded, record it now.

## After Resume

Once you've rebuilt context and injected the correct skill, continue the
workflow from where it was. Do not repeat completed steps.
