---
name: skill-promote
description: Promote mode — guide validated candidates through L2 promotion gate.
trigger: status == "validated"
---

# Promote Mode

You are in **promote** mode. Your job: present validated candidates to the human
for L2 promotion approval.

## What to Do

1. **List validated candidates** by calling:
   ```
   aitp_list_candidates(topics_root, topic_slug)
   ```
   Filter for `status == "validated"`.

2. **For each validated candidate**, read its file at `L3/candidates/<id>.md`
   and present the evidence to the human using AskUserQuestion:

   ```
   AskUserQuestion(questions=[{
     "header": "Promote",
     "question": "Candidate '[title]' has passed validation. It claims [brief claim]. Evidence: [summary]. Should I promote it to reusable knowledge (L2)?",
     "options": [
       {"label": "Approve promotion", "description": "Promote to L2/canonical/ as trusted knowledge"},
       {"label": "Needs revision", "description": "Return to derive mode for corrections"},
       {"label": "Reject", "description": "Mark as rejected, do not promote"}
     ],
     "multiSelect": false
   }])
   ```

3. **On human approval**, follow the promotion gate lifecycle:

   a. Request promotion review:
   ```
   aitp_request_promotion(topics_root, topic_slug, candidate_id="...")
   ```

   b. Resolve the promotion gate with the human's decision:
   ```
   aitp_resolve_promotion_gate(topics_root, topic_slug, candidate_id="...", decision="approve", reason="Human approved")
   ```

   c. Execute the promotion:
   ```
   aitp_promote_candidate(topics_root, topic_slug, candidate_id="...", comment="Human approved")
   ```

4. **On revision request**, update the candidate:
   - Read `L3/candidates/<id>.md`
   - Change frontmatter `status: revision_needed`
   - Add the human's feedback to the body
   - Return to derive mode (skill-derive)

5. **After all candidates are resolved**, update topic status:
   ```
   aitp_update_status(topics_root, topic_slug, status="promoted")
   ```

## Promotion Gate Lifecycle

The promotion gate requires three sequential steps. Skipping any step is blocked:

1. `validated` -> `aitp_request_promotion()` -> `pending_approval`
2. `pending_approval` -> `aitp_resolve_promotion_gate(decision="approve")` -> `approved_for_promotion`
3. `approved_for_promotion` -> `aitp_promote_candidate()` -> `promoted` (writes L2 copy)

## Rules

- **L2 promotion ALWAYS requires human approval via AskUserQuestion.** No exceptions.
- **Direct promotion from `validated` is blocked.** You must go through the gate.
- Do not auto-promote without asking the human.
- Present evidence honestly, including gaps and assumptions.
- If a candidate is too wide (mixes multiple claims), split it before promoting.

## Promotion Trace

Every promotion must leave a trace in the candidate file:
- `status: promoted`
- `promotion_requested_at: <timestamp>`
- `approved_at: <timestamp>`
- `promoted_at: <timestamp>`
- `promotion_comment: <why approved>`
- The resulting L2 file path

## After Promotion

After promoting all candidates:
- Ask the human if they want to continue with another candidate
- Or start writing (L5, skill-write)
- Or explore new directions
