# Write a supporting note around a useful question

Use this when a main argument needs a longer explanation, proof, source reading,
method or experiment. Locate related material first. One file can serve several
of the roles below; these are writing choices, not mandatory document types or
directories. A short explanation can stay in the main note.

| Role | What makes the note useful |
| --- | --- |
| Concept or background | A concrete reason to introduce the object, precise definition and conventions, a worked example, and limits of the analogy. |
| Literature reading | The question answered by the source, the inspected passage and locator, its hypotheses, convention translations and relevance to the topic. |
| Derivation or proof | The exact claim, assumptions, mechanism, justified steps, and the conditions under which the conclusion follows. |
| Method or implementation | The mathematical operation, representation and approximation, relevant code entrypoints, and a comparison that tests the operation. |
| Calculation and analysis | The question tested, settings actually used, inputs and output locations, defined observables and errors, results and interpretation. |
| Exploratory branch | Why the route was plausible, what was established, the obstruction or missing step, and the remaining conditions for continuation. |

Failures belong where their reasons are explained. A rejected ansatz does not
require a separate failure directory. Several attempts at the same question
can become one explanation. Independent research questions need their own main
accounts, even if they share code or background.

## Follow a side investigation

A converging main argument may depend on unfinished side work. When the
researcher chooses an independent branch, retain its question and agreement
before that context is lost. Use
[research's collaboration guidance](../../aitp-research/SKILL.md#agree-on-consequential-research-choices)
to settle its purpose, stage objective and approach before dependent work.
An agreed independent research branch needs its own folder and `research.md`
even before results exist; reuse a suitable existing branch folder and main note
when they already cover its question. A passing idea can remain a proposed direction
in the existing text without a new file or implied execution agreement. If work
has already begun without a clear agreement, preserve what was done honestly and
resolve the consequential choice before extending it.

Place the branch folder near the originating question or in an established topic
family, following the actual working location. Check relevant existing notes
before creating another; use
[nearby directories and note titles](../../aitp-memory/references/local-assets.md#browse-nearby-topics-and-shared-knowledge)
when their location or scope is unfamiliar. A short diagnostic within the
agreed work can remain a paragraph; a substantial derivation, experiment or
development effort serving the same question can use a supporting note. The
folder and `research.md` decision follows an agreed independent research question,
not the duration of work or a casual use of the word "branch". Do not create
empty note, code or results directories alongside it.

Explain in ordinary prose what prompted the branch, the agreed stage objective,
approach and scope, what evidence would settle it or call for reconsideration,
what has actually been established, and the next action needed to resume it.
Keep proposed alternatives and unresolved choices distinct from agreed work.
A short plan can live in this note; link a longer plan, derivation, implementation
account, scripts, inputs and results when they have their own useful homes.
These are content needs, not a required set of documents. Preserve useful
failures and the reasons for material changes of plan; replace obsolete next
steps while retaining the evidence. In the originating main note, link the
branch `research.md` beside the question it supports and explain whether it is
a prerequisite, alternative or related exploration. Do not invent that
relationship if it is undecided. The branch main note links back to the
relevant question.
For a dependency, say what result would let that work continue; an independent
spin-off can retain its origin without blocking the earlier question. These are
scientific connections, not mandatory fields or a second status report.
Explain the branch folder and any shared working locations in the nearest suitable
README; the README maps folders, while the two main notes explain the scientific
relationship. A branch-specific README is useful only if its own material locations
need explanation.

A branch may lead to another branch or be reused by several topics. Follow those
dependencies through links, not necessarily nested folders. For example, a
screening study can link a band calculation in an existing electronic-structure
topic, which links a reusable restart investigation near that code. Keep one
restart account and one code workspace; another material should reuse them.
Read the current branch and the relevant upstream context when switching work,
reusing context already understood. Read a main note's complete argument before
substantively changing it, not every ancestor or sibling for a local branch task.
Resume from the retained agreement and current request. A proposed next stage
is not automatically agreed; ordinary work inside a confirmed objective can
continue without another planning exchange.

When pausing, leave the unresolved step and useful assets findable. On completion
or a consequential failure, update the branch and the affected originating
claim or next step. Fixing restart support does not establish that the dependent
material calculation ran or converged. Propagate only consequences actually
supported. Keep useful abandoned branches and their failures; an existing README
or note index can retain a link if they leave the main argument. A small
"Related investigations" passage is useful when several branches need context,
but routine commands, job polls and unchanged branch states need no updates.

## Make the explanation usable without a navigation chase

Choose what the reader should be able to explain, reproduce or use after this
note. A useful unit includes the premises and steps needed for that result;
it need not match a paragraph, one equation, or a prescribed file size. State
the reader assumptions when consequential, and use
[learning from sources](learning.md) for lecture companions or sustained teaching.

Start from a concrete question and a faithful example when it clarifies the
difficulty. Introduce each new object sufficiently to perform its first use,
including the domain, convention or physical meaning that the operation needs.
Then develop the central calculation, use a relevant check that can expose a failure and
explain the result's use and limitation. These needs do not require fixed
headings. An obstruction needs an example that exhibits it; a trivial case
cannot supply that mechanism.

Expand a transition when the reader would have to guess a new identity,
assumption, sign, boundary term, approximation or physical identification.
State an imported theorem's hypotheses and conclusion to the strength used;
identify its proof as external when it is not supplied. Distinguish a source
claim from a calculation reconstructed here. A link to a later glossary or an
exercise does not supply an explanation required for the current step.

For a method or numerical note, apply this to the operation the reader must
reproduce: connect the mathematical problem, implemented approximation, relevant
settings, observable and evidence. A run log alone does not explain that chain.
Use the existing assets and distinguish an analytic check, code agreement and
physical convergence.

Review the explanation in reading order from its stated prerequisites. Locate
the first unsupported step and repair it and its affected conclusions. Check
captions, examples and exercises too; assigning the central missing derivation
as an exercise is insufficient for a self-study explanation. Keep routine algebra
compact once its operation is established. Scientific correctness and whether a
reader can follow the explanation need separate judgments.

Name the parent topic where it explains the purpose, without making the argument
depend on that project's latest status. Introduce prerequisites at the point of
need, with a short local explanation and a link for depth.

For a reusable concept or theorem, follow
[shared theoretical knowledge](../../aitp-memory/references/shared-knowledge.md).
A concept note teaches an object; a theorem note states quantified hypotheses
and proves or precisely attributes a claim about those objects. Split them only
when each has a substantial independent use. A theorem name or dictionary
definition alone is not a graduate-level explanation.

For an experiment, explain what each comparison discriminates and connect its
conclusion to the actual inputs, code, output and figure. Keep command histories
out of the central argument unless the failure of a command explains a relevant
observation. Reuse an existing report rather than adding a second summary wrapper.

## Connect main text, support and assets

The main note retains the result, decisive assumption and central implication.
Its link says what the supporting note establishes, for example: "The boundary
term invalidates the proposed extension; the linked derivation identifies the
surviving term." Use [citation conventions](citations.md) for formulas and sources.

A supporting note connects its own claims to deeper explanations and original
assets. Direct main-note links to a paper, figure or code file are also useful;
no intermediate Markdown file is required merely to wrap a link. Keep a figure
beside its generating analysis when practical, and identify the data and script
in its caption or nearby prose. A local source path plus a function name is more
useful for evolving code than an unexplained line number alone.

When moving detail, give it its new home before shortening the main text. Repair
outgoing relative links and affected incoming references. Preserve the original
scientific assets and historical run observations. A substantive correction
changes dependent claims as well as the last paragraph of the supporting note.

## Correct claims and keep earlier routes findable

Update according to the changed claim, in either direction between main and
supporting notes. A main-note rewording or shorter exposition need not change a
valid derivation. A new assumption, sign, result or objection requires inspecting
the explanations and applications that actually depend on it. Understand each
affected note's argument before revising it; matching a term is not evidence that
its conclusion fails under the same assumptions.

Search relevant note collections for the changed claim, its terminology or
aliases, and the affected file's name and incoming links. Include retained notes
that the current main note no longer cites. Start with the current topic, the
shared explanation and known dependent topics; follow substantive dependencies
as needed. Do not scan all assets or recursively audit the entire knowledge graph
for an ordinary revision. If the consequences reach beyond the work completed,
identify the known uses still needing review instead of claiming full consistency.

When an error is established, correct the affected statement and conclusions in
the maintained note. Preserve a short explanation of the rejected step when it
prevents repetition. For a historical derivation worth retaining, put a clear
notice before its argument: what claim fails, why, what remains usable, and where
the corrected treatment is, if one exists. Mark the affected passage too when a
search may land there directly. Do not leave a known false claim unqualified until
a future search. If the objection is unresolved, state the precise doubt and
needed check without declaring the whole note false or inventing a replacement.
Keep original PDFs, raw outputs and frozen evidence intact; place their changed
interpretation in the maintained companion or discovery entry.

Removing a citation is a change of relevance, not a deletion request or a verdict
on correctness. Keep useful omitted detail, abandoned approaches and their assets
in place. If no useful route to a retained note remains, add a short entry to the
existing topic README or note index: descriptive linked title, useful search
terms, and the reason to revisit it. A small "Earlier approaches" subsection is
sufficient when appropriate. Label a superseded or disputed conclusion in that
entry and in the note itself. No new index is needed if an existing entry already
makes the material discoverable; do not turn the main note into an inventory.

For a shared explanation, maintain one primary correction and inspect known
applications. Update affected maintained claims, or visibly qualify them when
their derivations still need checking. A correct local result can survive a
failed global extension. On later retrieval, read the note's qualifications and
replacement links before reusing an old formula or copying it into a new note.
Index entries aid discovery; they do not certify validity. Unrelated reads need
no maintenance, and no status schema, backlink database or scheduled sweep is
required.
