# Roadmap: v2.1 L2 Real-Topic Relevance Hardening

## Result

Milestone phase work complete. Lifecycle closure is next.

## Phases

- [x] **Phase 175: Staging Provenance And Noise Suppression** *(Axis 1 + Axis 3)*
- [x] **Phase 175.1: Topic-Local Consultation Relevance Ordering** *(Axis 1 + Axis 2)*
- [x] **Phase 175.2: Multi-Paper Real-Topic L2 Relevance Proof** *(Axis 4 + Axis 5)*

## Target Outcome

- fresh-topic staged rows carry cleaner reusable knowledge instead of noisy
  generic notation and weak method artifacts
- fresh-topic staged rows preserve correct source provenance across multi-paper
  intake
- fresh-topic `consult-l2` primary hits favor the locally relevant topic rows
  over unrelated canonical carryover when the query clearly targets the new
  topic
- the milestone ends with one replayable multi-paper proof package and explicit
  non-claims

## Next Step

Run milestone audit / archive for `v2.1`.

### Phase 175: Staging Provenance And Noise Suppression

**Axis:** Axis 1 (layer-internal optimization) + Axis 3 (data recording)

**Goal:** harden literature-intake staging so reusable rows stay clean and keep
the true source provenance before they reach consultation or downstream `L2`
surfaces.

**Requirements:**

- `L2H-01`
- `L2H-02`

**Depends on:** `v2.0`
**Plans:** 1 plan

Plans:

- [x] `175-01` Suppress noisy staged rows and preserve true source provenance

### Phase 175.1: Topic-Local Consultation Relevance Ordering

**Axis:** Axis 1 (layer-internal optimization) + Axis 2 (inter-layer connection)

**Goal:** improve `consult-l2` ranking so clear fresh-topic queries surface the
most relevant local staged or canonical rows before unrelated carryover from
other topics.

**Requirements:**

- `L2H-03`

**Depends on:** Phase `175`
**Plans:** 1 plan

Plans:

- [x] `175.1-01` Raise topic-local staged relevance above unrelated canonical carryover

### Phase 175.2: Multi-Paper Real-Topic L2 Relevance Proof

**Axis:** Axis 4 (human evidence) + Axis 5 (agent-facing steering)

**Goal:** prove the bounded `L2` hardening slice on one replayable multi-paper
real-topic acceptance lane, then close with durable receipts and explicit
non-claims.

**Requirements:**

- `L2H-04`
- `L2H-05`

**Depends on:** Phase `175.1`
**Plans:** 1 plan

Plans:

- [x] `175.2-01` Replay the multi-paper real-topic proof and close the milestone honestly
