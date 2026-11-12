# Plans and archived stage arguments

A plan explains why an agreed stage is worth doing and how it will answer its question.
The main note develops the current research judgment; its Current work owns each live
thread's frontier and next discriminating action. A stage account retains the actual
reasoning and evidence. Connect these roles without copying their changing contents.

## Keep stages with the question that owns them

For substantial staged work, use two working locations within the owning question:

```text
question/
  research.md
  plan/<stage>/plan.md          Design and sequence for an open stage
  archive/<earlier-stage>/
    plan.md                    Retired design, with outcome and closure reason
    result.md                  Argument and evidence, when owned by this stage
  subquestion/research.md       An independent branch, with its own stages as needed
```

The stage folder can contain a developing derivation or analysis alongside its plan.
When the stage closes, move the stage folder together to `archive/<stage>/`. This keeps
the design and what it actually established connected. Create only locations needed
for real work. A few routine actions can remain in Current work. Reuse established
equivalent layouts; this convention does not require moving historical evidence or
creating folders for every small question. The nearest suitable README maps the
chosen locations.

The plan links to the precise question or gap in `research.md`; the owning Current work
entry links to the plan and identifies its operative phase. An independent branch owns
its plans and arguments. Its parent links to the branch's contribution and limitation,
rather than collecting copies of its plans. Dependencies on siblings link to the exact
required claim and its status; a folder's location does not establish that dependency.

`result.md` is an explanatory account, not an additional report required for every stage.
If an existing derivation or report already owns the result, the retired plan's outcome
links to it; do not duplicate the account. Code, raw inputs/outputs and shared sources
retain their established homes, with links from the stage. Reusable explanations and
readings follow [shared knowledge](shared-knowledge.md), rather than being copied into
each stage. Directory placement does not establish scientific validity.

## Design the stage around an informative result

A substantial plan explains, in ordinary prose:

- **Question and contribution.** The bounded question, why it matters to the current
  main argument, what success could establish and which inference it would leave open.
- **Foundations and literature.** The theoretical mechanism and assumptions; the
  references actually used, with decisive passage locators; the method selected from
  them, why it applies here and any changes of model, convention or approximation.
  A bibliography alone does not explain the chosen route.
- **Inputs and dependencies.** Required claims, states, data or methods, their actual
  support and the missing understanding or open research input that could block use.
  Link foundational explanations or source readings where they are needed.
- **Expected information.** The intended deliverable and conditional prediction or
  competing possibilities. An exploratory stage can produce an obstruction or a better
  question without promising a particular physical answer.
- **Benchmarks and acceptance.** Independent references or discriminating tests, the
  reason they are suitable, and what makes the result trustworthy and sufficient for
  this stage. Distinguish implementation calibration from scientific inference. A
  credible negative result can complete a stage; agreement with an expected curve is
  not itself a calibration.
- **Route and decisions.** Phases with inputs and outputs, what can run in parallel,
  what depends on earlier results, and what the possible outcomes mean for continuing,
  changing route or stopping. Include consequential choices still needing resolution.
- **Cost and stopping conditions.** Expected resources for expensive work, refinement
  limits and evidence that would make further work uninformative. For calculations,
  justify the cases and fix appropriate tolerances before seeing results; an adaptive
  refinement rule can be specified in advance, as
  [computational work](../../aitp-research/references/computational-work.md#design-the-experiment-before-running-it)
  describes.

These are explanatory needs, not mandatory headings or a form for every operation.

## Review before running

Explain and review a substantial phased plan before execution, honouring any review the
researcher reserves for themselves or for another model. Check that each acceptance
condition can actually discriminate, and that complete success of the stage would advance
the main question. Judge another model's findings on the evidence, as
[aitp-verify](../../aitp-verify/SKILL.md#assess-another-models-review) describes.
Drafting a plan or receiving a favourable review does not authorize executing it; an
existing reviewed authorization carries across its phases.

## Keep the plan current, then retire it

Revise a plan when its objective, dependencies, acceptance conditions or agreed route
changes, explaining why and preserving consequential earlier decisions. Link each
phase's evidence and assess it against the intended question and acceptance or stopping
condition. Job states belong in run reports. Completing execution, accepting a finite
result and establishing the parent scientific claim remain distinct.

Keep a paused or blocked stage in `plan/`, with its pause point and resume conditions;
do not archive it merely because execution stopped. Partial accepted results enter the
main argument when consequential, while the unfinished stage remains open. A genuinely
independent completed substage may close separately, without declaring its parent done.

At a meaningful stage end, make the outcome explicit: completed with its qualified
answer, stopped with its reason, or superseded with its replacement when one exists.
Assess the result against the original expectation and benchmark. Retain the decisive
argument, evidence, limitations, useful failures and what the result teaches. A reliable
negative answer can be complete; retirement of a plan does not prove its hypothesis.

For a stage using the two-folder convention, move its design and stage-owned argument
together from `plan/<stage>/` to `archive/<stage>/`, without overwriting an existing
stage. Follow [checks and moves](checks-and-moves.md): preserve recoverability and repair
affected incoming and outgoing links, including main notes and knowledge references.
In another established layout, an explicit retirement with a reachable outcome serves
the same role. Preserve original run evidence and do not rewrite its historical status.

Integrate the outcome into the scientific account of the owning `research.md`: explain
what changed, under which conditions, with a link to the archived argument or its existing
owner. Remove its obsolete live-plan entry once integrated; an archived plan stays
reachable from the account or retained alternatives. Update parent uses only when the
branch contribution or limitation changes. The main note needs no exhaustive archive
inventory and no update for unchanged polls or routine intermediate files.

Archive does not mean immune to correction. Correct a qualified conclusion at its owner,
explain consequential changes and repair affected uses. Reopening the investigation can
start a new descriptive stage linked to the earlier outcome, preserving why it ended.
Link a follow-up plan only when that work is actually chosen. Archiving or drafting a
follow-up does not resume a paused investigation or authorize a calculation.
