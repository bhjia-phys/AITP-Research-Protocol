# Design Principles

## 1. Charter before implementation

The public charter defines the intended research posture.
The implementation should be replaceable without redefining the charter.

## 2. Protocol before hidden logic

If a research decision can be expressed as a durable contract, it should not
live only inside Python or prompt residue.

## 3. Evidence before speculation

AITP should distinguish:

- what a source states,
- what follows by short reasoning,
- what is plausible but unestablished,
- what is genuinely conjectural.

## 4. Durable artifacts before chat residue

If something matters, it should exist as an inspectable artifact on disk.

## 5. Reusable knowledge before local convenience

The point of AITP is not just to answer one question. It is to compound useful
research structure over time.

## 6. Preserve uncertainty honestly

Partial derivations, failed attempts, anomalies, and unresolved contradictions
must remain visible rather than being flattened into fake closure.

## 7. Validation is a first-class surface

Language-level plausibility is not enough.
Non-trivial claims should face explicit validation or explicit deferral.

## 8. Human checkpoints remain central

AITP is meant to support serious human-AI research collaboration, not perform
fake autonomy for its own sake.

## 9. Context should be layered

The system should load:

- a short charter,
- a topic-local protocol bundle,
- and only the specific sub-contracts needed for the current step.

This avoids context blowup while preserving rigor.

## 10. Conformance is not correctness

A conformant run means the agent followed the charter and protocol surface.
It does not guarantee that the science is correct.

## 11. Borrow workflow shells, preserve protocol kernel

AITP should learn from systems like Superpowers, GSD, Compound, and OpenSpec
at the workflow-shell layer:

- natural-language entry
- progressive disclosure
- explicit planning and review loops
- compact public command surfaces

But topic state, validation state, promotion gates, and durable runtime truth
must remain part of the protocol kernel rather than collapsing into prompt
convention.

See:

- [`AITP_WORKFLOW_SHELL_AND_PROTOCOL_KERNEL.md`](AITP_WORKFLOW_SHELL_AND_PROTOCOL_KERNEL.md)
- [`AITP_INTELLIGENCE_PRESERVATION_PRINCIPLES.md`](AITP_INTELLIGENCE_PRESERVATION_PRINCIPLES.md)
- [`AITP_ONTOLOGY_AND_MODE_COMPLETENESS.md`](AITP_ONTOLOGY_AND_MODE_COMPLETENESS.md)
- [`AITP_MODE_ENVELOPE_PROTOCOL.md`](AITP_MODE_ENVELOPE_PROTOCOL.md)
- [`AITP_L3_L4_ITERATIVE_VERIFY_LOOP_PROTOCOL.md`](AITP_L3_L4_ITERATIVE_VERIFY_LOOP_PROTOCOL.md)
- [`AITP_TRANSITION_AND_BACKEDGE_PROTOCOL.md`](AITP_TRANSITION_AND_BACKEDGE_PROTOCOL.md)

## 12. Markdown-first human review, thin machine contracts

When a surface primarily exists so a human can review, steer, or audit a
research run, Markdown should carry the full narrative.

JSON and JSONL should remain thin companion contracts only.

Use them for:

- stable ids and statuses,
- artifact paths and replay pointers,
- deterministic machine triggers,
- append-only ledgers,
- staging and promotion decisions that automation must read without scraping
  prose.

Do not duplicate full research narratives, long explanations, or human-facing
judgment in both Markdown and JSON.

For iterative `L3 -> L4 -> L3` research loops, the human should be able to read
one Markdown-first journal, while machine companions stay narrow enough to be
validated and replayed safely.
