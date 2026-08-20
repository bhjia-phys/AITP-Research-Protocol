> method-card: <slug>

> Usage (remove this blockquote before saving): a method card is a `mode:
> theory` AITP Note. Create the draft with `aitp note prepare --mode theory
> --title "Method card: <slug>" --created-by agent:<name>`, then replace the
> draft body with the whole template (the `> method-card: <slug>` marker line
> included) and remove this usage blockquote. Slug substitution and
> placeholder removal are Skill completion checks, not runtime gates:
> substitute the real slug into the title and the marker line, and replace
> each section's placeholder text below with actual content from recorded,
> pinned evidence — no placeholder survives in the saved Note. Keep the six
> `##` headings exactly as written — they are the frozen theory Note
> headings — and do not add frontmatter fields, a `#` title, or any AITP
> template prompt comment. The runtime save gate enforces only the fields
> that exist: no AITP template prompt comments, nonempty required sections,
> nonempty `summary`, nonempty pinned reachable `basis_refs`, `review_state:
> agent_draft`, and existing `supersedes` targets.

## Question And Obstruction

What question does this procedure answer, and what would obstruct it?
Triggers: the concrete situations in which this card applies. Route
elsewhere: when this card does NOT apply, and which other card, Skill, or
tool should be used instead.

## Setup And Assumptions

Inputs and preconditions: what must already exist — files, builds, data,
environment, conventions. Applicability: the domain and scale this
procedure is valid for. Resource and tool handoff: which tool Skills or
packages perform the concrete work, and where their parameters live.

## Central Construction Or Argument

Steps and routing: the dependency-ordered procedure — what runs, in what
order, and how each step routes to the tool that performs it.

## Main Result

Outputs, cost, control knobs: what the procedure produces and where the
outputs land; the measured cost (wall time, resources); the control knobs
that change it.

## Checks, Examples, And Failure Modes

Stop-now conditions and verification anchors; benchmarks and solvable
examples; cross-checks against independent methods; the failure map — known
failure modes and their workarounds; trials — the ledger Entries that
pinned this card.

## Limitations And Open Questions

Limits of the procedure and what remains open; what must be re-verified
before the card is reused.
