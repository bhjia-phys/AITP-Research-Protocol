# Roadmap: v1.94 L4 Analytical Cross-Check Surface

## Result

`v1.94` closed successfully.

## Phases

- [x] **Phase 168: Analytical Check Rows And Review Contract Expansion** *(Axis 1 + Axis 2)*
- [x] **Phase 168.1: Analytical Runtime Surface And Proof Lane** *(Axis 2 + Axis 4)*

## Target Outcome

- analytical validation records explicit bounded check rows instead of only a
  flatter aggregate review artifact
- each analytical check keeps the source anchors, assumption or regime context,
  and per-check status needed for human judgment
- runtime-facing read paths expose the same analytical cross-check surface
- one bounded analytical proof lane closes the milestone

## Next Step

Start the next milestone with `$gsd-new-milestone`.

### Phase 168: Analytical Check Rows And Review Contract Expansion

**Axis:** Axis 1 (`L4` internal) + Axis 2 (`L4 -> runtime artifacts`)

**Goal:** Expand the analytical review contract so bounded analytical checks are
 first-class rows with explicit context instead of only a flatter aggregate
 review payload.

**Motivation:**

- `v1.47` made analytical review a first-class production mode, but broader
  analytical validation beyond the baseline review artifact remains open
- `v1.93` now makes contradiction visibility explicit, which creates a natural
  downstream need for stronger analytical cross-check surfaces
- the next bounded improvement should make analytical validation easier to read,
  replay, and compare without reopening the symbolic backend question

**Requirements:**

- `REQ-ANX-01`
- `REQ-ANX-02`

**Depends on:** `v1.93`
**Plans:** 1 plan

Plans:

- [x] `168-01` Add explicit analytical check rows and richer review contract context

### Phase 168.1: Analytical Runtime Surface And Proof Lane

**Axis:** Axis 2 (`L4 -> runtime read path`) + Axis 4 (human experience)

**Goal:** Surface the richer analytical cross-check contract on runtime/read
paths and leave one bounded analytical proof lane.

**Motivation:**

- analytical check rows are only useful if they survive into the runtime
  surfaces humans actually read
- the milestone should close on one bounded proof lane rather than on contract
  claims alone

**Requirements:**

- `REQ-ANX-03`
- `REQ-VERIFY-01`

**Depends on:** Phase `168`
**Plans:** 1 plan

Plans:

- [x] `168.1-01` Surface analytical cross-check rows across runtime read paths
  and prove one bounded analytical lane
