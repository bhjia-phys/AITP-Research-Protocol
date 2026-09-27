# On-use revision of an existing research note

This small synthetic exercise checks whether active AITP instructions repair an
existing scientific account when normal research use exposes a substantive
mismatch, then leave the repaired account alone on an unchanged second visit.
It is separate from the frozen `general-v0.1` suite. It adds no runner or framework.

The starting note has more than an old layout: its opening drops a decisive
condition, its proposed next calculation has already been performed, and its
later entries do not reconcile those claims. A correct original derivation, a
subsequent analysis and the original numerical observations are already present.
No outside sources, private research or live services are needed.

## Materials and use

- [prompt.md](prompt.md): first user request, which resumes the research without
  explicitly asking to rewrite its files.
- [workspace/](workspace/): original actor-visible files. Use a disposable copy;
  keep this published starting fixture unchanged.
- [revisit.md](revisit.md): a fresh second session using the workspace resulting
  from the first session. Do not supply the first conversation or new findings.
- [readonly.md](readonly.md): a separate control starting from a fresh copy of
  the original fixture, with an explicit prohibition on file changes.
- [evaluator.md](evaluator.md): evaluator-only expectations and score anchors.

Give an actor only its workspace, the relevant user prompt and the AITP version
being tested. Keep this README and the evaluator separate from actor context.
For a direct comparison of Skill versions, use separate clean copies of the
same fixture, the same model and comparable available tools. A revisit always
starts from its own first session's output, not another version's result.

Retain enough output outside this published fixture to inspect the actual file
changes, the final response and which Skill version was active. Before the
revisit, preserve a copy of the first session's resulting workspace so that a
no-change outcome can be checked directly. The read-only control uses the
original fixture, not the repaired one. No required status schema is introduced.

Evaluate substantive recovery and preservation, not an exact target document or
particular headings. The first pass should repair the live interpretation; it
need not move files, introduce a template or change valid historical evidence.
The second pass should be an ordinary read. Merely repackaging the fixture or
walking through these instructions does not establish the behavior in a fresh
session. No actor trial is included with this exercise.

Executed observations and their limits are summarized in
[validation](../../docs/validation.md#on-use-revision-of-an-outdated-main-note-2026-09-22).
Actual actor records stay outside the published tree.
