# Plan: 187.1-01 — Evaluate Jones corpus usefulness against a bounded gold question set

**Phase:** 187.1
**Axis:** Axis 4 (human evidence) + Axis 3 (evaluation recording)
**Requirements:** L2Q-02, L2Q-03

## Goal

Turn the Phase `187` Jones corpus growth result into one bounded usefulness
evaluation with an explicit gold-question set and honest useful / partial / weak
 verdicts.

## Steps

### Step 1: Freeze the gold-question set

Write one bounded question set that covers:

- backbone retrieval
- supporting theorem retrieval
- proof-fragment retrieval
- stronger-theorem limitation retrieval
- full-Chapter-4 out-of-scope retrieval
- local concept-neighborhood retrieval

### Step 2: Run the query set against the current compiled Jones corpus

Use `aitp consult-l2` with the profile chosen per question.

Capture:

- primary hits
- whether gold anchors appeared
- whether unrelated material polluted the answer surface

### Step 3: Score each question honestly

Use only:

- `useful`
- `partial`
- `weak`

Do not hide ranking weaknesses inside prose.

### Step 4: Summarize the corpus-level result

Produce:

- total useful / partial / weak counts
- what the corpus answers well
- what still feels brittle
- what Phase `187.2` must report honestly

## Must Do

- keep the evaluation bounded to the Jones direction
- use explicit gold anchors for each question
- distinguish ranking quality from mere recall
- record at least one residual weakness even if the evaluation is mostly good

## Must Not Do

- do not silently retune the corpus during evaluation
- do not treat "some related hit exists" as automatically useful
- do not claim broad retrieval maturity from one bounded question set
