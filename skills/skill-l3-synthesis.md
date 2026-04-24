---
name: skill-l3-synthesis
description: L3 Study — synthesis subplane. Reconstruct the source's contribution and propose L2 updates.
trigger: l3_subplane == "synthesis" AND l3_mode == "study"
---

# Synthesis (Study Mode)

## MANDATORY: AskUserQuestion rule

When you need to ask the user ANY question, you MUST:
1. Call `ToolSearch(query="select:AskUserQuestion", max_results=1)` to load the tool.
2. Call `AskUserQuestion(questions=[{...}])` with your question and options.
NEVER type questions or options as plain text. ALWAYS use the popup tool.

---

You are reconstructing the source's contribution in your own framework and preparing L2 knowledge graph updates.

## Active artifact

`L3/synthesis/active_synthesis.md`

## What to do

### 1. Reconstruct the contribution
- In your own words, what does this source contribute?
- What are the key results, concepts, and techniques?
- How does it connect to the broader physics landscape?

### 2. Propose L2 node updates
For each atomic concept, result, or technique that is `new_to_l2`:
- Define a proposed L2 node with:
  - `node_id`: slugified name
  - `type`: concept | theorem | technique | derivation_chain | result | approximation | open_question
  - `regime_of_validity`: where does this apply?
  - `mathematical_expression`: key formula (if applicable)
  - `physical_meaning`: one-paragraph explanation in simple language

### 3. Propose L2 edge updates
For each relationship between concepts:
- Define proposed edges with:
  - `from_node`, `to_node`
  - `type`: limits_to | derives_from | uses | assumes | corresponds_to | etc.
  - `regime_condition`: under what conditions does this relation hold?
  - `evidence`: what in the source supports this relation?

### 4. Document open questions
- What questions does this source raise but not answer?
- What would need to be studied next?
- Are there contradictions with existing L2 knowledge?

### 5. Submit candidates
For each significant L2 update, submit a candidate via `aitp_submit_candidate`:
- `candidate_type`: atomic_concept | derivation_chain | correspondence_link | regime_boundary | open_question
- `regime_of_validity`: required for study candidates
- `claim`: the knowledge claim in precise language
- `evidence`: trace back to source decomposition and derivation

Fill the artifact:
- `synthesis_statement`: one-paragraph reconstruction
- `l2_update_summary`: summary of proposed nodes and edges
- `## Reconstructed Contribution`: detailed reconstruction
- `## L2 Node Proposals`: proposed nodes with full metadata
- `## L2 Edge Proposals`: proposed edges with types and evidence
- `## Open Questions`: unresolved questions from the source
- `## Regime Annotations`: regime information for all new nodes

## Quality gate (mandatory before submitting candidates)

For each candidate:
1. Does it have `regime_of_validity`?
2. Does every result have a corresponding `limits_to` relation?
3. Does every derivation step have a `justification_type`?
4. Are all blocking gaps from gap_audit resolved or deferred with reason?

## Exit condition

The synthesis subplane is the last study subplane. When complete:
- Submit candidates via `aitp_submit_candidate` for each significant L2 update
- Proceed to L4 validation

The subplane is complete when:
- `synthesis_statement` is filled
- `l2_update_summary` is filled
- At least one candidate has been submitted (or the source had no new contributions)

## Allowed transitions

- Backedges: `gap_audit` (if synthesis reveals additional gaps)
