# Phase 147: Research Question Competing Hypotheses Surface

## Status

passed

## Goal

Close the research-question modeling gap by making multiple plausible bounded
answers first-class on the active topic surface.

## Background

AITP already has:

- deferred candidates
- follow-up subtopics
- runtime transition/demotion history
- human modification records on approval

But it still lacks one explicit question-level place to say:

- these are the current competing answers
- this one is favored for now
- this one remains alive but weaker
- this one is excluded and why

## Requirements

- add `competing_hypotheses` to the question-level runtime/research surface
- keep statuses and evidence summaries explicit
- make the new surface coexist with deferred candidates and follow-up subtopics
- add one isolated acceptance lane for the bounded multi-hypothesis path

## Depends On

Phase 146 (`v1.72` closure must complete first)

## Deliverables

1. competing hypotheses research-question/runtime surface
2. replay/read-path visibility for that surface
3. isolated acceptance and aligned docs/tests

## Plans

- [x] `147-01`: add competing hypotheses to research-question/runtime surfaces and isolated acceptance
