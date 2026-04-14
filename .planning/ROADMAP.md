# Roadmap: v2.7 Consultation-Followup Selection Closure

## Result

Milestone phase work complete. Lifecycle closure is next.

## Phases

- [x] **Phase 181: Consultation-Followup Auto Execution** *(Axis 2 + Axis 4)*
- [x] **Phase 181.1: Selected Candidate Route Advancement** *(Axis 4 + Axis 5)*
- [x] **Phase 181.2: Fresh Consultation-Followup Selection Replay Proof** *(Axis 4 + Axis 3)*

## Target Outcome

- once post-review consultation becomes the selected route, the loop can now
  execute that route instead of stalling on a visible-but-non-executable step
- the same consultation step now writes durable consultation and selection
  artifacts, then advances public `next` / `status` onto one selected
  topic-local staged candidate
- one replayable fresh-topic proof records the fourth bounded continue step
  from staged-L2 review into candidate-specific follow-up

## Next Step

Run milestone audit / archive for `v2.7`.

### Phase 181: Consultation-Followup Auto Execution

**Axis:** Axis 2 (inter-layer connection) + Axis 4 (human experience)

**Goal:** make the post-review consultation step executable and durable once it
becomes the selected route on the same fresh topic.

**Requirements:**

- `CFS-01`
- `CFS-02`

**Depends on:** `v2.6`
**Plans:** 1 plan

Plans:

- [x] `181-01` Execute consultation-followup through the bounded auto-action lane and retain durable selection artifacts

### Phase 181.1: Selected Candidate Route Advancement

**Axis:** Axis 4 (human evidence) + Axis 5 (agent-facing steering)

**Goal:** make queue materialization and public surfaces advance from generic
consultation-followup to one selected staged-candidate follow-up.

**Requirements:**

- `CFS-03`

**Depends on:** Phase `181`
**Plans:** 1 plan

Plans:

- [x] `181.1-01` Advance queue and public surfaces onto the selected consultation candidate

### Phase 181.2: Fresh Consultation-Followup Selection Replay Proof

**Axis:** Axis 4 (human evidence) + Axis 3 (data recording)

**Goal:** close the milestone with one replayable fresh-topic proof that the
same topic can execute consultation-followup, write the selection artifact, and
advance onto the selected staged candidate.

**Requirements:**

- `CFS-04`

**Depends on:** Phase `181.1`
**Plans:** 1 plan

Plans:

- [x] `181.2-01` Capture the replayable fresh-topic consultation-followup selection closure packet
