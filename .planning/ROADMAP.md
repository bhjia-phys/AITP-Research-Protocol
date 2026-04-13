# Roadmap: v2.2 Fresh-Topic First-Use Reliability

## Result

Milestone phase work complete. Lifecycle closure is next.

## Phases

- [x] **Phase 176: New-Topic Session-Start Routing Hardening** *(Axis 4 + Axis 5)*
- [x] **Phase 176.1: Windows Source Registration Path And Status Coherence** *(Axis 1 + Axis 4)*
- [x] **Phase 176.2: Fresh Real-Topic First-Use Replay Proof** *(Axis 4 + Axis 5)*

## Target Outcome

- explicit natural-language "start a new topic" requests allocate fresh topics
  instead of silently reopening stale current-topic memory
- first-source registration on Windows survives long real-topic slugs and long
  paper titles without non-credible operator workarounds
- `aitp status` and related topic-state surfaces become coherent immediately
  after first-source registration
- the milestone ends with one replayable fresh real-topic first-use proof
  package and explicit non-claims

## Next Step

Run milestone audit / archive for `v2.2`.

### Phase 176: New-Topic Session-Start Routing Hardening

**Axis:** Axis 4 (human experience) + Axis 5 (agent-facing steering)

**Goal:** make fresh natural-language topic-start requests reliably outrank
stale current-topic continuation when the operator explicitly asks to begin a
new research topic.

**Requirements:**

- `FTF-01`
- `FTF-02`

**Depends on:** `v2.1`
**Plans:** 1 plan

Plans:

- [x] `176-01` Fix fresh-topic intent routing so explicit new-topic requests do not reopen current topics

### Phase 176.1: Windows Source Registration Path And Status Coherence

**Axis:** Axis 1 (layer-internal optimization) + Axis 4 (human experience)

**Goal:** make first-source registration survive long Windows paths and keep
status-facing `L0` state coherent immediately after successful registration.

**Requirements:**

- `FTF-03`
- `FTF-04`

**Depends on:** Phase `176`
**Plans:** 1 plan

Plans:

- [x] `176.1-01` Shorten Windows source paths and synchronize status after registration

### Phase 176.2: Fresh Real-Topic First-Use Replay Proof

**Axis:** Axis 4 (human evidence) + Axis 5 (agent-facing steering)

**Goal:** replay one fresh real-topic first-use lane from natural-language
topic start through first-source registration and honest status readback, then
close with durable receipts and explicit non-claims.

**Requirements:**

- `FTF-05`

**Depends on:** Phase `176.1`
**Plans:** 1 plan

Plans:

- [x] `176.2-01` Replay a fresh real-topic first-use proof from session-start through first source registration
