---
name: skill-continuous
description: Resume mode — restore workflow after session break or context compaction.
trigger: any status after session break
---

# Resume Mode

Your session was interrupted (context compaction, new session, or break).
This skill helps you pick up where you left off.

## What to Do

1. **Check system health** (optional but recommended after long breaks):
   ```
   aitp_health_check(topics_root)
   ```
   Returns aggregated status across all topics — useful for spotting
   stuck topics, background job failures, or gate anomalies.

2. **Read the current execution brief** by calling:
   ```
   aitp_get_execution_brief(topics_root, topic_slug)
   ```

3. **Inspect the brief fields:**
   - `stage` — which research stage (L0, L1, L3, L4, L2)
   - `posture` — current operating stance (discover, read, frame, derive, verify, distill)
   - `gate_status` — ready or blocked, and why
   - `entry_profile` — which L3 workflow profile is active (learn_paper / explore_idea / continue_work / l4_return)
   - `required_artifact_path` — what file needs work
   - `missing_requirements` — specific fields or sections to fill
   - `skill` — which skill to load next

4. **If `entry_profile` is set**, note the recommended L3 activity DAG:
   - `learn_paper`: trace-derivation → gap-audit → connect → integrate → distill
   - `explore_idea`: ideate → plan → derive → gap-audit → integrate → distill
   - `continue_work`: resume from state.md `l3_activity`, follow parent DAG
   - `l4_return`: integrate → distill (revise claim from L4 feedback)

5. **Read the posture skill** named by the brief's `skill` field.

6. **Do not advance** if the brief says the topic is blocked. Fix the missing requirements first.

7. **If you need the full topic picture**, also read:
   - `state.md` — current status, research question, lane, domain
   - `L1/convention_snapshot.md` — locked notation and conventions
   - `L3/derive/active_derivation.md` — what derivations have been done
   - `L3/candidates/*.md` — what candidates exist
   - `L4/reviews/*.md` — what validations have been done

8. **Check topic status directly** if the brief seems stale:
   ```
   aitp_get_status(topics_root, topic_slug)
   ```

9. **Resume the session** if interrupted:
   ```
   aitp_session_resume(topics_root, topic_slug)
   ```
   This restores session state and logs the continuation.

## Rules

- Do NOT start from scratch. Read what already exists.
- Do NOT assume the status is correct. The brief is the authority.
- Do NOT bypass a blocked gate. Fix the missing artifact first.
- If you find work that was in progress but not recorded, record it now.
- If the brief shows `l1_feedback_status: "missing"`, check whether L3
  discovered conventions or contradictions that should flow back to L1.

## After Resume

Once you've rebuilt context and injected the correct skill, continue the
workflow from where it was. Do not repeat completed steps.

## Administrative Operations

These are available but should be used sparingly — usually at human request:

| Operation | Tool | When |
|-----------|------|------|
| Switch lane | `aitp_switch_lane(topics_root, topic_slug, new_lane)` | If the research approach needs to change |
| Gate override | `aitp_gate_override(topics_root, topic_slug, reason)` | If a gate is blocking incorrectly (rare) |
| Fork topic | `aitp_fork_topic(topics_root, topic_slug, new_slug)` | For parallel exploration of different approaches |
| Archive topic | `aitp_archive_topic(topics_root, topic_slug)` | When a topic is complete or abandoned |
| Restore topic | `aitp_restore_topic(topics_root, topic_slug)` | To resume an archived topic |
| Set interaction | `aitp_set_interaction_level(topics_root, topic_slug, level)` | To adjust agent verbosity |
| Resolve conflict | `aitp_resolve_conflict(topics_root, topic_slug, conflict_id, resolution)` | To close a registered contradiction |
