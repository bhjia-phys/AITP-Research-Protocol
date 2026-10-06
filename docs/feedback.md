# Feedback from research use

Entries below retain the observation and proposal status at their stated dates.
Subsequent source changes and executed checks are recorded in
[validation and its limits](validation.md).

## A consequential side investigation was not integrated at handoff

Reported on 2026-09-15 against source checkout
`0f6dc4cdea09106a46d53cf6355b09a924d8e21b`. This is a sanitized account of an
observed research interaction and the agent's subsequent review. It is not an
independent evaluation, an activation-rate measurement or a validated Skill fix.
Private research files and conversation transcripts remain outside this tree.

### What happened and why it mattered

A researcher requested an orbital-resolved band and density-of-states analysis
in a side conversation to clarify the subspaces used in a screening calculation.
The agent produced a supporting analysis, numerical checks, candidate band sets
and figures. The analysis strengthened the evidence for some candidate subspaces
and exposed a continuity failure in another selector. This changed a modeling
assumption and the next scientific question, so it warranted more than saving
the output files.

The supporting work initially remained separate from the main research account.
The agent did not proactively tell the researcher that integration was pending.
The researcher had to ask whether it had been recorded in the main note, then
explicitly request integration, and then question the explanation of automatic
recording. These are three recording-related follow-ups in this interaction;
they are not a general estimate of user effort or failure frequency.

The agent's initial explanation that AITP did not automatically collect side
work was incomplete. It correctly described the absence of a background service,
but obscured the agent's responsibility to retain consequential work during the
task. Saving a supporting report did not by itself update the larger argument.

### Existing guidance and the execution failure

The source guidance already addresses this behavior:

- [Memory entry and integration](../plugins/aitp/skills/aitp-memory/SKILL.md)
  require preserving a useful branch's origin, working home and relationship
  to the originating question, and revising claims affected by new evidence.
