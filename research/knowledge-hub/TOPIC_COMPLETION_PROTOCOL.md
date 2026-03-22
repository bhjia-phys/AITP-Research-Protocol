# Topic Completion Protocol

This file defines the public AITP contract for deciding when a theory topic is
complete enough to control promotion, cited-gap recovery, and downstream reuse.

Topic completion is not "many notes exist."
It is the point where a topic branch can answer bounded regression questions,
route failures durably, and expose exactly which claims are still external.

## 1. Why this exists

Proof-grade theory work becomes unreliable when:

- a topic has many units but no stable question surface,
- promotion is attempted from coverage alone,
- follow-up source recovery happens ad hoc,
- or wide candidates are treated as reusable just because they sound coherent.

This protocol makes topic completion a first-class gate.

## 2. Required completion surfaces

Every reusable theory topic should maintain:

- a source-map or topic-charter backbone,
- a stable regression suite manifest,
- stable regression questions,
- stable question oracles,
- recent regression run logs,
- durable writeback from non-pass results into gaps, follow-up tasks, or future buffers.

If these surfaces are missing, the topic is not completion-ready.

The runtime `topic_completion.json` surface may materialize that manifest as an
embedded regression-manifest object plus explicit gate checks, but it must not
hide whether questions, oracles, runs, blocker clearance, or follow-up debt are
still missing.

## 3. Regression-governed promotion rule

Theory-formal promotion must be governed by the topic regression surface.

At minimum, a promotion-ready candidate should expose:

- the supporting regression question ids,
- the supporting oracle ids,
- at least one recent regression run id that justifies the local claim surface,
- a topic-completion status,
- an explicit blocker list,
- explicit split and cited-recovery flags when relevant.

Coverage and consensus remain necessary.
They are not substitutes for regression-backed topic readiness.

## 4. Completion states

Projects may refine the labels, but the public interpretation should stay:

- `not_assessed`: no topic-completion judgment yet
- `gap-aware`: the branch can at least state what is missing
- `regression-seeded`: the branch owns a stable question/oracle surface
- `regression-stable`: flagship questions pass without hidden proof collapse
- `promotion-ready`: the candidate's relevant regression surface is recent and blocker-clear
- `promotion-blocked`: the candidate still carries blocker or split debt

## 5. Wide or mixed candidate rule

If a candidate mixes several independent claims, or mixes reusable content with
still-unresolved material, the topic must not promote it as one object.

The correct route is:

1. emit a split contract,
2. promote bounded children only,
3. park unresolved fragments in the deferred buffer,
4. reactivate those fragments only when their declared triggers are satisfied.

## 6. Cited-gap recovery rule

When a regression or self-interrogation answer says the topic cannot complete a
step locally, the follow-up route must be explicit:

- create or update the relevant open gap,
- create or update the follow-up source task,
- run bounded literature follow-up,
- spawn an independent follow-up subtopic when the gap deserves fresh `L0`,
- give that child topic a return packet naming the parent gaps and reintegration targets.

The child topic should return recovered units or an honest unresolved result,
not silent background reading.

That return should be updated in the child-side return packet before the parent
topic runs reintegration.
Parent reintegration is a separate durable receipt, not a hidden side effect of
the child topic itself.

## 7. Verification non-equivalence

A topic may be verification-rich but still not completion-ready.

For example:

- a numerical check may pass while the proof surface is still compressed,
- a coverage audit may pass while regression-backed gap honesty is missing,
- or a child follow-up topic may exist while its return packet has not been reintegrated.

Topic completion remains a separate gate.

## 8. Script boundary

Scripts may:

- materialize completion artifacts,
- aggregate regression state,
- detect declared blockers,
- scaffold follow-up return packets,
- and gate auto-promotion against declared policy fields.

Scripts may not decide that a topic is mathematically complete merely because a
schema is full or a coverage audit passed.
