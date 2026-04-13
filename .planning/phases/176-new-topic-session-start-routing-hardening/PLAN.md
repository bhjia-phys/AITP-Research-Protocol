# Plan: 176-01 - Fix fresh-topic intent routing so explicit new-topic requests do not reopen current topics

**Phase:** 176
**Axis:** Axis 4 (human experience) + Axis 5 (agent-facing steering)
**Requirements:** FTF-01, FTF-02

## Goal

Make long natural-language fresh-topic requests route to `request_new_topic`
even when the same sentence also references continuing AITP autonomously or not
continuing the current topic.

## Planned Route

### Step 1: Add failing route regressions

**File:**
- `research/knowledge-hub/tests/test_aitp_service.py`

Add one route-level regression and one `start_chat_session()` regression for a
long "start a new research program from scratch on ..." request while durable
current-topic memory is present.

### Step 2: Fix bounded title extraction

**File:**
- `research/knowledge-hub/knowledge_hub/aitp_service.py`

Extend `_extract_new_topic_title()` to recognize fresh-topic requests phrased
as new research programs/projects, including "from scratch" wording, and trim
follow-up steering clauses out of the extracted title.

### Step 3: Preserve receipts

**Command to preserve as evidence:**
- `python -m pytest research/knowledge-hub/tests/test_aitp_service.py -k "detects_new_topic_from_natural_language or detects_brand_new_research_topic_named_in_english or prefers_current_topic_reference or from_scratch_new_research_program_outranks_current_topic_memory or projection_hint_does_not_override_current_topic or start_chat_session_materializes_current_topic_route or start_chat_session_allocates_fresh_slug_for_explicit_new_topic_collision or start_chat_session_from_scratch_request_allocates_new_topic_even_with_current_topic_memory" -q`

## Acceptance Criteria

- [x] a long "from scratch" new-topic request outranks durable current-topic
      memory at route time
- [x] `start_chat_session()` records the same new-topic route durably
- [x] existing bounded current-topic and explicit new-topic routing regressions
      remain green