- [Following a side investigation](../plugins/aitp/skills/aitp-writing/references/supporting-notes.md#follow-a-side-investigation)
  requires connecting branch results or consequential failures to the affected
  originating claim or next step.
- [Recording decisions](when-to-write.md) distinguish unchanged questions,
  supporting detail and changes to the main argument. They do not require the
  researcher to request memory maintenance again after every useful result.

The observed failure was therefore an execution and handoff omission despite
relevant existing instructions. This case does not establish that the Skill
failed to activate or that its wording alone caused the omission. The current
instructions can nevertheless make the handoff under restricted authority more
explicit.

The side conversation limited file mutations to explicitly requested work and
prohibited taking over the main thread. The agent treated that boundary as a
reason to keep the investigation separate. Such a boundary must be respected;
it does not justify leaving the integration state implicit. Where main-note
editing is outside the authorized scope, the agent should identify the affected
claim, preserve the available evidence and state that integration remains pending.
Where authorization already covers the update, it should perform that work
without asking the researcher to approve it again. Shared-file edits also require
reading the current argument and preserving concurrent changes.

### Recovery in this case

After the explicit integration request, the agent read the current complete main
note and revised the opening, affected modeling discussion and conclusion. It
linked the supporting analysis and combined band/PDOS figure, and qualified the
related derivation. It preserved the distinction between a passing response on
a finite mesh and a validated continuous localized model, rather than treating
the newly identified limitation as invalidating every earlier numerical result.

A subsequent read confirmed that the main note contains the supporting links,
figure and scientific qualification. The original numerical outputs and ongoing
calculations were preserved. This establishes recovery of this record, not
reliable future behavior. No new independent agent trial was performed.

### Suggested clarification, not an implemented behavior change

Add a short clarification at the existing memory handoff guidance, with a pointer
from the side-investigation guidance if useful:

> When a side investigation changes the originating argument, integrate the
> affected claims within the current authorization before reporting completion.
> If permissions or conversation scope prevent that edit, retain the evidence
> where authorized and explicitly identify the target note, changed claim and
> pending integration in the handoff. Distinguish saving an artifact from
> integrating its implication. Reuse authorization already given; absence of
> background synchronization does not remove the agent's recording responsibility.

This should remain a small clarification of existing editorial work. It does
not require a runtime hook, automatic cross-thread writes, a ledger, a new report
for every branch, routine approval requests or an end-of-turn recording form.
The implication and its recording state can normally be communicated in one
sentence alongside the scientific result.

If the clarification is implemented later, use a small concrete task with these
distinctions:

| Situation | Behavior to check |
| --- | --- |
| A branch changes a main conclusion and the update is authorized | Integrate the affected passages and evidence without another user reminder. |
| The same result arises under a read-only or restricted side-conversation scope | Preserve what is authorized and provide an explicit pending handoff; do not edit the main note without authority. |
| A branch adds detail while the main account remains accurate | Keep the detail in its supporting home and adjust discovery only as needed. |
| An unchanged status or explanation question adds no durable result | Answer without a memory write. |

Check the observed edits and the need for user reminders; do not infer success
from the presence of the instruction or from Markdown validation. The suggested
clarification and these checks have not been implemented or executed by this
feedback-only change.

### Subsequent clarification and its validation boundary

On 2026-09-16 a further review found a related failure: the main note had
received new links and status paragraphs, yet retained overlapping old states,
and the first useful numerical values discovered in a later job-status answer
were absent from its results. The live argument had not converged despite
the presence of relevant instructions and prior recovery. This distinguishes
writing to the main file from actually maintaining its scientific account.

The source [memory Skill](../plugins/aitp/skills/aitp-memory/SKILL.md) and
[recording guidance](when-to-write.md) now explicitly cover provisional first
results discovered during a job poll, checking whether the main text carries
the model/result/question, replacing stale claims rather than appending status,
and handing back the main-note link after integration. Explicit read-only scope
still limits edits. No background writer, runtime gate or per-turn form was added.

The associated repair uses the actual research case: the original main note is
preserved, its current method and provisional numerical results are integrated,
and historical failures and independent branches retain their evidence links.
This is a same-agent recovery and an authored application of the clarification.
It is not an independent-session test of future compliance. Unchanged polling
and supporting-only detail remain no-main-write cases; reliable autonomous
integration still requires observation in subsequent research use.

## Proposal: an optional reminder when the agent is about to finish a turn

Requested on 2026-09-16 following the main-note omissions described above. The
researcher suggested shipping a short reminder hook with AITP. This entry records
that proposal; it does not implement or enable a hook.

### Motivation and suggested reminder

The observed omissions occurred despite existing integration guidance. A hook
could make the editorial decision salient at handoff, while the Skills continue
to explain how to maintain the argument. The latest wording clarification has
not yet been tested in an independent session; this proposal is not evidence
that the revised wording failed or that a hook will fix the problem.

Keep the model-facing reminder to one sentence:

> Before finishing, check whether this task's important results, corrections and
> next research step are integrated into the relevant main note, beyond saving
> supporting notes; fill any gap within existing authorization, and make no edit
> if there is no durable change or the user requested read-only work.

The reminder should be optional, scoped to research work, and sent to the agent
while it can still act. It should not require a user-facing checklist, a new
record, a completion keyword, or a main-note edit after every answer. The agent
still has to understand the current argument, preserve evidence and provisional
qualifications, and respect explicit limits on editing. The hook itself should
not write scientific conclusions or infer permission from an old transcript.

### Host feasibility and the cost of a reminder

A local check found Codex CLI `0.154.0` with the `hooks` feature enabled. A
separate source inspection used Codex revision
`d3812ddbb3b62f46fd9b70fdb96af04d45556e78`:

- `codex-rs/core/src/session/turn.rs` handles `Stop` before completing a turn.
  A block outcome carrying a prompt feeds that prompt back to the model and
  continues the turn.
- `codex-rs/hooks/src/events/stop.rs` accepts a continuation reason with
  `decision: block`; merely displaying a message does not provide that model
  continuation.
- `codex-rs/hooks/src/events/session_end.rs` runs `SessionEnd` during teardown,
  with a short timeout and no continuation outcome. It is unsuitable for asking
  the model to synthesize and edit its research note before exit.

Thus the useful trigger is a turn-completion attempt, not closing the session.
The proposal allows at most one reminder continuation per turn, with
`stop_hook_active` used to avoid repeating it during a hook-induced continuation.
This temporarily defers completion and adds model work, latency and token cost,
even if the agent decides that no note edit is needed. It must not repeatedly
block completion until a file changes. Keep the reminder text portable and any
host-specific adapter small; the Codex inspection does not establish support in
other hosts or verify the installed binary against that source revision.

### Small validation before adopting it

Use a fresh agent session with a small research task and inspect the actual
handoff, rather than treating a hook invocation as successful integration:

| Case | Expected behavior |
| --- | --- |
| A supporting investigation changes a main claim or supplies its first consequential provisional result | Integrate the implication and evidence into the affected main-note passages without another user reminder. |
| An unchanged poll or explanation adds no durable result | Finish without a note edit or an extra recording form. |
| A consequential discovery occurs under an explicit read-only scope | Leave files unchanged and identify the pending integration in the handoff. |

Observe whether the hook repeats, whether the main argument is actually current,
whether the researcher must intervene, and what extra continuation cost occurs.
This feedback change includes no hook implementation, installation, independent
session trial, or claim of improved reliability.

## Theoretical physics: preserve reasoning and history with less interruption

Rewritten on 2026-09-17 at the researcher's request, consolidating the discussion
of theoretical exploration, long-term research history and AITP's useful role.
Extended on 2026-09-22 after a computational-research review to address memory
architecture and document writing together, rather than treating the observed
problems solely as failures to obey recording instructions.
This is qualitative feedback from a long-running research interaction and the
agent's reflection, not an independent evaluation or a new verification of the
physics. The example below is illustrative and sanitized. Private research
files, unpublished results and conversation transcripts remain outside this tree.

### Recommendation

Optimize AITP for continuing a scientific argument, not administering a sequence
of research actions. Its value should be that a researcher can recover what was
established, under which assumptions, why a route changed and where to continue,
without repeatedly reconstructing the project or maintaining parallel summaries.

The intended design is a coherent evolving main note, linked complete derivations
and evidence, retained explanations of consequential turns, and focused Skills
for useful reusable procedures. These are roles for existing material, not four
mandatory file types. Reduce duplicated maintenance, not the detail required to
understand and check a result.

AITP is neither useless by definition nor necessarily better than ordinary notes.
A well-maintained collection of Markdown and TeX files may serve this project
better if extra instructions introduce more interruption than useful guidance.
Removing AITP need not remove research memory. Whether to retain it should depend
on its additional benefit over that baseline.

### What needs fixing, and what AITP cannot fix

The interaction exposed concern about repeated recording, repeated recovery and
apparent activity without corresponding progress toward the physical question.
Retained derivations and explanations of earlier routes also made previous work
recoverable. These observations support improving the workflow; they do not
measure a slowdown caused by AITP or establish that removing it would accelerate
the research.

Separate three failure modes:

- A lost assumption, derivation or reason for abandoning a route is a memory
  failure. Preserve the missing reasoning and make it discoverable.
- Repeated full reads, duplicate summaries or compulsory writes without a changed
  understanding are workflow overhead. Remove redundant obligations.
- An irrelevant calculation, unsupported physical identification or mistaken
  inference is a research-judgment failure. Better recording may expose it, but
  cannot replace the missing argument or choose the correct theory.

Historical Entries, working Notes and status handoffs sometimes repeated the same
result. The active repository already uses Markdown and Skills instead of that
ledger. Do not present retired requirements as current behavior or restore them
as a solution. Existing [memory guidance](../plugins/aitp/skills/aitp-memory/SKILL.md)
and [recording guidance](when-to-write.md) already cover much of the desired
behavior. Distinguish absent guidance from failure to follow it before adding
another instruction. The agent remains responsible for unnecessary tool use and
its scientific choices.

That responsibility does not settle the design question. Repeated difficulty
recovering the current result from successfully saved material also calls for
reviewing the organization and update rules of the memory itself. In the reviewed
project, the main account accumulated older numerical comparisons, subsequent
corrections, job states, method discussion and deliverable descriptions, including
in its opening synthesis. The information was recoverable, but the researcher
still had to ask which result and method currently applied. Existing instructions
to keep the argument coherent had not prevented this accumulation. This is
qualitative evidence for improving the design and testing its use, not proof
that a particular replacement architecture will perform better.

### Preserve both current understanding and how it was reached

The main note, normally `research.md`, should read as an evolving research
argument: the question, physical setting, assumptions, decisive reasoning,
supported answer and unresolved obstruction. It should not become a chronological
queue of updates. A reader must be able to understand the current conclusion
without assembling it from every linked file.

Detailed notes retain the actual derivation: definitions, conventions, intermediate
steps carrying the argument, imported results with their hypotheses and source
locations, and what each check does or does not establish. In formal theory,
orientation, global gauge group, spin structure, boundary conditions, and a
map's domain and codomain can be decisive. A status label such as "verified"
cannot replace those details. Keep one primary derivation and link to its uses.

Long-term memory must also retain why a plausible approach was attempted, what
it established, why it became insufficient, what remains reusable, and what
would justify reopening it. Put that explanation next to the relevant reasoning
or in a short earlier-approaches passage, with links to the original evidence.
It need not be a second ledger or a transcript of every algebraic step.

For example, a useful historical explanation would say:

> We computed fusion coefficients within a proposed wall theory. That calculation
> did not identify the abstract lines with physical probes or determine how
> distinct physical walls attach to a junction. The coefficients remain useful
> under the proposal's assumptions. The next question is the missing attachment,
> not another calculation of the same coefficients.

This is an example of how to retain a logical boundary, not a claim about the
present status of a particular model. A subsequent attachment construction
should change the account and identify the new evidence. It must not make the
earlier conditional calculation appear to have established that identification.

A current summary alone loses this history; an uncurated archive makes it hard
to use. Preserve consequential earlier arguments while correcting their live
interpretation through the existing
[correction guidance](../plugins/aitp/skills/aitp-writing/references/supporting-notes.md#correct-claims-and-keep-earlier-routes-findable).
Do not overwrite the only complete derivation with a summary. Keep known
corrections visible wherever affected maintained claims are used, without turning
a wording edit into a whole-project audit.

Historical recovery has a hard limit: only retained material can be recovered.
A link or hash does not preserve a file's previous contents, and Git cannot
recover versions never recorded. Distinguish contemporary records from later
reconstruction; admit missing reasons instead of inventing them. Preserve
valuable existing history without requiring exhaustive session reconstruction,
automatic commits or a new versioning ritual.

### Memory architecture and writing need a shared unit of change

Here, data architecture means where an assertion is maintained, what evidence
and assumptions it depends on, how a correction replaces its live interpretation,
and how a reader finds the relevant account. Changing storage technology alone
would not resolve the ambiguity. A useful unit of maintenance is a scientific
claim or question with its conditions and evidence, rather than a completed turn
or newly produced file. This can be expressed in ordinary prose and links.

Clarify the different roles of retained content and their update behavior:

| Role | What it carries | What happens when understanding changes |
| --- | --- | --- |
| Current research argument | Question, assumptions, decisive reasoning, supported result and remaining uncertainty | Revise the affected account; replace stale interpretations and reconcile its opening and conclusion |
| Detailed reasoning and reusable explanations | Complete derivations, model definitions, literature interpretation and useful failed routes | Correct affected reasoning while retaining why an earlier route was plausible and what remains reusable |
| Experimental evidence and historical observations | Inputs, original outputs, analysis, observation times and provenance | Preserve original evidence; identify which later interpretation or calculation supersedes its use |
| Demonstrated methods | A transferable procedure, its applicability and meaningful checks | Refine the existing method when evidence changes its limits; keep unvalidated proposals distinguishable |

These are semantic roles, not four mandatory directories, document types or a
new claim database. A small topic can keep several roles in one file; a large
topic can use linked notes. Give each maintained assertion or derivation one
primary home, with enough context at its uses to preserve its meaning. Avoid
separate status, handoff and overview files that repeat the same scientific
account and then require manual synchronization.

The main note should offer a brief orientation and then the substantive argument.
Its opening should let a reader identify the current answer and its limits
without reconstructing successive runs. Detailed history remains discoverable
through relevant links. Brevity is not a fixed line limit: removing a decisive
assumption or the only complete derivation would make memory worse. For ordinary
recall, select evidence by the question; for a substantive revision, recover the
complete relevant argument. Repeatedly reading every linked artifact cannot
compensate for an incoherent primary account.

Make the responsibilities of memory and writing meet at the actual revision.
Memory identifies what changed, its authoritative location and affected uses;
writing integrates that change without losing conditions, reasoning or history.
Saving a new supporting note and appending its link is insufficient when an old
conclusion remains active. Conversely, new detail that leaves the main argument
unchanged should not trigger a rewrite of every summary. If the changed claim is
used elsewhere, revise those maintained uses within scope; original run reports
remain historical evidence with an explicit correction or successor where needed.

For example, if two symmetry-related sites were originally compared in different
local frames, preserve the original numerical outputs and explain why that
comparison was insufficient. The current argument should identify the corrected
comparison and whether its results actually exist. A repaired implementation
must not make old outputs appear to have been recomputed. Similarly, temporarily
treating a numerical limit as reliable is a working assumption, not a validation
result; that qualification must survive a shorter summary and later retrieval.

Time-sensitive observations need equally clear scope: a job reported as running
at the last check is a dated observation, not a permanently current state. A
failure can cease to block today's route while remaining unresolved. Writing
should distinguish those meanings instead of collecting all pending issues into
an ever-growing list of prerequisites.

The proposed improvement is a small worked revision showing these choices in
the existing memory and writing guidance. A reminder hook may prompt the review,
but cannot decide which interpretation is current or perform the synthesis by
itself. This feedback does not propose a background writer, mandatory metadata,
automatic commits, per-turn forms or another parallel summary layer.

### Concrete changes to prioritize

1. **Shorten the ordinary research path.** Establish the current argument, do the
   scientific work, then retain a meaningful change at a natural pause. Reuse a
   complete, known-current reading during continuous work. Load specialist
   instructions and older derivations only when relevant; do not reread every
   Skill or historical session after each follow-up. Simplify the obligations
   presented to the model, not just the implementation behind them.

2. **Retrieve reasons, not just the latest status.** For a status question, use the
   current account. For "why this direction?" or a suspected repeated calculation,
   follow the specific earlier derivation and route decision. For a disputed
   inference, inspect its primary evidence. Retrieval locates recorded reasoning;
   it does not independently verify it. A historical `next_action` is context to
   reassess, not today's instruction or authorization.

3. **Make scientific dependencies explicit in ordinary prose.** Distinguish a
   literature input, demonstrated result, conditional construction, conjecture
   and physical identification. State what a result depends on and what remains
   necessary for the target conclusion. A local algebra check, an example and
   a physical anomaly match are different evidence. A failure of one ansatz is
   not a general no-go theorem. No claim database, confidence score or compulsory
   claim cards are needed to express these distinctions.

4. **Record changes in understanding, not every action.** Retain consequential
   results, corrected premises, informative failures, substantial route choices
   and fragile unfinished insights. A direction change can matter before a result
   exists. Routine algebra stays in its derivation; an unchanged explanation or
   status answer needs no write. Exploration through analogies and toy models
   remains legitimate even before a decisive test is known. A sharper question
   or a precise obstruction can be progress without a successful construction.

5. **Integrate implications and remove obsolete next steps.** When evidence changes
   the argument, revise the affected opening, reasoning and conclusion together.
   A new link does not repair stale claims. Retain why a consequential reversal
   occurred and which earlier results survive. Keep requested lectures and papers
   as distinct deliverables, not extra copies to synchronize after every small
   calculation. Under restricted authority, identify pending integration rather
   than editing outside scope.

These are improvement priorities, not a five-step form to complete on every turn.
First remove duplication and observe whether the existing instructions are
actually followed. For a recurring demonstrated failure, make the smallest
relevant clarification. Distill a Skill only from a useful reusable procedure;
keep topic conclusions and conceptual explanations in the research notes.
Do not add mandatory gates, automatic cross-thread writers or compulsory goal
resets. An optional reminder must allow no-write outcomes and must not repeatedly
extend a turn until a document changes.

### How to judge whether the changes help

Use a small, separately authorized continuation task in a fresh session, not a
new evaluation framework. Can another researcher recover the supported claim,
its assumptions and full derivation; explain why an earlier approach was limited;
reuse its surviving result; and identify the actual unresolved inference?
Then introduce a consequential correction and another handoff. The current
argument should change without losing the reason for the correction. Include an
unchanged question requiring no write and an unrecorded historical reason that
must be acknowledged as unknown.

For the memory/writing revision specifically, inspect whether a fresh reader
can distinguish the superseded comparison from the current one, retrieve the
full surviving derivation, preserve a provisional assumption as provisional,
and recognize that a last-observed job state may be stale. Exercise both a
supporting-only result and a change to the central claim: only the latter should
require changing the main conclusion. Measure the need for user corrections and
repeated recovery, alongside maintenance effort. Counting saved files or merely
shortening the main note cannot establish success.

Compare with ordinary well-maintained notes containing the same sources,
derivations and failed routes, under comparable model and task budgets. Removing
all persistent evidence from the baseline would test memory versus no memory,
not AITP's added value. Observe recovery errors, unsupported upgrades of claims,
unnecessary repeated work, user reminders, recovery and maintenance effort,
and progress toward a scientifically relevant result or obstruction. Record count,
shorter context, valid Markdown and hook activation are not research outcomes.

This feedback performs no such comparison and claims no measured improvement.
If AITP helps preserve the argument while reducing recovery and maintenance work,
keep that help. If ordinary notes do as well with less interruption, simplify or
omit the additional protocol while retaining the research history.

Only this feedback section is revised: no Skills, hooks, goals, physics notes or
manuscripts are changed, and no new behavior is claimed to be implemented.

## Long-running goals must converge on the physical question

Reported on 2026-09-20 against source checkout
91f4fc6c0bb16fd6ad3b3182c7d5f9683210844a, with pre-existing working-tree
changes. This is a sanitized account of an observed research interaction and
the agent's review. It is not an independent evaluation, a causal attribution
to AITP, or a validated improvement. Private research results, numerical values,
workstation paths and conversation transcripts are omitted.

### Observed failure: a succession of prerequisites displaced the objective

The researcher set a broad goal about the physical low-energy theories of
defects, their operators and junctions, and the composition and anomaly tests
of the resulting networks. The intended argument concerned a family of
theories; particular low-rank examples were supporting tests.

The agent pursued a compactified effective-theory example, then numerical
backgrounds, fluctuations, charged saddles, exterior matching and increasingly
elaborate vacuum-boundary diagnostics. Some calculations supplied useful
evidence within that model. Each also exposed another local technical question.
The agent repeatedly promoted the next technical question into a prerequisite
for solving the original physical problem, without establishing that dependency.

The missing implication was decisive: even a perfectly converged effective-theory
calculation did not identify the microscopic probe with an internal defect
operator, establish the required defect continuation, or determine the physical
junction maps. Improving a regulator cannot supply an unspecified dynamical
identification. Nevertheless, the work continued to optimize the auxiliary
problem and expanded the research note and manuscripts around it.

The agent kept saying that the full goal was unresolved. It did not falsely
declare completion, but that was insufficient: honest incompleteness coexisted
with persistent route drift. When asked which research stage it had reached,
the agent mapped the numerical work back onto a broad stage label without
explaining how little the decisive physical implication had advanced.
The researcher had to challenge the choice of numerical work and point out
the deviation. The subsequent recovery stopped expanding that branch,
preserved its limited evidence and restored the analytical physical question
as the current continuation.

This is not evidence that numerical methods are generally inappropriate.
The same failure could occur through indefinite algebra in an assumed category,
ever finer literature summaries, or repeated manuscript polishing. The problem
is replacing the requested physical conclusion with work that is easier to
execute and verify locally.

### Existing guidance and the gap exposed by sustained continuation

The [research Skill](../plugins/aitp/skills/aitp-research/SKILL.md)
already requires a discriminating physical question, explicit assumptions,
agreement on consequential route choices, and stopping or reconsideration
criteria. It also says that a small residual does not settle the physics.
The [memory Skill](../plugins/aitp/skills/aitp-memory/SKILL.md)
requires recovering the central argument and its most consequential gap.
These instructions were relevant; their existence did not prevent this case.
The agent remains responsible for its scientific choices. The case does not
establish failed Skill activation or show that wording alone caused the drift.

What needs stronger guidance is cumulative drift under a long-running host goal.
Individually routine steps can collectively change the route. A sequence of
successful diagnostics can still leave the target inference untouched.
Retaining the full objective in every continuation and refusing premature
completion do not by themselves tell the agent when to abandon an increasingly
expensive prerequisite chain.

AITP can guide this judgment without owning the host's goal machinery.
The host supplies persistence; the research Skill should help decide whether
the next action still serves the physical objective. An unbounded goal is not
a reason to pursue every prerequisite indefinitely, and broad authorization to
solve a topic does not establish the scientific merit of a particular route.

### Proposed guidance: connect the next result to a physical conclusion

Before a sustained branch, and again when its prerequisites proliferate,
work backward from the desired physical conclusion. Identify the evidence
that would support it, the observable or derivation the branch can actually
produce, and the assumptions connecting the two. Locate the first unsupported
implication. Use ordinary prose in the existing argument; no separate claim
registry or compulsory per-turn form is needed.

Ask a counterfactual that this case needed much earlier:

> If this calculation succeeded perfectly, what would we then be entitled to
> conclude about the original physical question? Which essential inference
> would remain missing, and why would the next refinement change it?

There need not be a complete proof route before useful exploration begins.
A toy model can reveal a mechanism, eliminate a plausible explanation or sharpen
the question. Name that limited purpose and the observation that would justify
continuing or returning to the main argument. Do not silently upgrade an
exploratory example into a necessary route to the full theory.

The practical distinctions are:

- **A relevant controlled approximation.** The target observable and its physical
  interpretation are established, and regulator error prevents the needed
  discrimination. Numerical improvement directly serves the question.
- **A conceptual or dynamical gap.** The operator identification, protection,
  continuation or effective description is not justified. Additional accuracy
  in the auxiliary model does not establish the missing implication.
- **A useful but completed diagnostic.** The branch has exposed its intended
  mechanism or limitation. Retain it and return to the main question instead of
  automatically repairing every new technical problem it reveals.
- **An unresolved exploratory route.** The connection is still a hypothesis.
  State what evidence could make it useful and reassess when that evidence
  fails to appear; neither force a success claim nor invent a general no-go.

At a natural reconsideration point, compare what is now known about the physical
question with what was known when the branch began. New artifacts, passing
tests, a smaller residual and a longer manuscript are not substitutes for that
comparison. A sharper obstruction can be scientific progress, but finding one
does not make repairing its entire numerical setting the next required task.
Repeated methodological progress without a changed physical judgment should
trigger reconsideration even when every individual calculation succeeds.

Retain the broad goal while choosing a bounded, discriminating next question.
Do not replace the original objective with that smaller question or mark the
whole goal complete when the local question is answered. Equally, do not turn
the incomplete broad goal into a standing instruction to keep working on the
most recently active branch. Reuse existing route agreement; discuss a material
change with the researcher before making it the new programme. This is a check
on consequential choices, not a request for approval of every routine step.

Status reports should state which physical inference moved, what remains
conditional, and whether the current work is a supporting diagnostic. A stage
number or a list of successful checks must not conceal that the target
identification remains unchanged. When the user questions the route, reassess
the dependency itself rather than defending the branch through its technical
sophistication or sunk cost.

### A small proposed addition to the research Skill

Place concise guidance alongside the existing choice of a discriminating
calculation, rather than adding another workflow or mandatory goal mechanism:

> During sustained goal work, keep the next action tied to the physical
> conclusion it could change. When a branch generates further prerequisites,
> ask what perfect success would establish and identify the first missing
> implication back to the main question. Numerical convergence, candidate
> algebra and completed artifacts can be useful without advancing that
> implication. If the next refinement cannot address it, retain the branch's
> result and limitation, then return to the unresolved physical inference or
> discuss a material route change. Explore with a stated purpose and a
> reconsideration criterion; do not require a fully known proof route.
> Persistence preserves the original objective, not the currently active method.

Memory guidance may point to this decision when preserving a continuation:
record why the next step advances the argument, not merely which unfinished
calculation comes next. It should not automatically turn every newly discovered
technical limitation into the main note's priority.

This proposal requires neither a numerical-method ban nor an assumption that
all physical questions admit purely analytical solutions. It adds no fixed
iteration quota, automatic goal reset, background watcher, ledger or repeated
permission prompt. Strong research judgment remains necessary.

### How to check a future implementation

Use a small fresh-session continuation with an ordinary-note baseline and
comparable resources. Inspect the action actually chosen, not whether the agent
can repeat the new wording. Include examples where continuing computation is
correct, so that avoiding numerical work cannot trivially pass.

| Situation | Behavior that would support improvement |
| --- | --- |
| A defect calculation lacks a justified microscopic operator map; the next refinement only reduces its mesh error | Identify the missing map before launching another refinement, retain the diagnostic and work on the physical inference. |
| A calibrated physical observable cannot distinguish two hypotheses at the current numerical uncertainty | Continue the relevant convergence calculation under existing authorization and state what discrimination it enables. |
| A candidate-theory algebra calculation is complete but physical identification is absent | Reuse the conditional algebra and address the identification; do not generate more algebra as a proxy for it. |
| A toy model is being explored for a stated mechanism | Allow the exploration and reassess at its declared evidential boundary, without demanding a complete solution in advance. |
| Several individually reasonable steps have cumulatively changed the research route | Detect the cumulative change before further expansion and return to the existing agreement or discuss the material change. |
| The evidence establishes an obstruction but leaves the larger goal unresolved | Retain the precise obstruction, identify what could resolve it, and report the scope honestly without declaring the whole topic solved. |
| The researcher asks for status or challenges the route | Explain the actual physical advance and inspect the disputed dependency without hiding behind stage labels or artifact counts. |

Observe unnecessary refinements, time to a physically relevant inference or
obstruction, user interventions needed to correct the route, and whether useful
authorized work is mistakenly blocked. A packaging check or a same-agent
walkthrough does not establish improved scientific convergence.

This change records feedback only. No Skill behavior, host-goal integration or
independent-session test is implemented here, and no improvement is claimed as
validated. Existing feedback and unrelated working-tree changes are preserved.

## Formal-theory memory must make the research contribution reconstructible

Reported on 2026-09-22 against source checkout
`91f4fc6c0bb16fd6ad3b3182c7d5f9683210844a`, with existing local changes.
This extends the earlier memory/writing architecture and long-running-goal
feedback with a manuscript-reading failure. It is a sanitized account of the
researcher's interaction and the same agent's document review, not an independent
reader study or a demonstrated improvement. Unpublished physics, private paths
and conversation transcripts are omitted.

### What the document review exposed

The researcher requested a careful consolidation of a theoretical-physics main
note, graduate lecture and research article. The agent reorganized the argument,
retained detailed derivations, moved lengthy auxiliary calculations into
appendices, added a chapter on the unresolved physical matching, and rebuilt
the PDFs. The article contained the research question, useful partial results,
conditional constructions and explicit statements of incompleteness. Its
references and layout checks passed. The title was subsequently revised to
identify the physical objects and relevant symmetry more precisely and concisely.

The researcher then asked whether the PDF actually explained our question and
what we had done. The agent's review found those elements in the abstract,
introduction, several technical chapters and discussion, but found that their
relationship still required the reader to assemble the account across sections.
In particular, the overall physical objective, the immediate operator-matching
question and the contribution of each established result were not sufficiently
concentrated in the opening argument. The researcher identified this as feedback
on both formal-theory writing and memory data architecture.

The observation is narrower than saying the information was absent or every
derivation was unclear. It also differs from losing an unrecorded branch:
retention and local qualifications were present, yet the research contribution
was harder to reconstruct than it should have been. A successful build, a shorter
main note, complete links and an accurate title did not establish that the
documents communicated the scientific state. Reporting only those checks made
the editorial completion claim too strong.

### Existing instructions address the goal but did not secure the outcome

The [main-note guidance](../plugins/aitp/skills/aitp-writing/references/research-note.md)
already asks whether a reader can explain the question, supported answer,
decisive reasoning and remaining gap. The
[formal-theory guidance](../plugins/aitp/skills/aitp-writing/references/formal-theory.md)
already distinguishes an exact conditional calculation from physical
identification. The [memory Skill](../plugins/aitp/skills/aitp-memory/SKILL.md)
already requires integrating changes into the whole argument. These are relevant
instructions; this case does not establish that they failed to activate.

The agent remains responsible for its synthesis and overbroad completion report.
However, attributing the difficulty only to instruction compliance would leave
the researcher's design criticism unanswered. A design that stores results and
their supporting files, but leaves the relationships between results implicit,
makes every later synthesis depend on reconstructing those relationships again.
The proposed improvement should address how the argument is maintained and used,
rather than merely add another reminder to write clearly.

### Preserve the relationships that make a formal result usable

The unit of retention should include the question a result answers, the precise
statement and assumptions, its source or derivation, and its implication for the
larger physical argument. Give that reasoning one primary home. At a use site,
retain enough of the statement and decisive qualification to explain why the
link matters. This is a semantic responsibility for ordinary prose and links,
not a mandatory record format, claim database or graph service.

Two distinctions are especially important:

- **Provenance and logical status are separate.** A literature theorem, a
  rederivation, a specialization, and a construction developed in this project
  have different provenance. Any of them may be exact under assumptions,
  perturbative, conjectural or conditional on a physical identification.
  Describing work done in the project does not establish publication novelty.
- **Support is not always implication.** A calculation may prove a lemma,
  discriminate between candidates, illustrate a mechanism or merely suggest a
  route. A link from an auxiliary model to the physical target must explain
  which relation holds and which bridge is still missing. Exactness inside a
  candidate theory does not turn that candidate into an identified physical
  theory.

For formal work, the decisive assumptions may be a map's domain and codomain,
the structure it preserves, a spin or boundary choice, a nonzero projection,
or the order of limits. Those conditions must survive compression, reuse in a
lecture, and presentation in an article. A local qualification near an equation
does not repair an unconditional overview elsewhere.

The main account should therefore make the following relationships readable:
the broad physical question motivates a discriminating subquestion; a derivation
establishes a stated conclusion under stated assumptions; that conclusion changes
one part of the current answer while leaving a specific inference unresolved.
Independent branches can converge on the same inference. Exploratory work need
not have a complete route to the final answer before it begins; retain its
limited purpose and what would make its result relevant. Do not impose a linear
proof plan on non-linear research.

### Give research memory, lectures and articles distinct responsibilities

The documents need a common scientific meaning, but not identical paragraphs or
automatic synchronization after every calculation.

| Existing document role | What its reader should recover | Appropriate update |
| --- | --- | --- |
| Main research note | Overall question, present answer, important dependencies, reasons earlier routes were limited, and the next unresolved inference | Integrate changes to the live argument; retain links to complete reasoning |
| Supporting derivation | Definitions, assumptions, proof or calculation, imported inputs, failure scope and implication for the originating question | Maintain the complete argument and its connection to the main note |
| Graduate lecture | Why the question arises and how the reader can follow representative reasoning from declared prerequisites | Explain missing conceptual transitions; distinguish reviewed material from project-specific work |
| Research article | A coherent supported contribution, its relation to prior work, decisive reasoning and remaining limitation | Select and integrate the relevant argument when manuscript work is authorized |
| Historical evidence or earlier edition | What was actually calculated or written in its original setting | Preserve it and make supersession clear in the maintained account |

These are roles that may share existing files, not a required new directory tree.
A separate progress dashboard or contribution registry would duplicate the
scientific account. When a premise changes, update the affected maintained
claims and their uses within scope. Rebuild a requested PDF after its source
changes; preserve earlier editions. Do not make every research update require
rewriting a lecture and article. A document's current-build designation identifies
its source/output pair; it does not imply that it contains all later research.

### Make the opening carry the synthesis, not just a section itinerary

The title should identify the objects and relevant physical setting without
becoming a list of methods. The abstract and opening introduction should let the
intended reader state the physical question, what this work establishes, why it
matters, and what inference remains open. Put imported results and project work
in their proper relationship there, then develop the evidence in the body.
For an exploratory paper, the contribution may be a counterexample, an
obstruction or a conditional construction rather than a completed theory.

A generic before-and-after example illustrates the needed synthesis:

> An insufficient overview says that we reviewed candidate theories, checked an
> algebra, studied a toy model and organized the supporting calculations. The
> section list names activities but does not explain the answer they support.
>
> A useful overview says that we seek a physical operator identification; an
> imported classification constrains the candidates; a counterexample developed
> here shows that the specified protected data cannot determine the required
> nonzero map; and an auxiliary calculation establishes a local coefficient under
> its own assumptions. The remaining task is the connecting physical matrix
> element and its controlled relation to the target theory. The existing
> calculations narrow that task without completing it.

This is an illustrative writing pattern, not a claim about a particular model or
a fixed paragraph template. Detailed mathematics remains necessary. A contribution
summary cannot replace a proof, and shortening the document cannot justify
discarding the only full derivation or the reason a previous approach failed.

### Proposed changes and a meaningful way to assess them

Revise the existing memory and writing guidance together around one worked formal
example: locate the primary statements and their dependencies; revise an affected
premise; retain the surviving conditional result; and write the resulting main
account and requested article opening. Add the reader check to the existing
manuscript review guidance. Prefer that concrete demonstration and removal of
duplicate obligations to another long general instruction. This feedback does
not implement those changes.

Assess the proposal with a small fresh-reader or fresh-session task using the
documents alone, without the originating chat or the author's oral explanation:

| Situation | Evidence that the design helps |
| --- | --- |
| Read the article's opening | Recover the overall problem, supported contribution, imported inputs, decisive condition and unresolved inference without assembling a section-by-section inventory |
| Follow one substantive result | Locate its complete derivation and explain how it changes the answer to the main question |
| Read an exact calculation in a candidate theory | Retain the unproved physical identification instead of promoting the calculation to a result about the microscopic theory |
| A premise is corrected or a route fails | Revise the affected live conclusions while preserving valid lemmas and the reason for the earlier route |
| The detailed calculation changes no main conclusion | Update only the relevant supporting material, without unnecessary document-wide synchronization |
| Compare the lecture and article | Recover consistent claims and limits while retaining the lecture's declared prerequisites and the article's contribution focus |

Compare against ordinary well-maintained Markdown and TeX notes with the same
evidence. Observe mistaken claims of completion or novelty, missed dependencies,
reader reconstruction effort, lost useful detail and maintenance burden. Separate
these checks from citation resolution, PDF compilation and visual inspection.
The present same-agent review is evidence of the reported shortcoming, not an
independent validation of this proposed architecture.

This entry records feedback only. It changes no Skills, schemas, hooks, host
goals or scientific manuscripts, and it claims no measured improvement. Existing
feedback and unrelated local changes must remain intact.

## Practical usefulness: reduce recovery effort and researcher correction

Reported on 2026-10-03 as a follow-up to the computational memory and writing
feedback above. This is a qualitative review with the researcher, not an
independent trial or a measurement of time saved. Examples are sanitized;
private research files, numerical results and conversations remain outside
this tree.

### What helps, and what remains difficult

AITP is useful for long-running research when it preserves settled model choices,
reasons for rejecting earlier routes, and the connection between conclusions and
evidence. In an orbital-resolved screening project, those records helped recover
the research context. The researcher nevertheless had to ask repeatedly which
implementation and results currently applied and what the checks established.
Saving the information did not make the current understanding easy to recover.

A large main note can contain accurate details while leaving the reader to
assemble the live answer across older comparisons, corrections and supporting
reports. The problem is the effort needed to recover their relationships, not
file length alone. Shortening a note must preserve decisive reasoning and the
reasons that useful earlier routes failed.

The current [memory guidance](../plugins/aitp/skills/aitp-memory/SKILL.md) already
requires integrating consequential changes, replacing stale claims and avoiding
unchanged writes. This review does not establish an activation failure or prove
that AITP caused the observed difficulties. The agent remains responsible for
its execution. The absence of a background writer explains how maintenance
works; it does not excuse an omitted update within existing authorization.

### Focus the next improvement on observed use

- Make the existing opening and conclusion carry the current question, operative
  model, supported answer and decisive remaining uncertainty. Keep detailed
  calculations linked from their relevant claims, with one primary home for each
  argument. Do not create a parallel status dashboard.
- Use selective recovery for ordinary questions and reuse known-current context.
  Retain whole-argument reading before substantive revision; do not turn it into
  a compulsory full read on every turn.
- Before another expensive refinement, explain what a successful result would
  establish. Distinguish a numerical uncertainty from a mismatch in physical
  models that more precision cannot resolve. Recording more tests cannot replace
  that missing inference.
- Demonstrate these behaviors with a small concrete example and a fresh-session
  check before adding more general instructions. The earlier optional reminder
  proposal remains a candidate, not a demonstrated remedy or permission for
  automatic cross-thread edits.

### Evidence that would justify calling it easier to use

Compare against ordinary, well-maintained Markdown notes with the same evidence
and task scope. A returning reader should recover the current answer, an important
qualification, a rejected route and the next discriminating check without the
originating conversation. A corrected premise should change affected live claims
while preserving valid earlier results. An unchanged status question should add
neither a memory write nor another recording ritual. Restricted read-only work
should identify a consequential pending integration without editing outside scope.

Observe recovery effort, researcher corrections, repeated rejected routes,
unsupported completion claims and maintenance cost. File counts, successful
packaging checks and the presence of instructions do not measure these outcomes.
Current experience supports retaining AITP as guidance, but does not quantify
saved wall time, tokens or computing allocation.

This entry records feedback only. It implements no Skill changes, reminder,
runtime service or evaluation, and leaves existing feedback and unrelated work
intact.

## Computational validation: completion, transfer and practical benefit

This feedback extends the
[practical-usefulness review](#practical-usefulness-reduce-recovery-effort-and-researcher-correction)
with observations from a computational validation campaign and a read-only
review of the current Skills and benchmark documentation. It is a qualitative
assessment by the same assistant, not an independent evaluation or a measured
causal benefit of AITP. Examples are sanitized; private materials, numerical
results, machine paths and conversation records remain outside this tree.

### What the experience supports

The campaign retained implementation boundaries, failed controls and the
difference between intermediate operators and final predicted energies.
These records made it possible to explain which routes had been exercised,
which agreements depended on a numerical setting, and which questions were
still unresolved. This supports keeping linked research memory and explicit
acceptance conditions. It does not separate the contribution of AITP from
model capability, ordinary research practice or the researcher's corrections.

The closeout already disclosed strict failures and conditional passes, and
the researcher subsequently asked what problems remained. This is not evidence
that the closeout claimed universal success. It does expose a reporting risk:
a host's completed label cannot express the distinction between completing a
requested investigation and obtaining an accepted scientific result. A test can
be resolved by a reproduced, localized failure. An implementation request can
still be incomplete if a required supported route remains unavailable.

One numerical screening issue was explicitly retained as known and deferred.
That decision should survive later recovery without becoming an automatic
repair priority. Conditional passing controls remain useful, while the deferred
default-setting failure stays visible.

### Improvements to prioritize

| Priority | Concrete change or check |
| --- | --- |
| Make completion conditions visible | In the existing closeout and main argument, distinguish experiments completed, numerical gates passed, defects repaired, unsupported routes and physical acceptance. Attach the condition to each passing claim; define completion from the actual request rather than from a count of finished tests. |
| Reduce recovery and maintenance effort | Apply the existing selective-reading and context-reuse rules to ordinary questions and narrow annotations. Preserve whole-argument reading for substantive revisions. Move historical detail to a supporting note when it has an independent role, retaining the implication and reasons for changed conclusions in the main account. Shortening alone is not success. |
| Test domain Skills through independent use | Give a fresh session a different small instance, the local method and its evidence, without the originating chat or evaluator hints. Check version selection, input compatibility, actual execution of the requested route, unsupported-case detection and acceptance. Valid frontmatter and links do not establish this transfer. |
| Evaluate the choice of the next calculation | Ask for competing explanations and the observations that would distinguish them before expanding a scan. Choose a small informative control. A finite-input symmetry residual, a screening approximation and an incorrect transformation require different checks; numerical refinement need not resolve all three. |
| Measure added benefit against ordinary notes | Compare the same task, persistent evidence, model, tools and budget with and without AITP guidance. Report correctness, researcher corrections, repeated failures, time to verified progress, reading and maintenance effort, and compute/model costs separately. Preserve failed and timed-out trials. |

Much of this behavior is already required by
[memory](../plugins/aitp/skills/aitp-memory/SKILL.md),
[research](../plugins/aitp/skills/aitp-research/SKILL.md) and
[distillation](../plugins/aitp/skills/aitp-distill/SKILL.md).
An unnecessary full reread, an unsupported inference or a repeated request for
settled information remains the agent's execution responsibility. This review
does not establish an activation failure or attribute those choices to a
specific sentence in a Skill. First check whether the existing rule is followed;
make a narrow clarification only where an observed ambiguity warrants it.

### Evidence needed before claiming improvement

The [general regression suite](../benchmarks/general-v0.1/README.md) reports
twelve completed development cases, each scored 2/2, and a fresh continuation.
Its documentation also explicitly states that there is no matched ordinary-note
or old-versus-new baseline. These are useful behavior checks, not evidence of
causal superiority, general physical accuracy or original discovery.
[Validation records](validation.md) distinguish authored walkthroughs,
fresh-session observations and document-consistency checks; retain those
distinctions when discussing future results.

A small continuation comparison could test the priorities without adding a
runtime or another memory format. Give new sessions the same retained evidence
and inspect whether they:

- recover a mixed pass/fail campaign and its conditions without upgrading it to
  universal implementation correctness;
- preserve an explicitly deferred issue while pursuing the requested remaining
  question;
- use a method on a changed instance, including recognizing a genuinely
  unsupported input instead of silently falling back;
- make a narrow authorized annotation without redundant recovery, while still
  reading the full argument before a consequential premise revision;
- select a control that distinguishes candidate mechanisms, and recognize when
  further refinement would leave the essential inference untouched.

Use a baseline with equally complete ordinary notes; removing the evidence
would compare memory with no memory rather than isolate AITP. Keep host
instructions, injected memory, actual Skill versions and resource conditions
observable, and use held-out instances after tuning. Score the action and
resulting artifacts, not the agent's ability to repeat the instructions.

This section records feedback only. It implements no Skill change, evaluation
or research action, and claims no validated improvement. Existing feedback and
unrelated working-tree changes are preserved.

## Choose the physical diagnostic before expanding the calculation

Reported on 2026-10-04 from a researcher-agent exchange about out-of-time-order
correlators (OTOCs) and quantum chaos. This extends the feedback on
[long-running research goals](#long-running-goals-must-converge-on-the-physical-question)
with a case about choosing an observable and its time window. It is a qualitative
review of the interaction and current source guidance, not an independent trial
or evidence that AITP caused the observed choices. The account is sanitized:
private parameter grids, numerical results, run identities, machine paths and
conversation transcripts are omitted.

### The next calculation was specified before its interpretation was settled

The researcher wanted to understand what existing OTOC curves could say about
chaos in a spin-chain family. The agent distinguished spatial spreading from a
chaos diagnosis, but then elevated post-growth temporal fluctuations into the
next substantial calculation. It proposed a much longer time window before
explaining why this diagnostic should take priority in the present model over
analysis of the already available growth and propagation data.

The researcher questioned that choice, pointing to literature focused on early
growth. The agent then returned to a closer model comparison, explained the
difference between the strict short-time expansion and the pre-saturation front,
and discussed which parameters could actually be inferred. The proposed
longer-time job had not been submitted when this correction was discussed.
This case therefore shows a premature research recommendation, not demonstrated
wasted compute or an invalid numerical result.

The conversation also included repeated requests to see the project's figures.
Figures were subsequently linked and explained. This supports a need to make
the physical evidence easier to reach and interpret; it does not establish that
the figures had never existed or that every status report was misleading.

The late-time proposal was not intrinsically inappropriate. Its priority and
connection to the target inference were insufficiently justified. Likewise,
the correction does not establish that early growth is always preferable.
For a diagnostic to be useful, the agent must explain what alternative physical
mechanisms could produce the same observation and which comparison would
distinguish them.

### Relevant rules already exist

The current [research Skill](../plugins/aitp/skills/aitp-research/SKILL.md#agree-on-consequential-research-choices)
asks what perfect success of a calculation would establish, calls for a small
informative case before an expensive expansion, and separates physical validity
from numerical convergence. Its
[objection guidance](../plugins/aitp/skills/aitp-research/SKILL.md#reason-and-respond-to-objections)
requires examining the disputed inference rather than agreeing merely to end a
disagreement. The [literature guidance](../plugins/aitp/skills/aitp-research/references/literature.md#read-for-the-claim-that-matters)
requires checking source assumptions and separating published results from their
application to the current topic. The
[learning Skill](../plugins/aitp/skills/aitp-human-learning/SKILL.md#explain-then-locate-the-remaining-difficulty)
requires resolving a conceptual obstacle before building on it.

Repeating these principles in another long checklist would not by itself address
the case. The execution failure is observable; the cause is not isolated. A useful
design change would make their application concrete at the decision where a
plausible literature method becomes a proposed research programme. AITP guidance,
model capability, host instructions and researcher intervention remain distinct
possible influences.

### Focused improvements to test

1. **Explain the diagnostic before specifying a costly extension.** In the
   calculation proposal, state what is measured, which competing explanations
   remain, and how the proposed result could distinguish them. A longer time
   window or larger size should remove an identified uncertainty. Bounded
   exploration is also legitimate when its purpose is to discover whether a
   useful diagnostic exists; do not demand a complete solution in advance.

2. **Use applicability to rank literature methods.** Compare the features that
   determine transfer: Hamiltonian, symmetries, ensemble, operator normalization,
   available limits and observation window. Explain why one method is preferred
   and what remains an analogy. A paper from a different model can supply the
   best method, but a shared keyword or an accessible implementation is not
   sufficient justification. Put a short worked comparison in the existing
   literature guidance if fresh-session use shows that clarification is needed.

3. **Turn limitations into discriminating questions.** Saying that an observable
   does not prove chaos is a useful boundary, not a complete continuation. In a
   generic OTOC example, altered coupling strength, interaction range and
   integrable operator propagation are possible alternative explanations for
   changed growth. Select a control or derivation that addresses one such
   ambiguity, or state why the observable cannot settle the intended question.
   More precision must not silently replace the missing physical distinction.

4. **Make corrections change the reasoning and the next action.** After a
   challenge, identify the premise that survives, changes or fails, retain the
   useful part of the earlier route, and explain the new priority. Test both
   valid and mistaken researcher objections. Agreement with the most recent
   message is not evidence of good judgment; neither is defending a route only
   because work has already been invested in it.

5. **Present a usable physical result early.** Give the researcher an accessible
   figure, derivation, counterexample or bounded negative result, with its
   interpretation and remaining ambiguity. Coverage counts, job states and
   numerical controls support that result but should not displace it. Preserve
   the distinction between data produced, numerical reliability and the physical
   conclusion supported. This requires no additional dashboard or report type.

6. **Respect a change from execution to understanding.** When the researcher
   asks for a derivation of the premise behind a proposed calculation, resolve
   that premise before launching new work that depends on it. Continue unrelated
   authorized work when appropriate; a conceptual question does not itself
   authorize canceling existing jobs. Resume within the existing agreement when
   the issue is resolved, without asking again for settled permissions. Apply
   current conversation boundaries to any durable edits.

### Evaluate decisions, not instruction recitation

Use small, generic continuations compatible with the existing
[human-interaction cases](../benchmarks/human-interaction-v0.1/README.md).
These are proposed checks; no new benchmark or independent session is executed
by this feedback change.

| Situation | Behavior that would support improvement |
| --- | --- |
| Existing early-time data and a request to diagnose chaos | Explain what the data can distinguish, compare plausible diagnostics, and justify any new time window before expanding the calculation. |
| A proposed late-time measurement has a clear discriminating role | Retain and pursue that route under existing authorization; do not pass by always rejecting long-time work. |
| A method works in a related model with different assumptions | Identify the relevant differences and distinguish a justified transfer from a hypothesis requiring a control. |
| The researcher gives a valid objection, then a separate case with an invalid objection | Revise or defend the claim using its premises and evidence, and make the next action consistent with that reasoning. |
| The researcher asks to see the result or understand its derivation | Provide the relevant artifact or complete requested explanation before work that depends on the unresolved interpretation. |
| A numerical refinement would resolve a scientifically relevant uncertainty | Continue the refinement without inventing a new approval stage or replacing useful computation with indefinite discussion. |

Compare current guidance, a narrowly revised version and ordinary well-maintained
notes with the same task evidence, model, tools, authorization and resource budget.
Keep evaluator hints outside the tested session and use held-out instances after
tuning. Observe unsupported inferences, the relevance of the next action, time to
a usable scientific result, researcher corrections, unnecessary tool or compute
cost, and whether useful authorized work is wrongly delayed. A Skill read, a
passing link check or a larger number of saved artifacts does not establish these
outcomes.

This entry adds feedback only. It changes no Skills, runtime behavior, host goals
or research calculations, and makes no claim of validated improvement.
